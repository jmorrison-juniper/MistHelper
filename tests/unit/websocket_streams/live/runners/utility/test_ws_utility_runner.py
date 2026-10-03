"""Tests for the owned WebSockets utility runner."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # The Show Route fake output is one JSON text line, as on the live SRX.
import threading  # The fake sink waits for the background runner thread.
import time  # Reliability tests report measured run time.
from dataclasses import replace  # Short timing tables replace immutable trigger records.

import pytest  # The tests verify request errors and time bounds.
import websocket  # Tests build the same handshake exceptions as websocket-client.

from src.mist.realtime.websocket_streams.catalog.model import (
    Safety,
    UtilityDefinition,
)  # Tests build utility definitions.
from src.mist.realtime.websocket_streams.intake.start_request.models import (
    StartRequest,
)  # Tests build checked start requests.
from src.mist.realtime.websocket_streams.live.runners.utility.runner.execution import (
    UtilityStreamOpener,
)  # Subscribe seam.
from src.mist.realtime.websocket_streams.live.runners.utility.runner.utility_runner import (
    UtilityRunner,
)  # Utility runner class.
from src.mist.realtime.websocket_streams.live.runners.utility.triggers.models import (
    UtilityRequest,
    UtilityTiming,
)  # Immutable trigger records.
from src.mist.realtime.websocket_streams.live.runners.utility.triggers.table import (
    UtilityTriggerTable,
)  # Trigger table class.
from src.mist.realtime.websocket_streams.live.sessions.record.state import (
    SessionState,
)  # Sink assertions use final states.
from src.mist.realtime.websocket_streams.live.transport.endpoint import (
    ConnectFailure,
    MistStreamEndpoint,
    TransportProfile,
)  # Endpoint setup.
from src.mist.realtime.websocket_streams.live.transport.stream_client import (
    StreamClient,
)  # Stop tests override open behavior.
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.api import (
    FakeApiCall,
    FakeApiSession,
)  # Offline REST trigger fake.
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.devices import (
    StreamDevice,
)  # Offline stream device fake.
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.server import (
    FakeMistCloud,
    HandshakeFault,
)  # Offline WebSocket fake.

SITE_ID = "11111111-1111-1111-1111-111111111111"  # Stable site identifier for trigger paths.
DEVICE_ID = "22222222-2222-2222-2222-222222222222"  # Stable device identifier for trigger paths.
ORG_ID = "33333333-3333-3333-3333-333333333333"  # Stable org identifier for org captures.
COMMAND_CHANNEL = f"/sites/{SITE_ID}/devices/{DEVICE_ID}/cmd"  # Command stream channel path.
CAPTURE_CHANNEL = f"/sites/{SITE_ID}/pcaps"  # Site packet capture channel path.


class FakeSink:
    """A thread-safe sink for runner tests."""

    def __init__(self) -> None:
        """Build an empty sink."""
        self.messages: list[tuple[str, object, str | None]] = []  # Keep output messages in order.
        self.finished: list[tuple[SessionState, str]] = []  # Keep the final state and reason.
        self.live_calls = 0  # Count mark_live calls.
        self._condition = threading.Condition()  # The test waits for finish with this condition.

    def mark_live(self, note: str = "") -> None:
        """Record a live transition."""
        _note_length = len(note)  # Read the optional note without storing sensitive text.
        with self._condition:  # Protect the counter because the runner uses another thread.
            self.live_calls += 1  # The runner should mark live once per run.

    def add_message(self, kind: str, content: object, *, source: str | None = None, summary: str | None = None) -> None:
        """Record one output message."""
        _source_length = len(source or "")  # Read the optional source without changing message assertions.
        with self._condition:  # Protect output order.
            self.messages.append((kind, content, summary))  # Store only the fields that page tests need.
            self._condition.notify_all()  # Wake waits that look for output.

    def finish(self, state: SessionState, reason: str) -> None:
        """Record the final state."""
        with self._condition:  # Protect the final state.
            self.finished.append((state, reason))  # Store each finish call.
            self._condition.notify_all()  # Wake the waiting test.

    def wait_finished(self, timeout: float = 3.0) -> tuple[SessionState, str]:
        """Wait for one final state.

        Args:
            timeout: The maximum wait in seconds.

        Returns:
            The final state and reason.
        """
        deadline = time.monotonic() + timeout  # Bound every test wait.
        with self._condition:  # Wait on the same condition that finish() notifies.
            while not self.finished:  # Stop when the runner records a final state.
                remaining = deadline - time.monotonic()  # Recalculate the remaining wait.
                if remaining <= 0.0:  # A missing finish is a test failure.
                    raise AssertionError("The utility runner did not finish in time.")  # Give one clear failure.
                self._condition.wait(remaining)  # Wait until finish() or timeout.
            return self.finished[-1]  # Return the latest state for assertions.


class ExplodingSink(FakeSink):
    """A sink that raises when the runner emits output."""

    def add_message(self, kind: str, content: object, *, source: str | None = None, summary: str | None = None) -> None:
        """Raise during output to test the broad failure path."""
        _kind_length = len(kind)  # Read the kind without using output content.
        _source_length = len(source or "")  # Read the source without storing it.
        _summary_length = len(summary or "")  # Read the summary without storing it.
        raise TypeError("sink exploded")  # Model an unexpected sink failure.


class ShortTriggerTable(UtilityTriggerTable):
    """Return real triggers with test timing limits."""

    def __init__(self, timing: UtilityTiming) -> None:
        """Build a short trigger table.

        Args:
            timing: The replacement timing.
        """
        super().__init__()  # Keep base table initialization behavior.
        self._timing = timing  # Store replacement timing for request_for().

    def request_for(self, request: StartRequest) -> UtilityRequest:
        """Return a real request with short timing.

        Args:
            request: The checked start request.

        Returns:
            The real request with replacement timing.
        """
        trigger = super().request_for(request)  # Read real method, path, body, and channel.
        listen = replace(trigger.listen, timing=self._timing)  # Keep the channel and path exact.
        return replace(trigger, listen=listen)  # Return an immutable trigger copy.


def test_trigger_posts_only_after_channel_subscribed() -> None:
    """Send the trigger only after the stream subscription succeeds."""
    with FakeMistCloud() as cloud:  # Start a loopback fake Mist cloud.
        device = StreamDevice()  # Build one fake stream device.
        cloud.register("/api-ws/v1/stream", device)  # Register the stream route.
        api = FakeApiSession(cloud)  # Build a fake API session for the trigger.
        api.add_override("/show_arp", data={"session": "session-order"})  # Make the session id deterministic.
        subscribed_before_post = threading.Event()  # The hook records subscription order.
        _set_before_post_return(api, _publish_after_subscription(cloud, device, subscribed_before_post))  # Hook.
        sink = _run_utility(cloud, api, _request("ex.retrieveArpTable"), _fast_table())  # Start the runner.
        state, _reason = sink.wait_finished()  # Wait for the background run.
    assert subscribed_before_post.is_set()  # The trigger hook saw a stream subscription first.
    assert api.calls[0].method == "POST"  # The first REST call is the trigger POST.
    assert state == SessionState.FINISHED  # Output plus quiet completion finishes cleanly.
    assert sink.messages == [("text", "show arp output", None)]  # The command line shape is stable.


def test_early_command_output_before_post_return_is_kept() -> None:
    """Keep output that arrives before the REST trigger returns."""
    with FakeMistCloud() as cloud:  # Start a loopback fake Mist cloud.
        device = StreamDevice()  # Build one fake stream device.
        cloud.register("/api-ws/v1/stream", device)  # Register the stream route.
        api = FakeApiSession(cloud)  # Build a fake API session.
        api.add_override("/show_arp", data={"session": "session-early"})  # Use a known session id.
        _set_before_post_return(api, _publish_lines(device, "session-early", ["early", "done"]))  # Hook.
        sink = _run_utility(cloud, api, _request("ex.retrieveArpTable"), _fast_table())  # Start the runner.
        state, _reason = sink.wait_finished()  # Wait for completion.
    assert state == SessionState.FINISHED  # The utility completes after quiet time.
    assert [message[1] for message in sink.messages] == ["early", "done"]  # Early lines stay in order.


def test_first_output_limit_times_out_without_output() -> None:
    """End as timed out when the device sends no first output."""
    with FakeMistCloud() as cloud:  # Start a loopback fake Mist cloud.
        device = StreamDevice()  # Build one fake stream device.
        cloud.register("/api-ws/v1/stream", device)  # Register the stream route.
        api = FakeApiSession(cloud)  # Build a fake API session.
        api.add_override("/show_arp", data={"session": "session-timeout"})  # Return a valid trigger answer.
        timing = UtilityTiming(0.2, 0.2, 1.0)  # Keep the no-output wait short.
        sink = _run_utility(cloud, api, _request("ex.retrieveArpTable"), ShortTriggerTable(timing))  # Run.
        state, reason = sink.wait_finished()  # Wait for timeout.
    assert state == SessionState.TIMED_OUT  # No output uses the timeout state.
    assert "no output" in reason  # The reason tells the operator what happened.


def test_quiet_limit_finishes_after_output() -> None:
    """Finish after the quiet limit when output already arrived."""
    with FakeMistCloud() as cloud:  # Start a loopback fake Mist cloud.
        device = StreamDevice()  # Build one fake stream device.
        cloud.register("/api-ws/v1/stream", device)  # Register the stream route.
        api = FakeApiSession(cloud)  # Build a fake API session.
        api.add_override("/show_arp", data={"session": "session-quiet"})  # Use a deterministic session id.
        _set_before_post_return(api, _publish_lines(device, "session-quiet", ["one line"]))  # Publish one line.
        sink = _run_utility(cloud, api, _request("ex.retrieveArpTable"), _fast_table())  # Run with short quiet time.
        state, reason = sink.wait_finished()  # Wait for quiet completion.
    assert state == SessionState.FINISHED  # Output before quiet time is successful.
    assert reason == "The utility finished."  # Quiet completion keeps the current success reason.


def test_total_limit_reason_names_the_limit() -> None:
    """End at the total limit with a reason that names that limit."""
    with FakeMistCloud() as cloud:  # Start a loopback fake Mist cloud.
        device = StreamDevice()  # Build one fake stream device.
        cloud.register("/api-ws/v1/stream", device)  # Register the stream route.
        api = FakeApiSession(cloud)  # Build a fake API session.
        api.add_override("/show_arp", data={"session": "session-total"})  # Use a deterministic session id.
        _set_before_post_return(api, _publish_lines(device, "session-total", ["one line"]))  # Publish one line.
        timing = UtilityTiming(1.0, 5.0, 0.3)  # Force the total limit before quiet time.
        sink = _run_utility(cloud, api, _request("ex.retrieveArpTable"), ShortTriggerTable(timing))  # Run.
        state, reason = sink.wait_finished()  # Wait for total completion.
    assert state == SessionState.FINISHED  # Output arrived before the total limit.
    assert reason == "The utility reached its time limit of 0.3 seconds."  # The reason names the limit of this run.


def test_stop_closes_stream_within_three_seconds() -> None:
    """Stop a running command session within three seconds."""
    with FakeMistCloud() as cloud:  # Start a loopback fake Mist cloud.
        device = StreamDevice()  # Build one fake stream device.
        cloud.register("/api-ws/v1/stream", device)  # Register the stream route.
        api = FakeApiSession(cloud)  # Build a fake API session.
        api.add_override("/show_arp", data={"session": "session-stop"})  # Use a deterministic session id.
        runner, sink = _build_runner(cloud, api, _request("ex.retrieveArpTable"), _slow_table())  # Build runner.
        runner.start()  # Start the command runner.
        _wait_for_calls(api, 1)  # Wait until the trigger was sent.
        started = time.monotonic()  # Start the stop timer.
        runner.stop()  # Close the stream from the test thread.
        state, _reason = sink.wait_finished()  # Wait for the run thread to finish.
        elapsed = time.monotonic() - started  # Measure the stop duration.
    assert state == SessionState.STOPPED  # A user stop wins over transport close.
    assert elapsed < 3.0  # The close path must not block the operator.


def test_stop_after_subscribe_prevents_utility_trigger(monkeypatch: pytest.MonkeyPatch) -> None:
    """Do not send the REST trigger when stop arrives after subscribe."""
    with FakeMistCloud() as cloud:  # Start a loopback fake Mist cloud.
        device = StreamDevice()  # Build one fake stream device.
        cloud.register("/api-ws/v1/stream", device)  # Register the stream route.
        api = FakeApiSession(cloud)  # Build a fake API session.
        profile = TransportProfile(
            stream_url=f"{cloud.base_ws_url}/api-ws/v1/stream",
            allow_loopback=True,
            read_timeout_seconds=0.2,
            subscribe_timeout_seconds=1.0,
        )  # Point transport to the fake stream.
        endpoint = MistStreamEndpoint(api, profile)  # Use the same API session for auth and REST.
        sink = FakeSink()  # Record the final state.
        runner = UtilityRunner(api, endpoint, _request("ex.retrieveArpTable"), sink, _slow_table())  # Build runner.
        original_open = UtilityStreamOpener._client  # Keep the real subscribe implementation.

        def stop_after_open(opener: UtilityStreamOpener, trigger: UtilityRequest) -> StreamClient:
            client = original_open(opener, trigger)  # Subscribe before the stop request.
            runner.stop()  # Model Stop while the page still shows connecting.
            return client  # Let the execution guard prevent the trigger.

        monkeypatch.setattr(UtilityStreamOpener, "_client", stop_after_open)  # Install the stop seam.
        runner.start()  # Start the background utility.
        state, reason = sink.wait_finished()  # Wait for stop handling.
    assert state == SessionState.STOPPED  # Stop wins before the trigger.
    assert reason == "The operator stopped the session."  # The page receives the standard stop reason.
    assert api.calls == []  # No REST call can bounce a port after Stop.


def test_subscribe_refusal_does_not_leak_channel_path() -> None:
    """Return a safe subscribe failure reason without the channel path."""
    with FakeMistCloud() as cloud:  # Start a loopback fake Mist cloud.
        device = StreamDevice()  # Build one fake stream device.
        device.refuse(COMMAND_CHANNEL, "denied")  # Refuse the command stream channel.
        cloud.register("/api-ws/v1/stream", device)  # Register the stream route.
        api = FakeApiSession(cloud)  # Build a fake API session.
        sink = _run_utility(cloud, api, _request("ex.retrieveArpTable"), _fast_table())  # Start the runner.
        state, reason = sink.wait_finished()  # Wait for the subscribe failure.
    assert state == SessionState.FAILED  # Subscribe refusal fails the session.
    assert reason == "The stream subscription failed: denied."  # The reason uses only safe detail.
    assert "/sites/" not in reason  # The channel path must not reach the page.


@pytest.mark.parametrize(
    ("kind", "status_code", "error"),
    (
        ("refuse", 403, websocket.WebSocketBadStatusException("Handshake status 403", 403)),
        ("refuse", 503, websocket.WebSocketBadStatusException("Handshake status 503", 503)),
        ("stall", 0, TimeoutError("The handshake stalled.")),
        ("reset", 0, ConnectionError("The peer reset the handshake.")),
    ),
)
def test_open_failures_report_connect_failure_reason(kind: str, status_code: int, error: BaseException) -> None:
    """Show the operator-safe connection failure reason for utility open failures."""
    with FakeMistCloud() as cloud:  # Start a loopback fake Mist cloud.
        cloud.fail_handshake("/api-ws/v1/stream", HandshakeFault(kind, status_code=status_code))  # Fault open.
        api = FakeApiSession(cloud)  # Build a fake API session.
        expected = ConnectFailure.reason(error)  # Use the product mapper for the expected text.
        if expected is None:  # Fail clearly if a row no longer maps to a safe reason.
            raise AssertionError("The representative open error did not map to a safe reason.")  # Fail fast.
        sink = _run_utility(cloud, api, _request("ex.retrieveArpTable"), _fast_table())  # Start the runner.
        state, actual_reason = sink.wait_finished(5.0)  # Wait for the open failure.
    assert state == SessionState.FAILED  # Open failures fail the utility session.
    assert actual_reason == expected  # The page shows the safe transport reason.


@pytest.mark.parametrize(
    ("status_code", "data"),
    (
        (403, {}),
        (503, {}),
        (200, "bad json"),
    ),
)
def test_trigger_failure_bodies_fail_safely(status_code: int, data: object) -> None:
    """Fail safely when the trigger returns an HTTP error or a non-JSON body."""
    with FakeMistCloud() as cloud:  # Start a loopback fake Mist cloud.
        device = StreamDevice()  # Build one fake stream device.
        cloud.register("/api-ws/v1/stream", device)  # Register the stream route.
        api = FakeApiSession(cloud)  # Build a fake API session.
        api.add_override("/show_arp", status_code=status_code, data=data)  # Return the trigger failure shape.
        sink = _run_utility(cloud, api, _request("ex.retrieveArpTable"), _fast_table())  # Start the runner.
        state, reason = sink.wait_finished()  # Wait for failure.
    assert state == SessionState.FAILED  # Trigger failures fail the utility session.
    assert reason == f"The utility failed with status {status_code}."  # The page reason is stable.


def test_empty_trigger_body_fails_safely() -> None:
    """Fail safely when the trigger returns an empty body."""
    with FakeMistCloud() as cloud:  # Start a loopback fake Mist cloud.
        device = StreamDevice()  # Build one fake stream device.
        cloud.register("/api-ws/v1/stream", device)  # Register the stream route.
        api = FakeApiSession(cloud)  # Build a fake API session.
        api.add_override("/show_arp", status_code=200, data="")  # Return the empty trigger body.
        sink = _run_utility(cloud, api, _request("ex.retrieveArpTable"), _fast_table())  # Start the runner.
        state, reason = sink.wait_finished()  # Wait for failure.
    assert state == SessionState.FAILED  # Empty trigger bodies fail the utility session.
    assert reason == "The utility failed with status 200."  # The page reason is stable.


def test_unexpected_output_exception_fails_session_safely() -> None:
    """Convert an unexpected output exception into a safe failed session."""
    with FakeMistCloud() as cloud:  # Start a loopback fake Mist cloud.
        device = StreamDevice()  # Build one fake stream device.
        cloud.register("/api-ws/v1/stream", device)  # Register the stream route.
        api = FakeApiSession(cloud)  # Build a fake API session.
        api.add_override("/show_arp", data={"session": "session-crash"})  # Use a deterministic session id.
        _set_before_post_return(api, _publish_lines(device, "session-crash", ["boom"]))  # Publish one output line.
        runner, sink = _build_runner(
            cloud, api, _request("ex.retrieveArpTable"), _fast_table(), ExplodingSink()
        )  # Build.
        runner.start()  # Start the runner with the exploding sink.
        state, reason = sink.wait_finished()  # Wait for the broad exception handler.
    assert state == SessionState.FAILED  # Unexpected exceptions fail the session.
    assert reason == "The utility failed. Read the portal log for the cause."  # The page reason is safe.


@pytest.mark.parametrize(
    ("key", "trigger_path", "label"),
    [
        ("ex.retrieveArpTable", "/show_arp", "show_arp"),
        ("srx.retrieveRoutes", "/show_route", "show_route"),
    ],
)  # SC-003 names Show ARP and Show Route.
def test_show_command_runs_one_hundred_times_with_full_output(
    key: str, trigger_path: str, label: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """Run one show command one hundred times against a fast fake device."""
    started = time.perf_counter()  # Measure only the loop run time.
    with FakeMistCloud() as cloud:  # Reuse one loopback server to keep the reliability test bounded.
        for index in range(100):  # Repeat the SC-003 reliability path.
            device = StreamDevice()  # Use a fresh fake device without stale closed sockets.
            cloud.register("/api-ws/v1/stream", device)  # Replace the stream route for this run.
            api = FakeApiSession(cloud)  # Build a fake API session.
            session_id = f"session-{index}"  # Give each run an exact filter value.
            lines = _show_output(label, index)  # Full output expected from the device.
            api.add_override(trigger_path, data={"session": session_id})  # Force the filter identifier.
            _set_before_post_return(api, _publish_lines(device, session_id, lines))  # Publish during trigger.
            sink = _run_utility(cloud, api, _request(key), _very_fast_table())  # Run once.
            state, _reason = sink.wait_finished()  # Wait for the utility to finish.
            assert state == SessionState.FINISHED  # Each fast run finishes cleanly.
            assert [message[1] for message in sink.messages] == lines  # Each run preserves full output.
    elapsed = time.perf_counter() - started  # Compute the reliability measurement.
    print(f"{label}_100_run_seconds={elapsed:.3f}")  # Report the runtime for the builder report.
    assert f"{label}_100_run_seconds" in capsys.readouterr().out  # Prove the measurement printed.


def test_capture_filters_capture_id_and_adds_packet_summary() -> None:
    """Emit only matching capture packets and include a packet summary."""
    with FakeMistCloud() as cloud:  # Start a loopback fake Mist cloud.
        device = StreamDevice()  # Build one fake stream device.
        cloud.register("/api-ws/v1/stream", device)  # Register the stream route.
        api = FakeApiSession(cloud)  # Build a fake API session.
        api.add_override("/pcaps/capture", data={"id": "cap-ok"})  # Use a deterministic capture id.
        _set_before_post_return(api, _publish_capture_pair(device))  # Publish noise and the matching packet.
        sink = _run_utility(cloud, api, _request("ex.remotePcap", "packets"), _fast_table())  # Run capture.
        state, _reason = sink.wait_finished()  # Wait for quiet completion.
    assert state == SessionState.FINISHED  # A matching capture packet completes successfully.
    assert len(sink.messages) == 1  # The filter drops the nonmatching capture.
    assert sink.messages[0][0] == "packet"  # Packet captures keep the packet message kind.
    assert sink.messages[0][1] == _packet_record()  # The page sees only the packet dictionary.
    assert sink.messages[0][2] == "12:00 1.1.1.1 -> 2.2.2.2 TCP 64"  # Summary uses packet fields.


def test_capture_stop_sends_delete_only_for_matching_capture() -> None:
    """Stop a running capture with the capture identifier from the trigger answer."""
    with FakeMistCloud() as cloud:  # Start a loopback fake Mist cloud.
        device = StreamDevice()  # Build one fake stream device.
        cloud.register("/api-ws/v1/stream", device)  # Register the stream route.
        api = FakeApiSession(cloud)  # Build a fake API session.
        api.add_override("/pcaps/capture", data={"id": "cap-stop"})  # Use a deterministic capture id.
        api.add_override("/pcaps?limit=1", data=[{"id": "cap-stop"}])  # Let CaptureStopper match the capture.
        runner, sink = _build_runner(cloud, api, _request("ex.remotePcap", "packets"), _slow_table())  # Build.
        runner.start()  # Start the capture runner.
        _wait_for_calls(api, 1)  # Wait for the capture trigger.
        runner.stop()  # Ask the runner to stop the capture.
        state, _reason = sink.wait_finished()  # Wait for stopped state.
    assert state == SessionState.STOPPED  # Stop produces the operator stopped state.
    assert _has_call(api.calls, "DELETE", f"/api/v1/sites/{SITE_ID}/pcaps")  # Matching capture was stopped.


def test_screen_utility_is_refused() -> None:
    """Reject screen utilities in the utility runner."""
    with FakeMistCloud() as cloud:  # Start a loopback fake Mist cloud.
        api = FakeApiSession(cloud)  # Build a fake API session.
        runner, sink = _build_runner(cloud, api, _request("ex.topCommand", "screen"), _fast_table())  # Build.
        runner.start()  # Start a screen request in the wrong runner.
        state, _reason = sink.wait_finished()  # Wait for refusal.
    assert state == SessionState.FAILED  # Screen commands must use ScreenRunner.
    assert sink.live_calls == 0  # Refused screen utilities never become live.


def _request(key: str, output: str = "lines") -> StartRequest:
    """Build a checked utility request for tests."""
    definition = UtilityDefinition(key, "ex", "unused", key, key, (), Safety.READ, output, ())  # Catalog entry.
    targets = {"site_id": (SITE_ID,), "device_id": (DEVICE_ID,), "org_id": (ORG_ID,)}  # Stable targets.
    params = {"duration": 60, "port_id": "ge-0/0/1", "protocol": "tcp"}  # Common trigger parameters.
    return StartRequest("utility", definition, targets, params, key)  # Return checked request shape.


def _build_runner(
    cloud: FakeMistCloud,
    api: FakeApiSession,
    request: StartRequest,
    table: UtilityTriggerTable,
    sink: FakeSink | None = None,
) -> tuple[UtilityRunner, FakeSink]:
    """Build a runner and sink for one fake cloud."""
    profile = TransportProfile(
        stream_url=f"{cloud.base_ws_url}/api-ws/v1/stream",
        allow_loopback=True,
        read_timeout_seconds=0.2,
        subscribe_timeout_seconds=1.0,
    )  # Point transport to the fake stream.
    endpoint = MistStreamEndpoint(api, profile)  # Use the same API session for auth and REST.
    selected_sink = sink or FakeSink()  # Let tests inject a sink that raises.
    runner = UtilityRunner(api, endpoint, request, selected_sink, table)  # Build the runner under test.
    return runner, selected_sink  # The caller starts the runner.


def _run_utility(
    cloud: FakeMistCloud, api: FakeApiSession, request: StartRequest, table: UtilityTriggerTable
) -> FakeSink:
    """Start one utility runner."""
    runner, sink = _build_runner(cloud, api, request, table)  # Build the runner and sink.
    runner.start()  # Start the utility run.
    return sink  # The caller waits for finish.


def _fast_table() -> ShortTriggerTable:
    """Return short but stable utility timing."""
    return ShortTriggerTable(UtilityTiming(0.5, 0.05, 1.0))  # Keep unit tests fast.


def _very_fast_table() -> ShortTriggerTable:
    """Return very short utility timing for reliability loops."""
    return ShortTriggerTable(UtilityTiming(0.5, 0.01, 1.0))  # Keep the 100-run test bounded.


def _slow_table() -> ShortTriggerTable:
    """Return long timing for stop tests."""
    return ShortTriggerTable(UtilityTiming(10.0, 10.0, 10.0))  # Prevent limits from winning over stop().


def _set_before_post_return(api: FakeApiSession, hook) -> None:
    """Set and verify the pre-return hook on the fake API session."""
    api.before_post_return = hook  # Configure the fake API session hook.
    assert api.before_post_return is hook  # Read the attribute so tests prove the hook is installed.


def _publish_after_subscription(cloud: FakeMistCloud, device: StreamDevice, subscribed: threading.Event):
    """Return a hook that proves subscription order and publishes output."""

    def publish(_uri: str, _body: object | None) -> None:
        if _is_subscribed(cloud, COMMAND_CHANNEL):  # The stream must subscribe before the REST trigger.
            subscribed.set()  # Record the subscribe state.
        device.publish_command_lines(COMMAND_CHANNEL, "session-order", ["show arp output"])  # Publish output.

    return publish  # FakeApiSession calls this hook before returning.


def _publish_lines(device: StreamDevice, session_id: str, lines: list[str]):
    """Return a hook that publishes command output."""

    def publish(_uri: str, _body: object | None) -> None:
        device.publish_command_lines(COMMAND_CHANNEL, session_id, lines)  # Publish each command line.

    return publish  # FakeApiSession calls this hook before returning.


def _show_output(label: str, index: int) -> list[str]:
    """Return the device output for one show command run.

    Args:
        label: The show command label.
        index: The run number.

    Returns:
        The raw output lines. The SRX sends the route table as one JSON text line.
    """
    if label != "show_route":  # Show ARP sends plain text lines.
        return [f"run {index} header", f"run {index} detail"]  # Two lines prove the order.
    columns = [{"id": name, "display_name": name, "type": "string"} for name in ("Table", "Destination")]  # Live shape.
    rows = [{"Table": "inet.0", "Destination": f"10.{index}.0.0/16"}]  # One route row for each run.
    table = {"columns": columns, "rows": rows, "finished": True, "status": "SUCCESS", "message": ""}  # Live keys.
    return [json.dumps(table)]  # The device sends the table as one raw text line.


def _publish_capture_pair(device: StreamDevice):
    """Return a hook that publishes one noise packet and one matching packet."""

    def publish(_uri: str, _body: object | None) -> None:
        device.publish_capture(CAPTURE_CHANNEL, "cap-noise", {"src_ip": "9.9.9.9"})  # Publish noise first.
        device.publish_capture(CAPTURE_CHANNEL, "cap-ok", _packet_record())  # Publish the matching packet.

    return publish  # FakeApiSession calls this hook before returning.


def _packet_record() -> dict[str, object]:
    """Return one packet record with every summary field."""
    return {
        "timestamp": "12:00",
        "src_ip": "1.1.1.1",
        "dst_ip": "2.2.2.2",
        "proto": "TCP",
        "length": 64,
    }  # PacketSummary should use each value.


def _is_subscribed(cloud: FakeMistCloud, channel: str) -> bool:
    """Return whether any connection has subscribed to a channel."""
    needle = f'"subscribe": "{channel}"'.encode()  # The fake cloud records raw subscribe frames.
    return any(needle in frame.payload for frame in cloud.frames)  # Tests need only a boolean proof.


def _wait_for_calls(api: FakeApiSession, count: int) -> None:
    """Wait until the fake API session has at least a count of calls."""
    deadline = time.monotonic() + 2.0  # Bound the poll loop.
    while len(api.calls) < count:  # Wait until the background thread sends REST.
        if time.monotonic() >= deadline:  # Missing REST call is a test failure.
            raise AssertionError("The utility runner did not send the REST trigger.")  # Explain the missing event.
        time.sleep(0.01)  # Keep the poll cheap.


def _has_call(calls: list[FakeApiCall], method: str, uri: str) -> bool:
    """Return whether the fake API session recorded a matching call."""
    return any(call.method == method and call.uri == uri for call in calls)  # Tests assert stop request shape.
