"""Define the SDK-parity utility trigger rows."""

from __future__ import annotations

from types import MappingProxyType

from src.mist.realtime.websocket_streams.live.runners.utility.triggers.models import UtilityTiming


class UtilityTriggerDefinitions:
    """Provide immutable utility trigger metadata."""

    FIRST_OUTPUT_SECONDS = 30.0
    DEFAULT_TOTAL_SECONDS = 60.0
    _SHELL_TIMING = UtilityTiming(30.0, 5.0, 60.0)
    _CHANNEL_PATHS = MappingProxyType(
        {
            "cmd": "/sites/{site_id}/devices/{device_id}/cmd",
            "site_pcaps": "/sites/{site_id}/pcaps",
            "org_pcaps": "/orgs/{org_id}/pcaps",
            "url": "",
        }
    )
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
    )

    def keys(self) -> tuple[str, ...]:
        """Return trigger keys in SDK catalog order."""
        return tuple(self._ROWS)

    def row(self, key: str) -> tuple[str, str, str, str, float] | None:
        """Return one trigger row."""
        return self._ROWS.get(key)

    def channel_path(self, channel: str) -> str:
        """Return one stream channel path template."""
        return self._CHANNEL_PATHS[channel]

    def shell_timing(self) -> UtilityTiming:
        """Return the fixed shell timing record."""
        return self._SHELL_TIMING
