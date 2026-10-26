"""Prove that utility terminal notification follows capture cleanup."""

from __future__ import annotations

import logging
import threading
from dataclasses import replace
from unittest.mock import Mock

import pytest

from src.mist.realtime.websocket_streams.live.runners.utility.filters.message_filter import UtilityMessageFilter
from src.mist.realtime.websocket_streams.live.runners.utility.runner.execution import (
    UtilityExecution,
    UtilityStarter,
    UtilityStreamOpener,
)
from src.mist.realtime.websocket_streams.live.runners.utility.runner.monitoring import UtilityStreamMonitor
from src.mist.realtime.websocket_streams.live.runners.utility.runner.utility_runner import RunContext, RunnerState
from src.mist.realtime.websocket_streams.live.runners.utility.triggers.table import UtilityTriggerTable
from src.mist.realtime.websocket_streams.live.sessions.record.state import SessionState
from src.mist.realtime.websocket_streams.live.transport.endpoint import ConnectFailure, MistStreamEndpoint
from src.mist.realtime.websocket_streams.live.transport.stream_client import StreamClient
from tests.unit.websocket_streams.live.runners.utility.test_ws_utility_runner import FakeSink, _request
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.api import FakeApiSession


class CleanupCase:
    """Keep real cleanup and finalization with controlled execution seams."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, key: str) -> None:
        """Prepare one stopped capture without a network connection."""
        self.api = FakeApiSession()  # Keep the existing controlled REST response contract.
        self.sink = FakeSink()  # Observe the same terminal notification as the live regression.
        request = _request(key, "packets")  # Preserve the real checked capture request shape.
        request = replace(request, targets={**request.targets, "mxedge_id": ("edge-owned",)})
        table = UtilityTriggerTable()  # Resolve production capture scope and paths.
        trigger = table.request_for(request)  # Keep identity checks in the production cleanup code.
        state = RunnerState(trigger=trigger, answer={"id": "owned-capture"})  # Model a returned trigger answer.
        self.client = Mock(spec=StreamClient)  # Isolate stream I/O from the cleanup-order proof.
        state.client = self.client  # Exercise production stream closure before capture cleanup.
        self.context = RunContext(self.api, MistStreamEndpoint(self.api), request, self.sink, table, state)
        self.execution = UtilityExecution(self.context)  # Keep production exception and finalization paths.
        self.path = trigger.path.removesuffix("/capture")  # Use the actual scope from the trigger.
        self.api.add_override("/pcaps?limit=1", data=[{"id": "owned-capture"}])  # Match this capture only.
        opened = (self.client, trigger, UtilityMessageFilter(trigger.listen.channel))
        monkeypatch.setattr(UtilityStarter, "start", Mock(return_value=opened))  # Isolate subscription setup.
        monkeypatch.setattr(UtilityStreamMonitor, "read", Mock())  # Control when monitoring ends.
        state.stopping.set()  # Make capture cleanup required before terminal notification.

    def barrier(self, monkeypatch: pytest.MonkeyPatch) -> tuple[threading.Event, threading.Event]:
        """Hold DELETE before the fake cloud records the matching request."""
        entered, release = threading.Event(), threading.Event()  # Synchronize without a scheduling delay.
        delete = self.api.mist_delete  # Keep the real fake-cloud recording after the barrier.

        def blocked_delete(uri: str) -> object:
            """Pause cleanup until the test examines terminal state."""
            entered.set()  # Publish that execution reached the cleanup boundary.
            if not release.wait(3.0):  # Bound failed proofs without leaving a worker behind.
                raise RuntimeError("The cleanup barrier was not released.")
            return delete(uri)  # Record DELETE only after the test releases cleanup.

        monkeypatch.setattr(self.api, "mist_delete", blocked_delete)  # Pause the exact matching cleanup action.
        return entered, release  # Give the test ownership of barrier release.


class TestCaptureCleanupCompletion:
    """Check cleanup ordering without changing the existing live test."""

    @pytest.mark.parametrize("key", ["ex.remotePcap", "mxedge.orgRemotePcap"])
    @pytest.mark.parametrize("execution_error", [False, True])
    def test_terminal_waits_for_matching_delete(
        self, monkeypatch: pytest.MonkeyPatch, key: str, execution_error: bool
    ) -> None:
        """Withhold every terminal result while matching DELETE is blocked."""
        case = CleanupCase(monkeypatch, key)  # Use real scope selection and identity matching.
        if execution_error:  # Exercise the execution-error finalization path as well.
            monkeypatch.setattr(UtilityStreamMonitor, "read", Mock(side_effect=RuntimeError("monitor failed")))
        entered, release = case.barrier(monkeypatch)  # Stop cleanup before its request record exists.
        worker = threading.Thread(target=case.execution.run)  # Keep explicit worker ownership for teardown.
        worker.start()  # Run the unmodified production lifecycle on another thread.
        try:
            assert entered.wait(3.0), "The worker did not reach capture cleanup."
            assert case.sink.finished == [], "Terminal state preceded matching DELETE cleanup."
            assert [call.method for call in case.api.calls] == ["GET"]  # DELETE cannot pass the held barrier.
        finally:
            release.set()  # Release even when the unchanged-source proof fails.
            worker.join(3.0)  # Do not leave a worker active after this test.
        assert not worker.is_alive()  # Cleanup and finalization must both end.
        assert case.sink.finished == [(SessionState.STOPPED, "The operator stopped the session.")]
        assert [(call.method, call.uri) for call in case.api.calls] == [
            ("GET", f"{case.path}?limit=1"),
            ("DELETE", case.path),
        ]  # The exact owned capture cleanup precedes the final result.

    @pytest.mark.parametrize("key", ["ex.remotePcap", "mxedge.orgRemotePcap"])
    @pytest.mark.parametrize("capture_id", ["different-capture", None])
    def test_unowned_or_absent_capture_is_not_deleted(
        self, monkeypatch: pytest.MonkeyPatch, key: str, capture_id: str | None
    ) -> None:
        """Preserve capture identity checks when the active capture changes."""
        case = CleanupCase(monkeypatch, key)  # Use the production scope and identity decision.
        case.api.overrides.clear()  # Replace the owned match with the selected boundary response.
        rows = [] if capture_id is None else [{"id": capture_id}]  # Model absent and different captures.
        case.api.add_override("/pcaps?limit=1", data=rows)  # Keep production capture inspection active.
        case.execution.run()  # Complete cleanup before inspecting terminal state.
        assert [(call.method, call.uri) for call in case.api.calls] == [("GET", f"{case.path}?limit=1")]
        assert case.sink.finished == [(SessionState.STOPPED, "The operator stopped the session.")]
        case.client.close.assert_called_once_with()  # Close the owned stream even without a matching capture.

    @pytest.mark.parametrize("stage", ["GET", "DELETE", "close"])
    def test_cleanup_exception_reports_failure(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, stage: str
    ) -> None:
        """Do not hide cleanup failure behind an operator-stopped result."""
        case = CleanupCase(monkeypatch, "ex.remotePcap")  # The stop flag must not mask cleanup failure.
        failure = RuntimeError("controlled cleanup failure")  # Keep the test independent of network errors.
        if stage == "close":  # Cover stream closure as well as capture API errors.
            case.client.close.side_effect = failure
        else:
            method = "mist_get" if stage == "GET" else "mist_delete"
            monkeypatch.setattr(case.api, method, Mock(side_effect=failure))
        with caplog.at_level(logging.ERROR):  # Require an explicit diagnostic rather than a thread exception.
            case.execution.run()
        assert case.sink.finished == [
            (SessionState.FAILED, "The utility cleanup failed. Read the portal log for the cause.")
        ]
        assert "utility_cleanup_failed" in caplog.text  # Cleanup failure must remain visible in the log.
        assert "RuntimeError" in caplog.text  # The diagnostic names the failure type without private text.
        case.client.close.assert_called_once_with()  # Every path makes one stream cleanup attempt.

    @pytest.mark.parametrize(
        ("outcome", "expected"),
        [("output", SessionState.FINISHED), ("empty", SessionState.TIMED_OUT), ("error", SessionState.FAILED)],
    )
    def test_existing_execution_outcomes_follow_stream_close(
        self, monkeypatch: pytest.MonkeyPatch, outcome: str, expected: SessionState
    ) -> None:
        """Keep normal execution classification after the cleanup boundary."""
        case = CleanupCase(monkeypatch, "ex.remotePcap")  # Reuse production lifecycle and finalization.
        case.context.state.stopping.clear()  # Normal completion must not stop a remote capture.
        case.context.state.output_count = int(outcome == "output")  # Preserve finished versus no-output behavior.
        if outcome == "error":  # Exercise failure before monitoring starts.
            monkeypatch.setattr(UtilityStarter, "start", Mock(side_effect=RuntimeError("startup failed")))
        case.client.close.side_effect = lambda: case.sink.finished == [] or pytest.fail(
            "Terminal state preceded close."
        )  # Observe notification order inside the cleanup call.
        case.execution.run()  # Keep startup failure and normal finalization on the same cleanup path.
        assert len(case.sink.finished) == 1  # Each run produces exactly one terminal notification.
        assert case.sink.finished[0][0] == expected  # Cleanup must not change the execution classification.
        case.client.close.assert_called_once_with()  # Even startup failure closes an allocated stream.
        assert case.api.calls == []  # Normal completion must not introduce a capture-stop policy change.

    @pytest.mark.parametrize("interrupt", [KeyboardInterrupt, SystemExit])
    def test_process_interrupt_still_closes_stream(
        self, monkeypatch: pytest.MonkeyPatch, interrupt: type[BaseException]
    ) -> None:
        """Keep unconditional cleanup when execution cannot classify an interrupt."""
        case = CleanupCase(monkeypatch, "ex.remotePcap")  # Keep the existing finally-block safety contract.
        monkeypatch.setattr(UtilityStarter, "start", Mock(side_effect=interrupt))
        with pytest.raises(interrupt):  # Process-control exceptions must not become ordinary execution failures.
            case.execution.run()
        case.client.close.assert_called_once_with()  # An interrupt must still release the owned stream.
        assert [call.method for call in case.api.calls] == ["GET", "DELETE"]  # Preserve matching cleanup.
        assert case.sink.finished == []  # Do not report success for an unclassified process interrupt.


class TestTriggerFailureCompletion:
    """Keep cleanup and terminal failure ordering for rejected capture triggers."""

    @staticmethod
    def _case(monkeypatch: pytest.MonkeyPatch) -> CleanupCase:
        """Use the real starter and fake only the stream connection."""
        case = CleanupCase(monkeypatch, "ex.remotePcap")  # Retain the controlled API and sink.
        monkeypatch.undo()  # Restore the real starter and monitor for failure-path integration.
        monkeypatch.setattr(UtilityStreamOpener, "_client", Mock(return_value=case.client))
        case.context.state.stopping.clear()  # Trigger errors must retain their failure classification.
        case.context.state.answer = None  # A failed trigger never supplies a capture identifier.
        case.client.close.side_effect = lambda: case.sink.finished == [] or pytest.fail(
            "Terminal state preceded close."
        )  # Inspect ordering at the actual cleanup boundary.
        return case  # Let each failure reach the real sender and execution handler.

    @pytest.mark.parametrize("status_code", [400, 503])
    def test_http_trigger_failure_closes_before_notification(
        self, monkeypatch: pytest.MonkeyPatch, status_code: int
    ) -> None:
        """Keep HTTP client and server errors explicit after stream closure."""
        case = self._case(monkeypatch)  # Exercise the real startup, trigger, cleanup, and finisher.
        case.api.add_override("/pcaps/capture", status_code=status_code)  # Return a controlled HTTP failure.
        case.execution.run()  # Reject the trigger before any capture identifier exists.
        assert case.sink.finished == [(SessionState.FAILED, f"The utility failed with status {status_code}.")]
        case.client.close.assert_called_once_with()  # The opened stream must close before failure notification.
        assert [(call.method, call.uri) for call in case.api.calls] == [("POST", f"{case.path}/capture")]

    @pytest.mark.parametrize(
        ("error_type", "reason"),
        [(TimeoutError, ConnectFailure.TIMEOUT_TEXT), (ConnectionError, ConnectFailure.NETWORK_TEXT)],
    )
    def test_connection_failure_closes_before_notification(
        self, monkeypatch: pytest.MonkeyPatch, error_type: type[Exception], reason: str
    ) -> None:
        """Preserve safe timeout and connection-error reasons after cleanup."""
        case = self._case(monkeypatch)  # Keep the real failure classification path.
        case.api.add_override("/pcaps/capture", exception=error_type("controlled trigger failure"))
        case.execution.run()  # A failed external request must still release its allocated stream.
        assert case.sink.finished == [(SessionState.FAILED, reason)]  # Retain the safe connection reason.
        case.client.close.assert_called_once_with()  # Cleanup must precede terminal failure.
        assert [(call.method, call.uri) for call in case.api.calls] == [("POST", f"{case.path}/capture")]
