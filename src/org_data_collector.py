"""
Organization Data Collector

Bulk-collects all org-level read (list/search/get/count) API endpoints to
populate ArangoDB, Redis TimeSeries, and SQLite backends in a single pass.

Menu item 165 -- read-only, no destructive operations.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

import mistapi.api.v1.orgs.aamwprofiles
import mistapi.api.v1.orgs.admins
import mistapi.api.v1.orgs.alarms
import mistapi.api.v1.orgs.alarmtemplates
import mistapi.api.v1.orgs.apitokens
import mistapi.api.v1.orgs.aptemplates
import mistapi.api.v1.orgs.assetfilters
import mistapi.api.v1.orgs.assets
import mistapi.api.v1.orgs.avprofiles
import mistapi.api.v1.orgs.cert
import mistapi.api.v1.orgs.clients
import mistapi.api.v1.orgs.deviceprofiles
import mistapi.api.v1.orgs.devices
import mistapi.api.v1.orgs.events
import mistapi.api.v1.orgs.evpn_topologies
import mistapi.api.v1.orgs.gatewaytemplates
import mistapi.api.v1.orgs.guests
import mistapi.api.v1.orgs.idpprofiles
import mistapi.api.v1.orgs.inventory
import mistapi.api.v1.orgs.jsi
import mistapi.api.v1.orgs.licenses
import mistapi.api.v1.orgs.logs
import mistapi.api.v1.orgs.marvisinvites
import mistapi.api.v1.orgs.mxclusters
import mistapi.api.v1.orgs.mxedges
import mistapi.api.v1.orgs.mxtunnels
import mistapi.api.v1.orgs.nac_clients
import mistapi.api.v1.orgs.nacportals
import mistapi.api.v1.orgs.nacrules
import mistapi.api.v1.orgs.nactags
import mistapi.api.v1.orgs.networks
import mistapi.api.v1.orgs.networktemplates
import mistapi.api.v1.orgs.orgs
import mistapi.api.v1.orgs.otherdevices
import mistapi.api.v1.orgs.pcaps
import mistapi.api.v1.orgs.pma
import mistapi.api.v1.orgs.pskportals
import mistapi.api.v1.orgs.psks
import mistapi.api.v1.orgs.rftemplates
import mistapi.api.v1.orgs.sdkinvites
import mistapi.api.v1.orgs.sdktemplates
import mistapi.api.v1.orgs.secintelprofiles
import mistapi.api.v1.orgs.secpolicies
import mistapi.api.v1.orgs.servicepolicies
import mistapi.api.v1.orgs.services
import mistapi.api.v1.orgs.setting
import mistapi.api.v1.orgs.sitegroups
import mistapi.api.v1.orgs.sites
import mistapi.api.v1.orgs.sitetemplates
import mistapi.api.v1.orgs.ssoroles
import mistapi.api.v1.orgs.ssos
import mistapi.api.v1.orgs.ssr
import mistapi.api.v1.orgs.stats
import mistapi.api.v1.orgs.templates
import mistapi.api.v1.orgs.tickets
import mistapi.api.v1.orgs.uisettings
import mistapi.api.v1.orgs.usermacs
import mistapi.api.v1.orgs.vars
import mistapi.api.v1.orgs.vpns
import mistapi.api.v1.orgs.wan_clients
import mistapi.api.v1.orgs.webhooks
import mistapi.api.v1.orgs.wired_clients
import mistapi.api.v1.orgs.wlans
import mistapi.api.v1.orgs.wxrules
import mistapi.api.v1.orgs.wxtags
import mistapi.api.v1.orgs.wxtunnels

if TYPE_CHECKING:
    from collections.abc import Callable


# ---------------------------------------------------------------------------
# Collection registry -- each entry maps to one org-level API call
# ---------------------------------------------------------------------------
# Fields:
#   api_call      - mistapi function reference
#   data_type     - human label (used for filename & logging)
#   sort_key      - field to sort results by (None = default "name")
#   category      - grouping for progress display
#   paginated     - False if API does not accept limit parameter
#                   (default True when omitted)
#   api_kwargs    - extra keyword args passed to the API call
#                   (e.g. {"distinct": "mac"} for count endpoints)
# ---------------------------------------------------------------------------

_LIST_OPERATIONS: list[dict[str, Any]] = [
    # -- Organization --------------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.admins.listOrgAdmins,
        "data_type": "admins",
        "sort_key": "name",
        "category": "Organization",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.apitokens.listOrgApiTokens,
        "data_type": "api tokens",
        "sort_key": "name",
        "category": "Organization",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.licenses.getOrgLicensesBySite,
        "data_type": "licenses by site",
        "sort_key": None,
        "category": "Organization",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.ssos.listOrgSsos,
        "data_type": "ssos",
        "sort_key": "name",
        "category": "Organization",
    },
    {
        "api_call": mistapi.api.v1.orgs.ssoroles.listOrgSsoRoles,
        "data_type": "sso roles",
        "sort_key": "name",
        "category": "Organization",
    },
    # -- Sites & Groups ------------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.sites.listOrgSites,
        "data_type": "sites",
        "sort_key": "name",
        "category": "Sites & Groups",
    },
    {
        "api_call": mistapi.api.v1.orgs.sitegroups.listOrgSiteGroups,
        "data_type": "site groups",
        "sort_key": "name",
        "category": "Sites & Groups",
    },
    # -- Templates -----------------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.templates.listOrgTemplates,
        "data_type": "templates",
        "sort_key": "name",
        "category": "Templates",
    },
    {
        "api_call": mistapi.api.v1.orgs.sitetemplates.listOrgSiteTemplates,
        "data_type": "site templates",
        "sort_key": "name",
        "category": "Templates",
    },
    {
        "api_call": mistapi.api.v1.orgs.aptemplates.listOrgAptemplates,
        "data_type": "ap templates",
        "sort_key": "name",
        "category": "Templates",
    },
    {
        "api_call": mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates,
        "data_type": "gateway templates",
        "sort_key": "name",
        "category": "Templates",
    },
    {
        "api_call": mistapi.api.v1.orgs.networktemplates.listOrgNetworkTemplates,
        "data_type": "network templates",
        "sort_key": "name",
        "category": "Templates",
    },
    {
        "api_call": mistapi.api.v1.orgs.rftemplates.listOrgRfTemplates,
        "data_type": "rf templates",
        "sort_key": "name",
        "category": "Templates",
    },
    {
        "api_call": mistapi.api.v1.orgs.alarmtemplates.listOrgAlarmTemplates,
        "data_type": "alarm templates",
        "sort_key": "name",
        "category": "Templates",
    },
    # -- Device Profiles & Configs -------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles,
        "data_type": "device profiles",
        "sort_key": "name",
        "category": "Device Profiles",
    },
    # -- Devices & Inventory -------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.devices.listOrgDevices,
        "data_type": "devices",
        "sort_key": "name",
        "category": "Devices & Inventory",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.devices.listOrgDevicesSummary,
        "data_type": "devices summary",
        "sort_key": None,
        "category": "Devices & Inventory",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.devices.listOrgApsMacs,
        "data_type": "aps macs",
        "sort_key": None,
        "category": "Devices & Inventory",
    },
    {
        "api_call": mistapi.api.v1.orgs.devices.listOrgAvailableDeviceVersions,
        "data_type": "available device versions",
        "sort_key": None,
        "category": "Devices & Inventory",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.devices.listOrgDeviceUpgrades,
        "data_type": "device upgrades",
        "sort_key": None,
        "category": "Devices & Inventory",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.inventory.getOrgInventory,
        "data_type": "inventory",
        "sort_key": None,
        "category": "Devices & Inventory",
    },
    {
        "api_call": mistapi.api.v1.orgs.otherdevices.listOrgOtherDevices,
        "data_type": "other devices",
        "sort_key": "name",
        "category": "Devices & Inventory",
    },
    # -- Network & VPN -------------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.networks.listOrgNetworks,
        "data_type": "networks",
        "sort_key": "name",
        "category": "Network & VPN",
    },
    {
        "api_call": mistapi.api.v1.orgs.vpns.listOrgVpns,
        "data_type": "vpns",
        "sort_key": "name",
        "category": "Network & VPN",
    },
    {
        "api_call": mistapi.api.v1.orgs.evpn_topologies.listOrgEvpnTopologies,
        "data_type": "evpn topologies",
        "sort_key": "name",
        "category": "Network & VPN",
    },
    {
        "api_call": mistapi.api.v1.orgs.services.listOrgServices,
        "data_type": "services",
        "sort_key": "name",
        "category": "Network & VPN",
    },
    # -- Wireless Policy -----------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.wlans.listOrgWlans,
        "data_type": "wlans",
        "sort_key": "ssid",
        "category": "Wireless Policy",
    },
    {
        "api_call": mistapi.api.v1.orgs.wxrules.listOrgWxRules,
        "data_type": "wx rules",
        "sort_key": "order",
        "category": "Wireless Policy",
    },
    {
        "api_call": mistapi.api.v1.orgs.wxtags.listOrgWxTags,
        "data_type": "wx tags",
        "sort_key": "name",
        "category": "Wireless Policy",
    },
    {
        "api_call": mistapi.api.v1.orgs.wxtunnels.listOrgWxTunnels,
        "data_type": "wx tunnels",
        "sort_key": "name",
        "category": "Wireless Policy",
    },
    {
        "api_call": mistapi.api.v1.orgs.psks.listOrgPsks,
        "data_type": "psks",
        "sort_key": "name",
        "category": "Wireless Policy",
    },
    # -- Security Profiles ---------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.aamwprofiles.listOrgAAMWProfiles,
        "data_type": "aamw profiles",
        "sort_key": "name",
        "category": "Security Profiles",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.avprofiles.listOrgAntivirusProfiles,
        "data_type": "antivirus profiles",
        "sort_key": "name",
        "category": "Security Profiles",
    },
    {
        "api_call": mistapi.api.v1.orgs.idpprofiles.listOrgIdpProfiles,
        "data_type": "idp profiles",
        "sort_key": "name",
        "category": "Security Profiles",
    },
    {
        "api_call": mistapi.api.v1.orgs.secintelprofiles.listOrgSecIntelProfiles,
        "data_type": "secIntel profiles",
        "sort_key": "name",
        "category": "Security Profiles",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.secpolicies.listOrgSecPolicies,
        "data_type": "sec policies",
        "sort_key": "name",
        "category": "Security Profiles",
    },
    {
        "api_call": mistapi.api.v1.orgs.servicepolicies.listOrgServicePolicies,
        "data_type": "service policies",
        "sort_key": "name",
        "category": "Security Profiles",
    },
    # -- Edge Infrastructure -------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.mxedges.listOrgMxEdges,
        "data_type": "mxedges",
        "sort_key": "name",
        "category": "Edge Infrastructure",
    },
    {
        "api_call": mistapi.api.v1.orgs.mxclusters.listOrgMxEdgeClusters,
        "data_type": "mxedge clusters",
        "sort_key": "name",
        "category": "Edge Infrastructure",
    },
    {
        "api_call": mistapi.api.v1.orgs.mxedges.listOrgMxEdgeUpgrades,
        "data_type": "mxedge upgrades",
        "sort_key": None,
        "category": "Edge Infrastructure",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.mxtunnels.listOrgMxTunnels,
        "data_type": "mx tunnels",
        "sort_key": "name",
        "category": "Edge Infrastructure",
    },
    # -- NAC -----------------------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.nacportals.listOrgNacPortals,
        "data_type": "nac portals",
        "sort_key": "name",
        "category": "NAC",
    },
    {
        "api_call": mistapi.api.v1.orgs.nacrules.listOrgNacRules,
        "data_type": "nac rules",
        "sort_key": "name",
        "category": "NAC",
    },
    {
        "api_call": mistapi.api.v1.orgs.nactags.listOrgNacTags,
        "data_type": "nac tags",
        "sort_key": "name",
        "category": "NAC",
    },
    # -- Access & Auth -------------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.cert.listOrgCertificates,
        "data_type": "certificates",
        "sort_key": None,
        "category": "Access & Auth",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.setting.listOrgIssuedClientCertificates,
        "data_type": "issued client certificates",
        "sort_key": None,
        "category": "Access & Auth",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.guests.listOrgGuestAuthorizations,
        "data_type": "guest authorizations",
        "sort_key": None,
        "category": "Access & Auth",
        "paginated": False,
    },
    # -- Assets --------------------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.assets.listOrgAssets,
        "data_type": "assets",
        "sort_key": "name",
        "category": "Assets",
    },
    {
        "api_call": mistapi.api.v1.orgs.assetfilters.listOrgAssetFilters,
        "data_type": "asset filters",
        "sort_key": "name",
        "category": "Assets",
    },
    # -- JSI (Juniper Support Insights) --------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.jsi.listOrgJsiDevices,
        "data_type": "jsi devices",
        "sort_key": None,
        "category": "JSI",
    },
    # -- PSK Portals ---------------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.pskportals.listOrgPskPortals,
        "data_type": "psk portals",
        "sort_key": "name",
        "category": "PSK Portals",
    },
    {
        "api_call": mistapi.api.v1.orgs.pskportals.listOrgPskPortalLogs,
        "data_type": "psk portal logs",
        "sort_key": None,
        "category": "PSK Portals",
    },
    # -- SDK & Invites -------------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.sdkinvites.listSdkInvites,
        "data_type": "sdk invites",
        "sort_key": None,
        "category": "SDK & Invites",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.sdktemplates.listSdkTemplates,
        "data_type": "sdk templates",
        "sort_key": "name",
        "category": "SDK & Invites",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.marvisinvites.listOrgMarvisClientInvites,
        "data_type": "marvis client invites",
        "sort_key": None,
        "category": "SDK & Invites",
        "paginated": False,
    },
    # -- SSR -----------------------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.ssr.listOrgAvailableSsrVersions,
        "data_type": "available ssr versions",
        "sort_key": None,
        "category": "SSR",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.ssr.listOrgSsrUpgrades,
        "data_type": "ssr upgrades",
        "sort_key": None,
        "category": "SSR",
        "paginated": False,
    },
    # -- Alarms & Tickets ----------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.alarmtemplates.listOrgSuppressedAlarms,
        "data_type": "suppressed alarms",
        "sort_key": None,
        "category": "Alarms & Tickets",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.tickets.listOrgTickets,
        "data_type": "tickets",
        "sort_key": None,
        "category": "Alarms & Tickets",
        "paginated": False,
    },
    # -- Packet Captures -----------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.pcaps.listOrgPacketCaptures,
        "data_type": "packet captures",
        "sort_key": None,
        "category": "Packet Captures",
    },
    # -- Audit Logs ----------------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.logs.listOrgAuditLogs,
        "data_type": "audit logs",
        "sort_key": None,
        "category": "Audit Logs",
    },
    # -- Webhooks ------------------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.webhooks.listOrgWebhooks,
        "data_type": "webhooks",
        "sort_key": "name",
        "category": "Webhooks",
    },
    # -- Dashboards & UI -----------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.pma.listOrgPmaDashboards,
        "data_type": "pma dashboards",
        "sort_key": None,
        "category": "Dashboards & UI",
    },
    {
        "api_call": mistapi.api.v1.orgs.uisettings.listOrgUiSettings,
        "data_type": "ui settings",
        "sort_key": None,
        "category": "Dashboards & UI",
        "paginated": False,
    },
]

_SEARCH_OPERATIONS: list[dict[str, Any]] = [
    # -- Device Searches -----------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.devices.searchOrgDevices,
        "data_type": "devices search",
        "sort_key": None,
        "category": "Device Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.devices.searchOrgDeviceEvents,
        "data_type": "device events",
        "sort_key": None,
        "category": "Device Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.devices.searchOrgDeviceLastConfigs,
        "data_type": "device last configs",
        "sort_key": None,
        "category": "Device Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.inventory.searchOrgInventory,
        "data_type": "inventory search",
        "sort_key": None,
        "category": "Device Searches",
    },
    # -- Client Searches -----------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.clients.searchOrgWirelessClients,
        "data_type": "wireless clients",
        "sort_key": None,
        "category": "Client Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.clients.searchOrgWirelessClientEvents,
        "data_type": "wireless client events",
        "sort_key": None,
        "category": "Client Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.clients.searchOrgWirelessClientSessions,
        "data_type": "wireless client sessions",
        "sort_key": None,
        "category": "Client Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients,
        "data_type": "wired clients",
        "sort_key": None,
        "category": "Client Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.wan_clients.searchOrgWanClients,
        "data_type": "wan clients",
        "sort_key": None,
        "category": "Client Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.wan_clients.searchOrgWanClientEvents,
        "data_type": "wan client events",
        "sort_key": None,
        "category": "Client Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.nac_clients.searchOrgNacClients,
        "data_type": "nac clients",
        "sort_key": None,
        "category": "Client Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.nac_clients.searchOrgNacClientEvents,
        "data_type": "nac client events",
        "sort_key": None,
        "category": "Client Searches",
    },
    # -- Event Searches ------------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.events.searchOrgEvents,
        "data_type": "org events",
        "sort_key": None,
        "category": "Event Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.events.searchOrgSystemEvents,
        "data_type": "system events",
        "sort_key": None,
        "category": "Event Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.mxedges.searchOrgMistEdgeEvents,
        "data_type": "mist edge events",
        "sort_key": None,
        "category": "Event Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.otherdevices.searchOrgOtherDeviceEvents,
        "data_type": "other device events",
        "sort_key": None,
        "category": "Event Searches",
    },
    # -- Alarm Searches ------------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.alarms.searchOrgAlarms,
        "data_type": "alarms",
        "sort_key": None,
        "category": "Alarm Searches",
    },
    # -- Infrastructure Searches ---------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.mxedges.searchOrgMxEdges,
        "data_type": "mxedges search",
        "sort_key": None,
        "category": "Infrastructure Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.sites.searchOrgSites,
        "data_type": "sites search",
        "sort_key": None,
        "category": "Infrastructure Searches",
    },
    # -- Stats Searches ------------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.stats.searchOrgAssets,
        "data_type": "assets search",
        "sort_key": None,
        "category": "Stats Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.stats.searchOrgBgpStats,
        "data_type": "bgp stats",
        "sort_key": None,
        "category": "Stats Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.stats.searchOrgOspfStats,
        "data_type": "ospf stats",
        "sort_key": None,
        "category": "Stats Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.stats.searchOrgPeerPathStats,
        "data_type": "peer path stats",
        "sort_key": None,
        "category": "Stats Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.stats.searchOrgSwOrGwPorts,
        "data_type": "switch gateway ports",
        "sort_key": None,
        "category": "Stats Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.stats.searchOrgTunnelsStats,
        "data_type": "tunnels stats",
        "sort_key": None,
        "category": "Stats Searches",
    },
    # -- Stats List ----------------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.stats.listOrgDevicesStats,
        "data_type": "devices stats",
        "sort_key": None,
        "category": "Stats Lists",
    },
    {
        "api_call": mistapi.api.v1.orgs.stats.listOrgMxEdgesStats,
        "data_type": "mxedges stats",
        "sort_key": None,
        "category": "Stats Lists",
    },
    {
        "api_call": mistapi.api.v1.orgs.stats.listOrgSiteStats,
        "data_type": "site stats",
        "sort_key": None,
        "category": "Stats Lists",
    },
    {
        "api_call": mistapi.api.v1.orgs.stats.listOrgAssetsStats,
        "data_type": "assets stats",
        "sort_key": None,
        "category": "Stats Lists",
    },
    # -- Access Searches -----------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.usermacs.searchOrgUserMacs,
        "data_type": "user macs",
        "sort_key": None,
        "category": "Access Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.guests.searchOrgGuestAuthorization,
        "data_type": "guest authorization search",
        "sort_key": None,
        "category": "Access Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.pskportals.searchOrgPskPortalLogs,
        "data_type": "psk portal logs search",
        "sort_key": None,
        "category": "Access Searches",
    },
    # -- JSI Searches --------------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.jsi.searchOrgJsiAssetsAndContracts,
        "data_type": "jsi assets and contracts",
        "sort_key": None,
        "category": "JSI Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.jsi.searchOrgJsiPbn,
        "data_type": "jsi pbn",
        "sort_key": None,
        "category": "JSI Searches",
    },
    {
        "api_call": mistapi.api.v1.orgs.jsi.searchOrgJsiSirt,
        "data_type": "jsi sirt",
        "sort_key": None,
        "category": "JSI Searches",
    },
    # -- Misc Searches -------------------------------------------------------
    {
        "api_call": mistapi.api.v1.orgs.vars.searchOrgVars,
        "data_type": "org vars",
        "sort_key": None,
        "category": "Misc Searches",
    },
]

_GET_OPERATIONS: list[dict[str, Any]] = [
    {
        "api_call": mistapi.api.v1.orgs.orgs.getOrg,
        "data_type": "org info",
        "sort_key": None,
        "category": "Organization Info",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.licenses.getOrgLicensesSummary,
        "data_type": "licenses summary",
        "sort_key": None,
        "category": "Organization Info",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.setting.getOrgSettings,
        "data_type": "org settings",
        "sort_key": None,
        "category": "Organization Info",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.stats.getOrgStats,
        "data_type": "org stats",
        "sort_key": None,
        "category": "Organization Info",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.wxtags.getOrgApplicationList,
        "data_type": "application list",
        "sort_key": None,
        "category": "Organization Info",
        "paginated": False,
    },
    {
        "api_call": mistapi.api.v1.orgs.pcaps.getOrgCapturingStatus,
        "data_type": "capturing status",
        "sort_key": None,
        "category": "Organization Info",
        "paginated": False,
    },
]

_COUNT_OPERATIONS: list[dict[str, Any]] = [
    {
        "api_call": mistapi.api.v1.orgs.alarms.countOrgAlarms,
        "data_type": "alarms count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.devices.countOrgDevices,
        "data_type": "devices count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.devices.countOrgDeviceEvents,
        "data_type": "device events count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.clients.countOrgWirelessClients,
        "data_type": "wireless clients count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.clients.countOrgWirelessClientEvents,
        "data_type": "wireless client events count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.clients.countOrgWirelessClientsSessions,
        "data_type": "wireless client sessions count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.wired_clients.countOrgWiredClients,
        "data_type": "wired clients count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.wan_clients.countOrgWanClients,
        "data_type": "wan clients count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.nac_clients.countOrgNacClients,
        "data_type": "nac clients count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.nac_clients.countOrgNacClientEvents,
        "data_type": "nac client events count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.events.countOrgSystemEvents,
        "data_type": "system events count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.inventory.countOrgInventory,
        "data_type": "inventory count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.sites.countOrgSites,
        "data_type": "sites count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.mxedges.countOrgMxEdges,
        "data_type": "mxedges count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.mxedges.countOrgSiteMxEdgeEvents,
        "data_type": "mxedge events count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.otherdevices.countOrgOtherDeviceEvents,
        "data_type": "other device events count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.guests.countOrgGuestAuthorizations,
        "data_type": "guest authorizations count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.logs.countOrgAuditLogs,
        "data_type": "audit logs count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.tickets.countOrgTickets,
        "data_type": "tickets count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.usermacs.countOrgUserMacs,
        "data_type": "user macs count",
        "sort_key": None,
        "category": "Counts",
        "api_kwargs": {"distinct": "mac"},
    },
    {
        "api_call": mistapi.api.v1.orgs.pskportals.countOrgPskPortalLogs,
        "data_type": "psk portal logs count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.devices.countOrgDeviceLastConfigs,
        "data_type": "device last configs count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.jsi.countOrgJsiAssetsAndContracts,
        "data_type": "jsi assets contracts count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.jsi.countOrgJsiPbn,
        "data_type": "jsi pbn count",
        "sort_key": None,
        "category": "Counts",
        "api_kwargs": {"distinct": "mac"},
    },
    {
        "api_call": mistapi.api.v1.orgs.jsi.countOrgJsiSirt,
        "data_type": "jsi sirt count",
        "sort_key": None,
        "category": "Counts",
        "api_kwargs": {"distinct": "mac"},
    },
    {
        "api_call": mistapi.api.v1.orgs.stats.countOrgBgpStats,
        "data_type": "bgp stats count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.stats.countOrgOspfStats,
        "data_type": "ospf stats count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.stats.countOrgPeerPathStats,
        "data_type": "peer path stats count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.stats.countOrgSwOrGwPorts,
        "data_type": "switch gateway ports count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.stats.countOrgTunnelsStats,
        "data_type": "tunnels stats count",
        "sort_key": None,
        "category": "Counts",
    },
    {
        "api_call": mistapi.api.v1.orgs.stats.countOrgAssetsByDistanceField,
        "data_type": "assets by distance count",
        "sort_key": None,
        "category": "Counts",
    },
]

ALL_OPERATIONS: list[dict[str, Any]] = _LIST_OPERATIONS + _SEARCH_OPERATIONS + _GET_OPERATIONS + _COUNT_OPERATIONS


class OrgDataCollector:
    """Bulk-collect all org-level read APIs for database population.

    Iterates through every registered list/search/get/count endpoint,
    delegates to the existing ``OrgExportUtils.export_data`` pipeline
    (which handles pagination, rate-limiting, and multi-backend writes),
    and logs per-call success/failure without aborting the run.
    """

    @staticmethod
    def execute(
        export_data_fn: Callable[..., None],
        get_org_id_fn: Callable[[], str],
        safe_input_fn: Callable[..., str],
    ) -> None:
        """Run the full org-level data collection.

        Args:
            export_data_fn: Reference to ``OrgExportUtils.export_data``.
            get_org_id_fn:  Reference to ``ConfigUtils.get_cached_or_prompted_org_id``.
            safe_input_fn:  Reference to ``InputUtils.safe_input``.
        """
        org_id = get_org_id_fn()
        total = len(ALL_OPERATIONS)
        logging.info(f"Org Data Collector: starting {total} operations for org {org_id}")

        confirmation = safe_input_fn(
            f"\nThis will run {total} org-level API calls to populate databases.\n" "Continue? (y/N): ",
            context="org_data_collector",
        )
        if confirmation.strip().lower() != "y":
            logging.info("Org Data Collector: cancelled by user")
            print("Cancelled.")
            return

        result = _collect_all(export_data_fn, total)
        _print_summary(total, *result)


def _collect_all(
    export_data_fn: Callable[..., None],
    total: int,
) -> tuple[int, int, int, float]:
    """Execute every registered operation, return (succeeded, failed, skipped, elapsed)."""
    succeeded = 0
    failed = 0
    skipped = 0
    start_time = time.time()
    current_category = ""

    for index, operation in enumerate(ALL_OPERATIONS, 1):
        category = operation["category"]
        if category != current_category:
            current_category = category
            print(f"\n{'=' * 60}")
            print(f"  {category}")
            print(f"{'=' * 60}")

        result = _run_single(export_data_fn, operation, index, total)
        if result == "ok":
            succeeded += 1
        elif result == "failed":
            failed += 1
        else:
            skipped += 1

    elapsed = time.time() - start_time
    return succeeded, failed, skipped, elapsed


def _run_single(
    export_data_fn: Callable[..., None],
    operation: dict[str, Any],
    index: int,
    total: int,
) -> str:
    """Execute one operation, return 'ok', 'failed', or 'skipped'."""
    api_name = operation["api_call"].__name__
    data_type = operation["data_type"]
    sort_key = operation["sort_key"]
    paginated = operation.get("paginated", True)
    progress = f"[{index}/{total}]"

    print(f"{progress} {api_name} ({data_type})...", end=" ", flush=True)
    try:
        limit_value = 1000 if paginated else None
        extra_kwargs = operation.get("api_kwargs", {})
        export_data_fn(
            api_call=operation["api_call"],
            data_type=data_type,
            sort_key=sort_key if sort_key else "name",
            limit=limit_value,
            **extra_kwargs,
        )
        print("OK")
        return "ok"
    except Exception as error:
        error_name = type(error).__name__
        print(f"FAILED ({error_name})")
        logging.error(f"Org Data Collector: {api_name} failed: {error_name}: {error}")
        return "failed"


def _print_summary(
    total: int,
    succeeded: int,
    failed: int,
    skipped: int,
    elapsed: float,
) -> None:
    """Print collection summary to console and log."""
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    print(f"\n{'=' * 60}")
    print("  Org Data Collection Complete")
    print(f"{'=' * 60}")
    print(f"  Total:     {total}")
    print(f"  Succeeded: {succeeded}")
    print(f"  Failed:    {failed}")
    print(f"  Skipped:   {skipped}")
    print(f"  Duration:  {minutes}m {seconds}s")
    print(f"{'=' * 60}")
    logging.info(
        f"Org Data Collector: complete -- "
        f"{succeeded}/{total} succeeded, {failed} failed, "
        f"{minutes}m {seconds}s elapsed"
    )
