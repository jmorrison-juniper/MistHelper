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
        mh["Python CLI tool<br/>209 operations"]
    end

    mist_cloud["Juniper Mist Cloud<br/>REST API + WebSocket"]
    ghcr["GitHub Container Registry<br/>ghcr.io"]
    network_devices["Network Devices<br/>APs, switches, gateways"]

    noc_engineer -->|"SSH 2200 / HTTP 8055"| mh
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

        subgraph realtime["Real-Time Services"]
            websocket["WebSocket Manager"]
            ssh_runner["SSH Runner"]
            pcap["Packet Capture"]
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
    ssh_server --> menu
    web_portal --> menu
    container --> ssh_server
    container --> web_portal
```

> **PNG fallback**: If this diagram does not render, see [architecture-overview.png](architecture-overview.png).

## Module Decomposition (`src/`)

Feature-domain packages extracted from `MistHelper.py` during Wave 1 and Wave 2
decomposition. Each package owns its classes and delegates back to the entrypoint
only for shared state (session, config, output routing).

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

    subgraph wave1["Wave 1 Packages"]
        clients["src/clients/"]
        device_mgmt["src/device_mgmt/"]
        events["src/events/"]
        firmware["src/firmware/"]
        maps["src/maps/"]
        monitoring["src/monitoring/"]
        nac["src/nac/"]
        org_config["src/org_config/"]
        sle["src/sle/"]
        tickets["src/tickets/"]
        utilities["src/utilities/"]
    end

    subgraph wave2["Wave 2 Packages"]
        analytics["src/analytics/"]
        capture["src/capture/"]
        export_pkg["src/export/"]
        gateway["src/gateway/"]
        inventory["src/inventory/"]
        site["src/site/"]
        ssh_pkg["src/ssh/"]
        troubleshooting["src/troubleshooting/"]
        websocket["src/websocket/"]
    end

    entrypoint --> wave1
    entrypoint --> wave2
```

| Package | Primary Classes | Menu Ops |
|---------|----------------|----------|
| `src/analytics/` | `ZoneConfigurationAnalyzer`, `SiteInventoryHealthAnalyzer`, `SiteAnalyticsConfigurator` | 7, 77-79, 169 |
| `src/capture/` | `PacketCaptureManager`, `PacketCaptureDownloadManager` | 134-135 |
| `src/clients/` | `WirelessClientExporter`, `WiredClientExporter`, `WANClientExporter` | 27-30 |
| `src/device_mgmt/` | `DeviceManagementUtils`, `DeviceConfigManager` | 128-133, 148 |
| `src/events/` | `EventExporter`, `AlarmExporter` | 20-26 |
| `src/export/` | `SiteExportUtils`, `SiteInsightsExporter` | 60-96 |
| `src/firmware/` | `FirmwareManager` | 154-157 |
| `src/gateway/` | `GatewayExportUtils`, `GatewayStatsExporter`, `WAN2MigrationManager` | 31-50, 104-111, 149, 167 |
| `src/inventory/` | `OrgDeviceInventorySummaryCore`, `OrgDeviceInventoryMSPOrchestrator` | 8-9, 13-14 |
| `src/monitoring/` | `ContinuousMonitor` | 151-152 |
| `src/site/` | `SiteConfigManager` | 171-174 |
| `src/sle/` | `SLEExporter` | 51-55 |
| `src/ssh/` | `EnhancedSSHRunner`, `SSHRunnerManager` | 175-176 |
| `src/tickets/` | `OrgTicketManager` | 188-193 |
| `src/troubleshooting/` | `MarvisTroubleshootUtils` | 124-127, 139 |
| `src/websocket/` | `WebSocketManager`, `ServicePingManager` | 102-123 |

## Key Subsystems

| Subsystem | Primary Classes | Purpose |
|-----------|----------------|---------|
| Menu System | `OperationRegistry`, `MistHelperTUI` | 193-operation interactive/CLI menu |
| API Layer | `APIFetchUtils`, `RateLimitingUtils` | Paginated API calls with adaptive rate limiting |
| Data Exporters | `DataExporter`, `SQLiteDatabaseWriter`, `DatabaseRouter` | Multi-backend output (CSV/SQLite/ArangoDB/Redis) with business keys |
| WebSocket | `WebSocketManager`, `WebSocketCommands`, `ServicePingManager` | Real-time device commands plus extracted service-ping orchestration |
| SSH Runner | `EnhancedSSHRunner`, `SSHRunnerManager` | Paramiko-based device command execution |
| Packet Capture | `PacketCaptureManager`, `PacketCaptureDownloadManager` | Site/org packet captures with extracted poll/download handling |
| Container | Non-root user, ForceCommand SSH | Isolated session management |
| Web Portal | Gunicorn on port 8055 | Browser-based UI for operations |

---

## Related Diagrams

- [Data Pipeline](data-pipeline.md) - How data flows from menu selection to output
- [Database Strategy](database-strategy.md) - Hybrid PK system for data persistence
- [Container Architecture](../infrastructure/container-architecture.md) - Container internals and SSH isolation
- [Class Hierarchy Overview](../class-hierarchy/overview.md) - All 99+ classes organized by family
