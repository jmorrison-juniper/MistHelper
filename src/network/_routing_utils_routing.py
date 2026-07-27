"""Routing-table orchestrator cluster for :mod:`src.network.routing_utils`.

Owns the switch routing-table (RIB) orchestration entry point
``execute_show_routing_table`` plus its helper chain
(``_select_routing_table_device``, ``_display_routing_device_guidance``,
``_get_routing_table_params``, ``_execute_routing_table_command``,
``_process_routing_table_results``, ``_display_routing_table_output``),
the SSR/SRX compatibility verifier (``_verify_ssr_compatibility``), and
the route-line classifier (``_classify_and_parse_route_line``). Splitting
these helpers off the parent :class:`~src.network.routing_utils.RoutingUtils`
cuts the remaining STRUCT-LENGTH and STRUCT-COMPLEXITY hotspots that kept
the parent module in the F range.

The parent binds an instance as ``self._routing`` and its
``__getattr__`` proxies unknown attribute lookups here so shared state
(dependencies, apisession, parsing/display/payload clusters) stays
transparent. Mirrors the Phase 1/2/3 parsing + display + payload split.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import logging  # WHY: orchestrator emits structured log lines around device commands
from typing import TYPE_CHECKING, Any, cast  # WHY: cast narrows Any from parent __getattr__

from src.network._routing_utils_payload import RoutingPayloadQuery  # WHY: params builder returns one

if TYPE_CHECKING:  # WHY: only needed for static type checkers. Skipped at runtime
    from src.network.routing_utils import RoutingTableContext, RoutingUtils  # WHY: types only


# WHY: standard-format route lines carry one of these three kw tokens (space-delimited)
_STANDARD_ROUTE_TOKENS: tuple[str, ...] = ("via", "dev", "proto")

# WHY: protocol-format route lines contain one of these three uppercase-ish identifiers
_PROTOCOL_ROUTE_TOKENS: tuple[str, ...] = ("BGP", "OSPF", "static")

# WHY: minimum whitespace-split tokens required to attempt tabular parsing
_TABULAR_MIN_TOKENS: int = 2

# WHY: yes/no prompt answers considered affirmative (lowercase compare)
_AFFIRMATIVE_ANSWERS: frozenset[str] = frozenset({"y", "yes"})

# WHY: WebSocket wait timeout for the routing-table command result (seconds)
_ROUTING_WAIT_TIMEOUT: int = 60


class _RoutingUtilsRouting:  # WHY: cluster wrapper matching the parsing/display/payload split
    """Wrapper class holding the extracted routing-table orchestrators."""

    def __init__(self, parent: RoutingUtils) -> None:  # WHY: bind parent for delegated state
        """Store the parent :class:`RoutingUtils` for delegate lookups."""
        self._ru = parent  # WHY: enable __getattr__ delegation back to RoutingUtils

    def __getattr__(self, name: str) -> Any:  # WHY: transparent proxy so callers see combined API
        """Delegate unknown attributes to the wrapped parent object."""
        parent = self.__dict__.get("_ru")  # WHY: guard against half-initialized instances
        if parent is None:  # WHY: only trips during broken init. Avoid infinite recursion
            raise AttributeError(name)  # WHY: signal missing attribute cleanly to callers
        return getattr(parent, name)  # WHY: transparent proxy to the parent RoutingUtils

    # ------------------------------------------------------------------
    # Route-line classifier (was STRUCT-COMPLEXITY hotspot on parent)
    # ------------------------------------------------------------------

    def _classify_and_parse_route_line(self, line: str) -> dict[str, Any] | None:
        """Classify a route line and dispatch to the correct parser."""
        if self._has_standard_tokens(line):  # WHY: guard clause: via/dev/proto → standard parser
            return cast(  # WHY: narrow Any from parent __getattr__ proxy to declared return type
                "dict[str, Any] | None",
                self._ru._parse_standard_route_line(line),  # WHY: parser stays on parent
            )
        if self._has_protocol_tokens(line):  # WHY: guard clause: BGP/OSPF/static → protocol parser
            return cast(  # WHY: narrow Any from parent __getattr__ proxy to declared return type
                "dict[str, Any] | None",
                self._ru._parse_protocol_route_line(line),  # WHY: parser stays on parent
            )
        return self._try_parse_tabular(line)  # WHY: last-resort tabular attempt

    @staticmethod
    def _has_standard_tokens(line: str) -> bool:
        """Return True when ``line`` carries any standard-route keyword."""
        return any(tok in line for tok in _STANDARD_ROUTE_TOKENS)  # WHY: single scan over tuple

    @staticmethod
    def _has_protocol_tokens(line: str) -> bool:
        """Return True when ``line`` carries any protocol-route identifier."""
        return any(tok in line for tok in _PROTOCOL_ROUTE_TOKENS)  # WHY: single scan over tuple

    def _try_parse_tabular(self, line: str) -> dict[str, Any] | None:
        """Attempt to parse ``line`` as a tabular route row (or return ``None``)."""
        parts = line.split()  # WHY: whitespace-split for token count check
        if len(parts) < _TABULAR_MIN_TOKENS:  # WHY: guard clause on short lines
            return None  # WHY: single-token lines are section headers, not routes
        return self._ru._parsing._parse_tabular_route_line(line)  # WHY: delegate row build

    # ------------------------------------------------------------------
    # SSR/SRX compatibility verifier (was STRUCT-COMPLEXITY on parent)
    # ------------------------------------------------------------------

    def _verify_ssr_compatibility(self, device_info: dict[str, Any] | None) -> bool:
        """Verify device is SSR/SRX compatible. False to cancel."""
        if not device_info:  # WHY: no info → assume compatible. Caller keeps going
            return True  # WHY: matches legacy behavior — proceed on missing metadata
        device_type = device_info.get("type", "unknown")  # WHY: type steers the branch
        device_model = device_info.get("model", "unknown")  # WHY: model shown in guidance text
        if device_type == "gateway":  # WHY: gateway path has its own compatibility grid
            return self._verify_gateway_ssr(device_model)  # WHY: split for CC≤5
        return self._prompt_non_gateway_continue(device_type, device_model)  # WHY: split for CC≤5

    def _verify_gateway_ssr(self, device_model: str) -> bool:
        """Handle SSR compatibility check for a gateway device."""
        upper_model = device_model.upper()  # WHY: normalize once for the two membership checks
        if "SSR" in upper_model or "128T" in device_model:  # WHY: legacy also probed 128T (mixed case)
            print(f"!? SSR gateway detected ({device_model}): Fully compatible")  # WHY: UX preserved
            return True  # WHY: fully compatible path returns immediately
        if "SRX" in upper_model:  # WHY: SRX is separately labeled but also fully compatible
            print(f"!? SRX router detected ({device_model}): Fully compatible")  # WHY: UX preserved
            return True  # WHY: fully compatible path
        print(f"!? Gateway device ({device_model}): May have limited compatibility")  # WHY: UX
        return self._prompt_yes_no("Continue anyway? (y/N): ")  # WHY: user-driven decision

    def _prompt_non_gateway_continue(self, device_type: str, device_model: str) -> bool:
        """Prompt when a non-gateway device is selected for the SSR flow."""
        print(f"!? Non-gateway device detected ({device_type}/{device_model})")  # WHY: UX preserved
        return self._prompt_yes_no("Continue anyway? (y/N): ")  # WHY: user-driven decision

    def _prompt_yes_no(self, prompt_text: str) -> bool:
        """Prompt for a yes/no answer and return True on affirmative response."""
        answer = self._ru.safe_input_fn(prompt_text).strip().lower()  # WHY: normalized once
        return answer in _AFFIRMATIVE_ANSWERS  # WHY: y/yes are the only affirmatives

    # ------------------------------------------------------------------
    # Device selection helper (routing-table variant)
    # ------------------------------------------------------------------

    def _select_routing_table_device(
        self,
        debug_mode: bool,
    ) -> tuple[str | None, str | None, dict[str, Any] | None]:
        """Select site and switch device for routing table."""
        site_id = self._ru.select_site_fn()  # WHY: user picks a site or bails out
        if not site_id:  # WHY: guard clause when the user cancels site selection
            print("! No site selected. Operation cancelled.")  # WHY: UX preserved
            return None, None, None  # WHY: signal cancellation to the orchestrator
        self._log_site_selected(site_id, debug_mode)  # WHY: DEBUG output split out for CC≤5
        self._print_routing_selection_guidance()  # WHY: multiline banner split out for CC≤5
        device_id = self._ru.select_device_fn(site_id, "switch")  # WHY: switch-scoped device chooser
        if not device_id:  # WHY: user bailed at device chooser
            print("! No device selected. Operation cancelled.")  # WHY: UX preserved
            return None, None, None  # WHY: signal cancellation
        if debug_mode:  # WHY: emit selected device id only when debug is on
            print(f"[DEBUG] Selected device_id = {device_id}")  # WHY: legacy debug format
        device_info = self._ru._get_device_info(site_id, device_id, "switch", debug_mode)  # WHY: mist
        if not self._display_routing_device_guidance(device_info):  # WHY: user may cancel here too
            return None, None, None  # WHY: propagate cancellation from guidance step
        return site_id, device_id, device_info  # WHY: happy path — everything selected

    @staticmethod
    def _log_site_selected(site_id: str, debug_mode: bool) -> None:
        """Emit the selected site_id when debug is on."""
        if debug_mode:  # WHY: guard clause keeps the hot path free of DEBUG strings
            print(f"[DEBUG] Selected site_id = {site_id}")  # WHY: legacy debug format preserved

    @staticmethod
    def _print_routing_selection_guidance() -> None:
        """Print the 4-line device-selection guidance banner."""
        print("-> Switch routing table information (Layer 3 routing protocols)")  # WHY: UX preserved
        print("-> This shows the Routing Information Base (RIB) maintained by routing protocols")
        print("-> Includes routes from BGP, OSPF, static routes, direct routes, etc.")  # WHY: UX
        print("-> For SSR/SRX devices, use Menu Option 8 (dedicated SSR/SRX routing API)")  # WHY: UX

    def _display_routing_device_guidance(self, device_info: dict[str, Any] | None) -> bool:
        """Display device-specific guidance. Returns False to cancel."""
        if not device_info:  # WHY: no info → keep going without emitting guidance text
            return True  # WHY: matches legacy behavior — proceed on missing metadata
        device_type = device_info.get("type", "unknown")  # WHY: type steers the guidance branch
        device_model = device_info.get("model", "unknown")  # WHY: model appears in every branch
        if device_type == "switch":  # WHY: switch branch is the happy path (no cancel prompt)
            self._print_switch_guidance(device_model)  # WHY: split out for CC≤5
            return True  # WHY: all switch models proceed without prompting
        # WHY: non-switch device selected for a switch-scoped routing call — prompt for override
        print(f"!? Non-switch device detected ({device_type}/{device_model})")  # WHY: UX preserved
        print("  -> For SSR/SRX devices, use Menu Option 8")  # WHY: UX preserved
        print("  -> For gateway forwarding tables, use Menu Option 6")  # WHY: UX preserved
        return self._prompt_yes_no("Continue with switch routing command anyway? (y/N): ")

    @staticmethod
    def _print_switch_guidance(device_model: str) -> None:
        """Print the model-specific switch guidance line."""
        upper_model = device_model.upper()  # WHY: normalize once for both keyword membership checks
        if "EX" in upper_model:  # WHY: Juniper EX family
            print(f"!? Juniper EX switch detected ({device_model}): Excellent Layer 3 routing support")
            return  # WHY: early-return keeps CC low
        if "QFX" in upper_model:  # WHY: Juniper QFX family
            print(f"!? Juniper QFX switch detected ({device_model}): Good Layer 3 routing support")
            return  # WHY: early-return keeps CC low
        print(f"-> Switch device detected ({device_model}): Layer 3 routing table support")  # WHY: UX

    # ------------------------------------------------------------------
    # Routing-table parameter collector
    # ------------------------------------------------------------------

    def _get_routing_table_params(self) -> dict[str, Any]:
        """Get user input for routing table query parameters."""
        self._print_routing_params_header()  # WHY: banner split out for CC≤5
        query = self._collect_routing_query_inputs()  # WHY: input collection split for CC≤5
        return self._ru._payload._build_routing_payload(query)  # WHY: payload cluster owns the build

    @staticmethod
    def _print_routing_params_header() -> None:
        """Print the routing-table parameters guidance header."""
        print("\n=== Routing Table Query Parameters ===")  # WHY: UX preserved
        print("Configure the routing table query (all parameters are optional):")  # WHY: UX preserved
        print("  X  Prefix: Specific route prefix to look up (e.g., 192.168.1.0/24)")  # WHY: UX
        print("  X  Protocol: Filter by routing protocol (bgp, ospf, static, direct, evpn, any)")
        print("  X  VRF: Virtual Routing and Forwarding instance name")  # WHY: UX preserved
        print("  X  Neighbor: BGP neighbor IP (shows received/advertised routes)")  # WHY: UX preserved
        print("  X  Node: For HA devices (node0/node1)")  # WHY: UX preserved

    def _collect_routing_query_inputs(self) -> RoutingPayloadQuery:
        """Prompt the user for the 6 routing-query fields and bundle them."""
        prefix_input = self._ru.safe_input_fn(
            "\nEnter route prefix (press Enter to show all routes): "
        ).strip()  # WHY: prefix filter (optional)
        print("\nProtocol options: any (default), bgp, ospf, static, direct, evpn")  # WHY: UX
        protocol_input = self._ru.safe_input_fn(
            "Enter protocol filter (press Enter for 'any'): "
        ).strip()  # WHY: protocol filter (defaults to any)
        vrf_input = self._ru.safe_input_fn("Enter VRF name (press Enter to skip): ").strip()
        neighbor_input = self._ru.safe_input_fn("Enter BGP neighbor IP (press Enter to skip): ").strip()
        route_direction = self._prompt_route_direction(neighbor_input)  # WHY: conditional prompt
        node_input = self._ru.safe_input_fn(
            "Enter node (node0/node1 for HA, press Enter to skip): "
        ).strip()  # WHY: HA node identifier (optional)
        return RoutingPayloadQuery(
            prefix_input=prefix_input,
            protocol_input=protocol_input,
            vrf_input=vrf_input,
            neighbor_input=neighbor_input,
            route_direction=route_direction,
            node_input=node_input,
        )

    def _prompt_route_direction(self, neighbor_input: str) -> str:
        """Prompt for received/advertised direction only when a neighbor is set."""
        if not neighbor_input:  # WHY: direction is meaningful only when neighbor is present
            return ""  # WHY: empty means "no direction filter"
        print("\nRoute direction options: received, advertised, (empty for both)")  # WHY: UX
        return self._ru.safe_input_fn(
            "Enter route direction (press Enter for both): "
        ).strip()  # WHY: user-supplied direction (may be empty)

    # ------------------------------------------------------------------
    # Routing-table command executor
    # ------------------------------------------------------------------

    def _execute_routing_table_command(
        self,
        site_id: str,
        device_id: str,
        payload: dict[str, Any],
        debug_mode: bool,
    ) -> str | None:
        """Execute the routing table command via REST API."""
        print("-> Issuing show route command...")  # WHY: UX preserved
        logging.debug("Route payload: %s", payload)  # WHY: capture payload in logs regardless of debug
        if debug_mode:  # WHY: also echo payload to stdout when debug is on
            print(f"[DEBUG] Route payload = {payload}")  # WHY: legacy debug format
        session_id, error_msg = self._ru._payload._post_device_command(  # WHY: cluster owns POST
            site_id,
            device_id,
            "show_route",
            payload,
            debug_mode,
        )
        if error_msg:  # WHY: guard clause surfaces failure message and bails out
            print(f"! Failed to issue show route command: {error_msg}")  # WHY: UX preserved
            return None  # WHY: caller treats None as cancel-and-cleanup
        self._report_route_command_issued(session_id, debug_mode)  # WHY: multi-line UX split out
        return session_id  # WHY: caller correlates results by this id

    @staticmethod
    def _report_route_command_issued(session_id: str | None, debug_mode: bool) -> None:
        """Emit the success UX + optional debug line after issuing a show-route command."""
        short = (session_id or "")[:8]  # WHY: legacy prints only the first 8 chars for brevity
        print(f"-> Show route command issued (session: {short}...)")  # WHY: UX preserved
        print("-> Waiting for routing table results...")  # WHY: UX preserved
        if debug_mode:  # WHY: full-id only in debug mode
            print(f"[DEBUG] Full session ID = {session_id}")  # WHY: legacy debug format

    # ------------------------------------------------------------------
    # Routing-table result processor + renderer
    # ------------------------------------------------------------------

    def _process_routing_table_results(self, ctx: RoutingTableContext) -> None:
        """Wait for and process routing table results."""
        if ctx.debug_mode:  # WHY: emit wait banner only in debug mode
            print("[DEBUG] Starting to wait for WebSocket results...")  # WHY: legacy debug format
        result = ctx.websocket_manager.wait_for_command_result(
            ctx.session_id,
            timeout_seconds=_ROUTING_WAIT_TIMEOUT,
        )
        if ctx.debug_mode:  # WHY: log wait outcome + keys when debug is on
            print(f"[DEBUG] wait_for_command_result returned: {result is not None}")  # WHY: legacy
            if result:  # WHY: only dump keys if the result is present
                print(f"[DEBUG] Result keys: {list(result.keys())}")  # WHY: legacy debug format
        if result:  # WHY: happy path renders the table
            self._display_routing_table_output(result, ctx)  # WHY: renderer split for CC≤5
            return  # WHY: early-return prevents falling into the timeout branch
        self._print_routing_timeout()  # WHY: timeout UX split for CC≤5

    @staticmethod
    def _print_routing_timeout() -> None:
        """Print the routing-table timeout diagnostic block."""
        print("! Timeout waiting for routing table results")  # WHY: UX preserved
        print("! This may indicate:")  # WHY: UX preserved
        print("  - The device doesn't support routing table commands")  # WHY: UX preserved
        print("  - The device has no routing protocols configured")  # WHY: UX preserved
        print("  - The device is busy or not responding")  # WHY: UX preserved

    def _display_routing_table_output(
        self,
        result: dict[str, Any],
        ctx: RoutingTableContext,
    ) -> None:
        """Display formatted routing table results."""
        print("\n" + "=" * 80)  # WHY: separator matches legacy exactly
        print("ROUTING TABLE RESULTS:")  # WHY: UX preserved
        print("=" * 80)  # WHY: separator matches legacy exactly
        raw_output = result.get("raw", "")  # WHY: primary payload field for parsed rendering
        self._render_routing_section(raw_output, ctx.payload)  # WHY: main table renderer
        output_fields = result.get("Output", "")  # WHY: some devices emit an ADDITIONAL Output field
        if output_fields and output_fields != raw_output:  # WHY: skip when identical to raw
            self._render_additional_routing(output_fields, ctx.payload)  # WHY: additional renderer
        self._ru._display_debug_result_fields(result, ctx.debug_mode)  # WHY: shared debug dump
        self._ru._display_no_data_message(result, "routing table")  # WHY: shared no-data messaging
        print("=" * 80)  # WHY: bottom separator matches legacy exactly
        self._ru._log_command_completion("show routing table", ctx.device_id, ctx.device_info)

    def _render_routing_section(self, raw_output: str, payload: dict[str, Any]) -> None:
        """Render the primary routing-table section from ``raw_output``."""
        if not raw_output:  # WHY: guard clause avoids parsing an empty string
            return  # WHY: caller still emits debug/no-data messaging afterwards
        entries = self._ru._parse_routing_table(raw_output)  # WHY: shared parser on parent
        self._ru._display._display_routing_summary(entries, payload)  # WHY: display cluster owns

    def _render_additional_routing(self, output_fields: str, payload: dict[str, Any]) -> None:
        """Render an additional routing-table section from an alternate output field."""
        print("\n" + "=" * 40)  # WHY: separator matches legacy exactly
        print("ADDITIONAL OUTPUT:")  # WHY: UX preserved
        print("=" * 40)  # WHY: separator matches legacy exactly
        additional = self._ru._parse_routing_table(output_fields)  # WHY: shared parser on parent
        self._ru._display._display_routing_summary(additional, payload)  # WHY: display cluster owns

    # ------------------------------------------------------------------
    # Top-level routing-table orchestrator entry point
    # ------------------------------------------------------------------

    def execute_show_routing_table(self) -> None:
        """Execute show route command on switches via WebSocket."""
        debug_mode = (
            self._ru.check_fn()
        )  # WHY: capture debug flag once for entire flow (renamed from is_debug_mode_fn per 1012)
        self._ru._setup_debug_mode(debug_mode)  # WHY: hoist logger to DEBUG when needed
        logging.info("Starting WebSocket show routing table operation...")  # WHY: production log
        logging.debug("ENTER: execute_show_routing_table")  # WHY: trace marker for debug logs
        websocket_manager = None  # WHY: init early so finally-block cleanup is always safe
        try:  # WHY: outer try wraps the whole flow so KeyboardInterrupt/Exception cleanup runs
            websocket_manager = self._run_routing_table_flow(debug_mode)  # WHY: happy path split
        except KeyboardInterrupt:  # WHY: user interrupted with Ctrl-C
            print("\n! Operation interrupted by user")  # WHY: UX preserved
            logging.info("WebSocket show routing table operation interrupted by user")  # WHY: log
        except Exception as error:  # WHY: match legacy catch-all so no exceptions escape
            self._ru._handle_routing_error("routing table", error, debug_mode)  # WHY: shared handler
        finally:  # WHY: always disconnect regardless of success/failure
            self._ru._cleanup_websocket(websocket_manager, debug_mode)  # WHY: shared cleanup
            logging.debug("EXIT: execute_show_routing_table")  # WHY: trace marker for debug logs

    def _run_routing_table_flow(self, debug_mode: bool) -> Any | None:
        """Run the happy-path routing-table flow. Returns the websocket_manager to clean up."""
        from src.network.routing_utils import RoutingTableContext  # WHY: lazy import avoids cycle

        site_id, device_id, device_info = self._select_routing_table_device(debug_mode)  # WHY: pick
        if not site_id or not device_id:  # WHY: guard: user cancelled selection
            return None  # WHY: nothing to clean up
        payload = self._get_routing_table_params()  # WHY: prompt user for query params
        session = self._start_routing_session(site_id, device_id, payload, debug_mode)  # WHY: WS+cmd
        if session is None:  # WHY: guard: WS connect or POST failed
            return None  # WHY: nothing to disconnect / caller skips processing
        websocket_manager, session_id = session  # WHY: unpack the (WS handle, session id) tuple
        self._process_routing_table_results(  # WHY: block until result arrives
            RoutingTableContext(  # WHY: dataclass fields not counted as func params
                websocket_manager=websocket_manager,
                session_id=session_id,
                device_id=device_id,
                device_info=device_info,
                payload=payload,
                debug_mode=debug_mode,
            )
        )
        return websocket_manager  # WHY: caller finally-block will disconnect

    def _start_routing_session(
        self,
        site_id: str,
        device_id: str,
        payload: dict[str, Any],
        debug_mode: bool,
    ) -> tuple[Any, str] | None:
        """Open WebSocket + issue routing-table command. Return (ws, sid) or None on failure."""
        websocket_manager = self._ru._connect_websocket(site_id, device_id, debug_mode)  # WHY: WS
        if not websocket_manager:  # WHY: guard: connection failed
            return None  # WHY: nothing to disconnect
        session_id = self._execute_routing_table_command(  # WHY: POST the show-route command
            site_id, device_id, payload, debug_mode
        )
        if not session_id:  # WHY: guard: POST failed
            websocket_manager.disconnect()  # WHY: eager cleanup of half-open WS
            return None  # WHY: signal caller to skip result processing
        return websocket_manager, session_id  # WHY: caller consumes both handles
