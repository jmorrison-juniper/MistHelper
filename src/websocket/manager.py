"""WebSocket Manager for Mist API real-time communications."""

from __future__ import annotations

import json  # Used by subscribe_to_channel to encode subscription frames
import logging  # Standard logger used across the module
import os  # Reads MIST_HOST / MIST_APITOKEN env fallbacks
import sys  # Used by _is_debug_mode for --debug detection
import threading  # Background WebSocket thread + results lock
import time  # Connection-wait timing + sleep
import traceback  # Used by log_ws_error for verbose tracebacks
from typing import Any  # Generic shapes used across helper functions

from src.websocket.polling.message_router import MessageRouter  # _on_message collaborator
from src.websocket.polling.result_collector import ResultCollector  # wait_for_command_result collaborator

try:
    import websocket
except ImportError as _ws_err:
    raise ImportError("websocket-client is required but not installed. Run: pip install websocket-client") from _ws_err


def _is_debug_mode() -> bool:
    """Check if debug mode is enabled via command line arguments."""
    return "--debug" in sys.argv or "-d" in sys.argv


def log_ws_error(error_message: str, debug_mode: bool) -> None:
    """Print and log a WebSocket operation error with optional debug traceback."""
    print(f"! {error_message}")
    logging.error(error_message)
    if debug_mode:
        print("[DEBUG] Exception details:")
        traceback.print_exc()


def cleanup_ws_connection(ws_manager: Any, debug_mode: bool = False) -> None:
    """Disconnect WebSocket manager and log cleanup, swallowing cleanup errors."""
    try:
        if ws_manager is not None:
            ws_manager.disconnect()
            print("-> WebSocket connection closed")
            if debug_mode:
                print("[DEBUG] WebSocket cleanup completed")
    except Exception as cleanup_error:
        logging.warning(f"WebSocket cleanup error: {cleanup_error}")


def get_mist_credentials(apisession: Any) -> tuple[str | None, str | None]:
    """Extract Mist host and API token from session or environment variables."""
    mist_host = getattr(apisession, "host", None) or os.getenv("MIST_HOST")
    mist_apitoken = getattr(apisession, "apitoken", None) or os.getenv("MIST_APITOKEN")
    return mist_host, mist_apitoken


def dump_ws_debug_state(ws_mgr: Any, debug_mode: bool) -> None:
    """Print WebSocket manager debug state when debug mode is active."""
    if debug_mode:
        print("[DEBUG] Checking WebSocket manager state...")
        print(f"[DEBUG] Connected = {ws_mgr.connected}")
        print(f"[DEBUG] Subscribed channels = {ws_mgr.subscribed_channels}")
        with ws_mgr.results_lock:
            print(f"[DEBUG] Pending results = {list(ws_mgr.command_results.keys())}")


def select_ws_site(deps: Any, debug_mode: bool) -> str | None:
    """Prompt for site selection, returning None and printing a message if cancelled."""
    site_id: str | None = deps.select_site_fn() or None
    if not site_id:
        print("! No site selected. Operation cancelled.")
        return None
    if debug_mode:
        print(f"[DEBUG] Selected site_id = {site_id}")
    return site_id


def check_mist_credentials(ws_mgr: Any, mist_host: str | None, mist_apitoken: str | None, debug_mode: bool) -> bool:
    """Validate Mist host and token; disconnect ws_mgr and return False if invalid."""
    if not mist_host or not mist_apitoken:
        print("! Mist host or API token not found in session or environment")
        if ws_mgr is not None:
            ws_mgr.disconnect()
        return False
    if debug_mode:
        print(f"[DEBUG] mist_host = {mist_host}")
        print(f"[DEBUG] API token length = {len(mist_apitoken) if mist_apitoken else 0}")
    return True


class WebSocketManager:
    """WebSocket Manager for Mist API real-time communications.

    This class handles WebSocket connections to the Mist API following the
    documented patterns: subscribe first, issue POST command, await results.

    SECURITY: WebSocket connections use authenticated sessions with proper
    credential handling and session-based command demultiplexing.
    """

    def __init__(self, mist_session: Any, mist_host: str | None = None) -> None:
        """Initialize WebSocket manager with Mist session.

        Args:
            mist_session: Authenticated Mist API session
            mist_host: Mist API host (if None, will get from session)
        """
        self.mist_session = mist_session
        self.mist_host = mist_host or getattr(mist_session, "host", None) or os.getenv("MIST_HOST", "api.mist.com")

        # Convert API host to WebSocket host
        assert self.mist_host is not None, "mist_host must be set"  # nosec B101
        websocket_host = self.mist_host.replace("api.", "api-ws.")
        self.websocket_url = f"wss://{websocket_host}/api-ws/v1/stream"
        self.websocket_connection: websocket.WebSocketApp | None = None
        self.logger = logging.getLogger(__name__)
        self.connected = False
        self.subscribed_channels: set[str] = set()
        self.confirmed_subscriptions: set[str] = set()

        # Results storage for command outputs
        self.command_results: dict[str, Any] = {}
        self.results_lock = threading.Lock()
        self.websocket_thread: threading.Thread | None = None

    def connect(self) -> bool:
        """Establish WebSocket connection with proper authentication.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Prepare authentication headers using session token
            mist_apitoken = getattr(self.mist_session, "apitoken", None) or os.getenv("MIST_APITOKEN")
            if not mist_apitoken:
                self.logger.error("No API token found in session or environment")
                return False

            self.logger.debug(f"WebSocket URL: {self.websocket_url}")
            self.logger.debug(f"Auth token configured (length: {len(mist_apitoken)} chars)")
            auth_header = f"Authorization: Token {mist_apitoken}"
            headers = [auth_header]

            # Create WebSocket connection
            self.websocket_connection = websocket.WebSocketApp(
                self.websocket_url,
                header=headers,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open,
            )

            # Start connection in background thread
            connection = self.websocket_connection
            self.websocket_thread = threading.Thread(target=connection.run_forever, daemon=True)
            self.websocket_thread.start()

            # Wait for connection to establish
            timeout_counter = 0
            while not self.connected and timeout_counter < 10:
                time.sleep(0.5)
                timeout_counter += 1
                if timeout_counter % 2 == 0:
                    self.logger.debug(f"WebSocket handshake waiting... ({timeout_counter * 0.5:.1f}s)")

            if self.connected:
                self.logger.info("WebSocket connection established successfully")
                return True
            else:
                self.logger.error("WebSocket connection timeout")
                return False

        except Exception as connection_error:
            self.logger.error(f"WebSocket connection failed: {connection_error}")
            return False

    def connect_and_subscribe(self, site_id: str, device_id: str, debug_mode: bool) -> bool:
        """Connect to WebSocket and subscribe to the device command channel.

        Handles initialization, connection, subscription, and a brief stabilization
        wait as a single atomic setup step used by all WebSocket command methods.

        Args:
            site_id (str): Mist site UUID.
            device_id (str): Mist device UUID.
            debug_mode (bool): Whether to print debug output.

        Returns:
            bool: True if connected and subscribed, False otherwise.
        """
        if debug_mode:
            print("[DEBUG] WebSocketManager initialized")

        if not self.connect():
            print("! Failed to establish WebSocket connection")
            return False

        if debug_mode:
            print("[DEBUG] WebSocket connection established")

        command_channel = f"/sites/{site_id}/devices/{device_id}/cmd"
        if not self.subscribe_to_channel(command_channel):
            print("! Failed to subscribe to device command channel")
            self.disconnect()
            return False

        if debug_mode:
            print(f"[DEBUG] Subscribed to channel: {command_channel}")

        print("-> WebSocket connected and subscribed")
        time.sleep(1)
        return True

    def subscribe_to_channel(self, channel_path: str) -> bool:
        """Subscribe to a WebSocket channel for receiving command outputs.

        Args:
            channel_path (str): Channel path (e.g., "/sites/{site_id}/devices/{device_id}/cmd")

        Returns:
            bool: True if subscription successful, False otherwise
        """
        if not self.connected:
            self.logger.error("Cannot subscribe: WebSocket not connected")
            return False

        try:
            subscription_message = {"subscribe": channel_path}

            if self.websocket_connection is not None:
                self.websocket_connection.send(json.dumps(subscription_message))
            self.subscribed_channels.add(channel_path)
            self.logger.debug(f"Subscribed to channel: {channel_path}")
            return True

        except Exception as subscription_error:
            self.logger.error(f"Channel subscription failed: {subscription_error}")
            return False

    def wait_for_subscription_confirmation(self, channel_path, timeout_seconds=10):
        """Wait for WebSocket subscription confirmation for a specific channel.

        Args:
            channel_path (str): Channel path to wait for confirmation
            timeout_seconds (int): Maximum time to wait for confirmation

        Returns:
            bool: True if confirmation received, False if timeout
        """
        start_time = time.time()

        debug_mode = getattr(self, "debug_mode", False) or os.getenv("DEBUG", "").lower() in ["true", "1", "yes"]

        if debug_mode:
            self.logger.debug(f"Waiting for subscription confirmation for: {channel_path}")
            print(f"[DEBUG] Waiting for subscription confirmation for: {channel_path}")

        while time.time() - start_time < timeout_seconds:
            # Check if subscription is confirmed
            if channel_path in self.confirmed_subscriptions:
                if debug_mode:
                    self.logger.debug(f"Subscription confirmed for: {channel_path}")
                    print(f"[DEBUG] Subscription confirmed for: {channel_path}")
                return True

            time.sleep(0.1)  # Small sleep to avoid busy waiting

        # Timeout reached
        if debug_mode:
            self.logger.debug(f"Timeout waiting for subscription confirmation: {channel_path}")
            print(f"[DEBUG] Timeout waiting for subscription confirmation: {channel_path}")
        self.logger.warning(f"Timeout waiting for subscription confirmation: {channel_path}")
        return False

    def wait_for_command_result(
        self,
        session_id: str,
        timeout_seconds: int = 30,
        activity_timeout_seconds: int | None = None,
    ) -> dict[str, Any] | None:
        """Wait for a command session to complete and return its combined result.

        Thin orchestrator over :class:`ResultCollector`. The collector owns the
        polling loop, indicator detection, activity-timeout logic, and the
        per-segment merge. Behaviour and timing are preserved verbatim from the
        original 450-line implementation.

        Args:
            session_id: Session ID from the command POST response.
            timeout_seconds: Absolute upper bound on the wait.
            activity_timeout_seconds: Idle window before assuming completion
                (defaults to 2 seconds inside :class:`ResultCollector`).

        Returns:
            Combined result dict, or ``None`` on timeout with no segments.
        """
        self.logger.info("Dispatching wait_for_command_result for session %s", session_id)  # Pre-action log
        collector = ResultCollector(  # Construct the collaborator with manager-owned shared state
            self.command_results,
            self.results_lock,
            self.logger,
            _is_debug_mode(),
        )
        result = collector.collect(session_id, timeout_seconds, activity_timeout_seconds)  # Run the wait loop
        self.logger.debug("wait_for_command_result returned has_result=%s", result is not None)  # Post-action log
        return result

    def _on_open(self, websocket_connection):
        """Handle connection-opened event from stream."""
        self.connected = True
        self.logger.debug("WebSocket connection opened")

    def _on_message(self, websocket_connection, message):
        r"""Handle incoming message from stream.

        Thin orchestrator over :class:`MessageRouter`. The router parses the
        frame, traces it (in debug mode), and routes subscription / data
        events into the shared command_results buffer.
        """
        self.logger.info("Dispatching incoming WebSocket message to router")  # Pre-action log
        router = MessageRouter(  # Build router with manager-owned shared state
            self.command_results,
            self.results_lock,
            self.confirmed_subscriptions,
            self.logger,
            _is_debug_mode(),
        )
        router.route(message)  # Single-purpose call into the collaborator
        self.logger.debug("WebSocket message routed")  # Post-action log

    def _on_error(self, websocket_connection, error):
        """Handle error events from connection."""
        self.logger.debug(f"WebSocket error type: {type(error).__name__}")
        self.logger.error(f"WebSocket error: {error}")

    def _on_close(self, websocket_connection, close_status_code, close_message):
        """Handle closed connection event."""
        self.connected = False
        self.logger.debug(f"WebSocket close details: status_code={close_status_code}, message={close_message}")
        self.logger.info(f"WebSocket connection closed (status: {close_status_code})")

    def disconnect(self) -> None:
        """Close WebSocket connection and cleanup resources."""
        if self.websocket_connection:
            self.websocket_connection.close()
        self.connected = False
        self.subscribed_channels.clear()

        with self.results_lock:
            self.command_results.clear()
