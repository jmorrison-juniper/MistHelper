# MistHelper

**A comprehensive Python application for interacting with the Juniper Mist Cloud API to extract, analyze, and manage network infrastructure data.**

MistHelper provides both interactive menu-driven access and command-line automation for network administrators managing Juniper Mist cloud-managed networks. The application s### Configuration

Create a `.env` file with your API credentials and upgrade preferences:

```env
# Mist API Configuration (Required)
MIST_HOST=api.mist.com
MIST_APITOKEN=your_api_token_here
org_id=your_organization_id

# UV Auto-Upgrade Configuration
AUTO_UPGRADE_UV=true                     # Auto-upgrade UV itself on startup
AUTO_UPGRADE_DEPENDENCIES=true           # Auto-upgrade all dependencies on startup  
UPGRADE_CHECK_TIMEOUT=60                 # Timeout for upgrade checks (seconds)

# Optional Configuration
CSV_FRESHNESS_MINUTES=15                 # Cache duration
```

### Auto-Upgrade Control

MistHelper can automatically keep UV and all dependencies updated:

#### Environment Variables
```env
AUTO_UPGRADE_UV=true                     # Keep UV package manager updated
AUTO_UPGRADE_DEPENDENCIES=true           # Keep all Python packages updated
UPGRADE_CHECK_TIMEOUT=60                 # Max time for upgrade checks
```

#### Command Line Flags
```bash
# Disable all auto-upgrades for this run
python MistHelper.py --no-upgrade --menu 11

# Force auto-upgrades even if disabled in .env
python MistHelper.py --force-upgrade --menu 11

# Skip dependency checks entirely (fastest startup)
python MistHelper.py --skip-deps --menu 11
```

#### Upgrade Behavior
- **UV Auto-Upgrade**: Checks and upgrades UV package manager on startup
- **Dependency Auto-Upgrade**: Updates all Python packages to latest versions
- **Smart Fallback**: If UV upgrade fails, continues with current version
- **Timeout Protection**: Upgrade checks timeout after configurable period
- **Version Reporting**: Shows before/after versions when upgrades occuroutput formats and deployment options for flexible integration into existing workflows.

## ✨ Key Features

- **Complete API Coverage**: Access to all major Mist API endpoints with 93 distinct operations
- **Dual Output Formats**: CSV files and hybrid SQLite database with natural primary keys
- **Interactive & Automated**: Menu-driven interface with CLI automation and systematic testing
- **Container Ready**: Docker and Podman deployment support with cross-platform scripts
- **Production Safe**: Built-in rate limiting, systematic testing, and comprehensive logging
- **Cross-Platform**: Windows, macOS, and Linux support with platform-specific optimizations

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** with pip
- **Juniper Mist API Token** (Organization Admin level recommended)
- **Organization ID** from your Mist dashboard

### Installation Options

#### Option 1: One-Command Setup (Recommended)
```bash
# Clone and run - everything auto-installs including UV!
git clone <repository-url>
cd MistHelper
python MistHelper.py  # Auto-installs UV + dependencies + creates .env template

# Follow the on-screen guidance to configure your API credentials
# Then run again: python MistHelper.py
```

#### Option 2: Manual UV Installation (For Speed)
```bash
# Install UV first for maximum speed
python -m pip install uv

# Clone and setup
git clone <repository-url>
cd MistHelper
python MistHelper.py  # Detects UV and uses it for ultra-fast setup
```

#### Option 3: Traditional pip (Works Everywhere)
```bash
git clone <repository-url>
cd MistHelper
python MistHelper.py  # Falls back to pip if UV installation fails
```

### First Run Experience

When you run MistHelper for the first time, it will:

1. **Auto-install UV** (if possible) for 10-100x faster dependency management
2. **Install all dependencies** using the fastest method available
3. **Create .env template** with all necessary configuration options
4. **Show setup guidance** with links to get your API credentials
5. **Ready to use** - just add your API token and run again!

```bash
# First run output example:
🚀 MistHelper - First Time Setup
==================================================
📝 Setting up environment configuration...
✅ Created basic .env template
⚠️  Please edit .env with your Mist API credentials before continuing
🚀 UV not found. Installing UV for faster dependency management...
   This is a one-time setup that will speed up future runs significantly.
✅ UV successfully installed: uv 0.2.18
📦 Using UV package manager for optimal performance...
🔍 Installing dependencies with UV (fast parallel mode)...
✅ Dependencies installed with UV (10-100x faster than pip).
🎯 Setup complete! MistHelper is ready with optimized performance.

============================================================
🎯 NEXT STEPS:
1. Edit .env file with your Mist API credentials
2. Get your API token from: https://manage.mist.com/...
3. Run MistHelper again: python MistHelper.py
============================================================
```

### First Run

```bash
# Interactive menu (recommended for first use)
python MistHelper.py

# Direct execution with SQLite output  
python MistHelper.py --output-format sqlite --menu 11

# CSV output format (legacy)
python MistHelper.py --output-format csv --menu 1

# Systematic testing of all safe operations
python MistHelper.py --test
```

## 📋 Complete Feature Reference

MistHelper provides **93 distinct operations** organized into logical categories. All operations are available through both interactive menu and direct CLI access.

### 🗂️ Core Data & Diagnostics (Options 1-10)

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

### 🏢 Organization-Level Data (Options 11-28)

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

### 🏢 Site-Specific Data (Options 29-34)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **29** | Site Port Statistics | Export port statistics for selected site | `SitePortStats.csv` |
| **30** | Site Clients | Export client statistics for selected site | `SiteClients.csv` |
| **31** | Site Devices | Export device list for selected site | `SiteDevices.csv` |
| **32** | Site Device Statistics | Export device statistics for selected site | `SiteDeviceStats.csv` |
| **33** | Virtual Chassis Info | Export virtual chassis info for selected switch | `VirtualChassisInfo.csv` |
| **34** | WiFi Clients | Export current WiFi clients and sessions | `SiteWiFiClients.csv` |

### 📋 Templates & Configuration (Options 35-39)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **35** | Organization Templates | Export all org templates (gateway, network, RF, etc.) | `OrgTemplates.csv` |
| **36** | Network Templates | Export network template information | `NetworkTemplates.csv` |
| **37** | RF Templates | Export RF template information | `RFTemplates.csv` |
| **38** | AP Templates | Export AP template information | `APTemplates.csv` |
| **39** | Switch Templates | Export switch template information | `SwitchTemplates.csv` |

### 📊 Analytics & Client Data (Options 40-41)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **40** | Wireless Clients | Export wireless client statistics | `OrgWirelessClients.csv` |
| **41** | Wired Clients | Export wired client statistics | `OrgWiredClients.csv` |

### 🔒 Security & Monitoring (Options 42-44)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **42** | Security Events | Export organization security events | `OrgSecurityEvents.csv` |
| **43** | Rogue Clients | Export rogue client detections | `OrgRogueClients.csv` |
| **44** | Rogue APs | Export rogue AP detections | `OrgRogueAPs.csv` |

### ⚙️ Configuration Management (Options 45-59)

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

### 📈 Status & Monitoring (Options 60-62)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **60** | Firmware Upgrade Status | Check current firmware upgrade progress | `FirmwareUpgradeStatus.csv` |
| **61** | Inventory Comparison | Compare inventory with external CSV | Console output |
| **62** | Marvis Actions | Poll Marvis actions and export open items | `MarvisActions.csv` |

### 🧪 Work In Progress Features (Options 63-65)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **63** | 52-Week Device Events | Export device events from last 52 weeks | `OrgDeviceEvents52w.csv` |
| **64** | 52-Week Audit Logs | Export audit logs from last 52 weeks | `OrgAuditLogs52w.csv` |
| **65** | Gateway Device Configs | Export configuration details for all gateways | `GatewayDeviceConfigs.csv` |

### 🎛️ Interactive Tools (Options 70-74)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **70** | Site Selection | Select a site for other functions | Interactive only |
| **71** | Site Inventory Browser | Interactive device inventory viewer | `SiteInventory.csv` |
| **72** | Device Statistics Viewer | Interactive device statistics browser | `DeviceStats.csv` |
| **73** | Device Tests Viewer | Interactive synthetic test results viewer | `DeviceTestResults.csv` |
| **74** | Device Config Viewer | Interactive device configuration viewer | `DeviceConfig.csv` |

### 🔄 Continuous Operations (Options 75-76)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **75** | Loop Refresh | Continuous refresh of core datasets | Multiple files |
| **76** | Data Collection Loop | Continuous data collection with rate limiting | Multiple files |

### 🛠️ File Processing & Support (Options 77-78)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **77** | SFP Data Merge | Process and merge SFP module location data | `MergedTransceiverData.csv` |
| **78** | Support Package | Generate support package for each site | Site-specific packages |

### 🖥️ CLI & WebSocket Operations (Options 79-83)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **79** | CLI Shell | Interactive CLI shell for gateway/switch | Interactive session |
| **80** | ARP via WebSocket | Run ARP command on AP via WebSocket | `arp_output_raw.txt` |
| **81** | Show Default Route | Run 'show route 0.0.0.0' via shell session | `RouteDefault.csv` |
| **82** | DHCP Security Bindings | Run 'show dhcp-security binding' via shell | `DhcpSecurityBindings.csv` |
| **83** | Show VLANs | Run 'show vlans' via shell session | `Vlans.csv` |

### ⚡ Advanced Operations (Options 90-93)

| Option | Function | Description | Output Files |
|--------|----------|-------------|--------------|
| **90** | 🔥 **DESTRUCTIVE** | Bulk AP firmware upgrade with multiple strategies | Upgrade logs |
| **91** | 🔥 **DESTRUCTIVE** | Reboot devices by template list | Reboot logs |
| **92** | 🔥 **DESTRUCTIVE** | Convert virtual chassis to virtual MAC | Conversion logs |
| **93** | 🔥 **DESTRUCTIVE** | Bulk virtual chassis conversion by site list | Conversion logs |

## 🎯 Usage Examples

### Data Extraction

```bash
# Export all sites and devices with location information
python MistHelper.py --menu 20 --output-format sqlite
python MistHelper.py --menu 22 --output-format sqlite

# Get comprehensive device statistics and port information
python MistHelper.py --menu 13 --output-format sqlite
python MistHelper.py --menu 14 --output-format sqlite

# Export security and monitoring data
python MistHelper.py --menu 42 --output-format sqlite  # Security events
python MistHelper.py --menu 43 --output-format sqlite  # Rogue clients
python MistHelper.py --menu 1 --output-format sqlite   # Active alarms
```

### Container Deployment

```bash
# Podman (Recommended)
python setup-podman.py  # Auto-detect Podman installation
python run-misthelper.py --output-format sqlite --menu 11

# Docker
docker-compose up --build
docker-compose run --rm misthelper python MistHelper.py --menu 11

# Windows batch script
run-podman.bat 11

# PowerShell script
.\run-podman.ps1 -OutputFormat sqlite -Menu 11
```

### Automation & Testing

```bash
# Test all safe operations systematically
python MistHelper.py --test

# Test with debug logging
python MistHelper.py --test --debug

# Batch data collection
for menu in 11 12 13 14 15; do
    python MistHelper.py --menu $menu --output-format sqlite
done
```

## 📄 Output Formats

### Hybrid SQLite Database (Recommended)
- **File**: `data/mist_data.db`
- **Schema**: Natural primary keys using API business identifiers
- **Strategy**: Endpoint-specific optimization (natural keys, composite keys, auto-increment fallback)
- **Benefits**: 
  - No artificial `api_id` fields needed
  - Proper business key relationships
  - Efficient upsert operations with `INSERT OR REPLACE`
  - Optimized indexing for performance
  - Single file storage with SQL query capabilities

```bash
# Access hybrid SQLite database
sqlite3 data/mist_data.db
.tables
.schema OrgInventory  # View natural primary key schema
SELECT * FROM SiteList LIMIT 5;
```

### CSV Files (Legacy)
- **Location**: Project root directory
- **Format**: Standard CSV with headers
- **Benefits**: 
  - Excel compatibility
  - Easy data sharing
  - Human-readable format

## 🔧 Configuration

### Environment Variables

Create a `.env` file with your API credentials:

```env
# Mist API Configuration (Required)
MIST_HOST=api.mist.com
MIST_APITOKEN=your_api_token_here
org_id=your_organization_id

# Optional Configuration
MIST_USERNAME=your_username@example.com  # For legacy auth
MIST_PASSWORD=your_password              # For legacy auth
CSV_FRESHNESS_MINUTES=15                 # Cache duration
```

### API Token Setup

1. Log into your Mist dashboard
2. Go to **Organization > API Tokens**
3. Create a new token with **Organization Admin** privileges
4. Copy the token to your `.env` file

### Organization ID

Find your Organization ID in the Mist dashboard URL:
```
https://manage.mist.com/admin/?org_id=12345678-1234-1234-1234-123456789abc
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

## 🚀 Deployment Options

### Local Installation

```bash
git clone <repository-url>
cd MistHelper
python MistHelper.py  # Dependencies auto-install
```

### Docker Deployment

```bash
# Using docker-compose (recommended)
docker-compose up --build

# Manual Docker build
docker build -t misthelper .
docker run -it --rm -v ./data:/app/data -v ./.env:/app/.env misthelper
```

### Podman Deployment

```bash
# Automatic setup (recommended)
python setup-podman.py
python run-misthelper.py --menu 11

# Manual Podman
podman build -t misthelper .
podman run -it --rm -v ./data:/app/data:Z -v ./.env:/app/.env:ro,Z misthelper
```

### Cross-Platform Scripts

| Platform | Script | Usage |
|----------|--------|-------|
| **Windows** | `run-podman.bat` | `run-podman.bat 11` |
| **PowerShell** | `run-podman.ps1` | `.\run-podman.ps1 -Menu 11` |
| **Cross-Platform** | `run-misthelper.py` | `python run-misthelper.py --menu 11` |

## 🔍 Advanced Features

### Systematic Testing

MistHelper includes comprehensive testing capabilities:

```bash
# Test all safe operations (54 operations tested)
python MistHelper.py --test

# Operations tested include:
# - All read-only data exports
# - Event and alarm definitions
# - Templates and configurations
# - Statistics and analytics

# Operations skipped (for safety):
# - Interactive functions requiring user input
# - WebSocket operations
# - Destructive operations (reboots, upgrades)
# - Continuous loops
```

### Data Processing Features

- **Automatic Data Flattening**: Complex nested JSON converted to flat CSV/table structure
- **Rate Limiting**: Built-in API throttling with dynamic delays
- **Error Handling**: Comprehensive error catching and logging
- **Data Sanitization**: Clean data formatting for Excel compatibility
- **Progress Tracking**: Real-time progress bars for long operations

### Logging & Debugging

```bash
# Enable debug logging
python MistHelper.py --debug

# Check log files
tail -f script.log

# Monitor specific operations
grep "menu option" script.log
```

## 🛠️ Development & Integration

### API Integration

MistHelper is built on the official Mist API with:
- **Complete endpoint coverage**: All major API endpoints supported
- **Authentication handling**: Token-based and legacy username/password
- **Rate limiting compliance**: Automatic throttling to prevent API limits
- **Error resilience**: Automatic retry logic and graceful failure handling

### Custom Development

```python
# Import MistHelper functions
from MistHelper import export_all_sites_to_csv, save_data_to_output

# Use in your scripts
sites_data = export_all_sites_to_csv()
save_data_to_output(custom_data, 'custom_output.csv')
```

### Testing Framework

```bash
# Run built-in test suite
python test_misthelper.py

# Database verification
python verify_db.py

# Dependency verification
python MistHelper.py --help  # Triggers dependency check
```

## 📚 Documentation

MistHelper includes comprehensive documentation:

- **[Installation Guide](INSTALLATION-GUIDE.md)**: Detailed setup instructions
- **[API Reference](API-REFERENCE.md)**: Complete function and endpoint documentation  
- **[Troubleshooting Guide](TROUBLESHOOTING.md)**: Common issues and solutions
- **[Container Setup](PODMAN_SETUP.md)**: Docker and Podman deployment details
- **[Implementation Summary](IMPLEMENTATION-SUMMARY.md)**: Technical architecture details

## 🔐 Security Considerations

- **API Token Security**: Store tokens securely in `.env` files (not in code)
- **Network Access**: Requires HTTPS access to api.mist.com
- **Data Handling**: All data remains local - no third-party data transmission
- **Permission Model**: Uses read-only operations by default
- **Safe Defaults**: Destructive operations clearly marked and require explicit selection

## 🐛 Troubleshooting

### Common Issues

**Authentication Errors:**
```bash
# Verify API token and organization ID
python MistHelper.py --menu 11  # Test basic connectivity
```

**Missing Dependencies:**
```bash
# Force dependency reinstall
python MistHelper.py --skip-deps  # Skip check, then run normally
python MistHelper.py  # Dependencies will auto-install
```

**Container Issues:**
```bash
# Check Podman/Docker status
podman --version
docker --version

# Rebuild container
python setup-podman.py  # Re-detect and configure
```

**Database Issues:**
```bash
# Verify database integrity
python verify_db.py

# Check database contents
sqlite3 data/mist_data.db ".tables"
```

### Getting Help

1. **Check logs**: `script.log` contains detailed operation logs
2. **Review documentation**: Each feature is documented in detail
3. **Test systematically**: Use `--test` flag to verify functionality
4. **Container deployment**: Often resolves environment-specific issues

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature-name`
3. **Add comprehensive tests**: Use existing test patterns
4. **Update documentation**: Include API reference updates
5. **Submit pull request**: With detailed description

### Development Standards

- **Function Documentation**: Every function includes docstring
- **Error Handling**: Comprehensive try/catch blocks
- **Logging**: Detailed operation logging
- **Testing**: Both unit tests and integration tests
- **Cross-Platform**: Windows, macOS, and Linux compatibility

## 📞 Support

For technical support:
1. Check the **[Troubleshooting Guide](TROUBLESHOOTING.md)**
2. Review **[API Reference](API-REFERENCE.md)** for function details
3. Use systematic testing: `python MistHelper.py --test`
4. Check logs in `script.log` for detailed error information

---

**MistHelper** - Comprehensive Juniper Mist API automation for network infrastructure management.
