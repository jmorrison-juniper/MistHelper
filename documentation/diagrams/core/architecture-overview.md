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
C4Context
    title MistHelper - System Context

    Person(noc_engineer, "NOC Engineer", "Network operations staff using MistHelper via SSH or local terminal")
    Person(ci_system, "CI/CD System", "GitHub Actions running quality gates and container builds")

    System(misthelper, "MistHelper", "Python CLI tool for Mist Cloud network operations, data export, and device management")

    System_Ext(mist_cloud, "Juniper Mist Cloud", "REST API and WebSocket endpoints for network management")
    System_Ext(ghcr, "GitHub Container Registry", "Container image storage (ghcr.io)")
    System_Ext(network_devices, "Network Devices", "APs, switches, gateways managed by Mist")

    Rel(noc_engineer, misthelper, "Uses", "SSH (2200) / Terminal / HTTP (8055)")
    Rel(ci_system, misthelper, "Builds & Tests", "GitHub Actions")
    Rel(misthelper, mist_cloud, "Calls API", "HTTPS REST + WebSocket")
    Rel(misthelper, ghcr, "Publishes image", "OCI push")
    Rel(mist_cloud, network_devices, "Manages", "Cloud control plane")
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
architecture-beta
    group misthelper[MistHelper Application]

    service menu(server)[Menu System] in misthelper
    service registry(server)[OperationRegistry] in misthelper
    service api(cloud)[API Layer] in misthelper
    service exporters(disk)[Data Exporters] in misthelper
    service db(database)[SQLite Backend] in misthelper

    group realtime[Real-Time Services] in misthelper
    service websocket(internet)[WebSocket Manager] in realtime
    service ssh_runner(server)[SSH Runner] in realtime
    service pcap(server)[Packet Capture] in realtime

    group infra[Infrastructure] in misthelper
    service container(server)[Container Runtime] in infra
    service web_portal(internet)[Web Portal 8055] in infra
    service ssh_server(server)[SSH Server 2200] in infra

    group external[External Systems]
    service mist_api(cloud)[Mist Cloud API] in external
    service devices(server)[Network Devices] in external

    menu:R --> L:registry
    registry:R --> L:api
    api:R --> L:exporters
    exporters:B --> T:db
    api:B --> T:mist_api
    websocket:B --> T:mist_api
    ssh_runner:R --> L:devices
    pcap:B --> T:mist_api
    ssh_server:T --> B:menu
    web_portal:T --> B:menu
    container:R --> L:ssh_server
    container:R --> L:web_portal
```

> **PNG fallback**: If the architecture-beta diagram does not render, see [architecture-overview.png](architecture-overview.png).

## Key Subsystems

| Subsystem | Primary Classes | Purpose |
|-----------|----------------|---------|
| Menu System | `OperationRegistry`, `MistHelperTUI` | 159-operation interactive/CLI menu |
| API Layer | `APIFetchUtils`, `RateLimitingUtils` | Paginated API calls with adaptive rate limiting |
| Data Exporters | `DataExporter`, `SQLiteDatabaseWriter` | Dual CSV/SQLite output with business keys |
| WebSocket | `WebSocketManager`, `WebSocketCommands` | Real-time device commands |
| SSH Runner | `EnhancedSSHRunner`, `SSHRunnerManager` | Paramiko-based device command execution |
| Packet Capture | `PacketCaptureManager` | Site and org-level packet captures |
| Container | Non-root user, ForceCommand SSH | Isolated session management |
| Web Portal | Gunicorn on port 8055 | Browser-based UI for operations |

---

## Related Diagrams

- [Data Pipeline](data-pipeline.md) - How data flows from menu selection to output
- [Database Strategy](database-strategy.md) - Hybrid PK system for data persistence
- [Container Architecture](../infrastructure/container-architecture.md) - Container internals and SSH isolation
- [Class Hierarchy Overview](../class-hierarchy/overview.md) - All 99+ classes organized by family
