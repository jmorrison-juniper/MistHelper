"""Routing utilities for Mist network devices.

Extracted from MistHelper.py (Issue #207). Provides three WebSocket-based
routing table operations: forwarding table (gateways), routing table
(switches), and SSR/SRX dedicated routing queries.

Dependencies are injected via constructor for testability.
"""

# pylint: disable=logging-fstring-interpolation

from __future__ import annotations  # WHY: postponed evaluation for cluster forward refs

import logging  # WHY: shared logger for debug/info/error messaging
import time  # WHY: pause after WebSocket subscription completes
from collections.abc import Callable  # WHY: dependency-callable typing
from dataclasses import dataclass  # WHY: frozen deps + WebSocket context bundles
from typing import Any  # WHY: opaque handles for mistapi/manager objects

import mistapi  # WHY: device metadata lookup for compatibility checks

from src.network._routing_utils_display import _RoutingUtilsDisplay  # WHY: table renderers
from src.network._routing_utils_forwarding import _RoutingUtilsForwarding  # WHY: forwarding orchestrator
from src.network._routing_utils_parsing import _RoutingUtilsParsing  # WHY: parser cluster
from src.network._routing_utils_payload import _RoutingUtilsPayload  # WHY: HTTP/API cluster
from src.network._routing_utils_routing import _RoutingUtilsRouting  # WHY: routing table orchestrator
from src.network._routing_utils_ssr import _RoutingUtilsSSR  # WHY: SSR orchestrator

logger = logging.getLogger(__name__)  # WHY: module-scoped logger for #886 print-to-logger migration.


# ---------------------------------------------------------------------------
# Type aliases for dependency injection
# ---------------------------------------------------------------------------
SelectSiteFn = Callable[[], str | None]  # WHY: interactive site picker
SelectDeviceFn = Callable[[str, str], str | None]  # WHY: interactive device picker
SafeInputFn = Callable[..., str]  # WHY: KeyboardInterrupt-safe input helper
WebSocketManagerFactory = Callable[[Any], Any]  # WHY: factory for injected manager
IsDebugModeFn = Callable[[], bool]  # WHY: debug-mode toggle probe


@dataclass(frozen=True)
class RoutingDeps:
    """Injected dependencies for :class:`RoutingUtils` (Phase 1 refactor).

    Bundles the 6 constructor callables/objects into a single frozen
    dataclass so downstream call sites and tests build one object
    instead of passing 6 kwargs, and so the parent ``__init__`` stays
    within STRUCT-PARAMS limits.
    """

    apisession: Any  # WHY: mistapi.APISession handle
    select_site_fn: SelectSiteFn  # WHY: site picker callable
    select_device_fn: SelectDeviceFn  # WHY: device picker callable
    safe_input_fn: SafeInputFn  # WHY: safe stdin reader
    websocket_manager_factory: WebSocketManagerFactory  # WHY: WSManager constructor
    check_fn: IsDebugModeFn  # WHY: debug-mode probe (renamed from is_debug_mode_fn per 1012 DI-cluster rename)


@dataclass
class RoutingTableContext:
    """Shared context for routing table WebSocket operations."""

    websocket_manager: Any  # WHY: live WS handle for cleanup
    session_id: str  # WHY: correlates async command result
    device_id: str  # WHY: target device identifier
    device_info: dict[str, Any] | None  # WHY: enriches user-facing messages
    payload: dict[str, Any]  # WHY: outgoing REST body
    debug_mode: bool  # WHY: gates verbose debug traces


@dataclass
class SsrRouteQuery:
    """User inputs for building an SSR/SRX route query payload."""

    protocol_input: str  # WHY: bgp/ospf/static/direct/evpn/any
    prefix_input: str  # WHY: CIDR prefix filter
    vrf_input: str  # WHY: VRF instance name
    neighbor_input: str  # WHY: BGP neighbor IP
    route_direction: str  # WHY: received/advertised
    node_input: str  # WHY: node0/node1 for HA clusters
    interval_input: str  # WHY: refresh interval seconds
    duration_input: str  # WHY: refresh duration seconds


@dataclass
class SsrRouteContext:
    """Shared context for SSR/SRX routing WebSocket operations."""

    websocket_manager: Any  # WHY: live WS handle for cleanup
    session_id: str  # WHY: correlates async command result
    device_id: str  # WHY: target device identifier
    device_info: dict[str, Any] | None  # WHY: enriches user-facing messages
    request_body: dict[str, Any]  # WHY: SSR-specific request payload
    debug_mode: bool  # WHY: gates verbose debug traces


# WHY: cluster attribute names looped over by __getattr__ for O(1) proxying.
_CLUSTER_ATTRS: tuple[str, ...] = (
    "_parsing",  # WHY: text/JSON route parsers
    "_display",  # WHY: PrettyTable renderers
    "_payload",  # WHY: HTTP payload builders
    "_routing",  # WHY: routing-table orchestrator
    "_forwarding",  # WHY: forwarding-table orchestrator
    "_ssr",  # WHY: SSR/SRX orchestrator
)


class RoutingUtils:
    """Routing table operations via WebSocket and dedicated APIs.

    Three public entry points:
    - execute_show_forwarding_table: FIB on gateways/SSR via WebSocket
    - execute_show_routing_table: RIB on switches via WebSocket
    - execute_show_ssr_routes: SSR/SRX dedicated routing API

    All external dependencies are injected via constructor.
    """

    def __init__(self, deps: RoutingDeps) -> None:
        """Initialize RoutingUtils with injected dependencies (see RoutingDeps)."""
        self.apisession = deps.apisession  # WHY: unpack for direct mistapi calls
        self.select_site_fn = deps.select_site_fn  # WHY: unpack site picker
        self.select_device_fn = deps.select_device_fn  # WHY: unpack device picker
        self.safe_input_fn = deps.safe_input_fn  # WHY: unpack safe-input callable
        self.websocket_manager_factory = deps.websocket_manager_factory  # WHY: unpack WS factory
        self.check_fn = deps.check_fn  # WHY: unpack debug probe (renamed from is_debug_mode_fn per 1012)
        self._parsing = _RoutingUtilsParsing(self)  # WHY: parser cluster binding
        self._display = _RoutingUtilsDisplay(self)  # WHY: renderer cluster binding
        self._payload = _RoutingUtilsPayload(self)  # WHY: payload cluster binding
        self._routing = _RoutingUtilsRouting(self)  # WHY: routing orchestrator binding
        self._forwarding = _RoutingUtilsForwarding(self)  # WHY: forwarding orchestrator binding
        self._ssr = _RoutingUtilsSSR(self)  # WHY: SSR orchestrator binding

    def __getattr__(self, name: str) -> Any:
        """Proxy cluster-attribute access to the six helper clusters.

        Python only invokes ``__getattr__`` when normal lookup fails, so this
        method resolves cluster method calls (``self._parse_ssr_routing``,
        ``self._display_forwarding_summary``, ``self._post_device_command``,
        ``self.execute_show_routing_table``, and so on) without explicit delegator
        wrappers. The class-level ``hasattr`` check on ``type(cluster)``
        avoids invoking the cluster's own ``__getattr__`` (which would proxy
        back to this class and create infinite recursion for unknown attrs).
        """
        for attr in _CLUSTER_ATTRS:  # WHY: iterate cluster attribute names
            cluster = self.__dict__.get(attr)  # WHY: direct dict access avoids recursion
            if cluster is not None and hasattr(type(cluster), name):  # WHY: class-level lookup only
                return getattr(cluster, name)  # WHY: bound method resolves through cluster
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")

    # =====================================================================
    # PUBLIC ENTRY POINTS (delegated to orchestrator clusters)
    # =====================================================================

    def execute_show_forwarding_table(self) -> None:
        """Execute show forwarding table on a gateway/SSR via WebSocket."""
        self._forwarding.execute_show_forwarding_table()  # WHY: delegate to cluster

    def execute_show_ssr_routes(self) -> None:
        """Execute SSR/SRX routing table via dedicated API."""
        self._ssr.execute_show_ssr_routes()  # WHY: delegate to cluster

    # =====================================================================
    # SHARED HELPERS (used by forwarding, routing, and SSR clusters)
    # =====================================================================

    def _setup_debug_mode(self, debug_mode: bool) -> None:
        """Configure logging for debug mode if enabled."""
        if debug_mode:  # WHY: only elevate logger when debug requested
            logging.getLogger().setLevel(logging.DEBUG)  # WHY: hoist root logger to DEBUG
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.debug("[DEBUG] DEBUG MODE ENABLED")  # WHY: user-visible confirmation

    def _get_device_info(
        self,
        site_id: str,
        device_id: str,
        device_type: str,
        debug_mode: bool,
    ) -> dict[str, Any] | None:
        """Retrieve device information for compatibility checking."""
        try:  # WHY: mistapi calls may raise on network/auth failures
            return self._fetch_device_info(site_id, device_id, device_type, debug_mode)  # WHY: happy path
        except Exception as error:  # WHY: log-and-continue on any mistapi error
            self._log_device_info_error(error, debug_mode)  # WHY: warn + degrade gracefully
            return None  # WHY: caller treats None as "compatibility unknown"

    def _fetch_device_info(
        self,
        site_id: str,
        device_id: str,
        device_type: str,
        debug_mode: bool,
    ) -> dict[str, Any] | None:
        """Look up the device record via mistapi and emit debug details."""
        rawdata = mistapi.api.v1.sites.devices.listSiteDevices(  # WHY: list devices at site
            self.apisession, site_id, type=device_type
        ).data
        device_info = next(  # WHY: match on device id
            (device for device in rawdata if device.get("id") == device_id),
            None,
        )
        if device_info and debug_mode:  # WHY: emit metadata only when both present
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.debug(
                "[DEBUG] Device type: %s, model: %s, name: %s",
                device_info.get("type"),
                device_info.get("model"),
                device_info.get("name"),
            )
        return device_info  # WHY: caller uses metadata for guidance rendering

    def _log_device_info_error(self, error: Exception, debug_mode: bool) -> None:
        """Emit user-facing warning and optional debug trace for device lookup failure."""
        logging.warning("Could not verify device compatibility: %s", error)  # WHY: audit trail
        if debug_mode:  # WHY: extra visibility when troubleshooting
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.debug("[DEBUG] Device check failed: %s", error)  # WHY: expose exception message
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("   -> Proceeding with standard command")  # WHY: reassure operator

    def _connect_websocket(self, site_id: str, device_id: str, debug_mode: bool) -> Any | None:
        """Establish WebSocket connection and subscribe to channel."""
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("\n-> Executing show forwarding table on device %s...", device_id)  # WHY: user progress
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("-> Establishing WebSocket connection...")  # WHY: signal WS phase start
        websocket_manager = self._init_websocket_manager(debug_mode)  # WHY: build + connect
        if not websocket_manager:  # WHY: bail on connection failure
            return None
        if not self._subscribe_command_channel(  # WHY: bail on subscription failure
            websocket_manager,
            site_id,
            device_id,
            debug_mode,
        ):
            return None
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("-> WebSocket connected and subscribed")  # WHY: confirm success
        time.sleep(1)  # WHY: give server a beat before command dispatch
        return websocket_manager  # WHY: hand back live handle

    def _init_websocket_manager(self, debug_mode: bool) -> Any | None:
        """Create the WebSocket manager and establish the transport connection."""
        websocket_manager = self.websocket_manager_factory(self.apisession)  # WHY: instantiate via factory
        if debug_mode:  # WHY: trace lifecycle
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.debug("[DEBUG] WebSocketManager initialized")  # WHY: confirm object built
        if not websocket_manager.connect():  # WHY: attempt TCP/TLS handshake
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("! Failed to establish WebSocket connection")  # WHY: user-facing failure
            return None  # WHY: signal caller to abort
        if debug_mode:  # WHY: trace lifecycle
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.debug("[DEBUG] WebSocket connection established")  # WHY: confirm handshake success
        return websocket_manager  # WHY: caller subscribes next

    def _subscribe_command_channel(
        self,
        websocket_manager: Any,
        site_id: str,
        device_id: str,
        debug_mode: bool,
    ) -> bool:
        """Subscribe to the device command channel; returns False on failure."""
        command_channel = f"/sites/{site_id}/devices/{device_id}/cmd"  # WHY: per-device command topic
        if not websocket_manager.subscribe_to_channel(command_channel):  # WHY: attempt subscription
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("! Failed to subscribe to device command channel")  # WHY: user-facing failure
            websocket_manager.disconnect()  # WHY: clean up partial connection
            return False  # WHY: caller aborts flow
        if debug_mode:  # WHY: trace subscription success
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.debug("[DEBUG] Subscribed to channel: %s", command_channel)  # WHY: confirm channel name
        return True  # WHY: caller may proceed with dispatch

    def _display_debug_result_fields(self, result: dict[str, Any], debug_mode: bool) -> None:
        """Display debug fields from WebSocket result if debug mode is on."""
        if not debug_mode:  # WHY: guard clause skips output when disabled
            return
        available = self._collect_debug_fields(result)  # WHY: filter to non-standard keys
        if not available:  # WHY: skip banner when nothing to show
            return
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.debug("\n[DEBUG] OTHER AVAILABLE FIELDS: %s", available)  # WHY: banner + key list
        self._dump_debug_field_values(result, available)  # WHY: emit per-field values

    @staticmethod
    def _collect_debug_fields(result: dict[str, Any]) -> list[str]:
        """Return keys in result that are not part of the standard payload."""
        excluded = {"raw", "Output", "session"}  # WHY: already rendered elsewhere
        return [key for key in result if key not in excluded]  # WHY: keep only extras

    @staticmethod
    def _dump_debug_field_values(result: dict[str, Any], available: list[str]) -> None:
        """Print each non-empty extra field on its own debug line."""
        for field in available:  # WHY: iterate discovered extras
            if result.get(field):  # WHY: skip empty/None values
                # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
                logger.debug("[DEBUG] %s: %s", field, result.get(field))  # WHY: expose value for triage

    def _display_no_data_message(self, result: dict[str, Any], label: str) -> None:
        """Display message when no raw or Output data is present."""
        raw_output = result.get("raw", "")  # WHY: primary payload slot
        output_fields = result.get("Output", "")  # WHY: secondary payload slot
        if not raw_output and not output_fields:  # WHY: both empty means nothing came back
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("! No %s data received", label)  # WHY: user-facing summary
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("Available result keys: %s", list(result.keys()))  # WHY: aid triage

    def _log_command_completion(
        self,
        operation: str,
        device_id: str,
        device_info: dict[str, Any] | None,
    ) -> None:
        """Log successful command completion with device context."""
        device_context = f"device {device_id}"  # WHY: fallback when no metadata
        if device_info:  # WHY: prefer human-friendly type+name
            device_context = f"{device_info.get('type', 'unknown')} {device_info.get('name', device_id[:8])}"
        logging.info("WebSocket %s completed successfully for %s", operation, device_context)  # WHY: audit trail

    def _handle_routing_error(
        self,
        operation_name: str,
        error: Exception,
        debug_mode: bool,
    ) -> None:
        """Handle exceptions during routing operations."""
        error_message = f"WebSocket {operation_name} operation failed: {error}"  # WHY: formatted context
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.error("! %s", error_message)  # WHY: user-facing failure
        logging.error(error_message)  # WHY: persist in log
        if debug_mode:  # WHY: dump traceback only under debug
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.debug("[DEBUG] Exception details:")  # WHY: banner
            import traceback  # WHY: lazy import to avoid unused cost in hot paths

            traceback.print_exc()  # WHY: full traceback for triage

    def _cleanup_websocket(self, websocket_manager: Any | None, debug_mode: bool) -> None:
        """Cleanup WebSocket connection."""
        try:  # WHY: never let cleanup escalate to caller
            if websocket_manager is not None:  # WHY: skip when never connected
                websocket_manager.disconnect()  # WHY: release socket
                # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
                logger.info("-> WebSocket connection closed")  # WHY: user confirmation
                if debug_mode:  # WHY: trace lifecycle end
                    # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
                    logger.debug("[DEBUG] WebSocket cleanup completed")  # WHY: confirm cleanup step
        except Exception as cleanup_error:  # WHY: swallow to guarantee finally-safety
            logging.warning("WebSocket cleanup error: %s", cleanup_error)  # WHY: audit trail
