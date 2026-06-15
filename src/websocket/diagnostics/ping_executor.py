"""PingDeviceExecutor: orchestrate ping-over-WebSocket diagnostic workflow."""

from __future__ import annotations  # Defer annotation evaluation for forward refs

import logging  # Standard logging for action observability
from typing import Any  # Generic typing for the ping-result payload

from src.websocket.context import WebSocketCmdDeps  # Injected dependency bundle
from src.websocket.diagnostics.common import (  # Shared executor helpers
    detect_debug_mode,
    extract_command_session,
    post_device_command,
    prepare_command_credentials,
    print_extra_result_fields,
)
from src.websocket.manager import (  # WebSocket lifecycle + error utilities
    WebSocketManager,
    cleanup_ws_connection,
    dump_ws_debug_state,
    log_ws_error,
    select_ws_site,
)

_DEFAULT_PING_TARGET = "8.8.8.8"  # Legacy default destination preserved verbatim
_DEFAULT_PING_COUNT = 4  # Legacy default packet count preserved verbatim
_MIN_PING_COUNT = 1  # Inclusive lower bound enforced on user input
_MAX_PING_COUNT = 100  # Inclusive upper bound enforced on user input
_WS_RESULT_TIMEOUT = 30  # Seconds to wait for ping output via WebSocket


class PingDeviceExecutor:
    """Run an interactive ping command on a Mist device via the WebSocket stream."""

    def execute(self, deps: WebSocketCmdDeps) -> None:
        """Top-level entry: prompt user, run ping, render results."""
        logging.info("Starting WebSocket ping operation...")  # Action log before workflow begins
        debug_mode = detect_debug_mode()  # Honor --debug / -d flag once per run
        if debug_mode:  # Mirror legacy escalation of root logger level
            logging.getLogger().setLevel(logging.DEBUG)  # Surface DEBUG records to handlers
            print("[DEBUG] DEBUG MODE ENABLED")  # User-facing banner kept verbatim
        logging.info("Starting WebSocket ping operation...")  # Legacy duplicate log preserved
        logging.debug("ENTER: ping_device_websocket")  # Trace marker kept verbatim
        websocket_manager: WebSocketManager | None = None  # Tracked so finally can clean up
        try:  # Wrap entire workflow to mirror legacy try/except/finally
            websocket_manager = self._run_workflow(deps, debug_mode)  # Drive prompts + WS work
        except Exception as ping_error:
            log_ws_error(f"WebSocket ping operation failed: {ping_error}", debug_mode)  # Legacy log
            logging.debug("EXIT: ping_device_websocket - error")  # Trace marker preserved
        finally:  # Always release WS resources on exit path
            cleanup_ws_connection(websocket_manager, debug_mode)  # Disconnect if connected
            logging.debug("EXIT: ping_device_websocket")  # Trace marker preserved

    def _run_workflow(self, deps: WebSocketCmdDeps, debug_mode: bool) -> WebSocketManager | None:
        """Prompt user, dispatch ping, render output; return WS manager for cleanup."""
        site_id = select_ws_site(deps, debug_mode)  # Interactive site picker
        if site_id is None:  # User cancelled site selection
            return None  # Skip rest of workflow
        device_id = deps.select_device_fn(site_id, device_type="all")  # Interactive device picker
        if not device_id:  # User cancelled or no devices available
            print("! No device selected. Operation cancelled.")  # Legacy phrasing preserved
            return None  # Skip rest of workflow
        if debug_mode:  # Mirror legacy debug print of chosen device id
            print(f"[DEBUG] Selected device_id = {device_id}")
        target_host = self._prompt_target_host(deps, debug_mode)  # Get + validate target host
        if target_host is None:  # Validation failed (user message already printed)
            return None
        ping_count = self._prompt_ping_count(deps, debug_mode)  # Get + clamp packet count
        return self._issue_ping_and_render(  # Connect, POST, wait, render
            deps, site_id, device_id, target_host, ping_count, debug_mode
        )

    def _prompt_target_host(self, deps: WebSocketCmdDeps, debug_mode: bool) -> str | None:
        """Ask user for ping target; return validated host string or None on rejection."""
        target_input = deps.safe_input_fn(  # EOF-safe input wrapper
            "Enter the target hostname or IP address to ping (default: 8.8.8.8): ",
            context="websocket_ping",
        ).strip()  # Drop incidental whitespace from prompt response
        target_host = target_input if target_input else _DEFAULT_PING_TARGET  # Apply default
        logging.debug("Validating ping target host=%s", target_host)  # Action log before check
        if not deps.validate_target_fn(target_host):  # Reject unsafe / malformed hosts
            print(f"! Invalid ping target: {target_host}")  # Legacy phrasing preserved
            logging.warning("Rejected invalid ping target host=%s", target_host)  # After log
            return None  # Caller aborts workflow
        if debug_mode:  # Mirror legacy debug echo of the chosen host
            print(f"[DEBUG] Target host = {target_host}")
        logging.debug("Ping target accepted host=%s", target_host)  # Action log after success
        return target_host  # Validated host returned to caller

    def _prompt_ping_count(self, deps: WebSocketCmdDeps, debug_mode: bool) -> int:
        """Ask user for ping packet count; return clamped int with legacy defaults."""
        raw_count = deps.safe_input_fn(  # EOF-safe input wrapper
            "Enter number of ping packets (default: 4): ",
            context="websocket_ping",
        ).strip()  # Drop incidental whitespace from prompt response
        if not raw_count:  # Empty input means accept default count
            return self._announce_count(_DEFAULT_PING_COUNT, debug_mode)
        try:  # Parse user input as integer; revert to default on failure
            parsed_count = int(raw_count)  # Raises ValueError on non-numeric input
        except ValueError:  # Match legacy behavior of warning + default
            print("! Invalid ping count. Using default: 4")  # Legacy phrasing preserved
            logging.warning("Rejected non-numeric ping count input=%r", raw_count)  # After log
            return self._announce_count(_DEFAULT_PING_COUNT, debug_mode)
        if parsed_count < _MIN_PING_COUNT or parsed_count > _MAX_PING_COUNT:  # Range guard
            print("! Ping count must be between 1 and 100. Using default: 4")  # Legacy phrasing
            logging.warning("Rejected out-of-range ping count=%d", parsed_count)  # After log
            return self._announce_count(_DEFAULT_PING_COUNT, debug_mode)
        return self._announce_count(parsed_count, debug_mode)  # Accepted value path

    @staticmethod
    def _announce_count(ping_count: int, debug_mode: bool) -> int:
        """Echo selected ping count under debug mode then return it for chaining."""
        if debug_mode:  # Mirror legacy debug echo of the chosen count
            print(f"[DEBUG] Ping count = {ping_count}")
        return ping_count  # Chainable return keeps callers concise

    def _issue_ping_and_render(
        self,
        deps: WebSocketCmdDeps,
        site_id: str,
        device_id: str,
        target_host: str,
        ping_count: int,
        debug_mode: bool,
    ) -> WebSocketManager | None:
        """Connect WS, POST ping, await results, render output. Returns WS for cleanup."""
        print(f"\n-> Executing ping to {target_host} on device {device_id}...")  # Legacy banner
        print(f"-> Ping count: {ping_count}")  # Legacy banner line preserved
        print("-> Establishing WebSocket connection...")  # Legacy banner line preserved
        websocket_manager = WebSocketManager(deps.apisession)  # Build per-run WS manager
        logging.info("Connecting WebSocket for ping site=%s device=%s", site_id, device_id)  # Before
        if not websocket_manager.connect_and_subscribe(site_id, device_id, debug_mode):  # Subscribe
            logging.warning("WebSocket connect+subscribe failed for ping")  # After log on failure
            return websocket_manager  # Return so finally can clean it up
        logging.debug("WebSocket connect+subscribe succeeded for ping")  # After log on success
        session_id = self._post_ping_command(  # POST the ping HTTP command and pull session id
            deps, websocket_manager, site_id, device_id, target_host, ping_count, debug_mode
        )
        if session_id is None:  # POST failed; helpers already disconnected
            return websocket_manager  # Return for finally (already disconnected, but safe)
        self._await_and_render(  # Wait for the WS result then render to console
            websocket_manager, session_id, target_host, debug_mode
        )
        return websocket_manager  # Hand back for finally cleanup

    def _post_ping_command(
        self,
        deps: WebSocketCmdDeps,
        websocket_manager: WebSocketManager,
        site_id: str,
        device_id: str,
        target_host: str,
        ping_count: int,
        debug_mode: bool,
    ) -> str | None:
        """POST the ping command and return the session id (or None on failure)."""
        ping_payload = {"host": target_host, "count": ping_count}  # API body for ping endpoint
        print("-> Issuing ping command...")  # Legacy status line preserved
        logging.debug("Ping payload prepared host=%s count=%d", target_host, ping_count)  # Before
        if debug_mode:  # Mirror legacy debug echo of the payload
            print(f"[DEBUG] Ping payload = {ping_payload}")
        credentials = prepare_command_credentials(  # Pull + validate Mist host/token
            deps.apisession, websocket_manager, debug_mode
        )
        if credentials is None:  # Credential lookup failed and disconnected
            return None  # Caller aborts the workflow
        mist_host, mist_apitoken = credentials  # Unpack into local variables
        ping_url = (  # Build the device-scoped ping endpoint URL
            f"https://{mist_host}/api/v1/sites/{site_id}/devices/{device_id}/ping"
        )
        headers = {  # REST headers required by the Mist API
            "Authorization": f"Token {mist_apitoken}",
            "Content-Type": "application/json",
        }
        ping_response = post_device_command(  # POST and capture full response
            ping_url, headers, ping_payload, debug_mode, "ping"
        )
        if ping_response is None:  # Defensive: helper currently never returns None
            return None  # Treat as POST failure
        return extract_command_session(ping_response, websocket_manager, "ping")  # Demux session

    def _await_and_render(
        self,
        websocket_manager: WebSocketManager,
        session_id: str,
        target_host: str,
        debug_mode: bool,
    ) -> None:
        """Wait for the ping result on the WS, then render it or report timeout."""
        print(f"-> Ping command issued (session: {session_id[:8]}...)")  # Legacy status line
        print("-> Waiting for ping results...")  # Legacy status line preserved
        if debug_mode:  # Mirror legacy debug prints of session + waiting state
            print(f"[DEBUG] Full session ID = {session_id}")
            print("[DEBUG] Starting to wait for WebSocket results...")
        logging.info("Awaiting ping result session=%s", session_id[:8])  # Action log before wait
        ping_result = websocket_manager.wait_for_command_result(  # Block until result or timeout
            session_id, timeout_seconds=_WS_RESULT_TIMEOUT
        )
        logging.debug("Ping wait completed; has_result=%s", ping_result is not None)  # After log
        if debug_mode:  # Mirror legacy debug echo of wait outcome
            print(f"[DEBUG] wait_for_command_result returned: {ping_result is not None}")
            if ping_result:  # Show available top-level keys to aid diagnosis
                print(f"[DEBUG] Result keys: {list(ping_result.keys())}")
        if ping_result:  # Success path: render the captured payload
            self._render_ping_result(ping_result, target_host)
            return  # Done rendering
        print("! Timeout waiting for ping results")  # Failure path matches legacy phrasing
        logging.warning("WebSocket ping operation timed out")  # After log on timeout
        dump_ws_debug_state(websocket_manager, debug_mode)  # Surface WS state for triage

    def _render_ping_result(self, ping_result: dict[str, Any], target_host: str) -> None:
        """Print the well-known + extra fields of a ping result payload."""
        print("\n" + "=" * 60)  # Visual separator preserved verbatim
        print("PING RESULTS:")  # Header preserved verbatim
        print("=" * 60)  # Visual separator preserved verbatim
        raw_output = ping_result.get("raw", "")  # Primary output field from documented schema
        if raw_output:  # Render raw output block when present
            print("RAW OUTPUT:")  # Section header preserved
            print("-" * 40)  # Section underline preserved
            print(raw_output)  # Show captured raw text
        other_output = ping_result.get("Output", "")  # Secondary output field; sometimes empty
        if other_output and other_output != raw_output:  # Avoid duplicate echo when identical
            print("\nOTHER OUTPUT:")  # Section header preserved
            print("-" * 40)  # Section underline preserved
            print(other_output)  # Show captured secondary text
        print_extra_result_fields(ping_result, {"raw", "Output", "session"})  # Catch-all renderer
        if not raw_output and not other_output:  # Surface empty-result diagnostic message
            print("No output data received")  # Legacy phrasing preserved
            print(f"Available result keys: {list(ping_result.keys())}")  # Aid for triage
        print("=" * 60)  # Visual closer preserved verbatim
        logging.info("WebSocket ping completed successfully for %s", target_host)  # Final log
