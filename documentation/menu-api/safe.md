<!-- The tool python -m scripts.menu_api_map writes this page. Do not edit it by hand. -->

# Menu API endpoints: safe

This page lists the Mist API endpoints of the 79 menu options in the `safe` category.
A menu option in this category reads data and exports it. The --test run executes this category.

The index page explains how to read the map: [Menu API endpoint map](README.md).

## Overview

The overview diagram shows the SDK families that the menu options of this category use.
Each family node shows the number of menu options that use that family.
A menu option with three endpoints or more has a second diagram in its section.
That diagram links the menu option to the classes that send the requests, and each class to its endpoints.

```mermaid
flowchart LR
    root["safe: 79 menu<br/>options"]
    root --> f_orgs_sites["orgs/sites<br/>19 menu options"]
    root --> f_orgs_inventory["orgs/inventory<br/>12 menu options"]
    root --> f_orgs_devices["orgs/devices<br/>5 menu options"]
    root --> f_orgs_gatewaytemplates["orgs/gatewaytemplates<br/>5 menu options"]
    root --> f_orgs_stats["orgs/stats<br/>5 menu options"]
    root --> f_sites_devices["sites/devices<br/>5 menu options"]
    root --> f_orgs_jsi["orgs/jsi<br/>4 menu options"]
    root --> f_orgs_networktemplates["orgs/networktemplates<br/>4 menu options"]
    root --> f_orgs_admins["orgs/admins<br/>3 menu options"]
    root --> f_orgs_apitokens["orgs/apitokens<br/>3 menu options"]
    root --> f_orgs_clients["orgs/clients<br/>3 menu options"]
    root --> f_orgs_deviceprofiles["orgs/deviceprofiles<br/>3 menu options"]
    root --> more["71 more families"]
```

## Menu 1

- Title: Export a list of all sites in the organization
- Handler: `OrgSiteExporter.sites`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/sites` | [`orgs.sites.listOrgSites`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sites/list-org-sites) | [`OrgSiteExporter.sites`](../../src/export/org_site_exporter.py) | Reference |

## Menu 2

- Title: Export a list of sites with location and timezone info
- Handler: `OrgSiteExporter.sites_with_location`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/sites` | [`orgs.sites.listOrgSites`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sites/list-org-sites) | [`APICoreFetchUtils.all_sites_with_limit`](../../src/api/api_core_fetch_utils.py) | Call |

## Menu 3

- Title: Export all sites using the 'list' sites API endpoint (to SiteList_ListAPI.csv, only if not already present)
- Handler: `OrgSiteExporter.sites_list_api`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/sites` | [`orgs.sites.listOrgSites`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sites/list-org-sites) | [`APICoreFetchUtils.all_sites_with_limit`](../../src/api/api_core_fetch_utils.py) | Call |

## Menu 4

- Title: Export all current guest users and last 7 days of historical guests to CSV
- Handler: `lambda: (OrgSiteExporter.current_guests(), OrgSiteExporter.historical_guests())`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/guests/search` | [`orgs.guests.searchOrgGuestAuthorization`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/guests/search-org-guest-authorization) | [`OrgSiteExporter.current_guests`](../../src/export/org_site_exporter.py) | Call |

## Menu 5

- Title: Export E911 report for the organization
- Handler: `OrgExportUtils.e911_report`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/exports/e911_report` | [`orgs.exports.getOrgE911Report`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/reports/get-org-e911-report) | [`OrgExportUtils.e911_report`](../../src/export/org_export_utils.py) | Reference |

## Menu 6

- Title: Site Config Analysis - Scan all sites for zone, engagement dwell tag, and occupancy setting deviations
- Handler: `lambda: GlobalImportManager.SiteExportUtilsFactory().build().zone_config_analysis()`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`MainEntrypoint`](README.md#mainentrypoint), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 3

```mermaid
flowchart LR
    menu["Menu 6: Site Config<br/>Analysis - Scan all<br/>sites..."]
    menu --> c1["APICoreFetchUtils"]
    c1 --> e1["GET<br/>/api/v1/orgs<br/>/{org_id}/sites"]
    menu --> c2["_collect_one_setting"]
    c2 --> e2["GET<br/>/api/v1/sites<br/>/{site_id}/setting"]
    menu --> c3["_collect_one_zone"]
    c3 --> e3["GET<br/>/api/v1/sites<br/>/{site_id}/zones"]
```

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/sites` | [`orgs.sites.listOrgSites`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sites/list-org-sites) | [`APICoreFetchUtils.all_sites_with_limit`](../../src/api/api_core_fetch_utils.py) | Call |
| GET | `/api/v1/sites/{site_id}/setting` | [`sites.setting.getSiteSetting`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/setting/get-site-setting) | [`_collect_one_setting`](../../src/analytics/zone_analyzer.py) | Call |
| GET | `/api/v1/sites/{site_id}/zones` | [`sites.zones.listSiteZones`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/zones/list-site-zones) | [`_collect_one_zone`](../../src/analytics/zone_analyzer.py) | Call |

## Menu 7

- Title: Site Inventory Health Analysis - Find sites with APs missing switches/gateways, or with offline infrastructure
- Handler: `lambda: ExtractedSiteInventoryHealthAnalyzer.analyze(SiteInventoryHealthAnalyzerDeps(apisession=MainEntrypoint.context.apisession, mistapi=mistapi, get_org_i...`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`MainEntrypoint`](README.md#mainentrypoint), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 2

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/inventory` | [`orgs.inventory.getOrgInventory`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/inventory/get-org-inventory) | [`SiteInventoryHealthAnalyzer._fetch_devices`](../../src/analytics/site_inventory_health_analyzer.py) | Call |
| GET | `/api/v1/orgs/{org_id}/sites` | [`orgs.sites.listOrgSites`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sites/list-org-sites) | [`APICoreFetchUtils.all_sites_with_limit`](../../src/api/api_core_fetch_utils.py) | Call |

## Menu 8

- Title: Export the full inventory of devices in the organization
- Handler: `OrgInventoryExporter.inventory`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/inventory` | [`orgs.inventory.getOrgInventory`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/inventory/get-org-inventory) | [`OrgInventoryExporter.inventory`](../../src/export/org_inventory_exporter.py) | Reference |

## Menu 9

- Title: Export a list of all devices in the organization
- Handler: `OrgInventoryExporter.devices`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/devices` | [`orgs.devices.listOrgDevices`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/devices/list-org-devices) | [`OrgInventoryExporter.devices`](../../src/export/org_inventory_exporter.py) | Reference |

## Menu 10

- Title: Export a list of all devices with associated site and address info
- Handler: `OrgInventoryExporter.devices_with_site_info`
- Shared helpers: [`CacheUtils`](README.md#cacheutils), [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 2

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/inventory` | [`orgs.inventory.getOrgInventory`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/inventory/get-org-inventory) | [`APICoreFetchUtils.all_inventory_with_limit`](../../src/api/api_core_fetch_utils.py) | Call |
| GET | `/api/v1/orgs/{org_id}/sites` | [`orgs.sites.listOrgSites`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sites/list-org-sites) | [`APICoreFetchUtils.all_sites_with_limit`](../../src/api/api_core_fetch_utils.py) | Call |

## Menu 11

- Title: Export a list of gateways with associated site and address info
- Handler: `OrgInventoryExporter.gateways_with_site_info`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 2

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/inventory` | [`orgs.inventory.getOrgInventory`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/inventory/get-org-inventory) | [`APICoreFetchUtils.all_inventory_with_limit`](../../src/api/api_core_fetch_utils.py) | Call |
| GET | `/api/v1/orgs/{org_id}/sites` | [`orgs.sites.listOrgSites`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sites/list-org-sites) | [`APICoreFetchUtils.all_sites_with_limit`](../../src/api/api_core_fetch_utils.py) | Call |

## Menu 12

- Title: Export combined inventory with site and address info by calendar week
- Handler: `OrgInventoryExporter.combined_inventory_with_site_info`
- Shared helpers: [`CacheUtils`](README.md#cacheutils), [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 3

```mermaid
flowchart LR
    menu["Menu 12: Export<br/>combined inventory<br/>with site a..."]
    menu --> c1["OrgInventoryExporter"]
    c1 --> e1["GET<br/>/api/v1/orgs<br/>/{org_id}"]
    c1 --> e2["GET<br/>/api/v1/orgs<br/>/{org_id}/inventory"]
    menu --> c2["APICoreFetchUtils"]
    c2 --> e3["GET<br/>/api/v1/orgs<br/>/{org_id}/sites"]
```

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}` | [`orgs.orgs.getOrg`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/get-org) | [`OrgInventoryExporter._resolve_combined_inventory_org_name`](../../src/export/org_inventory_exporter.py) | Call |
| GET | `/api/v1/orgs/{org_id}/inventory` | [`orgs.inventory.getOrgInventory`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/inventory/get-org-inventory) | [`OrgInventoryExporter._fetch_and_persist_raw_inventory_variant`](../../src/export/org_inventory_exporter.py) | Call |
| GET | `/api/v1/orgs/{org_id}/sites` | [`orgs.sites.listOrgSites`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sites/list-org-sites) | [`APICoreFetchUtils.all_sites_with_limit`](../../src/api/api_core_fetch_utils.py) | Call |

## Menu 13

- Title: Export org device model counts, firmware version distribution, and versions per model (MSP-aware)
- Handler: `OrgDeviceInventorySummary.dispatch`
- Shared helpers: [`DataExporter`](README.md#dataexporter), [`InputUtils`](README.md#inpututils), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 4

```mermaid
flowchart LR
    menu["Menu 13: Export org<br/>device model counts,<br/>firmw..."]
    menu --> c1["OrgDeviceInventory<br/>SummaryCore"]
    c1 --> e1["GET<br/>/api/v1/orgs<br/>/{org_id}"]
    c1 --> e2["GET<br/>/api/v1/orgs<br/>/{org_id}/devices<br/>/search"]
    c1 --> e3["GET<br/>/api/v1/orgs<br/>/{org_id}/inventory"]
    menu --> c2["_call_list_msp_orgs"]
    c2 --> e4["GET<br/>/api/v1/msps<br/>/{msp_id}/orgs"]
```

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/msps/{msp_id}/orgs` | [`msps.orgs.listMspOrgs`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/msps/orgs/list-msp-orgs) | [`_call_list_msp_orgs`](../../src/inventory/org_device_inventory_msp.py) | Call |
| GET | `/api/v1/orgs/{org_id}` | [`orgs.orgs.getOrg`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/get-org) | [`OrgDeviceInventorySummaryCore._lookup_org_name_from_api`](../../src/inventory/org_device_inventory_summary.py) | Call |
| GET | `/api/v1/orgs/{org_id}/devices/search` | [`orgs.devices.searchOrgDevices`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/devices/search-org-devices) | [`OrgDeviceInventorySummaryCore._search_switch_page`](../../src/inventory/org_device_inventory_summary.py) | Call |
| GET | `/api/v1/orgs/{org_id}/inventory` | [`orgs.inventory.getOrgInventory`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/inventory/get-org-inventory) | [`OrgDeviceInventorySummaryCore._fetch_ap_inventory`](../../src/inventory/org_device_inventory_summary.py) | Call |

## Menu 15

- Title: Export statistics for all devices in the organization
- Handler: `OrgDeviceStatsExporter.device_stats`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/stats/devices` | [`orgs.stats.listOrgDevicesStats`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/stats/devices/list-org-devices-stats) | [`OrgDeviceStatsExporter.device_stats`](../../src/export/org_device_stats_exporter.py) | Reference |

## Menu 16

- Title: Export VPN peer path statistics for the organization
- Handler: `OrgDeviceStatsExporter.vpn_peer_stats`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/stats/vpn_peers/search` | [`orgs.stats.searchOrgPeerPathStats`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/stats/vpn-peers/search-org-peer-path-stats) | [`OrgDeviceStatsExporter.vpn_peer_stats`](../../src/export/org_device_stats_exporter.py) | Reference |

## Menu 17

- Title: Export all switch virtual chassis (VC/stacking) stats to CSV
- Handler: `OrgDeviceStatsExporter.switch_vc_stats`
- Shared helpers: [`CacheUtils`](README.md#cacheutils), [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 2

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/inventory` | [`orgs.inventory.getOrgInventory`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/inventory/get-org-inventory) | [`OrgInventoryExporter.inventory`](../../src/export/org_inventory_exporter.py) | Reference |
| GET | `/api/v1/sites/{site_id}/devices/{device_id}/vc` | [`sites.devices.getSiteDeviceVirtualChassis`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/devices/wired/virtual-chassis/get-site-device-virtual-chassis) | [`SwitchVcStatsService._fetch_vc_for_switch`](../../src/refactors/serial_cc/switch_vc_stats.py) | Call |

## Menu 20

- Title: Export all organization alarms from the past day
- Handler: `OrgAlarmEventExporter.alarms`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/alarms/search` | [`orgs.alarms.searchOrgAlarms`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/alarms/search-org-alarms) | [`OrgAlarmEventExporter.alarms`](../../src/export/org_alarm_event_exporter.py) | Reference |

## Menu 21

- Title: Export all device events from the past 24 hours
- Handler: `OrgAlarmEventExporter.device_events`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/devices/events/search` | [`orgs.devices.searchOrgDeviceEvents`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/devices/search-org-device-events) | [`OrgAlarmEventExporter.device_events`](../../src/export/org_alarm_event_exporter.py) | Call |

## Menu 22

- Title: Export audit logs for the organization (last 24 hours)
- Handler: `lambda: OrgExportUtils.audit_logs(full_history=False)`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/logs/search` | [`orgs.logs.listOrgAuditLogs`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/logs/list-org-audit-logs) | [`OrgExportUtils.audit_logs`](../../src/export/org_export_utils.py) | Call |

## Menu 23

- Title: Export self (admin account) audit log
- Handler: `SelfExportUtils.audit_logs`
- Shared helpers: [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/self/logs` | [`self.logs.listSelfAuditLogs`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/self/audit-logs/list-self-audit-logs) | [`SelfExportUtils.audit_logs`](../../src/export/self_export_utils.py) | Call |

## Menu 24

- Title: Export security events for the organization
- Handler: `OrgClientSecurityExporter.security_events`
- Shared helpers: [`CacheUtils`](README.md#cacheutils), [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 5

```mermaid
flowchart LR
    menu["Menu 24: Export<br/>security events for<br/>the organi..."]
    menu --> c1["SecurityEvents<br/>Service"]
    c1 --> e1["GET<br/>/api/v1/orgs<br/>/{org_id}<br/>/secintelprofiles"]
    c1 --> e2["GET<br/>/api/v1/orgs<br/>/{org_id}<br/>/secpolicies"]
    c1 --> e3["GET<br/>/api/v1/sites<br/>/{site_id}/insights<br/>/rogues/clients"]
    menu --> c2["OrgSiteExporter"]
    c2 --> e4["GET<br/>/api/v1/orgs<br/>/{org_id}/sites"]
    menu --> c3["_ROGUE_KINDS"]
    c3 --> e5["GET<br/>/api/v1/sites<br/>/{site_id}/insights<br/>/rogues"]
```

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/secintelprofiles` | [`orgs.secintelprofiles.listOrgSecIntelProfiles`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/secintel-profiles/list-org-sec-intel-profiles) | [`SecurityEventsService._build_flattened_specs`](../../src/refactors/serial_cc/security_events.py) | Call |
| GET | `/api/v1/orgs/{org_id}/secpolicies` | [`orgs.secpolicies.listOrgSecPolicies`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/security-policies/list-org-sec-policies) | [`SecurityEventsService._build_flattened_specs`](../../src/refactors/serial_cc/security_events.py) | Call |
| GET | `/api/v1/orgs/{org_id}/sites` | [`orgs.sites.listOrgSites`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sites/list-org-sites) | [`OrgSiteExporter.sites`](../../src/export/org_site_exporter.py) | Reference |
| GET | `/api/v1/sites/{site_id}/insights/rogues` | [`sites.insights.listSiteRogueAPs`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/rogues/list-site-rogue-a-ps) | [`_ROGUE_KINDS`](../../src/refactors/serial_cc/security_events.py) | Name |
| GET | `/api/v1/sites/{site_id}/insights/rogues/clients` | [`sites.insights.listSiteRogueClients`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/rogues/list-site-rogue-clients) | [`SecurityEventsService._export_rogue_combined`](../../src/refactors/serial_cc/security_events.py) | Name |

## Menu 25

- Title: Audit Log Analysis - Mermaid timeline + interactive HTML report
- Handler: `AuditAnalysisOps.audit_log_analysis`
- Shared helpers: [`CacheUtils`](README.md#cacheutils), [`ConfigUtils`](README.md#configutils), [`InputUtils`](README.md#inpututils), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/logs/search` | [`orgs.logs.listOrgAuditLogs`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/logs/list-org-audit-logs) | [`AuditAnalysisOps._fetch_filtered_audit_entries`](../../src/audit/audit_analysis_ops.py) | Call |

## Menu 26

- Title: Offline Device Report
- Handler: `OfflineDeviceReporter.execute`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`InputUtils`](README.md#inpututils), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 2

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/sites` | [`orgs.sites.listOrgSites`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sites/list-org-sites) | [`APICoreFetchUtils.all_sites_with_limit`](../../src/api/api_core_fetch_utils.py) | Call |
| GET | `/api/v1/orgs/{org_id}/stats/devices` | [`orgs.stats.listOrgDevicesStats`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/stats/devices/list-org-devices-stats) | [`OfflineDeviceReporter._fetch_data`](../../src/reports/offline_device_reporter.py) | Call |

## Menu 27

- Title: Export wireless client statistics for the organization
- Handler: `OrgClientSecurityExporter.wireless_clients`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/clients/search` | [`orgs.clients.searchOrgWirelessClients`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/clients/wireless/search-org-wireless-clients) | [`OrgClientSecurityExporter.wireless_clients`](../../src/export/org_client_security_exporter.py) | Reference |

## Menu 28

- Title: Export wired client statistics for the organization
- Handler: `OrgClientSecurityExporter.wired_clients`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/wired_clients/search` | [`orgs.wired_clients.searchOrgWiredClients`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/clients/wired/search-org-wired-clients) | [`OrgClientSecurityExporter.wired_clients`](../../src/export/org_client_security_exporter.py) | Reference |

## Menu 29

- Title: Export rogue client detections for the organization
- Handler: `OrgClientSecurityExporter.rogue_clients`
- Shared helpers: [`CacheUtils`](README.md#cacheutils), [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 3

```mermaid
flowchart LR
    menu["Menu 29: Export<br/>rogue client<br/>detections for th..."]
    menu --> c1["OrgClientSecurityExporter"]
    c1 --> e1["GET<br/>/api/v1/sites<br/>/{site_id}/insights<br/>/rogues"]
    c1 --> e2["GET<br/>/api/v1/sites<br/>/{site_id}/insights<br/>/rogues/clients"]
    menu --> c2["OrgSiteExporter"]
    c2 --> e3["GET<br/>/api/v1/orgs<br/>/{org_id}/sites"]
```

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/sites` | [`orgs.sites.listOrgSites`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sites/list-org-sites) | [`OrgSiteExporter.sites`](../../src/export/org_site_exporter.py) | Reference |
| GET | `/api/v1/sites/{site_id}/insights/rogues` | [`sites.insights.listSiteRogueAPs`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/rogues/list-site-rogue-a-ps) | [`OrgClientSecurityExporter._export_rogues`](../../src/export/org_client_security_exporter.py) | Name |
| GET | `/api/v1/sites/{site_id}/insights/rogues/clients` | [`sites.insights.listSiteRogueClients`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/rogues/list-site-rogue-clients) | [`OrgClientSecurityExporter.rogue_clients`](../../src/export/org_client_security_exporter.py) | Reference |

## Menu 30

- Title: Export rogue AP detections for the organization
- Handler: `OrgClientSecurityExporter.rogue_aps`
- Shared helpers: [`CacheUtils`](README.md#cacheutils), [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 2

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/sites` | [`orgs.sites.listOrgSites`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sites/list-org-sites) | [`OrgSiteExporter.sites`](../../src/export/org_site_exporter.py) | Reference |
| GET | `/api/v1/sites/{site_id}/insights/rogues` | [`sites.insights.listSiteRogueAPs`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/rogues/list-site-rogue-a-ps) | [`OrgClientSecurityExporter.rogue_aps`](../../src/export/org_client_security_exporter.py) | Reference |

## Menu 31

- Title: Export gateway management overlay IPs grouped by template association
- Handler: `_dispatch_gateway_management_ips`
- Shared helpers: [`CacheUtils`](README.md#cacheutils), [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`MainEntrypoint`](README.md#mainentrypoint), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 6

```mermaid
flowchart LR
    menu["Menu 31: Export<br/>gateway management<br/>overlay IPs..."]
    menu --> c1["GatewayExportUtils"]
    c1 --> e1["GET<br/>/api/v1/orgs<br/>/{org_id}<br/>/gatewaytemplates"]
    c1 --> e2["GET<br/>/api/v1/sites<br/>/{site_id}/devices"]
    c1 --> e3["GET<br/>/api/v1/sites<br/>/{site_id}/stats<br/>/ports/search"]
    menu --> c2["APICoreFetchUtils"]
    c2 --> e4["GET<br/>/api/v1/orgs<br/>/{org_id}/inventory"]
    c2 --> e5["GET<br/>/api/v1/orgs<br/>/{org_id}/sites"]
    menu --> c3["APIFetchUtils"]
    c3 --> e6["GET<br/>/api/v1/sites<br/>/{site_id}/devices<br/>/{device_id}"]
```

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/gatewaytemplates` | [`orgs.gatewaytemplates.listOrgGatewayTemplates`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/gateway-templates/list-org-gateway-templates) | [`GatewayExportUtils.templates`](../../src/gateway/gateway_export_utils.py) | Call |
| GET | `/api/v1/orgs/{org_id}/inventory` | [`orgs.inventory.getOrgInventory`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/inventory/get-org-inventory) | [`APICoreFetchUtils.all_inventory_with_limit`](../../src/api/api_core_fetch_utils.py) | Call |
| GET | `/api/v1/orgs/{org_id}/sites` | [`orgs.sites.listOrgSites`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sites/list-org-sites) | [`APICoreFetchUtils.all_sites_with_limit`](../../src/api/api_core_fetch_utils.py) | Call |
| GET | `/api/v1/sites/{site_id}/devices` | [`sites.devices.listSiteDevices`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/devices/list-site-devices) | [`GatewayExportUtils._finalise_management_ip_output`](../../src/gateway/gateway_export_utils.py) | Name |
| GET | `/api/v1/sites/{site_id}/devices/{device_id}` | [`sites.devices.getSiteDevice`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/devices/get-site-device) | [`APIFetchUtils._gw_fetch_one_config`](../../src/api/api_fetch_utils.py) | Call |
| GET | `/api/v1/sites/{site_id}/stats/ports/search` | [`sites.stats.searchSiteSwOrGwPorts`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/stats/ports/search-site-sw-or-gw-ports) | [`GatewayExportUtils._save_filtered_port_configs`](../../src/gateway/gateway_export_utils.py) | Name |

## Menu 32

- Title: Export gateway templates from the organization
- Handler: `_dispatch_gateway_templates`
- Shared helpers: [`CacheUtils`](README.md#cacheutils), [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`MainEntrypoint`](README.md#mainentrypoint)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/gatewaytemplates` | [`orgs.gatewaytemplates.listOrgGatewayTemplates`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/gateway-templates/list-org-gateway-templates) | [`GatewayExportUtils.templates`](../../src/gateway/gateway_export_utils.py) | Call |

## Menu 33

- Title: Export synthetic test results for all gateways
- Handler: `GatewayTestExporter.synthetic_tests`
- Shared helpers: [`CacheUtils`](README.md#cacheutils), [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`RateLimitingUtils`](README.md#ratelimitingutils), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 3

```mermaid
flowchart LR
    menu["Menu 33: Export<br/>synthetic test<br/>results for all..."]
    menu --> c1["APICoreFetchUtils"]
    c1 --> e1["GET<br/>/api/v1/orgs<br/>/{org_id}/inventory"]
    menu --> c2["GatewayTestExporter"]
    c2 --> e2["GET<br/>/api/v1/sites<br/>/{site_id}/devices<br/>/{device_id}<br/>/synthetic_test"]
    menu --> c3["_fetch_site_name<br/>_lookup_from_api"]
    c3 --> e3["GET<br/>/api/v1/orgs<br/>/{org_id}/sites"]
```

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/inventory` | [`orgs.inventory.getOrgInventory`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/inventory/get-org-inventory) | [`APICoreFetchUtils.all_inventory_with_limit`](../../src/api/api_core_fetch_utils.py) | Call |
| GET | `/api/v1/orgs/{org_id}/sites` | [`orgs.sites.listOrgSites`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sites/list-org-sites) | [`_fetch_site_name_lookup_from_api`](../../src/gateway/gateway_export_utils.py) | Call |
| GET | `/api/v1/sites/{site_id}/devices/{device_id}/synthetic_test` | [`sites.devices.getSiteDeviceSyntheticTest`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/synthetic-tests/get-site-device-synthetic-test) | [`GatewayTestExporter._call_synthetic_endpoint`](../../src/export/gateway_test_exporter.py) | Call |

## Menu 34

- Title: Export all synthetic test results (including speed tests) for gateways
- Handler: `GatewayTestExporter.test_results_by_site`
- Shared helpers: [`CacheUtils`](README.md#cacheutils), [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`RateLimitingUtils`](README.md#ratelimitingutils), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 2

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/inventory` | [`orgs.inventory.getOrgInventory`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/inventory/get-org-inventory) | [`APICoreFetchUtils.all_inventory_with_limit`](../../src/api/api_core_fetch_utils.py) | Call |
| GET | `/api/v1/sites/{site_id}/synthetic_test/search` | [`sites.synthetic_test.searchSiteSyntheticTest`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/synthetic-tests/search-site-synthetic-test) | [`GatewayTestResultsService._invoke_search_api`](../../src/refactors/serial_cc/test_results_by_site.py) | Call |

## Menu 35

- Title: Find gateway ports overridden from template (outliers for compliance correction)
- Handler: `_dispatch_gateway_with_wan_overrides`
- Shared helpers: [`CacheUtils`](README.md#cacheutils), [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`MainEntrypoint`](README.md#mainentrypoint), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 6

```mermaid
flowchart LR
    menu["Menu 35: Find<br/>gateway ports<br/>overridden from<br/>te..."]
    menu --> c1["DeviceDataFetcher"]
    c1 --> e1["GET<br/>/api/v1/sites<br/>/{site_id}/devices<br/>/{device_id}"]
    c1 --> e2["GET<br/>/api/v1/sites<br/>/{site_id}/stats<br/>/devices/{device_id}"]
    menu --> c2["GatewayExportUtils"]
    c2 --> e3["GET<br/>/api/v1/sites<br/>/{site_id}/devices"]
    c2 --> e4["GET<br/>/api/v1/sites<br/>/{site_id}/stats<br/>/ports/search"]
    menu --> c3["APICoreFetchUtils"]
    c3 --> e5["GET<br/>/api/v1/orgs<br/>/{org_id}/sites"]
    menu --> c4["APIFetchUtils"]
    c4 --> e6["GET<br/>/api/v1/orgs<br/>/{org_id}/inventory"]
```

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/inventory` | [`orgs.inventory.getOrgInventory`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/inventory/get-org-inventory) | [`APIFetchUtils._gw_load_inventory`](../../src/api/api_fetch_utils.py) | Call |
| GET | `/api/v1/orgs/{org_id}/sites` | [`orgs.sites.listOrgSites`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sites/list-org-sites) | [`APICoreFetchUtils.all_sites_with_limit`](../../src/api/api_core_fetch_utils.py) | Call |
| GET | `/api/v1/sites/{site_id}/devices` | [`sites.devices.listSiteDevices`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/devices/list-site-devices) | [`GatewayExportUtils.device_configs`](../../src/gateway/gateway_export_utils.py) | Name |
| GET | `/api/v1/sites/{site_id}/devices/{device_id}` | [`sites.devices.getSiteDevice`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/devices/get-site-device) | [`DeviceDataFetcher._fetch_port_configs`](../../src/gateway/overrides/device_data_fetcher.py) | Call |
| GET | `/api/v1/sites/{site_id}/stats/devices/{device_id}` | [`sites.stats.getSiteDeviceStats`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/stats/devices/get-site-device-stats) | [`DeviceDataFetcher._fetch_interface_stats`](../../src/gateway/overrides/device_data_fetcher.py) | Call |
| GET | `/api/v1/sites/{site_id}/stats/ports/search` | [`sites.stats.searchSiteSwOrGwPorts`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/stats/ports/search-site-sw-or-gw-ports) | [`GatewayExportUtils._save_filtered_port_configs`](../../src/gateway/gateway_export_utils.py) | Name |

## Menu 36

- Title: Check and export gateways with duplicate WAN port IP addresses (0/0/0, 0/0/1, 0/0/2)
- Handler: `_dispatch_gateway_stats_wan_port_conflicts`
- Shared helpers: [`CacheUtils`](README.md#cacheutils), [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`MainEntrypoint`](README.md#mainentrypoint), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 3

```mermaid
flowchart LR
    menu["Menu 36: Check and<br/>export gateways with<br/>duplic..."]
    menu --> c1["APICoreFetchUtils"]
    c1 --> e1["GET<br/>/api/v1/orgs<br/>/{org_id}/inventory"]
    menu --> c2["_call_get_site<br/>_device_stats"]
    c2 --> e2["GET<br/>/api/v1/sites<br/>/{site_id}/stats<br/>/devices/{device_id}"]
    menu --> c3["_fetch_site_name<br/>_lookup_from_api"]
    c3 --> e3["GET<br/>/api/v1/orgs<br/>/{org_id}/sites"]
```

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/inventory` | [`orgs.inventory.getOrgInventory`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/inventory/get-org-inventory) | [`APICoreFetchUtils.all_inventory_with_limit`](../../src/api/api_core_fetch_utils.py) | Call |
| GET | `/api/v1/orgs/{org_id}/sites` | [`orgs.sites.listOrgSites`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sites/list-org-sites) | [`_fetch_site_name_lookup_from_api`](../../src/gateway/gateway_export_utils.py) | Call |
| GET | `/api/v1/sites/{site_id}/stats/devices/{device_id}` | [`sites.stats.getSiteDeviceStats`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/stats/devices/get-site-device-stats) | [`_call_get_site_device_stats`](../../src/gateway/gateway_stats_exporter.py) | Call |

## Menu 37

- Title: Export all organization templates (gateway, network, RF, site, AP)
- Handler: `OrgTemplateExporter.all_templates`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 5

```mermaid
flowchart LR
    menu["Menu 37: Export all<br/>organization<br/>templates gat..."]
    menu --> c1["OrgTemplateExporter"]
    c1 --> e1["GET<br/>/api/v1/orgs<br/>/{org_id}<br/>/aptemplates"]
    c1 --> e2["GET<br/>/api/v1/orgs<br/>/{org_id}<br/>/gatewaytemplates"]
    c1 --> e3["GET<br/>/api/v1/orgs<br/>/{org_id}<br/>/networktemplates"]
    c1 --> e4["GET<br/>/api/v1/orgs<br/>/{org_id}<br/>/rftemplates"]
    c1 --> e5["GET<br/>/api/v1/orgs<br/>/{org_id}<br/>/sitetemplates"]
```

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/aptemplates` | [`orgs.aptemplates.listOrgAptemplates`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/ap-templates/list-org-aptemplates) | [`OrgTemplateExporter._template_export_specs`](../../src/export/org_template_exporter.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/gatewaytemplates` | [`orgs.gatewaytemplates.listOrgGatewayTemplates`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/gateway-templates/list-org-gateway-templates) | [`OrgTemplateExporter._template_export_specs`](../../src/export/org_template_exporter.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/networktemplates` | [`orgs.networktemplates.listOrgNetworkTemplates`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/network-templates/list-org-network-templates) | [`OrgTemplateExporter._template_export_specs`](../../src/export/org_template_exporter.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/rftemplates` | [`orgs.rftemplates.listOrgRfTemplates`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/rf-templates/list-org-rf-templates) | [`OrgTemplateExporter._template_export_specs`](../../src/export/org_template_exporter.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/sitetemplates` | [`orgs.sitetemplates.listOrgSiteTemplates`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/site-templates/list-org-site-templates) | [`OrgTemplateExporter._template_export_specs`](../../src/export/org_template_exporter.py) | Reference |

## Menu 38

- Title: Export network template information for the organization
- Handler: `OrgTemplateExporter.network_templates`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/networktemplates` | [`orgs.networktemplates.listOrgNetworkTemplates`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/network-templates/list-org-network-templates) | [`OrgTemplateExporter.network_templates`](../../src/export/org_template_exporter.py) | Reference |

## Menu 39

- Title: Export RF template information for the organization
- Handler: `OrgTemplateExporter.rf_templates`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/rftemplates` | [`orgs.rftemplates.listOrgRfTemplates`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/rf-templates/list-org-rf-templates) | [`OrgTemplateExporter.rf_templates`](../../src/export/org_template_exporter.py) | Reference |

## Menu 40

- Title: Export AP template information for the organization
- Handler: `OrgTemplateExporter.ap_templates`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/deviceprofiles` | [`orgs.deviceprofiles.listOrgDeviceProfiles`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/device-profiles/list-org-device-profiles) | [`OrgTemplateExporter.ap_templates`](../../src/export/org_template_exporter.py) | Call |

## Menu 41

- Title: Export switch template information for the organization
- Handler: `OrgTemplateExporter.switch_templates`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/networktemplates` | [`orgs.networktemplates.listOrgNetworkTemplates`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/network-templates/list-org-network-templates) | [`OrgTemplateExporter.switch_templates`](../../src/export/org_template_exporter.py) | Call |

## Menu 42

- Title: Export license information for the organization
- Handler: `OrgAdminExporter.licenses`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{current_org_id}/licenses` | None (raw request) | [`OrgAdminExporter._fetch_license_payload`](../../src/export/org_admin_exporter.py) | Path |

## Menu 43

- Title: Export license usage information for the organization
- Handler: `OrgAdminExporter.usage`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/licenses/usages` | [`orgs.licenses.getOrgLicensesBySite`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/licenses/get-org-licenses-by-site) | [`OrgAdminExporter.usage`](../../src/export/org_admin_exporter.py) | Reference |

## Menu 44

- Title: Export PSK (Pre-Shared Key) information for the organization
- Handler: `OrgConfigExporter.psks`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/psks` | [`orgs.psks.listOrgPsks`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/psks/list-org-psks) | [`OrgConfigExporter.psks`](../../src/export/org_config_exporter.py) | Reference |

## Menu 45

- Title: Export webhook configuration for the organization
- Handler: `OrgConfigExporter.webhooks`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/webhooks` | [`orgs.webhooks.listOrgWebhooks`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/webhooks/list-org-webhooks) | [`OrgConfigExporter.webhooks`](../../src/export/org_config_exporter.py) | Reference |

## Menu 46

- Title: Export WLAN configuration for the organization
- Handler: `OrgConfigExporter.wlans`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/wlans` | [`orgs.wlans.listOrgWlans`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/wlans/list-org-wlans) | [`OrgConfigExporter.wlans`](../../src/export/org_config_exporter.py) | Reference |

## Menu 47

- Title: Export API token information for the organization
- Handler: `OrgAdminExporter.api_tokens`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/apitokens` | [`orgs.apitokens.listOrgApiTokens`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/api-tokens/list-org-api-tokens) | [`OrgAdminExporter.api_tokens`](../../src/export/org_admin_exporter.py) | Reference |

## Menu 48

- Title: Export administrator information for the organization
- Handler: `OrgAdminExporter.admins`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/admins` | [`orgs.admins.listOrgAdmins`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/admins/list-org-admins) | [`OrgAdminExporter.admins`](../../src/export/org_admin_exporter.py) | Reference |

## Menu 49

- Title: Export SSO (Single Sign-On) information for the organization
- Handler: `OrgAdminExporter.sso`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/ssos` | [`orgs.ssos.listOrgSsos`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sso/list-org-ssos) | [`OrgAdminExporter.sso`](../../src/export/org_admin_exporter.py) | Reference |

## Menu 50

- Title: Export MX Edge information for the organization
- Handler: `OrgConfigExporter.mx_edges`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/mxedges` | [`orgs.mxedges.listOrgMxEdges`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/mxedges/list-org-mx-edges) | [`OrgConfigExporter.mx_edges`](../../src/export/org_config_exporter.py) | Reference |

## Menu 51

- Title: Export Organization SLE Metrics (Service Level Experience)
- Handler: `OrgExportUtils.sle_metrics`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 2

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/insights/sites-sle` | [`orgs.insights.getOrgSitesSle`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sles/get-org-sites-sle) | [`SLEMetricsService._fetch_aggregated_category`](../../src/refactors/serial_cc/sle_metrics.py) | Call |
| GET | `/api/v1/orgs/{org_id}/insights/{metric}` | [`orgs.insights.getOrgSle`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sles/get-org-sle) | [`SLEMetricsService._fetch_single_sle`](../../src/refactors/serial_cc/sle_metrics.py) | Call |

## Menu 52

- Title: Export SLE summary metrics for all sites in the organization
- Handler: `OrgExportUtils.sites_sle_summary`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/insights/sites-sle` | [`orgs.insights.getOrgSitesSle`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sles/get-org-sites-sle) | [`OrgExportUtils._collect_one_sle_type`](../../src/export/org_export_utils.py) | Call |

## Menu 53

- Title: Export Organization Insight Metrics (comprehensive operational insights)
- Handler: `OrgExportUtils.insight_metrics`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 30

```mermaid
flowchart LR
    menu["Menu 53: Export<br/>Organization Insight<br/>Metrics c..."]
    menu --> c1["ConstDefinitionsExporter"]
    c1 --> e1["GET<br/>/api/v1/const<br/>/alarm_defs"]
    c1 --> e2["GET<br/>/api/v1/const<br/>/ap_channels"]
    c1 --> e3["GET<br/>/api/v1/const<br/>/ap_esl_versions"]
    c1 --> e4["GET<br/>/api/v1/const<br/>/ap_led_status"]
    c1 --> e5["GET<br/>/api/v1/const<br/>/app_categories"]
    c1 --> e6["GET<br/>/api/v1/const<br/>/app_subcategories"]
    c1 --> e7["GET<br/>/api/v1/const<br/>/applications"]
    c1 --> e8["GET<br/>/api/v1/const<br/>/client_events"]
    c1 --> e9["GET<br/>/api/v1/const<br/>/countries"]
    c1 --> e10["GET<br/>/api/v1/const<br/>/default_gateway_config"]
    c1 --> e11["GET<br/>/api/v1/const<br/>/device_events"]
    c1 --> e12["GET<br/>/api/v1/const<br/>/device_models"]
    menu --> more["18 more endpoints in<br/>the table"]
```

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/const/alarm_defs` | [`const.alarm_defs.listAlarmDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/events/list-alarm-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/ap_channels` | [`const.ap_channels.listApChannels`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-ap-channels) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/ap_esl_versions` | [`const.ap_esl_versions.listApLEslVersions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-ap-l-esl-versions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/ap_led_status` | [`const.ap_led_status.listApLedDefinition`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-ap-led-definition) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/app_categories` | [`const.app_categories.listAppCategoryDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-app-category-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/app_subcategories` | [`const.app_subcategories.listAppSubCategoryDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-app-sub-category-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/applications` | [`const.applications.listApplications`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-applications) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/client_events` | [`const.client_events.listClientEventsDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/events/list-client-events-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/countries` | [`const.countries.listCountryCodes`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-country-codes) | [`ConstDefinitionsExporter._get_channel_country_codes`](../../src/export/const_definitions_exporter.py) | Reference |
| GET | `/api/v1/const/default_gateway_config` | [`const.default_gateway_config.getGatewayDefaultConfig`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/models/get-gateway-default-config) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/device_events` | [`const.device_events.listDeviceEventsDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/events/list-device-events-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/device_models` | [`const.device_models.listDeviceModels`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/models/list-device-models) | [`ConstDefinitionsExporter._get_gateway_models_list`](../../src/export/const_definitions_exporter.py) | Reference |
| GET | `/api/v1/const/fingerprint_types` | [`const.fingerprint_types.listFingerprintTypes`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-fingerprint-types) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/gateway_applications` | [`const.gateway_applications.listGatewayApplications`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-gateway-applications) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/insight_metrics` | [`const.insight_metrics.listInsightMetrics`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-insight-metrics) | [`OrgExportUtils._load_parameterized_metric_choices`](../../src/export/org_export_utils.py) | Call |
| GET | `/api/v1/const/languages` | [`const.languages.listSiteLanguages`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-site-languages) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/license_types` | [`const.license_types.listLicenseTypes`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-license-types) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/marvisclient_events` | [`const.marvisclient_events.listMarvisClientEventsDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-marvis-client-events-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/marvisclient_versions` | [`const.marvisclient_versions.listMarvisClientVersions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-marvis-client-versions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/mxedge_events` | [`const.mxedge_events.listMxEdgeEventsDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/events/list-mx-edge-events-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/mxedge_models` | [`const.mxedge_models.listMxEdgeModels`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/models/list-mx-edge-models) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/nac_events` | [`const.nac_events.listNacEventsDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/events/list-nac-events-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/otherdevice_events` | [`const.otherdevice_events.listOtherDeviceEventsDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/events/list-other-device-events-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/otherdevice_models` | [`const.otherdevice_models.listSupportedOtherDeviceModels`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/models/list-supported-other-device-models) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/states` | [`const.states.listStates`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-states) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/system_events` | [`const.system_events.listSystemEventsDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/events/list-system-events-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/traffic_types` | [`const.traffic_types.listTrafficTypes`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-traffic-types) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/webhook_topics` | [`const.webhook_topics.listWebhookTopics`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-webhook-topics) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/orgs/{org_id}/insights/sites-sle` | [`orgs.insights.getOrgSitesSle`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sles/get-org-sites-sle) | [`OrgExportUtils._insight_fetch_sites_sle_summary`](../../src/export/org_export_utils.py) | Call |
| GET | `/api/v1/orgs/{org_id}/insights/{metric}` | [`orgs.insights.getOrgSle`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sles/get-org-sle) | [`OrgExportUtils._insight_fetch_default_metric`](../../src/export/org_export_utils.py) | Call |

## Menu 54

- Title: Export all available const definitions from the Mist API (comprehensive endpoint coverage)
- Handler: `lambda: ConstDefinitionsExporter(MainEntrypoint.context.apisession).export_all()`
- Shared helpers: [`DataExporter`](README.md#dataexporter), [`MainEntrypoint`](README.md#mainentrypoint), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 28

```mermaid
flowchart LR
    menu["Menu 54: Export all<br/>available const<br/>definition..."]
    menu --> c1["ConstDefinitionsExporter"]
    c1 --> e1["GET<br/>/api/v1/const<br/>/alarm_defs"]
    c1 --> e2["GET<br/>/api/v1/const<br/>/ap_channels"]
    c1 --> e3["GET<br/>/api/v1/const<br/>/ap_esl_versions"]
    c1 --> e4["GET<br/>/api/v1/const<br/>/ap_led_status"]
    c1 --> e5["GET<br/>/api/v1/const<br/>/app_categories"]
    c1 --> e6["GET<br/>/api/v1/const<br/>/app_subcategories"]
    c1 --> e7["GET<br/>/api/v1/const<br/>/applications"]
    c1 --> e8["GET<br/>/api/v1/const<br/>/client_events"]
    c1 --> e9["GET<br/>/api/v1/const<br/>/countries"]
    c1 --> e10["GET<br/>/api/v1/const<br/>/default_gateway_config"]
    c1 --> e11["GET<br/>/api/v1/const<br/>/device_events"]
    c1 --> e12["GET<br/>/api/v1/const<br/>/device_models"]
    menu --> more["16 more endpoints in<br/>the table"]
```

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/const/alarm_defs` | [`const.alarm_defs.listAlarmDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/events/list-alarm-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/ap_channels` | [`const.ap_channels.listApChannels`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-ap-channels) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/ap_esl_versions` | [`const.ap_esl_versions.listApLEslVersions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-ap-l-esl-versions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/ap_led_status` | [`const.ap_led_status.listApLedDefinition`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-ap-led-definition) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/app_categories` | [`const.app_categories.listAppCategoryDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-app-category-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/app_subcategories` | [`const.app_subcategories.listAppSubCategoryDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-app-sub-category-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/applications` | [`const.applications.listApplications`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-applications) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/client_events` | [`const.client_events.listClientEventsDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/events/list-client-events-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/countries` | [`const.countries.listCountryCodes`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-country-codes) | [`ConstDefinitionsExporter._get_channel_country_codes`](../../src/export/const_definitions_exporter.py) | Reference |
| GET | `/api/v1/const/default_gateway_config` | [`const.default_gateway_config.getGatewayDefaultConfig`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/models/get-gateway-default-config) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/device_events` | [`const.device_events.listDeviceEventsDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/events/list-device-events-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/device_models` | [`const.device_models.listDeviceModels`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/models/list-device-models) | [`ConstDefinitionsExporter._get_gateway_models_list`](../../src/export/const_definitions_exporter.py) | Reference |
| GET | `/api/v1/const/fingerprint_types` | [`const.fingerprint_types.listFingerprintTypes`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-fingerprint-types) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/gateway_applications` | [`const.gateway_applications.listGatewayApplications`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-gateway-applications) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/insight_metrics` | [`const.insight_metrics.listInsightMetrics`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-insight-metrics) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/languages` | [`const.languages.listSiteLanguages`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-site-languages) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/license_types` | [`const.license_types.listLicenseTypes`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-license-types) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/marvisclient_events` | [`const.marvisclient_events.listMarvisClientEventsDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-marvis-client-events-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/marvisclient_versions` | [`const.marvisclient_versions.listMarvisClientVersions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-marvis-client-versions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/mxedge_events` | [`const.mxedge_events.listMxEdgeEventsDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/events/list-mx-edge-events-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/mxedge_models` | [`const.mxedge_models.listMxEdgeModels`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/models/list-mx-edge-models) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/nac_events` | [`const.nac_events.listNacEventsDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/events/list-nac-events-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/otherdevice_events` | [`const.otherdevice_events.listOtherDeviceEventsDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/events/list-other-device-events-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/otherdevice_models` | [`const.otherdevice_models.listSupportedOtherDeviceModels`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/models/list-supported-other-device-models) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/states` | [`const.states.listStates`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-states) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/system_events` | [`const.system_events.listSystemEventsDefinitions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/events/list-system-events-definitions) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/traffic_types` | [`const.traffic_types.listTrafficTypes`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-traffic-types) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |
| GET | `/api/v1/const/webhook_topics` | [`const.webhook_topics.listWebhookTopics`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/constants/definitions/list-webhook-topics) | [`ConstDefinitionsExporter._discover_endpoints`](../../src/export/const_definitions_exporter.py) | Curated |

## Menu 55

- Title: Export OSPF adjacency statistics for the organization
- Handler: `OrgExportUtils.ospf_stats`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/stats/ospf_peers/search` | [`orgs.stats.searchOrgOspfStats`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/stats/ospf/search-org-ospf-stats) | [`OrgExportUtils.ospf_stats`](../../src/export/org_export_utils.py) | Reference |

## Menu 56

- Title: Export JSI PBN (Product Bulletin Notifications) data
- Handler: `OrgExportUtils.jsi_pbn`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/jsi/pbn/search` | [`orgs.jsi.searchOrgJsiPbn`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/jsi/search-org-jsi-pbn) | [`OrgExportUtils.jsi_pbn`](../../src/export/org_export_utils.py) | Reference |

## Menu 57

- Title: Export JSI SIRT (Security Incident Response) advisories
- Handler: `OrgExportUtils.jsi_sirt`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/jsi/sirt/search` | [`orgs.jsi.searchOrgJsiSirt`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/jsi/search-org-jsi-sirt) | [`OrgExportUtils.jsi_sirt`](../../src/export/org_export_utils.py) | Reference |

## Menu 58

- Title: Export Org WAN/Gateway Config (JSON bundle for cross-org migration)
- Handler: `lambda: cast(Any, OrgConfigMigrationManager)(MainEntrypoint.context.apisession, ConfigUtils.get_cached_or_prompted_org_id, InputUtils.safe_input).export_conf...`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`InputUtils`](README.md#inpututils), [`MainEntrypoint`](README.md#mainentrypoint)
- Endpoints: 13

```mermaid
flowchart LR
    menu["Menu 58: Export Org<br/>WAN/Gateway Config<br/>JSON bu..."]
    menu --> c1["OrgConfigMigrationManager"]
    c1 --> e1["GET<br/>/api/v1/orgs<br/>/{org_id}"]
    c1 --> e2["GET<br/>/api/v1/orgs<br/>/{org_id}<br/>/deviceprofiles"]
    c1 --> e3["POST<br/>/api/v1/orgs<br/>/{org_id}<br/>/deviceprofiles"]
    c1 --> e4["GET<br/>/api/v1/orgs<br/>/{org_id}<br/>/gatewaytemplates"]
    c1 --> e5["POST<br/>/api/v1/orgs<br/>/{org_id}<br/>/gatewaytemplates"]
    c1 --> e6["GET<br/>/api/v1/orgs<br/>/{org_id}/networks"]
    c1 --> e7["POST<br/>/api/v1/orgs<br/>/{org_id}/networks"]
    c1 --> e8["GET<br/>/api/v1/orgs<br/>/{org_id}<br/>/servicepolicies"]
    c1 --> e9["POST<br/>/api/v1/orgs<br/>/{org_id}<br/>/servicepolicies"]
    c1 --> e10["GET<br/>/api/v1/orgs<br/>/{org_id}/services"]
    c1 --> e11["POST<br/>/api/v1/orgs<br/>/{org_id}/services"]
    c1 --> e12["GET<br/>/api/v1/orgs<br/>/{org_id}/vpns"]
    menu --> more["1 more endpoint in<br/>the table"]
```

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}` | [`orgs.orgs.getOrg`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/get-org) | [`OrgConfigMigrationManager._get_org_name`](../../src/org/org_config_migration_manager.py) | Call |
| GET | `/api/v1/orgs/{org_id}/deviceprofiles` | [`orgs.deviceprofiles.listOrgDeviceProfiles`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/device-profiles/list-org-device-profiles) | [`OrgConfigMigrationManager.CONFIG_TYPES`](../../src/org/org_config_migration_manager.py) | Reference |
| POST | `/api/v1/orgs/{org_id}/deviceprofiles` | [`orgs.deviceprofiles.createOrgDeviceProfile`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/device-profiles/create-org-device-profile) | [`OrgConfigMigrationManager.CONFIG_TYPES`](../../src/org/org_config_migration_manager.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/gatewaytemplates` | [`orgs.gatewaytemplates.listOrgGatewayTemplates`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/gateway-templates/list-org-gateway-templates) | [`OrgConfigMigrationManager.CONFIG_TYPES`](../../src/org/org_config_migration_manager.py) | Reference |
| POST | `/api/v1/orgs/{org_id}/gatewaytemplates` | [`orgs.gatewaytemplates.createOrgGatewayTemplate`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/gateway-templates/create-org-gateway-template) | [`OrgConfigMigrationManager.CONFIG_TYPES`](../../src/org/org_config_migration_manager.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/networks` | [`orgs.networks.listOrgNetworks`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/networks/list-org-networks) | [`OrgConfigMigrationManager.CONFIG_TYPES`](../../src/org/org_config_migration_manager.py) | Reference |
| POST | `/api/v1/orgs/{org_id}/networks` | [`orgs.networks.createOrgNetwork`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/networks/create-org-network) | [`OrgConfigMigrationManager.CONFIG_TYPES`](../../src/org/org_config_migration_manager.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/servicepolicies` | [`orgs.servicepolicies.listOrgServicePolicies`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/service-policies/list-org-service-policies) | [`OrgConfigMigrationManager.CONFIG_TYPES`](../../src/org/org_config_migration_manager.py) | Reference |
| POST | `/api/v1/orgs/{org_id}/servicepolicies` | [`orgs.servicepolicies.createOrgServicePolicy`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/service-policies/create-org-service-policy) | [`OrgConfigMigrationManager.CONFIG_TYPES`](../../src/org/org_config_migration_manager.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/services` | [`orgs.services.listOrgServices`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/services/list-org-services) | [`OrgConfigMigrationManager.CONFIG_TYPES`](../../src/org/org_config_migration_manager.py) | Reference |
| POST | `/api/v1/orgs/{org_id}/services` | [`orgs.services.createOrgService`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/services/create-org-service) | [`OrgConfigMigrationManager.CONFIG_TYPES`](../../src/org/org_config_migration_manager.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/vpns` | [`orgs.vpns.listOrgVpns`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/vpns/list-org-vpns) | [`OrgConfigMigrationManager.CONFIG_TYPES`](../../src/org/org_config_migration_manager.py) | Reference |
| POST | `/api/v1/orgs/{org_id}/vpns` | [`orgs.vpns.createOrgVpn`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/vpns/create-org-vpn) | [`OrgConfigMigrationManager.CONFIG_TYPES`](../../src/org/org_config_migration_manager.py) | Reference |

## Menu 188

- Title: Export all organization support tickets to CSV
- Handler: `OrgTicketManager.list_tickets`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/tickets` | [`orgs.tickets.listOrgTickets`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/tickets/list-org-tickets) | [`OrgTicketManager.list_tickets`](../../src/org/org_ticket_manager.py) | Reference |

## Menu 193

- Title: Export all tickets with full details and comments
- Handler: `OrgTicketManager.export_ticket_details`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 2

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/tickets` | [`orgs.tickets.listOrgTickets`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/tickets/list-org-tickets) | [`OrgTicketManager._fetch_all_ticket_summaries`](../../src/org/org_ticket_manager.py) | Call |
| GET | `/api/v1/orgs/{org_id}/tickets/{ticket_id}` | [`orgs.tickets.getOrgTicket`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/tickets/get-org-ticket) | [`OrgTicketManager._fetch_ticket_detail`](../../src/org/org_ticket_manager.py) | Call |

## Menu 204

- Title: Export JSI assets and contract search results
- Handler: `OrgExportUtils.jsi_assets`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/jsi/inventory/search` | [`orgs.jsi.searchOrgJsiAssetsAndContracts`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/jsi/search-org-jsi-assets-and-contracts) | [`OrgExportUtils.jsi_assets`](../../src/export/org_export_utils.py) | Reference |

## Menu 205

- Title: Export Org Mist Edge event search results
- Handler: `OrgExportUtils.mist_edge_events`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/mxedges/events/search` | [`orgs.mxedges.searchOrgMistEdgeEvents`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/mxedges/search-org-mist-edge-events) | [`OrgExportUtils.mist_edge_events`](../../src/export/org_export_utils.py) | Reference |

## Menu 230

- Title: Search wireless client sessions for the organization (searchOrgWirelessClientSessions)
- Handler: `OrgSearchExporter.wireless_client_sessions`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`InputUtils`](README.md#inpututils), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/clients/sessions/search` | [`orgs.clients.searchOrgWirelessClientSessions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/clients/wireless/search-org-wireless-client-sessions) | [`OrgSearchExporter.wireless_client_sessions`](../../src/export/org_search_exporter.py) | Reference |

## Menu 231

- Title: Search wireless client events for the organization (searchOrgWirelessClientEvents)
- Handler: `OrgSearchExporter.wireless_client_events`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`InputUtils`](README.md#inpututils), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/clients/events/search` | [`orgs.clients.searchOrgWirelessClientEvents`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/clients/wireless/search-org-wireless-client-events) | [`OrgSearchExporter.wireless_client_events`](../../src/export/org_search_exporter.py) | Reference |

## Menu 232

- Title: Search WAN clients for the organization (searchOrgWanClients)
- Handler: `OrgSearchExporter.wan_clients`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`InputUtils`](README.md#inpututils), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/wan_clients/search` | [`orgs.wan_clients.searchOrgWanClients`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/clients/wan/search-org-wan-clients) | [`OrgSearchExporter.wan_clients`](../../src/export/org_search_exporter.py) | Reference |

## Menu 233

- Title: Search WAN client events for the organization (searchOrgWanClientEvents)
- Handler: `OrgSearchExporter.wan_client_events`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`InputUtils`](README.md#inpututils), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/wan_clients/events/search` | [`orgs.wan_clients.searchOrgWanClientEvents`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/clients/wan/search-org-wan-client-events) | [`OrgSearchExporter.wan_client_events`](../../src/export/org_search_exporter.py) | Reference |

## Menu 234

- Title: Search system events for the organization (searchOrgSystemEvents)
- Handler: `OrgSearchExporter.system_events`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`InputUtils`](README.md#inpututils), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/events/system/search` | [`orgs.events.searchOrgSystemEvents`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/events/search-org-system-events) | [`OrgSearchExporter.system_events`](../../src/export/org_search_exporter.py) | Reference |

## Menu 243

- Title: Generate the SNMP MIB from the Mist OpenAPI file and the metric catalog
- Handler: `lambda: _launch_mib_generator()`
- Endpoints: 0

Menu 243 builds the SNMP MIB from the local Mist OpenAPI file and the metric catalog. It sends no API request.

## Menu 248

- Title: Search sites for the organization (searchOrgSites)
- Handler: `OrgSearchExporter.sites`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`InputUtils`](README.md#inpututils), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/sites/search` | [`orgs.sites.searchOrgSites`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sites/search-org-sites) | [`OrgSearchExporter.sites`](../../src/export/org_search_exporter.py) | Reference |

## Menu 249

- Title: Search devices for the organization (searchOrgDevices)
- Handler: `OrgSearchExporter.devices`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`InputUtils`](README.md#inpututils), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/devices/search` | [`orgs.devices.searchOrgDevices`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/devices/search-org-devices) | [`OrgSearchExporter.devices`](../../src/export/org_search_exporter.py) | Reference |

## Menu 250

- Title: Search organization variables (searchOrgVars)
- Handler: `OrgSearchExporter.org_vars`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`InputUtils`](README.md#inpututils), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/vars/search` | [`orgs.vars.searchOrgVars`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/vars/search-org-vars) | [`OrgSearchExporter.org_vars`](../../src/export/org_search_exporter.py) | Reference |

## Menu 251

- Title: Search user MAC assignments for the organization (searchOrgUserMacs)
- Handler: `OrgSearchExporter.user_macs`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`InputUtils`](README.md#inpututils), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/usermacs/search` | [`orgs.usermacs.searchOrgUserMacs`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/user-macs/search-org-user-macs) | [`OrgSearchExporter.user_macs`](../../src/export/org_search_exporter.py) | Reference |

## Menu 252

- Title: Search other-device events for the organization (searchOrgOtherDeviceEvents)
- Handler: `OrgExportUtils.other_device_events`
- Shared helpers: [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/otherdevices/events/search` | [`orgs.otherdevices.searchOrgOtherDeviceEvents`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/devices/others/search-org-other-device-events) | [`OrgExportUtils.other_device_events`](../../src/export/org_export_utils.py) | Reference |

## Menu 253

- Title: Search Mist Edges for the organization (searchOrgMxEdges)
- Handler: `OrgSearchExporter.mx_edges`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`InputUtils`](README.md#inpututils), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/mxedges/search` | [`orgs.mxedges.searchOrgMxEdges`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/mxedges/search-org-mx-edges) | [`OrgSearchExporter.mx_edges`](../../src/export/org_search_exporter.py) | Reference |

## Menu 255

- Title: Search PSK portal logs for the organization (searchOrgPskPortalLogs)
- Handler: `OrgSearchExporter.psk_portal_logs`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`InputUtils`](README.md#inpututils), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 1

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/pskportals/logs/search` | [`orgs.pskportals.searchOrgPskPortalLogs`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/psk-portals/search-org-psk-portal-logs) | [`OrgSearchExporter.psk_portal_logs`](../../src/export/org_search_exporter.py) | Reference |

## Menu 269

- Title: Scan the organization for rogue DHCP servers on switches (30 days)
- Handler: `RogueDhcpScanOperation.run`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter)
- Endpoints: 6

```mermaid
flowchart LR
    menu["Menu 269: Scan the<br/>organization for<br/>rogue DHCP..."]
    menu --> c1["RogueDhcpScanner"]
    c1 --> e1["GET<br/>/api/v1/orgs<br/>/{org_id}/alarms<br/>/search"]
    c1 --> e2["GET<br/>/api/v1/orgs<br/>/{org_id}/devices<br/>/events/search"]
    c1 --> e3["GET<br/>/api/v1/orgs<br/>/{org_id}/sites"]
    c1 --> e4["GET<br/>/api/v1/sites<br/>/{site_id}/alarms<br/>/search"]
    c1 --> e5["GET<br/>/api/v1/sites<br/>/{site_id}/devices<br/>/events/search"]
    c1 --> e6["GET<br/>/api/v1/sites<br/>/{site_id}<br/>/marvis_configs<br/>/search"]
```

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/alarms/search` | [`orgs.alarms.searchOrgAlarms`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/alarms/search-org-alarms) | [`RogueDhcpScanner._default_api`](../../src/security/rogue_dhcp/scanner.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/devices/events/search` | [`orgs.devices.searchOrgDeviceEvents`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/devices/search-org-device-events) | [`RogueDhcpScanner._default_api`](../../src/security/rogue_dhcp/scanner.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/sites` | [`orgs.sites.listOrgSites`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sites/list-org-sites) | [`RogueDhcpScanner._default_api`](../../src/security/rogue_dhcp/scanner.py) | Reference |
| GET | `/api/v1/sites/{site_id}/alarms/search` | [`sites.alarms.searchSiteAlarms`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/alarms/search-site-alarms) | [`RogueDhcpScanner._default_api`](../../src/security/rogue_dhcp/scanner.py) | Reference |
| GET | `/api/v1/sites/{site_id}/devices/events/search` | [`sites.devices.searchSiteDeviceEvents`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/devices/search-site-device-events) | [`RogueDhcpScanner._default_api`](../../src/security/rogue_dhcp/scanner.py) | Reference |
| GET | `/api/v1/sites/{site_id}/marvis_configs/search` | [`sites.marvis_configs.searchSiteMarvisConfigActions`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/marvis-configs/search-site-marvis-config-actions) | [`RogueDhcpScanner._default_api`](../../src/security/rogue_dhcp/scanner.py) | Reference |

## Menu 271

- Title: Export the subscription and contract expiry report
- Handler: `SubscriptionExpiryReport.run`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 3

```mermaid
flowchart LR
    menu["Menu 271: Export the<br/>subscription and<br/>contract..."]
    menu --> c1["SubscriptionExpiry<br/>Client"]
    c1 --> e1["GET<br/>/api/v1/orgs<br/>/{org_id}/jsi<br/>/inventory/search"]
    c1 --> e2["GET<br/>/api/v1/orgs<br/>/{org_id}/licenses"]
    c1 --> e3["GET<br/>/api/v1/orgs<br/>/{org_id}/licenses<br/>/usages"]
```

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/jsi/inventory/search` | [`orgs.jsi.searchOrgJsiAssetsAndContracts`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/jsi/search-org-jsi-assets-and-contracts) | [`SubscriptionExpiryClient.search_jsi_assets_and_contracts`](../../src/reports/subscription_expiry/client.py) | Call |
| GET | `/api/v1/orgs/{org_id}/licenses` | [`orgs.licenses.getOrgLicensesSummary`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/licenses/get-org-licenses-summary) | [`SubscriptionExpiryClient.fetch_license_summary`](../../src/reports/subscription_expiry/client.py) | Call |
| GET | `/api/v1/orgs/{org_id}/licenses/usages` | [`orgs.licenses.getOrgLicensesBySite`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/licenses/get-org-licenses-by-site) | [`SubscriptionExpiryClient.fetch_license_usage_by_site`](../../src/reports/subscription_expiry/client.py) | Call |

## Menu 272

- Title: Export the certificate expiry report
- Handler: `CertificateExpiryReport.run`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter)
- Endpoints: 7

```mermaid
flowchart LR
    menu["Menu 272: Export the<br/>certificate expiry<br/>report"]
    menu --> c1["CertificateExpiry<br/>Client"]
    c1 --> e1["GET<br/>/api/v1/orgs<br/>/{org_id}/cert"]
    c1 --> e2["GET<br/>/api/v1/orgs<br/>/{org_id}/crl"]
    c1 --> e3["GET<br/>/api/v1/orgs<br/>/{org_id}/pskportals"]
    c1 --> e4["GET<br/>/api/v1/orgs<br/>/{org_id}/setting"]
    c1 --> e5["GET<br/>/api/v1/orgs<br/>/{org_id}/setting<br/>/mist_nac_crls"]
    c1 --> e6["GET<br/>/api/v1/orgs<br/>/{org_id}/ssos"]
    c1 --> e7["GET<br/>/api/v1/orgs<br/>/{org_id}/stats<br/>/devices"]
```

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/cert` | [`orgs.cert.listOrgCertificates`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/cert/list-org-certificates) | [`CertificateExpiryClient.read_org_certificates`](../../src/reports/certificate_expiry/client.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/crl` | [`orgs.crl.getOrgCrlFile`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/crl/get-org-crl-file) | [`CertificateExpiryClient.read_crl_metadata`](../../src/reports/certificate_expiry/client.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/pskportals` | [`orgs.pskportals.listOrgPskPortals`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/psk-portals/list-org-psk-portals) | [`CertificateExpiryClient._read_org_psk_portals_page`](../../src/reports/certificate_expiry/client.py) | Call |
| GET | `/api/v1/orgs/{org_id}/setting` | [`orgs.setting.getOrgSettings`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/setting/get-org-settings) | [`CertificateExpiryClient.read_org_settings`](../../src/reports/certificate_expiry/client.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/setting/mist_nac_crls` | [`orgs.setting.getOrgNacCrl`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/nac-crl/get-org-nac-crl) | [`CertificateExpiryClient.read_crl_metadata`](../../src/reports/certificate_expiry/client.py) | Name |
| GET | `/api/v1/orgs/{org_id}/ssos` | [`orgs.ssos.listOrgSsos`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sso/list-org-ssos) | [`CertificateExpiryClient._read_org_ssos_page`](../../src/reports/certificate_expiry/client.py) | Call |
| GET | `/api/v1/orgs/{org_id}/stats/devices` | [`orgs.stats.listOrgDevicesStats`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/stats/devices/list-org-devices-stats) | [`CertificateExpiryClient._read_device_stats_page`](../../src/reports/certificate_expiry/client.py) | Call |

## Menu 273

- Title: Admin and API Token Hygiene Report
- Handler: `AdminTokenHygieneReport.run`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter)
- Endpoints: 3

```mermaid
flowchart LR
    menu["Menu 273: Admin and<br/>API Token Hygiene<br/>Report"]
    menu --> c1["AdminTokenHygiene<br/>Client"]
    c1 --> e1["GET<br/>/api/v1/orgs<br/>/{org_id}/admins"]
    c1 --> e2["GET<br/>/api/v1/orgs<br/>/{org_id}/apitokens"]
    c1 --> e3["GET<br/>/api/v1/orgs<br/>/{org_id}/setting"]
```

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/admins` | [`orgs.admins.listOrgAdmins`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/admins/list-org-admins) | [`AdminTokenHygieneClient.list_admins`](../../src/reports/admin_token_hygiene/client.py) | Call |
| GET | `/api/v1/orgs/{org_id}/apitokens` | [`orgs.apitokens.listOrgApiTokens`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/api-tokens/list-org-api-tokens) | [`AdminTokenHygieneClient.list_tokens`](../../src/reports/admin_token_hygiene/client.py) | Call |
| GET | `/api/v1/orgs/{org_id}/setting` | [`orgs.setting.getOrgSettings`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/setting/get-org-settings) | [`AdminTokenHygieneClient.get_settings`](../../src/reports/admin_token_hygiene/client.py) | Call |

## Menu 274

- Title: Export the PSK hygiene report
- Handler: `PskHygieneReport.run`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 0

The map finds no Mist API request for this menu option.

## Menu 275

- Title: Audit site variable coverage
- Handler: `SiteVariableAudit.run`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter), [`SourceDependencyResolver`](README.md#sourcedependencyresolver)
- Endpoints: 7

```mermaid
flowchart LR
    menu["Menu 275: Audit site<br/>variable coverage"]
    menu --> c1["SiteVariableAudit<br/>Client"]
    c1 --> e1["GET<br/>/api/v1/orgs<br/>/{org_id}<br/>/deviceprofiles"]
    c1 --> e2["GET<br/>/api/v1/orgs<br/>/{org_id}<br/>/gatewaytemplates"]
    c1 --> e3["GET<br/>/api/v1/orgs<br/>/{org_id}<br/>/networktemplates"]
    c1 --> e4["GET<br/>/api/v1/orgs<br/>/{org_id}/sites"]
    c1 --> e5["GET<br/>/api/v1/orgs<br/>/{org_id}/templates"]
    c1 --> e6["GET<br/>/api/v1/orgs<br/>/{org_id}/vars<br/>/search"]
    c1 --> e7["GET<br/>/api/v1/orgs<br/>/{org_id}/wlans"]
```

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/deviceprofiles` | [`orgs.deviceprofiles.listOrgDeviceProfiles`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/device-profiles/list-org-device-profiles) | [`SiteVariableAuditClient._default_operations`](../../src/reports/site_variable_audit/client.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/gatewaytemplates` | [`orgs.gatewaytemplates.listOrgGatewayTemplates`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/gateway-templates/list-org-gateway-templates) | [`SiteVariableAuditClient._default_operations`](../../src/reports/site_variable_audit/client.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/networktemplates` | [`orgs.networktemplates.listOrgNetworkTemplates`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/network-templates/list-org-network-templates) | [`SiteVariableAuditClient._default_operations`](../../src/reports/site_variable_audit/client.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/sites` | [`orgs.sites.listOrgSites`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sites/list-org-sites) | [`SiteVariableAuditClient._default_operations`](../../src/reports/site_variable_audit/client.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/templates` | [`orgs.templates.listOrgTemplates`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/wlan-templates/list-org-templates) | [`SiteVariableAuditClient._default_operations`](../../src/reports/site_variable_audit/client.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/vars/search` | [`orgs.vars.searchOrgVars`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/vars/search-org-vars) | [`SiteVariableAuditClient._default_operations`](../../src/reports/site_variable_audit/client.py) | Reference |
| GET | `/api/v1/orgs/{org_id}/wlans` | [`orgs.wlans.listOrgWlans`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/wlans/list-org-wlans) | [`SiteVariableAuditClient._default_operations`](../../src/reports/site_variable_audit/client.py) | Reference |

## Menu 276

- Title: Export the organization security posture checklist
- Handler: `OrgSecurityPostureChecklist.run`
- Shared helpers: [`ConfigUtils`](README.md#configutils), [`DataExporter`](README.md#dataexporter)
- Endpoints: 5

```mermaid
flowchart LR
    menu["Menu 276: Export the<br/>organization<br/>security post..."]
    menu --> c1["OrgSecurityPosture<br/>SourceClient"]
    c1 --> e1["GET<br/>/api/v1/orgs<br/>/{org_id}/admins"]
    c1 --> e2["GET<br/>/api/v1/orgs<br/>/{org_id}/apitokens"]
    c1 --> e3["GET<br/>/api/v1/orgs<br/>/{org_id}/setting"]
    c1 --> e4["GET<br/>/api/v1/orgs<br/>/{org_id}/ssos"]
    c1 --> e5["GET<br/>/api/v1/orgs<br/>/{org_id}/webhooks"]
```

| Method | Path | SDK function | Called from | Found by |
| - | - | - | - | - |
| GET | `/api/v1/orgs/{org_id}/admins` | [`orgs.admins.listOrgAdmins`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/admins/list-org-admins) | [`OrgSecurityPostureSourceClient.collect`](../../src/reports/org_security_posture/io/sources.py) | Call |
| GET | `/api/v1/orgs/{org_id}/apitokens` | [`orgs.apitokens.listOrgApiTokens`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/api-tokens/list-org-api-tokens) | [`OrgSecurityPostureSourceClient.collect`](../../src/reports/org_security_posture/io/sources.py) | Call |
| GET | `/api/v1/orgs/{org_id}/setting` | [`orgs.setting.getOrgSettings`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/setting/get-org-settings) | [`OrgSecurityPostureSourceClient.collect`](../../src/reports/org_security_posture/io/sources.py) | Call |
| GET | `/api/v1/orgs/{org_id}/ssos` | [`orgs.ssos.listOrgSsos`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/sso/list-org-ssos) | [`OrgSecurityPostureSourceClient.collect`](../../src/reports/org_security_posture/io/sources.py) | Call |
| GET | `/api/v1/orgs/{org_id}/webhooks` | [`orgs.webhooks.listOrgWebhooks`](https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/webhooks/list-org-webhooks) | [`OrgSecurityPostureSourceClient.collect`](../../src/reports/org_security_posture/io/sources.py) | Call |
