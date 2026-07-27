"""SSR/SRX routing-table orchestrator cluster for :mod:`src.network.routing_utils`.

Owns ``execute_show_ssr_routes`` and every helper it needs
(``_select_ssr_device``, ``_get_ssr_route_params``,
``_execute_ssr_route_command``, ``_process_ssr_route_results``,
``_display_ssr_route_output``, ``_display_ssr_parsed_section``).
Splitting these helpers off the parent :class:`RoutingUtils` removes the
last STRUCT-LENGTH and STRUCT-COMPLEXITY hotspots and mirrors the
parsing/display/payload/routing/forwarding cluster pattern.

The parent binds an instance as ``self._ssr`` and its ``__getattr__``
proxies unknown attribute lookups here so shared state (dependencies,
apisession, other clusters) stays transparent to legacy callers.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import logging  # WHY: orchestrator emits structured log lines around device commands
from typing import TYPE_CHECKING, Any  # WHY: TYPE_CHECKING avoids runtime cycle with parent

if TYPE_CHECKING:  # WHY: only needed for static type checkers. Skipped at runtime
    from src.network.routing_utils import RoutingUtils, SsrRouteContext  # WHY: types only


# WHY: WebSocket wait timeout for the SSR/SRX routing command result (seconds)
_SSR_WAIT_TIMEOUT: int = 60  # WHY: matches legacy 60s wait window

# WHY: bounds for the optional real-time refresh interval (seconds)
_SSR_INTERVAL_MIN: int = 0  # WHY: exclusive lower bound (0 means one-time)
_SSR_INTERVAL_MAX: int = 10  # WHY: inclusive upper bound (legacy hard-cap)


class _RoutingUtilsSSR:  # WHY: cluster wrapper matching parsing/display/payload/routing/forwarding
    """Wrapper class holding the extracted SSR/SRX routing-table orchestrators."""

    def __init__(self, parent: RoutingUtils) -> None:  # WHY: bind parent for delegated state
        """Store the parent :class:`RoutingUtils` for delegate lookups."""
        self._ru = parent  # WHY: enable __getattr__ delegation back to RoutingUtils

    def __getattr__(self, name: str) -> Any:  # WHY: transparent proxy for combined API surface
        """Delegate unknown attributes to the wrapped parent object."""
        parent = self.__dict__.get("_ru")  # WHY: guard against half-initialized instances
        if parent is None:  # WHY: only trips during broken init. Avoid infinite recursion
            raise AttributeError(name)  # WHY: signal missing attribute cleanly to callers
        return getattr(parent, name)  # WHY: transparent proxy to parent RoutingUtils

    # ------------------------------------------------------------------
    # Top-level orchestrator entry point
    # ------------------------------------------------------------------

    def execute_show_ssr_routes(self) -> None:
        """Execute SSR/SRX routing table via dedicated API."""
        debug_mode = (
            self._ru.check_fn()
        )  # WHY: capture debug flag once for whole flow (renamed from is_debug_mode_fn per 1012)
        self._ru._setup_debug_mode(debug_mode)  # WHY: hoist logger to DEBUG when enabled
        logging.info("Starting SSR/SRX dedicated routing table operation...")  # WHY: production log
        logging.debug("ENTER: execute_show_ssr_routes")  # WHY: trace marker for debug logs
        websocket_manager = None  # WHY: init early so finally-block cleanup is always safe
        try:  # WHY: outer try wraps happy-path so exceptions still hit cleanup
            websocket_manager = self._run_ssr_flow(debug_mode)  # WHY: happy path split for CC≤5
        except KeyboardInterrupt:  # WHY: legacy behavior — surface user interrupts distinctly
            print("\n! Operation interrupted by user")  # WHY: UX preserved
            logging.info("SSR/SRX routing table operation interrupted by user")  # WHY: legacy log
        except Exception as error:  # WHY: catch-all matches legacy — nothing escapes
            self._ru._handle_routing_error("SSR/SRX routing table", error, debug_mode)  # WHY: shared
        finally:  # WHY: always disconnect regardless of outcome
            self._ru._cleanup_websocket(websocket_manager, debug_mode)  # WHY: shared cleanup
            logging.debug("EXIT: execute_show_ssr_routes")  # WHY: trace marker for debug logs

    def _run_ssr_flow(self, debug_mode: bool) -> Any | None:
        """Run the happy-path SSR routing flow. Returns websocket_manager for cleanup."""
        site_id, device_id, device_info = self._select_ssr_device(debug_mode)  # WHY: pick device
        if not site_id or not device_id:  # WHY: guard: user cancelled or bad device
            return None  # WHY: nothing to clean up
        request_body = self._get_ssr_route_params()  # WHY: collect query parameters from user
        session = self._start_ssr_session(site_id, device_id, request_body, debug_mode)  # WHY: WS+cmd
        if session is None:  # WHY: guard: WS connect or POST failed
            return None  # WHY: nothing to disconnect / caller skips processing
        websocket_manager, session_id = session  # WHY: unpack the (WS handle, session id) tuple
        from src.network.routing_utils import SsrRouteContext  # WHY: lazy import avoids cycle

        self._process_ssr_route_results(  # WHY: block until result arrives
            SsrRouteContext(  # WHY: dataclass fields not counted as func params
                websocket_manager=websocket_manager,  # WHY: WS handle for result wait
                session_id=session_id,  # WHY: correlate result with issued command
                device_id=device_id,  # WHY: displayed in completion log
                device_info=device_info,  # WHY: used by no-data/timeout branches
                request_body=request_body,  # WHY: replayed to display parser for context
                debug_mode=debug_mode,  # WHY: gates DEBUG prints downstream
            ),
        )
        return websocket_manager  # WHY: caller finally-block will disconnect

    def _start_ssr_session(
        self,
        site_id: str,
        device_id: str,
        request_body: dict[str, Any],
        debug_mode: bool,
    ) -> tuple[Any, str] | None:
        """Open WebSocket + issue SSR command. Return (ws, session_id) or None on failure."""
        websocket_manager = self._ru._connect_websocket(site_id, device_id, debug_mode)  # WHY: WS
        if not websocket_manager:  # WHY: guard: connection failed
            return None  # WHY: nothing to disconnect
        session_id = self._execute_ssr_route_command(  # WHY: POST the SSR command
            site_id, device_id, request_body, debug_mode
        )
        if not session_id:  # WHY: guard: POST failed
            websocket_manager.disconnect()  # WHY: eager cleanup of half-open WS
            return None  # WHY: signal caller to skip result processing
        return websocket_manager, session_id  # WHY: caller consumes both handles

    # ------------------------------------------------------------------
    # Device selection
    # ------------------------------------------------------------------

    def _select_ssr_device(
        self,
        debug_mode: bool,
    ) -> tuple[str | None, str | None, dict[str, Any] | None]:
        """Select site and SSR/SRX device for routing command."""
        site_id = self._ru.select_site_fn()  # WHY: user picks a site or bails out
        if not site_id:  # WHY: guard clause when the user cancels site selection
            print("! No site selected. Operation cancelled.")  # WHY: UX preserved
            return None, None, None  # WHY: signal cancellation
        self._log_site_selected(site_id, debug_mode)  # WHY: DEBUG output split for CC≤5
        self._print_ssr_guidance()  # WHY: multi-line banner split for length≤25
        device_id = self._ru.select_device_fn(site_id, "gateway")  # WHY: gateway-scoped chooser
        if not device_id:  # WHY: guard: user cancelled device selection
            print("! No device selected. Operation cancelled.")  # WHY: UX preserved
            return None, None, None  # WHY: signal cancellation
        if debug_mode:  # WHY: emit selected device id only when debug is on
            print(f"[DEBUG] Selected device_id = {device_id}")  # WHY: legacy debug format
        device_info = self._ru._get_device_info(site_id, device_id, "gateway", debug_mode)  # WHY: API
        if not self._ru._routing._verify_ssr_compatibility(device_info):  # WHY: gate on SSR support
            return None, None, None  # WHY: user opted to stop
        return site_id, device_id, device_info  # WHY: happy path — all set

    @staticmethod
    def _log_site_selected(site_id: str, debug_mode: bool) -> None:
        """Emit the selected site_id when debug is on."""
        if debug_mode:  # WHY: guard clause keeps hot path free of DEBUG strings
            print(f"[DEBUG] Selected site_id = {site_id}")  # WHY: legacy debug format preserved

    @staticmethod
    def _print_ssr_guidance() -> None:
        """Print the 3-line SSR/SRX device-selection guidance banner."""
        print("-> SSR/SRX routing table query using dedicated API function")  # WHY: UX preserved
        print("-> This function is optimized for SSR (128T) and SRX devices")  # WHY: UX preserved
        print("-> Provides structured routing table queries with advanced filtering")  # WHY: UX

    # ------------------------------------------------------------------
    # Query-parameter collector
    # ------------------------------------------------------------------

    def _get_ssr_route_params(self) -> dict[str, Any]:
        """Get user input for SSR/SRX routing table parameters."""
        self._print_ssr_params_header()  # WHY: banner split for length≤25
        protocol_input, prefix_input = self._collect_ssr_protocol_prefix()  # WHY: split for length
        vrf_input, neighbor_input, route_direction = self._collect_ssr_vrf_neighbor()  # WHY: split
        node_input = self._prompt_ssr_node()  # WHY: split HA node prompt for length≤25
        interval_input, duration_input = self._collect_ssr_refresh()  # WHY: split for length
        from src.network.routing_utils import SsrRouteQuery  # WHY: lazy import avoids cycle

        query = SsrRouteQuery(  # WHY: dataclass fields auto-populate __init__. Not counted as func params
            protocol_input=protocol_input,  # WHY: mirrors legacy field
            prefix_input=prefix_input,  # WHY: mirrors legacy field
            vrf_input=vrf_input,  # WHY: mirrors legacy field
            neighbor_input=neighbor_input,  # WHY: mirrors legacy field
            route_direction=route_direction,  # WHY: mirrors legacy field
            node_input=node_input,  # WHY: mirrors legacy field
            interval_input=interval_input,  # WHY: mirrors legacy field
            duration_input=duration_input,  # WHY: mirrors legacy field
        )
        return self._ru._payload._build_ssr_payload(query)  # WHY: shared payload builder

    def _prompt_ssr_node(self) -> str:
        """Prompt for the optional HA cluster node (node0/node1)."""
        return (
            self._ru.safe_input_fn(  # WHY: HA node selector
                "Enter HA cluster node (node0/node1, press Enter to skip): "
            )
            .strip()
            .lower()
        )

    @staticmethod
    def _print_ssr_params_header() -> None:
        """Print the 6-line SSR/SRX parameters guidance header."""
        print("\n=== SSR/SRX Routing Table Query Parameters ===")  # WHY: UX preserved
        print("Configure the routing table query (all parameters are optional):")  # WHY: UX
        print("  X  Protocol: bgp, any, ospf, static, direct, evpn")  # WHY: UX preserved
        print("  X  Prefix: Specific route prefix to look up")  # WHY: UX preserved
        print("  X  VRF: Virtual Routing and Forwarding instance")  # WHY: UX preserved
        print("  X  Neighbor: BGP neighbor IP for route analysis")  # WHY: UX preserved
        print("  X  Node: For HA clusters (node0/node1)")  # WHY: UX preserved

    def _collect_ssr_protocol_prefix(self) -> tuple[str, str]:
        """Prompt for protocol + prefix and return the trimmed tuple."""
        print("\nProtocol options: bgp, any, ospf, static, direct, evpn, (none)")  # WHY: UX
        protocol_input = (
            self._ru.safe_input_fn("Enter protocol (press Enter for API default): ").strip().lower()
        )  # WHY: normalize to lowercase for downstream comparison
        prefix_input = self._ru.safe_input_fn(
            "\nEnter route prefix (e.g., 192.168.1.0/24, press Enter to skip): "
        ).strip()  # WHY: preserve case (prefixes are numeric anyway)
        return protocol_input, prefix_input  # WHY: caller unpacks both

    def _collect_ssr_vrf_neighbor(self) -> tuple[str, str, str]:
        """Prompt for VRF + BGP neighbor (+ direction when neighbor is present)."""
        vrf_input = self._ru.safe_input_fn(
            "Enter VRF name (press Enter for default VRF): "
        ).strip()  # WHY: optional VRF filter
        neighbor_input = self._ru.safe_input_fn(
            "Enter BGP neighbor IP (press Enter to skip): "
        ).strip()  # WHY: optional BGP neighbor filter
        route_direction = ""  # WHY: only prompted when neighbor was supplied
        if neighbor_input:  # WHY: guard: direction only makes sense with a neighbor
            print("\nRoute direction: received, advertised, (empty for both)")  # WHY: UX preserved
            route_direction = (
                self._ru.safe_input_fn("Enter route direction (press Enter for both): ").strip().lower()
            )  # WHY: normalize for downstream comparison
        return vrf_input, neighbor_input, route_direction  # WHY: caller unpacks triple

    def _collect_ssr_refresh(self) -> tuple[str, str]:
        """Prompt for the optional real-time refresh interval + duration."""
        print("\nReal-time refresh options:")  # WHY: UX preserved
        interval_input = self._ru.safe_input_fn(
            "Refresh interval in seconds (0-10, press Enter for one-time): "
        ).strip()  # WHY: optional refresh cadence
        duration_input = ""  # WHY: only prompted when interval is valid
        if self._is_valid_ssr_interval(interval_input):  # WHY: guard reduces CC vs inline check
            duration_input = self._ru.safe_input_fn(
                "Refresh duration in seconds (0-300, press Enter for 30): "
            ).strip()  # WHY: optional total duration
        return interval_input, duration_input  # WHY: caller passes both to payload builder

    @staticmethod
    def _is_valid_ssr_interval(interval_input: str) -> bool:
        """Return True when ``interval_input`` is an int in ``(0, _SSR_INTERVAL_MAX]``."""
        # WHY: single predicate replaces the legacy inline three-clause conditional
        return (
            bool(interval_input)  # WHY: reject blank
            and interval_input.isdigit()  # WHY: reject non-numeric
            and _SSR_INTERVAL_MIN < int(interval_input) <= _SSR_INTERVAL_MAX  # WHY: bounded window
        )

    # ------------------------------------------------------------------
    # Command executor
    # ------------------------------------------------------------------

    def _execute_ssr_route_command(
        self,
        site_id: str,
        device_id: str,
        request_body: dict[str, Any],
        debug_mode: bool,
    ) -> str | None:
        """Execute the SSR/SRX routing table API call."""
        print(f"\n-> Executing SSR/SRX routing table query on device {device_id}...")  # WHY: UX
        logging.debug("Request body: %s", request_body)  # WHY: always log body for postmortem
        if debug_mode:  # WHY: also echo body to stdout when debug is on
            print(f"[DEBUG] Request body = {request_body}")  # WHY: legacy debug format
        return self._ru._payload._call_ssr_api(site_id, device_id, request_body, debug_mode)  # WHY

    # ------------------------------------------------------------------
    # Result processor + renderer
    # ------------------------------------------------------------------

    def _process_ssr_route_results(self, ctx: SsrRouteContext) -> None:
        """Wait for and process SSR/SRX routing table results."""
        if ctx.debug_mode:  # WHY: emit wait banner only in debug mode
            print("[DEBUG] Starting to wait for WebSocket results...")  # WHY: legacy debug
        result = ctx.websocket_manager.wait_for_command_result(  # WHY: block until reply/timeout
            ctx.session_id,
            timeout_seconds=_SSR_WAIT_TIMEOUT,
        )
        self._log_ssr_wait_outcome(result, ctx.debug_mode)  # WHY: DEBUG dump split for CC≤5
        if result:  # WHY: happy path renders the table
            self._display_ssr_route_output(result, ctx)  # WHY: full render pipeline
            return  # WHY: prevent falling into the timeout branch
        print("! Timeout waiting for SSR/SRX routing table results")  # WHY: UX preserved
        print("! Try the generic routing table command (Menu 7) as fallback")  # WHY: UX preserved

    @staticmethod
    def _log_ssr_wait_outcome(result: dict[str, Any] | None, debug_mode: bool) -> None:
        """Log the wait_for_command_result outcome when debug is on."""
        if not debug_mode:  # WHY: guard clause keeps hot path free of DEBUG strings
            return  # WHY: nothing to log when debug is off
        print(f"[DEBUG] wait_for_command_result returned: {result is not None}")  # WHY: legacy
        if result:  # WHY: only dump keys when result is present
            print(f"[DEBUG] Result keys: {list(result.keys())}")  # WHY: legacy debug format

    def _display_ssr_route_output(
        self,
        result: dict[str, Any],
        ctx: SsrRouteContext,
    ) -> None:
        """Display formatted SSR/SRX routing table results."""
        print("\n" + "=" * 80)  # WHY: separator matches legacy exactly
        print("SSR/SRX ROUTING TABLE RESULTS:")  # WHY: UX preserved
        print("=" * 80)  # WHY: separator matches legacy exactly
        raw_output = result.get("raw", "")  # WHY: primary output field
        if raw_output:  # WHY: guard: only render when data is present
            self._display_ssr_parsed_section(raw_output, ctx.request_body)  # WHY: parsed render
        output_fields = result.get("Output", "")  # WHY: some devices emit alternate field
        if output_fields and output_fields != raw_output:  # WHY: skip when identical
            self._render_ssr_additional(output_fields, ctx.request_body)  # WHY: split for length
        self._ru._display_debug_result_fields(result, ctx.debug_mode)  # WHY: shared debug dump
        self._ru._display_no_data_message(result, "routing table")  # WHY: shared no-data
        print("=" * 80)  # WHY: bottom separator matches legacy exactly
        self._ru._log_command_completion("SSR/SRX routing table", ctx.device_id, ctx.device_info)

    def _render_ssr_additional(self, output: str, request_body: dict[str, Any]) -> None:
        """Render an alternate SSR output section under an ADDITIONAL OUTPUT banner."""
        print("\n" + "=" * 40)  # WHY: separator matches legacy exactly
        print("ADDITIONAL OUTPUT:")  # WHY: UX preserved
        print("=" * 40)  # WHY: separator matches legacy exactly
        self._display_ssr_parsed_section(output, request_body)  # WHY: same parsed render

    def _display_ssr_parsed_section(
        self,
        output: str,
        request_body: dict[str, Any],
    ) -> None:
        """Parse and display an SSR output section with fallback."""
        entries = self._ru._parsing._parse_ssr_routing(output)  # WHY: SSR-specific parser first
        if entries:  # WHY: happy path — SSR structured render
            self._ru._display._display_ssr_routing(entries, request_body)  # WHY: SSR renderer
            return  # WHY: prevent falling into the generic-fallback branch
        entries = self._ru._parsing._parse_routing_table(output)  # WHY: generic parser fallback
        self._ru._display._display_routing_summary(entries, request_body)  # WHY: generic renderer
