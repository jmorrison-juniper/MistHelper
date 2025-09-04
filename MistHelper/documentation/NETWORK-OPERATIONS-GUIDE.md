# MistHelper Network Operations Guide

## Overview

MistHelper is an enterprise-grade network operations platform designed for NOC engineers managing Juniper Mist cloud infrastructure. This comprehensive tool provides 96 distinct operations covering all major Mist API endpoints with advanced features including PID-controlled rate limiting, Marvis AI integration, natural primary key database design, and sophisticated error handling. This guide provides operational procedures for network monitoring, troubleshooting, and infrastructure management.

## Operational Use Cases

### Daily Operations

#### Network Health Monitoring with Advanced Rate Management
```bash
# Continuous monitoring with PID-controlled rate limiting
python MistHelper.py --continuous --delay 30 --export-format sqlite

# Check current alarms across organization  
python MistHelper.py --menu 1 --output-format sqlite

# Review device events from past 24 hours
python MistHelper.py --menu 2 --output-format sqlite

# Monitor security events and rogue device detection
python MistHelper.py --menu 42 --output-format sqlite
python MistHelper.py --menu 43 --output-format sqlite
```

**Advanced Features:**
- **PID Rate Limiting**: Dynamic API throttling based on response times (tuning_data.json)
- **Connection Pooling**: Optimized session management for enterprise-scale operations
- **Natural Primary Keys**: Business-meaningful database identifiers for operational clarity
- **Intelligent Retry Logic**: Exponential backoff with configurable thresholds

#### Device Status and Performance Analysis
```bash
# Export comprehensive device statistics with cross-model analysis
python MistHelper.py --menu 13 --output-format sqlite

# Port utilization with intelligent aggregation
python MistHelper.py --menu 14 --output-format sqlite  

# Gateway synthetic test results with performance baselines
python MistHelper.py --menu 16 --output-format sqlite
```

**Enterprise Capabilities:**
- **GlobalImportManager**: UV package manager integration with intelligent fallbacks
- **Data Validation**: Comprehensive sanitization and error handling
- **Cross-Platform Support**: Optimized for Windows/Linux enterprise environments

#### Client Connectivity Analysis
```bash
# Wireless client statistics with trend analysis
python MistHelper.py --menu 40 --output-format sqlite

# Wired client connectivity data
python MistHelper.py --menu 41 --output-format sqlite

# Site-specific client analysis
python MistHelper.py --menu 30 --site "Site_Name" --output-format sqlite
```

### Weekly Operations

#### Infrastructure Inventory
```bash
# Complete organizational inventory audit
python MistHelper.py --menu 12 --output-format sqlite

# Site inventory with location data
python MistHelper.py --menu 20 --output-format sqlite

# Device inventory with site associations
python MistHelper.py --menu 22 --output-format sqlite
```

#### Configuration Management
```bash
# Export all organizational templates
python MistHelper.py --menu 35 --output-format sqlite

# WLAN configuration audit
python MistHelper.py --menu 48 --output-format sqlite

# License usage and compliance
python MistHelper.py --menu 58 --output-format sqlite
```

### Monthly Operations

#### Historical Analysis
```bash
# 52-week device events for trend analysis
python MistHelper.py --menu 63 --output-format sqlite

# 52-week audit logs for compliance
python MistHelper.py --menu 64 --output-format sqlite

# Combined inventory analysis by week
python MistHelper.py --menu 25 --output-format sqlite
```

#### Capacity Planning
```bash
# VPN peer statistics for WAN analysis
python MistHelper.py --menu 15 --output-format sqlite

# Switch virtual chassis statistics
python MistHelper.py --menu 24 --output-format sqlite

# Gateway device statistics with freshness check
python MistHelper.py --menu 95 --output-format sqlite
```

## Advanced Operations and Troubleshooting

### Marvis AI Integration

MistHelper provides native integration with Marvis AI for intelligent network troubleshooting:

```bash
# Interactive Marvis troubleshooting workflows
python MistHelper.py --menu 62

# Guided troubleshooting options:
# - Client connectivity issues
# - Device performance problems  
# - Network-wide analysis
# - Proactive issue identification
```

**Marvis Capabilities:**
- **Client Analysis**: Troubleshoot specific client connectivity issues
- **Device Diagnostics**: AI-powered device problem identification
- **Network Analysis**: Organization-wide network health assessment
- **Proactive Monitoring**: Identify potential issues before they impact users

### Address Validation and Comparison

For organizations maintaining external address databases:

```bash
# Compare Mist inventory with external CSV data
python MistHelper.py --menu 61 --address-check --debug

# Features:
# - Configurable similarity thresholds (ADDRESS_MATCH_THRESHOLD in .env)
# - External address validation using Nominatim API
# - Intelligent address parsing and normalization
# - Skip lists for known problematic addresses
# - Comprehensive mismatch reporting
```

### Advanced Firmware Management

**CAUTION: The following operations are destructive and require careful planning**

MistHelper provides sophisticated firmware upgrade capabilities with multiple strategies:

```bash
# Check current firmware status across organization
python MistHelper.py --menu 60 --output-format sqlite

# DESTRUCTIVE: Advanced bulk AP firmware upgrade
python MistHelper.py --menu 90
```

**Firmware Upgrade Features:**
- **Multiple Strategies**: big_bang (simultaneous), canary (phased), rrm (intelligent), serial (sequential)
- **Cross-Model Compatibility**: Universal version detection and model-specific optimization
- **P2P Firmware Sharing**: Peer-to-peer distribution with configurable cluster sizes  
- **Progress Monitoring**: Real-time upgrade status and rollback capabilities
- **Scheduling**: Immediate or time-delayed upgrade execution
- **Auto-Upgrade Configuration**: Site-level automatic firmware management

### WebSocket Operations

Real-time device command execution for advanced troubleshooting:

```bash
# Interactive CLI shell for gateways and switches
python MistHelper.py --menu 79

# WebSocket-based AP commands
python MistHelper.py --menu 80  # ARP table queries

# Automated command execution with output capture
python MistHelper.py --menu 81  # Default route information
python MistHelper.py --menu 82  # DHCP security bindings
python MistHelper.py --menu 83  # VLAN information
```

### Network Outage Investigation

1. **Initial Assessment**
   ```bash
   # Check for active alarms
   python MistHelper.py --menu 1 --debug
   
   # Review recent device events
   python MistHelper.py --menu 2 --debug
   ```

2. **Site-Specific Analysis**
   ```bash
   # Target specific site for detailed analysis
   python MistHelper.py --menu 31 --site "Affected_Site"
   python MistHelper.py --menu 32 --site "Affected_Site"
   ```

3. **Device-Level Diagnostics**
   ```bash
   # Interactive device statistics viewer
   python MistHelper.py --menu 72
   
   # Device configuration analysis
   python MistHelper.py --menu 74 --device "Device_Name"
   ```

### Security Incident Response

1. **Rogue Device Detection**
   ```bash
   # Identify rogue access points
   python MistHelper.py --menu 44 --output-format sqlite
   
   # Detect rogue clients
   python MistHelper.py --menu 43 --output-format sqlite
   ```

2. **Security Event Analysis**
   ```bash
   # Comprehensive security events
   python MistHelper.py --menu 42 --output-format sqlite
   
   # Audit trail examination
   python MistHelper.py --menu 3 --output-format sqlite
   ```

### Performance Degradation Analysis

1. **Network Performance Assessment**
   ```bash
   # Gateway synthetic test results
   python MistHelper.py --menu 19 --output-format sqlite
   
   # Port statistics for bottleneck identification
   python MistHelper.py --menu 14 --output-format sqlite
   ```

2. **Client Experience Analysis**
   ```bash
   # WiFi client session data
   python MistHelper.py --menu 34 --site "Target_Site"
   
   # Site-specific client statistics
   python MistHelper.py --menu 30 --site "Target_Site"
   ```

## Data Analysis and Reporting

### SQLite Database Queries

After data collection, use SQL queries for advanced analysis:

```sql
-- Active alarm summary by severity
SELECT severity, COUNT(*) as alarm_count
FROM OrgAlarms 
WHERE severity IS NOT NULL 
GROUP BY severity 
ORDER BY alarm_count DESC;

-- Top devices by event count
SELECT mac, hostname, COUNT(*) as event_count
FROM OrgDeviceEvents 
GROUP BY mac, hostname 
ORDER BY event_count DESC 
LIMIT 10;

-- Site inventory summary
SELECT site_name, COUNT(*) as device_count, 
       GROUP_CONCAT(DISTINCT type) as device_types
FROM AllDevicesWithSiteInfo 
GROUP BY site_name 
ORDER BY device_count DESC;

-- Gateway WAN port conflicts
SELECT COUNT(*) as conflict_count, wan_port_ip
FROM GatewayWANPortConflicts 
GROUP BY wan_port_ip 
HAVING COUNT(*) > 1;
```

### Report Generation

1. **Executive Summary Reports**
   ```bash
   # Generate support packages for management
   python MistHelper.py --menu 78
   ```

2. **Technical Analysis Reports**
   ```bash
   # Marvis action items for proactive resolution
   python MistHelper.py --menu 62 --output-format sqlite
   ```

## Maintenance Operations

### Firmware Management

**CAUTION: The following operations are destructive and require careful planning**

1. **Pre-Maintenance Assessment**
   ```bash
   # Check current firmware upgrade status
   python MistHelper.py --menu 60 --output-format sqlite
   
   # Device inventory for upgrade planning
   python MistHelper.py --menu 12 --output-format sqlite
   ```

2. **Controlled Firmware Upgrades** (Advanced Users Only)
   ```bash
   # DESTRUCTIVE: Bulk AP firmware upgrade
   # Requires careful preparation and testing
   python MistHelper.py --menu 90
   ```

### Virtual Chassis Operations

1. **Status Monitoring**
   ```bash
   # Virtual chassis conversion status
   python MistHelper.py --menu 94 --output-format sqlite
   
   # Virtual chassis statistics
   python MistHelper.py --menu 24 --output-format sqlite
   ```

2. **Configuration Changes** (Advanced Users Only)
   ```bash
   # DESTRUCTIVE: Virtual chassis to virtual MAC conversion
   # Requires extensive planning and change control
   python MistHelper.py --menu 92
   python MistHelper.py --menu 93
   ```

## Automation and Integration

### Scheduled Data Collection

Create automated scripts for regular data collection:

```bash
#!/bin/bash
# Daily NOC data collection script
DATE=$(date +%Y%m%d)
LOG_DIR="/var/log/misthelper"
DATA_DIR="/var/data/mist"

# Create timestamped backup
cp data/mist_data.db "${DATA_DIR}/mist_data_${DATE}.db"

# Collect daily operational data
python MistHelper.py --menu 1 --output-format sqlite >> "${LOG_DIR}/daily_${DATE}.log" 2>&1
python MistHelper.py --menu 2 --output-format sqlite >> "${LOG_DIR}/daily_${DATE}.log" 2>&1
python MistHelper.py --menu 13 --output-format sqlite >> "${LOG_DIR}/daily_${DATE}.log" 2>&1

# Generate alert summary
sqlite3 data/mist_data.db "SELECT severity, COUNT(*) FROM OrgAlarms GROUP BY severity;" > "${LOG_DIR}/alarm_summary_${DATE}.txt"
```

### Integration with Monitoring Systems

1. **SNMP Integration**
   - Export device statistics for SNMP monitoring system ingestion
   - Use CSV format for easy parsing by monitoring platforms

2. **Syslog Integration**
   - Configure MistHelper logging to forward to central syslog server
   - Parse device events and alarms for correlation

3. **Dashboard Integration**
   - Use SQLite database for direct integration with Grafana or similar platforms
   - Create automated reporting dashboards using SQL queries

## Security and Compliance

### Access Control

1. **API Token Management**
   - Rotate API tokens regularly (recommended: monthly)
   - Use dedicated service accounts for automated operations
   - Implement least-privilege access principles

2. **Data Protection**
   - Encrypt sensitive configuration files
   - Implement secure backup procedures for database files
   - Monitor access to output data containing network information

### Audit Trail Maintenance

```bash
# Regular audit log collection for compliance
python MistHelper.py --menu 3 --output-format sqlite

# Administrator activity monitoring
python MistHelper.py --menu 55 --output-format sqlite

# API token usage tracking
python MistHelper.py --menu 54 --output-format sqlite
```

## Best Practices

### Operational Guidelines

1. **Data Collection Frequency**
   - Real-time monitoring: Alarms and device events (every 5-15 minutes)
   - Performance metrics: Device and port statistics (every 30 minutes)
   - Inventory updates: Device inventory (daily)
   - Configuration audits: Templates and settings (weekly)

2. **Storage Management**
   - Implement database rotation for large datasets
   - Archive historical data beyond operational requirements
   - Monitor disk space usage for data directory

3. **Error Handling**
   - Monitor script.log for API rate limiting
   - Implement retry logic for critical data collection
   - Set up alerting for persistent API failures

### Performance Optimization

1. **Use SQLite for Production**
   - SQLite format provides better performance for large datasets
   - Enables complex queries and data relationships
   - Single file simplifies backup and portability

2. **Batch Operations**
   - Collect multiple datasets in single session to minimize API calls
   - Use systematic testing to validate all operations periodically

3. **Container Deployment**
   - Use container deployment for consistent environment
   - Implement automated container updates for security patches

## Support and Escalation

### Internal Troubleshooting

1. **First-Level Support**
   ```bash
   # Verify system health
   python MistHelper.py --test
   
   # Check API connectivity
   python MistHelper.py --menu 11 --debug
   ```

2. **Advanced Diagnostics**
   - Review detailed logs in script.log
   - Use debug mode for API communication analysis
   - Verify database integrity with verification tools

### Vendor Support

1. **Prepare Support Information**
   - Collect system configuration details
   - Document error messages and conditions
   - Generate support packages using menu option 78

2. **Escalation Procedures**
   - Contact Juniper Mist support with detailed network information
   - Provide API logs and error details for faster resolution
   - Maintain separate test environment for vendor troubleshooting

This guide provides comprehensive operational procedures for network engineers using MistHelper in production environments. Regular review and updates ensure alignment with evolving operational requirements and platform capabilities.
