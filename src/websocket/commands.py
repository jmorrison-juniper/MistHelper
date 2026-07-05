"""WebSocket device command: show MAC table retrieval via Mist API WebSocket stream."""

from __future__ import annotations  # WHY: Postpone annotation evaluation for cross-module type unions.

import logging  # WHY: Structured operational logging for action tracing.
import sys  # WHY: Read CLI argv to detect interactive debug flag.
from typing import Any  # WHY: Dynamic payload typing for vendor JSON shapes.

import requests  # WHY: HTTP client for Mist REST API used to trigger the show_mac_table RPC.

from src.websocket.context import WebSocketCmdDeps  # WHY: Typed dependency bundle injected by orchestrator.
from src.websocket.manager import (  # WHY: WebSocket lifecycle + credential helpers reused across commands.
    WebSocketManager,
    check_mist_credentials,
    cleanup_ws_connection,
    dump_ws_debug_state,
    get_mist_credentials,
    log_ws_error,
    select_ws_site,
)

_RESULT_TRANSPORT_KEYS = frozenset({"raw", "Output", "session"})  # WHY: Fields rendered elsewhere or transport-only.
_WAIT_TIMEOUT_SECONDS = 60  # WHY: Legacy budget matching Mist show_mac_table RPC latency envelope.
_HTTP_TIMEOUT_SECONDS = 30  # WHY: Legacy REST timeout used by the previous inline implementation.


class MacTableCommand:  # WHY: Namespace grouping the show_mac_table workflow helpers as a cohesive unit.
    """Execute the Mist `show_mac_table` switch command over an authenticated WebSocket session.

    MAC tables are a Layer 2 switching feature: routers and access points are excluded
    so operators do not waste time waiting on an unsupported device. The command follows
    the documented Mist pattern: connect WS -> subscribe device channel -> POST RPC ->
    await session-keyed result on the WS stream.
    """

    @staticmethod
    def execute(deps: WebSocketCmdDeps) -> None:  # WHY: Entry-point wired into the operator menu dispatcher.
        """Run the show-MAC-table workflow end-to-end and print results to stdout."""
        debug_mode = MacTableCommand._enter_workflow()  # WHY: Consolidate debug-flag detection and log banner.
        websocket_manager: WebSocketManager | None = None  # WHY: Pre-declare so `finally` cleanup always has binding.
        try:
            websocket_manager = MacTableCommand._run_workflow(deps, debug_mode)  # WHY: Body isolated for CC budget.
        except Exception as mac_table_error:  # WHY: Broad catch preserves legacy operator-facing error banner.
            error_message = f"WebSocket show MAC table operation failed: {mac_table_error}"  # WHY: Legacy text.
            log_ws_error(error_message, debug_mode)  # WHY: Route through shared WS error formatter.
            logging.debug("EXIT: show_mac_table_websocket - error")  # WHY: Preserve legacy exit-trace marker.
        finally:
            cleanup_ws_connection(websocket_manager, debug_mode)  # WHY: Always release WS socket and subscriptions.
            logging.debug("EXIT: show_mac_table_websocket")  # WHY: Preserve legacy exit-trace marker.

    @staticmethod
    def _enter_workflow() -> bool:  # WHY: Isolates debug detection so execute() stays under complexity budget.
        """Log workflow entry, honor --debug flag, and return the resolved debug mode."""
        logging.info("Menu #5: Starting WebSocket show MAC table operation")  # WHY: Log workflow entry boundary.
        debug_mode = "--debug" in sys.argv or "-d" in sys.argv  # WHY: Honor user-supplied verbose-output flag.
        if debug_mode:  # WHY: Gate verbose logger + banner behind operator opt-in.
            logging.getLogger().setLevel(logging.DEBUG)  # WHY: Raise log verbosity for interactive troubleshooting.
            print("[DEBUG] DEBUG MODE ENABLED")  # WHY: Preserve legacy operator-facing debug banner.
        logging.debug("ENTER: show_mac_table_websocket")  # WHY: Preserve legacy enter-trace for log greppability.
        return debug_mode  # WHY: Caller decides whether to escalate downstream helpers into debug output.

    @staticmethod
    def _run_workflow(deps: WebSocketCmdDeps, debug_mode: bool) -> WebSocketManager | None:  # WHY: Body helper.
        """Perform target selection, WS connect, RPC trigger, and result display; return WS manager for cleanup."""
        targets = MacTableCommand._resolve_targets(deps, debug_mode)  # WHY: Prompt operator for site + switch.
        if targets is None:  # WHY: Guard clause — operator abort short-circuits workflow before WS open.
            return None  # WHY: Operator aborted target selection — nothing left to clean up.
        site_id, device_id = targets  # WHY: Unpack chosen IDs for downstream API calls.

        print(f"\n-> Executing show MAC table on device {device_id}...")  # WHY: Preserve legacy progress message.
        print("-> Establishing WebSocket connection...")  # WHY: Preserve legacy progress message.

        websocket_manager = MacTableCommand._open_websocket(deps, site_id, device_id, debug_mode)  # WHY: WS setup.
        if websocket_manager is None:  # WHY: Guard clause — no WS means RPC/response phases must be skipped.
            return None  # WHY: Connect failure already logged inside helper; nothing to display.

        session_id = MacTableCommand._trigger_rpc(  # WHY: Kick off REST RPC that produces the WS session id.
            deps, websocket_manager, site_id, device_id, debug_mode
        )
        if session_id is None:  # WHY: Guard clause — RPC helper already disconnected WS on failure.
            return websocket_manager  # WHY: RPC helper disconnected on failure; return manager for cleanup finalize.

        MacTableCommand._announce_session(session_id, debug_mode)  # WHY: Emit legacy progress + debug detail lines.
        MacTableCommand._await_and_display(websocket_manager, session_id, debug_mode)  # WHY: Block on WS result.
        return websocket_manager  # WHY: Hand back manager so finally cleanup runs uniformly.

    @staticmethod
    def _announce_session(session_id: str, debug_mode: bool) -> None:  # WHY: Extract print block from run_workflow.
        """Print legacy progress banners after a successful RPC trigger."""
        print(f"-> Show MAC table command issued (session: {session_id[:8]}...)")  # WHY: Legacy progress message.
        print("-> Waiting for MAC table results...")  # WHY: Legacy progress message.
        if debug_mode:  # WHY: Gate detailed session-id echo behind operator opt-in.
            print(f"[DEBUG] Full session ID = {session_id}")  # WHY: Legacy debug detail line.
            print("[DEBUG] Starting to wait for WebSocket results...")  # WHY: Legacy debug detail line.

    @staticmethod
    def _resolve_targets(deps: WebSocketCmdDeps, debug_mode: bool) -> tuple[str, str] | None:  # WHY: Prompt helper.
        """Prompt operator for the site and switch device and return their IDs, or None on abort."""
        logging.info("Prompting operator for WebSocket MAC table target site")  # WHY: Log before interactive prompt.
        site_id = select_ws_site(deps, debug_mode)  # WHY: Interactive site selection via shared helper.
        logging.debug("Site selection result: %s", site_id)  # WHY: Log result without leaking richer data.
        if site_id is None:  # WHY: Guard clause — abort cleanly when operator cancels site pick.
            return None  # WHY: Operator cancelled site selection — propagate abort.

        print("-> MAC table is available on switches (Layer 2 devices)")  # WHY: Legacy operator guidance line.
        print("-> Routers/gateways operate at Layer 3 and typically don't maintain MAC tables")  # WHY: Legacy.
        print("-> APs forward wireless traffic but don't maintain traditional MAC tables")  # WHY: Legacy guidance.

        logging.info("Prompting operator to select a switch device under site %s", site_id)  # WHY: Before pick.
        device_id = deps.select_device_fn(site_id, device_type="switch")  # WHY: Filter pick list to switches only.
        logging.debug("Device selection result: %s", device_id)  # WHY: Log selection result for traceability.
        if not device_id:  # WHY: Guard clause — a MAC table requires a Layer-2 device.
            print("! No switch device selected. MAC table command requires Layer 2 switching devices.")  # WHY: Legacy.
            print("! Only switches maintain MAC address learning tables for Ethernet forwarding.")  # WHY: Legacy.
            return None  # WHY: Operator declined to pick a switch — abort cleanly.

        if debug_mode:  # WHY: Emit device-id detail only when operator opted into verbose output.
            print(f"[DEBUG] Selected device_id = {device_id}")  # WHY: Legacy debug detail line.
        return site_id, device_id  # WHY: Return resolved tuple for orchestrator continuation.

    @staticmethod
    def _open_websocket(
        deps: WebSocketCmdDeps, site_id: str, device_id: str, debug_mode: bool
    ) -> WebSocketManager | None:  # WHY: Encapsulates WS handshake so caller stays under length budget.
        """Construct WS manager and perform connect+subscribe, returning manager on success or None on failure."""
        logging.info("Opening WebSocket and subscribing to device %s on site %s", device_id, site_id)  # WHY: Before.
        websocket_manager = WebSocketManager(deps.apisession)  # WHY: Build manager bound to current auth session.
        connected = websocket_manager.connect_and_subscribe(site_id, device_id, debug_mode)  # WHY: WS open + sub.
        logging.debug("WebSocket connect_and_subscribe returned: %s", connected)  # WHY: After-call trace.
        if not connected:
            return None  # WHY: Connection failure — caller returns without printing extra text.
        return websocket_manager  # WHY: Manager ready for RPC + result wait.

    @staticmethod
    def _trigger_rpc(
        deps: WebSocketCmdDeps,
        websocket_manager: WebSocketManager,
        site_id: str,
        device_id: str,
        debug_mode: bool,
    ) -> str | None:
        """POST the show_mac_table RPC and return the Mist session id, or None on failure."""
        credentials = MacTableCommand._resolve_and_check_credentials(deps, websocket_manager, debug_mode)
        if credentials is None:
            return None  # WHY: Credential validator already emitted operator-facing diagnostics.
        mist_host, mist_apitoken = credentials  # WHY: Unpack for URL/header assembly.

        response = MacTableCommand._post_show_mac_table(
            mist_host, mist_apitoken, site_id, device_id, debug_mode
        )  # WHY: Isolated HTTP call keeps this function's block count under limit.
        return MacTableCommand._extract_session_id(response, websocket_manager)  # WHY: Handle status + JSON envelope.

    @staticmethod
    def _resolve_and_check_credentials(
        deps: WebSocketCmdDeps, websocket_manager: WebSocketManager, debug_mode: bool
    ) -> tuple[str, str] | None:
        """Return (host, token) when credentials pass validation, otherwise None."""
        logging.info("Resolving Mist credentials for direct REST RPC")  # WHY: Log before credential lookup action.
        mist_host, mist_apitoken = get_mist_credentials(deps.apisession)  # WHY: Extract host + token from session.
        logging.debug("Mist credentials resolved (host=%s, token=[REDACTED])", mist_host)  # WHY: Result, redacted.
        if not check_mist_credentials(websocket_manager, mist_host, mist_apitoken, debug_mode):
            return None  # WHY: Validator failed and already printed operator-facing text.
        return mist_host, mist_apitoken  # WHY: Caller uses tuple to assemble RPC URL + auth headers.

    @staticmethod
    def _post_show_mac_table(
        mist_host: str, mist_apitoken: str, site_id: str, device_id: str, debug_mode: bool
    ) -> requests.Response:
        """Issue the REST RPC that initiates the WebSocket session response and return the raw response."""
        mac_table_payload: dict[str, Any] = {}  # WHY: show_mac_table requires no additional parameters.
        print("-> Issuing show MAC table command...")  # WHY: Legacy progress message.
        logging.debug("MAC table payload: %s", mac_table_payload)  # WHY: Trace request body (always empty by design).
        if debug_mode:
            print(f"[DEBUG] MAC table payload = {mac_table_payload}")  # WHY: Legacy debug detail line.
        mac_table_url = f"https://{mist_host}/api/v1/sites/{site_id}/devices/{device_id}/show_mac_table"  # WHY: URL.
        headers = {"Authorization": f"Token {mist_apitoken}", "Content-Type": "application/json"}  # WHY: Auth head.
        if debug_mode:
            print(f"[DEBUG] POST URL = {mac_table_url}")  # WHY: Legacy debug detail line.
            print("[DEBUG] Headers = {'Authorization': 'Token [REDACTED]', 'Content-Type': 'application/json'}")
        logging.info("POST %s to trigger show_mac_table RPC", mac_table_url)  # WHY: Log before HTTP request action.
        response = requests.post(  # WHY: Issue REST RPC that initiates the WebSocket session response.
            mac_table_url, headers=headers, json=mac_table_payload, timeout=_HTTP_TIMEOUT_SECONDS
        )
        logging.debug("show_mac_table HTTP status=%s", response.status_code)  # WHY: After-call result.
        if debug_mode:
            print(f"[DEBUG] HTTP Response Status = {response.status_code}")  # WHY: Legacy debug line.
            print(f"[DEBUG] HTTP Response Body = {response.text}")  # WHY: Legacy debug line.
        return response  # WHY: Hand response back to extractor for status + session-id parsing.

    @staticmethod
    def _extract_session_id(response: requests.Response, websocket_manager: WebSocketManager) -> str | None:
        """Return the Mist-assigned session id, disconnecting the WS if the response is unusable."""
        if response.status_code != 200:
            print(f"! Failed to issue show MAC table command: {response.status_code}")  # WHY: Legacy error.
            print(f"! Response: {response.text}")  # WHY: Legacy error body echo for operator diagnosis.
            websocket_manager.disconnect()  # WHY: Free WS socket since we won't await a result.
            return None  # WHY: Signal failure to orchestrator.
        response_data = response.json()  # WHY: Parse JSON envelope returning the session correlation id.
        session_id = response_data.get("session")  # WHY: Extract Mist-assigned session id used to demux WS messages.
        if not session_id:
            print("! No session ID returned from show MAC table command")  # WHY: Legacy error message.
            websocket_manager.disconnect()  # WHY: No correlation id means no result can arrive — close WS.
            return None  # WHY: Signal failure to orchestrator.
        return session_id  # WHY: Caller blocks on websocket_manager.wait_for_command_result(session_id).

    @staticmethod
    def _await_and_display(websocket_manager: WebSocketManager, session_id: str, debug_mode: bool) -> None:
        """Block on the WS result for the given session and render formatted output."""
        logging.info("Waiting for MAC table result on session %s", session_id)  # WHY: Log before blocking WS wait.
        mac_table_result = websocket_manager.wait_for_command_result(
            session_id, timeout_seconds=_WAIT_TIMEOUT_SECONDS
        )  # WHY: 60s budget matches legacy behavior.
        logging.debug(
            "wait_for_command_result returned populated=%s", mac_table_result is not None
        )  # WHY: After-call summary.
        if debug_mode:
            print(f"[DEBUG] wait_for_command_result returned: {mac_table_result is not None}")  # WHY: Legacy line.
            if mac_table_result:
                print(f"[DEBUG] Result keys: {list(mac_table_result.keys())}")  # WHY: Legacy debug detail.

        if mac_table_result:
            MacTableCommand._render_result(mac_table_result)  # WHY: Pretty-print MAC table fields to stdout.
            logging.info("WebSocket show MAC table completed successfully")  # WHY: Log success outcome.
            return  # WHY: Done — successful path.

        MacTableCommand._render_timeout(websocket_manager, debug_mode)  # WHY: Emit legacy timeout diagnostics.

    @staticmethod
    def _render_timeout(websocket_manager: WebSocketManager, debug_mode: bool) -> None:
        """Print legacy timeout banner and dump WS debug state if enabled."""
        print("! Timeout waiting for MAC table results")  # WHY: Legacy timeout banner.
        print("! This may indicate:")  # WHY: Legacy diagnostic preface.
        print("  - The device doesn't support MAC table commands (common for routers/Layer 3 devices)")  # WHY.
        print("  - The device is busy or not responding")  # WHY: Legacy diagnostic hint.
        print("  - Network connectivity issues")  # WHY: Legacy diagnostic hint.
        print("! Note: MAC tables are primarily a Layer 2 (switch) feature")  # WHY: Legacy diagnostic reminder.
        logging.warning("WebSocket show MAC table operation timed out")  # WHY: Log timeout outcome.
        dump_ws_debug_state(websocket_manager, debug_mode)  # WHY: Emit additional WS state when debug enabled.

    @staticmethod
    def _render_result(mac_table_result: dict[str, Any]) -> None:
        """Print the formatted MAC table result block to stdout (legacy formatting preserved)."""
        print("\n" + "=" * 60)  # WHY: Legacy top separator line.
        print("MAC TABLE RESULTS:")  # WHY: Legacy section header.
        print("=" * 60)  # WHY: Legacy separator line.

        raw_output = mac_table_result.get("raw", "")  # WHY: Primary documented output channel for show_mac_table.
        output_fields = mac_table_result.get("Output", "")  # WHY: Secondary capitalized field for some firmware revs.

        MacTableCommand._render_primary_output(raw_output, output_fields)  # WHY: Print well-known output channels.
        MacTableCommand._render_extra_fields(mac_table_result)  # WHY: Print any unexpected extra fields.

        if not raw_output and not output_fields:
            print("No output data received")  # WHY: Legacy empty-data notice.
            print(f"Available result keys: {list(mac_table_result.keys())}")  # WHY: Legacy diagnostic listing.

        print("=" * 60)  # WHY: Legacy closing separator line.

    @staticmethod
    def _render_primary_output(raw_output: str, output_fields: str) -> None:
        """Print the `raw` and `Output` channels (the documented MAC table payload locations)."""
        if raw_output:
            print("RAW OUTPUT:")  # WHY: Legacy subsection label.
            print("-" * 40)  # WHY: Legacy subsection separator.
            print(raw_output)  # WHY: Echo device-formatted MAC table text.
        if output_fields and output_fields != raw_output:
            print("\nOTHER OUTPUT:")  # WHY: Legacy subsection label.
            print("-" * 40)  # WHY: Legacy subsection separator.
            print(output_fields)  # WHY: Echo alternate output channel when distinct from raw.

    @staticmethod
    def _render_extra_fields(mac_table_result: dict[str, Any]) -> None:
        """Print any unexpected non-standard fields present in the WS result envelope."""
        extras = MacTableCommand._collect_extras(mac_table_result)  # WHY: Filter transport keys via module constant.
        if not extras:
            return  # WHY: Nothing extra to display.
        print(f"\nOTHER AVAILABLE FIELDS: {list(extras.keys())}")  # WHY: Legacy listing line for operator visibility.
        for field, field_value in extras.items():
            print(f"{field}: {field_value}")  # WHY: Echo non-empty extras for completeness.

    @staticmethod
    def _collect_extras(mac_table_result: dict[str, Any]) -> dict[str, Any]:
        """Return non-empty non-transport fields keyed for stable ordering."""
        return {
            key: value for key, value in mac_table_result.items() if key not in _RESULT_TRANSPORT_KEYS and value
        }  # WHY: Dict-comp collapses filter + truth check into a single expression to keep caller CC low.
