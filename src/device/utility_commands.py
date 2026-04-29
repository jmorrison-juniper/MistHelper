"""Device utility commands for Mist network devices.

Extracted from MistHelper.py (Issue #210). Provides 35 device utility
operations spanning diagnostics, show commands, management, clear/reset,
and hardware operations. Menu range: 123-157.

Dependencies are injected via constructor for testability.
"""

# pylint: disable=too-many-lines,logging-fstring-interpolation,implicit-str-concat

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import mistapi

# ---------------------------------------------------------------------------
# Type aliases for dependency injection
# ---------------------------------------------------------------------------
SelectSiteFn = Callable[[], str | None]
SelectDeviceFn = Callable[[str, str], str | None]
SafeInputFn = Callable[..., str]
WriteExportFn = Callable[[list[dict[str, Any]], str, str], None]
WebSocketManagerFactory = Callable[[Any], Any]


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

    def __init__(  # noqa: PLR0913
        self,
        *,
        apisession: Any,
        select_site_fn: SelectSiteFn,
        select_device_fn: SelectDeviceFn,
        safe_input_fn: SafeInputFn,
        write_export_fn: WriteExportFn,
        websocket_manager_factory: WebSocketManagerFactory,
    ) -> None:
        """Initialize with injected dependencies.

        Args:
            apisession: Authenticated Mist API session.
            select_site_fn: Returns selected site_id or None.
            select_device_fn: Returns selected device_id given site_id
                and device_type filter.
            safe_input_fn: Safe input with EOF handling.
            write_export_fn: Writes export data (list, filename, api_name).
            websocket_manager_factory: Creates WebSocketManager from session.
        """
        self._apisession = apisession
        self._select_site_fn = select_site_fn
        self._select_device_fn = select_device_fn
        self._safe_input_fn = safe_input_fn
        self._write_export_fn = write_export_fn
        self._ws_factory = websocket_manager_factory

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_device_type(self, device_type: str, command_name: str) -> bool:
        """Check device type against compatibility map."""
        allowed = self.DEVICE_TYPE_COMPATIBILITY_MAP.get(command_name, [])
        if device_type not in allowed:
            allowed_str = ", ".join(allowed)
            print(f"! This command is only available on: {allowed_str}")
            print(f"! The selected device is a {device_type}.")
            return False
        return True

    def _select_site_and_device(
        self, command_name: str, device_type_filter: str = "all"
    ) -> tuple[str, str, str] | None:
        """Select site and device, validate type, warn if offline."""
        site_id = self._select_site_fn()
        if not site_id:
            print("! No site selected. Operation cancelled.")
            return None
        device_id = self._select_device_fn(site_id, device_type_filter)
        if not device_id:
            print("! No device selected. Operation cancelled.")
            return None
        device_info = self._get_device_info(site_id, device_id)
        if not device_info:
            print("! Could not retrieve device info from stats API.")
            return None
        device_type = device_info.get("type")
        if not device_type:
            print("! Could not determine device type.")
            return None
        if not self._validate_device_type(device_type, command_name):
            return None
        status = device_info.get("status", "unknown")
        if status != "connected":
            print(f"[WARNING] Device status is '{status}'" " - command may not succeed.")
        return (site_id, device_id, device_type)

    def _get_device_info(self, site_id: str, device_id: str) -> dict[str, Any] | None:
        """Fetch device type and status from stats API."""
        try:
            response = mistapi.api.v1.sites.stats.getSiteDeviceStats(self._apisession, site_id, device_id)
            if hasattr(response, "data") and isinstance(response.data, dict):
                return response.data  # type: ignore[no-any-return]
        except Exception as error:
            logging.error(f"Failed to get device stats: {error}")
        return None

    def _select_port_from_device(self, site_id: str, device_id: str) -> str | None:
        """Fetch ports from device stats, display list, return selected."""
        try:
            response = mistapi.api.v1.sites.stats.getSiteDeviceStats(self._apisession, site_id, device_id)
            if not hasattr(response, "data") or not isinstance(response.data, dict):
                return self._manual_port_entry()
            ports = response.data.get("ports", [])
            if ports:
                return self._display_and_select_port(ports)
            if_stat = response.data.get("if_stat", {})
            if isinstance(if_stat, dict) and if_stat:
                return self._display_and_select_ifstat(if_stat)
            return self._manual_port_entry()
        except Exception as error:
            logging.debug(f"Could not fetch port list: {error}")
            return self._manual_port_entry()

    def _display_and_select_port(self, ports: list[dict[str, Any]]) -> str | None:
        """Display numbered port list and get selection."""
        print("\nAvailable ports:")
        for index, port in enumerate(ports, 1):
            port_name = port.get("port_id", port.get("name", f"port_{index}"))
            port_status = port.get("up", "unknown")
            status_str = "UP" if port_status else "DOWN"
            speed = port.get("speed", "")
            print(f"  {index}. {port_name} [{status_str}] {speed}")
        selection = self._safe_input_fn(
            "\nSelect port by number or type port name: ",
            context="port_selection",
        )
        if not selection:
            print("! No port selected.")
            return None
        if selection.isdigit():
            idx = int(selection) - 1
            if 0 <= idx < len(ports):
                result: str = str(ports[idx].get("port_id", ports[idx].get("name", "")))
                return result
            print("! Invalid port number.")
            return None
        return selection

    def _display_and_select_ifstat(self, if_stat: dict[str, Any]) -> str | None:
        """Display interfaces from if_stat dict."""
        physical = [name for name in if_stat if name.startswith(("ge-", "xe-", "et-", "mge-"))]
        if not physical:
            physical = list(if_stat.keys())
        physical.sort()
        print("\nAvailable ports/interfaces:")
        for idx, name in enumerate(physical, 1):
            info = if_stat.get(name, {})
            up = "UP" if info.get("up") else "DOWN"
            print(f"  {idx}. {name} [{up}]")
        selection = self._safe_input_fn(
            "\nSelect by number or type port name: ",
            context="ifstat_selection",
        )
        if not selection:
            print("! No port selected.")
            return None
        if selection.isdigit():
            sel_idx = int(selection) - 1
            if 0 <= sel_idx < len(physical):
                base = physical[sel_idx]
                return base.split(".")[0] if "." in base else base
            print("! Invalid port number.")
            return None
        return selection

    def _manual_port_entry(self) -> str | None:
        """Prompt for manual port name entry."""
        port = self._safe_input_fn(
            "Enter port name (e.g., ge-0/0/0): ",
            context="manual_port_entry",
        )
        return port if port else None

    def _select_port_optional(self, site_id: str, device_id: str) -> str:
        """Show port list and let user pick or skip."""
        port_names = self._discover_ports(site_id, device_id)
        selection = self._safe_input_fn(
            "Port (number, name, or Enter to skip): ",
            context="port_optional",
        )
        if not selection:
            return ""
        return self._resolve_port_selection(selection, port_names)

    def _discover_ports(self, site_id: str, device_id: str) -> list[str]:
        """Fetch and display available ports from device stats."""
        try:
            response = mistapi.api.v1.sites.stats.getSiteDeviceStats(self._apisession, site_id, device_id)
            if not hasattr(response, "data") or not isinstance(response.data, dict):
                return []
            ports = response.data.get("ports", [])
            if ports:
                return self._display_ports_from_list(ports)
            return self._display_ports_from_if_stat(response.data.get("if_stat", {}))
        except Exception:  # nosec B110
            return []

    @staticmethod
    def _display_ports_from_list(ports: list[dict[str, Any]]) -> list[str]:
        """Display ports from the ports array in stats response."""
        port_names: list[str] = []
        print("\nAvailable ports:")
        for idx, port in enumerate(ports, 1):
            name = port.get("port_id", port.get("name", f"port_{idx}"))
            up = "UP" if port.get("up") else "DOWN"
            print(f"  {idx}. {name} [{up}]")
            port_names.append(name)
        return port_names

    @staticmethod
    def _display_ports_from_if_stat(if_stat: Any) -> list[str]:
        """Display physical ports from if_stat dict as fallback."""
        if not isinstance(if_stat, dict) or not if_stat:
            return []
        physical = sorted(n for n in if_stat if n.startswith(("ge-", "xe-", "et-", "mge-")))
        if not physical:
            return []
        port_names: list[str] = []
        print("\nAvailable ports:")
        for idx, name in enumerate(physical, 1):
            info = if_stat.get(name, {})
            up = "UP" if info.get("up") else "DOWN"
            print(f"  {idx}. {name} [{up}]")
            port_names.append(name)
        return port_names

    @staticmethod
    def _resolve_port_selection(selection: str, port_names: list[str]) -> str:
        """Resolve user selection to a port name."""
        if selection.isdigit() and port_names:
            idx = int(selection) - 1
            if 0 <= idx < len(port_names):
                base = port_names[idx]
                return base.split(".")[0] if "." in base else base
        return selection

    def _select_interface_from_device(self, site_id: str, device_id: str) -> str | None:
        """Fetch network interfaces from device stats."""
        try:
            response = mistapi.api.v1.sites.stats.getSiteDeviceStats(self._apisession, site_id, device_id)
            if not hasattr(response, "data") or not isinstance(response.data, dict):
                return self._manual_interface_entry()
            if_stat = response.data.get("if_stat", {})
            ip_stat = response.data.get("ip_stat", {})
            ports = response.data.get("ports", [])
            interfaces = self._extract_interfaces(if_stat, ip_stat, ports)
            if not interfaces:
                return self._manual_interface_entry()
            self._print_interface_list(interfaces, if_stat, ip_stat)
            return self._get_interface_selection(interfaces)
        except Exception as error:
            logging.debug(f"Could not fetch interface list: {error}")
            return self._manual_interface_entry()

    @staticmethod
    def _extract_interfaces(
        if_stat: Any,
        ip_stat: Any,
        ports: list[dict[str, Any]],
    ) -> list[str]:
        """Extract interface names from stats, trying multiple sources."""
        if isinstance(if_stat, dict) and if_stat:
            return list(if_stat.keys())
        ip_interfaces = DeviceUtilityCommands._interfaces_from_ip_stat(ip_stat)
        if ip_interfaces:
            return ip_interfaces
        return [p.get("port_id", p.get("name", "")) for p in ports if p.get("port_id") or p.get("name")]

    @staticmethod
    def _interfaces_from_ip_stat(ip_stat: Any) -> list[str]:
        """Extract interface names from ip_stat dict."""
        if not isinstance(ip_stat, dict) or not ip_stat:
            return []
        iface_prefixes = ("ge-", "xe-", "et-", "mge-", "lte-", "irb", "lo")
        return [k for k in ip_stat if k.startswith(iface_prefixes)]

    def _print_interface_list(
        self,
        interfaces: list[str],
        if_stat: dict[str, Any] | Any,
        ip_stat: dict[str, Any] | Any,
    ) -> None:
        """Print numbered list of available interfaces."""
        print("\nAvailable interfaces:")
        for idx, iface in enumerate(interfaces, 1):
            extra = ""
            if isinstance(if_stat, dict) and iface in if_stat:
                entry = if_stat[iface]
                ips = entry.get("ips", [])
                if ips:
                    extra = f" ({', '.join(ips)})"
            elif isinstance(ip_stat, dict) and iface in ip_stat:
                ip_info = ip_stat[iface]
                ip_addr = ip_info.get("ip", "")
                if ip_addr:
                    extra = f" ({ip_addr})"
            print(f"  {idx}. {iface}{extra}")

    def _get_interface_selection(self, interfaces: list[str]) -> str | None:
        """Prompt user to select from interface list."""
        selection = self._safe_input_fn(
            "\nSelect interface by number or type name: ",
            context="interface_selection",
        )
        if not selection:
            print("! No interface selected.")
            return None
        if selection.isdigit():
            sel_idx = int(selection) - 1
            if 0 <= sel_idx < len(interfaces):
                return interfaces[sel_idx]
            print("! Invalid interface number.")
            return None
        return selection

    def _manual_interface_entry(self) -> str | None:
        """Prompt for manual interface name entry."""
        iface = self._safe_input_fn(
            "Enter interface name (e.g., ge-0/0/0, wan0): ",
            context="manual_interface_entry",
            allow_empty=False,
        )
        return iface if iface else None

    def _select_network_from_device(self, site_id: str, device_id: str) -> str:
        """Fetch DHCP/network config from device."""
        network_names, network_labels = self._discover_networks(site_id, device_id)
        if network_names:
            self._display_network_list(network_names, network_labels)
            if len(network_names) == 1:
                print(f"\n-> Auto-selecting: {network_names[0]}")
                return network_names[0]
        selection = self._safe_input_fn(
            "Select network (number or name, required): ",
            context="dhcp_network",
            allow_empty=False,
        )
        if not selection:
            return ""
        return self._resolve_network_selection(selection, network_names)

    def _discover_networks(self, site_id: str, device_id: str) -> tuple[list[str], list[str]]:
        """Fetch network names and labels from device config."""
        network_names: list[str] = []
        network_labels: list[str] = []
        try:
            response = mistapi.api.v1.sites.devices.getSiteDevice(self._apisession, site_id, device_id)
            if hasattr(response, "data") and isinstance(response.data, dict):
                self._collect_dhcp_networks(
                    response.data.get("dhcpd_config", {}),
                    network_names,
                    network_labels,
                )
                self._collect_ip_networks(
                    response.data.get("ip_config", {}),
                    network_names,
                    network_labels,
                )
        except Exception as error:
            logging.debug(f"Could not fetch network config: {error}")
        return network_names, network_labels

    @staticmethod
    def _collect_dhcp_networks(
        dhcpd_config: Any,
        names: list[str],
        labels: list[str],
    ) -> None:
        """Add DHCP server networks to the lists."""
        if not isinstance(dhcpd_config, dict):
            return
        for net_name in dhcpd_config:
            names.append(net_name)
            labels.append(f"{net_name} (dhcp server)")

    @staticmethod
    def _collect_ip_networks(
        ip_config: Any,
        names: list[str],
        labels: list[str],
    ) -> None:
        """Add IP config networks (not already in DHCP) to the lists."""
        if not isinstance(ip_config, dict):
            return
        for net_name, net_cfg in ip_config.items():
            if net_name not in names:
                names.append(net_name)
                ip_addr = net_cfg.get("ip", "") if isinstance(net_cfg, dict) else ""
                label = f"{net_name} ({ip_addr})" if ip_addr else net_name
                labels.append(label)

    @staticmethod
    def _display_network_list(network_names: list[str], network_labels: list[str]) -> None:
        """Print numbered list of available networks."""
        print("\nAvailable networks:")
        for idx, label in enumerate(network_labels, 1):
            print(f"  {idx}. {label}")

    @staticmethod
    def _resolve_network_selection(selection: str, network_names: list[str]) -> str:
        """Resolve user selection to a network name."""
        if selection.isdigit() and network_names:
            sel_idx = int(selection) - 1
            if 0 <= sel_idx < len(network_names):
                return network_names[sel_idx]
        return selection

    def _run_websocket_command(
        self,
        site_id: str,
        device_id: str,
        sdk_method: Any,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Execute WebSocket command: POST -> subscribe -> await."""
        websocket_manager = self._ws_factory(self._apisession)
        if not websocket_manager.connect():
            print("! Failed to establish WebSocket connection.")
            return None
        channel = f"/sites/{site_id}/devices/{device_id}/cmd"
        if not websocket_manager.subscribe_to_channel(channel):
            print("! Failed to subscribe to device command channel.")
            websocket_manager.disconnect()
            return None
        time.sleep(1)
        try:
            return self._execute_ws_command(
                site_id,
                device_id,
                sdk_method,
                body,
                websocket_manager,
            )
        except Exception as error:
            logging.error(f"WebSocket command failed: {error}", exc_info=True)
            print(f"! Command failed: {error}")
            return None
        finally:
            websocket_manager.disconnect()

    def _execute_ws_command(
        self,
        site_id: str,
        device_id: str,
        sdk_method: Any,
        body: dict[str, Any] | None,
        websocket_manager: Any,
    ) -> dict[str, Any] | None:
        """Run SDK method and wait for WebSocket result."""
        if body is not None:
            response = sdk_method(self._apisession, site_id, device_id, body)
        else:
            response = sdk_method(self._apisession, site_id, device_id)
        if not hasattr(response, "data"):
            print("! No response data from API.")
            return None
        response_data = response.data if isinstance(response.data, dict) else {}
        session_id = response_data.get("session")
        if not session_id:
            print("! No session ID returned from command.")
            return None
        print(f"-> Command issued (session: {session_id[:8]}...)")
        print("-> Waiting for results...")
        result: dict[str, Any] | None = websocket_manager.wait_for_command_result(session_id, timeout_seconds=120)
        return result

    def _run_streaming_command(  # noqa: PLR0913
        self,
        site_id: str,
        device_id: str,
        sdk_method: Any,
        body: dict[str, Any] | None = None,
        timeout_seconds: int = 120,
    ) -> None:
        """Execute streaming WebSocket command with output display."""
        websocket_manager = self._ws_factory(self._apisession)
        if not websocket_manager.connect():
            print("! Failed to establish WebSocket connection.")
            return
        channel = f"/sites/{site_id}/devices/{device_id}/cmd"
        if not websocket_manager.subscribe_to_channel(channel):
            print("! Failed to subscribe to device command channel.")
            websocket_manager.disconnect()
            return
        time.sleep(1)
        try:
            self._stream_ws_output(
                site_id,
                device_id,
                sdk_method,
                body,
                websocket_manager,
                timeout_seconds,
            )
        except KeyboardInterrupt:
            print("\n-> Streaming stopped by user.")
        except Exception as error:
            logging.error(f"Streaming command failed: {error}", exc_info=True)
            print(f"! Streaming failed: {error}")
        finally:
            websocket_manager.disconnect()

    def _stream_ws_output(  # noqa: PLR0913
        self,
        site_id: str,
        device_id: str,
        sdk_method: Any,
        body: dict[str, Any] | None,
        websocket_manager: Any,
        timeout_seconds: int,
    ) -> None:
        """Stream WebSocket output to console."""
        if body is not None:
            response = sdk_method(self._apisession, site_id, device_id, body)
        else:
            response = sdk_method(self._apisession, site_id, device_id)
        if not hasattr(response, "data"):
            print("! No response data from API.")
            return
        response_data = response.data if isinstance(response.data, dict) else {}
        session_id = response_data.get("session")
        if not session_id:
            print("! No session ID returned.")
            return
        print(f"-> Streaming started (session: {session_id[:8]}...)")
        print("-> Press Ctrl+C to stop.\n")
        result = websocket_manager.wait_for_command_result(
            session_id,
            timeout_seconds=timeout_seconds,
            activity_timeout_seconds=30,
        )
        if result:
            raw = result.get("raw", "")
            if raw:
                print(raw)

    def _display_and_export_result(  # noqa: PLR0913
        self,
        result: dict[str, Any] | None,
        command_name: str,
        site_id: str,
        device_id: str,
        api_function_name: str,
        filename: str,
    ) -> None:
        """Display WebSocket result and write to dual output."""
        if not result:
            print("! No results received (timeout or error).")
            return
        print("\n" + "=" * 60)
        print(f"{command_name.upper()} RESULTS:")
        print("=" * 60)
        raw_output = result.get("raw", "")
        if raw_output:
            print(raw_output)
        other_output = result.get("Output", "")
        if other_output and other_output != raw_output:
            print(other_output)
        export_data = {
            "device_id": device_id,
            "site_id": site_id,
            "command": command_name,
            "timestamp": datetime.now(UTC).isoformat(),
            "raw_output": raw_output or other_output or str(result),
        }
        self._write_export_fn([export_data], filename, api_function_name)

    def _confirm_destructive(self, prompt: str, keyword: str, context: str) -> bool:
        """Require typed keyword confirmation for destructive ops."""
        confirmation = self._safe_input_fn(prompt, context=context)
        if confirmation != keyword:
            print("! Operation cancelled - confirmation not matched.")
            return False
        return True

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
    # DIAGNOSTIC COMMANDS
    # ------------------------------------------------------------------

    def traceroute(self) -> None:
        """Menu 123: Run traceroute from device to destination host."""
        logging.info("Menu #123: Traceroute from device")
        selection = self._select_site_and_device("traceroute")
        if not selection:
            return
        site_id, device_id, _ = selection
        host = self._safe_input_fn(
            "Enter destination host or IP (required): ",
            context="traceroute_host",
            allow_empty=False,
        )
        if not host:
            print("! Destination host is required.")
            return
        protocol = self._safe_input_fn(
            "Protocol (udp/icmp, default: udp): ",
            default_value="udp",
            context="traceroute_protocol",
        )
        body: dict[str, Any] = {"host": host}
        if protocol and protocol.lower() in ("udp", "icmp"):
            body["protocol"] = protocol.lower()
        print(f"\n-> Running traceroute to {host}...")
        result = self._run_websocket_command(
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.tracerouteFromDevice,
            body,
        )
        self._display_and_export_result(
            result,
            "Traceroute",
            site_id,
            device_id,
            "tracerouteFromDevice",
            "DeviceTraceroute.csv",
        )

    def show_ospf_neighbors(self) -> None:
        """Menu 124: Show OSPF neighbors on SSR/SRX gateway."""
        logging.info("Menu #124: Show OSPF Neighbors")
        selection = self._select_site_and_device("show_ospf_neighbors", "gateway")
        if not selection:
            return
        site_id, device_id, _ = selection
        body: dict[str, Any] = {}
        vrf = self._safe_input_fn("VRF (Enter to skip): ", context="ospf_vrf")
        if vrf:
            body["vrf"] = vrf
        node = self._safe_input_fn("Node (node0/node1, Enter to skip): ", context="ospf_node")
        if node:
            body["node"] = node
        neighbor = self._safe_input_fn("Neighbor IP (Enter to skip): ", context="ospf_neighbor")
        if neighbor:
            body["neighbor"] = neighbor
        print("\n-> Fetching OSPF neighbors...")
        result = self._run_websocket_command(
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.showSiteGatewayOspfNeighbors,
            body,
        )
        self._display_and_export_result(
            result,
            "OSPF Neighbors",
            site_id,
            device_id,
            "showSiteGatewayOspfNeighbors",
            "DeviceOspfNeighbors.csv",
        )

    def show_ospf_interfaces(self) -> None:
        """Menu 125: Show OSPF interfaces on SSR/SRX gateway."""
        logging.info("Menu #125: Show OSPF Interfaces")
        selection = self._select_site_and_device("show_ospf_interfaces", "gateway")
        if not selection:
            return
        site_id, device_id, _ = selection
        body: dict[str, Any] = {}
        vrf = self._safe_input_fn("VRF (Enter to skip): ", context="ospf_vrf")
        if vrf:
            body["vrf"] = vrf
        node = self._safe_input_fn("Node (node0/node1, Enter to skip): ", context="ospf_node")
        if node:
            body["node"] = node
        port_id = self._select_port_optional(site_id, device_id)
        if port_id:
            body["port_id"] = port_id
        print("\n-> Fetching OSPF interfaces...")
        result = self._run_websocket_command(
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.showSiteGatewayOspfInterfaces,
            body,
        )
        self._display_and_export_result(
            result,
            "OSPF Interfaces",
            site_id,
            device_id,
            "showSiteGatewayOspfInterfaces",
            "DeviceOspfInterfaces.csv",
        )

    def show_ospf_database(self) -> None:
        """Menu 126: Show OSPF database on SSR/SRX gateway."""
        logging.info("Menu #126: Show OSPF Database")
        selection = self._select_site_and_device("show_ospf_database", "gateway")
        if not selection:
            return
        site_id, device_id, _ = selection
        body: dict[str, Any] = {}
        vrf = self._safe_input_fn("VRF (Enter to skip): ", context="ospf_vrf")
        if vrf:
            body["vrf"] = vrf
        node = self._safe_input_fn("Node (node0/node1, Enter to skip): ", context="ospf_node")
        if node:
            body["node"] = node
        self_orig = self._safe_input_fn(
            "Show self-originated only? (y/N): ",
            context="ospf_self_originate",
        )
        if self_orig and self_orig.lower() == "y":
            body["self_originate"] = True
        print("\n-> Fetching OSPF database...")
        result = self._run_websocket_command(
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.showSiteGatewayOspfDatabase,
            body,
        )
        self._display_and_export_result(
            result,
            "OSPF Database",
            site_id,
            device_id,
            "showSiteGatewayOspfDatabase",
            "DeviceOspfDatabase.csv",
        )

    def show_ospf_summary(self) -> None:
        """Menu 127: Show OSPF summary on SSR/SRX gateway."""
        logging.info("Menu #127: Show OSPF Summary")
        selection = self._select_site_and_device("show_ospf_summary", "gateway")
        if not selection:
            return
        site_id, device_id, _ = selection
        body: dict[str, Any] = {}
        vrf = self._safe_input_fn("VRF (Enter to skip): ", context="ospf_vrf")
        if vrf:
            body["vrf"] = vrf
        node = self._safe_input_fn("Node (node0/node1, Enter to skip): ", context="ospf_node")
        if node:
            body["node"] = node
        print("\n-> Fetching OSPF summary...")
        result = self._run_websocket_command(
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.showSiteGatewayOspfSummary,
            body,
        )
        self._display_and_export_result(
            result,
            "OSPF Summary",
            site_id,
            device_id,
            "showSiteGatewayOspfSummary",
            "DeviceOspfSummary.csv",
        )

    def resolve_dns(self) -> None:
        """Menu 135: Test DNS resolution on SSR gateway."""
        logging.info("Menu #135: Resolve DNS")
        selection = self._select_site_and_device("resolve_dns", "gateway")
        if not selection:
            return
        site_id, device_id, _ = selection
        print("\n-> Testing DNS resolution on device...")
        result = self._run_websocket_command(
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.testSiteSsrDnsResolution,
        )
        self._display_and_export_result(
            result,
            "DNS Resolution",
            site_id,
            device_id,
            "testSiteSsrDnsResolution",
            "DeviceDnsResolution.csv",
        )

    def monitor_traffic(self) -> None:
        """Menu 136: Monitor traffic on switch/SRX port (streaming)."""
        logging.info("Menu #136: Monitor Traffic (streaming)")
        selection = self._select_site_and_device("monitor_traffic", "switch")
        if not selection:
            return
        site_id, device_id, _ = selection
        port_id = self._select_port_from_device(site_id, device_id)
        if not port_id:
            return
        body: dict[str, Any] = {"port_id": port_id}
        duration_str = self._safe_input_fn(
            "Duration in seconds (default: 60): ",
            default_value="60",
            context="monitor_duration",
        )
        try:
            duration = int(duration_str) if duration_str else 60
        except ValueError:
            duration = 60
        body["duration"] = duration
        print(f"\n-> Monitoring traffic on port {port_id}...")
        self._run_streaming_command(
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.monitorSiteDeviceTraffic,
            body,
            timeout_seconds=duration + 30,
        )

    def run_top(self) -> None:
        """Menu 137: Run top command on switch/SRX (streaming)."""
        logging.info("Menu #137: Run Top (streaming)")
        selection = self._select_site_and_device("run_top", "switch")
        if not selection:
            return
        site_id, device_id, _ = selection
        print("\n-> Running top command...")
        self._run_streaming_command(
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.runSiteSrxTopCommand,
            timeout_seconds=120,
        )

    # ------------------------------------------------------------------
    # SHOW COMMANDS
    # ------------------------------------------------------------------

    def show_session(self) -> None:
        """Menu 128: Show sessions on SSR/SRX gateway."""
        logging.info("Menu #128: Show Sessions")
        selection = self._select_site_and_device("show_session", "gateway")
        if not selection:
            return
        site_id, device_id, _ = selection
        body: dict[str, Any] = {}
        service = self._safe_input_fn(
            "Service name filter (Enter to skip): ",
            context="session_service",
        )
        if service:
            body["service_name"] = service
        session = self._safe_input_fn(
            "Session ID filter (Enter to skip): ",
            context="session_id_filter",
        )
        if session:
            body["session_id"] = session
        node = self._safe_input_fn(
            "Node (node0/node1, Enter to skip): ",
            context="session_node",
        )
        if node:
            body["node"] = node
        print("\n-> Fetching device sessions...")
        result = self._run_websocket_command(
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.showSiteSsrAndSrxSessions,
            body,
        )
        self._display_and_export_result(
            result,
            "Sessions",
            site_id,
            device_id,
            "showSiteSsrAndSrxSessions",
            "DeviceSessions.csv",
        )

    def show_service_path(self) -> None:
        """Menu 129: Show service path on SSR gateway."""
        logging.info("Menu #129: Show Service Path")
        selection = self._select_site_and_device("show_service_path", "gateway")
        if not selection:
            return
        site_id, device_id, _ = selection
        body: dict[str, Any] = {}
        service = self._safe_input_fn(
            "Service name (Enter to skip): ",
            context="service_path_name",
        )
        if service:
            body["service_name"] = service
        node = self._safe_input_fn(
            "Node (node0/node1, Enter to skip): ",
            context="service_path_node",
        )
        if node:
            body["node"] = node
        print("\n-> Fetching service path...")
        result = self._run_websocket_command(
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.showSiteSsrServicePath,
            body,
        )
        self._display_and_export_result(
            result,
            "Service Path",
            site_id,
            device_id,
            "showSiteSsrServicePath",
            "DeviceServicePath.csv",
        )

    def show_bgp_summary(self) -> None:
        """Menu 130: Show BGP summary on switch or gateway."""
        logging.info("Menu #130: Show BGP Summary")
        selection = self._select_site_and_device("show_bgp_summary")
        if not selection:
            return
        site_id, device_id, _ = selection
        body: dict[str, Any] = {}
        node = self._safe_input_fn("Node (node0/node1, Enter to skip): ", context="bgp_node")
        if node:
            body["node"] = node
        print("\n-> Fetching BGP summary...")
        result = self._run_websocket_command(
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.showSiteDeviceBgpSummary,
            body,
        )
        self._display_and_export_result(
            result,
            "BGP Summary",
            site_id,
            device_id,
            "showSiteDeviceBgpSummary",
            "DeviceBgpSummary.csv",
        )

    def show_arp_table(self) -> None:
        """Menu 131: Show ARP table on switch or gateway."""
        logging.info("Menu #131: Show ARP Table")
        selection = self._select_site_and_device("show_arp_table")
        if not selection:
            return
        site_id, device_id, _ = selection
        body: dict[str, Any] = {}
        node = self._safe_input_fn("Node (node0/node1, Enter to skip): ", context="arp_node")
        if node:
            body["node"] = node
        print("\n-> Fetching ARP table...")
        result = self._run_websocket_command(
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.showSiteDeviceArpTable,
            body,
        )
        self._display_and_export_result(
            result,
            "ARP Table",
            site_id,
            device_id,
            "showSiteDeviceArpTable",
            "DeviceArpTable.csv",
        )

    def show_dhcp_leases(self) -> None:
        """Menu 132: Show DHCP leases on switch or gateway."""
        logging.info("Menu #132: Show DHCP Leases")
        selection = self._select_site_and_device("show_dhcp_leases")
        if not selection:
            return
        site_id, device_id, _ = selection
        body: dict[str, Any] = {}
        network = self._select_network_from_device(site_id, device_id)
        if network:
            body["network"] = network
        node = self._safe_input_fn("Node (node0/node1, Enter to skip): ", context="dhcp_node")
        if node:
            body["node"] = node
        print("\n-> Fetching DHCP leases...")
        result = self._run_websocket_command(
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.showSiteDeviceDhcpLeases,
            body,
        )
        self._display_and_export_result(
            result,
            "DHCP Leases",
            site_id,
            device_id,
            "showSiteDeviceDhcpLeases",
            "DeviceDhcpLeases.csv",
        )

    def show_dot1x(self) -> None:
        """Menu 133: Show 802.1X table on switch."""
        logging.info("Menu #133: Show 802.1X Table")
        selection = self._select_site_and_device("show_dot1x", "switch")
        if not selection:
            return
        site_id, device_id, _ = selection
        body: dict[str, Any] = {}
        node = self._safe_input_fn("Node (node0/node1, Enter to skip): ", context="dot1x_node")
        if node:
            body["node"] = node
        print("\n-> Fetching 802.1X table...")
        result = self._run_websocket_command(
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.showSiteDeviceDot1xTable,
            body,
        )
        self._display_and_export_result(
            result,
            "802.1X Table",
            site_id,
            device_id,
            "showSiteDeviceDot1xTable",
            "DeviceDot1xTable.csv",
        )

    def show_evpn_database(self) -> None:
        """Menu 134: Show EVPN database on switch or gateway."""
        logging.info("Menu #134: Show EVPN Database")
        selection = self._select_site_and_device("show_evpn_database")
        if not selection:
            return
        site_id, device_id, _ = selection
        body: dict[str, Any] = {}
        node = self._safe_input_fn("Node (node0/node1, Enter to skip): ", context="evpn_node")
        if node:
            body["node"] = node
        print("\n-> Fetching EVPN database...")
        result = self._run_websocket_command(
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.showSiteDeviceEvpnDatabase,
            body,
        )
        self._display_and_export_result(
            result,
            "EVPN Database",
            site_id,
            device_id,
            "showSiteDeviceEvpnDatabase",
            "DeviceEvpnDatabase.csv",
        )

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
            logging.error(f"Locate device failed: {error}", exc_info=True)
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
            logging.error(f"Unlocate device failed: {error}", exc_info=True)
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

    def cable_test(self) -> None:
        """Menu 141: Run cable test on switch port."""
        logging.info("Menu #141: Cable Test")
        selection = self._select_site_and_device("cable_test", "switch")
        if not selection:
            return
        site_id, device_id, _ = selection
        port_id = self._select_port_from_device(site_id, device_id)
        if not port_id:
            return
        body: dict[str, Any] = {"port": port_id}
        print(f"\n-> Running cable test on port {port_id}...")
        result = self._run_websocket_command(
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.cableTestFromSwitch,
            body,
        )
        self._display_and_export_result(
            result,
            "Cable Test",
            site_id,
            device_id,
            "cableTestFromSwitch",
            "DeviceCableTest.csv",
        )

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
            logging.error(f"Reprovision failed: {error}", exc_info=True)
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
            logging.warning(f"VC preflight check failed: {error}", exc_info=True)
        try:
            response = mistapi.api.v1.sites.devices.readoptSiteOctermDevice(self._apisession, site_id, device_id)
            self._print_api_result(
                response,
                "Device re-adoption initiated.",
                "Re-adopt failed",
            )
        except Exception as error:
            logging.error(f"Re-adopt failed: {error}", exc_info=True)
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
            logging.error(f"ZTP password request failed: {error}", exc_info=True)
            print(f"! ZTP password request failed: {error}")

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
            logging.error(
                f"Config commands request failed: {error}",
                exc_info=True,
            )
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
            logging.error(f"Support file upload failed: {error}", exc_info=True)
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
            logging.error(f"Clear ARP cache failed: {error}", exc_info=True)
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
            logging.error(f"Clear BGP routes failed: {error}", exc_info=True)
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
            logging.error(f"Clear session failed: {error}", exc_info=True)
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
            logging.error(f"Clear MAC table failed: {error}", exc_info=True)
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
            logging.error(f"Clear BPDU errors failed: {error}", exc_info=True)
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
            logging.error(f"Clear learned MACs failed: {error}", exc_info=True)
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
            logging.error(
                f"Clear policy hit count failed: {error}",
                exc_info=True,
            )
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
            logging.error(f"Release DHCP lease failed: {error}", exc_info=True)
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
            logging.error(
                f"Release SSR DHCP lease failed: {error}",
                exc_info=True,
            )
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
            logging.error(f"Poll switch stats failed: {error}", exc_info=True)
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
            logging.error(f"Create snapshot failed: {error}", exc_info=True)
            print(f"! Create snapshot failed: {error}")
