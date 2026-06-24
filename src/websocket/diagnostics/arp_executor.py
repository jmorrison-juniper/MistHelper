"""ArpDeviceExecutor: orchestrate ARP-over-WebSocket diagnostic workflow."""

from __future__ import annotations  # Defer annotation evaluation for forward refs

import json  # Parse gateway JSON ARP responses
import logging  # Standard logging for action observability
from typing import Any  # Generic typing for arbitrary JSON-shaped payloads

from src.websocket.context import WebSocketCmdDeps  # Injected dependency bundle
from src.websocket.diagnostics.common import (  # Shared executor helpers
    detect_debug_mode,
    extract_command_session,
    post_device_command,
    prepare_command_credentials,
)
from src.websocket.manager import (  # WebSocket lifecycle + error utilities
    WebSocketManager,
    cleanup_ws_connection,
    log_ws_error,
    select_ws_site,
)

_TIMEOUT_SWITCH = 45  # Extended ARP timeout for switches (legacy value)
_TIMEOUT_GATEWAY = 35  # Extended ARP timeout for gateways (legacy value)
_TIMEOUT_DEFAULT = 30  # Default ARP timeout for APs / unknown devices
_MAX_COLUMN_WIDTH = 20  # Column-width cap when rendering gateway ARP tables


class ArpDeviceExecutor:
    """Run an interactive ARP command on a Mist device via the WebSocket stream."""

    def execute(self, deps: WebSocketCmdDeps) -> None:
        """Top-level entry: prompt user, run ARP, render results."""
        logging.info("Starting WebSocket ARP operation...")  # Action log before workflow begins
        logging.debug("ENTER: arp_device_websocket")  # Trace marker preserved
        debug_mode = detect_debug_mode()  # Honor --debug / -d flag once per run
        if debug_mode:  # Mirror legacy debug banner
            print("[DEBUG] Starting ARP via WebSocket operation...")
        websocket_manager: WebSocketManager | None = None  # Tracked so finally can clean up
        try:  # Wrap entire workflow to mirror legacy try/except/finally
            websocket_manager = self._run_workflow(deps, debug_mode)  # Drive prompts + WS work
        except Exception as arp_error:  # noqa: BLE001  # Mirror legacy broad catch for resilience
            log_ws_error(f"WebSocket ARP operation failed: {arp_error}", False)  # Legacy log
            logging.debug("EXIT: arp_device_websocket - error")  # Trace marker preserved
        finally:  # Always release WS resources on exit path
            cleanup_ws_connection(websocket_manager)  # Disconnect if connected (legacy 1-arg call)
            logging.debug("EXIT: arp_device_websocket")  # Trace marker preserved

    def _run_workflow(self, deps: WebSocketCmdDeps, debug_mode: bool) -> WebSocketManager | None:
        """Prompt for site+device, check compatibility, run ARP; returns WS for cleanup."""
        site_id = select_ws_site(deps, debug_mode)  # Interactive site picker
        if site_id is None:  # User cancelled site selection
            return None  # Skip rest of workflow
        device_id = deps.select_device_fn(site_id, device_type="all")  # Interactive device picker
        if not device_id:  # User cancelled or no devices available
            print("! No device selected. Operation cancelled.")  # Legacy phrasing preserved
            return None  # Skip rest of workflow
        if debug_mode:  # Mirror legacy debug echo of chosen device
            print(f"[DEBUG] Selected device_id = {device_id}")
        device_info = self._fetch_device_info(deps, site_id, device_id, debug_mode)  # Type/model
        if not self._maybe_warn_and_confirm(deps, device_info, debug_mode):  # Compat / cancel
            return None  # User declined to proceed
        return self._issue_arp_and_render(  # Connect, POST, await, render
            deps, site_id, device_id, device_info, debug_mode
        )

    def _fetch_device_info(
        self,
        deps: WebSocketCmdDeps,
        site_id: str,
        device_id: str,
        debug_mode: bool,
    ) -> dict[str, Any] | None:
        """Look up device record for type/model context; return None if unavailable."""
        logging.debug("Fetching device record for ARP target device=%s", device_id)  # Before log
        try:  # Legacy code swallows errors to keep the ARP attempt going
            rawdata = deps.list_devices_fn(deps.apisession, site_id, type="all").data  # API call
            device_info = next(  # Walk list for the chosen device id
                (entry for entry in rawdata if entry.get("id") == device_id), None
            )
        except Exception as device_check_error:  # noqa: BLE001  # Match legacy broad catch
            logging.warning(  # Action log after failed lookup
                "Could not verify device compatibility: %s", device_check_error
            )
            if debug_mode:  # Mirror legacy debug echo of the failure
                print(f"[DEBUG] Device check failed: {device_check_error}")
            print("   -> Proceeding with standard ARP command")  # Legacy phrasing preserved
            return None  # Caller proceeds with no device-context
        if device_info and debug_mode:  # Mirror legacy debug print of resolved attributes
            device_type = device_info.get("type", "unknown")  # Pull type for echo
            device_model = device_info.get("model", "unknown")  # Pull model for echo
            device_name = device_info.get("name", f"Device {device_id[:8]}")  # Pull name for echo
            print(  # Single legacy debug line preserved verbatim
                f"[DEBUG] Device type: {device_type}, model: {device_model}, name: {device_name}"
            )
        logging.debug(  # Action log after successful lookup
            "Device record resolved present=%s", device_info is not None
        )
        return device_info  # May be None if not found in the list

    def _maybe_warn_and_confirm(
        self,
        deps: WebSocketCmdDeps,
        device_info: dict[str, Any] | None,
        debug_mode: bool,  # noqa: ARG002  # Kept for symmetry with sibling helpers
    ) -> bool:
        """Print device-type compatibility notes; ask switches to confirm. Returns proceed."""
        if not device_info:  # No metadata available; nothing to warn about
            return True  # Proceed unconditionally to preserve legacy behavior
        device_type = device_info.get("type", "unknown")  # Branch by device type
        device_model = device_info.get("model", "unknown")  # Surface model in messages
        if device_type == "switch":  # Switches need explicit user confirmation per legacy
            return self._confirm_switch_arp(deps, device_model)
        if device_type == "gateway":  # Informational only for gateways
            print(f"!? Gateway detected (Model: {device_model})")  # Legacy phrasing preserved
            print("   -> Gateways have good WebSocket ARP support")  # Legacy phrasing preserved
            print("   -> Results may differ from Access Points")  # Legacy phrasing preserved
            return True  # Proceed
        if device_type == "ap":  # Informational only for APs
            print(f"!? Access Point detected (Model: {device_model})")  # Legacy phrasing preserved
            print("   -> Access Points have full WebSocket ARP support")  # Legacy phrasing
            return True  # Proceed
        print(f"? Unknown device type: {device_type} (Model: {device_model})")  # Legacy phrasing
        print("   -> Proceeding with standard ARP command")  # Legacy phrasing preserved
        return True  # Proceed with standard command

    @staticmethod
    def _confirm_switch_arp(deps: WebSocketCmdDeps, device_model: str) -> bool:
        """Warn about switch ARP limitations and require explicit y/yes to proceed."""
        print(f"!?  WARNING: Switch detected (Model: {device_model})")  # Legacy phrasing
        print("   -> Switches may have limited WebSocket ARP support")  # Legacy phrasing
        print("   -> Consider using SSH-based ARP commands instead")  # Legacy phrasing
        print("   -> This operation may timeout or return limited results")  # Legacy phrasing
        logging.info("Prompting operator to confirm switch ARP attempt model=%s", device_model)
        response = (  # EOF-safe input wrapper drops trailing newline, lower-cased for match
            deps.safe_input_fn(
                "   -> Continue anyway? (y/N): ",
                context="websocket_arp",
            )
            .strip()
            .lower()
        )
        if response in ("y", "yes"):  # Affirmative answers per legacy behavior
            logging.debug("Switch ARP attempt confirmed by operator")  # After log on confirm
            return True  # Caller proceeds
        print("! Operation cancelled by user")  # Legacy phrasing preserved
        logging.info("Switch ARP attempt cancelled by operator")  # After log on cancel
        return False  # Caller aborts

    def _issue_arp_and_render(
        self,
        deps: WebSocketCmdDeps,
        site_id: str,
        device_id: str,
        device_info: dict[str, Any] | None,
        debug_mode: bool,
    ) -> WebSocketManager | None:
        """Connect WS, POST ARP, await results, render output. Returns WS for cleanup."""
        print(f"\n-> Executing ARP command on device {device_id}...")  # Legacy banner preserved
        print("-> Establishing WebSocket connection...")  # Legacy banner preserved
        websocket_manager = WebSocketManager(deps.apisession)  # Build per-run WS manager
        logging.info("Connecting WebSocket for ARP site=%s device=%s", site_id, device_id)
        if not websocket_manager.connect_and_subscribe(site_id, device_id, debug_mode):  # Sub
            logging.warning("WebSocket connect+subscribe failed for ARP")  # After log on failure
            return websocket_manager  # Hand to finally for cleanup
        logging.debug("WebSocket connect+subscribe succeeded for ARP")  # After log on success
        print("-> Issuing ARP command...")  # Legacy banner preserved
        session_id = self._post_arp_command(  # POST the ARP HTTP command and pull session id
            deps, websocket_manager, site_id, device_id, debug_mode
        )
        if session_id is None:  # POST failed; helpers already disconnected
            return websocket_manager  # Return for finally (already disconnected, but safe)
        self._await_and_render(  # Wait for the WS result then render to console
            websocket_manager, session_id, device_info, device_id, debug_mode
        )
        return websocket_manager  # Hand to finally for cleanup

    def _post_arp_command(
        self,
        deps: WebSocketCmdDeps,
        websocket_manager: WebSocketManager,
        site_id: str,
        device_id: str,
        debug_mode: bool,
    ) -> str | None:
        """POST the ARP command and return the session id (or None on failure)."""
        credentials = prepare_command_credentials(  # Pull + validate Mist host/token
            deps.apisession, websocket_manager, debug_mode
        )
        if credentials is None:  # Credential lookup failed and disconnected
            return None  # Caller aborts the workflow
        mist_host, mist_apitoken = credentials  # Unpack into local variables
        arp_url = (  # Build the device-scoped ARP endpoint URL
            f"https://{mist_host}/api/v1/sites/{site_id}/devices/{device_id}/arp"
        )
        headers = {  # REST headers required by the Mist API
            "Authorization": f"Token {mist_apitoken}",
            "Content-Type": "application/json",
        }
        arp_response = post_device_command(  # POST and capture full response (empty body)
            arp_url, headers, {}, debug_mode, "ARP"
        )
        if arp_response is None:  # Defensive: helper currently never returns None
            return None  # Treat as POST failure
        return extract_command_session(arp_response, websocket_manager, "ARP")  # Demux session

    def _await_and_render(
        self,
        websocket_manager: WebSocketManager,
        session_id: str,
        device_info: dict[str, Any] | None,
        device_id: str,
        debug_mode: bool,
    ) -> None:
        """Wait for the ARP result on the WS, then render it or report timeout."""
        print(f"-> ARP command issued (session: {session_id[:8]}...)")  # Legacy banner preserved
        print("-> Waiting for ARP results...")  # Legacy banner preserved
        if debug_mode:  # Mirror legacy debug prints of session + waiting state
            print(f"[DEBUG] Full session ID = {session_id}")
            print("[DEBUG] Starting to wait for WebSocket results...")
        timeout_seconds = self._compute_timeout(device_info)  # Type-aware timeout selection
        logging.info(  # Action log before blocking wait
            "Awaiting ARP result session=%s timeout=%ds", session_id[:8], timeout_seconds
        )
        arp_result = websocket_manager.wait_for_command_result(  # Block until result or timeout
            session_id, timeout_seconds=timeout_seconds
        )
        logging.debug("ARP wait completed; has_result=%s", arp_result is not None)  # After log
        if debug_mode:  # Mirror legacy debug echo of wait outcome
            print(f"[DEBUG] wait_for_command_result returned: {arp_result is not None}")
            if arp_result:  # Show available top-level keys to aid diagnosis
                print(f"[DEBUG] Result keys: {list(arp_result.keys())}")
        if arp_result:  # Success path: render the captured payload
            self._render_arp_result(arp_result, device_info, device_id, debug_mode)
            return  # Done rendering
        self._render_timeout(device_info)  # Failure path with type-aware help text

    @staticmethod
    def _compute_timeout(device_info: dict[str, Any] | None) -> int:
        """Pick the WS wait timeout based on device type, printing legacy notice line."""
        if not device_info:  # No metadata; use baseline timeout
            return _TIMEOUT_DEFAULT
        device_type = device_info.get("type", "unknown")  # Switch on type for timeout
        if device_type == "switch":  # Switches need more time per legacy code
            print("   -> Using extended timeout for switch (45 seconds)")  # Legacy phrasing
            return _TIMEOUT_SWITCH
        if device_type == "gateway":  # Gateways slightly slower than APs
            print("   -> Using extended timeout for gateway (35 seconds)")  # Legacy phrasing
            return _TIMEOUT_GATEWAY
        return _TIMEOUT_DEFAULT  # APs / unknown use baseline

    def _render_arp_result(
        self,
        arp_result: dict[str, Any],
        device_info: dict[str, Any] | None,
        device_id: str,
        debug_mode: bool,
    ) -> None:
        """Render an ARP success payload, dispatching gateway JSON to the table renderer."""
        print("\n" + "=" * 60)  # Visual separator preserved verbatim
        print("ARP TABLE RESULTS:")  # Header preserved verbatim
        print("=" * 60)  # Visual separator preserved verbatim
        self._render_device_context(device_info)  # Optional device-context block
        raw_output = arp_result.get("raw", "")  # Primary output field from documented schema
        parsed_output = arp_result.get("Output", "")  # Secondary output field (sometimes empty)
        if raw_output:  # Decide gateway-table vs raw-passthrough rendering
            self._render_raw_output_block(raw_output, device_info, debug_mode)
        if parsed_output and parsed_output != raw_output:  # Avoid duplicate echo when identical
            print("\nPARSED OUTPUT:")  # Section header preserved
            print("-" * 40)  # Section underline preserved
            print(parsed_output)  # Show captured parsed text
        if not raw_output and not parsed_output:  # Surface empty-result diagnostic message
            print("No output data received")  # Legacy phrasing preserved
            if device_info and device_info.get("type") == "switch":  # Switch-only troubleshooting
                print("\nTroubleshooting for switches:")  # Legacy phrasing preserved
                print("-> Try using SSH-based commands instead")  # Legacy phrasing preserved
                print("-> Some switches require specific ARP command syntax")  # Legacy phrasing
                print("-> WebSocket API may have limited switch support")  # Legacy phrasing
        print("=" * 60)  # Visual closer preserved verbatim
        device_context = self._format_device_context(device_info, device_id)  # Log payload
        logging.info("WebSocket ARP completed successfully for %s", device_context)  # Final log

    @staticmethod
    def _render_device_context(device_info: dict[str, Any] | None) -> None:
        """Print the device-type context header when device metadata is available."""
        if not device_info:  # Nothing to render without metadata
            return  # Skip header section entirely
        device_type = device_info.get("type", "unknown")  # Switch on type for note text
        device_model = device_info.get("model", "unknown")  # Surface model in header
        device_name = device_info.get("name", "Unknown Device")  # Surface name in header
        print(f"Device: {device_name} ({device_type.upper()}: {device_model})")  # Legacy header
        if device_type == "switch":  # Switch-specific note
            print("Note: Switch ARP data may show forwarding table or limited ARP information")
        elif device_type == "gateway":  # Gateway-specific note
            print("Note: Gateway ARP data may include routing information")
        elif device_type == "ap":  # AP-specific note
            print("Note: Access Point ARP data shows client connectivity information")
        print("-" * 60)  # Underline preserved verbatim

    def _render_raw_output_block(
        self,
        raw_output: str,
        device_info: dict[str, Any] | None,
        debug_mode: bool,
    ) -> None:
        """Render raw output; if gateway JSON, dispatch to table renderer."""
        is_gateway = device_info is not None and device_info.get("type") == "gateway"  # Type gate
        looks_like_json = raw_output.strip().startswith("{")  # Cheap JSON sniff
        if is_gateway and looks_like_json:  # Try to parse + tabulate gateway response
            self._render_gateway_table_or_fallback(raw_output, debug_mode)
            return  # Gateway path handled fully by helper
        print("RAW OUTPUT:")  # Section header preserved
        print("-" * 40)  # Section underline preserved
        print(raw_output)  # Show captured raw text verbatim

    def _render_gateway_table_or_fallback(self, raw_output: str, debug_mode: bool) -> None:
        """Parse gateway JSON ARP response; tabulate on success, fall back on failure."""
        logging.debug("Attempting to parse gateway ARP JSON payload")  # Action log before parse
        try:  # Parse and dispatch to rendering helpers
            gateway_data = json.loads(raw_output)  # Decode the JSON document
        except json.JSONDecodeError as json_error:  # Match legacy fallback phrasing on failure
            if debug_mode:  # Mirror legacy debug echo of the parse error
                print(f"[DEBUG] Failed to parse gateway JSON: {json_error}")
            logging.warning("Gateway ARP JSON parse failed: %s", json_error)  # After log
            print("Failed to parse gateway JSON output")  # Legacy phrasing preserved
            print("RAW OUTPUT:")  # Fallback section header preserved
            print("-" * 40)  # Fallback section underline preserved
            print(raw_output)  # Show captured raw text verbatim
            return  # Done with fallback path
        if gateway_data.get("status") != "SUCCESS" or "rows" not in gateway_data:  # Schema check
            print("Gateway response format not recognized")  # Legacy phrasing preserved
            print("RAW OUTPUT:")  # Fallback section header preserved
            print("-" * 40)  # Fallback section underline preserved
            print(raw_output)  # Show captured raw text verbatim
            return  # Done with fallback path
        self._render_gateway_arp_table(gateway_data, raw_output, debug_mode)  # Tabulate rows

    def _render_gateway_arp_table(
        self,
        gateway_data: dict[str, Any],
        raw_output: str,
        debug_mode: bool,
    ) -> None:
        """Render the parsed gateway ARP response as an aligned text table."""
        columns = gateway_data.get("columns", [])  # Column metadata describing the rows
        if not columns:  # No column descriptors means we cannot tabulate
            print("No column information available in gateway response")  # Legacy phrasing
            print("RAW OUTPUT:")  # Fallback section header preserved
            print("-" * 40)  # Fallback section underline preserved
            print(raw_output)  # Show captured raw text verbatim
            return  # Done with fallback path
        print("PARSED ARP TABLE:")  # Section header preserved
        print("-" * 40)  # Section underline preserved
        rows = gateway_data.get("rows", [])  # Row payloads to render
        column_headers = [  # Display names with id fallback per legacy logic
            col.get("display_name", col.get("id", "Unknown")) for col in columns
        ]
        col_widths = self._compute_column_widths(columns, column_headers, rows)  # Widths per col
        self._print_table_header(column_headers, col_widths)  # Header + underline
        self._print_table_rows(columns, rows, col_widths)  # Body rows
        print(f"\nTotal ARP Entries: {len(rows)}")  # Footer preserved verbatim
        if debug_mode:  # Mirror legacy debug echo of the raw JSON
            print("\nRAW JSON OUTPUT (Debug):")
            print("-" * 40)
            print(raw_output)

    @staticmethod
    def _compute_column_widths(
        columns: list[dict[str, Any]],
        column_headers: list[str],
        rows: list[dict[str, Any]],
    ) -> list[int]:
        """Compute per-column display widths (max(header,cell)+2, capped at 20)."""
        col_widths: list[int] = []  # Accumulator returned to caller
        for column_index, header_text in enumerate(column_headers):  # Walk columns by index
            max_width = len(header_text)  # Header sets baseline
            column_id = columns[column_index].get("id", "")  # Look up cell key for this column
            for row in rows:  # Scan rows for the widest cell in this column
                cell_value = str(row.get(column_id, ""))  # Coerce to string for length
                if len(cell_value) > max_width:  # Track the maximum cell width seen
                    max_width = len(cell_value)
            col_widths.append(min(max_width + 2, _MAX_COLUMN_WIDTH))  # +2 padding, cap at 20
        return col_widths  # Caller uses widths for header + row alignment

    @staticmethod
    def _print_table_header(column_headers: list[str], col_widths: list[int]) -> None:
        """Print the header row + underline for the gateway ARP table."""
        header_line = " | ".join(  # Join padded headers with the legacy separator
            header_text.ljust(col_widths[column_index]) for column_index, header_text in enumerate(column_headers)
        )
        print(header_line)  # Show the header row
        print("-" * len(header_line))  # Underline matching the header width

    @staticmethod
    def _print_table_rows(
        columns: list[dict[str, Any]],
        rows: list[dict[str, Any]],
        col_widths: list[int],
    ) -> None:
        """Print the data rows of the gateway ARP table, truncating long cells."""
        for row in rows:  # Render one line per ARP entry
            row_values: list[str] = []  # Accumulator for the line's padded cells
            for column_index, column in enumerate(columns):  # Walk columns to keep order
                column_id = column.get("id", "")  # Look up cell key for this column
                cell_value = str(row.get(column_id, ""))  # Coerce to string for display
                width = col_widths[column_index]  # Width budget for this column
                if len(cell_value) > width - 2:  # Truncate overlong cells with trailing ellipsis
                    cell_value = cell_value[: width - 5] + "..."  # Reserve 3 chars for the dots
                row_values.append(cell_value.ljust(width))  # Pad to fixed width
            print(" | ".join(row_values))  # Emit the row using legacy separator

    def _render_timeout(self, device_info: dict[str, Any] | None) -> None:
        """Render the ARP-timeout message with optional type-specific troubleshooting."""
        print("! Timeout waiting for ARP results")  # Legacy phrasing preserved
        if device_info:  # Type-specific help when we know what we hit
            self._render_timeout_help(device_info)
        logging.warning("WebSocket ARP operation timed out")  # After log on timeout

    @staticmethod
    def _render_timeout_help(device_info: dict[str, Any]) -> None:
        """Print the per-device-type troubleshooting block on ARP timeout."""
        device_type = device_info.get("type", "unknown")  # Branch by type for guidance
        device_model = device_info.get("model", "unknown")  # Surface model in messages
        if device_type == "switch":  # Switch-specific troubleshooting block
            print(f"\nSwitch troubleshooting ({device_model}):")  # Legacy header preserved
            print("-> Switches often have limited WebSocket ARP support")  # Legacy line
            print("-> Try using SSH-based 'show arp' commands instead")  # Legacy line
            print("-> Some switch models require specific command syntax")  # Legacy line
            print("-> Consider using Menu option for SSH device commands")  # Legacy line
            return  # Done with switch path
        if device_type == "gateway":  # Gateway-specific troubleshooting block
            print(f"\nGateway troubleshooting ({device_model}):")  # Legacy header preserved
            print("-> Try increasing timeout or checking network connectivity")  # Legacy line
            print("-> Gateway may require different ARP command format")  # Legacy line
            return  # Done with gateway path
        print(f"\nGeneral troubleshooting ({device_type}):")  # Fallback header preserved
        print("-> Check device connectivity and WebSocket support")  # Legacy line preserved
        print("-> Some devices may require SSH-based commands")  # Legacy line preserved

    @staticmethod
    def _format_device_context(
        device_info: dict[str, Any] | None,
        device_id: str,
    ) -> str:
        """Format the trailing log payload used by the successful ARP completion message."""
        if not device_info:  # No metadata; legacy used the raw device id string
            return f"device {device_id}"
        device_type = device_info.get("type", "unknown")  # Echo type when known
        device_name = device_info.get("name", device_id[:8])  # Echo name when known
        return f"{device_type} {device_name}"  # Matches legacy log payload format
