"""EndpointFamilyExporter exports remaining Mist endpoint issues.

Issue #1807 stage two groups endpoint calls by identifier tuple.
Each operation row names a real SDK function from the installed package.
The exporter prompts for identifiers in SDK signature order.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on the project toolchain.

import importlib  # WHY: lazy imports avoid a circular MistHelper import.
import logging  # WHY: operators need an action trace for each export.
from dataclasses import dataclass  # WHY: immutable rows keep the operation table clear.
from typing import Any  # WHY: Mist SDK responses have dynamic row shapes.

import mistapi  # WHY: the SDK supplies endpoint calls and the pagination helper.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: shared flatten and escape logic keeps exports consistent.
from src.utils.input_utils import InputUtils  # WHY: MSP selection must use the EOF-safe prompt.


@dataclass(frozen=True)
class _EndpointFamilyOp:
    """One endpoint operation and its required identifier tuple."""

    operation: str  # The Mist operationId selects the API call and primary-key strategy.
    module: str  # The dotted SDK module lets the resolver import the function lazily.
    required: tuple[str, ...]  # The tuple preserves the SDK signature order.
    issues: tuple[int, ...]  # The issue tuple states which endpoint issues this row closes.


@dataclass(frozen=True)
class _EndpointArgumentSet:
    """Collected positional arguments and a safe file label."""

    values: tuple[str, ...]  # The SDK call receives these values after the session.
    label: str  # The export filename uses this label to name the target.


_SITE_SLE_OPS: tuple[_EndpointFamilyOp, ...] = (
    _EndpointFamilyOp(
        "listSiteSlesMetrics", "mistapi.api.v1.sites.sle", ("site_id", "scope", "scope_id"), (1349,)
    ),  # Issue #1349.
    _EndpointFamilyOp(
        "getSiteSleHistogram", "mistapi.api.v1.sites.sle", ("site_id", "scope", "scope_id", "metric"), (1214,)
    ),  # Issue #1214.
    _EndpointFamilyOp(
        "getSiteSleImpactSummary", "mistapi.api.v1.sites.sle", ("site_id", "scope", "scope_id", "metric"), (1215,)
    ),  # Issue #1215.
    _EndpointFamilyOp(
        "getSiteSleSummary", "mistapi.api.v1.sites.sle", ("site_id", "scope", "scope_id", "metric"), (1216,)
    ),  # Issue #1216.
    _EndpointFamilyOp(
        "getSiteSleSummaryTrend", "mistapi.api.v1.sites.sle", ("site_id", "scope", "scope_id", "metric"), (1217,)
    ),  # Issue #1217.
    _EndpointFamilyOp(
        "getSiteSleThreshold", "mistapi.api.v1.sites.sle", ("site_id", "scope", "scope_id", "metric"), (1218,)
    ),  # Issue #1218.
    _EndpointFamilyOp(
        "listSiteSleImpactedApplications",
        "mistapi.api.v1.sites.sle",
        ("site_id", "scope", "scope_id", "metric"),
        (1340,),
    ),  # Issue #1340.
    _EndpointFamilyOp(
        "listSiteSleImpactedAps", "mistapi.api.v1.sites.sle", ("site_id", "scope", "scope_id", "metric"), (1341,)
    ),  # Issue #1341.
    _EndpointFamilyOp(
        "listSiteSleImpactedChassis", "mistapi.api.v1.sites.sle", ("site_id", "scope", "scope_id", "metric"), (1342,)
    ),  # Issue #1342.
    _EndpointFamilyOp(
        "listSiteSleImpactedGateways", "mistapi.api.v1.sites.sle", ("site_id", "scope", "scope_id", "metric"), (1343,)
    ),  # Issue #1343.
    _EndpointFamilyOp(
        "listSiteSleImpactedInterfaces", "mistapi.api.v1.sites.sle", ("site_id", "scope", "scope_id", "metric"), (1344,)
    ),  # Issue #1344.
    _EndpointFamilyOp(
        "listSiteSleImpactedSwitches", "mistapi.api.v1.sites.sle", ("site_id", "scope", "scope_id", "metric"), (1345,)
    ),  # Issue #1345.
    _EndpointFamilyOp(
        "listSiteSleImpactedWiredClients",
        "mistapi.api.v1.sites.sle",
        ("site_id", "scope", "scope_id", "metric"),
        (1346,),
    ),  # Issue #1346.
    _EndpointFamilyOp(
        "listSiteSleImpactedWirelessClients",
        "mistapi.api.v1.sites.sle",
        ("site_id", "scope", "scope_id", "metric"),
        (1347,),
    ),  # Issue #1347.
    _EndpointFamilyOp(
        "listSiteSleMetricClassifiers", "mistapi.api.v1.sites.sle", ("site_id", "scope", "scope_id", "metric"), (1348,)
    ),  # Issue #1348.
    _EndpointFamilyOp(
        "getSiteSleClassifierDetails",
        "mistapi.api.v1.sites.sle",
        ("site_id", "scope", "scope_id", "metric", "classifier"),
        (1212,),
    ),  # Issue #1212.
    _EndpointFamilyOp(
        "getSiteSleClassifierSummaryTrend",
        "mistapi.api.v1.sites.sle",
        ("site_id", "scope", "scope_id", "metric", "classifier"),
        (1213,),
    ),  # Issue #1213.
)

_SITE_MAP_OPS: tuple[_EndpointFamilyOp, ...] = (
    _EndpointFamilyOp(
        "getSiteApAutoOrientation", "mistapi.api.v1.sites.maps", ("map_id", "site_id"), (1177,)
    ),  # Issue #1177.
    _EndpointFamilyOp(
        "getSiteMapAutoZoneStatus", "mistapi.api.v1.sites.maps", ("map_id", "site_id"), (1199,)
    ),  # Issue #1199.
    _EndpointFamilyOp(
        "getSiteApAutoPlacement", "mistapi.api.v1.sites.maps", ("site_id", "map_id"), (1178,)
    ),  # Issue #1178.
    _EndpointFamilyOp(
        "getSiteDiscoveredAssetByMap", "mistapi.api.v1.sites.stats", ("site_id", "map_id"), (1188,)
    ),  # Issue #1188.
    _EndpointFamilyOp(
        "getSiteSdkStatsByMap", "mistapi.api.v1.sites.stats", ("site_id", "map_id"), (1209,)
    ),  # Issue #1209.
    _EndpointFamilyOp(
        "getSiteWirelessClientsStatsByMap", "mistapi.api.v1.sites.stats", ("site_id", "map_id"), (1226,)
    ),  # Issue #1226.
    _EndpointFamilyOp(
        "listSiteUnconnectedClientStats", "mistapi.api.v1.sites.stats", ("site_id", "map_id"), (1354,)
    ),  # Issue #1354.
)

_SITE_DETAIL_OPS: tuple[_EndpointFamilyOp, ...] = (
    _EndpointFamilyOp("exportSiteDevices", "mistapi.api.v1.sites.devices", ("site_id",), (1088,)),  # Issue #1088.
    _EndpointFamilyOp(
        "getSiteAssetStats", "mistapi.api.v1.sites.stats", ("site_id", "asset_id"), (1179,)
    ),  # Issue #1179.
    _EndpointFamilyOp(
        "listSiteCurrentRrmNeighbors", "mistapi.api.v1.sites.rrm", ("site_id", "band"), (1318,)
    ),  # Issue #1318.
    _EndpointFamilyOp(
        "getSiteEventsForClient", "mistapi.api.v1.sites.clients", ("site_id", "client_mac"), (1189,)
    ),  # Issue #1189.
    _EndpointFamilyOp(
        "getSiteWirelessClientStats", "mistapi.api.v1.sites.stats", ("site_id", "client_mac"), (1225,)
    ),  # Issue #1225.
    _EndpointFamilyOp(
        "getSiteAllClientsStatsByDevice", "mistapi.api.v1.sites.stats", ("site_id", "device_id"), (1176,)
    ),  # Issue #1176.
    _EndpointFamilyOp(
        "getSiteDeviceConfigCmd", "mistapi.api.v1.sites.devices", ("site_id", "device_id"), (1186,)
    ),  # Issue #1186.
    _EndpointFamilyOp(
        "getSiteDeviceIotPort", "mistapi.api.v1.sites.devices", ("site_id", "device_id"), (1187,)
    ),  # Issue #1187.
    _EndpointFamilyOp(
        "getSiteCurrentRrmConsiderations", "mistapi.api.v1.sites.rrm", ("site_id", "device_id", "band"), (1184,)
    ),  # Issue #1184.
    _EndpointFamilyOp(
        "getSiteInsightMetricsForGateway", "mistapi.api.v1.sites.insights", ("site_id", "device_id", "metrics"), (1193,)
    ),  # Issue #1193.
    _EndpointFamilyOp(
        "getSiteEvpnTopology", "mistapi.api.v1.sites.evpn_topologies", ("site_id", "evpn_topology_id"), (1190,)
    ),  # Issue #1190.
    _EndpointFamilyOp(
        "getSiteGuestAuthorization", "mistapi.api.v1.sites.guests", ("site_id", "guest_mac"), (1192,)
    ),  # Issue #1192.
    _EndpointFamilyOp(
        "getSiteInsightMetricsForMxEdge", "mistapi.api.v1.sites.insights", ("site_id", "metric", "device_mac"), (1194,)
    ),  # Issue #1194.
    _EndpointFamilyOp(
        "getSiteInsightMetricsForSwitch", "mistapi.api.v1.sites.insights", ("site_id", "metric", "device_mac"), (1195,)
    ),  # Issue #1195.
    _EndpointFamilyOp(
        "getSiteMxEdge", "mistapi.api.v1.sites.mxedges", ("site_id", "mxedge_id"), (1200,)
    ),  # Issue #1200.
    _EndpointFamilyOp(
        "getSiteMxEdgeStats", "mistapi.api.v1.sites.stats", ("site_id", "mxedge_id"), (1201,)
    ),  # Issue #1201.
    _EndpointFamilyOp("getSitePsk", "mistapi.api.v1.sites.psks", ("site_id", "psk_id"), (1202,)),  # Issue #1202.
    _EndpointFamilyOp(
        "downloadSiteRfdiagRecording", "mistapi.api.v1.sites.rfdiags", ("site_id", "rfdiag_id"), (1087,)
    ),  # Issue #1087.
    _EndpointFamilyOp(
        "getSiteRfdiagRecording", "mistapi.api.v1.sites.rfdiags", ("site_id", "rfdiag_id"), (1203,)
    ),  # Issue #1203.
    _EndpointFamilyOp(
        "getSiteRogueAP", "mistapi.api.v1.sites.rogues", ("site_id", "rogue_bssid"), (1204,)
    ),  # Issue #1204.
    _EndpointFamilyOp(
        "getSiteRssiZone", "mistapi.api.v1.sites.rssizones", ("site_id", "rssizone_id"), (1205,)
    ),  # Issue #1205.
    _EndpointFamilyOp(
        "getSiteSdkStats", "mistapi.api.v1.sites.stats", ("site_id", "sdkclient_id"), (1208,)
    ),  # Issue #1208.
    _EndpointFamilyOp(
        "getSiteUiSetting", "mistapi.api.v1.sites.uisettings", ("site_id", "uisetting_id"), (1222,)
    ),  # Issue #1222.
    _EndpointFamilyOp(
        "getSiteSsrUpgrade", "mistapi.api.v1.sites.ssr", ("site_id", "upgrade_id"), (1219,)
    ),  # Issue #1219.
    _EndpointFamilyOp(
        "getSiteVBeacon", "mistapi.api.v1.sites.vbeacons", ("site_id", "vbeacon_id"), (1223,)
    ),  # Issue #1223.
    _EndpointFamilyOp(
        "getSiteWebhook", "mistapi.api.v1.sites.webhooks", ("site_id", "webhook_id"), (1224,)
    ),  # Issue #1224.
    _EndpointFamilyOp("getSiteWlan", "mistapi.api.v1.sites.wlans", ("site_id", "wlan_id"), (1227,)),  # Issue #1227.
    _EndpointFamilyOp(
        "getSiteWxRule", "mistapi.api.v1.sites.wxrules", ("site_id", "wxrule_id"), (1228,)
    ),  # Issue #1228.
    _EndpointFamilyOp("getSiteWxTag", "mistapi.api.v1.sites.wxtags", ("site_id", "wxtag_id"), (1230,)),  # Issue #1230.
    _EndpointFamilyOp(
        "getSiteWxTunnel", "mistapi.api.v1.sites.wxtunnels", ("site_id", "wxtunnel_id"), (1231,)
    ),  # Issue #1231.
    _EndpointFamilyOp(
        "getSiteRssiZoneStats", "mistapi.api.v1.sites.stats", ("site_id", "zone_id"), (1206,)
    ),  # Issue #1206.
    _EndpointFamilyOp("getSiteZone", "mistapi.api.v1.sites.zones", ("site_id", "zone_id"), (1232,)),  # Issue #1232.
    _EndpointFamilyOp(
        "getSiteZoneStats", "mistapi.api.v1.sites.stats", ("site_id", "zone_id"), (1233,)
    ),  # Issue #1233.
)

_ORG_DETAIL_OPS: tuple[_EndpointFamilyOp, ...] = (
    _EndpointFamilyOp("getMspOrg", "mistapi.api.v1.msps.orgs", ("msp_id", "org_id"), (1097,)),  # Issue #1097.
    _EndpointFamilyOp("adoptOrgJsiDevice", "mistapi.api.v1.orgs.jsi", ("org_id",), (1016,)),  # Issue #1016.
    _EndpointFamilyOp(
        "searchOrgDeviceLastConfigs", "mistapi.api.v1.orgs.devices", ("org_id",), (1370,)
    ),  # Issue #1370.
    _EndpointFamilyOp(
        "getOrgAAMWProfile", "mistapi.api.v1.orgs.aamwprofiles", ("org_id", "aamwprofile_id"), (1105,)
    ),  # Issue #1105.
    _EndpointFamilyOp(
        "getOrgAlarmTemplate", "mistapi.api.v1.orgs.alarmtemplates", ("org_id", "alarmtemplate_id"), (1106,)
    ),  # Issue #1106.
    _EndpointFamilyOp(
        "getOrgApiToken", "mistapi.api.v1.orgs.apitokens", ("org_id", "apitoken_id"), (1109,)
    ),  # Issue #1109.
    _EndpointFamilyOp(
        "getOrgOauthAppLinkedStatus", "mistapi.api.v1.orgs.setting", ("org_id", "app_name", "forward"), (1141,)
    ),  # Issue #1141.
    _EndpointFamilyOp(
        "getOrgAptemplate", "mistapi.api.v1.orgs.aptemplates", ("org_id", "aptemplate_id"), (1111,)
    ),  # Issue #1111.
    _EndpointFamilyOp("getOrgAsset", "mistapi.api.v1.orgs.assets", ("org_id", "asset_id"), (1112,)),  # Issue #1112.
    _EndpointFamilyOp(
        "getOrgAssetFilter", "mistapi.api.v1.orgs.assetfilters", ("org_id", "assetfilter_id"), (1113,)
    ),  # Issue #1113.
    _EndpointFamilyOp(
        "getOrgAntivirusProfile", "mistapi.api.v1.orgs.avprofiles", ("org_id", "avprofile_id"), (1107,)
    ),  # Issue #1107.
    _EndpointFamilyOp(
        "getOrgOtherDevice", "mistapi.api.v1.orgs.otherdevices", ("org_id", "device_mac"), (1142,)
    ),  # Issue #1142.
    _EndpointFamilyOp(
        "getOrgOtherDeviceStats", "mistapi.api.v1.orgs.stats", ("org_id", "device_mac"), (1143,)
    ),  # Issue #1143.
    _EndpointFamilyOp(
        "getOrgDeviceProfile", "mistapi.api.v1.orgs.deviceprofiles", ("org_id", "deviceprofile_id"), (1117,)
    ),  # Issue #1117.
    _EndpointFamilyOp(
        "getOrgEvpnTopology", "mistapi.api.v1.orgs.evpn_topologies", ("org_id", "evpn_topology_id"), (1119,)
    ),  # Issue #1119.
    _EndpointFamilyOp(
        "getInstallerDeviceVirtualChassis", "mistapi.api.v1.installer.orgs.devices", ("org_id", "fpc0_mac"), (1093,)
    ),  # Issue #1093.
    _EndpointFamilyOp(
        "getOrgGuestAuthorization", "mistapi.api.v1.orgs.guests", ("org_id", "guest_mac"), (1120,)
    ),  # Issue #1120.
    _EndpointFamilyOp(
        "getOrgIdpProfile", "mistapi.api.v1.orgs.idpprofiles", ("org_id", "idpprofile_id"), (1121,)
    ),  # Issue #1121.
    _EndpointFamilyOp(
        "getOrgMarvisClientInvite", "mistapi.api.v1.orgs.marvisinvites", ("org_id", "marvisinvite_id"), (1126,)
    ),  # Issue #1126.
    _EndpointFamilyOp(
        "getOrgMxEdgeCluster", "mistapi.api.v1.orgs.mxclusters", ("org_id", "mxcluster_id"), (1129,)
    ),  # Issue #1129.
    _EndpointFamilyOp("getOrgMxEdge", "mistapi.api.v1.orgs.mxedges", ("org_id", "mxedge_id"), (1128,)),  # Issue #1128.
    _EndpointFamilyOp(
        "getOrgMxEdgeVmParams", "mistapi.api.v1.orgs.mxedges", ("org_id", "mxedge_id"), (1132,)
    ),  # Issue #1132.
    _EndpointFamilyOp(
        "getOrgMxTunnel", "mistapi.api.v1.orgs.mxtunnels", ("org_id", "mxtunnel_id"), (1133,)
    ),  # Issue #1133.
    _EndpointFamilyOp(
        "downloadOrgNacPortalSamlMetadata", "mistapi.api.v1.orgs.nacportals", ("org_id", "nacportal_id"), (1085,)
    ),  # Issue #1085.
    _EndpointFamilyOp(
        "getOrgNacPortal", "mistapi.api.v1.orgs.nacportals", ("org_id", "nacportal_id"), (1135,)
    ),  # Issue #1135.
    _EndpointFamilyOp(
        "getOrgNacPortalSamlMetadata", "mistapi.api.v1.orgs.nacportals", ("org_id", "nacportal_id"), (1136,)
    ),  # Issue #1136.
    _EndpointFamilyOp(
        "listOrgNacPortalSsoLatestFailures", "mistapi.api.v1.orgs.nacportals", ("org_id", "nacportal_id"), (1291,)
    ),  # Issue #1291.
    _EndpointFamilyOp(
        "getOrgNacRule", "mistapi.api.v1.orgs.nacrules", ("org_id", "nacrule_id"), (1137,)
    ),  # Issue #1137.
    _EndpointFamilyOp("getOrgNacTag", "mistapi.api.v1.orgs.nactags", ("org_id", "nactag_id"), (1138,)),  # Issue #1138.
    _EndpointFamilyOp(
        "getOrgNetwork", "mistapi.api.v1.orgs.networks", ("org_id", "network_id"), (1139,)
    ),  # Issue #1139.
    _EndpointFamilyOp(
        "getOrgNetworkTemplate", "mistapi.api.v1.orgs.networktemplates", ("org_id", "networktemplate_id"), (1140,)
    ),  # Issue #1140.
    _EndpointFamilyOp("getOrgPsk", "mistapi.api.v1.orgs.psks", ("org_id", "psk_id"), (1144,)),  # Issue #1144.
    _EndpointFamilyOp(
        "getOrgPskPortal", "mistapi.api.v1.orgs.pskportals", ("org_id", "pskportal_id"), (1145,)
    ),  # Issue #1145.
    _EndpointFamilyOp(
        "getOrgRfTemplate", "mistapi.api.v1.orgs.rftemplates", ("org_id", "rftemplate_id"), (1146,)
    ),  # Issue #1146.
    _EndpointFamilyOp(
        "getSdkInvite", "mistapi.api.v1.orgs.sdkinvites", ("org_id", "sdkinvite_id"), (1171,)
    ),  # Issue #1171.
    _EndpointFamilyOp(
        "getSdkInviteQrCode", "mistapi.api.v1.orgs.sdkinvites", ("org_id", "sdkinvite_id"), (1172,)
    ),  # Issue #1172.
    _EndpointFamilyOp(
        "getSdkTemplate", "mistapi.api.v1.orgs.sdktemplates", ("org_id", "sdktemplate_id"), (1173,)
    ),  # Issue #1173.
    _EndpointFamilyOp(
        "getOrgSecPolicy", "mistapi.api.v1.orgs.secpolicies", ("org_id", "secpolicy_id"), (1149,)
    ),  # Issue #1149.
    _EndpointFamilyOp(
        "getOrgService", "mistapi.api.v1.orgs.services", ("org_id", "service_id"), (1150,)
    ),  # Issue #1150.
    _EndpointFamilyOp(
        "getOrgServicePolicy", "mistapi.api.v1.orgs.servicepolicies", ("org_id", "servicepolicy_id"), (1151,)
    ),  # Issue #1151.
    _EndpointFamilyOp(
        "listInstallerMaps", "mistapi.api.v1.installer.orgs.sites", ("org_id", "site_name"), (1252,)
    ),  # Issue #1252.
    _EndpointFamilyOp(
        "getOrgSiteGroup", "mistapi.api.v1.orgs.sitegroups", ("org_id", "sitegroup_id"), (1153,)
    ),  # Issue #1153.
    _EndpointFamilyOp(
        "downloadOrgSamlMetadata", "mistapi.api.v1.orgs.ssos", ("org_id", "sso_id"), (1086,)
    ),  # Issue #1086.
    _EndpointFamilyOp("getOrgSamlMetadata", "mistapi.api.v1.orgs.ssos", ("org_id", "sso_id"), (1147,)),  # Issue #1147.
    _EndpointFamilyOp("getOrgSso", "mistapi.api.v1.orgs.ssos", ("org_id", "sso_id"), (1156,)),  # Issue #1156.
    _EndpointFamilyOp(
        "listOrgSsoLatestFailures", "mistapi.api.v1.orgs.ssos", ("org_id", "sso_id"), (1297,)
    ),  # Issue #1297.
    _EndpointFamilyOp(
        "getOrgSsoRole", "mistapi.api.v1.orgs.ssoroles", ("org_id", "ssorole_id"), (1157,)
    ),  # Issue #1157.
    _EndpointFamilyOp(
        "getOrgTemplate", "mistapi.api.v1.orgs.templates", ("org_id", "template_id"), (1161,)
    ),  # Issue #1161.
    _EndpointFamilyOp(
        "GetOrgTicketAttachment", "mistapi.api.v1.orgs.tickets", ("org_id", "ticket_id", "attachment_id"), (1014,)
    ),  # Issue #1014.
    _EndpointFamilyOp(
        "getOrgUiSetting", "mistapi.api.v1.orgs.uisettings", ("org_id", "uisetting_id"), (1162,)
    ),  # Issue #1162.
    _EndpointFamilyOp(
        "getOrgDeviceUpgrade", "mistapi.api.v1.orgs.devices", ("org_id", "upgrade_id"), (1118,)
    ),  # Issue #1118.
    _EndpointFamilyOp(
        "getOrgMxEdgeUpgrade", "mistapi.api.v1.orgs.mxedges", ("org_id", "upgrade_id"), (1130,)
    ),  # Issue #1130.
    _EndpointFamilyOp("getOrgSsrUpgrade", "mistapi.api.v1.orgs.ssr", ("org_id", "upgrade_id"), (1159,)),  # Issue #1159.
    _EndpointFamilyOp(
        "getOrgUserMac", "mistapi.api.v1.orgs.usermacs", ("org_id", "usermac_id"), (1163,)
    ),  # Issue #1163.
    _EndpointFamilyOp("getOrgVpn", "mistapi.api.v1.orgs.vpns", ("org_id", "vpn_id"), (1164,)),  # Issue #1164.
    _EndpointFamilyOp(
        "getOrgWebhook", "mistapi.api.v1.orgs.webhooks", ("org_id", "webhook_id"), (1166,)
    ),  # Issue #1166.
    _EndpointFamilyOp("getOrgWLAN", "mistapi.api.v1.orgs.wlans", ("org_id", "wlan_id"), (1165,)),  # Issue #1165.
    _EndpointFamilyOp("getOrgWxRule", "mistapi.api.v1.orgs.wxrules", ("org_id", "wxrule_id"), (1167,)),  # Issue #1167.
    _EndpointFamilyOp(
        "getOrgCurrentMatchingClientsOfAWxTag", "mistapi.api.v1.orgs.wxtags", ("org_id", "wxtag_id"), (1116,)
    ),  # Issue #1116.
    _EndpointFamilyOp("getOrgWxTag", "mistapi.api.v1.orgs.wxtags", ("org_id", "wxtag_id"), (1168,)),  # Issue #1168.
    _EndpointFamilyOp(
        "getOrgWxTunnel", "mistapi.api.v1.orgs.wxtunnels", ("org_id", "wxtunnel_id"), (1169,)
    ),  # Issue #1169.
)

_MSP_DETAIL_OPS: tuple[_EndpointFamilyOp, ...] = (
    _EndpointFamilyOp("searchMspOrgs", "mistapi.api.v1.msps.orgs", ("msp_id",), (1368,)),  # Issue #1368.
    _EndpointFamilyOp("getMspAdmin", "mistapi.api.v1.msps.admins", ("msp_id", "admin_id"), (1094,)),  # Issue #1094.
    _EndpointFamilyOp("getMspSle", "mistapi.api.v1.msps.insights", ("msp_id", "metric"), (1100,)),  # Issue #1100.
    _EndpointFamilyOp(
        "getMspInventoryByMac", "mistapi.api.v1.msps.inventory", ("msp_id", "device_mac"), (1096,)
    ),  # Issue #1096.
    _EndpointFamilyOp(
        "getMspOrgGroup", "mistapi.api.v1.msps.orggroups", ("msp_id", "orggroup_id"), (1098,)
    ),  # Issue #1098.
    _EndpointFamilyOp(
        "downloadMspSamlMetadata", "mistapi.api.v1.msps.ssos", ("msp_id", "sso_id"), (1084,)
    ),  # Issue #1084.
    _EndpointFamilyOp("getMspSamlMetadata", "mistapi.api.v1.msps.ssos", ("msp_id", "sso_id"), (1099,)),  # Issue #1099.
    _EndpointFamilyOp("getMspSso", "mistapi.api.v1.msps.ssos", ("msp_id", "sso_id"), (1101,)),  # Issue #1101.
    _EndpointFamilyOp(
        "listMspSsoLatestFailures", "mistapi.api.v1.msps.ssos", ("msp_id", "sso_id"), (1265,)
    ),  # Issue #1265.
    _EndpointFamilyOp(
        "searchMspOrgGroup", "mistapi.api.v1.msps.search", ("msp_id", "type", "q"), (1367,)
    ),  # Issue #1367.
)

_OTHER_DETAIL_OPS: tuple[_EndpointFamilyOp, ...] = (
    _EndpointFamilyOp(
        "generateSecretFor2faVerification", "mistapi.api.v1.self.two_factor", (), (1089,)
    ),  # Issue #1089.
    _EndpointFamilyOp("getApiToken", "mistapi.api.v1.self.apitokens", ("apitoken_id",), (1091,)),  # Issue #1091.
    _EndpointFamilyOp("listStates", "mistapi.api.v1.const.states", ("country_code",), (1361,)),  # Issue #1361.
    _EndpointFamilyOp(
        "getGatewayDefaultConfig", "mistapi.api.v1.const.default_gateway_config", ("model",), (1092,)
    ),  # Issue #1092.
    _EndpointFamilyOp(
        "getOauth2AuthorizationUrlForLogin", "mistapi.api.v1.login.oauth", ("provider",), (1102,)
    ),  # Issue #1102.
    _EndpointFamilyOp("getOauth2UrlForLinking", "mistapi.api.v1.self.oauth", ("provider",), (1103,)),  # Issue #1103.
)

ALL_STAGE_TWO_ENDPOINT_OPS: tuple[_EndpointFamilyOp, ...] = (
    *_SITE_SLE_OPS,  # Include the site SLE endpoint table in integrity tests.
    *_SITE_MAP_OPS,  # Include the site map endpoint table in integrity tests.
    *_SITE_DETAIL_OPS,  # Include the site detail endpoint table in integrity tests.
    *_ORG_DETAIL_OPS,  # Include the org detail endpoint table in integrity tests.
    *_MSP_DETAIL_OPS,  # Include the MSP detail endpoint table in integrity tests.
    *_OTHER_DETAIL_OPS,  # Include the other endpoint table in integrity tests.
)


class EndpointFamilyExporter:
    """Exporter for remaining endpoint issues from issue #1807."""

    @staticmethod
    def _mist_helper() -> Any:
        """Return the loaded MistHelper module."""
        return importlib.import_module("MistHelper")  # Load MistHelper lazily to avoid an import cycle.

    @staticmethod
    def _resolve(operation: _EndpointFamilyOp) -> Any:
        """Return the SDK function for one operation."""
        try:
            module = importlib.import_module(operation.module)  # Load the SDK module only when selected.
        except ImportError:
            logging.error("SDK module %s is not importable", operation.module)  # Record the missing SDK module.
            return None
        callable_obj = getattr(module, operation.operation, None)  # Read the selected function from the module.
        if callable_obj is None:
            logging.error("SDK module %s does not define %s", operation.module, operation.operation)  # Record drift.
        return callable_obj

    @staticmethod
    def _choose(operations: tuple[_EndpointFamilyOp, ...], scope_label: str) -> _EndpointFamilyOp | None:
        """Prompt the operator to select one operation from a scope table."""
        mh = EndpointFamilyExporter._mist_helper()  # Load the prompt helper at use time.
        logging.info("Offering %d %s endpoint operations", len(operations), scope_label)  # Log the prompt.
        for index, operation in enumerate(operations, start=1):
            print(
                f"  [{index}] {operation.operation} ({', '.join(operation.required) or 'no identifier'})"
            )  # Show each choice.
        answer = str(
            mh.InputUtils.safe_input(
                f"Select a {scope_label} endpoint operation (1-{len(operations)}): ",
                allow_empty=False,
                context=f"endpoint_family_exporter.{scope_label}.selection",
            )
        ).strip()  # Normalize the answer.
        logging.debug("Operator answered %r for the %s endpoint selection", answer, scope_label)  # Trace the answer.
        if not answer.isdigit():
            logging.info("! No operation selected. Returning to the menu.")  # Explain the safe cancel path.
            return None
        position = int(answer)  # Convert after the numeric guard to avoid ValueError.
        if not 1 <= position <= len(operations):
            logging.error("Selection %d is outside 1-%d", position, len(operations))  # Record the bad bound.
            logging.info("! That number is not on the list. Returning to the menu.")  # Explain the safe cancel path.
            return None
        return operations[position - 1]  # Map the one-based menu row to the tuple index.

    @staticmethod
    def _prompt_identifier(param: str, operation: str) -> tuple[str, str] | None:
        """Prompt for one identifier and return its value with a label."""
        mh = EndpointFamilyExporter._mist_helper()  # Use the shared selectors from MistHelper.
        if param == "org_id":
            org_id = str(mh.ConfigUtils.get_cached_or_prompted_org_id())  # Reuse the cached org prompt.
            return (org_id, org_id) if org_id else None  # Return no value when the operator cancels.
        if param == "site_id":
            resolved = mh.SiteDeviceExporter._resolve_site_for_stats(operation)  # Reuse the site prompt.
            return (resolved[0], resolved[1]) if resolved is not None else None  # Keep the site name for files.
        if param == "msp_id":
            msp_id = InputUtils.prompt_msp_id()  # Use the shared EOF-safe MSP prompt.
            return (msp_id, msp_id) if msp_id is not None else None  # Return no value when the prompt stops.
        answer = str(
            mh.InputUtils.safe_input(
                f"Enter {param} for {operation}: ",
                allow_empty=False,
                context=f"endpoint_family_exporter.{operation}.{param}",
            )
        ).strip()  # Read the raw identifier.
        return (answer, f"{param}_{answer}") if answer else None  # Empty values cancel the call safely.

    @staticmethod
    def _collect_arguments(operation: _EndpointFamilyOp) -> _EndpointArgumentSet | None:
        """Collect required identifiers in SDK signature order."""
        values: list[str] = []  # Preserve the positional SDK argument order.
        labels: list[str] = []  # Keep a readable target label for the export file.
        for param in operation.required:
            logging.info("Prompting for %s for %s", param, operation.operation)  # Log before each prompt.
            resolved = EndpointFamilyExporter._prompt_identifier(param, operation.operation)  # Collect one value.
            logging.debug("Prompt result for %s on %s: %s", param, operation.operation, bool(resolved))  # Log status.
            if resolved is None:
                logging.info("! No %s selected. Returning to the menu.", param)  # Explain the safe cancel path.
                return None
            values.append(resolved[0])  # Add the identifier in signature order.
            labels.append(resolved[1])  # Add a safe filename label for the identifier.
        label = "_".join(labels) if labels else "global"  # Name global calls without identifiers.
        return _EndpointArgumentSet(tuple(values), label)  # Return immutable call data to the runner.

    @staticmethod
    def _normalize(rawdata: Any) -> list[Any]:
        """Return response data as a list that the shared exporter can write."""
        if rawdata is None:
            return []
        if isinstance(rawdata, list):
            return rawdata
        if isinstance(rawdata, tuple):
            return list(rawdata)
        if isinstance(rawdata, dict):
            return [rawdata]
        return [{"value": rawdata}]

    @staticmethod
    def _persist(rawdata: Any, filename: str, operation: str) -> None:
        """Flatten and persist endpoint rows through the shared exporter."""
        mh = EndpointFamilyExporter._mist_helper()  # Load the shared DataExporter only when needed.
        rows = EndpointFamilyExporter._normalize(rawdata)  # Convert single-object responses to one row.
        logging.debug("%s returned %d normalized rows", operation, len(rows))  # Record the normalized size.
        if not rows:
            logging.info("! No %s data found", operation)  # Empty read results are valid.
            return
        flattened_data = DataProcessingUtils.flatten_nested_fields(rows)  # Flatten nested JSON for tabular output.
        sanitized_data = DataProcessingUtils.escape_multiline(flattened_data)  # Keep line breaks safe in CSV cells.
        mh.DataExporter.write_with_format_selection(
            sanitized_data, filename, api_function_name=operation
        )  # Persist data.
        logging.info("! %d %s records exported to %s", len(rows), operation, filename)  # Tell the operator.
        logging.debug("%s persisted %d rows to %s", operation, len(rows), filename)  # Record the write result.

    @staticmethod
    def _run(operation: _EndpointFamilyOp) -> None:
        """Call one endpoint and persist all returned rows."""
        mh = EndpointFamilyExporter._mist_helper()  # Load apisession only during execution.
        arguments = EndpointFamilyExporter._collect_arguments(operation)  # Prompt before the SDK call.
        if arguments is None:
            return
        callable_obj = EndpointFamilyExporter._resolve(operation)  # Resolve the SDK function before the API call.
        if callable_obj is None:
            logging.info("! %s is unavailable in this SDK version.", operation.operation)  # Explain SDK drift.
            return
        try:
            logging.info("Calling %s for %s", operation.operation, arguments.label)  # Log before the SDK call.
            response = callable_obj(mh.apisession, *arguments.values)  # Call the SDK with identifiers in order.
            rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Collect every page.
            filename = f"{operation.operation}_{arguments.label.replace(' ', '_')}.csv"  # Build a readable export name.
            EndpointFamilyExporter._persist(rawdata, filename, operation.operation)  # Write the selected output format.
        except Exception as exc:
            logging.exception(
                "Error running %s for %s", operation.operation, arguments.label
            )  # Keep traceback details.
            logging.info("! Error running %s: %s", operation.operation, exc)  # Show a short operator message.

    @staticmethod
    def _run_menu(operations: tuple[_EndpointFamilyOp, ...], scope_label: str) -> None:
        """Choose and run one endpoint from a menu table."""
        logging.info("%s Endpoint Family:", scope_label.title())  # Show the menu header.
        operation = EndpointFamilyExporter._choose(operations, scope_label)  # Ask which endpoint to run.
        if operation is None:
            return
        EndpointFamilyExporter._run(operation)  # Execute the selected endpoint.

    @staticmethod
    def site_sle_endpoints() -> None:
        """Run the site SLE endpoint family."""
        EndpointFamilyExporter._run_menu(_SITE_SLE_OPS, "site SLE")  # Use one menu row for this endpoint family.

    @staticmethod
    def site_map_endpoints() -> None:
        """Run the site map endpoint family."""
        EndpointFamilyExporter._run_menu(_SITE_MAP_OPS, "site map")  # Use one menu row for this endpoint family.

    @staticmethod
    def site_detail_endpoints() -> None:
        """Run the site detail endpoint family."""
        EndpointFamilyExporter._run_menu(_SITE_DETAIL_OPS, "site detail")  # Use one menu row for this endpoint family.

    @staticmethod
    def org_detail_endpoints() -> None:
        """Run the org detail endpoint family."""
        EndpointFamilyExporter._run_menu(_ORG_DETAIL_OPS, "org detail")  # Use one menu row for this endpoint family.

    @staticmethod
    def msp_detail_endpoints() -> None:
        """Run the MSP detail endpoint family."""
        EndpointFamilyExporter._run_menu(_MSP_DETAIL_OPS, "MSP detail")  # Use one menu row for this endpoint family.

    @staticmethod
    def other_endpoints() -> None:
        """Run the other endpoint family."""
        EndpointFamilyExporter._run_menu(_OTHER_DETAIL_OPS, "other")  # Use one menu row for this endpoint family.
