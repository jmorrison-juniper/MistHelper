"""Build SDK-parity utility trigger bodies."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from src.websocket_streams.intake.start_request.models import StartRequest


class CommandBodyBuilder:
    """Build command and screen request bodies."""

    _COPY_FIELDS = {
        "ap_arp": ("node",),
        "clear_sessions": ("node", "service_name", "service_ids", "vrf"),
        "dhcp_release": ("macs", "network", "node", "port_id"),
        "dhcp_show": ("network", "node"),
        "mac_table": ("mac_address", "port_id", "vlan_id"),
        "ospf_database": ("node", "self_originate", "vrf"),
        "ospf_interfaces": ("node", "port_id", "vrf"),
        "ospf_neighbors": ("node", "port_id", "vrf", "neighbor"),
        "ospf_summary": ("node", "vrf"),
        "ping": ("count", "host", "node", "size", "vrf"),
        "routes": ("node", "prefix", "protocol", "route_type", "vrf"),
        "service_path": ("node", "service_name"),
        "sessions": ("node", "service_name", "service_ids"),
        "traceroute": ("host", "protocol", "port"),
    }

    def build(self, kind: str, params: Mapping[str, object]) -> dict[str, object] | None:
        """Return one command body."""
        if kind == "none":
            return None
        names = self._COPY_FIELDS.get(kind)
        if names is not None:
            return self._copy(params, names)
        return self._special(kind, params)

    def _special(self, kind: str, params: Mapping[str, object]) -> dict[str, object]:
        """Return one non-copy command body."""
        builders: dict[str, Callable[[], dict[str, object]]] = {
            "bgp": lambda: {"protocol": "bgp"},
            "cable": lambda: {"port": params["port_id"]},
            "junos_arp": lambda: {"duration": 1, "interval": 1, **self._copy(params, ("ip", "vrf", "port_id"))},
            "monitor": lambda: {"duration": 60, **({"port": params["port_id"]} if "port_id" in params else {})},
            "ports": lambda: {"ports": params["port_ids"]},
        }
        return builders[kind]()

    @staticmethod
    def _copy(params: Mapping[str, object], names: tuple[str, ...]) -> dict[str, object]:
        """Copy present parameters in SDK order."""
        return {name: params[name] for name in names if name in params}


class CaptureBodyBuilder:
    """Build packet capture request bodies."""

    def build(self, kind: str, request: StartRequest) -> dict[str, object]:
        """Return one packet capture body."""
        body = self._base(request.parameters)
        builders: dict[str, Callable[[], dict[str, object]]] = {
            "ap_wired_pcap": lambda: {**body, "type": "wired", "format": "stream"},
            "ap_wireless_pcap": lambda: self._wireless(body, request),
            "switch_pcap": lambda: self._device(body, request, "switches", "switch", None),
            "ssr_pcap": lambda: self._device(body, request, "gateways", "gateway", False),
            "gateway_pcap": lambda: self._device(body, request, "gateways", "gateway", None),
            "mxedge_pcap": lambda: self._mxedge(body, request),
        }
        return builders[kind]()

    @staticmethod
    def _base(params: Mapping[str, object]) -> dict[str, object]:
        """Return shared capture fields."""
        body: dict[str, object] = {
            "duration": 60,
            "max_pkt_len": params.get("max_pkt_len", 512),
            "num_packets": params.get("num_packets", 1024),
        }
        if "tcpdump_expression" in params:
            body["tcpdump_expression"] = params["tcpdump_expression"]
        return body

    @staticmethod
    def _wireless(body: dict[str, object], request: StartRequest) -> dict[str, object]:
        """Return a wireless AP capture body."""
        params = request.parameters
        result = {"band": params["band"], **body, "type": "radiotap", "format": "stream"}
        if "ssid" in params:
            result["ssid"] = params["ssid"]
        result["ap_mac"] = params.get("ap_mac", request.target("device_id").split("-")[-1])
        return result

    @staticmethod
    def _device(
        body: dict[str, object], request: StartRequest, key: str, device_type: str, raw: bool | None
    ) -> dict[str, object]:
        """Return a switch or gateway capture body."""
        ports: dict[str, object] = (
            {str(name): {} for name in values}
            if isinstance(values := request.parameters.get("port_ids", []), list)
            else {}
        )
        device = request.target("device_id").split("-")[-1]
        result = {**body, key: {device: {"ports": ports}}, "type": device_type, "format": "stream"}
        if raw is not None:
            result["raw"] = raw
        return result

    @staticmethod
    def _mxedge(body: dict[str, object], request: StartRequest) -> dict[str, object]:
        """Return a Mist Edge capture body."""
        values = request.parameters.get("interfaces", [])
        names = values if isinstance(values, list) else []
        interfaces: dict[str, object] = {str(name): {} for name in names}
        mxedge = request.target("mxedge_id")
        return {**body, "format": "stream", "mxedges": {mxedge: {"interfaces": interfaces}}, "type": "mxedge"}
