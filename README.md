# MistHelper
Network Operations & Data Export Tool for Juniper Mist Cloud

[![Quality Gates](https://github.com/jmorrison-juniper/MistHelper/actions/workflows/ci.yml/badge.svg)](https://github.com/jmorrison-juniper/MistHelper/actions/workflows/ci.yml)
[![Container Build](https://github.com/jmorrison-juniper/MistHelper/actions/workflows/container-build.yml/badge.svg)](https://github.com/jmorrison-juniper/MistHelper/actions/workflows/container-build.yml)

**Operation Count:** The code currently defines 194 actionable menu entries (1-194), organized into 31 logical groups with no gaps. Exit is menu 0.

MistHelper is a production-focused Python application that streamlines large-scale Juniper Mist Cloud data extraction, enrichment, transformation, and limited lifecycle operations. It supports both interactive (menu) and fully automated CLI execution, with flexible output to CSV files, a local SQLite database, or a polyglot backend (ArangoDB for documents, Redis for time-series and JSON caching) using natural/composite business keys (no artificial surrogate IDs for core entities). The codebase emphasizes safety, transparency, and predictable behavior-aligned with the included internal Agents Guide and NASA/JPL style defensive programming practices.

> **[Full Documentation Wiki](https://github.com/jmorrison-juniper/MistHelper/wiki)** | [Menu Reference](https://github.com/jmorrison-juniper/MistHelper/wiki/Menu-Reference) | [Troubleshooting](https://github.com/jmorrison-juniper/MistHelper/wiki/Troubleshooting) | [Container Setup](https://github.com/jmorrison-juniper/MistHelper/wiki/Container-Setup)

## Quality Gates

Every PR runs these checks in parallel via GitHub Actions:

| Gate | Tool | Threshold |
|------|------|-----------|
| Lint | Ruff | Zero violations |
| Type Check | mypy --strict | Phased enforcement |
| Tests | pytest + coverage | >= 70% |
| Security | Bandit | Zero findings |
| Dependencies | pip-audit | Zero vulnerabilities |

## Deployment Options

| Method | File | Description |
|--------|------|-------------|
| Systemd | `deploy/misthelper.service` | Standalone host deployment |
| Podman Quadlet | `deploy/misthelper.container` | Containerized with auto-restart |
| Docker Compose | `compose.yml` | Container orchestration |

See `deploy/.env.example` for environment variable documentation. For full container and SSH setup, see the [Container Setup](https://github.com/jmorrison-juniper/MistHelper/wiki/Container-Setup) and [SSH Remote Access](https://github.com/jmorrison-juniper/MistHelper/wiki/SSH-Remote-Access) wiki pages.

---

## Visual Documentation

MistHelper includes a comprehensive [visual documentation suite](documentation/diagrams/README.md) with 20 Mermaid diagram types covering architecture, class hierarchy, operations, and infrastructure -- all themed with T-Mobile dark-mode colors.

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

> See [detailed architecture diagrams](documentation/diagrams/core/architecture-overview.md) including C4 Context view.

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
   root((MistHelper<br/>195 Operations))
    Safe Org Exports (60)
      Sites and Analysis 1-7
      Device Inventory 8-14
      Device Stats 15-19
      Events and Logs 20-26
      Client Stats 27-30
      Gateway Ops 31-36
      Templates 37-41
      Config and Admin 42-50
      SLE and Insights 51-55
      Misc Exports 56-59
    Interactive Safe (37)
      Site Devices 60-72
      Site Insights 73-79
      Site Stats 80-91
      Viewers 92-96
    Resource Intensive (6)
      Long-Running 97-101
      Bulk 153
    WebSocket (22)
      Show Commands 102-115
      Diagnostics 116-123
    Interactive (27)
      Device Diag 124-127
      Device Mgmt 128-133
      Packet Capture 134-135
      Tools 136-147
      Config Mgmt 148-150
    Continuous (2)
      Loops 151-152
    Destructive (41)
      ::icon(fa fa-warning)
      Firmware 154-157
      Reboot 158-160
      Virtual Chassis 161-162
      Templates 163-167
      Site Config 168-170
      Test Data 171-174
      SSH Runners 175-176
      Clear Reset 177-187
      Support Tickets 188-193
      Gateway Template 194
```

> See [full operations reference](documentation/diagrams/operations/operations-reference.md) with lifecycle states, NOC engineer journey, and safety requirements.
>
> **[Browse all diagrams ->](documentation/diagrams/README.md)**

---

## Core Capabilities

* Multi-mode execution: interactive menu or direct CLI (`--menu <id>`)
* Multi-backend output: CSV (simple exchange), SQLite (`data/mist_data.db`), or polyglot (ArangoDB + Redis) with adaptive routing strategies
* Hybrid primary key strategy: natural keys when stable IDs exist, composite keys for time-series, and guarded fallback
* Adaptive dependency and import system (`GlobalImportManager`) with UV-to-pip fallback and optional auto-upgrade (disable in containers)
* Intelligent rate limiting & pacing (delay metrics + tuning persistence via `delay_metrics.json`, `tuning_data.json`)
* Robust flattening + sanitization pipeline for nested API JSON
* Optional fuzzy address normalization (scourgify + rapidfuzz; safe fallbacks if not installed)
* Enhanced SSH execution framework (Paramiko) with validation, shell mode, per-host logging stubs (option 97)
* Systematic safe-operation test harness (`--test` / `--testinteractive`) with **fail-closed** classification: `OperationRegistry` skips any menu option not explicitly classified `safe`/`interactive_safe` (unregistered options fail closed instead of defaulting to safe), so destructive/interactive/resource-intensive operations — including menu 194 — never auto-run. An exhaustive menu/registry coverage guardrail (`tests/guardrails/test_operation_registry_menu_coverage.py`) fails CI the instant `menu_actions` and the registry diverge.
* Safety preflights before any live systematic run: an isolated-virtual-environment guard blocks automatic dependency install/upgrade into system Python by default (override with `MISTHELPER_ALLOW_SYSTEM_PYTHON_INSTALL=true`), and a secret-safe credential/config preflight exits with a redacted, actionable message when host/token or org id are missing/placeholder. Copy `deploy/.env.example` to the repository-root `.env`, then set `MIST_APITOKEN`/`MIST_API_TOKEN` and `org_id`; systematic modes validate all of them before session or MSP API work begins.
* Container ready (Podman first, Docker compatible) with two build profiles (`Containerfile` simple, `Dockerfile` with HEALTHCHECK + UV logic)
* Defensive logging: `script.log` plus targeted debug gating

---

## Directory & Runtime Layout

| Path | Purpose |
|------|---------|
| `MistHelper.py` | Legacy entrypoint -- actively being decomposed into `src/` modules (see Architecture Evolution below) |
| `src/` | Extracted modules mirroring the Mist API / mistapi hierarchy (db, output, constants, WAN builders) |
| `data/` | SQLite DB (`mist_data.db`), generated CSV outputs, derived artifacts; polyglot backends run in containers |
| `CombinedInventory_ByWeek/` | Time-series weekly inventory snapshots |
| `data/SSH_COMMANDS.CSV` | Fallback SSH command list (legacy root path still supported) |
| `delay_metrics.json` / `tuning_data.json` | Adaptive rate / tuning persistence |
| `data/script.log` | Unified runtime log |
| `Dockerfile` / `Containerfile` | Two container strategies (UV hybrid vs simplified SSL-bypass) |
| `compose.yml` | Orchestrated service definition (uses `Containerfile` by default) |
| `agents.md` | Internal "Agents Guide" (style, safety, refactor guidance) |

All export CSVs are now written inside `data/` (the code enforces a data directory even if a legacy doc claims root CSV placement).

---

## Architecture Evolution

MistHelper started as a single-file script (`MistHelper.py`) and is being incrementally decomposed into a modular `src/` package. The target structure mirrors both the **Mist Cloud API hierarchy** (from the OpenAPI spec) and **Thomas Munzer's mistapi library** (`tmunzer/mistapi_python`), so that MistHelper's internal organization matches the APIs it consumes.

### Current `src/` Layout

```text
src/
├── analytics/              # Site inventory health analysis and zone configuration
├── api/                    # API operation modules (orgs, sites, const)
├── audit/                  # Audit log operations
├── auth/                   # Authentication and session management
├── cache/                  # Caching utilities
├── capture/                # Packet capture workflows and download management
├── db/                     # Database backends (ArangoDB, Redis, retention, routing)
├── device/                 # Device utility operations
├── export/                 # Site data export and insights extraction
├── firmware/               # Firmware management operations
├── gateway/                # Gateway exports, stats, overrides, WAN migration
├── input/                  # Input handling utilities
├── inventory/              # Device inventory summary, MSP orchestration, CSV comparison
├── maps/                   # Maps manager operations
├── marvis/                 # Marvis AI integration
├── network/                # Network configuration operations
├── org_data_collector.py   # Org-level data collection
├── output/                 # Output formatting (writer)
├── reports/                # Report generation
├── site/                   # Site configuration management (test sites, RF, profiles)
├── ssh/                    # SSH runner and execution management
├── ssid_consolidation/     # SSID consolidation operations
├── troubleshooting/        # Marvis troubleshooting workflows
├── ui/                     # Web portal components
├── utils/                  # Shared utility functions
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
| `src/output/` | **Done** | Output writer |
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

## Installation and Setup

### Step 1: Get the Code
```powershell
git clone https://github.com/jmorrison-juniper/MistHelper.git
cd MistHelper
```

### Step 2: Create a Virtual Environment
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

**Option A: Using UV (Faster, Recommended)**
```powershell
python -m pip install uv
uv pip install -r requirements.txt
```

**Option B: Using pip (Standard)**
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Your Environment
```powershell
cp documentation\sample.env .env
```

Edit `.env` with your settings:
- **Required:** Set `MIST_APITOKEN` to your Mist API token
- **Optional but Helpful:** Set `org_id` to skip organization selection
- **Optional:** Configure SSH settings for device commands

To get your API token:
1. Login to https://manage.mist.com
2. Go to Organization > API Tokens
3. Create a new token with appropriate permissions
4. Copy the token to your `.env` file

### Step 5: Test Your Setup
```powershell
python MistHelper.py --help
python MistHelper.py --menu 1
```

---

## How to Run MistHelper

### Interactive Menu Mode (Beginner Friendly)
```powershell
python MistHelper.py
```

### Direct Command Mode (For Automation)
```powershell
# Export organization inventory
python MistHelper.py -M 11

# Export sites information
python MistHelper.py -M 12

# Run gateway synthetic tests (fast mode)
python MistHelper.py -M 16 --fast

# Export data to SQLite database
python MistHelper.py -M 11 --output-format sqlite
```

### Test Mode (Verify Everything Works)
```powershell
python MistHelper.py --test
```

### Common Useful Commands
```powershell
# Get help with all options
python MistHelper.py --help

# Run with detailed logging for troubleshooting
python MistHelper.py -M 11 --debug

# SSH into devices (requires SSH configuration in .env)
python MistHelper.py -M 97

# Fast mode for large organizations
python MistHelper.py -M 16 --fast
```

### Working with Output Files
MistHelper creates organized output in the `data/` directory:
- **CSV files:** Easy to open in Excel or import elsewhere
- **SQLite database:** Use `data/mist_data.db` for complex queries
- **Weekly inventory:** Time-series data in `CombinedInventory_ByWeek/`

---

## Command Line Interface

Primary flags (from argparse block near end of file):

| Flag | Purpose |
|------|---------|
| `-O, --org` | Organization ID |
| `-M, --menu <id>` | Execute a single menu action non-interactively |
| `-S, --site` | Human-readable site name |
| `-D, --device` | Human-readable device name |
| `-P, --port` | Port ID |
| `--output-format {csv,sqlite}` | Select output backend (default csv) |
| `--test` | Run systematic safe-operation test suite |
| `--fast` | Enable fast mode heuristics (threading & reduced retries) |
| `--skip-deps` | Skip dependency auto-install / upgrade phase |
| `--debug` | Enable debug output (includes detailed table data in logs) |
| `--delay <seconds>` | Fixed delay between loop iterations (in seconds) |
| `--address-check` | Enable external address validation using Nominatim API |
| `--skip-ssl-verify` | Skip SSL certificate verification for external API calls |
| `--no-env` | Disable .env file loading for SSH operations |
| `--dry-run` | Preview destructive operations without making changes |
| `--tui` | Launch Terminal User Interface mode for visual API navigation |
| `--login` | Use interactive login (email/password) instead of API token - enables MSP-level API access |
| `--web-portal` | Launch the web portal interface on port 8055 (or WEB_PORT env var) |
| `--testinteractive` | Run systematic test of read-only interactive menu options |

Examples (PowerShell friendly):
```powershell
python .\MistHelper.py -M 11 --output-format sqlite
python .\MistHelper.py -M 13 --output-format sqlite --fast
python .\MistHelper.py --test --output-format sqlite --debug
```

Interactive fallback occurs if no `-M/--menu` is supplied.

---

## Menu Reference

This README is intentionally lean. The full, up-to-date menu reference (each option, description, safety level, and usage examples) is maintained in the repository documentation and the GitHub Wiki:

- Repository copy (authoritative, auto-generated): documentation/menu_reference.md
- GitHub Wiki mirror: https://github.com/jmorrison-juniper/MistHelper/wiki/Menu-Reference

For quick category guidance, see the Wiki Menu Reference page linked above.

- New in this branch: Menu `196` exports org async license-claim status summary and optional per-device detail rows.
- New in this branch: Menu `197` interactively downloads client packet captures grouped by VLAN (site -> client -> VLAN -> `data/packet_captures/<mac>/vlan_<id>/`).
- New in this branch: Menu `198` searches site WAN usage records (`searchSiteWanUsage`) and exports them to `SiteWanUsages_<site>.csv` (CSV/SQLite/ArangoDB via `DataExporter`).
## Security & Safety

| Area | Practice |
|------|---------|
| Credentials | Loaded from `.env`, never logged in cleartext |
| Destructive Ops | Uppercase warnings + explicit invocation required |
| File Output | Filenames sanitized; path traversal blocked in helpers |
| SSH | Paramiko host key auto-add restricted to trusted internal contexts |
| Logging | Secrets & tokens excluded; debug gating prevents noisy stdout |
| Data Integrity | Natural/composite PK strategies avoid silent duplication |

Before extending destructive workflows, replicate existing confirmation pattern and add SECURITY comments as per `agents.md`.

---

## Contributing

1. Fork & branch (`feat/<topic>` or `fix/<issue>`)
2. Add/adjust tests where logic changes (start with validators)
3. Keep commits focused; annotate with tags (`[FEAT]`, `[FIX]`, `[REF]`, `[DOC]`)
4. Update this README if public behavior or filenames change
5. Run `--test` (when feasible) before submitting PR

License: CC-BY-NC-SA-4.0 (Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International)

---

## Roadmap (Short Horizon)

* Structured operation registry + `--list-operations`
* Modular extraction of SSH runner + validators
* Optional JSON log output mode
* Test harness for primary key strategy correctness
* Address verification toggle documented (when externally validated)

---

## Attribution

Built for operational reliability and clarity in large enterprise / NOC contexts. See `agents.md` for internal safety and refactor guidance.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full version history.

---
**MistHelper** -- Practical, transparent data operations for Juniper Mist Cloud.
