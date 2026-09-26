[<- Back to Diagram Index](../README.md)

# Architecture Overview

System-level context and internal component relationships for MistHelper.

## System Context (C4)

Who interacts with MistHelper and what external systems does it depend on?

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {
  'primaryColor': '#E20074',
  'primaryTextColor': '#E0E0E0',
  'primaryBorderColor': '#99004D',
  'lineColor': '#FF4DA6',
  'secondaryColor': '#16213E',
  'tertiaryColor': '#1A1A2E',
  'fontFamily': 'ui-monospace, monospace'
}}}%%
flowchart TB
    noc_engineer(["NOC Engineer<br/>Network operations staff"])
    ci_system(["CI/CD System<br/>GitHub Actions"])

    subgraph misthelper["MistHelper"]
        mh["Python CLI tool<br/>270 registered menu entries"]
    end

    mist_cloud["Juniper Mist Cloud<br/>REST API + WebSocket"]
    ghcr["GitHub Container Registry<br/>ghcr.io"]
    network_devices["Network Devices<br/>APs, switches, gateways"]

    noc_engineer -->|"SSH 2200 / HTTP 8055, 8056, 8057"| mh
    ci_system -->|"Builds & Tests"| mh
    mh -->|"HTTPS REST + WebSocket"| mist_cloud
    mh -->|"OCI push"| ghcr
    mist_cloud -->|"Cloud control plane"| network_devices
```

## Internal Architecture

How MistHelper's subsystems connect and interact internally.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {
  'primaryColor': '#E20074',
  'primaryTextColor': '#E0E0E0',
  'primaryBorderColor': '#99004D',
  'lineColor': '#FF4DA6',
  'secondaryColor': '#16213E',
  'tertiaryColor': '#1A1A2E',
  'fontFamily': 'ui-monospace, monospace'
}}}%%
flowchart LR
    subgraph misthelper["MistHelper Application"]
        menu["Menu System"]
        registry["OperationRegistry"]
        api["API Layer"]
        exporters["Data Exporters"]
        db[("SQLite Backend")]
        arango[("ArangoDB")]
        redis[("Redis Stack")]

        subgraph services["Long-Running Services"]
            websocket["WebSocketManager"]
            ssh_runner["EnhancedSSHRunner"]
            pcap["PacketCaptureManager"]
            capture_portal["Upgrade portal 8056"]
            metrics_gateway["Metrics gateway 8057"]
        end

        subgraph infra["Infrastructure"]
            container["Container Runtime"]
            web_portal["Web Portal 8055"]
            ssh_server["SSH Server 2200"]
        end
    end

    subgraph external["External Systems"]
        mist_api["Mist Cloud API"]
        devices["Network Devices"]
    end

    menu --> registry --> api --> exporters --> db
    exporters --> arango
    exporters --> redis
    api --> mist_api
    websocket --> mist_api
    ssh_runner --> devices
    pcap --> mist_api
    capture_portal --> mist_api
    metrics_gateway --> mist_api
    ssh_server --> menu
    web_portal --> menu
    container --> ssh_server
    container --> web_portal
```

> **PNG fallback**: If this diagram does not render, see [architecture-overview.png](architecture-overview.png).

## Module Decomposition (`src/`)

Feature-domain packages now hold most runtime code. `MistHelper.py` remains the
entrypoint and menu dispatch surface.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {
  'primaryColor': '#E20074',
  'primaryTextColor': '#E0E0E0',
  'primaryBorderColor': '#99004D',
  'lineColor': '#FF4DA6',
  'secondaryColor': '#16213E',
  'tertiaryColor': '#1A1A2E',
  'fontFamily': 'ui-monospace, monospace'
}}}%%
flowchart TD
    entrypoint["MistHelper.py<br/>Entrypoint + Menu Dispatch"]

    subgraph core["Core Packages"]
        api["src/api/"]
        db_pkg["src/db/"]
        export_pkg["src/export/"]
        utils["src/utils/"]
        refactors["src/refactors/"]
    end

    subgraph features["Feature Packages"]
        analytics["src/analytics/"]
        capture["src/capture/"]
        device["src/device/"]
        firmware["src/firmware/"]
        gateway["src/gateway/"]
        inventory["src/inventory/"]
        org_pkg["src/org/"]
        site["src/site/"]
        ssh_pkg["src/ssh/"]
        troubleshooting["src/troubleshooting/"]
        websocket["src/websocket/"]
    end

    subgraph portals["Portal Packages"]
        ui["src/ui/"]
        upgrade_portal["src/upgrade_portal/"]
        metrics_gateway["src/metrics_gateway/"]
    end

    entrypoint --> core
    entrypoint --> features
    entrypoint --> portals
```

| Package | Primary Classes | Menu Ops |
|---------|----------------|----------|
| `src/analytics/` | `ZoneConfigurationAnalyzer`, `SiteInventoryHealthAnalyzer`, `SiteAnalyticsConfigurator` | 7, 77-79, 169 |
| `src/capture/` | `PacketCaptureManager`, `PacketCaptureDownloadManager` | 134-135 |
| `src/db/` | `DatabaseRouter`, `ArangoDBWriter`, `RedisTimeSeriesWriter`, `RedisJSONWriter` | Output backends |
| `src/device/` | Device utility modules | 128-133, 148, 207-208 |
| `src/export/` | `SiteExportUtils`, `SiteInsightsExporter` | 60-96 |
| `src/firmware/` | `FirmwareManager` | 153-157, 239 |
| `src/gateway/` | `GatewayExportUtils`, `GatewayStatsExporter`, `WAN2MigrationManager` | 31-50, 104-111, 149, 167 |
| `src/inventory/` | `OrgDeviceInventorySummaryCore`, `OrgDeviceInventoryMSPOrchestrator` | 8-9, 13-14 |
| `src/site/` | `SiteConfigManager` | 171-174 |
| `src/sle/` | `SLEExporter` | 51-55 |
| `src/ssh/` | `EnhancedSSHRunner`, `SSHRunnerManager` | 175-176 |
| `src/org/` | `OrgTicketManager` | 188-193 |
| `src/troubleshooting/` | `MarvisTroubleshootUtils` | 124-127, 139 |
| `src/websocket/` | `WebSocketManager`, `ServicePingManager` | 102-123 |
| `src/metrics_gateway/` | `MistMetricsCollector`, `PrometheusRenderer`, `SnmpPassPersistResponder` | 241 |
| `src/upgrade_portal/` | Upgrade portal modules | 239 |

## Key Subsystems

| Subsystem | Primary Classes | Purpose |
|-----------|----------------|---------|
| Menu System | `OperationRegistry`, `MistHelperTUI` | 270 registered entries, with no menu 152 |
| API Layer | `APIFetchUtils`, `RateLimitingUtils` | Paginated API calls with adaptive rate limiting |
| Data Exporters | `DataExporter`, `SQLiteDatabaseWriter`, `DatabaseRouter` | CSV, SQLite, ArangoDB, Redis JSON, and Redis TimeSeries output |
| WebSocket | `WebSocketManager`, `WebSocketCommands`, `ServicePingManager` | Real-time device commands plus extracted service-ping orchestration |
| SSH Runner | `EnhancedSSHRunner`, `SSHRunnerManager` | Paramiko-based device command execution |
| Packet Capture | `PacketCaptureManager`, `PacketCaptureDownloadManager` | Site/org packet captures with extracted poll/download handling |
| Container | Non-root user, ForceCommand SSH | Isolated session management |
| Web Portal | Gunicorn on port 8055 | Browser UI for operations |
| Upgrade Portal | `src/upgrade_portal/` on port 8056 | Pre-check, upgrade, and post-check capture workflow |
| Metrics Gateway | `src/metrics_gateway/` on port 8057 | Prometheus and SNMP monitoring output |

---

## Related Diagrams

- [Data Pipeline](data-pipeline.md) - How data flows from menu selection to output
- [Database Strategy](database-strategy.md) - Hybrid PK system for data persistence
- [Container Architecture](../infrastructure/container-architecture.md) - Container internals and SSH isolation
- [Class Hierarchy Overview](../class-hierarchy/overview.md) - Class families and dependencies
