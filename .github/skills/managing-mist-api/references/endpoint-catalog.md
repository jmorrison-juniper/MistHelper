# Endpoint and source catalog

## Contents

1. [Coverage and lookup](#coverage-and-lookup)
2. [Primary categories](#primary-categories)
3. [SDK-only entries](#sdk-only-entries)
4. [Older-edition differences](#older-edition-differences)
5. [Saved guides and source fingerprints](#saved-guides-and-source-fingerprints)

## Coverage and lookup

This catalog routes all 206 categories used by the primary OpenAPI specification.
The category counts total 1,013 HTTP operations across 719 paths.
Each category link opens the existing endpoint index at its exact heading.
Each index row provides the method, path, `operationId`, and endpoint page.

This structure provides exhaustive navigation without duplicating 1,799 schemas or 1,013 endpoint pages.
Read the original operation and its referenced schema before implementing a request.
Do not infer undocumented operations from the category name.

The SDK-only section lists all 61 indexed helper entries separately.
The older-edition section preserves all 30 operation triples absent from the primary edition.
The saved guides cover narrative behavior and additional HTML-only material.

### Lookup procedure

1. Select the category that matches the resource and actual request scope.
2. Find the exact operation in the linked index section.
3. Open its endpoint page and inspect the primary specification node.
4. Read the matching saved guide when narrative behavior or missing fields require it.
5. Apply the source-conflict rules before a live request.

For an SDK-only operation, begin with its linked stub and the installed SDK signature.
For an HTML-only operation, record the saved heading and its lower-confidence contract status.
If no source defines the operation, state that gap. Do not construct a plausible route.

### Primary and SDK counts by folder

These counts describe the checked 2026-09-09 snapshot.

| Folder | Primary operations | SDK-only entries | Indexed pages |
| - | -: | -: | -: |
| `admins` | 13 | 0 | 13 |
| `constants` | 27 | 0 | 27 |
| `installer` | 23 | 2 | 25 |
| `msps` | 50 | 1 | 51 |
| `orgs` | 449 | 27 | 476 |
| `self` | 18 | 0 | 18 |
| `sites` | 330 | 31 | 361 |
| `utilities` | 103 | 0 | 103 |
| **Total** | **1,013** | **61** | **1,074** |

The folder and tag identify documentation categories, not guaranteed SDK module paths.
Use the path's parameters to determine the API scope.

## Primary categories

### Administrators, constants, installer, and self

| Category | Operations | Source |
| - | -: | - |
| Admins | 4 | [Index](../../../../documentation/api/INDEX.md#admins) |
| Admins Login | 2 | [Index](../../../../documentation/api/INDEX.md#admins-login) |
| Admins Login - OAuth2 | 3 | [Index](../../../../documentation/api/INDEX.md#admins-login---oauth2) |
| Admins Logout | 1 | [Index](../../../../documentation/api/INDEX.md#admins-logout) |
| Admins Lookup | 1 | [Index](../../../../documentation/api/INDEX.md#admins-lookup) |
| Admins Recover Password | 2 | [Index](../../../../documentation/api/INDEX.md#admins-recover-password) |
| Constants Definitions | 16 | [Index](../../../../documentation/api/INDEX.md#constants-definitions) |
| Constants Events | 7 | [Index](../../../../documentation/api/INDEX.md#constants-events) |
| Constants Models | 4 | [Index](../../../../documentation/api/INDEX.md#constants-models) |
| Installer | 23 | [Index](../../../../documentation/api/INDEX.md#installer) |
| Self API Token | 5 | [Index](../../../../documentation/api/INDEX.md#self-api-token) |
| Self Account | 7 | [Index](../../../../documentation/api/INDEX.md#self-account) |
| Self Alarms | 1 | [Index](../../../../documentation/api/INDEX.md#self-alarms) |
| Self Audit Logs | 1 | [Index](../../../../documentation/api/INDEX.md#self-audit-logs) |
| Self MFA | 2 | [Index](../../../../documentation/api/INDEX.md#self-mfa) |
| Self OAuth2 | 2 | [Index](../../../../documentation/api/INDEX.md#self-oauth2) |

### Managed service providers

| Category | Operations | Source |
| - | -: | - |
| MSPs | 5 | [Index](../../../../documentation/api/INDEX.md#msps) |
| MSPs Admins | 7 | [Index](../../../../documentation/api/INDEX.md#msps-admins) |
| MSPs Inventory | 1 | [Index](../../../../documentation/api/INDEX.md#msps-inventory) |
| MSPs Licenses | 4 | [Index](../../../../documentation/api/INDEX.md#msps-licenses) |
| MSPs Logo | 2 | [Index](../../../../documentation/api/INDEX.md#msps-logo) |
| MSPs Logs | 2 | [Index](../../../../documentation/api/INDEX.md#msps-logs) |
| MSPs Marvis | 1 | [Index](../../../../documentation/api/INDEX.md#msps-marvis) |
| MSPs Org Groups | 5 | [Index](../../../../documentation/api/INDEX.md#msps-org-groups) |
| MSPs Orgs | 8 | [Index](../../../../documentation/api/INDEX.md#msps-orgs) |
| MSPs SLEs | 1 | [Index](../../../../documentation/api/INDEX.md#msps-sles) |
| MSPs SSO | 8 | [Index](../../../../documentation/api/INDEX.md#msps-sso) |
| MSPs SSO Roles | 4 | [Index](../../../../documentation/api/INDEX.md#msps-sso-roles) |
| MSPs Tickets | 2 | [Index](../../../../documentation/api/INDEX.md#msps-tickets) |

### Organizations

| Category | Operations | Source |
| - | -: | - |
| Orgs | 5 | [Index](../../../../documentation/api/INDEX.md#orgs) |
| Orgs AP Templates | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-ap-templates) |
| Orgs API Tokens | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-api-tokens) |
| Orgs Admins | 6 | [Index](../../../../documentation/api/INDEX.md#orgs-admins) |
| Orgs Advanced Anti Malware Profiles | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-advanced-anti-malware-profiles) |
| Orgs Alarm Templates | 8 | [Index](../../../../documentation/api/INDEX.md#orgs-alarm-templates) |
| Orgs Alarms | 9 | [Index](../../../../documentation/api/INDEX.md#orgs-alarms) |
| Orgs Antivirus Profiles | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-antivirus-profiles) |
| Orgs Asset Filters | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-asset-filters) |
| Orgs Assets | 6 | [Index](../../../../documentation/api/INDEX.md#orgs-assets) |
| Orgs CRL | 1 | [Index](../../../../documentation/api/INDEX.md#orgs-crl) |
| Orgs Cert | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-cert) |
| Orgs Clients - Marvis | 1 | [Index](../../../../documentation/api/INDEX.md#orgs-clients---marvis) |
| Orgs Clients - NAC | 4 | [Index](../../../../documentation/api/INDEX.md#orgs-clients---nac) |
| Orgs Clients - SDK | 1 | [Index](../../../../documentation/api/INDEX.md#orgs-clients---sdk) |
| Orgs Clients - Wan | 4 | [Index](../../../../documentation/api/INDEX.md#orgs-clients---wan) |
| Orgs Clients - Wired | 2 | [Index](../../../../documentation/api/INDEX.md#orgs-clients---wired) |
| Orgs Clients - Wireless | 6 | [Index](../../../../documentation/api/INDEX.md#orgs-clients---wireless) |
| Orgs Device Profiles | 7 | [Index](../../../../documentation/api/INDEX.md#orgs-device-profiles) |
| Orgs Devices | 10 | [Index](../../../../documentation/api/INDEX.md#orgs-devices) |
| Orgs Devices - AOS | 1 | [Index](../../../../documentation/api/INDEX.md#orgs-devices---aos) |
| Orgs Devices - Others | 8 | [Index](../../../../documentation/api/INDEX.md#orgs-devices---others) |
| Orgs Devices - SSR | 3 | [Index](../../../../documentation/api/INDEX.md#orgs-devices---ssr) |
| Orgs EVPN Topologies | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-evpn-topologies) |
| Orgs Events | 3 | [Index](../../../../documentation/api/INDEX.md#orgs-events) |
| Orgs Gateway Templates | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-gateway-templates) |
| Orgs Guests | 6 | [Index](../../../../documentation/api/INDEX.md#orgs-guests) |
| Orgs IDP Profiles | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-idp-profiles) |
| Orgs Integration Cradlepoint | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-integration-cradlepoint) |
| Orgs Integration JSE | 4 | [Index](../../../../documentation/api/INDEX.md#orgs-integration-jse) |
| Orgs Integration Juniper | 2 | [Index](../../../../documentation/api/INDEX.md#orgs-integration-juniper) |
| Orgs Integration SkyATP | 6 | [Index](../../../../documentation/api/INDEX.md#orgs-integration-skyatp) |
| Orgs Integration Zscaler | 3 | [Index](../../../../documentation/api/INDEX.md#orgs-integration-zscaler) |
| Orgs Inventory | 9 | [Index](../../../../documentation/api/INDEX.md#orgs-inventory) |
| Orgs JSI | 10 | [Index](../../../../documentation/api/INDEX.md#orgs-jsi) |
| Orgs Licenses | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-licenses) |
| Orgs Linked Applications | 4 | [Index](../../../../documentation/api/INDEX.md#orgs-linked-applications) |
| Orgs Logs | 2 | [Index](../../../../documentation/api/INDEX.md#orgs-logs) |
| Orgs Maps | 2 | [Index](../../../../documentation/api/INDEX.md#orgs-maps) |
| Orgs Marvis | 1 | [Index](../../../../documentation/api/INDEX.md#orgs-marvis) |
| Orgs Marvis Invites | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-marvis-invites) |
| Orgs MxClusters | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-mxclusters) |
| Orgs MxEdges | 22 | [Index](../../../../documentation/api/INDEX.md#orgs-mxedges) |
| Orgs MxTunnels | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-mxtunnels) |
| Orgs NAC CRL | 3 | [Index](../../../../documentation/api/INDEX.md#orgs-nac-crl) |
| Orgs NAC Fingerprints | 2 | [Index](../../../../documentation/api/INDEX.md#orgs-nac-fingerprints) |
| Orgs NAC IDP | 1 | [Index](../../../../documentation/api/INDEX.md#orgs-nac-idp) |
| Orgs NAC Portals | 11 | [Index](../../../../documentation/api/INDEX.md#orgs-nac-portals) |
| Orgs NAC Rules | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-nac-rules) |
| Orgs NAC Tags | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-nac-tags) |
| Orgs Network Templates | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-network-templates) |
| Orgs Networks | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-networks) |
| Orgs Premium Analytics | 1 | [Index](../../../../documentation/api/INDEX.md#orgs-premium-analytics) |
| Orgs Psk Portals | 11 | [Index](../../../../documentation/api/INDEX.md#orgs-psk-portals) |
| Orgs Psks | 9 | [Index](../../../../documentation/api/INDEX.md#orgs-psks) |
| Orgs RF Templates | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-rf-templates) |
| Orgs SCEP | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-scep) |
| Orgs SDK Invites | 9 | [Index](../../../../documentation/api/INDEX.md#orgs-sdk-invites) |
| Orgs SDK Templates | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-sdk-templates) |
| Orgs SLEs | 2 | [Index](../../../../documentation/api/INDEX.md#orgs-sles) |
| Orgs SSO | 8 | [Index](../../../../documentation/api/INDEX.md#orgs-sso) |
| Orgs SSO Roles | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-sso-roles) |
| Orgs SecIntel Profiles | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-secintel-profiles) |
| Orgs Security Policies | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-security-policies) |
| Orgs Service Policies | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-service-policies) |
| Orgs Services | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-services) |
| Orgs Setting | 6 | [Index](../../../../documentation/api/INDEX.md#orgs-setting) |
| Orgs Site Templates | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-site-templates) |
| Orgs Sitegroups | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-sitegroups) |
| Orgs Sites | 4 | [Index](../../../../documentation/api/INDEX.md#orgs-sites) |
| Orgs Stats | 1 | [Index](../../../../documentation/api/INDEX.md#orgs-stats) |
| Orgs Stats - Assets | 3 | [Index](../../../../documentation/api/INDEX.md#orgs-stats---assets) |
| Orgs Stats - BGP Peers | 2 | [Index](../../../../documentation/api/INDEX.md#orgs-stats---bgp-peers) |
| Orgs Stats - Devices | 1 | [Index](../../../../documentation/api/INDEX.md#orgs-stats---devices) |
| Orgs Stats - MxEdges | 2 | [Index](../../../../documentation/api/INDEX.md#orgs-stats---mxedges) |
| Orgs Stats - Ospf | 2 | [Index](../../../../documentation/api/INDEX.md#orgs-stats---ospf) |
| Orgs Stats - Other Devices | 1 | [Index](../../../../documentation/api/INDEX.md#orgs-stats---other-devices) |
| Orgs Stats - Ports | 2 | [Index](../../../../documentation/api/INDEX.md#orgs-stats---ports) |
| Orgs Stats - Sites | 1 | [Index](../../../../documentation/api/INDEX.md#orgs-stats---sites) |
| Orgs Stats - Tunnels | 2 | [Index](../../../../documentation/api/INDEX.md#orgs-stats---tunnels) |
| Orgs Stats - VPN Peers | 2 | [Index](../../../../documentation/api/INDEX.md#orgs-stats---vpn-peers) |
| Orgs Tickets | 8 | [Index](../../../../documentation/api/INDEX.md#orgs-tickets) |
| Orgs UI Settings | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-ui-settings) |
| Orgs User MACs | 9 | [Index](../../../../documentation/api/INDEX.md#orgs-user-macs) |
| Orgs VPNs | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-vpns) |
| Orgs Vars | 1 | [Index](../../../../documentation/api/INDEX.md#orgs-vars) |
| Orgs WLAN Templates | 6 | [Index](../../../../documentation/api/INDEX.md#orgs-wlan-templates) |
| Orgs Webhooks | 8 | [Index](../../../../documentation/api/INDEX.md#orgs-webhooks) |
| Orgs Wlans | 8 | [Index](../../../../documentation/api/INDEX.md#orgs-wlans) |
| Orgs WxRules | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-wxrules) |
| Orgs WxTags | 7 | [Index](../../../../documentation/api/INDEX.md#orgs-wxtags) |
| Orgs WxTunnels | 5 | [Index](../../../../documentation/api/INDEX.md#orgs-wxtunnels) |

### Sites

| Category | Operations | Source |
| - | -: | - |
| Sites | 3 | [Index](../../../../documentation/api/INDEX.md#sites) |
| Sites AP Templates | 1 | [Index](../../../../documentation/api/INDEX.md#sites-ap-templates) |
| Sites Advanced Anti Malware Profiles | 1 | [Index](../../../../documentation/api/INDEX.md#sites-advanced-anti-malware-profiles) |
| Sites Alarms | 10 | [Index](../../../../documentation/api/INDEX.md#sites-alarms) |
| Sites Anomaly | 3 | [Index](../../../../documentation/api/INDEX.md#sites-anomaly) |
| Sites Antivirus Profiles | 1 | [Index](../../../../documentation/api/INDEX.md#sites-antivirus-profiles) |
| Sites Applications | 1 | [Index](../../../../documentation/api/INDEX.md#sites-applications) |
| Sites Asset Filters | 5 | [Index](../../../../documentation/api/INDEX.md#sites-asset-filters) |
| Sites Assets | 8 | [Index](../../../../documentation/api/INDEX.md#sites-assets) |
| Sites Beacons | 5 | [Index](../../../../documentation/api/INDEX.md#sites-beacons) |
| Sites Clients - NAC | 4 | [Index](../../../../documentation/api/INDEX.md#sites-clients---nac) |
| Sites Clients - Wan | 4 | [Index](../../../../documentation/api/INDEX.md#sites-clients---wan) |
| Sites Clients - Wired | 2 | [Index](../../../../documentation/api/INDEX.md#sites-clients---wired) |
| Sites Clients - Wireless | 7 | [Index](../../../../documentation/api/INDEX.md#sites-clients---wireless) |
| Sites Device Profiles | 1 | [Index](../../../../documentation/api/INDEX.md#sites-device-profiles) |
| Sites Devices | 16 | [Index](../../../../documentation/api/INDEX.md#sites-devices) |
| Sites Devices - Others | 3 | [Index](../../../../documentation/api/INDEX.md#sites-devices---others) |
| Sites Devices - WAN Cluster | 3 | [Index](../../../../documentation/api/INDEX.md#sites-devices---wan-cluster) |
| Sites Devices - Wired | 2 | [Index](../../../../documentation/api/INDEX.md#sites-devices---wired) |
| Sites Devices - Wired - Virtual Chassis | 7 | [Index](../../../../documentation/api/INDEX.md#sites-devices---wired---virtual-chassis) |
| Sites Devices - Wireless | 3 | [Index](../../../../documentation/api/INDEX.md#sites-devices---wireless) |
| Sites EVPN Topologies | 5 | [Index](../../../../documentation/api/INDEX.md#sites-evpn-topologies) |
| Sites Events | 3 | [Index](../../../../documentation/api/INDEX.md#sites-events) |
| Sites Gateway Templates | 1 | [Index](../../../../documentation/api/INDEX.md#sites-gateway-templates) |
| Sites Guests | 7 | [Index](../../../../documentation/api/INDEX.md#sites-guests) |
| Sites IDP Profiles | 1 | [Index](../../../../documentation/api/INDEX.md#sites-idp-profiles) |
| Sites Insights | 6 | [Index](../../../../documentation/api/INDEX.md#sites-insights) |
| Sites JSE | 1 | [Index](../../../../documentation/api/INDEX.md#sites-jse) |
| Sites Licenses | 1 | [Index](../../../../documentation/api/INDEX.md#sites-licenses) |
| Sites Location | 8 | [Index](../../../../documentation/api/INDEX.md#sites-location) |
| Sites Map Stacks | 2 | [Index](../../../../documentation/api/INDEX.md#sites-map-stacks) |
| Sites Maps | 13 | [Index](../../../../documentation/api/INDEX.md#sites-maps) |
| Sites Maps - Auto-Zone | 3 | [Index](../../../../documentation/api/INDEX.md#sites-maps---auto-zone) |
| Sites Maps - Auto-placement | 9 | [Index](../../../../documentation/api/INDEX.md#sites-maps---auto-placement) |
| Sites MxEdges | 7 | [Index](../../../../documentation/api/INDEX.md#sites-mxedges) |
| Sites Network Templates | 1 | [Index](../../../../documentation/api/INDEX.md#sites-network-templates) |
| Sites Networks | 1 | [Index](../../../../documentation/api/INDEX.md#sites-networks) |
| Sites Psks | 7 | [Index](../../../../documentation/api/INDEX.md#sites-psks) |
| Sites RF Templates | 1 | [Index](../../../../documentation/api/INDEX.md#sites-rf-templates) |
| Sites RRM | 4 | [Index](../../../../documentation/api/INDEX.md#sites-rrm) |
| Sites RSSI Zones | 5 | [Index](../../../../documentation/api/INDEX.md#sites-rssi-zones) |
| Sites Rfdiags | 7 | [Index](../../../../documentation/api/INDEX.md#sites-rfdiags) |
| Sites Rogues | 5 | [Index](../../../../documentation/api/INDEX.md#sites-rogues) |
| Sites SLEs | 19 | [Index](../../../../documentation/api/INDEX.md#sites-sles) |
| Sites SecIntel Profiles | 1 | [Index](../../../../documentation/api/INDEX.md#sites-secintel-profiles) |
| Sites Service Policies | 1 | [Index](../../../../documentation/api/INDEX.md#sites-service-policies) |
| Sites Services | 3 | [Index](../../../../documentation/api/INDEX.md#sites-services) |
| Sites Setting | 9 | [Index](../../../../documentation/api/INDEX.md#sites-setting) |
| Sites Site Templates | 1 | [Index](../../../../documentation/api/INDEX.md#sites-site-templates) |
| Sites Skyatp | 2 | [Index](../../../../documentation/api/INDEX.md#sites-skyatp) |
| Sites Spectrum Analysis | 3 | [Index](../../../../documentation/api/INDEX.md#sites-spectrum-analysis) |
| Sites Stats | 1 | [Index](../../../../documentation/api/INDEX.md#sites-stats) |
| Sites Stats - Apps | 1 | [Index](../../../../documentation/api/INDEX.md#sites-stats---apps) |
| Sites Stats - Assets | 7 | [Index](../../../../documentation/api/INDEX.md#sites-stats---assets) |
| Sites Stats - BGP Peers | 2 | [Index](../../../../documentation/api/INDEX.md#sites-stats---bgp-peers) |
| Sites Stats - Beacons | 1 | [Index](../../../../documentation/api/INDEX.md#sites-stats---beacons) |
| Sites Stats - Calls | 5 | [Index](../../../../documentation/api/INDEX.md#sites-stats---calls) |
| Sites Stats - Clients SDK | 2 | [Index](../../../../documentation/api/INDEX.md#sites-stats---clients-sdk) |
| Sites Stats - Clients Wireless | 4 | [Index](../../../../documentation/api/INDEX.md#sites-stats---clients-wireless) |
| Sites Stats - Devices | 5 | [Index](../../../../documentation/api/INDEX.md#sites-stats---devices) |
| Sites Stats - Discovered Switches | 4 | [Index](../../../../documentation/api/INDEX.md#sites-stats---discovered-switches) |
| Sites Stats - MxEdges | 2 | [Index](../../../../documentation/api/INDEX.md#sites-stats---mxedges) |
| Sites Stats - Ospf | 2 | [Index](../../../../documentation/api/INDEX.md#sites-stats---ospf) |
| Sites Stats - Ports | 2 | [Index](../../../../documentation/api/INDEX.md#sites-stats---ports) |
| Sites Stats - WxRules | 1 | [Index](../../../../documentation/api/INDEX.md#sites-stats---wxrules) |
| Sites Stats - Zones | 4 | [Index](../../../../documentation/api/INDEX.md#sites-stats---zones) |
| Sites Synthetic Tests | 5 | [Index](../../../../documentation/api/INDEX.md#sites-synthetic-tests) |
| Sites UI Settings | 6 | [Index](../../../../documentation/api/INDEX.md#sites-ui-settings) |
| Sites VPNs | 1 | [Index](../../../../documentation/api/INDEX.md#sites-vpns) |
| Sites WAN Usages | 2 | [Index](../../../../documentation/api/INDEX.md#sites-wan-usages) |
| Sites Webhooks | 8 | [Index](../../../../documentation/api/INDEX.md#sites-webhooks) |
| Sites Wlans | 9 | [Index](../../../../documentation/api/INDEX.md#sites-wlans) |
| Sites WxRules | 6 | [Index](../../../../documentation/api/INDEX.md#sites-wxrules) |
| Sites WxTags | 6 | [Index](../../../../documentation/api/INDEX.md#sites-wxtags) |
| Sites WxTunnels | 5 | [Index](../../../../documentation/api/INDEX.md#sites-wxtunnels) |
| Sites Zones | 7 | [Index](../../../../documentation/api/INDEX.md#sites-zones) |
| Sites vBeacons | 5 | [Index](../../../../documentation/api/INDEX.md#sites-vbeacons) |

### Utilities

| Category | Operations | Source |
| - | -: | - |
| Utilities Common | 25 | [Index](../../../../documentation/api/INDEX.md#utilities-common) |
| Utilities LAN | 17 | [Index](../../../../documentation/api/INDEX.md#utilities-lan) |
| Utilities Location | 1 | [Index](../../../../documentation/api/INDEX.md#utilities-location) |
| Utilities MxEdge | 1 | [Index](../../../../documentation/api/INDEX.md#utilities-mxedge) |
| Utilities PCAPs | 9 | [Index](../../../../documentation/api/INDEX.md#utilities-pcaps) |
| Utilities Upgrade | 22 | [Index](../../../../documentation/api/INDEX.md#utilities-upgrade) |
| Utilities WAN | 14 | [Index](../../../../documentation/api/INDEX.md#utilities-wan) |
| Utilities Wi-Fi | 14 | [Index](../../../../documentation/api/INDEX.md#utilities-wi-fi) |

## SDK-only entries

The [SDK-only index](../../../../documentation/api/INDEX.md#library-only-mistapi-sdk-not-in-openapi-spec) records these 61 entries.
Each linked stub identifies its historical module and signature when available.
Read the installed implementation before treating that signature as current.
Missing request, response, or error descriptions remain unknown, not unrestricted.

### Installer and MSP helpers

| Helper | Source |
| - | - |
| `addInstallerDeviceImageFile` | [Stub](../../../../documentation/api/installer/SDK_addInstallerDeviceImageFile.md) |
| `importInstallerMapFile` | [Stub](../../../../documentation/api/installer/SDK_importInstallerMapFile.md) |
| `deleteMspSsoAdmins` | [Stub](../../../../documentation/api/msps/SDK_deleteMspSsoAdmins.md) |

### Organization helpers

| Helper | Source |
| - | - |
| `UploadOrgTicketAttachmentFile` | [Stub](../../../../documentation/api/orgs/SDK_UploadOrgTicketAttachmentFile.md) |
| `addOrgMxEdgeImageFile` | [Stub](../../../../documentation/api/orgs/SDK_addOrgMxEdgeImageFile.md) |
| `addOrgTicketCommentFile` | [Stub](../../../../documentation/api/orgs/SDK_addOrgTicketCommentFile.md) |
| `cancelOrgMxEdgeUpgrade` | [Stub](../../../../documentation/api/orgs/SDK_cancelOrgMxEdgeUpgrade.md) |
| `countOrgMarvisClientEvents` | [Stub](../../../../documentation/api/orgs/SDK_countOrgMarvisClientEvents.md) |
| `countOrgMarvisClientsStats` | [Stub](../../../../documentation/api/orgs/SDK_countOrgMarvisClientsStats.md) |
| `createOrgAsyncClaim` | [Stub](../../../../documentation/api/orgs/SDK_createOrgAsyncClaim.md) |
| `deleteOrgSsoAdmins` | [Stub](../../../../documentation/api/orgs/SDK_deleteOrgSsoAdmins.md) |
| `disableOrgE911Report` | [Stub](../../../../documentation/api/orgs/SDK_disableOrgE911Report.md) |
| `enableOrgE911Report` | [Stub](../../../../documentation/api/orgs/SDK_enableOrgE911Report.md) |
| `getOrgAsyncClaimStatus` | [Stub](../../../../documentation/api/orgs/SDK_getOrgAsyncClaimStatus.md) |
| `getOrgE911Report` | [Stub](../../../../documentation/api/orgs/SDK_getOrgE911Report.md) |
| `getOrgMarvisClientInsights` | [Stub](../../../../documentation/api/orgs/SDK_getOrgMarvisClientInsights.md) |
| `importOrgAssetsFile` | [Stub](../../../../documentation/api/orgs/SDK_importOrgAssetsFile.md) |
| `importOrgMapToSiteFile` | [Stub](../../../../documentation/api/orgs/SDK_importOrgMapToSiteFile.md) |
| `importOrgMapsFile` | [Stub](../../../../documentation/api/orgs/SDK_importOrgMapsFile.md) |
| `importOrgNacCrlFile` | [Stub](../../../../documentation/api/orgs/SDK_importOrgNacCrlFile.md) |
| `importOrgPsksFile` | [Stub](../../../../documentation/api/orgs/SDK_importOrgPsksFile.md) |
| `importOrgUserMacsFile` | [Stub](../../../../documentation/api/orgs/SDK_importOrgUserMacsFile.md) |
| `listOrgAsyncClaims` | [Stub](../../../../documentation/api/orgs/SDK_listOrgAsyncClaims.md) |
| `searchOrgMarvisClientEvents` | [Stub](../../../../documentation/api/orgs/SDK_searchOrgMarvisClientEvents.md) |
| `searchOrgMarvisClientsStats` | [Stub](../../../../documentation/api/orgs/SDK_searchOrgMarvisClientsStats.md) |
| `sendOrgNacClientCoA` | [Stub](../../../../documentation/api/orgs/SDK_sendOrgNacClientCoA.md) |
| `updateOrgMxEdgeUpgrade` | [Stub](../../../../documentation/api/orgs/SDK_updateOrgMxEdgeUpgrade.md) |
| `uploadOrgNacPortalImageFile` | [Stub](../../../../documentation/api/orgs/SDK_uploadOrgNacPortalImageFile.md) |
| `uploadOrgPskPortalImageFile` | [Stub](../../../../documentation/api/orgs/SDK_uploadOrgPskPortalImageFile.md) |
| `uploadOrgWlanPortalImageFile` | [Stub](../../../../documentation/api/orgs/SDK_uploadOrgWlanPortalImageFile.md) |

### Site helpers

| Helper | Source |
| - | - |
| `acceptSiteApLocalizationData` | [Stub](../../../../documentation/api/sites/SDK_acceptSiteApLocalizationData.md) |
| `addSiteDeviceImageFile` | [Stub](../../../../documentation/api/sites/SDK_addSiteDeviceImageFile.md) |
| `addSiteMapImageFile` | [Stub](../../../../documentation/api/sites/SDK_addSiteMapImageFile.md) |
| `applySiteAutoMapAssignment` | [Stub](../../../../documentation/api/sites/SDK_applySiteAutoMapAssignment.md) |
| `attachSiteAssetImageFile` | [Stub](../../../../documentation/api/sites/SDK_attachSiteAssetImageFile.md) |
| `cancelSiteAutoMapAssignment` | [Stub](../../../../documentation/api/sites/SDK_cancelSiteAutoMapAssignment.md) |
| `cancelSiteMxEdgeUpgrade` | [Stub](../../../../documentation/api/sites/SDK_cancelSiteMxEdgeUpgrade.md) |
| `clearSiteAutoMapAssignment` | [Stub](../../../../documentation/api/sites/SDK_clearSiteAutoMapAssignment.md) |
| `countSiteClientFingerprints` | [Stub](../../../../documentation/api/sites/SDK_countSiteClientFingerprints.md) |
| `countSiteMarvisConfigActions` | [Stub](../../../../documentation/api/sites/SDK_countSiteMarvisConfigActions.md) |
| `deleteSiteMarvisConfigAction` | [Stub](../../../../documentation/api/sites/SDK_deleteSiteMarvisConfigAction.md) |
| `enableSiteDeviceZigbeeJoin` | [Stub](../../../../documentation/api/sites/SDK_enableSiteDeviceZigbeeJoin.md) |
| `getSiteAutoMapAssignmentStatus` | [Stub](../../../../documentation/api/sites/SDK_getSiteAutoMapAssignmentStatus.md) |
| `getSiteChannelScores` | [Stub](../../../../documentation/api/sites/SDK_getSiteChannelScores.md) |
| `getSiteInsightMetricsForAP` | [Stub](../../../../documentation/api/sites/SDK_getSiteInsightMetricsForAP.md) |
| `getSiteMxEdgeUpgrade` | [Stub](../../../../documentation/api/sites/SDK_getSiteMxEdgeUpgrade.md) |
| `importSiteAssetsFile` | [Stub](../../../../documentation/api/sites/SDK_importSiteAssetsFile.md) |
| `importSiteDevicesFile` | [Stub](../../../../documentation/api/sites/SDK_importSiteDevicesFile.md) |
| `importSiteMapsFile` | [Stub](../../../../documentation/api/sites/SDK_importSiteMapsFile.md) |
| `importSitePsksFile` | [Stub](../../../../documentation/api/sites/SDK_importSitePsksFile.md) |
| `listSiteMxEdgeUpgrades` | [Stub](../../../../documentation/api/sites/SDK_listSiteMxEdgeUpgrades.md) |
| `replaceSiteMapImageFile` | [Stub](../../../../documentation/api/sites/SDK_replaceSiteMapImageFile.md) |
| `searchSiteClientFingerprints` | [Stub](../../../../documentation/api/sites/SDK_searchSiteClientFingerprints.md) |
| `searchSiteIotEndpoints` | [Stub](../../../../documentation/api/sites/SDK_searchSiteIotEndpoints.md) |
| `searchSiteMarvisConfigActions` | [Stub](../../../../documentation/api/sites/SDK_searchSiteMarvisConfigActions.md) |
| `sendSiteNacClientCoA` | [Stub](../../../../documentation/api/sites/SDK_sendSiteNacClientCoA.md) |
| `startSiteAutoMapAssignment` | [Stub](../../../../documentation/api/sites/SDK_startSiteAutoMapAssignment.md) |
| `submitSiteMarvisConfigFeedback` | [Stub](../../../../documentation/api/sites/SDK_submitSiteMarvisConfigFeedback.md) |
| `updateSiteMxEdgeUpgrade` | [Stub](../../../../documentation/api/sites/SDK_updateSiteMxEdgeUpgrade.md) |
| `upgradeSiteMxEdges` | [Stub](../../../../documentation/api/sites/SDK_upgradeSiteMxEdges.md) |
| `uploadSiteWlanPortalImageFile` | [Stub](../../../../documentation/api/sites/SDK_uploadSiteWlanPortalImageFile.md) |

## Older-edition differences

Compare the [older JSON](../../../../documentation/mist-api-openapi3json.json) with the [primary JSON](../../../../documentation/mist-api-openapi31json.json).
The comparison uses exact `(method, path, operationId)` triples, not just path names.
There are 37 primary-only triples and 30 older-only triples.
The primary category index covers all 37 primary-only triples.

A changed triple can represent a corrected spelling or a moved path, not necessarily a new capability.
An absent triple is not proof of cloud deprecation.
Do not restore an older path automatically when a current request fails.

### Older management operations

These seven older-only triples require comparison before use:

| Method | Older path | Older `operationId` | Difference |
| - | - | - | - |
| DELETE | `/api/v1/sites/{site_id}/devices/{device_id}/image{image_number}` | `deleteSiteDeviceImage` | The primary path has `/image/{image_number}`. |
| POST | `/api/v1/sites/{site_id}/devices/{device_id}/image{image_number}` | `addSiteDeviceImage` | The primary path has `/image/{image_number}`. |
| GET | `/api/v1/orgs/{org_id}/mxedges/version` | `getOrgMxEdgeUpgradeInfo` | The primary path uses `versions`. |
| GET | `/api/v1/sites/{site_id}/analyze_spectrum` | `getSiteRunningSprectrumAnalysis` | The primary identifier is `getSiteRunningSpectrumAnalysis`. |
| POST | `/api/v1/sites/{site_id}/devices/{device_id}/show_bgp_rummary` | `showSiteDeviceBgpSummary` | The primary path uses `show_bgp_summary`. |
| PUT | `/api/v1/orgs/{org_id}/setting/{app_name}/link_accounts` | `updateOrgOauthAppAccount` | The primary path includes `/{account_id}`. |
| PUT | `/api/v1/sites/{site_id}/devices/{device_id}/set_ant_mode` | `setSiteApAntennaMode` | The primary edition contains no matching operation. |

### Older webhook payload examples

The older edition contains 23 `Samples` operations under `/webhook_example/`.
All use POST in the source, but these paths describe sample webhook payloads.
Do not send authenticated Mist management requests to them.
Read their request schemas as examples of receiver input.

| Method | Sample path | `operationId` |
| - | - | - |
| POST | `/webhook_example/_alarm_` | `alarms` |
| POST | `/webhook_example/_audit_` | `audits` |
| POST | `/webhook_example/_client_info_` | `clientInfo` |
| POST | `/webhook_example/_client_join_` | `clientJoin` |
| POST | `/webhook_example/_client_latency_` | `client_latency` |
| POST | `/webhook_example/_client_sessions_` | `clientSessions` |
| POST | `/webhook_example/_device_events_` | `deviceEvents` |
| POST | `/webhook_example/_device_updowns_` | `deviceUpDown` |
| POST | `/webhook_example/_discovered_raw_rssi_` | `discovered-raw-rssi` |
| POST | `/webhook_example/_guest_authorizations_` | `guestAuthorization` |
| POST | `/webhook_example/_location_` | `location` |
| POST | `/webhook_example/_location_asset_` | `location_asset` |
| POST | `/webhook_example/_location_centrak_` | `location_centrak` |
| POST | `/webhook_example/_location_client_` | `location_client` |
| POST | `/webhook_example/_location_sdk_` | `location_sdk` |
| POST | `/webhook_example/_location_unclient_` | `location_unclient` |
| POST | `/webhook_example/_nac_accounting_` | `nacAccounting` |
| POST | `/webhook_example/_nac_events_` | `nac_events` |
| POST | `/webhook_example/_occupancy_alerts_` | `occupancyAlerts` |
| POST | `/webhook_example/_ping_` | `ping` |
| POST | `/webhook_example/_sdkclient_scan_data` | `sdkclientScanData` |
| POST | `/webhook_example/_site_sle_` | `site_sle` |
| POST | `/webhook_example/_zone_` | `zone` |

## Saved guides and source fingerprints

### Narrative source routing

| Source | Subjects | Use |
| - | - | - |
| [Home](../../../../documentation/Home%20_%20API%20_%20Mist.html) | The original guide contents and category links. | Find the relevant saved guide rather than following operational example URLs. |
| [Overview](../../../../documentation/Overview%20_%20API%20_%20Mist.html) | Models, CRUD, permissions, CSRF, pagination, time, WebSocket, and rate limits. | Establish shared transport behavior. |
| [Auth](../../../../documentation/Auth%20_%20API%20_%20Mist.html) | Identity, login, MFA, OAuth, tokens, registration, recovery, audit, usage, and account deletion. | Establish identity and account workflow semantics. |
| [Org](../../../../documentation/Org%20_%20API%20_%20Mist.html) | Sites, groups, inventory, templates, settings, security, licenses, integrations, Mist Edge, and SSR. | Read organization workflows and inheritance rules. |
| [Site](../../../../documentation/Site%20_%20API%20_%20Mist.html) | WLANs, devices, maps, location, clients, ports, SLEs, captures, commands, upgrades, and clusters. | Read device-family requirements and asynchronous behavior. |
| [MSP](../../../../documentation/MSP%20_%20API%20_%20Mist.html) | Provider scope, customer organizations, groups, licenses, administrators, SSO, insights, and tickets. | Preserve provider/customer boundaries. |
| [Location guide](../../../../documentation/location%20services%20guide.txt) | Location services and deployment context. | Clarify location workflows without inventing HTTP contracts. |

The saved Home page contains online links. The matching local saved page remains the source for this task.
Do not mistake an example callback, signed URL, image URL, or verification URL for a reference to fetch.

For material absent from the primary index, search these guides by heading and exact path.
Record the HTML heading and the absence from the primary specification.
Do not claim complete machine-verified HTTP coverage of prose-only examples.

### Supporting MistHelper documents

| Source | Purpose |
| - | - |
| [Architecture](../../../../documentation/architecture.md) | Locate implementation responsibilities. |
| [Development setup](../../../../documentation/development-setup.md) | Prepare the environment and approved credential configuration. |
| [CLI reference](../../../../documentation/cli-reference.md) | Distinguish CLI behavior from API behavior. |
| [Quality gates](../../../../documentation/quality-gates.md) | Select the current implementation checks. |
| [Security](../../../../documentation/security.md) | Apply repository security guidance. |
| [Endpoint enrichment guide](../../../../documentation/api/ENRICHMENT_GUIDE.md) | Identify generated notes and regeneration effects. |
| [GET inventory report](../../../../documentation/MIST_API_GET_ENDPOINTS.md) | Read historical API inventory analysis. |
| [Missing-endpoint report](../../../../documentation/MIST_API_MISSING_ENDPOINTS.md) | Read historical implementation-gap analysis, not current coverage. |

### Public source hashes

These SHA-256 values identify the public source bytes checked on 2026-09-09 in the documentation worktree.
They do not identify or hash credentials.
Line-ending changes alter byte hashes, so compare parsed structures when checking content parity.

| Source | SHA-256 |
| - | - |
| `mist-api-openapi31json.json` | `240b7d774c9345df0cb0eff6db526330c9e5005517d1ae856615612c13aba282` |
| `mist-api-openapi31yaml.yaml` | `42ea161a5b32327687df7ee229af9453ce018ea38470ca41a0aa5ea8400bd01d` |
| `mist-api-openapi3json.json` | `28f7aa21e615c565665c8574939a5bfd502683dccb7fce95bc1d3710da748734` |
| `mist-api-openapi3yaml.yaml` | `b730f66d5c9612650d9b2265b95bc1ada8edf24beb308ad9076683d7adb24b1c` |
