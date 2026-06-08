"""WebSocket device command: show MAC table retrieval via Mist API WebSocket stream."""

from __future__ import annotations

import logging  # Structured operational logging for action tracing.
import sys  # Read CLI argv to detect interactive debug flag.
from typing import Any  # Dynamic payload typing for vendor JSON shapes.

import requests  # HTTP client for Mist REST API used to trigger the show_mac_table RPC.

from src.websocket.context import WebSocketCmdDeps  # Typed dependency bundle injected by orchestrator.
from src.websocket.manager import (  # WebSocket lifecycle + credential helpers reused across commands.
    WebSocketManager,
    check_mist_credentials,
    cleanup_ws_connection,
    dump_ws_debug_state,
    get_mist_credentials,
    log_ws_error,
    select_ws_site,
)


class MacTableCommand:
    """Execute the Mist `show_mac_table` switch command over an authenticated WebSocket session.

    MAC tables are a Layer 2 switching feature: routers and access points are excluded
    so operators do not waste time waiting on an unsupported device. The command follows
    the documented Mist pattern: connect WS -> subscribe device channel -> POST RPC ->
    await session-keyed result on the WS stream.
    """

    @staticmethod
    def execute(deps: WebSocketCmdDeps) -> None:
        """Run the show-MAC-table workflow end-to-end and print results to stdout."""
        logging.info("Menu #5: Starting WebSocket show MAC table operation")  # Log workflow entry boundary.
        debug_mode = "--debug" in sys.argv or "-d" in sys.argv  # Honor user-supplied verbose-output flag.
        if debug_mode:
            logging.getLogger().setLevel(logging.DEBUG)  # Raise log verbosity for interactive troubleshooting.
            print("[DEBUG] DEBUG MODE ENABLED")  # Preserve legacy operator-facing debug banner.
        logging.debug("ENTER: show_mac_table_websocket")  # Preserve legacy enter-trace for log greppability.

        websocket_manager: WebSocketManager | None = None  # Pre-declare so `finally` cleanup always has a binding.
        try:
            targets = MacTableCommand._resolve_targets(deps, debug_mode)  # Prompt operator for site + switch device.
            if targets is None:
                return  # Early exit when operator aborts target selection.
            site_id, device_id = targets  # Unpack chosen IDs for downstream API calls.

            print(f"\n-> Executing show MAC table on device {device_id}...")  # Preserve legacy progress message.
            print("-> Establishing WebSocket connection...")  # Preserve legacy progress message.

            websocket_manager = MacTableCommand._open_websocket(deps, site_id, device_id, debug_mode)  # WS setup.
            if websocket_manager is None:
                return  # Early exit when WS connect/subscribe failed (already logged inside helper).

            session_id = MacTableCommand._trigger_rpc(deps, websocket_manager, site_id, device_id, debug_mode)
            if session_id is None:
                return  # Early exit when REST RPC failed; manager already disconnected by helper.

            print(f"-> Show MAC table command issued (session: {session_id[:8]}...)")  # Legacy progress message.
            print("-> Waiting for MAC table results...")  # Legacy progress message.
            if debug_mode:
                print(f"[DEBUG] Full session ID = {session_id}")  # Legacy debug detail line.
                print("[DEBUG] Starting to wait for WebSocket results...")  # Legacy debug detail line.

            MacTableCommand._await_and_display(websocket_manager, session_id, debug_mode)  # Block on WS result.
        except Exception as mac_table_error:
            error_message = f"WebSocket show MAC table operation failed: {mac_table_error}"  # Build legacy text.
            log_ws_error(error_message, debug_mode)  # Route through shared WS error formatter.
            logging.debug("EXIT: show_mac_table_websocket - error")  # Preserve legacy exit-trace marker.
        finally:
            cleanup_ws_connection(websocket_manager, debug_mode)  # Always release WS socket and subscriptions.
            logging.debug("EXIT: show_mac_table_websocket")  # Preserve legacy exit-trace marker.

    @staticmethod
    def _resolve_targets(deps: WebSocketCmdDeps, debug_mode: bool) -> tuple[str, str] | None:
        """Prompt operator for the site and switch device and return their IDs, or None on abort."""
        logging.info("Prompting operator for WebSocket MAC table target site")  # Log before interactive site prompt.
        site_id = select_ws_site(deps, debug_mode)  # Interactive site selection via shared helper.
        logging.debug("Site selection result: %s", site_id)  # Log result without leaking richer data.
        if site_id is None:
            return None  # Operator cancelled site selection — propagate abort.

        print("-> MAC table is available on switches (Layer 2 devices)")  # Legacy operator guidance line.
        print("-> Routers/gateways operate at Layer 3 and typically don't maintain MAC tables")  # Legacy guidance.
        print("-> APs forward wireless traffic but don't maintain traditional MAC tables")  # Legacy guidance.

        logging.info("Prompting operator to select a switch device under site %s", site_id)  # Log before device pick.
        device_id = deps.select_device_fn(site_id, device_type="switch")  # Filter pick list to switches only.
        logging.debug("Device selection result: %s", device_id)  # Log selection result for traceability.
        if not device_id:
            print("! No switch device selected. MAC table command requires Layer 2 switching devices.")  # Legacy.
            print("! Only switches maintain MAC address learning tables for Ethernet forwarding.")  # Legacy.
            return None  # Operator declined to pick a switch — abort cleanly.

        if debug_mode:
            print(f"[DEBUG] Selected device_id = {device_id}")  # Legacy debug detail line.
        return site_id, device_id  # Return resolved tuple for orchestrator continuation.

    @staticmethod
    def _open_websocket(
        deps: WebSocketCmdDeps, site_id: str, device_id: str, debug_mode: bool
    ) -> WebSocketManager | None:
        """Construct WS manager and perform connect+subscribe, returning manager on success or None on failure."""
        logging.info("Opening WebSocket and subscribing to device %s on site %s", device_id, site_id)  # Before.
        websocket_manager = WebSocketManager(deps.apisession)  # Build manager bound to current auth session.
        connected = websocket_manager.connect_and_subscribe(site_id, device_id, debug_mode)  # WS open + subscribe.
        logging.debug("WebSocket connect_and_subscribe returned: %s", connected)  # After.
        if not connected:
            return None  # Connection failure — caller will return early without printing extra text.
        return websocket_manager  # Manager ready for RPC + result wait.

    @staticmethod
    def _trigger_rpc(
        deps: WebSocketCmdDeps,
        websocket_manager: WebSocketManager,
        site_id: str,
        device_id: str,
        debug_mode: bool,
    ) -> str | None:
        """POST the show_mac_table RPC and return the Mist session id, or None on failure."""
        mac_table_payload: dict[str, Any] = {}  # show_mac_table requires no additional parameters.
        print("-> Issuing show MAC table command...")  # Legacy progress message.
        logging.debug("MAC table payload: %s", mac_table_payload)  # Trace request body (always empty by design).
        if debug_mode:
            print(f"[DEBUG] MAC table payload = {mac_table_payload}")  # Legacy debug detail line.

        logging.info("Resolving Mist credentials for direct REST RPC")  # Log before credential lookup action.
        mist_host, mist_apitoken = get_mist_credentials(deps.apisession)  # Extract host + token from session.
        logging.debug("Mist credentials resolved (host=%s, token=[REDACTED])", mist_host)  # Result, redacted.
        if not check_mist_credentials(websocket_manager, mist_host, mist_apitoken, debug_mode):
            return None  # Credential validator already emitted operator-facing diagnostics.

        mac_table_url = f"https://{mist_host}/api/v1/sites/{site_id}/devices/{device_id}/show_mac_table"  # RPC URL.
        headers = {"Authorization": f"Token {mist_apitoken}", "Content-Type": "application/json"}  # Auth headers.
        if debug_mode:
            print(f"[DEBUG] POST URL = {mac_table_url}")  # Legacy debug detail line.
            print("[DEBUG] Headers = {'Authorization': 'Token [REDACTED]', 'Content-Type': 'application/json'}")

        logging.info("POST %s to trigger show_mac_table RPC", mac_table_url)  # Log before HTTP request action.
        mac_table_response = requests.post(  # Issue REST RPC that initiates the WebSocket session response.
            mac_table_url, headers=headers, json=mac_table_payload, timeout=30
        )
        logging.debug("show_mac_table HTTP status=%s", mac_table_response.status_code)  # After-call result.
        if debug_mode:
            print(f"[DEBUG] HTTP Response Status = {mac_table_response.status_code}")  # Legacy debug line.
            print(f"[DEBUG] HTTP Response Body = {mac_table_response.text}")  # Legacy debug line.

        if mac_table_response.status_code != 200:
            print(f"! Failed to issue show MAC table command: {mac_table_response.status_code}")  # Legacy error.
            print(f"! Response: {mac_table_response.text}")  # Legacy error body echo for operator diagnosis.
            websocket_manager.disconnect()  # Free WS socket since we won't await a result.
            return None  # Signal failure to orchestrator.

        response_data = mac_table_response.json()  # Parse JSON envelope returning the session correlation id.
        session_id = response_data.get("session")  # Extract Mist-assigned session id used to demux WS messages.
        if not session_id:
            print("! No session ID returned from show MAC table command")  # Legacy error message.
            websocket_manager.disconnect()  # No correlation id means no result can ever arrive — close WS.
            return None  # Signal failure to orchestrator.
        return session_id  # Caller will block on websocket_manager.wait_for_command_result(session_id).

    @staticmethod
    def _await_and_display(websocket_manager: WebSocketManager, session_id: str, debug_mode: bool) -> None:
        """Block on the WS result for the given session and render formatted output."""
        logging.info("Waiting for MAC table result on session %s", session_id)  # Log before blocking WS wait.
        mac_table_result = websocket_manager.wait_for_command_result(session_id, timeout_seconds=60)  # 60s budget.
        logging.debug(
            "wait_for_command_result returned populated=%s", mac_table_result is not None
        )  # After-call summary.
        if debug_mode:
            print(f"[DEBUG] wait_for_command_result returned: {mac_table_result is not None}")  # Legacy line.
            if mac_table_result:
                print(f"[DEBUG] Result keys: {list(mac_table_result.keys())}")  # Legacy debug detail.

        if mac_table_result:
            MacTableCommand._render_result(mac_table_result)  # Pretty-print MAC table fields to stdout.
            logging.info("WebSocket show MAC table completed successfully")  # Log success outcome.
            return  # Done — successful path.

        print("! Timeout waiting for MAC table results")  # Legacy timeout banner.
        print("! This may indicate:")  # Legacy diagnostic preface.
        print("  - The device doesn't support MAC table commands (common for routers/Layer 3 devices)")
        print("  - The device is busy or not responding")  # Legacy diagnostic hint.
        print("  - Network connectivity issues")  # Legacy diagnostic hint.
        print("! Note: MAC tables are primarily a Layer 2 (switch) feature")  # Legacy diagnostic reminder.
        logging.warning("WebSocket show MAC table operation timed out")  # Log timeout outcome.
        dump_ws_debug_state(websocket_manager, debug_mode)  # Emit additional WS state when debug enabled.

    @staticmethod
    def _render_result(mac_table_result: dict[str, Any]) -> None:
        """Print the formatted MAC table result block to stdout (legacy formatting preserved)."""
        print("\n" + "=" * 60)  # Legacy top separator line.
        print("MAC TABLE RESULTS:")  # Legacy section header.
        print("=" * 60)  # Legacy separator line.

        raw_output = mac_table_result.get("raw", "")  # Primary documented output channel for show_mac_table.
        output_fields = mac_table_result.get("Output", "")  # Secondary capitalized field for some firmware revs.

        MacTableCommand._render_primary_output(raw_output, output_fields)  # Print well-known output channels.
        MacTableCommand._render_extra_fields(mac_table_result)  # Print any unexpected extra fields.

        if not raw_output and not output_fields:
            print("No output data received")  # Legacy empty-data notice.
            print(f"Available result keys: {list(mac_table_result.keys())}")  # Legacy diagnostic listing.

        print("=" * 60)  # Legacy closing separator line.

    @staticmethod
    def _render_primary_output(raw_output: str, output_fields: str) -> None:
        """Print the `raw` and `Output` channels (the documented MAC table payload locations)."""
        if raw_output:
            print("RAW OUTPUT:")  # Legacy subsection label.
            print("-" * 40)  # Legacy subsection separator.
            print(raw_output)  # Echo device-formatted MAC table text.
        if output_fields and output_fields != raw_output:
            print("\nOTHER OUTPUT:")  # Legacy subsection label.
            print("-" * 40)  # Legacy subsection separator.
            print(output_fields)  # Echo alternate output channel when distinct from raw.

    @staticmethod
    def _render_extra_fields(mac_table_result: dict[str, Any]) -> None:
        """Print any unexpected non-standard fields present in the WS result envelope."""
        available_fields = [
            key for key in mac_table_result.keys() if key not in ["raw", "Output", "session"]
        ]  # Filter out the keys already rendered or used for transport only.
        if not available_fields:
            return  # Nothing extra to display.
        print(f"\nOTHER AVAILABLE FIELDS: {available_fields}")  # Legacy listing line.
        for field in available_fields:
            field_value = mac_table_result.get(field)  # Look up each extra field for echo to operator.
            if field_value:
                print(f"{field}: {field_value}")  # Echo non-empty extras for completeness.
