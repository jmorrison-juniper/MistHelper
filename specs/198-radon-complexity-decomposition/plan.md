# Implementation Plan: Radon Complexity Decomposition — PR #391 CI Unblock

**Branch**: `feat/391-clone-device-config-to-gateway-template` | **Date**: 2026-06-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/198-radon-complexity-decomposition/spec.md`

## DIRECTIVE OVERRIDE (2026-06-08, applied retroactively)

**NO FAÇADES.** Original files are deleted (callers updated to import from the new
submodule package directly) or restructured into the new primary implementation. Never
produce thin delegation shims, never preserve a legacy class purely for back-compat,
never keep `__init__.py` re-exports that exist solely to satisfy old import paths.
Update callers, tests, and imports in the same commit as the deletion.

This supersedes the "façade pattern: original class delegates to extracted collaborators"
language in the Summary and every "becomes a 2–5-line façade" / "preserve public class
name" line in tasks.md. Already-completed Tier 1 façades were retroactively removed.

## Summary

Decompose every function in `src/` with cyclomatic complexity > 10 down to CC ≤ 10 across three sequential tier waves (Tier 1: CC > 40, Tier 2: CC 25–40, Tier 3: CC 11–24). No complexity suppression markers, no Radon allowlists, no new external dependencies. Refactor via Extract Method / Extract Class / Extract Submodule / Replace Conditional with Dispatch Table / Guard Clauses. Public class names and signatures called from outside `src/` are preserved (façade pattern: original class delegates to extracted collaborators).

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: mistapi 0.59+ (no new deps added by this work)
**Storage**: N/A (refactor only; `ENDPOINT_PRIMARY_KEY_STRATEGIES` untouched per FR-013)
**Testing**: pytest (`tests/guardrails/`, `tests/unit/`, `tests/integration/`), radon CC gate, ruff, black, mypy
**Target Platform**: Windows 11 development; Linux container runtime (Podman)
**Project Type**: Single-project Python CLI/TUI (`src/` package + `MistHelper.py` top-level dispatcher)
**Performance Goals**: No measurable regression; dispatch tables built once at `__init__` (not per-call)
**Constraints**: 5-Item Rule (max 5 children per level, max 5 params per function, max 25 lines per function); inline comments on every executable line; `logging.info` before / `logging.debug` after every meaningful action; ASCII-only logs; `os.path.join` / `pathlib.Path`; preserve all user-facing strings verbatim; `safe_input()` for any new input handling
**Scale/Scope**: ~75 offending functions across ~25 files in `src/`; ~28K LOC total in `MistHelper.py` + `src/`

## Constitution Check

| Principle | Compliance |
|---|---|
| I. Five-Item Rule | PASS — extracted helpers/classes/submodules sized to fit; new submodule dirs each hold ≤ 5 files |
| II. Class-Based Architecture (No Wrappers) | PASS — all extractions become methods on existing classes, new collaborator classes, or new submodule classes; zero standalone wrapper functions |
| III. Safety-First (safe_input) | PASS — no new input prompts introduced; existing `safe_input` call sites preserved verbatim |
| IV. Data path / DB schema | PASS — out of scope; FR-013 forbids changes |
| V. Observability & Logging | PASS — FR-009 requires `logging.info` before / `logging.debug` after every new action |
| VI. Inline Comments (NON-NEGOTIABLE) | PASS — FR-008 requires same-line comments on every new executable line |
| VII. Action Logging (NON-NEGOTIABLE) | PASS — same as V; sampled audit ≥ 95% per SC-009 |

No violations. No entries in Complexity Tracking table below.

## Project Structure

### Documentation (this feature)

```text
specs/198-radon-complexity-decomposition/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0 — decomposition pattern decisions
├── data-model.md        # Phase 1 — collaborator class catalog & responsibilities
├── quickstart.md        # Phase 1 — per-tier execution + validation runbook
├── contracts/
│   └── public-api-contract.md   # Phase 1 — preserved public surface (façade contract)
└── tasks.md             # Phase 2 — generated later by /speckit.tasks
```

### Source Code Delta

New submodule directories are introduced *under* the existing parent packages so the 5-Item Rule holds at every level. Each new directory holds focused single-responsibility collaborators that the original façade class composes and delegates to.

```text
src/
├── websocket/
│   ├── manager.py                          # façade — delegates to polling/ + message_handlers/
│   ├── commands.py                         # façade — delegates to commands/handlers/
│   ├── diag_commands.py                    # façade — delegates to diag/
│   ├── service_ping_discovery.py           # façade — delegates to service_ping/
│   ├── polling/                            # NEW (Tier 1)
│   │   ├── __init__.py
│   │   ├── result_poller.py                # WebSocketResultPoller — drain & buffer WS frames
│   │   ├── completion_detector.py          # CompletionDetector — decide when polling is done
│   │   └── state.py                        # PollState dataclass (explicit state passing)
│   ├── message_handlers/                   # NEW (Tier 1)
│   │   ├── __init__.py
│   │   └── dispatch.py                     # MessageDispatchTable — replaces _on_message if/elif
│   ├── commands/handlers/                  # NEW (Tier 2)
│   │   ├── __init__.py
│   │   └── mac_table_renderer.py           # MacTableRenderer — show_mac_table extraction
│   ├── diag/                               # NEW (Tier 1)
│   │   ├── __init__.py
│   │   ├── arp_executor.py                 # ArpDeviceExecutor — arp_device CC=61
│   │   ├── ping_executor.py                # PingDeviceExecutor — ping_device CC=36
│   │   └── diag_command_dispatch.py        # DiagCommandDispatch — replaces big-class CC=50
│   └── service_ping/                       # NEW (Tier 2/3)
│       ├── __init__.py
│       ├── tenant_category_renderer.py     # TenantCategoryRenderer
│       └── service_category_renderer.py    # ServiceCategoryRenderer
│
├── ui/
│   ├── tui.py                              # façade — delegates to input_handlers/, layout/, execution/, formatting/
│   ├── input_handlers/                     # NEW (Tier 1)
│   │   ├── __init__.py
│   │   ├── keyboard_dispatch.py            # KeyboardDispatchTable — replaces handle_input CC=65
│   │   ├── key_poller.py                   # KeyPoller — check_keyboard_input CC=59 extraction
│   │   └── focus_router.py                 # FocusRouter — route key to active pane
│   ├── layout/                             # NEW (Tier 1)
│   │   ├── __init__.py
│   │   ├── layout_builder.py               # LayoutBuilder — create_layout CC=52 extraction
│   │   ├── pane_factory.py                 # PaneFactory — per-pane construction helpers
│   │   └── results_grid_builder.py         # ResultsGridBuilder — _create_results_grid extraction
│   ├── execution/                          # NEW (Tier 1)
│   │   ├── __init__.py
│   │   ├── item_executor.py                # ItemExecutor — execute_current_item CC=54 extraction
│   │   ├── function_executor.py            # FunctionExecutor — _execute_function CC=36 extraction
│   │   └── parameter_collector.py          # ParameterCollector — _submit_parameter / _start_function_execution
│   └── formatting/                         # NEW (Tier 3)
│       ├── __init__.py
│       └── hierarchical_value_formatter.py # _format_value_hierarchical CC=22
│
├── ssh/
│   ├── ssh_runner.py                       # façade — delegates to shell_execution/, multi_host/, application/, config/
│   ├── ssh_runner_manager.py               # façade — delegates to runner_manager/
│   ├── shell_execution/                    # NEW (Tier 1)
│   │   ├── __init__.py
│   │   ├── shell_session.py                # ShellSession — _execute_with_shell CC=51 extraction
│   │   ├── interactive_loop.py             # InteractiveLoop — _interactive_mode CC=19
│   │   └── connect_strategy.py             # ConnectStrategy — _connect CC=15
│   ├── multi_host/                         # NEW (Tier 1)
│   │   ├── __init__.py
│   │   ├── interactive_orchestrator.py     # InteractiveOrchestrator — _run_multiple_ssh_commands_interactive CC=42
│   │   ├── batch_orchestrator.py           # BatchOrchestrator — _run_multiple_ssh_commands CC=23
│   │   ├── single_host_runner.py           # SingleHostRunner — _run_ssh_command_on_host CC=18 + _run_ssh_command CC=19
│   │   └── multi_host_runner.py            # MultiHostRunner — run_ssh_commands_multi_host CC=20
│   ├── application/                        # NEW (Tier 1)
│   │   ├── __init__.py
│   │   └── application_runner.py           # ApplicationRunner — run_application CC=64
│   ├── config/                             # NEW (Tier 1)
│   │   ├── __init__.py
│   │   ├── env_config_loader.py            # EnvConfigLoader — load_ssh_config_from_env CC=33
│   │   └── csv_command_loader.py           # CsvCommandLoader — load_commands_from_csv CC=16 + _parse_command_list CC=11
│   └── runner_manager/                     # NEW (Tier 2/3)
│       ├── __init__.py
│       ├── interactive_flow.py             # interactive CC=15
│       ├── data_collector.py               # _collect_missing_data CC=17
│       └── gateway_template_selector.py    # _select_gateway_template CC=18
│
├── auth/
│   ├── interactive_session.py              # façade — delegates to session_init/
│   └── session_init/                       # NEW (Tier 1)
│       ├── __init__.py
│       ├── session_initializer.py          # SessionInitializer — initialize_mist_session_interactive CC=40
│       └── msp_org_selector.py             # MspOrgSelector — select_msp_and_org CC=26
│
├── gateway/
│   ├── gateway_override_analyzer.py        # façade — delegates to overrides/
│   ├── gateway_export_utils.py             # in-place method extraction (Tier 3)
│   ├── gateway_stats_exporter.py           # in-place method extraction (Tier 3)
│   ├── wan_probe_device_override_manager.py # in-place method extraction (Tier 3)
│   ├── wan2_migration_manager.py           # in-place method extraction (Tier 3)
│   └── overrides/                          # NEW (Tier 1)
│       ├── __init__.py
│       ├── wan_override_walker.py          # WanOverrideWalker — with_wan_overrides CC=41
│       └── override_classifier.py          # OverrideClassifier — override row categorization
│
├── maps/
│   ├── maps_manager.py                     # façade — delegates to plotly_viewer/
│   └── plotly_viewer/                      # NEW (Tier 2)
│       ├── __init__.py
│       ├── viewer_launcher.py              # ViewerLauncher — _launch_plotly_viewer CC=36
│       ├── ppm_validator.py                # PpmValidator — _validate_ppm CC=13
│       └── vbeacon_figure_builder.py       # VbeaconFigureBuilder — _add_vbeacons_to_figure CC=13
│
├── export/
│   ├── wifi_clients_exporter.py            # façade — delegates to wifi_clients/
│   ├── site_insights_exporter.py           # façade — delegates to site_insights/
│   ├── site_export_utils.py                # in-place method extraction (Tier 3)
│   ├── wifi_clients/                       # NEW (Tier 2)
│   │   ├── __init__.py
│   │   ├── client_fetcher.py               # ClientFetcher
│   │   ├── client_row_builder.py           # ClientRowBuilder
│   │   └── output_writer_selector.py       # OutputWriterSelector
│   └── site_insights/                      # NEW (Tier 2)
│       ├── __init__.py
│       ├── device_insights_collector.py    # device_insights CC=25
│       └── insight_metric_collector.py     # insight_metrics CC=13
│
├── inventory/                              # in-place extraction only (Tier 3) — no submodules
├── troubleshooting/                        # in-place extraction only (Tier 3)
├── analytics/                              # in-place extraction only (Tier 3)
├── site/                                   # in-place extraction only (Tier 3)
├── capture/                                # in-place extraction only (Tier 3)
└── bootstrap/                              # in-place extraction only (Tier 3)

tests/
├── guardrails/   # unchanged — authoritative behavioral contract
├── unit/         # unchanged signatures; any private-helper imports updated to new locations
└── integration/  # unchanged
```

**Structure Decision**: Hybrid — large façade classes (`WebSocketManager`, `MistHelperTUI`, `EnhancedSSHRunner`, `MapsManager`) get **Extract Submodule** to keep their parent files navigable; smaller offenders (single CC 11–24 methods inside otherwise-healthy classes) get **Extract Method** in-place. Every new submodule directory holds ≤ 5 files (5-Item Rule). Every façade class keeps its public method names and signatures (consumer compatibility) and internally instantiates / delegates to extracted collaborators.

## Sub-Plans by Tier

### Tier 1 — Files with CC > 40 (Worst Offenders — Highest Risk)

**Files affected (6)**: `src/websocket/manager.py`, `src/websocket/diag_commands.py`, `src/ui/tui.py`, `src/ssh/ssh_runner.py`, `src/auth/interactive_session.py`, `src/gateway/gateway_override_analyzer.py`

**Functions to refactor**:

| File | Function | CC | Strategy | New Submodule / Class |
|---|---|---|---|---|
| websocket/manager.py | `WebSocketManager.wait_for_command_result` | 110 | Extract Class + State Dataclass | `websocket/polling/result_poller.py::WebSocketResultPoller` + `completion_detector.py::CompletionDetector` + `state.py::PollState` |
| websocket/manager.py | `WebSocketManager._on_message` | 37 | Dispatch Table | `websocket/message_handlers/dispatch.py::MessageDispatchTable` |
| websocket/diag_commands.py | `WebSocketNetworkDiagCommands.arp_device` | 61 | Extract Class | `websocket/diag/arp_executor.py::ArpDeviceExecutor` |
| websocket/diag_commands.py | `WebSocketNetworkDiagCommands.ping_device` | 36 | Extract Class | `websocket/diag/ping_executor.py::PingDeviceExecutor` |
| websocket/diag_commands.py | `WebSocketNetworkDiagCommands` (class CC=50) | 50 | Dispatch Table + Class extraction | `websocket/diag/diag_command_dispatch.py::DiagCommandDispatch` |
| ui/tui.py | `MistHelperTUI.handle_input` | 65 | Dispatch Table (built once in `__init__`) | `ui/input_handlers/keyboard_dispatch.py::KeyboardDispatchTable` |
| ui/tui.py | `MistHelperTUI.check_keyboard_input` | 59 | Extract Class + Guard Clauses | `ui/input_handlers/key_poller.py::KeyPoller` + `focus_router.py::FocusRouter` |
| ui/tui.py | `MistHelperTUI.execute_current_item` | 54 | Extract Class | `ui/execution/item_executor.py::ItemExecutor` |
| ui/tui.py | `MistHelperTUI.create_layout` | 52 | Extract Class + Pane Factory | `ui/layout/layout_builder.py::LayoutBuilder` + `pane_factory.py::PaneFactory` |
| ui/tui.py | `MistHelperTUI._execute_function` | 36 | Extract Class | `ui/execution/function_executor.py::FunctionExecutor` |
| ui/tui.py | `MistHelperTUI.run` | 33 | Extract Method + Guard Clauses | private helpers on `MistHelperTUI` |
| ssh/ssh_runner.py | `EnhancedSSHRunner.run_application` | 64 | Extract Class | `ssh/application/application_runner.py::ApplicationRunner` |
| ssh/ssh_runner.py | `EnhancedSSHRunner._execute_with_shell` | 51 | Extract Class | `ssh/shell_execution/shell_session.py::ShellSession` |
| ssh/ssh_runner.py | `EnhancedSSHRunner._run_multiple_ssh_commands_interactive` | 42 | Extract Class | `ssh/multi_host/interactive_orchestrator.py::InteractiveOrchestrator` |
| ssh/ssh_runner.py | `EnhancedSSHRunner.load_ssh_config_from_env` | 33 | Extract Class + Guard Clauses | `ssh/config/env_config_loader.py::EnvConfigLoader` |
| auth/interactive_session.py | `InteractiveSessionManager.initialize_mist_session_interactive` | 40 | Extract Class | `auth/session_init/session_initializer.py::SessionInitializer` |
| gateway/gateway_override_analyzer.py | `GatewayOverrideAnalyzer.with_wan_overrides` (+ class CC=42) | 41 | Extract Class | `gateway/overrides/wan_override_walker.py::WanOverrideWalker` + `override_classifier.py::OverrideClassifier` |

**Public API preservation (façade pattern)**: Every public method on `WebSocketManager`, `MistHelperTUI`, `EnhancedSSHRunner`, `InteractiveSessionManager`, `WebSocketNetworkDiagCommands`, and `GatewayOverrideAnalyzer` keeps its name and signature. The façade body becomes a 2–5-line delegation: instantiate or look up the collaborator, call its `execute` (or equivalent), return the result. Logging messages and user-facing strings are moved verbatim into the collaborator.

**Risk**: HIGH — these methods sit on critical paths (WebSocket polling for menu 102/154, SSH shell execution for menu 175/176, TUI input handling for every interactive session, MSP/org auth flow for every startup).
**Mitigation**: (1) `tests/guardrails/` runs after every commit; (2) manual smoke matrix before tier push — menu 154 (firmware upgrade dry-run via cancelled `'UPGRADE'` confirmation), menu 102 (WebSocket show mac-table), `--menu 175` SSH runner with one cancelled host, MSP/org login on a multi-org token, TUI launch + arrow-key navigation + Enter; (3) commits are file-scoped so any regression bisects to a single file.

**Validation gate (after Tier 1 push)**:
```powershell
python -m radon cc -n D src\websocket src\ui\tui.py src\ssh\ssh_runner.py src\auth\interactive_session.py src\gateway\gateway_override_analyzer.py   # expect: empty (no D/E/F)
python -m radon cc -n C src\websocket src\ui\tui.py src\ssh\ssh_runner.py src\auth\interactive_session.py src\gateway\gateway_override_analyzer.py   # expect: empty
python -m ruff check .
python -m black --check .
python -m mypy src/
python -m pytest tests/guardrails/ -q
```

---

### Tier 2 — Files with CC 25–40 (Medium Risk)

**Files affected (6)**: `src/maps/maps_manager.py`, `src/export/wifi_clients_exporter.py`, `src/export/site_insights_exporter.py`, `src/auth/interactive_session.py` (remaining), `src/ssh/ssh_runner.py` (remaining), `src/websocket/commands.py`, `src/websocket/service_ping_discovery.py`

**Functions to refactor**:

| File | Function | CC | Strategy | New Submodule / Class |
|---|---|---|---|---|
| maps/maps_manager.py | `MapsManager._launch_plotly_viewer` | 36 | Extract Class | `maps/plotly_viewer/viewer_launcher.py::ViewerLauncher` |
| export/wifi_clients_exporter.py | `WifiClientsExporter.execute` (+ class CC=31) | 30 | Extract Class | `export/wifi_clients/client_fetcher.py` + `client_row_builder.py` + `output_writer_selector.py` |
| export/site_insights_exporter.py | `SiteInsightsExporter.device_insights` | 25 | Extract Class | `export/site_insights/device_insights_collector.py` |
| auth/interactive_session.py | `InteractiveSessionManager.select_msp_and_org` | 26 | Extract Class | `auth/session_init/msp_org_selector.py::MspOrgSelector` |
| ssh/ssh_runner.py | `EnhancedSSHRunner._run_multiple_ssh_commands` | 23 | Extract Class | `ssh/multi_host/batch_orchestrator.py::BatchOrchestrator` |
| ssh/ssh_runner.py | `EnhancedSSHRunner.run_ssh_commands_multi_host` | 20 | Extract Method on collaborator | `ssh/multi_host/multi_host_runner.py::MultiHostRunner` |
| ssh/ssh_runner.py | `EnhancedSSHRunner._run_ssh_command` / `_run_ssh_command_on_host` | 19 / 18 | move into collaborator | `ssh/multi_host/single_host_runner.py::SingleHostRunner` |
| ssh/ssh_runner.py | `EnhancedSSHRunner._interactive_mode` | 19 | move into collaborator | `ssh/shell_execution/interactive_loop.py::InteractiveLoop` |
| websocket/commands.py | `WebSocketCommands.show_mac_table` (+ class CC=29) | 28 | Extract Class | `websocket/commands/handlers/mac_table_renderer.py::MacTableRenderer` |
| websocket/service_ping_discovery.py | `ServicePingDiscoveryMixin._display_tenant_categories` | 33 | Extract Class | `websocket/service_ping/tenant_category_renderer.py::TenantCategoryRenderer` |

**Public API preservation**: `MapsManager`, `WifiClientsExporter`, `SiteInsightsExporter`, `WebSocketCommands`, and the public ssh_runner methods retain names + signatures. Façades delegate.

**Risk**: MEDIUM — `maps_manager._launch_plotly_viewer` (menu 92–96 viewers) and `wifi_clients_exporter.execute` (menu 27–30 exports) are the most user-visible. Auth flow `select_msp_and_org` is exercised on every multi-org login.
**Mitigation**: (1) Capture CSV/SQLite output of a representative export run (e.g., `--menu 27`) before refactor and diff after — must be byte-identical. (2) Manually launch Plotly viewer (menu 93) before and after; verify identical figure render. (3) Auth flow exercised by existing tests.

**Validation gate (after Tier 2 push)**:
```powershell
python -m radon cc -n D src\   # expect: empty (no D/E/F org-wide)
python -m ruff check .
python -m black --check .
python -m mypy src/
python -m pytest tests/guardrails/ tests/unit/ -q
```

---

### Tier 3 — Files with CC 11–24 (Lowest Risk, Largest Count)

**Files affected (~15)**: `src/analytics/site_inventory_health_analyzer.py`, `src/bootstrap/uv_runtime.py`, `src/capture/multi_ap_scan_workflow.py`, `src/export/site_export_utils.py`, `src/export/site_insights_exporter.py` (remaining), `src/gateway/gateway_export_utils.py`, `src/gateway/gateway_stats_exporter.py`, `src/gateway/wan2_migration_manager.py`, `src/gateway/wan_probe_device_override_manager.py`, `src/inventory/org_device_inventory_msp.py`, `src/inventory/org_device_inventory_summary.py`, `src/maps/maps_manager.py` (remaining: `_validate_ppm`, `_add_vbeacons_to_figure`, `download_site_map_images`), `src/site/site_config_manager.py`, `src/ssh/ssh_runner_manager.py`, `src/ssh/ssh_runner.py` (remaining: `load_commands_from_csv`, `_connect`, `_parse_command_list`), `src/troubleshooting/interactive_test_runner.py`, `src/troubleshooting/marvis_troubleshoot_utils.py`, `src/ui/tui.py` (remaining smaller methods), `src/websocket/service_ping_discovery.py` (remaining)

**Strategy**: Predominantly **Extract Method** in-place (private `_verb_noun` helpers on the same class) + **Guard Clauses** to flatten nested conditionals. A handful of cohesive 2–3-method clusters (`maps/plotly_viewer/ppm_validator.py`, `maps/plotly_viewer/vbeacon_figure_builder.py`, `ui/formatting/hierarchical_value_formatter.py`, `ssh/runner_manager/*`, `ssh/config/csv_command_loader.py`, `ssh/shell_execution/connect_strategy.py`, `websocket/service_ping/service_category_renderer.py`) move into submodules already created in Tier 1 / Tier 2 — no *new* directories are introduced in Tier 3.

**Representative function list (sample, not exhaustive)**:

| File | Function | CC | Strategy |
|---|---|---|---|
| analytics/site_inventory_health_analyzer.py | `_find_sites_with_offline_infrastructure` | 13 | Extract Method + Guard Clauses |
| analytics/site_inventory_health_analyzer.py | `_display_results` | 12 | Extract Method (per-section renderers) |
| analytics/site_inventory_health_analyzer.py | `_fetch_devices` | 11 | Extract Method |
| analytics/site_inventory_health_analyzer.py | `_group_devices_by_site` | 11 | Extract Method (dict-building helper) |
| bootstrap/uv_runtime.py | `UVRuntimeHelper.version_satisfies` | 12 | Replace Conditional with helper per operator |
| capture/multi_ap_scan_workflow.py | `MultiApScanCaptureWorkflow.run` | 17 | Extract Method (phase helpers) |
| export/site_export_utils.py | `SiteExportUtils._export_data` | 14 | Extract Method (per output backend) |
| export/site_insights_exporter.py | `insight_metrics` | 13 | Extract Method |
| gateway/gateway_export_utils.py | `management_ips` | 13 | Extract Method (row builder) |
| gateway/gateway_export_utils.py | `device_configs` | 11 | Extract Method |
| gateway/gateway_stats_exporter.py | `device_stats` | 16 | Extract Method (per-stat-group renderer) |
| gateway/wan2_migration_manager.py | `_print_site_variable_summary` | 13 | Extract Method (per-section printer) |
| gateway/wan_probe_device_override_manager.py | `_find_devices_with_overrides` | 19 | Extract Method + Guard Clauses |
| gateway/wan_probe_device_override_manager.py | `_generate_report` | 14 | Extract Method |
| gateway/wan_probe_device_override_manager.py | `_update_single_device` | 12 | Extract Method |
| inventory/org_device_inventory_msp.py | `_display_combined_pivot_and_export` | 13 | Extract Method |
| inventory/org_device_inventory_summary.py | `_fetch_versions_per_model` | 24 | Extract Method (per-device-type fetcher) |
| inventory/org_device_inventory_summary.py | `_display_pivot_and_export` | 12 | Extract Method |
| maps/maps_manager.py | `_validate_ppm` | 13 | move into `maps/plotly_viewer/ppm_validator.py` |
| maps/maps_manager.py | `_add_vbeacons_to_figure` | 13 | move into `maps/plotly_viewer/vbeacon_figure_builder.py` |
| maps/maps_manager.py | `download_site_map_images` | 11 | Extract Method |
| site/site_config_manager.py | `_analyze_sites_for_rf_templates` | 12 | Extract Method |
| ssh/ssh_runner_manager.py | `interactive` | 15 | move into `ssh/runner_manager/interactive_flow.py` |
| ssh/ssh_runner_manager.py | `_collect_missing_data` | 17 | move into `ssh/runner_manager/data_collector.py` |
| ssh/ssh_runner_manager.py | `_select_gateway_template` | 18 | move into `ssh/runner_manager/gateway_template_selector.py` |
| ssh/ssh_runner.py | `load_commands_from_csv` | 16 | move into `ssh/config/csv_command_loader.py` |
| ssh/ssh_runner.py | `_connect` | 15 | move into `ssh/shell_execution/connect_strategy.py` |
| ssh/ssh_runner.py | `_parse_command_list` | 11 | move into `ssh/config/csv_command_loader.py` |
| troubleshooting/interactive_test_runner.py | `execute` (+ class CC=15) | 18 | Extract Method (per-test-phase) |
| troubleshooting/marvis_troubleshoot_utils.py | `network_connectivity` | 23 | Extract Method |
| troubleshooting/marvis_troubleshoot_utils.py | `device_performance` | 18 | Extract Method |
| troubleshooting/marvis_troubleshoot_utils.py | `client_connectivity` | 13 | Extract Method |
| ui/tui.py | `_discover_current_level` | 26 | Extract Method |
| ui/tui.py | `_format_value_hierarchical` | 22 | move into `ui/formatting/hierarchical_value_formatter.py` |
| ui/tui.py | `_start_function_execution` | 15 | move into `ui/execution/parameter_collector.py` |
| ui/tui.py | `_submit_parameter` | 14 | move into `ui/execution/parameter_collector.py` |
| ui/tui.py | `_create_results_grid` | 14 | move into `ui/layout/results_grid_builder.py` |
| ui/tui.py | `_should_show_results_grid` | 13 | Extract Method + Guard Clauses |
| ui/tui.py | `_load_dotenv_only` | 12 | Extract Method |
| websocket/service_ping_discovery.py | `_display_service_categories` | 15 | move into `websocket/service_ping/service_category_renderer.py` |
| websocket/service_ping_discovery.py | `_extract_from_device_config` | 14 | Extract Method |

**Public API preservation**: All affected classes keep their public method names + signatures. Tier 3 extractions are mostly in-place private helpers, so consumer code does not change.

**Risk**: LOW — these are predominantly export / inventory / display / formatter methods. Worst case is a CSV column-order or a printed-line ordering regression, both caught by guardrail tests and easy to spot in diffs.
**Mitigation**: Spot-check one CSV export (e.g., `--menu 27`) and one printed report (`--menu 19`) byte-identically before and after Tier 3 push.

**Validation gate (after Tier 3 push — FINAL)**:
```powershell
python -m radon cc src\ -n C                                # expect: NO OUTPUT
python -m radon cc src\ -j | python -c "import sys, json; data = json.loads(sys.stdin.read()); offenders = [(f, b['name'], b['complexity']) for f, blocks in data.items() for b in blocks if b['complexity'] > 10]; print('All functions within complexity threshold.' if not offenders else offenders); sys.exit(0 if not offenders else 1)"
python -m ruff check .
python -m black --check .
python -m mypy src/ --config-file pyproject.toml
python -m pytest tests/guardrails/ tests/unit/ tests/integration/ -q
python -m pytest --cov=src --cov-report=term-missing tests/    # expect: coverage >= 80%
```

---

## Commit Strategy

- **Granularity**: One commit per **file refactored** (not per function). A single commit contains all extractions, new collaborator files, and façade updates for one offender file, plus any test-import updates.
- **Commit message format**: `refactor(<module>): decompose <Class>.<method> CC=<N> -> <=10`
  - When a commit decomposes multiple methods on the same class/file: `refactor(<module>): decompose <Class> hotspots (handle_input CC=65, check_keyboard_input CC=59, execute_current_item CC=54) -> <=10`
  - Body lists every extracted class/submodule and confirms façade preservation.
- **Push cadence**: Push after each tier wave completes locally and all validation gates pass for that tier's file set. Three pushes total (one per tier).
- **PR shape**: Preferred — three sequential PRs against `main` (P1, P2, P3 from spec), each rebased on the prior merge. Acceptable fallback — single PR if Tier 1 + 2 + 3 combined diff stays reviewable.

## Out of Scope (Explicit Exclusions)

- `MistHelper.py` top-level dispatcher (FR-012). Not refactored.
- Database schemas and `ENDPOINT_PRIMARY_KEY_STRATEGIES` (FR-013). Not modified.
- Public class names and signatures called from outside `src/` (FR-006). Preserved verbatim.
- CLI flags and menu numbers (FR-013). Not changed.
- `data/`, `.env`, container images, SSH runner credentials. Not touched.
- New external dependencies (FR-011). None added.
- Complexity suppression markers (FR-002). Strictly forbidden.

## Phase 0: Outline & Research

See [research.md](research.md). Resolves: which decomposition pattern fits each Tier 1 hotspot, dataclass-vs-tuple for shared state, mypy compatibility of dispatch tables, safe handling of nested loop / threading state in `wait_for_command_result`.

## Phase 1: Design & Contracts

- [data-model.md](data-model.md) — catalog of every new collaborator class with single-responsibility description, public method list, internal state.
- [contracts/public-api-contract.md](contracts/public-api-contract.md) — full enumeration of public symbols preserved across the refactor.
- [quickstart.md](quickstart.md) — operator runbook: per-tier loop (refactor file -> run gates -> commit -> repeat -> push tier).
- Agent context updated: plan reference inside `<!-- SPECKIT START / END -->` markers in `.github/copilot-instructions.md` now points to this plan.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| *(none)* | — | — |

No constitutional gate violations — refactor strictly follows the Five-Item Rule, Class-Based Architecture, and the NON-NEGOTIABLE Inline Comments + Action Logging principles.
