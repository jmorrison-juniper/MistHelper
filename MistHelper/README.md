# MistHelper

**Network Operations Tool for Juniper Mist Cloud Infrastructure Management**

MistHelper is a production-ready Python application that provides comprehensive access to the Juniper Mist Cloud API for network infrastructure data extraction, analysis, and management operations. The tool supports both interactive menu-driven operations and automated command-line execution, making it suitable for both ad-hoc analysis and integration into existing NOC workflows.

The application provides 96 distinct operations covering all major Mist API endpoints with dual output formats (CSV and SQLite) for flexible integration into monitoring and management workflows.

## Core Capabilities

- **Complete API Coverage**: Access to all major Mist API endpoints with 96 operations
- **Dual Output Formats**: CSV files and SQLite database with optimized schemas  
- **Advanced Architecture**: GlobalImportManager with UV/pip integration and natural primary keys
- **Enterprise Features**: PID-controlled rate limiting, connection pool management, and comprehensive error handling
- **Operational Modes**: Interactive menu interface and direct CLI automation
- **Container Support**: Docker and Podman deployment with cross-platform scripts
- **Production Features**: Systematic testing framework, comprehensive logging, and audit trails
- **Cross-Platform**: Windows, macOS, and Linux compatibility

## Quick Start

### Prerequisites

- **Python 3.8+** with pip
- **Juniper Mist API Token** (Organization Admin privileges recommended)
- **Organization ID** from Mist dashboard

### Installation Options

#### Option 1: Automated Setup (Recommended)
```bash
git clone <repository-url>
cd MistHelper
python MistHelper.py  # Auto-installs dependencies and creates configuration template
```

#### Option 2: Manual UV Installation
```bash
python -m pip install uv  # Install UV package manager for faster operations
git clone <repository-url>
cd MistHelper
python MistHelper.py
```

#### Option 3: Traditional Installation
```bash
git clone <repository-url>
cd MistHelper
pip install -r requirements.txt
python MistHelper.py
```

### Initial Configuration

On first run, MistHelper will:
1. Install required dependencies using fastest available method (UV or pip)
2. Create `.env` configuration template
3. Display setup instructions with API credential requirements
4. Provide links for obtaining necessary API tokens

### First Execution

```bash
# Interactive menu interface
python MistHelper.py

# Direct execution with SQLite output  
python MistHelper.py --output-format sqlite --menu 11

# CSV output format
python MistHelper.py --output-format csv --menu 1

# Systematic testing of all safe operations
python MistHelper.py --test
```

## Operation Categories

MistHelper provides 96 distinct operations organized into functional categories. All operations support both CSV and SQLite output formats.

### Core Data & Diagnostics (Options 1-10)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **1** | Organization Alarms | Export all active alarms from past 24 hours | `OrgAlarms.csv` |
| **2** | Device Events | Export all device events from past 24 hours | `OrgDeviceEvents.csv` |
| **3** | Audit Logs | Export audit logs (last 24 hours) | `OrgAuditLogs.csv` |
| **4** | NAC Event Definitions | Export Network Access Control event definitions | `NacEventDefinitions.csv` |
| **5** | Client Event Definitions | Export client event definitions | `ClientEventDefinitions.csv` |
| **6** | Device Event Definitions | Export device event definitions | `DeviceEventDefinitions.csv` |
| **7** | Mist Edge Event Definitions | Export Mist Edge event definitions | `MistEdgeEventDefinitions.csv` |
| **8** | Other Device Event Definitions | Export other device event definitions | `OtherDeviceEventDefinitions.csv` |
| **9** | System Event Definitions | Export system event definitions | `SystemEventDefinitions.csv` |
| **10** | Alarm Definitions | Export alarm definitions with severity info | `AlarmDefinitions.csv` |

### Organization-Level Data (Options 11-28)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **11** | Site List | Export complete list of all sites | `SiteList.csv` |
| **12** | Device Inventory | Export full device inventory | `OrgInventory.csv` |
| **13** | Device Statistics | Export performance stats for all devices | `OrgDeviceStats.csv` |
| **14** | Port Statistics | Export port-level statistics for switches/gateways | `OrgDevicePortStats.csv` |
| **15** | VPN Peer Statistics | Export VPN peer path statistics | `OrgVPNPeerStats.csv` |
| **16** | Gateway Synthetic Tests | Export synthetic test results for gateways | `GatewaySyntheticTests.csv` |
| **17** | All Devices List | Export comprehensive device list | `AllDevices.csv` |
| **18** | Site Settings | Export configuration settings for all sites | `AllSiteConfigs.csv` |
| **19** | Gateway Test Results | Export all synthetic test results by site | `GatewayTestResults.csv` |
| **20** | Sites with Location | Export sites with GPS coordinates and timezone | `SitesWithLocation.csv` |
| **21** | Gateways with Site Info | Export gateways with site and address details | `GatewaysWithSiteInfo.csv` |
| **22** | Devices with Site Info | Export all devices with site and address details | `AllDevicesWithSiteInfo.csv` |
| **23** | Guest Users | Export current and historical guest users | `CurrentGuestUsers.csv`, `HistoricalGuestUsers.csv` |
| **24** | Switch VC Statistics | Export virtual chassis (stacking) statistics | `SwitchVCStats.csv` |
| **25** | Combined Inventory | Export inventory by calendar week with site info | `CombinedInventory_ByWeek/` |
| **26** | Gateway Templates | Export gateway templates | `GatewayTemplates.csv` |
| **27** | Sites List API | Export sites using list API endpoint | `SiteList_ListAPI.csv` |
| **28** | Gateway WAN Overrides | Find gateway ports overridden from template | `GatewaysWithWANOverrides.csv` |

### Site-Specific Data (Options 29-34)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **29** | Site Port Statistics | Export port statistics for selected site | `SitePortStats.csv` |
| **30** | Site Clients | Export client statistics for selected site | `SiteClients.csv` |
| **31** | Site Devices | Export device list for selected site | `SiteDevices.csv` |
| **32** | Site Device Statistics | Export device statistics for selected site | `SiteDeviceStats.csv` |
| **33** | Virtual Chassis Info | Export virtual chassis info for selected switch | `VirtualChassisInfo.csv` |
| **34** | WiFi Clients | Export current WiFi clients and sessions | `SiteWiFiClients.csv` |

### Templates & Configuration (Options 35-39)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **35** | Organization Templates | Export all org templates (gateway, network, RF, etc.) | `OrgTemplates.csv` |
| **36** | Network Templates | Export network template information | `NetworkTemplates.csv` |
| **37** | RF Templates | Export RF template information | `RFTemplates.csv` |
| **38** | AP Templates | Export AP template information | `APTemplates.csv` |
| **39** | Switch Templates | Export switch template information | `SwitchTemplates.csv` |

### Analytics & Client Data (Options 40-41)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **40** | Wireless Clients | Export wireless client statistics | `OrgWirelessClients.csv` |
| **41** | Wired Clients | Export wired client statistics | `OrgWiredClients.csv` |

### Security & Monitoring (Options 42-44)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **42** | Security Events | Export organization security events | `OrgSecurityEvents.csv` |
| **43** | Rogue Clients | Export rogue client detections | `OrgRogueClients.csv` |
| **44** | Rogue APs | Export rogue AP detections | `OrgRogueAPs.csv` |

### Configuration Management (Options 45-59)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **45** | Licenses | Export license information | `OrgLicenses.csv` |
| **46** | PSK Information | Export Pre-Shared Key configurations | `OrgPSKs.csv` |
| **47** | Webhooks | Export webhook configurations | `OrgWebhooks.csv` |
| **48** | Organization WLANs | Export WLAN configurations | `OrgWLANs.csv` |
| **49** | Site WLANs | Export WLAN configuration for selected site | `SiteWLANs.csv` |
| **50** | Site Beacons | Export beacon information for selected site | `SiteBeacons.csv` |
| **51** | Site Maps | Export map information for selected site | `SiteMaps.csv` |
| **52** | Site Zones | Export zone information for selected site | `SiteZones.csv` |
| **53** | Site Insights | Export insights for selected site | `SiteInsights.csv` |
| **54** | API Tokens | Export API token information | `OrgAPITokens.csv` |
| **55** | Administrators | Export administrator information | `OrgAdmins.csv` |
| **56** | MSP Information | Export Managed Service Provider details | `OrgMSP.csv` |
| **57** | SSO Configuration | Export Single Sign-On information | `OrgSSO.csv` |
| **58** | License Usage | Export license usage information | `OrgUsage.csv` |
| **59** | MX Edges | Export MX Edge information | `OrgMXEdges.csv` |

### Status & Monitoring (Options 60-62)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **60** | Firmware Upgrade Status | Check current firmware upgrade progress | `FirmwareUpgradeStatus.csv` |
| **61** | Inventory Comparison | Compare inventory with external CSV | Console output |
| **62** | Marvis Actions | Poll Marvis actions and export open items | `MarvisActions.csv` |

### Extended Features (Options 63-65)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **63** | 52-Week Device Events | Export device events from last 52 weeks | `OrgDeviceEvents52w.csv` |
| **64** | 52-Week Audit Logs | Export audit logs from last 52 weeks | `OrgAuditLogs52w.csv` |
| **65** | Gateway Device Configs | Export configuration details for all gateways | `GatewayDeviceConfigs.csv` |

### Interactive Tools (Options 70-74)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **70** | Site Selection | Select a site for other functions | Interactive only |
| **71** | Site Inventory Browser | Interactive device inventory viewer | `SiteInventory.csv` |
| **72** | Device Statistics Viewer | Interactive device statistics browser | `DeviceStats.csv` |
| **73** | Device Tests Viewer | Interactive synthetic test results viewer | `DeviceTestResults.csv` |
| **74** | Device Config Viewer | Interactive device configuration viewer | `DeviceConfig.csv` |

### Continuous Operations (Options 75-76)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **75** | Loop Refresh | Continuous refresh of core datasets | Multiple files |
| **76** | Data Collection Loop | Continuous data collection with rate limiting | Multiple files |

### File Processing & Support (Options 77-78)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **77** | SFP Data Merge | Process and merge SFP module location data | `MergedTransceiverData.csv` |
| **78** | Support Package | Generate support package for each site | Site-specific packages |

### CLI & WebSocket Operations (Options 79-83)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **79** | CLI Shell | Interactive CLI shell for gateway/switch | Interactive session |
| **80** | ARP via WebSocket | Run ARP command on AP via WebSocket | `arp_output_raw.txt` |
| **81** | Show Default Route | Run 'show route 0.0.0.0' via shell session | `RouteDefault.csv` |
| **82** | DHCP Security Bindings | Run 'show dhcp-security binding' via shell | `DhcpSecurityBindings.csv` |
| **83** | Show VLANs | Run 'show vlans' via shell session | `Vlans.csv` |

### Advanced Operations (Options 90-96)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **90** | **DESTRUCTIVE** | Bulk AP firmware upgrade with multiple strategies | Upgrade logs |
| **91** | **DESTRUCTIVE** | Reboot devices by template list | Reboot logs |
| **92** | **DESTRUCTIVE** | Convert virtual chassis to virtual MAC | Conversion logs |
| **93** | **DESTRUCTIVE** | Bulk virtual chassis conversion by site list | Conversion logs |
| **94** | Virtual Chassis Status | Check virtual chassis to virtual MAC conversion status | `VirtualChassisConversionStatus.csv` |
| **95** | Gateway Device Statistics | Export detailed device statistics for all gateways with freshness check | `GatewayDeviceStats.csv` |
| **96** | WAN Port Conflict Detection | Check and export gateways with duplicate WAN port IP addresses | `GatewayWANPortConflicts.csv` |

## Usage Examples

### Data Collection Operations

```bash
# Export comprehensive site and device information
python MistHelper.py --menu 20 --output-format sqlite  # Sites with location data
python MistHelper.py --menu 22 --output-format sqlite  # All devices with site info

# Collect device statistics and port information
python MistHelper.py --menu 13 --output-format sqlite  # Device statistics
python MistHelper.py --menu 14 --output-format sqlite  # Port statistics

# Security and monitoring data collection
python MistHelper.py --menu 42 --output-format sqlite  # Security events
python MistHelper.py --menu 43 --output-format sqlite  # Rogue clients
python MistHelper.py --menu 1 --output-format sqlite   # Active alarms
```

### Container Deployment

```bash
# Podman deployment (recommended)
python setup-podman.py  # Detect and configure Podman
python run-misthelper.py --output-format sqlite --menu 11

# Docker deployment
docker-compose up --build
docker-compose run --rm misthelper python MistHelper.py --menu 11

# Platform-specific container scripts
run-podman.bat 11                              # Windows batch
.\run-podman.ps1 -OutputFormat sqlite -Menu 11 # PowerShell
python run-misthelper.py --menu 11             # Cross-platform
```

### Automation and Testing

```bash
# Systematic testing of all safe operations
python MistHelper.py --test

# Debug mode for troubleshooting
python MistHelper.py --test --debug

# Batch data collection for multiple operations
for menu in 11 12 13 14 15; do
    python MistHelper.py --menu $menu --output-format sqlite
done
```

## Output Formats

### SQLite Database (Recommended)
- **Location**: `data/mist_data.db`
- **Schema Design**: Natural primary keys using API business identifiers
- **Key Strategy**: Endpoint-specific optimization with natural keys, composite keys, or auto-increment fallback
- **Advantages**: 
  - Business-meaningful primary keys without artificial identifiers
  - Proper relational structure for joins and queries
  - Efficient upsert operations using `INSERT OR REPLACE`
  - Optimized indexing for query performance
  - Single-file database with full SQL capabilities

```bash
# Access SQLite database
sqlite3 data/mist_data.db
.tables                         # List all tables
.schema OrgInventory           # View table structure
SELECT * FROM SiteList LIMIT 5; # Query data
```

### CSV Files
- **Location**: Project root directory
- **Format**: Standard CSV with headers
- **Advantages**: 
  - Direct Excel compatibility
  - Simple data sharing and import
  - Human-readable text format

## Configuration

### Environment Configuration

Create a `.env` file with API credentials and operational parameters:

```env
# Mist API Configuration (Required)
MIST_HOST=api.mist.com
MIST_APITOKEN=your_api_token_here
org_id=your_organization_id

# Auto-Upgrade Configuration
AUTO_UPGRADE_UV=true                     # Auto-upgrade UV package manager
AUTO_UPGRADE_DEPENDENCIES=true           # Auto-upgrade dependencies
UPGRADE_CHECK_TIMEOUT=60                 # Upgrade timeout in seconds

# Operational Parameters
CSV_FRESHNESS_MINUTES=15                 # Data cache duration
```

### API Token Setup

1. Access Mist dashboard at https://manage.mist.com
2. Navigate to **Organization > API Tokens**
3. Create new token with **Organization Admin** privileges
4. Copy token value to `.env` file

### Organization ID Location

Organization ID is visible in Mist dashboard URL:
```
https://manage.mist.com/admin/?org_id=12345678-1234-1234-1234-123456789abc
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

## Deployment Options

### Local Installation

```bash
git clone <repository-url>
cd MistHelper
python MistHelper.py  # Dependencies install automatically
```

### Docker Deployment

```bash
# Using docker-compose
docker-compose up --build

# Manual Docker build
docker build -t misthelper .
docker run -it --rm -v ./data:/app/data -v ./.env:/app/.env misthelper
```

### Podman Deployment

```bash
# Automated setup
python setup-podman.py        # Configure Podman environment
python run-misthelper.py --menu 11

# Manual Podman deployment
podman build -t misthelper .
podman run -it --rm -v ./data:/app/data:Z -v ./.env:/app/.env:ro,Z misthelper
```

### Cross-Platform Container Scripts

| Platform | Script | Usage Example |
|----------|--------|---------------|
| **Windows Batch** | `run-podman.bat` | `run-podman.bat 11` |
| **PowerShell** | `run-podman.ps1` | `.\run-podman.ps1 -Menu 11` |
| **Python** | `run-misthelper.py` | `python run-misthelper.py --menu 11` |

## Advanced Features

### Systematic Testing

MistHelper provides comprehensive testing of all safe operations with intelligent operation filtering:

```bash
# Test all read-only operations (54 operations tested)
python MistHelper.py --test

# Test with fast mode enabled
python MistHelper.py --test --fast

# Test with debug logging
python MistHelper.py --test --debug
```

**Testing Categories:**
- **Tested Operations (54)**: All read-only data export functions, configuration exports, statistics, and reference data
- **Excluded Operations (32)**: Interactive functions, WebSocket operations, destructive operations, continuous loops, and WIP features
- **API Rate Limit Aware**: Automatically handles rate limiting during large test runs
- **Production Validation**: Confirms all core functionality works correctly with live API data

**Test Results Analysis:**
The systematic test validates core functionality by executing operations like:
- Organization alarms and device events (Options 1-2) 
- Complete site and device inventory (Options 11-12)
- Performance statistics and port data (Options 13-14)
- VPN peer statistics and gateway tests (Options 15-16)

Test execution continues until API rate limits are reached (expected behavior for large organizations), confirming proper rate limiting implementation.

### Data Processing Capabilities

- **Advanced Dependency Management**: GlobalImportManager with UV package manager integration and intelligent fallbacks
- **Natural Primary Keys**: Business-meaningful identifiers eliminating artificial database keys
- **Nested JSON Flattening**: Complex API responses converted to flat table structures with intelligent field mapping
- **PID-Controlled Rate Limiting**: Dynamic API throttling with tuning data persistence and connection pool management
- **Marvis AI Integration**: Native support for Marvis troubleshooting workflows and intelligent network analysis
- **Address Validation**: External API integration with Nominatim for intelligent address comparison and validation
- **Error Handling**: Comprehensive exception handling with automatic retry logic and detailed logging
- **Data Sanitization**: Clean formatting for Excel and database compatibility with Unicode normalization
- **Progress Tracking**: Real-time progress indicators with tqdm integration for long-running operations

### Logging and Debugging

```bash
# Enable debug logging
python MistHelper.py --debug

# Monitor log files
tail -f script.log

# Search specific operations
grep "menu option" script.log
```

## Development Integration

### API Integration Features

- **Complete Endpoint Coverage**: All major Mist API endpoints supported
- **Authentication Methods**: Token-based and legacy username/password authentication
- **Rate Limiting Compliance**: Automatic throttling to prevent API rate limit violations
- **Error Resilience**: Automatic retry logic with exponential backoff

### Custom Development Support

```python
# Import MistHelper functions for custom applications
from MistHelper import export_all_sites_to_csv, save_data_to_output

# Use core functions in custom scripts
sites_data = export_all_sites_to_csv()
save_data_to_output(custom_data, 'custom_output.csv')
```

### Testing Framework

```bash
# Run comprehensive test suite
python test_misthelper.py

# Database integrity verification
python verify_db.py

# Dependency verification
python MistHelper.py --help  # Triggers dependency check
```

## Documentation Reference

Comprehensive documentation is available in the `documentation/` directory:

- **[Installation Guide](documentation/INSTALLATION-GUIDE.md)**: Detailed setup procedures
- **[API Reference](documentation/API-REFERENCE.md)**: Complete function and endpoint documentation  
- **[Troubleshooting Guide](documentation/TROUBLESHOOTING.md)**: Common issues and solutions
- **[Container Setup](documentation/PODMAN_SETUP.md)**: Docker and Podman deployment details
- **[Implementation Summary](documentation/IMPLEMENTATION_SUMMARY.md)**: Technical architecture overview

## Security Considerations

- **Credential Security**: API tokens stored in `.env` files, never in source code
- **Network Requirements**: HTTPS access to api.mist.com required
- **Data Handling**: All data processing occurs locally, no third-party transmission
- **Permission Model**: Read-only operations by default, destructive operations clearly identified
- **Safe Defaults**: All destructive operations require explicit confirmation

## Troubleshooting

### Common Issues and Solutions

**Authentication Failures:**
```bash
# Test API connectivity
python MistHelper.py --menu 11  # Basic site list test
```

**Dependency Issues:**
```bash
# Force dependency reinstall
python MistHelper.py --skip-deps  # Skip initial check
python MistHelper.py              # Normal run will reinstall dependencies
```

**Container Deployment Issues:**
```bash
# Verify container runtime
podman --version
docker --version

# Rebuild container environment
python setup-podman.py  # Re-detect and configure
```

**Database Integrity Issues:**
```bash
# Verify database structure and data
python verify_db.py

# Examine database contents
sqlite3 data/mist_data.db ".tables"
```

### Support Resources

1. **Log Analysis**: `script.log` contains detailed operation logs
2. **Comprehensive Documentation**: All features documented with examples
3. **Systematic Testing**: Use `--test` flag to verify functionality
4. **Container Deployment**: Often resolves environment-specific issues

## Contributing

Development contributions should follow these guidelines:

1. **Repository Management**: Fork repository and create feature branches
2. **Code Standards**: Maintain comprehensive function documentation and error handling
3. **Testing Requirements**: Include both unit tests and integration tests
4. **Documentation Updates**: Update API reference and user documentation
5. **Cross-Platform Compatibility**: Ensure Windows, macOS, and Linux support

## Technical Support

For technical assistance:
1. Review the **[Troubleshooting Guide](documentation/TROUBLESHOOTING.md)**
2. Consult the **[API Reference](documentation/API-REFERENCE.md)** for function details
3. Execute systematic testing: `python MistHelper.py --test`
4. Examine detailed logs in `script.log` for error diagnostics

---

**MistHelper** - Production network operations tool for Juniper Mist infrastructure management and monitoring.
