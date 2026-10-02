"""Prove actual stored routes and native stand-in runner writes without external stores."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from copy import deepcopy
from typing import Any
from unittest.mock import Mock

import pytest
import redis
import requests

from src.export.data_exporter import DataExporter
from src.upgrade_portal.app.routes import capture
from src.upgrade_portal.capture import assembly, store
from tests.support.upgrade_portal_e2e import RunOwnerHeaderCheck
from tests.support.upgrade_portal_e2e.capture_fidelity import NativeCaptureFixture, PrivateCaptureScenario

logger = logging.getLogger(__name__)


class NativeRunnerChecks:
    """Check the actual stored runner document without replacing the writer."""

    @staticmethod
    def document(document: dict[str, Any], job: dict[str, Any]) -> None:
        """Require native content, lifecycle, ownership, counts, and serving names."""
        assert document["capture_status"] == assembly.STATUS_COMPLETE
        assert document[store.CAPTURE_STATE_FIELD] == store.CaptureState.VERIFIED.value
        assert {field: document[field] for field in ("run_id", "role", "tier", "site_id")} == {
            field: job[field] for field in ("run_id", "role", "tier", "site_id")
        }
        assert len(document["device_index"]) == 3 and len(document["counts"]) == 9
        assert [row["device_name"] for row in document["clients"]["wireless"]] == [
            "E2E ap 1",
            "E2E gateway 2",
            "E2E switch 3",
        ]
        progress = capture.read_progress(job["capture_id"])
        assert progress is not None and progress["state"] == capture.STATE_VERIFIED
        print(
            "Checked actual stand-in runner calls=1 stored document delta=1 "
            "device rows=3 count fields=9 parent rows=3."
        )


class TestNativeStoredCaptureContracts:
    """Keep each test in a fresh private store with explicit outside-I/O refusals."""

    @pytest.fixture
    def scenario(
        self, request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
    ) -> Iterator[PrivateCaptureScenario]:
        """Own a native scenario and fail instead of making any outside store or SDK call."""
        targets = [
            (requests.sessions.Session, "request"),
            (redis.Redis, "execute_command"),
            (store, "connect_database"),
            (DataExporter, "write_with_format_selection"),
        ]
        forbidden = [
            Mock(side_effect=AssertionError("The harness reached outside transport or storage.")) for _ in targets
        ]
        for (owner, name), callback in zip(targets, forbidden, strict=True):
            monkeypatch.setattr(owner, name, callback)
        monkeypatch.setattr(capture, "_PROGRESS", {})
        scenario = PrivateCaptureScenario(NativeCaptureFixture.read(request.config), monkeypatch)
        try:
            yield scenario
        finally:
            scenario.session.close()
            assert [callback.call_count for callback in forbidden] == [0, 0, 0, 0]
            assert scenario.reads.actions == []
            print("Checked outside transport/store boundaries=4 calls=0 actual upgrade/start/cancel callbacks=0.")

    @pytest.mark.parametrize("capture_id", ["e2e-capture-pre-0001", "e2e-capture-tier3-0001"])
    def test_stored_content_and_terminal_lifecycle_stay_separate(
        self, scenario: PrivateCaptureScenario, capture_id: str
    ) -> None:
        """Stored complete and partial content must not replace terminal lifecycle progress."""
        logger.info("Read the actual stored document and status routes")
        document = scenario.records.load_capture(capture_id).capture
        assert document is not None and document["capture_id"] == capture_id
        response = scenario.session.client.get(f"/api/captures/{capture_id}/status")
        RunOwnerHeaderCheck(scenario.overrides.test_run_id).require(response.headers)
        assert response.status_code == 200
        body = response.get_json()
        expected = assembly.STATUS_PARTIAL if capture_id == "e2e-capture-tier3-0001" else assembly.STATUS_COMPLETE
        assert document["capture_status"] == expected and document[store.CAPTURE_STATE_FIELD] == "verified"
        assert body["state"] == capture.STATE_VERIFIED and body["verified"] is True
        assert body["counts"] == document["counts"] and len(body["counts"]) == 9
        assert body["partial_reasons"] == document["partial_reasons"]
        logger.debug("Checked stored documents=1 native count fields=9 terminal lifecycle fields=2")

    def test_real_precheck_card_adopts_private_partial_and_refuses_pending(
        self, scenario: PrivateCaptureScenario
    ) -> None:
        """Render the actual card after the actual plan save, without starting any capture or upgrade."""
        identifiers = scenario.Identifiers
        scenario.session.save_plan()
        response = scenario.session.client.get("/upgrade/org/confirm")
        RunOwnerHeaderCheck(scenario.overrides.test_run_id).require(response.headers)
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert f'data-testid="org-upgrade-precheck-row-{identifiers.SITE_ID}"' in page
        assert f'href="/captures/{identifiers.CAPTURE_ID}"' in page
        assert f'data-testid="org-upgrade-precheck-row-{identifiers.PENDING_SITE_ID}"' in page
        assert identifiers.PENDING_CAPTURE_ID not in page
        assert scenario.records.newest_precheck_tier(identifiers.SITE_ID) == (identifiers.CAPTURE_ID, 3)
        assert scenario.records.newest_precheck_tier(identifiers.PENDING_SITE_ID) == ("", 2)
        for capture_id, original in scenario.original.items():
            current = scenario.records.load_capture(capture_id).capture
            assert current is not None and current["capture_id"] == capture_id
            assert {key: value for key, value in current.items() if key != "test_run_id"} == original
        assert scenario.reads.actions == []
        print(
            "Checked rendered pre-check cards=1 site rows=2 partial adoptions=1 "
            "pending refusals=1 preserved global seeds=5."
        )

    @pytest.mark.parametrize(("role", "tier"), [("pre", 2), ("pre", 3), ("post", 2), ("post", 3)])
    def test_actual_runner_stores_one_native_standalone_document(
        self, scenario: PrivateCaptureScenario, request: pytest.FixtureRequest, role: str, tier: int
    ) -> None:
        """Observe the actual runner write rather than fabricating its document."""
        native = NativeCaptureFixture.read(request.config)
        job: dict[str, Any] = {
            "capture_id": f"e2e-3375-runner-{role}-{tier}",
            "run_id": "",
            "role": role,
            "tier": tier,
            "site_id": scenario.Identifiers.SITE_ID,
        }
        before = scenario.records.list_captures()
        capture.open_progress(job["capture_id"], capture.opening_record(job))
        with scenario.app.app_context():
            native.stand_in_capture_runner(job)
        after = scenario.records.list_captures()
        document = scenario.records.load_capture(job["capture_id"]).capture
        assert document is not None and len(after) == len(before) + 1
        NativeRunnerChecks.document(document, job)


class TestNativeCaptureErrorContracts:
    """Retain explicit HTTP failure evidence and the actual run-owned runner behavior."""

    @pytest.fixture
    def scenario(
        self, request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
    ) -> Iterator[PrivateCaptureScenario]:
        """Own one process-isolated error scenario."""
        monkeypatch.setattr(capture, "_PROGRESS", {})
        scenario = PrivateCaptureScenario(NativeCaptureFixture.read(request.config), monkeypatch)
        try:
            yield scenario
        finally:
            scenario.session.close()
            assert scenario.reads.actions == []

    def test_missing_capture_returns_http_404(self, scenario: PrivateCaptureScenario) -> None:
        """An absent record must report a real refusal without a store fallback."""
        response = scenario.session.client.get("/api/captures/e2e-3375-missing/status")
        assert response.status_code == 404
        body: dict[str, Any] = response.get_json()
        assert body["error"]["code"] == store.REASON_CAPTURE_NOT_FOUND
        assert scenario.records.load_capture("e2e-3375-missing").capture is None

    def test_capture_loader_failure_returns_http_500(self, scenario: PrivateCaptureScenario) -> None:
        """A controlled loader failure must remain visible through the real Flask error boundary."""
        loader = Mock(side_effect=RuntimeError("Controlled capture loader failure for issue 3375."))
        scenario.app.config.update(TESTING=False, CAPTURE_LOADER=loader)
        response = scenario.session.client.get(f"/api/captures/{scenario.Identifiers.CAPTURE_ID}/status")
        assert response.status_code == 500
        assert loader.call_count == 1
        assert response.get_json()["error"]["code"] == "server_error"

    def test_run_owned_job_keeps_the_existing_zero_document_write(
        self, scenario: PrivateCaptureScenario, request: pytest.FixtureRequest
    ) -> None:
        """The field repair must not add unrelated run-owned capture persistence."""
        job: dict[str, Any] = {
            "capture_id": "e2e-3375-run-owned-job",
            "run_id": "e2e-3375-missing-run",
            "role": "pre",
            "tier": 2,
            "site_id": scenario.Identifiers.SITE_ID,
        }
        before = deepcopy(scenario.records.list_captures())
        native = NativeCaptureFixture.read(request.config)
        capture.open_progress(job["capture_id"], capture.opening_record(job))
        with scenario.app.app_context():
            native.stand_in_capture_runner(job)
        assert scenario.records.list_captures() == before
        assert scenario.records.load_capture(job["capture_id"]).capture is None
        progress = capture.read_progress(job["capture_id"])
        assert progress is not None and progress["state"] == capture.STATE_VERIFIED
        print("Checked actual run-owned runner calls=1 document delta=0 upgrade callbacks=0.")
