"""ArangoDBWriter: document store backend for configuration entities.

Handles upserts, graph edge management, soft-deletes, and config snapshots
for the MistHelper polyglot database layer.  Uses batch import for high
throughput on bulk API data pulls.
"""

from __future__ import annotations

import hashlib
import json
import socket
import time
import uuid
from typing import Any
from urllib.parse import urlparse

from arango import ArangoClient  # type: ignore[attr-defined]

from . import DatabaseConfig, WriteResult, get_logger

logger = get_logger(__name__)

GRAPH_NAME = "mist_network_topology"
IMPORT_BATCH_SIZE = 5000

# Core config & hierarchy edges registered in the named graph for visualization.
# Models the Mist config inheritance tree from the OpenAPI spec:
#   Org -> Sitegroups -> Sites -> Devices -> Ports
#   Org -> Templates -> Sites (assigned via site.*template_id fields)
#   Org -> Device Profiles -> Devices (assigned via device.deviceprofile_id)
#   Org -> Config objects (Networks, Services, VPNs, NAC, WxLAN, Security)
#   Org -> Infrastructure (MxClusters, MxTunnels, MxEdges)
# Events, stats, telemetry, clients, and sessions are excluded from the
# graph view but their edge collections are still created and populated.
GRAPH_EDGE_DEFINITIONS = [
    # -- Containment: Org -> Site -> Device -> Port --
    {
        "edge_collection": "OrgContainsSite",
        "from_vertex_collections": ["orgs"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "OrgContainsDevice",
        "from_vertex_collections": ["orgs"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "SiteContainsDevice",
        "from_vertex_collections": ["sites"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "DeviceHasPort",
        "from_vertex_collections": ["devices"],
        "to_vertex_collections": ["ports"],
    },
    {
        "edge_collection": "DeviceConnectedToDevice",
        "from_vertex_collections": ["devices"],
        "to_vertex_collections": ["devices"],
    },
    # -- Logical grouping: Sites <-> Sitegroups --
    {
        "edge_collection": "SiteBelongsToSiteGroup",
        "from_vertex_collections": ["sites"],
        "to_vertex_collections": ["sitegroups"],
    },
    {
        "edge_collection": "SiteGroupContainsSite",
        "from_vertex_collections": ["sitegroups"],
        "to_vertex_collections": ["sites"],
    },
    # -- Template assignment (site.*template_id fields) --
    # Templates are org-level config that gets assigned to sites
    {
        "edge_collection": "TemplateAssignedToSite",
        "from_vertex_collections": ["templates"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "TemplateAppliedToSite",
        "from_vertex_collections": ["templates"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "TemplateAppliedToSiteGroup",
        "from_vertex_collections": ["templates"],
        "to_vertex_collections": ["sitegroups"],
    },
    {
        "edge_collection": "AlarmTemplateAssignedToSite",
        "from_vertex_collections": ["alarm_templates"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "SecurityPolicyAssignedToSite",
        "from_vertex_collections": ["security_policies"],
        "to_vertex_collections": ["sites"],
    },
    # -- Device config: profiles assigned to devices --
    {
        "edge_collection": "DeviceUsesProfile",
        "from_vertex_collections": ["devices"],
        "to_vertex_collections": ["device_profiles"],
    },
    {
        "edge_collection": "ProfileAppliedToSite",
        "from_vertex_collections": ["device_profiles"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "ProfileAppliedToSiteGroup",
        "from_vertex_collections": ["device_profiles"],
        "to_vertex_collections": ["sitegroups"],
    },
    # -- Wireless config: WLANs belong to sites or templates --
    {
        "edge_collection": "WlanBelongsToSite",
        "from_vertex_collections": ["wlans"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "WlanUsesTemplate",
        "from_vertex_collections": ["wlans"],
        "to_vertex_collections": ["templates"],
    },
    {
        "edge_collection": "WlanUsesMxTunnel",
        "from_vertex_collections": ["wlans"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "PSKBelongsToSite",
        "from_vertex_collections": ["psks"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "PSKBelongsToWlan",
        "from_vertex_collections": ["psks"],
        "to_vertex_collections": ["wlans"],
    },
    # -- Org-level config objects --
    {
        "edge_collection": "NetworkBelongsToOrg",
        "from_vertex_collections": ["networks"],
        "to_vertex_collections": ["orgs"],
    },
    {
        "edge_collection": "ServiceBelongsToOrg",
        "from_vertex_collections": ["services"],
        "to_vertex_collections": ["orgs"],
    },
    {
        "edge_collection": "VpnBelongsToOrg",
        "from_vertex_collections": ["vpns"],
        "to_vertex_collections": ["orgs"],
    },
    {
        "edge_collection": "SecurityPolicyBelongsToOrg",
        "from_vertex_collections": ["security_policies"],
        "to_vertex_collections": ["orgs"],
    },
    {
        "edge_collection": "AlarmTemplateBelongsToOrg",
        "from_vertex_collections": ["alarm_templates"],
        "to_vertex_collections": ["orgs"],
    },
    {
        "edge_collection": "ServicePolicyUsesService",
        "from_vertex_collections": ["security_policies"],
        "to_vertex_collections": ["services"],
    },
    # -- NAC: rules reference tags, tags reference portals --
    {
        "edge_collection": "NACRuleUsesTag",
        "from_vertex_collections": ["nac_rules"],
        "to_vertex_collections": ["nac_tags"],
    },
    {
        "edge_collection": "NACRuleMatchesSite",
        "from_vertex_collections": ["nac_rules"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "NACRuleMatchesSiteGroup",
        "from_vertex_collections": ["nac_rules"],
        "to_vertex_collections": ["sitegroups"],
    },
    {
        "edge_collection": "NACTagBelongsToPortal",
        "from_vertex_collections": ["nac_tags"],
        "to_vertex_collections": ["nac_portals"],
    },
    # -- WxLAN policy: rules reference tags and templates --
    {
        "edge_collection": "WxRuleBelongsToTemplate",
        "from_vertex_collections": ["wx_rules"],
        "to_vertex_collections": ["templates"],
    },
    {
        "edge_collection": "WxRuleMatchesSrcTag",
        "from_vertex_collections": ["wx_rules"],
        "to_vertex_collections": ["wx_tags"],
    },
    {
        "edge_collection": "WxRuleAllowsDstTag",
        "from_vertex_collections": ["wx_rules"],
        "to_vertex_collections": ["wx_tags"],
    },
    {
        "edge_collection": "WxRuleDeniesDstTag",
        "from_vertex_collections": ["wx_rules"],
        "to_vertex_collections": ["wx_tags"],
    },
    # -- Edge infrastructure: MxEdge clusters and tunnels --
    {
        "edge_collection": "MxEdgeBelongsToCluster",
        "from_vertex_collections": ["devices"],
        "to_vertex_collections": ["mxclusters"],
    },
    {
        "edge_collection": "MxTunnelUsesCluster",
        "from_vertex_collections": ["mx_tunnels"],
        "to_vertex_collections": ["mxclusters"],
    },
    # -- EVPN fabric topology --
    {
        "edge_collection": "EvpnBelongsToSite",
        "from_vertex_collections": ["evpn_topologies"],
        "to_vertex_collections": ["sites"],
    },
]

# Full edge definitions: ALL relationship types including events, stats,
# telemetry, and operational data.  Used for collection creation and data
# writing -- every edge collection below is created and populated.
EDGE_DEFINITIONS = [
    {
        "edge_collection": "OrgContainsSite",
        "from_vertex_collections": ["orgs"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "OrgContainsDevice",
        "from_vertex_collections": ["orgs"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "SiteContainsDevice",
        "from_vertex_collections": ["sites"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "TemplateAssignedToSite",
        "from_vertex_collections": ["templates"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "DeviceHasPort",
        "from_vertex_collections": ["devices"],
        "to_vertex_collections": ["ports"],
    },
    {
        "edge_collection": "ClientConnectedToDevice",
        "from_vertex_collections": ["clients"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "WlanBelongsToSite",
        "from_vertex_collections": ["wlans"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "WlanUsesTemplate",
        "from_vertex_collections": ["wlans"],
        "to_vertex_collections": ["templates"],
    },
    {
        "edge_collection": "SiteBelongsToSiteGroup",
        "from_vertex_collections": ["sites"],
        "to_vertex_collections": ["sitegroups"],
    },
    {
        "edge_collection": "MxEdgeBelongsToCluster",
        "from_vertex_collections": ["devices"],
        "to_vertex_collections": ["mxclusters"],
    },
    {
        "edge_collection": "ConfigSnapshotForEntity",
        "from_vertex_collections": ["config_snapshots"],
        "to_vertex_collections": [
            "sites",
            "devices",
            "templates",
            "wlans",
            "networks",
            "nac_rules",
            "security_policies",
            "psks",
            "webhooks",
            "device_profiles",
            "alarm_templates",
            "guests",
            "mx_tunnels",
            "wx_rules",
            "wx_tags",
            "tickets",
            "other_devices",
            "evpn_topologies",
            "packet_captures",
            "psk_portals",
            "suppressed_alarms",
            "device_configs",
            "certificates",
            "aamw_profiles",
            "av_profiles",
            "idp_profiles",
            "secIntel_profiles",
        ],
    },
    # -- Client relationships --
    {
        "edge_collection": "ClientConnectedToWlan",
        "from_vertex_collections": ["clients"],
        "to_vertex_collections": ["wlans"],
    },
    {
        "edge_collection": "ClientBelongsToSite",
        "from_vertex_collections": ["clients"],
        "to_vertex_collections": ["sites"],
    },
    # -- Org-level entity ownership --
    {
        "edge_collection": "NetworkBelongsToOrg",
        "from_vertex_collections": ["networks"],
        "to_vertex_collections": ["orgs"],
    },
    {
        "edge_collection": "ServiceBelongsToOrg",
        "from_vertex_collections": ["services"],
        "to_vertex_collections": ["orgs"],
    },
    {
        "edge_collection": "VpnBelongsToOrg",
        "from_vertex_collections": ["vpns"],
        "to_vertex_collections": ["orgs"],
    },
    # -- Events and alarms --
    {
        "edge_collection": "AlarmBelongsToSite",
        "from_vertex_collections": ["alarms"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "EventBelongsToSite",
        "from_vertex_collections": ["events"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "EventOccurredOnDevice",
        "from_vertex_collections": ["events"],
        "to_vertex_collections": ["devices"],
    },
    # -- Security and NAC --
    {
        "edge_collection": "NACRuleMatchesSite",
        "from_vertex_collections": ["nac_rules"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "NACRuleMatchesSiteGroup",
        "from_vertex_collections": ["nac_rules"],
        "to_vertex_collections": ["sitegroups"],
    },
    {
        "edge_collection": "NACTagBelongsToPortal",
        "from_vertex_collections": ["nac_tags"],
        "to_vertex_collections": ["nac_portals"],
    },
    {
        "edge_collection": "SecurityPolicyBelongsToOrg",
        "from_vertex_collections": ["security_policies"],
        "to_vertex_collections": ["orgs"],
    },
    # -- Assets and config --
    {
        "edge_collection": "PSKBelongsToSite",
        "from_vertex_collections": ["psks"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "AssetBelongsToSite",
        "from_vertex_collections": ["assets"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "AssetOnMap",
        "from_vertex_collections": ["assets"],
        "to_vertex_collections": ["maps"],
    },
    {
        "edge_collection": "WebhookBelongsToSite",
        "from_vertex_collections": ["webhooks"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "SiteGroupContainsSite",
        "from_vertex_collections": ["sitegroups"],
        "to_vertex_collections": ["sites"],
    },
    # -- WLAN and template relationships --
    {
        "edge_collection": "WlanUsesMxTunnel",
        "from_vertex_collections": ["wlans"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "TemplateAppliedToSite",
        "from_vertex_collections": ["templates"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "TemplateAppliedToSiteGroup",
        "from_vertex_collections": ["templates"],
        "to_vertex_collections": ["sitegroups"],
    },
    # -- Tier 1: High-value entity relationships --
    {
        "edge_collection": "DeviceUsesProfile",
        "from_vertex_collections": ["devices"],
        "to_vertex_collections": ["device_profiles"],
    },
    {
        "edge_collection": "PSKBelongsToWlan",
        "from_vertex_collections": ["psks"],
        "to_vertex_collections": ["wlans"],
    },
    {
        "edge_collection": "AlarmOnDevice",
        "from_vertex_collections": ["alarms"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "NacPortalServesSiteGroup",
        "from_vertex_collections": ["nac_portals"],
        "to_vertex_collections": ["sitegroups"],
    },
    {
        "edge_collection": "MxTunnelUsesCluster",
        "from_vertex_collections": ["mx_tunnels"],
        "to_vertex_collections": ["mxclusters"],
    },
    {
        "edge_collection": "AuditLogBelongsToSite",
        "from_vertex_collections": ["audit_logs"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "GuestBelongsToSite",
        "from_vertex_collections": ["guests"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "GuestAuthorizedOnWlan",
        "from_vertex_collections": ["guests"],
        "to_vertex_collections": ["wlans"],
    },
    {
        "edge_collection": "GuestConnectedToAP",
        "from_vertex_collections": ["guests"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "RogueAPDetectedBySite",
        "from_vertex_collections": ["rogue_aps"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "RogueAPDetectedByAP",
        "from_vertex_collections": ["rogue_aps"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "RogueClientDetectedByAP",
        "from_vertex_collections": ["rogue_clients"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "RogueClientOnBSSID",
        "from_vertex_collections": ["rogue_clients"],
        "to_vertex_collections": ["rogue_aps"],
    },
    {
        "edge_collection": "RogueEventBelongsToSite",
        "from_vertex_collections": ["rogue_events"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "RogueEventOnDevice",
        "from_vertex_collections": ["rogue_events"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "MxEdgeBelongsToSite",
        "from_vertex_collections": ["devices"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "MxEdgeEventOnDevice",
        "from_vertex_collections": ["mxedge_events"],
        "to_vertex_collections": ["devices"],
    },
    # -- Tier 2: Event/search entity relationships --
    {
        "edge_collection": "ClientEventBelongsToSite",
        "from_vertex_collections": ["client_events"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "ClientEventOnDevice",
        "from_vertex_collections": ["client_events"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "SessionBelongsToSite",
        "from_vertex_collections": ["client_sessions"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "SessionOnWlan",
        "from_vertex_collections": ["client_sessions"],
        "to_vertex_collections": ["wlans"],
    },
    {
        "edge_collection": "SessionOnDevice",
        "from_vertex_collections": ["client_sessions"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "NacEventBelongsToSite",
        "from_vertex_collections": ["nac_events"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "WanEventBelongsToSite",
        "from_vertex_collections": ["wan_events"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "MxEdgeEventBelongsToSite",
        "from_vertex_collections": ["mxedge_events"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "OtherEventBelongsToSite",
        "from_vertex_collections": ["other_events"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "OrgEventBelongsToSite",
        "from_vertex_collections": ["org_events"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "SystemEventBelongsToSite",
        "from_vertex_collections": ["system_events"],
        "to_vertex_collections": ["sites"],
    },
    # -- Tier 3: Stats/telemetry relationships --
    {
        "edge_collection": "DeviceStatsBelongsToSite",
        "from_vertex_collections": ["device_stats"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "DeviceStatsForDevice",
        "from_vertex_collections": ["device_stats"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "BgpStatsBelongsToSite",
        "from_vertex_collections": ["bgp_stats"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "OspfStatsBelongsToSite",
        "from_vertex_collections": ["ospf_stats"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "PeerPathBelongsToSite",
        "from_vertex_collections": ["peer_paths"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "PortBelongsToSite",
        "from_vertex_collections": ["ports"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "PortBelongsToDevice",
        "from_vertex_collections": ["ports"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "TunnelBelongsToSite",
        "from_vertex_collections": ["tunnels"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "MxEdgeStatsBelongsToSite",
        "from_vertex_collections": ["mxedge_stats"],
        "to_vertex_collections": ["sites"],
    },
    # -- Issue #181: Config history, synthetic tests, webhooks, packet captures --
    {
        "edge_collection": "ConfigHistoryForDevice",
        "from_vertex_collections": ["config_history"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "SyntheticTestOnDevice",
        "from_vertex_collections": ["synthetic_tests"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "WebhookDeliveryFromWebhook",
        "from_vertex_collections": ["webhook_deliveries"],
        "to_vertex_collections": ["webhooks"],
    },
    {
        "edge_collection": "PacketCaptureOnDevice",
        "from_vertex_collections": ["packet_captures"],
        "to_vertex_collections": ["devices"],
    },
    # -- Tier 4: WxLAN policy relationships --
    {
        "edge_collection": "WxRuleBelongsToTemplate",
        "from_vertex_collections": ["wx_rules"],
        "to_vertex_collections": ["templates"],
    },
    {
        "edge_collection": "WxRuleMatchesSrcTag",
        "from_vertex_collections": ["wx_rules"],
        "to_vertex_collections": ["wx_tags"],
    },
    {
        "edge_collection": "WxRuleAllowsDstTag",
        "from_vertex_collections": ["wx_rules"],
        "to_vertex_collections": ["wx_tags"],
    },
    {
        "edge_collection": "WxRuleDeniesDstTag",
        "from_vertex_collections": ["wx_rules"],
        "to_vertex_collections": ["wx_tags"],
    },
    # -- Tier 5: Remaining entity relationships --
    {
        "edge_collection": "TicketBelongsToSite",
        "from_vertex_collections": ["tickets"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "PacketCaptureBelongsToSite",
        "from_vertex_collections": ["packet_captures"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "OtherDeviceBelongsToSite",
        "from_vertex_collections": ["other_devices"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "EvpnBelongsToSite",
        "from_vertex_collections": ["evpn_topologies"],
        "to_vertex_collections": ["sites"],
    },
    # -- Edges added for full relationship coverage --
    {
        "edge_collection": "AlarmTemplateAssignedToSite",
        "from_vertex_collections": ["alarm_templates"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "SecurityPolicyAssignedToSite",
        "from_vertex_collections": ["security_policies"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "DeviceConnectedToDevice",
        "from_vertex_collections": ["devices"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "ProfileAppliedToSite",
        "from_vertex_collections": ["device_profiles"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "ProfileAppliedToSiteGroup",
        "from_vertex_collections": ["device_profiles"],
        "to_vertex_collections": ["sitegroups"],
    },
    {
        "edge_collection": "AlarmTemplateBelongsToOrg",
        "from_vertex_collections": ["alarm_templates"],
        "to_vertex_collections": ["orgs"],
    },
    {
        "edge_collection": "WlanAppliedToSite",
        "from_vertex_collections": ["wlans"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "WlanAppliedToSiteGroup",
        "from_vertex_collections": ["wlans"],
        "to_vertex_collections": ["sitegroups"],
    },
    {
        "edge_collection": "SessionForClient",
        "from_vertex_collections": ["client_sessions"],
        "to_vertex_collections": ["clients"],
    },
    {
        "edge_collection": "NacEventForClient",
        "from_vertex_collections": ["nac_events"],
        "to_vertex_collections": ["clients"],
    },
    {
        "edge_collection": "WanEventForClient",
        "from_vertex_collections": ["wan_events"],
        "to_vertex_collections": ["clients"],
    },
    {
        "edge_collection": "NACRuleUsesTag",
        "from_vertex_collections": ["nac_rules"],
        "to_vertex_collections": ["nac_tags"],
    },
    {
        "edge_collection": "ServicePolicyUsesService",
        "from_vertex_collections": ["security_policies"],
        "to_vertex_collections": ["services"],
    },
    # -- Unmapped entity relationships --
    {
        "edge_collection": "PskPortalServesSiteGroup",
        "from_vertex_collections": ["psk_portals"],
        "to_vertex_collections": ["sitegroups"],
    },
    {
        "edge_collection": "SuppressedAlarmBelongsToSite",
        "from_vertex_collections": ["suppressed_alarms"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "DeviceConfigBelongsToSite",
        "from_vertex_collections": ["device_configs"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "DeviceConfigForDevice",
        "from_vertex_collections": ["device_configs"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "SiteStatsBelongsToSite",
        "from_vertex_collections": ["site_stats"],
        "to_vertex_collections": ["sites"],
    },
]

# Derived set: names of all edge collections declared in EDGE_DEFINITIONS.
# Used by _ensure_collection() to create them with the correct ArangoDB type.
_EDGE_COLLECTION_NAMES: set[str] = {str(d["edge_collection"]) for d in EDGE_DEFINITIONS}

# Maps entity_type (API function name) to the vertex collection
# that holds the entity.  Used by snapshot() to create
# ConfigSnapshotForEntity edges linking snapshots to their entities.
ENTITY_TYPE_TO_VERTEX: dict[str, str] = {
    "listOrgSites": "sites",
    "listSiteDevices": "devices",
    "getOrgInventory": "devices",
    "listOrgGatewayTemplates": "templates",
    "listOrgRfTemplates": "templates",
    "listOrgNetworkTemplates": "templates",
    "listOrgAptemplates": "templates",
    "listOrgSiteTemplates": "templates",
    "listOrgTemplates": "templates",
    "listOrgDeviceProfiles": "device_profiles",
    "getOrgWlans": "wlans",
    "listOrgWlans": "wlans",
    "listOrgNetworks": "networks",
    "listOrgNacRules": "nac_rules",
    "listOrgSecPolicies": "security_policies",
    "listOrgServicePolicies": "security_policies",
    "listOrgPsks": "psks",
    "listOrgWebhooks": "webhooks",
    "listOrgGuestAuthorizations": "guests",
    "listOrgMxTunnels": "mx_tunnels",
    "listOrgAlarmTemplates": "alarm_templates",
    "listOrgWxRules": "wx_rules",
    "listOrgWxTags": "wx_tags",
    "listOrgTickets": "tickets",
    "listOrgOtherDevices": "other_devices",
    "listOrgEvpnTopologies": "evpn_topologies",
    "listOrgPacketCaptures": "packet_captures",
    "listOrgNacTags": "nac_tags",
    "listOrgNacPortals": "nac_portals",
    "listOrgSiteGroups": "sitegroups",
    "listOrgMxEdges": "devices",
    "listOrgMxEdgeClusters": "mxclusters",
    "listOrgServices": "services",
    "listOrgVpns": "vpns",
    "listOrgAssets": "assets",
    "listOrgAuditLogs": "audit_logs",
    "searchOrgAssets": "assets",
    "searchOrgDevices": "devices",
    # -- Unmapped entity types --
    "listOrgAdmins": "admins",
    "listOrgApiTokens": "api_tokens",
    "listOrgSsos": "ssos",
    "listOrgSsoRoles": "sso_roles",
    "listOrgAAMWProfiles": "aamw_profiles",
    "listOrgAntivirusProfiles": "av_profiles",
    "listOrgIdpProfiles": "idp_profiles",
    "listOrgSecIntelProfiles": "secIntel_profiles",
    "listOrgCertificates": "certificates",
    "listOrgPskPortals": "psk_portals",
    "listOrgSuppressedAlarms": "suppressed_alarms",
    "searchOrgDeviceLastConfigs": "device_configs",
    "listOrgSiteStats": "site_stats",
    "searchOrgGuestAuthorization": "guests",
    "listSiteAllGuestAuthorizations": "guests",
    "searchSiteGuestAuthorization": "guests",
    "listSiteRogueAPs": "rogue_aps",
    "listSiteRogueClients": "rogue_clients",
    "searchSiteRogueEvents": "rogue_events",
    "searchOrgMxEdges": "devices",
    # Issue #178: Site MxEdge endpoints
    "listSiteMxEdges": "devices",
    "listSiteMxEdgesStats": "mxedge_stats",
    "searchSiteMistEdgeEvents": "mxedge_events",
    # Issue #181: Config history, synthetic tests, webhooks, packet captures
    "searchSiteDeviceConfigHistory": "config_history",
    "searchSiteDeviceLastConfigs": "config_history",
    "searchSiteSyntheticTest": "synthetic_tests",
    "searchSiteWebhooksDeliveries": "webhook_deliveries",
    "listSitePacketCaptures": "packet_captures",
    "searchOrgSites": "sites",
    # -- New operations for complete SDK coverage ----------------------------
    "listOrgJsiPastPurchases": "jsi_purchases",
    "getOrgJseInfo": "org_settings",
    "getOrgJseIntegration": "org_settings",
    "getOrgSkyAtpIntegration": "org_settings",
    "getOrgZscalerIntegration": "org_settings",
    "getOrgMistScep": "org_settings",
    "getOrgNacCrl": "org_settings",
    "getOrgCrlFile": "org_settings",
    "getOrgSslProxyCert": "org_settings",
    "getOrgAosRegisterCmd": "org_settings",
    "getOrgSsrRegistrationCommands": "org_settings",
    "getOrgMxEdgeUpgradeInfo": "org_settings",
    "getOrgSitesSle": "org_sle",
    "countOrgWanClientEvents": "counts",
}

# Maps API collection names to graph vertex + edge relationships.
# Each entry defines which vertex collection to populate and which
# edges to create from the raw API data fields.
COLLECTION_VERTEX_MAP: dict[str, dict[str, Any]] = {
    "listOrgSites": {
        "vertex": "sites",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "OrgContainsSite",
                "from_col": "orgs",
                "from_field": "org_id",
                "to_col": "sites",
            },
            {
                "edge_col": "SiteBelongsToSiteGroup",
                "from_col": "sites",
                "from_field": "id",
                "to_col": "sitegroups",
                "to_field": "sitegroup_ids",
            },
            {
                "edge_col": "AlarmTemplateAssignedToSite",
                "from_col": "alarm_templates",
                "from_field": "alarmtemplate_id",
                "to_col": "sites",
            },
            {
                "edge_col": "SecurityPolicyAssignedToSite",
                "from_col": "security_policies",
                "from_field": "secpolicy_id",
                "to_col": "sites",
            },
        ],
        "template_edges": True,
        "ensure_target_vertices": [
            ("sitegroup_ids", "sitegroups"),
            ("alarmtemplate_id", "alarm_templates"),
            ("secpolicy_id", "security_policies"),
        ],
    },
    "getOrgInventory": {
        "vertex": "devices",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "OrgContainsDevice",
                "from_col": "orgs",
                "from_field": "org_id",
                "to_col": "devices",
            },
            {
                "edge_col": "SiteContainsDevice",
                "from_col": "sites",
                "from_field": "site_id",
                "to_col": "devices",
            },
            {
                "edge_col": "DeviceUsesProfile",
                "from_col": "devices",
                "from_field": "id",
                "to_col": "device_profiles",
                "to_field": "deviceprofile_id",
            },
            {
                "edge_col": "DeviceConnectedToDevice",
                "from_col": "devices",
                "from_field": "id",
                "to_col": "devices",
                "to_field": "connected_device_id",
            },
        ],
        "ensure_target_vertices": [
            ("deviceprofile_id", "device_profiles"),
            ("connected_device_id", "devices"),
        ],
    },
    "listOrgGatewayTemplates": {"vertex": "templates", "key_field": "id"},
    "listOrgRfTemplates": {"vertex": "templates", "key_field": "id"},
    "listOrgNetworkTemplates": {"vertex": "templates", "key_field": "id"},
    "listOrgAptemplates": {"vertex": "templates", "key_field": "id"},
    "listOrgSiteTemplates": {"vertex": "templates", "key_field": "id"},
    "searchOrgWiredClients": {
        "vertex": "clients",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "ClientConnectedToDevice",
                "from_col": "clients",
                "from_field": "mac",
                "to_col": "devices",
                "to_field": "device_mac",
                "to_key_lookup": "mac",
            },
            {
                "edge_col": "ClientBelongsToSite",
                "from_col": "clients",
                "from_field": "mac",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "searchOrgWirelessClients": {
        "vertex": "clients",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "ClientConnectedToDevice",
                "from_col": "clients",
                "from_field": "mac",
                "to_col": "devices",
                "to_field": "ap",
                "to_key_lookup": "mac",
            },
            {
                "edge_col": "ClientConnectedToWlan",
                "from_col": "clients",
                "from_field": "mac",
                "to_col": "wlans",
                "to_field": "wlan_id",
            },
            {
                "edge_col": "ClientBelongsToSite",
                "from_col": "clients",
                "from_field": "mac",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listOrgWlans": {
        "vertex": "wlans",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "WlanBelongsToSite",
                "from_col": "wlans",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "WlanUsesTemplate",
                "from_col": "wlans",
                "from_field": "id",
                "to_col": "templates",
                "to_field": "template_id",
            },
            {
                "edge_col": "WlanUsesMxTunnel",
                "from_col": "wlans",
                "from_field": "id",
                "to_col": "devices",
                "to_field": "mxtunnel_id",
            },
            {
                "edge_col": "WlanAppliedToSite",
                "from_col": "wlans",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "applies.site_ids",
            },
            {
                "edge_col": "WlanAppliedToSiteGroup",
                "from_col": "wlans",
                "from_field": "id",
                "to_col": "sitegroups",
                "to_field": "applies.sitegroup_ids",
            },
        ],
        "ensure_target_vertices": [
            ("applies.site_ids", "sites"),
            ("applies.sitegroup_ids", "sitegroups"),
        ],
    },
    "listOrgMxEdges": {
        "vertex": "devices",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "OrgContainsDevice",
                "from_col": "orgs",
                "from_field": "org_id",
                "to_col": "devices",
            },
            {
                "edge_col": "MxEdgeBelongsToCluster",
                "from_col": "devices",
                "from_field": "id",
                "to_col": "mxclusters",
                "to_field": "mxcluster_id",
            },
        ],
        "ensure_target_vertices": [("mxcluster_id", "mxclusters")],
    },
    "searchOrgNacClients": {
        "vertex": "clients",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "ClientConnectedToDevice",
                "from_col": "clients",
                "from_field": "mac",
                "to_col": "devices",
                "to_field": "device_mac",
                "to_key_lookup": "mac",
            },
            {
                "edge_col": "ClientBelongsToSite",
                "from_col": "clients",
                "from_field": "mac",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "searchOrgAlarms": {
        "vertex": "alarms",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "AlarmBelongsToSite",
                "from_col": "alarms",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "AlarmOnDevice",
                "from_col": "alarms",
                "from_field": "id",
                "to_col": "devices",
                "to_field": "device_id",
            },
        ],
    },
    "searchOrgDeviceEvents": {
        "vertex": "events",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "EventBelongsToSite",
                "from_col": "events",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "EventOccurredOnDevice",
                "from_col": "events",
                "from_field": "id",
                "to_col": "devices",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "listOrgNetworks": {
        "vertex": "networks",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "NetworkBelongsToOrg",
                "from_col": "networks",
                "from_field": "id",
                "to_col": "orgs",
                "to_field": "org_id",
            },
        ],
    },
    "listOrgServices": {
        "vertex": "services",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "ServiceBelongsToOrg",
                "from_col": "services",
                "from_field": "id",
                "to_col": "orgs",
                "to_field": "org_id",
            },
        ],
    },
    "listOrgVpns": {
        "vertex": "vpns",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "VpnBelongsToOrg",
                "from_col": "vpns",
                "from_field": "id",
                "to_col": "orgs",
                "to_field": "org_id",
            },
        ],
    },
    "listOrgNacRules": {
        "vertex": "nac_rules",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "NACRuleMatchesSite",
                "from_col": "nac_rules",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "matching.site_ids",
            },
            {
                "edge_col": "NACRuleMatchesSiteGroup",
                "from_col": "nac_rules",
                "from_field": "id",
                "to_col": "sitegroups",
                "to_field": "matching.sitegroup_ids",
            },
            {
                "edge_col": "NACRuleUsesTag",
                "from_col": "nac_rules",
                "from_field": "id",
                "to_col": "nac_tags",
                "to_field": "matching.nactags",
            },
        ],
        "ensure_target_vertices": [
            ("matching.nactags", "nac_tags"),
        ],
    },
    "listOrgNacTags": {
        "vertex": "nac_tags",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "NACTagBelongsToPortal",
                "from_col": "nac_tags",
                "from_field": "id",
                "to_col": "nac_portals",
                "to_field": "nacportal_id",
            },
        ],
        "ensure_target_vertices": [("nacportal_id", "nac_portals")],
    },
    "listOrgSecPolicies": {
        "vertex": "security_policies",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "SecurityPolicyBelongsToOrg",
                "from_col": "security_policies",
                "from_field": "id",
                "to_col": "orgs",
                "to_field": "org_id",
            },
        ],
    },
    "listOrgServicePolicies": {
        "vertex": "security_policies",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "SecurityPolicyBelongsToOrg",
                "from_col": "security_policies",
                "from_field": "id",
                "to_col": "orgs",
                "to_field": "org_id",
            },
            {
                "edge_col": "ServicePolicyUsesService",
                "from_col": "security_policies",
                "from_field": "id",
                "to_col": "services",
                "to_field": "services",
            },
        ],
        "ensure_target_vertices": [
            ("services", "services"),
        ],
    },
    "listOrgPsks": {
        "vertex": "psks",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "PSKBelongsToSite",
                "from_col": "psks",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "PSKBelongsToWlan",
                "from_col": "psks",
                "from_field": "id",
                "to_col": "wlans",
                "to_field": "wlan_id",
            },
        ],
    },
    "listOrgAssets": {
        "vertex": "assets",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "AssetBelongsToSite",
                "from_col": "assets",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "AssetOnMap",
                "from_col": "assets",
                "from_field": "id",
                "to_col": "maps",
                "to_field": "map_id",
            },
        ],
        "ensure_target_vertices": [("map_id", "maps")],
    },
    "listOrgWebhooks": {
        "vertex": "webhooks",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "WebhookBelongsToSite",
                "from_col": "webhooks",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listOrgSiteGroups": {
        "vertex": "sitegroups",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "SiteGroupContainsSite",
                "from_col": "sitegroups",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_ids",
            },
        ],
    },
    "listOrgMxEdgeClusters": {
        "vertex": "mxclusters",
        "key_field": "id",
    },
    "listOrgNacPortals": {
        "vertex": "nac_portals",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "NacPortalServesSiteGroup",
                "from_col": "nac_portals",
                "from_field": "id",
                "to_col": "sitegroups",
                "to_field": "sitegroup_ids",
            },
        ],
    },
    "listOrgAuditLogs": {
        "vertex": "audit_logs",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "AuditLogBelongsToSite",
                "from_col": "audit_logs",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listOrgTemplates": {
        "vertex": "templates",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "TemplateAppliedToSite",
                "from_col": "templates",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "applies.site_ids",
            },
            {
                "edge_col": "TemplateAppliedToSiteGroup",
                "from_col": "templates",
                "from_field": "id",
                "to_col": "sitegroups",
                "to_field": "applies.sitegroup_ids",
            },
        ],
    },
    # -- Tier 1: Guest authorizations, MxTunnels, device profiles, alarm templates --
    "listOrgGuestAuthorizations": {
        "vertex": "guests",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "GuestBelongsToSite",
                "from_col": "guests",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "GuestAuthorizedOnWlan",
                "from_col": "guests",
                "from_field": "id",
                "to_col": "wlans",
                "to_field": "wlan_id",
            },
        ],
    },
    # -- Site-level guest authorizations --
    "listSiteAllGuestAuthorizations": {
        "vertex": "guests",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "GuestBelongsToSite",
                "from_col": "guests",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "GuestConnectedToAP",
                "from_col": "guests",
                "from_field": "id",
                "to_col": "devices",
                "to_field": "ap_mac",
                "to_key_lookup": "mac",
            },
            {
                "edge_col": "GuestAuthorizedOnWlan",
                "from_col": "guests",
                "from_field": "id",
                "to_col": "wlans",
                "to_field": "wlan_id",
            },
        ],
    },
    "searchSiteGuestAuthorization": {
        "vertex": "guests",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "GuestBelongsToSite",
                "from_col": "guests",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "GuestConnectedToAP",
                "from_col": "guests",
                "from_field": "id",
                "to_col": "devices",
                "to_field": "ap_mac",
                "to_key_lookup": "mac",
            },
            {
                "edge_col": "GuestAuthorizedOnWlan",
                "from_col": "guests",
                "from_field": "id",
                "to_col": "wlans",
                "to_field": "wlan_id",
            },
        ],
    },
    # -- Site-level rogue detection --
    "listSiteRogueAPs": {
        "vertex": "rogue_aps",
        "key_field": "bssid",
        "edges": [
            {
                "edge_col": "RogueAPDetectedBySite",
                "from_col": "rogue_aps",
                "from_field": "bssid",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "RogueAPDetectedByAP",
                "from_col": "rogue_aps",
                "from_field": "bssid",
                "to_col": "devices",
                "to_field": "ap_mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "listSiteRogueClients": {
        "vertex": "rogue_clients",
        "key_field": "client_mac",
        "edges": [
            {
                "edge_col": "RogueClientDetectedByAP",
                "from_col": "rogue_clients",
                "from_field": "client_mac",
                "to_col": "devices",
                "to_field": "ap_mac",
                "to_key_lookup": "mac",
            },
            {
                "edge_col": "RogueClientOnBSSID",
                "from_col": "rogue_clients",
                "from_field": "client_mac",
                "to_col": "rogue_aps",
                "to_field": "bssid",
            },
        ],
    },
    "searchSiteRogueEvents": {
        "vertex": "rogue_events",
        "key_field": "bssid",
        "edges": [
            {
                "edge_col": "RogueEventBelongsToSite",
                "from_col": "rogue_events",
                "from_field": "bssid",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "RogueEventOnDevice",
                "from_col": "rogue_events",
                "from_field": "bssid",
                "to_col": "devices",
                "to_field": "ap",
                "to_key_lookup": "mac",
            },
        ],
    },
    # Issue #178: Site MxEdge graph mappings
    "listSiteMxEdges": {
        "vertex": "devices",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "MxEdgeBelongsToSite",
                "from_col": "devices",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "MxEdgeBelongsToCluster",
                "from_col": "devices",
                "from_field": "id",
                "to_col": "mxclusters",
                "to_field": "mxcluster_id",
            },
        ],
        "ensure_target_vertices": [("mxcluster_id", "mxclusters")],
    },
    "listSiteMxEdgesStats": {
        "vertex": "mxedge_stats",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "MxEdgeStatsBelongsToSite",
                "from_col": "mxedge_stats",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "searchSiteMistEdgeEvents": {
        "vertex": "mxedge_events",
        "key_field": "mxedge_id",
        "edges": [
            {
                "edge_col": "MxEdgeEventBelongsToSite",
                "from_col": "mxedge_events",
                "from_field": "mxedge_id",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "MxEdgeEventOnDevice",
                "from_col": "mxedge_events",
                "from_field": "mxedge_id",
                "to_col": "devices",
                "to_field": "mxedge_id",
            },
        ],
    },
    # -- Issue #181: Config history, synthetic tests, webhooks, pcaps --
    "searchSiteDeviceConfigHistory": {
        "vertex": "config_history",
        "key_field": "device_mac",
        "edges": [
            {
                "edge_col": "ConfigHistoryForDevice",
                "from_col": "config_history",
                "from_field": "device_mac",
                "to_col": "devices",
                "to_field": "device_mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "searchSiteDeviceLastConfigs": {
        "vertex": "config_history",
        "key_field": "timestamp",
        "edges": [],
    },
    "searchSiteSyntheticTest": {
        "vertex": "synthetic_tests",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "SyntheticTestOnDevice",
                "from_col": "synthetic_tests",
                "from_field": "mac",
                "to_col": "devices",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "searchSiteWebhooksDeliveries": {
        "vertex": "webhook_deliveries",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "WebhookDeliveryFromWebhook",
                "from_col": "webhook_deliveries",
                "from_field": "id",
                "to_col": "webhooks",
                "to_field": "webhook_id",
            },
        ],
    },
    "listSitePacketCaptures": {
        "vertex": "packet_captures",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "PacketCaptureBelongsToSite",
                "from_col": "packet_captures",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listOrgMxTunnels": {
        "vertex": "mx_tunnels",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "MxTunnelUsesCluster",
                "from_col": "mx_tunnels",
                "from_field": "id",
                "to_col": "mxclusters",
                "to_field": "mxcluster_id",
            },
        ],
        "ensure_target_vertices": [("mxcluster_id", "mxclusters")],
    },
    "listOrgAlarmTemplates": {
        "vertex": "alarm_templates",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "AlarmTemplateBelongsToOrg",
                "from_col": "alarm_templates",
                "from_field": "id",
                "to_col": "orgs",
                "to_field": "org_id",
            },
        ],
    },
    "listOrgDeviceProfiles": {
        "vertex": "device_profiles",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "ProfileAppliedToSite",
                "from_col": "device_profiles",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "applies.site_ids",
            },
            {
                "edge_col": "ProfileAppliedToSiteGroup",
                "from_col": "device_profiles",
                "from_field": "id",
                "to_col": "sitegroups",
                "to_field": "applies.sitegroup_ids",
            },
        ],
        "ensure_target_vertices": [
            ("applies.site_ids", "sites"),
            ("applies.sitegroup_ids", "sitegroups"),
        ],
    },
    # -- Tier 2: Event/search entities --
    "searchOrgWanClients": {
        "vertex": "clients",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "ClientConnectedToDevice",
                "from_col": "clients",
                "from_field": "mac",
                "to_col": "devices",
                "to_field": "device_mac",
                "to_key_lookup": "mac",
            },
            {
                "edge_col": "ClientBelongsToSite",
                "from_col": "clients",
                "from_field": "mac",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "searchOrgWirelessClientEvents": {
        "vertex": "client_events",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "ClientEventBelongsToSite",
                "from_col": "client_events",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "ClientEventOnDevice",
                "from_col": "client_events",
                "from_field": "id",
                "to_col": "devices",
                "to_field": "ap",
                "to_key_lookup": "mac",
            },
        ],
    },
    "searchOrgWirelessClientSessions": {
        "vertex": "client_sessions",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "SessionBelongsToSite",
                "from_col": "client_sessions",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "SessionOnWlan",
                "from_col": "client_sessions",
                "from_field": "id",
                "to_col": "wlans",
                "to_field": "wlan_id",
            },
            {
                "edge_col": "SessionOnDevice",
                "from_col": "client_sessions",
                "from_field": "id",
                "to_col": "devices",
                "to_field": "ap",
                "to_key_lookup": "mac",
            },
            {
                "edge_col": "SessionForClient",
                "from_col": "client_sessions",
                "from_field": "id",
                "to_col": "clients",
                "to_field": "client_mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "searchOrgNacClientEvents": {
        "vertex": "nac_events",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "NacEventBelongsToSite",
                "from_col": "nac_events",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "NacEventForClient",
                "from_col": "nac_events",
                "from_field": "id",
                "to_col": "clients",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "searchOrgWanClientEvents": {
        "vertex": "wan_events",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "WanEventBelongsToSite",
                "from_col": "wan_events",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "WanEventForClient",
                "from_col": "wan_events",
                "from_field": "id",
                "to_col": "clients",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "searchOrgMistEdgeEvents": {
        "vertex": "mxedge_events",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "MxEdgeEventBelongsToSite",
                "from_col": "mxedge_events",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "searchOrgOtherDeviceEvents": {
        "vertex": "other_events",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "OtherEventBelongsToSite",
                "from_col": "other_events",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "searchOrgEvents": {
        "vertex": "org_events",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "OrgEventBelongsToSite",
                "from_col": "org_events",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "searchOrgSystemEvents": {
        "vertex": "system_events",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "SystemEventBelongsToSite",
                "from_col": "system_events",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    # -- Tier 3: Stats/telemetry --
    "listOrgDevicesStats": {
        "vertex": "device_stats",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "DeviceStatsBelongsToSite",
                "from_col": "device_stats",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "DeviceStatsForDevice",
                "from_col": "device_stats",
                "from_field": "id",
                "to_col": "devices",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "listOrgMxEdgesStats": {
        "vertex": "mxedge_stats",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "MxEdgeStatsBelongsToSite",
                "from_col": "mxedge_stats",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "searchOrgBgpStats": {
        "vertex": "bgp_stats",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "BgpStatsBelongsToSite",
                "from_col": "bgp_stats",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "searchOrgOspfStats": {
        "vertex": "ospf_stats",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "OspfStatsBelongsToSite",
                "from_col": "ospf_stats",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "searchOrgPeerPathStats": {
        "vertex": "peer_paths",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "PeerPathBelongsToSite",
                "from_col": "peer_paths",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "searchOrgSwOrGwPorts": {
        "vertex": "ports",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "PortBelongsToSite",
                "from_col": "ports",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "PortBelongsToDevice",
                "from_col": "ports",
                "from_field": "id",
                "to_col": "devices",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "searchOrgTunnelsStats": {
        "vertex": "tunnels",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "TunnelBelongsToSite",
                "from_col": "tunnels",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    # -- Tier 4: WxLAN policy --
    "listOrgWxRules": {
        "vertex": "wx_rules",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "WxRuleBelongsToTemplate",
                "from_col": "wx_rules",
                "from_field": "id",
                "to_col": "templates",
                "to_field": "template_id",
            },
            {
                "edge_col": "WxRuleMatchesSrcTag",
                "from_col": "wx_rules",
                "from_field": "id",
                "to_col": "wx_tags",
                "to_field": "src_wxtags",
            },
            {
                "edge_col": "WxRuleAllowsDstTag",
                "from_col": "wx_rules",
                "from_field": "id",
                "to_col": "wx_tags",
                "to_field": "dst_allow_wxtags",
            },
            {
                "edge_col": "WxRuleDeniesDstTag",
                "from_col": "wx_rules",
                "from_field": "id",
                "to_col": "wx_tags",
                "to_field": "dst_deny_wxtags",
            },
        ],
        "ensure_target_vertices": [
            ("src_wxtags", "wx_tags"),
            ("dst_allow_wxtags", "wx_tags"),
            ("dst_deny_wxtags", "wx_tags"),
        ],
    },
    "listOrgWxTags": {"vertex": "wx_tags", "key_field": "id"},
    "listOrgWxTunnels": {"vertex": "mx_tunnels", "key_field": "id"},
    # -- Tier 5: Remaining entities --
    "listOrgTickets": {
        "vertex": "tickets",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "TicketBelongsToSite",
                "from_col": "tickets",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listOrgPacketCaptures": {
        "vertex": "packet_captures",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "PacketCaptureBelongsToSite",
                "from_col": "packet_captures",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listOrgOtherDevices": {
        "vertex": "other_devices",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "OtherDeviceBelongsToSite",
                "from_col": "other_devices",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listOrgEvpnTopologies": {
        "vertex": "evpn_topologies",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "EvpnBelongsToSite",
                "from_col": "evpn_topologies",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "searchOrgAssets": {
        "vertex": "assets",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "AssetBelongsToSite",
                "from_col": "assets",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    # -- Unmapped entities: with edges --
    "listOrgPskPortals": {
        "vertex": "psk_portals",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "PskPortalServesSiteGroup",
                "from_col": "psk_portals",
                "from_field": "id",
                "to_col": "sitegroups",
                "to_field": "sitegroup_ids",
            },
        ],
    },
    "listOrgSuppressedAlarms": {
        "vertex": "suppressed_alarms",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "SuppressedAlarmBelongsToSite",
                "from_col": "suppressed_alarms",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "searchOrgDeviceLastConfigs": {
        "vertex": "device_configs",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "DeviceConfigBelongsToSite",
                "from_col": "device_configs",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "DeviceConfigForDevice",
                "from_col": "device_configs",
                "from_field": "id",
                "to_col": "devices",
                "to_field": "device_mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "listOrgSiteStats": {
        "vertex": "site_stats",
        "key_field": "site_id",
        "edges": [
            {
                "edge_col": "SiteStatsBelongsToSite",
                "from_col": "site_stats",
                "from_field": "site_id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    # -- Unmapped entities: vertex-only (org-level, no site FK) --
    "listOrgAdmins": {"vertex": "admins", "key_field": "id"},
    "listOrgApiTokens": {"vertex": "api_tokens", "key_field": "id"},
    "listOrgSsos": {"vertex": "ssos", "key_field": "id"},
    "listOrgSsoRoles": {"vertex": "sso_roles", "key_field": "id"},
    "listOrgCertificates": {"vertex": "certificates", "key_field": "id"},
    "listOrgAAMWProfiles": {"vertex": "aamw_profiles", "key_field": "id"},
    "listOrgAntivirusProfiles": {"vertex": "av_profiles", "key_field": "id"},
    "listOrgIdpProfiles": {"vertex": "idp_profiles", "key_field": "id"},
    "listOrgSecIntelProfiles": {"vertex": "secIntel_profiles", "key_field": "id"},
}

TEMPLATE_ID_FIELDS = [
    ("rftemplate_id", "rf"),
    ("gatewaytemplate_id", "gateway"),
    ("networktemplate_id", "network"),
    ("aptemplate_id", "ap"),
    ("sitetemplate_id", "site"),
]


class ArangoDBWriter:
    """Write documents to ArangoDB with upsert, graph, and snapshot support."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize ArangoDB connection and ensure database exists."""
        hostname = urlparse(config.arango_host).hostname or "arangodb"
        try:
            socket.getaddrinfo(hostname, None)
        except socket.gaierror as dns_error:
            raise ConnectionError(f"ArangoDB host '{hostname}' not resolvable") from dns_error
        self._client = ArangoClient(hosts=config.arango_host)
        self._config = config
        self._ensure_database()
        self._db = self._client.db(
            config.arango_database,
            username=config.arango_username,
            password=config.arango_password,
        )
        self._ensure_graph()
        logger.info("arango_writer_ready", database=config.arango_database)

    def _ensure_database(self) -> None:
        """Create the misthelper database if it does not exist."""
        sys_db = self._client.db(
            "_system",
            username=self._config.arango_username,
            password=self._config.arango_password,
        )
        if not sys_db.has_database(self._config.arango_database):
            sys_db.create_database(self._config.arango_database)
            logger.info("database_created", name=self._config.arango_database)

    def _ensure_graph(self) -> None:
        """Create or update the network topology graph.

        Uses GRAPH_EDGE_DEFINITIONS (core config/hierarchy only) for the
        named graph visualization.  All edge collections from the full
        EDGE_DEFINITIONS are still created and populated separately.
        """
        if self._db.has_graph(GRAPH_NAME):
            graph = self._db.graph(GRAPH_NAME)
            edge_defs: list[dict] = graph.edge_definitions()  # type: ignore[assignment]
            existing = {d["edge_collection"] for d in edge_defs}
            expected = {d["edge_collection"] for d in GRAPH_EDGE_DEFINITIONS}
            if existing != expected:
                self._db.delete_graph(GRAPH_NAME, drop_collections=False)
                self._db.create_graph(GRAPH_NAME, edge_definitions=GRAPH_EDGE_DEFINITIONS)
                logger.info("graph_updated", name=GRAPH_NAME)
        else:
            self._db.create_graph(GRAPH_NAME, edge_definitions=GRAPH_EDGE_DEFINITIONS)
            logger.info("graph_created", name=GRAPH_NAME)
        self._backfill_snapshot_edges()

    def _ensure_collection(self, name: str) -> Any:
        """Return collection, creating it if needed (edge-aware)."""
        if not self._db.has_collection(name):
            is_edge = name in _EDGE_COLLECTION_NAMES
            self._db.create_collection(name, edge=is_edge)
            logger.info("collection_created", name=name, edge=is_edge)
        return self._db.collection(name)

    def write(self, data: list[dict], collection_name: str, strategy: dict) -> WriteResult:
        """Upsert documents using batch import for performance."""
        collection = self._ensure_collection(collection_name)
        if not data:
            return WriteResult(
                success=True,
                backend="arangodb",
                records_written=0,
                records_failed=0,
            )

        docs = [self._prepare_document(r, strategy) for r in data]
        written, failed = self._batch_import(collection, docs)

        if written > 0:
            self._populate_graph(data, collection_name)

        return WriteResult(
            success=(failed == 0),
            backend="arangodb",
            records_written=written,
            records_failed=failed,
        )

    def _batch_import(
        self,
        collection: Any,
        docs: list[dict],
    ) -> tuple[int, int]:
        """Import documents in batches with on_duplicate=replace."""
        written = 0
        failed = 0
        for start in range(0, len(docs), IMPORT_BATCH_SIZE):
            batch = docs[start : start + IMPORT_BATCH_SIZE]
            try:
                result = collection.import_bulk(
                    batch,
                    on_duplicate="replace",
                )
                written += result.get("created", 0)
                written += result.get("updated", 0)
                failed += result.get("errors", 0)
            except Exception as error:
                failed += len(batch)
                logger.warning(
                    "batch_import_failed",
                    collection=collection.name,
                    batch_size=len(batch),
                    error=str(error),
                )
        logger.info(
            "import_complete",
            collection=collection.name,
            written=written,
            failed=failed,
        )
        return written, failed

    def _prepare_document(self, record: dict, strategy: dict) -> dict:
        """Add _key, timestamps, and clear soft-delete flag."""
        doc = dict(record)
        strategy_type = strategy.get("type", "natural_pk")
        primary_keys = strategy.get("primary_key", ["id"])

        if strategy_type == "auto_increment_with_unique":
            doc["_key"] = str(uuid.uuid4())
        else:
            key_value = doc.get(primary_keys[0], str(uuid.uuid4()))
            doc["_key"] = str(key_value)

        doc["_misthelper_updated_at"] = int(time.time())
        doc["_misthelper_deleted_at"] = None
        return doc

    # -- Graph population ------------------------------------------------

    def _populate_graph(self, data: list[dict], collection_name: str) -> None:
        """Populate graph vertex and edge collections from raw API data."""
        mapping = COLLECTION_VERTEX_MAP.get(collection_name)
        if not mapping:
            return

        vertex_col_name = mapping["vertex"]
        key_field = mapping["key_field"]
        vertex_col = self._ensure_collection(vertex_col_name)

        vertices = self._build_vertices(data, key_field)
        if vertices:
            self._batch_import(vertex_col, vertices)

        self._ensure_org_vertex(data)
        self._ensure_target_vertices(data, mapping)
        self._import_edge_docs(data, key_field, mapping)

        if mapping.get("template_edges"):
            self._build_template_edges(data)

        logger.info("graph_populated", collection=collection_name)

    def _import_edge_docs(
        self,
        data: list[dict],
        key_field: str,
        mapping: dict[str, Any],
    ) -> None:
        """Build and import edge documents for a mapping."""
        for edge_config in mapping.get("edges", []):
            edge_docs = self._build_edges(data, key_field, edge_config)
            if edge_docs:
                edge_col = self._ensure_collection(edge_config["edge_col"])
                self._batch_import(edge_col, edge_docs)

    def _build_vertices(self, data: list[dict], key_field: str) -> list[dict]:
        """Build full vertex documents from raw API records.

        Stores the complete API response in the vertex so graph
        traversals return rich data without joining back to the
        document collection.
        """
        vertices: list[dict] = []
        for record in data:
            key_value = record.get(key_field)
            if not key_value:
                continue
            vertex = dict(record)
            vertex["_key"] = self._sanitize_key(str(key_value))
            vertex["_misthelper_updated_at"] = int(time.time())
            vertices.append(vertex)
        return vertices

    def _build_edges(
        self,
        data: list[dict],
        key_field: str,
        edge_config: dict[str, str],
    ) -> list[dict]:
        """Build edge documents with deterministic keys for idempotent upserts."""
        edges: list[dict] = []
        from_col = edge_config["from_col"]
        to_col = edge_config.get("to_col", "")
        from_field = edge_config["from_field"]
        to_field = edge_config.get("to_field", key_field)

        to_key_lookup = self._build_key_lookup(to_col, edge_config.get("to_key_lookup", ""))

        for record in data:
            from_value = self._resolve_nested_field(record, from_field) if "." in from_field else record.get(from_field)
            to_raw = self._resolve_nested_field(record, to_field) if "." in to_field else record.get(to_field)
            if not from_value or not to_raw:
                continue
            to_values = to_raw if isinstance(to_raw, list) else [to_raw]
            for to_value in to_values:
                if not to_value:
                    continue
                to_key = to_key_lookup.get(str(to_value), str(to_value))
                from_id = f"{from_col}/{self._sanitize_key(str(from_value))}"
                to_id = f"{to_col}/{self._sanitize_key(to_key)}"
                edges.append(
                    {
                        "_key": self._edge_key(from_id, to_id),
                        "_from": from_id,
                        "_to": to_id,
                        "_misthelper_updated_at": int(time.time()),
                    }
                )
        return edges

    def _build_key_lookup(self, collection_name: str, lookup_field: str) -> dict[str, str]:
        """Build a lookup dict mapping a field value to vertex _key."""
        if not lookup_field:
            return {}
        try:
            col = self._db.collection(collection_name)
            cursor = col.all()
            if cursor is None:
                return {}
            lookup: dict[str, str] = {}
            for doc in cursor:  # type: ignore[union-attr]
                if lookup_field in doc:
                    lookup[str(doc[lookup_field])] = doc["_key"]
            return lookup
        except Exception:
            return {}

    def _ensure_org_vertex(self, data: list[dict]) -> None:
        """Create a single org vertex from the first record's org_id."""
        for record in data:
            org_id = record.get("org_id")
            if org_id:
                org_col = self._ensure_collection("orgs")
                org_doc = {
                    "_key": self._sanitize_key(str(org_id)),
                    "org_id": org_id,
                    "_misthelper_updated_at": int(time.time()),
                }
                try:
                    org_col.import_bulk([org_doc], on_duplicate="replace")
                except Exception as error:
                    logger.warning("org_vertex_failed", error=str(error))
                return

    def _ensure_target_vertices(self, data: list[dict], mapping: dict) -> None:
        """Create stub vertices for FK targets that lack their own API call."""
        for fk_field, vertex_col_name in mapping.get("ensure_target_vertices", []):
            col = self._ensure_collection(vertex_col_name)
            stubs: list[dict] = []
            for record in data:
                raw = self._resolve_nested_field(record, fk_field) if "." in fk_field else record.get(fk_field)
                if not raw:
                    continue
                values = raw if isinstance(raw, list) else [raw]
                for value in values:
                    if value:
                        stubs.append(
                            {
                                "_key": self._sanitize_key(str(value)),
                                "_misthelper_updated_at": int(time.time()),
                            }
                        )
            if stubs:
                self._batch_import(col, stubs)

    def _build_template_edges(self, data: list[dict]) -> None:
        """Create TemplateAssignedToSite edges from site template_id fields."""
        edge_col = self._ensure_collection("TemplateAssignedToSite")
        edges: list[dict] = []
        for record in data:
            site_id = record.get("id")
            if not site_id:
                continue
            for template_field, template_type in TEMPLATE_ID_FIELDS:
                template_id = record.get(template_field)
                if not template_id:
                    continue
                from_id = f"templates/{self._sanitize_key(str(template_id))}"
                to_id = f"sites/{self._sanitize_key(str(site_id))}"
                edges.append(
                    {
                        "_key": self._edge_key(from_id, to_id),
                        "_from": from_id,
                        "_to": to_id,
                        "template_type": template_type,
                        "_misthelper_updated_at": int(time.time()),
                    }
                )
        if edges:
            self._batch_import(edge_col, edges)

    @staticmethod
    def _edge_key(from_id: str, to_id: str) -> str:
        """Deterministic edge key from endpoints for idempotent upserts."""
        return hashlib.sha256(
            f"{from_id}:{to_id}".encode(),
        ).hexdigest()[:16]

    @staticmethod
    def _resolve_nested_field(record: dict, field_path: str) -> Any:
        """Resolve dot-separated field paths (e.g., 'matching.site_ids')."""
        parts = field_path.split(".")
        value: Any = record
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value

    @staticmethod
    def _sanitize_key(key: str) -> str:
        """Replace characters invalid in ArangoDB document keys."""
        return key.replace("/", "_").replace(":", "_")

    def mark_absent_as_deleted(self, collection_name: str, current_keys: set[str]) -> None:
        """Soft-delete documents whose keys are absent from current data."""
        if not self._db.has_collection(collection_name):
            return

        collection = self._db.collection(collection_name)
        now = int(time.time())

        for doc in collection.all():  # type: ignore[union-attr]
            key = doc.get("_key")
            already_deleted = doc.get("_misthelper_deleted_at")
            if key not in current_keys and not already_deleted:
                collection.update({"_key": key, "_misthelper_deleted_at": now})
                logger.debug("soft_deleted", collection=collection_name, key=key)

    def snapshot(
        self,
        entity_type: str,
        entity_id: str,
        config_body: dict,
        config_hash: str | None = None,
        trigger: str = "api_pull",
    ) -> bool:
        """Store a config snapshot, skipping if hash is unchanged."""
        if config_hash is None:
            config_hash = hashlib.sha256(json.dumps(config_body, sort_keys=True).encode()).hexdigest()

        collection = self._ensure_collection("config_snapshots")

        cursor = self._db.aql.execute(
            "FOR doc IN config_snapshots FILTER doc.entity_id == @eid SORT doc.timestamp DESC LIMIT 1 RETURN doc",
            bind_vars={"eid": entity_id},
        )
        for existing in cursor:  # type: ignore[union-attr]
            if existing.get("config_hash") == config_hash:
                return False

        snapshot_doc = {
            "_key": str(uuid.uuid4()),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "timestamp": int(time.time()),
            "config_hash": config_hash,
            "config_body": config_body,
            "trigger": trigger,
            "_misthelper_updated_at": int(time.time()),
        }
        collection.insert(snapshot_doc)
        self._create_snapshot_edge(str(snapshot_doc["_key"]), entity_type, entity_id)
        logger.info(
            "snapshot_stored",
            entity_type=entity_type,
            entity_id=entity_id,
            trigger=trigger,
        )
        return True

    def _create_snapshot_edge(
        self,
        snapshot_key: str,
        entity_type: str,
        entity_id: str,
    ) -> None:
        """Create a ConfigSnapshotForEntity edge linking snapshot to entity."""
        vertex_col = ENTITY_TYPE_TO_VERTEX.get(entity_type)
        if not vertex_col:
            return
        from_id = f"config_snapshots/{self._sanitize_key(snapshot_key)}"
        to_id = f"{vertex_col}/{self._sanitize_key(str(entity_id))}"
        edge_col = self._ensure_collection("ConfigSnapshotForEntity")
        edge_doc = {
            "_key": self._edge_key(from_id, to_id),
            "_from": from_id,
            "_to": to_id,
            "entity_type": entity_type,
            "_misthelper_updated_at": int(time.time()),
        }
        try:
            edge_col.import_bulk([edge_doc], on_duplicate="replace")
        except Exception as error:
            logger.warning("snapshot_edge_failed", error=str(error))

    def _backfill_snapshot_edges(self) -> None:
        """Create edges for existing snapshots that lack them."""
        if not self._db.has_collection("config_snapshots"):
            return
        edge_col = self._ensure_collection("ConfigSnapshotForEntity")
        try:
            if edge_col.count() >= self._db.collection("config_snapshots").count():
                return
        except TypeError:
            return

        cursor = self._db.aql.execute(
            "FOR s IN config_snapshots RETURN {  key: s._key, entity_type: s.entity_type, entity_id: s.entity_id}",
        )
        edges: list[dict] = []
        for snap in cursor:  # type: ignore[union-attr]
            vertex_col = ENTITY_TYPE_TO_VERTEX.get(snap["entity_type"] or "")
            if not vertex_col or not snap["entity_id"]:
                continue
            from_id = f"config_snapshots/{self._sanitize_key(snap['key'])}"
            to_id = f"{vertex_col}/{self._sanitize_key(str(snap['entity_id']))}"
            edges.append(
                {
                    "_key": self._edge_key(from_id, to_id),
                    "_from": from_id,
                    "_to": to_id,
                    "entity_type": snap["entity_type"],
                    "_misthelper_updated_at": int(time.time()),
                }
            )
        if edges:
            self._batch_import(edge_col, edges)
            logger.info("snapshot_edges_backfilled", count=len(edges))

    def close(self) -> None:
        """Close the ArangoDB client connection."""
        self._client.close()
        logger.info("arango_writer_closed")
