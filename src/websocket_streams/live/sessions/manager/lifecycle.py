"""Own session cleanup, background reaping, and manager construction."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Cleanup actions use structured JSON records.
import threading  # Web requests and the reaper share manager state.
import time  # Production managers use the monotonic clock.
from collections.abc import Callable  # Tests inject a fake clock.

from src.websocket_streams.live.sessions.manager.contracts import (
    ManagerAttributes,
    RunnerFactoryLike,
)  # Shared state and runner factory behavior.
from src.websocket_streams.live.sessions.manager.factory import SessionBuilder  # Build complete sessions.
from src.websocket_streams.live.sessions.manager.operations import SessionAccess, SessionExport, SessionStarter  # API.
from src.websocket_streams.live.sessions.record.session import StreamSession  # Cleanup inspects concrete state.
from src.websocket_streams.live.sessions.record.state import SessionState  # Stuck stops end in a stable state.
from src.websocket_streams.live.sessions.settings import StreamSettings  # Cleanup uses configured time limits.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import StructuredTransportLogger  # T072.


class SessionRetention(ManagerAttributes):
    """Apply idle, life, stuck-stop, count, and age cleanup rules."""

    ENDED_KEEP_COUNT = 5  # Preserve the bounded count of ended session buffers.
    ENDED_KEEP_SECONDS = 600.0  # Preserve ten minutes of ended session availability.

    def _reap_session(self, session: StreamSession) -> None:
        """Apply all stop rules to one session."""
        now = self._clock()  # Use one time value for each rule.
        if session.live and now - session.last_read_mono > self._settings.idle_seconds:  # The page stopped reading.
            self.stop(session.session_id, "The session stopped because no page read it.")  # Preserve idle reason.
        if session.live and now - session.started_mono > self._settings.max_stream_seconds:  # Life limit expired.
            self.stop(session.session_id, "The session reached its maximum life.")  # Preserve life reason.
        stopping_at = session.stopping_mono if session.stopping_mono is not None else now  # Bound stop age.
        if session.state == SessionState.STOPPING and now - stopping_at > 15.0:  # The runner did not finish.
            session.finish(SessionState.STOPPED, session.reason or "The session stopped.")  # Preserve stop cause.

    def _prune_ended(self) -> None:
        """Keep five recent ended sessions for at most ten minutes."""
        with self._lock:  # Cleanup changes the shared session map.
            ended = [session for session in self._sessions.values() if not session.live]  # Ignore live sessions.
            ended.sort(key=lambda item: item.ended_mono or item.started_mono, reverse=True)  # Newest first.
            removed = self._expired_session_ids(ended)  # Apply count and age bounds.
            for session_id in removed:  # Release each ended session buffer.
                self._sessions.pop(session_id, None)  # Another delete can make removal harmless.
        self._logger.emit(logging.DEBUG, "session_prune_complete", {"count": len(removed)})  # Log count only.

    def _expired_session_ids(self, ended: list[StreamSession]) -> list[str]:
        """Return ended session identifiers that exceed retention bounds."""
        now = self._clock()  # Use one clock value for a stable decision.
        return [
            session.session_id
            for position, session in enumerate(ended)
            if position >= self.ENDED_KEEP_COUNT
            or now - (session.ended_mono or session.started_mono) > self.ENDED_KEEP_SECONDS
        ]  # Preserve exact edge and newest-first behavior.


class SessionReaper(ManagerAttributes):
    """Own the background cleanup thread and manager shutdown."""

    def start_reaper(self) -> None:
        """Start the background reaper one time."""
        with self._lock:  # Several requests can initialize services together.
            if self._reaper_thread is not None:  # The background thread already exists.
                return  # Starting twice remains harmless.
            self._logger.emit(logging.INFO, "session_reaper_start")  # Log before thread creation.
            self._reaper_thread = threading.Thread(target=self._reaper_loop, name="ws-session-reaper", daemon=True)
            self._reaper_thread.start()  # Start the daemon after storing its reference.
        self._logger.emit(logging.DEBUG, "session_reaper_ready", {"status": "started"})  # Confirm safely.

    def stop_all(self, reason: str) -> int:
        """Request stop for every live session."""
        with self._lock:  # Copy one stable live list.
            sessions = [session for session in self._sessions.values() if session.live]  # Stop live sessions only.
        for session in sessions:  # Stop outside the manager map lock.
            self.stop(session.session_id, reason)  # Reuse normal stop semantics.
        self._logger.emit(logging.DEBUG, "session_stop_all_complete", {"count": len(sessions)})  # Log count only.
        return len(sessions)  # Shutdown and tests use the exact stop count.

    def shutdown(self) -> None:
        """Stop all streams and stop the background reaper."""
        with self._lock:  # Shutdown can run from more than one owner.
            if self._shutdown:  # A prior shutdown already started.
                return  # Repeat shutdown remains safe.
            self._shutdown = True  # Block duplicate shutdown work.
        self.stop_all("The portal is shutting down.")  # Preserve the existing shutdown reason.
        self._reaper_stop.set()  # Wake the background wait.
        if self._reaper_thread is not None:  # The reaper might never have started.
            self._reaper_thread.join(timeout=5.0)  # Bound shutdown wait time.

    def reap_once(self) -> None:
        """Run one cleanup pass."""
        with self._lock:  # Copy sessions before stop calls change state.
            sessions = list(self._sessions.values())  # Build one stable pass list.
        for session in sessions:  # Apply stop rules outside the map lock.
            self._reap_session(session)  # Preserve idle, life, and stuck-stop behavior.
        self._prune_ended()  # Apply ended-session retention after stop rules.

    def _reaper_loop(self) -> None:
        """Run cleanup every five seconds until shutdown."""
        while not self._reaper_stop.wait(5.0):  # Preserve the existing cleanup cadence.
            self.reap_once()  # Apply one complete cleanup pass.


class StreamSessionManager(SessionStarter, SessionAccess, SessionExport, SessionRetention, SessionReaper):
    """Own all WebSocket sessions in one portal process."""

    def __init__(
        self, settings: StreamSettings, runner_factory: RunnerFactoryLike, clock: Callable[[], float] | None = None
    ) -> None:
        """Build one empty thread-safe manager."""
        self._settings = settings  # Limits stay immutable for this manager.
        self._clock = time.monotonic if clock is None else clock  # Tests can supply deterministic time.
        self._lock = threading.RLock()  # Web requests and cleanup share the session map.
        self._sessions: dict[str, StreamSession] = {}  # Map public identifiers to concrete sessions.
        self._builder = SessionBuilder(settings, runner_factory, self._clock)  # Build sessions and bind terminals.
        self._logger = StructuredTransportLogger(logging.getLogger(__name__))  # Apply the T072 boundary.
        self._reaper_stop = threading.Event()  # Shutdown wakes the cleanup wait.
        self._reaper_thread: threading.Thread | None = None  # Cleanup starts lazily.
        self._shutdown = False  # Repeat shutdown remains safe.
