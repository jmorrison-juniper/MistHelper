"""Build REST triggers for WebSocket device utilities.

Why:
    Issue #3671 replaces Mist SDK WebSocket paths with owned stream code.
    The utility runner still needs the same REST trigger requests that the
    Mist SDK sends today.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # The table logs lookups without recording secrets or output.
from collections.abc import Callable, Mapping  # The row data uses typed callables and mappings.
from dataclasses import dataclass  # The trigger records are immutable dataclasses.
from types import MappingProxyType  # Mapping proxies keep class data read-only.

from src.websocket_streams.intake.fields import StreamRequestError  # Bad keys use the request error contract.
from src.websocket_streams.intake.start_request import StartRequest  # The table reads checked targets and parameters.

logger = logging.getLogger(__name__)  # Keep trigger table log records under this module name.


@dataclass(frozen=True, slots=True)
class UtilityTiming:
    """The timing limits for one utility stream.

    Attributes:
        first_output_seconds: The wait for the first stream payload.
        quiet_seconds: The quiet time after one payload.
        total_seconds: The total utility run time.
    """

    first_output_seconds: float  # The runner waits this long for the first payload.
    quiet_seconds: float  # The runner ends after this much quiet time.
    total_seconds: float  # The runner ends after this total time.


@dataclass(frozen=True, slots=True)
class UtilityListen:
    """The stream channel that receives the trigger output.

    Attributes:
        channel: The stream type for the runner.
        channel_path: The exact channel path to subscribe.
        timing: The timing limits for this stream.
    """

    channel: str  # The runner uses this value to choose the filter.
    channel_path: str  # The stream client subscribes to this path.
    timing: UtilityTiming  # The runner applies these limits.


@dataclass(frozen=True, slots=True)
class UtilityRequest:
    """The REST trigger request for one device utility.

    Attributes:
        key: The utility catalog key.
        method: The HTTP method for the trigger.
        path: The REST path with checked identifiers filled in.
        body: The SDK request body. Top command sends no body.
        listen: The stream channel information.
    """

    key: str  # The runner records which catalog entry started the request.
    method: str  # The SDK uses POST for each utility trigger.
    path: str  # The API session receives this REST path.
    body: dict[str, object] | None  # The SDK top command sends no body.
    listen: UtilityListen  # The runner opens this stream before the trigger.


class UtilityTriggerTable:
    """Hold the REST trigger definitions for device utility streams."""

    _FIRST_OUTPUT_SECONDS = 30.0  # The SDK first message timer is 30 seconds.
    _DEFAULT_TOTAL_SECONDS = 60.0  # The SDK maximum duration is 60 seconds.
    _SHELL_TIMING = UtilityTiming(30.0, 5.0, 60.0)  # Shell trigger metadata is fixed.
    _CHANNEL_PATHS = MappingProxyType(
        {
            "cmd": "/sites/{site_id}/devices/{device_id}/cmd",
            "site_pcaps": "/sites/{site_id}/pcaps",
            "org_pcaps": "/orgs/{org_id}/pcaps",
            "url": "",
        }
    )  # The stream paths match the Mist SDK websocket classes.
    _ROWS = MappingProxyType(
        {
            "ap.ping": ("site_device", "/ping", "ping", "cmd", 3.0),
            "ap.traceroute": ("site_device", "/traceroute", "traceroute", "cmd", 10.0),
            "ap.retrieveArpTable": ("site_device", "/arp", "ap_arp", "cmd", 1.0),
            "ap.remotePcapWired": ("site_pcap", "/pcaps/capture", "ap_wired_pcap", "site_pcaps", 10.0),
            "ap.remotePcapWireless": ("site_pcap", "/pcaps/capture", "ap_wireless_pcap", "site_pcaps", 10.0),
            "ex.retrieveArpTable": ("site_device", "/show_arp", "junos_arp", "cmd", 1.0),
            "ex.retrieveBgpSummary": ("site_device", "/show_bgp_summary", "bgp", "cmd", 5.0),
            "ex.retrieveDhcpLeases": ("site_device", "/show_dhcp_leases", "dhcp_show", "cmd", 15.0),
            "ex.releaseDhcpLeases": ("site_device", "/release_dhcp_leases", "dhcp_release", "cmd", 5.0),
            "ex.retrieveMacTable": ("site_device", "/show_mac_table", "mac_table", "cmd", 5.0),
            "ex.bouncePort": ("site_device", "/bounce_port", "ports", "cmd", 5.0),
            "ex.cableTest": ("site_device", "/cable_test", "cable", "cmd", 10.0),
            "ex.remotePcap": ("site_pcap", "/pcaps/capture", "switch_pcap", "site_pcaps", 10.0),
            "ex.monitorTraffic": ("site_device", "/monitor_traffic", "monitor", "url", 30.0),
            "ex.ping": ("site_device", "/ping", "ping", "cmd", 3.0),
            "ex.topCommand": ("site_device", "/run_top", "none", "url", 10.0),
            "ex.traceroute": ("site_device", "/traceroute", "traceroute", "cmd", 10.0),
            "srx.retrieveArpTable": ("site_device", "/show_arp", "junos_arp", "cmd", 1.0),
            "srx.retrieveBgpSummary": ("site_device", "/show_bgp_summary", "bgp", "cmd", 5.0),
            "srx.releaseDhcpLeases": ("site_device", "/release_dhcp_leases", "dhcp_release", "cmd", 5.0),
            "srx.retrieveDhcpLeases": ("site_device", "/show_dhcp_leases", "dhcp_show", "cmd", 15.0),
            "srx.retrieveOspfDatabase": ("site_device", "/show_ospf_database", "ospf_database", "cmd", 5.0),
            "srx.retrieveOspfNeighbors": ("site_device", "/show_ospf_neighbors", "ospf_neighbors", "cmd", 5.0),
            "srx.retrieveOspfInterfaces": ("site_device", "/show_ospf_interfaces", "ospf_interfaces", "cmd", 5.0),
            "srx.retrieveOspfSummary": ("site_device", "/show_ospf_summary", "ospf_summary", "cmd", 5.0),
            "srx.bouncePort": ("site_device", "/bounce_port", "ports", "cmd", 5.0),
            "srx.remotePcap": ("site_pcap", "/pcaps/capture", "gateway_pcap", "site_pcaps", 10.0),
            "srx.retrieveRoutes": ("site_device", "/show_route", "routes", "cmd", 2.0),
            "srx.retrieveSessions": ("site_device", "/show_session", "sessions", "cmd", 2.0),
            "srx.clearSessions": ("site_device", "/clear_session", "clear_sessions", "cmd", 2.0),
            "srx.monitorTraffic": ("site_device", "/monitor_traffic", "monitor", "url", 30.0),
            "srx.ping": ("site_device", "/ping", "ping", "cmd", 3.0),
            "srx.topCommand": ("site_device", "/run_top", "none", "url", 10.0),
            "srx.traceroute": ("site_device", "/traceroute", "traceroute", "cmd", 10.0),
            "ssr.retrieveArpTable": ("site_device", "/arp", "ap_arp", "cmd", 1.0),
            "ssr.retrieveBgpSummary": ("site_device", "/show_bgp_summary", "bgp", "cmd", 5.0),
            "ssr.releaseDhcpLeases": ("site_device", "/release_dhcp_leases", "dhcp_release", "cmd", 5.0),
            "ssr.retrieveDhcpLeases": ("site_device", "/show_dhcp_leases", "dhcp_show", "cmd", 15.0),
            "ssr.retrieveOspfDatabase": ("site_device", "/show_ospf_database", "ospf_database", "cmd", 5.0),
            "ssr.retrieveOspfNeighbors": ("site_device", "/show_ospf_neighbors", "ospf_neighbors", "cmd", 5.0),
            "ssr.retrieveOspfInterfaces": ("site_device", "/show_ospf_interfaces", "ospf_interfaces", "cmd", 5.0),
            "ssr.retrieveOspfSummary": ("site_device", "/show_ospf_summary", "ospf_summary", "cmd", 5.0),
            "ssr.bouncePort": ("site_device", "/bounce_port", "ports", "cmd", 5.0),
            "ssr.remotePcap": ("site_pcap", "/pcaps/capture", "ssr_pcap", "site_pcaps", 10.0),
            "ssr.retrieveRoutes": ("site_device", "/show_route", "routes", "cmd", 2.0),
            "ssr.showServicePath": ("site_device", "/show_service_path", "service_path", "cmd", 5.0),
            "ssr.retrieveSessions": ("site_device", "/show_session", "sessions", "cmd", 2.0),
            "ssr.clearSessions": ("site_device", "/clear_session", "clear_sessions", "cmd", 2.0),
            "ssr.ping": ("site_device", "/ping", "ping", "cmd", 3.0),
            "ssr.traceroute": ("site_device", "/traceroute", "traceroute", "cmd", 10.0),
            "mxedge.orgRemotePcap": ("org_pcap", "/pcaps/capture", "mxedge_pcap", "org_pcaps", 10.0),
            "mxedge.siteRemotePcap": ("site_pcap", "/pcaps/capture", "mxedge_pcap", "site_pcaps", 10.0),
        }
    )  # The row table mirrors the Mist SDK utility trigger set.

    def keys(self) -> tuple[str, ...]:
        """Return the catalog keys in table order.

        Returns:
            The supported utility keys.
        """
        logger.info("Reading WebSocket utility trigger keys")  # Log before reading class data.
        keys = tuple(self._ROWS)  # Freeze the mapping keys for the caller.
        logger.debug("Read %s WebSocket utility trigger keys", len(keys))  # Log the measured key count.
        return keys  # The caller cannot change class data.

    def request_for(self, request: StartRequest) -> UtilityRequest:
        """Return the REST trigger request for one checked start request.

        Args:
            request: The checked utility start request.

        Returns:
            The utility trigger request.

        Raises:
            StreamRequestError: The key is not in the trigger table.
        """
        logger.info("Building WebSocket utility trigger request for key %s", request.key)  # Log before lookup.
        row = self._ROWS.get(request.key)  # Read the trigger row for this key.
        if row is None:  # Unknown keys cannot safely build a Mist request.
            raise StreamRequestError("bad_request", "The utility trigger key is not supported.")  # Refuse bad keys.
        utility = self._build_request(request, row)  # Build the complete request.
        logger.debug("Built WebSocket utility trigger request for key %s", request.key)  # Log completion.
        return utility  # The runner sends this request after subscribe.

    def shell_request(self, site_id: str, device_id: str) -> UtilityRequest:
        """Return the shell REST trigger request.

        Args:
            site_id: The site identifier.
            device_id: The device identifier.

        Returns:
            The shell trigger request.
        """
        logger.info("Building WebSocket shell trigger request")  # Log before shell path creation.
        path = f"/api/v1/sites/{site_id}/devices/{device_id}/shell"  # Match the SDK shell endpoint.
        listen = UtilityListen("url", "", self._SHELL_TIMING)  # Shell answers with a URL, not a stream channel.
        logger.debug("Built WebSocket shell trigger request")  # Log completion without identifiers.
        return UtilityRequest("shell", "POST", path, {}, listen)  # Shell sends an empty body.

    def _build_request(self, request: StartRequest, row: tuple[str, str, str, str, float]) -> UtilityRequest:
        """Build one utility request from one table row.

        Args:
            request: The checked utility start request.
            row: The row metadata for the key.

        Returns:
            The complete utility request.
        """
        scope, suffix, body_kind, channel, quiet = row  # Unpack class row data.
        path = self._path(scope, suffix, request)  # Fill checked identifiers into the path.
        body = self._body(body_kind, request)  # Build the SDK body for this key.
        listen = self._listen(channel, quiet, request, body)  # Build stream metadata for the runner.
        return UtilityRequest(request.key, "POST", path, body, listen)  # Return one immutable request.

    def _path(self, scope: str, suffix: str, request: StartRequest) -> str:
        """Return the REST path for one scope.

        Args:
            scope: The table scope value.
            suffix: The API suffix for the trigger.
            request: The checked utility start request.

        Returns:
            The absolute Mist API path.
        """
        if scope == "org_pcap":  # Organization captures use an organization path.
            return f"/api/v1/orgs/{request.target('org_id')}{suffix}"  # Fill the checked organization.
        if scope == "site_pcap":  # Site captures do not include the device in the path.
            return f"/api/v1/sites/{request.target('site_id')}{suffix}"  # Fill the checked site.
        site_id = request.target("site_id")  # Use the checked site identifier.
        device_id = request.target("device_id")  # Use the checked device identifier.
        return f"/api/v1/sites/{site_id}/devices/{device_id}{suffix}"  # Fill the checked device path.

    def _listen(
        self, channel: str, quiet: float, request: StartRequest, body: dict[str, object] | None
    ) -> UtilityListen:
        """Return stream metadata for one request.

        Args:
            channel: The logical stream channel.
            quiet: The SDK quiet value.
            request: The checked utility start request.
            body: The trigger body.

        Returns:
            The listen information.
        """
        quiet_seconds = max(5.0, quiet)  # Slow device output needs at least five seconds.
        total_seconds = self._total_seconds(channel, body)  # Captures run for their duration plus ten seconds.
        timing = UtilityTiming(self._FIRST_OUTPUT_SECONDS, quiet_seconds, total_seconds)  # Build timing metadata.
        path = self._CHANNEL_PATHS[channel].format_map(
            {
                "site_id": request.target("site_id"),
                "device_id": request.target("device_id"),
                "org_id": request.target("org_id"),
            }
        )  # Fill the subscribe channel path.
        return UtilityListen(channel, path, timing)  # Return the immutable listen record.

    def _total_seconds(self, channel: str, body: dict[str, object] | None) -> float:
        """Return the total time for one request.

        Args:
            channel: The logical stream channel.
            body: The trigger body.

        Returns:
            The total time in seconds.
        """
        if channel not in {"site_pcaps", "org_pcaps"} or body is None:  # Only captures derive total time from body.
            return self._DEFAULT_TOTAL_SECONDS  # Commands and screens use the SDK maximum duration.
        duration = body.get("duration", self._DEFAULT_TOTAL_SECONDS)  # Capture bodies carry the duration.
        if isinstance(duration, int):  # Capture duration is an integer in SDK bodies.
            return float(duration) + 10.0  # Add capture slack.
        return self._DEFAULT_TOTAL_SECONDS  # Fall back to the command total.

    def _body(self, kind: str, request: StartRequest) -> dict[str, object] | None:
        """Return the SDK request body for one body kind.

        Args:
            kind: The row body kind.
            request: The checked utility start request.

        Returns:
            The SDK body, or None when the SDK sends no body.
        """
        params = request.parameters  # Use checked parameter values only.
        if kind == "none":  # The SDK top command sends no request body.
            return None  # Preserve the SDK request shape.
        if kind.endswith("_pcap"):  # Packet captures share duration and stream fields.
            return self._pcap_body(kind, request)  # Build the capture-specific body.
        return self._command_body(kind, params)  # Build command and screen bodies.

    def _command_body(self, kind: str, params: Mapping[str, object]) -> dict[str, object]:
        """Return a command or screen trigger body.

        Args:
            kind: The row body kind.
            params: The checked utility parameters.

        Returns:
            The SDK body.
        """
        builders: Mapping[str, Callable[[], dict[str, object]]] = {
            "ap_arp": lambda: self._copy(params, ("node",)),
            "bgp": lambda: {"protocol": "bgp"},
            "cable": lambda: {"port": params["port_id"]},
            "clear_sessions": lambda: self._copy(params, ("node", "service_name", "service_ids", "vrf")),
            "dhcp_release": lambda: self._copy(params, ("macs", "network", "node", "port_id")),
            "dhcp_show": lambda: self._copy(params, ("network", "node")),
            "junos_arp": lambda: {"duration": 1, "interval": 1, **self._copy(params, ("ip", "vrf", "port_id"))},
            "mac_table": lambda: self._copy(params, ("mac_address", "port_id", "vlan_id")),
            "monitor": lambda: {"duration": 60, **({"port": params["port_id"]} if "port_id" in params else {})},
            "ospf_database": lambda: self._copy(params, ("node", "self_originate", "vrf")),
            "ospf_interfaces": lambda: self._copy(params, ("node", "port_id", "vrf")),
            "ospf_neighbors": lambda: self._copy(params, ("node", "port_id", "vrf", "neighbor")),
            "ospf_summary": lambda: self._copy(params, ("node", "vrf")),
            "ping": lambda: self._copy(params, ("count", "host", "node", "size", "vrf")),
            "ports": lambda: {"ports": params["port_ids"]},
            "routes": lambda: self._copy(params, ("node", "prefix", "protocol", "route_type", "vrf")),
            "service_path": lambda: self._copy(params, ("node", "service_name")),
            "sessions": lambda: self._copy(params, ("node", "service_name", "service_ids")),
            "traceroute": lambda: self._copy(params, ("host", "protocol", "port")),
        }  # Each small builder mirrors one SDK body shape.
        return builders[kind]()  # The row table controls the body kind.

    def _pcap_body(self, kind: str, request: StartRequest) -> dict[str, object]:
        """Return a packet capture body.

        Args:
            kind: The row body kind.
            request: The checked utility start request.

        Returns:
            The SDK packet capture body.
        """
        params = request.parameters  # Capture parameters come from the checked request.
        body = self._pcap_base(params)  # Add shared capture values.
        if kind == "ap_wired_pcap":  # Wired AP capture has no device map.
            return {**body, "type": "wired", "format": "stream"}  # Match the SDK body.
        if kind == "ap_wireless_pcap":  # Wireless AP capture adds band and AP values.
            return self._ap_wireless_body(body, params, request)  # Build the AP wireless body.
        if kind == "switch_pcap":  # EX capture uses the switches field.
            return self._device_pcap_body(body, request, "switches", "switch", raw=None)  # Build switch capture.
        if kind == "ssr_pcap":  # SSR capture adds raw=false.
            return self._device_pcap_body(body, request, "gateways", "gateway", raw=False)  # Build SSR capture.
        if kind == "gateway_pcap":  # SRX capture uses the gateways field.
            return self._device_pcap_body(body, request, "gateways", "gateway", raw=None)  # Build SRX capture.
        return self._mxedge_pcap_body(body, request)  # Mist Edge captures use interfaces.

    def _pcap_base(self, params: Mapping[str, object]) -> dict[str, object]:
        """Return shared packet capture fields.

        Args:
            params: The checked utility parameters.

        Returns:
            The shared capture body fields.
        """
        body: dict[str, object] = {
            "duration": 60,
            "max_pkt_len": params.get("max_pkt_len", 512),
            "num_packets": params.get("num_packets", 1024),
        }  # Captures force a 60 second duration.
        if "tcpdump_expression" in params:  # Optional capture filter is omitted when empty.
            body["tcpdump_expression"] = params["tcpdump_expression"]  # Preserve the checked filter.
        return body  # The caller adds the capture type.

    def _ap_wireless_body(
        self, body: dict[str, object], params: Mapping[str, object], request: StartRequest
    ) -> dict[str, object]:
        """Return a wireless AP capture body.

        Args:
            body: The shared packet capture body.
            params: The checked utility parameters.
            request: The checked utility start request.

        Returns:
            The wireless AP capture body.
        """
        result = {"band": params["band"], **body, "type": "radiotap", "format": "stream"}  # Start with fixed fields.
        if "ssid" in params:  # The SDK omits an empty SSID.
            result["ssid"] = params["ssid"]  # Preserve the checked SSID.
        result["ap_mac"] = params.get("ap_mac", request.target("device_id").split("-")[-1])  # Use the SDK default.
        return result  # The caller compares this body to the SDK.

    def _device_pcap_body(
        self, body: dict[str, object], request: StartRequest, key: str, device_type: str, raw: bool | None
    ) -> dict[str, object]:
        """Return a switch or gateway capture body.

        Args:
            body: The shared packet capture body.
            request: The checked utility start request.
            key: The SDK device map key.
            device_type: The SDK capture type.
            raw: The optional raw flag.

        Returns:
            The switch or gateway capture body.
        """
        ports = self._ports(request.parameters.get("port_ids", []))  # Build the port map from checked values.
        device = request.target("device_id").split("-")[-1]  # The SDK keeps only the device MAC suffix.
        result = {**body, key: {device: {"ports": ports}}, "type": device_type, "format": "stream"}  # Match SDK shape.
        if raw is not None:  # SSR capture sets raw false.
            result["raw"] = raw  # Preserve the SDK flag.
        return result  # The caller sends this body to Mist.

    def _mxedge_pcap_body(self, body: dict[str, object], request: StartRequest) -> dict[str, object]:
        """Return a Mist Edge capture body.

        Args:
            body: The shared packet capture body.
            request: The checked utility start request.

        Returns:
            The Mist Edge capture body.
        """
        interfaces = self._ports(request.parameters.get("interfaces", []))  # Build the interface map.
        mxedge = request.target("mxedge_id")  # Mist Edge captures use the full identifier.
        return {
            **body,
            "format": "stream",
            "mxedges": {mxedge: {"interfaces": interfaces}},
            "type": "mxedge",
        }  # Match SDK.

    @staticmethod
    def _ports(values: object) -> dict[str, object]:
        """Return a port or interface map for packet captures.

        Args:
            values: The checked list of port names.

        Returns:
            The SDK port map.
        """
        names = values if isinstance(values, list) else []  # Bad shapes are impossible after checks.
        return {str(name): {} for name in names}  # The portal does not set per-port filters.

    @staticmethod
    def _copy(params: Mapping[str, object], names: tuple[str, ...]) -> dict[str, object]:
        """Copy present parameters in SDK order.

        Args:
            params: The checked utility parameters.
            names: The parameter names in SDK body order.

        Returns:
            A request body that holds only present values.
        """
        return {name: params[name] for name in names if name in params}  # Omit empty optional values.
