"""WebSocket Manager for Mist API real-time communications."""

from __future__ import annotations  # WHY: Defer annotation evaluation to keep forward refs cheap.

import json  # WHY: Encodes subscription frames sent to the Mist stream endpoint.
import logging  # WHY: Structured diagnostic output shared with the rest of the app.
import os  # WHY: Reads MIST_HOST / MIST_APITOKEN / DEBUG env fallbacks.
import sys  # WHY: Used by _is_debug_mode to inspect CLI flags.
import threading  # WHY: Background WebSocket reader thread + results lock.
import time  # WHY: Poll intervals for connect / subscription / stabilization waits.
import traceback  # WHY: Verbose exception dumps when debug mode is enabled.
from typing import Any  # WHY: Callback frames from websocket-client have no upstream stubs.

from src.websocket.polling.message_router import MessageRouter  # WHY: _on_message collaborator.
from src.websocket.polling.result_collector import ResultCollector  # WHY: wait_for_command_result collaborator.

logger = logging.getLogger(__name__)  # WHY: module-scoped logger for #886 print-to-logger migration.

try:  # WHY: websocket-client is a hard runtime dep. Fail loudly if missing.
    import websocket  # WHY: Actual client library import (may raise ImportError).
except ImportError as _ws_err:  # WHY: Convert to project-branded ImportError with install hint.
    raise ImportError(  # WHY: Re-raise with actionable install command for operators.
        "websocket-client is required but not installed. Run: pip install websocket-client",
    ) from _ws_err

# Module-level constants — collapse magic values into named knobs.
_WS_CONNECT_POLL_SECONDS = 0.5  # WHY: Half-second cadence when polling for handshake completion.
_WS_CONNECT_MAX_POLLS = 10  # WHY: Bounded to 5s total connect wait (0.5s * 10).
_WS_STABILIZE_SLEEP_SECONDS = 1  # WHY: Brief settle after subscribe before commands are issued.
_WS_SUBSCRIPTION_POLL_SECONDS = 0.1  # WHY: Fine-grained poll for subscription confirmation.
_WS_HANDSHAKE_LOG_MOD = 2  # WHY: Log every second handshake tick to reduce noise.
_WS_API_HOST_PREFIX = "api."  # WHY: Prefix on REST host, swapped for WS variant.
_WS_HOST_PREFIX = "api-ws."  # WHY: Prefix Mist uses for streaming endpoints.
_WS_STREAM_PATH = "/api-ws/v1/stream"  # WHY: Fixed Mist WebSocket entry point.
_DEBUG_TRUE_VALUES = frozenset({"true", "1", "yes"})  # WHY: Accepted truthy strings for DEBUG env.


def _is_debug_mode() -> bool:
    """Check if debug mode is enabled via command line arguments."""
    return "--debug" in sys.argv or "-d" in sys.argv  # WHY: Cheap CLI probe reused across module.


def _is_debug_env_flag_set() -> bool:
    """Return True when the DEBUG env var holds a recognised truthy string."""
    return os.getenv("DEBUG", "").lower() in _DEBUG_TRUE_VALUES  # WHY: Case-insensitive DEBUG probe.


def log_ws_error(error_message: str, debug_mode: bool) -> None:
    """Print and log a WebSocket operation error with optional debug traceback."""
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.error("! %s", error_message)  # WHY: User-visible error banner via logger.
    logging.error(error_message)  # WHY: Persist error to configured logging sinks.
    if debug_mode:  # WHY: Only emit stack trace when the operator asked for detail.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.debug("[DEBUG] Exception details:")  # WHY: Marker line preceding the traceback dump.
        traceback.print_exc()  # WHY: Full traceback for interactive debugging sessions.


def cleanup_ws_connection(ws_manager: Any, debug_mode: bool = False) -> None:
    """Disconnect WebSocket manager and log cleanup, swallowing cleanup errors."""
    try:  # WHY: Cleanup must never propagate — it runs from `finally` blocks.
        if ws_manager is not None:  # WHY: Callers may pass None if construction failed.
            ws_manager.disconnect()  # WHY: Release socket + clear internal state.
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logger.info("-> WebSocket connection closed")  # WHY: User confirmation via logger.
            if debug_mode:  # WHY: Extra diagnostic breadcrumb only for debug runs.
                # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
                logger.debug("[DEBUG] WebSocket cleanup completed")  # WHY: Marks end of teardown.
    except Exception as cleanup_error:  # WHY: Broad catch — teardown must be resilient.
        logging.warning("WebSocket cleanup error: %s", cleanup_error)  # WHY: Warn but do not fail.


def get_mist_credentials(apisession: Any) -> tuple[str | None, str | None]:
    """Extract Mist host and API token from session or environment variables."""
    mist_host = getattr(apisession, "host", None) or os.getenv("MIST_HOST")  # WHY: Session first, env fallback.
    mist_apitoken = getattr(apisession, "apitoken", None) or os.getenv("MIST_APITOKEN")  # WHY: Same precedence.
    return mist_host, mist_apitoken  # WHY: Tuple contract used by callers for guard checks.


def dump_ws_debug_state(ws_mgr: Any, debug_mode: bool) -> None:
    """Print WebSocket manager debug state when debug mode is active."""
    if not debug_mode:  # WHY: Guard clause avoids nested block for non-debug runs.
        return  # WHY: No side effects when debug is off.
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.debug("[DEBUG] Checking WebSocket manager state...")  # WHY: Section marker for debug dump.
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.debug("[DEBUG] Connected = %s", ws_mgr.connected)  # WHY: Surfaces socket-open flag.
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.debug("[DEBUG] Subscribed channels = %s", ws_mgr.subscribed_channels)  # WHY: Reveals routing state.
    with ws_mgr.results_lock:  # WHY: Snapshot pending results under the shared lock.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.debug("[DEBUG] Pending results = %s", list(ws_mgr.command_results.keys()))  # WHY: In-flight sessions.


def select_ws_site(deps: Any, debug_mode: bool) -> str | None:
    """Prompt for site selection, returning None and printing a message if cancelled."""
    site_id: str | None = deps.select_site_fn() or None  # WHY: Normalise falsy return to None.
    if not site_id:  # WHY: Cancellation path — surface a clear message to the operator.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.warning("! No site selected. Operation cancelled.")  # WHY: Explains why nothing runs next.
        return None  # WHY: Callers detect None to abort the workflow.
    if debug_mode:  # WHY: Only echo the selected id when detail is requested.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.debug("[DEBUG] Selected site_id = %s", site_id)  # WHY: Traceable id for later log correlation.
    return site_id  # WHY: Successful selection propagated to caller.


def _log_credential_debug(mist_host: str, mist_apitoken: str) -> None:
    """Emit debug lines describing which credentials the manager will use."""
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.debug("[DEBUG] mist_host = %s", mist_host)  # WHY: Confirms target Mist cloud region.
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.debug("[DEBUG] API token length = %d", len(mist_apitoken))  # WHY: Token itself never printed.


def check_mist_credentials(
    ws_mgr: Any,
    mist_host: str | None,
    mist_apitoken: str | None,
    debug_mode: bool,
) -> bool:
    """Validate Mist host and token. Disconnect ws_mgr and return False if invalid."""
    if not (mist_host and mist_apitoken):  # WHY: Combined guard shrinks branch count.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.error("! Mist host or API token not found in session or environment")  # WHY: Actionable hint.
        if ws_mgr is not None:  # WHY: Only tear down when a manager was actually constructed.
            ws_mgr.disconnect()  # WHY: Prevent leaked socket when we bail out early.
        return False  # WHY: Signals caller to abort the workflow.
    if debug_mode:  # WHY: Only dump credential shape when the operator requested detail.
        _log_credential_debug(mist_host, mist_apitoken)  # WHY: Encapsulates debug prints.
    return True  # WHY: Credentials are usable. Caller may proceed.


class WebSocketManager:
    """WebSocket Manager for Mist API real-time communications.

    Handles WebSocket connections to the Mist API following the documented
    pattern: subscribe first, issue POST command, await results. Uses
    authenticated sessions with proper credential handling and session-based
    command demultiplexing.
    """

    def __init__(self, mist_session: Any, mist_host: str | None = None) -> None:
        """Initialise WebSocket manager with a Mist API session."""
        self.mist_session = mist_session  # WHY: Retained for later token lookups.
        # WHY: Precedence — explicit arg, then session attr, then env var, then default cloud.
        self.mist_host = mist_host or getattr(mist_session, "host", None) or os.getenv("MIST_HOST", "api.mist.com")
        assert self.mist_host is not None, "mist_host must be set"  # nosec B101  # WHY: Contract for type narrow.
        websocket_host = self.mist_host.replace(_WS_API_HOST_PREFIX, _WS_HOST_PREFIX)  # WHY: REST -> WS host swap.
        self.websocket_url = f"wss://{websocket_host}{_WS_STREAM_PATH}"  # WHY: Full endpoint URL.
        self.websocket_connection: websocket.WebSocketApp | None = None  # WHY: Lazily created in connect().
        self.logger = logging.getLogger(__name__)  # WHY: Per-module logger with stable name.
        self.connected = False  # WHY: Handshake state flag toggled by _on_open/_on_close.
        self.subscribed_channels: set[str] = set()  # WHY: Tracks locally requested subscriptions.
        self.confirmed_subscriptions: set[str] = set()  # WHY: Populated when router sees the ack.
        self.command_results: dict[str, Any] = {}  # WHY: Shared buffer for command output segments.
        self.results_lock = threading.Lock()  # WHY: Guards command_results across reader thread.
        self.websocket_thread: threading.Thread | None = None  # WHY: Handle to the reader daemon.

    def _resolve_auth_headers(self) -> list[str] | None:
        """Return WebSocket auth headers, or None when no API token is available."""
        mist_apitoken = getattr(self.mist_session, "apitoken", None) or os.getenv("MIST_APITOKEN")  # WHY: Env fallback.
        if not mist_apitoken:  # WHY: Fail fast — the API rejects unauthenticated streams.
            self.logger.error("No API token found in session or environment")  # WHY: Actionable hint.
            return None  # WHY: Caller converts None into a connect() failure.
        self.logger.debug("WebSocket URL: %s", self.websocket_url)  # WHY: Trace target endpoint.
        self.logger.debug("Auth token configured (length: %s chars)", len(mist_apitoken))  # WHY: Length only.
        return [f"Authorization: Token {mist_apitoken}"]  # WHY: Format required by Mist gateway.

    def _start_websocket_thread(self, headers: list[str]) -> None:
        """Create the WebSocketApp and start the background reader thread."""
        self.websocket_connection = websocket.WebSocketApp(  # WHY: Bind callbacks + auth in one construction.
            self.websocket_url,
            header=headers,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open,
        )
        connection = self.websocket_connection  # WHY: Local alias so the closure captures a concrete value.
        self.websocket_thread = threading.Thread(  # WHY: Reader must run outside the main flow.
            target=connection.run_forever,
            daemon=True,  # WHY: Daemon so process exit tears the reader down cleanly.
        )
        self.websocket_thread.start()  # WHY: Kick the reader — handshake completes asynchronously.

    def _await_handshake(self) -> bool:
        """Poll for the connected flag with periodic debug logging."""
        for tick in range(_WS_CONNECT_MAX_POLLS):  # WHY: Bounded wait avoids indefinite hang.
            if self.connected:  # WHY: Fast-path exit once _on_open flips the flag.
                return True  # WHY: Handshake succeeded.
            time.sleep(_WS_CONNECT_POLL_SECONDS)  # WHY: Yield to reader thread.
            if (tick + 1) % _WS_HANDSHAKE_LOG_MOD == 0:  # WHY: Reduce log noise while still tracing.
                elapsed = (tick + 1) * _WS_CONNECT_POLL_SECONDS  # WHY: Precomputed for the log message.
                self.logger.debug("WebSocket handshake waiting... (%.1fs)", elapsed)  # WHY: Progress trace.
        return self.connected  # WHY: Last chance — reader may have flipped the flag on the final sleep.

    def connect(self) -> bool:
        """Establish WebSocket connection with proper authentication."""
        try:  # WHY: Any low-level failure is reported and returned as False.
            headers = self._resolve_auth_headers()  # WHY: Extracted for testability + CC budget.
            if headers is None:  # WHY: Missing token already logged inside the helper.
                return False  # WHY: Signal connection failure to caller.
            self._start_websocket_thread(headers)  # WHY: Kicks off the async reader.
            if not self._await_handshake():  # WHY: Bounded wait for _on_open to flip the flag.
                self.logger.error("WebSocket connection timeout")  # WHY: Distinct from bad-credential path.
                return False  # WHY: Timeout means the caller should abort.
            self.logger.info("WebSocket connection established successfully")  # WHY: Success trace.
            return True  # WHY: Manager is now usable for subscribe/command flows.
        except Exception as connection_error:  # WHY: Broad guard — never leak library exceptions.
            self.logger.error("WebSocket connection failed: %s", connection_error)  # WHY: Diagnosable log.
            return False  # WHY: Convert any raised error into a False return.

    def _debug_print(self, message: str, debug_mode: bool) -> None:
        """Print a `[DEBUG] ...` line only when debug_mode is truthy."""
        if debug_mode:  # WHY: Guard keeps quiet mode noise-free.
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logger.debug("[DEBUG] %s", message)  # WHY: Uniform debug marker.

    def _subscribe_command_channel(self, site_id: str, device_id: str, debug_mode: bool) -> bool:
        """Subscribe to the site/device command channel and log the outcome."""
        command_channel = f"/sites/{site_id}/devices/{device_id}/cmd"  # WHY: Mist channel convention.
        if not self.subscribe_to_channel(command_channel):  # WHY: Delegates the wire message.
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logger.error("! Failed to subscribe to device command channel")  # WHY: User-visible error banner.
            self.disconnect()  # WHY: Release the socket if subscribe failed.
            return False  # WHY: Caller must abort the workflow.
        self._debug_print(f"Subscribed to channel: {command_channel}", debug_mode)  # WHY: Trace success.
        return True  # WHY: Subscription in place. Ready for command POST.

    def connect_and_subscribe(self, site_id: str, device_id: str, debug_mode: bool) -> bool:
        """Connect to WebSocket and subscribe to the device command channel."""
        self._debug_print("WebSocketManager initialized", debug_mode)  # WHY: Trace lifecycle start.
        if not self.connect():  # WHY: Handshake is a hard precondition for subscribe.
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logger.error("! Failed to establish WebSocket connection")  # WHY: User-visible failure.
            return False  # WHY: Cannot proceed without a live socket.
        self._debug_print("WebSocket connection established", debug_mode)  # WHY: Trace handshake success.
        if not self._subscribe_command_channel(site_id, device_id, debug_mode):  # WHY: Second precondition.
            return False  # WHY: Subscribe helper already emitted its own error banner.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("-> WebSocket connected and subscribed")  # WHY: Positive user-facing confirmation.
        time.sleep(_WS_STABILIZE_SLEEP_SECONDS)  # WHY: Brief settle before first command POST.
        return True  # WHY: Manager is ready for command traffic.

    def subscribe_to_channel(self, channel_path: str) -> bool:
        """Subscribe to a WebSocket channel for receiving command outputs."""
        if not self.connected:  # WHY: Sending on a closed socket would raise.
            self.logger.error("Cannot subscribe: WebSocket not connected")  # WHY: Diagnosable error.
            return False  # WHY: Signal caller that no subscription happened.
        try:  # WHY: Guard against transient send errors.
            subscription_message = {"subscribe": channel_path}  # WHY: Mist stream subscribe frame.
            if self.websocket_connection is not None:  # WHY: mypy narrow — could still be None.
                self.websocket_connection.send(json.dumps(subscription_message))  # WHY: Wire format is JSON.
            self.subscribed_channels.add(channel_path)  # WHY: Track locally for teardown / diagnostics.
            self.logger.debug("Subscribed to channel: %s", channel_path)  # WHY: Trace success.
            return True  # WHY: Frame accepted by client library.
        except Exception as subscription_error:  # WHY: Broad guard — do not leak library errors.
            self.logger.error("Channel subscription failed: %s", subscription_error)  # WHY: Diagnose.
            return False  # WHY: Signal failure to caller.

    def _debug_log_sub(self, action: str, channel_path: str, debug_mode: bool) -> None:
        """Log a subscription-lifecycle debug line to both logger and stdout."""
        if not debug_mode:  # WHY: Guard keeps quiet mode noise-free.
            return  # WHY: Nothing to log in non-debug runs.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.debug("[DEBUG] %s: %s", action, channel_path)  # WHY: Debug echo for interactive debug.

    def _poll_subscription_confirmed(self, channel_path: str, timeout_seconds: float) -> bool:
        """Spin-wait for the router to record a subscription confirmation."""
        start_time = time.time()  # WHY: Absolute deadline anchor.
        while time.time() - start_time < timeout_seconds:  # WHY: Elapsed check against caller's cap.
            if channel_path in self.confirmed_subscriptions:  # WHY: Router populates this set on ack.
                return True  # WHY: Confirmation received — caller may proceed.
            time.sleep(_WS_SUBSCRIPTION_POLL_SECONDS)  # WHY: Yield to reader. Avoid busy-wait.
        return False  # WHY: Deadline exceeded without confirmation.

    def wait_for_subscription_confirmation(
        self,
        channel_path: str,
        timeout_seconds: int = 10,
    ) -> bool:
        """Wait for WebSocket subscription confirmation for a specific channel."""
        debug_mode = getattr(self, "debug_mode", False) or _is_debug_env_flag_set()  # WHY: Attr or env.
        self._debug_log_sub("Waiting for subscription confirmation for", channel_path, debug_mode)  # WHY: Trace start.
        if self._poll_subscription_confirmed(channel_path, timeout_seconds):  # WHY: Bounded spin.
            self._debug_log_sub("Subscription confirmed for", channel_path, debug_mode)  # WHY: Trace success.
            return True  # WHY: Confirmed within the deadline.
        self._debug_log_sub("Timeout waiting for subscription confirmation", channel_path, debug_mode)  # WHY: Debug.
        self.logger.warning("Timeout waiting for subscription confirmation: %s", channel_path)  # WHY: Always warn.
        return False  # WHY: Caller decides whether to retry.

    def _build_result_collector(self) -> ResultCollector:
        """Construct a ResultCollector bound to this manager's shared state."""
        return ResultCollector(  # WHY: Wire manager-owned buffers into the collector.
            self.command_results,
            self.results_lock,
            self.logger,
            _is_debug_mode(),
        )

    def wait_for_command_result(
        self,
        session_id: str,
        timeout_seconds: int = 30,
        activity_timeout_seconds: int | None = None,
    ) -> dict[str, Any] | None:
        """Wait for a command session to complete and return its combined result."""
        self.logger.info("Dispatching wait_for_command_result for session %s", session_id)  # WHY: Pre-action.
        result = self._build_result_collector().collect(  # WHY: Delegate polling to the collector.
            session_id,
            timeout_seconds,
            activity_timeout_seconds,
        )
        self.logger.debug("wait_for_command_result returned has_result=%s", result is not None)  # WHY: Post-action.
        return result  # WHY: Preserves original None-on-timeout contract.

    def _on_open(self, websocket_connection: Any) -> None:
        """Handle connection-opened event from stream."""
        self.connected = True  # WHY: Flag flip unblocks _await_handshake.
        self.logger.debug("WebSocket connection opened")  # WHY: Trace handshake success.

    def _on_message(self, websocket_connection: Any, message: Any) -> None:
        r"""Handle incoming message from stream via MessageRouter."""
        self.logger.info("Dispatching incoming WebSocket message to router")  # WHY: Pre-action log.
        router = MessageRouter(  # WHY: Build router with manager-owned shared state.
            self.command_results,
            self.results_lock,
            self.confirmed_subscriptions,
            self.logger,
            _is_debug_mode(),
        )
        router.route(message)  # WHY: Single-purpose call into the collaborator.
        self.logger.debug("WebSocket message routed")  # WHY: Post-action log.

    def _on_error(self, websocket_connection: Any, error: Any) -> None:
        """Handle error events from connection."""
        self.logger.debug("WebSocket error type: %s", type(error).__name__)  # WHY: Type helps triage.
        self.logger.error("WebSocket error: %s", error)  # WHY: Error string surfaced to logs.

    def _on_close(
        self,
        websocket_connection: Any,
        close_status_code: Any,
        close_message: Any,
    ) -> None:
        """Handle closed connection event."""
        self.connected = False  # WHY: Prevent further sends after remote close.
        self.logger.debug(  # WHY: Detailed close context aids reconnect logic.
            "WebSocket close details: status_code=%s, message=%s",
            close_status_code,
            close_message,
        )
        self.logger.info("WebSocket connection closed (status: %s)", close_status_code)  # WHY: User-facing.

    def disconnect(self) -> None:
        """Close WebSocket connection and cleanup resources."""
        if self.websocket_connection:  # WHY: Idempotent — no-op if never connected.
            self.websocket_connection.close()  # WHY: Ask library to shut the socket down.
        self.connected = False  # WHY: Reset flag regardless of prior state.
        self.subscribed_channels.clear()  # WHY: Force fresh subscribes on next connect.
        with self.results_lock:  # WHY: Serialise clearing shared buffer.
            self.command_results.clear()  # WHY: Drop stale in-flight sessions.
