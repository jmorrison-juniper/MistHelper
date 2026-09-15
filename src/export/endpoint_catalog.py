"""Description and safety flag for each endpoint family operation.

Why:
    Menus 259 through 268 group 286 read operations into ten families. Each
    family listed the raw operationId alone, so an operator read `getOrgWlan`
    and learned nothing about the call or its risk.

    This module gives one description and one safety flag to each operation.
    The description comes from the Mist API documentation name that the
    installed `mistapi` docstring carries, so the text states what the endpoint
    reads. The safety flag uses the words of `OperationRegistry`, so the menu
    agrees with `--test` and `--testinteractive`.

Safety words:
    `safe` names a read that needs no operator identifier. `--test` runs it.
    `interactive_safe` names a read that needs a site, an org, an MSP, or
    another identifier. `--testinteractive` runs it.
    `destructive` names a call that changes the Mist cloud. No endpoint family
    holds one, and `tests/guardrails/test_endpoint_catalog.py` keeps it that
    way.
"""

from __future__ import annotations

from dataclasses import dataclass

SAFE = "safe"  # A read that needs no operator identifier.
INTERACTIVE_SAFE = "interactive_safe"  # A read that needs an identifier.
DESTRUCTIVE = "destructive"  # A call that changes the Mist cloud.

VALID_SAFETY = (SAFE, INTERACTIVE_SAFE, DESTRUCTIVE)  # The words this module accepts.

# The words that the menu prints. The operator reads plain words, and the code
# keeps the registry word.
SAFETY_LABELS = {
    SAFE: "safe",
    INTERACTIVE_SAFE: "safe interactive",
    DESTRUCTIVE: "not safe",
}


@dataclass(frozen=True)
class EndpointInfo:
    """One menu description and one safety flag for a single operation."""

    description: str  # The plain text that the sub-menu prints after the name.
    safety: str  # One word from VALID_SAFETY.

    @property
    def label(self) -> str:
        """Return the safety word that the menu prints.

        Returns:
            The operator-facing safety word.
        """
        return SAFETY_LABELS.get(self.safety, self.safety)  # An unknown word prints as itself.


ENDPOINT_CATALOG: dict[str, EndpointInfo] = {
    "GetOrgTicketAttachment": EndpointInfo("Get org ticket attachment", INTERACTIVE_SAFE),
    "ListSiteWxRulesDerived": EndpointInfo("List site WxRules derived", INTERACTIVE_SAFE),
    "adoptOrgJsiDevice": EndpointInfo("Adopt org JSI device", INTERACTIVE_SAFE),
    "downloadMspSamlMetadata": EndpointInfo("Download MSP SAML metadata (needs SSO)", INTERACTIVE_SAFE),
    "downloadOrgNacPortalSamlMetadata": EndpointInfo("Download org NAC portal SAML metadata", INTERACTIVE_SAFE),
    "downloadOrgSamlMetadata": EndpointInfo("Download org SAML metadata (needs SSO)", INTERACTIVE_SAFE),
    "downloadSiteRfdiagRecording": EndpointInfo("Download site RF diagnostic recording", INTERACTIVE_SAFE),
    "exportSiteDevices": EndpointInfo("Export site devices", INTERACTIVE_SAFE),
    "generateSecretFor2faVerification": EndpointInfo("Generate secret for two-factor verification", INTERACTIVE_SAFE),
    "getAdminRegistrationInfo": EndpointInfo("Get admin registration info", SAFE),
    "getApiToken": EndpointInfo("Get API token", INTERACTIVE_SAFE),
    "getGatewayDefaultConfig": EndpointInfo("Get gateway default config (needs model)", INTERACTIVE_SAFE),
    "getInstallerDeviceVirtualChassis": EndpointInfo(
        "Get installer device virtual chassis (needs FPC0 MAC)",
        INTERACTIVE_SAFE,
    ),
    "getMspAdmin": EndpointInfo("Get MSP admin", INTERACTIVE_SAFE),
    "getMspDetails": EndpointInfo("Get MSP details", INTERACTIVE_SAFE),
    "getMspInventoryByMac": EndpointInfo("Get MSP inventory by MAC (needs device MAC)", INTERACTIVE_SAFE),
    "getMspOrg": EndpointInfo("Get MSP org", INTERACTIVE_SAFE),
    "getMspOrgGroup": EndpointInfo("Get MSP org group", INTERACTIVE_SAFE),
    "getMspSamlMetadata": EndpointInfo("Get MSP SAML metadata (needs SSO)", INTERACTIVE_SAFE),
    "getMspSle": EndpointInfo("Get MSP SLE (needs metric)", INTERACTIVE_SAFE),
    "getMspSso": EndpointInfo("Get MSP SSO", INTERACTIVE_SAFE),
    "getOauth2AuthorizationUrlForLogin": EndpointInfo(
        "Get OAuth 2.0 authorization URL for login (needs provider)",
        INTERACTIVE_SAFE,
    ),
    "getOauth2UrlForLinking": EndpointInfo("Get OAuth 2.0 URL for linking (needs provider)", INTERACTIVE_SAFE),
    "getOrgAAMWProfile": EndpointInfo("Get org AAMW profile", INTERACTIVE_SAFE),
    "getOrgAlarmTemplate": EndpointInfo("Get org alarm template", INTERACTIVE_SAFE),
    "getOrgAntivirusProfile": EndpointInfo("Get org antivirus profile (needs AV profile)", INTERACTIVE_SAFE),
    "getOrgAoscxRegisterCmd": EndpointInfo("Get org AOS-CX register command", INTERACTIVE_SAFE),
    "getOrgApiToken": EndpointInfo("Get org API token", INTERACTIVE_SAFE),
    "getOrgApplicationList": EndpointInfo("Get org application list", INTERACTIVE_SAFE),
    "getOrgAptemplate": EndpointInfo("Get org AP template", INTERACTIVE_SAFE),
    "getOrgAsset": EndpointInfo("Get org asset", INTERACTIVE_SAFE),
    "getOrgAssetFilter": EndpointInfo("Get org asset filter", INTERACTIVE_SAFE),
    "getOrgCapturingStatus": EndpointInfo("Get org capturing status", INTERACTIVE_SAFE),
    "getOrgCrlFile": EndpointInfo("Get org crl file", INTERACTIVE_SAFE),
    "getOrgCurrentMatchingClientsOfAWxTag": EndpointInfo(
        "Get org current matching clients of a WxTag",
        INTERACTIVE_SAFE,
    ),
    "getOrgDeviceProfile": EndpointInfo("Get org device profile", INTERACTIVE_SAFE),
    "getOrgDeviceUpgrade": EndpointInfo("Get org device upgrade", INTERACTIVE_SAFE),
    "getOrgEvpnTopology": EndpointInfo("Get org EVPN topology", INTERACTIVE_SAFE),
    "getOrgGuestAuthorization": EndpointInfo("Get org guest authorization (needs guest MAC)", INTERACTIVE_SAFE),
    "getOrgIdpProfile": EndpointInfo("Get org IDP profile", INTERACTIVE_SAFE),
    "getOrgJseInfo": EndpointInfo("Get org jse info", INTERACTIVE_SAFE),
    "getOrgJseIntegration": EndpointInfo("Get org jse integration", INTERACTIVE_SAFE),
    "getOrgJuniperDevicesCommand": EndpointInfo("Get org juniper devices command", INTERACTIVE_SAFE),
    "getOrgLicensesSummary": EndpointInfo("Get org licenses summary", INTERACTIVE_SAFE),
    "getOrgMarvisClientInvite": EndpointInfo("Get org marvis client invite (needs Marvis invite)", INTERACTIVE_SAFE),
    "getOrgMistScep": EndpointInfo("Get org mist scep", INTERACTIVE_SAFE),
    "getOrgMxEdge": EndpointInfo("Get org mx edge (needs Mist Edge)", INTERACTIVE_SAFE),
    "getOrgMxEdgeCluster": EndpointInfo("Get org mx edge cluster (needs Mist Edge cluster)", INTERACTIVE_SAFE),
    "getOrgMxEdgeUpgrade": EndpointInfo("Get org mx edge upgrade", INTERACTIVE_SAFE),
    "getOrgMxEdgeUpgradeInfo": EndpointInfo("Get org mx edge upgrade info", INTERACTIVE_SAFE),
    "getOrgMxEdgeVmParams": EndpointInfo("Get org mx edge vm params (needs Mist Edge)", INTERACTIVE_SAFE),
    "getOrgMxTunnel": EndpointInfo("Get org mx tunnel (needs Mist tunnel)", INTERACTIVE_SAFE),
    "getOrgNacCrl": EndpointInfo("Get org NAC crl", INTERACTIVE_SAFE),
    "getOrgNacPortal": EndpointInfo("Get org NAC portal", INTERACTIVE_SAFE),
    "getOrgNacPortalSamlMetadata": EndpointInfo("Get org NAC portal SAML metadata", INTERACTIVE_SAFE),
    "getOrgNacRule": EndpointInfo("Get org NAC rule", INTERACTIVE_SAFE),
    "getOrgNacTag": EndpointInfo("Get org NAC tag", INTERACTIVE_SAFE),
    "getOrgNetwork": EndpointInfo("Get org network", INTERACTIVE_SAFE),
    "getOrgNetworkTemplate": EndpointInfo("Get org network template", INTERACTIVE_SAFE),
    "getOrgOauthAppLinkedStatus": EndpointInfo(
        "Get org OAuth app linked status (needs app name, forward)",
        INTERACTIVE_SAFE,
    ),
    "getOrgOtherDevice": EndpointInfo("Get org other device (needs device MAC)", INTERACTIVE_SAFE),
    "getOrgOtherDeviceStats": EndpointInfo("Get org other device stats (needs device MAC)", INTERACTIVE_SAFE),
    "getOrgPsk": EndpointInfo("Get org PSK", INTERACTIVE_SAFE),
    "getOrgPskPortal": EndpointInfo("Get org PSK portal", INTERACTIVE_SAFE),
    "getOrgRfTemplate": EndpointInfo("Get org RF template", INTERACTIVE_SAFE),
    "getOrgSamlMetadata": EndpointInfo("Get org SAML metadata (needs SSO)", INTERACTIVE_SAFE),
    "getOrgSecPolicy": EndpointInfo("Get org sec policy (needs security policy)", INTERACTIVE_SAFE),
    "getOrgService": EndpointInfo("Get org service", INTERACTIVE_SAFE),
    "getOrgServicePolicy": EndpointInfo("Get org service policy", INTERACTIVE_SAFE),
    "getOrgSettings": EndpointInfo("Get org settings", INTERACTIVE_SAFE),
    "getOrgSiteGroup": EndpointInfo("Get org site group", INTERACTIVE_SAFE),
    "getOrgSkyAtpIntegration": EndpointInfo("Get org sky atp integration", INTERACTIVE_SAFE),
    "getOrgSslProxyCert": EndpointInfo("Get org ssl proxy cert", INTERACTIVE_SAFE),
    "getOrgSso": EndpointInfo("Get org SSO", INTERACTIVE_SAFE),
    "getOrgSsoRole": EndpointInfo("Get org SSO role", INTERACTIVE_SAFE),
    "getOrgSsrRegistrationCommands": EndpointInfo("Get org SSR registration commands", INTERACTIVE_SAFE),
    "getOrgSsrUpgrade": EndpointInfo("Get org SSR upgrade", INTERACTIVE_SAFE),
    "getOrgStats": EndpointInfo("Get org stats", INTERACTIVE_SAFE),
    "getOrgTemplate": EndpointInfo("Get org template", INTERACTIVE_SAFE),
    "getOrgUiSetting": EndpointInfo("Get org UI setting (needs uisetting)", INTERACTIVE_SAFE),
    "getOrgUserMac": EndpointInfo("Get org user MAC", INTERACTIVE_SAFE),
    "getOrgVpn": EndpointInfo("Get org VPN", INTERACTIVE_SAFE),
    "getOrgWLAN": EndpointInfo("Get org WLAN", INTERACTIVE_SAFE),
    "getOrgWebhook": EndpointInfo("Get org webhook", INTERACTIVE_SAFE),
    "getOrgWxRule": EndpointInfo("Get org WxRule", INTERACTIVE_SAFE),
    "getOrgWxTag": EndpointInfo("Get org WxTag", INTERACTIVE_SAFE),
    "getOrgWxTunnel": EndpointInfo("Get org WxTunnel", INTERACTIVE_SAFE),
    "getOrgZscalerIntegration": EndpointInfo("Get org zscaler integration", INTERACTIVE_SAFE),
    "getSdkInvite": EndpointInfo("Get sdk invite", INTERACTIVE_SAFE),
    "getSdkInviteQrCode": EndpointInfo("Get sdk invite qr code", INTERACTIVE_SAFE),
    "getSdkTemplate": EndpointInfo("Get sdk template", INTERACTIVE_SAFE),
    "getSelf": EndpointInfo("Get self", SAFE),
    "getSelfLoginFailures": EndpointInfo("Get self login failures", SAFE),
    "getSiteAllClientsStatsByDevice": EndpointInfo("Get site all clients stats by device", INTERACTIVE_SAFE),
    "getSiteApAutoOrientation": EndpointInfo("Get site AP auto orientation (needs map)", INTERACTIVE_SAFE),
    "getSiteApAutoPlacement": EndpointInfo("Get site AP auto placement (needs map)", INTERACTIVE_SAFE),
    "getSiteAssetStats": EndpointInfo("Get site asset stats", INTERACTIVE_SAFE),
    "getSiteBeamCoverageOverview": EndpointInfo("Get site beam coverage overview", INTERACTIVE_SAFE),
    "getSiteCallsSummary": EndpointInfo("Get site calls summary", INTERACTIVE_SAFE),
    "getSiteCapturingStatus": EndpointInfo("Get site capturing status", INTERACTIVE_SAFE),
    "getSiteCurrentChannelPlanning": EndpointInfo("Get site current channel planning", INTERACTIVE_SAFE),
    "getSiteCurrentRrmConsiderations": EndpointInfo(
        "Get site current RRM considerations (needs device, band)",
        INTERACTIVE_SAFE,
    ),
    "getSiteDefaultPlfForModels": EndpointInfo("Get site default plf for models", INTERACTIVE_SAFE),
    "getSiteDeviceConfigCmd": EndpointInfo("Get site device config cmd", INTERACTIVE_SAFE),
    "getSiteDeviceIotPort": EndpointInfo("Get site device iot port", INTERACTIVE_SAFE),
    "getSiteDiscoveredAssetByMap": EndpointInfo("Get site discovered asset by map", INTERACTIVE_SAFE),
    "getSiteEventsForClient": EndpointInfo("Get site events for client (needs client MAC)", INTERACTIVE_SAFE),
    "getSiteEvpnTopology": EndpointInfo("Get site EVPN topology", INTERACTIVE_SAFE),
    "getSiteGatewayMetrics": EndpointInfo("Get site gateway metrics", INTERACTIVE_SAFE),
    "getSiteGuestAuthorization": EndpointInfo("Get site guest authorization (needs guest MAC)", INTERACTIVE_SAFE),
    "getSiteInsightMetricsForGateway": EndpointInfo(
        "Get site insight metrics for gateway (needs device)",
        INTERACTIVE_SAFE,
    ),
    "getSiteInsightMetricsForMxEdge": EndpointInfo(
        "Get site insight metrics for mx edge (needs device MAC)",
        INTERACTIVE_SAFE,
    ),
    "getSiteInsightMetricsForSwitch": EndpointInfo(
        "Get site insight metrics for switch (needs device MAC)",
        INTERACTIVE_SAFE,
    ),
    "getSiteJseInfo": EndpointInfo("Get site jse info", INTERACTIVE_SAFE),
    "getSiteLicenseUsage": EndpointInfo("Get site license usage", INTERACTIVE_SAFE),
    "getSiteMachineLearningCurrentStat": EndpointInfo("Get site machine learning current stat", INTERACTIVE_SAFE),
    "getSiteMapAutoZoneStatus": EndpointInfo("Get site map auto zone status", INTERACTIVE_SAFE),
    "getSiteMxEdge": EndpointInfo("Get site mx edge (needs Mist Edge)", INTERACTIVE_SAFE),
    "getSiteMxEdgeStats": EndpointInfo("Get site mx edge stats (needs Mist Edge)", INTERACTIVE_SAFE),
    "getSitePsk": EndpointInfo("Get site PSK", INTERACTIVE_SAFE),
    "getSiteRfdiagRecording": EndpointInfo("Get site RF diagnostic recording", INTERACTIVE_SAFE),
    "getSiteRogueAP": EndpointInfo("Get site rogue AP (needs rogue BSSID)", INTERACTIVE_SAFE),
    "getSiteRssiZone": EndpointInfo("Get site RSSI zone", INTERACTIVE_SAFE),
    "getSiteRssiZoneStats": EndpointInfo("Get site RSSI zone stats", INTERACTIVE_SAFE),
    "getSiteRunningSpectrumAnalysis": EndpointInfo("Get site running spectrum analysis", INTERACTIVE_SAFE),
    "getSiteSdkStats": EndpointInfo("Get site sdk stats (needs SDK client)", INTERACTIVE_SAFE),
    "getSiteSdkStatsByMap": EndpointInfo("Get site sdk stats by map", INTERACTIVE_SAFE),
    "getSiteSettingDerived": EndpointInfo("Get site setting derived", INTERACTIVE_SAFE),
    "getSiteSiteRfdiagRecording": EndpointInfo("Get site RF diagnostic recording", INTERACTIVE_SAFE),
    "getSiteSleClassifierDetails": EndpointInfo(
        "Get site SLE classifier details (needs scope, scope ID, metric)",
        INTERACTIVE_SAFE,
    ),
    "getSiteSleClassifierSummaryTrend": EndpointInfo(
        "Get site SLE classifier summary trend (needs scope, scope ID, metric)",
        INTERACTIVE_SAFE,
    ),
    "getSiteSleHistogram": EndpointInfo("Get site SLE histogram (needs scope, scope ID, metric)", INTERACTIVE_SAFE),
    "getSiteSleImpactSummary": EndpointInfo(
        "Get site SLE impact summary (needs scope, scope ID, metric)",
        INTERACTIVE_SAFE,
    ),
    "getSiteSleSummary": EndpointInfo("Get site SLE summary (needs scope, scope ID, metric)", INTERACTIVE_SAFE),
    "getSiteSleSummaryTrend": EndpointInfo(
        "Get site SLE summary trend (needs scope, scope ID, metric)",
        INTERACTIVE_SAFE,
    ),
    "getSiteSleThreshold": EndpointInfo("Get site SLE threshold (needs scope, scope ID, metric)", INTERACTIVE_SAFE),
    "getSiteSsrUpgrade": EndpointInfo("Get site SSR upgrade", INTERACTIVE_SAFE),
    "getSiteStats": EndpointInfo("Get site stats", INTERACTIVE_SAFE),
    "getSiteSwitchesMetrics": EndpointInfo("Get site switches metrics", INTERACTIVE_SAFE),
    "getSiteUiSetting": EndpointInfo("Get site UI setting (needs uisetting)", INTERACTIVE_SAFE),
    "getSiteVBeacon": EndpointInfo("Get site vBeacon", INTERACTIVE_SAFE),
    "getSiteWebhook": EndpointInfo("Get site webhook", INTERACTIVE_SAFE),
    "getSiteWirelessClientStats": EndpointInfo("Get site wireless client stats (needs client MAC)", INTERACTIVE_SAFE),
    "getSiteWirelessClientsStatsByMap": EndpointInfo("Get site wireless clients stats by map", INTERACTIVE_SAFE),
    "getSiteWlan": EndpointInfo("Get site WLAN", INTERACTIVE_SAFE),
    "getSiteWxRule": EndpointInfo("Get site WxRule", INTERACTIVE_SAFE),
    "getSiteWxRulesUsage": EndpointInfo("Get site WxRules usage", INTERACTIVE_SAFE),
    "getSiteWxTag": EndpointInfo("Get site WxTag", INTERACTIVE_SAFE),
    "getSiteWxTunnel": EndpointInfo("Get site WxTunnel", INTERACTIVE_SAFE),
    "getSiteZone": EndpointInfo("Get site zone", INTERACTIVE_SAFE),
    "getSiteZoneStats": EndpointInfo("Get site zone stats", INTERACTIVE_SAFE),
    "listAlarmDefinitions": EndpointInfo("List alarm definitions", SAFE),
    "listAlarmSubscriptions": EndpointInfo("List alarm subscriptions", SAFE),
    "listApChannels": EndpointInfo("List AP channels", SAFE),
    "listApLEslVersions": EndpointInfo("List AP ESL versions", SAFE),
    "listApLedDefinition": EndpointInfo("List AP LED definition", SAFE),
    "listApiTokens": EndpointInfo("List API tokens", SAFE),
    "listAppCategoryDefinitions": EndpointInfo("List app category definitions", SAFE),
    "listAppSubCategoryDefinitions": EndpointInfo("List app sub category definitions", SAFE),
    "listApplications": EndpointInfo("List applications", SAFE),
    "listClientEventsDefinitions": EndpointInfo("List client events definitions", SAFE),
    "listCountryCodes": EndpointInfo("List country codes", SAFE),
    "listDeviceEventsDefinitions": EndpointInfo("List device events definitions", SAFE),
    "listDeviceModels": EndpointInfo("List device models", SAFE),
    "listFingerprintTypes": EndpointInfo("List fingerprint types", SAFE),
    "listGatewayApplications": EndpointInfo("List gateway applications", SAFE),
    "listInstallerAlarmTemplates": EndpointInfo("List installer alarm templates", INTERACTIVE_SAFE),
    "listInstallerDeviceProfiles": EndpointInfo("List installer device profiles", INTERACTIVE_SAFE),
    "listInstallerListOfRecentlyClaimedDevices": EndpointInfo(
        "List installer list of recently claimed devices",
        INTERACTIVE_SAFE,
    ),
    "listInstallerMaps": EndpointInfo("List installer maps (needs site name)", INTERACTIVE_SAFE),
    "listInstallerRfTemplatesNames": EndpointInfo("List installer RF templates names", INTERACTIVE_SAFE),
    "listInstallerSiteGroups": EndpointInfo("List installer site groups", INTERACTIVE_SAFE),
    "listInstallerSites": EndpointInfo("List installer sites", INTERACTIVE_SAFE),
    "listLicenseTypes": EndpointInfo("List license types", SAFE),
    "listMarvisClientVersions": EndpointInfo("List marvis client versions", SAFE),
    "listMspAdmins": EndpointInfo("List MSP admins", INTERACTIVE_SAFE),
    "listMspAuditLogs": EndpointInfo("List MSP audit logs", INTERACTIVE_SAFE),
    "listMspOrgGroups": EndpointInfo("List MSP org groups", INTERACTIVE_SAFE),
    "listMspOrgLicenses": EndpointInfo("List MSP org licenses", INTERACTIVE_SAFE),
    "listMspOrgStats": EndpointInfo("List MSP org stats", INTERACTIVE_SAFE),
    "listMspOrgs": EndpointInfo("List MSP org", INTERACTIVE_SAFE),
    "listMspSsoLatestFailures": EndpointInfo("List MSP SSO latest failures", INTERACTIVE_SAFE),
    "listMspSsoRoles": EndpointInfo("List MSP SSO roles", INTERACTIVE_SAFE),
    "listMspSsos": EndpointInfo("List MSP SSO", INTERACTIVE_SAFE),
    "listMspTickets": EndpointInfo("List MSP tickets", INTERACTIVE_SAFE),
    "listMxEdgeEventsDefinitions": EndpointInfo("List mx edge events definitions", SAFE),
    "listMxEdgeModels": EndpointInfo("List mx edge models", SAFE),
    "listNacEventsDefinitions": EndpointInfo("List NAC events definitions", SAFE),
    "listOrgAAMWProfiles": EndpointInfo("List org AAMW profiles", INTERACTIVE_SAFE),
    "listOrgAntivirusProfiles": EndpointInfo("List org antivirus profiles", INTERACTIVE_SAFE),
    "listOrgApsMacs": EndpointInfo("List org APs macs", INTERACTIVE_SAFE),
    "listOrgAssetFilters": EndpointInfo("List org asset filters", INTERACTIVE_SAFE),
    "listOrgAssets": EndpointInfo("List org assets", INTERACTIVE_SAFE),
    "listOrgAssetsStats": EndpointInfo("List org assets stats", INTERACTIVE_SAFE),
    "listOrgCertificates": EndpointInfo("List org certificates", INTERACTIVE_SAFE),
    "listOrgDeviceUpgrades": EndpointInfo("List org device upgrades", INTERACTIVE_SAFE),
    "listOrgDevicesSummary": EndpointInfo("List org devices summary", INTERACTIVE_SAFE),
    "listOrgEvpnTopologies": EndpointInfo("List org EVPN topologies", INTERACTIVE_SAFE),
    "listOrgGuestAuthorizations": EndpointInfo("List org guest authorizations", INTERACTIVE_SAFE),
    "listOrgIdpProfiles": EndpointInfo("List org IDP profiles", INTERACTIVE_SAFE),
    "listOrgIssuedClientCertificates": EndpointInfo("List org issued client certificates", INTERACTIVE_SAFE),
    "listOrgJsiDevices": EndpointInfo("List org JSI devices", INTERACTIVE_SAFE),
    "listOrgJsiPastPurchases": EndpointInfo("List org JSI past purchases", INTERACTIVE_SAFE),
    "listOrgMarvisClientInvites": EndpointInfo("List org marvis client invites", INTERACTIVE_SAFE),
    "listOrgMxEdgeClusters": EndpointInfo("List org mx edge clusters", INTERACTIVE_SAFE),
    "listOrgMxEdgeUpgrades": EndpointInfo("List org mx edge upgrades", INTERACTIVE_SAFE),
    "listOrgMxTunnels": EndpointInfo("List org mx tunnels", INTERACTIVE_SAFE),
    "listOrgNacPortalSsoLatestFailures": EndpointInfo("List org NAC portal SSO latest failures", INTERACTIVE_SAFE),
    "listOrgOtherDevices": EndpointInfo("List org other devices", INTERACTIVE_SAFE),
    "listOrgPmaDashboards": EndpointInfo("List org pma dashboards", INTERACTIVE_SAFE),
    "listOrgPskPortalLogs": EndpointInfo("List org PSK portal logs", INTERACTIVE_SAFE),
    "listOrgPskPortals": EndpointInfo("List org PSK portals", INTERACTIVE_SAFE),
    "listOrgSiteGroups": EndpointInfo("List org site groups", INTERACTIVE_SAFE),
    "listOrgSsoLatestFailures": EndpointInfo("List org SSO latest failures", INTERACTIVE_SAFE),
    "listOrgSsoRoles": EndpointInfo("List org SSO roles", INTERACTIVE_SAFE),
    "listOrgSuppressedAlarms": EndpointInfo("List org suppressed alarms", INTERACTIVE_SAFE),
    "listOrgUiSettings": EndpointInfo("List org UI settings", INTERACTIVE_SAFE),
    "listOrgWxRules": EndpointInfo("List org WxRules", INTERACTIVE_SAFE),
    "listOrgWxTags": EndpointInfo("List org WxTags", INTERACTIVE_SAFE),
    "listOrgWxTunnels": EndpointInfo("List org WxTunnels", INTERACTIVE_SAFE),
    "listOtherDeviceEventsDefinitions": EndpointInfo("List other device events definitions", SAFE),
    "listSdkInvites": EndpointInfo("List sdk invites", INTERACTIVE_SAFE),
    "listSdkTemplates": EndpointInfo("List sdk templates", INTERACTIVE_SAFE),
    "listSiteAAMWProfilesDerived": EndpointInfo("List site AAMW profiles derived", INTERACTIVE_SAFE),
    "listSiteAllGuestAuthorizations": EndpointInfo("List site all guest authorizations", INTERACTIVE_SAFE),
    "listSiteAllGuestAuthorizationsDerived": EndpointInfo(
        "List site all guest authorizations derived",
        INTERACTIVE_SAFE,
    ),
    "listSiteAntivirusProfilesDerived": EndpointInfo("List site antivirus profiles derived", INTERACTIVE_SAFE),
    "listSiteApTemplatesDerived": EndpointInfo("List site AP templates derived", INTERACTIVE_SAFE),
    "listSiteApps": EndpointInfo("List site apps", INTERACTIVE_SAFE),
    "listSiteAssetFilters": EndpointInfo("List site asset filters", INTERACTIVE_SAFE),
    "listSiteAssets": EndpointInfo("List site assets", INTERACTIVE_SAFE),
    "listSiteAssetsStats": EndpointInfo("List site assets stats", INTERACTIVE_SAFE),
    "listSiteAvailableDeviceVersions": EndpointInfo("List site available device versions", INTERACTIVE_SAFE),
    "listSiteBeaconsStats": EndpointInfo("List site beacons stats", INTERACTIVE_SAFE),
    "listSiteCurrentRrmNeighbors": EndpointInfo("List site current RRM neighbors (needs band)", INTERACTIVE_SAFE),
    "listSiteDeviceProfilesDerived": EndpointInfo("List site device profiles derived", INTERACTIVE_SAFE),
    "listSiteDeviceRadioChannels": EndpointInfo("List site device radio channels", INTERACTIVE_SAFE),
    "listSiteDiscoveredAssets": EndpointInfo("List site discovered assets", INTERACTIVE_SAFE),
    "listSiteDiscoveredSwitchesMetrics": EndpointInfo("List site discovered switches metrics", INTERACTIVE_SAFE),
    "listSiteEvpnTopologies": EndpointInfo("List site EVPN topologies", INTERACTIVE_SAFE),
    "listSiteIdpProfilesDerived": EndpointInfo("List site IDP profiles derived", INTERACTIVE_SAFE),
    "listSiteLanguages": EndpointInfo("List site languages", SAFE),
    "listSiteMapStacks": EndpointInfo("List site map stacks", INTERACTIVE_SAFE),
    "listSiteMxEdges": EndpointInfo("List site mx edges", INTERACTIVE_SAFE),
    "listSiteMxEdgesStats": EndpointInfo("List site mx edges stats", INTERACTIVE_SAFE),
    "listSiteNetworkTemplatesDerived": EndpointInfo("List site network templates derived", INTERACTIVE_SAFE),
    "listSiteOtherDevices": EndpointInfo("List site other devices", INTERACTIVE_SAFE),
    "listSitePsks": EndpointInfo("List site PSKs", INTERACTIVE_SAFE),
    "listSiteRfTemplatesDerived": EndpointInfo("List site RF templates derived", INTERACTIVE_SAFE),
    "listSiteRoamingEvents": EndpointInfo("List site roaming events", INTERACTIVE_SAFE),
    "listSiteRrmEvents": EndpointInfo("List site RRM events", INTERACTIVE_SAFE),
    "listSiteRssiZones": EndpointInfo("List site RSSI zones", INTERACTIVE_SAFE),
    "listSiteRssiZonesStats": EndpointInfo("List site RSSI zones stats", INTERACTIVE_SAFE),
    "listSiteSecIntelProfilesDerived": EndpointInfo("List site sec intel profiles derived", INTERACTIVE_SAFE),
    "listSiteServicesDerived": EndpointInfo("List site services derived", INTERACTIVE_SAFE),
    "listSiteSiteTemplatesDerived": EndpointInfo("List site templates derived", INTERACTIVE_SAFE),
    "listSiteSleImpactedApplications": EndpointInfo(
        "List site SLE impacted applications (needs scope, scope ID, metric)",
        INTERACTIVE_SAFE,
    ),
    "listSiteSleImpactedAps": EndpointInfo(
        "List site SLE impacted APs (needs scope, scope ID, metric)",
        INTERACTIVE_SAFE,
    ),
    "listSiteSleImpactedChassis": EndpointInfo(
        "List site SLE impacted chassis (needs scope, scope ID, metric)",
        INTERACTIVE_SAFE,
    ),
    "listSiteSleImpactedGateways": EndpointInfo(
        "List site SLE impacted gateways (needs scope, scope ID, metric)",
        INTERACTIVE_SAFE,
    ),
    "listSiteSleImpactedInterfaces": EndpointInfo(
        "List site SLE impacted interfaces (needs scope, scope ID, metric)",
        INTERACTIVE_SAFE,
    ),
    "listSiteSleImpactedSwitches": EndpointInfo(
        "List site SLE impacted switches (needs scope, scope ID, metric)",
        INTERACTIVE_SAFE,
    ),
    "listSiteSleImpactedWiredClients": EndpointInfo(
        "List site SLE impacted wired clients (needs scope, scope ID, metric)",
        INTERACTIVE_SAFE,
    ),
    "listSiteSleImpactedWirelessClients": EndpointInfo(
        "List site SLE impacted wireless clients (needs scope, scope ID, metric)",
        INTERACTIVE_SAFE,
    ),
    "listSiteSleMetricClassifiers": EndpointInfo(
        "List site SLE metric classifiers (needs scope, scope ID)",
        INTERACTIVE_SAFE,
    ),
    "listSiteSlesMetrics": EndpointInfo("List site SLE metrics (needs scope, scope ID)", INTERACTIVE_SAFE),
    "listSiteSpectrumAnalysis": EndpointInfo("List site spectrum analysis", INTERACTIVE_SAFE),
    "listSiteTroubleshootCalls": EndpointInfo("List site troubleshoot calls", INTERACTIVE_SAFE),
    "listSiteUiSettingDerived": EndpointInfo("List site UI setting derived", INTERACTIVE_SAFE),
    "listSiteUiSettings": EndpointInfo("List site UI settings", INTERACTIVE_SAFE),
    "listSiteUnconnectedClientStats": EndpointInfo("List site unconnected client stats (needs map)", INTERACTIVE_SAFE),
    "listSiteVpnsDerived": EndpointInfo("List site VPNs derived", INTERACTIVE_SAFE),
    "listSiteWebhooks": EndpointInfo("List site webhooks", INTERACTIVE_SAFE),
    "listSiteWxRules": EndpointInfo("List site WxRules", INTERACTIVE_SAFE),
    "listSiteWxTags": EndpointInfo("List site WxTags", INTERACTIVE_SAFE),
    "listSiteWxTunnels": EndpointInfo("List site WxTunnels", INTERACTIVE_SAFE),
    "listSiteZonesStats": EndpointInfo("List site zones stats", INTERACTIVE_SAFE),
    "listStates": EndpointInfo("List states (needs country code)", INTERACTIVE_SAFE),
    "listSupportedOtherDeviceModels": EndpointInfo("List supported other device models", SAFE),
    "listSystemEventsDefinitions": EndpointInfo("List system events definitions", SAFE),
    "listTrafficTypes": EndpointInfo("List traffic types", SAFE),
    "listWebhookTopics": EndpointInfo("List webhook topics", SAFE),
    "searchMspOrgGroup": EndpointInfo("Search MSP org group (needs type, search text)", INTERACTIVE_SAFE),
    "searchMspOrgs": EndpointInfo("Search MSP org", INTERACTIVE_SAFE),
    "searchOrgDeviceLastConfigs": EndpointInfo("Search org device last configs", INTERACTIVE_SAFE),
    "searchSiteClientFingerprints": EndpointInfo("Search site client fingerprints", INTERACTIVE_SAFE),
}


def describe(operation: str) -> EndpointInfo:
    """Return the catalog entry for one operation.

    Why:
        A table row can name an operation that this catalog does not hold. The
        menu must still print a line, so this function answers with the
        operation name and the strictest safety word.

    Args:
        operation: The Mist operationId of the table row.

    Returns:
        The catalog entry, or a fallback entry when the catalog holds none.
    """
    found = ENDPOINT_CATALOG.get(operation)
    if found is not None:
        return found
    # WHY: An unknown operation must never read as a plain safe call.
    return EndpointInfo(operation, INTERACTIVE_SAFE)


def menu_text(operation: str) -> str:
    """Return the full sub-menu text for one operation.

    Args:
        operation: The Mist operationId of the table row.

    Returns:
        The operation name, the description, and the safety word.
    """
    info = describe(operation)
    return f"{operation} - {info.description} [{info.label}]"  # One row of the family sub-menu.
