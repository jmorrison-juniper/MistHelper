"""Selection helper cluster for :mod:`src.device.utility_commands`.

Owns the 24 helpers that resolve user selections (site + device, ports,
interfaces, networks) before a Mist device command is issued. Splitting
these helpers off the parent :class:`~src.device.utility_commands.DeviceUtilityCommands`
removes the highest-complexity hotspots on the parent (``_display_and_select_ifstat``
was C=10, ``_display_ports_from_if_stat`` C=8, ``_print_interface_list`` C=8,
``_select_site_and_device`` C=7, ``_select_port_from_device`` C=7) and cuts
the parent's line count roughly in half so it fits inside STRUCT-LENGTH.

The parent binds an instance as ``self._selection`` and its
``__getattr__`` proxies unknown attribute lookups here so shared state
(dependency callables, mistapi module) stays transparent. This module
mirrors the wrapper + ``__getattr__`` pattern used by
:mod:`src.network._routing_utils_payload`.
"""

# pylint: disable=logging-fstring-interpolation

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import logging  # WHY: debug-level logging when stat lookups fail silently
from typing import Any, cast  # WHY: Any parameterizes SDK payload dicts; cast narrows API responses

import mistapi  # WHY: stats + device APIs live under mistapi.api.v1.sites.*

from src.device._utility_commands_cluster import _ClusterBase  # WHY: shared proxy base

_PHYSICAL_PORT_PREFIXES: tuple[str, ...] = ("ge-", "xe-", "et-", "mge-")  # WHY: Juniper physical port prefixes

_ROUTABLE_IFACE_PREFIXES: tuple[str, ...] = (  # WHY: routable interface name prefixes
    "ge-",
    "xe-",
    "et-",
    "mge-",
    "lte-",
    "irb",
    "lo",
)


class _UtilityCommandsSelection(_ClusterBase):  # WHY: cluster wrapper matching the routing_utils split pattern
    """Wrapper class holding the 24 extracted selection helpers."""

    # ------------------------------------------------------------------
    # Device type + site+device selection
    # ------------------------------------------------------------------

    def _validate_device_type(self, device_type: str, command_name: str) -> bool:  # WHY: enforce compat map
        """Check device type against the parent's compatibility map."""
        allowed = self._uc.DEVICE_TYPE_COMPATIBILITY_MAP.get(command_name, [])  # WHY: closed enum per cmd
        if device_type not in allowed:  # WHY: reject incompatible device types up front
            allowed_str = ", ".join(allowed)  # WHY: comma-list for user-facing hint
            print(f"! This command is only available on: {allowed_str}")  # WHY: signal wrong device type
            print(f"! The selected device is a {device_type}.")  # WHY: name the actual device
            return False  # WHY: caller aborts command flow
        return True  # WHY: caller proceeds with matching device

    def _select_site_and_device(
        self, command_name: str, device_type_filter: str = "all"
    ) -> tuple[str, str, str] | None:  # WHY: three-tuple result; None on cancel
        """Select site and device, validate type, warn if offline."""
        ids = self._resolve_site_device_ids(device_type_filter)  # WHY: gather user picks first
        if ids is None:  # WHY: user cancelled selection at some stage
            return None  # WHY: propagate cancellation to caller
        site_id, device_id = ids  # WHY: unpack for downstream stats lookup
        # WHY: route through parent so patch.object(duc, "_get_device_info", ...) intercepts
        device_info = cast(  # WHY: parent proxy returns Any; narrow to concrete type
            "dict[str, Any] | None",
            self._uc._get_device_info(site_id, device_id),  # noqa: SLF001
        )
        if not device_info:  # WHY: no info means we can't verify compatibility
            print("! Could not retrieve device info from stats API.")  # WHY: signal API failure
            return None  # WHY: abort when stats unavailable
        device_type = device_info.get("type")  # WHY: needed for compatibility check
        if not device_type:  # WHY: guard against malformed stats payload
            print("! Could not determine device type.")  # WHY: expose the problem to operator
            return None  # WHY: abort without a device type
        if not self._validate_device_type(device_type, command_name):  # WHY: enforce per-command allowlist
            return None  # WHY: incompatible device; caller must not proceed
        self._warn_if_offline(device_info)  # WHY: soft warning, does not abort
        return (site_id, device_id, device_type)  # WHY: caller uses this tuple to route commands

    def _resolve_site_device_ids(self, device_type_filter: str) -> tuple[str, str] | None:  # WHY: gather picks
        """Prompt the user for a site and device, returning both IDs."""
        site_id = self._select_site_fn()  # WHY: interactive site picker (via __getattr__ proxy)
        if not site_id:  # WHY: user cancelled or no site available
            print("! No site selected. Operation cancelled.")  # WHY: signal cancellation
            return None  # WHY: abort without a site
        device_id = self._select_device_fn(site_id, device_type_filter)  # WHY: device picker (proxy)
        if not device_id:  # WHY: user cancelled or no device available
            print("! No device selected. Operation cancelled.")  # WHY: signal cancellation
            return None  # WHY: abort without a device
        return (site_id, device_id)  # WHY: both IDs known; caller continues to stats lookup

    @staticmethod
    def _warn_if_offline(device_info: dict[str, Any]) -> None:
        """Emit a soft warning when the target device is not connected."""
        status = device_info.get("status", "unknown")  # WHY: default keeps message informative
        if status != "connected":  # WHY: only warn on non-connected states
            print(f"[WARNING] Device status is '{status}' - command may not succeed.")  # WHY: operator hint

    def _get_device_info(self, site_id: str, device_id: str) -> dict[str, Any] | None:
        """Fetch device type and status from the stats API."""
        try:  # WHY: mistapi may raise on network/auth failures
            response = mistapi.api.v1.sites.stats.getSiteDeviceStats(  # WHY: authoritative type+status source
                self._apisession, site_id, device_id  # WHY: __getattr__ proxy
            )
            if hasattr(response, "data") and isinstance(response.data, dict):  # WHY: guard shape
                return response.data  # WHY: caller consumes type/status keys
        except Exception as error:  # WHY: log-and-continue on any mistapi error
            logging.error("Failed to get device stats: %s", error)  # WHY: audit trail
        return None  # WHY: caller treats None as unavailable

    # ------------------------------------------------------------------
    # Port selection helpers
    # ------------------------------------------------------------------

    def _select_port_from_device(self, site_id: str, device_id: str) -> str | None:
        """Fetch ports from device stats, display list, return selected."""
        stats = self._fetch_stats_data(site_id, device_id)  # WHY: shared stats fetch + guard
        if stats is None:  # WHY: stats unavailable, fall back to manual entry
            # WHY: route via parent so test patches on duc apply
            return cast("str | None", self._uc._manual_port_entry())  # noqa: SLF001
        ports = stats.get("ports", [])  # WHY: newer devices use the 'ports' array
        if ports:  # WHY: prefer structured port list when present
            # WHY: route via parent for test patches
            return cast("str | None", self._uc._display_and_select_port(ports))  # noqa: SLF001
        if_stat = stats.get("if_stat", {})  # WHY: fallback to legacy if_stat dict
        if isinstance(if_stat, dict) and if_stat:  # WHY: only use if it's a populated mapping
            # WHY: route via parent for test patches
            return cast("str | None", self._uc._display_and_select_ifstat(if_stat))  # noqa: SLF001
        # WHY: no structured data, ask user directly; route via parent for patches
        return cast("str | None", self._uc._manual_port_entry())  # noqa: SLF001

    def _fetch_stats_data(self, site_id: str, device_id: str) -> dict[str, Any] | None:
        """Fetch the raw stats data dict for a device, or None on any failure."""
        try:  # WHY: mistapi may raise on network/auth failures
            response = mistapi.api.v1.sites.stats.getSiteDeviceStats(  # WHY: source of port/if data
                self._apisession, site_id, device_id  # WHY: __getattr__ proxy
            )
            if not hasattr(response, "data") or not isinstance(response.data, dict):  # WHY: guard shape
                return None
            return response.data  # WHY: caller drills into 'ports' / 'if_stat' / 'ip_stat'
        except Exception as error:  # WHY: log-and-return-None on any error
            logging.debug("Could not fetch device stats: %s", error)  # WHY: debug-only trace
            return None

    def _display_and_select_port(self, ports: list[dict[str, Any]]) -> str | None:
        """Display numbered port list and get selection."""
        self._render_port_rows(ports)  # WHY: emit numbered rows for user
        selection = self._safe_input_fn(  # WHY: EOF-safe prompt (via __getattr__ proxy)
            "\nSelect port by number or type port name: ",
            context="port_selection",
        )
        if not selection:  # WHY: empty input cancels selection
            print("! No port selected.")  # WHY: signal cancellation
            return None
        return self._resolve_port_choice(selection, ports)  # WHY: numeric or literal path

    @staticmethod
    def _render_port_rows(ports: list[dict[str, Any]]) -> None:
        """Print the numbered port list for interactive selection."""
        print("\nAvailable ports:")  # WHY: banner announcing list
        for index, port in enumerate(ports, 1):  # WHY: 1-based numbering matches operator input
            port_name = port.get("port_id", port.get("name", f"port_{index}"))  # WHY: fallback name
            port_status = port.get("up", "unknown")  # WHY: default informs "unknown" rendering
            status_str = "UP" if port_status else "DOWN"  # WHY: boolean → human label
            speed = port.get("speed", "")  # WHY: optional speed hint for operator
            print(f"  {index}. {port_name} [{status_str}] {speed}")  # WHY: numbered row

    @staticmethod
    def _resolve_port_choice(selection: str, ports: list[dict[str, Any]]) -> str | None:
        """Resolve a numeric or literal port choice to a port name."""
        if selection.isdigit():  # WHY: numeric input references list index
            idx = int(selection) - 1  # WHY: 0-based indexing
            if 0 <= idx < len(ports):  # WHY: bounds check
                result: str = str(ports[idx].get("port_id", ports[idx].get("name", "")))  # WHY: fallback
                return result
            print("! Invalid port number.")  # WHY: signal out-of-range
            return None
        return selection  # WHY: literal port name typed by user

    def _display_and_select_ifstat(self, if_stat: dict[str, Any]) -> str | None:
        """Display interfaces from an if_stat dict and prompt for selection."""
        physical = self._physical_iface_names(if_stat)  # WHY: prefer physical ports
        self._render_ifstat_rows(if_stat, physical)  # WHY: emit numbered rows
        selection = self._safe_input_fn(  # WHY: EOF-safe prompt (via __getattr__ proxy)
            "\nSelect by number or type port name: ",
            context="ifstat_selection",
        )
        if not selection:  # WHY: empty input cancels selection
            print("! No port selected.")  # WHY: signal cancellation
            return None
        return self._resolve_ifstat_choice(selection, physical)  # WHY: numeric or literal path

    @staticmethod
    def _physical_iface_names(if_stat: dict[str, Any]) -> list[str]:
        """Return sorted physical-port names, falling back to all keys."""
        physical = [name for name in if_stat if name.startswith(_PHYSICAL_PORT_PREFIXES)]  # WHY: filter
        if not physical:  # WHY: some platforms report only logical interfaces
            physical = list(if_stat.keys())  # WHY: show whatever is available
        physical.sort()  # WHY: stable order for operator recognition
        return physical

    @staticmethod
    def _render_ifstat_rows(if_stat: dict[str, Any], physical: list[str]) -> None:
        """Print numbered rows of if_stat entries with UP/DOWN status."""
        print("\nAvailable ports/interfaces:")  # WHY: banner announcing list
        for idx, name in enumerate(physical, 1):  # WHY: 1-based numbering
            info = if_stat.get(name, {})  # WHY: per-interface dict may be missing
            up = "UP" if info.get("up") else "DOWN"  # WHY: boolean → human label
            print(f"  {idx}. {name} [{up}]")  # WHY: numbered row

    @staticmethod
    def _resolve_ifstat_choice(selection: str, physical: list[str]) -> str | None:
        """Resolve a numeric or literal ifstat choice, stripping VLAN suffix."""
        if selection.isdigit():  # WHY: numeric selection references list index
            sel_idx = int(selection) - 1  # WHY: 0-based indexing
            if 0 <= sel_idx < len(physical):  # WHY: bounds check
                base = physical[sel_idx]  # WHY: pick the matched interface
                return base.split(".")[0] if "." in base else base  # WHY: drop unit suffix
            print("! Invalid port number.")  # WHY: signal out-of-range
            return None
        return selection  # WHY: literal port name typed by user

    def _manual_port_entry(self) -> str | None:
        """Prompt for manual port name entry."""
        port = self._safe_input_fn(  # WHY: EOF-safe prompt (via __getattr__ proxy)
            "Enter port name (e.g., ge-0/0/0): ",
            context="manual_port_entry",
        )
        return port if port else None  # WHY: empty input treated as cancel

    def _select_port_optional(self, site_id: str, device_id: str) -> str:
        """Show port list and let the user pick or skip."""
        port_names = self._discover_ports(site_id, device_id)  # WHY: gather names for numeric input
        selection = self._safe_input_fn(  # WHY: EOF-safe prompt (via __getattr__ proxy)
            "Port (number, name, or Enter to skip): ",
            context="port_optional",
        )
        if not selection:  # WHY: empty input skips port filter
            return ""
        return self._resolve_port_selection(selection, port_names)  # WHY: numeric or literal path

    def _discover_ports(self, site_id: str, device_id: str) -> list[str]:
        """Fetch and display available ports from device stats."""
        stats = self._fetch_stats_data(site_id, device_id)  # WHY: shared stats fetch + guard
        if stats is None:  # WHY: no stats means no discovered ports
            return []
        ports = stats.get("ports", [])  # WHY: newer devices use the 'ports' array
        if ports:  # WHY: prefer structured port list when present
            return self._display_ports_from_list(ports)
        return self._display_ports_from_if_stat(stats.get("if_stat", {}))  # WHY: fallback path

    @staticmethod
    def _display_ports_from_list(ports: list[dict[str, Any]]) -> list[str]:
        """Display ports from the ports array in stats response."""
        port_names: list[str] = []  # WHY: accumulate names returned to caller
        print("\nAvailable ports:")  # WHY: banner announcing list
        for idx, port in enumerate(ports, 1):  # WHY: 1-based numbering
            name = port.get("port_id", port.get("name", f"port_{idx}"))  # WHY: fallback name
            up = "UP" if port.get("up") else "DOWN"  # WHY: boolean → human label
            print(f"  {idx}. {name} [{up}]")  # WHY: numbered row
            port_names.append(name)  # WHY: caller resolves numeric input via this list
        return port_names

    @staticmethod
    def _display_ports_from_if_stat(if_stat: Any) -> list[str]:
        """Display physical ports from if_stat dict as fallback."""
        physical = _UtilityCommandsSelection._physical_from_if_stat(if_stat)  # WHY: filter to physical
        if not physical:  # WHY: no physical entries means nothing to render
            return []
        return _UtilityCommandsSelection._emit_if_stat_rows(if_stat, physical)  # WHY: render + return

    @staticmethod
    def _physical_from_if_stat(if_stat: Any) -> list[str]:
        """Return sorted physical-port names from an if_stat mapping (or empty)."""
        if not isinstance(if_stat, dict) or not if_stat:  # WHY: guard shape + emptiness
            return []
        return sorted(n for n in if_stat if n.startswith(_PHYSICAL_PORT_PREFIXES))  # WHY: filter+sort

    @staticmethod
    def _emit_if_stat_rows(if_stat: dict[str, Any], physical: list[str]) -> list[str]:
        """Print numbered if_stat rows and return the port-name list."""
        port_names: list[str] = []  # WHY: caller resolves numeric input via this list
        print("\nAvailable ports:")  # WHY: banner announcing list
        for idx, name in enumerate(physical, 1):  # WHY: 1-based numbering
            info = if_stat.get(name, {})  # WHY: per-interface dict may be missing
            up = "UP" if info.get("up") else "DOWN"  # WHY: boolean → human label
            print(f"  {idx}. {name} [{up}]")  # WHY: numbered row
            port_names.append(name)  # WHY: build parallel array for resolve step
        return port_names

    @staticmethod
    def _resolve_port_selection(selection: str, port_names: list[str]) -> str:
        """Resolve a user's optional port selection to a port name."""
        if selection.isdigit() and port_names:  # WHY: numeric requires known list
            idx = int(selection) - 1  # WHY: 0-based indexing
            if 0 <= idx < len(port_names):  # WHY: bounds check
                base = port_names[idx]  # WHY: pick matched port
                return base.split(".")[0] if "." in base else base  # WHY: drop unit suffix
        return selection  # WHY: literal name or out-of-range numeric returned verbatim

    # ------------------------------------------------------------------
    # Interface selection helpers
    # ------------------------------------------------------------------

    def _select_interface_from_device(self, site_id: str, device_id: str) -> str | None:
        """Fetch network interfaces from device stats and prompt for selection."""
        stats = self._fetch_stats_data(site_id, device_id)  # WHY: shared stats fetch + guard
        if stats is None:  # WHY: no stats means we must fall back to manual entry
            # WHY: route via parent so test patches on duc apply
            return cast("str | None", self._uc._manual_interface_entry())  # noqa: SLF001
        if_stat = stats.get("if_stat", {})  # WHY: primary interface source
        ip_stat = stats.get("ip_stat", {})  # WHY: fallback interface source with IP metadata
        ports = stats.get("ports", [])  # WHY: last-resort interface source
        interfaces = self._extract_interfaces(if_stat, ip_stat, ports)  # WHY: unified list
        if not interfaces:  # WHY: nothing discoverable, ask user directly
            # WHY: route via parent for test patches
            return cast("str | None", self._uc._manual_interface_entry())  # noqa: SLF001
        # WHY: render menu via parent so tests can patch _print_interface_list on duc
        self._uc._print_interface_list(interfaces, if_stat, ip_stat)  # noqa: SLF001
        # WHY: prompt + resolve via parent so tests can patch _get_interface_selection on duc
        return cast("str | None", self._uc._get_interface_selection(interfaces))  # noqa: SLF001

    @staticmethod
    def _extract_interfaces(
        if_stat: Any,
        ip_stat: Any,
        ports: list[dict[str, Any]],
    ) -> list[str]:
        """Extract interface names from stats, trying multiple sources."""
        if isinstance(if_stat, dict) and if_stat:  # WHY: primary source when populated
            return list(if_stat.keys())  # WHY: keys are interface names
        ip_interfaces = _UtilityCommandsSelection._interfaces_from_ip_stat(ip_stat)  # WHY: fallback #1
        if ip_interfaces:  # WHY: prefer routable set from ip_stat when present
            return ip_interfaces  # WHY: return routable names
        return _UtilityCommandsSelection._interfaces_from_ports(ports)  # WHY: last-resort port array

    @staticmethod
    def _interfaces_from_ports(ports: list[dict[str, Any]]) -> list[str]:
        """Extract non-empty port names from a raw ports array."""
        return [
            p.get("port_id", p.get("name", "")) for p in ports if p.get("port_id") or p.get("name")
        ]  # WHY: pluck any usable name, drop empty entries

    @staticmethod
    def _interfaces_from_ip_stat(ip_stat: Any) -> list[str]:
        """Extract interface names from an ip_stat dict."""
        if not isinstance(ip_stat, dict) or not ip_stat:  # WHY: guard shape + emptiness
            return []
        return [k for k in ip_stat if k.startswith(_ROUTABLE_IFACE_PREFIXES)]  # WHY: routable filter

    def _print_interface_list(
        self,
        interfaces: list[str],
        if_stat: dict[str, Any] | Any,
        ip_stat: dict[str, Any] | Any,
    ) -> None:
        """Print a numbered list of available interfaces."""
        print("\nAvailable interfaces:")  # WHY: banner announcing list
        for idx, iface in enumerate(interfaces, 1):  # WHY: 1-based numbering
            extra = self._format_iface_extra(iface, if_stat, ip_stat)  # WHY: append IP metadata
            print(f"  {idx}. {iface}{extra}")  # WHY: numbered row with optional IP annotation

    @staticmethod
    def _format_iface_extra(
        iface: str,
        if_stat: dict[str, Any] | Any,
        ip_stat: dict[str, Any] | Any,
    ) -> str:
        """Return the suffix (`` (ip...)``) that annotates an interface row."""
        ifstat_extra = _UtilityCommandsSelection._ips_annotation(iface, if_stat)  # WHY: if_stat annotation
        if ifstat_extra:  # WHY: prefer if_stat which lists all IPs on interface
            return ifstat_extra  # WHY: return multi-IP annotation
        return _UtilityCommandsSelection._ip_annotation(iface, ip_stat)  # WHY: fallback single IP

    @staticmethod
    def _ips_annotation(iface: str, if_stat: dict[str, Any] | Any) -> str:
        """Return `` (ip1, ip2)`` suffix from an if_stat entry, or empty."""
        if not isinstance(if_stat, dict) or iface not in if_stat:  # WHY: guard shape + presence
            return ""  # WHY: no annotation available
        ips = if_stat[iface].get("ips", [])  # WHY: list of IPs on the interface
        return f" ({', '.join(ips)})" if ips else ""  # WHY: annotate only when non-empty

    @staticmethod
    def _ip_annotation(iface: str, ip_stat: dict[str, Any] | Any) -> str:
        """Return `` (ip)`` suffix from an ip_stat entry, or empty."""
        if not isinstance(ip_stat, dict) or iface not in ip_stat:  # WHY: guard shape + presence
            return ""  # WHY: no annotation available
        ip_addr = ip_stat[iface].get("ip", "")  # WHY: single primary IP
        return f" ({ip_addr})" if ip_addr else ""  # WHY: annotate only when present

    def _get_interface_selection(self, interfaces: list[str]) -> str | None:
        """Prompt the user to select from an interface list."""
        selection = cast(
            "str",
            self._safe_input_fn(  # WHY: EOF-safe prompt (via __getattr__ proxy)
                "\nSelect interface by number or type name: ",
                context="interface_selection",
            ),
        )
        if not selection:  # WHY: empty input cancels selection
            print("! No interface selected.")  # WHY: signal cancellation
            return None
        if selection.isdigit():  # WHY: numeric selection references list index
            sel_idx = int(selection) - 1  # WHY: 0-based indexing
            if 0 <= sel_idx < len(interfaces):  # WHY: bounds check
                return interfaces[sel_idx]
            print("! Invalid interface number.")  # WHY: signal out-of-range
            return None
        return selection  # WHY: literal interface name typed by user

    def _manual_interface_entry(self) -> str | None:
        """Prompt for manual interface name entry."""
        iface = self._safe_input_fn(  # WHY: EOF-safe prompt (via __getattr__ proxy)
            "Enter interface name (e.g., ge-0/0/0, wan0): ",
            context="manual_interface_entry",
            allow_empty=False,
        )
        return iface if iface else None  # WHY: empty treated as cancel

    # ------------------------------------------------------------------
    # Network (DHCP / ip_config) selection helpers
    # ------------------------------------------------------------------

    def _select_network_from_device(self, site_id: str, device_id: str) -> str:
        """Fetch DHCP/network config from device and prompt for selection."""
        network_names, network_labels = self._discover_networks(site_id, device_id)  # WHY: gather
        if network_names:  # WHY: only render menu when discovery yielded entries
            self._display_network_list(network_names, network_labels)  # WHY: render numbered menu
            if len(network_names) == 1:  # WHY: single option: auto-pick for operator convenience
                print(f"\n-> Auto-selecting: {network_names[0]}")  # WHY: transparency about choice
                return network_names[0]
        selection = self._safe_input_fn(  # WHY: EOF-safe prompt (via __getattr__ proxy)
            "Select network (number or name, required): ",
            context="dhcp_network",
            allow_empty=False,
        )
        if not selection:  # WHY: user cancelled required input
            return ""
        return self._resolve_network_selection(selection, network_names)  # WHY: numeric or literal

    def _discover_networks(self, site_id: str, device_id: str) -> tuple[list[str], list[str]]:
        """Fetch network names and labels from device config."""
        network_names: list[str] = []  # WHY: parallel arrays keep names in sync with labels
        network_labels: list[str] = []
        data = self._fetch_device_config(site_id, device_id)  # WHY: shared fetch + guard
        if data is not None:  # WHY: no fetch failure, populate from response
            self._collect_dhcp_networks(  # WHY: DHCP server entries come first
                data.get("dhcpd_config", {}), network_names, network_labels
            )
            self._collect_ip_networks(  # WHY: ip_config entries second, deduplicated by name
                data.get("ip_config", {}), network_names, network_labels
            )
        return network_names, network_labels

    def _fetch_device_config(self, site_id: str, device_id: str) -> dict[str, Any] | None:
        """Fetch the raw device-config dict, or None on any failure."""
        try:  # WHY: mistapi may raise on network/auth failures
            response = mistapi.api.v1.sites.devices.getSiteDevice(  # WHY: source of dhcpd/ip config
                self._apisession, site_id, device_id  # WHY: __getattr__ proxy
            )
            if hasattr(response, "data") and isinstance(response.data, dict):  # WHY: guard shape
                return response.data
        except Exception as error:  # WHY: log-and-return-None on any error
            logging.debug("Could not fetch network config: %s", error)  # WHY: debug-only trace
        return None

    @staticmethod
    def _collect_dhcp_networks(
        dhcpd_config: Any,
        names: list[str],
        labels: list[str],
    ) -> None:
        """Add DHCP-server networks to the parallel names/labels lists."""
        if not isinstance(dhcpd_config, dict):  # WHY: guard shape
            return
        for net_name in dhcpd_config:  # WHY: each key is a network name
            names.append(net_name)  # WHY: track selectable name
            labels.append(f"{net_name} (dhcp server)")  # WHY: annotate role for operator

    @staticmethod
    def _collect_ip_networks(
        ip_config: Any,
        names: list[str],
        labels: list[str],
    ) -> None:
        """Add ip_config networks (deduped against DHCP list) to the lists."""
        if not isinstance(ip_config, dict):  # WHY: guard shape
            return
        for net_name, net_cfg in ip_config.items():  # WHY: each key is a candidate network
            if net_name in names:  # WHY: skip duplicates already added by DHCP pass
                continue
            names.append(net_name)  # WHY: track selectable name
            labels.append(_UtilityCommandsSelection._label_for_ip_net(net_name, net_cfg))  # WHY: annotate

    @staticmethod
    def _label_for_ip_net(net_name: str, net_cfg: Any) -> str:
        """Build the display label for an ip_config entry."""
        ip_addr = net_cfg.get("ip", "") if isinstance(net_cfg, dict) else ""  # WHY: optional IP hint
        return f"{net_name} ({ip_addr})" if ip_addr else net_name  # WHY: annotate only if IP present

    @staticmethod
    def _display_network_list(network_names: list[str], network_labels: list[str]) -> None:
        """Print a numbered list of available networks."""
        del network_names  # WHY: names unused for rendering; kept for API symmetry with resolver
        print("\nAvailable networks:")  # WHY: banner announcing list
        for idx, label in enumerate(network_labels, 1):  # WHY: 1-based numbering
            print(f"  {idx}. {label}")  # WHY: numbered row

    @staticmethod
    def _resolve_network_selection(selection: str, network_names: list[str]) -> str:
        """Resolve a numeric or literal network selection to a name."""
        if selection.isdigit() and network_names:  # WHY: numeric requires known list
            sel_idx = int(selection) - 1  # WHY: 0-based indexing
            if 0 <= sel_idx < len(network_names):  # WHY: bounds check
                return network_names[sel_idx]
        return selection  # WHY: literal name or out-of-range numeric returned verbatim
