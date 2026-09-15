# Mist API GET Endpoint Catalog

> Generated 2026-09-15T21:39:14Z from `documentation/mist-api-openapi31json.json`.

- **Total GET endpoints**: 529
- **Tags represented**: 198

## Index

- [Admins](#admins) (1 endpoints)
- [Admins Login - OAuth2](#admins-login---oauth2) (1 endpoints)
- [Constants Definitions](#constants-definitions) (17 endpoints)
- [Constants Events](#constants-events) (7 endpoints)
- [Constants Models](#constants-models) (4 endpoints)
- [Installer](#installer) (9 endpoints)
- [MSPs](#msps) (2 endpoints)
- [MSPs Admins](#msps-admins) (2 endpoints)
- [MSPs Inventory](#msps-inventory) (1 endpoints)
- [MSPs Licenses](#msps-licenses) (2 endpoints)
- [MSPs Logs](#msps-logs) (2 endpoints)
- [MSPs Marvis](#msps-marvis) (1 endpoints)
- [MSPs Org Groups](#msps-org-groups) (2 endpoints)
- [MSPs Orgs](#msps-orgs) (4 endpoints)
- [MSPs SLEs](#msps-sles) (1 endpoints)
- [MSPs SSO](#msps-sso) (5 endpoints)
- [MSPs SSO Roles](#msps-sso-roles) (1 endpoints)
- [MSPs Tickets](#msps-tickets) (2 endpoints)
- [Orgs](#orgs) (1 endpoints)
- [Orgs AP Templates](#orgs-ap-templates) (2 endpoints)
- [Orgs API Tokens](#orgs-api-tokens) (2 endpoints)
- [Orgs Admins](#orgs-admins) (1 endpoints)
- [Orgs Advanced Anti Malware Profiles](#orgs-advanced-anti-malware-profiles) (2 endpoints)
- [Orgs Alarm Templates](#orgs-alarm-templates) (3 endpoints)
- [Orgs Alarms](#orgs-alarms) (2 endpoints)
- [Orgs Antivirus Profiles](#orgs-antivirus-profiles) (2 endpoints)
- [Orgs Asset Filters](#orgs-asset-filters) (2 endpoints)
- [Orgs Assets](#orgs-assets) (2 endpoints)
- [Orgs CRL](#orgs-crl) (1 endpoints)
- [Orgs Cert](#orgs-cert) (2 endpoints)
- [Orgs Clients - Marvis](#orgs-clients---marvis) (3 endpoints)
- [Orgs Clients - NAC](#orgs-clients---nac) (4 endpoints)
- [Orgs Clients - Wan](#orgs-clients---wan) (4 endpoints)
- [Orgs Clients - Wired](#orgs-clients---wired) (2 endpoints)
- [Orgs Clients - Wireless](#orgs-clients---wireless) (6 endpoints)
- [Orgs Device Profiles](#orgs-device-profiles) (2 endpoints)
- [Orgs Devices](#orgs-devices) (10 endpoints)
- [Orgs Devices - AOSCX](#orgs-devices---aoscx) (1 endpoints)
- [Orgs Devices - EdgeConnect](#orgs-devices---edgeconnect) (1 endpoints)
- [Orgs Devices - Others](#orgs-devices---others) (4 endpoints)
- [Orgs Devices - SSR](#orgs-devices---ssr) (2 endpoints)
- [Orgs EVPN Topologies](#orgs-evpn-topologies) (2 endpoints)
- [Orgs Events](#orgs-events) (3 endpoints)
- [Orgs Gateway Templates](#orgs-gateway-templates) (2 endpoints)
- [Orgs Guests](#orgs-guests) (4 endpoints)
- [Orgs IDP Profiles](#orgs-idp-profiles) (2 endpoints)
- [Orgs Integration Cradlepoint](#orgs-integration-cradlepoint) (1 endpoints)
- [Orgs Integration JSE](#orgs-integration-jse) (2 endpoints)
- [Orgs Integration SkyATP](#orgs-integration-skyatp) (1 endpoints)
- [Orgs Integration Zscaler](#orgs-integration-zscaler) (1 endpoints)
- [Orgs Inventory](#orgs-inventory) (3 endpoints)
- [Orgs JSI](#orgs-jsi) (9 endpoints)
- [Orgs Licenses](#orgs-licenses) (5 endpoints)
- [Orgs Linked Applications](#orgs-linked-applications) (1 endpoints)
- [Orgs Logs](#orgs-logs) (3 endpoints)
- [Orgs Marvis](#orgs-marvis) (1 endpoints)
- [Orgs Marvis Invites](#orgs-marvis-invites) (2 endpoints)
- [Orgs MxClusters](#orgs-mxclusters) (2 endpoints)
- [Orgs MxEdges](#orgs-mxedges) (8 endpoints)
- [Orgs MxTunnels](#orgs-mxtunnels) (2 endpoints)
- [Orgs NAC CRL](#orgs-nac-crl) (1 endpoints)
- [Orgs NAC Portals](#orgs-nac-portals) (5 endpoints)
- [Orgs NAC Rules](#orgs-nac-rules) (2 endpoints)
- [Orgs NAC Tags](#orgs-nac-tags) (2 endpoints)
- [Orgs Network Templates](#orgs-network-templates) (2 endpoints)
- [Orgs Networks](#orgs-networks) (2 endpoints)
- [Orgs Premium Analytics](#orgs-premium-analytics) (1 endpoints)
- [Orgs Psk Portals](#orgs-psk-portals) (5 endpoints)
- [Orgs Psks](#orgs-psks) (2 endpoints)
- [Orgs RF Templates](#orgs-rf-templates) (2 endpoints)
- [Orgs Reports](#orgs-reports) (1 endpoints)
- [Orgs SCEP](#orgs-scep) (2 endpoints)
- [Orgs SDK Invites](#orgs-sdk-invites) (3 endpoints)
- [Orgs SDK Templates](#orgs-sdk-templates) (2 endpoints)
- [Orgs SLEs](#orgs-sles) (2 endpoints)
- [Orgs SSO](#orgs-sso) (5 endpoints)
- [Orgs SSO Roles](#orgs-sso-roles) (2 endpoints)
- [Orgs SecIntel Profiles](#orgs-secintel-profiles) (2 endpoints)
- [Orgs Security Policies](#orgs-security-policies) (2 endpoints)
- [Orgs Service Policies](#orgs-service-policies) (2 endpoints)
- [Orgs Services](#orgs-services) (2 endpoints)
- [Orgs Setting](#orgs-setting) (1 endpoints)
- [Orgs Site Templates](#orgs-site-templates) (2 endpoints)
- [Orgs Sitegroups](#orgs-sitegroups) (2 endpoints)
- [Orgs Sites](#orgs-sites) (3 endpoints)
- [Orgs Stats](#orgs-stats) (1 endpoints)
- [Orgs Stats - Assets](#orgs-stats---assets) (3 endpoints)
- [Orgs Stats - BGP Peers](#orgs-stats---bgp-peers) (2 endpoints)
- [Orgs Stats - Devices](#orgs-stats---devices) (1 endpoints)
- [Orgs Stats - Marvis Clients](#orgs-stats---marvis-clients) (2 endpoints)
- [Orgs Stats - MxEdges](#orgs-stats---mxedges) (2 endpoints)
- [Orgs Stats - Ospf](#orgs-stats---ospf) (2 endpoints)
- [Orgs Stats - Other Devices](#orgs-stats---other-devices) (1 endpoints)
- [Orgs Stats - Ports](#orgs-stats---ports) (2 endpoints)
- [Orgs Stats - Sites](#orgs-stats---sites) (1 endpoints)
- [Orgs Stats - Tunnels](#orgs-stats---tunnels) (2 endpoints)
- [Orgs Stats - VPN Peers](#orgs-stats---vpn-peers) (2 endpoints)
- [Orgs Tickets](#orgs-tickets) (4 endpoints)
- [Orgs UI Settings](#orgs-ui-settings) (2 endpoints)
- [Orgs User MACs](#orgs-user-macs) (3 endpoints)
- [Orgs VPNs](#orgs-vpns) (2 endpoints)
- [Orgs Vars](#orgs-vars) (1 endpoints)
- [Orgs WLAN Templates](#orgs-wlan-templates) (2 endpoints)
- [Orgs Webhooks](#orgs-webhooks) (4 endpoints)
- [Orgs Wlans](#orgs-wlans) (2 endpoints)
- [Orgs WxRules](#orgs-wxrules) (2 endpoints)
- [Orgs WxTags](#orgs-wxtags) (4 endpoints)
- [Orgs WxTunnels](#orgs-wxtunnels) (2 endpoints)
- [Self API Token](#self-api-token) (2 endpoints)
- [Self Account](#self-account) (4 endpoints)
- [Self Alarms](#self-alarms) (1 endpoints)
- [Self Audit Logs](#self-audit-logs) (1 endpoints)
- [Self MFA](#self-mfa) (1 endpoints)
- [Self OAuth2](#self-oauth2) (1 endpoints)
- [Sites](#sites) (1 endpoints)
- [Sites AP Templates](#sites-ap-templates) (1 endpoints)
- [Sites Advanced Anti Malware Profiles](#sites-advanced-anti-malware-profiles) (1 endpoints)
- [Sites Alarms](#sites-alarms) (2 endpoints)
- [Sites Anomaly](#sites-anomaly) (3 endpoints)
- [Sites Antivirus Profiles](#sites-antivirus-profiles) (1 endpoints)
- [Sites Applications](#sites-applications) (1 endpoints)
- [Sites Asset Filters](#sites-asset-filters) (2 endpoints)
- [Sites Assets](#sites-assets) (2 endpoints)
- [Sites Auto Map Assignment](#sites-auto-map-assignment) (1 endpoints)
- [Sites Beacons](#sites-beacons) (2 endpoints)
- [Sites Clients - NAC](#sites-clients---nac) (4 endpoints)
- [Sites Clients - Wan](#sites-clients---wan) (4 endpoints)
- [Sites Clients - Wired](#sites-clients---wired) (2 endpoints)
- [Sites Clients - Wireless](#sites-clients---wireless) (7 endpoints)
- [Sites Device Profiles](#sites-device-profiles) (1 endpoints)
- [Sites Devices](#sites-devices) (11 endpoints)
- [Sites Devices - Others](#sites-devices---others) (3 endpoints)
- [Sites Devices - WAN Cluster](#sites-devices---wan-cluster) (1 endpoints)
- [Sites Devices - Wired - Virtual Chassis](#sites-devices---wired---virtual-chassis) (1 endpoints)
- [Sites Devices - Wireless](#sites-devices---wireless) (2 endpoints)
- [Sites EVPN Topologies](#sites-evpn-topologies) (2 endpoints)
- [Sites Events](#sites-events) (3 endpoints)
- [Sites Gateway Templates](#sites-gateway-templates) (1 endpoints)
- [Sites Guests](#sites-guests) (5 endpoints)
- [Sites IDP Profiles](#sites-idp-profiles) (1 endpoints)
- [Sites Insights](#sites-insights) (7 endpoints)
- [Sites JSE](#sites-jse) (1 endpoints)
- [Sites Licenses](#sites-licenses) (1 endpoints)
- [Sites Location](#sites-location) (3 endpoints)
- [Sites Map Stacks](#sites-map-stacks) (1 endpoints)
- [Sites Maps](#sites-maps) (2 endpoints)
- [Sites Maps - Auto-Zone](#sites-maps---auto-zone) (1 endpoints)
- [Sites Maps - Auto-placement](#sites-maps---auto-placement) (2 endpoints)
- [Sites Marvis Configs](#sites-marvis-configs) (2 endpoints)
- [Sites MxEdges](#sites-mxedges) (4 endpoints)
- [Sites NAC Fingerprints](#sites-nac-fingerprints) (2 endpoints)
- [Sites Network Templates](#sites-network-templates) (1 endpoints)
- [Sites Networks](#sites-networks) (1 endpoints)
- [Sites Psks](#sites-psks) (2 endpoints)
- [Sites RF Templates](#sites-rf-templates) (1 endpoints)
- [Sites RRM](#sites-rrm) (5 endpoints)
- [Sites RSSI Zones](#sites-rssi-zones) (2 endpoints)
- [Sites Rfdiags](#sites-rfdiags) (3 endpoints)
- [Sites Rogues](#sites-rogues) (5 endpoints)
- [Sites SLEs](#sites-sles) (17 endpoints)
- [Sites SecIntel Profiles](#sites-secintel-profiles) (1 endpoints)
- [Sites Service Policies](#sites-service-policies) (1 endpoints)
- [Sites Services](#sites-services) (3 endpoints)
- [Sites Setting](#sites-setting) (2 endpoints)
- [Sites Site Templates](#sites-site-templates) (1 endpoints)
- [Sites Skyatp](#sites-skyatp) (2 endpoints)
- [Sites Spectrum Analysis](#sites-spectrum-analysis) (2 endpoints)
- [Sites Stats](#sites-stats) (1 endpoints)
- [Sites Stats - Apps](#sites-stats---apps) (1 endpoints)
- [Sites Stats - Assets](#sites-stats---assets) (7 endpoints)
- [Sites Stats - BGP Peers](#sites-stats---bgp-peers) (2 endpoints)
- [Sites Stats - Beacons](#sites-stats---beacons) (1 endpoints)
- [Sites Stats - Calls](#sites-stats---calls) (5 endpoints)
- [Sites Stats - Clients SDK](#sites-stats---clients-sdk) (2 endpoints)
- [Sites Stats - Clients Wireless](#sites-stats---clients-wireless) (4 endpoints)
- [Sites Stats - Devices](#sites-stats---devices) (5 endpoints)
- [Sites Stats - Discovered Switches](#sites-stats---discovered-switches) (4 endpoints)
- [Sites Stats - IoT Endpoints](#sites-stats---iot-endpoints) (2 endpoints)
- [Sites Stats - MxEdges](#sites-stats---mxedges) (2 endpoints)
- [Sites Stats - Ospf](#sites-stats---ospf) (2 endpoints)
- [Sites Stats - Ports](#sites-stats---ports) (2 endpoints)
- [Sites Stats - WxRules](#sites-stats---wxrules) (1 endpoints)
- [Sites Stats - Zones](#sites-stats---zones) (4 endpoints)
- [Sites Synthetic Tests](#sites-synthetic-tests) (2 endpoints)
- [Sites UI Settings](#sites-ui-settings) (3 endpoints)
- [Sites VPNs](#sites-vpns) (1 endpoints)
- [Sites WAN Usages](#sites-wan-usages) (2 endpoints)
- [Sites Webhooks](#sites-webhooks) (4 endpoints)
- [Sites Wlans](#sites-wlans) (3 endpoints)
- [Sites WxRules](#sites-wxrules) (3 endpoints)
- [Sites WxTags](#sites-wxtags) (3 endpoints)
- [Sites WxTunnels](#sites-wxtunnels) (2 endpoints)
- [Sites Zones](#sites-zones) (4 endpoints)
- [Sites vBeacons](#sites-vbeacons) (2 endpoints)
- [Utilities Common](#utilities-common) (1 endpoints)
- [Utilities LAN](#utilities-lan) (1 endpoints)
- [Utilities PCAPs](#utilities-pcaps) (4 endpoints)
- [Utilities Upgrade](#utilities-upgrade) (14 endpoints)

## Admins

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getAdminRegistrationInfo` | `/api/v1/register/recaptcha` | getAdminRegistrationInfo | `mistapi.api.v1.register.recaptcha` |

## Admins Login - OAuth2

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOauth2AuthorizationUrlForLogin` | `/api/v1/login/oauth/{provider}` | getOauth2AuthorizationUrlForLogin | `mistapi.api.v1.login.oauth` |

## Constants Definitions

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listApChannels` | `/api/v1/const/ap_channels` | listApChannels | `mistapi.api.v1.const.ap_channels` |
| `listApLEslVersions` | `/api/v1/const/ap_esl_versions` | listApLEslVersions | `mistapi.api.v1.const.ap_esl_versions` |
| `listApLedDefinition` | `/api/v1/const/ap_led_status` | listApLedDefinition | `mistapi.api.v1.const.ap_led_status` |
| `listAppCategoryDefinitions` | `/api/v1/const/app_categories` | listAppCategoryDefinitions | `mistapi.api.v1.const.app_categories` |
| `listAppSubCategoryDefinitions` | `/api/v1/const/app_subcategories` | listAppSubCategoryDefinitions | `mistapi.api.v1.const.app_subcategories` |
| `listApplications` | `/api/v1/const/applications` | listApplications | `mistapi.api.v1.const.applications` |
| `listCountryCodes` | `/api/v1/const/countries` | listCountryCodes | `mistapi.api.v1.const.countries` |
| `listFingerprintTypes` | `/api/v1/const/fingerprint_types` | listFingerprintTypes | `mistapi.api.v1.const.fingerprint_types` |
| `listGatewayApplications` | `/api/v1/const/gateway_applications` | listGatewayApplications | `mistapi.api.v1.const.gateway_applications` |
| `listInsightMetrics` | `/api/v1/const/insight_metrics` | listInsightMetrics | `mistapi.api.v1.const.insight_metrics` |
| `listLicenseTypes` | `/api/v1/const/license_types` | listLicenseTypes | `mistapi.api.v1.const.license_types` |
| `listMarvisClientEventsDefinitions` | `/api/v1/const/marvisclient_events` | listMarvisClientEventsDefinitions | `mistapi.api.v1.const.marvisclient_events` |
| `listMarvisClientVersions` | `/api/v1/const/marvisclient_versions` | listMarvisClientVersions | `mistapi.api.v1.const.marvisclient_versions` |
| `listSiteLanguages` | `/api/v1/const/languages` | listSiteLanguages | `mistapi.api.v1.const.languages` |
| `listStates` | `/api/v1/const/states` | listStates | `mistapi.api.v1.const.states` |
| `listTrafficTypes` | `/api/v1/const/traffic_types` | listTrafficTypes | `mistapi.api.v1.const.traffic_types` |
| `listWebhookTopics` | `/api/v1/const/webhook_topics` | listWebhookTopics | `mistapi.api.v1.const.webhook_topics` |

## Constants Events

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listAlarmDefinitions` | `/api/v1/const/alarm_defs` | listAlarmDefinitions | `mistapi.api.v1.const.alarm_defs` |
| `listClientEventsDefinitions` | `/api/v1/const/client_events` | listClientEventsDefinitions | `mistapi.api.v1.const.client_events` |
| `listDeviceEventsDefinitions` | `/api/v1/const/device_events` | listDeviceEventsDefinitions | `mistapi.api.v1.const.device_events` |
| `listMxEdgeEventsDefinitions` | `/api/v1/const/mxedge_events` | listMxEdgeEventsDefinitions | `mistapi.api.v1.const.mxedge_events` |
| `listNacEventsDefinitions` | `/api/v1/const/nac_events` | listNacEventsDefinitions | `mistapi.api.v1.const.nac_events` |
| `listOtherDeviceEventsDefinitions` | `/api/v1/const/otherdevice_events` | listOtherDeviceEventsDefinitions | `mistapi.api.v1.const.otherdevice_events` |
| `listSystemEventsDefinitions` | `/api/v1/const/system_events` | listSystemEventsDefinitions | `mistapi.api.v1.const.system_events` |

## Constants Models

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getGatewayDefaultConfig` | `/api/v1/const/default_gateway_config` | getGatewayDefaultConfig | `mistapi.api.v1.const.default_gateway_config` |
| `listDeviceModels` | `/api/v1/const/device_models` | listDeviceModels | `mistapi.api.v1.const.device_models` |
| `listMxEdgeModels` | `/api/v1/const/mxedge_models` | listMxEdgeModels | `mistapi.api.v1.const.mxedge_models` |
| `listSupportedOtherDeviceModels` | `/api/v1/const/otherdevice_models` | listSupportedOtherDeviceModels | `mistapi.api.v1.const.otherdevice_models` |

## Installer

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getInstallerDeviceVirtualChassis` | `/api/v1/installer/orgs/{org_id}/devices/{fpc0_mac}/vc` | getInstallerDeviceVirtualChassis | `mistapi.api.v1.installer.orgs.devices` |
| `listInstallerAlarmTemplates` | `/api/v1/installer/orgs/{org_id}/alarmtemplates` | listInstallerAlarmTemplates | `mistapi.api.v1.installer.orgs.alarmtemplates` |
| `listInstallerDeviceProfiles` | `/api/v1/installer/orgs/{org_id}/deviceprofiles` | listInstallerDeviceProfiles | `mistapi.api.v1.installer.orgs.deviceprofiles` |
| `listInstallerListOfRecentlyClaimedDevices` | `/api/v1/installer/orgs/{org_id}/devices` | listInstallerListOfRecentlyClaimedDevices | `mistapi.api.v1.installer.orgs.devices` |
| `listInstallerMaps` | `/api/v1/installer/orgs/{org_id}/sites/{site_name}/maps` | listInstallerMaps | `mistapi.api.v1.installer.orgs.sites` |
| `listInstallerRfTemplatesNames` | `/api/v1/installer/orgs/{org_id}/rftemplates` | listInstallerRfTemplatesNames | `mistapi.api.v1.installer.orgs.rftemplates` |
| `listInstallerSiteGroups` | `/api/v1/installer/orgs/{org_id}/sitegroups` | listInstallerSiteGroups | `mistapi.api.v1.installer.orgs.sitegroups` |
| `listInstallerSites` | `/api/v1/installer/orgs/{org_id}/sites` | listInstallerSites | `mistapi.api.v1.installer.orgs.sites` |
| `optimizeInstallerRrm` | `/api/v1/installer/sites/{site_name}/optimize` | optimizeInstallerRrm | `mistapi.api.v1.installer.sites.optimize` |

## MSPs

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getMspDetails` | `/api/v1/msps/{msp_id}` | getMspDetails | `mistapi.api.v1.msps.msps` |
| `searchMspOrgGroup` | `/api/v1/msps/{msp_id}/search` | searchMspOrgGroup | `mistapi.api.v1.msps.search` |

## MSPs Admins

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getMspAdmin` | `/api/v1/msps/{msp_id}/admins/{admin_id}` | getMspAdmin | `mistapi.api.v1.msps.admins` |
| `listMspAdmins` | `/api/v1/msps/{msp_id}/admins` | listMspAdmins | `mistapi.api.v1.msps.admins` |

## MSPs Inventory

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getMspInventoryByMac` | `/api/v1/msps/{msp_id}/inventory/{device_mac}` | getMspInventoryByMac | `mistapi.api.v1.msps.inventory` |

## MSPs Licenses

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listMspLicenses` | `/api/v1/msps/{msp_id}/licenses` | listMspLicenses | `mistapi.api.v1.msps.licenses` |
| `listMspOrgLicenses` | `/api/v1/msps/{msp_id}/stats/licenses` | listMspOrgLicenses | `mistapi.api.v1.msps.stats` |

## MSPs Logs

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countMspAuditLogs` | `/api/v1/msps/{msp_id}/logs/count` | countMspAuditLogs | `mistapi.api.v1.msps.logs` |
| `listMspAuditLogs` | `/api/v1/msps/{msp_id}/logs` | listMspAuditLogs | `mistapi.api.v1.msps.logs` |

## MSPs Marvis

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countMspsMarvisActions` | `/api/v1/msps/{msp_id}/suggestion/count` | countMspsMarvisActions | `mistapi.api.v1.msps.suggestion` |

## MSPs Org Groups

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getMspOrgGroup` | `/api/v1/msps/{msp_id}/orggroups/{orggroup_id}` | getMspOrgGroup | `mistapi.api.v1.msps.orggroups` |
| `listMspOrgGroups` | `/api/v1/msps/{msp_id}/orggroups` | listMspOrgGroups | `mistapi.api.v1.msps.orggroups` |

## MSPs Orgs

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getMspOrg` | `/api/v1/msps/{msp_id}/orgs/{org_id}` | getMspOrg | `mistapi.api.v1.msps.orgs` |
| `listMspOrgStats` | `/api/v1/msps/{msp_id}/stats/orgs` | listMspOrgStats | `mistapi.api.v1.msps.stats` |
| `listMspOrgs` | `/api/v1/msps/{msp_id}/orgs` | listMspOrgs | `mistapi.api.v1.msps.orgs` |
| `searchMspOrgs` | `/api/v1/msps/{msp_id}/orgs/search` | searchMspOrgs | `mistapi.api.v1.msps.orgs` |

## MSPs SLEs

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getMspSle` | `/api/v1/msps/{msp_id}/insights/{metric}` | getMspSle | `mistapi.api.v1.msps.insights` |

## MSPs SSO

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `downloadMspSamlMetadata` | `/api/v1/msps/{msp_id}/ssos/{sso_id}/metadata.xml` | downloadMspSamlMetadata | `mistapi.api.v1.msps.ssos` |
| `getMspSamlMetadata` | `/api/v1/msps/{msp_id}/ssos/{sso_id}/metadata` | getMspSamlMetadata | `mistapi.api.v1.msps.ssos` |
| `getMspSso` | `/api/v1/msps/{msp_id}/ssos/{sso_id}` | getMspSso | `mistapi.api.v1.msps.ssos` |
| `listMspSsoLatestFailures` | `/api/v1/msps/{msp_id}/ssos/{sso_id}/failures` | listMspSsoLatestFailures | `mistapi.api.v1.msps.ssos` |
| `listMspSsos` | `/api/v1/msps/{msp_id}/ssos` | listMspSsos | `mistapi.api.v1.msps.ssos` |

## MSPs SSO Roles

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listMspSsoRoles` | `/api/v1/msps/{msp_id}/ssoroles` | listMspSsoRoles | `mistapi.api.v1.msps.ssoroles` |

## MSPs Tickets

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countMspTickets` | `/api/v1/msps/{msp_id}/tickets/count` | countMspTickets | `mistapi.api.v1.msps.tickets` |
| `listMspTickets` | `/api/v1/msps/{msp_id}/tickets` | listMspTickets | `mistapi.api.v1.msps.tickets` |

## Orgs

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrg` | `/api/v1/orgs/{org_id}` | getOrg | `mistapi.api.v1.orgs.orgs` |

## Orgs AP Templates

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgAptemplate` | `/api/v1/orgs/{org_id}/aptemplates/{aptemplate_id}` | getOrgAptemplate | `mistapi.api.v1.orgs.aptemplates` |
| `listOrgAptemplates` | `/api/v1/orgs/{org_id}/aptemplates` | listOrgAptemplates | `mistapi.api.v1.orgs.aptemplates` |

## Orgs API Tokens

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgApiToken` | `/api/v1/orgs/{org_id}/apitokens/{apitoken_id}` | getOrgApiToken | `mistapi.api.v1.orgs.apitokens` |
| `listOrgApiTokens` | `/api/v1/orgs/{org_id}/apitokens` | listOrgApiTokens | `mistapi.api.v1.orgs.apitokens` |

## Orgs Admins

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listOrgAdmins` | `/api/v1/orgs/{org_id}/admins` | listOrgAdmins | `mistapi.api.v1.orgs.admins` |

## Orgs Advanced Anti Malware Profiles

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgAAMWProfile` | `/api/v1/orgs/{org_id}/aamwprofiles/{aamwprofile_id}` | getOrgAAMWProfile | `mistapi.api.v1.orgs.aamwprofiles` |
| `listOrgAAMWProfiles` | `/api/v1/orgs/{org_id}/aamwprofiles` | listOrgAAMWProfiles | `mistapi.api.v1.orgs.aamwprofiles` |

## Orgs Alarm Templates

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgAlarmTemplate` | `/api/v1/orgs/{org_id}/alarmtemplates/{alarmtemplate_id}` | getOrgAlarmTemplate | `mistapi.api.v1.orgs.alarmtemplates` |
| `listOrgAlarmTemplates` | `/api/v1/orgs/{org_id}/alarmtemplates` | listOrgAlarmTemplates | `mistapi.api.v1.orgs.alarmtemplates` |
| `listOrgSuppressedAlarms` | `/api/v1/orgs/{org_id}/alarmtemplates/suppress` | listOrgSuppressedAlarms | `mistapi.api.v1.orgs.alarmtemplates` |

## Orgs Alarms

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgAlarms` | `/api/v1/orgs/{org_id}/alarms/count` | countOrgAlarms | `mistapi.api.v1.orgs.alarms` |
| `searchOrgAlarms` | `/api/v1/orgs/{org_id}/alarms/search` | searchOrgAlarms | `mistapi.api.v1.orgs.alarms` |

## Orgs Antivirus Profiles

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgAntivirusProfile` | `/api/v1/orgs/{org_id}/avprofiles/{avprofile_id}` | getOrgAntivirusProfile | `mistapi.api.v1.orgs.avprofiles` |
| `listOrgAntivirusProfiles` | `/api/v1/orgs/{org_id}/avprofiles` | listOrgAntivirusProfiles | `mistapi.api.v1.orgs.avprofiles` |

## Orgs Asset Filters

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgAssetFilter` | `/api/v1/orgs/{org_id}/assetfilters/{assetfilter_id}` | getOrgAssetFilter | `mistapi.api.v1.orgs.assetfilters` |
| `listOrgAssetFilters` | `/api/v1/orgs/{org_id}/assetfilters` | listOrgAssetFilters | `mistapi.api.v1.orgs.assetfilters` |

## Orgs Assets

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgAsset` | `/api/v1/orgs/{org_id}/assets/{asset_id}` | getOrgAsset | `mistapi.api.v1.orgs.assets` |
| `listOrgAssets` | `/api/v1/orgs/{org_id}/assets` | listOrgAssets | `mistapi.api.v1.orgs.assets` |

## Orgs CRL

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgCrlFile` | `/api/v1/orgs/{org_id}/crl` | getOrgCrlFile | `mistapi.api.v1.orgs.crl` |

## Orgs Cert

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgSslProxyCert` | `/api/v1/orgs/{org_id}/ssl_proxy_cert` | getOrgSslProxyCert | `mistapi.api.v1.orgs.ssl_proxy_cert` |
| `listOrgCertificates` | `/api/v1/orgs/{org_id}/cert` | listOrgCertificates | `mistapi.api.v1.orgs.cert` |

## Orgs Clients - Marvis

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgMarvisClientEvents` | `/api/v1/orgs/{org_id}/marvisclients/events/count` | countOrgMarvisClientEvents | `mistapi.api.v1.orgs.marvisclients` |
| `getOrgMarvisClientInsights` | `/api/v1/orgs/{org_id}/insights/marvisclient/{marvisclient_id}/marvisclient-metrics` | getOrgMarvisClientInsights | `mistapi.api.v1.orgs.insights` |
| `searchOrgMarvisClientEvents` | `/api/v1/orgs/{org_id}/marvisclients/events/search` | searchOrgMarvisClientEvents | `mistapi.api.v1.orgs.marvisclients` |

## Orgs Clients - NAC

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgNacClientEvents` | `/api/v1/orgs/{org_id}/nac_clients/events/count` | countOrgNacClientEvents | `mistapi.api.v1.orgs.nac_clients` |
| `countOrgNacClients` | `/api/v1/orgs/{org_id}/nac_clients/count` | countOrgNacClients | `mistapi.api.v1.orgs.nac_clients` |
| `searchOrgNacClientEvents` | `/api/v1/orgs/{org_id}/nac_clients/events/search` | searchOrgNacClientEvents | `mistapi.api.v1.orgs.nac_clients` |
| `searchOrgNacClients` | `/api/v1/orgs/{org_id}/nac_clients/search` | searchOrgNacClients | `mistapi.api.v1.orgs.nac_clients` |

## Orgs Clients - Wan

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgWanClientEvents` | `/api/v1/orgs/{org_id}/wan_client/events/count` | countOrgWanClientEvents | `mistapi.api.v1.orgs.wan_client` |
| `countOrgWanClients` | `/api/v1/orgs/{org_id}/wan_clients/count` | countOrgWanClients | `mistapi.api.v1.orgs.wan_clients` |
| `searchOrgWanClientEvents` | `/api/v1/orgs/{org_id}/wan_clients/events/search` | searchOrgWanClientEvents | `mistapi.api.v1.orgs.wan_clients` |
| `searchOrgWanClients` | `/api/v1/orgs/{org_id}/wan_clients/search` | searchOrgWanClients | `mistapi.api.v1.orgs.wan_clients` |

## Orgs Clients - Wired

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgWiredClients` | `/api/v1/orgs/{org_id}/wired_clients/count` | countOrgWiredClients | `mistapi.api.v1.orgs.wired_clients` |
| `searchOrgWiredClients` | `/api/v1/orgs/{org_id}/wired_clients/search` | searchOrgWiredClients | `mistapi.api.v1.orgs.wired_clients` |

## Orgs Clients - Wireless

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgWirelessClientEvents` | `/api/v1/orgs/{org_id}/clients/events/count` | countOrgWirelessClientEvents | `mistapi.api.v1.orgs.clients` |
| `countOrgWirelessClients` | `/api/v1/orgs/{org_id}/clients/count` | countOrgWirelessClients | `mistapi.api.v1.orgs.clients` |
| `countOrgWirelessClientsSessions` | `/api/v1/orgs/{org_id}/clients/sessions/count` | countOrgWirelessClientsSessions | `mistapi.api.v1.orgs.clients` |
| `searchOrgWirelessClientEvents` | `/api/v1/orgs/{org_id}/clients/events/search` | searchOrgWirelessClientEvents | `mistapi.api.v1.orgs.clients` |
| `searchOrgWirelessClientSessions` | `/api/v1/orgs/{org_id}/clients/sessions/search` | searchOrgWirelessClientSessions | `mistapi.api.v1.orgs.clients` |
| `searchOrgWirelessClients` | `/api/v1/orgs/{org_id}/clients/search` | searchOrgWirelessClients | `mistapi.api.v1.orgs.clients` |

## Orgs Device Profiles

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgDeviceProfile` | `/api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}` | getOrgDeviceProfile | `mistapi.api.v1.orgs.deviceprofiles` |
| `listOrgDeviceProfiles` | `/api/v1/orgs/{org_id}/deviceprofiles` | listOrgDeviceProfiles | `mistapi.api.v1.orgs.deviceprofiles` |

## Orgs Devices

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgDeviceEvents` | `/api/v1/orgs/{org_id}/devices/events/count` | countOrgDeviceEvents | `mistapi.api.v1.orgs.devices` |
| `countOrgDeviceLastConfigs` | `/api/v1/orgs/{org_id}/devices/last_config/count` | countOrgDeviceLastConfigs | `mistapi.api.v1.orgs.devices` |
| `countOrgDevices` | `/api/v1/orgs/{org_id}/devices/count` | countOrgDevices | `mistapi.api.v1.orgs.devices` |
| `getOrgJuniperDevicesCommand` | `/api/v1/orgs/{org_id}/ocdevices/outbound_ssh_cmd` | getOrgJuniperDevicesCommand | `mistapi.api.v1.orgs.ocdevices` |
| `listOrgApsMacs` | `/api/v1/orgs/{org_id}/devices/radio_macs` | listOrgApsMacs | `mistapi.api.v1.orgs.devices` |
| `listOrgDevices` | `/api/v1/orgs/{org_id}/devices` | listOrgDevices | `mistapi.api.v1.orgs.devices` |
| `listOrgDevicesSummary` | `/api/v1/orgs/{org_id}/devices/summary` | listOrgDevicesSummary | `mistapi.api.v1.orgs.devices` |
| `searchOrgDeviceEvents` | `/api/v1/orgs/{org_id}/devices/events/search` | searchOrgDeviceEvents | `mistapi.api.v1.orgs.devices` |
| `searchOrgDeviceLastConfigs` | `/api/v1/orgs/{org_id}/devices/last_config/search` | searchOrgDeviceLastConfigs | `mistapi.api.v1.orgs.devices` |
| `searchOrgDevices` | `/api/v1/orgs/{org_id}/devices/search` | searchOrgDevices | `mistapi.api.v1.orgs.devices` |

## Orgs Devices - AOSCX

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgAoscxRegisterCmd` | `/api/v1/orgs/{org_id}/aoscx/register_cmd` | getOrgAoscxRegisterCmd | `mistapi.api.v1.orgs.aoscx` |

## Orgs Devices - EdgeConnect

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgEdgeconnectRegisterCmd` | `/api/v1/orgs/{org_id}/edgeconnect/register_cmd` | getOrgEdgeconnectRegisterCmd | `mistapi.api.v1.orgs.edgeconnect` |

## Orgs Devices - Others

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgOtherDeviceEvents` | `/api/v1/orgs/{org_id}/otherdevices/events/count` | countOrgOtherDeviceEvents | `mistapi.api.v1.orgs.otherdevices` |
| `getOrgOtherDevice` | `/api/v1/orgs/{org_id}/otherdevices/{device_mac}` | getOrgOtherDevice | `mistapi.api.v1.orgs.otherdevices` |
| `listOrgOtherDevices` | `/api/v1/orgs/{org_id}/otherdevices` | listOrgOtherDevices | `mistapi.api.v1.orgs.otherdevices` |
| `searchOrgOtherDeviceEvents` | `/api/v1/orgs/{org_id}/otherdevices/events/search` | searchOrgOtherDeviceEvents | `mistapi.api.v1.orgs.otherdevices` |

## Orgs Devices - SSR

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrg128TRegistrationCommands` | `/api/v1/orgs/{org_id}/128routers/register_cmd` | getOrg128TRegistrationCommands | `` |
| `getOrgSsrRegistrationCommands` | `/api/v1/orgs/{org_id}/ssr/register_cmd` | getOrgSsrRegistrationCommands | `mistapi.api.v1.orgs.ssr` |

## Orgs EVPN Topologies

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgEvpnTopology` | `/api/v1/orgs/{org_id}/evpn_topologies/{evpn_topology_id}` | getOrgEvpnTopology | `mistapi.api.v1.orgs.evpn_topologies` |
| `listOrgEvpnTopologies` | `/api/v1/orgs/{org_id}/evpn_topologies` | listOrgEvpnTopologies | `mistapi.api.v1.orgs.evpn_topologies` |

## Orgs Events

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgSystemEvents` | `/api/v1/orgs/{org_id}/events/system/count` | countOrgSystemEvents | `mistapi.api.v1.orgs.events` |
| `searchOrgEvents` | `/api/v1/orgs/{org_id}/events/search` | searchOrgEvents | `mistapi.api.v1.orgs.events` |
| `searchOrgSystemEvents` | `/api/v1/orgs/{org_id}/events/system/search` | searchOrgSystemEvents | `mistapi.api.v1.orgs.events` |

## Orgs Gateway Templates

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgGatewayTemplate` | `/api/v1/orgs/{org_id}/gatewaytemplates/{gatewaytemplate_id}` | getOrgGatewayTemplate | `mistapi.api.v1.orgs.gatewaytemplates` |
| `listOrgGatewayTemplates` | `/api/v1/orgs/{org_id}/gatewaytemplates` | listOrgGatewayTemplates | `mistapi.api.v1.orgs.gatewaytemplates` |

## Orgs Guests

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgGuestAuthorizations` | `/api/v1/orgs/{org_id}/guests/count` | countOrgGuestAuthorizations | `mistapi.api.v1.orgs.guests` |
| `getOrgGuestAuthorization` | `/api/v1/orgs/{org_id}/guests/{guest_mac}` | getOrgGuestAuthorization | `mistapi.api.v1.orgs.guests` |
| `listOrgGuestAuthorizations` | `/api/v1/orgs/{org_id}/guests` | listOrgGuestAuthorizations | `mistapi.api.v1.orgs.guests` |
| `searchOrgGuestAuthorization` | `/api/v1/orgs/{org_id}/guests/search` | searchOrgGuestAuthorization | `mistapi.api.v1.orgs.guests` |

## Orgs IDP Profiles

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgIdpProfile` | `/api/v1/orgs/{org_id}/idpprofiles/{idpprofile_id}` | getOrgIdpProfile | `mistapi.api.v1.orgs.idpprofiles` |
| `listOrgIdpProfiles` | `/api/v1/orgs/{org_id}/idpprofiles` | listOrgIdpProfiles | `mistapi.api.v1.orgs.idpprofiles` |

## Orgs Integration Cradlepoint

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `testOrgCradlepointConnection` | `/api/v1/orgs/{org_id}/setting/cradlepoint/setup` | testOrgCradlepointConnection | `mistapi.api.v1.orgs.setting` |

## Orgs Integration JSE

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgJseInfo` | `/api/v1/orgs/{org_id}/setting/jse/info` | getOrgJseInfo | `mistapi.api.v1.orgs.setting` |
| `getOrgJseIntegration` | `/api/v1/orgs/{org_id}/setting/jse/setup` | getOrgJseIntegration | `mistapi.api.v1.orgs.setting` |

## Orgs Integration SkyATP

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgSkyAtpIntegration` | `/api/v1/orgs/{org_id}/setting/skyatp/setup` | getOrgSkyAtpIntegration | `mistapi.api.v1.orgs.setting` |

## Orgs Integration Zscaler

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgZscalerIntegration` | `/api/v1/orgs/{org_id}/setting/zscaler/setup` | getOrgZscalerIntegration | `mistapi.api.v1.orgs.setting` |

## Orgs Inventory

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgInventory` | `/api/v1/orgs/{org_id}/inventory/count` | countOrgInventory | `mistapi.api.v1.orgs.inventory` |
| `getOrgInventory` | `/api/v1/orgs/{org_id}/inventory` | getOrgInventory | `mistapi.api.v1.orgs.inventory` |
| `searchOrgInventory` | `/api/v1/orgs/{org_id}/inventory/search` | searchOrgInventory | `mistapi.api.v1.orgs.inventory` |

## Orgs JSI

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `adoptOrgJsiDevice` | `/api/v1/orgs/{org_id}/jsi/devices/outbound_ssh_cmd` | adoptOrgJsiDevice | `mistapi.api.v1.orgs.jsi` |
| `countOrgJsiAssetsAndContracts` | `/api/v1/orgs/{org_id}/jsi/inventory/count` | countOrgJsiAssetsAndContracts | `mistapi.api.v1.orgs.jsi` |
| `countOrgJsiPbn` | `/api/v1/orgs/{org_id}/jsi/pbn/count` | countOrgJsiPbn | `mistapi.api.v1.orgs.jsi` |
| `countOrgJsiSirt` | `/api/v1/orgs/{org_id}/jsi/sirt/count` | countOrgJsiSirt | `mistapi.api.v1.orgs.jsi` |
| `listOrgJsiDevices` | `/api/v1/orgs/{org_id}/jsi/devices` | listOrgJsiDevices | `mistapi.api.v1.orgs.jsi` |
| `listOrgJsiPastPurchases` | `/api/v1/orgs/{org_id}/jsi/inventory` | listOrgJsiPastPurchases | `mistapi.api.v1.orgs.jsi` |
| `searchOrgJsiAssetsAndContracts` | `/api/v1/orgs/{org_id}/jsi/inventory/search` | searchOrgJsiAssetsAndContracts | `mistapi.api.v1.orgs.jsi` |
| `searchOrgJsiPbn` | `/api/v1/orgs/{org_id}/jsi/pbn/search` | searchOrgJsiPbn | `mistapi.api.v1.orgs.jsi` |
| `searchOrgJsiSirt` | `/api/v1/orgs/{org_id}/jsi/sirt/search` | searchOrgJsiSirt | `mistapi.api.v1.orgs.jsi` |

## Orgs Licenses

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `GetOrgLicenseAsyncClaimStatus` | `/api/v1/orgs/{org_id}/claim/status` | GetOrgLicenseAsyncClaimStatus | `mistapi.api.v1.orgs.claim` |
| `getOrgAsyncClaimStatus` | `/api/v1/orgs/{org_id}/claims/{claim_id}` | getOrgAsyncClaimStatus | `mistapi.api.v1.orgs.claims` |
| `getOrgLicensesBySite` | `/api/v1/orgs/{org_id}/licenses/usages` | getOrgLicensesBySite | `mistapi.api.v1.orgs.licenses` |
| `getOrgLicensesSummary` | `/api/v1/orgs/{org_id}/licenses` | getOrgLicensesSummary | `mistapi.api.v1.orgs.licenses` |
| `listOrgAsyncClaims` | `/api/v1/orgs/{org_id}/claims` | listOrgAsyncClaims | `mistapi.api.v1.orgs.claims` |

## Orgs Linked Applications

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgOauthAppLinkedStatus` | `/api/v1/orgs/{org_id}/setting/{app_name}/link_accounts` | getOrgOauthAppAuthorizationUrl | `mistapi.api.v1.orgs.setting` |

## Orgs Logs

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgAuditLogs` | `/api/v1/orgs/{org_id}/logs/count` | countOrgAuditLogs | `mistapi.api.v1.orgs.logs` |
| `listOrgAuditLogs` | `/api/v1/orgs/{org_id}/logs/search` | listOrgAuditLogs | `mistapi.api.v1.orgs.logs` |
| `listOrgAuditLogsLegacy` | `/api/v1/orgs/{org_id}/logs` | listOrgAuditLogsLegacy | `` |

## Orgs Marvis

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `troubleshootOrg` | `/api/v1/orgs/{org_id}/troubleshoot` | troubleshootOrg | `mistapi.api.v1.orgs.troubleshoot` |

## Orgs Marvis Invites

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgMarvisClientInvite` | `/api/v1/orgs/{org_id}/marvisinvites/{marvisinvite_id}` | getOrgMarvisClientInvite | `mistapi.api.v1.orgs.marvisinvites` |
| `listOrgMarvisClientInvites` | `/api/v1/orgs/{org_id}/marvisinvites` | listOrgMarvisClientInvites | `mistapi.api.v1.orgs.marvisinvites` |

## Orgs MxClusters

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgMxEdgeCluster` | `/api/v1/orgs/{org_id}/mxclusters/{mxcluster_id}` | getOrgMxEdgeCluster | `mistapi.api.v1.orgs.mxclusters` |
| `listOrgMxEdgeClusters` | `/api/v1/orgs/{org_id}/mxclusters` | listOrgMxEdgeClusters | `mistapi.api.v1.orgs.mxclusters` |

## Orgs MxEdges

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgMxEdges` | `/api/v1/orgs/{org_id}/mxedges/count` | countOrgMxEdges | `mistapi.api.v1.orgs.mxedges` |
| `countOrgSiteMxEdgeEvents` | `/api/v1/orgs/{org_id}/mxedges/events/count` | countOrgSiteMxEdgeEvents | `mistapi.api.v1.orgs.mxedges` |
| `getOrgMxEdge` | `/api/v1/orgs/{org_id}/mxedges/{mxedge_id}` | getOrgMxEdge | `mistapi.api.v1.orgs.mxedges` |
| `getOrgMxEdgeUpgradeInfo` | `/api/v1/orgs/{org_id}/mxedges/versions` | getOrgMxEdgeUpgradeInfo | `mistapi.api.v1.orgs.mxedges` |
| `getOrgMxEdgeVmParams` | `/api/v1/orgs/{org_id}/mxedges/{mxedge_id}/vm_params` | getOrgMxEdgeVmParams | `mistapi.api.v1.orgs.mxedges` |
| `listOrgMxEdges` | `/api/v1/orgs/{org_id}/mxedges` | listOrgMxEdges | `mistapi.api.v1.orgs.mxedges` |
| `searchOrgMistEdgeEvents` | `/api/v1/orgs/{org_id}/mxedges/events/search` | searchOrgMistEdgeEvents | `mistapi.api.v1.orgs.mxedges` |
| `searchOrgMxEdges` | `/api/v1/orgs/{org_id}/mxedges/search` | searchOrgMxEdges | `mistapi.api.v1.orgs.mxedges` |

## Orgs MxTunnels

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgMxTunnel` | `/api/v1/orgs/{org_id}/mxtunnels/{mxtunnel_id}` | getOrgMxTunnel | `mistapi.api.v1.orgs.mxtunnels` |
| `listOrgMxTunnels` | `/api/v1/orgs/{org_id}/mxtunnels` | listOrgMxTunnels | `mistapi.api.v1.orgs.mxtunnels` |

## Orgs NAC CRL

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgNacCrl` | `/api/v1/orgs/{org_id}/setting/mist_nac_crls` | getOrgNacCrl | `mistapi.api.v1.orgs.setting` |

## Orgs NAC Portals

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `downloadOrgNacPortalSamlMetadata` | `/api/v1/orgs/{org_id}/nacportals/{nacportal_id}/saml_metadata.xml` | downloadOrgNacPortalSamlMetadata | `mistapi.api.v1.orgs.nacportals` |
| `getOrgNacPortal` | `/api/v1/orgs/{org_id}/nacportals/{nacportal_id}` | getOrgNacPortal | `mistapi.api.v1.orgs.nacportals` |
| `getOrgNacPortalSamlMetadata` | `/api/v1/orgs/{org_id}/nacportals/{nacportal_id}/saml_metadata` | getOrgNacPortalSamlMetadata | `mistapi.api.v1.orgs.nacportals` |
| `listOrgNacPortalSsoLatestFailures` | `/api/v1/orgs/{org_id}/nacportals/{nacportal_id}/failures` | listOrgNacPortalSsoLatestFailures | `mistapi.api.v1.orgs.nacportals` |
| `listOrgNacPortals` | `/api/v1/orgs/{org_id}/nacportals` | listOrgNacPortals | `mistapi.api.v1.orgs.nacportals` |

## Orgs NAC Rules

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgNacRule` | `/api/v1/orgs/{org_id}/nacrules/{nacrule_id}` | getOrgNacRule | `mistapi.api.v1.orgs.nacrules` |
| `listOrgNacRules` | `/api/v1/orgs/{org_id}/nacrules` | listOrgNacRules | `mistapi.api.v1.orgs.nacrules` |

## Orgs NAC Tags

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgNacTag` | `/api/v1/orgs/{org_id}/nactags/{nactag_id}` | getOrgNacTag | `mistapi.api.v1.orgs.nactags` |
| `listOrgNacTags` | `/api/v1/orgs/{org_id}/nactags` | listOrgNacTags | `mistapi.api.v1.orgs.nactags` |

## Orgs Network Templates

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgNetworkTemplate` | `/api/v1/orgs/{org_id}/networktemplates/{networktemplate_id}` | getOrgNetworkTemplate | `mistapi.api.v1.orgs.networktemplates` |
| `listOrgNetworkTemplates` | `/api/v1/orgs/{org_id}/networktemplates` | listOrgNetworkTemplates | `mistapi.api.v1.orgs.networktemplates` |

## Orgs Networks

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgNetwork` | `/api/v1/orgs/{org_id}/networks/{network_id}` | getOrgNetwork | `mistapi.api.v1.orgs.networks` |
| `listOrgNetworks` | `/api/v1/orgs/{org_id}/networks` | listOrgNetworks | `mistapi.api.v1.orgs.networks` |

## Orgs Premium Analytics

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listOrgPmaDashboards` | `/api/v1/orgs/{org_id}/pma/dashboards` | listOrgPmaDashboards | `mistapi.api.v1.orgs.pma` |

## Orgs Psk Portals

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgPskPortalLogs` | `/api/v1/orgs/{org_id}/pskportals/logs/count` | countOrgPskPortalLogs | `mistapi.api.v1.orgs.pskportals` |
| `getOrgPskPortal` | `/api/v1/orgs/{org_id}/pskportals/{pskportal_id}` | getOrgPskPortal | `mistapi.api.v1.orgs.pskportals` |
| `listOrgPskPortalLogs` | `/api/v1/orgs/{org_id}/pskportals/logs` | listOrgPskPortalLogs | `mistapi.api.v1.orgs.pskportals` |
| `listOrgPskPortals` | `/api/v1/orgs/{org_id}/pskportals` | listOrgPskPortals | `mistapi.api.v1.orgs.pskportals` |
| `searchOrgPskPortalLogs` | `/api/v1/orgs/{org_id}/pskportals/logs/search` | searchOrgPskPortalLogs | `mistapi.api.v1.orgs.pskportals` |

## Orgs Psks

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgPsk` | `/api/v1/orgs/{org_id}/psks/{psk_id}` | getOrgPsk | `mistapi.api.v1.orgs.psks` |
| `listOrgPsks` | `/api/v1/orgs/{org_id}/psks` | listOrgPsks | `mistapi.api.v1.orgs.psks` |

## Orgs RF Templates

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgRfTemplate` | `/api/v1/orgs/{org_id}/rftemplates/{rftemplate_id}` | getOrgRfTemplate | `mistapi.api.v1.orgs.rftemplates` |
| `listOrgRfTemplates` | `/api/v1/orgs/{org_id}/rftemplates` | listOrgRfTemplates | `mistapi.api.v1.orgs.rftemplates` |

## Orgs Reports

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgE911Report` | `/api/v1/orgs/{org_id}/exports/e911_report` | getOrgE911Report | `mistapi.api.v1.orgs.exports` |

## Orgs SCEP

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgMistScep` | `/api/v1/orgs/{org_id}/setting/mist_scep` | getOrgMistScep | `mistapi.api.v1.orgs.setting` |
| `listOrgIssuedClientCertificates` | `/api/v1/orgs/{org_id}/setting/mist_scep/client_certs` | listOrgIssuedClientCertificates | `mistapi.api.v1.orgs.setting` |

## Orgs SDK Invites

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSdkInvite` | `/api/v1/orgs/{org_id}/sdkinvites/{sdkinvite_id}` | getSdkInvite | `mistapi.api.v1.orgs.sdkinvites` |
| `getSdkInviteQrCode` | `/api/v1/orgs/{org_id}/sdkinvites/{sdkinvite_id}/qrcode` | getSdkInviteQrCode | `mistapi.api.v1.orgs.sdkinvites` |
| `listSdkInvites` | `/api/v1/orgs/{org_id}/sdkinvites` | listSdkInvites | `mistapi.api.v1.orgs.sdkinvites` |

## Orgs SDK Templates

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSdkTemplate` | `/api/v1/orgs/{org_id}/sdktemplates/{sdktemplate_id}` | getSdkTemplate | `mistapi.api.v1.orgs.sdktemplates` |
| `listSdkTemplates` | `/api/v1/orgs/{org_id}/sdktemplates` | listSdkTemplates | `mistapi.api.v1.orgs.sdktemplates` |

## Orgs SLEs

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgSitesSle` | `/api/v1/orgs/{org_id}/insights/sites-sle` | getOrgSitesSle | `mistapi.api.v1.orgs.insights` |
| `getOrgSle` | `/api/v1/orgs/{org_id}/insights/{metric}` | getOrgSle | `mistapi.api.v1.orgs.insights` |

## Orgs SSO

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `downloadOrgSamlMetadata` | `/api/v1/orgs/{org_id}/ssos/{sso_id}/metadata.xml` | downloadOrgSamlMetadata | `mistapi.api.v1.orgs.ssos` |
| `getOrgSamlMetadata` | `/api/v1/orgs/{org_id}/ssos/{sso_id}/metadata` | getOrgSamlMetadata | `mistapi.api.v1.orgs.ssos` |
| `getOrgSso` | `/api/v1/orgs/{org_id}/ssos/{sso_id}` | getOrgSso | `mistapi.api.v1.orgs.ssos` |
| `listOrgSsoLatestFailures` | `/api/v1/orgs/{org_id}/ssos/{sso_id}/failures` | listOrgSsoLatestFailures | `mistapi.api.v1.orgs.ssos` |
| `listOrgSsos` | `/api/v1/orgs/{org_id}/ssos` | listOrgSsos | `mistapi.api.v1.orgs.ssos` |

## Orgs SSO Roles

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgSsoRole` | `/api/v1/orgs/{org_id}/ssoroles/{ssorole_id}` | getOrgSsoRole | `mistapi.api.v1.orgs.ssoroles` |
| `listOrgSsoRoles` | `/api/v1/orgs/{org_id}/ssoroles` | listOrgSsoRoles | `mistapi.api.v1.orgs.ssoroles` |

## Orgs SecIntel Profiles

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgSecIntelProfile` | `/api/v1/orgs/{org_id}/secintelprofiles/{secintelprofile_id}` | getOrgSecIntelProfile | `mistapi.api.v1.orgs.secintelprofiles` |
| `listOrgSecIntelProfiles` | `/api/v1/orgs/{org_id}/secintelprofiles` | listOrgSecIntelProfiles | `mistapi.api.v1.orgs.secintelprofiles` |

## Orgs Security Policies

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgSecPolicy` | `/api/v1/orgs/{org_id}/secpolicies/{secpolicy_id}` | getOrgSecPolicy | `mistapi.api.v1.orgs.secpolicies` |
| `listOrgSecPolicies` | `/api/v1/orgs/{org_id}/secpolicies` | listOrgSecPolicies | `mistapi.api.v1.orgs.secpolicies` |

## Orgs Service Policies

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgServicePolicy` | `/api/v1/orgs/{org_id}/servicepolicies/{servicepolicy_id}` | getOrgServicePolicy | `mistapi.api.v1.orgs.servicepolicies` |
| `listOrgServicePolicies` | `/api/v1/orgs/{org_id}/servicepolicies` | listOrgServicePolicies | `mistapi.api.v1.orgs.servicepolicies` |

## Orgs Services

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgService` | `/api/v1/orgs/{org_id}/services/{service_id}` | getOrgService | `mistapi.api.v1.orgs.services` |
| `listOrgServices` | `/api/v1/orgs/{org_id}/services` | listOrgServices | `mistapi.api.v1.orgs.services` |

## Orgs Setting

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgSettings` | `/api/v1/orgs/{org_id}/setting` | getOrgSettings | `mistapi.api.v1.orgs.setting` |

## Orgs Site Templates

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgSiteTemplate` | `/api/v1/orgs/{org_id}/sitetemplates/{sitetemplate_id}` | getOrgSiteTemplate | `mistapi.api.v1.orgs.sitetemplates` |
| `listOrgSiteTemplates` | `/api/v1/orgs/{org_id}/sitetemplates` | listOrgSiteTemplates | `mistapi.api.v1.orgs.sitetemplates` |

## Orgs Sitegroups

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgSiteGroup` | `/api/v1/orgs/{org_id}/sitegroups/{sitegroup_id}` | getOrgSiteGroup | `mistapi.api.v1.orgs.sitegroups` |
| `listOrgSiteGroups` | `/api/v1/orgs/{org_id}/sitegroups` | listOrgSiteGroups | `mistapi.api.v1.orgs.sitegroups` |

## Orgs Sites

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgSites` | `/api/v1/orgs/{org_id}/sites/count` | countOrgSites | `mistapi.api.v1.orgs.sites` |
| `listOrgSites` | `/api/v1/orgs/{org_id}/sites` | listOrgSites | `mistapi.api.v1.orgs.sites` |
| `searchOrgSites` | `/api/v1/orgs/{org_id}/sites/search` | searchOrgSites | `mistapi.api.v1.orgs.sites` |

## Orgs Stats

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgStats` | `/api/v1/orgs/{org_id}/stats` | getOrgStats | `mistapi.api.v1.orgs.stats` |

## Orgs Stats - Assets

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgAssetsByDistanceField` | `/api/v1/orgs/{org_id}/stats/assets/count` | countOrgAssetsByDistanceField | `mistapi.api.v1.orgs.stats` |
| `listOrgAssetsStats` | `/api/v1/orgs/{org_id}/stats/assets` | listOrgAssetsStats | `mistapi.api.v1.orgs.stats` |
| `searchOrgAssets` | `/api/v1/orgs/{org_id}/stats/assets/search` | searchOrgAssets | `mistapi.api.v1.orgs.stats` |

## Orgs Stats - BGP Peers

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgBgpStats` | `/api/v1/orgs/{org_id}/stats/bgp_peers/count` | countOrgBgpStats | `mistapi.api.v1.orgs.stats` |
| `searchOrgBgpStats` | `/api/v1/orgs/{org_id}/stats/bgp_peers/search` | searchOrgBgpStats | `mistapi.api.v1.orgs.stats` |

## Orgs Stats - Devices

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listOrgDevicesStats` | `/api/v1/orgs/{org_id}/stats/devices` | listOrgDevicesStats | `mistapi.api.v1.orgs.stats` |

## Orgs Stats - Marvis Clients

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgMarvisClientsStats` | `/api/v1/orgs/{org_id}/stats/marvisclients/count` | countOrgMarvisClientsStats | `mistapi.api.v1.orgs.stats` |
| `searchOrgMarvisClientsStats` | `/api/v1/orgs/{org_id}/stats/marvisclients/search` | searchOrgMarvisClientsStats | `mistapi.api.v1.orgs.stats` |

## Orgs Stats - MxEdges

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgMxEdgeStats` | `/api/v1/orgs/{org_id}/stats/mxedges/{mxedge_id}` | getOrgMxEdgeStats | `mistapi.api.v1.orgs.stats` |
| `listOrgMxEdgesStats` | `/api/v1/orgs/{org_id}/stats/mxedges` | listOrgMxEdgesStats | `mistapi.api.v1.orgs.stats` |

## Orgs Stats - Ospf

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgOspfStats` | `/api/v1/orgs/{org_id}/stats/ospf_peers/count` | countOrgOspfStats | `mistapi.api.v1.orgs.stats` |
| `searchOrgOspfStats` | `/api/v1/orgs/{org_id}/stats/ospf_peers/search` | searchOrgOspfStats | `mistapi.api.v1.orgs.stats` |

## Orgs Stats - Other Devices

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgOtherDeviceStats` | `/api/v1/orgs/{org_id}/stats/otherdevices/{device_mac}` | getOrgOtherDeviceStats | `mistapi.api.v1.orgs.stats` |

## Orgs Stats - Ports

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgSwOrGwPorts` | `/api/v1/orgs/{org_id}/stats/ports/count` | countOrgSwOrGwPorts | `mistapi.api.v1.orgs.stats` |
| `searchOrgSwOrGwPorts` | `/api/v1/orgs/{org_id}/stats/ports/search` | searchOrgSwOrGwPorts | `mistapi.api.v1.orgs.stats` |

## Orgs Stats - Sites

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listOrgSiteStats` | `/api/v1/orgs/{org_id}/stats/sites` | listOrgSiteStats | `mistapi.api.v1.orgs.stats` |

## Orgs Stats - Tunnels

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgTunnelsStats` | `/api/v1/orgs/{org_id}/stats/tunnels/count` | countOrgTunnelsStats | `mistapi.api.v1.orgs.stats` |
| `searchOrgTunnelsStats` | `/api/v1/orgs/{org_id}/stats/tunnels/search` | searchOrgTunnelsStats | `mistapi.api.v1.orgs.stats` |

## Orgs Stats - VPN Peers

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgPeerPathStats` | `/api/v1/orgs/{org_id}/stats/vpn_peers/count` | countOrgPeerPathStats | `mistapi.api.v1.orgs.stats` |
| `searchOrgPeerPathStats` | `/api/v1/orgs/{org_id}/stats/vpn_peers/search` | searchOrgPeerPathStats | `mistapi.api.v1.orgs.stats` |

## Orgs Tickets

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `GetOrgTicketAttachment` | `/api/v1/orgs/{org_id}/tickets/{ticket_id}/attachments/{attachment_id}` | GetOrgTicketAttachment | `mistapi.api.v1.orgs.tickets` |
| `countOrgTickets` | `/api/v1/orgs/{org_id}/tickets/count` | countOrgTickets | `mistapi.api.v1.orgs.tickets` |
| `getOrgTicket` | `/api/v1/orgs/{org_id}/tickets/{ticket_id}` | getOrgTicket | `mistapi.api.v1.orgs.tickets` |
| `listOrgTickets` | `/api/v1/orgs/{org_id}/tickets` | listOrgTickets | `mistapi.api.v1.orgs.tickets` |

## Orgs UI Settings

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgUiSetting` | `/api/v1/orgs/{org_id}/uisettings/{uisetting_id}` | getOrgUiSetting | `mistapi.api.v1.orgs.uisettings` |
| `listOrgUiSettings` | `/api/v1/orgs/{org_id}/uisettings` | listOrgUiSettings | `mistapi.api.v1.orgs.uisettings` |

## Orgs User MACs

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgUserMacs` | `/api/v1/orgs/{org_id}/usermacs/count` | countOrgUserMacs | `mistapi.api.v1.orgs.usermacs` |
| `getOrgUserMac` | `/api/v1/orgs/{org_id}/usermacs/{usermac_id}` | getOrgUserMac | `mistapi.api.v1.orgs.usermacs` |
| `searchOrgUserMacs` | `/api/v1/orgs/{org_id}/usermacs/search` | searchOrgUserMacs | `mistapi.api.v1.orgs.usermacs` |

## Orgs VPNs

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgVpn` | `/api/v1/orgs/{org_id}/vpns/{vpn_id}` | getOrgVpn | `mistapi.api.v1.orgs.vpns` |
| `listOrgVpns` | `/api/v1/orgs/{org_id}/vpns` | listOrgVpns | `mistapi.api.v1.orgs.vpns` |

## Orgs Vars

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `searchOrgVars` | `/api/v1/orgs/{org_id}/vars/search` | searchOrgVars | `mistapi.api.v1.orgs.vars` |

## Orgs WLAN Templates

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgTemplate` | `/api/v1/orgs/{org_id}/templates/{template_id}` | getOrgTemplate | `mistapi.api.v1.orgs.templates` |
| `listOrgTemplates` | `/api/v1/orgs/{org_id}/templates` | listOrgTemplates | `mistapi.api.v1.orgs.templates` |

## Orgs Webhooks

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countOrgWebhooksDeliveries` | `/api/v1/orgs/{org_id}/webhooks/{webhook_id}/events/count` | countOrgWebhooksDeliveries | `mistapi.api.v1.orgs.webhooks` |
| `getOrgWebhook` | `/api/v1/orgs/{org_id}/webhooks/{webhook_id}` | getOrgWebhook | `mistapi.api.v1.orgs.webhooks` |
| `listOrgWebhooks` | `/api/v1/orgs/{org_id}/webhooks` | listOrgWebhooks | `mistapi.api.v1.orgs.webhooks` |
| `searchOrgWebhooksDeliveries` | `/api/v1/orgs/{org_id}/webhooks/{webhook_id}/events/search` | searchOrgWebhooksDeliveries | `mistapi.api.v1.orgs.webhooks` |

## Orgs Wlans

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgWLAN` | `/api/v1/orgs/{org_id}/wlans/{wlan_id}` | getOrgWLAN | `mistapi.api.v1.orgs.wlans` |
| `listOrgWlans` | `/api/v1/orgs/{org_id}/wlans` | listOrgWlans | `mistapi.api.v1.orgs.wlans` |

## Orgs WxRules

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgWxRule` | `/api/v1/orgs/{org_id}/wxrules/{wxrule_id}` | getOrgWxRule | `mistapi.api.v1.orgs.wxrules` |
| `listOrgWxRules` | `/api/v1/orgs/{org_id}/wxrules` | listOrgWxRules | `mistapi.api.v1.orgs.wxrules` |

## Orgs WxTags

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgApplicationList` | `/api/v1/orgs/{org_id}/wxtags/apps` | getOrgApplicationList | `mistapi.api.v1.orgs.wxtags` |
| `getOrgCurrentMatchingClientsOfAWxTag` | `/api/v1/orgs/{org_id}/wxtags/{wxtag_id}/clients` | getOrgCurrentMatchingClientsOfAWxTag | `mistapi.api.v1.orgs.wxtags` |
| `getOrgWxTag` | `/api/v1/orgs/{org_id}/wxtags/{wxtag_id}` | getOrgWxTag | `mistapi.api.v1.orgs.wxtags` |
| `listOrgWxTags` | `/api/v1/orgs/{org_id}/wxtags` | listOrgWxTags | `mistapi.api.v1.orgs.wxtags` |

## Orgs WxTunnels

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgWxTunnel` | `/api/v1/orgs/{org_id}/wxtunnels/{wxtunnel_id}` | getOrgWxTunnel | `mistapi.api.v1.orgs.wxtunnels` |
| `listOrgWxTunnels` | `/api/v1/orgs/{org_id}/wxtunnels` | listOrgWxTunnels | `mistapi.api.v1.orgs.wxtunnels` |

## Self API Token

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getApiToken` | `/api/v1/self/apitokens/{apitoken_id}` | getApiToken | `mistapi.api.v1.self.apitokens` |
| `listApiTokens` | `/api/v1/self/apitokens` | listApiTokens | `mistapi.api.v1.self.apitokens` |

## Self Account

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSelf` | `/api/v1/self` | getSelf | `mistapi.api.v1.self.self` |
| `getSelfApiUsage` | `/api/v1/self/usage` | getSelfApiUsage | `mistapi.api.v1.self.usage` |
| `getSelfLoginFailures` | `/api/v1/self/login_failures` | getSelfLoginFailures | `mistapi.api.v1.self.login_failures` |
| `verifySelfEmail` | `/api/v1/self/update/verify/{token}` | verifySelfEmail | `mistapi.api.v1.self.update` |

## Self Alarms

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listAlarmSubscriptions` | `/api/v1/self/subscriptions` | listAlarmSubscriptions | `mistapi.api.v1.self.subscriptions` |

## Self Audit Logs

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listSelfAuditLogs` | `/api/v1/self/logs` | listSelfAuditLogs | `mistapi.api.v1.self.logs` |

## Self MFA

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `generateSecretFor2faVerification` | `/api/v1/self/two_factor/token` | generateSecretFor2faVerification | `mistapi.api.v1.self.two_factor` |

## Self OAuth2

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOauth2UrlForLinking` | `/api/v1/self/oauth/{provider}` | getOauth2UrlForLinking | `mistapi.api.v1.self.oauth` |

## Sites

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteInfo` | `/api/v1/sites/{site_id}` | getSiteInfo | `mistapi.api.v1.sites.sites` |

## Sites AP Templates

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listSiteApTemplatesDerived` | `/api/v1/sites/{site_id}/aptemplates/derived` | listSiteApTemplatesDerived | `mistapi.api.v1.sites.aptemplates` |

## Sites Advanced Anti Malware Profiles

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listSiteAAMWProfilesDerived` | `/api/v1/sites/{site_id}/aamwprofiles/derived` | listSiteAAMWProfilesDerived | `mistapi.api.v1.sites.aamwprofiles` |

## Sites Alarms

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteAlarms` | `/api/v1/sites/{site_id}/alarms/count` | countSiteAlarms | `mistapi.api.v1.sites.alarms` |
| `searchSiteAlarms` | `/api/v1/sites/{site_id}/alarms/search` | searchSiteAlarms | `mistapi.api.v1.sites.alarms` |

## Sites Anomaly

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteAnomalyEventsForClient` | `/api/v1/sites/{site_id}/anomaly/client/{client_mac}/{metric}` | getSiteAnomalyEventsForClient | `mistapi.api.v1.sites.anomaly` |
| `getSiteAnomalyEventsForDevice` | `/api/v1/sites/{site_id}/anomaly/device/{device_mac}/{metric}` | getSiteAnomalyEventsForDevice | `mistapi.api.v1.sites.anomaly` |
| `listSiteAnomalyEvents` | `/api/v1/sites/{site_id}/anomaly/{metric}` | listSiteAnomalyEvents | `mistapi.api.v1.sites.anomaly` |

## Sites Antivirus Profiles

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listSiteAntivirusProfilesDerived` | `/api/v1/sites/{site_id}/avprofiles/derived` | listSiteAntivirusProfilesDerived | `mistapi.api.v1.sites.avprofiles` |

## Sites Applications

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listSiteApps` | `/api/v1/sites/{site_id}/apps` | listSiteApps | `mistapi.api.v1.sites.apps` |

## Sites Asset Filters

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteAssetFilter` | `/api/v1/sites/{site_id}/assetfilters/{assetfilter_id}` | getSiteAssetFilter | `mistapi.api.v1.sites.assetfilters` |
| `listSiteAssetFilters` | `/api/v1/sites/{site_id}/assetfilters` | listSiteAssetFilters | `mistapi.api.v1.sites.assetfilters` |

## Sites Assets

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteAsset` | `/api/v1/sites/{site_id}/assets/{asset_id}` | getSiteAsset | `mistapi.api.v1.sites.assets` |
| `listSiteAssets` | `/api/v1/sites/{site_id}/assets` | listSiteAssets | `mistapi.api.v1.sites.assets` |

## Sites Auto Map Assignment

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteAutoMapAssignmentStatus` | `/api/v1/sites/{site_id}/auto_map_assignment` | getSiteAutoMapAssignmentStatus | `mistapi.api.v1.sites.auto_map_assignment` |

## Sites Beacons

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteBeacon` | `/api/v1/sites/{site_id}/beacons/{beacon_id}` | getSiteBeacon | `mistapi.api.v1.sites.beacons` |
| `listSiteBeacons` | `/api/v1/sites/{site_id}/beacons` | listSiteBeacons | `mistapi.api.v1.sites.beacons` |

## Sites Clients - NAC

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteNacClientEvents` | `/api/v1/sites/{site_id}/nac_clients/events/count` | countSiteNacClientEvents | `mistapi.api.v1.sites.nac_clients` |
| `countSiteNacClients` | `/api/v1/sites/{site_id}/nac_clients/count` | countSiteNacClients | `mistapi.api.v1.sites.nac_clients` |
| `searchSiteNacClientEvents` | `/api/v1/sites/{site_id}/nac_clients/events/search` | searchSiteNacClientEvents | `mistapi.api.v1.sites.nac_clients` |
| `searchSiteNacClients` | `/api/v1/sites/{site_id}/nac_clients/search` | searchSiteNacClients | `mistapi.api.v1.sites.nac_clients` |

## Sites Clients - Wan

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteWanClientEvents` | `/api/v1/sites/{site_id}/wan_client/events/count` | countSiteWanClientEvents | `mistapi.api.v1.sites.wan_client` |
| `countSiteWanClients` | `/api/v1/sites/{site_id}/wan_clients/count` | countSiteWanClients | `mistapi.api.v1.sites.wan_clients` |
| `searchSiteWanClientEvents` | `/api/v1/sites/{site_id}/wan_clients/events/search` | searchSiteWanClientEvents | `mistapi.api.v1.sites.wan_clients` |
| `searchSiteWanClients` | `/api/v1/sites/{site_id}/wan_clients/search` | searchSiteWanClients | `mistapi.api.v1.sites.wan_clients` |

## Sites Clients - Wired

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteWiredClients` | `/api/v1/sites/{site_id}/wired_clients/count` | countSiteWiredClients | `mistapi.api.v1.sites.wired_clients` |
| `searchSiteWiredClients` | `/api/v1/sites/{site_id}/wired_clients/search` | searchSiteWiredClients | `mistapi.api.v1.sites.wired_clients` |

## Sites Clients - Wireless

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteWirelessClientEvents` | `/api/v1/sites/{site_id}/clients/events/count` | countSiteWirelessClientEvents | `mistapi.api.v1.sites.clients` |
| `countSiteWirelessClientSessions` | `/api/v1/sites/{site_id}/clients/sessions/count` | countSiteWirelessClientSessions | `mistapi.api.v1.sites.clients` |
| `countSiteWirelessClients` | `/api/v1/sites/{site_id}/clients/count` | countSiteWirelessClients | `mistapi.api.v1.sites.clients` |
| `getSiteEventsForClient` | `/api/v1/sites/{site_id}/clients/{client_mac}/events` | getSiteEventsForClient | `mistapi.api.v1.sites.clients` |
| `searchSiteWirelessClientEvents` | `/api/v1/sites/{site_id}/clients/events/search` | searchSiteWirelessClientEvents | `mistapi.api.v1.sites.clients` |
| `searchSiteWirelessClientSessions` | `/api/v1/sites/{site_id}/clients/sessions/search` | searchSiteWirelessClientSessions | `mistapi.api.v1.sites.clients` |
| `searchSiteWirelessClients` | `/api/v1/sites/{site_id}/clients/search` | searchSiteWirelessClients | `mistapi.api.v1.sites.clients` |

## Sites Device Profiles

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listSiteDeviceProfilesDerived` | `/api/v1/sites/{site_id}/deviceprofiles/derived` | listSiteDeviceProfilesDerived | `mistapi.api.v1.sites.deviceprofiles` |

## Sites Devices

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteDeviceConfigHistory` | `/api/v1/sites/{site_id}/devices/config_history/count` | countSiteDeviceConfigHistory | `mistapi.api.v1.sites.devices` |
| `countSiteDeviceEvents` | `/api/v1/sites/{site_id}/devices/events/count` | countSiteDeviceEvents | `mistapi.api.v1.sites.devices` |
| `countSiteDeviceLastConfig` | `/api/v1/sites/{site_id}/devices/last_config/count` | countSiteDeviceLastConfig | `mistapi.api.v1.sites.devices` |
| `countSiteDevices` | `/api/v1/sites/{site_id}/devices/count` | countSiteDevices | `mistapi.api.v1.sites.devices` |
| `exportSiteDevices` | `/api/v1/sites/{site_id}/devices/export` | exportSiteDevices | `mistapi.api.v1.sites.devices` |
| `getSiteDevice` | `/api/v1/sites/{site_id}/devices/{device_id}` | getSiteDevice | `mistapi.api.v1.sites.devices` |
| `listSiteDevices` | `/api/v1/sites/{site_id}/devices` | listSiteDevices | `mistapi.api.v1.sites.devices` |
| `searchSiteDeviceConfigHistory` | `/api/v1/sites/{site_id}/devices/config_history/search` | searchSiteDeviceConfigHistory | `mistapi.api.v1.sites.devices` |
| `searchSiteDeviceEvents` | `/api/v1/sites/{site_id}/devices/events/search` | searchSiteDeviceEvents | `mistapi.api.v1.sites.devices` |
| `searchSiteDeviceLastConfigs` | `/api/v1/sites/{site_id}/devices/last_config/search` | searchSiteDeviceLastConfigs | `mistapi.api.v1.sites.devices` |
| `searchSiteDevices` | `/api/v1/sites/{site_id}/devices/search` | searchSiteDevices | `mistapi.api.v1.sites.devices` |

## Sites Devices - Others

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteOtherDeviceEvents` | `/api/v1/sites/{site_id}/otherdevices/events/count` | countSiteOtherDeviceEvents | `mistapi.api.v1.sites.otherdevices` |
| `listSiteOtherDevices` | `/api/v1/sites/{site_id}/otherdevices` | listSiteOtherDevices | `mistapi.api.v1.sites.otherdevices` |
| `searchSiteOtherDeviceEvents` | `/api/v1/sites/{site_id}/otherdevices/events/search` | searchSiteOtherDeviceEvents | `mistapi.api.v1.sites.otherdevices` |

## Sites Devices - WAN Cluster

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `GetSiteDeviceHaClusterNode` | `/api/v1/sites/{site_id}/devices/{device_id}/ha` | GetSiteDeviceHaClusterNode | `mistapi.api.v1.sites.devices` |

## Sites Devices - Wired - Virtual Chassis

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteDeviceVirtualChassis` | `/api/v1/sites/{site_id}/devices/{device_id}/vc` | getSiteDeviceVirtualChassis | `mistapi.api.v1.sites.devices` |

## Sites Devices - Wireless

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteDeviceIotPort` | `/api/v1/sites/{site_id}/devices/{device_id}/iot` | getSiteDeviceIotPort | `mistapi.api.v1.sites.devices` |
| `listSiteDeviceRadioChannels` | `/api/v1/sites/{site_id}/devices/ap_channels` | listSiteDeviceRadioChannels | `mistapi.api.v1.sites.devices` |

## Sites EVPN Topologies

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteEvpnTopology` | `/api/v1/sites/{site_id}/evpn_topologies/{evpn_topology_id}` | getSiteEvpnTopology | `mistapi.api.v1.sites.evpn_topologies` |
| `listSiteEvpnTopologies` | `/api/v1/sites/{site_id}/evpn_topologies` | listSiteEvpnTopologies | `mistapi.api.v1.sites.evpn_topologies` |

## Sites Events

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteSystemEvents` | `/api/v1/sites/{site_id}/events/system/count` | countSiteSystemEvents | `mistapi.api.v1.sites.events` |
| `listSiteRoamingEvents` | `/api/v1/sites/{site_id}/events/fast_roam` | listSiteRoamingEvents | `mistapi.api.v1.sites.events` |
| `searchSiteSystemEvents` | `/api/v1/sites/{site_id}/events/system/search` | searchSiteSystemEvents | `mistapi.api.v1.sites.events` |

## Sites Gateway Templates

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listSiteGatewayTemplatesDerived` | `/api/v1/sites/{site_id}/gatewaytemplates/derived` | listSiteGatewayTemplatesDerived | `mistapi.api.v1.sites.gatewaytemplates` |

## Sites Guests

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteGuestAuthorizations` | `/api/v1/sites/{site_id}/guests/count` | countSiteGuestAuthorizations | `mistapi.api.v1.sites.guests` |
| `getSiteGuestAuthorization` | `/api/v1/sites/{site_id}/guests/{guest_mac}` | getSiteGuestAuthorization | `mistapi.api.v1.sites.guests` |
| `listSiteAllGuestAuthorizations` | `/api/v1/sites/{site_id}/guests` | listSiteAllGuestAuthorizations | `mistapi.api.v1.sites.guests` |
| `listSiteAllGuestAuthorizationsDerived` | `/api/v1/sites/{site_id}/guests/derived` | listSiteAllGuestAuthorizationsDerived | `mistapi.api.v1.sites.guests` |
| `searchSiteGuestAuthorization` | `/api/v1/sites/{site_id}/guests/search` | searchSiteGuestAuthorization | `mistapi.api.v1.sites.guests` |

## Sites IDP Profiles

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listSiteIdpProfilesDerived` | `/api/v1/sites/{site_id}/idpprofiles/derived` | listSiteIdpProfilesDerived | `mistapi.api.v1.sites.idpprofiles` |

## Sites Insights

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteInsightMetrics` | `/api/v1/sites/{site_id}/insights` | getSiteInsightMetrics | `mistapi.api.v1.sites.insights` |
| `getSiteInsightMetricsForAP` | `/api/v1/sites/{site_id}/insights/ap/{device_id}/stats` | getSiteInsightMetricsForAP | `mistapi.api.v1.sites.insights` |
| `getSiteInsightMetricsForClient` | `/api/v1/sites/{site_id}/insights/client/{client_mac}` | getSiteInsightMetricsForClient | `mistapi.api.v1.sites.insights` |
| `getSiteInsightMetricsForDevice` | `/api/v1/sites/{site_id}/insights/device/{device_mac}/{metric}` | getSiteInsightMetricsForDevice | `mistapi.api.v1.sites.insights` |
| `getSiteInsightMetricsForGateway` | `/api/v1/sites/{site_id}/insights/gateway/{device_id}/stats` | getSiteInsightMetricsForGateway | `mistapi.api.v1.sites.insights` |
| `getSiteInsightMetricsForMxEdge` | `/api/v1/sites/{site_id}/insights/mxedge/{device_mac}/{metric}` | getSiteInsightMetricsForMxEdge | `mistapi.api.v1.sites.insights` |
| `getSiteInsightMetricsForSwitch` | `/api/v1/sites/{site_id}/insights/switch/{device_mac}/{metric}` | getSiteInsightMetricsForSwitch | `mistapi.api.v1.sites.insights` |

## Sites JSE

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteJseInfo` | `/api/v1/sites/{site_id}/setting/jse/info` | getSiteJseInfo | `mistapi.api.v1.sites.setting` |

## Sites Licenses

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteLicenseUsage` | `/api/v1/sites/{site_id}/licenses/usages` | getSiteLicenseUsage | `mistapi.api.v1.sites.licenses` |

## Sites Location

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteBeamCoverageOverview` | `/api/v1/sites/{site_id}/location/coverage` | getSiteBeamCoverageOverview | `mistapi.api.v1.sites.location` |
| `getSiteDefaultPlfForModels` | `/api/v1/sites/{site_id}/location/ml/defaults` | getSiteDefaultPlfForModels | `mistapi.api.v1.sites.location` |
| `getSiteMachineLearningCurrentStat` | `/api/v1/sites/{site_id}/location/ml/current` | getSiteMachineLearningCurrentStat | `mistapi.api.v1.sites.location` |

## Sites Map Stacks

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listSiteMapStacks` | `/api/v1/sites/{site_id}/mapstacks` | listSiteMapStacks | `mistapi.api.v1.sites.mapstacks` |

## Sites Maps

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteMap` | `/api/v1/sites/{site_id}/maps/{map_id}` | getSiteMap | `mistapi.api.v1.sites.maps` |
| `listSiteMaps` | `/api/v1/sites/{site_id}/maps` | listSiteMaps | `mistapi.api.v1.sites.maps` |

## Sites Maps - Auto-Zone

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteMapAutoZoneStatus` | `/api/v1/sites/{site_id}/maps/{map_id}/auto_zones` | getSiteMapAutoZoneStatus | `mistapi.api.v1.sites.maps` |

## Sites Maps - Auto-placement

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteApAutoOrientation` | `/api/v1/sites/{site_id}/maps/{map_id}/auto_orient` | getSiteApAutoOrientation | `mistapi.api.v1.sites.maps` |
| `getSiteApAutoPlacement` | `/api/v1/sites/{site_id}/maps/{map_id}/auto_placement` | getSiteApAutoplacement | `mistapi.api.v1.sites.maps` |

## Sites Marvis Configs

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteMarvisConfigActions` | `/api/v1/sites/{site_id}/marvis_configs/count` | countSiteMarvisConfigActions | `mistapi.api.v1.sites.marvis_configs` |
| `searchSiteMarvisConfigActions` | `/api/v1/sites/{site_id}/marvis_configs/search` | searchSiteMarvisConfigActions | `mistapi.api.v1.sites.marvis_configs` |

## Sites MxEdges

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteMxEdgeEvents` | `/api/v1/sites/{site_id}/mxedges/events/count` | countSiteMxEdgeEvents | `mistapi.api.v1.sites.mxedges` |
| `getSiteMxEdge` | `/api/v1/sites/{site_id}/mxedges/{mxedge_id}` | getSiteMxEdge | `mistapi.api.v1.sites.mxedges` |
| `listSiteMxEdges` | `/api/v1/sites/{site_id}/mxedges` | listSiteMxEdges | `mistapi.api.v1.sites.mxedges` |
| `searchSiteMistEdgeEvents` | `/api/v1/sites/{site_id}/mxedges/events/search` | searchSiteMistEdgeEvents | `mistapi.api.v1.sites.mxedges` |

## Sites NAC Fingerprints

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteClientFingerprints` | `/api/v1/sites/{site_id}/insights/fingerprints/count` | countSiteClientFingerprints | `mistapi.api.v1.sites.insights` |
| `searchSiteClientFingerprints` | `/api/v1/sites/{site_id}/insights/fingerprints/search` | searchSiteClientFingerprints | `mistapi.api.v1.sites.insights` |

## Sites Network Templates

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listSiteNetworkTemplatesDerived` | `/api/v1/sites/{site_id}/networktemplates/derived` | listSiteNetworkTemplatesDerived | `mistapi.api.v1.sites.networktemplates` |

## Sites Networks

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listSiteNetworksDerived` | `/api/v1/sites/{site_id}/networks/derived` | listSiteNetworksDerived | `mistapi.api.v1.sites.networks` |

## Sites Psks

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSitePsk` | `/api/v1/sites/{site_id}/psks/{psk_id}` | getSitePsk | `mistapi.api.v1.sites.psks` |
| `listSitePsks` | `/api/v1/sites/{site_id}/psks` | listSitePsks | `mistapi.api.v1.sites.psks` |

## Sites RF Templates

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listSiteRfTemplatesDerived` | `/api/v1/sites/{site_id}/rftemplates/derived` | listSiteRfTemplatesDerived | `mistapi.api.v1.sites.rftemplates` |

## Sites RRM

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteChannelScores` | `/api/v1/sites/{site_id}/rrm/channel_scores/band/{band}` | getSiteChannelScores | `mistapi.api.v1.sites.rrm` |
| `getSiteCurrentChannelPlanning` | `/api/v1/sites/{site_id}/rrm/current` | getSiteCurrentChannelPlanning | `mistapi.api.v1.sites.rrm` |
| `getSiteCurrentRrmConsiderations` | `/api/v1/sites/{site_id}/rrm/current/devices/{device_id}/band/{band}` | getSiteCurrentRrmConsiderations | `mistapi.api.v1.sites.rrm` |
| `listSiteCurrentRrmNeighbors` | `/api/v1/sites/{site_id}/rrm/neighbors/band/{band}` | listSiteCurrentRrmNeighbors | `mistapi.api.v1.sites.rrm` |
| `listSiteRrmEvents` | `/api/v1/sites/{site_id}/rrm/events` | listSiteRrmEvents | `mistapi.api.v1.sites.rrm` |

## Sites RSSI Zones

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteRssiZone` | `/api/v1/sites/{site_id}/rssizones/{rssizone_id}` | getSiteRssiZone | `mistapi.api.v1.sites.rssizones` |
| `listSiteRssiZones` | `/api/v1/sites/{site_id}/rssizones` | listSiteRssiZones | `mistapi.api.v1.sites.rssizones` |

## Sites Rfdiags

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `downloadSiteRfdiagRecording` | `/api/v1/sites/{site_id}/rfdiags/{rfdiag_id}/download` | downloadSiteRfdiagRecording | `mistapi.api.v1.sites.rfdiags` |
| `getSiteRfdiagRecording` | `/api/v1/sites/{site_id}/rfdiags/{rfdiag_id}` | getSiteRfdiagRecording | `mistapi.api.v1.sites.rfdiags` |
| `getSiteSiteRfdiagRecording` | `/api/v1/sites/{site_id}/rfdiags` | getSiteSiteRfdiagRecording | `mistapi.api.v1.sites.rfdiags` |

## Sites Rogues

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteRogueEvents` | `/api/v1/sites/{site_id}/rogues/events/count` | countSiteRogueEvents | `mistapi.api.v1.sites.rogues` |
| `getSiteRogueAP` | `/api/v1/sites/{site_id}/rogues/{rogue_bssid}` | getSiteRogueAP | `mistapi.api.v1.sites.rogues` |
| `listSiteRogueAPs` | `/api/v1/sites/{site_id}/insights/rogues` | listSiteRogueAPs | `mistapi.api.v1.sites.insights` |
| `listSiteRogueClients` | `/api/v1/sites/{site_id}/insights/rogues/clients` | listSiteRogueClients | `mistapi.api.v1.sites.insights` |
| `searchSiteRogueEvents` | `/api/v1/sites/{site_id}/rogues/events/search` | searchSiteRogueEvents | `mistapi.api.v1.sites.rogues` |

## Sites SLEs

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteSleClassifierDetails` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/classifier/{classifier}/summary` | getSiteSleClassifierDetails | `mistapi.api.v1.sites.sle` |
| `getSiteSleClassifierSummaryTrend` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/classifier/{classifier}/summary-trend` | getSiteSleClassifierSummaryTrend | `mistapi.api.v1.sites.sle` |
| `getSiteSleHistogram` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/histogram` | getSiteSleHistogram | `mistapi.api.v1.sites.sle` |
| `getSiteSleImpactSummary` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impact-summary` | getSiteSleImpactSummary | `mistapi.api.v1.sites.sle` |
| `getSiteSleSummary` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/summary` | getSiteSleSummary | `mistapi.api.v1.sites.sle` |
| `getSiteSleSummaryTrend` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/summary-trend` | getSiteSleSummaryTrend | `mistapi.api.v1.sites.sle` |
| `getSiteSleThreshold` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/threshold` | getSiteSleThreshold | `mistapi.api.v1.sites.sle` |
| `listSiteSleImpactedApplications` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-applications` | listSiteSleImpactedApplications | `mistapi.api.v1.sites.sle` |
| `listSiteSleImpactedAps` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-aps` | listSiteSleImpactedAps | `mistapi.api.v1.sites.sle` |
| `listSiteSleImpactedChassis` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-chassis` | listSiteSleImpactedChassis | `mistapi.api.v1.sites.sle` |
| `listSiteSleImpactedGateways` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-gateways` | listSiteSleImpactedGateways | `mistapi.api.v1.sites.sle` |
| `listSiteSleImpactedInterfaces` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-interfaces` | listSiteSleImpactedInterfaces | `mistapi.api.v1.sites.sle` |
| `listSiteSleImpactedSwitches` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-switches` | listSiteSleImpactedSwitches | `mistapi.api.v1.sites.sle` |
| `listSiteSleImpactedWiredClients` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-clients` | listSiteSleImpactedWiredClients | `mistapi.api.v1.sites.sle` |
| `listSiteSleImpactedWirelessClients` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-users` | listSiteSleImpactedWirelessClients | `mistapi.api.v1.sites.sle` |
| `listSiteSleMetricClassifiers` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/classifiers` | listSiteSleMetricClassifiers | `mistapi.api.v1.sites.sle` |
| `listSiteSlesMetrics` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metrics` | listSiteSlesMetrics | `mistapi.api.v1.sites.sle` |

## Sites SecIntel Profiles

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listSiteSecIntelProfilesDerived` | `/api/v1/sites/{site_id}/secintelprofiles/derived` | listSiteSecIntelProfilesDerived | `mistapi.api.v1.sites.secintelprofiles` |

## Sites Service Policies

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listSiteServicePoliciesDerived` | `/api/v1/sites/{site_id}/servicepolicies/derived` | listSiteServicePoliciesDerived | `mistapi.api.v1.sites.servicepolicies` |

## Sites Services

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteServicePathEvents` | `/api/v1/sites/{site_id}/services/events/count` | countSiteServicePathEvents | `mistapi.api.v1.sites.services` |
| `listSiteServicesDerived` | `/api/v1/sites/{site_id}/services/derived` | listSiteServicesDerived | `mistapi.api.v1.sites.services` |
| `searchSiteServicePathEvents` | `/api/v1/sites/{site_id}/services/events/search` | searchSiteServicePathEvents | `mistapi.api.v1.sites.services` |

## Sites Setting

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteSetting` | `/api/v1/sites/{site_id}/setting` | getSiteSetting | `mistapi.api.v1.sites.setting` |
| `getSiteSettingDerived` | `/api/v1/sites/{site_id}/setting/derived` | getSiteSettingDerived | `mistapi.api.v1.sites.setting` |

## Sites Site Templates

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listSiteSiteTemplatesDerived` | `/api/v1/sites/{site_id}/sitetemplates/derived` | listSiteSiteTemplatesDerived | `mistapi.api.v1.sites.sitetemplates` |

## Sites Skyatp

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteSkyatpEvents` | `/api/v1/sites/{site_id}/skyatp/events/count` | countSiteSkyatpEvents | `mistapi.api.v1.sites.skyatp` |
| `searchSiteSkyatpEvents` | `/api/v1/sites/{site_id}/skyatp/events/search` | searchSiteSkyatpEvents | `mistapi.api.v1.sites.skyatp` |

## Sites Spectrum Analysis

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteRunningSpectrumAnalysis` | `/api/v1/sites/{site_id}/analyze_spectrum` | getSiteRunningSpectrumAnalysis | `mistapi.api.v1.sites.analyze_spectrum` |
| `listSiteSpectrumAnalysis` | `/api/v1/sites/{site_id}/stats/analyze_spectrum` | listSiteSpectrumAnalysis | `mistapi.api.v1.sites.stats` |

## Sites Stats

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteStats` | `/api/v1/sites/{site_id}/stats` | getSiteStats | `mistapi.api.v1.sites.stats` |

## Sites Stats - Apps

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteApps` | `/api/v1/sites/{site_id}/stats/apps/count` | countSiteApps | `mistapi.api.v1.sites.stats` |

## Sites Stats - Assets

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteAssets` | `/api/v1/sites/{site_id}/stats/assets/count` | countSiteAssets | `mistapi.api.v1.sites.stats` |
| `getSiteAssetStats` | `/api/v1/sites/{site_id}/stats/assets/{asset_id}` | getSiteAssetStats | `mistapi.api.v1.sites.stats` |
| `getSiteAssetsOfInterest` | `/api/v1/sites/{site_id}/stats/filtered_assets` | getSiteAssetsOfInterest | `mistapi.api.v1.sites.stats` |
| `getSiteDiscoveredAssetByMap` | `/api/v1/sites/{site_id}/stats/maps/{map_id}/discovered_assets` | getSiteDiscoveredAssetByMap | `mistapi.api.v1.sites.stats` |
| `listSiteAssetsStats` | `/api/v1/sites/{site_id}/stats/assets` | listSiteAssetsStats | `mistapi.api.v1.sites.stats` |
| `listSiteDiscoveredAssets` | `/api/v1/sites/{site_id}/stats/discovered_assets` | listSiteDiscoveredAssets | `mistapi.api.v1.sites.stats` |
| `searchSiteAssets` | `/api/v1/sites/{site_id}/stats/assets/search` | searchSiteAssets | `mistapi.api.v1.sites.stats` |

## Sites Stats - BGP Peers

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteBgpStats` | `/api/v1/sites/{site_id}/stats/bgp_peers/count` | countSiteBgpStats | `mistapi.api.v1.sites.stats` |
| `searchSiteBgpStats` | `/api/v1/sites/{site_id}/stats/bgp_peers/search` | searchSiteBgpStats | `mistapi.api.v1.sites.stats` |

## Sites Stats - Beacons

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listSiteBeaconsStats` | `/api/v1/sites/{site_id}/stats/beacons` | listSiteBeaconsStats | `mistapi.api.v1.sites.stats` |

## Sites Stats - Calls

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteCalls` | `/api/v1/sites/{site_id}/stats/calls/count` | countSiteCalls | `mistapi.api.v1.sites.stats` |
| `getSiteCallsSummary` | `/api/v1/sites/{site_id}/stats/calls/summary` | getSiteCallsSummary | `mistapi.api.v1.sites.stats` |
| `listSiteTroubleshootCalls` | `/api/v1/sites/{site_id}/stats/calls/troubleshoot` | listSiteTroubleshootCalls | `mistapi.api.v1.sites.stats` |
| `searchSiteCalls` | `/api/v1/sites/{site_id}/stats/calls/search` | searchSiteCalls | `mistapi.api.v1.sites.stats` |
| `troubleshootSiteCall` | `/api/v1/sites/{site_id}/stats/calls/client/{client_mac}/troubleshoot` | troubleshootSiteCall | `mistapi.api.v1.sites.stats` |

## Sites Stats - Clients SDK

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteSdkStats` | `/api/v1/sites/{site_id}/stats/sdkclients/{sdkclient_id}` | getSiteSdkStats | `mistapi.api.v1.sites.stats` |
| `getSiteSdkStatsByMap` | `/api/v1/sites/{site_id}/stats/maps/{map_id}/sdkclients` | getSiteSdkStatsByMap | `mistapi.api.v1.sites.stats` |

## Sites Stats - Clients Wireless

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteWirelessClientStats` | `/api/v1/sites/{site_id}/stats/clients/{client_mac}` | getSiteWirelessClientStats | `mistapi.api.v1.sites.stats` |
| `getSiteWirelessClientsStatsByMap` | `/api/v1/sites/{site_id}/stats/maps/{map_id}/clients` | getSiteWirelessClientsStatsByMap | `mistapi.api.v1.sites.stats` |
| `listSiteUnconnectedClientStats` | `/api/v1/sites/{site_id}/stats/maps/{map_id}/unconnected_clients` | listSiteUnconnectedClientStats | `mistapi.api.v1.sites.stats` |
| `listSiteWirelessClientsStats` | `/api/v1/sites/{site_id}/stats/clients` | listSiteWirelessClientsStats | `mistapi.api.v1.sites.stats` |

## Sites Stats - Devices

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteAllClientsStatsByDevice` | `/api/v1/sites/{site_id}/stats/devices/{device_id}/clients` | getSiteAllClientsStatsByDevice | `mistapi.api.v1.sites.stats` |
| `getSiteDeviceStats` | `/api/v1/sites/{site_id}/stats/devices/{device_id}` | getSiteDeviceStats | `mistapi.api.v1.sites.stats` |
| `getSiteGatewayMetrics` | `/api/v1/sites/{site_id}/stats/gateways/metrics` | getSiteGatewayMetrics | `mistapi.api.v1.sites.stats` |
| `getSiteSwitchesMetrics` | `/api/v1/sites/{site_id}/stats/switches/metrics` | getSiteSwitchesMetrics | `mistapi.api.v1.sites.stats` |
| `listSiteDevicesStats` | `/api/v1/sites/{site_id}/stats/devices` | listSiteDevicesStats | `mistapi.api.v1.sites.stats` |

## Sites Stats - Discovered Switches

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteDiscoveredSwitches` | `/api/v1/sites/{site_id}/stats/discovered_switches/count` | countSiteDiscoveredSwitches | `mistapi.api.v1.sites.stats` |
| `listSiteDiscoveredSwitchesMetrics` | `/api/v1/sites/{site_id}/stats/discovered_switches/metrics` | listSiteDiscoveredSwitchesMetrics | `mistapi.api.v1.sites.stats` |
| `searchSiteDiscoveredSwitches` | `/api/v1/sites/{site_id}/stats/discovered_switches/search` | searchSiteDiscoveredSwitches | `mistapi.api.v1.sites.stats` |
| `searchSiteDiscoveredSwitchesMetrics` | `/api/v1/sites/{site_id}/stats/discovered_switch_metrics/search` | searchSiteDiscoveredSwitchesMetrics | `mistapi.api.v1.sites.stats` |

## Sites Stats - IoT Endpoints

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteIotEndpoints` | `/api/v1/sites/{site_id}/iotendpoints/count` | countSiteIotEndpoints | `mistapi.api.v1.sites.iotendpoints` |
| `searchSiteIotEndpoints` | `/api/v1/sites/{site_id}/iotendpoints/search` | searchSiteIotEndpoints | `mistapi.api.v1.sites.iotendpoints` |

## Sites Stats - MxEdges

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteMxEdgeStats` | `/api/v1/sites/{site_id}/stats/mxedges/{mxedge_id}` | getSiteMxEdgeStats | `mistapi.api.v1.sites.stats` |
| `listSiteMxEdgesStats` | `/api/v1/sites/{site_id}/stats/mxedges` | listSiteMxEdgesStats | `mistapi.api.v1.sites.stats` |

## Sites Stats - Ospf

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteOspfStats` | `/api/v1/sites/{site_id}/stats/ospf_peers/count` | countOrgOspfStats | `mistapi.api.v1.sites.stats` |
| `searchSiteOspfStats` | `/api/v1/sites/{site_id}/stats/ospf_peers/search` | searchSiteOspfStats | `mistapi.api.v1.sites.stats` |

## Sites Stats - Ports

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteSwOrGwPorts` | `/api/v1/sites/{site_id}/stats/ports/count` | countSiteSwOrGwPorts | `mistapi.api.v1.sites.stats` |
| `searchSiteSwOrGwPorts` | `/api/v1/sites/{site_id}/stats/ports/search` | searchSiteSwOrGwPorts | `mistapi.api.v1.sites.stats` |

## Sites Stats - WxRules

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteWxRulesUsage` | `/api/v1/sites/{site_id}/stats/wxrules` | getSiteWxRulesUsage | `mistapi.api.v1.sites.stats` |

## Sites Stats - Zones

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteRssiZoneStats` | `/api/v1/sites/{site_id}/stats/rssizones/{zone_id}` | getSiteRssiZoneStats | `mistapi.api.v1.sites.stats` |
| `getSiteZoneStats` | `/api/v1/sites/{site_id}/stats/zones/{zone_id}` | getSiteZoneStats | `mistapi.api.v1.sites.stats` |
| `listSiteRssiZonesStats` | `/api/v1/sites/{site_id}/stats/rssizones` | listSiteRssiZonesStats | `mistapi.api.v1.sites.stats` |
| `listSiteZonesStats` | `/api/v1/sites/{site_id}/stats/zones` | listSiteZonesStats | `mistapi.api.v1.sites.stats` |

## Sites Synthetic Tests

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteDeviceSyntheticTest` | `/api/v1/sites/{site_id}/devices/{device_id}/synthetic_test` | getSiteDeviceSyntheticTest | `mistapi.api.v1.sites.devices` |
| `searchSiteSyntheticTest` | `/api/v1/sites/{site_id}/synthetic_test/search` | searchSiteSyntheticTest | `mistapi.api.v1.sites.synthetic_test` |

## Sites UI Settings

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteUiSetting` | `/api/v1/sites/{site_id}/uisettings/{uisetting_id}` | getSiteUiSetting | `mistapi.api.v1.sites.uisettings` |
| `listSiteUiSettingDerived` | `/api/v1/sites/{site_id}/uisettings/derived` | listSiteUiSettingDerived | `mistapi.api.v1.sites.uisettings` |
| `listSiteUiSettings` | `/api/v1/sites/{site_id}/uisettings` | listSiteUiSettings | `mistapi.api.v1.sites.uisettings` |

## Sites VPNs

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `listSiteVpnsDerived` | `/api/v1/sites/{site_id}/vpns/derived` | listSiteVpnsDerived | `mistapi.api.v1.sites.vpns` |

## Sites WAN Usages

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteWanUsage` | `/api/v1/sites/{site_id}/wan_usages/count` | countSiteWanUsage | `mistapi.api.v1.sites.wan_usages` |
| `searchSiteWanUsage` | `/api/v1/sites/{site_id}/wan_usages/search` | searchSiteWanUsage | `mistapi.api.v1.sites.wan_usages` |

## Sites Webhooks

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteWebhooksDeliveries` | `/api/v1/sites/{site_id}/webhooks/{webhook_id}/events/count` | countSiteWebhooksDeliveries | `mistapi.api.v1.sites.webhooks` |
| `getSiteWebhook` | `/api/v1/sites/{site_id}/webhooks/{webhook_id}` | getSiteWebhook | `mistapi.api.v1.sites.webhooks` |
| `listSiteWebhooks` | `/api/v1/sites/{site_id}/webhooks` | listSiteWebhooks | `mistapi.api.v1.sites.webhooks` |
| `searchSiteWebhooksDeliveries` | `/api/v1/sites/{site_id}/webhooks/{webhook_id}/events/search` | searchSiteWebhooksDeliveries | `mistapi.api.v1.sites.webhooks` |

## Sites Wlans

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteWlan` | `/api/v1/sites/{site_id}/wlans/{wlan_id}` | getSiteWlan | `mistapi.api.v1.sites.wlans` |
| `listSiteWlans` | `/api/v1/sites/{site_id}/wlans` | listSiteWlans | `mistapi.api.v1.sites.wlans` |
| `listSiteWlansDerived` | `/api/v1/sites/{site_id}/wlans/derived` | listSiteWlansDerived | `mistapi.api.v1.sites.wlans` |

## Sites WxRules

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `ListSiteWxRulesDerived` | `/api/v1/sites/{site_id}/wxrules/derived` | ListSiteWxRulesDerived | `mistapi.api.v1.sites.wxrules` |
| `getSiteWxRule` | `/api/v1/sites/{site_id}/wxrules/{wxrule_id}` | getSiteWxRule | `mistapi.api.v1.sites.wxrules` |
| `listSiteWxRules` | `/api/v1/sites/{site_id}/wxrules` | listSiteWxRules | `mistapi.api.v1.sites.wxrules` |

## Sites WxTags

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteApplicationList` | `/api/v1/sites/{site_id}/wxtags/apps` | getSiteApplicationList | `mistapi.api.v1.sites.wxtags` |
| `getSiteWxTag` | `/api/v1/sites/{site_id}/wxtags/{wxtag_id}` | getSiteWxTag | `mistapi.api.v1.sites.wxtags` |
| `listSiteWxTags` | `/api/v1/sites/{site_id}/wxtags` | listSiteWxTags | `mistapi.api.v1.sites.wxtags` |

## Sites WxTunnels

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteWxTunnel` | `/api/v1/sites/{site_id}/wxtunnels/{wxtunnel_id}` | getSiteWxTunnel | `mistapi.api.v1.sites.wxtunnels` |
| `listSiteWxTunnels` | `/api/v1/sites/{site_id}/wxtunnels` | listSiteWxTunnels | `mistapi.api.v1.sites.wxtunnels` |

## Sites Zones

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `countSiteZoneSessions` | `/api/v1/sites/{site_id}/{zone_type}/count` | countSiteZoneSessions | `mistapi.api.v1.sites.count` |
| `getSiteZone` | `/api/v1/sites/{site_id}/zones/{zone_id}` | getSiteZone | `mistapi.api.v1.sites.zones` |
| `listSiteZones` | `/api/v1/sites/{site_id}/zones` | listSiteZones | `mistapi.api.v1.sites.zones` |
| `searchSiteZoneSessions` | `/api/v1/sites/{site_id}/{zone_type}/visits/search` | searchSiteZoneSessions | `mistapi.api.v1.sites.visits` |

## Sites vBeacons

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteVBeacon` | `/api/v1/sites/{site_id}/vbeacons/{vbeacon_id}` | getSiteVBeacon | `mistapi.api.v1.sites.vbeacons` |
| `listSiteVBeacons` | `/api/v1/sites/{site_id}/vbeacons` | listSiteVBeacons | `mistapi.api.v1.sites.vbeacons` |

## Utilities Common

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getSiteDeviceConfigCmd` | `/api/v1/sites/{site_id}/devices/{device_id}/config_cmd` | getSiteDeviceConfigCmd | `mistapi.api.v1.sites.devices` |

## Utilities LAN

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `searchSiteDeviceFlowRecords` | `/api/v1/sites/{site_id}/devices/{device_id}/flow_records/search` | searchSiteDeviceFlowRecords | `mistapi.api.v1.sites.devices` |

## Utilities PCAPs

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgCapturingStatus` | `/api/v1/orgs/{org_id}/pcaps/capture` | getOrgCapturingStatus | `mistapi.api.v1.orgs.pcaps` |
| `getSiteCapturingStatus` | `/api/v1/sites/{site_id}/pcaps/capture` | getSiteCapturingStatus | `mistapi.api.v1.sites.pcaps` |
| `listOrgPacketCaptures` | `/api/v1/orgs/{org_id}/pcaps` | listOrgPacketCaptures | `mistapi.api.v1.orgs.pcaps` |
| `listSitePacketCaptures` | `/api/v1/sites/{site_id}/pcaps` | listSitePacketCaptures | `mistapi.api.v1.sites.pcaps` |

## Utilities Upgrade

| operationId | Path | Summary | mistapi module |
|---|---|---|---|
| `getOrgDeviceUpgrade` | `/api/v1/orgs/{org_id}/devices/upgrade/{upgrade_id}` | getOrgDeviceUpgrade | `mistapi.api.v1.orgs.devices` |
| `getOrgMxEdgeUpgrade` | `/api/v1/orgs/{org_id}/mxedges/upgrade/{upgrade_id}` | getOrgMxEdgeUpgrade | `mistapi.api.v1.orgs.mxedges` |
| `getOrgSsrUpgrade` | `/api/v1/orgs/{org_id}/ssr/upgrade/{upgrade_id}/cancel` | getOrgSsrUpgrade | `mistapi.api.v1.orgs.ssr` |
| `getSiteDeviceUpgrade` | `/api/v1/sites/{site_id}/devices/upgrade/{upgrade_id}` | getSiteDeviceUpgrade | `mistapi.api.v1.sites.devices` |
| `getSiteMxEdgeUpgrade` | `/api/v1/sites/{site_id}/mxedges/upgrade/{upgrade_id}` | getSiteMxEdgeUpgrade | `mistapi.api.v1.sites.mxedges` |
| `getSiteSsrUpgrade` | `/api/v1/sites/{site_id}/ssr/upgrade/{upgrade_id}` | getSiteSsrUpgrade | `mistapi.api.v1.sites.ssr` |
| `listOrgAvailableDeviceVersions` | `/api/v1/orgs/{org_id}/devices/versions` | listOrgAvailableDeviceVersions | `mistapi.api.v1.orgs.devices` |
| `listOrgAvailableSsrVersions` | `/api/v1/orgs/{org_id}/ssr/versions` | listOrgAvailableSsrVersions | `mistapi.api.v1.orgs.ssr` |
| `listOrgDeviceUpgrades` | `/api/v1/orgs/{org_id}/devices/upgrade` | listOrgDeviceUpgrades | `mistapi.api.v1.orgs.devices` |
| `listOrgMxEdgeUpgrades` | `/api/v1/orgs/{org_id}/mxedges/upgrade` | listOrgMxEdgeUpgrades | `mistapi.api.v1.orgs.mxedges` |
| `listOrgSsrUpgrades` | `/api/v1/orgs/{org_id}/ssr/upgrade` | listOrgSsrUpgrades | `mistapi.api.v1.orgs.ssr` |
| `listSiteAvailableDeviceVersions` | `/api/v1/sites/{site_id}/devices/versions` | listSiteAvailableDeviceVersions | `mistapi.api.v1.sites.devices` |
| `listSiteDeviceUpgrades` | `/api/v1/sites/{site_id}/devices/upgrade` | listSiteDeviceUpgrades | `mistapi.api.v1.sites.devices` |
| `listSiteMxEdgeUpgrades` | `/api/v1/sites/{site_id}/mxedges/upgrade` | listSiteMxEdgeUpgrades | `mistapi.api.v1.sites.mxedges` |

