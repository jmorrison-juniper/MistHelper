"""Unit tests for the post-check seam of the multi-site phase watch.

Why:
    Issue #3244. The phase watch thread holds no request, so the route binds
    the capture seams inside the request. The watch thread then takes each
    capture through the capture route. These tests prove the job fields
    (FR-003 and FR-004), the verdict of each end state, the context of the
    runner, and the log rule of FR-017. A bare Flask application holds the
    stand-in runner, so no test reads a cloud or a database.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import pytest
from flask import Flask, has_app_context

from src.upgrade_portal.app.config import POST_CHECK_MODE_VARIABLE
from src.upgrade_portal.app.routes import capture as capture_routes
from src.upgrade_portal.app.routes.org_postcheck import OrgPostCheckBridge
from src.upgrade_portal.upgrade.org_postcheck import PostCheckResult, PostCheckSite

ORG_ID = "00000000-0000-0000-0000-00000000c244"  # An obviously fake organization.
OPERATOR = "postcheck.operator@juniper.net"  # The address that the operation stores.
SECRET = "SECRET-SESSION-TOKEN-3244"  # The text that no log line may hold.
SITE = PostCheckSite("00000000-0000-0000-0000-00000000a244", "Alpha site", 3, True)  # One site at tier 3.
FAILED_TEXT = "The portal could not read the capture back."  # The failure text of one runner.
KEY_FIELDS = ("run_id", "ordinal", "role", "org_id", "org_name", "actor_email", "site_id", "site_name", "tier")


class SecretSession:
    """Stand in for a signed cloud session whose text holds the token."""

    def __repr__(self) -> str:
        """Return the secret, so a logged session shows the leak."""
        return SECRET  # Any log line that prints this object fails the test.


class StandInRunner:
    """Record each job, and end each capture with one scripted progress change."""

    def __init__(self, change: Callable[[str], None] | None = None) -> None:
        """Keep the scripted end of each capture.

        Args:
            change: The change for the capture key, or None to leave the capture pending.
        """
        self.jobs: list[dict[str, Any]] = []  # The job of each call, in order.
        self.contexts: list[bool] = []  # True when the call ran inside an application context.
        self._change = change  # The scripted end.

    def __call__(self, job: dict[str, Any]) -> None:
        """Record the job and the context, then write the scripted end."""
        self.jobs.append(dict(job))  # A detached copy of the job.
        self.contexts.append(has_app_context())  # The runner reads the configuration of the application.
        if self._change is not None:  # The test scripts an end state.
            self._change(str(job["capture_id"]))  # The same writer as the real collector.


def verified(capture_id: str) -> None:
    """End one capture as the collector ends a verified capture."""
    capture_routes.record_status(capture_id, state=capture_routes.STATE_VERIFIED, verified=True, message="Matched.")


def not_verified(capture_id: str) -> None:
    """End one capture as the collector ends a capture that failed the read-back."""
    capture_routes.record_status(capture_id, state=capture_routes.STATE_FAILED, verified=False, message=FAILED_TEXT)


def raises(capture_id: str) -> None:
    """Raise a fault inside the runner, with the secret in the text."""
    raise RuntimeError(f"{capture_id} {SECRET}")  # The bridge must log the type only.


def bridge_for(runner: Callable[[dict[str, Any]], None], operation: dict[str, Any] | None = None) -> OrgPostCheckBridge:
    """Bind one bridge inside a request of a bare application, and return it."""
    app = Flask("org-postcheck-bridge-test")  # A bare application holds the stand-in runner.
    app.config[capture_routes.RUNNER_KEY] = runner  # The capture route reads this seam.
    with app.test_request_context("/api/org-upgrades/x"):  # The route binds inside one request.
        return OrgPostCheckBridge.bind(operation or {"org_id": ORG_ID, "actor_email": OPERATOR}, SecretSession())


def test_bind_reads_the_mode_inside_the_request(monkeypatch: pytest.MonkeyPatch) -> None:
    """The bridge keeps the post-check mode that the request read."""
    monkeypatch.setenv(POST_CHECK_MODE_VARIABLE, "manual")  # The operator chose the manual mode.
    assert bridge_for(StandInRunner()).mode == "manual"  # The stage then holds each site.


def test_a_verified_capture_runs_in_a_context_with_the_post_check_job() -> None:
    """FR-003 and FR-004: the job names no run, the ordinal 2, the role post, and the tier of the site."""
    runner = StandInRunner(verified)  # The capture verifies.
    bridge = bridge_for(runner)  # Bound inside the request.
    capture_id = bridge.new_capture_id()  # A fresh key with the ordinal 2.
    result = bridge.take(SITE, capture_id)  # The watch thread holds no request.
    assert result == PostCheckResult(capture_id, True, "Matched.")  # The stage stores a verified row.
    assert runner.contexts == [True]  # The bridge pushed a fresh application context.
    fields = {name: runner.jobs[0][name] for name in KEY_FIELDS}  # The fields that the collector reads.
    assert fields == {
        "run_id": "",
        "ordinal": 2,
        "role": "post",
        "org_id": ORG_ID,
        "org_name": ORG_ID,  # A session with no privilege list names the organization by its key.
        "actor_email": OPERATOR,
        "site_id": SITE.site_id,
        "site_name": SITE.site_name,
        "tier": 3,
    }  # The job of a capture with no run.
    assert repr(runner.jobs[0]["cloud_session"]) == SECRET  # The collector receives the signed session.


def test_the_progress_record_opens_before_the_runner_starts() -> None:
    """The capture page can read the capture while the runner still reads the site."""
    seen: list[str] = []  # The progress state that the runner found.
    runner = StandInRunner(
        lambda capture_id: seen.append(str((capture_routes.read_progress(capture_id) or {})["state"]))
    )
    bridge = bridge_for(runner)  # Bound inside the request.
    bridge.take(SITE, bridge.new_capture_id())  # The runner reads the progress record.
    assert seen == [capture_routes.STATE_PENDING]  # The record existed before the read started.


@pytest.mark.parametrize(
    ("change", "message"),
    [(not_verified, FAILED_TEXT), (None, capture_routes.START_MESSAGE), (raises, capture_routes.FAILED_MESSAGE)],
    ids=["failed-read-back", "still-pending", "runner-fault"],
)
def test_a_capture_that_did_not_verify_reads_failed(change: Callable[[str], None] | None, message: str) -> None:
    """FR-011: a failed read-back, a capture that never ended, and a fault all read as not verified."""
    bridge = bridge_for(StandInRunner(change))  # Bound inside the request.
    capture_id = bridge.new_capture_id()  # A fresh key with the ordinal 2.
    assert bridge.take(SITE, capture_id) == PostCheckResult(capture_id, False, message)  # The stage stores failed.


def test_a_dropped_progress_record_reads_the_stored_capture(monkeypatch: pytest.MonkeyPatch) -> None:
    """After a trim, the verdict comes from the stored capture and its read-back flag."""
    stored = {"state": "complete", "verified": True, "message": ""}  # The stored status of a verified capture.
    monkeypatch.setattr(capture_routes, "read_progress", lambda capture_id: None)  # The trim dropped the record.
    monkeypatch.setattr(capture_routes, "stored_body", lambda capture_id: dict(stored) if has_app_context() else None)
    bridge = bridge_for(StandInRunner())  # Bound inside the request.
    capture_id = bridge.new_capture_id()  # A fresh key with the ordinal 2.
    assert bridge.take(SITE, capture_id) == PostCheckResult(capture_id, True, "")  # The store proves the capture.


def test_an_operation_with_no_operator_names_nobody() -> None:
    """A record of an earlier release holds no address, and a bare request names no operator."""
    runner = StandInRunner(verified)  # The capture verifies.
    bridge = bridge_for(runner, {"org_id": ORG_ID})  # The operation stores no operator.
    bridge.take(SITE, bridge.new_capture_id())  # One capture.
    assert runner.jobs[0]["actor_email"] == ""  # The honest fallback.


def test_no_log_line_holds_the_cloud_session_or_the_job(caplog: pytest.LogCaptureFixture) -> None:
    """FR-017: the bridge logs the key, the site, the tier, and the fault type only."""
    caplog.set_level(logging.DEBUG)  # Read every line of every logger.
    bridge = bridge_for(StandInRunner(raises))  # The runner fault holds the secret in its text.
    bridge.take(SITE, bridge.new_capture_id())  # One capture that fails.
    assert SECRET not in caplog.text  # No line printed the session or the fault text.
    assert "cloud_session" not in caplog.text  # No line printed the job.
    assert SECRET not in repr(bridge)  # A stray log of the bridge leaks nothing.
