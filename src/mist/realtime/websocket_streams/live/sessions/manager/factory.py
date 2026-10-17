"""Build runners, terminal state, and complete stream sessions."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Construction actions use structured JSON records.
import re  # Finite shell commands need a normalized prompt boundary.
import secrets  # Public session identifiers must be hard to guess.
import threading  # Several apps can install the SDK filter together.
import time  # Batch workers use bounded waits and command deadlines.
from collections.abc import Callable, Mapping  # Tests inject a monotonic clock.
from concurrent.futures import ThreadPoolExecutor, as_completed  # Bound private target execution.
from dataclasses import replace  # Child requests retain the checked target only.
from datetime import UTC, datetime, timedelta  # Terminal expiry uses public UTC text.
from typing import cast  # Shell input uses the existing interactive runner contract.

from src.mist.realtime.websocket_streams.catalog.model import (
    UtilityDefinition,
)  # Screen selection follows catalog output.
from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Target construction failures use stable request errors.
from src.mist.realtime.websocket_streams.intake.start_request.models import (
    BatchExecutionPlan,
    BatchTargetRequest,
    StartRequest,
)  # Builders receive checked requests.
from src.mist.realtime.websocket_streams.live.runners.channel.runner import (
    ChannelStreamRunner,
)  # Channel requests use this runner.
from src.mist.realtime.websocket_streams.live.runners.shell.runners import (
    ScreenRunner,
    ShellRunner,
)  # Terminal runner classes.
from src.mist.realtime.websocket_streams.live.runners.text.redaction import (
    ShellAddressFilter,
)  # Redact SDK shell addresses.
from src.mist.realtime.websocket_streams.live.runners.utility.runner.utility_runner import (
    UtilityRunner,
)  # Utility runner class.
from src.mist.realtime.websocket_streams.live.sessions.buffer.message_buffer import (
    MessageBuffer,
)  # Sessions keep bounded messages.
from src.mist.realtime.websocket_streams.live.sessions.manager.contracts import (
    RunnerFactoryLike,
    StreamRunner,
)  # Typed contracts.
from src.mist.realtime.websocket_streams.live.sessions.record.session import (
    StreamSession,
)  # Builders create concrete sessions.
from src.mist.realtime.websocket_streams.live.sessions.record.state import (
    SessionResources,
    SessionSink,
    SessionState,
)  # Construction values.
from src.mist.realtime.websocket_streams.live.sessions.settings import StreamSettings  # Settings define all limits.
from src.mist.realtime.websocket_streams.live.terminal.byte_history import (
    ByteHistory,
)  # Finite shell collection reads exact raw bytes.
from src.mist.realtime.websocket_streams.live.terminal.gateway import (
    TerminalRunner,
)  # Writable terminals expose input methods.
from src.mist.realtime.websocket_streams.live.terminal.input_queue import (
    TerminalInput,
)  # Each shell child owns its private input queue.
from src.mist.realtime.websocket_streams.live.terminal.state.terminal_state import (
    TerminalState,
)  # Each shell target has private terminal state.
from src.mist.realtime.websocket_streams.live.transport.endpoint import (
    MistStreamEndpoint,
    TransportProfile,
)  # Connection values.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.redaction import (
    LineSecretRedactor,
)  # Keep split terminal credentials out of batch output.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # T072.


class RunnerFactory:
    """Build the matching runner for each checked request."""

    _filter_installed = False  # Install the Mist SDK shell redaction filter one time.
    _filter_lock = threading.Lock()  # Protect the one-time filter state.

    def __init__(
        self, apisession: object, profile: TransportProfile | None = None, settings: StreamSettings | None = None
    ) -> None:
        """Build one factory for a Mist API session."""
        self._apisession = apisession  # Utility and shell triggers use the same API session.
        self._endpoint = MistStreamEndpoint(apisession, profile)  # Build owned transport connection values.
        self._settings = settings or StreamSettings.from_environment()
        self._transport = SharedTransport(self._settings.max_sessions)  # Share capacity with private batch targets.
        self._logger = StructuredTransportLogger(logging.getLogger(__name__))  # Use bounded content-free records.

    @staticmethod
    def is_screen(request: StartRequest) -> bool:
        """Return whether a request uses a full-screen utility runner."""
        definition = request.definition  # The catalog owns utility output mode.
        return isinstance(definition, UtilityDefinition) and definition.output == "screen"  # Select screen output only.

    def build(self, request: StartRequest, sink: SessionSink) -> StreamRunner:
        """Build one runner without starting it."""
        self._logger.emit(logging.INFO, "session_runner_build_start", {"action": request.key})  # Log safe key only.
        if request.batch_plan is not None and request.kind != "channel":  # Batch plans use the parent scheduler.
            runner: StreamRunner = BatchRunner(request, sink, self._select_single, self._settings, self._transport)
        else:  # Single Site requests hold one public transport permit.
            runner = self._transport.wrap(self._select_single(request, sink), sink)
        self._logger.emit(
            logging.DEBUG, "session_runner_build_complete", {"status": type(runner).__name__}
        )  # Safe type.
        return runner  # The manager starts it after the session becomes visible.

    @classmethod
    def _install_shell_filter(cls) -> None:
        """Install the shell address filter one time."""
        with cls._filter_lock:  # Several threads can start the first shell together.
            if cls._filter_installed:  # The safe filter already protects the SDK logger.
                return  # Do not install a duplicate filter.
            logging.getLogger("mistapi").addFilter(ShellAddressFilter())  # Redact shell WebSocket addresses.
            cls._filter_installed = True  # Record the completed one-time action.

    def _select_single(self, request: StartRequest, sink: SessionSink) -> StreamRunner:
        """Return one existing Single Site runner without batch dispatch."""
        if request.kind == "channel":  # Channel requests use the owned stream transport.
            return ChannelStreamRunner(self._endpoint, request, sink)  # Build a channel runner.
        if request.kind == "shell":  # Shell requests use a writable terminal runner.
            self._install_shell_filter()  # Protect SDK logs before the REST trigger.
            return ShellRunner(self._apisession, self._endpoint, request, sink)  # Build a shell runner.
        if self.is_screen(request):  # Screen utilities use a read-only terminal runner.
            self._install_shell_filter()  # Protect SDK logs before the REST trigger.
            return ScreenRunner(self._apisession, self._endpoint, request, sink)  # Build a screen runner.
        return UtilityRunner(self._apisession, self._endpoint, request, sink)  # Build a line or packet runner.


class SharedTransport:
    """Share one bounded transport budget across public sessions and private targets."""

    FINAL_STATES = {
        SessionState.STOPPED,
        SessionState.FINISHED,
        SessionState.TIMED_OUT,
        SessionState.FAILED,
    }  # Permit lifetime follows session lifetime.

    class Gate:
        """Count active connections and give waiting Single Site work priority."""

        def __init__(self, capacity: int) -> None:
            """Create one fair capacity gate."""
            self._capacity = capacity  # Match the configured live session limit.
            self._condition = threading.Condition()  # Wake work when a transport releases capacity.
            self._active = 0  # Count active single and batch target connections.
            self._single_waiters = 0  # Batch work yields to admitted Single Site work.

        def admit(self, stopping: threading.Event, batch: bool) -> tuple[bool, int]:
            """Wait for capacity and return the result with the active count."""
            with self._condition:  # Protect both active counts and priority waiters.
                if not batch:  # Record admitted Single Site work before batch dispatch.
                    self._single_waiters += 1  # Batch workers yield while this count is nonzero.
                try:
                    acquired = self._wait(stopping, batch)  # Wait until capacity or a stop request.
                finally:  # Always remove single-session priority after the wait ends.
                    self._leave(batch)  # Later batch dispatch can use spare capacity.
                return acquired, self._active  # Capture a bounded count for the completion record.

        def release(self) -> int:
            """Return one connection slot and report the active count."""
            with self._condition:  # Update pool state atomically.
                self._active -= 1  # Return one connection slot.
                self._condition.notify_all()  # Wake the next eligible single or batch waiter.
                return self._active  # Report the safe pool count.

        def _wait(self, stopping: threading.Event, batch: bool) -> bool:
            """Wait while the pool is full or Single Site work has priority."""
            while self._active >= self._capacity or (batch and self._single_waiters):  # Apply capacity and priority.
                if stopping.is_set():  # Do not keep cancelled work queued.
                    break  # Exit and report a cancelled acquisition.
                self._condition.wait(0.05)  # Recheck stop and capacity at a bounded interval.
            acquired = not stopping.is_set()  # A cancelled waiter cannot acquire a permit.
            if acquired:  # Only successful callers increase active transport count.
                self._active += 1  # Reserve capacity before runner construction.
            return acquired  # Tell the caller whether it owns capacity.

        def _leave(self, batch: bool) -> None:
            """Release Single Site priority after its wait ends."""
            if not batch:  # Only Single Site waiters hold priority.
                self._single_waiters -= 1  # Later batch dispatch can use spare capacity.
                self._condition.notify_all()  # Wake batch workers after priority changes.

    class Lifecycle:
        """Hold one transport permit for the lifetime of one delegate runner."""

        def __init__(self, pool: SharedTransport, runner: StreamRunner, sink: SessionSink) -> None:
            """Store the runner and its lifecycle observer."""
            self._pool, self._runner, self._sink = pool, runner, sink  # Keep one private delegate.
            self._stopping = threading.Event()  # Stop can cancel a queued permit request.

        def _run(self) -> None:
            """Acquire one permit and retain it until the session ends."""
            if not self._pool.acquire(self._stopping, batch=False):  # A stopped queued session owns no permit.
                self._sink.finish(SessionState.STOPPED, "The operator stopped the session.")  # Close the public record.
                return  # No delegate started.
            try:  # Release capacity when the delegate ends or startup fails.
                if self._stopping.is_set():  # Recheck stop after acquiring capacity.
                    self._sink.finish(
                        SessionState.STOPPED, "The operator stopped the session."
                    )  # Close the public record.
                    return  # Do not start after a stop.
                if not self._start_runner():  # Convert expected startup failure to a final session result.
                    return  # The helper already finished the public record.
                self._wait_for_finish()  # Retain capacity while the delegate remains active.
            finally:
                self._pool.release()  # Do not leak capacity after any runner outcome.

        def _start_runner(self) -> bool:
            """Start the delegate and report one safe setup failure."""
            try:
                self._runner.start()  # Delegate retains its existing connection lifecycle.
            except (OSError, RuntimeError, ValueError) as error:  # Record only the exception type.
                self._pool._logger.emit(logging.ERROR, "transport_runner_start_error", {"status": type(error).__name__})
                self._sink.finish(SessionState.FAILED, "The stream could not start.")  # Report a safe start refusal.
                return False  # The caller must release the permit.
            return True  # The delegate owns a started public session.

        def _wait_for_finish(self) -> None:
            """Stop once and retain capacity until the session reaches a final state."""
            stop_sent = False  # Send one stop when the manager or operator requests it.
            while self._sink.state not in self._pool.FINAL_STATES:  # Keep the permit through final runner cleanup.
                if self._stopping.wait(0.1) and not stop_sent:  # Poll a stop without a busy loop.
                    self._runner.stop()  # Signal the delegate exactly once.
                    stop_sent = True  # Prevent repeated close calls.

    class PermitRunner(Lifecycle):
        """Expose the public runner protocol while the lifecycle holds one permit."""

        def start(self) -> None:
            """Start permit acquisition outside the web request thread."""
            thread = threading.Thread(
                target=self._run, name="ws-transport-permit", daemon=True
            )  # Keep HTTP admission fast.
            thread.start()  # Acquire capacity on the private worker.

        def stop(self) -> None:
            """Stop a pending wait or signal the active runner through its worker."""
            self._stopping.set()  # Wake acquisition or active lifecycle polling.

        def send_input(self, text: str) -> None:
            """Forward checked input to the writable terminal runner."""
            cast(TerminalRunner, self._runner).send_input(text)  # Preserve the existing shell input path.

        def resize(self, cols: int, rows: int) -> None:
            """Forward checked dimensions to the writable terminal runner."""
            cast(TerminalRunner, self._runner).resize(cols, rows)  # Preserve the existing shell resize path.

    def __init__(self, capacity: int) -> None:
        """Create one fair transport permit pool."""
        self._gate = self.Gate(capacity)  # Own capacity and priority state.
        self._logger = StructuredTransportLogger(logging.getLogger(__name__))  # Log only safe pool state.

    def acquire(self, stopping: threading.Event, batch: bool) -> bool:
        """Acquire capacity and prioritize a waiting public single-site session."""
        priority = "batch" if batch else "single"  # Keep the scheduling field bounded.
        self._logger.emit(logging.INFO, "transport_permit_wait_started", {"priority": priority})  # Log before waiting.
        acquired, active = self._gate.admit(stopping, batch)  # Wait for capacity or cancellation.
        status = "acquired" if acquired else "cancelled"  # Report no target identity or request data.
        self._logger.emit(
            logging.DEBUG, "transport_permit_wait_completed", {"priority": priority, "status": status, "active": active}
        )  # Log after waiting.
        return acquired  # Tell the caller whether it owns capacity.

    def release(self) -> None:
        """Release one active transport and wake waiting work."""
        active = self._gate.release()  # Return one connection slot and read the safe count.
        self._logger.emit(logging.DEBUG, "transport_permit_released", {"active": active})  # Confirm release.

    def wrap(self, runner: StreamRunner, sink: SessionSink) -> StreamRunner:
        """Guard one public runner with the shared transport permit pool."""
        return self.PermitRunner(self, runner, sink)  # Keep the existing runner protocol.


class BatchRunner:
    """Schedule bounded utility or finite shell work under one parent session."""

    INITIAL_SECONDS = 30.0  # Initial shell output must arrive before this deadline.
    COMMAND_SECONDS = 30.0  # Each shell command has a finite response deadline.
    QUIET_SECONDS = 2.0  # A prompt must remain quiet for this interval.
    PROMPT = re.compile(r"([^\r\n]{1,160}[>#%])")  # Match one bounded terminal prompt line.
    ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")  # Remove terminal color and control sequences.

    class Part:
        """Share the parent scheduler state with one cohesive helper."""

        def __init__(self, owner: BatchRunner) -> None:
            """Keep the owner and its cancellation state."""
            self._owner = owner  # Reach the shared request, sink, and registry.
            self._stopping = owner._stopping  # Stop requests use one shared event.
            self._plan = owner._plan  # Read the checked plan from the parent request.

    class Registry(Part):
        """Track active children, terminal state, and the parent result."""

        def terminal(self) -> TerminalState:
            """Build bounded private terminal state for one shell target."""
            life = float(self._owner._settings.max_stream_seconds)
            expiry = datetime.now(UTC).replace(microsecond=0) + timedelta(seconds=life)
            return TerminalState(
                ByteHistory(self._owner._settings.terminal_history_bytes),
                TerminalInput(),
                time.monotonic() + life,
                expiry.isoformat().replace("+00:00", "Z"),
            )

        def register(self, target_key: str, runner: StreamRunner) -> bool:
            """Publish one active child so stop can signal it."""
            with self._owner._lock:
                if self._stopping.is_set():
                    return False
                self._owner._active[target_key] = runner
                return True

        def unregister(self, target_key: str) -> None:
            """Remove one completed child from the active runner map."""
            with self._owner._lock:
                self._owner._active.pop(target_key, None)

        def finish_parent(self) -> None:
            """Finish the public parent after every private target stops."""
            self._plan().progress.artifacts.finish()
            status = self._plan().progress.summary.summary()["status"]
            state = (
                SessionState.STOPPED
                if status == "stopped"
                else SessionState.FAILED if status == "failed" else SessionState.FINISHED
            )
            reason = "The batch stopped." if state == SessionState.STOPPED else "The batch finished."
            self._owner._sink.finish(state, reason)

    class Shell(Part):
        """Collect finite shell output through exact prompt boundaries."""

        def collect(
            self,
            runner: StreamRunner,
            child_sink: BatchRunner.TargetSink,
            target: BatchTargetRequest,
            terminal: TerminalState,
        ) -> None:
            """Collect the initial prompt and the exact approved command sequence."""
            cursor, prompt = self._initial_prompt(terminal)  # Require a verified prompt before the first command.
            if prompt is None:  # Do not send commands to an unknown shell state.
                child_sink.fail("completion_unproven", "unproven")  # Preserve the target's safe failure reason.
                return  # Stop this target before command dispatch.
            for index, command in enumerate(self._plan().commands):  # Preserve the confirmed command order.
                if self._stopping.is_set():  # Observe cancellation between commands.
                    child_sink.stopped()  # Preserve the parent stop outcome.
                    return  # Do not send later approved commands.
                self._plan().progress.transitions.set_command_index(target.target_key, index)  # Record safe progress.
                self._owner._targets._send_shell_command(runner, command, index)  # Send only after operator approval.
                cursor, complete = self._command_prompt(terminal, cursor, prompt, index)  # Prove command completion.
                if not complete:  # Keep later commands behind a verified boundary.
                    child_sink.fail("completion_unproven", "unproven")  # Preserve partial output and safe status.
                    return  # Do not send later commands after an unproven result.
            child_sink.completed()  # Mark the target collected after every command boundary.

        def _initial_prompt(self, terminal: TerminalState) -> tuple[int, str | None]:
            """Wait for initial output and capture one normalized prompt."""
            deadline = time.monotonic() + BatchRunner.INITIAL_SECONDS  # Bound the first device response.
            cursor = 0  # Read the retained terminal stream from its first byte.
            output = bytearray()  # Retain initial bytes until prompt recognition.
            prompt = None  # No prompt is valid until the collector observes one.
            self._owner._logger.emit(logging.INFO, "batch_shell_initial_collection_started", {})  # Log before reads.
            try:  # Log page-read failures while preserving their exception.
                while time.monotonic() < deadline and not self._stopping.is_set():  # Respect time and cancellation.
                    page = terminal.history.read(cursor, 0.1)  # Read one bounded output slice.
                    cursor = page.next_position  # Advance to the next unread byte.
                    output.extend(page.data)  # Retain bytes until prompt normalization.
                    prompt = self._prompt(bytes(output))  # Check the latest accumulated terminal output.
                    if prompt is not None or page.closed:  # Stop after a prompt or a closed stream.
                        break  # No more initial output can improve this result.
            except Exception as error:  # Log collection failures and preserve the original exception.
                error_fields = {"error_type": type(error).__name__}  # Keep the error context free of terminal data.
                self._owner._logger.emit(logging.ERROR, "batch_shell_initial_collection_error", error_fields)  # Log.
                raise  # Preserve the original failure for the target runner.
            status = "recognized" if prompt is not None else "unproven"  # Keep the result state bounded.
            result = {"output_bytes": len(output), "status": status}  # Keep the result free of terminal content.
            self._owner._logger.emit(logging.DEBUG, "batch_shell_initial_collection_completed", result)  # Report state.
            return cursor, prompt  # Return the verified prompt or the unproven result.

        def _command_prompt(
            self, terminal: TerminalState, cursor: int, prompt: str, command_index: int
        ) -> tuple[int, bool]:
            """Wait for the same prompt and quiet interval after command output."""
            fields = {"command_index": command_index}  # Identify the command without exposing its text.
            self._owner._logger.emit(logging.INFO, "batch_shell_output_collection_started", fields)  # Log before reads.
            try:  # Preserve output errors after writing a safe error record.
                cursor, complete, output_bytes = self._read_command_output(
                    terminal, cursor, prompt  # Read through the verified prompt boundary.
                )
            except Exception as error:  # Record failure without shell output or secrets.
                error_result = fields | {"error_type": type(error).__name__}  # Keep only the exception class.
                self._owner._logger.emit(  # Log the failure without terminal output.
                    logging.ERROR, "batch_shell_output_collection_error", error_result
                )
                raise  # Preserve the original output error.
            status = "collected" if complete else "unproven"  # Keep the result state bounded.
            result = fields | {"output_bytes": output_bytes, "status": status}  # Retain safe collection metadata.
            self._owner._logger.emit(  # Publish the output collection result.
                logging.DEBUG,  # Use debug after the collection.
                "batch_shell_output_collection_completed",  # Identify the completed action.
                result,  # Include only safe collection metadata.
            )
            return cursor, complete  # Return the cursor and proof state.

        def _read_command_output(self, terminal: TerminalState, cursor: int, prompt: str) -> tuple[int, bool, int]:
            """Read one command until its latest prompt remains quiet."""
            deadline = time.monotonic() + BatchRunner.COMMAND_SECONDS  # Bound this command response.
            quiet_since = 0.0  # Hold monotonic time after the latest matching prompt.
            quiet_started = False  # Track whether a matching prompt started the interval.
            output = bytearray()  # Retain only output from this command boundary.
            while time.monotonic() < deadline and not self._stopping.is_set():  # Respect the deadline and stop state.
                page = terminal.history.read(cursor, 0.1)  # Read one bounded output slice.
                cursor = page.next_position  # Advance to the next unread byte.
                if page.data:  # Any new byte starts a new quiet interval.
                    output.extend(page.data)  # Retain output for prompt-boundary checks.
                    quiet_started = False  # Discard silence measured before this output.
                if page.closed:  # A closed stream cannot prove later completion.
                    break  # Preserve partial output as unproven.
                if output and self._prompt(bytes(output)) == prompt:  # Require the same prompt at output end.
                    quiet_since = time.monotonic() if not quiet_started else quiet_since  # Reset after new output.
                    quiet_started = True  # Mark the interval start as valid.
                    if time.monotonic() - quiet_since >= BatchRunner.QUIET_SECONDS:  # Require two quiet seconds.
                        return cursor, True, len(output)  # Report completion and its byte count.
            return cursor, False, len(output)  # Preserve partial output when proof fails.

        @classmethod
        def _prompt(cls, data: bytes) -> str | None:
            """Return one normalized prompt at the end of terminal output."""
            text = BatchRunner.ANSI.sub("", data.decode("utf-8", errors="replace")).replace("\r", "")  # Normalize.
            final_line = text.rstrip().split("\n")[-1].strip()  # Inspect only the latest nonblank line.
            match = BatchRunner.PROMPT.fullmatch(final_line)  # Require a prompt at the end of the output.
            return match.group(1).strip() if match else None  # Return the final normalized prompt only.

    class Targets(Part):
        """Run each private target after its transport permit is reserved."""

        def run(self, target: BatchTargetRequest) -> None:
            """Run one utility or finite shell target and preserve its outcome."""
            plan = self._plan()
            if self._stopping.is_set() or plan.progress.cancellation.is_cancelled():
                plan.progress.transitions.transition(target.target_key, "stopped", "cancelled", "cancelled")
                return
            if not self._owner._transport.acquire(self._stopping, batch=True):
                plan.progress.transitions.transition(target.target_key, "stopped", "cancelled", "cancelled")
                return
            if self._stopping.is_set() or plan.progress.cancellation.is_cancelled():
                plan.progress.transitions.transition(target.target_key, "stopped", "cancelled", "cancelled")
                return
            if not plan.progress.transitions.transition(target.target_key, "running"):
                return
            try:
                self._run_target(target, plan)
            finally:
                self._owner._transport.release()

        def _run_target(self, target: BatchTargetRequest, plan: BatchExecutionPlan) -> None:
            """Run one target after its transport permit is reserved."""
            registry = self._owner._registry
            terminal = registry.terminal() if self._owner._request.kind == "shell" else None
            child_sink = BatchRunner.TargetSink(self._owner._sink, plan, target, terminal)
            runner: StreamRunner | None = None
            try:
                runner = self._owner._build(replace(target.request, batch_plan=None), child_sink)
                child_sink.bind_runner(runner)
                if not registry.register(target.target_key, runner):
                    child_sink.stopped()
                    return
                self._start_target(runner, child_sink, target, terminal)
            except (OSError, RuntimeError, StreamRequestError, ValueError):  # Contain expected target setup failures.
                child_sink.fail("target_failed")  # Do not expose upstream exception text.
            finally:
                if runner is not None:
                    runner.stop()  # Close a finite runner after its output or failure.
                    registry.unregister(target.target_key)  # Remove the completed child from stop coordination.

        def _start_target(
            self,
            runner: StreamRunner,
            child_sink: BatchRunner.TargetSink,
            target: BatchTargetRequest,
            terminal: TerminalState | None,
        ) -> None:
            """Start one child runner and wait for its finite outcome."""
            if terminal is not None:
                if terminal.input is None:
                    raise RuntimeError("A finite shell target needs an input queue.")
                terminal.input.bind(cast(ShellRunner, runner).send_input)
            if self._stopping.is_set():
                child_sink.stopped()
                return
            runner.start()
            if terminal is None:
                self._wait_for_finish(runner, child_sink)
                return
            self._owner._shell.collect(runner, child_sink, target, terminal)

        def _wait_for_finish(self, runner: StreamRunner, child_sink: BatchRunner.TargetSink) -> None:
            """Wait for utility completion while honoring parent cancellation."""
            stop_sent = False
            while not child_sink.finished.wait(0.1):
                if self._stopping.is_set() and not stop_sent:
                    runner.stop()
                    stop_sent = True

        def _send_shell_command(self, runner: StreamRunner, command: str, command_index: int) -> None:
            """Send one approved command and log only its bounded index."""
            fields = {"command_index": command_index}  # Keep command text and secrets outside logs.
            self._owner._logger.emit(logging.INFO, "batch_shell_command_dispatch_started", fields)  # Log before send.
            try:  # Preserve dispatch failures after logging safe context.
                cast(ShellRunner, runner).send_input(command + "\n")  # Send only the approved command line.
            except Exception as error:  # Record the error without command text.
                result = fields | {"error_type": type(error).__name__}  # Keep only the exception class.
                self._owner._logger.emit(logging.ERROR, "batch_shell_command_dispatch_error", result)  # Log failure.
                raise  # Preserve the original dispatch failure.
            result = fields | {"status": "sent"}  # Keep the completion state bounded.
            self._owner._logger.emit(logging.DEBUG, "batch_shell_command_dispatch_completed", result)  # Log after send.

    def __init__(
        self,
        request: StartRequest,
        sink: SessionSink,
        build: Callable[[StartRequest, SessionSink], StreamRunner],
        settings: StreamSettings,
        transport: SharedTransport,
    ) -> None:
        """Store one frozen target plan and its private runner factory."""
        self._request = request  # Keep the one frozen parent request.
        self._sink = sink  # Publish every target through one public session.
        self._build = build  # Reuse the existing Single Site runner constructors.
        self._settings = settings  # Bound shell state by the configured runtime limits.
        self._transport = transport  # Share active capacity with Single Site runners.
        self._logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep batch records content-free.
        self._stopping = threading.Event()  # Stop can cancel queued target dispatch.
        self._active: dict[str, StreamRunner] = {}  # Keep only active child delegates.
        self._lock = threading.RLock()  # Coordinate stop and registration.
        self._thread: threading.Thread | None = None  # Keep one parent scheduler thread.
        self._registry = self.Registry(self)  # Own active children and the parent result.
        self._shell = self.Shell(self)  # Own finite shell collection.
        self._targets = self.Targets(self)  # Own private target execution.

    def start(self) -> None:
        """Start the batch scheduler outside the request thread."""
        self._thread = threading.Thread(target=self._run, name="ws-batch", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop queued dispatch and signal every active target runner."""
        plan = self._plan()
        self._stopping.set()
        plan.progress.cancellation.cancel_queued()
        with self._lock:
            runners = tuple(self._active.values())
        for runner in runners:
            runner.stop()

    def _run(self) -> None:
        """Run targets with the preview's bounded concurrency."""
        plan = self._plan()
        with ThreadPoolExecutor(max_workers=plan.concurrency, thread_name_prefix="ws-target") as pool:
            futures = [pool.submit(self._targets.run, target) for target in plan.targets]
            for future in as_completed(futures):
                future.result()
        self._registry.finish_parent()

    def _plan(self) -> BatchExecutionPlan:
        """Return the immutable plan from the checked parent request."""
        plan = self._request.batch_plan
        if plan is None:
            raise RuntimeError("The batch runner requires a checked batch plan.")
        return plan

    class SinkBase:
        """Hold the parent, target, and private shell state for one target sink."""

        def __init__(
            self,
            parent: SessionSink,
            plan: BatchExecutionPlan,
            target: BatchTargetRequest,
            terminal: TerminalState | None,
        ):
            """Store the parent, target, and private shell state."""
            self._parent, self._plan, self._target, self.terminal = parent, plan, target, terminal
            self.state = parent.state
            self.finished = threading.Event()
            self._runner: StreamRunner | None = None
            self._redactor = LineSecretRedactor()  # Delay terminal lines until split secrets can be checked.

        def bind_runner(self, runner: StreamRunner) -> None:
            """Keep the child runner available for an output failure stop."""
            self._runner = runner

        def mark_live(self, note: str = "") -> None:
            """Mark the parent live after one target connects."""
            self._parent.mark_live(note)

        def mark_input_ready(self) -> None:
            """Release initial shell input after the first output."""
            if self.terminal is not None and self.terminal.input is not None:
                self.terminal.input.release()

    class Outcomes(SinkBase):
        """Record one terminal outcome for one target."""

        def completed(self) -> None:
            """Mark a finite command list as collected."""
            self._record_outcome("completed", None, "collected")

        def fail(self, reason_code: str, completion: str | None = None) -> None:
            """Mark one target failed without exposing upstream exception text."""
            self._record_outcome("failed", reason_code, completion)

        def stopped(self) -> None:
            """Mark one active target stopped after cancellation."""
            self._record_outcome("stopped", "cancelled", "cancelled")

        def _record_outcome(self, state: str, reason_code: str | None, completion: str | None) -> None:
            """Persist and publish one target outcome after a valid terminal transition."""
            if not self._plan.progress.transitions.transition(self._target.target_key, state, reason_code, completion):
                self.finished.set()  # Preserve the first terminal result.
                return
            outcome = {
                "target": dict(self._target.identity),
                "state": state,
                "reason_code": reason_code,
                "completion": completion,
            }  # Keep every terminal result tied to its frozen target identity.
            self._persist_outcome(outcome)  # Persist under the same artifact quota as result data.
            self._parent.add_message(
                "error" if state == "failed" else "outcome",
                outcome,
                source=self._target.target_key,
            )  # Publish one outcome event for this target.
            self.finished.set()  # Release the bounded scheduler wait.

        def _persist_outcome(self, outcome: Mapping[str, object]) -> None:
            """Write one outcome artifact and report a write failure to the parent."""
            if not self._plan.progress.artifacts.write_result(
                self._target.target_key, self._target.identity, "outcome", outcome, None
            ):
                self._parent.add_message(
                    "error",
                    {"target": dict(self._target.identity), "reason_code": "output_failed"},
                    source=self._target.target_key,
                )  # Report a manifest or output-write failure to the parent.

    class TargetSink(Outcomes):
        """Route one target's output and final result through its public parent."""

        def add_message(self, kind: str, content: object, **metadata: str | None) -> None:
            """Add one result with complete target identity."""
            if kind == "terminal" and isinstance(content, str):  # Terminal text needs line-boundary redaction.
                content = self._redactor.feed(content, False)  # Keep split secrets buffered until the next chunk.
                if not content:  # Empty redactor output has no safe result to publish.
                    return  # Avoid writing an empty artifact record.
            self._write_message(kind, content, metadata.get("summary"))  # Share storage and publication behavior.

        def _write_message(self, kind: str, content: object, summary: str | None) -> None:
            """Save one redacted target result before publishing it."""
            if not self._plan.progress.artifacts.write_result(
                self._target.target_key,
                self._target.identity,
                kind,
                content,
                summary,
            ):  # Required artifact writes must succeed before the result becomes public.
                self.fail("output_failed")  # Preserve one stable failure reason for this target.
                if self._runner is not None:  # An active child must stop after required output failure.
                    self._runner.stop()  # Prevent later output from escaping the failed artifact.
                return  # Do not publish data that the artifact store rejected.
            self._plan.progress.transitions.record_result(self._target.target_key)  # Count only saved output.
            record = {"target": dict(self._target.identity), "data": content}  # Bind data to its frozen identity.
            self._parent.add_message(
                kind,
                record,
                source=self._target.target_key,
                summary=summary,
            )  # Publish only after storage and target accounting succeed.

        def add_bytes(self, data: bytes) -> None:
            """Retain exact private shell bytes and emit readable target output."""
            if self.terminal is not None:  # Shell targets retain exact bytes outside the public message buffer.
                self.terminal.history.append(data)  # Preserve the raw terminal transcript for artifact review.
            self.add_message(
                "terminal", data.decode("utf-8", errors="replace")
            )  # Decode only for the bounded, redacted message stream.

        def finish(self, state: SessionState, reason: str) -> None:
            """Record one child outcome without ending the public batch."""
            pending = self._redactor.feed("", True)  # Flush only terminal text that passed secret checks.
            if pending:  # A trailing line can remain after the final transport chunk.
                self._write_message("terminal", pending, None)  # Save the checked remainder before the outcome.
            terminal = (
                "completed"
                if state == SessionState.FINISHED
                else "stopped" if state == SessionState.STOPPED else "failed"
            )  # Map child lifecycle values to the batch outcome contract.
            code = (
                None if terminal == "completed" else "cancelled" if terminal == "stopped" else "target_failed"
            )  # Use stable reason codes.
            self._record_outcome(
                terminal, code, "collected" if terminal == "completed" else None
            )  # Persist the terminal result after all checked output.
            del reason  # Child text is not safe for the public target outcome.


class TerminalSessionBuilder:
    """Build terminal state for shell and screen sessions."""

    def __init__(self, settings: StreamSettings, clock: Callable[[], float]) -> None:
        """Store terminal limits and the injected monotonic clock."""
        self._settings, self._clock = settings, clock  # Use shared immutable settings and deterministic time.

    def build(self, request: StartRequest) -> TerminalState | None:
        """Return terminal state for shell and screen requests."""
        if request.batch_plan is not None:
            return None  # Batch shell children own private terminal state and reject broadcast input.
        shell, screen = request.kind == "shell", RunnerFactory.is_screen(request)  # Identify terminal request types.
        if not shell and not screen:  # Message-list sessions do not need terminal state.
            return None  # Preserve the existing channel and utility shape.
        history = ByteHistory(self._settings.terminal_history_bytes)  # Bound exact terminal output bytes.
        input_queue = TerminalInput(self._clock) if shell else None  # Screen utilities stay read-only.
        state = TerminalState(history, input_queue, *self._expiry())  # Build one terminal state.
        if screen:  # Mist screen utilities use fixed dimensions.
            state.set_size(ScreenRunner.SCREEN_COLS, ScreenRunner.SCREEN_ROWS)  # Preserve 80 by 40 screen size.
        return state  # Return terminal state after screen-specific sizing.

    def _expiry(self) -> tuple[float, str]:
        """Return monotonic and public UTC expiry values."""
        life = float(self._settings.max_stream_seconds)  # Preserve the configured maximum life.
        expires = datetime.now(UTC).replace(microsecond=0) + timedelta(seconds=life)  # Build UTC expiry.
        return self._clock() + life, expires.isoformat().replace("+00:00", "Z")  # Preserve public time format.


class SessionBuilder:
    """Build one complete session and attach its runner."""

    def __init__(self, settings: StreamSettings, factory: RunnerFactoryLike, clock: Callable[[], float]) -> None:
        """Build child construction collaborators."""
        self._settings, self._factory, self._clock = settings, factory, clock  # Store shared construction inputs.
        self._terminals = TerminalSessionBuilder(settings, clock)  # Own terminal-specific construction.

    def build(self, request: StartRequest) -> StreamSession:
        """Build a session, attach its runner, and bind shell input."""
        buffer = MessageBuffer(self._settings.buffer_messages, self._settings.buffer_bytes)  # Apply message limits.
        resources = SessionResources(buffer, self._clock, self._terminals.build(request))  # Group session resources.
        session = StreamSession(secrets.token_hex(8), request, resources)  # Preserve 16 hexadecimal characters.
        session.runner = self._factory.build(request, session)  # Let the runner write through this session.
        self._bind_input(session)  # Connect writable shell input after runner creation.
        return session  # The manager stores this session before runner start.

    @staticmethod
    def _bind_input(session: StreamSession) -> None:
        """Bind a writable terminal queue to its concrete runner."""
        terminal, runner = session.terminal, session.runner  # Read both optional collaborators once.
        if terminal is None or terminal.input is None or not isinstance(runner, TerminalRunner):  # No writable shell.
            return  # Message-list and screen sessions accept no keys.
        terminal.input.bind(runner.send_input)  # Preserve ordered early and live input delivery.
