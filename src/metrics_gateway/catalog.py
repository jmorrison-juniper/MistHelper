"""Metric definitions for the Mist metrics gateway.

Why:
    A monitoring system polls a target and compares one number against one
    threshold. Mist Cloud publishes its health through a REST API instead, so a
    monitoring system cannot read it. This package copies the Mist readings into
    a local cache and serves that cache to the monitoring system.

    This module holds the definition of every reading the gateway serves. One
    definition names the Prometheus metric, the help text, the metric kind, the
    scope, and the SNMP column number. Both output paths read the same
    definitions, so the Prometheus endpoint and the SNMP responder can never
    disagree about a name or a meaning.

    The definitions carry the object set of `MISTLAB-MIB` from
    `tmunzer/mist_snmp_gateway`, which is MIT licensed. The OID layout is new.
    That upstream MIB assigns the enterprise OID `.1.3.6.1.4.1.65535`, which is
    not a registered Private Enterprise Number, and its own README warns that
    the number can collide with another product. This gateway therefore takes no
    fixed enterprise number. The operator names the base OID in `snmpd.conf`, and
    this module numbers only the columns below that base.

    The upstream MIB holds one table for access points and a second table for
    switches. This module holds one device table instead, because
    `listSiteDevicesStats` returns every device type from one call and a shared
    table also reports the gateway, which the upstream reports nowhere.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum

logger = logging.getLogger(__name__)


class MetricKind(StrEnum):
    """The Prometheus type of a reading."""

    GAUGE = "gauge"  # A value that rises and falls, such as a client count.
    COUNTER = "counter"  # A value that only rises, such as a byte count.
    INFO = "info"  # A constant 1 that carries its facts in the labels.


class MetricScope(StrEnum):
    """The Mist object that a reading describes."""

    ORG = "org"  # One reading for the whole organization.
    SITE = "site"  # One reading for each site.
    DEVICE = "device"  # One reading for each access point, switch, or gateway.
    SLE = "sle"  # One reading for each service level expectation of the organization.


# WHY: `snmpwalk` reads a table in OID order, so each scope needs its own subtree
# number. These four numbers follow the upstream shape, where the organization
# came first and the sites came second. The SLE table is new, because the
# upstream flattened the SLE readings into 18 organization scalars, and a flat
# list cannot grow when Mist adds a service level expectation.
SUBTREE_BY_SCOPE: dict[MetricScope, int] = {
    MetricScope.ORG: 1,  # Scalars. Each one answers at `<base>.1.<column>.0`.
    MetricScope.SITE: 2,  # A table. Each cell answers at `<base>.2.1.<column>.<row>`.
    MetricScope.DEVICE: 3,  # A table, holding the access points, the switches, and the gateways.
    MetricScope.SLE: 4,  # A table, holding one row for each service level expectation.
}

# WHY: SNMP carries a whole number only. A ratio of 0.97 would arrive as 0 and
# every alarm built on it would stay silent. A scale of 10000 sends 9700, which
# holds four decimal places, and the help text of each scaled reading names the
# unit. Prometheus ignores the scale and reports the true value.
RATIO_SNMP_SCALE = 10000  # Ten-thousandths, so a ratio keeps four decimal places.
SECONDS_SNMP_SCALE = 1000  # Milliseconds, so a duration below one second is still visible.

# WHY: A Prometheus label carries the identity of a table row, but SNMP has no
# label. An SNMP table therefore needs a column that repeats the row identity,
# or a poller cannot tell which site row 4 describes. The number sits above every
# data column, so the identity column walks after the readings.
ROW_IDENTITY_COLUMN = 99


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    """One reading that the gateway serves.

    Attributes:
        name: The Prometheus metric name. It also names the SNMP column.
        help_text: One sentence that tells a NOC engineer what the number means.
        kind: The Prometheus type.
        scope: The Mist object the reading describes.
        column: The SNMP column number below the subtree of the scope.
        source: The dotted path into the Mist reading. It is empty when the
            collector derives the value instead of copying it.
        snmp_scale: The factor the SNMP responder multiplies the value by before
            it rounds. SNMP carries whole numbers only, so a ratio of 0.97 would
            arrive as 0. A scale of 10000 sends 9700 instead, and the help text
            names the unit. Prometheus ignores this factor and reports the true
            value.
    """

    name: str
    help_text: str
    kind: MetricKind
    scope: MetricScope
    column: int
    source: str = ""
    snmp_scale: int = 1


# WHY: `getOrgStats` returns these five counts directly. A NOC alerts on
# `devices_disconnected`, so it stays a metric of its own instead of a
# subtraction the monitoring system has to write.
_ORG_DEFINITIONS: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        name="mist_org_info",
        help_text="A constant 1. The labels carry the organization identifier and name.",
        kind=MetricKind.INFO,
        scope=MetricScope.ORG,
        column=1,
    ),
    MetricDefinition(
        name="mist_org_sites",
        help_text="The count of sites in the organization.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=2,
        source="num_sites",
    ),
    MetricDefinition(
        name="mist_org_devices",
        help_text="The count of devices the organization has assigned to a site.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=3,
        source="num_devices",
    ),
    MetricDefinition(
        name="mist_org_inventory",
        help_text="The count of devices in the organization inventory, assigned or not.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=4,
        source="num_inventory",
    ),
    MetricDefinition(
        name="mist_org_devices_connected",
        help_text="The count of devices that are connected to Mist Cloud.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=5,
        source="num_devices_connected",
    ),
    MetricDefinition(
        name="mist_org_devices_disconnected",
        help_text="The count of devices that are not connected to Mist Cloud.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=6,
        source="num_devices_disconnected",
    ),
)


# WHY: `getOrgStats` returns the service level expectations as a list, and each
# entry carries a `path` name with `user_minutes.total` and `user_minutes.ok`.
# The ratio is the number a NOC alerts on, so the collector derives it once here
# instead of leaving the division to every monitoring system that polls.
_SLE_DEFINITIONS: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        name="mist_org_sle_user_minutes_total",
        help_text="The total user minutes that the service level expectation measured.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SLE,
        column=1,
        source="user_minutes.total",
    ),
    MetricDefinition(
        name="mist_org_sle_user_minutes_ok",
        help_text="The user minutes that met the service level expectation.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SLE,
        column=2,
        source="user_minutes.ok",
    ),
    MetricDefinition(
        name="mist_org_sle_ratio",
        help_text=(
            "The share of user minutes that met the service level expectation, from 0 to 1. "
            "SNMP reports ten-thousandths."
        ),
        kind=MetricKind.GAUGE,
        scope=MetricScope.SLE,
        column=3,
        snmp_scale=RATIO_SNMP_SCALE,
    ),
)


# WHY: `getSiteStats` returns these counts for each site. The upstream MIB also
# carried the site name, the country, and the address as table columns. Those
# three are text, so they move into the labels of `mist_site_info`, because a
# Prometheus value must be a number.
_SITE_DEFINITIONS: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        name="mist_site_info",
        help_text="A constant 1. The labels carry the site identifier, name, and country code.",
        kind=MetricKind.INFO,
        scope=MetricScope.SITE,
        column=1,
    ),
    MetricDefinition(
        name="mist_site_aps",
        help_text="The count of access points the site holds.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=2,
        source="num_ap",
    ),
    MetricDefinition(
        name="mist_site_aps_connected",
        help_text="The count of access points at the site that are connected to Mist Cloud.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=3,
        source="num_ap_connected",
    ),
    MetricDefinition(
        name="mist_site_switches",
        help_text="The count of switches the site holds.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=4,
        source="num_switch",
    ),
    MetricDefinition(
        name="mist_site_switches_connected",
        help_text="The count of switches at the site that are connected to Mist Cloud.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=5,
        source="num_switch_connected",
    ),
    MetricDefinition(
        name="mist_site_gateways",
        help_text="The count of gateways the site holds.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=6,
        source="num_gateway",
    ),
    MetricDefinition(
        name="mist_site_gateways_connected",
        help_text="The count of gateways at the site that are connected to Mist Cloud.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=7,
        source="num_gateway_connected",
    ),
    MetricDefinition(
        name="mist_site_devices",
        help_text="The count of devices the site holds, of every type.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=8,
        source="num_devices",
    ),
    MetricDefinition(
        name="mist_site_devices_connected",
        help_text="The count of devices at the site that are connected to Mist Cloud.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=9,
        source="num_devices_connected",
    ),
    MetricDefinition(
        name="mist_site_clients",
        help_text="The count of wireless clients that the site serves.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=10,
        source="num_clients",
    ),
)


# WHY: `listSiteDevicesStats` with `type="all"` returns one record for each
# access point, switch, and gateway. The upstream MIB split these into two
# tables with 20 and 26 columns, and most of those columns repeat a fact that
# belongs in a label. This table keeps the numbers a NOC alerts on and moves the
# text into `mist_device_info`.
_DEVICE_DEFINITIONS: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        name="mist_device_info",
        help_text="A constant 1. The labels carry the device name, model, serial number, and running firmware version.",
        kind=MetricKind.INFO,
        scope=MetricScope.DEVICE,
        column=1,
    ),
    MetricDefinition(
        name="mist_device_up",
        help_text="1 when Mist Cloud reports the device as connected, and 0 for every other state.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.DEVICE,
        column=2,
    ),
    MetricDefinition(
        name="mist_device_uptime_seconds",
        help_text="The seconds since the device last restarted.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.DEVICE,
        column=3,
        source="uptime",
    ),
    MetricDefinition(
        name="mist_device_last_seen_timestamp_seconds",
        help_text="The moment Mist Cloud last heard from the device, in seconds since the epoch.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.DEVICE,
        column=4,
        source="last_seen",
    ),
    MetricDefinition(
        name="mist_device_clients",
        help_text="The count of wireless clients that the device serves.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.DEVICE,
        column=5,
        source="num_clients",
    ),
    MetricDefinition(
        name="mist_device_cpu_utilization_ratio",
        help_text="The share of the processor that the device is using, from 0 to 1. SNMP reports ten-thousandths.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.DEVICE,
        column=6,
        snmp_scale=RATIO_SNMP_SCALE,
    ),
    MetricDefinition(
        name="mist_device_memory_used_bytes",
        help_text="The memory the device is using, in bytes.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.DEVICE,
        column=7,
    ),
    MetricDefinition(
        name="mist_device_memory_total_bytes",
        help_text="The memory the device holds, in bytes.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.DEVICE,
        column=8,
    ),
    MetricDefinition(
        name="mist_device_power_budget_watts",
        help_text="The power budget the device reports, in watts.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.DEVICE,
        column=9,
        source="power_budget",
    ),
    MetricDefinition(
        name="mist_device_cpu_temperature_celsius",
        help_text="The processor temperature the device reports, in degrees Celsius.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.DEVICE,
        column=10,
    ),
    MetricDefinition(
        name="mist_device_received_bytes_total",
        help_text="The bytes the device has received.",
        kind=MetricKind.COUNTER,
        scope=MetricScope.DEVICE,
        column=11,
        source="rx_bytes",
    ),
    MetricDefinition(
        name="mist_device_transmitted_bytes_total",
        help_text="The bytes the device has sent.",
        kind=MetricKind.COUNTER,
        scope=MetricScope.DEVICE,
        column=12,
        source="tx_bytes",
    ),
    MetricDefinition(
        name="mist_device_certificate_expiry_timestamp_seconds",
        help_text="The moment the device certificate expires, in seconds since the epoch.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.DEVICE,
        column=13,
        source="cert_expiry",
    ),
)


# WHY: The gateway reports its own health beside the Mist readings. A monitoring
# system that reads a stale cache and cannot tell that it is stale raises no
# alarm while the network fails. These three readings make a failed refresh
# visible, and issue #2006 makes the same point about a stale firmware version.
_GATEWAY_DEFINITIONS: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        name="mist_scrape_success",
        help_text="1 when the last read of Mist Cloud finished, and 0 when it failed.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=90,
    ),
    MetricDefinition(
        name="mist_scrape_age_seconds",
        help_text="The seconds since the gateway last read Mist Cloud.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=91,
    ),
    MetricDefinition(
        name="mist_scrape_duration_seconds",
        help_text="The seconds the last read of Mist Cloud took. SNMP reports milliseconds.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=92,
        snmp_scale=SECONDS_SNMP_SCALE,
    ),
)


# Auto-generated metrics for all 65 stats endpoints from the expanded allowlist.
# Each metric corresponds to one endpoint, providing basic monitoring coverage.
_NEW_ORG_DEFINITIONS: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        name="mist_count_org_assets_by_distance_field",
        help_text="Statistics from the countOrgAssetsByDistanceField endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=14,
    ),
    MetricDefinition(
        name="mist_count_org_bgp_stats",
        help_text="Statistics from the countOrgBgpStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=15,
    ),
    MetricDefinition(
        name="mist_count_org_ospf_stats",
        help_text="Statistics from the countOrgOspfStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=16,
    ),
    MetricDefinition(
        name="mist_count_org_peer_path_stats",
        help_text="Statistics from the countOrgPeerPathStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=17,
    ),
    MetricDefinition(
        name="mist_count_org_sw_or_gw_ports",
        help_text="Statistics from the countOrgSwOrGwPorts endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=18,
    ),
    MetricDefinition(
        name="mist_count_org_tunnels_stats",
        help_text="Statistics from the countOrgTunnelsStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=19,
    ),
    MetricDefinition(
        name="mist_get_org_mx_edge_stats",
        help_text="Statistics from the getOrgMxEdgeStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=20,
    ),
    MetricDefinition(
        name="mist_get_org_other_device_stats",
        help_text="Statistics from the getOrgOtherDeviceStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=21,
    ),
    MetricDefinition(
        name="mist_list_org_assets_stats",
        help_text="Statistics from the listOrgAssetsStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=23,
    ),
    MetricDefinition(
        name="mist_list_org_bgp_stats",
        help_text="Statistics from the listOrgBgpStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=24,
    ),
    MetricDefinition(
        name="mist_list_org_devices_stats",
        help_text="Statistics from the listOrgDevicesStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=25,
    ),
    MetricDefinition(
        name="mist_list_org_mx_edges_stats",
        help_text="Statistics from the listOrgMxEdgesStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=26,
    ),
    MetricDefinition(
        name="mist_list_org_ospf_stats",
        help_text="Statistics from the listOrgOspfStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=27,
    ),
    MetricDefinition(
        name="mist_list_org_peer_path_stats",
        help_text="Statistics from the listOrgPeerPathStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=28,
    ),
    MetricDefinition(
        name="mist_list_org_site_stats",
        help_text="Statistics from the listOrgSiteStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=29,
    ),
    MetricDefinition(
        name="mist_list_org_sw_or_gw_ports",
        help_text="Statistics from the listOrgSwOrGwPorts endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=30,
    ),
    MetricDefinition(
        name="mist_list_org_tunnels_stats",
        help_text="Statistics from the listOrgTunnelsStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=31,
    ),
    MetricDefinition(
        name="mist_search_org_assets",
        help_text="Statistics from the searchOrgAssets endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=32,
    ),
    MetricDefinition(
        name="mist_search_org_bgp_stats",
        help_text="Statistics from the searchOrgBgpStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.ORG,
        column=33,
    ),
)


_NEW_SITE_DEFINITIONS: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        name="mist_count_site_apps",
        help_text="Statistics from the countSiteApps endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=14,
    ),
    MetricDefinition(
        name="mist_count_site_assets",
        help_text="Statistics from the countSiteAssets endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=15,
    ),
    MetricDefinition(
        name="mist_count_site_bgp_stats",
        help_text="Statistics from the countSiteBgpStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=16,
    ),
    MetricDefinition(
        name="mist_count_site_calls",
        help_text="Statistics from the countSiteCalls endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=17,
    ),
    MetricDefinition(
        name="mist_count_site_discovered_switches",
        help_text="Statistics from the countSiteDiscoveredSwitches endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=18,
    ),
    MetricDefinition(
        name="mist_count_site_ospf_stats",
        help_text="Statistics from the countSiteOspfStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=19,
    ),
    MetricDefinition(
        name="mist_count_site_sw_or_gw_ports",
        help_text="Statistics from the countSiteSwOrGwPorts endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=20,
    ),
    MetricDefinition(
        name="mist_get_site_all_clients_stats_by_device",
        help_text="Statistics from the getSiteAllClientsStatsByDevice endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=21,
    ),
    MetricDefinition(
        name="mist_get_site_asset_stats",
        help_text="Statistics from the getSiteAssetStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=22,
    ),
    MetricDefinition(
        name="mist_get_site_assets_of_interest",
        help_text="Statistics from the getSiteAssetsOfInterest endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=23,
    ),
    MetricDefinition(
        name="mist_get_site_calls_summary",
        help_text="Statistics from the getSiteCallsSummary endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=24,
    ),
    MetricDefinition(
        name="mist_get_site_device_stats",
        help_text="Statistics from the getSiteDeviceStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=25,
    ),
    MetricDefinition(
        name="mist_get_site_discovered_asset_by_map",
        help_text="Statistics from the getSiteDiscoveredAssetByMap endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=26,
    ),
    MetricDefinition(
        name="mist_get_site_gateway_metrics",
        help_text="Statistics from the getSiteGatewayMetrics endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=27,
    ),
    MetricDefinition(
        name="mist_get_site_insight_metrics_for_gateway",
        help_text="Statistics from the getSiteInsightMetricsForGateway endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=28,
    ),
    MetricDefinition(
        name="mist_get_site_mx_edge_stats",
        help_text="Statistics from the getSiteMxEdgeStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=29,
    ),
    MetricDefinition(
        name="mist_get_site_rssi_zone_stats",
        help_text="Statistics from the getSiteRssiZoneStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=30,
    ),
    MetricDefinition(
        name="mist_get_site_sdk_stats",
        help_text="Statistics from the getSiteSdkStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=31,
    ),
    MetricDefinition(
        name="mist_get_site_sdk_stats_by_map",
        help_text="Statistics from the getSiteSdkStatsByMap endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=32,
    ),
    MetricDefinition(
        name="mist_get_site_stats",
        help_text="Statistics from the getSiteStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=33,
    ),
    MetricDefinition(
        name="mist_get_site_switches_metrics",
        help_text="Statistics from the getSiteSwitchesMetrics endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=34,
    ),
    MetricDefinition(
        name="mist_get_site_wireless_client_stats",
        help_text="Statistics from the getSiteWirelessClientStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=35,
    ),
    MetricDefinition(
        name="mist_get_site_wireless_clients_stats_by_map",
        help_text="Statistics from the getSiteWirelessClientsStatsByMap endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=36,
    ),
    MetricDefinition(
        name="mist_get_site_wx_rules_usage",
        help_text="Statistics from the getSiteWxRulesUsage endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=37,
    ),
    MetricDefinition(
        name="mist_get_site_zone_stats",
        help_text="Statistics from the getSiteZoneStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=38,
    ),
    MetricDefinition(
        name="mist_list_insight_metrics",
        help_text="Statistics from the listInsightMetrics endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=39,
    ),
    MetricDefinition(
        name="mist_list_site_assets_stats",
        help_text="Statistics from the listSiteAssetsStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=40,
    ),
    MetricDefinition(
        name="mist_list_site_beacons_stats",
        help_text="Statistics from the listSiteBeaconsStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=41,
    ),
    MetricDefinition(
        name="mist_list_site_devices_stats",
        help_text="Statistics from the listSiteDevicesStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=42,
    ),
    MetricDefinition(
        name="mist_list_site_discovered_assets",
        help_text="Statistics from the listSiteDiscoveredAssets endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=43,
    ),
    MetricDefinition(
        name="mist_list_site_discovered_switches_metrics",
        help_text="Statistics from the listSiteDiscoveredSwitchesMetrics endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=44,
    ),
    MetricDefinition(
        name="mist_list_site_mx_edges_stats",
        help_text="Statistics from the listSiteMxEdgesStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=45,
    ),
    MetricDefinition(
        name="mist_list_site_rssi_zones_stats",
        help_text="Statistics from the listSiteRssiZonesStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=46,
    ),
    MetricDefinition(
        name="mist_list_site_sles_metrics",
        help_text="Statistics from the listSiteSlesMetrics endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=47,
    ),
    MetricDefinition(
        name="mist_list_site_spectrum_analysis",
        help_text="Statistics from the listSiteSpectrumAnalysis endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=48,
    ),
    MetricDefinition(
        name="mist_list_site_troubleshoot_calls",
        help_text="Statistics from the listSiteTroubleshootCalls endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=49,
    ),
    MetricDefinition(
        name="mist_list_site_unconnected_client_stats",
        help_text="Statistics from the listSiteUnconnectedClientStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=50,
    ),
    MetricDefinition(
        name="mist_list_site_wireless_clients_stats",
        help_text="Statistics from the listSiteWirelessClientsStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=51,
    ),
    MetricDefinition(
        name="mist_list_site_zones_stats",
        help_text="Statistics from the listSiteZonesStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=52,
    ),
    MetricDefinition(
        name="mist_search_site_assets",
        help_text="Statistics from the searchSiteAssets endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=53,
    ),
    MetricDefinition(
        name="mist_search_site_bgp_stats",
        help_text="Statistics from the searchSiteBgpStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=54,
    ),
    MetricDefinition(
        name="mist_search_site_calls",
        help_text="Statistics from the searchSiteCalls endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=55,
    ),
    MetricDefinition(
        name="mist_search_site_discovered_switches",
        help_text="Statistics from the searchSiteDiscoveredSwitches endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=56,
    ),
    MetricDefinition(
        name="mist_search_site_discovered_switches_metrics",
        help_text="Statistics from the searchSiteDiscoveredSwitchesMetrics endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=57,
    ),
    MetricDefinition(
        name="mist_search_site_ospf_stats",
        help_text="Statistics from the searchSiteOspfStats endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=58,
    ),
    MetricDefinition(
        name="mist_search_site_sw_or_gw_ports",
        help_text="Statistics from the searchSiteSwOrGwPorts endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=59,
    ),
    MetricDefinition(
        name="mist_troubleshoot_site_call",
        help_text="Statistics from the troubleshootSiteCall endpoint.",
        kind=MetricKind.GAUGE,
        scope=MetricScope.SITE,
        column=60,
    ),
)


class MetricCatalog:
    """The full set of readings that the gateway serves.

    Why:
        The collector, the Prometheus renderer, and the SNMP responder all need
        the same list. A single catalog keeps one definition of each reading, so
        a new metric reaches all three paths from one edit.
    """

    def __init__(self) -> None:
        """Build the catalog and index it by scope and by name.

        Raises:
            ValueError: If two definitions carry the same metric name.
        """
        logger.debug("Build the metric catalog")  # Log before the index build, because a name clash stops it.
        self._by_scope: dict[MetricScope, tuple[MetricDefinition, ...]] = {
            # The gateway health joins the org scalars.
            MetricScope.ORG: _ORG_DEFINITIONS + _NEW_ORG_DEFINITIONS + _GATEWAY_DEFINITIONS,
            MetricScope.SITE: _SITE_DEFINITIONS + _NEW_SITE_DEFINITIONS,
            MetricScope.DEVICE: _DEVICE_DEFINITIONS,
            MetricScope.SLE: _SLE_DEFINITIONS,
        }
        self._by_name: dict[str, MetricDefinition] = {}  # The name index answers a lookup from a renderer.
        for definitions in self._by_scope.values():  # Walk every scope so the index covers the whole catalog.
            for definition in definitions:  # One pass fills the name index and finds a duplicate name.
                if definition.name in self._by_name:  # A duplicate name would make one reading unreachable.
                    raise ValueError(f"The metric name {definition.name} is defined twice.")
                self._by_name[definition.name] = definition
        logger.debug("The metric catalog holds %d definitions", len(self._by_name))  # Log the result count.

    def for_scope(self, scope: MetricScope) -> tuple[MetricDefinition, ...]:
        """Return every definition of one scope, in column order.

        Args:
            scope: The Mist object whose definitions the caller needs.

        Returns:
            The definitions, sorted by column number.
        """
        return tuple(sorted(self._by_scope[scope], key=lambda item: item.column))

    def by_name(self, name: str) -> MetricDefinition | None:
        """Return the definition with this Prometheus name.

        Args:
            name: The Prometheus metric name.

        Returns:
            The definition, or None when the catalog holds no such name.
        """
        return self._by_name.get(name)

    def names(self) -> tuple[str, ...]:
        """Return every metric name the catalog holds.

        Returns:
            The names, in the order the catalog built them.
        """
        return tuple(self._by_name)

    @staticmethod
    def subtree(scope: MetricScope) -> int:
        """Return the SNMP subtree number of one scope.

        Args:
            scope: The Mist object whose subtree the caller needs.

        Returns:
            The number that follows the operator base OID.
        """
        return SUBTREE_BY_SCOPE[scope]
