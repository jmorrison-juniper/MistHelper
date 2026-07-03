"""Device utility commands for Mist network devices.

Extracted from MistHelper.py (Issue #210). Provides 35 device utility
operations spanning diagnostics, show commands, management, clear/reset,
and hardware operations. Menu range: 123-157.

Dependencies are injected via constructor for testability.
"""

# pylint: disable=too-many-lines,logging-fstring-interpolation,implicit-str-concat

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass  # WHY: bundle 6 injected deps into a frozen struct
from typing import Any

import mistapi

from src.device._utility_commands_selection import (
    _UtilityCommandsSelection,  # WHY: selection helper cluster (Phase 1 split)
)
from src.device._utility_commands_show import (
    _UtilityCommandsShow,  # WHY: show/diagnostic command cluster (Phase 3 split)
)
from src.device._utility_commands_websocket import (
    _UtilityCommandsWebsocket,  # WHY: websocket helper cluster (Phase 2 split)
)

# ---------------------------------------------------------------------------
# Type aliases for dependency injection
# ---------------------------------------------------------------------------
SelectSiteFn = Callable[[], str | None]
SelectDeviceFn = Callable[[str, str], str | None]
SafeInputFn = Callable[..., str]
WriteExportFn = Callable[[list[dict[str, Any]], str, str], bool]  # Exporter returns a success bool, not None
WebSocketManagerFactory = Callable[[Any], Any]


@dataclass(frozen=True)
class UtilityCommandsDeps:
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


# WHY: cluster attribute names looped over by __getattr__ for O(N) proxying.
_CLUSTER_ATTRS: tuple[str, ...] = (
    "_selection",  # WHY: site/device/port/interface/network selection helpers
    "_websocket",  # WHY: WebSocket command lifecycle + confirm/print helpers
    "_show",  # WHY: read-only show / diagnostic commands (Phase 3)
)


class DeviceUtilityCommands:
    """Device utility commands covering 35 Mist API endpoints.

    Categories: diagnostics, show commands, device management, clear/reset,
    hardware operations. Device type validation before every API call.
    Three-tier confirmation: none (read-only), y/N (port bounce, reprovision),
    typed 'CLEAR' (clear/reset operations).
    """

    DEVICE_TYPE_COMPATIBILITY_MAP: dict[str, list[str]] = {
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

    def __init__(self, deps: UtilityCommandsDeps) -> None:
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
        self._selection = _UtilityCommandsSelection(self)  # WHY: selection cluster binding
        self._websocket = _UtilityCommandsWebsocket(self)  # WHY: websocket cluster binding
        self._show = _UtilityCommandsShow(self)  # WHY: show/diagnostic cluster binding

    def __getattr__(self, name: str) -> Any:
        """Proxy cluster-attribute access to helper clusters.

        Python only invokes ``__getattr__`` when normal lookup fails, so
        this method resolves cluster method calls (``self._validate_device_type``,
        ``self._select_site_and_device``, ``self._select_port_from_device``,
        etc.) without explicit delegator wrappers. The class-level
        ``hasattr`` check on ``type(cluster)`` avoids invoking the
        cluster's own ``__getattr__`` (which would proxy back to this
        class and cause infinite recursion for unknown attrs).
        """
        for attr in _CLUSTER_ATTRS:  # WHY: iterate cluster attribute names
            cluster = self.__dict__.get(attr)  # WHY: direct dict avoids recursion
            if cluster is not None and hasattr(type(cluster), name):  # WHY: class-level lookup only
                return getattr(cluster, name)  # WHY: bound method resolves through cluster
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _print_api_result(response: Any, success_msg: str, fail_msg: str) -> bool:
        """Check API response status and print message."""
        if hasattr(response, "status_code") and response.status_code >= 400:
            detail = ""
            if hasattr(response, "data") and isinstance(response.data, dict):
                detail = response.data.get("detail", "")
            error_text = f"! {fail_msg} (HTTP {response.status_code})"
            if detail:
                error_text += f": {detail}"
            print(error_text)
            return False
        print(f"-> {success_msg}")
        return True

    # ------------------------------------------------------------------
    # MANAGEMENT COMMANDS
    # ------------------------------------------------------------------

    def locate_device(self) -> None:
        """Menu 138: Locate device by blinking LED."""
        logging.info("Menu #138: Locate Device")
        selection = self._select_site_and_device("locate")
        if not selection:
            return
        site_id, device_id, _ = selection
        duration_str = self._safe_input_fn(
            "LED blink duration in minutes (1-120, default 5): ",
            default_value="5",
            context="locate_duration",
        )
        try:
            duration = max(1, min(120, int(duration_str)))
        except ValueError:
            duration = 5
        body: dict[str, Any] = {"duration": duration}
        try:
            response = mistapi.api.v1.sites.devices.startSiteLocateDevice(self._apisession, site_id, device_id, body)
            if self._print_api_result(
                response,
                f"Device LED blinking for {duration} minutes.",
                "Locate device failed",
            ):
                print("-> Use 'Unlocate Device' (menu 139) to stop.")
        except Exception as error:
            logging.exception("Locate device failed: %s", error)
            print(f"! Locate failed: {error}")

    def unlocate_device(self) -> None:
        """Menu 139: Stop device LED blinking."""
        logging.info("Menu #139: Unlocate Device")
        selection = self._select_site_and_device("unlocate")
        if not selection:
            return
        site_id, device_id, _ = selection
        try:
            response = mistapi.api.v1.sites.devices.stopSiteLocateDevice(self._apisession, site_id, device_id)
            self._print_api_result(
                response,
                "Device LED blinking stopped.",
                "Unlocate failed",
            )
        except Exception as error:
            logging.exception("Unlocate device failed: %s", error)
            print(f"! Unlocate failed: {error}")

    def bounce_port(self) -> None:
        """Menu 140: Bounce switch/gateway port (y/N confirmation)."""
        logging.info("Menu #140: Bounce Port")
        selection = self._select_site_and_device("bounce_port")
        if not selection:
            return
        site_id, device_id, _ = selection
        port_id = self._select_port_from_device(site_id, device_id)
        if not port_id:
            return
        blocked_prefixes = ("vme", "ae", "irb")
        if port_id.startswith(blocked_prefixes):
            print(f"! Port '{port_id}' cannot be bounced" " (management/aggregate/IRB port).")
            return
        confirm = self._safe_input_fn(
            f"Bounce port {port_id}?" " This will briefly disrupt traffic. (y/N): ",
            context="bounce_port",
        )
        if confirm.lower() != "y":
            print("! Operation cancelled.")
            return
        body: dict[str, Any] = {"ports": [port_id]}
        print(f"\n-> Bouncing port {port_id}...")
        result = self._run_websocket_command(
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.bounceDevicePort,
            body,
        )
        if result:
            print("-> Port bounce complete.")
        else:
            print("! Port bounce may have timed out." " Check device status.")

    def reprovision_device(self) -> None:
        """Menu 142: Reprovision switch/gateway (y/N confirmation)."""
        logging.info("Menu #142: Reprovision Device")
        selection = self._select_site_and_device("reprovision")
        if not selection:
            return
        site_id, device_id, _ = selection
        confirm = self._safe_input_fn(
            "Reprovision this device?" " This will push fresh config. (y/N): ",
            context="reprovision",
        )
        if confirm.lower() != "y":
            print("! Operation cancelled.")
            return
        try:
            response = mistapi.api.v1.sites.devices.reprovisionSiteOctermDevice(self._apisession, site_id, device_id)
            self._print_api_result(
                response,
                "Device reprovisioning initiated.",
                "Reprovision failed",
            )
        except Exception as error:
            logging.exception("Reprovision failed: %s", error)
            print(f"! Reprovision failed: {error}")

    def readopt_device(self) -> None:
        """Menu 143: Re-adopt switch device.

        Preflight the device's Virtual Chassis (VC) membership before
        calling the readopt API to avoid a 400 response.
        """
        logging.info("Menu #143: Re-adopt Device")
        selection = self._select_site_and_device("readopt", "switch")
        if not selection:
            return
        site_id, device_id, _ = selection
        try:
            vc_resp = mistapi.api.v1.sites.devices.getSiteDeviceVirtualChassis(self._apisession, site_id, device_id)
            vc_data = getattr(vc_resp, "data", None) or {}
            is_vc = vc_data.get("is_virtual_chassis", False)
            if not is_vc:
                print("! Device is not a Virtual Chassis member." " 'readopt' applies only to VC devices. Skipping.")
                return
        except Exception as error:
            logging.warning("VC preflight check failed: %s", error, exc_info=True)
        try:
            response = mistapi.api.v1.sites.devices.readoptSiteOctermDevice(self._apisession, site_id, device_id)
            self._print_api_result(
                response,
                "Device re-adoption initiated.",
                "Re-adopt failed",
            )
        except Exception as error:
            logging.exception("Re-adopt failed: %s", error)
            print(f"! Re-adopt failed: {error}")

    def get_ztp_password(self) -> None:
        """Menu 144: Get ZTP password for switch/gateway."""
        logging.info("Menu #144: Get ZTP Password")
        selection = self._select_site_and_device("ztp_password")
        if not selection:
            return
        site_id, device_id, _ = selection
        try:
            response = mistapi.api.v1.sites.devices.getSiteDeviceZtpPassword(self._apisession, site_id, device_id)
            if hasattr(response, "data"):
                data = response.data if isinstance(response.data, dict) else {}
                ztp_credential = data.get("password", str(response.data))
                # Intentional: user-requested display of ZTP credential
                # to console only. Not sent to logging framework.
                print(f"\n-> ZTP Password: {ztp_credential}")  # noqa: T201
                print("-> (Password displayed on console only" " - not logged or saved)")
            else:
                print("! No password data returned.")
        except Exception as error:
            error_msg = f"{type(error).__name__}: {str(error)}"
            logging.error("ZTP password request failed: %s", error_msg)
            print(f"! ZTP password request failed: {error_msg}")

    def get_config_commands(self) -> None:
        """Menu 145: Get configuration CLI commands for switch."""
        logging.info("Menu #145: Get Config CLI Commands")
        selection = self._select_site_and_device("config_cmd", "switch")
        if not selection:
            return
        site_id, device_id, _ = selection
        try:
            response = mistapi.api.v1.sites.devices.getSiteDeviceConfigCmd(self._apisession, site_id, device_id)
            if hasattr(response, "data"):
                data = response.data
                print("\n" + "=" * 60)
                print("CONFIGURATION CLI COMMANDS:")
                print("=" * 60)
                if isinstance(data, dict):
                    for key, value in data.items():
                        print(f"\n--- {key} ---")
                        print(str(value))
                else:
                    print(str(data))
            else:
                print("! No configuration commands returned.")
        except Exception as error:
            logging.exception("Config commands request failed: %s", error)
            print(f"! Config commands request failed: {error}")

    def upload_support_file(self) -> None:
        """Menu 146: Upload support file from switch/gateway."""
        logging.info("Menu #146: Upload Support File")
        selection = self._select_site_and_device("support_upload")
        if not selection:
            return
        site_id, device_id, _ = selection
        file_types = [
            "full",
            "process",
            "outbound-ssh",
            "messages",
            "core-dumps",
            "var-logs",
            "jma-logs",
        ]
        print("\nSupport file types:")
        for idx, ft in enumerate(file_types, 1):
            print(f"  {idx}. {ft}")
        type_input = self._safe_input_fn(
            "Select type (1-7, default: 1 = full): ",
            default_value="1",
            context="support_type",
        )
        try:
            type_idx = int(type_input) - 1
            info = file_types[type_idx] if 0 <= type_idx < len(file_types) else "full"
        except (ValueError, IndexError):
            info = "full"
        body: dict[str, Any] = {"info": info}
        node = self._safe_input_fn(
            "Node (node0/node1, Enter for both): ",
            context="support_node",
        )
        if node:
            body["node"] = node
        try:
            response = mistapi.api.v1.sites.devices.uploadSiteDeviceSupportFile(
                self._apisession, site_id, device_id, body
            )
            if self._print_api_result(
                response,
                f"Support file upload ({info}) initiated.",
                "Support file upload failed",
            ):
                print("-> Files will be available in the Mist dashboard.")
        except Exception as error:
            logging.exception("Support file upload failed: %s", error)
            print(f"! Support file upload failed: {error}")

    # ------------------------------------------------------------------
    # CLEAR/RESET COMMANDS
    # ------------------------------------------------------------------

    def clear_arp_cache(self) -> None:
        """Menu 147: Clear ARP cache (typed 'CLEAR' confirmation)."""
        logging.info("Menu #147: Clear ARP Cache")
        selection = self._select_site_and_device("clear_arp")
        if not selection:
            return
        site_id, device_id, _ = selection
        body: dict[str, Any] = {}
        node = self._safe_input_fn(
            "Node (node0/node1, Enter to skip): ",
            context="clear_arp_node",
        )
        if node:
            body["node"] = node
        port_id = self._select_port_optional(site_id, device_id)
        if port_id:
            body["port_id"] = port_id
        ip_addr = self._safe_input_fn(
            "IP address to clear (Enter for all): ",
            context="clear_arp_ip",
        )
        if ip_addr:
            body["ip"] = ip_addr
        if not self._confirm_destructive("Type 'CLEAR' to clear ARP cache: ", "CLEAR", "clear_arp"):
            return
        try:
            response = mistapi.api.v1.sites.devices.clearSiteSsrArpCache(self._apisession, site_id, device_id, body)
            self._print_api_result(
                response,
                "ARP cache cleared.",
                "Clear ARP cache failed",
            )
        except Exception as error:
            logging.exception("Clear ARP cache failed: %s", error)
            print(f"! Clear ARP cache failed: {error}")

    def clear_bgp_routes(self) -> None:
        """Menu 148: Clear BGP routes (typed 'CLEAR' confirmation)."""
        logging.info("Menu #148: Clear BGP Routes")
        selection = self._select_site_and_device("clear_bgp", "gateway")
        if not selection:
            return
        site_id, device_id, _ = selection
        body: dict[str, Any] = {}
        neighbor = self._safe_input_fn(
            "BGP neighbor IP (required): ",
            context="clear_bgp_neighbor",
            allow_empty=False,
        )
        if not neighbor:
            print("! Neighbor IP is required.")
            return
        body["neighbor"] = neighbor
        bgp_type = self._safe_input_fn(
            "Type (in/out, Enter for both): ",
            context="clear_bgp_type",
        )
        if bgp_type and bgp_type.lower() in ("in", "out"):
            body["type"] = bgp_type.lower()
        vrf = self._safe_input_fn("VRF (Enter to skip): ", context="clear_bgp_vrf")
        if vrf:
            body["vrf"] = vrf
        node = self._safe_input_fn(
            "Node (node0/node1, Enter to skip): ",
            context="clear_bgp_node",
        )
        if node:
            body["node"] = node
        if not self._confirm_destructive(
            "Type 'CLEAR' to clear BGP routes: ",
            "CLEAR",
            "clear_bgp",
        ):
            return
        try:
            response = mistapi.api.v1.sites.devices.clearSiteSsrBgpRoutes(self._apisession, site_id, device_id, body)
            self._print_api_result(
                response,
                "BGP routes cleared.",
                "Clear BGP routes failed",
            )
        except Exception as error:
            logging.exception("Clear BGP routes failed: %s", error)
            print(f"! Clear BGP routes failed: {error}")

    def clear_session(self) -> None:
        """Menu 149: Clear session on SSR/SRX gateway."""
        logging.info("Menu #149: Clear Session")
        selection = self._select_site_and_device("clear_session", "gateway")
        if not selection:
            return
        site_id, device_id, _ = selection
        body = self._build_clear_session_body()
        if body is None:
            return
        if not self._confirm_destructive(
            "Type 'CLEAR' to clear session(s): ",
            "CLEAR",
            "clear_session",
        ):
            return
        try:
            response = mistapi.api.v1.sites.devices.clearSiteDeviceSession(self._apisession, site_id, device_id, body)
            self._print_api_result(
                response,
                "Session(s) cleared.",
                "Clear session failed",
            )
        except Exception as error:
            logging.exception("Clear session failed: %s", error)
            self._handle_clear_session_error(error)

    def _build_clear_session_body(self) -> dict[str, Any] | None:
        """Gather clear-session parameters from user input.

        Returns None if the user cancels.
        """
        body: dict[str, Any] = {}
        service_name = self._safe_input_fn(
            "Service name to clear (Enter to skip): ",
            context="clear_session_service_name",
        )
        session_ids_input = self._safe_input_fn(
            "Session IDs to clear (comma-separated, Enter to skip): ",
            context="clear_session_ids",
        )
        if service_name:
            body["service_name"] = service_name
        elif session_ids_input:
            session_ids = [s.strip() for s in session_ids_input.split(",") if s.strip()]
            if session_ids:
                body["session_ids"] = session_ids
        else:
            if not self._confirm_clear_all_sessions():
                return None
        node = self._safe_input_fn(
            "Node (node0/node1, Enter to skip): ",
            context="clear_session_node",
        )
        if node:
            body["node"] = node
        return body

    def _confirm_clear_all_sessions(self) -> bool:
        """Confirm clearing all sessions when no filter provided."""
        confirm_all = self._safe_input_fn(
            "No service name or session IDs provided."
            " This may attempt to clear ALL sessions."
            " Type 'CLEAR ALL' to proceed"
            " or press Enter to cancel: ",
            context="clear_session_confirm_all",
        )
        if confirm_all != "CLEAR ALL":
            print("Cancelled: No service name or session IDs provided.")
            return False
        return True

    @staticmethod
    def _handle_clear_session_error(error: Exception) -> None:
        """Handle clear session API errors with guidance."""
        try:
            code = getattr(error, "status_code", None) or getattr(
                getattr(error, "response", None),
                "status_code",
                None,
            )
            if code == 400:
                print(
                    "! API returned 400. The API expects either"
                    " 'service_name' or 'session_ids' in the"
                    " request body."
                )
                print("  Provide a service name or a comma-separated" " list of session IDs, and retry.")
            else:
                print(f"! Clear session failed: {error}")
        except Exception:  # pylint: disable=broad-exception-caught
            print(f"! Clear session failed: {error}")

    def clear_mac_table(self) -> None:
        """Menu 150: Clear MAC table (typed 'CLEAR' confirmation)."""
        logging.info("Menu #150: Clear MAC Table")
        selection = self._select_site_and_device("clear_mac_table")
        if not selection:
            return
        site_id, device_id, _ = selection
        body: dict[str, Any] = {}
        node = self._safe_input_fn(
            "Node (node0/node1, Enter to skip): ",
            context="clear_mac_node",
        )
        if node:
            body["node"] = node
        if not self._confirm_destructive(
            "Type 'CLEAR' to clear MAC table: ",
            "CLEAR",
            "clear_mac_table",
        ):
            return
        try:
            response = mistapi.api.v1.sites.devices.clearSiteDeviceMacTable(self._apisession, site_id, device_id, body)
            self._print_api_result(
                response,
                "MAC table cleared.",
                "Clear MAC table failed",
            )
        except Exception as error:
            logging.exception("Clear MAC table failed: %s", error)
            print(f"! Clear MAC table failed: {error}")

    def clear_bpdu_error(self) -> None:
        """Menu 151: Clear BPDU errors on switch."""
        logging.info("Menu #151: Clear BPDU Errors")
        selection = self._select_site_and_device("clear_bpdu_error", "switch")
        if not selection:
            return
        site_id, device_id, _ = selection
        port_id = self._select_port_optional(site_id, device_id)
        port_target = port_id if port_id else "all"
        if not self._confirm_destructive(
            f"Type 'CLEAR' to clear BPDU errors on port {port_target}: ",
            "CLEAR",
            "clear_bpdu_error",
        ):
            return
        body: dict[str, Any] = {"port": port_target}
        try:
            response = mistapi.api.v1.sites.devices.clearBpduErrorsFromPortsOnSwitch(
                self._apisession, site_id, device_id, body
            )
            self._print_api_result(
                response,
                "BPDU errors cleared.",
                "Clear BPDU errors failed",
            )
        except Exception as error:
            logging.exception("Clear BPDU errors failed: %s", error)
            print(f"! Clear BPDU errors failed: {error}")

    def clear_learned_macs(self) -> None:
        """Menu 152: Clear learned MACs from switch port."""
        logging.info("Menu #152: Clear Learned MACs")
        selection = self._select_site_and_device("clear_macs", "switch")
        if not selection:
            return
        site_id, device_id, _ = selection
        port_id = self._select_port_from_device(site_id, device_id)
        if not port_id:
            print("! Port selection is required for clearing" " learned MACs.")
            return
        port_with_unit = port_id if "." in port_id else f"{port_id}.0"
        if not self._confirm_destructive(
            f"Type 'CLEAR' to clear learned MACs" f" on port {port_with_unit}: ",
            "CLEAR",
            "clear_macs",
        ):
            return
        body: dict[str, Any] = {"ports": [port_with_unit]}
        try:
            response = mistapi.api.v1.sites.devices.clearAllLearnedMacsFromPortOnSwitch(
                self._apisession, site_id, device_id, body
            )
            self._print_api_result(
                response,
                f"Learned MACs cleared from port {port_with_unit}.",
                "Clear learned MACs failed",
            )
        except Exception as error:
            logging.exception("Clear learned MACs failed: %s", error)
            print(f"! Clear learned MACs failed: {error}")

    def clear_policy_hit_count(self) -> None:
        """Menu 153: Clear policy hit count on SSR."""
        # TODO: Returns 400 on DC-West SSR120. Investigate API
        # requirements - may need node param or be unsupported.
        logging.info("Menu #153: Clear Policy Hit Count")
        selection = self._select_site_and_device("clear_policy_hit_count", "gateway")
        if not selection:
            return
        site_id, device_id, _ = selection
        body: dict[str, Any] = {}
        node = self._safe_input_fn(
            "Node (node0/node1, Enter to skip): ",
            context="clear_policy_node",
        )
        if node:
            body["node"] = node
        if not self._confirm_destructive(
            "Type 'CLEAR' to clear policy hit count: ",
            "CLEAR",
            "clear_policy_hit_count",
        ):
            return
        try:
            response = mistapi.api.v1.sites.devices.clearSiteDevicePolicyHitCount(
                self._apisession, site_id, device_id, body
            )
            self._print_api_result(
                response,
                "Policy hit count cleared.",
                "Clear policy hit count failed",
            )
        except Exception as error:
            logging.exception("Clear policy hit count failed: %s", error)
            print(f"! Clear policy hit count failed: {error}")

    def release_dhcp_lease(self) -> None:
        """Menu 154: Release DHCP lease on switch/gateway."""
        logging.info("Menu #154: Release DHCP Lease")
        selection = self._select_site_and_device("release_dhcp")
        if not selection:
            return
        site_id, device_id, _ = selection
        port_id = self._select_port_from_device(site_id, device_id)
        if not port_id:
            print("! Port selection is required.")
            return
        body: dict[str, Any] = {"port_id": port_id}
        node = self._safe_input_fn(
            "Node (node0/node1, Enter to skip): ",
            context="release_dhcp_node",
        )
        if node:
            body["node"] = node
        confirm = self._safe_input_fn(
            f"Release DHCP lease on port {port_id}? (y/N): ",
            context="release_dhcp",
        )
        if confirm.lower() != "y":
            print("! Operation cancelled.")
            return
        try:
            response = mistapi.api.v1.sites.devices.releaseSiteDeviceDhcpLease(
                self._apisession, site_id, device_id, body
            )
            self._print_api_result(
                response,
                f"DHCP lease released on port {port_id}.",
                "Release DHCP lease failed",
            )
        except Exception as error:
            logging.exception("Release DHCP lease failed: %s", error)
            print(f"! Release DHCP lease failed: {error}")

    def release_dhcp_ssr(self) -> None:
        """Menu 155: Release DHCP lease on SSR/SRX."""
        logging.info("Menu #155: Release DHCP Lease (SSR)")
        selection = self._select_site_and_device("release_dhcp_ssr", "gateway")
        if not selection:
            return
        site_id, device_id, _ = selection
        port_id = self._select_interface_from_device(site_id, device_id)
        if not port_id:
            print("! Network interface is required.")
            return
        body: dict[str, Any] = {"port_id": port_id}
        node = self._safe_input_fn(
            "Node (node0/node1, Enter to skip): ",
            context="release_dhcp_ssr_node",
        )
        if node:
            body["node"] = node
        confirm = self._safe_input_fn(
            f"Release DHCP lease on interface {port_id}? (y/N): ",
            context="release_dhcp_ssr",
        )
        if confirm.lower() != "y":
            print("! Operation cancelled.")
            return
        try:
            response = mistapi.api.v1.sites.devices.releaseSiteSsrDhcpLease(self._apisession, site_id, device_id, body)
            self._print_api_result(
                response,
                f"SSR DHCP lease released on interface {port_id}.",
                "Release SSR DHCP lease failed",
            )
        except Exception as error:
            logging.exception("Release SSR DHCP lease failed: %s", error)
            print(f"! Release SSR DHCP lease failed: {error}")

    # ------------------------------------------------------------------
    # HARDWARE COMMANDS
    # ------------------------------------------------------------------

    def poll_switch_stats(self) -> None:
        """Menu 156: Poll fresh statistics from switch."""
        logging.info("Menu #156: Poll Switch Stats")
        selection = self._select_site_and_device("poll_stats", "switch")
        if not selection:
            return
        site_id, device_id, _ = selection
        try:
            response = mistapi.api.v1.sites.devices.pollSiteSwitchStats(self._apisession, site_id, device_id)
            if self._print_api_result(
                response,
                "Fresh statistics polled from switch.",
                "Poll switch stats failed",
            ):
                print("-> Updated stats will appear in next" " stats export.")
        except Exception as error:
            logging.exception("Poll switch stats failed: %s", error)
            print(f"! Poll switch stats failed: {error}")

    def create_device_snapshot(self) -> None:
        """Menu 157: Create device snapshot on switch."""
        logging.info("Menu #157: Create Device Snapshot")
        selection = self._select_site_and_device("snapshot", "switch")
        if not selection:
            return
        site_id, device_id, _ = selection
        try:
            response = mistapi.api.v1.sites.devices.createSiteDeviceSnapshot(self._apisession, site_id, device_id)
            self._print_api_result(
                response,
                "Device snapshot created successfully.",
                "Create snapshot failed",
            )
        except Exception as error:
            logging.exception("Create snapshot failed: %s", error)
            print(f"! Create snapshot failed: {error}")
