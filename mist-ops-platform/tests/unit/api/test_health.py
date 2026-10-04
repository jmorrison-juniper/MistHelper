"""Tests proving the health route silent failures now leave a record.

Issue #2038, findings 1 and 2.
Finding 1: /readyz logged nothing on both failure paths.
Finding 2: /metrics answered 200 with a placeholder body.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# WHY: import the router so we can mount a minimal FastAPI app for tests.
from fastapi import FastAPI

from src.api.routes.health import router


def _build_app(engine: object | None = None) -> FastAPI:
    """Build a minimal FastAPI app with the health router and optional engine."""
    app = FastAPI()  # WHY: a real FastAPI instance keeps middleware wiring intact.
    app.include_router(router)  # WHY: attach the health routes under test.
    app.state.engine = engine  # WHY: the readyz handler reads this attribute.
    return app


# ---------------------------------------------------------------------------
# Finding 1: /readyz silent failure paths
# ---------------------------------------------------------------------------


class TestReadyzLogsOnMissingEngine:
    """Prove that /readyz logs a warning when the engine is absent."""

    def test_missing_engine_emits_a_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        # WHY: build an app with no engine so the first failure path triggers.
        app = _build_app(engine=None)
        client = TestClient(app, raise_server_exceptions=False)

        with caplog.at_level(logging.WARNING, logger="src.api.routes.health"):
            response = client.get("/readyz")  # WHY: call the probe directly.

        # WHY: the response contract must not change.
        assert response.status_code == 200
        assert response.json() == {"status": "unavailable"}
        # WHY: the bug was silence. The fix must produce at least one warning record.
        assert any(
            r.levelno >= logging.WARNING for r in caplog.records
        ), "Expected a WARNING on the missing-engine path but the log was empty."


class TestReadyzLogsOnQueryFailure:
    """Prove that /readyz logs the exception when the database query fails."""

    def test_query_failure_emits_exception_info(self, caplog: pytest.LogCaptureFixture) -> None:
        # WHY: supply a fake engine whose connect raises, so the except branch runs.
        fake_conn = AsyncMock()
        fake_conn.execute.side_effect = RuntimeError("connection refused")

        # WHY: the async context manager must deliver the fake conn object.
        fake_conn_ctx = AsyncMock()
        fake_conn_ctx.__aenter__.return_value = fake_conn
        fake_conn_ctx.__aexit__.return_value = False

        fake_engine = MagicMock()
        fake_engine.connect.return_value = fake_conn_ctx

        app = _build_app(engine=fake_engine)
        client = TestClient(app, raise_server_exceptions=False)

        with caplog.at_level(logging.WARNING, logger="src.api.routes.health"):
            response = client.get("/readyz")  # WHY: call the probe with a broken engine.

        # WHY: the response contract must not change.
        assert response.status_code == 200
        assert response.json() == {"status": "unavailable"}
        # WHY: the fix must record the exception, not swallow it.
        has_exc_info = any(r.levelno >= logging.WARNING and r.exc_info for r in caplog.records)
        has_error_text = any(
            "connection refused" in r.getMessage().lower() or "connection refused" in str(r.exc_info).lower()
            for r in caplog.records
            if r.exc_info
        )
        assert has_exc_info or has_error_text, "Expected the query exception to appear in the log, but it was absent."


# ---------------------------------------------------------------------------
# Finding 2: /metrics must not answer 200 while delivering nothing
# ---------------------------------------------------------------------------


class TestMetricsAnswers501:
    """Prove that /metrics answers 501 instead of 200."""

    def test_metrics_returns_501(self) -> None:
        # WHY: an app with no engine is fine here because metrics does not use it.
        app = _build_app()
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/metrics")  # WHY: call the placeholder endpoint.

        # WHY: 200 hides the gap from monitoring. The fix must return 501.
        assert response.status_code == 501, f"Expected HTTP 501 from /metrics but received {response.status_code}."

    def test_metrics_emits_a_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        # WHY: every scrape should announce the gap in the log.
        app = _build_app()
        client = TestClient(app, raise_server_exceptions=False)

        with caplog.at_level(logging.WARNING, logger="src.api.routes.health"):
            client.get("/metrics")  # WHY: call the route to trigger the log.

        # WHY: a silent placeholder is the bug. The fix must produce a warning.
        assert any(
            r.levelno >= logging.WARNING for r in caplog.records
        ), "Expected a WARNING from /metrics but the log was empty."
