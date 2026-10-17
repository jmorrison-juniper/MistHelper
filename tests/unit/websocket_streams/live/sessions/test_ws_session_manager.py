"""Tests for the WebSockets stream session manager."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # The read test decodes the joined JSON text.
import logging  # caplog checks the audit line.
import threading  # Permit tests run competing acquisition requests.
import time  # Real runner failure tests use bounded waits.
from dataclasses import replace  # Parent requests retain the checked batch plan.
from unittest.mock import Mock  # Artifact callbacks simulate safe storage outcomes.

import pytest  # The tests check contract errors.
import websocket  # Failure tests build the same exception type as websocket-client.

from src.mist.realtime.websocket_streams.catalog.model import (
    ChannelDefinition,
    FieldKind,
    FieldSpec,
    Safety,
    UtilityDefinition,
)  # Tests build local definitions.
from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # The manager raises these errors.
from src.mist.realtime.websocket_streams.intake.start_request.models import (
    BatchExecutionPlan,
    BatchTargetRequest,
    StartRequest,
)  # Tests build checked requests by hand.
from src.mist.realtime.websocket_streams.live.runners.channel.runner import (
    ChannelStreamRunner,
)  # Factory tests assert runner classes.
from src.mist.realtime.websocket_streams.live.runners.shell.runners import (
    ScreenRunner,
    ShellRunner,
)  # Factory runner classes.
from src.mist.realtime.websocket_streams.live.runners.text.redaction import (
    ShellAddressFilter,
)  # Count redaction filters.
from src.mist.realtime.websocket_streams.live.runners.utility.runner.utility_runner import (
    UtilityRunner,
)  # Utility runner class.
from src.mist.realtime.websocket_streams.live.sessions.manager.factory import (
    BatchRunner,
    RunnerFactory,
    SharedTransport,
)  # Test concrete runner selection.
from src.mist.realtime.websocket_streams.live.sessions.manager.lifecycle import (
    StreamSessionManager,
)  # Test manager behavior.
from src.mist.realtime.websocket_streams.live.sessions.record.state import (
    SessionSink,
    SessionState,
)  # Tests finish sessions directly.
from src.mist.realtime.websocket_streams.live.sessions.settings import StreamSettings  # The manager needs limits.
from src.mist.realtime.websocket_streams.live.terminal.byte_history import (
    ByteHistory,
    HistoryRead,
)  # Tests control finite shell output pages.
from src.mist.realtime.websocket_streams.live.terminal.input_queue import (
    TerminalInput,
)  # Tests assert the shell queue type.
from src.mist.realtime.websocket_streams.live.terminal.state.size import (
    TerminalSize,
)  # Tests assert terminal size values.
from src.mist.realtime.websocket_streams.live.terminal.state.terminal_state import (
    TerminalState,
)  # Tests assert state values.
from src.mist.realtime.websocket_streams.live.transport.endpoint import (
    ConnectFailure,
    TransportProfile,
)  # Factory tests avoid real Mist sockets.
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.api import (
    FakeApiSession,
)  # Factory tests need SDK-shaped session data.
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.server import (
    FakeMistCloud,  # Real runner tests use a loopback cloud.
    HandshakeFault,  # Fake cloud handshake failure control.
)


class FakeClock:
    """A clock that tests can move."""

    def __init__(self) -> None:
        """Build a clock at zero seconds."""
        self.value = 0.0  # Tests mutate this value directly.

    def __call__(self) -> float:
        """Return the fake time."""
        return self.value  # The manager uses this as monotonic time.


class FakeRunner:
    """A runner that records calls."""

    def __init__(self) -> None:
        """Build a runner with no calls."""
        self.started = 0  # Count start calls.
        self.stopped = 0  # Count stop calls.
        self.inputs: list[str] = []  # Keep sent input text.
        self.sizes: list[tuple[int, int]] = []  # TerminalRunner needs resize for runtime protocol checks.

    def start(self) -> None:
        """Record a start call."""
        self.started += 1  # The manager calls this after storing a session.

    def stop(self) -> None:
        """Record a stop call."""
        self.stopped += 1  # The manager calls this at most once per stop.

    def send_input(self, text: str) -> None:
        """Record shell input.

        Args:
            text: The checked shell input.
        """
        self.inputs.append(text)  # Tests verify shaped input text.

    def resize(self, cols: int, rows: int) -> None:
        """Record terminal size changes.

        Args:
            cols: The accepted terminal column count.
            rows: The accepted terminal row count.
        """
        self.sizes.append((cols, rows))  # The protocol method lets manager bind shell input.


class FakeFactory:
    """A runner factory that returns fake runners."""

    def __init__(self) -> None:
        """Build an empty factory."""
        self.runners: list[FakeRunner] = []  # Keep each runner for assertions.

    def build(self, request: StartRequest, sink: object) -> FakeRunner:
        """Build one fake runner.

        Args:
            request: The checked start request.
            sink: The session sink.

        Returns:
            A fake runner.
        """
        runner = FakeRunner()  # Build one runner for this session.
        self.runners.append(runner)  # Keep it for assertions.
        return runner  # The manager calls start on this runner.


class FakeSink:
    """A fake sink for runner factory tests."""

    terminal = None  # Factory tests build runners without a real terminal sink.
    state = SessionState.LIVE  # Batch child sinks read the parent lifecycle state.

    def __init__(self) -> None:
        """Retain messages for batch redaction tests."""
        self.messages: list[dict[str, object]] = []  # Keep the safe parent output for assertions.

    def mark_live(self, note: str = "") -> None:
        """Ignore live transitions."""
        return None  # Factory tests do not start runners.

    def add_message(self, kind: str, content: object, *, source: str | None = None, summary: str | None = None) -> None:
        """Retain one public parent message."""
        self.messages.append({"kind": kind, "content": content})  # Retain only the public parent payload.

    def finish(self, state: SessionState, reason: str) -> None:
        """Ignore final states."""
        return None  # Factory tests do not start runners.

    def mark_input_ready(self) -> None:
        """Ignore shell readiness."""
        return None  # Factory tests do not start runners.

    def add_bytes(self, data: bytes) -> None:
        """Ignore terminal output bytes.

        Args:
            data: Terminal output bytes from a runner.
        """
        return None  # Factory tests do not start runners.


class TestStreamSessionManager:
    """Verify manager behavior."""

    def test_batch_target_states_preserve_first_terminal_outcome(self) -> None:
        """Keep terminal target state and aggregate counts stable."""
        targets = (
            BatchTargetRequest("one", {"site_id": "one"}, self._channel_request("one")),
            BatchTargetRequest("two", {"site_id": "two"}, self._channel_request("two")),
        )  # Build two frozen natural-key targets.
        plan = BatchExecutionPlan(targets, 2)  # Start both with a bounded target concurrency.
        transitions = plan.progress.transitions
        assert transitions.transition("one", "running") is True  # Dispatch the first target.
        assert transitions.transition("one", "completed", completion="collected") is True  # Record its result.
        assert transitions.transition("one", "failed", "late_failure") is False  # Reject a later duplicate outcome.
        assert transitions.transition("two", "failed", "target_failed") is True  # Preserve one target failure.
        summary = plan.progress.summary.summary()  # Read the aggregate target state.
        assert summary["counts"] == {"queued": 0, "running": 0, "completed": 1, "stopped": 0, "failed": 1}
        assert summary["status"] == "partial"  # Mixed target outcomes remain visible.
        assert plan.progress.summary.target_page(0, 2)["targets"][0]["completion"] == "collected"

    def test_batch_stop_during_runner_build_prevents_target_start(self) -> None:
        """A stop while a runner is built prevents late target registration."""
        entered, release = threading.Event(), threading.Event()  # Hold construction at the race boundary.
        runner = FakeRunner()  # Record whether dispatch starts after the stop.
        target = BatchTargetRequest("target", {"site_id": "site"}, self._channel_request("target"))
        plan = BatchExecutionPlan((target,), 1)  # One running target makes the cancellation outcome clear.

        def build(_request: StartRequest, _sink: SessionSink) -> FakeRunner:
            """Pause runner construction until the parent has stopped."""
            entered.set()  # Signal that the scheduler reached the build boundary.
            release.wait(1)  # Let the test stop before registration.
            return runner  # Reuse the observable runner after the barrier.

        parent = replace(self._channel_request("parent"), batch_plan=plan)  # Bind the frozen batch plan.
        batch = BatchRunner(parent, FakeSink(), build, StreamSettings.from_environment(), SharedTransport(1))
        batch.start()  # Run the scheduler outside the test thread.
        assert entered.wait(1) is True  # Confirm the target reached construction.
        batch.stop()  # Cancel the parent while no child runner is registered.
        release.set()  # Let construction complete after cancellation.
        assert batch._thread is not None  # The scheduler owns its worker thread.
        batch._thread.join(timeout=1)  # Wait for the scheduler to record its final outcome.
        assert batch._thread.is_alive() is False  # Do not leak the test worker.
        assert runner.started == 0  # A late target cannot start after cancellation.
        assert plan.progress.summary.target_page(0, 1)["targets"][0]["state"] == "stopped"

    def test_batch_terminal_chunks_redact_secrets_before_parent_output(self) -> None:
        """Keep split terminal credentials out of the parent session messages."""
        target = BatchTargetRequest("target", {"site_id": "site"}, self._channel_request("target"))
        plan = BatchExecutionPlan((target,), 1)  # Store one target outcome with bounded concurrency.
        parent = FakeSink()  # Observe the public parent messages.
        sink = BatchRunner.TargetSink(parent, plan, target, None)  # Build one private target output sink.
        sink.add_message("terminal", "Authorization: Bearer ")  # Split the header before its secret value.
        sink.add_message("terminal", "split-secret")  # Complete the secret value in another transport chunk.
        assert parent.messages == []  # Do not emit an incomplete line.
        sink.finish(SessionState.FINISHED, "complete")  # Flush only after the target stream ends.
        result = json.dumps(parent.messages)  # Inspect the exact data that entered the parent buffer.
        assert "split-secret" not in result  # Keep raw credentials out of saved and displayed results.
        assert "[REDACTED]" in result  # Preserve evidence that the content was filtered.

    def test_batch_shell_quiet_interval_restarts_after_new_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Require two quiet seconds after the latest matching prompt."""
        clock = FakeClock()  # Control the elapsed time without sleeping.
        pages = [
            (0.1, b"router#"),
            (0.1, b"\r\nroute\r\nrouter#"),
            (1.5, b""),
            (0.1, b"\r\nmore\r\nrouter#"),
            (1.0, b""),
            (1.1, b""),
        ]  # Keep the prompt, new output, and quiet periods deterministic.
        history = ByteHistory()  # Supply the terminal history interface.

        def read_page(after: int, wait_seconds: float = 0.0) -> HistoryRead:
            """Return one scripted output page and advance the monotonic clock."""
            elapsed, data = pages.pop(0)  # Consume one deterministic output event.
            clock.value += elapsed  # Advance time by the scripted wait duration.
            return HistoryRead(data, after, after + len(data), 0, False)  # Preserve the absolute byte cursor.

        monkeypatch.setattr(history, "read", read_page)  # Replace blocking history reads with scripted pages.
        clock_target = "src.mist.realtime.websocket_streams.live.sessions.manager.factory.time.monotonic"  # Patch time.
        monkeypatch.setattr(clock_target, clock)  # Advance each shell wait through scripted time.
        target = BatchTargetRequest("target", {"site_id": "site"}, self._channel_request("target"))  # Freeze identity.
        plan = BatchExecutionPlan((target,), 1)  # Build one private shell target.
        parent = replace(self._channel_request("parent"), batch_plan=plan)  # Bind the checked plan.
        batch = BatchRunner(
            parent,  # Bind the confirmed parent request.
            FakeSink(),  # Capture target output.
            FakeFactory().build,  # Reuse the deterministic runner builder.
            StreamSettings.from_environment(),  # Use bounded runtime settings.
            SharedTransport(1),  # Reserve one shared transport slot.
        )  # Build the batch collector.
        terminal = TerminalState(history, TerminalInput(), 30.0, "2030-01-01T00:00:00Z")  # Build private state.
        prompt_cursor, prompt = batch._shell._initial_prompt(terminal)  # Capture the first verified prompt.
        assert prompt == "router#"  # Normalize the prompt before command dispatch.
        assert BatchRunner.Shell._prompt(b"router#\r\nmore output") is None  # Reject an earlier prompt match.
        cursor, complete = batch._shell._command_prompt(
            terminal, prompt_cursor, prompt, 0  # Continue from the verified initial cursor.
        )
        assert complete is True  # The latest prompt completes after a full quiet interval.
        assert cursor > 0 and not pages  # The collector reads through the final quiet interval.

    def test_batch_shell_dispatch_logs_no_command_text(self, caplog: pytest.LogCaptureFixture) -> None:
        """Log shell dispatch state without command text."""
        target = BatchTargetRequest("target", {"site_id": "site"}, self._channel_request("target"))  # Freeze identity.
        plan = BatchExecutionPlan((target,), 1)  # Build one private shell target.
        parent = replace(self._channel_request("parent"), batch_plan=plan)  # Bind the checked plan.
        batch = BatchRunner(
            parent,  # Bind the confirmed parent request.
            FakeSink(),  # Capture target output.
            FakeFactory().build,  # Reuse the deterministic runner builder.
            StreamSettings.from_environment(),  # Use bounded runtime settings.
            SharedTransport(1),  # Reserve one shared transport slot.
        )  # Build the batch collector.
        runner = FakeRunner()  # Observe the command sent to the child runner.
        caplog.set_level(logging.DEBUG)  # Capture the structured dispatch records.
        batch._targets._send_shell_command(runner, "show version", 0)  # Dispatch one approved command.
        assert runner.inputs == ["show version\n"]  # Send the exact approved command with one line ending.
        assert "batch_shell_command_dispatch_started" in caplog.text  # Record the pre-action event.
        assert "batch_shell_command_dispatch_completed" in caplog.text  # Record the post-action event.
        assert "show version" not in caplog.text  # Keep command text out of logs.

    def test_batch_artifact_failure_remains_failed_after_manifest_write(self) -> None:
        """Keep a successful manifest from hiding an earlier result write failure."""
        target = BatchTargetRequest("target", {"site_id": "site"}, self._channel_request("target"))
        writer = Mock(side_effect=StreamRequestError("output_failed", "The output could not be saved."))
        finisher = Mock()
        plan = BatchExecutionPlan(
            (target,),
            1,
            artifact_id="artifact",
            artifact_writer=writer,
            artifact_finisher=finisher,
        )
        saved = plan.progress.artifacts.write_result("target", target.identity, "output", {}, None)
        finished = plan.progress.artifacts.finish()
        assert saved is False  # Reject the result that the artifact writer did not save.
        assert finished is False  # Preserve the earlier write failure after manifest completion.
        assert finisher.call_count == 1  # Still write terminal target metadata for recovery.
        assert plan.progress.summary.summary()["artifact_status"] == "failed"  # Keep the public status truthful.

    def test_single_site_waiter_has_priority_over_batch_target(self) -> None:
        """Reserve a released transport slot for an admitted Single Site waiter."""
        pool = SharedTransport(1)  # Use the smallest pool that exposes priority ordering.
        assert pool.acquire(threading.Event(), batch=True) is True  # Hold the only slot for existing work.
        batch_done = threading.Event()  # Observe the queued batch target.
        single_done = threading.Event()  # Observe the admitted Single Site waiter.
        results: list[tuple[str, bool]] = []  # Retain each acquisition result.

        def acquire_batch() -> None:
            """Wait for one batch slot."""
            results.append(("batch", pool.acquire(threading.Event(), batch=True)))  # Queue batch work.
            batch_done.set()  # Signal acquisition completion.

        def acquire_single() -> None:
            """Wait for one Single Site slot."""
            results.append(("single", pool.acquire(threading.Event(), batch=False)))  # Queue admitted single work.
            single_done.set()  # Signal acquisition completion.

        batch_thread = threading.Thread(target=acquire_batch)  # Start the lower-priority waiter.
        batch_thread.start()  # Register batch work before the Single Site request.
        time.sleep(0.05)  # Allow the batch worker to enter its bounded wait.
        single_thread = threading.Thread(target=acquire_single)  # Start the reserved-priority waiter.
        single_thread.start()  # Register admitted Single Site work.
        time.sleep(0.05)  # Allow both waiters to observe the occupied pool.
        pool.release()  # Make one transport slot available.
        assert single_done.wait(1) is True  # The Single Site request receives the released slot first.
        assert batch_done.is_set() is False  # Batch work waits while a Single Site session owns the slot.
        pool.release()  # Let the next eligible batch target proceed.
        assert batch_done.wait(1) is True  # Batch work starts after Single Site work releases capacity.
        pool.release()  # Return the last test permit.
        batch_thread.join(timeout=1)  # Do not leave background test work running.
        single_thread.join(timeout=1)  # Do not leave background test work running.
        assert results == [("single", True), ("batch", True)]  # Verify the exact scheduling order.

    def test_start_limit_lists_live_titles(self) -> None:
        """Refuse a session when the live limit is reached."""
        manager, _factory, _clock = self._manager(max_sessions=1)  # Allow one live session.
        manager.start(self._channel_request("first"))  # Fill the limit.
        with pytest.raises(StreamRequestError) as error:  # The next start must fail.
            manager.start(self._channel_request("second"))  # Try one too many.
        assert error.value.code == "limit_reached"  # The contract code is stable.
        assert error.value.extra["live"] == ["first"]  # The live title helps the page.

    def test_read_clamps_limit_and_gap(self) -> None:
        """Clamp read limits and report a gap."""
        manager, _factory, _clock = self._manager(max_sessions=1, buffer_messages=2)  # Keep only two messages.
        payload = manager.start(self._channel_request("first"))  # Start one session.
        session = manager.session(str(payload["session_id"]))  # Read the session for direct sink calls.
        session.mark_live()  # Allow messages.
        for index in range(3):  # Add three messages to force one drop.
            session.add_message("text", str(index))  # Store one message.
        read = manager.read(str(payload["session_id"]), 0, 999)  # Ask for more than the max.
        _filename, lines = manager.download(str(payload["session_id"]))  # Build a download of the kept messages.
        assert read.gap is True  # The page missed a dropped message.
        assert read.first_seq == 2 and read.next_after == 3  # The oldest kept sequence is two, and the newest is three.
        decoded = json.loads(read.to_json_text())  # Decode the answer that the route sends.
        assert [message["content"] for message in decoded["messages"]] == ["1", "2"]  # The kept messages.
        assert [json.loads(line)["seq"] for line in lines] == [2, 3]  # Each download line holds one kept message.

    def test_stop_repeat_delete_and_download(self) -> None:
        """Stop once, reject live delete, and stream download lines."""
        manager, factory, _clock = self._manager(max_sessions=1)  # Build one manager.
        payload = manager.start(self._channel_request("first"))  # Start one session.
        session_id = str(payload["session_id"])  # Store the public identifier.
        with pytest.raises(StreamRequestError):  # Live sessions cannot be deleted.
            manager.delete(session_id)  # Try to delete a live session.
        first = manager.stop(session_id)  # Request a stop.
        second = manager.stop(session_id)  # Repeat the stop.
        assert first["state"] == "stopping"  # A stop request moves to stopping.
        assert second["state"] == "stopping"  # A repeat stop returns the same state.
        assert factory.runners[0].stopped == 2  # Each live Stop request wakes the runner.
        manager.session(session_id).finish(SessionState.STOPPED, "done")  # End the session.
        filename, lines = manager.download(session_id)  # Build a download.
        assert filename.startswith("site.stats.devices-")  # The file name includes the key.
        assert list(lines) == []  # No messages were added.
        manager.delete(session_id)  # Ended sessions can be deleted.

    def test_shell_audit_and_terminal_input_queue(self, caplog: pytest.LogCaptureFixture) -> None:
        """Audit a shell start and bind queued terminal input to the runner."""
        caplog.set_level(logging.WARNING)  # Capture the audit warning.
        manager, factory, _clock = self._manager(max_sessions=1)  # Build one manager.
        payload = manager.start(self._shell_request())  # Start a shell session.
        session = manager.session(str(payload["session_id"]))  # Read the public session handle.
        terminal = session.terminal  # Store terminal state for type narrowing.
        assert isinstance(terminal, TerminalState)  # Shell sessions get a terminal state.
        terminal_input = terminal.input  # Store the input queue for type narrowing.
        assert isinstance(terminal_input, TerminalInput)  # Shell sessions get a writable input queue.
        first = terminal_input.submit("show ")  # Queue early input before first output.
        second = terminal_input.submit("version\r")  # Queue another part to verify order.
        session.mark_live()  # Mark the shell as live.
        session.mark_input_ready()  # Open input after first output.
        third = terminal_input.submit("exit\r")  # Later input sends at once.
        assert (first, second, third) == (True, True, False)  # Only input before readiness is queued.
        assert factory.runners[0].inputs == ["show ", "version\r", "exit\r"]  # The runner receives exact order.
        assert "ex.shell" in caplog.text  # The audit line names the key.
        assert '"status":"shell"' in caplog.text  # The structured audit names the bounded safety state.
        assert "device-a" not in caplog.text  # The safe field boundary removes device identifiers.
        assert "site-a" not in caplog.text  # The safe field boundary removes site identifiers.
        assert "show " not in caplog.text  # The audit line never logs shell text.

    def test_session_returns_handle_and_unknown_session_raises(self) -> None:
        """Return known sessions through the public lookup."""
        manager, _factory, _clock = self._manager(max_sessions=1)  # Build one manager.
        payload = manager.start(self._channel_request("first"))  # Start one session.
        session = manager.session(str(payload["session_id"]))  # Read the public session handle.
        assert session.session_id == payload["session_id"]  # The lookup returns the same record.
        with pytest.raises(StreamRequestError) as error:  # Unknown sessions use the contract error.
            manager.session("missing")  # Look up an absent session.
        assert error.value.code == "not_found"  # The route depends on this code.

    def test_terminal_shape_and_expiry_for_each_session_kind(self) -> None:
        """Build the expected terminal state for shell, screen, channel, and utility sessions."""
        manager, _factory, clock = self._manager(max_sessions=4)  # Build one manager with room for four sessions.
        shell = manager.session(str(manager.start(self._shell_request())["session_id"]))  # Start shell session.
        screen = manager.session(str(manager.start(self._screen_request())["session_id"]))  # Start screen session.
        channel = manager.session(str(manager.start(self._channel_request("channel"))["session_id"]))  # Channel.
        utility = manager.session(str(manager.start(self._utility_request())["session_id"]))  # Start utility.
        assert shell.terminal is not None and shell.terminal.read_only is False  # Shell accepts input.
        assert shell.terminal.input.submit("show version\r") is True  # Shell input queues before first output.
        assert screen.terminal is not None and screen.terminal.read_only is True  # Screen is read-only.
        assert shell.terminal.size() == TerminalSize(80, 24)  # Shell keeps the normal terminal default size.
        assert screen.terminal.size() == TerminalSize(80, 40)  # Screen uses the fixed Mist screen size.
        assert channel.terminal is None  # Channel sessions use the message list.
        assert utility.terminal is None  # Non-screen utility sessions use the message list.
        assert shell.terminal.expires_mono == clock.value + 1800.0  # The monotonic expiry uses settings.
        assert shell.terminal.expires_at.endswith("Z")  # The public expiry is UTC text.

    @pytest.mark.parametrize(
        ("fault", "error"),
        [
            (
                HandshakeFault("refuse", status_code=403),
                websocket.WebSocketBadStatusException("Handshake status 403", 403),
            ),
            (
                HandshakeFault("refuse", status_code=503),
                websocket.WebSocketBadStatusException("Handshake status 503", 503),
            ),
            (HandshakeFault("stall"), TimeoutError("The handshake stalled.")),
            (HandshakeFault("reset"), ConnectionError("The peer reset the handshake.")),
        ],
    )
    def test_real_factory_terminal_open_failures_update_session(
        self,
        fault: HandshakeFault,
        error: BaseException,
    ) -> None:
        """Real shell open failures become failed sessions with plain reasons."""
        expected = ConnectFailure.reason(error)  # Compute expected text through the production mapper.
        assert isinstance(expected, str)  # Each table row must map to public operator text.
        with FakeMistCloud() as cloud:  # The fake cloud drives the real WebSocket open path.
            cloud.fail_handshake("/shell/fail", fault)  # Force this shell path to fail its handshake.
            api = FakeApiSession(cloud)  # Build a fake Mist API session.
            api.add_override("/shell", status_code=200, data={"url": f"{cloud.base_ws_url}/shell/fail"})  # Route.
            manager = self._real_manager(api, cloud)  # Use the real RunnerFactory and manager path.
            payload = manager.start(self._shell_request())  # Start returns before the runner fails.
            session = self._wait_for_state(
                manager, str(payload["session_id"]), {SessionState.FAILED}, timeout=5.0
            )  # Wait for the mapped open failure.
            requests = cloud.wait_for_requests(1, 5.0)  # Prove that the WebSocket path was attempted.
        assert requests[0].path == "/shell/fail"  # The fake cloud recorded the failed open.
        assert session.reason == expected  # The selected session receives the mapped reason.
        assert "fake-token" not in session.reason  # The reason must not expose secrets.

    def test_reaper_stops_idle_and_prunes_old_ended(self) -> None:
        """Stop idle sessions, keep 5 ended sessions at most, and remove them after 10 minutes."""
        manager, _factory, clock = self._manager(
            max_sessions=10, idle_seconds=30
        )  # Build a manager with short idle time.
        payload = manager.start(self._channel_request("idle"))  # Start one session.
        clock.value = 31.0  # Move past the idle limit.
        manager.reap_once()  # Run one reaper pass.
        assert manager.session(str(payload["session_id"])).state.value == "stopping"  # The idle session stopped.
        clock.value = 47.0  # Move past the stuck stopping limit.
        manager.reap_once()  # Run another reaper pass.
        assert manager.session(str(payload["session_id"])).state.value == "stopped"  # Stuck stopping became stopped.
        for index in range(6):  # Add six ended sessions to test retention.
            ended_payload = manager.start(self._channel_request(f"ended-{index}"))  # Start one extra session.
            ended = manager.session(str(ended_payload["session_id"]))  # Read it for a direct finish.
            ended.finish(SessionState.FINISHED, "done")  # Mark the session ended.
        manager.reap_once()  # Seven new ended sessions exist, so the count limit applies.
        assert len(manager.list_payload()["sessions"]) == 5  # The manager keeps five ended sessions at most.
        clock.value = 47.0 + 600.0  # Move to the exact edge of the age limit.
        manager.reap_once()  # Run pruning at the edge.
        assert len(manager.list_payload()["sessions"]) == 5  # A session that is exactly 10 minutes old stays.
        clock.value = 700.0  # Move past the ended retention age.
        manager.reap_once()  # Run pruning.
        assert manager.list_payload()["sessions"] == []  # Each ended session older than 10 minutes left.

    def test_prune_keeps_the_newest_ended_sessions(self) -> None:
        """Remove the oldest ended sessions first when more than five ended sessions exist."""
        manager, _factory, clock = self._manager(max_sessions=10)  # Allow enough live sessions for the setup.
        for index in range(7):  # End seven sessions at different times.
            clock.value = 100.0 + index  # Each session ends one second after the previous session.
            payload = manager.start(self._channel_request(f"ended-{index}"))  # Start one session.
            manager.session(str(payload["session_id"])).finish(SessionState.FINISHED, "done")  # End it at once.
        clock.value = 200.0  # Start the live session last, so the list order is clear.
        live = manager.start(self._channel_request("live"))  # A live session never counts as ended.
        manager.reap_once()  # Apply the count limit.
        titles = [session["title"] for session in manager.list_payload()["sessions"]]  # Newest first.
        assert titles == ["live", "ended-6", "ended-5", "ended-4", "ended-3", "ended-2"]  # The two oldest left.
        assert manager.session(str(live["session_id"])).live is True  # The live session stays live.

    def test_not_found_bad_input_stop_all_and_shutdown(self) -> None:
        """Cover manager error paths and shutdown behavior."""
        manager, _factory, _clock = self._manager(max_sessions=2)  # Build one manager.
        with pytest.raises(StreamRequestError):  # Unknown sessions raise not_found.
            manager.read("missing", 0, 1)  # Try to read an unknown session.
        manager.start(self._shell_request())  # Start one shell session.
        assert manager.live_count() == 1  # One live session is counted.
        assert manager.stop_all("stop all") == 1  # The live session receives one stop.
        manager.shutdown()  # Shutdown is safe after stop_all.
        manager.shutdown()  # A second shutdown does nothing.

    def test_runner_factory_builds_each_runner_kind(self) -> None:
        """Build each concrete runner kind and install shell filters once."""
        factory = self._runner_factory_for_class_tests()  # Build a factory with a fake API session.
        mist_logger = logging.getLogger("mistapi")  # The factory installs the redaction filter here.
        original_filters = list(mist_logger.filters)  # Restore shared logger state after the test.
        original_flag = RunnerFactory._filter_installed  # Restore class state after the test.
        mist_logger.filters = [
            item for item in mist_logger.filters if not isinstance(item, ShellAddressFilter)
        ]  # Reset.
        RunnerFactory._filter_installed = False  # Force the test to measure one installation.
        try:  # Always restore logger state for later tests.
            channel_runner = factory.build(self._channel_request("channel"), FakeSink())  # Build channel runner.
            utility_runner = factory.build(self._utility_request(), FakeSink())  # Build command runner.
            shell_runner = factory.build(self._shell_request(), FakeSink())  # Build shell runner.
            screen_runner = factory.build(self._screen_request(), FakeSink())  # Build screen runner.
            filters = [item for item in mist_logger.filters if isinstance(item, ShellAddressFilter)]  # Count filters.
        finally:  # Put back the global logger state even when assertions fail.
            mist_logger.filters = original_filters  # Restore the previous logger filter list.
            RunnerFactory._filter_installed = original_flag  # Restore the previous class flag.
        assert isinstance(getattr(channel_runner, "_runner", channel_runner), ChannelStreamRunner)
        assert isinstance(getattr(utility_runner, "_runner", utility_runner), UtilityRunner)
        assert isinstance(getattr(shell_runner, "_runner", shell_runner), ShellRunner)
        assert isinstance(getattr(screen_runner, "_runner", screen_runner), ScreenRunner)
        assert len(filters) == 1  # Shell and screen share one redaction filter.

    def _runner_factory_for_class_tests(self) -> RunnerFactory:
        """Build a real runner factory for class-selection tests.

        Returns:
            A runner factory with loopback transport settings.
        """
        profile = TransportProfile(
            stream_url="ws://127.0.0.1:1/api-ws/v1/stream", allow_loopback=True
        )  # Avoid deriving a production address in the test.
        return RunnerFactory(FakeApiSession(), profile)  # Return a factory with SDK-shaped attributes.

    def _real_manager(self, api: FakeApiSession, cloud: FakeMistCloud) -> StreamSessionManager:
        """Build a manager that uses the real runner factory.

        Args:
            api: The fake Mist API session.
            cloud: The fake Mist cloud that owns loopback URLs.

        Returns:
            A session manager with short WebSocket waits.
        """
        profile = TransportProfile(
            stream_url=f"{cloud.base_ws_url}/api-ws/v1/stream",
            allow_loopback=True,
            read_timeout_seconds=0.05,
            subscribe_timeout_seconds=0.2,
            reconnect_delays=(),
        )  # Keep all failure paths fast and loopback-only.
        settings = StreamSettings(max_sessions=1)  # One session is enough for each failure case.
        return StreamSessionManager(settings, RunnerFactory(api, profile), time.monotonic)  # Return manager.

    def _wait_for_state(
        self, manager: StreamSessionManager, session_id: str, states: set[SessionState], timeout: float = 2.0
    ) -> object:
        """Wait until one session reaches an expected state.

        Args:
            manager: The manager that owns the session.
            session_id: The selected session identifier.
            states: Acceptable final states.
            timeout: Maximum wait seconds.

        Returns:
            The session after it reaches one expected state.
        """
        deadline = time.monotonic() + timeout  # Bound each async assertion.
        while time.monotonic() < deadline:  # Poll for a short time.
            session = manager.session(session_id)  # Read the current session state.
            if session.state in states:  # The background runner reached the target state.
                return session  # The caller can assert the reason.
            time.sleep(0.01)  # Avoid a busy loop while the runner thread works.
        return manager.session(session_id)  # Return the observed state for assertion failure context.

    def _manager(
        self, max_sessions: int, buffer_messages: int = 500, idle_seconds: int = 120
    ) -> tuple[StreamSessionManager, FakeFactory, FakeClock]:
        """Build a manager with fakes.

        Args:
            max_sessions: The live session limit.
            buffer_messages: The message buffer limit.
            idle_seconds: The idle limit.

        Returns:
            The manager, factory, and clock.
        """
        clock = FakeClock()  # Use deterministic time.
        factory = FakeFactory()  # Use fake runners.
        settings = StreamSettings(
            max_sessions=max_sessions, buffer_messages=buffer_messages, idle_seconds=idle_seconds
        )  # Use small limits.
        return StreamSessionManager(settings, factory, clock), factory, clock  # Return the assembled manager.

    def _channel_request(self, title: str) -> StartRequest:
        """Build a checked channel request.

        Args:
            title: The session title.

        Returns:
            A channel start request.
        """
        definition = ChannelDefinition(
            "site.stats.devices", "site", "Device statistics", "Live data.", "/sites/{site_id}"
        )  # Build a channel.
        return StartRequest("channel", definition, {"site_id": ("site-a",)}, {}, title)  # Return a checked request.

    def _shell_request(self) -> StartRequest:
        """Build a checked shell request.

        Returns:
            A shell start request.
        """
        target = FieldSpec("device_id", "Device", FieldKind.UUID, picker="devices")  # Build the device target field.
        definition = UtilityDefinition(
            "ex.shell", "ex", "createShellSession", "Shell", "Open a shell.", (), Safety.SHELL, "terminal", (target,)
        )  # Build a shell utility.
        return StartRequest(
            "shell", definition, {"site_id": ("site-a",), "device_id": ("dev-a",)}, {}, "Shell", device_name="device-a"
        )  # Return a checked request.

    def _utility_request(self) -> StartRequest:
        """Build a checked utility request.

        Returns:
            A utility start request.
        """
        target = FieldSpec("device_id", "Device", FieldKind.UUID, picker="devices")  # Build the device target field.
        definition = UtilityDefinition(
            "ex.ping", "ex", "ping", "Ping", "Send ping.", (), Safety.READ, "lines", (target,)
        )  # Build a read utility.
        return StartRequest(
            "utility", definition, {"site_id": ("site-a",), "device_id": ("dev-a",)}, {}, "Ping"
        )  # Return a checked request.

    def _screen_request(self) -> StartRequest:
        """Build a checked screen utility request.

        Returns:
            A screen start request.
        """
        target = FieldSpec("device_id", "Device", FieldKind.UUID, picker="devices")  # Build the device target field.
        definition = UtilityDefinition(
            "ex.topCommand", "ex", "topCommand", "Top", "Run top.", (), Safety.READ, "screen", (target,)
        )  # Build a screen utility.
        return StartRequest(
            "utility", definition, {"site_id": ("site-a",), "device_id": ("dev-a",)}, {}, "Top"
        )  # Return a checked request.
