"""Own session start, lookup, read, stop, delete, and export operations."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Session actions use the shared structured logger.
import threading  # Web requests share the session map.
from collections.abc import Iterator  # Downloads return a lazy line iterator.
from typing import cast  # Stored runner objects satisfy the manager protocol.

from src.mist.realtime.websocket_streams.catalog.model import (
    Safety,
    UtilityDefinition,
)  # Audit starts use utility safety.
from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Routes use stable contract errors.
from src.mist.realtime.websocket_streams.intake.start_request.models import (
    StartRequest,
)  # Starts receive checked requests.
from src.mist.realtime.websocket_streams.live.sessions.buffer.page import (
    MessagePage,
)  # Reads return joined response records.
from src.mist.realtime.websocket_streams.live.sessions.manager.contracts import (
    ManagerAttributes,
    StreamRunner,
)  # Shared state and runner methods.
from src.mist.realtime.websocket_streams.live.sessions.manager.factory import SessionBuilder  # Build complete sessions.
from src.mist.realtime.websocket_streams.live.sessions.record.session import (
    StreamSession,
)  # The manager map owns sessions.
from src.mist.realtime.websocket_streams.live.sessions.settings import StreamSettings  # Payloads report session limits.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # T072.


class SessionStarter(ManagerAttributes):
    """Own atomic session admission and runner start."""

    _lock: threading.RLock  # Admission and insertion share the manager lock.
    _sessions: dict[str, StreamSession]  # The manager stores each visible session.
    _settings: StreamSettings  # Admission uses the configured live limit.
    _builder: SessionBuilder  # Construction stays outside this operation class.
    _logger: StructuredTransportLogger  # All records cross the T072 boundary.

    def start(self, request: StartRequest) -> dict[str, object]:
        """Start one checked request under the live session limit."""
        self._logger.emit(logging.INFO, "session_start_begin", {"action": request.key})  # Log safe request key only.
        with self._lock:  # Admission and insertion must be atomic.
            self._check_limit()  # Refuse before any SDK or transport work.
            session = self._builder.build(request)  # Build the session and its stopped runner.
            self._sessions[session.session_id] = session  # Make callbacks able to find the session.
            self._audit_start(request)  # Record risky starts without identifiers or content.
        cast(StreamRunner, session.runner).start()  # Start outside the manager lock.
        self._logger.emit(logging.DEBUG, "session_start_complete", {"status": "started"})  # Confirm safely.
        return session.payload()  # Preserve the public start response.

    def _check_limit(self) -> None:
        """Raise the stable limit error when all live slots are used."""
        live = [session.request.title for session in self._sessions.values() if session.live]  # Preserve page help.
        if len(live) >= self._settings.max_sessions:  # Compare one stable live snapshot.
            raise StreamRequestError(
                "limit_reached", "The live session limit was reached.", {"live": live}
            )  # Contract.

    def _audit_start(self, request: StartRequest) -> None:
        """Write one bounded audit event for change and shell starts."""
        definition = request.definition  # Utility definitions hold their safety class.
        if isinstance(definition, UtilityDefinition) and definition.safety in {
            Safety.CHANGE,
            Safety.SHELL,
        }:  # Read and capture starts need no warning audit event.
            fields = {"action": request.key, "status": definition.safety.value}  # Use bounded safe values only.
            self._logger.emit(logging.WARNING, "session_audit_start", fields)  # Omit device data and shell content.


class SessionAccess(ManagerAttributes):
    """Own list, read, stop, lookup, and delete operations."""

    _lock: threading.RLock  # The session map can change during web requests.
    _sessions: dict[str, StreamSession]  # Public operations resolve sessions here.
    _settings: StreamSettings  # List payloads report the configured limit.
    _logger: StructuredTransportLogger  # All records cross the T072 boundary.

    def list_payload(self) -> dict[str, object]:
        """Return held sessions from newest to oldest."""
        with self._lock:  # Build one stable list snapshot.
            sessions = sorted(
                self._sessions.values(), key=lambda item: item.started_mono, reverse=True
            )  # Newest first.
            payloads = [session.payload() for session in sessions]  # Build public records under the map lock.
            live_count = sum(session.live for session in sessions)  # Count current live sessions.
        limits = {"max_sessions": self._settings.max_sessions, "live_count": live_count}  # Preserve contract fields.
        return {"sessions": payloads, "limits": limits}  # Return the stable list response.

    def read(self, session_id: str, after: int, limit: int) -> MessagePage:
        """Return bounded messages after one cursor."""
        session = self.session(session_id)  # Raise the stable not-found error when absent.
        session.mark_read()  # Prevent idle cleanup after a successful read.
        count = min(500, max(1, limit))  # Preserve the 1 through 500 request clamp.
        records, first_seq, gap = session.read_records(max(0, after), count)  # Copy under the session lock.
        next_after = records[-1].seq if records else after  # Keep the cursor stable when no record exists.
        return MessagePage(session.payload(), records, next_after, first_seq, gap)  # Preserve response shape.

    def stop(self, session_id: str, reason: str = "The operator stopped the session.") -> dict[str, object]:
        """Request one session stop and return current state."""
        session = self.session(session_id)  # Raise the stable not-found error when absent.
        session.request_stop(reason)  # Preserve the first stop reason and idempotent state change.
        if session.live and session.runner is not None:  # Each live request must wake the runner.
            cast(StreamRunner, session.runner).stop()  # Concrete and fake runners stop without blocking.
        return session.payload()  # Return the current public state.

    def session(self, session_id: str) -> StreamSession:
        """Return one session or raise the stable contract error."""
        with self._lock:  # Cleanup can remove ended sessions concurrently.
            session = self._sessions.get(session_id)  # Resolve from one stable map access.
        if session is None:  # Unknown and pruned sessions use the same contract error.
            raise StreamRequestError("not_found", "The session was not found.")  # Preserve route behavior.
        return session  # Terminal and service callers use the concrete record.

    def delete(self, session_id: str) -> None:
        """Delete one ended session."""
        with self._lock:  # Validation and removal must be atomic.
            session = self._sessions.get(session_id)  # Resolve before any state check.
            if session is None:  # Unknown sessions use the stable route error.
                raise StreamRequestError("not_found", "The session was not found.")  # Preserve contract code.
            if session.live:  # Live sessions cannot disappear from the portal.
                raise StreamRequestError("session_live", "Stop the session before you delete it.")  # Preserve contract.
            del self._sessions[session_id]  # Release the ended session and its buffers.


class SessionExport(ManagerAttributes):
    """Own downloads and live session counts."""

    _sessions: dict[str, StreamSession]  # Live counts read the manager map.

    def download(self, session_id: str) -> tuple[str, Iterator[str]]:
        """Return a JSON Lines download for one session."""
        session = self.session(session_id)  # Raise the stable not-found error when absent.
        stamp = session.started_at.replace("-", "").replace(":", "")  # Build a file-safe UTC stamp.
        filename = f"{session.request.key}-{stamp}.jsonl"  # Preserve key and start time in the name.
        lines = (
            "".join((*record.json_parts(), "\n")) for record in session.snapshot_records()
        )  # Copy now, format later.
        return filename, lines  # Let the web response stream each compact line.

    def live_count(self) -> int:
        """Return the current live session count."""
        return sum(session.live for session in self._sessions.values())  # Callers hold the map lock when needed.
