"""Manage live WebSocket stream sessions.

Why:
    Issue #3551. The Operations portal can receive many web requests while the
    Mist SDK calls back on its own threads. The manager owns the session map,
    enforces the live limit, stops idle sessions, and never blocks a web
    request on a stream close.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # The manager logs starts, stops, and audit events.
import secrets  # Session identifiers must be hard to guess.
import threading  # Gunicorn threads share one manager.
import time  # The default clock and reaper sleep use monotonic time.
from collections.abc import Callable, Iterator  # The manager injects a fake clock in tests.
from datetime import UTC, datetime, timedelta  # The terminal expiry time is public UTC text.
from typing import Protocol, cast  # Web services and tests inject runner factories.

from src.websocket_streams.catalog.model import Safety, UtilityDefinition  # Audit decisions use utility safety.
from src.websocket_streams.intake.fields import StreamRequestError  # The manager raises contract errors.
from src.websocket_streams.intake.start_request import StartRequest  # The manager starts checked requests only.
from src.websocket_streams.live.runners.channel import ChannelStreamRunner  # Channel requests use this runner.
from src.websocket_streams.live.runners.shell import ShellRunner  # Shell requests use this runner.
from src.websocket_streams.live.runners.text import ShellAddressFilter  # The SDK can log a shell address.
from src.websocket_streams.live.runners.utility.runner import UtilityRunner  # Utility requests use this runner.
from src.websocket_streams.live.runners.utility.screen import ScreenRunner  # Top and Monitor Traffic use this runner.
from src.websocket_streams.live.sessions.buffer import MessageBuffer, MessagePage  # Buffers and read answers.
from src.websocket_streams.live.sessions.record import (
    SessionSink,
    SessionState,
    StreamSession,
)  # The manager owns sessions.
from src.websocket_streams.live.sessions.settings import StreamSettings  # Settings define limits.
from src.websocket_streams.live.terminal.byte_history import ByteHistory  # Terminal sessions keep raw output bytes.
from src.websocket_streams.live.terminal.gateway import TerminalRunner  # A shell runner receives the queued keys.
from src.websocket_streams.live.terminal.input_queue import TerminalInput  # Early keys wait for the first output.
from src.websocket_streams.live.terminal.state import TerminalState  # One terminal state for each terminal session.
from src.websocket_streams.live.transport.endpoint import MistStreamEndpoint, TransportProfile  # Connection values.

logger = logging.getLogger(__name__)  # Keep manager records under this module.


class StreamRunner(Protocol):
    """The behavior that each stream runner exposes to the manager."""

    def start(self) -> None:
        """Start stream work and return at once."""

    def stop(self) -> None:
        """Request stream stop and return at once."""


class RunnerFactoryLike(Protocol):
    """The runner factory behavior that the manager needs."""

    def build(self, request: StartRequest, sink: SessionSink) -> StreamRunner:
        """Build a runner for one checked request.

        Args:
            request: The checked start request.
            sink: The session sink.

        Returns:
            A stream runner.
        """


class RunnerFactory:
    """Build the stream runners for checked requests."""

    _filter_installed = False  # Install the Mist SDK shell redaction filter one time.
    _filter_lock = threading.Lock()  # Several apps can build at the same time in tests.

    def __init__(self, apisession: object, profile: TransportProfile | None = None) -> None:
        """Build one runner factory.

        Args:
            apisession: The Mist API session.
            profile: The transport values, or None for the production values. Tests use a loopback profile.
        """
        self._apisession = apisession  # Each runner sends its REST trigger with the same session.
        self._endpoint = MistStreamEndpoint(apisession, profile)  # One endpoint builds each connection value.

    @staticmethod
    def is_screen(request: StartRequest) -> bool:
        """Return whether a request runs a full-screen device command.

        Args:
            request: The checked start request.

        Returns:
            True for Top and Monitor Traffic, which send screen updates.
        """
        definition = request.definition  # The catalog marks each screen command.
        return isinstance(definition, UtilityDefinition) and definition.output == "screen"  # Catalog decides.

    def build(self, request: StartRequest, sink: SessionSink) -> StreamRunner:
        """Build a runner for one checked request.

        Args:
            request: The checked start request.
            sink: The session sink.

        Returns:
            The matching stream runner.
        """
        logger.info("Building WebSockets runner for key %s", request.key)  # Log before building a runner.
        if request.kind == "channel":  # Channel streams read the Mist stream connection.
            runner: StreamRunner = ChannelStreamRunner(self._endpoint, request, sink)  # Build a channel runner.
        elif request.kind == "shell":  # A shell is a two-way terminal.
            self._install_shell_filter()  # The REST layer of the SDK can log the shell address.
            runner = ShellRunner(self._apisession, self._endpoint, request, sink)  # Build a shell runner.
        elif self.is_screen(request):  # Top and Monitor Traffic are read-only terminals.
            self._install_shell_filter()  # The screen trigger answer holds a WebSocket address too.
            runner = ScreenRunner(self._apisession, self._endpoint, request, sink)  # Build a screen runner.
        else:  # All other utilities send lines or packets on the stream connection.
            runner = UtilityRunner(self._apisession, self._endpoint, request, sink)  # Build a utility runner.
        logger.debug("Built WebSockets runner for key %s", request.key)  # Log safe metadata only.
        return runner  # The manager starts it outside the lock.

    @classmethod
    def _install_shell_filter(cls) -> None:
        """Install the shell address filter on the Mist SDK logger."""
        with cls._filter_lock:  # Several threads can start the first shell.
            if cls._filter_installed:  # The filter is already active.
                return  # No duplicate filters are needed.
            logging.getLogger("mistapi").addFilter(ShellAddressFilter())  # Redact shell WebSocket addresses.
            cls._filter_installed = True  # Remember the one-time install.


class StreamSessionManager:
    """Own and bound all WebSockets tab sessions in one portal process."""

    ENDED_KEEP_COUNT = 5  # Research decision: keep 5 ended sessions at most, so their buffers stay bounded.
    ENDED_KEEP_SECONDS = 600.0  # Research decision: keep an ended session 10 minutes for a read or a download.

    def __init__(
        self, settings: StreamSettings, runner_factory: RunnerFactoryLike, clock: Callable[[], float] | None = None
    ) -> None:
        """Build one empty manager.

        Args:
            settings: The session limits.
            runner_factory: The factory that builds runners.
            clock: The monotonic clock, or None for ``time.monotonic``.
        """
        self._settings = settings  # Limits are immutable after build.
        self._runner_factory = runner_factory  # Tests inject a fake factory.
        self._clock = time.monotonic if clock is None else clock  # A fake clock keeps tests fast.
        self._lock = threading.RLock()  # Web requests and reaper share the session map.
        self._sessions: dict[str, StreamSession] = {}  # Session identifier to session.
        self._reaper_stop = threading.Event()  # Shutdown uses this event.
        self._reaper_thread: threading.Thread | None = None  # The reaper starts lazily.
        self._shutdown = False  # Shutdown is safe to repeat.

    def start(self, request: StartRequest) -> dict[str, object]:
        """Start a checked stream request.

        Args:
            request: The checked start request.

        Returns:
            The new session payload.

        Raises:
            StreamRequestError: When the live session limit is reached.
        """
        logger.info("Starting WebSockets session for key %s", request.key)  # Log before changing state.
        with self._lock:  # The live limit and insert must be atomic.
            if self.live_count() >= self._settings.max_sessions:  # The process reached its live limit.
                live = [
                    session.request.title for session in self._sessions.values() if session.live
                ]  # Give live titles.
                raise StreamRequestError(
                    "limit_reached", "The live session limit was reached.", {"live": live}
                )  # Refuse before SDK work.
            session = self._new_session(request)  # Build the session and runner.
            self._sessions[session.session_id] = session  # Make it visible before the runner sends output.
            self._audit_start(request)  # Log risky starts at WARNING level.
        runner = cast(StreamRunner, session.runner)  # The runner is set by _new_session.
        runner.start()  # Fakes and concrete runners expose start.
        logger.debug("Started WebSockets session %s", session.session_id)  # Log after runner start.
        return session.payload()  # Return the public session payload.

    def list_payload(self) -> dict[str, object]:
        """Return every held session, newest first."""
        logger.debug("Building WebSockets session list payload")  # Debug level: the page refreshes the list often.
        with self._lock:  # The session map can change during a request.
            sessions = sorted(
                self._sessions.values(), key=lambda item: item.started_mono, reverse=True
            )  # Newest first.
            payloads = [session.payload() for session in sessions]  # Build public session payloads.
            live_count = sum(1 for session in sessions if session.live)  # Count live sessions.
        logger.debug("Built WebSockets session list payload with %s session(s)", len(payloads))  # Log result count.
        return {
            "sessions": payloads,
            "limits": {"max_sessions": self._settings.max_sessions, "live_count": live_count},
        }  # Contract shape.

    def read(self, session_id: str, after: int, limit: int) -> MessagePage:
        """Read messages after a sequence number.

        Args:
            session_id: The session identifier.
            after: The newest sequence number that the page has.
            limit: The requested message count.

        Returns:
            The read answer, with the records of the returned messages.
        """
        session = self.session(session_id)  # Raise not_found when absent.
        session.mark_read()  # Prevent an idle stop after a successful read.
        count = min(500, max(1, limit))  # The contract clamps the limit to 1 through 500.
        records, first_seq, gap = session.read_records(max(0, after), count)  # Copy the records under the lock.
        next_after = records[-1].seq if records else after  # Keep the cursor stable when no message exists.
        logger.debug("Read %s WebSockets messages for session %s", len(records), session_id)  # Log the count only.
        return MessagePage(session.payload(), records, next_after, first_seq, gap)  # The route joins the text later.

    def stop(self, session_id: str, reason: str = "The operator stopped the session.") -> dict[str, object]:
        """Request a session stop.

        Args:
            session_id: The session identifier.
            reason: The stop reason.

        Returns:
            The session payload.
        """
        session = self.session(session_id)  # Raise not_found when absent.
        changed = session.request_stop(reason)  # Stop is safe to repeat.
        if changed and session.runner is not None:  # A new stop needs a runner call.
            cast(StreamRunner, session.runner).stop()  # Runner stop returns at once.
        return session.payload()  # Return the current public state.

    def session(self, session_id: str) -> StreamSession:
        """Return one session or raise a contract error.

        Args:
            session_id: The session identifier.

        Returns:
            The matching session. The terminal gateway reads and writes through it.

        Raises:
            StreamRequestError: The identifier is unknown.
        """
        with self._lock:  # The session map can change during a request.
            session = self._sessions.get(session_id)  # Check the map.
        if session is None:  # The identifier is unknown.
            raise StreamRequestError("not_found", "The session was not found.")  # Contract error.
        return session  # The caller can operate on the session.

    def delete(self, session_id: str) -> None:
        """Delete an ended session.

        Args:
            session_id: The session identifier.
        """
        with self._lock:  # The session map changes.
            session = self._sessions.get(session_id)  # Check existence first.
            if session is None:  # The identifier is unknown.
                raise StreamRequestError("not_found", "The session was not found.")  # Contract error.
            if session.live:  # Live sessions cannot be removed from the list.
                raise StreamRequestError("session_live", "Stop the session before you delete it.")  # Contract error.
            del self._sessions[session_id]  # Remove the ended session.

    def download(self, session_id: str) -> tuple[str, Iterator[str]]:
        """Return a JSON Lines download for one session.

        Args:
            session_id: The session identifier.

        Returns:
            The file name and an iterator of lines.
        """
        session = self.session(session_id)  # Raise not_found when absent.
        stamp = session.started_at.replace("-", "").replace(":", "")  # Build a file-safe UTC stamp.
        filename = f"{session.request.key}-{stamp}.jsonl"  # Include the key and start time.
        lines = (
            "".join((*record.json_parts(), "\n")) for record in session.snapshot_records()
        )  # Python copies the record list now and formats one line for each download step.
        return filename, lines  # The blueprint streams these lines.

    def live_count(self) -> int:
        """Return the count of live sessions."""
        return sum(1 for session in self._sessions.values() if session.live)  # The caller holds the lock when needed.

    def start_reaper(self) -> None:
        """Start the background reaper one time."""
        with self._lock:  # Several requests can initialize services.
            if self._reaper_thread is not None:  # The reaper already exists.
                return  # Starting twice is harmless.
            logger.info("Starting WebSockets session reaper")  # Log before thread start.
            self._reaper_thread = threading.Thread(
                target=self._reaper_loop, name="ws-session-reaper", daemon=True
            )  # The reaper must not block exit.
            self._reaper_thread.start()  # Start the daemon thread.
            logger.debug("Started WebSockets session reaper")  # Log after thread start.

    def stop_all(self, reason: str) -> int:
        """Stop every live session.

        Args:
            reason: The stop reason.

        Returns:
            The count of sessions that received a stop request.
        """
        logger.info("Stopping all WebSockets sessions")  # Log before stopping sessions.
        with self._lock:  # Freeze the live session list.
            sessions = [session for session in self._sessions.values() if session.live]  # Stop only live sessions.
        for session in sessions:  # Stop outside the manager lock.
            self.stop(session.session_id, reason)  # Reuse the normal stop path.
        logger.debug("Requested stop for %s WebSockets session(s)", len(sessions))  # Log result count.
        return len(sessions)  # Shutdown reports this count.

    def shutdown(self) -> None:
        """Stop every stream and stop the reaper."""
        with self._lock:  # Shutdown is safe to call twice.
            if self._shutdown:  # A previous call already ran.
                return  # Nothing remains to do.
            self._shutdown = True  # Block future shutdown work.
        self.stop_all("The portal is shutting down.")  # Stop every live session.
        self._reaper_stop.set()  # Ask the reaper loop to exit.
        thread = self._reaper_thread  # Copy the thread reference.
        if thread is not None:  # The reaper may never have started.
            thread.join(timeout=5.0)  # Bound shutdown wait time.

    def reap_once(self) -> None:
        """Run one reaper pass for tests and the background loop."""
        logger.debug("Running WebSockets session reaper pass")  # Debug level: the reaper runs every few seconds.
        with self._lock:  # Build a stable list for the pass.
            sessions = list(self._sessions.values())  # Copy the sessions for decisions.
        for session in sessions:  # Stop and prune without holding the main lock.
            self._reap_session(session)  # Apply idle, life, and stopping rules.
        self._prune_ended()  # Apply ended-session retention.
        logger.debug("Completed WebSockets session reaper pass")  # Log after the pass.

    def _new_session(self, request: StartRequest) -> StreamSession:
        """Build a session and attach its runner.

        Args:
            request: The checked start request.

        Returns:
            The new stream session.
        """
        session_id = secrets.token_hex(8)  # The contract requires 16 hexadecimal characters.
        buffer = MessageBuffer(
            self._settings.buffer_messages, self._settings.buffer_bytes
        )  # Each session owns one buffer.
        terminal = self._new_terminal(request)  # Shell and screen sessions keep raw output bytes.
        session = StreamSession(session_id, request, buffer, self._clock, terminal)  # Build the sink first.
        session.runner = self._runner_factory.build(request, session)  # The runner writes to this session.
        self._bind_input(session)  # Early keys wait in the queue and go to this runner after the first output.
        return session  # The caller stores and starts it.

    def _new_terminal(self, request: StartRequest) -> TerminalState | None:
        """Build the terminal state of a shell session or a screen session.

        Args:
            request: The checked start request.

        Returns:
            The terminal state, or None for a session that shows a message list.
        """
        shell = request.kind == "shell"  # Only a shell accepts keys from the page.
        if not shell and not RunnerFactory.is_screen(request):  # Lines and packets use the message list.
            return None  # The session keeps no byte history.
        logger.debug("Building the terminal state for key %s", request.key)  # Log before the build.
        history = ByteHistory(self._settings.terminal_history_bytes)  # The setting bounds the kept bytes.
        keys = TerminalInput(self._clock) if shell else None  # A screen command is read-only.
        life = float(self._settings.max_stream_seconds)  # The reaper stops the session at this age.
        expires = datetime.now(UTC).replace(microsecond=0) + timedelta(seconds=life)  # The page warns before it.
        expires_at = expires.isoformat().replace("+00:00", "Z")  # Use the public UTC format of the payload.
        return TerminalState(history, keys, self._clock() + life, expires_at)  # One state for the session.

    @staticmethod
    def _bind_input(session: StreamSession) -> None:
        """Connect the input queue of a shell session to its runner.

        Args:
            session: The new session with its runner.
        """
        terminal = session.terminal  # Only terminal sessions have an input queue.
        runner = session.runner  # The runner sends the keys to the device.
        if terminal is None or terminal.input is None or not isinstance(runner, TerminalRunner):  # No keys.
            return  # Message-list sessions and screen sessions accept no keys.
        terminal.input.bind(runner.send_input)  # The queue sends each released text through the runner.
        logger.debug("Bound the terminal input of session %s", session.session_id)  # Log after the bind.

    def _audit_start(self, request: StartRequest) -> None:
        """Write the required audit line for risky starts.

        Args:
            request: The checked start request.
        """
        definition = request.definition  # The safety class lives on utility definitions.
        if not isinstance(definition, UtilityDefinition) or definition.safety not in {
            Safety.CHANGE,
            Safety.SHELL,
        }:  # Only risky starts need WARNING.
            return  # Read and capture starts use normal logs.
        logger.warning(
            "WebSockets audit start key=%s device=%s device_id=%s site_id=%s",
            request.key,
            request.device_name or "unknown",
            request.target("device_id"),
            request.target("site_id"),
        )  # Never include shell input or secrets.

    def _reap_session(self, session: StreamSession) -> None:
        """Apply stop rules to one session.

        Args:
            session: The session to inspect.
        """
        now = self._clock()  # Use one time value for this session.
        if session.live and now - session.last_read_mono > self._settings.idle_seconds:  # The page stopped reading.
            self.stop(session.session_id, "The session stopped because no page read it.")  # Stop idle sessions.
        if (
            session.live and now - session.started_mono > self._settings.max_stream_seconds
        ):  # The session lived too long.
            self.stop(session.session_id, "The session reached its maximum life.")  # Stop old sessions.
        stopping_at = (
            session.stopping_mono if session.stopping_mono is not None else now
        )  # Stopping age starts at stop request.
        if session.state == SessionState.STOPPING and now - stopping_at > 15.0:  # A stuck stop must end.
            session.finish(
                SessionState.STOPPED, session.reason or "The session stopped."
            )  # Mark stuck stopping as stopped.

    def _prune_ended(self) -> None:
        """Remove ended sessions after 10 minutes, and keep 5 ended sessions at most.

        Why:
            Issue #3551, task T075. The old rule kept the 5 newest ended
            sessions with no time limit, and it kept any count of older ended
            sessions for 10 minutes. Each ended session holds a full buffer,
            so a fast start and stop cycle grew the memory with no bound.
        """
        logger.debug("Pruning ended WebSockets sessions")  # Debug level: the reaper runs every five seconds.
        with self._lock:  # The session map changes.
            ended = [
                session for session in self._sessions.values() if not session.live
            ]  # Only ended sessions are pruned.
            ended.sort(
                key=lambda item: item.ended_mono or item.started_mono, reverse=True
            )  # The newest ended session comes first.
            now = self._clock()  # Age decisions use the fake clock in tests.
            removed = [
                session.session_id
                for position, session in enumerate(ended)
                if position >= self.ENDED_KEEP_COUNT
                or now - (session.ended_mono or session.started_mono) > self.ENDED_KEEP_SECONDS
            ]  # A session past the count limit or past the age limit leaves.
            for session_id in removed:  # Release each removed buffer.
                self._sessions.pop(session_id, None)  # The buffer memory returns to the process.
        logger.debug("Pruned %s ended WebSockets sessions", len(removed))  # Log the result count.

    def _reaper_loop(self) -> None:
        """Run the reaper until shutdown."""
        while not self._reaper_stop.wait(5.0):  # The contract sets a five-second cadence.
            self.reap_once()  # Apply all stop and prune rules.
