"""ArpDeviceExecutor: orchestrate ARP-over-WebSocket diagnostic workflow."""

from __future__ import annotations  # WHY: forward refs for WebSocketManager and typing.

import json  # WHY: parse gateway JSON ARP responses.
import logging  # WHY: action-observability trace for operator diagnostics.
from typing import Any  # WHY: generic typing for JSON-shaped payloads.

from src.websocket.context import WebSocketCmdDeps  # WHY: injected dependency bundle.
from src.websocket.diagnostics.common import (  # WHY: shared executor helpers.
    detect_debug_mode,
    extract_command_session,
    post_device_command,
    prepare_command_credentials,
)
from src.websocket.manager import (  # WHY: WebSocket lifecycle + error utilities.
    WebSocketManager,
    cleanup_ws_connection,
    log_ws_error,
    select_ws_site,
)

_TIMEOUT_SWITCH = 45  # WHY: extended ARP timeout for switches (legacy value).
_TIMEOUT_GATEWAY = 35  # WHY: extended ARP timeout for gateways (legacy value).
_TIMEOUT_DEFAULT = 30  # WHY: default ARP timeout for APs / unknown devices.
_MAX_COLUMN_WIDTH = 20  # WHY: cap column width when rendering gateway ARP tables.

_TIMEOUT_TABLE: dict[str, tuple[int, str]] = {  # WHY: table-driven timeout dispatch.
    "switch": (_TIMEOUT_SWITCH, "   -> Using extended timeout for switch (45 seconds)"),
    "gateway": (_TIMEOUT_GATEWAY, "   -> Using extended timeout for gateway (35 seconds)"),
}

_COMPAT_NOTES: dict[str, tuple[str, str]] = {  # WHY: table-driven compat-note dispatch.
    "gateway": (
        "!? Gateway detected (Model: {model})",
        "   -> Gateways have good WebSocket ARP support\n" "   -> Results may differ from Access Points",
    ),
    "ap": (
        "!? Access Point detected (Model: {model})",
        "   -> Access Points have full WebSocket ARP support",
    ),
}

_DEVICE_HEADER_NOTES: dict[str, str] = {  # WHY: table-driven header-note dispatch.
    "switch": "Note: Switch ARP data may show forwarding table or limited ARP information",
    "gateway": "Note: Gateway ARP data may include routing information",
    "ap": "Note: Access Point ARP data shows client connectivity information",
}


class ArpDeviceExecutor:  # WHY: orchestrates ARP-over-WebSocket diagnostic workflow.
    """Run an interactive ARP command on a Mist device via the WebSocket stream."""

    def execute(self, deps: WebSocketCmdDeps) -> None:  # WHY: top-level workflow entry.
        """Top-level entry: prompt user, run ARP, render results."""
        logging.info("Starting WebSocket ARP operation...")  # WHY: action log at workflow start.
        logging.debug("ENTER: arp_device_websocket")  # WHY: trace marker preserved.
        debug_mode = detect_debug_mode()  # WHY: honor --debug / -d once per run.
        if debug_mode:  # WHY: mirror legacy debug banner.
            print("[DEBUG] Starting ARP via WebSocket operation...")  # WHY: legacy banner.
        websocket_manager: WebSocketManager | None = None  # WHY: tracked for finally cleanup.
        try:  # WHY: mirror legacy try/except/finally so cleanup always runs.
            websocket_manager = self._run_workflow(deps, debug_mode)  # WHY: drive workflow.
        except Exception as arp_error:  # WHY: match legacy resilience broad catch.
            log_ws_error(f"WebSocket ARP operation failed: {arp_error}", False)  # WHY: legacy log.
            logging.debug("EXIT: arp_device_websocket - error")  # WHY: trace marker preserved.
        finally:  # WHY: always release WS resources on any exit path.
            cleanup_ws_connection(websocket_manager)  # WHY: disconnect if connected.
            logging.debug("EXIT: arp_device_websocket")  # WHY: trace marker preserved.

    def _run_workflow(  # WHY: drive site+device prompts, compat check, and ARP dispatch.
        self, deps: WebSocketCmdDeps, debug_mode: bool
    ) -> WebSocketManager | None:
        """Prompt for site+device, check compatibility, run ARP. Returns WS for cleanup."""
        site_id = select_ws_site(deps, debug_mode)  # WHY: interactive site picker.
        if site_id is None:  # WHY: user cancelled site selection.
            return None  # WHY: skip rest of workflow.
        device_id = deps.select_device_fn(site_id, device_type="all")  # WHY: device picker.
        if not device_id:  # WHY: user cancelled or no devices available.
            print("! No device selected. Operation cancelled.")  # WHY: legacy phrasing.
            return None  # WHY: skip rest of workflow.
        if debug_mode:  # WHY: legacy debug echo of chosen device id.
            print(f"[DEBUG] Selected device_id = {device_id}")  # WHY: legacy phrasing.
        device_info = self._fetch_device_info(deps, site_id, device_id, debug_mode)  # WHY: meta.
        if not self._maybe_warn_and_confirm(deps, device_info):  # WHY: compat / cancel gate.
            return None  # WHY: user declined to proceed.
        return self._issue_arp_and_render(  # WHY: connect, POST, await, render.
            deps, site_id, device_id, device_info, debug_mode
        )

    def _fetch_device_info(  # WHY: resolve device metadata for compat/timeout decisions.
        self,
        deps: WebSocketCmdDeps,
        site_id: str,
        device_id: str,
        debug_mode: bool,
    ) -> dict[str, Any] | None:
        """Look up device record for type/model context. Return None if unavailable."""
        logging.debug("Fetching device record for ARP target device=%s", device_id)  # WHY: log.
        device_info = self._lookup_device_record(deps, site_id, device_id, debug_mode)  # WHY: API.
        if device_info and debug_mode:  # WHY: legacy debug echo of resolved attributes.
            self._echo_device_attributes(device_info, device_id)  # WHY: legacy debug line.
        logging.debug("Device record resolved present=%s", device_info is not None)  # WHY: log.
        return device_info  # WHY: caller uses metadata for compat + timeout selection.

    @staticmethod
    def _lookup_device_record(  # WHY: isolate broad try/except for the device list call.
        deps: WebSocketCmdDeps,
        site_id: str,
        device_id: str,
        debug_mode: bool,
    ) -> dict[str, Any] | None:
        """Call the device list API and pick the matching record. None on failure."""
        try:  # WHY: legacy swallows errors so ARP attempt still proceeds.
            rawdata = deps.list_devices_fn(deps.apisession, site_id, type="all").data  # WHY: API.
        except Exception as device_check_error:  # WHY: match legacy broad catch.
            logging.warning(  # WHY: action log after failed lookup.
                "Could not verify device compatibility: %s", device_check_error
            )
            if debug_mode:  # WHY: legacy debug echo of the failure.
                print(f"[DEBUG] Device check failed: {device_check_error}")  # WHY: legacy line.
            print("   -> Proceeding with standard ARP command")  # WHY: legacy phrasing preserved.
            return None  # WHY: caller proceeds with no device-context.
        return next(  # WHY: walk list for the chosen device id.
            (entry for entry in rawdata if entry.get("id") == device_id), None
        )

    @staticmethod
    def _echo_device_attributes(  # WHY: legacy debug line describing resolved device.
        device_info: dict[str, Any], device_id: str
    ) -> None:
        """Print the legacy debug line describing the resolved device."""
        device_type = device_info.get("type", "unknown")  # WHY: pull type for echo.
        device_model = device_info.get("model", "unknown")  # WHY: pull model for echo.
        device_name = device_info.get("name", f"Device {device_id[:8]}")  # WHY: pull name.
        print(  # WHY: single legacy debug line preserved verbatim.
            f"[DEBUG] Device type: {device_type}, model: {device_model}, name: {device_name}"
        )

    def _maybe_warn_and_confirm(  # WHY: gate on device-type compatibility notes and prompt.
        self,
        deps: WebSocketCmdDeps,
        device_info: dict[str, Any] | None,
    ) -> bool:
        """Print device-type compatibility notes. Ask switches to confirm. Returns proceed."""
        if not device_info:  # WHY: no metadata means proceed (legacy behavior).
            return True  # WHY: proceed unconditionally to preserve legacy behavior.
        device_type = device_info.get("type", "unknown")  # WHY: branch by device type.
        device_model = device_info.get("model", "unknown")  # WHY: surface model in messages.
        if device_type == "switch":  # WHY: switches need explicit confirmation per legacy.
            return self._confirm_switch_arp(deps, device_model)  # WHY: prompt operator.
        note = _COMPAT_NOTES.get(device_type)  # WHY: table-driven note dispatch.
        if note is not None:  # WHY: gateway / AP path uses table entry.
            print(note[0].format(model=device_model))  # WHY: legacy header line preserved.
            print(note[1])  # WHY: legacy detail lines preserved.
            return True  # WHY: proceed for gateway / AP paths.
        print(f"? Unknown device type: {device_type} (Model: {device_model})")  # WHY: legacy.
        print("   -> Proceeding with standard ARP command")  # WHY: legacy phrasing preserved.
        return True  # WHY: proceed with standard command.

    @staticmethod
    def _confirm_switch_arp(  # WHY: interactive switch-only confirmation.
        deps: WebSocketCmdDeps, device_model: str
    ) -> bool:
        """Warn about switch ARP limitations and require explicit y/yes to proceed."""
        print(f"!?  WARNING: Switch detected (Model: {device_model})")  # WHY: legacy phrasing.
        print("   -> Switches may have limited WebSocket ARP support")  # WHY: legacy phrasing.
        print("   -> Consider using SSH-based ARP commands instead")  # WHY: legacy phrasing.
        print("   -> This operation may timeout or return limited results")  # WHY: legacy.
        logging.info(  # WHY: action log before blocking on user input.
            "Prompting operator to confirm switch ARP attempt model=%s", device_model
        )
        response = (  # WHY: EOF-safe input wrapper drops newline, lower-case for match.
            deps.safe_input_fn("   -> Continue anyway? (y/N): ", context="websocket_arp").strip().lower()
        )
        if response in ("y", "yes"):  # WHY: legacy affirmative answers.
            logging.debug("Switch ARP attempt confirmed by operator")  # WHY: after log on confirm.
            return True  # WHY: caller proceeds.
        print("! Operation cancelled by user")  # WHY: legacy phrasing preserved.
        logging.info("Switch ARP attempt cancelled by operator")  # WHY: after log on cancel.
        return False  # WHY: caller aborts.

    def _issue_arp_and_render(  # WHY: connect WS, POST ARP, await results, render output.
        self,
        deps: WebSocketCmdDeps,
        site_id: str,
        device_id: str,
        device_info: dict[str, Any] | None,
        debug_mode: bool,
    ) -> WebSocketManager | None:
        """Connect WS, POST ARP, await results, render output. Returns WS for cleanup."""
        websocket_manager = self._connect_ws(deps, site_id, device_id, debug_mode)  # WHY: WS.
        if websocket_manager is None:  # WHY: connect failure short-circuits workflow.
            return None  # WHY: caller has nothing to clean up.
        print("-> Issuing ARP command...")  # WHY: legacy banner preserved.
        session_id = self._post_arp_command(  # WHY: POST + demux session id.
            deps, websocket_manager, site_id, device_id, debug_mode
        )
        if session_id is None:  # WHY: POST failed. Helpers already disconnected.
            return websocket_manager  # WHY: hand to finally for cleanup.
        self._await_and_render(  # WHY: wait for the WS result then render to console.
            websocket_manager, session_id, device_info, device_id, debug_mode
        )
        return websocket_manager  # WHY: hand to finally for cleanup.

    @staticmethod
    def _connect_ws(  # WHY: build WS manager and subscribe. None on connect failure.
        deps: WebSocketCmdDeps,
        site_id: str,
        device_id: str,
        debug_mode: bool,
    ) -> WebSocketManager | None:
        """Build a WebSocketManager and subscribe to the device. None returns skip caller."""
        print(f"\n-> Executing ARP command on device {device_id}...")  # WHY: legacy banner.
        print("-> Establishing WebSocket connection...")  # WHY: legacy banner preserved.
        websocket_manager = WebSocketManager(deps.apisession)  # WHY: per-run WS manager.
        logging.info(  # WHY: action log before connect+subscribe.
            "Connecting WebSocket for ARP site=%s device=%s", site_id, device_id
        )
        if not websocket_manager.connect_and_subscribe(site_id, device_id, debug_mode):  # WHY: sub.
            logging.warning("WebSocket connect+subscribe failed for ARP")  # WHY: after log.
            return websocket_manager  # WHY: hand to finally for cleanup.
        logging.debug("WebSocket connect+subscribe succeeded for ARP")  # WHY: after log.
        return websocket_manager  # WHY: caller proceeds with POST + wait.

    def _post_arp_command(  # WHY: POST device-scoped ARP endpoint, demux session id.
        self,
        deps: WebSocketCmdDeps,
        websocket_manager: WebSocketManager,
        site_id: str,
        device_id: str,
        debug_mode: bool,
    ) -> str | None:
        """POST the ARP command and return the session id (or None on failure)."""
        credentials = prepare_command_credentials(  # WHY: pull + validate Mist host/token.
            deps.apisession, websocket_manager, debug_mode
        )
        if credentials is None:  # WHY: credential lookup failed. Helper disconnected.
            return None  # WHY: caller aborts the workflow.
        mist_host, mist_apitoken = credentials  # WHY: unpack into local variables.
        arp_url, headers = self._build_arp_request(  # WHY: build request tuple.
            mist_host, mist_apitoken, site_id, device_id
        )
        arp_response = post_device_command(arp_url, headers, {}, debug_mode, "ARP")  # WHY: POST.
        if arp_response is None:  # WHY: defensive. Helper currently never returns None.
            return None  # WHY: treat as POST failure.
        return extract_command_session(arp_response, websocket_manager, "ARP")  # WHY: demux.

    @staticmethod
    def _build_arp_request(  # WHY: assemble URL + REST headers for ARP endpoint.
        mist_host: str,
        mist_apitoken: str,
        site_id: str,
        device_id: str,
    ) -> tuple[str, dict[str, str]]:
        """Return the (url, headers) pair for the device-scoped ARP REST call."""
        arp_url = (  # WHY: device-scoped ARP endpoint URL.
            f"https://{mist_host}/api/v1/sites/{site_id}/devices/{device_id}/arp"
        )
        headers = {  # WHY: REST headers required by the Mist API.
            "Authorization": f"Token {mist_apitoken}",
            "Content-Type": "application/json",
        }
        return arp_url, headers  # WHY: caller passes tuple to post_device_command.

    def _await_and_render(  # WHY: block on WS result then dispatch success/timeout render.
        self,
        websocket_manager: WebSocketManager,
        session_id: str,
        device_info: dict[str, Any] | None,
        device_id: str,
        debug_mode: bool,
    ) -> None:
        """Wait for the ARP result on the WS, then render it or report timeout."""
        self._announce_wait(session_id, debug_mode)  # WHY: legacy banner + debug lines.
        timeout_seconds = self._compute_timeout(device_info)  # WHY: type-aware timeout.
        logging.info(  # WHY: action log before blocking wait.
            "Awaiting ARP result session=%s timeout=%ds", session_id[:8], timeout_seconds
        )
        arp_result = websocket_manager.wait_for_command_result(  # WHY: block until result.
            session_id, timeout_seconds=timeout_seconds
        )
        logging.debug("ARP wait completed; has_result=%s", arp_result is not None)  # WHY: log.
        if debug_mode:  # WHY: legacy debug echo of wait outcome + shape.
            self._echo_wait_outcome(arp_result)  # WHY: emit legacy debug lines.
        if arp_result:  # WHY: success path renders the captured payload.
            self._render_arp_result(arp_result, device_info, device_id, debug_mode)  # WHY: ok.
            return  # WHY: done rendering successful result.
        self._render_timeout(device_info)  # WHY: timeout path with type-aware help.

    @staticmethod
    def _announce_wait(session_id: str, debug_mode: bool) -> None:
        """Print the legacy banner + optional debug lines announcing the wait."""
        print(f"-> ARP command issued (session: {session_id[:8]}...)")  # WHY: legacy banner.
        print("-> Waiting for ARP results...")  # WHY: legacy banner preserved.
        if debug_mode:  # WHY: mirror legacy debug prints of session + waiting state.
            print(f"[DEBUG] Full session ID = {session_id}")  # WHY: legacy debug line.
            print("[DEBUG] Starting to wait for WebSocket results...")  # WHY: legacy line.

    @staticmethod
    def _echo_wait_outcome(arp_result: dict[str, Any] | None) -> None:
        """Print the legacy debug summary of the wait outcome shape."""
        print(f"[DEBUG] wait_for_command_result returned: {arp_result is not None}")  # WHY: line.
        if arp_result:  # WHY: only echo keys when a payload was returned.
            print(f"[DEBUG] Result keys: {list(arp_result.keys())}")  # WHY: legacy debug echo.

    @staticmethod
    def _compute_timeout(device_info: dict[str, Any] | None) -> int:
        """Pick the WS wait timeout based on device type, printing legacy notice line."""
        if not device_info:  # WHY: baseline timeout when metadata missing.
            return _TIMEOUT_DEFAULT  # WHY: APs / unknown fall through to baseline.
        device_type = device_info.get("type", "unknown")  # WHY: switch on type for timeout.
        entry = _TIMEOUT_TABLE.get(device_type)  # WHY: table-driven timeout dispatch.
        if entry is None:  # WHY: APs / unknown fall through to baseline.
            return _TIMEOUT_DEFAULT  # WHY: legacy fallback timeout.
        timeout_seconds, notice = entry  # WHY: destructure tuple from dispatch table.
        print(notice)  # WHY: legacy notice line preserved verbatim.
        return timeout_seconds  # WHY: caller uses value in wait_for_command_result.

    def _render_arp_result(  # WHY: dispatch banner + body + footer sections for success.
        self,
        arp_result: dict[str, Any],
        device_info: dict[str, Any] | None,
        device_id: str,
        debug_mode: bool,
    ) -> None:
        """Render an ARP success payload, dispatching gateway JSON to the table renderer."""
        self._print_result_banner()  # WHY: legacy header block preserved.
        self._render_device_context(device_info)  # WHY: optional device-context block.
        raw_output = arp_result.get("raw", "")  # WHY: primary output field in the schema.
        parsed_output = arp_result.get("Output", "")  # WHY: secondary output (often empty).
        self._render_output_sections(  # WHY: pick raw/parsed/empty branch.
            raw_output, parsed_output, device_info, debug_mode
        )
        print("=" * 60)  # WHY: legacy visual closer preserved verbatim.
        device_context = self._format_device_context(device_info, device_id)  # WHY: log payload.
        logging.info("WebSocket ARP completed successfully for %s", device_context)  # WHY: log.

    @staticmethod
    def _print_result_banner() -> None:
        """Emit the legacy header block above ARP success output."""
        print("\n" + "=" * 60)  # WHY: legacy visual separator preserved.
        print("ARP TABLE RESULTS:")  # WHY: legacy header preserved verbatim.
        print("=" * 60)  # WHY: legacy visual separator preserved.

    def _render_output_sections(  # WHY: pick raw/parsed/empty branches for success payloads.
        self,
        raw_output: str,
        parsed_output: str,
        device_info: dict[str, Any] | None,
        debug_mode: bool,
    ) -> None:
        """Render the raw / parsed / empty result sections for a successful ARP call."""
        if not raw_output and not parsed_output:  # WHY: empty-result diagnostic path.
            self._render_empty_result(device_info)  # WHY: emit legacy phrasing block.
            return  # WHY: nothing further to render.
        if raw_output:  # WHY: gateway-table vs raw-passthrough decision lives here.
            self._render_raw_output_block(raw_output, device_info, debug_mode)  # WHY: raw.
        self._maybe_render_parsed(raw_output, parsed_output)  # WHY: optional parsed section.

    @staticmethod
    def _maybe_render_parsed(raw_output: str, parsed_output: str) -> None:
        """Print the PARSED OUTPUT block when it differs from the raw echo."""
        if not parsed_output or parsed_output == raw_output:  # WHY: skip duplicate echo.
            return  # WHY: nothing new to print.
        print("\nPARSED OUTPUT:")  # WHY: legacy section header preserved.
        print("-" * 40)  # WHY: legacy section underline preserved.
        print(parsed_output)  # WHY: show captured parsed text.

    @staticmethod
    def _render_empty_result(device_info: dict[str, Any] | None) -> None:
        """Print the legacy empty-result diagnostic block with switch-only tips."""
        print("No output data received")  # WHY: legacy phrasing preserved.
        if device_info and device_info.get("type") == "switch":  # WHY: switch-only tips.
            print("\nTroubleshooting for switches:")  # WHY: legacy phrasing preserved.
            print("-> Try using SSH-based commands instead")  # WHY: legacy phrasing.
            print("-> Some switches require specific ARP command syntax")  # WHY: legacy.
            print("-> WebSocket API may have limited switch support")  # WHY: legacy phrasing.

    @staticmethod
    def _render_device_context(device_info: dict[str, Any] | None) -> None:
        """Print the device-type context header when device metadata is available."""
        if not device_info:  # WHY: nothing to render without metadata.
            return  # WHY: skip header section entirely.
        device_type = device_info.get("type", "unknown")  # WHY: switch on type for note.
        device_model = device_info.get("model", "unknown")  # WHY: surface model in header.
        device_name = device_info.get("name", "Unknown Device")  # WHY: surface name in header.
        print(f"Device: {device_name} ({device_type.upper()}: {device_model})")  # WHY: header.
        note = _DEVICE_HEADER_NOTES.get(device_type)  # WHY: table-driven note dispatch.
        if note is not None:  # WHY: emit note when device type is known.
            print(note)  # WHY: legacy per-type note line preserved.
        print("-" * 60)  # WHY: legacy underline preserved verbatim.

    def _render_raw_output_block(  # WHY: choose gateway table renderer or raw passthrough.
        self,
        raw_output: str,
        device_info: dict[str, Any] | None,
        debug_mode: bool,
    ) -> None:
        """Render raw output. If gateway JSON, dispatch to table renderer."""
        is_gateway = device_info is not None and device_info.get("type") == "gateway"  # WHY: gate.
        looks_like_json = raw_output.strip().startswith("{")  # WHY: cheap JSON sniff.
        if is_gateway and looks_like_json:  # WHY: try tabulate for gateway JSON responses.
            self._render_gateway_table_or_fallback(raw_output, debug_mode)  # WHY: dispatch.
            return  # WHY: gateway path handled fully by helper.
        print("RAW OUTPUT:")  # WHY: legacy section header preserved.
        print("-" * 40)  # WHY: legacy section underline preserved.
        print(raw_output)  # WHY: show captured raw text verbatim.

    def _render_gateway_table_or_fallback(  # WHY: parse gateway JSON. Fall back on failure.
        self, raw_output: str, debug_mode: bool
    ) -> None:
        """Parse gateway JSON ARP response. Tabulate on success, fall back on failure."""
        logging.debug("Attempting to parse gateway ARP JSON payload")  # WHY: log before parse.
        try:  # WHY: match legacy fallback phrasing on JSON parse failure.
            gateway_data = json.loads(raw_output)  # WHY: decode the JSON document.
        except json.JSONDecodeError as json_error:  # WHY: fall back to raw echo on failure.
            self._fallback_gateway_output(raw_output, debug_mode, json_error)  # WHY: legacy.
            return  # WHY: done with fallback path.
        if gateway_data.get("status") != "SUCCESS" or "rows" not in gateway_data:  # WHY: check.
            print("Gateway response format not recognized")  # WHY: legacy phrasing preserved.
            self._echo_raw_fallback(raw_output)  # WHY: emit legacy raw echo block.
            return  # WHY: done with fallback path.
        self._render_gateway_arp_table(gateway_data, raw_output, debug_mode)  # WHY: tabulate.

    def _fallback_gateway_output(  # WHY: emit legacy JSON-parse-failure block.
        self,
        raw_output: str,
        debug_mode: bool,
        json_error: json.JSONDecodeError,
    ) -> None:
        """Print the JSON-parse-failure fallback (legacy phrasing + raw echo)."""
        if debug_mode:  # WHY: legacy debug echo of the parse error.
            print(f"[DEBUG] Failed to parse gateway JSON: {json_error}")  # WHY: legacy line.
        logging.warning("Gateway ARP JSON parse failed: %s", json_error)  # WHY: after log.
        print("Failed to parse gateway JSON output")  # WHY: legacy phrasing preserved.
        self._echo_raw_fallback(raw_output)  # WHY: emit legacy raw echo block.

    @staticmethod
    def _echo_raw_fallback(raw_output: str) -> None:
        """Emit the legacy 'RAW OUTPUT:' fallback block with underline."""
        print("RAW OUTPUT:")  # WHY: legacy fallback section header preserved.
        print("-" * 40)  # WHY: legacy fallback section underline preserved.
        print(raw_output)  # WHY: show captured raw text verbatim.

    def _render_gateway_arp_table(  # WHY: render parsed gateway ARP response as text table.
        self,
        gateway_data: dict[str, Any],
        raw_output: str,
        debug_mode: bool,
    ) -> None:
        """Render the parsed gateway ARP response as an aligned text table."""
        columns = gateway_data.get("columns", [])  # WHY: column metadata describing rows.
        if not columns:  # WHY: no descriptors means cannot tabulate. Fall back.
            print("No column information available in gateway response")  # WHY: legacy phrasing.
            self._echo_raw_fallback(raw_output)  # WHY: emit legacy raw echo block.
            return  # WHY: done with fallback path.
        rows = gateway_data.get("rows", [])  # WHY: row payloads to render.
        column_headers = [  # WHY: display names with id fallback per legacy logic.
            col.get("display_name", col.get("id", "Unknown")) for col in columns
        ]
        col_widths = self._compute_column_widths(columns, column_headers, rows)  # WHY: widths.
        print("PARSED ARP TABLE:")  # WHY: legacy section header preserved.
        print("-" * 40)  # WHY: legacy section underline preserved.
        self._print_table_header(column_headers, col_widths)  # WHY: header + underline.
        self._print_table_rows(columns, rows, col_widths)  # WHY: body rows aligned.
        print(f"\nTotal ARP Entries: {len(rows)}")  # WHY: legacy footer preserved.
        if debug_mode:  # WHY: legacy debug echo of the raw JSON.
            self._echo_debug_json(raw_output)  # WHY: emit legacy debug JSON echo.

    @staticmethod
    def _echo_debug_json(raw_output: str) -> None:
        """Emit the legacy 'RAW JSON OUTPUT (Debug)' echo block."""
        print("\nRAW JSON OUTPUT (Debug):")  # WHY: legacy debug section header preserved.
        print("-" * 40)  # WHY: legacy debug section underline preserved.
        print(raw_output)  # WHY: show captured raw text verbatim.

    @staticmethod
    def _compute_column_widths(
        columns: list[dict[str, Any]],
        column_headers: list[str],
        rows: list[dict[str, Any]],
    ) -> list[int]:
        """Compute per-column display widths (max(header,cell)+2, capped at 20)."""
        col_widths: list[int] = []  # WHY: accumulator returned to caller.
        for column_index, header_text in enumerate(column_headers):  # WHY: walk columns.
            max_width = len(header_text)  # WHY: header sets baseline width.
            column_id = columns[column_index].get("id", "")  # WHY: cell key for column.
            for row in rows:  # WHY: track widest cell in this column.
                cell_value = str(row.get(column_id, ""))  # WHY: coerce to string for length.
                if len(cell_value) > max_width:  # WHY: keep the maximum seen so far.
                    max_width = len(cell_value)  # WHY: update running max.
            col_widths.append(min(max_width + 2, _MAX_COLUMN_WIDTH))  # WHY: +2 pad, cap at 20.
        return col_widths  # WHY: caller uses widths for header + row alignment.

    @staticmethod
    def _print_table_header(column_headers: list[str], col_widths: list[int]) -> None:
        """Print the header row + underline for the gateway ARP table."""
        header_line = " | ".join(  # WHY: join padded headers with legacy separator.
            header_text.ljust(col_widths[column_index]) for column_index, header_text in enumerate(column_headers)
        )
        print(header_line)  # WHY: show the header row.
        print("-" * len(header_line))  # WHY: underline matches header width.

    @staticmethod
    def _print_table_rows(
        columns: list[dict[str, Any]],
        rows: list[dict[str, Any]],
        col_widths: list[int],
    ) -> None:
        """Print the data rows of the gateway ARP table, truncating long cells."""
        for row in rows:  # WHY: render one line per ARP entry.
            row_values: list[str] = []  # WHY: accumulator for the line's padded cells.
            for column_index, column in enumerate(columns):  # WHY: walk columns for order.
                column_id = column.get("id", "")  # WHY: cell key for this column.
                cell_value = str(row.get(column_id, ""))  # WHY: coerce to string for display.
                width = col_widths[column_index]  # WHY: width budget for this column.
                if len(cell_value) > width - 2:  # WHY: truncate overlong cells with ellipsis.
                    cell_value = cell_value[: width - 5] + "..."  # WHY: reserve 3 chars for dots.
                row_values.append(cell_value.ljust(width))  # WHY: pad to fixed width.
            print(" | ".join(row_values))  # WHY: emit the row using legacy separator.

    def _render_timeout(self, device_info: dict[str, Any] | None) -> None:
        """Render the ARP-timeout message with optional type-specific troubleshooting."""
        print("! Timeout waiting for ARP results")  # WHY: legacy phrasing preserved.
        if device_info:  # WHY: type-specific help when we know what we hit.
            self._render_timeout_help(device_info)  # WHY: emit legacy troubleshooting block.
        logging.warning("WebSocket ARP operation timed out")  # WHY: after log on timeout.

    @staticmethod
    def _render_timeout_help(device_info: dict[str, Any]) -> None:
        """Print the per-device-type troubleshooting block on ARP timeout."""
        device_type = device_info.get("type", "unknown")  # WHY: branch by type for guidance.
        device_model = device_info.get("model", "unknown")  # WHY: surface model in messages.
        if device_type == "switch":  # WHY: switch-specific troubleshooting block.
            print(f"\nSwitch troubleshooting ({device_model}):")  # WHY: legacy header preserved.
            print("-> Switches often have limited WebSocket ARP support")  # WHY: legacy line.
            print("-> Try using SSH-based 'show arp' commands instead")  # WHY: legacy line.
            print("-> Some switch models require specific command syntax")  # WHY: legacy line.
            print("-> Consider using Menu option for SSH device commands")  # WHY: legacy line.
            return  # WHY: done with switch path.
        if device_type == "gateway":  # WHY: gateway-specific troubleshooting block.
            print(f"\nGateway troubleshooting ({device_model}):")  # WHY: legacy header preserved.
            print("-> Try increasing timeout or checking network connectivity")  # WHY: legacy.
            print("-> Gateway may require different ARP command format")  # WHY: legacy line.
            return  # WHY: done with gateway path.
        print(f"\nGeneral troubleshooting ({device_type}):")  # WHY: fallback header preserved.
        print("-> Check device connectivity and WebSocket support")  # WHY: legacy line.
        print("-> Some devices may require SSH-based commands")  # WHY: legacy line preserved.

    @staticmethod
    def _format_device_context(
        device_info: dict[str, Any] | None,
        device_id: str,
    ) -> str:
        """Format the trailing log payload used by the successful ARP completion message."""
        if not device_info:  # WHY: legacy uses raw device id string on missing metadata.
            return f"device {device_id}"  # WHY: legacy fallback string preserved.
        device_type = device_info.get("type", "unknown")  # WHY: echo type when known.
        device_name = device_info.get("name", device_id[:8])  # WHY: echo name when known.
        return f"{device_type} {device_name}"  # WHY: matches legacy log payload format.
