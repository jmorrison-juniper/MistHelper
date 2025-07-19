# MistHelper API Reference

## Command Line Interface

### Usage
```bash
python MistHelper.py [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output-format` | Output format: `csv` or `sqlite` | `csv` |
| `--menu` | Direct menu access (1-47) | Interactive |
| `--help` | Show help message | - |

### Examples

```bash
# Interactive menu (default)
python MistHelper.py

# CSV output with specific menu option
python MistHelper.py --output-format csv --menu 1

# SQLite output with device inventory
python MistHelper.py --output-format sqlite --menu 2

# Show help
python MistHelper.py --help
```

## Menu Options

### Organization-Level Data (1-8)

#### 1. Export Site List
- **Function**: `export_all_sites_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/sites`
- **Output**: Site list with names, IDs, and configuration
- **CSV File**: `SiteList.csv` or `SiteList_ListAPI.csv`
- **SQLite Table**: `SiteList`

#### 2. Export Device Inventory
- **Function**: `export_device_inventory_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/inventory`
- **Output**: All devices with models, serials, and assignments
- **CSV File**: `OrgInventory.csv`
- **SQLite Table**: `OrgInventory`

#### 3. Export Device Statistics
- **Function**: `export_device_stats_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/stats/devices`
- **Output**: Device performance metrics and status
- **CSV File**: `OrgDeviceStats.csv`
- **SQLite Table**: `OrgDeviceStats`

#### 4. Export Device Port Statistics
- **Function**: `export_device_port_stats_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/stats/ports/search`
- **Output**: Port-level statistics for all devices
- **CSV File**: `OrgDevicePortStats.csv`
- **SQLite Table**: `OrgDevicePortStats`

#### 5. Export VPN Peer Statistics
- **Function**: `export_vpn_peer_stats_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/stats/vpn_peers/search`
- **Output**: VPN peer path statistics
- **CSV File**: `OrgVPNPeerStats.csv`
- **SQLite Table**: `OrgVPNPeerStats`

#### 6. Export Audit Logs
- **Function**: `export_audit_logs_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/logs/audit`
- **Output**: Organization audit logs
- **CSV File**: `OrgAuditLogs.csv`
- **SQLite Table**: `OrgAuditLogs`

#### 7. Export Open Alarms
- **Function**: `export_open_org_alarms_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/alarms/search`
- **Output**: Current active alarms
- **CSV File**: `OrgAlarms.csv`
- **SQLite Table**: `OrgAlarms`

#### 8. Export Device Events
- **Function**: `export_recent_device_events_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/devices/events/search`
- **Output**: Device events from last 24 hours
- **CSV File**: `OrgDeviceEvents.csv`
- **SQLite Table**: `OrgDeviceEvents`

### Site-Level Operations (9-13)

#### 9. Site Device Inventory
- **Function**: `interactive_display_site_inventory()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/devices`
- **Output**: Interactive site device browser
- **CSV File**: `SiteInventory.csv`
- **SQLite Table**: `SiteInventory`

#### 10. Device Configuration
- **Function**: `interactive_display_device_config()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/devices/{device_id}`
- **Output**: Device configuration details
- **CSV File**: `DeviceConfig.csv`
- **SQLite Table**: `DeviceConfig`

#### 11. Device Statistics
- **Function**: `interactive_display_device_stats()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/stats/devices/{device_id}`
- **Output**: Individual device statistics
- **CSV File**: `DeviceStats.csv`
- **SQLite Table**: `DeviceStats`

#### 12. Device Test Results
- **Function**: `interactive_display_device_tests()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/devices/{device_id}/synthetic_test`
- **Output**: Gateway synthetic test results
- **CSV File**: `DeviceTestResults.csv`
- **SQLite Table**: `DeviceTestResults`

#### 13. Export Site Configurations
- **Function**: `export_site_settings_to_csv()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/setting`
- **Output**: Site configuration settings
- **CSV File**: `AllSiteConfigs.csv`
- **SQLite Table**: `AllSiteConfigs`

### Advanced Features (14-19)

#### 14. Export Gateway Synthetic Tests
- **Function**: `export_gateway_synthetic_tests_to_csv()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/devices/{device_id}/synthetic_test`
- **Output**: All gateway synthetic tests
- **CSV File**: `AllGatewaySyntheticTests.csv`
- **SQLite Table**: `AllGatewaySyntheticTests`

#### 15. Export Test Results by Site
- **Function**: `export_gateway_test_results_by_site_to_csv()`
- **API Endpoint**: `GET /api/v1/sites/{site_id}/synthetic_tests/search`
- **Output**: Test results per site
- **CSV File**: `AllTestResultsBySite.csv`
- **SQLite Table**: `AllTestResultsBySite`

#### 16. Export Event Definitions
- **Multiple Functions**: Various event definition exports
- **API Endpoints**: Multiple `/api/v1/const/*/events/definitions`
- **Output**: Event log definitions
- **CSV Files**: Multiple definition files
- **SQLite Tables**: Multiple definition tables

#### 17. Export Sites with Location
- **Function**: `export_sites_with_location_to_csv()`
- **API Endpoint**: `GET /api/v1/orgs/{org_id}/sites`
- **Output**: Sites with GPS coordinates
- **CSV File**: `SitesWithLocation.csv`
- **SQLite Table**: `SitesWithLocation`

#### 18. Export Devices with Site Info
- **Function**: `export_devices_with_site_info_to_csv()`
- **API Endpoint**: Multiple endpoints combined
- **Output**: Devices with site details
- **CSV File**: `AllDevicesWithSiteInfo.csv`
- **SQLite Table**: `AllDevicesWithSiteInfo`

#### 19. Merge SFP Transceiver Data
- **Function**: `process_and_merge_csv_for_sfp_address()`
- **API Endpoint**: Processes existing data
- **Output**: Transceiver data with location info
- **CSV File**: `MergedTransceiverData.csv`
- **SQLite Table**: `MergedTransceiverData`

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
