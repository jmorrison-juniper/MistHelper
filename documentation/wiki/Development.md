# Development Notes

Recommended incremental refactor targets (mirrors Agents Guide Section 18):

- Extract API domain modules: `api_ops/`, `output/`, `ssh/`
- Add unit tests for validators (hostname, port, command sanitation)
- Migrate SSH command CSV to structured JSON + schema validation
- Introduce optional structured JSON logging mode (feature flag)
- Implement `--list-operations` CLI flag (enumerate menu descriptors machine-readably)

## Coding Style Essentials

- Explicit naming, early validation + early return
- All network calls wrapped with logging context and coarse-grained exception handling
- Restrict broad except clauses; log with context
- No abbreviations: `for device in devices` NOT `for d in devices`
- Class-based architecture: All features organized under semantic class names

## Key Classes

| Class | Purpose |
|-------|---------|
| `GlobalImportManager` | Adaptive dependency and import system with UV/pip fallback |
| `WebSocketManager` | Real-time device command execution |
| `PacketCaptureManager` | Site and org-level packet captures |
| `PacketCaptureDownloadManager` | Poll and download lifecycle for packet capture artifacts |
| `ServicePingManager` | Service ping orchestration and execution flow |
| `FirmwareManager` | AP, switch, and SSR firmware upgrades |
| `EnhancedSSHRunner` | SSH command execution framework |
| `SFPTransceiverDataProcessor` | SFP transceiver data merge operations |
| `DataExporter` | Multi-backend output (CSV/SQLite/ArangoDB/Redis) |
| `OperationRegistry` | Menu safety classification. The single source of truth. |

## Decomposition Wave 2

All 9 phases are complete. The decomposition moved feature-domain packages out
of `MistHelper.py` into `src/`. The entrypoint fell from roughly 28,000 lines to
6,054, and `src/` now holds 123,785 lines across 360 files.

The phase-by-phase table of packages, key classes, and owned menu operations
lives in the repository README, under **Wave 2 Module Ownership**:
<https://github.com/jmorrison-juniper/MistHelper/blob/main/README.md>

This page does not repeat that table. One copy cannot drift from itself.

## Internal Documentation

- **[agents.md](https://github.com/jmorrison-juniper/MistHelper/blob/main/agents.md)**: Internal agent guide with safety patterns, refactor guidance
- **[documentation/](https://github.com/jmorrison-juniper/MistHelper/tree/main/documentation)**: Sample files, API specs, diagrams
- **[documentation/diagrams/](https://github.com/jmorrison-juniper/MistHelper/tree/main/documentation/diagrams)**: 20+ Mermaid diagrams covering architecture, operations, infrastructure
