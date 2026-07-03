"""Show / diagnostic command cluster for :mod:`src.device.utility_commands`.

Owns the 16 read-only device commands (``traceroute``, ``show_ospf_*``,
``show_session``, ``show_service_path``, ``show_bgp_summary``,
``show_arp_table``, ``show_dhcp_leases``, ``show_dot1x``,
``show_evpn_database``, ``resolve_dns``, ``monitor_traffic``, ``run_top``,
``cable_test``) that gather device state through the WebSocket lifecycle
and render / export the result. Splitting these off
:class:`~src.device.utility_commands.DeviceUtilityCommands` moves roughly
480 lines out of the parent so it fits the STRUCT-LENGTH budget, and
reduces the parent's public-method count so STRUCT-METHOD-COUNT passes.

Because none of the helpers these commands call
(``_run_websocket_command``, ``_display_and_export_result``,
``_select_site_and_device``, etc.) are defined on this cluster, plain
``self._method(...)`` calls resolve via the cluster's ``__getattr__``
back to the parent, so tests that use
``patch.object(duc, "_run_websocket_command", ...)`` continue to win.

To keep every public method under the 25-line STRUCT-LENGTH budget the
per-command SDK method / display label / CSV filename triples are frozen
as module-level :class:`ShowCommandSpec` constants and dispatched through
a single :meth:`_run_and_export` helper. Body-builders for the
multi-prompt commands (OSPF variants, session, service-path, DHCP leases)
are broken out as small private helpers so each public method reads as a
straight-line selection -> body-build -> dispatch trio at C<=5.
"""

# pylint: disable=logging-fstring-interpolation

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import logging  # WHY: menu-level info logging on every command entry
from dataclasses import dataclass  # WHY: frozen ShowCommandSpec preset per command
from typing import Any  # WHY: Any parameterizes bundle dataclasses and dict payloads

import mistapi  # WHY: device show / diagnostic SDK calls live under mistapi.api.v1.sites.devices

from src.device._utility_commands_cluster import _ClusterBase  # WHY: shared proxy base
from src.device._utility_commands_websocket import ExportResultSpec  # WHY: single-arg spec for exporter


@dataclass(frozen=True)  # WHY: frozen so shared module constants cannot be mutated at runtime
class ShowCommandSpec:  # WHY: preset bundle per show command
    """Preset identifying the SDK method and export metadata for a show command.

    Grouping the four per-command constants (SDK bound method, display
    label, mistapi function label, CSV filename) into a single frozen
    dataclass lets :meth:`_UtilityCommandsShow._run_and_export` stay at a
    4-parameter signature (STRUCT-PARAMS limit 5) and moves the boilerplate
    ``ExportResultSpec(...)`` construction out of every public method,
    shrinking them below the 25-line STRUCT-LENGTH limit.
    """

    sdk_method: Any  # WHY: bound mistapi method (traceroute/show*/monitor/etc.)
    command_name: str  # WHY: banner label printed above rendered output
    api_function_name: str  # WHY: audit label recorded on the export row
    filename: str  # WHY: CSV output filename passed to write_export


# ----------------------------------------------------------------------
# Per-command specs (module-level constants keep public methods short)
# ----------------------------------------------------------------------

_TRACEROUTE_SPEC = ShowCommandSpec(  # WHY: Menu #123 traceroute dispatch preset
    sdk_method=mistapi.api.v1.sites.devices.tracerouteFromDevice,  # WHY: SDK entrypoint
    command_name="Traceroute",  # WHY: banner label
    api_function_name="tracerouteFromDevice",  # WHY: audit label
    filename="DeviceTraceroute.csv",  # WHY: CSV output file
)
_OSPF_NEIGHBORS_SPEC = ShowCommandSpec(  # WHY: Menu #124 OSPF neighbors preset
    sdk_method=mistapi.api.v1.sites.devices.showSiteGatewayOspfNeighbors,  # WHY: SDK entrypoint
    command_name="OSPF Neighbors",  # WHY: banner label
    api_function_name="showSiteGatewayOspfNeighbors",  # WHY: audit label
    filename="DeviceOspfNeighbors.csv",  # WHY: CSV output file
)
_OSPF_INTERFACES_SPEC = ShowCommandSpec(  # WHY: Menu #125 OSPF interfaces preset
    sdk_method=mistapi.api.v1.sites.devices.showSiteGatewayOspfInterfaces,  # WHY: SDK entrypoint
    command_name="OSPF Interfaces",  # WHY: banner label
    api_function_name="showSiteGatewayOspfInterfaces",  # WHY: audit label
    filename="DeviceOspfInterfaces.csv",  # WHY: CSV output file
)
_OSPF_DATABASE_SPEC = ShowCommandSpec(  # WHY: Menu #126 OSPF database preset
    sdk_method=mistapi.api.v1.sites.devices.showSiteGatewayOspfDatabase,  # WHY: SDK entrypoint
    command_name="OSPF Database",  # WHY: banner label
    api_function_name="showSiteGatewayOspfDatabase",  # WHY: audit label
    filename="DeviceOspfDatabase.csv",  # WHY: CSV output file
)
_OSPF_SUMMARY_SPEC = ShowCommandSpec(  # WHY: Menu #127 OSPF summary preset
    sdk_method=mistapi.api.v1.sites.devices.showSiteGatewayOspfSummary,  # WHY: SDK entrypoint
    command_name="OSPF Summary",  # WHY: banner label
    api_function_name="showSiteGatewayOspfSummary",  # WHY: audit label
    filename="DeviceOspfSummary.csv",  # WHY: CSV output file
)
_DNS_RESOLUTION_SPEC = ShowCommandSpec(  # WHY: Menu #135 DNS resolution preset
    sdk_method=mistapi.api.v1.sites.devices.testSiteSsrDnsResolution,  # WHY: SDK entrypoint
    command_name="DNS Resolution",  # WHY: banner label
    api_function_name="testSiteSsrDnsResolution",  # WHY: audit label
    filename="DeviceDnsResolution.csv",  # WHY: CSV output file
)
_SESSION_SPEC = ShowCommandSpec(  # WHY: Menu #128 show sessions preset
    sdk_method=mistapi.api.v1.sites.devices.showSiteSsrAndSrxSessions,  # WHY: SDK entrypoint
    command_name="Sessions",  # WHY: banner label
    api_function_name="showSiteSsrAndSrxSessions",  # WHY: audit label
    filename="DeviceSessions.csv",  # WHY: CSV output file
)
_SERVICE_PATH_SPEC = ShowCommandSpec(  # WHY: Menu #129 show service path preset
    sdk_method=mistapi.api.v1.sites.devices.showSiteSsrServicePath,  # WHY: SDK entrypoint
    command_name="Service Path",  # WHY: banner label
    api_function_name="showSiteSsrServicePath",  # WHY: audit label
    filename="DeviceServicePath.csv",  # WHY: CSV output file
)
_BGP_SUMMARY_SPEC = ShowCommandSpec(  # WHY: Menu #130 BGP summary preset
    sdk_method=mistapi.api.v1.sites.devices.showSiteDeviceBgpSummary,  # WHY: SDK entrypoint
    command_name="BGP Summary",  # WHY: banner label
    api_function_name="showSiteDeviceBgpSummary",  # WHY: audit label
    filename="DeviceBgpSummary.csv",  # WHY: CSV output file
)
_ARP_TABLE_SPEC = ShowCommandSpec(  # WHY: Menu #131 ARP table preset
    sdk_method=mistapi.api.v1.sites.devices.showSiteDeviceArpTable,  # WHY: SDK entrypoint
    command_name="ARP Table",  # WHY: banner label
    api_function_name="showSiteDeviceArpTable",  # WHY: audit label
    filename="DeviceArpTable.csv",  # WHY: CSV output file
)
_DHCP_LEASES_SPEC = ShowCommandSpec(  # WHY: Menu #132 DHCP leases preset
    sdk_method=mistapi.api.v1.sites.devices.showSiteDeviceDhcpLeases,  # WHY: SDK entrypoint
    command_name="DHCP Leases",  # WHY: banner label
    api_function_name="showSiteDeviceDhcpLeases",  # WHY: audit label
    filename="DeviceDhcpLeases.csv",  # WHY: CSV output file
)
_DOT1X_SPEC = ShowCommandSpec(  # WHY: Menu #133 802.1X table preset
    sdk_method=mistapi.api.v1.sites.devices.showSiteDeviceDot1xTable,  # WHY: SDK entrypoint
    command_name="802.1X Table",  # WHY: banner label
    api_function_name="showSiteDeviceDot1xTable",  # WHY: audit label
    filename="DeviceDot1xTable.csv",  # WHY: CSV output file
)
_EVPN_DATABASE_SPEC = ShowCommandSpec(  # WHY: Menu #134 EVPN database preset
    sdk_method=mistapi.api.v1.sites.devices.showSiteDeviceEvpnDatabase,  # WHY: SDK entrypoint
    command_name="EVPN Database",  # WHY: banner label
    api_function_name="showSiteDeviceEvpnDatabase",  # WHY: audit label
    filename="DeviceEvpnDatabase.csv",  # WHY: CSV output file
)
_CABLE_TEST_SPEC = ShowCommandSpec(  # WHY: Menu #141 cable test preset
    sdk_method=mistapi.api.v1.sites.devices.cableTestFromSwitch,  # WHY: SDK entrypoint
    command_name="Cable Test",  # WHY: banner label
    api_function_name="cableTestFromSwitch",  # WHY: audit label
    filename="DeviceCableTest.csv",  # WHY: CSV output file
)


class _UtilityCommandsShow(_ClusterBase):  # WHY: cluster wrapper mirroring _UtilityCommandsWebsocket
    """Wrapper class holding the 16 read-only show / diagnostic commands."""

    # ------------------------------------------------------------------
    # Common dispatch helper
    # ------------------------------------------------------------------

    def _run_and_export(
        self,
        site_id: str,  # WHY: mistapi site scope for SDK call
        device_id: str,  # WHY: mistapi device scope for SDK call
        body: dict[str, Any] | None,  # WHY: optional request body (None for arg-less SDKs)
        spec: ShowCommandSpec,  # WHY: preset holding SDK method + export metadata
    ) -> None:
        """Run the WebSocket command per ``spec`` then display + export the result."""
        result = self._run_websocket_command(  # WHY: __getattr__ -> websocket cluster (patchable via duc)
            site_id, device_id, spec.sdk_method, body,
        )
        self._display_and_export_result(  # WHY: renders banner + writes CSV row
            ExportResultSpec(
                result=result,  # WHY: WebSocket command payload (None on timeout)
                command_name=spec.command_name,  # WHY: banner label
                site_id=site_id,  # WHY: audit metadata on exported row
                device_id=device_id,  # WHY: audit metadata on exported row
                api_function_name=spec.api_function_name,  # WHY: mistapi function label
                filename=spec.filename,  # WHY: output CSV filename
            )
        )

    # ------------------------------------------------------------------
    # DIAGNOSTIC COMMANDS
    # ------------------------------------------------------------------

    def traceroute(self) -> None:
        """Menu 123: Run traceroute from device to destination host."""
        logging.info("Menu #123: Traceroute from device")  # WHY: menu entry audit trail
        selection = self._select_site_and_device("traceroute")  # WHY: __getattr__ -> selection cluster
        if not selection:  # WHY: user cancelled / no picks
            return  # WHY: nothing to do without a device target
        site_id, device_id, _ = selection  # WHY: destructure IDs, ignore display name
        host = self._safe_input_fn(  # WHY: destination host is mandatory user input
            "Enter destination host or IP (required): ",
            context="traceroute_host",  # WHY: context key wires into safe_input policy
            allow_empty=False,  # WHY: reject blank input at the prompt layer
        )
        if not host:  # WHY: defensive re-check even though allow_empty=False
            print("! Destination host is required.")  # WHY: surface reason to operator
            return  # WHY: abort without firing SDK call
        body = self._build_traceroute_body(host)  # WHY: extract keeps public method under 25 lines
        print(f"\n-> Running traceroute to {host}...")  # WHY: operator progress feedback
        self._run_and_export(site_id, device_id, body, _TRACEROUTE_SPEC)  # WHY: dispatch + export

    def _build_traceroute_body(self, host: str) -> dict[str, Any]:
        """Build the traceroute request body from prompted protocol input."""
        body: dict[str, Any] = {"host": host}  # WHY: required destination goes in body
        protocol = self._safe_input_fn(  # WHY: optional udp/icmp protocol selector
            "Protocol (udp/icmp, default: udp): ",
            default_value="udp",  # WHY: mistapi default when operator skips
            context="traceroute_protocol",  # WHY: context key wires into safe_input policy
        )
        if protocol and protocol.lower() in ("udp", "icmp"):  # WHY: filter to accepted protocols
            body["protocol"] = protocol.lower()  # WHY: normalize case for SDK
        return body  # WHY: dict consumed by _run_and_export

    # ------------------------------------------------------------------
    # OSPF SHOW COMMANDS
    # ------------------------------------------------------------------

    def show_ospf_neighbors(self) -> None:
        """Menu 124: Show OSPF neighbors on SSR/SRX gateway."""
        logging.info("Menu #124: Show OSPF Neighbors")  # WHY: menu entry audit trail
        selection = self._select_site_and_device("show_ospf_neighbors", "gateway")  # WHY: gateway-only
        if not selection:  # WHY: user cancelled / no picks
            return  # WHY: nothing to do without a device target
        site_id, device_id, _ = selection  # WHY: destructure IDs, ignore display name
        body = self._build_ospf_neighbors_body()  # WHY: extract keeps public method under 25 lines
        print("\n-> Fetching OSPF neighbors...")  # WHY: operator progress feedback
        self._run_and_export(site_id, device_id, body, _OSPF_NEIGHBORS_SPEC)  # WHY: dispatch + export

    def _build_ospf_neighbors_body(self) -> dict[str, Any]:
        """Prompt for optional vrf / node / neighbor filters."""
        body: dict[str, Any] = {}  # WHY: start empty; only add prompted filters
        vrf = self._safe_input_fn("VRF (Enter to skip): ", context="ospf_vrf")  # WHY: optional VRF
        if vrf:  # WHY: skip filter if blank
            body["vrf"] = vrf  # WHY: propagate to SDK
        node = self._safe_input_fn("Node (node0/node1, Enter to skip): ", context="ospf_node")  # WHY: node
        if node:  # WHY: skip filter if blank
            body["node"] = node  # WHY: propagate to SDK
        neighbor = self._safe_input_fn("Neighbor IP (Enter to skip): ", context="ospf_neighbor")  # WHY: IP
        if neighbor:  # WHY: skip filter if blank
            body["neighbor"] = neighbor  # WHY: propagate to SDK
        return body  # WHY: dict consumed by _run_and_export

    def show_ospf_interfaces(self) -> None:
        """Menu 125: Show OSPF interfaces on SSR/SRX gateway."""
        logging.info("Menu #125: Show OSPF Interfaces")  # WHY: menu entry audit trail
        selection = self._select_site_and_device("show_ospf_interfaces", "gateway")  # WHY: gateway-only
        if not selection:  # WHY: user cancelled / no picks
            return  # WHY: nothing to do without a device target
        site_id, device_id, _ = selection  # WHY: destructure IDs, ignore display name
        body = self._build_ospf_interfaces_body(site_id, device_id)  # WHY: extract keeps <=25 lines
        print("\n-> Fetching OSPF interfaces...")  # WHY: operator progress feedback
        self._run_and_export(site_id, device_id, body, _OSPF_INTERFACES_SPEC)  # WHY: dispatch + export

    def _build_ospf_interfaces_body(self, site_id: str, device_id: str) -> dict[str, Any]:
        """Prompt for optional vrf / node / port filters."""
        body: dict[str, Any] = {}  # WHY: start empty; only add prompted filters
        vrf = self._safe_input_fn("VRF (Enter to skip): ", context="ospf_vrf")  # WHY: optional VRF
        if vrf:  # WHY: skip filter if blank
            body["vrf"] = vrf  # WHY: propagate to SDK
        node = self._safe_input_fn("Node (node0/node1, Enter to skip): ", context="ospf_node")  # WHY: node
        if node:  # WHY: skip filter if blank
            body["node"] = node  # WHY: propagate to SDK
        port_id = self._select_port_optional(site_id, device_id)  # WHY: __getattr__ -> selection cluster
        if port_id:  # WHY: only add if operator picked one
            body["port_id"] = port_id  # WHY: propagate to SDK
        return body  # WHY: dict consumed by _run_and_export

    def show_ospf_database(self) -> None:
        """Menu 126: Show OSPF database on SSR/SRX gateway."""
        logging.info("Menu #126: Show OSPF Database")  # WHY: menu entry audit trail
        selection = self._select_site_and_device("show_ospf_database", "gateway")  # WHY: gateway-only
        if not selection:  # WHY: user cancelled / no picks
            return  # WHY: nothing to do without a device target
        site_id, device_id, _ = selection  # WHY: destructure IDs, ignore display name
        body = self._build_ospf_database_body()  # WHY: extract keeps this method at C<=5
        print("\n-> Fetching OSPF database...")  # WHY: operator progress feedback
        self._run_and_export(site_id, device_id, body, _OSPF_DATABASE_SPEC)  # WHY: dispatch + export

    def _build_ospf_database_body(self) -> dict[str, Any]:
        """Collect optional OSPF database filter inputs into a body dict."""
        body: dict[str, Any] = {}  # WHY: start empty; only add prompted filters
        vrf = self._safe_input_fn("VRF (Enter to skip): ", context="ospf_vrf")  # WHY: optional VRF
        if vrf:  # WHY: skip filter if blank
            body["vrf"] = vrf  # WHY: propagate to SDK
        node = self._safe_input_fn("Node (node0/node1, Enter to skip): ", context="ospf_node")  # WHY: node
        if node:  # WHY: skip filter if blank
            body["node"] = node  # WHY: propagate to SDK
        self_orig = self._safe_input_fn(  # WHY: optional self-originated LSA filter
            "Show self-originated only? (y/N): ",
            context="ospf_self_originate",  # WHY: context key wires into safe_input policy
        )
        if self_orig and self_orig.lower() == "y":  # WHY: normalize to bool for API
            body["self_originate"] = True  # WHY: SDK expects boolean flag
        return body  # WHY: dict consumed by _run_and_export

    def show_ospf_summary(self) -> None:
        """Menu 127: Show OSPF summary on SSR/SRX gateway."""
        logging.info("Menu #127: Show OSPF Summary")  # WHY: menu entry audit trail
        selection = self._select_site_and_device("show_ospf_summary", "gateway")  # WHY: gateway-only
        if not selection:  # WHY: user cancelled / no picks
            return  # WHY: nothing to do without a device target
        site_id, device_id, _ = selection  # WHY: destructure IDs, ignore display name
        body = self._build_vrf_node_body("ospf_vrf", "ospf_node")  # WHY: shared vrf+node prompt helper
        print("\n-> Fetching OSPF summary...")  # WHY: operator progress feedback
        self._run_and_export(site_id, device_id, body, _OSPF_SUMMARY_SPEC)  # WHY: dispatch + export

    def _build_vrf_node_body(self, vrf_ctx: str, node_ctx: str) -> dict[str, Any]:
        """Prompt for optional VRF + node and return a filter body dict."""
        body: dict[str, Any] = {}  # WHY: start empty; only add prompted filters
        vrf = self._safe_input_fn("VRF (Enter to skip): ", context=vrf_ctx)  # WHY: optional VRF
        if vrf:  # WHY: skip filter if blank
            body["vrf"] = vrf  # WHY: propagate to SDK
        node = self._safe_input_fn("Node (node0/node1, Enter to skip): ", context=node_ctx)  # WHY: node
        if node:  # WHY: skip filter if blank
            body["node"] = node  # WHY: propagate to SDK
        return body  # WHY: dict consumed by _run_and_export

    def _build_node_only_body(self, node_ctx: str) -> dict[str, Any]:
        """Prompt for optional node filter only (BGP/ARP/DOT1X/EVPN pattern)."""
        body: dict[str, Any] = {}  # WHY: start empty; only add prompted node
        node = self._safe_input_fn("Node (node0/node1, Enter to skip): ", context=node_ctx)  # WHY: node
        if node:  # WHY: skip filter if blank
            body["node"] = node  # WHY: propagate to SDK
        return body  # WHY: dict consumed by _run_and_export

    # ------------------------------------------------------------------
    # SSR / SRX DIAGNOSTIC / STREAMING COMMANDS
    # ------------------------------------------------------------------

    def resolve_dns(self) -> None:
        """Menu 135: Test DNS resolution on SSR gateway."""
        logging.info("Menu #135: Resolve DNS")  # WHY: menu entry audit trail
        selection = self._select_site_and_device("resolve_dns", "gateway")  # WHY: gateway-only
        if not selection:  # WHY: user cancelled / no picks
            return  # WHY: nothing to do without a device target
        site_id, device_id, _ = selection  # WHY: destructure IDs, ignore display name
        print("\n-> Testing DNS resolution on device...")  # WHY: operator progress feedback
        self._run_and_export(site_id, device_id, None, _DNS_RESOLUTION_SPEC)  # WHY: no body for this SDK

    def monitor_traffic(self) -> None:
        """Menu 136: Monitor traffic on switch/SRX port (streaming)."""
        logging.info("Menu #136: Monitor Traffic (streaming)")  # WHY: menu entry audit trail
        selection = self._select_site_and_device("monitor_traffic", "switch")  # WHY: switch/SRX only
        if not selection:  # WHY: user cancelled / no picks
            return  # WHY: nothing to do without a device target
        site_id, device_id, _ = selection  # WHY: destructure IDs, ignore display name
        port_id = self._select_port_from_device(site_id, device_id)  # WHY: __getattr__ -> selection cluster
        if not port_id:  # WHY: no port -> no traffic to sniff
            return  # WHY: abort without firing SDK call
        body, duration = self._build_monitor_traffic_body(port_id)  # WHY: extract keeps <=25 lines
        print(f"\n-> Monitoring traffic on port {port_id}...")  # WHY: operator progress feedback
        self._run_streaming_command(  # WHY: __getattr__ -> websocket cluster
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.monitorSiteDeviceTraffic,  # WHY: streaming SDK
            body,
            timeout_seconds=duration + 30,  # WHY: cushion for setup/teardown latency
        )

    def _build_monitor_traffic_body(self, port_id: str) -> tuple[dict[str, Any], int]:
        """Prompt for capture duration and build the monitor-traffic body."""
        duration_str = self._safe_input_fn(  # WHY: capture-window prompt
            "Duration in seconds (default: 60): ",
            default_value="60",  # WHY: sensible default matches mistapi guidance
            context="monitor_duration",  # WHY: context key wires into safe_input policy
        )
        try:
            duration = int(duration_str) if duration_str else 60  # WHY: parse operator input
        except ValueError:  # WHY: fall back to default on non-numeric input
            duration = 60  # WHY: match default_value above
        body: dict[str, Any] = {"port_id": port_id, "duration": duration}  # WHY: required SDK payload
        return body, duration  # WHY: caller needs duration for timeout budget

    def run_top(self) -> None:
        """Menu 137: Run top command on switch/SRX (streaming)."""
        logging.info("Menu #137: Run Top (streaming)")  # WHY: menu entry audit trail
        selection = self._select_site_and_device("run_top", "switch")  # WHY: switch/SRX only
        if not selection:  # WHY: user cancelled / no picks
            return  # WHY: nothing to do without a device target
        site_id, device_id, _ = selection  # WHY: destructure IDs, ignore display name
        print("\n-> Running top command...")  # WHY: operator progress feedback
        self._run_streaming_command(  # WHY: __getattr__ -> websocket cluster
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.runSiteSrxTopCommand,  # WHY: streaming SDK
            timeout_seconds=120,  # WHY: 2-minute cap matches operator patience
        )

    # ------------------------------------------------------------------
    # SHOW COMMANDS
    # ------------------------------------------------------------------

    def show_session(self) -> None:
        """Menu 128: Show sessions on SSR/SRX gateway."""
        logging.info("Menu #128: Show Sessions")  # WHY: menu entry audit trail
        selection = self._select_site_and_device("show_session", "gateway")  # WHY: gateway-only
        if not selection:  # WHY: user cancelled / no picks
            return  # WHY: nothing to do without a device target
        site_id, device_id, _ = selection  # WHY: destructure IDs, ignore display name
        body = self._build_session_body()  # WHY: extract keeps public method under 25 lines
        print("\n-> Fetching device sessions...")  # WHY: operator progress feedback
        self._run_and_export(site_id, device_id, body, _SESSION_SPEC)  # WHY: dispatch + export

    def _build_session_body(self) -> dict[str, Any]:
        """Prompt for optional service_name / session_id / node filters."""
        body: dict[str, Any] = {}  # WHY: start empty; only add prompted filters
        service = self._safe_input_fn(  # WHY: optional service filter
            "Service name filter (Enter to skip): ",
            context="session_service",  # WHY: context key wires into safe_input policy
        )
        if service:  # WHY: skip filter if blank
            body["service_name"] = service  # WHY: propagate to SDK
        session = self._safe_input_fn(  # WHY: optional session-id filter
            "Session ID filter (Enter to skip): ",
            context="session_id_filter",  # WHY: context key wires into safe_input policy
        )
        if session:  # WHY: skip filter if blank
            body["session_id"] = session  # WHY: propagate to SDK
        node = self._safe_input_fn(  # WHY: optional node filter
            "Node (node0/node1, Enter to skip): ",
            context="session_node",  # WHY: context key wires into safe_input policy
        )
        if node:  # WHY: skip filter if blank
            body["node"] = node  # WHY: propagate to SDK
        return body  # WHY: dict consumed by _run_and_export

    def show_service_path(self) -> None:
        """Menu 129: Show service path on SSR gateway."""
        logging.info("Menu #129: Show Service Path")  # WHY: menu entry audit trail
        selection = self._select_site_and_device("show_service_path", "gateway")  # WHY: gateway-only
        if not selection:  # WHY: user cancelled / no picks
            return  # WHY: nothing to do without a device target
        site_id, device_id, _ = selection  # WHY: destructure IDs, ignore display name
        body = self._build_service_path_body()  # WHY: extract keeps public method under 25 lines
        print("\n-> Fetching service path...")  # WHY: operator progress feedback
        self._run_and_export(site_id, device_id, body, _SERVICE_PATH_SPEC)  # WHY: dispatch + export

    def _build_service_path_body(self) -> dict[str, Any]:
        """Prompt for optional service_name and node filters."""
        body: dict[str, Any] = {}  # WHY: start empty; only add prompted filters
        service = self._safe_input_fn(  # WHY: optional service filter
            "Service name (Enter to skip): ",
            context="service_path_name",  # WHY: context key wires into safe_input policy
        )
        if service:  # WHY: skip filter if blank
            body["service_name"] = service  # WHY: propagate to SDK
        node = self._safe_input_fn(  # WHY: optional node filter
            "Node (node0/node1, Enter to skip): ",
            context="service_path_node",  # WHY: context key wires into safe_input policy
        )
        if node:  # WHY: skip filter if blank
            body["node"] = node  # WHY: propagate to SDK
        return body  # WHY: dict consumed by _run_and_export

    def show_bgp_summary(self) -> None:
        """Menu 130: Show BGP summary on switch or gateway."""
        logging.info("Menu #130: Show BGP Summary")  # WHY: menu entry audit trail
        selection = self._select_site_and_device("show_bgp_summary")  # WHY: any device type
        if not selection:  # WHY: user cancelled / no picks
            return  # WHY: nothing to do without a device target
        site_id, device_id, _ = selection  # WHY: destructure IDs, ignore display name
        body = self._build_node_only_body("bgp_node")  # WHY: shared node-only prompt helper
        print("\n-> Fetching BGP summary...")  # WHY: operator progress feedback
        self._run_and_export(site_id, device_id, body, _BGP_SUMMARY_SPEC)  # WHY: dispatch + export

    def show_arp_table(self) -> None:
        """Menu 131: Show ARP table on switch or gateway."""
        logging.info("Menu #131: Show ARP Table")  # WHY: menu entry audit trail
        selection = self._select_site_and_device("show_arp_table")  # WHY: any device type
        if not selection:  # WHY: user cancelled / no picks
            return  # WHY: nothing to do without a device target
        site_id, device_id, _ = selection  # WHY: destructure IDs, ignore display name
        body = self._build_node_only_body("arp_node")  # WHY: shared node-only prompt helper
        print("\n-> Fetching ARP table...")  # WHY: operator progress feedback
        self._run_and_export(site_id, device_id, body, _ARP_TABLE_SPEC)  # WHY: dispatch + export

    def show_dhcp_leases(self) -> None:
        """Menu 132: Show DHCP leases on switch or gateway."""
        logging.info("Menu #132: Show DHCP Leases")  # WHY: menu entry audit trail
        selection = self._select_site_and_device("show_dhcp_leases")  # WHY: any device type
        if not selection:  # WHY: user cancelled / no picks
            return  # WHY: nothing to do without a device target
        site_id, device_id, _ = selection  # WHY: destructure IDs, ignore display name
        body = self._build_dhcp_leases_body(site_id, device_id)  # WHY: extract keeps <=25 lines
        print("\n-> Fetching DHCP leases...")  # WHY: operator progress feedback
        self._run_and_export(site_id, device_id, body, _DHCP_LEASES_SPEC)  # WHY: dispatch + export

    def _build_dhcp_leases_body(self, site_id: str, device_id: str) -> dict[str, Any]:
        """Prompt for optional network + node filters."""
        body: dict[str, Any] = {}  # WHY: start empty; only add prompted filters
        network = self._select_network_from_device(site_id, device_id)  # WHY: __getattr__ -> selection
        if network:  # WHY: only add if operator picked one
            body["network"] = network  # WHY: propagate to SDK
        node = self._safe_input_fn("Node (node0/node1, Enter to skip): ", context="dhcp_node")  # WHY: node
        if node:  # WHY: skip filter if blank
            body["node"] = node  # WHY: propagate to SDK
        return body  # WHY: dict consumed by _run_and_export

    def show_dot1x(self) -> None:
        """Menu 133: Show 802.1X table on switch."""
        logging.info("Menu #133: Show 802.1X Table")  # WHY: menu entry audit trail
        selection = self._select_site_and_device("show_dot1x", "switch")  # WHY: switch-only
        if not selection:  # WHY: user cancelled / no picks
            return  # WHY: nothing to do without a device target
        site_id, device_id, _ = selection  # WHY: destructure IDs, ignore display name
        body = self._build_node_only_body("dot1x_node")  # WHY: shared node-only prompt helper
        print("\n-> Fetching 802.1X table...")  # WHY: operator progress feedback
        self._run_and_export(site_id, device_id, body, _DOT1X_SPEC)  # WHY: dispatch + export

    def show_evpn_database(self) -> None:
        """Menu 134: Show EVPN database on switch or gateway."""
        logging.info("Menu #134: Show EVPN Database")  # WHY: menu entry audit trail
        selection = self._select_site_and_device("show_evpn_database")  # WHY: any device type
        if not selection:  # WHY: user cancelled / no picks
            return  # WHY: nothing to do without a device target
        site_id, device_id, _ = selection  # WHY: destructure IDs, ignore display name
        body = self._build_node_only_body("evpn_node")  # WHY: shared node-only prompt helper
        print("\n-> Fetching EVPN database...")  # WHY: operator progress feedback
        self._run_and_export(site_id, device_id, body, _EVPN_DATABASE_SPEC)  # WHY: dispatch + export

    # ------------------------------------------------------------------
    # HARDWARE DIAGNOSTIC
    # ------------------------------------------------------------------

    def cable_test(self) -> None:
        """Menu 141: Run cable test on switch port."""
        logging.info("Menu #141: Cable Test")  # WHY: menu entry audit trail
        selection = self._select_site_and_device("cable_test", "switch")  # WHY: switch-only
        if not selection:  # WHY: user cancelled / no picks
            return  # WHY: nothing to do without a device target
        site_id, device_id, _ = selection  # WHY: destructure IDs, ignore display name
        port_id = self._select_port_from_device(site_id, device_id)  # WHY: __getattr__ -> selection cluster
        if not port_id:  # WHY: cable test needs a physical port target
            return  # WHY: abort without firing SDK call
        body: dict[str, Any] = {"port": port_id}  # WHY: SDK expects 'port' key (not port_id)
        print(f"\n-> Running cable test on port {port_id}...")  # WHY: operator progress feedback
        self._run_and_export(site_id, device_id, body, _CABLE_TEST_SPEC)  # WHY: dispatch + export
