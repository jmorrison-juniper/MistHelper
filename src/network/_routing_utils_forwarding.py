"""Forwarding-table orchestrator cluster for :mod:`src.network.routing_utils`.

Owns the gateway/SSR forwarding-table (FIB) orchestration entry point
``execute_show_forwarding_table`` plus its helper chain
(``_select_forwarding_table_device``, ``_display_forwarding_device_guidance``,
``_get_forwarding_table_params``, ``_execute_forwarding_table_command``,
``_process_forwarding_table_results``, ``_display_forwarding_table_output``,
``_display_forwarding_table_timeout``) and the 7 forwarding-specific
parsers that translate raw device output into route dicts. Splitting
these helpers off the parent :class:`~src.network.routing_utils.RoutingUtils`
cuts the last STRUCT-LENGTH and STRUCT-COMPLEXITY hotspots that kept the
parent module in the D range.

The parent binds an instance as ``self._forwarding`` and its
``__getattr__`` proxies unknown attribute lookups here so shared state
(dependencies, apisession, other clusters) stays transparent. Mirrors
the Phase 1/2/3/4 parsing + display + payload + routing split.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import json  # WHY: forwarding output arrives as either raw text or a JSON body
import logging  # WHY: orchestrator emits structured log lines around device commands
from typing import TYPE_CHECKING, Any  # WHY: TYPE_CHECKING avoids runtime cycle with parent

if TYPE_CHECKING:  # WHY: only needed for static type checkers; skipped at runtime
    from src.network.routing_utils import RoutingUtils  # WHY: parent type for cross-reference only


# WHY: WebSocket wait timeout for the forwarding-table command result (seconds)
_FORWARDING_WAIT_TIMEOUT: int = 60  # WHY: matches legacy 60s wait window

# WHY: HA node identifiers accepted by the forwarding-table API
_VALID_NODES: frozenset[str] = frozenset({"node0", "node1"})  # WHY: API-defined enum

# WHY: default prefix used when the user leaves the prefix filter blank
_DEFAULT_PREFIX: str = "0.0.0.0/0"  # WHY: matches legacy default (all routes)

# WHY: minimum whitespace-split tokens required for a tabular forwarding row
_FORWARDING_MIN_TOKENS: int = 2  # WHY: at least destination + next-hop


class _RoutingUtilsForwarding:  # WHY: cluster wrapper matching the parsing/display/payload/routing split
    """Wrapper class holding the extracted forwarding-table orchestrators."""

    def __init__(self, parent: RoutingUtils) -> None:  # WHY: bind parent for delegated state
        """Store the parent :class:`RoutingUtils` for delegate lookups."""
        self._ru = parent  # WHY: enable __getattr__ delegation back to RoutingUtils

    def __getattr__(self, name: str) -> Any:  # WHY: transparent proxy so callers see combined API
        """Delegate unknown attributes to the wrapped parent object."""
        parent = self.__dict__.get("_ru")  # WHY: guard against half-initialized instances
        if parent is None:  # WHY: only trips during broken init; avoid infinite recursion
            raise AttributeError(name)  # WHY: signal missing attribute cleanly to callers
        return getattr(parent, name)  # WHY: transparent proxy to the parent RoutingUtils

    # ------------------------------------------------------------------
    # Top-level orchestrator entry point
    # ------------------------------------------------------------------

    def execute_show_forwarding_table(self) -> None:
        """Execute show forwarding table on a gateway/SSR via WebSocket."""
        debug_mode = (
            self._ru.check_fn()
        )  # WHY: capture debug flag once for entire flow (renamed from is_debug_mode_fn per 1012)
        self._ru._setup_debug_mode(debug_mode)  # WHY: hoist logger to DEBUG when needed
        logging.info("Starting WebSocket show forwarding table operation...")  # WHY: production log
        logging.debug("ENTER: execute_show_forwarding_table")  # WHY: trace marker for debug logs
        websocket_manager = None  # WHY: init early so finally-block cleanup is always safe
        try:  # WHY: outer try wraps the whole flow so exceptions still hit cleanup
            websocket_manager = self._run_forwarding_flow(debug_mode)  # WHY: happy path split
        except Exception as error:  # WHY: match legacy catch-all so no exceptions escape
            self._ru._handle_routing_error("forwarding table", error, debug_mode)  # WHY: shared
        finally:  # WHY: always disconnect regardless of success/failure
            self._ru._cleanup_websocket(websocket_manager, debug_mode)  # WHY: shared cleanup
            logging.debug("EXIT: execute_show_forwarding_table")  # WHY: trace marker for debug logs

    def _run_forwarding_flow(self, debug_mode: bool) -> Any | None:
        """Run the happy-path forwarding-table flow. Returns websocket_manager to clean up."""
        site_id, device_id, device_info = self._select_forwarding_table_device(debug_mode)  # WHY: pick
        if not site_id or not device_id:  # WHY: guard: user cancelled selection
            return None  # WHY: nothing to clean up
        payload = self._get_forwarding_table_params()  # WHY: prompt user for query params
        session = self._start_forwarding_session(site_id, device_id, payload, debug_mode)  # WHY: WS+cmd
        if session is None:  # WHY: guard: WS connect or POST failed
            return None  # WHY: nothing to clean up / caller skips processing
        websocket_manager, session_id = session  # WHY: unpack the (WS handle, session id) tuple
        self._process_forwarding_table_results(  # WHY: block until result arrives
            websocket_manager,
            session_id,
            device_id,
            device_info,
            debug_mode,
        )
        return websocket_manager  # WHY: caller finally-block will disconnect

    def _start_forwarding_session(
        self,
        site_id: str,
        device_id: str,
        payload: dict[str, Any],
        debug_mode: bool,
    ) -> tuple[Any, str] | None:
        """Open WebSocket + issue forwarding-table command; return (ws, sid) or None on failure."""
        websocket_manager = self._ru._connect_websocket(site_id, device_id, debug_mode)  # WHY: WS
        if not websocket_manager:  # WHY: guard: connection failed
            return None  # WHY: nothing to disconnect
        session_id = self._execute_forwarding_table_command(  # WHY: POST the FIB command
            site_id,
            device_id,
            payload,
            debug_mode,
        )
        if not session_id:  # WHY: guard: POST failed
            websocket_manager.disconnect()  # WHY: eager cleanup of half-open WS
            return None  # WHY: signal caller to skip result processing
        return websocket_manager, session_id  # WHY: caller consumes both handles

    # ------------------------------------------------------------------
    # Device-selection helper
    # ------------------------------------------------------------------

    def _select_forwarding_table_device(
        self,
        debug_mode: bool,
    ) -> tuple[str | None, str | None, dict[str, Any] | None]:
        """Select site and gateway device for forwarding table."""
        site_id = self._ru.select_site_fn()  # WHY: user picks a site or bails out
        if not site_id:  # WHY: guard clause when the user cancels site selection
            print("! No site selected. Operation cancelled.")  # WHY: UX preserved
            return None, None, None  # WHY: signal cancellation to the orchestrator
        self._log_site_selected(site_id, debug_mode)  # WHY: DEBUG output split out for CC≤5
        self._print_forwarding_guidance()  # WHY: multiline banner split out for length≤25
        device_id = self._ru.select_device_fn(site_id, "gateway")  # WHY: gateway-scoped chooser
        if not device_id:  # WHY: guard: user cancelled device selection
            print(
                "! No gateway device selected. Forwarding table command is optimized for Layer 3 routing devices."
            )  # WHY: UX preserved
            return None, None, None  # WHY: signal cancellation
        if debug_mode:  # WHY: emit selected device id only when debug is on
            print(f"[DEBUG] Selected device_id = {device_id}")  # WHY: legacy debug format
        device_info = self._ru._get_device_info(site_id, device_id, "all", debug_mode)  # WHY: mist
        self._display_forwarding_device_guidance(device_info)  # WHY: device-specific banner
        return site_id, device_id, device_info  # WHY: happy path — everything selected

    @staticmethod
    def _log_site_selected(site_id: str, debug_mode: bool) -> None:
        """Emit the selected site_id when debug is on."""
        if debug_mode:  # WHY: guard clause keeps the hot path free of DEBUG strings
            print(f"[DEBUG] Selected site_id = {site_id}")  # WHY: legacy debug format preserved

    @staticmethod
    def _print_forwarding_guidance() -> None:
        """Print the 3-line device-selection guidance banner."""
        print("-> Forwarding table is available on routers and gateways (Layer 3 devices)")
        print(
            "-> This shows the Forwarding Information Base (FIB) used for packet routing decisions"
        )  # WHY: UX preserved
        print("-> SSR gateways provide the most comprehensive forwarding table information")  # WHY: UX preserved

    def _display_forwarding_device_guidance(
        self,
        device_info: dict[str, Any] | None,
    ) -> None:
        """Display device-specific guidance for forwarding table."""
        if not device_info:  # WHY: guard: no info → no guidance needed
            return  # WHY: caller carries on without a banner
        device_type = device_info.get("type", "unknown")  # WHY: type steers the branch
        device_model = device_info.get("model", "unknown")  # WHY: model appears in every branch
        # WHY: dispatch table maps type → renderer to keep CC≤5
        renderers = {  # WHY: dict literal cheaper + flatter than if/elif ladder
            "gateway": self._print_gateway_forwarding_hint,  # WHY: gateway UX
            "switch": self._print_switch_forwarding_hint,  # WHY: switch UX
            "ap": self._print_ap_forwarding_hint,  # WHY: access-point UX
        }
        renderer = renderers.get(device_type)  # WHY: unknown types get no banner
        if renderer is not None:  # WHY: guard against unknown device_type
            renderer(device_model)  # WHY: invoke selected renderer with model context

    @staticmethod
    def _print_gateway_forwarding_hint(device_model: str) -> None:
        """Print forwarding-hint banner for a gateway device."""
        upper_model = device_model.upper()  # WHY: normalize once for two membership checks
        if "SSR" in upper_model or "128T" in device_model:  # WHY: legacy also probes 128T mixed-case
            print(f"-> SSR gateway detected ({device_model}): Excellent forwarding table support")
            return  # WHY: early-return keeps CC low
        print(f"-> Gateway device detected ({device_model}): Good forwarding table support")

    @staticmethod
    def _print_switch_forwarding_hint(device_model: str) -> None:
        """Print forwarding-hint banner for a switch device."""
        print(f"!? Switch device ({device_model}): Limited forwarding table - primarily Layer 2")
        print("  -> Consider using MAC table command for Layer 2 switching information")

    @staticmethod
    def _print_ap_forwarding_hint(device_model: str) -> None:
        """Print forwarding-hint banner for an access point."""
        print(f"!? Access Point ({device_model}): No forwarding table - wireless bridging only")

    # ------------------------------------------------------------------
    # Parameter collector
    # ------------------------------------------------------------------

    def _get_forwarding_table_params(self) -> dict[str, Any]:
        """Get user input for forwarding table query parameters."""
        self._print_forwarding_params_header()  # WHY: banner split out for CC≤5
        prefix_input = self._ru.safe_input_fn(
            "\nEnter IP prefix (press Enter for default 0.0.0.0/0): "
        ).strip()  # WHY: prefix filter (defaults to 0.0.0.0/0)
        service_name_input = self._ru.safe_input_fn(
            "Enter service name (press Enter to skip): "
        ).strip()  # WHY: SSR service name filter (optional)
        vrf_input = self._ru.safe_input_fn(
            "Enter VRF name (press Enter to skip): "
        ).strip()  # WHY: VRF filter (optional)
        node_input = self._ru.safe_input_fn(
            "Enter node (node0/node1 for HA, press Enter to skip): "
        ).strip()  # WHY: HA node filter (optional)
        return self._build_forwarding_payload(prefix_input, service_name_input, vrf_input, node_input)

    @staticmethod
    def _print_forwarding_params_header() -> None:
        """Print the forwarding-table parameters guidance header."""
        print("\n=== Forwarding Table Lookup Parameters ===")  # WHY: UX preserved
        print("The Mist API requires filtering parameters for forwarding table lookups.")
        print("You can provide:")  # WHY: UX preserved
        print("  1. IP prefix (e.g., 192.168.1.0/24, 10.0.0.0/8)")  # WHY: UX preserved
        print("  2. Service name (for SSR gateways)")  # WHY: UX preserved
        print("  3. Both prefix and service name")  # WHY: UX preserved
        print("  4. Leave empty to use default (0.0.0.0/0 - all routes)")  # WHY: UX preserved

    @staticmethod
    def _build_forwarding_payload(
        prefix_input: str,
        service_name_input: str,
        vrf_input: str,
        node_input: str,
    ) -> dict[str, Any]:
        """Build the forwarding-table payload dict from collected user inputs."""
        payload = _RoutingUtilsForwarding._init_prefix_payload(prefix_input)  # WHY: prefix + echo
        _RoutingUtilsForwarding._apply_forwarding_optional(  # WHY: service/vrf split for CC≤5
            payload, service_name_input, vrf_input
        )
        _RoutingUtilsForwarding._apply_node_filter(payload, node_input)  # WHY: node validation split
        return payload  # WHY: caller POSTs this as the command body

    @staticmethod
    def _init_prefix_payload(prefix_input: str) -> dict[str, Any]:
        """Seed the payload dict with the prefix (defaulting when blank) and echo the default."""
        if not prefix_input:  # WHY: echo the applied default so the user knows what was sent
            print(f"-> Using default prefix: {_DEFAULT_PREFIX} (all routes)")  # WHY: UX preserved
            return {"prefix": _DEFAULT_PREFIX}  # WHY: legacy default (all routes)
        return {"prefix": prefix_input}  # WHY: user-supplied prefix

    @staticmethod
    def _apply_forwarding_optional(
        payload: dict[str, Any],
        service_name_input: str,
        vrf_input: str,
    ) -> None:
        """Attach optional service_name and vrf filters to ``payload`` when supplied."""
        if service_name_input:  # WHY: only send when the user supplied a value
            payload["service_name"] = service_name_input  # WHY: SSR service filter
        if vrf_input:  # WHY: only send when the user supplied a value
            payload["vrf"] = vrf_input  # WHY: VRF filter

    @staticmethod
    def _apply_node_filter(payload: dict[str, Any], node_input: str) -> None:
        """Attach the HA node filter to ``payload`` when it matches a known identifier."""
        if node_input and node_input.lower() in _VALID_NODES:  # WHY: reject invalid identifiers
            payload["node"] = node_input.lower()  # WHY: normalize to lowercase form

    # ------------------------------------------------------------------
    # Command executor
    # ------------------------------------------------------------------

    def _execute_forwarding_table_command(
        self,
        site_id: str,
        device_id: str,
        payload: dict[str, Any],
        debug_mode: bool,
    ) -> str | None:
        """Execute the forwarding table command via REST API."""
        print("-> Issuing show forwarding table command...")  # WHY: UX preserved
        logging.debug("Forwarding table payload: %s", payload)  # WHY: always log payload
        if debug_mode:  # WHY: also echo payload to stdout when debug is on
            print(f"[DEBUG] Forwarding table payload = {payload}")  # WHY: legacy debug format
        session_id, error_msg = self._ru._payload._post_device_command(  # WHY: shared POST
            site_id,
            device_id,
            "show_forwarding_table",
            payload,
            debug_mode,
        )
        if error_msg:  # WHY: guard clause surfaces failure message and bails out
            print(f"! Failed to issue show forwarding table command: {error_msg}")  # WHY: UX
            return None  # WHY: caller treats None as cancel-and-cleanup
        self._report_command_issued(session_id, debug_mode)  # WHY: multi-line UX split for CC≤5
        return session_id  # WHY: caller correlates results by this id

    @staticmethod
    def _report_command_issued(session_id: str | None, debug_mode: bool) -> None:
        """Emit success UX + optional debug line after issuing the command."""
        short = (session_id or "")[:8]  # WHY: legacy prints only the first 8 chars for brevity
        print(f"-> Show forwarding table command issued (session: {short}...)")  # WHY: UX preserved
        print("-> Waiting for forwarding table results...")  # WHY: UX preserved
        if debug_mode:  # WHY: full-id only in debug mode
            print(f"[DEBUG] Full session ID = {session_id}")  # WHY: legacy debug format

    # ------------------------------------------------------------------
    # Result processor + renderer
    # ------------------------------------------------------------------

    def _process_forwarding_table_results(
        self,
        websocket_manager: Any,
        session_id: str,
        device_id: str,
        device_info: dict[str, Any] | None,
        debug_mode: bool,
    ) -> None:
        """Wait for and process forwarding table results."""
        if debug_mode:  # WHY: emit wait banner only in debug mode
            print("[DEBUG] Starting to wait for WebSocket results...")  # WHY: legacy debug
        result = websocket_manager.wait_for_command_result(  # WHY: block until reply or timeout
            session_id,
            timeout_seconds=_FORWARDING_WAIT_TIMEOUT,
        )
        self._log_wait_outcome(result, debug_mode)  # WHY: DEBUG dump split for CC≤5
        if result:  # WHY: happy path renders the table
            self._display_forwarding_table_output(result, device_id, device_info, debug_mode)
            return  # WHY: early-return prevents falling into the timeout branch
        self._display_forwarding_table_timeout(device_info)  # WHY: timeout UX split out

    @staticmethod
    def _log_wait_outcome(result: dict[str, Any] | None, debug_mode: bool) -> None:
        """Log the wait_for_command_result outcome when debug is on."""
        if not debug_mode:  # WHY: guard clause keeps hot path free of DEBUG strings
            return  # WHY: nothing to log when debug is off
        print(f"[DEBUG] wait_for_command_result returned: {result is not None}")  # WHY: legacy
        if result:  # WHY: only dump keys when result is present
            print(f"[DEBUG] Result keys: {list(result.keys())}")  # WHY: legacy debug format

    def _display_forwarding_table_output(
        self,
        result: dict[str, Any],
        device_id: str,
        device_info: dict[str, Any] | None,
        debug_mode: bool,
    ) -> None:
        """Display formatted forwarding table results."""
        print("\n" + "=" * 80)  # WHY: separator matches legacy exactly
        print("FORWARDING TABLE RESULTS:")  # WHY: UX preserved
        print("=" * 80)  # WHY: separator matches legacy exactly
        raw_output = result.get("raw", "")  # WHY: primary field
        self._render_forwarding_section(raw_output)  # WHY: main section renderer
        output_fields = result.get("Output", "")  # WHY: some devices emit alternate field
        if output_fields and output_fields != raw_output:  # WHY: skip when identical
            self._render_additional_forwarding(output_fields)  # WHY: additional section
        self._ru._display_debug_result_fields(result, debug_mode)  # WHY: shared debug dump
        self._ru._display_no_data_message(result, "forwarding table")  # WHY: shared no-data
        print("=" * 80)  # WHY: bottom separator matches legacy exactly
        self._ru._log_command_completion("show forwarding table", device_id, device_info)

    def _render_forwarding_section(self, raw_output: str) -> None:
        """Render the primary forwarding-table section from ``raw_output``."""
        if not raw_output:  # WHY: guard clause avoids parsing an empty string
            return  # WHY: caller still emits debug/no-data messaging afterwards
        entries = self._parse_forwarding_table(raw_output)  # WHY: cluster-owned parser
        self._ru._display._display_forwarding_summary(entries)  # WHY: display cluster owns render

    def _render_additional_forwarding(self, output_fields: str) -> None:
        """Render an additional forwarding-table section from an alternate output field."""
        print("\n" + "=" * 40)  # WHY: separator matches legacy exactly
        print("ADDITIONAL OUTPUT:")  # WHY: UX preserved
        print("=" * 40)  # WHY: separator matches legacy exactly
        entries = self._parse_forwarding_table(output_fields)  # WHY: cluster-owned parser
        self._ru._display._display_forwarding_summary(entries)  # WHY: display cluster owns render

    def _display_forwarding_table_timeout(
        self,
        device_info: dict[str, Any] | None,
    ) -> None:
        """Display timeout message with troubleshooting guidance."""
        self._print_timeout_header()  # WHY: banner split out for length≤25
        if device_info:  # WHY: guard: emit device-specific hints only when info is present
            self._print_device_timeout_hint(  # WHY: split for CC≤5
                device_info.get("type", "unknown"),
                device_info.get("model", "unknown"),
            )
        logging.warning("WebSocket show forwarding table operation timed out")  # WHY: production

    @staticmethod
    def _print_timeout_header() -> None:
        """Print the 4-line timeout diagnostic block."""
        print("! Timeout waiting for forwarding table results")  # WHY: UX preserved
        print("! This may indicate:")  # WHY: UX preserved
        print("  - The device doesn't support forwarding table commands")  # WHY: UX preserved
        print("  - The device is busy or not responding")  # WHY: UX preserved
        print("  - Network connectivity issues")  # WHY: UX preserved

    def _print_device_timeout_hint(self, device_type: str, device_model: str) -> None:
        """Print the device-specific timeout troubleshooting hint."""
        # WHY: dispatch table keeps CC=1 while preserving all three legacy branches
        hints = {  # WHY: dict-of-callables cheaper than if/elif ladder
            "gateway": self._print_gateway_timeout,  # WHY: gateway troubleshooting hint
            "switch": self._print_switch_timeout,  # WHY: switch troubleshooting hint
            "ap": self._print_ap_timeout,  # WHY: access-point troubleshooting hint
        }
        renderer = hints.get(device_type)  # WHY: unknown device types produce no hint
        if renderer is not None:  # WHY: guard against unknown device_type
            renderer(device_model)  # WHY: invoke selected renderer with model context

    @staticmethod
    def _print_gateway_timeout(device_model: str) -> None:
        """Print gateway-specific timeout guidance."""
        print(f"\nGateway troubleshooting ({device_model}):")  # WHY: UX preserved
        print("-> Ensure the device is online and reachable")  # WHY: UX preserved
        print("-> Try the command again or use SSH-based routing commands")  # WHY: UX preserved

    @staticmethod
    def _print_switch_timeout(device_model: str) -> None:
        """Print switch-specific timeout guidance."""
        print(f"\nSwitch troubleshooting ({device_model}):")  # WHY: UX preserved
        print("-> Use 'Show MAC Table' command for Layer 2 forwarding information")  # WHY: UX

    @staticmethod
    def _print_ap_timeout(device_model: str) -> None:
        """Print access-point-specific timeout guidance."""
        print(f"\nAccess Point troubleshooting ({device_model}):")  # WHY: UX preserved
        print("-> APs don't maintain forwarding tables")  # WHY: UX preserved

    # ------------------------------------------------------------------
    # Forwarding-specific parsers
    # ------------------------------------------------------------------

    def _parse_forwarding_table(self, raw_output: str) -> list[dict[str, Any]]:
        """Parse raw forwarding table output into structured entries."""
        if not raw_output:  # WHY: empty input has no entries
            return []  # WHY: caller renders empty summary
        json_result = self._try_parse_forwarding_json(raw_output)  # WHY: JSON preferred
        if json_result is not None:  # WHY: guard: JSON parsed cleanly
            return json_result  # WHY: skip text-format fallback
        return self._parse_forwarding_text(raw_output)  # WHY: last-resort text parser

    def _try_parse_forwarding_json(
        self,
        raw_output: str,
    ) -> list[dict[str, Any]] | None:
        """Try parsing forwarding output as JSON. Returns None if not JSON."""
        try:  # WHY: routers frequently emit non-JSON — catch and fall through
            data = json.loads(raw_output)  # WHY: single json.loads for the whole payload
        except (json.JSONDecodeError, TypeError):  # WHY: match legacy exception set
            return None  # WHY: None signals caller to try the text-format parser
        if isinstance(data, list):  # WHY: top-level list of entry dicts
            return [self._normalize_forwarding_entry(item) for item in data]  # WHY: uniform project
        if isinstance(data, dict):  # WHY: top-level dict with entries nested under some key
            return self._extract_forwarding_from_dict(data)  # WHY: recover nested payloads
        return None  # WHY: unexpected shape — fall through to text parser

    @staticmethod
    def _normalize_forwarding_entry(item: dict[str, Any]) -> dict[str, Any]:
        """Normalize a single forwarding entry from JSON."""
        return {  # WHY: dict literal keeps projection concise
            "destination": item.get("prefix", item.get("destination", "")),  # WHY: 2 aliases
            "next_hop": item.get("nextHop", item.get("next_hop", "")),  # WHY: 2 aliases
            "interface": item.get("interface", item.get("dev", "")),  # WHY: 2 aliases
            "service": item.get("service", item.get("serviceName", "")),  # WHY: 2 aliases
            "table": item.get("table", ""),  # WHY: routing-table context (defaults to blank)
            "type": item.get("type", ""),  # WHY: route type (defaults to blank)
        }

    def _extract_forwarding_from_dict(
        self,
        data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Extract forwarding entries from a JSON dict with list values."""
        entries: list[dict[str, Any]] = []  # WHY: accumulator for projected entries
        for _key, value in data.items():  # WHY: iterate top-level fields looking for lists
            if not isinstance(value, list):  # WHY: guard: only list values hold entries
                continue  # WHY: skip scalar / dict values
            for item in value:  # WHY: each element is expected to be an entry dict
                if isinstance(item, dict):  # WHY: guard against malformed non-dict rows
                    entries.append(self._normalize_forwarding_entry(item))  # WHY: project it
        return entries  # WHY: caller renders empty list when no entries found

    def _parse_forwarding_text(self, raw_output: str) -> list[dict[str, Any]]:
        """Parse text-format forwarding table lines."""
        entries: list[dict[str, Any]] = []  # WHY: accumulator for parsed entries
        for line in raw_output.strip().split("\n"):  # WHY: iterate every input line
            stripped = line.strip()  # WHY: normalize whitespace once per line
            if self._should_skip_forwarding_line(stripped):  # WHY: skip empty/comment/divider
                continue  # WHY: continue with next line
            parts = stripped.split()  # WHY: whitespace-split into tokens
            if len(parts) >= _FORWARDING_MIN_TOKENS:  # WHY: at least destination + next-hop
                entries.append(self._normalize_forwarding_text_row(parts))  # WHY: project tokens
        return entries  # WHY: caller renders empty list when nothing parsed

    @staticmethod
    def _should_skip_forwarding_line(line: str) -> bool:
        """Return True for empty/comment/divider lines in a text-format forwarding dump."""
        # WHY: consolidates the three legacy skip conditions into a single predicate
        return not line or line.startswith("#") or line.startswith("---")

    @staticmethod
    def _normalize_forwarding_text_row(parts: list[str]) -> dict[str, Any]:
        """Normalize a tokenized forwarding-table line into the standard entry dict."""
        return {  # WHY: dict literal keeps positional projection concise
            "destination": parts[0],  # WHY: first token is always the destination
            "next_hop": parts[1] if len(parts) > 1 else "",  # WHY: 2nd token when present
            "interface": parts[2] if len(parts) > 2 else "",  # noqa: PLR2004  # WHY: 3rd token
            "service": parts[3] if len(parts) > 3 else "",  # noqa: PLR2004  # WHY: 4th token
            "table": "",  # WHY: text format has no table context
            "type": "",  # WHY: text format has no explicit type
        }
