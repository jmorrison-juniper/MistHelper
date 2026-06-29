# Mist API Missing GET Endpoints

> Generated 2026-06-29T00:28:12Z. Diff between OpenAPI GET endpoints and current `MistHelper.py` usage.

- **GET endpoints in spec**: 508
- **Implemented in repo**: 100
- **Missing (to be specced)**: 408

## Coverage by Tag

| Tag | Implemented | Missing | Total |
|---|---:|---:|---:|
| Admins | 0 | 1 | 1 |
| Admins Login - OAuth2 | 0 | 1 | 1 |
| Constants Definitions | 1 | 15 | 16 |
| Constants Events | 0 | 7 | 7 |
| Constants Models | 0 | 4 | 4 |
| Installer | 0 | 9 | 9 |
| MSPs | 0 | 2 | 2 |
| MSPs Admins | 0 | 2 | 2 |
| MSPs Inventory | 0 | 1 | 1 |
| MSPs Licenses | 0 | 2 | 2 |
| MSPs Logs | 0 | 2 | 2 |
| MSPs Marvis | 0 | 1 | 1 |
| MSPs Org Groups | 0 | 2 | 2 |
| MSPs Orgs | 0 | 4 | 4 |
| MSPs SLEs | 0 | 1 | 1 |
| MSPs SSO | 0 | 5 | 5 |
| MSPs SSO Roles | 0 | 1 | 1 |
| MSPs Tickets | 0 | 2 | 2 |
| Orgs | 1 | 0 | 1 |
| Orgs AP Templates | 1 | 1 | 2 |
| Orgs API Tokens | 1 | 1 | 2 |
| Orgs Admins | 1 | 0 | 1 |
| Orgs Advanced Anti Malware Profiles | 0 | 2 | 2 |
| Orgs Alarm Templates | 1 | 2 | 3 |
| Orgs Alarms | 1 | 1 | 2 |
| Orgs Antivirus Profiles | 0 | 2 | 2 |
| Orgs Asset Filters | 0 | 2 | 2 |
| Orgs Assets | 0 | 2 | 2 |
| Orgs CRL | 0 | 1 | 1 |
| Orgs Cert | 0 | 2 | 2 |
| Orgs Clients - NAC | 2 | 2 | 4 |
| Orgs Clients - Wan | 0 | 4 | 4 |
| Orgs Clients - Wired | 1 | 1 | 2 |
| Orgs Clients - Wireless | 1 | 5 | 6 |
| Orgs Device Profiles | 1 | 1 | 2 |
| Orgs Devices | 2 | 8 | 10 |
| Orgs Devices - AOS | 0 | 1 | 1 |
| Orgs Devices - Others | 0 | 4 | 4 |
| Orgs Devices - SSR | 0 | 2 | 2 |
| Orgs EVPN Topologies | 0 | 2 | 2 |
| Orgs Events | 1 | 2 | 3 |
| Orgs Gateway Templates | 2 | 0 | 2 |
| Orgs Guests | 1 | 3 | 4 |
| Orgs IDP Profiles | 0 | 2 | 2 |
| Orgs Integration Cradlepoint | 0 | 1 | 1 |
| Orgs Integration JSE | 0 | 2 | 2 |
| Orgs Integration SkyATP | 0 | 1 | 1 |
| Orgs Integration Zscaler | 0 | 1 | 1 |
| Orgs Inventory | 1 | 2 | 3 |
| Orgs JSI | 2 | 7 | 9 |
| Orgs Licenses | 1 | 2 | 3 |
| Orgs Linked Applications | 0 | 1 | 1 |
| Orgs Logs | 1 | 1 | 2 |
| Orgs Marvis | 1 | 0 | 1 |
| Orgs Marvis Invites | 0 | 2 | 2 |
| Orgs MxClusters | 0 | 2 | 2 |
| Orgs MxEdges | 1 | 7 | 8 |
| Orgs MxTunnels | 0 | 2 | 2 |
| Orgs NAC CRL | 0 | 1 | 1 |
| Orgs NAC Fingerprints | 0 | 2 | 2 |
| Orgs NAC Portals | 1 | 4 | 5 |
| Orgs NAC Rules | 1 | 1 | 2 |
| Orgs NAC Tags | 1 | 1 | 2 |
| Orgs Network Templates | 1 | 1 | 2 |
| Orgs Networks | 1 | 1 | 2 |
| Orgs Premium Analytics | 0 | 1 | 1 |
| Orgs Psk Portals | 0 | 5 | 5 |
| Orgs Psks | 1 | 1 | 2 |
| Orgs RF Templates | 1 | 1 | 2 |
| Orgs SCEP | 0 | 2 | 2 |
| Orgs SDK Invites | 0 | 3 | 3 |
| Orgs SDK Templates | 0 | 2 | 2 |
| Orgs SLEs | 2 | 0 | 2 |
| Orgs SSO | 1 | 4 | 5 |
| Orgs SSO Roles | 0 | 2 | 2 |
| Orgs SecIntel Profiles | 1 | 1 | 2 |
| Orgs Security Policies | 1 | 1 | 2 |
| Orgs Service Policies | 1 | 1 | 2 |
| Orgs Services | 1 | 1 | 2 |
| Orgs Setting | 0 | 1 | 1 |
| Orgs Site Templates | 2 | 0 | 2 |
| Orgs Sitegroups | 0 | 2 | 2 |
| Orgs Sites | 1 | 2 | 3 |
| Orgs Stats | 0 | 1 | 1 |
| Orgs Stats - Assets | 1 | 2 | 3 |
| Orgs Stats - BGP Peers | 1 | 1 | 2 |
| Orgs Stats - Devices | 1 | 0 | 1 |
| Orgs Stats - MxEdges | 2 | 0 | 2 |
| Orgs Stats - Ospf | 1 | 1 | 2 |
| Orgs Stats - Other Devices | 0 | 1 | 1 |
| Orgs Stats - Ports | 1 | 1 | 2 |
| Orgs Stats - Sites | 1 | 0 | 1 |
| Orgs Stats - Tunnels | 1 | 1 | 2 |
| Orgs Stats - VPN Peers | 1 | 1 | 2 |
| Orgs Tickets | 2 | 2 | 4 |
| Orgs UI Settings | 0 | 2 | 2 |
| Orgs User MACs | 0 | 3 | 3 |
| Orgs VPNs | 1 | 1 | 2 |
| Orgs Vars | 0 | 1 | 1 |
| Orgs WLAN Templates | 1 | 1 | 2 |
| Orgs Webhooks | 1 | 3 | 4 |
| Orgs Wlans | 1 | 1 | 2 |
| Orgs WxRules | 0 | 2 | 2 |
| Orgs WxTags | 0 | 4 | 4 |
| Orgs WxTunnels | 0 | 2 | 2 |
| Self API Token | 0 | 2 | 2 |
| Self Account | 1 | 3 | 4 |
| Self Alarms | 0 | 1 | 1 |
| Self Audit Logs | 1 | 0 | 1 |
| Self MFA | 0 | 1 | 1 |
| Self OAuth2 | 0 | 1 | 1 |
| Sites | 1 | 0 | 1 |
| Sites AP Templates | 0 | 1 | 1 |
| Sites Advanced Anti Malware Profiles | 0 | 1 | 1 |
| Sites Alarms | 0 | 2 | 2 |
| Sites Anomaly | 3 | 0 | 3 |
| Sites Antivirus Profiles | 0 | 1 | 1 |
| Sites Applications | 0 | 1 | 1 |
| Sites Asset Filters | 0 | 2 | 2 |
| Sites Assets | 0 | 2 | 2 |
| Sites Beacons | 1 | 1 | 2 |
| Sites Clients - NAC | 0 | 4 | 4 |
| Sites Clients - Wan | 0 | 4 | 4 |
| Sites Clients - Wired | 1 | 1 | 2 |
| Sites Clients - Wireless | 2 | 5 | 7 |
| Sites Device Profiles | 0 | 1 | 1 |
| Sites Devices | 2 | 9 | 11 |
| Sites Devices - Others | 0 | 3 | 3 |
| Sites Devices - WAN Cluster | 1 | 0 | 1 |
| Sites Devices - Wired - Virtual Chassis | 1 | 0 | 1 |
| Sites Devices - Wireless | 0 | 2 | 2 |
| Sites EVPN Topologies | 0 | 2 | 2 |
| Sites Events | 0 | 3 | 3 |
| Sites Gateway Templates | 1 | 0 | 1 |
| Sites Guests | 0 | 5 | 5 |
| Sites IDP Profiles | 0 | 1 | 1 |
| Sites Insights | 3 | 3 | 6 |
| Sites JSE | 0 | 1 | 1 |
| Sites Licenses | 0 | 1 | 1 |
| Sites Location | 0 | 3 | 3 |
| Sites Map Stacks | 0 | 1 | 1 |
| Sites Maps | 2 | 0 | 2 |
| Sites Maps - Auto-Zone | 0 | 1 | 1 |
| Sites Maps - Auto-placement | 0 | 2 | 2 |
| Sites MxEdges | 0 | 4 | 4 |
| Sites Network Templates | 0 | 1 | 1 |
| Sites Networks | 1 | 0 | 1 |
| Sites Psks | 0 | 2 | 2 |
| Sites RF Templates | 0 | 1 | 1 |
| Sites RRM | 0 | 4 | 4 |
| Sites RSSI Zones | 0 | 2 | 2 |
| Sites Rfdiags | 0 | 3 | 3 |
| Sites Rogues | 2 | 3 | 5 |
| Sites SLEs | 0 | 17 | 17 |
| Sites SecIntel Profiles | 0 | 1 | 1 |
| Sites Service Policies | 1 | 0 | 1 |
| Sites Services | 0 | 3 | 3 |
| Sites Setting | 1 | 1 | 2 |
| Sites Site Templates | 0 | 1 | 1 |
| Sites Skyatp | 0 | 2 | 2 |
| Sites Spectrum Analysis | 0 | 2 | 2 |
| Sites Stats | 0 | 1 | 1 |
| Sites Stats - Apps | 0 | 1 | 1 |
| Sites Stats - Assets | 0 | 7 | 7 |
| Sites Stats - BGP Peers | 0 | 2 | 2 |
| Sites Stats - Beacons | 0 | 1 | 1 |
| Sites Stats - Calls | 0 | 5 | 5 |
| Sites Stats - Clients SDK | 0 | 2 | 2 |
| Sites Stats - Clients Wireless | 1 | 3 | 4 |
| Sites Stats - Devices | 2 | 3 | 5 |
| Sites Stats - Discovered Switches | 0 | 4 | 4 |
| Sites Stats - MxEdges | 0 | 2 | 2 |
| Sites Stats - Ospf | 0 | 2 | 2 |
| Sites Stats - Ports | 1 | 1 | 2 |
| Sites Stats - WxRules | 0 | 1 | 1 |
| Sites Stats - Zones | 0 | 4 | 4 |
| Sites Synthetic Tests | 2 | 0 | 2 |
| Sites UI Settings | 0 | 3 | 3 |
| Sites VPNs | 0 | 1 | 1 |
| Sites WAN Usages | 0 | 2 | 2 |
| Sites Webhooks | 0 | 4 | 4 |
| Sites Wlans | 2 | 1 | 3 |
| Sites WxRules | 0 | 3 | 3 |
| Sites WxTags | 0 | 3 | 3 |
| Sites WxTunnels | 0 | 2 | 2 |
| Sites Zones | 1 | 3 | 4 |
| Sites vBeacons | 1 | 1 | 2 |
| Utilities Common | 0 | 1 | 1 |
| Utilities PCAPs | 2 | 2 | 4 |
| Utilities Upgrade | 5 | 7 | 12 |

## Missing Endpoints

### Admins

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getAdminRegistrationInfo` | `/api/v1/register/recaptcha` | getAdminRegistrationInfo | `mist-get-admin-registration-info` |

### Admins Login - OAuth2

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOauth2AuthorizationUrlForLogin` | `/api/v1/login/oauth/{provider}` | getOauth2AuthorizationUrlForLogin | `mist-get-oauth2-authorization-url-for-login` |

### Constants Definitions

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `listApChannels` | `/api/v1/const/ap_channels` | listApChannels | `mist-list-ap-channels` |
| `listApLEslVersions` | `/api/v1/const/ap_esl_versions` | listApLEslVersions | `mist-list-ap-l-esl-versions` |
| `listApLedDefinition` | `/api/v1/const/ap_led_status` | listApLedDefinition | `mist-list-ap-led-definition` |
| `listAppCategoryDefinitions` | `/api/v1/const/app_categories` | listAppCategoryDefinitions | `mist-list-app-category-definitions` |
| `listAppSubCategoryDefinitions` | `/api/v1/const/app_subcategories` | listAppSubCategoryDefinitions | `mist-list-app-sub-category-definitions` |
| `listApplications` | `/api/v1/const/applications` | listApplications | `mist-list-applications` |
| `listCountryCodes` | `/api/v1/const/countries` | listCountryCodes | `mist-list-country-codes` |
| `listFingerprintTypes` | `/api/v1/const/fingerprint_types` | listFingerprintTypes | `mist-list-fingerprint-types` |
| `listGatewayApplications` | `/api/v1/const/gateway_applications` | listGatewayApplications | `mist-list-gateway-applications` |
| `listLicenseTypes` | `/api/v1/const/license_types` | listLicenseTypes | `mist-list-license-types` |
| `listMarvisClientVersions` | `/api/v1/const/marvisclient_versions` | listMarvisClientVersions | `mist-list-marvis-client-versions` |
| `listSiteLanguages` | `/api/v1/const/languages` | listSiteLanguages | `mist-list-site-languages` |
| `listStates` | `/api/v1/const/states` | listStates | `mist-list-states` |
| `listTrafficTypes` | `/api/v1/const/traffic_types` | listTrafficTypes | `mist-list-traffic-types` |
| `listWebhookTopics` | `/api/v1/const/webhook_topics` | listWebhookTopics | `mist-list-webhook-topics` |

### Constants Events

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `listAlarmDefinitions` | `/api/v1/const/alarm_defs` | listAlarmDefinitions | `mist-list-alarm-definitions` |
| `listClientEventsDefinitions` | `/api/v1/const/client_events` | listClientEventsDefinitions | `mist-list-client-events-definitions` |
| `listDeviceEventsDefinitions` | `/api/v1/const/device_events` | listDeviceEventsDefinitions | `mist-list-device-events-definitions` |
| `listMxEdgeEventsDefinitions` | `/api/v1/const/mxedge_events` | listMxEdgeEventsDefinitions | `mist-list-mx-edge-events-definitions` |
| `listNacEventsDefinitions` | `/api/v1/const/nac_events` | listNacEventsDefinitions | `mist-list-nac-events-definitions` |
| `listOtherDeviceEventsDefinitions` | `/api/v1/const/otherdevice_events` | listOtherDeviceEventsDefinitions | `mist-list-other-device-events-definitions` |
| `listSystemEventsDefinitions` | `/api/v1/const/system_events` | listSystemEventsDefinitions | `mist-list-system-events-definitions` |

### Constants Models

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getGatewayDefaultConfig` | `/api/v1/const/default_gateway_config` | getGatewayDefaultConfig | `mist-get-gateway-default-config` |
| `listDeviceModels` | `/api/v1/const/device_models` | listDeviceModels | `mist-list-device-models` |
| `listMxEdgeModels` | `/api/v1/const/mxedge_models` | listMxEdgeModels | `mist-list-mx-edge-models` |
| `listSupportedOtherDeviceModels` | `/api/v1/const/otherdevice_models` | listSupportedOtherDeviceModels | `mist-list-supported-other-device-models` |

### Installer

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getInstallerDeviceVirtualChassis` | `/api/v1/installer/orgs/{org_id}/devices/{fpc0_mac}/vc` | getInstallerDeviceVirtualChassis | `mist-get-installer-device-virtual-chassis` |
| `listInstallerAlarmTemplates` | `/api/v1/installer/orgs/{org_id}/alarmtemplates` | listInstallerAlarmTemplates | `mist-list-installer-alarm-templates` |
| `listInstallerDeviceProfiles` | `/api/v1/installer/orgs/{org_id}/deviceprofiles` | listInstallerDeviceProfiles | `mist-list-installer-device-profiles` |
| `listInstallerListOfRecentlyClaimedDevices` | `/api/v1/installer/orgs/{org_id}/devices` | listInstallerListOfRecentlyClaimedDevices | `mist-list-installer-list-of-recently-claimed-devices` |
| `listInstallerMaps` | `/api/v1/installer/orgs/{org_id}/sites/{site_name}/maps` | listInstallerMaps | `mist-list-installer-maps` |
| `listInstallerRfTemplatesNames` | `/api/v1/installer/orgs/{org_id}/rftemplates` | listInstallerRfTemplatesNames | `mist-list-installer-rf-templates-names` |
| `listInstallerSiteGroups` | `/api/v1/installer/orgs/{org_id}/sitegroups` | listInstallerSiteGroups | `mist-list-installer-site-groups` |
| `listInstallerSites` | `/api/v1/installer/orgs/{org_id}/sites` | listInstallerSites | `mist-list-installer-sites` |
| `optimizeInstallerRrm` | `/api/v1/installer/sites/{site_name}/optimize` | optimizeInstallerRrm | `mist-optimize-installer-rrm` |

### MSPs

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getMspDetails` | `/api/v1/msps/{msp_id}` | getMspDetails | `mist-get-msp-details` |
| `searchMspOrgGroup` | `/api/v1/msps/{msp_id}/search` | searchMspOrgGroup | `mist-search-msp-org-group` |

### MSPs Admins

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getMspAdmin` | `/api/v1/msps/{msp_id}/admins/{admin_id}` | getMspAdmin | `mist-get-msp-admin` |
| `listMspAdmins` | `/api/v1/msps/{msp_id}/admins` | listMspAdmins | `mist-list-msp-admins` |

### MSPs Inventory

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getMspInventoryByMac` | `/api/v1/msps/{msp_id}/inventory/{device_mac}` | getMspInventoryByMac | `mist-get-msp-inventory-by-mac` |

### MSPs Licenses

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `listMspLicenses` | `/api/v1/msps/{msp_id}/licenses` | listMspLicenses | `mist-list-msp-licenses` |
| `listMspOrgLicenses` | `/api/v1/msps/{msp_id}/stats/licenses` | listMspOrgLicenses | `mist-list-msp-org-licenses` |

### MSPs Logs

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countMspAuditLogs` | `/api/v1/msps/{msp_id}/logs/count` | countMspAuditLogs | `mist-count-msp-audit-logs` |
| `listMspAuditLogs` | `/api/v1/msps/{msp_id}/logs` | listMspAuditLogs | `mist-list-msp-audit-logs` |

### MSPs Marvis

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countMspsMarvisActions` | `/api/v1/msps/{msp_id}/suggestion/count` | countMspsMarvisActions | `mist-count-msps-marvis-actions` |

### MSPs Org Groups

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getMspOrgGroup` | `/api/v1/msps/{msp_id}/orggroups/{orggroup_id}` | getMspOrgGroup | `mist-get-msp-org-group` |
| `listMspOrgGroups` | `/api/v1/msps/{msp_id}/orggroups` | listMspOrgGroups | `mist-list-msp-org-groups` |

### MSPs Orgs

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getMspOrg` | `/api/v1/msps/{msp_id}/orgs/{org_id}` | getMspOrg | `mist-get-msp-org` |
| `listMspOrgStats` | `/api/v1/msps/{msp_id}/stats/orgs` | listMspOrgStats | `mist-list-msp-org-stats` |
| `listMspOrgs` | `/api/v1/msps/{msp_id}/orgs` | listMspOrgs | `mist-list-msp-orgs` |
| `searchMspOrgs` | `/api/v1/msps/{msp_id}/orgs/search` | searchMspOrgs | `mist-search-msp-orgs` |

### MSPs SLEs

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getMspSle` | `/api/v1/msps/{msp_id}/insights/{metric}` | getMspSle | `mist-get-msp-sle` |

### MSPs SSO

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `downloadMspSamlMetadata` | `/api/v1/msps/{msp_id}/ssos/{sso_id}/metadata.xml` | downloadMspSamlMetadata | `mist-download-msp-saml-metadata` |
| `getMspSamlMetadata` | `/api/v1/msps/{msp_id}/ssos/{sso_id}/metadata` | getMspSamlMetadata | `mist-get-msp-saml-metadata` |
| `getMspSso` | `/api/v1/msps/{msp_id}/ssos/{sso_id}` | getMspSso | `mist-get-msp-sso` |
| `listMspSsoLatestFailures` | `/api/v1/msps/{msp_id}/ssos/{sso_id}/failures` | listMspSsoLatestFailures | `mist-list-msp-sso-latest-failures` |
| `listMspSsos` | `/api/v1/msps/{msp_id}/ssos` | listMspSsos | `mist-list-msp-ssos` |

### MSPs SSO Roles

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `listMspSsoRoles` | `/api/v1/msps/{msp_id}/ssoroles` | listMspSsoRoles | `mist-list-msp-sso-roles` |

### MSPs Tickets

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countMspTickets` | `/api/v1/msps/{msp_id}/tickets/count` | countMspTickets | `mist-count-msp-tickets` |
| `listMspTickets` | `/api/v1/msps/{msp_id}/tickets` | listMspTickets | `mist-list-msp-tickets` |

### Orgs AP Templates

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgAptemplate` | `/api/v1/orgs/{org_id}/aptemplates/{aptemplate_id}` | getOrgAptemplate | `mist-get-org-aptemplate` |

### Orgs API Tokens

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgApiToken` | `/api/v1/orgs/{org_id}/apitokens/{apitoken_id}` | getOrgApiToken | `mist-get-org-api-token` |

### Orgs Advanced Anti Malware Profiles

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgAAMWProfile` | `/api/v1/orgs/{org_id}/aamwprofiles/{aamwprofile_id}` | getOrgAAMWProfile | `mist-get-org-a-a-m-w-profile` |
| `listOrgAAMWProfiles` | `/api/v1/orgs/{org_id}/aamwprofiles` | listOrgAAMWProfiles | `mist-list-org-a-a-m-w-profiles` |

### Orgs Alarm Templates

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgAlarmTemplate` | `/api/v1/orgs/{org_id}/alarmtemplates/{alarmtemplate_id}` | getOrgAlarmTemplate | `mist-get-org-alarm-template` |
| `listOrgSuppressedAlarms` | `/api/v1/orgs/{org_id}/alarmtemplates/suppress` | listOrgSuppressedAlarms | `mist-list-org-suppressed-alarms` |

### Orgs Alarms

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgAlarms` | `/api/v1/orgs/{org_id}/alarms/count` | countOrgAlarms | `mist-count-org-alarms` |

### Orgs Antivirus Profiles

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgAntivirusProfile` | `/api/v1/orgs/{org_id}/avprofiles/{avprofile_id}` | getOrgAntivirusProfile | `mist-get-org-antivirus-profile` |
| `listOrgAntivirusProfiles` | `/api/v1/orgs/{org_id}/avprofiles` | listOrgAntivirusProfiles | `mist-list-org-antivirus-profiles` |

### Orgs Asset Filters

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgAssetFilter` | `/api/v1/orgs/{org_id}/assetfilters/{assetfilter_id}` | getOrgAssetFilter | `mist-get-org-asset-filter` |
| `listOrgAssetFilters` | `/api/v1/orgs/{org_id}/assetfilters` | listOrgAssetFilters | `mist-list-org-asset-filters` |

### Orgs Assets

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgAsset` | `/api/v1/orgs/{org_id}/assets/{asset_id}` | getOrgAsset | `mist-get-org-asset` |
| `listOrgAssets` | `/api/v1/orgs/{org_id}/assets` | listOrgAssets | `mist-list-org-assets` |

### Orgs CRL

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgCrlFile` | `/api/v1/orgs/{org_id}/crl` | getOrgCrlFile | `mist-get-org-crl-file` |

### Orgs Cert

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgSslProxyCert` | `/api/v1/orgs/{org_id}/ssl_proxy_cert` | getOrgSslProxyCert | `mist-get-org-ssl-proxy-cert` |
| `listOrgCertificates` | `/api/v1/orgs/{org_id}/cert` | listOrgCertificates | `mist-list-org-certificates` |

### Orgs Clients - NAC

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgNacClientEvents` | `/api/v1/orgs/{org_id}/nac_clients/events/count` | countOrgNacClientEvents | `mist-count-org-nac-client-events` |
| `countOrgNacClients` | `/api/v1/orgs/{org_id}/nac_clients/count` | countOrgNacClients | `mist-count-org-nac-clients` |

### Orgs Clients - Wan

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgWanClientEvents` | `/api/v1/orgs/{org_id}/wan_client/events/count` | countOrgWanClientEvents | `mist-count-org-wan-client-events` |
| `countOrgWanClients` | `/api/v1/orgs/{org_id}/wan_clients/count` | countOrgWanClients | `mist-count-org-wan-clients` |
| `searchOrgWanClientEvents` | `/api/v1/orgs/{org_id}/wan_clients/events/search` | searchOrgWanClientEvents | `mist-search-org-wan-client-events` |
| `searchOrgWanClients` | `/api/v1/orgs/{org_id}/wan_clients/search` | searchOrgWanClients | `mist-search-org-wan-clients` |

### Orgs Clients - Wired

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgWiredClients` | `/api/v1/orgs/{org_id}/wired_clients/count` | countOrgWiredClients | `mist-count-org-wired-clients` |

### Orgs Clients - Wireless

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgWirelessClientEvents` | `/api/v1/orgs/{org_id}/clients/events/count` | countOrgWirelessClientEvents | `mist-count-org-wireless-client-events` |
| `countOrgWirelessClients` | `/api/v1/orgs/{org_id}/clients/count` | countOrgWirelessClients | `mist-count-org-wireless-clients` |
| `countOrgWirelessClientsSessions` | `/api/v1/orgs/{org_id}/clients/sessions/count` | countOrgWirelessClientsSessions | `mist-count-org-wireless-clients-sessions` |
| `searchOrgWirelessClientEvents` | `/api/v1/orgs/{org_id}/clients/events/search` | searchOrgWirelessClientEvents | `mist-search-org-wireless-client-events` |
| `searchOrgWirelessClientSessions` | `/api/v1/orgs/{org_id}/clients/sessions/search` | searchOrgWirelessClientSessions | `mist-search-org-wireless-client-sessions` |

### Orgs Device Profiles

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgDeviceProfile` | `/api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}` | getOrgDeviceProfile | `mist-get-org-device-profile` |

### Orgs Devices

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgDeviceEvents` | `/api/v1/orgs/{org_id}/devices/events/count` | countOrgDeviceEvents | `mist-count-org-device-events` |
| `countOrgDeviceLastConfigs` | `/api/v1/orgs/{org_id}/devices/last_config/count` | countOrgDeviceLastConfigs | `mist-count-org-device-last-configs` |
| `countOrgDevices` | `/api/v1/orgs/{org_id}/devices/count` | countOrgDevices | `mist-count-org-devices` |
| `getOrgJuniperDevicesCommand` | `/api/v1/orgs/{org_id}/ocdevices/outbound_ssh_cmd` | getOrgJuniperDevicesCommand | `mist-get-org-juniper-devices-command` |
| `listOrgApsMacs` | `/api/v1/orgs/{org_id}/devices/radio_macs` | listOrgApsMacs | `mist-list-org-aps-macs` |
| `listOrgDevicesSummary` | `/api/v1/orgs/{org_id}/devices/summary` | listOrgDevicesSummary | `mist-list-org-devices-summary` |
| `searchOrgDeviceLastConfigs` | `/api/v1/orgs/{org_id}/devices/last_config/search` | searchOrgDeviceLastConfigs | `mist-search-org-device-last-configs` |
| `searchOrgDevices` | `/api/v1/orgs/{org_id}/devices/search` | searchOrgDevices | `mist-search-org-devices` |

### Orgs Devices - AOS

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgAosRegisterCmd` | `/api/v1/orgs/{org_id}/aos/register_cmd` | getOrgAosRegisterCmd | `mist-get-org-aos-register-cmd` |

### Orgs Devices - Others

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgOtherDeviceEvents` | `/api/v1/orgs/{org_id}/otherdevices/events/count` | countOrgOtherDeviceEvents | `mist-count-org-other-device-events` |
| `getOrgOtherDevice` | `/api/v1/orgs/{org_id}/otherdevices/{device_mac}` | getOrgOtherDevice | `mist-get-org-other-device` |
| `listOrgOtherDevices` | `/api/v1/orgs/{org_id}/otherdevices` | listOrgOtherDevices | `mist-list-org-other-devices` |
| `searchOrgOtherDeviceEvents` | `/api/v1/orgs/{org_id}/otherdevices/events/search` | searchOrgOtherDeviceEvents | `mist-search-org-other-device-events` |

### Orgs Devices - SSR

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrg128TRegistrationCommands` | `/api/v1/orgs/{org_id}/128routers/register_cmd` | getOrg128TRegistrationCommands | `mist-get-org128-t-registration-commands` |
| `getOrgSsrRegistrationCommands` | `/api/v1/orgs/{org_id}/ssr/register_cmd` | getOrgSsrRegistrationCommands | `mist-get-org-ssr-registration-commands` |

### Orgs EVPN Topologies

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgEvpnTopology` | `/api/v1/orgs/{org_id}/evpn_topologies/{evpn_topology_id}` | getOrgEvpnTopology | `mist-get-org-evpn-topology` |
| `listOrgEvpnTopologies` | `/api/v1/orgs/{org_id}/evpn_topologies` | listOrgEvpnTopologies | `mist-list-org-evpn-topologies` |

### Orgs Events

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgSystemEvents` | `/api/v1/orgs/{org_id}/events/system/count` | countOrgSystemEvents | `mist-count-org-system-events` |
| `searchOrgSystemEvents` | `/api/v1/orgs/{org_id}/events/system/search` | searchOrgSystemEvents | `mist-search-org-system-events` |

### Orgs Guests

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgGuestAuthorizations` | `/api/v1/orgs/{org_id}/guests/count` | countOrgGuestAuthorizations | `mist-count-org-guest-authorizations` |
| `getOrgGuestAuthorization` | `/api/v1/orgs/{org_id}/guests/{guest_mac}` | getOrgGuestAuthorization | `mist-get-org-guest-authorization` |
| `listOrgGuestAuthorizations` | `/api/v1/orgs/{org_id}/guests` | listOrgGuestAuthorizations | `mist-list-org-guest-authorizations` |

### Orgs IDP Profiles

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgIdpProfile` | `/api/v1/orgs/{org_id}/idpprofiles/{idpprofile_id}` | getOrgIdpProfile | `mist-get-org-idp-profile` |
| `listOrgIdpProfiles` | `/api/v1/orgs/{org_id}/idpprofiles` | listOrgIdpProfiles | `mist-list-org-idp-profiles` |

### Orgs Integration Cradlepoint

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `testOrgCradlepointConnection` | `/api/v1/orgs/{org_id}/setting/cradlepoint/setup` | testOrgCradlepointConnection | `mist-test-org-cradlepoint-connection` |

### Orgs Integration JSE

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgJseInfo` | `/api/v1/orgs/{org_id}/setting/jse/info` | getOrgJseInfo | `mist-get-org-jse-info` |
| `getOrgJseIntegration` | `/api/v1/orgs/{org_id}/setting/jse/setup` | getOrgJseIntegration | `mist-get-org-jse-integration` |

### Orgs Integration SkyATP

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgSkyAtpIntegration` | `/api/v1/orgs/{org_id}/setting/skyatp/setup` | getOrgSkyAtpIntegration | `mist-get-org-sky-atp-integration` |

### Orgs Integration Zscaler

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgZscalerIntegration` | `/api/v1/orgs/{org_id}/setting/zscaler/setup` | getOrgZscalerIntegration | `mist-get-org-zscaler-integration` |

### Orgs Inventory

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgInventory` | `/api/v1/orgs/{org_id}/inventory/count` | countOrgInventory | `mist-count-org-inventory` |
| `searchOrgInventory` | `/api/v1/orgs/{org_id}/inventory/search` | searchOrgInventory | `mist-search-org-inventory` |

### Orgs JSI

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `adoptOrgJsiDevice` | `/api/v1/orgs/{org_id}/jsi/devices/outbound_ssh_cmd` | adoptOrgJsiDevice | `mist-adopt-org-jsi-device` |
| `countOrgJsiAssetsAndContracts` | `/api/v1/orgs/{org_id}/jsi/inventory/count` | countOrgJsiAssetsAndContracts | `mist-count-org-jsi-assets-and-contracts` |
| `countOrgJsiPbn` | `/api/v1/orgs/{org_id}/jsi/pbn/count` | countOrgJsiPbn | `mist-count-org-jsi-pbn` |
| `countOrgJsiSirt` | `/api/v1/orgs/{org_id}/jsi/sirt/count` | countOrgJsiSirt | `mist-count-org-jsi-sirt` |
| `listOrgJsiDevices` | `/api/v1/orgs/{org_id}/jsi/devices` | listOrgJsiDevices | `mist-list-org-jsi-devices` |
| `listOrgJsiPastPurchases` | `/api/v1/orgs/{org_id}/jsi/inventory` | listOrgJsiPastPurchases | `mist-list-org-jsi-past-purchases` |
| `searchOrgJsiAssetsAndContracts` | `/api/v1/orgs/{org_id}/jsi/inventory/search` | searchOrgJsiAssetsAndContracts | `mist-search-org-jsi-assets-and-contracts` |

### Orgs Licenses

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `GetOrgLicenseAsyncClaimStatus` | `/api/v1/orgs/{org_id}/claim/status` | GetOrgLicenseAsyncClaimStatus | `mist-get-org-license-async-claim-status` |
| `getOrgLicensesSummary` | `/api/v1/orgs/{org_id}/licenses` | getOrgLicensesSummary | `mist-get-org-licenses-summary` |

### Orgs Linked Applications

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgOauthAppLinkedStatus` | `/api/v1/orgs/{org_id}/setting/{app_name}/link_accounts` | getOrgOauthAppLinkedStatus | `mist-get-org-oauth-app-linked-status` |

### Orgs Logs

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgAuditLogs` | `/api/v1/orgs/{org_id}/logs/count` | countOrgAuditLogs | `mist-count-org-audit-logs` |

### Orgs Marvis Invites

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgMarvisClientInvite` | `/api/v1/orgs/{org_id}/marvisinvites/{marvisinvite_id}` | getOrgMarvisClientInvite | `mist-get-org-marvis-client-invite` |
| `listOrgMarvisClientInvites` | `/api/v1/orgs/{org_id}/marvisinvites` | listOrgMarvisClientInvites | `mist-list-org-marvis-client-invites` |

### Orgs MxClusters

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgMxEdgeCluster` | `/api/v1/orgs/{org_id}/mxclusters/{mxcluster_id}` | getOrgMxEdgeCluster | `mist-get-org-mx-edge-cluster` |
| `listOrgMxEdgeClusters` | `/api/v1/orgs/{org_id}/mxclusters` | listOrgMxEdgeClusters | `mist-list-org-mx-edge-clusters` |

### Orgs MxEdges

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgMxEdges` | `/api/v1/orgs/{org_id}/mxedges/count` | countOrgMxEdges | `mist-count-org-mx-edges` |
| `countOrgSiteMxEdgeEvents` | `/api/v1/orgs/{org_id}/mxedges/events/count` | countOrgSiteMxEdgeEvents | `mist-count-org-site-mx-edge-events` |
| `getOrgMxEdge` | `/api/v1/orgs/{org_id}/mxedges/{mxedge_id}` | getOrgMxEdge | `mist-get-org-mx-edge` |
| `getOrgMxEdgeUpgradeInfo` | `/api/v1/orgs/{org_id}/mxedges/versions` | getOrgMxEdgeUpgradeInfo | `mist-get-org-mx-edge-upgrade-info` |
| `getOrgMxEdgeVmParams` | `/api/v1/orgs/{org_id}/mxedges/{mxedge_id}/vm_params` | getOrgMxEdgeVmParams | `mist-get-org-mx-edge-vm-params` |
| `searchOrgMistEdgeEvents` | `/api/v1/orgs/{org_id}/mxedges/events/search` | searchOrgMistEdgeEvents | `mist-search-org-mist-edge-events` |
| `searchOrgMxEdges` | `/api/v1/orgs/{org_id}/mxedges/search` | searchOrgMxEdges | `mist-search-org-mx-edges` |

### Orgs MxTunnels

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgMxTunnel` | `/api/v1/orgs/{org_id}/mxtunnels/{mxtunnel_id}` | getOrgMxTunnel | `mist-get-org-mx-tunnel` |
| `listOrgMxTunnels` | `/api/v1/orgs/{org_id}/mxtunnels` | listOrgMxTunnels | `mist-list-org-mx-tunnels` |

### Orgs NAC CRL

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgNacCrl` | `/api/v1/orgs/{org_id}/setting/mist_nac_crls` | getOrgNacCrl | `mist-get-org-nac-crl` |

### Orgs NAC Fingerprints

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgClientFingerprints` | `/api/v1/sites/{site_id}/insights/fingerprints/count` | countOrgClientFingerprints | `mist-count-org-client-fingerprints` |
| `searchOrgClientFingerprints` | `/api/v1/sites/{site_id}/insights/fingerprints/search` | searchOrgClientFingerprints | `mist-search-org-client-fingerprints` |

### Orgs NAC Portals

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `downloadOrgNacPortalSamlMetadata` | `/api/v1/orgs/{org_id}/nacportals/{nacportal_id}/saml_metadata.xml` | downloadOrgNacPortalSamlMetadata | `mist-download-org-nac-portal-saml-metadata` |
| `getOrgNacPortal` | `/api/v1/orgs/{org_id}/nacportals/{nacportal_id}` | getOrgNacPortal | `mist-get-org-nac-portal` |
| `getOrgNacPortalSamlMetadata` | `/api/v1/orgs/{org_id}/nacportals/{nacportal_id}/saml_metadata` | getOrgNacPortalSamlMetadata | `mist-get-org-nac-portal-saml-metadata` |
| `listOrgNacPortalSsoLatestFailures` | `/api/v1/orgs/{org_id}/nacportals/{nacportal_id}/failures` | listOrgNacPortalSsoLatestFailures | `mist-list-org-nac-portal-sso-latest-failures` |

### Orgs NAC Rules

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgNacRule` | `/api/v1/orgs/{org_id}/nacrules/{nacrule_id}` | getOrgNacRule | `mist-get-org-nac-rule` |

### Orgs NAC Tags

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgNacTag` | `/api/v1/orgs/{org_id}/nactags/{nactag_id}` | getOrgNacTag | `mist-get-org-nac-tag` |

### Orgs Network Templates

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgNetworkTemplate` | `/api/v1/orgs/{org_id}/networktemplates/{networktemplate_id}` | getOrgNetworkTemplate | `mist-get-org-network-template` |

### Orgs Networks

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgNetwork` | `/api/v1/orgs/{org_id}/networks/{network_id}` | getOrgNetwork | `mist-get-org-network` |

### Orgs Premium Analytics

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `listOrgPmaDashboards` | `/api/v1/orgs/{org_id}/pma/dashboards` | listOrgPmaDashboards | `mist-list-org-pma-dashboards` |

### Orgs Psk Portals

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgPskPortalLogs` | `/api/v1/orgs/{org_id}/pskportals/logs/count` | countOrgPskPortalLogs | `mist-count-org-psk-portal-logs` |
| `getOrgPskPortal` | `/api/v1/orgs/{org_id}/pskportals/{pskportal_id}` | getOrgPskPortal | `mist-get-org-psk-portal` |
| `listOrgPskPortalLogs` | `/api/v1/orgs/{org_id}/pskportals/logs` | listOrgPskPortalLogs | `mist-list-org-psk-portal-logs` |
| `listOrgPskPortals` | `/api/v1/orgs/{org_id}/pskportals` | listOrgPskPortals | `mist-list-org-psk-portals` |
| `searchOrgPskPortalLogs` | `/api/v1/orgs/{org_id}/pskportals/logs/search` | searchOrgPskPortalLogs | `mist-search-org-psk-portal-logs` |

### Orgs Psks

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgPsk` | `/api/v1/orgs/{org_id}/psks/{psk_id}` | getOrgPsk | `mist-get-org-psk` |

### Orgs RF Templates

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgRfTemplate` | `/api/v1/orgs/{org_id}/rftemplates/{rftemplate_id}` | getOrgRfTemplate | `mist-get-org-rf-template` |

### Orgs SCEP

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgMistScep` | `/api/v1/orgs/{org_id}/setting/mist_scep` | getOrgMistScep | `mist-get-org-mist-scep` |
| `listOrgIssuedClientCertificates` | `/api/v1/orgs/{org_id}/setting/mist_scep/client_certs` | listOrgIssuedClientCertificates | `mist-list-org-issued-client-certificates` |

### Orgs SDK Invites

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSdkInvite` | `/api/v1/orgs/{org_id}/sdkinvites/{sdkinvite_id}` | getSdkInvite | `mist-get-sdk-invite` |
| `getSdkInviteQrCode` | `/api/v1/orgs/{org_id}/sdkinvites/{sdkinvite_id}/qrcode` | getSdkInviteQrCode | `mist-get-sdk-invite-qr-code` |
| `listSdkInvites` | `/api/v1/orgs/{org_id}/sdkinvites` | listSdkInvites | `mist-list-sdk-invites` |

### Orgs SDK Templates

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSdkTemplate` | `/api/v1/orgs/{org_id}/sdktemplates/{sdktemplate_id}` | getSdkTemplate | `mist-get-sdk-template` |
| `listSdkTemplates` | `/api/v1/orgs/{org_id}/sdktemplates` | listSdkTemplates | `mist-list-sdk-templates` |

### Orgs SSO

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `downloadOrgSamlMetadata` | `/api/v1/orgs/{org_id}/ssos/{sso_id}/metadata.xml` | downloadOrgSamlMetadata | `mist-download-org-saml-metadata` |
| `getOrgSamlMetadata` | `/api/v1/orgs/{org_id}/ssos/{sso_id}/metadata` | getOrgSamlMetadata | `mist-get-org-saml-metadata` |
| `getOrgSso` | `/api/v1/orgs/{org_id}/ssos/{sso_id}` | getOrgSso | `mist-get-org-sso` |
| `listOrgSsoLatestFailures` | `/api/v1/orgs/{org_id}/ssos/{sso_id}/failures` | listOrgSsoLatestFailures | `mist-list-org-sso-latest-failures` |

### Orgs SSO Roles

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgSsoRole` | `/api/v1/orgs/{org_id}/ssoroles/{ssorole_id}` | getOrgSsoRole | `mist-get-org-sso-role` |
| `listOrgSsoRoles` | `/api/v1/orgs/{org_id}/ssoroles` | listOrgSsoRoles | `mist-list-org-sso-roles` |

### Orgs SecIntel Profiles

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgSecIntelProfile` | `/api/v1/orgs/{org_id}/secintelprofiles/{secintelprofile_id}` | getOrgSecIntelProfile | `mist-get-org-sec-intel-profile` |

### Orgs Security Policies

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgSecPolicy` | `/api/v1/orgs/{org_id}/secpolicies/{secpolicy_id}` | getOrgSecPolicy | `mist-get-org-sec-policy` |

### Orgs Service Policies

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgServicePolicy` | `/api/v1/orgs/{org_id}/servicepolicies/{servicepolicy_id}` | getOrgServicePolicy | `mist-get-org-service-policy` |

### Orgs Services

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgService` | `/api/v1/orgs/{org_id}/services/{service_id}` | getOrgService | `mist-get-org-service` |

### Orgs Setting

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgSettings` | `/api/v1/orgs/{org_id}/setting` | getOrgSettings | `mist-get-org-settings` |

### Orgs Sitegroups

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgSiteGroup` | `/api/v1/orgs/{org_id}/sitegroups/{sitegroup_id}` | getOrgSiteGroup | `mist-get-org-site-group` |
| `listOrgSiteGroups` | `/api/v1/orgs/{org_id}/sitegroups` | listOrgSiteGroups | `mist-list-org-site-groups` |

### Orgs Sites

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgSites` | `/api/v1/orgs/{org_id}/sites/count` | countOrgSites | `mist-count-org-sites` |
| `searchOrgSites` | `/api/v1/orgs/{org_id}/sites/search` | searchOrgSites | `mist-search-org-sites` |

### Orgs Stats

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgStats` | `/api/v1/orgs/{org_id}/stats` | getOrgStats | `mist-get-org-stats` |

### Orgs Stats - Assets

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgAssetsByDistanceField` | `/api/v1/orgs/{org_id}/stats/assets/count` | countOrgAssetsByDistanceField | `mist-count-org-assets-by-distance-field` |
| `listOrgAssetsStats` | `/api/v1/orgs/{org_id}/stats/assets` | listOrgAssetsStats | `mist-list-org-assets-stats` |

### Orgs Stats - BGP Peers

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgBgpStats` | `/api/v1/orgs/{org_id}/stats/bgp_peers/count` | countOrgBgpStats | `mist-count-org-bgp-stats` |

### Orgs Stats - Ospf

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgOspfStats` | `/api/v1/orgs/{org_id}/stats/ospf_peers/count` | countOrgOspfStats | `mist-count-org-ospf-stats` |

### Orgs Stats - Other Devices

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgOtherDeviceStats` | `/api/v1/orgs/{org_id}/stats/otherdevices/{device_mac}` | getOrgOtherDeviceStats | `mist-get-org-other-device-stats` |

### Orgs Stats - Ports

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgSwOrGwPorts` | `/api/v1/orgs/{org_id}/stats/ports/count` | countOrgSwOrGwPorts | `mist-count-org-sw-or-gw-ports` |

### Orgs Stats - Tunnels

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgTunnelsStats` | `/api/v1/orgs/{org_id}/stats/tunnels/count` | countOrgTunnelsStats | `mist-count-org-tunnels-stats` |

### Orgs Stats - VPN Peers

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgPeerPathStats` | `/api/v1/orgs/{org_id}/stats/vpn_peers/count` | countOrgPeerPathStats | `mist-count-org-peer-path-stats` |

### Orgs Tickets

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `GetOrgTicketAttachment` | `/api/v1/orgs/{org_id}/tickets/{ticket_id}/attachments/{attachment_id}` | GetOrgTicketAttachment | `mist-get-org-ticket-attachment` |
| `countOrgTickets` | `/api/v1/orgs/{org_id}/tickets/count` | countOrgTickets | `mist-count-org-tickets` |

### Orgs UI Settings

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgUiSetting` | `/api/v1/orgs/{org_id}/uisettings/{uisetting_id}` | getOrgUiSetting | `mist-get-org-ui-setting` |
| `listOrgUiSettings` | `/api/v1/orgs/{org_id}/uisettings` | listOrgUiSettings | `mist-list-org-ui-settings` |

### Orgs User MACs

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgUserMacs` | `/api/v1/orgs/{org_id}/usermacs/count` | countOrgUserMacs | `mist-count-org-user-macs` |
| `getOrgUserMac` | `/api/v1/orgs/{org_id}/usermacs/{usermac_id}` | getOrgUserMac | `mist-get-org-user-mac` |
| `searchOrgUserMacs` | `/api/v1/orgs/{org_id}/usermacs/search` | searchOrgUserMacs | `mist-search-org-user-macs` |

### Orgs VPNs

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgVpn` | `/api/v1/orgs/{org_id}/vpns/{vpn_id}` | getOrgVpn | `mist-get-org-vpn` |

### Orgs Vars

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `searchOrgVars` | `/api/v1/orgs/{org_id}/vars/search` | searchOrgVars | `mist-search-org-vars` |

### Orgs WLAN Templates

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgTemplate` | `/api/v1/orgs/{org_id}/templates/{template_id}` | getOrgTemplate | `mist-get-org-template` |

### Orgs Webhooks

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countOrgWebhooksDeliveries` | `/api/v1/orgs/{org_id}/webhooks/{webhook_id}/events/count` | countOrgWebhooksDeliveries | `mist-count-org-webhooks-deliveries` |
| `getOrgWebhook` | `/api/v1/orgs/{org_id}/webhooks/{webhook_id}` | getOrgWebhook | `mist-get-org-webhook` |
| `searchOrgWebhooksDeliveries` | `/api/v1/orgs/{org_id}/webhooks/{webhook_id}/events/search` | searchOrgWebhooksDeliveries | `mist-search-org-webhooks-deliveries` |

### Orgs Wlans

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgWLAN` | `/api/v1/orgs/{org_id}/wlans/{wlan_id}` | getOrgWLAN | `mist-get-org-w-l-a-n` |

### Orgs WxRules

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgWxRule` | `/api/v1/orgs/{org_id}/wxrules/{wxrule_id}` | getOrgWxRule | `mist-get-org-wx-rule` |
| `listOrgWxRules` | `/api/v1/orgs/{org_id}/wxrules` | listOrgWxRules | `mist-list-org-wx-rules` |

### Orgs WxTags

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgApplicationList` | `/api/v1/orgs/{org_id}/wxtags/apps` | getOrgApplicationList | `mist-get-org-application-list` |
| `getOrgCurrentMatchingClientsOfAWxTag` | `/api/v1/orgs/{org_id}/wxtags/{wxtag_id}/clients` | getOrgCurrentMatchingClientsOfAWxTag | `mist-get-org-current-matching-clients-of-a-wx-tag` |
| `getOrgWxTag` | `/api/v1/orgs/{org_id}/wxtags/{wxtag_id}` | getOrgWxTag | `mist-get-org-wx-tag` |
| `listOrgWxTags` | `/api/v1/orgs/{org_id}/wxtags` | listOrgWxTags | `mist-list-org-wx-tags` |

### Orgs WxTunnels

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgWxTunnel` | `/api/v1/orgs/{org_id}/wxtunnels/{wxtunnel_id}` | getOrgWxTunnel | `mist-get-org-wx-tunnel` |
| `listOrgWxTunnels` | `/api/v1/orgs/{org_id}/wxtunnels` | listOrgWxTunnels | `mist-list-org-wx-tunnels` |

### Self API Token

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getApiToken` | `/api/v1/self/apitokens/{apitoken_id}` | getApiToken | `mist-get-api-token` |
| `listApiTokens` | `/api/v1/self/apitokens` | listApiTokens | `mist-list-api-tokens` |

### Self Account

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSelf` | `/api/v1/self` | getSelf | `mist-get-self` |
| `getSelfLoginFailures` | `/api/v1/self/login_failures` | getSelfLoginFailures | `mist-get-self-login-failures` |
| `verifySelfEmail` | `/api/v1/self/update/verify/{token}` | verifySelfEmail | `mist-verify-self-email` |

### Self Alarms

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `listAlarmSubscriptions` | `/api/v1/self/subscriptions` | listAlarmSubscriptions | `mist-list-alarm-subscriptions` |

### Self MFA

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `generateSecretFor2faVerification` | `/api/v1/self/two_factor/token` | generateSecretFor2faVerification | `mist-generate-secret-for2fa-verification` |

### Self OAuth2

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOauth2UrlForLinking` | `/api/v1/self/oauth/{provider}` | getOauth2UrlForLinking | `mist-get-oauth2-url-for-linking` |

### Sites AP Templates

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `listSiteApTemplatesDerived` | `/api/v1/sites/{site_id}/aptemplates/derived` | listSiteApTemplatesDerived | `mist-list-site-ap-templates-derived` |

### Sites Advanced Anti Malware Profiles

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `listSiteAAMWProfilesDerived` | `/api/v1/sites/{site_id}/aamwprofiles/derived` | listSiteAAMWProfilesDerived | `mist-list-site-a-a-m-w-profiles-derived` |

### Sites Alarms

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteAlarms` | `/api/v1/sites/{site_id}/alarms/count` | countSiteAlarms | `mist-count-site-alarms` |
| `searchSiteAlarms` | `/api/v1/sites/{site_id}/alarms/search` | searchSiteAlarms | `mist-search-site-alarms` |

### Sites Antivirus Profiles

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `listSiteAntivirusProfilesDerived` | `/api/v1/sites/{site_id}/avprofiles/derived` | listSiteAntivirusProfilesDerived | `mist-list-site-antivirus-profiles-derived` |

### Sites Applications

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `listSiteApps` | `/api/v1/sites/{site_id}/apps` | listSiteApps | `mist-list-site-apps` |

### Sites Asset Filters

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteAssetFilter` | `/api/v1/sites/{site_id}/assetfilters/{assetfilter_id}` | getSiteAssetFilter | `mist-get-site-asset-filter` |
| `listSiteAssetFilters` | `/api/v1/sites/{site_id}/assetfilters` | listSiteAssetFilters | `mist-list-site-asset-filters` |

### Sites Assets

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteAsset` | `/api/v1/sites/{site_id}/assets/{asset_id}` | getSiteAsset | `mist-get-site-asset` |
| `listSiteAssets` | `/api/v1/sites/{site_id}/assets` | listSiteAssets | `mist-list-site-assets` |

### Sites Beacons

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteBeacon` | `/api/v1/sites/{site_id}/beacons/{beacon_id}` | getSiteBeacon | `mist-get-site-beacon` |

### Sites Clients - NAC

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteNacClientEvents` | `/api/v1/sites/{site_id}/nac_clients/events/count` | countSiteNacClientEvents | `mist-count-site-nac-client-events` |
| `countSiteNacClients` | `/api/v1/sites/{site_id}/nac_clients/count` | countSiteNacClients | `mist-count-site-nac-clients` |
| `searchSiteNacClientEvents` | `/api/v1/sites/{site_id}/nac_clients/events/search` | searchSiteNacClientEvents | `mist-search-site-nac-client-events` |
| `searchSiteNacClients` | `/api/v1/sites/{site_id}/nac_clients/search` | searchSiteNacClients | `mist-search-site-nac-clients` |

### Sites Clients - Wan

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteWanClientEvents` | `/api/v1/sites/{site_id}/wan_client/events/count` | countSiteWanClientEvents | `mist-count-site-wan-client-events` |
| `countSiteWanClients` | `/api/v1/sites/{site_id}/wan_clients/count` | countSiteWanClients | `mist-count-site-wan-clients` |
| `searchSiteWanClientEvents` | `/api/v1/sites/{site_id}/wan_clients/events/search` | searchSiteWanClientEvents | `mist-search-site-wan-client-events` |
| `searchSiteWanClients` | `/api/v1/sites/{site_id}/wan_clients/search` | searchSiteWanClients | `mist-search-site-wan-clients` |

### Sites Clients - Wired

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteWiredClients` | `/api/v1/sites/{site_id}/wired_clients/count` | countSiteWiredClients | `mist-count-site-wired-clients` |

### Sites Clients - Wireless

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteWirelessClientEvents` | `/api/v1/sites/{site_id}/clients/events/count` | countSiteWirelessClientEvents | `mist-count-site-wireless-client-events` |
| `countSiteWirelessClientSessions` | `/api/v1/sites/{site_id}/clients/sessions/count` | countSiteWirelessClientSessions | `mist-count-site-wireless-client-sessions` |
| `countSiteWirelessClients` | `/api/v1/sites/{site_id}/clients/count` | countSiteWirelessClients | `mist-count-site-wireless-clients` |
| `getSiteEventsForClient` | `/api/v1/sites/{site_id}/clients/{client_mac}/events` | getSiteEventsForClient | `mist-get-site-events-for-client` |
| `searchSiteWirelessClientEvents` | `/api/v1/sites/{site_id}/clients/events/search` | searchSiteWirelessClientEvents | `mist-search-site-wireless-client-events` |

### Sites Device Profiles

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `listSiteDeviceProfilesDerived` | `/api/v1/sites/{site_id}/deviceprofiles/derived` | listSiteDeviceProfilesDerived | `mist-list-site-device-profiles-derived` |

### Sites Devices

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteDeviceConfigHistory` | `/api/v1/sites/{site_id}/devices/config_history/count` | countSiteDeviceConfigHistory | `mist-count-site-device-config-history` |
| `countSiteDeviceEvents` | `/api/v1/sites/{site_id}/devices/events/count` | countSiteDeviceEvents | `mist-count-site-device-events` |
| `countSiteDeviceLastConfig` | `/api/v1/sites/{site_id}/devices/last_config/count` | countSiteDeviceLastConfig | `mist-count-site-device-last-config` |
| `countSiteDevices` | `/api/v1/sites/{site_id}/devices/count` | countSiteDevices | `mist-count-site-devices` |
| `exportSiteDevices` | `/api/v1/sites/{site_id}/devices/export` | exportSiteDevices | `mist-export-site-devices` |
| `searchSiteDeviceConfigHistory` | `/api/v1/sites/{site_id}/devices/config_history/search` | searchSiteDeviceConfigHistory | `mist-search-site-device-config-history` |
| `searchSiteDeviceEvents` | `/api/v1/sites/{site_id}/devices/events/search` | searchSiteDeviceEvents | `mist-search-site-device-events` |
| `searchSiteDeviceLastConfigs` | `/api/v1/sites/{site_id}/devices/last_config/search` | searchSiteDeviceLastConfigs | `mist-search-site-device-last-configs` |
| `searchSiteDevices` | `/api/v1/sites/{site_id}/devices/search` | searchSiteDevices | `mist-search-site-devices` |

### Sites Devices - Others

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteOtherDeviceEvents` | `/api/v1/sites/{site_id}/otherdevices/events/count` | countSiteOtherDeviceEvents | `mist-count-site-other-device-events` |
| `listSiteOtherDevices` | `/api/v1/sites/{site_id}/otherdevices` | listSiteOtherDevices | `mist-list-site-other-devices` |
| `searchSiteOtherDeviceEvents` | `/api/v1/sites/{site_id}/otherdevices/events/search` | searchSiteOtherDeviceEvents | `mist-search-site-other-device-events` |

### Sites Devices - Wireless

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteDeviceIotPort` | `/api/v1/sites/{site_id}/devices/{device_id}/iot` | getSiteDeviceIotPort | `mist-get-site-device-iot-port` |
| `listSiteDeviceRadioChannels` | `/api/v1/sites/{site_id}/devices/ap_channels` | listSiteDeviceRadioChannels | `mist-list-site-device-radio-channels` |

### Sites EVPN Topologies

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteEvpnTopology` | `/api/v1/sites/{site_id}/evpn_topologies/{evpn_topology_id}` | getSiteEvpnTopology | `mist-get-site-evpn-topology` |
| `listSiteEvpnTopologies` | `/api/v1/sites/{site_id}/evpn_topologies` | listSiteEvpnTopologies | `mist-list-site-evpn-topologies` |

### Sites Events

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteSystemEvents` | `/api/v1/sites/{site_id}/events/system/count` | countSiteSystemEvents | `mist-count-site-system-events` |
| `listSiteRoamingEvents` | `/api/v1/sites/{site_id}/events/fast_roam` | listSiteRoamingEvents | `mist-list-site-roaming-events` |
| `searchSiteSystemEvents` | `/api/v1/sites/{site_id}/events/system/search` | searchSiteSystemEvents | `mist-search-site-system-events` |

### Sites Guests

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteGuestAuthorizations` | `/api/v1/sites/{site_id}/guests/count` | countSiteGuestAuthorizations | `mist-count-site-guest-authorizations` |
| `getSiteGuestAuthorization` | `/api/v1/sites/{site_id}/guests/{guest_mac}` | getSiteGuestAuthorization | `mist-get-site-guest-authorization` |
| `listSiteAllGuestAuthorizations` | `/api/v1/sites/{site_id}/guests` | listSiteAllGuestAuthorizations | `mist-list-site-all-guest-authorizations` |
| `listSiteAllGuestAuthorizationsDerived` | `/api/v1/sites/{site_id}/guests/derived` | listSiteAllGuestAuthorizationsDerived | `mist-list-site-all-guest-authorizations-derived` |
| `searchSiteGuestAuthorization` | `/api/v1/sites/{site_id}/guests/search` | searchSiteGuestAuthorization | `mist-search-site-guest-authorization` |

### Sites IDP Profiles

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `listSiteIdpProfilesDerived` | `/api/v1/sites/{site_id}/idpprofiles/derived` | listSiteIdpProfilesDerived | `mist-list-site-idp-profiles-derived` |

### Sites Insights

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteInsightMetricsForGateway` | `/api/v1/sites/{site_id}/insights/gateway/{device_id}/stats/{metric}` | getSiteInsightMetricsForGateway | `mist-get-site-insight-metrics-for-gateway` |
| `getSiteInsightMetricsForMxEdge` | `/api/v1/sites/{site_id}/insights/mxedge/{device_mac}/{metric}` | getSiteInsightMetricsForMxEdge | `mist-get-site-insight-metrics-for-mx-edge` |
| `getSiteInsightMetricsForSwitch` | `/api/v1/sites/{site_id}/insights/switch/{device_mac}/{metric}` | getSiteInsightMetricsForSwitch | `mist-get-site-insight-metrics-for-switch` |

### Sites JSE

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteJseInfo` | `/api/v1/sites/{site_id}/setting/jse/info` | getSiteJseInfo | `mist-get-site-jse-info` |

### Sites Licenses

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteLicenseUsage` | `/api/v1/sites/{site_id}/licenses/usages` | getSiteLicenseUsage | `mist-get-site-license-usage` |

### Sites Location

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteBeamCoverageOverview` | `/api/v1/sites/{site_id}/location/coverage` | getSiteBeamCoverageOverview | `mist-get-site-beam-coverage-overview` |
| `getSiteDefaultPlfForModels` | `/api/v1/sites/{site_id}/location/ml/defaults` | getSiteDefaultPlfForModels | `mist-get-site-default-plf-for-models` |
| `getSiteMachineLearningCurrentStat` | `/api/v1/sites/{site_id}/location/ml/current` | getSiteMachineLearningCurrentStat | `mist-get-site-machine-learning-current-stat` |

### Sites Map Stacks

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `listSiteMapStacks` | `/api/v1/sites/{site_id}/mapstacks` | listSiteMapStacks | `mist-list-site-map-stacks` |

### Sites Maps - Auto-Zone

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteMapAutoZoneStatus` | `/api/v1/sites/{site_id}/maps/{map_id}/auto_zones` | getSiteMapAutoZoneStatus | `mist-get-site-map-auto-zone-status` |

### Sites Maps - Auto-placement

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteApAutoOrientation` | `/api/v1/sites/{site_id}/maps/{map_id}/auto_orient` | getSiteApAutoOrientation | `mist-get-site-ap-auto-orientation` |
| `getSiteApAutoPlacement` | `/api/v1/sites/{site_id}/maps/{map_id}/auto_placement` | getSiteApAutoPlacement | `mist-get-site-ap-auto-placement` |

### Sites MxEdges

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteMxEdgeEvents` | `/api/v1/sites/{site_id}/mxedges/events/count` | countSiteMxEdgeEvents | `mist-count-site-mx-edge-events` |
| `getSiteMxEdge` | `/api/v1/sites/{site_id}/mxedges/{mxedge_id}` | getSiteMxEdge | `mist-get-site-mx-edge` |
| `listSiteMxEdges` | `/api/v1/sites/{site_id}/mxedges` | listSiteMxEdges | `mist-list-site-mx-edges` |
| `searchSiteMistEdgeEvents` | `/api/v1/sites/{site_id}/mxedges/events/search` | searchSiteMistEdgeEvents | `mist-search-site-mist-edge-events` |

### Sites Network Templates

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `listSiteNetworkTemplatesDerived` | `/api/v1/sites/{site_id}/networktemplates/derived` | listSiteNetworkTemplatesDerived | `mist-list-site-network-templates-derived` |

### Sites Psks

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSitePsk` | `/api/v1/sites/{site_id}/psks/{psk_id}` | getSitePsk | `mist-get-site-psk` |
| `listSitePsks` | `/api/v1/sites/{site_id}/psks` | listSitePsks | `mist-list-site-psks` |

### Sites RF Templates

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `listSiteRfTemplatesDerived` | `/api/v1/sites/{site_id}/rftemplates/derived` | listSiteRfTemplatesDerived | `mist-list-site-rf-templates-derived` |

### Sites RRM

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteCurrentChannelPlanning` | `/api/v1/sites/{site_id}/rrm/current` | getSiteCurrentChannelPlanning | `mist-get-site-current-channel-planning` |
| `getSiteCurrentRrmConsiderations` | `/api/v1/sites/{site_id}/rrm/current/devices/{device_id}/band/{band}` | getSiteCurrentRrmConsiderations | `mist-get-site-current-rrm-considerations` |
| `listSiteCurrentRrmNeighbors` | `/api/v1/sites/{site_id}/rrm/neighbors/band/{band}` | listSiteCurrentRrmNeighbors | `mist-list-site-current-rrm-neighbors` |
| `listSiteRrmEvents` | `/api/v1/sites/{site_id}/rrm/events` | listSiteRrmEvents | `mist-list-site-rrm-events` |

### Sites RSSI Zones

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteRssiZone` | `/api/v1/sites/{site_id}/rssizones/{rssizone_id}` | getSiteRssiZone | `mist-get-site-rssi-zone` |
| `listSiteRssiZones` | `/api/v1/sites/{site_id}/rssizones` | listSiteRssiZones | `mist-list-site-rssi-zones` |

### Sites Rfdiags

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `downloadSiteRfdiagRecording` | `/api/v1/sites/{site_id}/rfdiags/{rfdiag_id}/download` | downloadSiteRfdiagRecording | `mist-download-site-rfdiag-recording` |
| `getSiteRfdiagRecording` | `/api/v1/sites/{site_id}/rfdiags/{rfdiag_id}` | getSiteRfdiagRecording | `mist-get-site-rfdiag-recording` |
| `getSiteSiteRfdiagRecording` | `/api/v1/sites/{site_id}/rfdiags` | getSiteSiteRfdiagRecording | `mist-get-site-site-rfdiag-recording` |

### Sites Rogues

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteRogueEvents` | `/api/v1/sites/{site_id}/rogues/events/count` | countSiteRogueEvents | `mist-count-site-rogue-events` |
| `getSiteRogueAP` | `/api/v1/sites/{site_id}/rogues/{rogue_bssid}` | getSiteRogueAP | `mist-get-site-rogue-a-p` |
| `searchSiteRogueEvents` | `/api/v1/sites/{site_id}/rogues/events/search` | searchSiteRogueEvents | `mist-search-site-rogue-events` |

### Sites SLEs

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteSleClassifierDetails` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/classifier/{classifier}/summary` | getSiteSleClassifierDetails | `mist-get-site-sle-classifier-details` |
| `getSiteSleClassifierSummaryTrend` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/classifier/{classifier}/summary-trend` | getSiteSleClassifierSummaryTrend | `mist-get-site-sle-classifier-summary-trend` |
| `getSiteSleHistogram` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/histogram` | getSiteSleHistogram | `mist-get-site-sle-histogram` |
| `getSiteSleImpactSummary` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impact-summary` | getSiteSleImpactSummary | `mist-get-site-sle-impact-summary` |
| `getSiteSleSummary` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/summary` | getSiteSleSummary | `mist-get-site-sle-summary` |
| `getSiteSleSummaryTrend` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/summary-trend` | getSiteSleSummaryTrend | `mist-get-site-sle-summary-trend` |
| `getSiteSleThreshold` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/threshold` | getSiteSleThreshold | `mist-get-site-sle-threshold` |
| `listSiteSleImpactedApplications` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-applications` | listSiteSleImpactedApplications | `mist-list-site-sle-impacted-applications` |
| `listSiteSleImpactedAps` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-aps` | listSiteSleImpactedAps | `mist-list-site-sle-impacted-aps` |
| `listSiteSleImpactedChassis` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-chassis` | listSiteSleImpactedChassis | `mist-list-site-sle-impacted-chassis` |
| `listSiteSleImpactedGateways` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-gateways` | listSiteSleImpactedGateways | `mist-list-site-sle-impacted-gateways` |
| `listSiteSleImpactedInterfaces` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-interfaces` | listSiteSleImpactedInterfaces | `mist-list-site-sle-impacted-interfaces` |
| `listSiteSleImpactedSwitches` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-switches` | listSiteSleImpactedSwitches | `mist-list-site-sle-impacted-switches` |
| `listSiteSleImpactedWiredClients` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-clients` | listSiteSleImpactedWiredClients | `mist-list-site-sle-impacted-wired-clients` |
| `listSiteSleImpactedWirelessClients` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-users` | listSiteSleImpactedWirelessClients | `mist-list-site-sle-impacted-wireless-clients` |
| `listSiteSleMetricClassifiers` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/classifiers` | listSiteSleMetricClassifiers | `mist-list-site-sle-metric-classifiers` |
| `listSiteSlesMetrics` | `/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metrics` | listSiteSlesMetrics | `mist-list-site-sles-metrics` |

### Sites SecIntel Profiles

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `listSiteSecIntelProfilesDerived` | `/api/v1/sites/{site_id}/secintelprofiles/derived` | listSiteSecIntelProfilesDerived | `mist-list-site-sec-intel-profiles-derived` |

### Sites Services

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteServicePathEvents` | `/api/v1/sites/{site_id}/services/events/count` | countSiteServicePathEvents | `mist-count-site-service-path-events` |
| `listSiteServicesDerived` | `/api/v1/sites/{site_id}/services/derived` | listSiteServicesDerived | `mist-list-site-services-derived` |
| `searchSiteServicePathEvents` | `/api/v1/sites/{site_id}/services/events/search` | searchSiteServicePathEvents | `mist-search-site-service-path-events` |

### Sites Setting

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteSettingDerived` | `/api/v1/sites/{site_id}/setting/derived` | getSiteSettingDerived | `mist-get-site-setting-derived` |

### Sites Site Templates

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `listSiteSiteTemplatesDerived` | `/api/v1/sites/{site_id}/sitetemplates/derived` | listSiteSiteTemplatesDerived | `mist-list-site-site-templates-derived` |

### Sites Skyatp

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteSkyatpEvents` | `/api/v1/sites/{site_id}/skyatp/events/count` | countSiteSkyatpEvents | `mist-count-site-skyatp-events` |
| `searchSiteSkyatpEvents` | `/api/v1/sites/{site_id}/skyatp/events/search` | searchSiteSkyatpEvents | `mist-search-site-skyatp-events` |

### Sites Spectrum Analysis

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteRunningSpectrumAnalysis` | `/api/v1/sites/{site_id}/analyze_spectrum` | getSiteRunningSpectrumAnalysis | `mist-get-site-running-spectrum-analysis` |
| `listSiteSpectrumAnalysis` | `/api/v1/sites/{site_id}/stats/analyze_spectrum` | listSiteSpectrumAnalysis | `mist-list-site-spectrum-analysis` |

### Sites Stats

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteStats` | `/api/v1/sites/{site_id}/stats` | getSiteStats | `mist-get-site-stats` |

### Sites Stats - Apps

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteApps` | `/api/v1/sites/{site_id}/stats/apps/count` | countSiteApps | `mist-count-site-apps` |

### Sites Stats - Assets

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteAssets` | `/api/v1/sites/{site_id}/stats/assets/count` | countSiteAssets | `mist-count-site-assets` |
| `getSiteAssetStats` | `/api/v1/sites/{site_id}/stats/assets/{asset_id}` | getSiteAssetStats | `mist-get-site-asset-stats` |
| `getSiteAssetsOfInterest` | `/api/v1/sites/{site_id}/stats/filtered_assets` | getSiteAssetsOfInterest | `mist-get-site-assets-of-interest` |
| `getSiteDiscoveredAssetByMap` | `/api/v1/sites/{site_id}/stats/maps/{map_id}/discovered_assets` | getSiteDiscoveredAssetByMap | `mist-get-site-discovered-asset-by-map` |
| `listSiteAssetsStats` | `/api/v1/sites/{site_id}/stats/assets` | listSiteAssetsStats | `mist-list-site-assets-stats` |
| `listSiteDiscoveredAssets` | `/api/v1/sites/{site_id}/stats/discovered_assets` | listSiteDiscoveredAssets | `mist-list-site-discovered-assets` |
| `searchSiteAssets` | `/api/v1/sites/{site_id}/stats/assets/search` | searchSiteAssets | `mist-search-site-assets` |

### Sites Stats - BGP Peers

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteBgpStats` | `/api/v1/sites/{site_id}/stats/bgp_peers/count` | countSiteBgpStats | `mist-count-site-bgp-stats` |
| `searchSiteBgpStats` | `/api/v1/sites/{site_id}/stats/bgp_peers/search` | searchSiteBgpStats | `mist-search-site-bgp-stats` |

### Sites Stats - Beacons

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `listSiteBeaconsStats` | `/api/v1/sites/{site_id}/stats/beacons` | listSiteBeaconsStats | `mist-list-site-beacons-stats` |

### Sites Stats - Calls

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteCalls` | `/api/v1/sites/{site_id}/stats/calls/count` | countSiteCalls | `mist-count-site-calls` |
| `getSiteCallsSummary` | `/api/v1/sites/{site_id}/stats/calls/summary` | getSiteCallsSummary | `mist-get-site-calls-summary` |
| `listSiteTroubleshootCalls` | `/api/v1/sites/{site_id}/stats/calls/troubleshoot` | listSiteTroubleshootCalls | `mist-list-site-troubleshoot-calls` |
| `searchSiteCalls` | `/api/v1/sites/{site_id}/stats/calls/search` | searchSiteCalls | `mist-search-site-calls` |
| `troubleshootSiteCall` | `/api/v1/sites/{site_id}/stats/calls/client/{client_mac}/troubleshoot` | troubleshootSiteCall | `mist-troubleshoot-site-call` |

### Sites Stats - Clients SDK

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteSdkStats` | `/api/v1/sites/{site_id}/stats/sdkclients/{sdkclient_id}` | getSiteSdkStats | `mist-get-site-sdk-stats` |
| `getSiteSdkStatsByMap` | `/api/v1/sites/{site_id}/stats/maps/{map_id}/sdkclients` | getSiteSdkStatsByMap | `mist-get-site-sdk-stats-by-map` |

### Sites Stats - Clients Wireless

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteWirelessClientStats` | `/api/v1/sites/{site_id}/stats/clients/{client_mac}` | getSiteWirelessClientStats | `mist-get-site-wireless-client-stats` |
| `getSiteWirelessClientsStatsByMap` | `/api/v1/sites/{site_id}/stats/maps/{map_id}/clients` | getSiteWirelessClientsStatsByMap | `mist-get-site-wireless-clients-stats-by-map` |
| `listSiteUnconnectedClientStats` | `/api/v1/sites/{site_id}/stats/maps/{map_id}/unconnected_clients` | listSiteUnconnectedClientStats | `mist-list-site-unconnected-client-stats` |

### Sites Stats - Devices

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteAllClientsStatsByDevice` | `/api/v1/sites/{site_id}/stats/devices/{device_id}/clients` | getSiteAllClientsStatsByDevice | `mist-get-site-all-clients-stats-by-device` |
| `getSiteGatewayMetrics` | `/api/v1/sites/{site_id}/stats/gateways/metrics` | getSiteGatewayMetrics | `mist-get-site-gateway-metrics` |
| `getSiteSwitchesMetrics` | `/api/v1/sites/{site_id}/stats/switches/metrics` | getSiteSwitchesMetrics | `mist-get-site-switches-metrics` |

### Sites Stats - Discovered Switches

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteDiscoveredSwitches` | `/api/v1/sites/{site_id}/stats/discovered_switches/count` | countSiteDiscoveredSwitches | `mist-count-site-discovered-switches` |
| `listSiteDiscoveredSwitchesMetrics` | `/api/v1/sites/{site_id}/stats/discovered_switches/metrics` | listSiteDiscoveredSwitchesMetrics | `mist-list-site-discovered-switches-metrics` |
| `searchSiteDiscoveredSwitches` | `/api/v1/sites/{site_id}/stats/discovered_switches/search` | searchSiteDiscoveredSwitches | `mist-search-site-discovered-switches` |
| `searchSiteDiscoveredSwitchesMetrics` | `/api/v1/sites/{site_id}/stats/discovered_switch_metrics/search` | searchSiteDiscoveredSwitchesMetrics | `mist-search-site-discovered-switches-metrics` |

### Sites Stats - MxEdges

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteMxEdgeStats` | `/api/v1/sites/{site_id}/stats/mxedges/{mxedge_id}` | getSiteMxEdgeStats | `mist-get-site-mx-edge-stats` |
| `listSiteMxEdgesStats` | `/api/v1/sites/{site_id}/stats/mxedges` | listSiteMxEdgesStats | `mist-list-site-mx-edges-stats` |

### Sites Stats - Ospf

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteOspfStats` | `/api/v1/sites/{site_id}/stats/ospf_peers/count` | countSiteOspfStats | `mist-count-site-ospf-stats` |
| `searchSiteOspfStats` | `/api/v1/sites/{site_id}/stats/ospf_peers/search` | searchSiteOspfStats | `mist-search-site-ospf-stats` |

### Sites Stats - Ports

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteSwOrGwPorts` | `/api/v1/sites/{site_id}/stats/ports/count` | countSiteSwOrGwPorts | `mist-count-site-sw-or-gw-ports` |

### Sites Stats - WxRules

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteWxRulesUsage` | `/api/v1/sites/{site_id}/stats/wxrules` | getSiteWxRulesUsage | `mist-get-site-wx-rules-usage` |

### Sites Stats - Zones

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteRssiZoneStats` | `/api/v1/sites/{site_id}/stats/rssizones/{zone_id}` | getSiteRssiZoneStats | `mist-get-site-rssi-zone-stats` |
| `getSiteZoneStats` | `/api/v1/sites/{site_id}/stats/zones/{zone_id}` | getSiteZoneStats | `mist-get-site-zone-stats` |
| `listSiteRssiZonesStats` | `/api/v1/sites/{site_id}/stats/rssizones` | listSiteRssiZonesStats | `mist-list-site-rssi-zones-stats` |
| `listSiteZonesStats` | `/api/v1/sites/{site_id}/stats/zones` | listSiteZonesStats | `mist-list-site-zones-stats` |

### Sites UI Settings

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteUiSetting` | `/api/v1/sites/{site_id}/uisettings/{uisetting_id}` | getSiteUiSetting | `mist-get-site-ui-setting` |
| `listSiteUiSettingDerived` | `/api/v1/sites/{site_id}/uisettings/derived` | listSiteUiSettingDerived | `mist-list-site-ui-setting-derived` |
| `listSiteUiSettings` | `/api/v1/sites/{site_id}/uisettings` | listSiteUiSettings | `mist-list-site-ui-settings` |

### Sites VPNs

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `listSiteVpnsDerived` | `/api/v1/sites/{site_id}/vpns/derived` | listSiteVpnsDerived | `mist-list-site-vpns-derived` |

### Sites WAN Usages

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteWanUsage` | `/api/v1/sites/{site_id}/wan_usages/count` | countSiteWanUsage | `mist-count-site-wan-usage` |
| `searchSiteWanUsage` | `/api/v1/sites/{site_id}/wan_usages/search` | searchSiteWanUsage | `mist-search-site-wan-usage` |

### Sites Webhooks

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteWebhooksDeliveries` | `/api/v1/sites/{site_id}/webhooks/{webhook_id}/events/count` | countSiteWebhooksDeliveries | `mist-count-site-webhooks-deliveries` |
| `getSiteWebhook` | `/api/v1/sites/{site_id}/webhooks/{webhook_id}` | getSiteWebhook | `mist-get-site-webhook` |
| `listSiteWebhooks` | `/api/v1/sites/{site_id}/webhooks` | listSiteWebhooks | `mist-list-site-webhooks` |
| `searchSiteWebhooksDeliveries` | `/api/v1/sites/{site_id}/webhooks/{webhook_id}/events/search` | searchSiteWebhooksDeliveries | `mist-search-site-webhooks-deliveries` |

### Sites Wlans

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteWlan` | `/api/v1/sites/{site_id}/wlans/{wlan_id}` | getSiteWlan | `mist-get-site-wlan` |

### Sites WxRules

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `ListSiteWxRulesDerived` | `/api/v1/sites/{site_id}/wxrules/derived` | ListSiteWxRulesDerived | `mist-list-site-wx-rules-derived` |
| `getSiteWxRule` | `/api/v1/sites/{site_id}/wxrules/{wxrule_id}` | getSiteWxRule | `mist-get-site-wx-rule` |
| `listSiteWxRules` | `/api/v1/sites/{site_id}/wxrules` | listSiteWxRules | `mist-list-site-wx-rules` |

### Sites WxTags

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteApplicationList` | `/api/v1/sites/{site_id}/wxtags/apps` | getSiteApplicationList | `mist-get-site-application-list` |
| `getSiteWxTag` | `/api/v1/sites/{site_id}/wxtags/{wxtag_id}` | getSiteWxTag | `mist-get-site-wx-tag` |
| `listSiteWxTags` | `/api/v1/sites/{site_id}/wxtags` | listSiteWxTags | `mist-list-site-wx-tags` |

### Sites WxTunnels

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteWxTunnel` | `/api/v1/sites/{site_id}/wxtunnels/{wxtunnel_id}` | getSiteWxTunnel | `mist-get-site-wx-tunnel` |
| `listSiteWxTunnels` | `/api/v1/sites/{site_id}/wxtunnels` | listSiteWxTunnels | `mist-list-site-wx-tunnels` |

### Sites Zones

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `countSiteZoneSessions` | `/api/v1/sites/{site_id}/{zone_type}/count` | countSiteZoneSessions | `mist-count-site-zone-sessions` |
| `getSiteZone` | `/api/v1/sites/{site_id}/zones/{zone_id}` | getSiteZone | `mist-get-site-zone` |
| `searchSiteZoneSessions` | `/api/v1/sites/{site_id}/{zone_type}/visits/search` | searchSiteZoneSessions | `mist-search-site-zone-sessions` |

### Sites vBeacons

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteVBeacon` | `/api/v1/sites/{site_id}/vbeacons/{vbeacon_id}` | getSiteVBeacon | `mist-get-site-v-beacon` |

### Utilities Common

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getSiteDeviceConfigCmd` | `/api/v1/sites/{site_id}/devices/{device_id}/config_cmd` | getSiteDeviceConfigCmd | `mist-get-site-device-config-cmd` |

### Utilities PCAPs

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgCapturingStatus` | `/api/v1/orgs/{org_id}/pcaps/capture` | getOrgCapturingStatus | `mist-get-org-capturing-status` |
| `getSiteCapturingStatus` | `/api/v1/sites/{site_id}/pcaps/capture` | getSiteCapturingStatus | `mist-get-site-capturing-status` |

### Utilities Upgrade

| operationId | Path | Summary | Proposed Spec Slug |
|---|---|---|---|
| `getOrgDeviceUpgrade` | `/api/v1/orgs/{org_id}/devices/upgrade/{upgrade_id}` | getOrgDeviceUpgrade | `mist-get-org-device-upgrade` |
| `getOrgMxEdgeUpgrade` | `/api/v1/orgs/{org_id}/mxedges/upgrade/{upgrade_id}` | getOrgMxEdgeUpgrade | `mist-get-org-mx-edge-upgrade` |
| `getOrgSsrUpgrade` | `/api/v1/orgs/{org_id}/ssr/upgrade/{upgrade_id}/cancel` | getOrgSsrUpgrade | `mist-get-org-ssr-upgrade` |
| `getSiteSsrUpgrade` | `/api/v1/sites/{site_id}/ssr/upgrade/{upgrade_id}` | getSiteSsrUpgrade | `mist-get-site-ssr-upgrade` |
| `listOrgDeviceUpgrades` | `/api/v1/orgs/{org_id}/devices/upgrade` | listOrgDeviceUpgrades | `mist-list-org-device-upgrades` |
| `listOrgMxEdgeUpgrades` | `/api/v1/orgs/{org_id}/mxedges/upgrade` | listOrgMxEdgeUpgrades | `mist-list-org-mx-edge-upgrades` |
| `listSiteAvailableDeviceVersions` | `/api/v1/sites/{site_id}/devices/versions` | listSiteAvailableDeviceVersions | `mist-list-site-available-device-versions` |

