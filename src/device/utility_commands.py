"""Device utility commands for Mist network devices.

Extracted from MistHelper.py (Issue #210). Provides 35 device utility
operations spanning diagnostics, show commands, management, clear/reset,
and hardware operations. Menu range: 123-157.

Dependencies are injected via constructor for testability.
"""

# pylint: disable=logging-fstring-interpolation,implicit-str-concat

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

from collections.abc import Callable  # WHY: type aliases for DI callables
from dataclasses import dataclass  # WHY: bundle 6 injected deps into a frozen struct
from typing import Any  # WHY: broad response typing for mistapi wrappers

from ._utility_commands_action import (
    _UtilityCommandsAction,  # WHY: management/action command cluster (Phase 4a split)
)
from ._utility_commands_clear import (
    _UtilityCommandsClear,  # WHY: destructive clear/reset command cluster (Phase 4b split)
)
from ._utility_commands_selection import (
    _UtilityCommandsSelection,  # WHY: selection helper cluster (Phase 1 split)
)
from ._utility_commands_show import (
    _UtilityCommandsShow,  # WHY: show/diagnostic command cluster (Phase 3 split)
)
from ._utility_commands_websocket import (
    _UtilityCommandsWebsocket,  # WHY: websocket helper cluster (Phase 2 split)
)

# ---------------------------------------------------------------------------
# Type aliases for dependency injection
# ---------------------------------------------------------------------------
SelectSiteFn = Callable[[], str | None]  # WHY: interactive site picker signature
SelectDeviceFn = Callable[[str, str], str | None]  # WHY: interactive device picker signature
SafeInputFn = Callable[..., str]  # WHY: EOF-safe stdin reader signature
WriteExportFn = Callable[[list[dict[str, Any]], str, str], bool]  # WHY: exporter returns success bool
WebSocketManagerFactory = Callable[[Any], Any]  # WHY: WSManager factory signature


@dataclass(frozen=True)
class UtilityCommandsDeps:  # WHY: frozen bundle keeps parent __init__ under STRUCT-PARAMS
    """Injected dependencies for :class:`DeviceUtilityCommands`.

    Bundles the 6 dependencies into a single frozen dataclass so
    construction sites and tests build one struct instead of passing 6
    kwargs, and so the parent ``__init__`` fits the STRUCT-PARAMS limit.
    """

    apisession: Any  # WHY: mistapi.APISession handle used by every command
    select_site_fn: SelectSiteFn  # WHY: interactive site picker
    select_device_fn: SelectDeviceFn  # WHY: interactive device picker (filtered by type)
    safe_input_fn: SafeInputFn  # WHY: EOF-safe stdin reader
    write_export_fn: WriteExportFn  # WHY: exporter writing device-command output
    websocket_manager_factory: WebSocketManagerFactory  # WHY: factory for WebSocketManager


# WHY: HTTP status codes >= this value denote an error response.
_HTTP_ERROR_THRESHOLD = 400  # WHY: sentinel threshold shared by API result helpers


def _extract_error_detail(response: Any) -> str:  # WHY: pull optional .data.detail off a response
    """Return the ``data.detail`` string from a response, or empty string."""
    data = getattr(response, "data", None)  # WHY: guard missing .data on error responses
    if isinstance(data, dict):  # WHY: only mistapi dicts carry the detail key
        return str(data.get("detail", ""))  # WHY: coerce to str for concatenation
    return ""  # WHY: unknown shape -> no detail available


def _print_api_error(response: Any, fail_msg: str, status_code: int) -> None:  # WHY: uniform HTTP-error formatter
    """Print a formatted error line including the status code and any detail."""
    detail = _extract_error_detail(response)  # WHY: pull optional server message
    error_text = f"! {fail_msg} (HTTP {status_code})"  # WHY: base line always includes status
    if detail:  # WHY: append server-side context when available
        error_text += f": {detail}"  # WHY: keep detail on same line for grep-ability
    print(error_text)  # WHY: single write to keep operator output atomic


class DeviceUtilityCommands:  # WHY: parent class hosting 35 device-command operations
    """Device utility commands covering 35 Mist API endpoints.

    Categories: diagnostics, show commands, device management, clear/reset,
    hardware operations. Device type validation before every API call.
    Three-tier confirmation: none (read-only), y/N (port bounce, reprovision),
    typed 'CLEAR' (clear/reset operations).
    """

    DEVICE_TYPE_COMPATIBILITY_MAP: dict[str, list[str]] = {  # WHY: gate per-command by device type
        "traceroute": ["ap", "switch", "gateway"],
        "show_ospf_neighbors": ["gateway"],
        "show_ospf_interfaces": ["gateway"],
        "show_ospf_database": ["gateway"],
        "show_ospf_summary": ["gateway"],
        "show_session": ["gateway"],
        "show_service_path": ["gateway"],
        "show_bgp_summary": ["switch", "gateway"],
        "show_arp_table": ["switch", "gateway"],
        "show_dhcp_leases": ["switch", "gateway"],
        "show_dot1x": ["switch"],
        "show_evpn_database": ["switch", "gateway"],
        "resolve_dns": ["gateway"],
        "monitor_traffic": ["switch", "gateway"],
        "run_top": ["switch", "gateway"],
        "locate": ["ap", "switch"],
        "unlocate": ["ap", "switch"],
        "bounce_port": ["switch", "gateway"],
        "cable_test": ["switch"],
        "reprovision": ["switch", "gateway"],
        "readopt": ["switch"],
        "ztp_password": ["switch", "gateway"],
        "config_cmd": ["switch"],
        "support_upload": ["switch", "gateway"],
        "clear_arp": ["switch", "gateway"],
        "clear_bgp": ["gateway"],
        "clear_session": ["gateway"],
        "clear_mac_table": ["switch", "gateway"],
        "clear_bpdu_error": ["switch"],
        "clear_macs": ["switch"],
        "clear_policy_hit_count": ["gateway"],
        "release_dhcp": ["switch", "gateway"],
        "release_dhcp_ssr": ["gateway"],
        "poll_stats": ["switch"],
        "snapshot": ["switch"],
    }

    def __init__(self, deps: UtilityCommandsDeps) -> None:  # WHY: single-arg deps struct satisfies STRUCT-PARAMS
        """Initialize with the injected :class:`UtilityCommandsDeps` bundle.

        Args:
            deps: Frozen dataclass carrying the 6 dependency callables/objects
                consumed by the various device-command flows.
        """
        self._apisession = deps.apisession  # WHY: mistapi handle
        self._select_site_fn = deps.select_site_fn  # WHY: site picker callable
        self._select_device_fn = deps.select_device_fn  # WHY: device picker callable
        self._safe_input_fn = deps.safe_input_fn  # WHY: EOF-safe input
        self._write_export_fn = deps.write_export_fn  # WHY: exporter callable
        self._ws_factory = deps.websocket_manager_factory  # WHY: WSManager factory
        # WHY: bundle clusters in a single tuple so parent stays at 7 instance attrs (R0902 gate)
        self._clusters: tuple[Any, ...] = (
            _UtilityCommandsSelection(self),  # WHY: selection cluster binding
            _UtilityCommandsWebsocket(self),  # WHY: websocket cluster binding
            _UtilityCommandsShow(self),  # WHY: show/diagnostic cluster binding
            _UtilityCommandsAction(self),  # WHY: management/action cluster binding
            _UtilityCommandsClear(self),  # WHY: destructive clear/reset cluster binding
        )

    def __getattr__(self, name: str) -> Any:  # WHY: transparently proxies to cluster helpers
        """Proxy cluster-attribute access to helper clusters.

        Python only invokes ``__getattr__`` when normal lookup fails, so
        this method resolves cluster method calls (``self._validate_device_type``,
        ``self._select_site_and_device``, ``self._select_port_from_device``,
        etc.) without explicit delegator wrappers. The class-level
        ``hasattr`` check on ``type(cluster)`` avoids invoking the
        cluster's own ``__getattr__`` (which would proxy back to this
        class and cause infinite recursion for unknown attrs).
        """
        for cluster in self.__dict__.get("_clusters", ()):  # WHY: iterate bundled clusters
            if hasattr(type(cluster), name):  # WHY: class-level lookup avoids cluster __getattr__ recursion
                return getattr(cluster, name)  # WHY: bound method resolves through cluster
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")  # WHY: mirror stdlib msg

    # ------------------------------------------------------------------
    # Private helpers retained on the parent (referenced by tests at class level)
    # ------------------------------------------------------------------

    @staticmethod
    def _print_api_result(response: Any, success_msg: str, fail_msg: str) -> bool:  # WHY: uniform HTTP-status renderer
        """Check API response status and print message.

        Delegates status extraction and error formatting to module-level
        helpers so this method stays at complexity <= 5.
        """
        status = getattr(response, "status_code", None)  # WHY: guard missing attr on mocks
        if isinstance(status, int) and status >= _HTTP_ERROR_THRESHOLD:  # WHY: only ints compare
            _print_api_error(response, fail_msg, status)  # WHY: delegate detail extraction
            return False  # WHY: caller treats False as failure
        print(f"-> {success_msg}")  # WHY: emit success line
        return True  # WHY: caller treats True as success

    @staticmethod
    def _handle_clear_session_error(error: Exception) -> None:
        """Handle clear session API errors with guidance."""
        try:
            code = getattr(error, "status_code", None) or getattr(
                getattr(error, "response", None),
                "status_code",
                None,
            )  # WHY: try both mistapi error shapes
            if code == 400:  # WHY: 400 == missing service_name/session_ids body key
                print(
                    "! API returned 400. The API expects either"
                    " 'service_name' or 'session_ids' in the"
                    " request body."
                )  # WHY: teach operator the fix
                print(
                    "  Provide a service name or a comma-separated list of session IDs, and retry."
                )  # WHY: guide follow-up input
            else:
                print(f"! Clear session failed: {error}")  # WHY: generic fallback
        except Exception:  # pylint: disable=broad-exception-caught
            print(f"! Clear session failed: {error}")  # WHY: never let error-handler raise
