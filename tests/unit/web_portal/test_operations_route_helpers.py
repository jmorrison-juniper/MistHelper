"""Tests for saved operation replay events."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

from web_portal.routes.operations import _build_replay, _fetch_msp_grants


class FakeMistSession:
    """Return one controlled self response through the SDK session contract."""

    def __init__(self, response: SimpleNamespace) -> None:
        self.response: SimpleNamespace = response  # Store the response returned by the fake transport.

    def mist_get(self, *, uri: str, query: dict[str, str]) -> SimpleNamespace:
        """Return the response that the SDK self endpoint requests."""
        assert uri == "/api/v1/self"  # Require the SDK to call the self endpoint.
        assert query == {}  # The self endpoint does not take query parameters.
        return self.response  # Return controlled data without a network request.


def _decode_event(event: str) -> tuple[str, dict[str, Any]]:
    """Decode one SSE string so tests can compare its event and payload fields."""
    event_type, data_line, _ = event.splitlines()  # Read the exact three-line SSE format.
    return event_type.removeprefix("event: "), json.loads(data_line.removeprefix("data: "))  # Decode event data.


def _replay_events(executor: Mock, run_id: str) -> list[str]:
    """Return a required replay or fail with a useful test error."""
    events = _build_replay(executor, run_id)  # Build the terminal replay under test.
    if events is None:  # A terminal test fixture must not use the active-run result.
        raise AssertionError(f"Expected replay events for {run_id}.")  # Name the missing test result.
    return events  # Give callers a statically non-empty replay result.


def test_completed_replay_keeps_logs_and_completion_payload() -> None:
    """A completed run replays saved logs before its completion event."""
    status = {
        "status": "completed",
        "log_messages": [{"message": "Started"}, "Legacy line"],
        "debug_messages": [{"message": "Trace"}, "Legacy trace"],
        "completion_message": "Finished without output.",
        "output_files": ["result.csv"],
        "started_at": 10.0,
        "completed_at": 12.5,
    }  # Include both saved message formats and the terminal payload.
    executor = Mock()  # Stand in for the executor without creating a portal service.
    executor.get_run_status.return_value = status  # Return the terminal state for this run.

    events = _replay_events(executor, "run-1")  # Build the browser replay.

    decoded = [_decode_event(event) for event in events]  # Compare structured SSE events.
    assert [event_type for event_type, _ in decoded] == [
        "log",
        "log",
        "debug_log",
        "debug_log",
        "complete",
    ]  # Keep both log groups before the terminal event.
    assert [payload["message"] for _, payload in decoded[:4]] == [
        "Started",
        "Legacy line",
        "Trace",
        "Legacy trace",
    ]  # Preserve messages from both stored formats.
    assert [payload["level"] for _, payload in decoded[:4]] == [
        "info",
        "info",
        "debug",
        "debug",
    ]  # Preserve each event type's default level.
    assert decoded[-1][1] == {
        "run_id": "run-1",
        "status": "completed",
        "message": "Finished without output.",
        "output_files": ["result.csv"],
        "duration_seconds": 2.5,
    }  # Preserve all completion fields and calculated duration.


def test_failed_replay_keeps_failure_message_and_duration() -> None:
    """A failed run replays its saved error event after any log events."""
    status = {
        "status": "failed",
        "error_message": "The operation failed.",
        "started_at": 2.0,
        "completed_at": 5.0,
    }  # Provide a terminal failure with timestamps.
    executor = Mock()  # Stand in for the executor without a running operation.
    executor.get_run_status.return_value = status  # Return the failed state for this run.

    events = _replay_events(executor, "run-2")  # Build the browser replay.

    assert [_decode_event(event) for event in events] == [
        (
            "error_event",
            {
                "run_id": "run-2",
                "status": "failed",
                "message": "The operation failed.",
                "duration_seconds": 3.0,
            },
        )
    ]  # Preserve the failure event and duration.


def test_replay_ignores_missing_and_active_runs() -> None:
    """Only runs with a completed or failed status receive a replay."""
    executor = Mock()  # Stand in for a live operation executor.
    executor.get_run_status.side_effect = [None, {"status": "running"}]  # Return absent and active states.

    assert _build_replay(executor, "missing") is None  # An absent status stays on the live path.
    assert _build_replay(executor, "active") is None  # An active status stays on the live path.
    executor.get_run_status.assert_any_call("missing")  # Confirm the absent run was checked.
    executor.get_run_status.assert_any_call("active")  # Confirm the active run was checked.


def test_msp_grants_filter_invalid_rows_and_sort_name_fallbacks() -> None:
    """Valid grants keep their existing name fallback and stable sort."""
    session = FakeMistSession(
        SimpleNamespace(
            status_code=200,
            data={
                "privileges": [
                    {"msp_id": "msp-z", "msp_name": "Zulu"},
                    {"msp_id": "msp-a", "name": "Alpha"},
                    {"msp_id": "msp-id"},
                    {"msp_id": ""},
                    {"msp_id": 7},
                    "invalid",
                ]
            },
        )
    )  # Use the SDK session interface without a production credential.

    grants = _fetch_msp_grants(session)  # Read the mocked self response.

    assert grants == [
        {"id": "msp-a", "name": "Alpha"},
        {"id": "msp-id", "name": "msp-id"},
        {"id": "msp-z", "name": "Zulu"},
    ]  # Keep valid rows in the label order used by the selector.
    assert grants.reason is None  # A non-empty grant list needs no empty-state explanation.


def test_msp_grants_report_client_error_status() -> None:
    """A refused Mist response remains distinct from an empty grant list."""
    session = FakeMistSession(
        SimpleNamespace(status_code=403, data={"privileges": []})
    )  # Model a refused response through the SDK session interface.
    grants = _fetch_msp_grants(session)  # Read the mocked refused response.

    assert grants == []  # Do not expose grants from a refused response.
    assert grants.reason == "The Mist API returned status 403 while reading MSP access."  # Preserve the refusal.


def test_msp_grants_report_server_error_status() -> None:
    """A Mist server failure remains distinct from an empty grant list."""
    session = FakeMistSession(
        SimpleNamespace(status_code=500, data={"privileges": []})
    )  # Model a failed response through the SDK session interface.
    grants = _fetch_msp_grants(session)  # Read the mocked failed response.

    assert grants == []  # Do not expose grants from a failed response.
    assert grants.reason == "The Mist API returned status 500 while reading MSP access."  # Preserve the failure.
