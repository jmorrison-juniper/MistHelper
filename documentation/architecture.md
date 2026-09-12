# Architecture

This page holds the structure of the code and the diagrams that describe it.

Read [the diagram suite](diagrams/README.md) for all 20 diagram types.

## The diagrams

MistHelper carries a full diagram suite with 20 Mermaid diagram types. The suite
covers the architecture, the class hierarchy, the operations, and the
infrastructure. Every diagram uses the same dark theme.

<!-- INLINE DIAGRAM: Architecture Overview (flowchart) -->

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
    api --> mist_api
    websocket --> mist_api
    ssh_runner --> devices
    pcap --> mist_api
    ssh_server --> menu
    web_portal --> menu
    container --> ssh_server
    container --> web_portal
```

> See [detailed architecture diagrams](diagrams/core/architecture-overview.md) including C4 Context view.

<!-- INLINE DIAGRAM: Menu Mindmap -->

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
mindmap
   root((MistHelper<br/>241 Operations))
    Safe Org Exports (64)
      Sites and Analysis 1-7
      Device Inventory 8-13
      Device Stats 15-17
      Events and Logs 20-26
      Client Stats 27-30
      Gateway Ops 31-36
      Templates 37-41
      Config and Admin 42-50
      SLE and Insights 51-55
      Misc Exports 56-58
      Support and Assets 188, 193
      JSI and Mist Edge 204-205
      Org Searches 230-234
    Interactive Safe (72)
      Site Devices 60-72
      Site Insights 73-79
      Site Stats 80-91
      Viewers 92-96
      Site Searches 195-203
      Site Beacon and Assets 209-213
      Site Event Searches 214-220
      Site Client and Device Searches 221-224
      Site Stats and Zones 225-229
      Counts and MSP Licenses 235-238
      Org SecIntel Profile 240
    Resource Intensive (10)
      Heavy Inventory 14, 18-19
      Bulk Exports 59
      Long-Running 97-101
      Bulk Upgrade 153
    WebSocket (22)
      Show Commands 102-115
      Diagnostics 116-123
    Interactive (29)
      Exit 0
      Device Diag 124-127
      Device Mgmt 128-133
      Packet Capture 134-135
      Tools 136-147
      Config Mgmt 148-150
      Ticket Viewer 192
    Continuous (1)
      Loops 151
    Destructive (42)
      ::icon(fa fa-warning)
      Firmware 154-157
      Reboot 158-160
      Virtual Chassis 161-162
      Templates 163-167
      Site Config 168-170
      Test Data 171-174
      SSH Runners 175-176
      Clear Reset 177-187
      Support Tickets 189-191
      Gateway Template 194
      Synthetic Probes 206
      AP Profile Migration 207-208
      Upgrade Capture Portal 239
```

> See [full operations reference](diagrams/operations/operations-reference.md) with lifecycle states, NOC engineer journey, and safety requirements.
>
> **[Browse all diagrams ->](diagrams/README.md)**

---

## Directory & Runtime Layout

| Path | Purpose |
|------|---------|
| `MistHelper.py` | Runtime entrypoint and menu registry. The decomposition moved most logic into `src/`. |
| `src/` | Extracted modules that mirror the Mist API and mistapi hierarchy |
| `tools/ste_linter/` | Simplified Technical English compliance linter and dictionary extractor |
| `data/` | SQLite DB (`mist_data.db`), generated CSV outputs, derived artifacts; polyglot backends run in containers |
| `CombinedInventory_ByWeek/` | Time-series weekly inventory snapshots |
| `data/SSH_COMMANDS.CSV` | Fallback SSH command list (legacy root path still supported) |
| `delay_metrics.json` / `tuning_data.json` | Adaptive rate / tuning persistence |
| `data/script.log` | Unified runtime log |
| `Dockerfile` / `Containerfile` | Two container strategies (UV hybrid vs simplified pip build). Both verify TLS certificates. |
| `compose.yml` | Orchestrated service definition (uses `Containerfile` by default) |
| `agents.md` | Internal "Agents Guide" (style, safety, refactor guidance) |

All export CSVs are now written inside `data/` (the code enforces a data directory even if a legacy doc claims root CSV placement).

---

## Architecture Evolution

MistHelper started as a single-file script (`MistHelper.py`). The decomposition
moved most logic into a modular `src/` package. The target structure mirrors
both the **Mist Cloud API hierarchy** (from the OpenAPI spec) and **Thomas
Munzer's mistapi library** (`tmunzer/mistapi_python`), so that the internal
organization matches the APIs that the tool consumes.

### Size Facts

Measured on 2026-08-05.

| Area | Python lines | Files |
|------|--------------|-------|
| `MistHelper.py` | 6,169 | 1 |
| `src/` | 124,675 | 363 |
| `tests/` | 129,893 | -- |

The entrypoint held roughly 28,000 lines before the decomposition. It now holds
6,169. The test suite is now larger than the source it covers.

### Current `src/` Layout

```text
src/
├── analytics/              # Site inventory health analysis and zone configuration
├── api/                    # API operation modules (orgs, sites, const)
├── audit/                  # Audit log operations
├── auth/                   # Authentication and session management
├── bootstrap/              # Dependency checks and package installation
├── cache/                  # Caching utilities
├── capture/                # Packet capture workflows and download management
├── config/                 # Configuration loading and resolution
├── data/                   # Shared data helpers
├── dataclasses/            # Structured payload definitions
├── db/                     # Database backends (ArangoDB, Redis, retention, routing)
├── device/                 # Device utility operations and AP profile migration
├── export/                 # Site data export and insights extraction
├── firmware/               # Firmware management operations
├── gateway/                # Gateway exports, stats, overrides, WAN migration
├── input/                  # Input handling utilities
├── inventory/              # Device inventory summary, MSP orchestration, CSV comparison
├── maps/                   # Maps manager operations
├── marvis/                 # Marvis AI integration
├── menu/                   # Menu system and option dispatch
├── network/                # Network configuration operations
├── org/                    # Organization operations and synthetic probes
├── org_data_collector.py   # Org-level data collection
├── output/                 # Output formatting (writer)
├── refactors/              # Extraction targets from the decomposition waves
├── reports/                # Report generation
├── site/                   # Site configuration management (test sites, RF, profiles)
├── ssh/                    # SSH runner and execution management
├── ssid_consolidation/     # SSID consolidation operations
├── time/                   # Time and lookback window utilities
├── troubleshooting/        # Marvis troubleshooting workflows
├── ui/                     # Web portal components
├── utils/                  # Shared utilities and the operation registry
├── validation/             # Input validation
├── wan_hub_group_manager.py  # WAN hub/group operations
├── wan_vpn_builder.py      # WAN VPN builder
├── websocket/              # WebSocket commands, diagnostics, service ping
├── constants.py            # Shared constants
└── __init__.py
```

### Decomposition Status

| Module | Status | Description |
|--------|--------|-------------|
| `src/db/` | **Done** | ArangoDB writer, Redis writer, retention, routing |
| `src/export/` | **Done** | Output writer (`DataExporter.write_with_format_selection`) |
| `src/constants.py` | **Done** | Shared constants |
| `src/wan_*.py` | **Done** | WAN hub group manager, VPN builder |
| `src/analytics/` | **Done (Wave 2)** | Site inventory health analyzer, site analytics configurator, zone analyzer |
| `src/capture/` | **Done (Wave 2)** | Canonical packet capture manager + download/poll helper extraction |
| `src/export/` | **Done (Wave 2)** | Site export utilities and site insights exporter |
| `src/gateway/` | **Done (Wave 2)** | Gateway exports, stats exporter, override analyzer, WAN2 migration, probe overrides |
| `src/inventory/` | **Done (Wave 2)** | Org device inventory summary, MSP orchestrator, CSV comparator |
| `src/site/` | **Done (Wave 2)** | Site config manager (test sites, RF templates, device profiles) |
| `src/ssh/` | **Done (Wave 2)** | SSH runner + SSH runner manager (orchestration retained in entrypoint) |
| `src/troubleshooting/` | **Done (Wave 2)** | Marvis troubleshooting helpers split from entrypoint |
| `src/websocket/` | **Done (Wave 2)** | WebSocket manager, commands, diagnostics, service ping manager + discovery |
| `src/api/` | In Progress | API operation modules (continuing incremental migration) |
| `src/auth/` | In Progress | Authentication/session flows |
| `src/ui/` | In Progress | Web portal extraction |

### Wave 2 Module Ownership (Phases 1-9)

All 9 phases completed with hard-gate evidence. Each phase passed: extraction, tests, quality gates, menu/API/output parity, import graph, runtime coupling, and sign-off.

| Phase | Package | Key Classes | Menu Operations |
|-------|---------|-------------|-----------------|
| 1 | `src/analytics/` | `SiteInventoryHealthAnalyzer`, `SiteAnalyticsConfigurator` | 7, 169 |
| 2 | `src/troubleshooting/`, `src/ssh/` | `MarvisTroubleshootUtils`, `SSHRunnerManager` | 124-127, 139, 175-176 |
| 3 | `src/gateway/` | `WAN2MigrationManager`, `WanProbeDeviceOverrideManager` | 149, 167 |
| 4 | `src/site/` | `SiteConfigManager` | 171-174 |
| 5 | `src/export/` | `SiteExportUtils`, `SiteInsightsExporter` | 60-96 |
| 6 | `src/inventory/` | `OrgDeviceInventorySummaryCore`, `OrgDeviceInventoryMSPOrchestrator` | 8-9, 13-14 |
| 7 | `src/gateway/` | `GatewayExportUtils`, `GatewayStatsExporter`, `GatewayOverrideAnalyzer` | 31-50, 99, 163 |
| 8 | `src/websocket/` | `ServicePingManager`, `ServicePingDiscoveryMixin` | 120-121 |
| 9 | `src/capture/` | `PacketCaptureManager`, `PacketCaptureDownloadManager` | 134-135 |

Compatibility surface preserved: `MistHelper.py` remains the runtime entrypoint with delegated ownership in `src/`. Hard-gate validations passed for all phases including menu/API/output parity, import graph cycle detection, runtime coupling isolation, and deployment pipeline.

### Guiding Principles

- **New features go in `src/`**, not `MistHelper.py`
- **MistHelper.py remains the entrypoint** but delegates to `src/` modules
- **Feature-domain packages** -- modules are organized by functional domain (analytics, capture, gateway, etc.)
- **Incremental migration** -- extract one class/feature at a time, keep tests green

---
