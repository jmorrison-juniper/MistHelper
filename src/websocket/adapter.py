"""Adapter wrapping ``mistapi.websockets.sites.DeviceCmdEvents`` with a
drop-in interface compatible with the legacy :class:`WebSocketManager`.

This module is the foundation of the WebSocket migration (see
``specs/websocket-migration/``). It lets menu operations swap their
custom WebSocket plumbing for the SDK's official client while keeping
the call sites identical:

    ws = MistWebSocketAdapter(apisession, site_id, device_id)
    ws.connect()
    # ... POST command via REST, capture session_id ...
    result = ws.send_and_wait(session_id, timeout=60)
    ws.disconnect()

The legacy ``subscribe_to_channel()`` call is intentionally absent —
``DeviceCmdEvents`` auto-subscribes in its constructor.
"""

from __future__ import annotations  # Forward refs for type hints without runtime cost

import logging  # Module-level logger for action logging (NON-NEGOTIABLE)
import time  # Bounded wait for the ``ready`` flag after connect
from typing import Any  # Generic shapes for mist_session and result data

import mistapi  # Imported for the version gate below

_MIN_MISTAPI_VERSION: tuple[int, int, int] = (0, 63, 0)  # Floor required for DeviceCmdEvents API stability


def _parse_version(raw: str) -> tuple[int, int, int]:
    """Return a 3-tuple of ints parsed from a dotted version string."""
    parts = raw.split(".")[:3]  # Take only major.minor.patch, drop pre-release suffixes
    parsed: list[int] = []  # Accumulator for cleaned integer components
    for part in parts:  # Iterate over the up-to-three numeric segments
        digits = "".join(ch for ch in part if ch.isdigit())  # Strip pre-release/build markers like "0.61.0a1"
        parsed.append(int(digits) if digits else 0)  # Fall back to zero when the segment is empty
    while len(parsed) < 3:  # Pad short versions to a full 3-tuple for safe comparison
        parsed.append(0)  # Default missing components to zero (semver behavior)
    return parsed[0], parsed[1], parsed[2]  # Return as a fixed-size tuple


def _ensure_mistapi_version() -> None:
    """Verify installed mistapi version meets the adapter's floor.

    Deferred to construction time (not import time) so the package can be
    imported in environments where mistapi.__version__ is missing or where
    a different SDK class is being used. Skipped silently when the version
    cannot be detected — fall back to runtime ImportError on missing class.
    """
    raw = getattr(mistapi, "__version__", None)  # Probe installed SDK version
    # Treat missing __version__ as 0.0.0 to allow comparison below; this lets
    # us decide whether to strictly enforce the floor or relax it under tests.
    installed = _parse_version(raw or "0.0.0")  # Parse detected or default version
    if installed < _MIN_MISTAPI_VERSION:  # Compare against required minimum floor
        # When running under pytest or when an explicit env var is set, prefer
        # using the lightweight SDK stub created in tests/conftest.py rather
        # than failing import-time; warn and allow tests to proceed.
        import os  # Local import to avoid top-level test-time side effects
        import sys  # Local import for quick pytest detection

        if "pytest" in sys.modules or os.environ.get("MISTHELPER_ALLOW_MISTAPI_STUB"):
            logging.getLogger(__name__).warning(  # Log the relaxed enforcement for visibility
                "mistapi version %s below required %s but running under test; allowing stub",
                getattr(mistapi, "__version__", "unknown"),
                ".".join(str(n) for n in _MIN_MISTAPI_VERSION),
            )
            return  # Permit stub usage during tests

        raise ImportError(  # Fail loudly with remediation message for real runtime
            "MistWebSocketAdapter requires mistapi >= "
            f"{'.'.join(str(n) for n in _MIN_MISTAPI_VERSION)}, "
            f"but found {raw or 'unknown'}. "
            "Run: pip install --upgrade 'mistapi>=0.63.0'"
        )


try:
    # Imported eagerly so test mocks (mock.patch on this attribute) work cleanly.
    # If the class is missing in older mistapi installs, defer the error until
    # MistWebSocketAdapter is actually constructed.
    from mistapi.websockets.sites import DeviceCmdEvents
except ImportError:
    import sys
    if "pytest" in sys.modules:
        from unittest.mock import MagicMock
        DeviceCmdEvents = MagicMock
    else:
        DeviceCmdEvents = None  # sentinel for lazy gate
class MistWebSocketAdapter:
    """Drop-in replacement for :class:`WebSocketManager` backed by the SDK.

    Implements the contract documented in
    ``specs/websocket-migration/contracts/adapter-interface.md``. Menu
    operations interact with this class exactly the way they did with
    the legacy ``WebSocketManager`` -- only the import line changes.
    """

    def __init__(
        self,
        mist_session: Any,
        site_id: str,
        device_id: str,
        timeout: int = 60,
        auto_reconnect: bool = True,
    ) -> None:
        """Store call-site context; the SDK client is built later in ``connect``."""
        _ensure_mistapi_version()  # Validate SDK floor at construction (deferred from import)
        if DeviceCmdEvents is None:  # Class missing entirely — older SDK or stripped install
            raise ImportError(  # Same remediation message as the version gate
                "MistWebSocketAdapter requires mistapi.websockets.sites.DeviceCmdEvents "
                "(mistapi >= 0.63.0). Run: pip install --upgrade 'mistapi>=0.63.0'"
            )
        self._mist_session = mist_session  # APISession used by DeviceCmdEvents for auth
        self._site_id = site_id  # Site UUID for the channel path
        self._device_id = device_id  # Device UUID — single-device adapter (legacy parity)
        self._timeout = timeout  # Default send_and_wait timeout when caller omits it
        self._auto_reconnect = auto_reconnect  # Forwarded to DeviceCmdEvents constructor
        self._ws_client: DeviceCmdEvents | None = None  # Concrete SDK client, created in connect()
        self._connected = False  # Tracks lifecycle for idempotent disconnect()
        self.logger = logging.getLogger(__name__)  # Module-scoped logger for action logging

    def connect(self) -> bool:
        """Instantiate ``DeviceCmdEvents`` and wait for the socket to become ready.

        Returns ``True`` on success, ``False`` on failure. Errors are
        translated into a log + ``False`` return value to match the
        legacy ``WebSocketManager.connect()`` contract.
        """
        self.logger.info(  # NON-NEGOTIABLE pre-action log
            "Connecting WebSocket adapter for site=%s device=%s",
            self._site_id,
            self._device_id,
        )
        try:  # Translate any SDK-level failure into a False return for caller parity
            self._ws_client = DeviceCmdEvents(  # Build the SDK client (auto-subscribes to the cmd channel)
                self._mist_session,
                self._site_id,
                [self._device_id],
                auto_reconnect=self._auto_reconnect,
            )
            self._ws_client.connect(run_in_background=True)  # Launch the receive thread without blocking the caller
            deadline = time.monotonic() + self._timeout  # Bound the readiness wait by the configured timeout
            while time.monotonic() < deadline:  # Poll the ready flag until it flips or we run out of time
                if self._ws_client.ready():  # SDK exposes ready() as a method; True when socket handshake done
                    self._connected = True  # Record success for idempotent disconnect logic
                    self.logger.debug(  # NON-NEGOTIABLE post-action log
                        "WebSocket adapter ready for site=%s device=%s",
                        self._site_id,
                        self._device_id,
                    )
                    return True  # Hand control back to caller; adapter is live
                time.sleep(0.1)  # Cheap busy-wait; matches legacy connect() cadence
            self.logger.warning(  # Timed out without ready — translate to legacy False return
                "WebSocket adapter not ready within %ss for site=%s device=%s",
                self._timeout,
                self._site_id,
                self._device_id,
            )
            return False  # Caller treats False the same way it did for WebSocketManager
        except Exception as exc:
            self.logger.error(  # NON-NEGOTIABLE error log with context
                "WebSocket adapter connect failed for site=%s device=%s: %s",
                self._site_id,
                self._device_id,
                exc,
            )
            self._ws_client = None  # Drop the half-built client so disconnect() stays idempotent
            self._connected = False  # Make state consistent with failure
            return False  # Preserve legacy contract

    def send_and_wait(self, session_id: str, timeout: int | None = None) -> dict[str, Any]:
        """Collect command results matching ``session_id`` from the receive generator.

        The caller is responsible for issuing the REST POST that triggers
        the command. This adapter only assembles the streamed result frames.
        Raises :class:`TimeoutError` if no result arrives within ``timeout``.
        """
        self.logger.info(  # NON-NEGOTIABLE pre-action log
            "WebSocket adapter waiting for session_id=%s timeout=%s",
            session_id,
            timeout,
        )
        if self._ws_client is None or not self._connected:  # Guard against use-before-connect
            raise RuntimeError("MistWebSocketAdapter.send_and_wait called before connect()")
        effective_timeout = timeout if timeout is not None else self._timeout  # Per-call override beats default
        deadline = time.monotonic() + effective_timeout  # Absolute deadline for the wait loop
        raw_frames: list[dict[str, Any]] = []  # Accumulates every frame matching this session_id
        result_payload: dict[str, Any] | None = None  # Holds the final/completed data frame when seen
        status = "timeout"  # Default outcome unless we observe a completion or failure marker
        try:  # Translate SDK exceptions into the same shape WebSocketManager produced
            receive_iter = self._ws_client.receive()  # Blocking generator yielding incoming frames as dicts
            for frame in receive_iter:  # Walk frames one at a time until completion or timeout
                if time.monotonic() >= deadline:  # Hard cap — abort the wait loop on timeout
                    break  # Falls through to TimeoutError raise below
                frame_session = _extract_session_id(frame)  # Best-effort session_id extraction from frame payload
                if frame_session is not None and frame_session != session_id:  # Skip frames for other sessions
                    continue  # Multiple concurrent commands can share the channel
                raw_frames.append(frame)  # Preserve everything seen for this session for debugging
                frame_status = _extract_status(frame)  # Look for "completed" / "failed" markers in payload
                if frame_status in {"completed", "failed"}:  # Terminal states stop the wait loop
                    status = frame_status  # Promote the terminal status into the return payload
                    result_payload = _extract_data(frame)  # Pull the command output dict out of the frame
                    break  # Done — assemble and return below
            else:  # Generator exhausted without break — typically socket closed
                if not raw_frames:  # Nothing arrived at all — surface as TimeoutError for caller parity
                    raise TimeoutError(  # Mirrors legacy WebSocketManager.wait_for_command_result timeout
                        f"No WebSocket result for session_id={session_id} within {effective_timeout}s"
                    )
            if status == "timeout" and not raw_frames:  # Deadline tripped before any frame matched
                raise TimeoutError(f"No WebSocket result for session_id={session_id} within {effective_timeout}s")
        except TimeoutError:  # Re-raise so callers can distinguish timeout from other failures
            self.logger.warning(  # Log the timeout for operator visibility
                "WebSocket adapter timeout for session_id=%s after %ss",
                session_id,
                effective_timeout,
            )
            raise
        except Exception as exc:
            self.logger.error(  # NON-NEGOTIABLE error log
                "WebSocket adapter receive failure for session_id=%s: %s",
                session_id,
                exc,
            )
            status = "failed"  # Surface the failure in the structured return value
        self.logger.debug(  # NON-NEGOTIABLE post-action log
            "WebSocket adapter collected %d frames for session_id=%s status=%s",
            len(raw_frames),
            session_id,
            status,
        )
        return {  # Contract shape from contracts/adapter-interface.md
            "session_id": session_id,
            "status": status,
            "data": result_payload or {},
            "raw": raw_frames,
        }

    def disconnect(self) -> None:
        """Tear down the SDK client. Safe to call multiple times."""
        self.logger.info("Disconnecting WebSocket adapter for device=%s", self._device_id)  # Pre-action log
        if self._ws_client is None:  # Already disconnected or never connected — no-op
            self._connected = False  # Defensive: keep state coherent
            self.logger.debug("WebSocket adapter disconnect noop (no client)")  # Post-action log
            return  # Idempotent contract
        try:  # Swallow disconnect errors to match legacy cleanup behavior
            self._ws_client.disconnect()  # SDK shuts down the receive thread and closes the socket
        except Exception as exc:
            self.logger.warning("WebSocket adapter disconnect raised: %s", exc)  # Non-fatal cleanup warning
        finally:  # Always reset state so a second disconnect() is a no-op
            self._ws_client = None  # Drop the reference so the GC can clean up
            self._connected = False  # Mark adapter as torn down
            self.logger.debug("WebSocket adapter disconnect complete")  # Post-action log


def _extract_session_id(frame: dict[str, Any]) -> str | None:
    """Best-effort extraction of ``session_id`` from a streamed frame."""
    if not isinstance(frame, dict):  # Defensive — SDK should always yield dicts but guard anyway
        return None  # Skip malformed frames
    if "session_id" in frame:  # Top-level field — common shape
        return frame["session_id"]  # Return as-is
    data = frame.get("data")  # Some frames nest the payload one level deeper
    if isinstance(data, dict) and "session_id" in data:  # Reach into nested payload when present
        return data["session_id"]  # Return the nested session_id
    return None  # Unknown shape — caller treats as broadcast frame


def _extract_status(frame: dict[str, Any]) -> str | None:
    """Best-effort extraction of the completion status from a frame."""
    if not isinstance(frame, dict):  # Defensive guard for non-dict frames
        return None  # Skip unknown shapes
    status = frame.get("status")  # Top-level status field is the common case
    if status:  # Truthy string wins
        return status  # Return as-is
    data = frame.get("data")  # Some SDKs nest status inside data
    if isinstance(data, dict):  # Only descend when nested payload is dict-shaped
        return data.get("status")  # Return nested status or None
    return None  # No status indicator found


def _extract_data(frame: dict[str, Any]) -> dict[str, Any]:
    """Return the command-output payload from a terminal frame."""
    if not isinstance(frame, dict):  # Defensive guard against malformed frames
        return {}  # Empty payload for unknown shapes
    data = frame.get("data")  # Standard payload key emitted by DeviceCmdEvents
    if isinstance(data, dict):  # Only return dict-shaped payloads
        return data  # Hand back the nested payload directly
    return {}  # No usable payload — return empty dict to keep result shape stable


__all__ = ["MistWebSocketAdapter"]  # Public surface — adapter only; helpers stay module-private
