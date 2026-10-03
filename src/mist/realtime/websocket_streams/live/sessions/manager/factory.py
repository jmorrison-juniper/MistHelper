"""Build runners, terminal state, and complete stream sessions."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Construction actions use structured JSON records.
import secrets  # Public session identifiers must be hard to guess.
import threading  # Several apps can install the SDK filter together.
from collections.abc import Callable  # Tests inject a monotonic clock.
from datetime import UTC, datetime, timedelta  # Terminal expiry uses public UTC text.

from src.mist.realtime.websocket_streams.catalog.model import (
    UtilityDefinition,
)  # Screen selection follows catalog output.
from src.mist.realtime.websocket_streams.intake.start_request.models import (
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
)  # Construction values.
from src.mist.realtime.websocket_streams.live.sessions.settings import StreamSettings  # Settings define all limits.
from src.mist.realtime.websocket_streams.live.terminal.byte_history import (
    ByteHistory,
)  # Terminal sessions keep exact bytes.
from src.mist.realtime.websocket_streams.live.terminal.gateway import (
    TerminalRunner,
)  # Writable terminals expose input methods.
from src.mist.realtime.websocket_streams.live.terminal.input_queue import TerminalInput  # Early shell keys wait here.
from src.mist.realtime.websocket_streams.live.terminal.state.terminal_state import (
    TerminalState,
)  # Hold terminal session state.
from src.mist.realtime.websocket_streams.live.transport.endpoint import (
    MistStreamEndpoint,
    TransportProfile,
)  # Connection values.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # T072.


class RunnerFactory:
    """Build the matching runner for each checked request."""

    _filter_installed = False  # Install the Mist SDK shell redaction filter one time.
    _filter_lock = threading.Lock()  # Protect the one-time filter state.

    def __init__(self, apisession: object, profile: TransportProfile | None = None) -> None:
        """Build one factory for a Mist API session."""
        self._apisession = apisession  # Utility and shell triggers use the same API session.
        self._endpoint = MistStreamEndpoint(apisession, profile)  # Build owned transport connection values.
        self._logger = StructuredTransportLogger(logging.getLogger(__name__))  # Use bounded content-free records.

    @staticmethod
    def is_screen(request: StartRequest) -> bool:
        """Return whether a request uses a full-screen utility runner."""
        definition = request.definition  # The catalog owns utility output mode.
        return isinstance(definition, UtilityDefinition) and definition.output == "screen"  # Select screen output only.

    def build(self, request: StartRequest, sink: SessionSink) -> StreamRunner:
        """Build one runner without starting it."""
        self._logger.emit(logging.INFO, "session_runner_build_start", {"action": request.key})  # Log safe key only.
        runner = self._select(request, sink)  # Select the concrete runner by checked request kind.
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

    def _select(self, request: StartRequest, sink: SessionSink) -> StreamRunner:
        """Return the concrete runner for one request."""
        if request.kind == "channel":  # Channel requests use the owned stream transport.
            return ChannelStreamRunner(self._endpoint, request, sink)  # Build a channel runner.
        if request.kind == "shell":  # Shell requests use a writable terminal runner.
            self._install_shell_filter()  # Protect SDK logs before the REST trigger.
            return ShellRunner(self._apisession, self._endpoint, request, sink)  # Build a shell runner.
        if self.is_screen(request):  # Screen utilities use a read-only terminal runner.
            self._install_shell_filter()  # Protect SDK logs before the REST trigger.
            return ScreenRunner(self._apisession, self._endpoint, request, sink)  # Build a screen runner.
        return UtilityRunner(self._apisession, self._endpoint, request, sink)  # Build a line or packet runner.


class TerminalSessionBuilder:
    """Build terminal state for shell and screen sessions."""

    def __init__(self, settings: StreamSettings, clock: Callable[[], float]) -> None:
        """Store terminal limits and the injected monotonic clock."""
        self._settings, self._clock = settings, clock  # Use shared immutable settings and deterministic time.

    def build(self, request: StartRequest) -> TerminalState | None:
        """Return terminal state for shell and screen requests."""
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
