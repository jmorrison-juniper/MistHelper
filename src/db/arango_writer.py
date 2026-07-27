"""ArangoDBWriter: document store backend for configuration entities.

Handles upserts, graph edge management, soft-deletes, and config snapshots
for the MistHelper polyglot database layer.  Uses batch import for high
throughput on bulk API data pulls.
"""

from __future__ import annotations  # WHY: enable postponed annotation evaluation for typing

import hashlib  # WHY: deterministic keys and snapshot hashes rely on sha256
import json  # WHY: canonical serialisation for snapshot hash comparison
import socket  # WHY: pre-flight DNS check before opening ArangoDB client
import time  # WHY: epoch timestamps stamp every write and snapshot doc
import uuid  # WHY: fallback random keys for auto-increment strategies
from typing import Any  # WHY: type hints for python-arango dynamic returns
from urllib.parse import urlparse  # WHY: extract hostname for DNS pre-flight

import structlog  # WHY: structured logging for observability of writes and edges
from arango import ArangoClient  # type: ignore[attr-defined]  # WHY: python-arango client entrypoint

from . import DatabaseConfig, WriteResult  # WHY: shared config and result dataclasses

logger = structlog.get_logger(__name__)  # WHY: module-scoped logger tags every event

GRAPH_NAME = "mist_network_topology"  # WHY: canonical name for the named graph in ArangoDB
IMPORT_BATCH_SIZE = 5000  # WHY: python-arango import_bulk size that balances memory and throughput

# Core config & hierarchy edges registered in the named graph for visualization.
# Models the Mist config inheritance tree from the OpenAPI spec:
#   Org -> Sitegroups -> Sites -> Devices -> Ports
#   Org -> Templates -> Sites (assigned via site.*template_id fields)
#   Org -> Device Profiles -> Devices (assigned via device.deviceprofile_id)
#   Org -> Config objects (Networks, Services, VPNs, NAC, WxLAN, Security)
#   Org -> Infrastructure (MxClusters, MxTunnels, MxEdges)
# Events, stats, telemetry, clients, and sessions are excluded from the
# graph view but their edge collections are still created and populated.
GRAPH_EDGE_DEFINITIONS = [  # WHY: named-graph edge definitions used to build the topology graph
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
EDGE_DEFINITIONS = [  # WHY: exhaustive edge definitions for every populated edge collection
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
        "edge_collection": "AssetFilterBelongsToSite",
        "from_vertex_collections": ["asset_filters"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "DiscoveredAssetOnMap",
        "from_vertex_collections": ["discovered_assets"],
        "to_vertex_collections": ["maps"],
    },
    {
        "edge_collection": "AssetTrackedByAP",
        "from_vertex_collections": ["assets"],
        "to_vertex_collections": ["devices"],
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
    # -- Issue #177: Routing / network topology --
    {
        "edge_collection": "DeviceHasBGPPeer",
        "from_vertex_collections": ["devices"],
        "to_vertex_collections": ["bgp_stats"],
    },
    {
        "edge_collection": "DeviceHasOSPFNeighbor",
        "from_vertex_collections": ["devices"],
        "to_vertex_collections": ["ospf_stats"],
    },
    {
        "edge_collection": "PortConnectsToDevice",
        "from_vertex_collections": ["ports"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "EVPNTopologyContainsSwitch",
        "from_vertex_collections": ["evpn_topologies"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "DiscoveredSwitchBelongsToSite",
        "from_vertex_collections": ["discovered_switches"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "RrmNeighborBelongsToSite",
        "from_vertex_collections": ["rrm_neighbors"],
        "to_vertex_collections": ["sites"],
    },
    # -- Issue #183: Applications, calls, WAN usage, fingerprints --
    {
        "edge_collection": "ApplicationOnSite",
        "from_vertex_collections": ["applications"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "CallOnDevice",
        "from_vertex_collections": ["calls"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "WanUsageOnDevice",
        "from_vertex_collections": ["wan_usage"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "WanUsagePeerDevice",
        "from_vertex_collections": ["wan_usage"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "TroubleshootCallOnDevice",
        "from_vertex_collections": ["troubleshoot_calls"],
        "to_vertex_collections": ["devices"],
    },
    # -- Issue #185: SLE impacted entity relationships --
    {
        "edge_collection": "SLEMetricForSite",
        "from_vertex_collections": ["sle_metrics"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "SLEImpactedDevice",
        "from_vertex_collections": ["sle_impacted_entities"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "SLEImpactedClient",
        "from_vertex_collections": ["sle_impacted_entities"],
        "to_vertex_collections": ["clients"],
    },
    {
        "edge_collection": "SLEImpactedApplication",
        "from_vertex_collections": ["sle_impacted_entities"],
        "to_vertex_collections": ["applications"],
    },
    {
        "edge_collection": "SLEImpactedBySite",
        "from_vertex_collections": ["sle_impacted_entities"],
        "to_vertex_collections": ["sites"],
    },
    # -- Tier 5: Maps, zones & location --
    {
        "edge_collection": "MapBelongsToSite",
        "from_vertex_collections": ["maps"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "ZoneBelongsToMap",
        "from_vertex_collections": ["zones"],
        "to_vertex_collections": ["maps"],
    },
    {
        "edge_collection": "ZoneBelongsToSite",
        "from_vertex_collections": ["zones"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "RssiZoneBelongsToMap",
        "from_vertex_collections": ["rssizones"],
        "to_vertex_collections": ["maps"],
    },
    {
        "edge_collection": "BeaconOnMap",
        "from_vertex_collections": ["beacons"],
        "to_vertex_collections": ["maps"],
    },
    {
        "edge_collection": "BeaconBelongsToSite",
        "from_vertex_collections": ["beacons"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "VBeaconOnMap",
        "from_vertex_collections": ["vbeacons"],
        "to_vertex_collections": ["maps"],
    },
    {
        "edge_collection": "DeviceOnMap",
        "from_vertex_collections": ["devices"],
        "to_vertex_collections": ["maps"],
    },
    {
        "edge_collection": "ZoneSessionInZone",
        "from_vertex_collections": ["zone_sessions"],
        "to_vertex_collections": ["zones"],
    },
    {
        "edge_collection": "ZoneSessionOnMap",
        "from_vertex_collections": ["zone_sessions"],
        "to_vertex_collections": ["maps"],
    },
    # -- Tier 6: Events & alarms (issue #174) --
    {
        "edge_collection": "ServicePathEventOnDevice",
        "from_vertex_collections": ["service_path_events"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "ServicePathEventUsesVPN",
        "from_vertex_collections": ["service_path_events"],
        "to_vertex_collections": ["vpns"],
    },
    {
        "edge_collection": "ServicePathEventBelongsToSite",
        "from_vertex_collections": ["service_path_events"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "SkyatpEventBelongsToSite",
        "from_vertex_collections": ["skyatp_events"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "RoamingEventBelongsToSite",
        "from_vertex_collections": ["roaming_events"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "RoamingEventOnDevice",
        "from_vertex_collections": ["roaming_events"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "RrmEventBelongsToSite",
        "from_vertex_collections": ["rrm_events"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "RrmEventOnDevice",
        "from_vertex_collections": ["rrm_events"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "AnomalyEventBelongsToSite",
        "from_vertex_collections": ["anomaly_events"],
        "to_vertex_collections": ["sites"],
    },
    # -- Tier 7: Config history, synthetic tests, webhook deliveries (issue #181) --
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
    # -- Tier 8: Site-level WLANs, PSKs, Webhooks, WxLAN policies (Issue #173) --
    {
        "edge_collection": "WxRuleBelongsToSite",
        "from_vertex_collections": ["wx_rules"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "WxTagBelongsToSite",
        "from_vertex_collections": ["wx_tags"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "WxTunnelBelongsToSite",
        "from_vertex_collections": ["mx_tunnels"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "WlanUsesWxTunnel",
        "from_vertex_collections": ["wlans"],
        "to_vertex_collections": ["mx_tunnels"],
    },
    # -- Tier 9: Site-level client relationships (Issue #172) --
    {
        "edge_collection": "ClientUsedPSK",
        "from_vertex_collections": ["clients"],
        "to_vertex_collections": ["psks"],
    },
    {
        "edge_collection": "ClientMatchedNACRule",
        "from_vertex_collections": ["clients"],
        "to_vertex_collections": ["nac_rules"],
    },
    {
        "edge_collection": "ClientEventForClient",
        "from_vertex_collections": ["client_events"],
        "to_vertex_collections": ["clients"],
    },
    {
        "edge_collection": "UnconnectedClientOnMap",
        "from_vertex_collections": ["unconnected_clients"],
        "to_vertex_collections": ["maps"],
    },
    {
        "edge_collection": "UnconnectedClientDetectedByAP",
        "from_vertex_collections": ["unconnected_clients"],
        "to_vertex_collections": ["devices"],
    },
    # -- Tier 10: Site-level device relationships (Issue #171) --
    {
        "edge_collection": "SpectrumAnalysisForDevice",
        "from_vertex_collections": ["spectrum_analysis"],
        "to_vertex_collections": ["devices"],
    },
    # -- Tier 11: Derived config relationships (Issue #184) --
    {
        "edge_collection": "DerivedConfigForSite",
        "from_vertex_collections": [
            "wlans",
            "networks",
            "vpns",
            "services",
            "security_policies",
            "ui_settings",
            "guests",
            "templates",
            "device_profiles",
            "idp_profiles",
            "aamw_profiles",
            "av_profiles",
            "secIntel_profiles",
        ],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "DerivedFromTemplate",
        "from_vertex_collections": [
            "wlans",
            "templates",
            "device_profiles",
        ],
        "to_vertex_collections": ["templates"],
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
_EDGE_COLLECTION_NAMES: set[str] = {str(d["edge_collection"]) for d in EDGE_DEFINITIONS}  # WHY: fast membership test

# Maps entity_type (API function name) to the vertex collection
# that holds the entity.  Used by snapshot() to create
# ConfigSnapshotForEntity edges linking snapshots to their entities.
ENTITY_TYPE_TO_VERTEX: dict[str, str] = {  # WHY: map API function names to vertex collections for snapshot edges
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
    # Issue #176: Site Asset endpoints
    "listSiteAssets": "assets",
    "searchSiteAssets": "assets",
    "listSiteAssetsStats": "assets",
    "listSiteDiscoveredAssets": "discovered_assets",
    "listSiteAssetFilters": "asset_filters",
    # -- Issue #183: Applications, calls, WAN usage, fingerprints --
    "listSiteApps": "applications",
    "searchSiteCalls": "calls",
    "searchSiteWanUsage": "wan_usage",
    "searchOrgClientFingerprints": "fingerprints",
    "listSiteUiSettings": "ui_settings",
    "listSiteTroubleshootCalls": "troubleshoot_calls",
    # -- Issue #185: SLE impacted entity endpoints --
    "listSiteSlesMetrics": "sle_metrics",
    "listSiteSleMetricClassifiers": "sle_classifiers",
    "listSiteSleImpactedAps": "sle_impacted_entities",
    "listSiteSleImpactedSwitches": "sle_impacted_entities",
    "listSiteSleImpactedGateways": "sle_impacted_entities",
    "listSiteSleImpactedInterfaces": "sle_impacted_entities",
    "listSiteSleImpactedChassis": "sle_impacted_entities",
    "listSiteSleImpactedWirelessClients": "sle_impacted_entities",
    "listSiteSleImpactedWiredClients": "sle_impacted_entities",
    "listSiteSleImpactedApplications": "sle_impacted_entities",
    # -- Issue #177: Routing / network topology --
    "searchSiteBgpStats": "bgp_stats",
    "searchSiteOspfStats": "ospf_stats",
    "searchSiteSwOrGwPorts": "ports",
    "listSiteEvpnTopologies": "evpn_topologies",
    "searchSiteDiscoveredSwitches": "discovered_switches",
    "listSiteDiscoveredSwitchesMetrics": "discovered_switch_metrics",
    "searchSiteDiscoveredSwitchesMetrics": "discovered_switch_metrics",
    "listSiteCurrentRrmNeighbors": "rrm_neighbors",
    # -- Issue #175: Maps, zones & location --
    "listSiteMaps": "maps",
    "getSiteMap": "maps",
    "listSiteMapStacks": "map_stacks",
    "listSiteZones": "zones",
    "listSiteZonesStats": "zone_stats",
    "listSiteRssiZones": "rssizones",
    "listSiteRssiZonesStats": "rssizone_stats",
    "listSiteBeacons": "beacons",
    "listSiteVBeacons": "vbeacons",
    "searchSiteZoneSessions": "zone_sessions",
    # -- Issue #174: Site events & alarms --
    "searchSiteAlarms": "alarms",
    "searchSiteDeviceEvents": "events",
    "searchSiteSystemEvents": "system_events",
    "searchSiteOtherDeviceEvents": "other_events",
    "searchSiteSkyatpEvents": "skyatp_events",
    "searchSiteServicePathEvents": "service_path_events",
    "listSiteRoamingEvents": "roaming_events",
    "listSiteRrmEvents": "rrm_events",
    "listSiteAnomalyEvents": "anomaly_events",
    # -- Issue #181: Config history, synthetic tests, webhook deliveries --
    "searchSiteDeviceConfigHistory": "config_history",
    "searchSiteDeviceLastConfigs": "config_history",
    "searchSiteSyntheticTest": "synthetic_tests",
    "searchSiteWebhooksDeliveries": "webhook_deliveries",
    "listSitePacketCaptures": "packet_captures",
    # -- Issue #173: Site-level WLANs, PSKs, Webhooks, WxLAN policies --
    "listSiteWlans": "wlans",
    "listSitePsks": "psks",
    "listSiteWebhooks": "webhooks",
    "listSiteWxRules": "wx_rules",
    "listSiteWxTags": "wx_tags",
    "listSiteWxTunnels": "mx_tunnels",
    # -- Issue #172: Site-level client search endpoints --
    "searchSiteWirelessClients": "clients",
    "searchSiteWiredClients": "clients",
    "searchSiteWanClients": "clients",
    "searchSiteNacClients": "clients",
    "searchSiteNacClientEvents": "nac_events",
    "searchSiteWirelessClientEvents": "client_events",
    "searchSiteWirelessClientSessions": "client_sessions",
    "searchSiteWanClientEvents": "wan_events",
    "listSiteWirelessClientsStats": "clients",
    "listSiteUnconnectedClientStats": "unconnected_clients",
    # -- Issue #171: Site-level device endpoints --
    "searchSiteDevices": "devices",
    "listSiteDevicesStats": "devices",
    "listSiteOtherDevices": "other_devices",
    "listSiteAvailableDeviceVersions": "device_versions",
    "listSiteSpectrumAnalysis": "spectrum_analysis",
    "listSiteDeviceRadioChannels": "radio_channels",
    "listSiteDeviceUpgrades": "device_upgrades",
    # -- Issue #184: Derived config endpoints --
    "listSiteWlansDerived": "wlans",
    "listSiteNetworksDerived": "networks",
    "listSiteVpnsDerived": "vpns",
    "listSiteServicesDerived": "services",
    "listSiteServicePoliciesDerived": "security_policies",
    "listSiteUiSettingDerived": "ui_settings",
    "listSiteAllGuestAuthorizationsDerived": "guests",
    "listSiteApTemplatesDerived": "templates",
    "listSiteRfTemplatesDerived": "templates",
    "listSiteNetworkTemplatesDerived": "templates",
    "listSiteGatewayTemplatesDerived": "templates",
    "listSiteSiteTemplatesDerived": "templates",
    "listSiteDeviceProfilesDerived": "device_profiles",
    "listSiteIdpProfilesDerived": "idp_profiles",
    "listSiteAAMWProfilesDerived": "aamw_profiles",
    "listSiteAntivirusProfilesDerived": "av_profiles",
    "listSiteSecIntelProfilesDerived": "secIntel_profiles",
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
COLLECTION_VERTEX_MAP: dict[str, dict[str, Any]] = {  # WHY: drives graph population for each raw collection
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
    # Issue #176: Site Asset graph mappings
    "listSiteAssets": {
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
    "searchSiteAssets": {
        "vertex": "assets",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "AssetOnMap",
                "from_col": "assets",
                "from_field": "mac",
                "to_col": "maps",
                "to_field": "map_id",
            },
        ],
        "ensure_target_vertices": [("map_id", "maps")],
    },
    "listSiteAssetsStats": {
        "vertex": "assets",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "AssetOnMap",
                "from_col": "assets",
                "from_field": "mac",
                "to_col": "maps",
                "to_field": "map_id",
            },
        ],
        "ensure_target_vertices": [("map_id", "maps")],
    },
    "listSiteDiscoveredAssets": {
        "vertex": "discovered_assets",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "DiscoveredAssetOnMap",
                "from_col": "discovered_assets",
                "from_field": "id",
                "to_col": "maps",
                "to_field": "map_id",
            },
        ],
        "ensure_target_vertices": [("map_id", "maps")],
    },
    "listSiteAssetFilters": {
        "vertex": "asset_filters",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "AssetFilterBelongsToSite",
                "from_col": "asset_filters",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    # -- Issue #183: Applications, calls, WAN usage, fingerprints --
    "listSiteApps": {
        "vertex": "applications",
        "key_field": "key",
        "edges": [],
    },
    "searchSiteCalls": {
        "vertex": "calls",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "CallOnDevice",
                "from_col": "calls",
                "from_field": "mac",
                "to_col": "devices",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "searchSiteWanUsage": {
        "vertex": "wan_usage",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "WanUsageOnDevice",
                "from_col": "wan_usage",
                "from_field": "mac",
                "to_col": "devices",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
            {
                "edge_col": "WanUsagePeerDevice",
                "from_col": "wan_usage",
                "from_field": "peer_mac",
                "to_col": "devices",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "searchOrgClientFingerprints": {
        "vertex": "fingerprints",
        "key_field": "mac",
        "edges": [],
    },
    "listSiteUiSettings": {
        "vertex": "ui_settings",
        "key_field": "id",
        "edges": [],
    },
    "listSiteTroubleshootCalls": {
        "vertex": "troubleshoot_calls",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "TroubleshootCallOnDevice",
                "from_col": "troubleshoot_calls",
                "from_field": "mac",
                "to_col": "devices",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    # -- Issue #185: SLE impacted entity endpoints --
    "listSiteSleImpactedAps": {
        "vertex": "sle_impacted_entities",
        "key_field": "ap_mac",
        "edges": [
            {
                "edge_col": "SLEImpactedDevice",
                "from_col": "sle_impacted_entities",
                "from_field": "ap_mac",
                "to_col": "devices",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "listSiteSleImpactedSwitches": {
        "vertex": "sle_impacted_entities",
        "key_field": "switch_mac",
        "edges": [
            {
                "edge_col": "SLEImpactedDevice",
                "from_col": "sle_impacted_entities",
                "from_field": "switch_mac",
                "to_col": "devices",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "listSiteSleImpactedGateways": {
        "vertex": "sle_impacted_entities",
        "key_field": "gateway_mac",
        "edges": [
            {
                "edge_col": "SLEImpactedDevice",
                "from_col": "sle_impacted_entities",
                "from_field": "gateway_mac",
                "to_col": "devices",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "listSiteSleImpactedInterfaces": {
        "vertex": "sle_impacted_entities",
        "key_field": "switch_mac",
        "edges": [
            {
                "edge_col": "SLEImpactedDevice",
                "from_col": "sle_impacted_entities",
                "from_field": "switch_mac",
                "to_col": "devices",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "listSiteSleImpactedChassis": {
        "vertex": "sle_impacted_entities",
        "key_field": "switch_mac",
        "edges": [
            {
                "edge_col": "SLEImpactedDevice",
                "from_col": "sle_impacted_entities",
                "from_field": "switch_mac",
                "to_col": "devices",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "listSiteSleImpactedWirelessClients": {
        "vertex": "sle_impacted_entities",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "SLEImpactedClient",
                "from_col": "sle_impacted_entities",
                "from_field": "mac",
                "to_col": "clients",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "listSiteSleImpactedWiredClients": {
        "vertex": "sle_impacted_entities",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "SLEImpactedClient",
                "from_col": "sle_impacted_entities",
                "from_field": "mac",
                "to_col": "clients",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "listSiteSleImpactedApplications": {
        "vertex": "sle_impacted_entities",
        "key_field": "app",
        "edges": [
            {
                "edge_col": "SLEImpactedApplication",
                "from_col": "sle_impacted_entities",
                "from_field": "app",
                "to_col": "applications",
                "to_field": "key",
            },
        ],
    },
    # -- Issue #177: Routing / network topology --
    "searchSiteBgpStats": {
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
            {
                "edge_col": "DeviceHasBGPPeer",
                "from_col": "devices",
                "from_field": "mac",
                "to_col": "bgp_stats",
                "to_field": "id",
                "from_key_lookup": "mac",
            },
        ],
    },
    "searchSiteOspfStats": {
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
            {
                "edge_col": "DeviceHasOSPFNeighbor",
                "from_col": "devices",
                "from_field": "mac",
                "to_col": "ospf_stats",
                "to_field": "id",
                "from_key_lookup": "mac",
            },
        ],
    },
    "searchSiteSwOrGwPorts": {
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
            {
                "edge_col": "PortConnectsToDevice",
                "from_col": "ports",
                "from_field": "id",
                "to_col": "devices",
                "to_field": "neighbor_mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "listSiteEvpnTopologies": {
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
    "searchSiteDiscoveredSwitches": {
        "vertex": "discovered_switches",
        "key_field": "system_name",
        "edges": [
            {
                "edge_col": "DiscoveredSwitchBelongsToSite",
                "from_col": "discovered_switches",
                "from_field": "system_name",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listSiteDiscoveredSwitchesMetrics": {
        "vertex": "discovered_switch_metrics",
        "key_field": "id",
        "edges": [],
    },
    "searchSiteDiscoveredSwitchesMetrics": {
        "vertex": "discovered_switch_metrics",
        "key_field": "system_name",
        "edges": [],
    },
    "listSiteCurrentRrmNeighbors": {
        "vertex": "rrm_neighbors",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "RrmNeighborBelongsToSite",
                "from_col": "rrm_neighbors",
                "from_field": "mac",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    # -- Issue #175: Maps, zones & location --
    "listSiteMaps": {
        "vertex": "maps",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "MapBelongsToSite",
                "from_col": "maps",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "getSiteMap": {
        "vertex": "maps",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "MapBelongsToSite",
                "from_col": "maps",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listSiteMapStacks": {
        "vertex": "map_stacks",
        "key_field": "id",
        "edges": [],
    },
    "listSiteZones": {
        "vertex": "zones",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "ZoneBelongsToMap",
                "from_col": "zones",
                "from_field": "id",
                "to_col": "maps",
                "to_field": "map_id",
            },
            {
                "edge_col": "ZoneBelongsToSite",
                "from_col": "zones",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
        "ensure_target_vertices": [("map_id", "maps")],
    },
    "listSiteZonesStats": {
        "vertex": "zone_stats",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "ZoneBelongsToMap",
                "from_col": "zones",
                "from_field": "id",
                "to_col": "maps",
                "to_field": "map_id",
            },
        ],
        "ensure_target_vertices": [("map_id", "maps"), ("id", "zones")],
    },
    "listSiteRssiZones": {
        "vertex": "rssizones",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "RssiZoneBelongsToMap",
                "from_col": "rssizones",
                "from_field": "id",
                "to_col": "maps",
                "to_field": "map_id",
            },
        ],
        "ensure_target_vertices": [("map_id", "maps")],
    },
    "listSiteRssiZonesStats": {
        "vertex": "rssizone_stats",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "RssiZoneBelongsToMap",
                "from_col": "rssizones",
                "from_field": "id",
                "to_col": "maps",
                "to_field": "map_id",
            },
        ],
        "ensure_target_vertices": [("map_id", "maps"), ("id", "rssizones")],
    },
    "listSiteBeacons": {
        "vertex": "beacons",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "BeaconOnMap",
                "from_col": "beacons",
                "from_field": "id",
                "to_col": "maps",
                "to_field": "map_id",
            },
            {
                "edge_col": "BeaconBelongsToSite",
                "from_col": "beacons",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
        "ensure_target_vertices": [("map_id", "maps")],
    },
    "listSiteVBeacons": {
        "vertex": "vbeacons",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "VBeaconOnMap",
                "from_col": "vbeacons",
                "from_field": "id",
                "to_col": "maps",
                "to_field": "map_id",
            },
        ],
        "ensure_target_vertices": [("map_id", "maps")],
    },
    "searchSiteZoneSessions": {
        "vertex": "zone_sessions",
        "key_field": "zone_id",
        "edges": [
            {
                "edge_col": "ZoneSessionInZone",
                "from_col": "zone_sessions",
                "from_field": "zone_id",
                "to_col": "zones",
                "to_field": "zone_id",
            },
            {
                "edge_col": "ZoneSessionOnMap",
                "from_col": "zone_sessions",
                "from_field": "zone_id",
                "to_col": "maps",
                "to_field": "map_id",
            },
        ],
        "ensure_target_vertices": [("zone_id", "zones"), ("map_id", "maps")],
    },
    # -- Issue #174: Site events & alarms --
    "searchSiteAlarms": {
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
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "searchSiteDeviceEvents": {
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
    "searchSiteSystemEvents": {
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
    "searchSiteOtherDeviceEvents": {
        "vertex": "other_events",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "OtherEventBelongsToSite",
                "from_col": "other_events",
                "from_field": "mac",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "searchSiteSkyatpEvents": {
        "vertex": "skyatp_events",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "SkyatpEventBelongsToSite",
                "from_col": "skyatp_events",
                "from_field": "mac",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "searchSiteServicePathEvents": {
        "vertex": "service_path_events",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "ServicePathEventBelongsToSite",
                "from_col": "service_path_events",
                "from_field": "mac",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "ServicePathEventOnDevice",
                "from_col": "service_path_events",
                "from_field": "mac",
                "to_col": "devices",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
            {
                "edge_col": "ServicePathEventUsesVPN",
                "from_col": "service_path_events",
                "from_field": "mac",
                "to_col": "vpns",
                "to_field": "vpn_name",
            },
        ],
        "ensure_target_vertices": [("vpn_name", "vpns")],
    },
    "listSiteRoamingEvents": {
        "vertex": "roaming_events",
        "key_field": "client_mac",
        "edges": [
            {
                "edge_col": "RoamingEventBelongsToSite",
                "from_col": "roaming_events",
                "from_field": "client_mac",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "RoamingEventOnDevice",
                "from_col": "roaming_events",
                "from_field": "client_mac",
                "to_col": "devices",
                "to_field": "ap",
                "to_key_lookup": "mac",
            },
        ],
    },
    "listSiteRrmEvents": {
        "vertex": "rrm_events",
        "key_field": "ap_id",
        "edges": [
            {
                "edge_col": "RrmEventBelongsToSite",
                "from_col": "rrm_events",
                "from_field": "ap_id",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "RrmEventOnDevice",
                "from_col": "rrm_events",
                "from_field": "ap_id",
                "to_col": "devices",
                "to_field": "ap_id",
            },
        ],
    },
    "listSiteAnomalyEvents": {
        "vertex": "anomaly_events",
        "key_field": "timestamp",
        "edges": [
            {
                "edge_col": "AnomalyEventBelongsToSite",
                "from_col": "anomaly_events",
                "from_field": "timestamp",
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
    # -- Issue #181: Config history, synthetic tests, webhook deliveries --
    "searchSiteDeviceConfigHistory": {
        "vertex": "config_history",
        "key_field": "timestamp",
        "edges": [
            {
                "edge_col": "ConfigHistoryForDevice",
                "from_col": "config_history",
                "from_field": "timestamp",
                "to_col": "devices",
                "to_field": "device_mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "searchSiteDeviceLastConfigs": {
        "vertex": "config_history",
        "key_field": "timestamp",
        "edges": [
            {
                "edge_col": "ConfigHistoryForDevice",
                "from_col": "config_history",
                "from_field": "timestamp",
                "to_col": "devices",
                "to_field": "device_mac",
                "to_key_lookup": "mac",
            },
        ],
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
                "edge_col": "PacketCaptureOnDevice",
                "from_col": "packet_captures",
                "from_field": "id",
                "to_col": "devices",
                "to_field": "ap_macs",
                "to_key_lookup": "mac",
            },
            {
                "edge_col": "PacketCaptureBelongsToSite",
                "from_col": "packet_captures",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    # -- Issue #173: Site-level WLANs, PSKs, Webhooks, WxLAN policies --
    "listSiteWlans": {
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
                "edge_col": "WlanUsesWxTunnel",
                "from_col": "wlans",
                "from_field": "id",
                "to_col": "mx_tunnels",
                "to_field": "wxtunnel_id",
            },
        ],
    },
    "listSitePsks": {
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
    "listSiteWebhooks": {
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
    "listSiteWxRules": {
        "vertex": "wx_rules",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "WxRuleBelongsToSite",
                "from_col": "wx_rules",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
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
    "listSiteWxTags": {
        "vertex": "wx_tags",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "WxTagBelongsToSite",
                "from_col": "wx_tags",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listSiteWxTunnels": {
        "vertex": "mx_tunnels",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "WxTunnelBelongsToSite",
                "from_col": "mx_tunnels",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    # -- Issue #172: Site-level client search endpoints --
    "searchSiteWirelessClients": {
        "vertex": "clients",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "ClientConnectedToDevice",
                "from_col": "clients",
                "from_field": "mac",
                "to_col": "devices",
                "to_field": "last_ap",
                "to_key_lookup": "mac",
            },
            {
                "edge_col": "ClientConnectedToWlan",
                "from_col": "clients",
                "from_field": "mac",
                "to_col": "wlans",
                "to_field": "last_wlan_id",
            },
            {
                "edge_col": "ClientBelongsToSite",
                "from_col": "clients",
                "from_field": "mac",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "ClientUsedPSK",
                "from_col": "clients",
                "from_field": "mac",
                "to_col": "psks",
                "to_field": "last_psk_id",
            },
        ],
    },
    "searchSiteWiredClients": {
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
    "searchSiteWanClients": {
        "vertex": "clients",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "ClientBelongsToSite",
                "from_col": "clients",
                "from_field": "mac",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "searchSiteNacClients": {
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
            {
                "edge_col": "ClientMatchedNACRule",
                "from_col": "clients",
                "from_field": "mac",
                "to_col": "nac_rules",
                "to_field": "last_nacrule_id",
            },
        ],
    },
    "searchSiteNacClientEvents": {
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
    "searchSiteWirelessClientEvents": {
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
            {
                "edge_col": "ClientEventForClient",
                "from_col": "client_events",
                "from_field": "id",
                "to_col": "clients",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
        "ensure_target_vertices": [("mac", "clients")],
    },
    "searchSiteWirelessClientSessions": {
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
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "searchSiteWanClientEvents": {
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
                "to_field": "wcid",
                "to_key_lookup": "mac",
            },
        ],
    },
    "listSiteUnconnectedClientStats": {
        "vertex": "unconnected_clients",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "UnconnectedClientOnMap",
                "from_col": "unconnected_clients",
                "from_field": "mac",
                "to_col": "maps",
                "to_field": "map_id",
            },
            {
                "edge_col": "UnconnectedClientDetectedByAP",
                "from_col": "unconnected_clients",
                "from_field": "mac",
                "to_col": "devices",
                "to_field": "ap_mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    # -- Issue #171: Site-level device endpoints --
    "listSiteDevices": {
        "vertex": "devices",
        "key_field": "id",
        "edges": [
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
                "edge_col": "DeviceOnMap",
                "from_col": "devices",
                "from_field": "id",
                "to_col": "maps",
                "to_field": "map_id",
            },
        ],
        "ensure_target_vertices": [
            ("deviceprofile_id", "device_profiles"),
            ("map_id", "maps"),
        ],
    },
    "searchSiteDevices": {
        "vertex": "devices",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "SiteContainsDevice",
                "from_col": "sites",
                "from_field": "site_id",
                "to_col": "devices",
            },
        ],
    },
    "listSiteDevicesStats": {
        "vertex": "devices",
        "key_field": "id",
        "edges": [
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
        ],
    },
    "listSiteOtherDevices": {
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
    "listSiteAvailableDeviceVersions": {
        "vertex": "device_versions",
        "key_field": "model",
    },
    "listSiteSpectrumAnalysis": {
        "vertex": "spectrum_analysis",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "SpectrumAnalysisForDevice",
                "from_col": "spectrum_analysis",
                "from_field": "mac",
                "to_col": "devices",
                "to_field": "mac",
                "to_key_lookup": "mac",
            },
        ],
    },
    "listSiteDeviceRadioChannels": {
        "vertex": "radio_channels",
        "key_field": "key",
    },
    "listSiteDeviceUpgrades": {
        "vertex": "device_upgrades",
        "key_field": "id",
    },
    # -- Issue #184: Derived config (effective merged config at site) --
    "listSiteWlansDerived": {
        "vertex": "wlans",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "DerivedConfigForSite",
                "from_col": "wlans",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
            {
                "edge_col": "DerivedFromTemplate",
                "from_col": "wlans",
                "from_field": "id",
                "to_col": "templates",
                "to_field": "wlan_template_id",
            },
        ],
    },
    "listSiteNetworksDerived": {
        "vertex": "networks",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "DerivedConfigForSite",
                "from_col": "networks",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listSiteVpnsDerived": {
        "vertex": "vpns",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "DerivedConfigForSite",
                "from_col": "vpns",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listSiteServicesDerived": {
        "vertex": "services",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "DerivedConfigForSite",
                "from_col": "services",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listSiteServicePoliciesDerived": {
        "vertex": "security_policies",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "DerivedConfigForSite",
                "from_col": "security_policies",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listSiteUiSettingDerived": {
        "vertex": "ui_settings",
        "key_field": "key",
    },
    "listSiteAllGuestAuthorizationsDerived": {
        "vertex": "guests",
        "key_field": "mac",
        "edges": [
            {
                "edge_col": "DerivedConfigForSite",
                "from_col": "guests",
                "from_field": "mac",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listSiteApTemplatesDerived": {
        "vertex": "templates",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "DerivedConfigForSite",
                "from_col": "templates",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listSiteRfTemplatesDerived": {
        "vertex": "templates",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "DerivedConfigForSite",
                "from_col": "templates",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listSiteNetworkTemplatesDerived": {
        "vertex": "templates",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "DerivedConfigForSite",
                "from_col": "templates",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listSiteGatewayTemplatesDerived": {
        "vertex": "templates",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "DerivedConfigForSite",
                "from_col": "templates",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listSiteSiteTemplatesDerived": {
        "vertex": "templates",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "DerivedConfigForSite",
                "from_col": "templates",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listSiteDeviceProfilesDerived": {
        "vertex": "device_profiles",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "DerivedConfigForSite",
                "from_col": "device_profiles",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listSiteIdpProfilesDerived": {
        "vertex": "idp_profiles",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "DerivedConfigForSite",
                "from_col": "idp_profiles",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listSiteAAMWProfilesDerived": {
        "vertex": "aamw_profiles",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "DerivedConfigForSite",
                "from_col": "aamw_profiles",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listSiteAntivirusProfilesDerived": {
        "vertex": "av_profiles",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "DerivedConfigForSite",
                "from_col": "av_profiles",
                "from_field": "id",
                "to_col": "sites",
                "to_field": "site_id",
            },
        ],
    },
    "listSiteSecIntelProfilesDerived": {
        "vertex": "secIntel_profiles",
        "key_field": "id",
        "edges": [
            {
                "edge_col": "DerivedConfigForSite",
                "from_col": "secIntel_profiles",
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

TEMPLATE_ID_FIELDS = [  # WHY: pairs each site template FK field with its template_type label for edge docs
    ("rftemplate_id", "rf"),
    ("gatewaytemplate_id", "gateway"),
    ("networktemplate_id", "network"),
    ("aptemplate_id", "ap"),
    ("sitetemplate_id", "site"),
]


class ArangoDBWriter:  # WHY: primary writer class for the ArangoDB polyglot backend
    """Write documents to ArangoDB with upsert, graph, and snapshot support."""

    def __init__(self, config: DatabaseConfig) -> None:  # WHY: constructor wires config and connects to the server
        """Initialize ArangoDB connection and ensure database exists."""
        hostname = urlparse(config.arango_host).hostname or "arangodb"  # WHY: parse URL to isolate host for DNS check
        self._preflight_dns(hostname)  # WHY: fail fast when host cannot resolve so callers see a clear error
        self._client = ArangoClient(hosts=config.arango_host)  # WHY: python-arango client is the entry to all ops
        self._config = config  # WHY: retain config for later system-db reconnects and diagnostics
        self._ensure_database()  # WHY: create the target database when the server is empty
        self._db = self._client.db(  # WHY: reopen the client bound to the target database
            config.arango_database,
            username=config.arango_username,
            password=config.arango_password,
        )
        self._ensure_graph()  # WHY: named graph must exist before any edge is imported
        logger.info("arango_writer_ready", database=config.arango_database)  # WHY: observability marker

    @staticmethod
    def _preflight_dns(hostname: str) -> None:  # WHY: guard clause factored out of __init__ to keep it short
        """Raise ConnectionError early if the ArangoDB hostname does not resolve."""
        try:
            socket.getaddrinfo(hostname, None)  # WHY: cheap DNS lookup surfaces misconfigurations up-front
        except socket.gaierror as dns_error:  # WHY: convert socket-level failure into a domain error
            raise ConnectionError(f"ArangoDB host '{hostname}' not resolvable") from dns_error

    def _ensure_database(self) -> None:  # WHY: idempotent bootstrap of the misthelper database
        """Create the misthelper database if it does not exist."""
        sys_db = self._client.db(  # WHY: system database is the only place create_database can run
            "_system",
            username=self._config.arango_username,
            password=self._config.arango_password,
        )
        if sys_db.has_database(self._config.arango_database):  # WHY: guard clause skips existing databases
            return
        sys_db.create_database(self._config.arango_database)  # WHY: create when missing
        logger.info("database_created", name=self._config.arango_database)  # WHY: log creation for auditing

    def _ensure_graph(self) -> None:  # WHY: bootstrap or refresh the named topology graph
        """Create or update the network topology graph.

        Uses GRAPH_EDGE_DEFINITIONS (core config/hierarchy only) for the
        named graph visualization.  All edge collections from the full
        EDGE_DEFINITIONS are still created and populated separately.
        """
        if self._db.has_graph(GRAPH_NAME):  # WHY: branch on whether the graph already exists
            self._refresh_graph_if_stale()  # WHY: refresh edge defs when they drift from the spec
        else:
            self._db.create_graph(GRAPH_NAME, edge_definitions=GRAPH_EDGE_DEFINITIONS)  # WHY: create fresh graph
            logger.info("graph_created", name=GRAPH_NAME)  # WHY: audit trail for graph creation
        self._backfill_snapshot_edges()  # WHY: legacy snapshots may lack edges; fill them in on boot

    def _refresh_graph_if_stale(self) -> None:  # WHY: extracted helper trims _ensure_graph blocks
        """Recreate the named graph when live edge definitions drift from the expected set."""
        graph = self._db.graph(GRAPH_NAME)  # WHY: fetch handle so we can read current edge defs
        edge_defs: list[dict] = graph.edge_definitions()  # type: ignore[assignment]  # WHY: live definitions from server
        existing = {d["edge_collection"] for d in edge_defs}  # WHY: set-compare against the expected set
        expected = {d["edge_collection"] for d in GRAPH_EDGE_DEFINITIONS}  # WHY: canonical expected edges
        if existing == expected:  # WHY: guard clause avoids unnecessary teardown when in sync
            return
        self._db.delete_graph(GRAPH_NAME, drop_collections=False)  # WHY: preserve underlying collection data
        self._db.create_graph(GRAPH_NAME, edge_definitions=GRAPH_EDGE_DEFINITIONS)  # WHY: recreate with new defs
        logger.info("graph_updated", name=GRAPH_NAME)  # WHY: audit trail for graph refresh

    def _ensure_collection(self, name: str) -> Any:  # WHY: idempotent collection creation with edge-awareness
        """Return collection, creating it if needed (edge-aware)."""
        if not self._db.has_collection(name):  # WHY: guard clause skips existing collections
            is_edge = name in _EDGE_COLLECTION_NAMES  # WHY: edge collections require the edge=True flag
            self._db.create_collection(name, edge=is_edge)  # WHY: create with correct edge flag
            logger.info("collection_created", name=name, edge=is_edge)  # WHY: audit trail
        return self._db.collection(name)  # WHY: return live handle for the caller

    def write(self, data: list[dict], collection_name: str, strategy: dict) -> WriteResult:  # WHY: public write API
        """Upsert documents using batch import for performance."""
        collection = self._ensure_collection(collection_name)  # WHY: guarantee target collection exists first
        if not data:  # WHY: empty payload returns a trivially successful WriteResult
            return WriteResult(  # WHY: zero-record success avoids downstream branches on empty input
                success=True,
                backend="arangodb",
                records_written=0,
                records_failed=0,
            )
        docs = [self._prepare_document(r, strategy) for r in data]  # WHY: stamp keys and timestamps up-front
        written, failed = self._batch_import(collection, docs)  # WHY: batched import with replace semantics
        if written > 0:  # WHY: only rebuild graph when at least one row landed
            self._populate_graph(data, collection_name)  # WHY: keep graph consistent with document state
        return WriteResult(  # WHY: return typed result so router can aggregate across backends
            success=(failed == 0),
            backend="arangodb",
            records_written=written,
            records_failed=failed,
        )

    def _batch_import(self, collection: Any, docs: list[dict]) -> tuple[int, int]:  # WHY: chunked import primitive
        """Import documents in batches with on_duplicate=replace."""
        written, failed = self._sum_batch_results(collection, docs)  # WHY: delegate loop to helper for length
        logger.info(  # WHY: single completion log per collection keeps output readable
            "import_complete",
            collection=collection.name,
            written=written,
            failed=failed,
        )
        return written, failed  # WHY: caller aggregates written/failed across many collections

    def _sum_batch_results(self, collection: Any, docs: list[dict]) -> tuple[int, int]:  # WHY: loop helper
        """Iterate through IMPORT_BATCH_SIZE chunks and sum written/failed counters."""
        written = 0  # WHY: running total of successfully imported docs
        failed = 0  # WHY: running total of failed docs
        for start in range(0, len(docs), IMPORT_BATCH_SIZE):  # WHY: window through docs in fixed-size chunks
            batch = docs[start : start + IMPORT_BATCH_SIZE]  # WHY: slice out this batch
            batch_written, batch_failed = self._import_single_batch(collection, batch)  # WHY: import one batch
            written += batch_written  # WHY: accumulate successes
            failed += batch_failed  # WHY: accumulate failures
        return written, failed  # WHY: expose totals to caller

    @staticmethod
    def _import_single_batch(collection: Any, batch: list[dict]) -> tuple[int, int]:  # WHY: try/except localised
        """Import a single batch and return (written, failed) counters for it."""
        try:
            result = collection.import_bulk(batch, on_duplicate="replace")  # WHY: python-arango bulk API
        except Exception as error:  # WHY: any driver-side failure marks the whole batch as failed
            logger.warning(  # WHY: preserve original diagnostics for operators
                "batch_import_failed",
                collection=collection.name,
                batch_size=len(batch),
                error=str(error),
            )
            return 0, len(batch)  # WHY: nothing succeeded so all rows count as failed
        written = result.get("created", 0) + result.get("updated", 0)  # WHY: driver reports created+updated
        failed = result.get("errors", 0)  # WHY: driver reports errors separately
        return written, failed  # WHY: hand counters back to the aggregator

    def _prepare_document(self, record: dict, strategy: dict) -> dict:  # WHY: shape a raw record for storage
        """Add _key, timestamps, and clear soft-delete flag."""
        doc = dict(record)  # WHY: copy so the caller's dict is never mutated
        strategy_type = strategy.get("type", "natural_pk")  # WHY: default to natural PK when unspecified
        primary_keys = strategy.get("primary_key", ["id"])  # WHY: default to 'id' when unspecified
        doc["_key"] = self._compute_key(doc, strategy_type, primary_keys)  # WHY: table-driven key selection
        now = int(time.time())  # WHY: single timestamp for both timestamp fields
        doc["_misthelper_updated_at"] = now  # WHY: track last write for staleness checks
        doc["_misthelper_deleted_at"] = None  # WHY: explicitly clear soft-delete on any fresh write
        return doc  # WHY: return storage-ready document

    @staticmethod
    def _compute_key(doc: dict, strategy_type: str, primary_keys: list[str]) -> str:  # WHY: key resolution helper
        """Return the _key that _prepare_document should assign for this strategy."""
        if strategy_type == "auto_increment_with_unique":  # WHY: auto-increment strategies always get UUIDs
            return str(uuid.uuid4())  # WHY: unique key when no natural PK is available
        key_value = doc.get(primary_keys[0], str(uuid.uuid4()))  # WHY: fall back to UUID when PK is missing
        return str(key_value)  # WHY: ArangoDB keys must be strings

    # -- Graph population ------------------------------------------------

    def _populate_graph(self, data: list[dict], collection_name: str) -> None:  # WHY: rebuild graph after writes
        """Populate graph vertex and edge collections from raw API data."""
        mapping = COLLECTION_VERTEX_MAP.get(collection_name)  # WHY: table-driven dispatch to graph rules
        if not mapping:  # WHY: skip collections with no graph mapping
            return
        vertex_col_name = mapping["vertex"]  # WHY: destination vertex collection
        key_field = mapping["key_field"]  # WHY: field used to build vertex _key
        vertex_col = self._ensure_collection(vertex_col_name)  # WHY: ensure destination vertex collection exists
        vertices = self._build_vertices(data, key_field)  # WHY: shape vertex docs from raw records
        if vertices:  # WHY: only import when we actually have vertices to write
            self._batch_import(vertex_col, vertices)  # WHY: bulk import the vertices
        self._ensure_org_vertex(data)  # WHY: every graph write also anchors the org vertex
        self._ensure_target_vertices(data, mapping)  # WHY: create stub vertices for FK targets lacking API pulls
        self._import_edge_docs(data, key_field, mapping)  # WHY: build and import edges declared by the mapping
        if mapping.get("template_edges"):  # WHY: sites need template->site edges wired separately
            self._build_template_edges(data)  # WHY: hydrate template->site edges from FK fields
        logger.info("graph_populated", collection=collection_name)  # WHY: audit event per collection

    def _import_edge_docs(self, data: list[dict], key_field: str, mapping: dict[str, Any]) -> None:  # WHY: helper
        """Build and import edge documents for a mapping."""
        for edge_config in mapping.get("edges", []):  # WHY: each mapping may declare many edge builders
            edge_docs = self._build_edges(data, key_field, edge_config)  # WHY: build docs from this config
            if not edge_docs:  # WHY: guard clause skips empty batches
                continue
            edge_col = self._ensure_collection(edge_config["edge_col"])  # WHY: ensure destination edge collection
            self._batch_import(edge_col, edge_docs)  # WHY: import the batch

    def _build_vertices(self, data: list[dict], key_field: str) -> list[dict]:  # WHY: shape vertex documents
        """Build full vertex documents from raw API records.

        Stores the complete API response in the vertex so graph
        traversals return rich data without joining back to the
        document collection.
        """
        vertices: list[dict] = []  # WHY: accumulator for output list
        for record in data:  # WHY: shape one vertex per record with a valid key
            key_value = record.get(key_field)  # WHY: identify record via its declared key field
            if not key_value:  # WHY: guard clause skips records without an identifying key
                continue
            vertex = dict(record)  # WHY: copy so we can safely mutate _key and timestamp
            vertex["_key"] = self._sanitize_key(str(key_value))  # WHY: keys must satisfy Arango rules
            vertex["_misthelper_updated_at"] = int(time.time())  # WHY: stamp for staleness tracking
            vertices.append(vertex)  # WHY: emit shaped vertex
        return vertices  # WHY: caller batch-imports the list

    def _build_edges(  # WHY: build edge documents with deterministic keys for idempotency
        self,
        data: list[dict],
        key_field: str,
        edge_config: dict[str, str],
    ) -> list[dict]:
        """Build edge documents with deterministic keys for idempotent upserts."""
        to_col = edge_config.get("to_col", "")  # WHY: destination collection identifier
        to_key_lookup = self._build_key_lookup(to_col, edge_config.get("to_key_lookup", ""))  # WHY: FK->key map
        edges: list[dict] = []  # WHY: accumulator for output edges
        for record in data:  # WHY: emit zero or more edges per record
            edges.extend(self._edges_for_record(record, key_field, edge_config, to_key_lookup))  # WHY: helper
        return edges  # WHY: return combined edges for batch import

    def _edges_for_record(  # WHY: per-record helper flattens the previously-nested loops
        self,
        record: dict,
        key_field: str,
        edge_config: dict[str, str],
        to_key_lookup: dict[str, str],
    ) -> list[dict]:
        """Return zero or more edge docs for a single source record."""
        from_value = self._resolve_field(record, edge_config["from_field"])  # WHY: source endpoint
        if not from_value:  # WHY: guard clause exits when source is missing
            return []
        to_field = edge_config.get("to_field", key_field)  # WHY: destination-side field, defaulting to record key
        to_values = self._as_nonempty_list(self._resolve_field(record, to_field))  # WHY: normalized non-empty list
        if not to_values:  # WHY: guard clause exits when destination is missing/empty
            return []
        from_col = edge_config["from_col"]  # WHY: source collection identifier
        to_col = edge_config.get("to_col", "")  # WHY: destination collection identifier
        return [  # WHY: comprehension keeps the helper compact and CC low
            self._build_edge_doc(from_col, from_value, to_col, to_key_lookup.get(str(v), str(v))) for v in to_values
        ]

    @staticmethod
    def _as_nonempty_list(raw: Any) -> list[Any]:  # WHY: shared normalizer used by edges and stubs
        """Return raw as a list with falsy entries dropped; empty list when raw is falsy."""
        if not raw:  # WHY: guard clause propagates a missing/empty value as an empty list
            return []
        values = raw if isinstance(raw, list) else [raw]  # WHY: normalize scalar to list
        return [v for v in values if v]  # WHY: drop falsy list entries

    def _build_edge_doc(self, from_col: str, from_value: Any, to_col: str, to_key: str) -> dict:  # WHY: build one
        """Assemble a single edge document with deterministic key and timestamp."""
        from_id = f"{from_col}/{self._sanitize_key(str(from_value))}"  # WHY: canonical Arango vertex id
        to_id = f"{to_col}/{self._sanitize_key(to_key)}"  # WHY: canonical Arango vertex id
        return {  # WHY: shape a standard edge document
            "_key": self._edge_key(from_id, to_id),  # WHY: deterministic key so re-runs upsert cleanly
            "_from": from_id,  # WHY: Arango-required _from
            "_to": to_id,  # WHY: Arango-required _to
            "_misthelper_updated_at": int(time.time()),  # WHY: staleness stamp
        }

    def _resolve_field(self, record: dict, field: str) -> Any:  # WHY: dispatcher for nested versus flat field access
        """Return the record value for a field, supporting dot-separated nested paths."""
        if "." in field:  # WHY: guard clause routes nested paths through the recursive helper
            return self._resolve_nested_field(record, field)
        return record.get(field)  # WHY: flat field lookup

    def _build_key_lookup(self, collection_name: str, lookup_field: str) -> dict[str, str]:  # WHY: FK->_key map
        """Build a lookup dict mapping a field value to vertex _key."""
        if not lookup_field:  # WHY: guard clause returns empty when caller opted out
            return {}
        cursor = self._safe_all(collection_name)  # WHY: helper hides driver errors and None cursors
        if cursor is None:  # WHY: guard clause exits when the collection is missing or empty
            return {}
        return {str(doc[lookup_field]): doc["_key"] for doc in cursor if lookup_field in doc}  # WHY: build map

    def _safe_all(self, collection_name: str) -> Any:  # WHY: driver returns Any and can raise on missing coll
        """Return an iterator over all docs in a collection, or None if unavailable."""
        try:
            col = self._db.collection(collection_name)  # WHY: driver call may raise if collection missing
            return col.all()  # WHY: cursor over the collection
        except Exception:  # WHY: preserve original 'swallow all errors' contract for compat
            return None

    def _ensure_org_vertex(self, data: list[dict]) -> None:  # WHY: derive org vertex from first-with-org record
        """Create a single org vertex from the first record's org_id."""
        for record in data:  # WHY: scan until we find one record carrying org_id
            org_id = record.get("org_id")  # WHY: not every record type carries org_id
            if not org_id:  # WHY: guard clause skips records without org_id
                continue
            self._import_org_doc(str(org_id))  # WHY: import single org doc using the id we found
            return  # WHY: only one org vertex per write is needed

    def _import_org_doc(self, org_id: str) -> None:  # WHY: single-doc import isolated for testability
        """Import a single org vertex, tolerating driver failures for observability."""
        org_col = self._ensure_collection("orgs")  # WHY: ensure the org vertex collection exists
        org_doc = {  # WHY: minimal doc shape - full record already lives in the domain collection
            "_key": self._sanitize_key(org_id),
            "org_id": org_id,
            "_misthelper_updated_at": int(time.time()),
        }
        try:
            org_col.import_bulk([org_doc], on_duplicate="replace")  # WHY: idempotent upsert via bulk API
        except Exception as error:  # WHY: driver errors are logged, not raised, to keep write path resilient
            logger.warning("org_vertex_failed", error=str(error))  # WHY: preserve original diagnostics

    def _ensure_target_vertices(self, data: list[dict], mapping: dict) -> None:  # WHY: create FK stub vertices
        """Create stub vertices for FK targets that lack their own API call."""
        for fk_field, vertex_col_name in mapping.get("ensure_target_vertices", []):  # WHY: iterate declared FKs
            stubs = self._collect_stubs(data, fk_field)  # WHY: build the stub-doc list for this FK
            if not stubs:  # WHY: guard clause skips empty stub lists
                continue
            col = self._ensure_collection(vertex_col_name)  # WHY: ensure destination vertex collection exists
            self._batch_import(col, stubs)  # WHY: bulk upsert the stubs

    def _collect_stubs(self, data: list[dict], fk_field: str) -> list[dict]:  # WHY: helper isolates loop body
        """Return stub vertex docs for every FK value found under fk_field."""
        stubs: list[dict] = []  # WHY: accumulator for output
        for record in data:  # WHY: scan every record for FK values
            values = self._as_nonempty_list(self._resolve_field(record, fk_field))  # WHY: normalize FK values
            stubs.extend(self._make_stub(v) for v in values)  # WHY: append one stub per non-empty FK value
        return stubs  # WHY: caller batch-imports the accumulated stubs

    @staticmethod
    def _make_stub(value: Any) -> dict:  # WHY: single-place shape for FK stubs
        """Return a minimal vertex stub document for the given FK value."""
        return {  # WHY: bare-minimum vertex - full data will be filled in when its own API pulls run
            "_key": ArangoDBWriter._sanitize_key(str(value)),
            "_misthelper_updated_at": int(time.time()),
        }

    def _build_template_edges(self, data: list[dict]) -> None:  # WHY: wire template->site edges from FK fields
        """Create TemplateAssignedToSite edges from site template_id fields."""
        edges: list[dict] = []  # WHY: accumulator for output edges
        for record in data:  # WHY: each site record may contribute several template edges
            site_id = record.get("id")  # WHY: template edges point at the site's own id
            if not site_id:  # WHY: guard clause skips records without an id
                continue
            edges.extend(self._template_edges_for_site(record, str(site_id)))  # WHY: helper builds edges
        if not edges:  # WHY: guard clause avoids ensure_collection when there is nothing to import
            return
        edge_col = self._ensure_collection("TemplateAssignedToSite")  # WHY: ensure destination edge collection
        self._batch_import(edge_col, edges)  # WHY: bulk upsert of collected edges

    def _template_edges_for_site(self, record: dict, site_id: str) -> list[dict]:  # WHY: per-site helper
        """Return template->site edges for every populated template FK on a site record."""
        to_id = f"sites/{self._sanitize_key(site_id)}"  # WHY: destination is the site vertex
        edges: list[dict] = []  # WHY: accumulator for output
        for template_field, template_type in TEMPLATE_ID_FIELDS:  # WHY: table-driven over supported FK fields
            template_id = record.get(template_field)  # WHY: read the template FK
            if not template_id:  # WHY: guard clause skips absent FKs
                continue
            from_id = f"templates/{self._sanitize_key(str(template_id))}"  # WHY: source is the template vertex
            edges.append(  # WHY: append shaped edge with template_type label
                {
                    "_key": self._edge_key(from_id, to_id),
                    "_from": from_id,
                    "_to": to_id,
                    "template_type": template_type,
                    "_misthelper_updated_at": int(time.time()),
                }
            )
        return edges  # WHY: caller aggregates across records

    @staticmethod
    def _edge_key(from_id: str, to_id: str) -> str:  # WHY: deterministic edge key derivation
        """Deterministic edge key from endpoints for idempotent upserts."""
        return hashlib.sha256(  # WHY: 16-char sha256 prefix is stable and short enough for Arango
            f"{from_id}:{to_id}".encode(),
        ).hexdigest()[:16]

    @staticmethod
    def _resolve_nested_field(record: dict, field_path: str) -> Any:  # WHY: dot-path resolver
        """Resolve dot-separated field paths (for example, 'matching.site_ids')."""
        parts = field_path.split(".")  # WHY: split path into successive keys
        value: Any = record  # WHY: walk starts at the record root
        for part in parts:  # WHY: descend through each dot-separated key
            if not isinstance(value, dict):  # WHY: guard clause: stop at first non-dict node
                return None
            value = value.get(part)  # WHY: descend one level
        return value  # WHY: final leaf value (or None when missing)

    @staticmethod
    def _sanitize_key(key: str) -> str:  # WHY: keep Arango happy with invalid-char stripping
        """Replace characters invalid in ArangoDB document keys."""
        return key.replace("/", "_").replace(":", "_")  # WHY: '/' and ':' collide with _id and edge format

    def mark_absent_as_deleted(self, collection_name: str, current_keys: set[str]) -> None:  # WHY: soft-delete
        """Soft-delete documents whose keys are absent from current data."""
        if not self._db.has_collection(collection_name):  # WHY: guard clause skips missing collections
            return
        collection = self._db.collection(collection_name)  # WHY: driver handle for updates
        now = int(time.time())  # WHY: single timestamp shared by every soft-delete in this pass
        for doc in collection.all():  # type: ignore[union-attr]  # WHY: scan every doc for absent keys
            self._soft_delete_if_absent(collection, collection_name, doc, current_keys, now)  # WHY: helper

    @staticmethod
    def _soft_delete_if_absent(  # WHY: per-doc helper isolates the mutation and its logging
        collection: Any,
        collection_name: str,
        doc: dict,
        current_keys: set[str],
        now: int,
    ) -> None:
        """Mark a single doc as soft-deleted if its key is not in current_keys."""
        key = doc.get("_key")  # WHY: read primary key from the doc
        if key in current_keys or doc.get("_misthelper_deleted_at"):  # WHY: guard clause skips live/already-gone
            return
        collection.update({"_key": key, "_misthelper_deleted_at": now})  # WHY: driver-side partial update
        logger.debug("soft_deleted", collection=collection_name, key=key)  # WHY: audit each soft-delete

    def snapshot(  # WHY: store a config snapshot when the payload hash changed
        self,
        entity_type: str,
        entity_id: str,
        config_body: dict,
        config_hash: str | None = None,
        trigger: str = "api_pull",
    ) -> bool:
        """Store a config snapshot, skipping if hash is unchanged."""
        effective_hash = config_hash or self._hash_body(config_body)  # WHY: default to canonical body hash
        collection = self._ensure_collection("config_snapshots")  # WHY: ensure destination collection exists
        if self._latest_snapshot_hash(entity_id) == effective_hash:  # WHY: skip when unchanged
            return False
        snapshot_doc = self._build_snapshot_doc(entity_type, entity_id, effective_hash, config_body, trigger)
        collection.insert(snapshot_doc)  # WHY: durable snapshot record
        self._create_snapshot_edge(str(snapshot_doc["_key"]), entity_type, entity_id)  # WHY: link to entity
        logger.info(  # WHY: audit event including trigger
            "snapshot_stored",
            entity_type=entity_type,
            entity_id=entity_id,
            trigger=trigger,
        )
        return True  # WHY: signal a new snapshot was written

    @staticmethod
    def _hash_body(config_body: dict) -> str:  # WHY: canonical hash helper
        """Return a stable sha256 hex digest of a config body."""
        return hashlib.sha256(json.dumps(config_body, sort_keys=True).encode()).hexdigest()

    def _latest_snapshot_hash(self, entity_id: str) -> str | None:  # WHY: dedupe check helper
        """Return the hash of the most-recent snapshot for entity_id (or None)."""
        cursor = self._db.aql.execute(  # WHY: AQL query bounded to LIMIT 1 for speed
            "FOR doc IN config_snapshots FILTER doc.entity_id == @eid SORT doc.timestamp DESC LIMIT 1 RETURN doc",
            bind_vars={"eid": entity_id},
        )
        for existing in cursor:  # type: ignore[union-attr]  # WHY: cursor yields at most one doc
            return existing.get("config_hash")  # WHY: return hash from newest snapshot
        return None  # WHY: entity has no prior snapshots

    @staticmethod
    def _build_snapshot_doc(  # WHY: builder helper isolates document shape
        entity_type: str,
        entity_id: str,
        config_hash: str,
        config_body: dict,
        trigger: str,
    ) -> dict:
        """Assemble the persisted snapshot document."""
        now = int(time.time())  # WHY: one timestamp shared by timestamp and _misthelper_updated_at
        return {  # WHY: shape stored in config_snapshots
            "_key": str(uuid.uuid4()),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "timestamp": now,
            "config_hash": config_hash,
            "config_body": config_body,
            "trigger": trigger,
            "_misthelper_updated_at": now,
        }

    def _create_snapshot_edge(  # WHY: link a snapshot doc to its entity via an edge
        self,
        snapshot_key: str,
        entity_type: str,
        entity_id: str,
    ) -> None:
        """Create a ConfigSnapshotForEntity edge linking snapshot to entity."""
        vertex_col = ENTITY_TYPE_TO_VERTEX.get(entity_type)  # WHY: entity type declares target vertex collection
        if not vertex_col:  # WHY: guard clause skips entity types not mapped to vertices
            return
        from_id = f"config_snapshots/{self._sanitize_key(snapshot_key)}"  # WHY: canonical Arango vertex id
        to_id = f"{vertex_col}/{self._sanitize_key(str(entity_id))}"  # WHY: canonical Arango vertex id
        edge_col = self._ensure_collection("ConfigSnapshotForEntity")  # WHY: ensure edge collection exists
        edge_doc = self._snapshot_edge_doc(from_id, to_id, entity_type)  # WHY: shape helper isolates the dict
        try:
            edge_col.import_bulk([edge_doc], on_duplicate="replace")  # WHY: idempotent upsert
        except Exception as error:  # WHY: driver errors are logged, not raised, to keep write path resilient
            logger.warning("snapshot_edge_failed", error=str(error))  # WHY: preserve original diagnostics

    @staticmethod
    def _snapshot_edge_doc(from_id: str, to_id: str, entity_type: str) -> dict:  # WHY: single-place shape
        """Return the edge document body for a snapshot->entity edge."""
        return {  # WHY: labelled edge shape reused by insert and backfill paths
            "_key": ArangoDBWriter._edge_key(from_id, to_id),
            "_from": from_id,
            "_to": to_id,
            "entity_type": entity_type,
            "_misthelper_updated_at": int(time.time()),
        }

    def _backfill_snapshot_edges(self) -> None:  # WHY: create edges for pre-existing edge-less snapshots
        """Create edges for existing snapshots that lack them."""
        if not self._db.has_collection("config_snapshots"):  # WHY: guard clause skips when no snapshots exist
            return
        edge_col = self._ensure_collection("ConfigSnapshotForEntity")  # WHY: ensure destination edge collection
        if self._backfill_already_done(edge_col):  # WHY: skip when counts already match
            return
        edges = self._collect_backfill_edges()  # WHY: build edges for all snapshots
        if not edges:  # WHY: guard clause when there is nothing to import
            return
        self._batch_import(edge_col, edges)  # WHY: bulk upsert
        logger.info("snapshot_edges_backfilled", count=len(edges))  # WHY: audit trail

    def _backfill_already_done(self, edge_col: Any) -> bool:  # WHY: cheap dedupe of the expensive scan
        """Return True when edge count already meets snapshot count."""
        try:
            return bool(edge_col.count() >= self._db.collection("config_snapshots").count())
        except TypeError:  # WHY: mocked collections in tests return non-comparable counts
            return True

    def _collect_backfill_edges(self) -> list[dict]:  # WHY: helper isolates the AQL scan and edge shaping
        """Return all snapshot->entity edges implied by current snapshot rows."""
        cursor = self._db.aql.execute(  # WHY: minimal projection reduces network traffic
            "FOR s IN config_snapshots RETURN {  key: s._key, entity_type: s.entity_type, entity_id: s.entity_id}",
        )
        edges: list[dict] = []  # WHY: accumulator for output
        for snap in cursor:  # type: ignore[union-attr]  # WHY: iterate every snapshot row
            edge = self._backfill_edge_for(snap)  # WHY: helper returns None when snap is unmappable
            if edge is not None:  # WHY: guard clause skips unmappable snapshots
                edges.append(edge)  # WHY: accumulate mappable edges
        return edges  # WHY: caller batches these into a single import

    def _backfill_edge_for(self, snap: dict) -> dict | None:  # WHY: single-snap edge builder
        """Return the edge doc for a snapshot row, or None if the target vertex is unknown."""
        vertex_col = ENTITY_TYPE_TO_VERTEX.get(snap["entity_type"] or "")  # WHY: table-driven vertex lookup
        if not vertex_col or not snap["entity_id"]:  # WHY: guard clause skips unmappable rows
            return None
        from_id = f"config_snapshots/{self._sanitize_key(snap['key'])}"  # WHY: canonical Arango vertex id
        to_id = f"{vertex_col}/{self._sanitize_key(str(snap['entity_id']))}"  # WHY: canonical Arango vertex id
        return self._snapshot_edge_doc(from_id, to_id, snap["entity_type"])  # WHY: shared shape helper

    def close(self) -> None:  # WHY: release underlying HTTP session
        """Close the ArangoDB client connection."""
        self._client.close()  # WHY: python-arango releases pooled connections here
        logger.info("arango_writer_closed")  # WHY: audit trail on shutdown
