# Data Model: Mermaid Documentation Suite

**Feature**: 016-mermaid-documentation-suite  
**Date**: 2026-03-28

## Entities

This feature is documentation-only with one CI utility. The "data model" describes the artifacts produced and their relationships, plus the lint script's internal model.

### Entity: DiagramFile

A markdown file containing one or more Mermaid code blocks.

| Field | Type | Description |
|-------|------|-------------|
| path | string | Relative path from repo root (e.g., `documentation/diagrams/data-pipeline.md`) |
| location | enum | `readme-inline` or `docs` |
| diagram_blocks | list[DiagramBlock] | Mermaid code blocks in this file |
| navigation_links | list[string] | Anchor links to/from other DiagramFiles |

### Entity: DiagramBlock

A single Mermaid fenced code block within a DiagramFile.

| Field | Type | Description |
|-------|------|-------------|
| type | string | Mermaid keyword (e.g., `flowchart`, `sequenceDiagram`, `classDiagram`) |
| is_beta | boolean | True if type ends in `-beta` |
| fallback_png | string or null | Path to PNG fallback (required if is_beta=True) |
| theme_init | string | The `%%{init}%%` directive applied |
| node_count | integer | Approximate node count (target: <=50) |
| referenced_identifiers | list[string] | Class/method names referenced in diagram labels |

### Entity: ColorTheme

The T-Mobile dark-mode palette applied across all diagrams.

| Field | Type | Description |
|-------|------|-------------|
| name | string | `tmobile-dark` |
| primary_accent | hex | `#E20074` (T-Mobile Magenta) |
| secondary_accent | hex | `#FF6F91` (Light Magenta) |
| tertiary_accent | hex | `#99004D` (Deep Magenta) |
| background | hex | `#1A1A2E` (Near Black) |
| surface | hex | `#16213E` (Dark Gray) |
| text_primary | hex | `#E0E0E0` (Off White) |
| text_secondary | hex | `#A0A0B0` (Light Gray) |
| link_color | hex | `#FF4DA6` (Soft Magenta) |
| safe_ops | hex | `#00C853` (Green) |
| warning_ops | hex | `#FFD600` (Amber) |
| danger_ops | hex | `#FF1744` (Red) |
| wip_ops | hex | `#448AFF` (Blue) |

### Entity: CodebaseReference

An identifier extracted from a Mermaid diagram that should match a real Python symbol.

| Field | Type | Description |
|-------|------|-------------|
| identifier | string | The class/method/operation name (e.g., `DataExporter`, `fetch_with_pagination`) |
| source_file | string | Diagram file path where the reference appears |
| source_line | integer | Line number in the diagram file |
| reference_type | enum | `class`, `method`, or `operation_number` |
| validated | boolean | True if identifier found in codebase |
| closest_match | string or null | Fuzzy match suggestion if not found |

## Relationships

```
DiagramFile 1--* DiagramBlock : contains
DiagramBlock *--1 ColorTheme : applies
DiagramBlock 1--* CodebaseReference : references
DiagramFile *--* DiagramFile : cross-links (navigation)
```

## Class Family Inventory (for class hierarchy diagrams)

Based on codebase exploration, the 99+ classes split into these families:

| Family | Count | Key Members |
|--------|-------|-------------|
| Infrastructure & Core | 2 | DataDirectoryChecker, PerformanceMonitor |
| Configuration Objects | 6 | SSHConnectionConfig, SSHExecutionConfig, AddressValidationConfig, MapViewerConfig, DeviceFetchConfig, EndpointConfig |
| Utility Classes | 23 | TimeUtils, InputUtils, CacheUtils, DisplayUtils, FilePathUtils, EnvironmentUtils, ValidationUtils, ConfigUtils, RateLimitingUtils, RoutingUtils, AddressUtils, NameNormalizationUtils, InteractiveDisplayUtils, TroubleshootUtils, DeviceUtilityCommands, DeviceUtils, PromptNetworkDeviceUtils, PromptClientUtils, PromptUtils, InsightMetricsUtils, DataCollectionManager, plus others |
| API Fetching | 4 | APICoreFetchUtils, APITenantFetchUtils, APIFetchUtils, DeviceDataFetcher |
| Data Processing & Export | 8 | DataProcessingUtils, MarvisDataUtils, DatabaseSchemaUtils, SQLiteDatabaseWriter, DataExporter, APIDataFetcher, SFPTransceiverDataProcessor, ConstDefinitionsExporter |
| Org-Level Exporters | 10 | OrgAlarmEventExporter, OrgSiteExporter, OrgInventoryExporter, OrgDeviceStatsExporter, OrgTemplateExporter, OrgClientSecurityExporter, OrgAdminExporter, OrgConfigExporter, OrgExportUtils, OfflineDeviceReporter |
| Site-Level Exporters | 5 | SiteDeviceExporter, SiteClientExporter, SiteConfigExporter, SiteAnomalyExporter, SiteExportUtils |
| Gateway/Special Exporters | 4 | GatewayTestExporter, GatewayStatsExporter, GatewayExportUtils, MSPInventoryExporter |
| WebSocket & Network | 5 | WebSocketManager, WebSocketNetworkDiagCommands, WebSocketCommands, ServicePingManager |
| Managers & Advanced | 28 | PacketCaptureManager, EnhancedSSHRunner, SSHRunnerManager, CLIShellManager, ARPCommandManager, VirtualChassisManager, FirmwareManager, BulkAPFirmwareUpgrader, BulkSwitchFirmwareUpgrader, MapsManager, WAN2MigrationManager, WANProbeConfigManager, and 16 more |
| UI/TUI | 2 | MistHelperTUI, (launcher) |
| System/Registry | 2 | OperationRegistry, TelemetryEmitter |

**Total: 99+ classes across 12 families**

## Operation Registry Summary (for menu mindmap)

| Category | Count | Menu Numbers |
|----------|-------|-------------|
| Safe | 18 | 1,3,4,11-13,15-17,19-28,35-48,54-55,57-59,66-67,82 |
| Interactive Safe | 15 | 29-34,49-53,68-74,81,84-86 |
| Interactive | 21 | 9-10,56,61-62,79,101-103,105,112,115,117,136-139,143-146,156-157 |
| WebSocket | 18 | 5-8,80,87-89,123-135,141 |
| Destructive | 50 | 90-100,104,106-111,113-114,116,118,120,122,140,142,147-155 |
| Resource Intensive | 3 | 14,18,77-78 |
| WIP | 3 | 63-65 |
| Continuous Loop | 2 | 75-76 |
| **Total** | **159** | |

## PK Strategy Entries (for database ER diagram)

| Endpoint | PK Type | Primary Key | Indexes |
|----------|---------|-------------|---------|
| listOrgSites | natural_pk | [id] | org_id, name, country_code, address |
| getOrgInventory | natural_pk | [id] | org_id, site_id, mac, serial, model, type |
| listOrgRfTemplates | natural_pk | [id] | org_id, name, band |
| searchOrgDeviceEvents | composite_pk | [id, device_id, timestamp] | device_id, timestamp, type, org_id, site_id |
| listOrgDevicesStats | composite_pk | [device_id, timestamp] | device_id, timestamp, org_id, site_id, type |
| searchOrgAlarms | composite_pk | [id, org_id, timestamp] | org_id, timestamp, severity, type, site_id |
| getOrgLicensesSummary | auto_increment_with_unique | [misthelper_internal_id] | org_id, sku, type |
