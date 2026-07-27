"""Organization Data Collector.

Bulk-collects all org-level read (list/search/get/count) API endpoints to
populate ArangoDB, Redis TimeSeries, and SQLite backends in a single pass.

Menu item 165 -- read-only, no destructive operations.
"""

from __future__ import annotations  # WHY: PEP 563 postponed annotations for forward Callable typing

import logging  # WHY: Structured per-call success/failure logging for the bulk sweep
import time  # WHY: Elapsed-time tracking for the run-completion summary
from dataclasses import dataclass, field  # WHY: Frozen slotted operation bundle collapses wide dict signatures
from typing import TYPE_CHECKING, Any  # WHY: Any covers heterogeneous mistapi callables + extra kwargs

import mistapi.api.v1.orgs.aamwprofiles  # WHY: Advanced anti-malware profiles endpoint bindings
import mistapi.api.v1.orgs.admins  # WHY: Org administrators endpoint bindings
import mistapi.api.v1.orgs.alarms  # WHY: Org alarm search and count endpoint bindings
import mistapi.api.v1.orgs.alarmtemplates  # WHY: Org alarm-template list endpoints
import mistapi.api.v1.orgs.aos  # WHY: AOS device-registration command endpoint
import mistapi.api.v1.orgs.apitokens  # WHY: Org API-token inventory endpoint
import mistapi.api.v1.orgs.aptemplates  # WHY: AP-template list endpoint
import mistapi.api.v1.orgs.assetfilters  # WHY: Asset-filter list endpoint
import mistapi.api.v1.orgs.assets  # WHY: Asset list endpoint
import mistapi.api.v1.orgs.avprofiles  # WHY: Antivirus profile list endpoint
import mistapi.api.v1.orgs.cert  # WHY: Org certificate inventory endpoint
import mistapi.api.v1.orgs.clients  # WHY: Wireless client search/count endpoint bindings
import mistapi.api.v1.orgs.crl  # WHY: CRL file retrieval endpoint
import mistapi.api.v1.orgs.deviceprofiles  # WHY: Device-profile list endpoint
import mistapi.api.v1.orgs.devices  # WHY: Device search/list/count endpoint bindings
import mistapi.api.v1.orgs.events  # WHY: Org and system event search/count endpoints
import mistapi.api.v1.orgs.evpn_topologies  # WHY: EVPN topology list endpoint
import mistapi.api.v1.orgs.gatewaytemplates  # WHY: Gateway-template list endpoint
import mistapi.api.v1.orgs.guests  # WHY: Guest authorization list/search endpoints
import mistapi.api.v1.orgs.idpprofiles  # WHY: IDP profile list endpoint
import mistapi.api.v1.orgs.insights  # WHY: Site-level SLE insight endpoint
import mistapi.api.v1.orgs.inventory  # WHY: Inventory list/search/count endpoints
import mistapi.api.v1.orgs.jsi  # WHY: Juniper Support Insights list/search/count endpoints
import mistapi.api.v1.orgs.licenses  # WHY: License summary and by-site endpoints
import mistapi.api.v1.orgs.logs  # WHY: Audit log list/count endpoints
import mistapi.api.v1.orgs.marvisinvites  # WHY: Marvis client invite list endpoint
import mistapi.api.v1.orgs.mxclusters  # WHY: Mist Edge cluster list endpoint
import mistapi.api.v1.orgs.mxedges  # WHY: Mist Edge list/search/count endpoints
import mistapi.api.v1.orgs.mxtunnels  # WHY: Mist Edge tunnel list endpoint
import mistapi.api.v1.orgs.nac_clients  # WHY: NAC client search/count endpoints
import mistapi.api.v1.orgs.nacportals  # WHY: NAC portal list endpoint
import mistapi.api.v1.orgs.nacrules  # WHY: NAC rule list endpoint
import mistapi.api.v1.orgs.nactags  # WHY: NAC tag list endpoint
import mistapi.api.v1.orgs.networks  # WHY: Network list endpoint
import mistapi.api.v1.orgs.networktemplates  # WHY: Network-template list endpoint
import mistapi.api.v1.orgs.orgs  # WHY: Org info retrieval endpoint
import mistapi.api.v1.orgs.otherdevices  # WHY: Other-device list/search/count endpoints
import mistapi.api.v1.orgs.pcaps  # WHY: Packet capture list and status endpoints
import mistapi.api.v1.orgs.pma  # WHY: Premium analytics dashboard list endpoint
import mistapi.api.v1.orgs.pskportals  # WHY: PSK portal list/log endpoints
import mistapi.api.v1.orgs.psks  # WHY: PSK list endpoint
import mistapi.api.v1.orgs.rftemplates  # WHY: RF template list endpoint
import mistapi.api.v1.orgs.sdkinvites  # WHY: SDK invite list endpoint
import mistapi.api.v1.orgs.sdktemplates  # WHY: SDK template list endpoint
import mistapi.api.v1.orgs.secintelprofiles  # WHY: Security-intel profile list endpoint
import mistapi.api.v1.orgs.secpolicies  # WHY: Security policy list endpoint
import mistapi.api.v1.orgs.servicepolicies  # WHY: Service policy list endpoint
import mistapi.api.v1.orgs.services  # WHY: Service list endpoint
import mistapi.api.v1.orgs.setting  # WHY: Org settings and integration endpoints
import mistapi.api.v1.orgs.sitegroups  # WHY: Site group list endpoint
import mistapi.api.v1.orgs.sites  # WHY: Site list/search/count endpoints
import mistapi.api.v1.orgs.sitetemplates  # WHY: Site-template list endpoint
import mistapi.api.v1.orgs.ssl_proxy_cert  # WHY: SSL proxy certificate endpoint
import mistapi.api.v1.orgs.ssoroles  # WHY: SSO role list endpoint
import mistapi.api.v1.orgs.ssos  # WHY: SSO configuration list endpoint
import mistapi.api.v1.orgs.ssr  # WHY: SSR device version/upgrade/registration endpoints
import mistapi.api.v1.orgs.stats  # WHY: Org stats list/search/count endpoints
import mistapi.api.v1.orgs.templates  # WHY: Configuration template list endpoint
import mistapi.api.v1.orgs.tickets  # WHY: Support ticket list/count endpoints
import mistapi.api.v1.orgs.uisettings  # WHY: UI settings list endpoint
import mistapi.api.v1.orgs.usermacs  # WHY: User MAC search/count endpoints
import mistapi.api.v1.orgs.vars  # WHY: Org variable search endpoint
import mistapi.api.v1.orgs.vpns  # WHY: VPN list endpoint
import mistapi.api.v1.orgs.wan_client  # WHY: WAN client event count endpoint (singular module)
import mistapi.api.v1.orgs.wan_clients  # WHY: WAN client search/count endpoints (plural module)
import mistapi.api.v1.orgs.webhooks  # WHY: Webhook list endpoint
import mistapi.api.v1.orgs.wired_clients  # WHY: Wired client search/count endpoints
import mistapi.api.v1.orgs.wlans  # WHY: WLAN list endpoint
import mistapi.api.v1.orgs.wxrules  # WHY: WLAN restriction rule list endpoint
import mistapi.api.v1.orgs.wxtags  # WHY: WLAN tag list and application list endpoints
import mistapi.api.v1.orgs.wxtunnels  # WHY: WLAN tunnel list endpoint

if TYPE_CHECKING:  # WHY: Import Callable only for type checking to keep runtime imports minimal
    from collections.abc import Callable

# --- Module constants ------------------------------------------------------
_DEFAULT_LIMIT = 1000  # WHY: Paginated APIs default to a 1000-item page for bulk collection
_DEFAULT_SORT_KEY = "name"  # WHY: Fallback sort key when the operation omits one
_SEPARATOR = "=" * 60  # WHY: Console banner rule for category and summary sections
_DISTINCT_MAC = {"distinct": "mac"}  # WHY: Extra kwargs marker for count endpoints keyed by MAC
_RESULT_OK = "ok"  # WHY: Success sentinel returned by _run_single
_RESULT_FAILED = "failed"  # WHY: Failure sentinel returned by _run_single
_RESULT_SKIPPED = "skipped"  # WHY: Skip sentinel reserved for future opt-outs
_SECONDS_PER_MINUTE = 60  # WHY: Divisor for elapsed-time minutes/seconds decomposition
_CONFIRM_YES = "y"  # WHY: Case-normalized affirmative reply the operator must type


@dataclass(frozen=True, slots=True)
class Operation:  # WHY: Immutable slotted bundle replaces per-entry dict[str, Any] payloads
    """Single org-level API operation registered for bulk collection."""

    api_call: Callable[..., Any]  # WHY: mistapi function reference invoked by _run_single
    data_type: str  # WHY: Human-readable label for filenames, logging, and progress lines
    category: str  # WHY: Grouping banner printed once per contiguous run of same-category ops
    sort_key: str | None = None  # WHY: Result sort field. None falls back to _DEFAULT_SORT_KEY
    paginated: bool = True  # WHY: Paginated endpoints receive limit=_DEFAULT_LIMIT. Others pass None
    api_kwargs: dict[str, Any] = field(default_factory=dict)  # WHY: Extra kwargs (for example distinct=mac)


# ---------------------------------------------------------------------------
# Collection registry -- one Operation per org-level API endpoint invoked.
# ---------------------------------------------------------------------------

_ORG = "Organization"  # WHY: Category label reused across org-scope endpoints
_SITES = "Sites & Groups"  # WHY: Category label for site and site-group entries
_TEMPLATES = "Templates"  # WHY: Category label for all template list entries
_PROFILES = "Device Profiles"  # WHY: Category label for device profile entries
_INVENTORY = "Devices & Inventory"  # WHY: Category label for device inventory entries
_NETWORK = "Network & VPN"  # WHY: Category label for network/vpn endpoints
_WIRELESS = "Wireless Policy"  # WHY: Category label for wireless-policy endpoints
_SECURITY = "Security Profiles"  # WHY: Category label for security-profile endpoints
_EDGE = "Edge Infrastructure"  # WHY: Category label for Mist Edge endpoints
_NAC = "NAC"  # WHY: Category label for NAC (Network Access Control) endpoints
_ACCESS = "Access & Auth"  # WHY: Category label for certificate/guest endpoints
_ASSETS = "Assets"  # WHY: Category label for asset/asset-filter endpoints
_JSI = "JSI"  # WHY: Category label for Juniper Support Insights list endpoints
_PSK_PORTALS = "PSK Portals"  # WHY: Category label for PSK portal endpoints
_SDK_INVITES = "SDK & Invites"  # WHY: Category label for SDK invite/template endpoints
_SSR = "SSR"  # WHY: Category label for SSR device endpoints
_ALARMS = "Alarms & Tickets"  # WHY: Category label for alarm and ticket endpoints
_PCAPS = "Packet Captures"  # WHY: Category label for packet-capture endpoints
_AUDIT = "Audit Logs"  # WHY: Category label for audit-log endpoints
_WEBHOOKS = "Webhooks"  # WHY: Category label for webhook endpoints
_UI = "Dashboards & UI"  # WHY: Category label for dashboard/UI setting endpoints
_DEV_SEARCH = "Device Searches"  # WHY: Category label for device search operations
_CLIENT_SEARCH = "Client Searches"  # WHY: Category label for client search operations
_EVT_SEARCH = "Event Searches"  # WHY: Category label for event search operations
_ALARM_SEARCH = "Alarm Searches"  # WHY: Category label for alarm search operations
_INFRA_SEARCH = "Infrastructure Searches"  # WHY: Category label for infrastructure searches
_STATS_SEARCH = "Stats Searches"  # WHY: Category label for stats-search operations
_STATS_LIST = "Stats Lists"  # WHY: Category label for stats-list operations
_ACCESS_SEARCH = "Access Searches"  # WHY: Category label for access-related search operations
_JSI_SEARCH = "JSI Searches"  # WHY: Category label for JSI search operations
_MISC_SEARCH = "Misc Searches"  # WHY: Category label for miscellaneous search operations
_ORG_INFO = "Organization Info"  # WHY: Category label for org-info GET endpoints
_INTEGRATION = "Integration Settings"  # WHY: Category label for third-party integration GET endpoints
_CERT_SEC = "Certificates & Security"  # WHY: Category label for cert/security GET endpoints
_DEVICE_REG = "Device Registration"  # WHY: Category label for device-registration commands
_SLE = "SLE"  # WHY: Category label for service-level expectation endpoints
_COUNTS = "Counts"  # WHY: Category label shared by every count endpoint

_LIST_OPERATIONS: tuple[Operation, ...] = (  # WHY: Immutable tuple of list-style org endpoints
    Operation(mistapi.api.v1.orgs.admins.listOrgAdmins, "admins", _ORG, sort_key="name", paginated=False),
    Operation(mistapi.api.v1.orgs.apitokens.listOrgApiTokens, "api tokens", _ORG, sort_key="name", paginated=False),
    Operation(mistapi.api.v1.orgs.licenses.getOrgLicensesBySite, "licenses by site", _ORG, paginated=False),
    Operation(mistapi.api.v1.orgs.ssos.listOrgSsos, "ssos", _ORG, sort_key="name"),
    Operation(mistapi.api.v1.orgs.ssoroles.listOrgSsoRoles, "sso roles", _ORG, sort_key="name"),
    Operation(mistapi.api.v1.orgs.sites.listOrgSites, "sites", _SITES, sort_key="name"),
    Operation(mistapi.api.v1.orgs.sitegroups.listOrgSiteGroups, "site groups", _SITES, sort_key="name"),
    Operation(mistapi.api.v1.orgs.templates.listOrgTemplates, "templates", _TEMPLATES, sort_key="name"),
    Operation(mistapi.api.v1.orgs.sitetemplates.listOrgSiteTemplates, "site templates", _TEMPLATES, sort_key="name"),
    Operation(mistapi.api.v1.orgs.aptemplates.listOrgAptemplates, "ap templates", _TEMPLATES, sort_key="name"),
    Operation(
        mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates,
        "gateway templates",
        _TEMPLATES,
        sort_key="name",
    ),
    Operation(
        mistapi.api.v1.orgs.networktemplates.listOrgNetworkTemplates,
        "network templates",
        _TEMPLATES,
        sort_key="name",
    ),
    Operation(mistapi.api.v1.orgs.rftemplates.listOrgRfTemplates, "rf templates", _TEMPLATES, sort_key="name"),
    Operation(
        mistapi.api.v1.orgs.alarmtemplates.listOrgAlarmTemplates,
        "alarm templates",
        _TEMPLATES,
        sort_key="name",
    ),
    Operation(
        mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles,
        "device profiles",
        _PROFILES,
        sort_key="name",
    ),
    Operation(mistapi.api.v1.orgs.devices.listOrgDevices, "devices", _INVENTORY, sort_key="name", paginated=False),
    Operation(mistapi.api.v1.orgs.devices.listOrgDevicesSummary, "devices summary", _INVENTORY, paginated=False),
    Operation(mistapi.api.v1.orgs.devices.listOrgApsMacs, "aps macs", _INVENTORY),
    Operation(
        mistapi.api.v1.orgs.devices.listOrgAvailableDeviceVersions,
        "available device versions",
        _INVENTORY,
        paginated=False,
    ),
    Operation(mistapi.api.v1.orgs.devices.listOrgDeviceUpgrades, "device upgrades", _INVENTORY, paginated=False),
    Operation(mistapi.api.v1.orgs.inventory.getOrgInventory, "inventory", _INVENTORY),
    Operation(mistapi.api.v1.orgs.otherdevices.listOrgOtherDevices, "other devices", _INVENTORY, sort_key="name"),
    Operation(mistapi.api.v1.orgs.networks.listOrgNetworks, "networks", _NETWORK, sort_key="name"),
    Operation(mistapi.api.v1.orgs.vpns.listOrgVpns, "vpns", _NETWORK, sort_key="name"),
    Operation(
        mistapi.api.v1.orgs.evpn_topologies.listOrgEvpnTopologies,
        "evpn topologies",
        _NETWORK,
        sort_key="name",
    ),
    Operation(mistapi.api.v1.orgs.services.listOrgServices, "services", _NETWORK, sort_key="name"),
    Operation(mistapi.api.v1.orgs.wlans.listOrgWlans, "wlans", _WIRELESS, sort_key="ssid"),
    Operation(mistapi.api.v1.orgs.wxrules.listOrgWxRules, "wx rules", _WIRELESS, sort_key="order"),
    Operation(mistapi.api.v1.orgs.wxtags.listOrgWxTags, "wx tags", _WIRELESS, sort_key="name"),
    Operation(mistapi.api.v1.orgs.wxtunnels.listOrgWxTunnels, "wx tunnels", _WIRELESS, sort_key="name"),
    Operation(mistapi.api.v1.orgs.psks.listOrgPsks, "psks", _WIRELESS, sort_key="name"),
    Operation(
        mistapi.api.v1.orgs.aamwprofiles.listOrgAAMWProfiles,
        "aamw profiles",
        _SECURITY,
        sort_key="name",
        paginated=False,
    ),
    Operation(
        mistapi.api.v1.orgs.avprofiles.listOrgAntivirusProfiles,
        "antivirus profiles",
        _SECURITY,
        sort_key="name",
    ),
    Operation(mistapi.api.v1.orgs.idpprofiles.listOrgIdpProfiles, "idp profiles", _SECURITY, sort_key="name"),
    Operation(
        mistapi.api.v1.orgs.secintelprofiles.listOrgSecIntelProfiles,
        "secIntel profiles",
        _SECURITY,
        sort_key="name",
        paginated=False,
    ),
    Operation(mistapi.api.v1.orgs.secpolicies.listOrgSecPolicies, "sec policies", _SECURITY, sort_key="name"),
    Operation(
        mistapi.api.v1.orgs.servicepolicies.listOrgServicePolicies,
        "service policies",
        _SECURITY,
        sort_key="name",
    ),
    Operation(mistapi.api.v1.orgs.mxedges.listOrgMxEdges, "mxedges", _EDGE, sort_key="name"),
    Operation(mistapi.api.v1.orgs.mxclusters.listOrgMxEdgeClusters, "mxedge clusters", _EDGE, sort_key="name"),
    Operation(mistapi.api.v1.orgs.mxedges.listOrgMxEdgeUpgrades, "mxedge upgrades", _EDGE, paginated=False),
    Operation(mistapi.api.v1.orgs.mxtunnels.listOrgMxTunnels, "mx tunnels", _EDGE, sort_key="name"),
    Operation(mistapi.api.v1.orgs.nacportals.listOrgNacPortals, "nac portals", _NAC, sort_key="name"),
    Operation(mistapi.api.v1.orgs.nacrules.listOrgNacRules, "nac rules", _NAC, sort_key="name"),
    Operation(mistapi.api.v1.orgs.nactags.listOrgNacTags, "nac tags", _NAC, sort_key="name"),
    Operation(mistapi.api.v1.orgs.cert.listOrgCertificates, "certificates", _ACCESS, paginated=False),
    Operation(
        mistapi.api.v1.orgs.setting.listOrgIssuedClientCertificates,
        "issued client certificates",
        _ACCESS,
        paginated=False,
    ),
    Operation(
        mistapi.api.v1.orgs.guests.listOrgGuestAuthorizations,
        "guest authorizations",
        _ACCESS,
        paginated=False,
    ),
    Operation(mistapi.api.v1.orgs.assets.listOrgAssets, "assets", _ASSETS, sort_key="name"),
    Operation(mistapi.api.v1.orgs.assetfilters.listOrgAssetFilters, "asset filters", _ASSETS, sort_key="name"),
    Operation(mistapi.api.v1.orgs.jsi.listOrgJsiDevices, "jsi devices", _JSI),
    Operation(mistapi.api.v1.orgs.jsi.listOrgJsiPastPurchases, "jsi past purchases", _JSI),
    Operation(mistapi.api.v1.orgs.pskportals.listOrgPskPortals, "psk portals", _PSK_PORTALS, sort_key="name"),
    Operation(mistapi.api.v1.orgs.pskportals.listOrgPskPortalLogs, "psk portal logs", _PSK_PORTALS),
    Operation(mistapi.api.v1.orgs.sdkinvites.listSdkInvites, "sdk invites", _SDK_INVITES, paginated=False),
    Operation(
        mistapi.api.v1.orgs.sdktemplates.listSdkTemplates,
        "sdk templates",
        _SDK_INVITES,
        sort_key="name",
        paginated=False,
    ),
    Operation(
        mistapi.api.v1.orgs.marvisinvites.listOrgMarvisClientInvites,
        "marvis client invites",
        _SDK_INVITES,
        paginated=False,
    ),
    Operation(
        mistapi.api.v1.orgs.ssr.listOrgAvailableSsrVersions,
        "available ssr versions",
        _SSR,
        paginated=False,
    ),
    Operation(mistapi.api.v1.orgs.ssr.listOrgSsrUpgrades, "ssr upgrades", _SSR, paginated=False),
    Operation(
        mistapi.api.v1.orgs.alarmtemplates.listOrgSuppressedAlarms,
        "suppressed alarms",
        _ALARMS,
        paginated=False,
    ),
    Operation(mistapi.api.v1.orgs.tickets.listOrgTickets, "tickets", _ALARMS, paginated=False),
    Operation(mistapi.api.v1.orgs.pcaps.listOrgPacketCaptures, "packet captures", _PCAPS),
    Operation(mistapi.api.v1.orgs.logs.listOrgAuditLogs, "audit logs", _AUDIT),
    Operation(mistapi.api.v1.orgs.webhooks.listOrgWebhooks, "webhooks", _WEBHOOKS, sort_key="name"),
    Operation(mistapi.api.v1.orgs.pma.listOrgPmaDashboards, "pma dashboards", _UI),
    Operation(mistapi.api.v1.orgs.uisettings.listOrgUiSettings, "ui settings", _UI, paginated=False),
)

_SEARCH_OPERATIONS: tuple[Operation, ...] = (  # WHY: Immutable tuple of search-style org endpoints
    Operation(mistapi.api.v1.orgs.devices.searchOrgDevices, "devices search", _DEV_SEARCH),
    Operation(mistapi.api.v1.orgs.devices.searchOrgDeviceEvents, "device events", _DEV_SEARCH),
    Operation(mistapi.api.v1.orgs.devices.searchOrgDeviceLastConfigs, "device last configs", _DEV_SEARCH),
    Operation(mistapi.api.v1.orgs.inventory.searchOrgInventory, "inventory search", _DEV_SEARCH),
    Operation(mistapi.api.v1.orgs.clients.searchOrgWirelessClients, "wireless clients", _CLIENT_SEARCH),
    Operation(
        mistapi.api.v1.orgs.clients.searchOrgWirelessClientEvents,
        "wireless client events",
        _CLIENT_SEARCH,
    ),
    Operation(
        mistapi.api.v1.orgs.clients.searchOrgWirelessClientSessions,
        "wireless client sessions",
        _CLIENT_SEARCH,
    ),
    Operation(mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients, "wired clients", _CLIENT_SEARCH),
    Operation(mistapi.api.v1.orgs.wan_clients.searchOrgWanClients, "wan clients", _CLIENT_SEARCH),
    Operation(mistapi.api.v1.orgs.wan_clients.searchOrgWanClientEvents, "wan client events", _CLIENT_SEARCH),
    Operation(mistapi.api.v1.orgs.nac_clients.searchOrgNacClients, "nac clients", _CLIENT_SEARCH),
    Operation(mistapi.api.v1.orgs.nac_clients.searchOrgNacClientEvents, "nac client events", _CLIENT_SEARCH),
    Operation(mistapi.api.v1.orgs.events.searchOrgEvents, "org events", _EVT_SEARCH),
    Operation(mistapi.api.v1.orgs.events.searchOrgSystemEvents, "system events", _EVT_SEARCH),
    Operation(mistapi.api.v1.orgs.mxedges.searchOrgMistEdgeEvents, "mist edge events", _EVT_SEARCH),
    Operation(mistapi.api.v1.orgs.otherdevices.searchOrgOtherDeviceEvents, "other device events", _EVT_SEARCH),
    Operation(mistapi.api.v1.orgs.alarms.searchOrgAlarms, "alarms", _ALARM_SEARCH),
    Operation(mistapi.api.v1.orgs.mxedges.searchOrgMxEdges, "mxedges search", _INFRA_SEARCH),
    Operation(mistapi.api.v1.orgs.sites.searchOrgSites, "sites search", _INFRA_SEARCH),
    Operation(mistapi.api.v1.orgs.stats.searchOrgAssets, "assets search", _STATS_SEARCH),
    Operation(mistapi.api.v1.orgs.stats.searchOrgBgpStats, "bgp stats", _STATS_SEARCH),
    Operation(mistapi.api.v1.orgs.stats.searchOrgOspfStats, "ospf stats", _STATS_SEARCH),
    Operation(mistapi.api.v1.orgs.stats.searchOrgPeerPathStats, "peer path stats", _STATS_SEARCH),
    Operation(mistapi.api.v1.orgs.stats.searchOrgSwOrGwPorts, "switch gateway ports", _STATS_SEARCH),
    Operation(mistapi.api.v1.orgs.stats.searchOrgTunnelsStats, "tunnels stats", _STATS_SEARCH),
    Operation(mistapi.api.v1.orgs.stats.listOrgDevicesStats, "devices stats", _STATS_LIST),
    Operation(mistapi.api.v1.orgs.stats.listOrgMxEdgesStats, "mxedges stats", _STATS_LIST),
    Operation(mistapi.api.v1.orgs.stats.listOrgSiteStats, "site stats", _STATS_LIST),
    Operation(mistapi.api.v1.orgs.stats.listOrgAssetsStats, "assets stats", _STATS_LIST),
    Operation(mistapi.api.v1.orgs.usermacs.searchOrgUserMacs, "user macs", _ACCESS_SEARCH),
    Operation(
        mistapi.api.v1.orgs.guests.searchOrgGuestAuthorization,
        "guest authorization search",
        _ACCESS_SEARCH,
    ),
    Operation(
        mistapi.api.v1.orgs.pskportals.searchOrgPskPortalLogs,
        "psk portal logs search",
        _ACCESS_SEARCH,
    ),
    Operation(
        mistapi.api.v1.orgs.jsi.searchOrgJsiAssetsAndContracts,
        "jsi assets and contracts",
        _JSI_SEARCH,
    ),
    Operation(mistapi.api.v1.orgs.jsi.searchOrgJsiPbn, "jsi pbn", _JSI_SEARCH),
    Operation(mistapi.api.v1.orgs.jsi.searchOrgJsiSirt, "jsi sirt", _JSI_SEARCH),
    Operation(mistapi.api.v1.orgs.vars.searchOrgVars, "org vars", _MISC_SEARCH),
)

_GET_OPERATIONS: tuple[Operation, ...] = (  # WHY: Immutable tuple of single-object GET endpoints
    Operation(mistapi.api.v1.orgs.orgs.getOrg, "org info", _ORG_INFO, paginated=False),
    Operation(mistapi.api.v1.orgs.licenses.getOrgLicensesSummary, "licenses summary", _ORG_INFO, paginated=False),
    Operation(mistapi.api.v1.orgs.setting.getOrgSettings, "org settings", _ORG_INFO, paginated=False),
    Operation(mistapi.api.v1.orgs.stats.getOrgStats, "org stats", _ORG_INFO, paginated=False),
    Operation(
        mistapi.api.v1.orgs.wxtags.getOrgApplicationList,
        "application list",
        _ORG_INFO,
        paginated=False,
    ),
    Operation(mistapi.api.v1.orgs.pcaps.getOrgCapturingStatus, "capturing status", _ORG_INFO, paginated=False),
    Operation(mistapi.api.v1.orgs.setting.getOrgJseInfo, "jse info", _INTEGRATION, paginated=False),
    Operation(mistapi.api.v1.orgs.setting.getOrgJseIntegration, "jse integration", _INTEGRATION, paginated=False),
    Operation(
        mistapi.api.v1.orgs.setting.getOrgSkyAtpIntegration,
        "sky atp integration",
        _INTEGRATION,
        paginated=False,
    ),
    Operation(
        mistapi.api.v1.orgs.setting.getOrgZscalerIntegration,
        "zscaler integration",
        _INTEGRATION,
        paginated=False,
    ),
    Operation(mistapi.api.v1.orgs.setting.getOrgMistScep, "mist scep", _INTEGRATION, paginated=False),
    Operation(mistapi.api.v1.orgs.setting.getOrgNacCrl, "nac crl", _INTEGRATION, paginated=False),
    Operation(mistapi.api.v1.orgs.crl.getOrgCrlFile, "crl file", _CERT_SEC, paginated=False),
    Operation(
        mistapi.api.v1.orgs.ssl_proxy_cert.getOrgSslProxyCert,
        "ssl proxy cert",
        _CERT_SEC,
        paginated=False,
    ),
    Operation(mistapi.api.v1.orgs.aos.getOrgAosRegisterCmd, "aos register cmd", _DEVICE_REG, paginated=False),
    Operation(
        mistapi.api.v1.orgs.ssr.getOrgSsrRegistrationCommands,
        "ssr registration commands",
        _DEVICE_REG,
        paginated=False,
    ),
    Operation(mistapi.api.v1.orgs.mxedges.getOrgMxEdgeUpgradeInfo, "mxedge upgrade info", _EDGE, paginated=False),
    Operation(mistapi.api.v1.orgs.insights.getOrgSitesSle, "sites sle", _SLE, paginated=False),
)

_COUNT_OPERATIONS: tuple[Operation, ...] = (  # WHY: Immutable tuple of count endpoints for cardinality
    Operation(mistapi.api.v1.orgs.alarms.countOrgAlarms, "alarms count", _COUNTS),
    Operation(mistapi.api.v1.orgs.devices.countOrgDevices, "devices count", _COUNTS),
    Operation(mistapi.api.v1.orgs.devices.countOrgDeviceEvents, "device events count", _COUNTS),
    Operation(mistapi.api.v1.orgs.clients.countOrgWirelessClients, "wireless clients count", _COUNTS),
    Operation(mistapi.api.v1.orgs.clients.countOrgWirelessClientEvents, "wireless client events count", _COUNTS),
    Operation(
        mistapi.api.v1.orgs.clients.countOrgWirelessClientsSessions,
        "wireless client sessions count",
        _COUNTS,
    ),
    Operation(mistapi.api.v1.orgs.wired_clients.countOrgWiredClients, "wired clients count", _COUNTS),
    Operation(mistapi.api.v1.orgs.wan_clients.countOrgWanClients, "wan clients count", _COUNTS),
    Operation(mistapi.api.v1.orgs.nac_clients.countOrgNacClients, "nac clients count", _COUNTS),
    Operation(mistapi.api.v1.orgs.nac_clients.countOrgNacClientEvents, "nac client events count", _COUNTS),
    Operation(mistapi.api.v1.orgs.events.countOrgSystemEvents, "system events count", _COUNTS),
    Operation(mistapi.api.v1.orgs.inventory.countOrgInventory, "inventory count", _COUNTS),
    Operation(mistapi.api.v1.orgs.sites.countOrgSites, "sites count", _COUNTS),
    Operation(mistapi.api.v1.orgs.mxedges.countOrgMxEdges, "mxedges count", _COUNTS),
    Operation(mistapi.api.v1.orgs.mxedges.countOrgSiteMxEdgeEvents, "mxedge events count", _COUNTS),
    Operation(
        mistapi.api.v1.orgs.otherdevices.countOrgOtherDeviceEvents,
        "other device events count",
        _COUNTS,
    ),
    Operation(mistapi.api.v1.orgs.guests.countOrgGuestAuthorizations, "guest authorizations count", _COUNTS),
    Operation(mistapi.api.v1.orgs.logs.countOrgAuditLogs, "audit logs count", _COUNTS),
    Operation(mistapi.api.v1.orgs.tickets.countOrgTickets, "tickets count", _COUNTS),
    Operation(
        mistapi.api.v1.orgs.usermacs.countOrgUserMacs,
        "user macs count",
        _COUNTS,
        api_kwargs=dict(_DISTINCT_MAC),
    ),
    Operation(mistapi.api.v1.orgs.pskportals.countOrgPskPortalLogs, "psk portal logs count", _COUNTS),
    Operation(mistapi.api.v1.orgs.devices.countOrgDeviceLastConfigs, "device last configs count", _COUNTS),
    Operation(mistapi.api.v1.orgs.jsi.countOrgJsiAssetsAndContracts, "jsi assets contracts count", _COUNTS),
    Operation(
        mistapi.api.v1.orgs.jsi.countOrgJsiPbn,
        "jsi pbn count",
        _COUNTS,
        api_kwargs=dict(_DISTINCT_MAC),
    ),
    Operation(
        mistapi.api.v1.orgs.jsi.countOrgJsiSirt,
        "jsi sirt count",
        _COUNTS,
        api_kwargs=dict(_DISTINCT_MAC),
    ),
    Operation(mistapi.api.v1.orgs.stats.countOrgBgpStats, "bgp stats count", _COUNTS),
    Operation(mistapi.api.v1.orgs.stats.countOrgOspfStats, "ospf stats count", _COUNTS),
    Operation(mistapi.api.v1.orgs.stats.countOrgPeerPathStats, "peer path stats count", _COUNTS),
    Operation(mistapi.api.v1.orgs.stats.countOrgSwOrGwPorts, "switch gateway ports count", _COUNTS),
    Operation(mistapi.api.v1.orgs.stats.countOrgTunnelsStats, "tunnels stats count", _COUNTS),
    Operation(mistapi.api.v1.orgs.stats.countOrgAssetsByDistanceField, "assets by distance count", _COUNTS),
    Operation(mistapi.api.v1.orgs.wan_client.countOrgWanClientEvents, "wan client events count", _COUNTS),
)

ALL_OPERATIONS: tuple[Operation, ...] = (  # WHY: Public frozen registry consumed by execute()
    _LIST_OPERATIONS + _SEARCH_OPERATIONS + _GET_OPERATIONS + _COUNT_OPERATIONS
)


@dataclass(frozen=True, slots=True)
class _RunTotals:  # WHY: Frozen counters returned by _collect_all keep the summary signature narrow
    """Aggregate counters returned by the bulk collection loop."""

    succeeded: int  # WHY: Number of operations whose export_data call returned normally
    failed: int  # WHY: Number of operations that raised and were logged as failures
    skipped: int  # WHY: Number of operations short-circuited (reserved for future filters)
    elapsed: float  # WHY: Wall-clock seconds from loop start to loop end


class OrgDataCollector:
    """Bulk-collect all org-level read APIs for database population.

    Iterates through every registered list/search/get/count endpoint,
    delegates to the existing ``OrgExportUtils.export_data`` pipeline
    (which handles pagination, rate-limiting, and multi-backend writes),
    and logs per-call success/failure without aborting the run.
    """

    @staticmethod
    def execute(  # WHY: Static orchestrator entry point invoked by MistHelper menu 153
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
        org_id = get_org_id_fn()  # WHY: Resolve org id up front so the confirmation banner reflects it
        total = len(ALL_OPERATIONS)  # WHY: Compute total once for banner text and progress denominator
        logging.info("Org Data Collector: starting %s operations for org %s", total, org_id)  # WHY: Audit trail
        if not _confirm_run(safe_input_fn, total):  # WHY: Abort early if the operator declines the prompt
            return
        totals = _collect_all(export_data_fn, total)  # WHY: Delegate the loop and receive aggregate counters
        _print_summary(total, totals)  # WHY: Emit closing banner + logging line for the completed run


def _confirm_run(safe_input_fn: Callable[..., str], total: int) -> bool:
    """Prompt the operator and return True iff they typed the affirmative reply."""  # WHY: Isolates I/O
    prompt = (  # WHY: Build the prompt string locally to keep execute() compact
        f"\nThis will run {total} org-level API calls to populate databases.\nContinue? (y/N): "
    )
    reply = safe_input_fn(prompt, context="org_data_collector")  # WHY: EOF-safe operator prompt
    if reply.strip().lower() == _CONFIRM_YES:  # WHY: Normalize whitespace/case before comparing
        return True
    logging.info("Org Data Collector: cancelled by user")  # WHY: Audit trail for the cancel path
    logging.warning("Cancelled.")  # WHY: Operator-visible cancel confirmation via logger.
    return False


def _collect_all(export_data_fn: Callable[..., None], total: int) -> _RunTotals:
    """Execute every registered operation and return the aggregate ``_RunTotals``."""  # WHY: Loop driver
    tally = {_RESULT_OK: 0, _RESULT_FAILED: 0, _RESULT_SKIPPED: 0}  # WHY: Tally by _run_single sentinel key
    start_time = time.time()  # WHY: Capture start timestamp for elapsed wall clock
    current_category = ""  # WHY: Track the last banner so we only print on category transitions
    for index, operation in enumerate(ALL_OPERATIONS, 1):  # WHY: 1-based counter matches "[i/total]" progress
        current_category = _maybe_print_category(operation.category, current_category)  # WHY: Section banner
        result = _run_single(export_data_fn, operation, index, total)  # WHY: Delegate per-call outcome
        tally[result] = tally.get(result, 0) + 1  # WHY: Increment the matching sentinel counter
    elapsed = time.time() - start_time  # WHY: Compute wall-clock duration once at loop exit
    return _RunTotals(
        succeeded=tally[_RESULT_OK],
        failed=tally[_RESULT_FAILED],
        skipped=tally[_RESULT_SKIPPED],
        elapsed=elapsed,
    )


def _maybe_print_category(category: str, previous: str) -> str:
    """Print the category banner when ``category`` differs from ``previous`` and return the new tag."""
    if category == previous:  # WHY: Guard clause avoids reprinting the banner for adjacent same-category ops
        return previous
    logging.warning("\n%s\n  %s\n%s", _SEPARATOR, category, _SEPARATOR)  # WHY: Category banner via logger.
    return category  # WHY: Return the new tag so the caller updates its watermark


def _run_single(
    export_data_fn: Callable[..., None],
    operation: Operation,
    index: int,
    total: int,
) -> str:
    """Execute one operation and return one of ``_RESULT_OK`` / ``_RESULT_FAILED`` / ``_RESULT_SKIPPED``."""
    api_name = operation.api_call.__name__  # WHY: Human-readable function name for progress + logging
    progress = f"[{index}/{total}]"  # WHY: Pre-format progress token so the print stays a single f-string
    logging.warning("%s %s (%s)...", progress, api_name, operation.data_type)  # WHY: Progress line via logger.
    try:
        export_data_fn(**_build_export_kwargs(operation))  # WHY: Delegate to the shared export pipeline
    except Exception as error:  # WHY: Catch broadly so one flaky API never aborts the entire sweep
        return _report_failure(api_name, error)  # WHY: Emit failure line + log and return the sentinel
    logging.warning("OK")  # WHY: Trailing status token confirming success via logger.
    return _RESULT_OK


def _build_export_kwargs(operation: Operation) -> dict[str, Any]:
    """Assemble the keyword-argument dict passed to ``export_data_fn`` for one operation."""
    limit_value = _DEFAULT_LIMIT if operation.paginated else None  # WHY: Non-paginated APIs must not receive limit
    sort_key = operation.sort_key or _DEFAULT_SORT_KEY  # WHY: Fall back to the default sort key when unset
    kwargs: dict[str, Any] = {  # WHY: Base kwargs shared by every operation
        "api_call": operation.api_call,
        "data_type": operation.data_type,
        "sort_key": sort_key,
        "limit": limit_value,
    }
    kwargs.update(operation.api_kwargs)  # WHY: Merge per-operation extras (for example distinct=mac) last
    return kwargs


def _report_failure(api_name: str, error: BaseException) -> str:
    """Print, log, and return the failure sentinel for a raised exception."""  # WHY: Isolates error-path I/O
    error_name = type(error).__name__  # WHY: Compact class name suffices in the console line
    logging.warning("FAILED (%s)", error_name)  # WHY: Failure marker via logger.
    logging.error("Org Data Collector: %s failed: %s: %s", api_name, error_name, error)  # WHY: Full detail log
    return _RESULT_FAILED


def _print_summary(total: int, totals: _RunTotals) -> None:
    """Print collection summary to console and log."""
    minutes, seconds = _split_elapsed(totals.elapsed)  # WHY: Precompute minutes/seconds for banner + log
    _print_summary_banner(total, totals, minutes, seconds)  # WHY: Console section for the operator
    logging.info(  # WHY: Structured completion record for post-run analysis
        "Org Data Collector: complete -- %s/%s succeeded, %s failed, %sm %ss elapsed",
        totals.succeeded,
        total,
        totals.failed,
        minutes,
        seconds,
    )


def _split_elapsed(elapsed: float) -> tuple[int, int]:
    """Split ``elapsed`` seconds into an integer (minutes, seconds) tuple."""  # WHY: Reused by summary + log
    minutes = int(elapsed // _SECONDS_PER_MINUTE)  # WHY: Floor-divide to isolate whole minutes
    seconds = int(elapsed % _SECONDS_PER_MINUTE)  # WHY: Remainder gives leftover whole seconds
    return minutes, seconds


def _print_summary_banner(total: int, totals: _RunTotals, minutes: int, seconds: int) -> None:
    """Emit the operator-facing summary banner for the completed run."""  # WHY: Pure console output helper
    logging.warning(  # WHY: Summary banner via logger. Single call preserves block cohesion.
        "\n%s\n  Org Data Collection Complete\n%s\n"
        "  Total:     %s\n"
        "  Succeeded: %s\n"
        "  Failed:    %s\n"
        "  Skipped:   %s\n"
        "  Duration:  %sm %ss\n"
        "%s",
        _SEPARATOR,
        _SEPARATOR,
        total,
        totals.succeeded,
        totals.failed,
        totals.skipped,
        minutes,
        seconds,
        _SEPARATOR,
    )
