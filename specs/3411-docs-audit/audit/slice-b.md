Slice B audits the core, infrastructure, and operations diagrams.

| File | Old claim | New claim | Evidence |
| - | - | - | - |
| `documentation/diagrams/README.md` | The suite used T-Mobile theming. | The suite uses a shared dark theme. | `documentation/diagrams/README.md`; `node scripts\mermaid\lint_mermaid.mjs` returned OK. |
| `documentation/diagrams/README.md` | The class hierarchy held 99+ classes in 12 families. | The class hierarchy pages group Python classes by responsibility. | `.venv\Scripts\python.exe` class count returned 1190 classes under `MistHelper.py` and `src/`. |
| `documentation/diagrams/core/architecture-overview.md` | MistHelper had 229 operations. | MistHelper has 270 registered menu entries, with no menu 152. | `src/utils/operation_registry.py`; registry query returned 270 entries and missing `[152]`. |
| `documentation/diagrams/core/architecture-overview.md` | Runtime services were SSH, web, WebSocket, SSH runner, and packet capture. | Runtime services also include the upgrade portal on 8056 and the metrics gateway on 8057. | `compose.yml`; `MistHelper.py`; `src/metrics_gateway/`; `src/upgrade_portal/`. |
| `documentation/diagrams/core/data-persistence-routing.md` | `save_data_to_output()` started the storage path. | `DataExporter.write_with_format_selection()` starts the storage path. | `src/export/data_exporter.py`; `rg save_data_to_output` found only removal tooling and comments. |
| `documentation/diagrams/core/data-persistence-routing.md` | `composite_pk` wrote to Redis TimeSeries. | `composite_pk` writes to ArangoDB plus Redis JSON. `timeseries_pk` writes to Redis TimeSeries. | `src/db/router.py`; `src/db/redis_writer.py`; `src/refactors/endpoint_primary_key_strategies.py`. |
| `documentation/diagrams/core/data-pipeline.md` | `OperationRegistry` dispatched menu selections. | `menu_actions` maps menu numbers to handlers. `OperationRegistry` classifies safety. | `MistHelper.py`; `src/utils/operation_registry.py`. |
| `documentation/diagrams/core/database-strategy.md` | Device stats used `composite_pk`. | Device stats use `timeseries_pk`. | `src/refactors/endpoint_primary_key_strategies.py`. |
| `documentation/diagrams/infrastructure/container-architecture.md` | The container published only SSH and web portal paths. | The default service publishes 2200, 8055, 8056, 8057, and 1161/udp. | `compose.yml`; `Dockerfile`. |
| `documentation/diagrams/infrastructure/container-architecture.md` | The storage diagram omitted RedisInsight and Observium. | The compose stack includes ArangoDB, Redis Stack, RedisInsight, and Observium. | `compose.yml`. |
| `documentation/diagrams/infrastructure/deployment-pipeline.md` | The pipeline diagram showed a small CI set and a timing chart. | The page shows quality gate groups, container build jobs, and release jobs. | `.github/workflows/ci.yml`; `.github/workflows/container-build.yml`; `.github/workflows/release.yml`. |
| `documentation/diagrams/infrastructure/network-protocols.md` | Packet capture used menus 9 and 10. | Packet capture uses menus 134 and 135. | `documentation/menu_reference.md`; `MistHelper.py`. |
| `documentation/diagrams/operations/development-workflow.md` | CI used seven parallel checks. | CI includes lint, types, tests, security, docs, diagrams, and portal gates. | `.github/workflows/ci.yml`. |
| `documentation/diagrams/operations/metrics-and-analytics.md` | The registry had 229 operations and stale category counts. | The registry has 270 entries. Counts are 93, 73, 42, 29, 22, 10, and 1 by category. | Registry query returned those counts from `OperationRegistry.registered_options()`. |
| `documentation/diagrams/operations/operations-reference.md` | The safety diagram pointed to `safe_input()` and `FirmwareManager` in `MistHelper.py`. | The safety diagram points to `InputUtils.safe_input()`, `OperationRegistry`, and `FirmwareManager`. | `src/utils/input_utils.py`; `src/utils/operation_registry.py`; `src/firmware/firmware_manager.py`. |
| `documentation/architecture.md` | The page used stale menu counts, size facts, and package layout. | The page uses 270 menu entries, 8,071 `MistHelper.py` lines, and 621 `src/` Python files. | Size query returned `MistHelper lines 8071`, `src files 621`, and `src lines 223491`. |
| `documentation/network-routing-diagram.md` | The page implied the topology was current. | The page now states that the topology is a reference diagram that the tree does not verify. | No source file in this tree verifies Dallas, Chicago, VLAN, or hardware claims. |

## Open questions

- `.github\skills\ste-writing\SKILL.md` does not exist in this worktree. I used `documentation/ASD-STE100_writing-guide.md`.
- `documentation/menu-api/README.md` does not exist in this worktree, so I added no link to it.
- No source file verifies the site names, VLAN names, or hardware inventory in `documentation/network-routing-diagram.md`.
