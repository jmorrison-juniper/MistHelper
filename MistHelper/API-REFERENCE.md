# MistHelper API Reference

## Command Line Interface

### Usage
```bash
python MistHelper.py [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-O, --org` | Organization ID | Prompted if not in .env |
| `-M, --menu` | Direct menu access (1-93) | Interactive |
| `-S, --site` | Human-readable site name | - |
| `-D, --device` | Human-readable device name | - |
| `-P, --port` | Port ID | - |
| `--output-format` | Output format: `csv` or `sqlite` | `csv` |
| `--debug` | Enable debug output and detailed logging | `false` |
| `--delay` | Fixed delay between operations (seconds) | Dynamic |
| `--fast` | Enable fast mode with multithreading | `false` |
| `--skip-deps` | Skip dependency check for faster startup | `false` |
| `--test` | Run systematic test of safe operations | `false` |
| `--help` | Show help message | - |

### Examples

```bash
# Interactive menu (default)
python MistHelper.py

# CSV output with specific menu option
python MistHelper.py --output-format csv --menu 1

# SQLite output with device inventory
python MistHelper.py --output-format sqlite --menu 12

# Run systematic testing
python MistHelper.py --test

# Debug mode with organization specified
python MistHelper.py --debug --org abc123-def456 --menu 11

# Show help
python MistHelper.py --help
```

## Menu Options Reference

MistHelper provides 93 distinct operations organized into logical categories. All operations support both CSV and SQLite output formats.

### Core Data & Diagnostics (1-10)

#### 1. Export Organization Alarms
- **Function**: `export_open_org_alarms_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/alarms/search`
- **Output**: Active alarms from past 24 hours
- **CSV File**: `OrgAlarms.csv`
- **SQLite Table**: `OrgAlarms`

#### 2. Export Device Events  
- **Function**: `export_recent_device_events_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/devices/events/search`
- **Output**: Device events from past 24 hours
- **CSV File**: `OrgDeviceEvents.csv`
- **SQLite Table**: `OrgDeviceEvents`

#### 3. Export Audit Logs
- **Function**: `export_audit_logs_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/logs/audit`
- **Output**: Organization audit logs (last 24 hours)
- **CSV File**: `OrgAuditLogs.csv`
- **SQLite Table**: `OrgAuditLogs`

#### 4. Export NAC Event Definitions
- **Function**: `export_nac_event_definitions_to_csv()`
- **API Endpoint**: `GET /api/v1/const/nac/events/definitions`
- **Output**: Network Access Control event definitions
- **CSV File**: `NacEventDefinitions.csv`
- **SQLite Table**: `NacEventDefinitions`

#### 5. Export Client Event Definitions
- **Function**: `export_client_event_definitions_to_csv()`
- **API Endpoint**: `GET /api/v1/const/client/events/definitions`
- **Output**: Client event definitions
- **CSV File**: `ClientEventDefinitions.csv`
- **SQLite Table**: `ClientEventDefinitions`

#### 6. Export Device Event Definitions
- **Function**: `export_device_event_definitions_to_csv()`
- **API Endpoint**: `GET /api/v1/const/device/events/definitions`
- **Output**: Device event definitions
- **CSV File**: `DeviceEventDefinitions.csv`
- **SQLite Table**: `DeviceEventDefinitions`

#### 7. Export Mist Edge Event Definitions
- **Function**: `export_mist_edge_event_definitions_to_csv()`
- **API Endpoint**: `GET /api/v1/const/mist_edge/events/definitions`
- **Output**: Mist Edge event definitions
- **CSV File**: `MistEdgeEventDefinitions.csv`
- **SQLite Table**: `MistEdgeEventDefinitions`

#### 8. Export Other Device Event Definitions
- **Function**: `export_other_device_event_definitions_to_csv()`
- **API Endpoint**: `GET /api/v1/const/other_device/events/definitions`
- **Output**: Other device event definitions
- **CSV File**: `OtherDeviceEventDefinitions.csv`
- **SQLite Table**: `OtherDeviceEventDefinitions`

#### 9. Export System Event Definitions
- **Function**: `export_system_event_definitions_to_csv()`
- **API Endpoint**: `GET /api/v1/const/system/events/definitions`
- **Output**: System event definitions
- **CSV File**: `SystemEventDefinitions.csv`
- **SQLite Table**: `SystemEventDefinitions`

#### 10. Export Alarm Definitions
- **Function**: `export_alarm_definitions_to_csv()`
- **API Endpoint**: `GET /api/v1/const/alarms/definitions`
- **Output**: Alarm definitions with severity and field info
- **CSV File**: `AlarmDefinitions.csv`
- **SQLite Table**: `AlarmDefinitions`

### Organization-Level Data (11-28)

#### 11. Export Site List
- **Function**: `export_all_sites_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/sites`
- **Output**: Complete list of all sites in organization
- **CSV File**: `SiteList.csv`
- **SQLite Table**: `SiteList`

#### 12. Export Device Inventory
- **Function**: `export_device_inventory_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/inventory`
- **Output**: Full inventory of devices in organization
- **CSV File**: `OrgInventory.csv`
- **SQLite Table**: `OrgInventory`

#### 13. Export Device Statistics
- **Function**: `export_device_stats_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/stats/devices`
- **Output**: Performance statistics for all devices
- **CSV File**: `OrgDeviceStats.csv`
- **SQLite Table**: `OrgDeviceStats`

#### 14. Export Port Statistics
- **Function**: `export_device_port_stats_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/stats/ports/search`
- **Output**: Port-level statistics for switches and gateways
- **CSV File**: `OrgDevicePortStats.csv`
- **SQLite Table**: `OrgDevicePortStats`

#### 15. Export VPN Peer Statistics
- **Function**: `export_vpn_peer_stats_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/stats/vpn_peers/search`
- **Output**: VPN peer path statistics
- **CSV File**: `OrgVPNPeerStats.csv`
- **SQLite Table**: `OrgVPNPeerStats`

#### 16. Export Gateway Synthetic Tests
- **Function**: `export_gateway_synthetic_tests_to_csv()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/devices/{device_id}/synthetic_test`
- **Output**: Synthetic test results for all gateways
- **CSV File**: `GatewaySyntheticTests.csv`
- **SQLite Table**: `GatewaySyntheticTests`

#### 17. Export All Devices List
- **Function**: `export_all_devices_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/devices`
- **Output**: List of all devices in organization
- **CSV File**: `AllDevices.csv`
- **SQLite Table**: `AllDevices`

#### 18. Export Site Settings
- **Function**: `export_site_settings_to_csv()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/setting`
- **Output**: Configuration settings for all sites
- **CSV File**: `AllSiteConfigs.csv`
- **SQLite Table**: `AllSiteConfigs`

#### 19. Export Gateway Test Results
- **Function**: `export_gateway_test_results_by_site_to_csv()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/synthetic_tests/search`
- **Output**: All synthetic test results by site
- **CSV File**: `GatewayTestResults.csv`
- **SQLite Table**: `GatewayTestResults`

#### 20. Export Sites with Location
- **Function**: `export_sites_with_location_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/sites`
- **Output**: Sites with GPS coordinates and timezone info
- **CSV File**: `SitesWithLocation.csv`
- **SQLite Table**: `SitesWithLocation`

#### 21. Export Gateways with Site Info
- **Function**: `export_gateways_with_site_info_to_csv()`
- **API Endpoint**: Multiple endpoints combined
- **CSV File**: `GatewaysWithSiteInfo.csv`
- **SQLite Table**: `GatewaysWithSiteInfo`

#### 22. Export Devices with Site Info
- **Function**: `export_devices_with_site_info_to_csv()`
- **API Endpoint**: Multiple endpoints combined
- **Output**: All devices with associated site and address info
- **CSV File**: `AllDevicesWithSiteInfo.csv`
- **SQLite Table**: `AllDevicesWithSiteInfo`

#### 23. Export Guest Users
- **Function**: Combined guest user export
- **API Endpoint**: `GET /api/v1/sites/{site_id}/guests`
- **Output**: Current and historical guest users
- **CSV File**: Multiple guest user files
- **SQLite Table**: Multiple guest user tables

#### 24. Export Switch VC Stats
- **Function**: `export_switch_vc_stats_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/stats/switch_ports`
- **Output**: Switch virtual chassis statistics
- **CSV File**: `SwitchVCStats.csv`
- **SQLite Table**: `SwitchVCStats`

#### 25. Export Combined Inventory
- **Function**: `export_combined_inventory_with_site_info()`
- **API Endpoint**: Multiple endpoints combined
- **Output**: Combined inventory with site and address info
- **CSV File**: `CombinedInventory.csv`
- **SQLite Table**: `CombinedInventory`

#### 26. Export Gateway Templates
- **Function**: `export_gateway_templates_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/gatewaytemplates`
- **Output**: Gateway templates from organization
- **CSV File**: `GatewayTemplates.csv`
- **SQLite Table**: `GatewayTemplates`

#### 27. Export Sites List API
- **Function**: `export_all_sites_list_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/sites`
- **Output**: Sites using list API endpoint
- **CSV File**: `SiteList_ListAPI.csv`
- **SQLite Table**: `SiteList_ListAPI`

#### 28. Export Gateway WAN Overrides
- **Function**: `export_gateways_with_wan_overrides_to_csv()`
- **API Endpoint**: Multiple endpoints combined
- **Output**: Gateway ports overridden from template
- **CSV File**: `GatewayOverriddenPorts.csv`
- **SQLite Table**: `GatewayOverriddenPorts`

### Templates & Configuration (35-59)

#### 35. Export Organization Templates
- **Function**: `export_organization_templates_to_csv()`
- **API Endpoint**: Multiple template endpoints
- **Output**: All organization templates (gateway, network, RF, site, AP)
- **CSV File**: `OrgTemplates.csv`
- **SQLite Table**: `OrgTemplates`

#### 36. Export Network Templates
- **Function**: `export_org_network_templates_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/networktemplates`
- **Output**: Network template information for the organization
- **CSV File**: `NetworkTemplates.csv`
- **SQLite Table**: `NetworkTemplates`

#### 37. Export RF Templates
- **Function**: `export_org_rf_templates_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/rftemplates`
- **Output**: RF template information for the organization
- **CSV File**: `RFTemplates.csv`
- **SQLite Table**: `RFTemplates`

#### 38. Export AP Templates
- **Function**: `export_org_ap_templates_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/deviceprofiles`
- **Output**: AP template information for the organization
- **CSV File**: `APTemplates.csv`
- **SQLite Table**: `APTemplates`

#### 39. Export Switch Templates
- **Function**: `export_org_switch_templates_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/deviceprofiles`
- **Output**: Switch template information for the organization
- **CSV File**: `SwitchTemplates.csv`
- **SQLite Table**: `SwitchTemplates`

#### 40. Export Wireless Clients
- **Function**: `export_org_wireless_clients_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/stats/clients`
- **Output**: Wireless client statistics for the organization
- **CSV File**: `OrgWirelessClients.csv`
- **SQLite Table**: `OrgWirelessClients`

#### 41. Export Wired Clients
- **Function**: `export_org_wired_clients_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/stats/clients`
- **Output**: Wired client statistics for the organization
- **CSV File**: `OrgWiredClients.csv`
- **SQLite Table**: `OrgWiredClients`

#### 42. Export Security Events
- **Function**: `export_org_security_events_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/secpolicy/events`
- **Output**: Security events for the organization
- **CSV File**: `OrgSecurityEvents.csv`
- **SQLite Table**: `OrgSecurityEvents`

#### 43. Export Rogue Clients
- **Function**: `export_org_rogue_clients_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/rogue/clients`
- **Output**: Rogue client detections for the organization
- **CSV File**: `OrgRogueClients.csv`
- **SQLite Table**: `OrgRogueClients`

#### 44. Export Rogue APs
- **Function**: `export_org_rogue_aps_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/rogue/aps`
- **Output**: Rogue AP detections for the organization
- **CSV File**: `OrgRogueAPs.csv`
- **SQLite Table**: `OrgRogueAPs`

#### 45. Export Organization Licenses
- **Function**: `export_org_licenses_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/licenses`
- **Output**: License information for the organization
- **CSV File**: `OrgLicenses.csv`
- **SQLite Table**: `OrgLicenses`

#### 46. Export PSK Information
- **Function**: `export_org_psks_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/psks`
- **Output**: PSK (Pre-Shared Key) information for the organization
- **CSV File**: `OrgPSKs.csv`
- **SQLite Table**: `OrgPSKs`

#### 47. Export Webhooks
- **Function**: `export_org_webhooks_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/webhooks`
- **Output**: Webhook configuration for the organization
- **CSV File**: `OrgWebhooks.csv`
- **SQLite Table**: `OrgWebhooks`

#### 48. Export Organization WLANs
- **Function**: `export_org_wlans_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/wlans`
- **Output**: WLAN configuration for the organization
- **CSV File**: `OrgWLANs.csv`
- **SQLite Table**: `OrgWLANs`

#### 49. Export Site WLANs
- **Function**: `export_site_wlans_to_csv()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/wlans`
- **Output**: WLAN configuration for a selected site
- **CSV File**: `SiteWLANs.csv`
- **SQLite Table**: `SiteWLANs`

#### 50. Export Site Beacons
- **Function**: `export_site_beacons_to_csv()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/beacons`
- **Output**: Beacon information for a selected site
- **CSV File**: `SiteBeacons.csv`
- **SQLite Table**: `SiteBeacons`

#### 51. Export Site Maps
- **Function**: `export_site_maps_to_csv()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/maps`
- **Output**: Map information for a selected site
- **CSV File**: `SiteMaps.csv`
- **SQLite Table**: `SiteMaps`

#### 52. Export Site Zones
- **Function**: `export_site_zones_to_csv()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/zones`
- **Output**: Zone information for a selected site
- **CSV File**: `SiteZones.csv`
- **SQLite Table**: `SiteZones`

#### 53. Export Site Insights
- **Function**: `export_site_insights_to_csv()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/insights`
- **Output**: Insights information for a selected site
- **CSV File**: `SiteInsights.csv`
- **SQLite Table**: `SiteInsights`

#### 54. Export API Tokens
- **Function**: `export_org_api_tokens_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/apitokens`
- **Output**: API token information for the organization
- **CSV File**: `OrgAPITokens.csv`
- **SQLite Table**: `OrgAPITokens`

#### 55. Export Administrators
- **Function**: `export_org_admins_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/admins`
- **Output**: Administrator information for the organization
- **CSV File**: `OrgAdmins.csv`
- **SQLite Table**: `OrgAdmins`

#### 56. Export MSP Information
- **Function**: `export_org_msp_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/msp`
- **Output**: MSP (Managed Service Provider) information for the organization
- **CSV File**: `OrgMSP.csv`
- **SQLite Table**: `OrgMSP`

#### 57. Export SSO Configuration
- **Function**: `export_org_sso_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/sso`
- **Output**: SSO (Single Sign-On) information for the organization
- **CSV File**: `OrgSSO.csv`
- **SQLite Table**: `OrgSSO`

#### 58. Export License Usage
- **Function**: `export_org_usage_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/usage`
- **Output**: License usage information for the organization
- **CSV File**: `OrgUsage.csv`
- **SQLite Table**: `OrgUsage`

#### 59. Export MX Edges
- **Function**: `export_org_mx_edges_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/mxedges`
- **Output**: MX Edge information for the organization
- **CSV File**: `OrgMXEdges.csv`
- **SQLite Table**: `OrgMXEdges`

### Status & Monitoring (60-62)

#### 60. Check Firmware Upgrade Status
- **Function**: `check_firmware_upgrade_status()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/stats/devices`
- **Output**: Current firmware upgrade status across organization with detailed progress monitoring
- **CSV File**: `FirmwareUpgradeStatus.csv`
- **SQLite Table**: `FirmwareUpgradeStatus`

#### 61. Compare Inventory
- **Function**: `compare_inventory_with_csv()`
- **API Endpoint**: Local CSV comparison
- **Output**: Compare inventory data with external CSV file and show zip code mismatches
- **CSV File**: Console output with comparison results

#### 62. Poll Marvis Actions
- **Function**: `poll_marvis_actions()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/marvis`
- **Output**: Poll Marvis actions and export open actions
- **CSV File**: `MarvisActions.csv`
- **SQLite Table**: `MarvisActions`

### Work In Progress Features (63-65)

#### 63. Export 52-Week Device Events
- **Function**: `export_all_org_device_events_52w_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/devices/events/search`
- **Output**: All org device events from the last 52 weeks
- **CSV File**: `OrgDeviceEvents_52w.csv`
- **SQLite Table**: `OrgDeviceEvents_52w`

#### 64. Export 52-Week Audit Logs
- **Function**: `export_audit_logs_to_csv(full_history=True, duration="52w")`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/logs/audit`
- **Output**: ALL audit logs for the organization (last 52 weeks)
- **CSV File**: `OrgAuditLogs_52w.csv`
- **SQLite Table**: `OrgAuditLogs_52w`

#### 65. Export Gateway Device Configs
- **Function**: `export_gateway_device_configs_to_csv()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/devices/{device_id}`
- **Output**: Configuration details for all gateway devices across all sites
- **CSV File**: `GatewayDeviceConfigs.csv`
- **SQLite Table**: `GatewayDeviceConfigs`

### Interactive Tools (70-74)

#### 70. Site Selection
- **Function**: `prompt_and_log_site_selection()`
- **API Endpoint**: Interactive only
- **Output**: Select a site (used by other functions)
- **CSV File**: Interactive only

#### 71. Site Inventory Browser
- **Function**: `interactive_display_site_inventory()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/devices`
- **Output**: Interactive device inventory viewer
- **CSV File**: `SiteInventory.csv`
- **SQLite Table**: `SiteInventory`

#### 72. Device Statistics Viewer
- **Function**: `interactive_display_device_stats()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/stats/devices/{device_id}`
- **Output**: Interactive device statistics browser
- **CSV File**: `DeviceStats.csv`
- **SQLite Table**: `DeviceStats`

#### 73. Device Tests Viewer
- **Function**: `interactive_display_device_tests()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/devices/{device_id}/synthetic_test`
- **Output**: Interactive synthetic test results viewer
- **CSV File**: `DeviceTestResults.csv`
- **SQLite Table**: `DeviceTestResults`

#### 74. Device Config Viewer
- **Function**: `interactive_display_device_config()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/devices/{device_id}`
- **Output**: Interactive device configuration viewer
- **CSV File**: `DeviceConfig.csv`
- **SQLite Table**: `DeviceConfig`

### Continuous Operations (75-76)

#### 75. Loop Refresh
- **Function**: `loop_refresh_core_datasets()`
- **API Endpoint**: Multiple endpoints
- **Output**: Continuous refresh of core datasets
- **CSV File**: Multiple files

#### 76. Data Collection Loop
- **Function**: `continuous_data_collection_loop()`
- **API Endpoint**: Multiple endpoints
- **Output**: Continuous data collection with rate limiting
- **CSV File**: Multiple files

### File Processing & Support (77-78)

#### 77. SFP Data Merge
- **Function**: `process_and_merge_csv_for_sfp_address()`
- **API Endpoint**: File processing
- **Output**: Process and merge SFP module location data
- **CSV File**: `MergedTransceiverData.csv`
- **SQLite Table**: `MergedTransceiverData`

#### 78. Support Package
- **Function**: `generate_support_package()`
- **API Endpoint**: Multiple endpoints
- **Output**: Generate support package for each site
- **CSV File**: Site-specific packages

### CLI & WebSocket Operations (79-83)

#### 79. Launch CLI Shell
- **Function**: `launch_cli_shell()`
- **API Endpoint**: WebSocket CLI interface
- **Output**: Interactively execute CLI commands on gateway or switch
- **CSV File**: Interactive only

#### 80. Run ARP via WebSocket
- **Function**: `run_arp_via_websocket()`
- **API Endpoint**: WebSocket command interface
- **Output**: Run ARP command on an AP and receive output via WebSocket
- **CSV File**: `ARPOutput.csv`

#### 81. Show Default Route
- **Function**: `run_shell_command_and_log()`
- **API Endpoint**: WebSocket command interface
- **Output**: Run 'show route 0.0.0.0' on a selected device via shell session
- **CSV File**: `RouteDefault.csv`

#### 82. Show DHCP Security Bindings
- **Function**: `run_shell_command_and_log()`
- **API Endpoint**: WebSocket command interface
- **Output**: Run 'show dhcp-security binding' on a selected device via shell session
- **CSV File**: `DhcpSecurityBindings.csv`

#### 83. Show VLANs
- **Function**: `run_shell_command_and_log()`
- **API Endpoint**: WebSocket command interface
- **Output**: Run 'show vlans' on a selected device via shell session
- **CSV File**: `Vlans.csv`

### Advanced Operations (90-93)

#### 90. Bulk AP Firmware Upgrade
- **Function**: `bulk_upgrade_ap_firmware_by_site()`
- **API Endpoint**: `POST /api/v1/orgs/{org_id}/devices/upgrade`
- **Output**: 🔥 **DESTRUCTIVE**: Advanced bulk AP firmware upgrade with multiple strategies
- **CSV File**: Upgrade logs

#### 91. Reboot Devices by Template
- **Function**: `reboot_devices_by_gateway_template_list()`
- **API Endpoint**: `POST /api/v1/sites/{site_id}/devices/{device_id}/restart`
- **Output**: 🔥 **DESTRUCTIVE**: Reboot devices by template list
- **CSV File**: Reboot logs

#### 92. Convert Virtual Chassis to Virtual MAC
- **Function**: `convert_virtual_chassis_to_virtual_mac()`
- **API Endpoint**: `PUT /api/v1/sites/{site_id}/devices/{device_id}`
- **Output**: 🔥 **DESTRUCTIVE**: Convert virtual chassis switch to virtual MAC
- **CSV File**: Conversion logs

#### 93. Bulk Virtual Chassis Conversion
- **Function**: `convert_virtual_chassis_by_site_list()`
- **API Endpoint**: `PUT /api/v1/sites/{site_id}/devices/{device_id}`
- **Output**: 🔥 **DESTRUCTIVE**: Convert all virtual chassis switches by site list
- **CSV File**: Conversion logs

## Core Functions

### Data Processing Functions

#### flatten_dict_recursively(d, parent_key='', sep='_')
Recursively flattens nested dictionaries into dot-notation fields.

**Parameters:**
- `d`: Dictionary to flatten
- `parent_key`: Parent key prefix
- `sep`: Separator character

**Returns:** Flattened dictionary

**Example:**
```python
nested = {'device': {'model': 'AP41', 'config': {'wifi': {'ssid': 'corporate'}}}}
flat = flatten_dict_recursively(nested)
# Result: {'device_model': 'AP41', 'device_config_wifi_ssid': 'corporate'}
```

#### flatten_nested_fields_in_list(data)
Flattens all nested fields in a list of dictionaries.

**Parameters:**
- `data`: List of dictionaries to process

**Returns:** List of flattened dictionaries

#### escape_multiline_strings_for_csv(data)
Escapes multiline strings for CSV compatibility.

**Parameters:**
- `data`: List of dictionaries to process

**Returns:** List with escaped strings

#### get_all_unique_dict_keys(data)
Returns all unique keys from a list of dictionaries.

**Parameters:**
- `data`: List of dictionaries

**Returns:** Sorted list of unique keys

### Output Functions

#### write_dict_list_to_csv(data, filename)
Writes dictionary list to CSV file.

**Parameters:**
- `data`: List of dictionaries
- `filename`: Output filename

#### write_dict_list_to_sqlite_database_inside_container(data, table_name)
Writes dictionary list to SQLite database.

**Parameters:**
- `data`: List of dictionaries
- `table_name`: Database table name

**Returns:** Boolean success status

#### save_data_to_output(data, filename)
Wrapper function that routes to appropriate output format.

**Parameters:**
- `data`: List of dictionaries
- `filename`: Output filename/table name

### API Functions

#### fetch_and_display_api_data(title, api_call, filename, sort_key=None, display_fields=None, **kwargs)
Generic function for API data fetching and processing.

**Parameters:**
- `title`: Display title
- `api_call`: Mist API function
- `filename`: Output filename
- `sort_key`: Optional sorting field
- `display_fields`: Fields to display
- `**kwargs`: Additional API parameters

#### get_cached_or_prompted_org_id()
Gets organization ID from cache, environment, or user prompt.

**Returns:** Organization ID string

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MIST_HOST` | Mist API host | `api.mist.com` |
| `MIST_APITOKEN` | API authentication token | Required |
| `MIST_USERNAME` | Username for authentication | Optional |
| `MIST_PASSWORD` | Password for authentication | Optional |
| `org_id` | Organization ID | Prompted if not set |
| `CSV_FRESHNESS_MINUTES` | CSV file freshness check | `15` |
| `OUTPUT_FORMAT` | Default output format | `csv` |

### Global Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OUTPUT_FORMAT` | Current output format | `csv` |
| `DATABASE_PATH` | SQLite database path | `data/mist_data.db` |
| `CSV_FRESHNESS_MINUTES` | File freshness threshold | `15` |

## Data Structures

### Common Data Fields

#### Site Data
- `id`: Site identifier
- `name`: Site name
- `org_id`: Organization ID
- `timezone`: Site timezone
- `address`: Physical address
- `lat`: GPS latitude
- `lng`: GPS longitude

#### Device Data
- `id`: Device identifier
- `site_id`: Associated site ID
- `mac`: Device MAC address
- `model`: Device model
- `type`: Device type (ap, switch, gateway)
- `serial`: Serial number
- `name`: Device name

#### Statistics Data
- `mac`: Device MAC address
- `type`: Device type
- `status`: Connection status
- `uptime`: Device uptime
- `version`: Firmware version
- `last_seen`: Last contact timestamp

### Database Schema

#### SQLite Tables
All tables include:
- `id`: Auto-incrementing primary key
- `timestamp`: Record creation timestamp
- `api_id`: Original API ID (preserved)
- `api_timestamp`: Original API timestamp

#### Field Naming
- Nested fields use underscore separation
- API fields are preserved with `api_` prefix
- All fields are stored as TEXT in SQLite

## Error Handling

### Common Errors

#### Authentication Errors
- **401 Unauthorized**: Invalid API token
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Invalid organization ID

#### Rate Limiting
- **429 Too Many Requests**: API rate limit exceeded
- **503 Service Unavailable**: Temporary service issues

#### Data Processing Errors
- **UnicodeEncodeError**: Character encoding issues
- **ValueError**: Invalid data format
- **KeyError**: Missing required fields

### Error Recovery

1. **Automatic Retry**: Built-in retry logic for transient errors
2. **Partial Data Save**: Saves collected data on interruption
3. **Graceful Degradation**: Continues operation with warnings
4. **Comprehensive Logging**: Detailed error tracking

## Performance Considerations

### Rate Limiting
- Default delay: 0.75 seconds between API calls
- Dynamic adjustment based on response times
- Automatic retry on rate limit errors

### Memory Management
- Streaming data processing for large datasets
- Efficient pagination handling
- Memory-conscious data structures

### Database Optimization
- Indexed primary keys for fast queries
- Batch insertions for performance
- Transaction-based operations

## Examples

### Basic Usage
```python
# Export site list to CSV
python MistHelper.py --output-format csv --menu 1

# Export device inventory to SQLite
python MistHelper.py --output-format sqlite --menu 2
```

### Programmatic Usage
```python
from MistHelper import export_all_sites_to_csv, save_data_to_output

# Export sites
export_all_sites_to_csv()

# Save custom data
data = [{'name': 'Site1', 'id': '123'}]
save_data_to_output(data, 'custom_sites.csv')
```

### Container Usage
```bash
# Run specific menu option
python run-misthelper.py --menu 1 --output-format sqlite

# Interactive mode
python run-misthelper.py
```

This API reference provides comprehensive documentation for all MistHelper functions, configuration options, and usage patterns. Use this as a reference for integrating MistHelper into your network management workflows.
