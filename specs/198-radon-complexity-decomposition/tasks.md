# Tasks: Radon Cyclomatic Complexity Decomposition — PR #391 CI Unblock

**Feature**: `specs/198-radon-complexity-decomposition/`
**Branch**: `feat/391-clone-device-config-to-gateway-template`
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Global Constraints (Apply to EVERY Task)

These constraints are **NON-NEGOTIABLE** for every task below. Repeated here so they cannot be
missed:

1. **NO exemptions**: zero `# noqa: C901`, zero `# pylint: disable=...` for complexity rules,
   zero new Radon allowlist or `pyproject.toml` suppression entries (FR-002).
2. **Inline per-line comments on all NEW code**: every executable line of every new helper,
   class, or submodule carries a same-line comment explaining *why* (FR-008).
3. **Action logging on all new helper methods**: `logging.info("...")` before every meaningful
   action, `logging.debug("...")` after with a result summary; ASCII-only (FR-009).
4. **Public API preservation (façade pattern)**: original class names + public method names +
   public signatures unchanged; façade body becomes 2–5-line delegation to the extracted
   collaborator. Consumer code in `MistHelper.py`, `tests/`, `web_portal/` does not change
   (FR-006).
5. **Preserve user-facing strings verbatim**: prompts, log messages, error messages, menu
   labels move into helpers byte-identically (FR-010).
6. **All extracted helpers MUST themselves have CC ≤ 10** (FR-005). Verify per-file with
   `python -m radon cc -n C <file>` after each task — empty output is required.
7. **5-Item Rule**: each new submodule directory holds ≤ 5 files; each new function takes ≤ 5
   parameters and is ≤ 25 lines (constitution principle I).
8. **No new dependencies** (FR-011); no `MistHelper.py` edits (FR-012); no schema /
   `ENDPOINT_PRIMARY_KEY_STRATEGIES` / CLI flag / menu number edits (FR-013).
9. **Commit message format**: `refactor(<module>): decompose <Class>.<method> CC=<old> -> <=10`
   (multi-method file: `refactor(<module>): decompose <Class> hotspots (m1 CC=N, m2 CC=N) -> <=10`).
10. **One commit per file** (a task = a commit). Body lists every extracted class/submodule and
    confirms façade preservation.

## Per-Task Local Validation (Run After Every Task)

```powershell
python -m radon cc -n C <path/to/file.py>             # MUST be empty
python -m radon cc -n D <path/to/file.py>             # MUST be empty
python -m ruff check <path/to/file.py> <new/submodule/>
python -m black --check <path/to/file.py> <new/submodule/>
python -m mypy src/ --config-file pyproject.toml
python -m pytest tests/guardrails/ -q
```

---

## Phase 1: Setup

- [ ] T001 Confirm working branch is `feat/391-clone-device-config-to-gateway-template` and
      clean: `git status` shows no uncommitted changes; `.venv` is active; baseline gate
      snapshot captured with `python -m radon cc src\ -j > data\radon-baseline.json` (kept
      local, not committed).

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T002 Verify the local gate tooling versions: `python -m radon --version`,
      `python -m ruff --version`, `python -m black --version`, `python -m mypy --version`,
      `python -m pytest --version`. Confirm all five tools are installed in `.venv`. If any
      missing: `pip install -r requirements.txt`. No code changes.

- [ ] T003 Capture pre-refactor smoke-matrix baseline outputs for spot-validation later
      (SC-007). Save under `data\smoke-baseline\` (gitignored): one CSV from `--menu 27`
      (WiFi clients export), one printed report capture from `--menu 19` (gateway test
      results), and a screenshot of TUI initial render after launch. No code changes.

---

## Phase 3: User Story 1 — Tier 1 (CC > 40) — Worst Offenders (P1)

**Story goal**: Decompose the six Tier 1 files so every function in them has CC ≤ 10. This
alone removes the majority of the Radon gate failure surface.

**Independent test**: `python -m radon cc src\websocket src\ui\tui.py src\ssh\ssh_runner.py
src\auth\interactive_session.py src\gateway\gateway_override_analyzer.py -n C` returns no
output, and `pytest tests/guardrails/ tests/unit/websocket/ tests/unit/ssh/ tests/unit/ui/ -q`
passes.

### Tier 1 Refactor Tasks (one per file)

- [ ] T010 [P] [US1] Decompose `src/websocket/manager.py` (functions: `wait_for_command_result`
      CC=110, `_on_message` CC=37). Create new submodule `src/websocket/polling/` with
      `__init__.py`, `result_poller.py` (`WebSocketResultPoller` — drain & buffer WS frames),
      `completion_detector.py` (`CompletionDetector` — decide when polling is done), `state.py`
      (`PollState` dataclass for explicit state passing). Create new submodule
      `src/websocket/message_handlers/` with `__init__.py` and `dispatch.py`
      (`MessageDispatchTable` — `{message_type: handler}` dict built once in `__init__`,
      replaces `_on_message` if/elif chain). `WebSocketManager.wait_for_command_result` becomes
      a 2–5-line façade: instantiate `WebSocketResultPoller` and `CompletionDetector`, loop
      until detector signals done, return buffered result. `WebSocketManager._on_message`
      becomes a 2-line façade that looks up the handler via `MessageDispatchTable` and calls
      it. Preserve all public methods on `WebSocketManager` verbatim. Local validation per
      template above + `pytest tests/unit/websocket/ -q`. Commit:
      `refactor(websocket): decompose WebSocketManager hotspots (wait_for_command_result CC=110, _on_message CC=37) -> <=10`.

- [ ] T011 [P] [US1] Decompose `src/websocket/diag_commands.py` (functions: `arp_device`
      CC=61, `ping_device` CC=36, class `WebSocketNetworkDiagCommands` CC=50). Create new
      submodule `src/websocket/diag/` with `__init__.py`, `arp_executor.py`
      (`ArpDeviceExecutor.execute(...)` — full arp logic), `ping_executor.py`
      (`PingDeviceExecutor.execute(...)` — full ping logic), `diag_command_dispatch.py`
      (`DiagCommandDispatch` — `{command_name: executor}` dict built once in `__init__` of
      `WebSocketNetworkDiagCommands`, replaces the long branching that drives class-level
      CC=50). `WebSocketNetworkDiagCommands.arp_device` and `.ping_device` become 2–5-line
      façades that instantiate the executor and call `.execute(...)`. Other diag commands on
      the class refactored similarly so the class itself drops to CC ≤ 10. Preserve public
      method names + signatures. Local validation per template + `pytest tests/unit/websocket/
      -q`. Commit: `refactor(websocket): decompose WebSocketNetworkDiagCommands hotspots
      (arp_device CC=61, ping_device CC=36, class CC=50) -> <=10`.

- [ ] T012 [P] [US1] Decompose `src/ui/tui.py` Tier 1 hotspots (functions: `handle_input`
      CC=65, `check_keyboard_input` CC=59, `execute_current_item` CC=54, `create_layout`
      CC=52, `_execute_function` CC=36, `run` CC=33). Create new submodules under `src/ui/`:
      `input_handlers/` (`__init__.py`, `keyboard_dispatch.py::KeyboardDispatchTable` —
      `{key: bound_method}` dict built once in `MistHelperTUI.__init__`, replaces
      `handle_input` if/elif; `key_poller.py::KeyPoller` — poll/read key extraction from
      `check_keyboard_input`; `focus_router.py::FocusRouter` — route key to active pane);
      `layout/` (`__init__.py`, `layout_builder.py::LayoutBuilder` — `create_layout`
      extraction; `pane_factory.py::PaneFactory` — per-pane construction helpers;
      `results_grid_builder.py::ResultsGridBuilder` — `_create_results_grid` extraction, used
      here in T012 because `create_layout` calls it); `execution/` (`__init__.py`,
      `item_executor.py::ItemExecutor` — `execute_current_item` extraction;
      `function_executor.py::FunctionExecutor` — `_execute_function` extraction;
      `parameter_collector.py::ParameterCollector` — stub for Tier 3 to fill in). Each
      `MistHelperTUI.handle_input`, `.check_keyboard_input`, `.execute_current_item`,
      `.create_layout`, `._execute_function`, `.run` becomes a 2–5-line façade. Dispatch
      tables built once at `__init__` time (no per-call rebuild — performance constraint).
      Preserve public class name `MistHelperTUI` and all public method names + signatures.
      Local validation per template + manual: launch TUI, navigate arrow keys, Enter to
      execute a safe menu item, Esc to back out. Commit: `refactor(ui): decompose
      MistHelperTUI Tier-1 hotspots (handle_input CC=65, check_keyboard_input CC=59,
      execute_current_item CC=54, create_layout CC=52, _execute_function CC=36, run CC=33)
      -> <=10`.

- [ ] T013 [P] [US1] Decompose `src/ssh/ssh_runner.py` Tier 1 hotspots (functions:
      `run_application` CC=64, `_execute_with_shell` CC=51,
      `_run_multiple_ssh_commands_interactive` CC=42, `load_ssh_config_from_env` CC=33).
      Create new submodules under `src/ssh/`: `application/` (`__init__.py`,
      `application_runner.py::ApplicationRunner.execute(...)` — full `run_application` logic);
      `shell_execution/` (`__init__.py`, `shell_session.py::ShellSession.execute(...)` —
      `_execute_with_shell` extraction; `interactive_loop.py::InteractiveLoop` — stub for
      Tier 2 to fill in; `connect_strategy.py::ConnectStrategy` — stub for Tier 3 to fill
      in); `multi_host/` (`__init__.py`,
      `interactive_orchestrator.py::InteractiveOrchestrator.execute(...)` —
      `_run_multiple_ssh_commands_interactive` extraction;
      `batch_orchestrator.py::BatchOrchestrator` — stub for Tier 2;
      `single_host_runner.py::SingleHostRunner` — stub for Tier 2;
      `multi_host_runner.py::MultiHostRunner` — stub for Tier 2); `config/` (`__init__.py`,
      `env_config_loader.py::EnvConfigLoader.load()` — `load_ssh_config_from_env` extraction
      with guard clauses; `csv_command_loader.py::CsvCommandLoader` — stub for Tier 3).
      `EnhancedSSHRunner.run_application`, `._execute_with_shell`,
      `._run_multiple_ssh_commands_interactive`, `.load_ssh_config_from_env` become
      2–5-line façades. Preserve public class name `EnhancedSSHRunner` and all public method
      names + signatures. Local validation per template + manual: `--menu 175` with one
      cancelled host. Commit: `refactor(ssh): decompose EnhancedSSHRunner Tier-1 hotspots
      (run_application CC=64, _execute_with_shell CC=51, _run_multiple_ssh_commands_interactive
      CC=42, load_ssh_config_from_env CC=33) -> <=10`.

- [X] T014 [P] [US1] Decompose `src/auth/interactive_session.py` Tier 1 hotspot (function:
      `initialize_mist_session_interactive` CC=40). Create new submodule
      `src/auth/session_init/` with `__init__.py`,
      `session_initializer.py::SessionInitializer.initialize()` (full Tier 1 extraction —
      env-var probe, token validation, prompt loops, fallbacks), and
      `msp_org_selector.py::MspOrgSelector` (stub class for Tier 2 to fill in).
      `InteractiveSessionManager.initialize_mist_session_interactive` becomes a 2–5-line
      façade. All `safe_input()` call sites moved verbatim into helpers. Preserve public class
      name `InteractiveSessionManager` and all public method names + signatures. Local
      validation per template + manual: relaunch MistHelper, exercise multi-org login. Commit:
      `refactor(auth): decompose InteractiveSessionManager.initialize_mist_session_interactive
      CC=40 -> <=10`.

- [X] T015 [P] [US1] Decompose `src/gateway/gateway_override_analyzer.py` (function:
      `with_wan_overrides` CC=41, class `GatewayOverrideAnalyzer` CC=42). Create new
      submodule `src/gateway/overrides/` with `__init__.py`,
      `wan_override_walker.py::WanOverrideWalker.walk(...)` (full `with_wan_overrides`
      logic), `override_classifier.py::OverrideClassifier.classify(row)` (per-row
      categorization extracted from the same method).
      `GatewayOverrideAnalyzer.with_wan_overrides` becomes a 2–5-line façade. Any other
      branching on the class that contributes to class-level CC=42 also extracted into
      `OverrideClassifier` or a private helper so class CC drops to ≤ 10. Preserve public
      class + method names. Local validation per template + manual: `--menu` for the override
      analyzer report. Commit: `refactor(gateway): decompose GatewayOverrideAnalyzer
      (with_wan_overrides CC=41, class CC=42) -> <=10`.

### Tier 1 Validation Gate

- [ ] T016 [US1] Tier 1 validation gate — run **all** of the following and confirm green
      before any Tier 2 task starts:
      ```powershell
      python -m radon cc -n D src\websocket src\ui\tui.py src\ssh\ssh_runner.py src\auth\interactive_session.py src\gateway\gateway_override_analyzer.py
      python -m radon cc -n C src\websocket src\ui\tui.py src\ssh\ssh_runner.py src\auth\interactive_session.py src\gateway\gateway_override_analyzer.py
      python -m ruff check .
      python -m black --check .
      python -m mypy src/ --config-file pyproject.toml
      python -m pytest tests/guardrails/ tests/unit/ -q
      ```
      First two commands MUST produce empty output. Remaining commands MUST exit 0. If any
      failure: fix in-place on the relevant Tier 1 file's commit branch BEFORE pushing.
      Push the Tier 1 commits: `git push origin feat/391-clone-device-config-to-gateway-template`.

**Checkpoint**: Tier 1 must be fully complete and pushed before Tier 2 starts. Tasks T011, T013,
T014 each touch files that Tier 2 and Tier 3 also touch — file-level serialization is enforced
across tiers.

---

## Phase 4: User Story 2 — Tier 2 (CC 25–40) — Medium Risk (P2)

**Story goal**: Decompose the Tier 2 files so every remaining CC 25–40 function drops to CC ≤
10. After this phase, `radon cc src\ -n D` produces no output org-wide.

**Independent test**: `python -m radon cc src\ -n D` returns no output, and `pytest
tests/guardrails/ tests/unit/ tests/integration/ -q` passes.

### Tier 2 Refactor Tasks

- [ ] T020 [P] [US2] Decompose `src/maps/maps_manager.py` Tier 2 portion (function:
      `_launch_plotly_viewer` CC=36). Create new submodule `src/maps/plotly_viewer/` with
      `__init__.py`, `viewer_launcher.py::ViewerLauncher.launch(...)` (full
      `_launch_plotly_viewer` extraction including Dash 3.x `app.run(...)` call with
      `use_reloader=False`), and stub files `ppm_validator.py::PpmValidator` and
      `vbeacon_figure_builder.py::VbeaconFigureBuilder` for Tier 3 to fill in.
      `MapsManager._launch_plotly_viewer` becomes a 2–5-line façade. Preserve public class +
      method names. Local validation per template + manual: launch menu 93 Plotly viewer,
      confirm identical render. Commit: `refactor(maps): decompose
      MapsManager._launch_plotly_viewer CC=36 -> <=10`.

- [ ] T021 [P] [US2] Decompose `src/export/wifi_clients_exporter.py` (function: `execute`
      CC=30, class `WifiClientsExporter` CC=31). Create new submodule
      `src/export/wifi_clients/` with `__init__.py`, `client_fetcher.py::ClientFetcher.fetch(...)`
      (API pull + pagination), `client_row_builder.py::ClientRowBuilder.build(client)` (single
      row flatten), `output_writer_selector.py::OutputWriterSelector.select(format)` (route to
      CSV / SQLite / ArangoDB writer). `WifiClientsExporter.execute` becomes a 2–5-line façade
      that composes the three collaborators. Preserve `api_function_name='searchOrgWirelessClients'`
      passthrough to `DataExporter.write_with_format_selection`. Preserve public class + method
      names. Local validation per template + byte-diff of `--menu 27` CSV output against
      `data\smoke-baseline\` capture. Commit: `refactor(export): decompose WifiClientsExporter
      (execute CC=30, class CC=31) -> <=10`.

- [ ] T022 [P] [US2] Decompose `src/export/site_insights_exporter.py` Tier 2 portion
      (function: `device_insights` CC=25). Create new submodule `src/export/site_insights/`
      with `__init__.py`, `device_insights_collector.py::DeviceInsightsCollector.collect(...)`
      (full `device_insights` extraction), and stub
      `insight_metric_collector.py::InsightMetricCollector` for Tier 3.
      `SiteInsightsExporter.device_insights` becomes a 2–5-line façade. Preserve public class +
      method names + the `api_function_name` passthrough. Local validation per template.
      Commit: `refactor(export): decompose SiteInsightsExporter.device_insights CC=25 -> <=10`.

- [ ] T023 [US2] Decompose `src/auth/interactive_session.py` Tier 2 portion (function:
      `select_msp_and_org` CC=26). Fill in the `MspOrgSelector` stub created in T014:
      implement `MspOrgSelector.select(...)` in `src/auth/session_init/msp_org_selector.py`
      with the full `select_msp_and_org` logic. `InteractiveSessionManager.select_msp_and_org`
      becomes a 2–5-line façade. Preserve public method name + signature; preserve all prompts
      verbatim. Local validation per template + manual: multi-org login. Commit:
      `refactor(auth): decompose InteractiveSessionManager.select_msp_and_org CC=26 -> <=10`.
      **Sequential after T014** (same file).

- [ ] T024 [US2] Decompose `src/ssh/ssh_runner.py` Tier 2 portion (functions:
      `_run_multiple_ssh_commands` CC=23, `run_ssh_commands_multi_host` CC=20,
      `_run_ssh_command` CC=19, `_run_ssh_command_on_host` CC=18, `_interactive_mode` CC=19).
      Fill in stubs created in T013: `BatchOrchestrator.execute(...)` in
      `src/ssh/multi_host/batch_orchestrator.py` (full `_run_multiple_ssh_commands` logic);
      `MultiHostRunner.run(...)` in `src/ssh/multi_host/multi_host_runner.py` (full
      `run_ssh_commands_multi_host` logic); `SingleHostRunner.run(...)` and `.run_on_host(...)`
      in `src/ssh/multi_host/single_host_runner.py` (full `_run_ssh_command` and
      `_run_ssh_command_on_host` logic); `InteractiveLoop.run(...)` in
      `src/ssh/shell_execution/interactive_loop.py` (full `_interactive_mode` logic). Each
      `EnhancedSSHRunner` method becomes a 2–5-line façade. Preserve all public method names +
      signatures. Local validation per template + manual: `--menu 175` multi-host run, `--menu
      176` interactive runner. Commit: `refactor(ssh): decompose EnhancedSSHRunner Tier-2
      hotspots (_run_multiple_ssh_commands CC=23, run_ssh_commands_multi_host CC=20,
      _run_ssh_command CC=19, _run_ssh_command_on_host CC=18, _interactive_mode CC=19) -> <=10`.
      **Sequential after T013** (same file).

- [ ] T025 [P] [US2] Decompose `src/websocket/commands.py` (function: `show_mac_table` CC=28,
      class `WebSocketCommands` CC=29). Create new submodule `src/websocket/commands/handlers/`
      with `__init__.py` and `mac_table_renderer.py::MacTableRenderer.render(...)` (full
      `show_mac_table` extraction). Refactor other `WebSocketCommands` methods contributing to
      class-level CC=29 into private helpers or additional handler classes so class drops to
      ≤ 10. `WebSocketCommands.show_mac_table` becomes a 2–5-line façade. Preserve public class
      + method names. Local validation per template + manual: `--menu 102` show mac-table
      command. Commit: `refactor(websocket): decompose WebSocketCommands (show_mac_table CC=28,
      class CC=29) -> <=10`.

- [ ] T026 [P] [US2] Decompose `src/websocket/service_ping_discovery.py` Tier 2 portion
      (function: `_display_tenant_categories` CC=33). Create new submodule
      `src/websocket/service_ping/` with `__init__.py`,
      `tenant_category_renderer.py::TenantCategoryRenderer.render(...)` (full extraction), and
      stub `service_category_renderer.py::ServiceCategoryRenderer` for Tier 3.
      `ServicePingDiscoveryMixin._display_tenant_categories` becomes a 2–5-line façade.
      Preserve public class + method names. Local validation per template. Commit:
      `refactor(websocket): decompose ServicePingDiscoveryMixin._display_tenant_categories
      CC=33 -> <=10`.

### Tier 2 Validation Gate

- [ ] T027 [US2] Tier 2 validation gate — run **all** of the following:
      ```powershell
      python -m radon cc -n D src\
      python -m ruff check .
      python -m black --check .
      python -m mypy src/ --config-file pyproject.toml
      python -m pytest tests/guardrails/ tests/unit/ tests/integration/ -q
      ```
      `radon cc -n D` MUST produce empty output (no D/E/F functions anywhere in `src\`).
      Push the Tier 2 commits: `git push origin feat/391-clone-device-config-to-gateway-template`.

**Checkpoint**: Tier 2 complete and pushed before Tier 3 starts.

---

## Phase 5: User Story 3 — Tier 3 (CC 11–24) — Long Tail (P3)

**Story goal**: Decompose every remaining CC 11–24 function so `radon cc src\ -n C` produces
no output and PR #391 CI gate turns green.

**Independent test**: `python -m radon cc src\ -n C` returns no output and
`python -m radon cc src\ -j | python -c "import sys,json; d=json.loads(sys.stdin.read()); off=[(f,b['name'],b['complexity']) for f,bs in d.items() for b in bs if b['complexity']>10]; print('OK' if not off else off); sys.exit(0 if not off else 1)"` exits 0.

### Tier 3 Refactor Tasks

- [ ] T030 [P] [US3] Decompose `src/analytics/site_inventory_health_analyzer.py` (functions:
      `_find_sites_with_offline_infrastructure` CC=13, `_display_results` CC=12,
      `_fetch_devices` CC=11, `_group_devices_by_site` CC=11). In-place Extract Method +
      Guard Clauses on the same class; per-section render helpers for `_display_results`. No
      new submodule. Local validation per template. Commit: `refactor(analytics): decompose
      SiteInventoryHealthAnalyzer hotspots (4 methods CC 11-13) -> <=10`.

- [ ] T031 [P] [US3] Decompose `src/bootstrap/uv_runtime.py` (function:
      `UVRuntimeHelper.version_satisfies` CC=12). Replace Conditional with per-operator helper
      methods or a `{operator: comparator}` dispatch dict built once. No new submodule. Local
      validation per template. Commit: `refactor(bootstrap): decompose
      UVRuntimeHelper.version_satisfies CC=12 -> <=10`.

- [ ] T032 [P] [US3] Decompose `src/capture/multi_ap_scan_workflow.py` (function: `run`
      CC=17). Extract per-phase private helpers on `MultiApScanCaptureWorkflow` (phase 1:
      site/AP selection; phase 2: capture orchestration; phase 3: result aggregation). No new
      submodule. Local validation per template. Commit: `refactor(capture): decompose
      MultiApScanCaptureWorkflow.run CC=17 -> <=10`.

- [ ] T033 [P] [US3] Decompose `src/export/site_export_utils.py` (function: `_export_data`
      CC=14). Extract per-output-backend (CSV / SQLite / ArangoDB) private helpers. No new
      submodule. Local validation per template. Commit: `refactor(export): decompose
      SiteExportUtils._export_data CC=14 -> <=10`.

- [ ] T034 [US3] Decompose `src/export/site_insights_exporter.py` Tier 3 portion (function:
      `insight_metrics` CC=13). Fill in `InsightMetricCollector.collect(...)` stub created in
      T022 (`src/export/site_insights/insight_metric_collector.py`).
      `SiteInsightsExporter.insight_metrics` becomes a 2–5-line façade. Local validation per
      template. Commit: `refactor(export): decompose SiteInsightsExporter.insight_metrics
      CC=13 -> <=10`. **Sequential after T022** (same file).

- [ ] T035 [P] [US3] Decompose `src/gateway/gateway_export_utils.py` (functions:
      `management_ips` CC=13, `device_configs` CC=11). In-place Extract Method (row-builder
      helper for `management_ips`; per-config-section helpers for `device_configs`). No new
      submodule. Local validation per template. Commit: `refactor(gateway): decompose
      GatewayExportUtils hotspots (management_ips CC=13, device_configs CC=11) -> <=10`.

- [ ] T036 [P] [US3] Decompose `src/gateway/gateway_stats_exporter.py` (function:
      `device_stats` CC=16). In-place Extract Method (per-stat-group renderer helpers). No new
      submodule. Local validation per template. Commit: `refactor(gateway): decompose
      GatewayStatsExporter.device_stats CC=16 -> <=10`.

- [ ] T037 [P] [US3] Decompose `src/gateway/wan2_migration_manager.py` (function:
      `_print_site_variable_summary` CC=13). In-place Extract Method (per-section printer
      helpers). No new submodule. Local validation per template. Commit: `refactor(gateway):
      decompose Wan2MigrationManager._print_site_variable_summary CC=13 -> <=10`.

- [ ] T038 [P] [US3] Decompose `src/gateway/wan_probe_device_override_manager.py` (functions:
      `_find_devices_with_overrides` CC=19, `_generate_report` CC=14, `_update_single_device`
      CC=12). In-place Extract Method + Guard Clauses on the same class. No new submodule.
      Local validation per template. Commit: `refactor(gateway): decompose
      WanProbeDeviceOverrideManager hotspots (3 methods CC 12-19) -> <=10`.

- [ ] T039 [P] [US3] Decompose `src/inventory/org_device_inventory_msp.py` (function:
      `_display_combined_pivot_and_export` CC=13). In-place Extract Method (pivot-build
      helper + export-route helper). No new submodule. Local validation per template. Commit:
      `refactor(inventory): decompose OrgDeviceInventoryMSP._display_combined_pivot_and_export
      CC=13 -> <=10`.

- [ ] T040 [P] [US3] Decompose `src/inventory/org_device_inventory_summary.py` (functions:
      `_fetch_versions_per_model` CC=24, `_display_pivot_and_export` CC=12). In-place Extract
      Method (per-device-type fetcher helpers for `_fetch_versions_per_model`; pivot-build +
      export helpers for `_display_pivot_and_export`). No new submodule. Local validation per
      template. Commit: `refactor(inventory): decompose OrgDeviceInventorySummary hotspots
      (_fetch_versions_per_model CC=24, _display_pivot_and_export CC=12) -> <=10`.

- [ ] T041 [US3] Decompose `src/maps/maps_manager.py` Tier 3 portion (functions:
      `_validate_ppm` CC=13, `_add_vbeacons_to_figure` CC=13, `download_site_map_images`
      CC=11). Fill in `PpmValidator.validate(...)` (`src/maps/plotly_viewer/ppm_validator.py`)
      and `VbeaconFigureBuilder.add(...)` (`src/maps/plotly_viewer/vbeacon_figure_builder.py`)
      stubs created in T020. `download_site_map_images` uses in-place Extract Method (per-image
      download helper). `MapsManager._validate_ppm` and `._add_vbeacons_to_figure` become
      2–5-line façades. Local validation per template. Commit: `refactor(maps): decompose
      MapsManager Tier-3 hotspots (_validate_ppm CC=13, _add_vbeacons_to_figure CC=13,
      download_site_map_images CC=11) -> <=10`. **Sequential after T020** (same file).

- [ ] T042 [P] [US3] Decompose `src/site/site_config_manager.py` (function:
      `_analyze_sites_for_rf_templates` CC=12). In-place Extract Method (per-template-class
      analyzer helpers). No new submodule. Local validation per template. Commit:
      `refactor(site): decompose SiteConfigManager._analyze_sites_for_rf_templates CC=12 -> <=10`.

- [ ] T043 [P] [US3] Decompose `src/ssh/ssh_runner_manager.py` (functions: `interactive`
      CC=15, `_collect_missing_data` CC=17, `_select_gateway_template` CC=18). Create new
      submodule `src/ssh/runner_manager/` with `__init__.py`,
      `interactive_flow.py::InteractiveFlow.run(...)` (full `interactive` logic),
      `data_collector.py::DataCollector.collect(...)` (full `_collect_missing_data` logic),
      `gateway_template_selector.py::GatewayTemplateSelector.select(...)` (full
      `_select_gateway_template` logic). Façade methods on `SSHRunnerManager` become 2–5-line
      delegations. Preserve public class + method names. Local validation per template + manual:
      `--menu 176` SSH runner manager. Commit: `refactor(ssh): decompose SSHRunnerManager
      hotspots (interactive CC=15, _collect_missing_data CC=17, _select_gateway_template CC=18)
      -> <=10`.

- [ ] T044 [US3] Decompose `src/ssh/ssh_runner.py` Tier 3 portion (functions:
      `load_commands_from_csv` CC=16, `_connect` CC=15, `_parse_command_list` CC=11). Fill in
      stubs created in T013: `CsvCommandLoader.load(...)` and `CsvCommandLoader.parse_list(...)`
      in `src/ssh/config/csv_command_loader.py`; `ConnectStrategy.connect(...)` in
      `src/ssh/shell_execution/connect_strategy.py`. `EnhancedSSHRunner.load_commands_from_csv`,
      `._connect`, `._parse_command_list` become 2–5-line façades. Local validation per template
      + manual: `--menu 175` (touches load + connect + parse). Commit: `refactor(ssh): decompose
      EnhancedSSHRunner Tier-3 hotspots (load_commands_from_csv CC=16, _connect CC=15,
      _parse_command_list CC=11) -> <=10`. **Sequential after T013 and T024** (same file).

- [ ] T045 [P] [US3] Decompose `src/troubleshooting/interactive_test_runner.py` (function:
      `execute` CC=18, class CC=15). In-place Extract Method (per-test-phase helpers) so both
      method and class drop to ≤ 10. No new submodule. Local validation per template. Commit:
      `refactor(troubleshooting): decompose InteractiveTestRunner (execute CC=18, class CC=15)
      -> <=10`.

- [ ] T046 [P] [US3] Decompose `src/troubleshooting/marvis_troubleshoot_utils.py` (functions:
      `network_connectivity` CC=23, `device_performance` CC=18, `client_connectivity` CC=13).
      In-place Extract Method (per-Marvis-action helpers) on the same class. No new submodule.
      Local validation per template. Commit: `refactor(troubleshooting): decompose
      MarvisTroubleshootUtils hotspots (3 methods CC 13-23) -> <=10`.

- [ ] T047 [US3] Decompose `src/ui/tui.py` Tier 3 portion (functions: `_discover_current_level`
      CC=26, `_format_value_hierarchical` CC=22, `_start_function_execution` CC=15,
      `_submit_parameter` CC=14, `_create_results_grid` CC=14, `_should_show_results_grid`
      CC=13, `_load_dotenv_only` CC=12). Move `_format_value_hierarchical` into new
      `src/ui/formatting/__init__.py` + `hierarchical_value_formatter.py::HierarchicalValueFormatter.format(...)`.
      Move `_start_function_execution` and `_submit_parameter` into the
      `ParameterCollector` stub from T012 (`src/ui/execution/parameter_collector.py`). Move
      `_create_results_grid` into the `ResultsGridBuilder` already created in T012
      (`src/ui/layout/results_grid_builder.py`). `_discover_current_level`,
      `_should_show_results_grid`, `_load_dotenv_only` use in-place Extract Method + Guard
      Clauses. Façade methods on `MistHelperTUI` become 2–5-line delegations. Preserve public
      class + method names. Local validation per template + manual: launch TUI, navigate,
      execute a safe menu, view results grid, exit. Commit: `refactor(ui): decompose
      MistHelperTUI Tier-3 hotspots (7 methods CC 12-26) -> <=10`. **Sequential after T012**
      (same file).

- [ ] T048 [US3] Decompose `src/websocket/service_ping_discovery.py` Tier 3 portion (functions:
      `_display_service_categories` CC=15, `_extract_from_device_config` CC=14). Fill in
      `ServiceCategoryRenderer.render(...)` stub created in T026
      (`src/websocket/service_ping/service_category_renderer.py`); `_extract_from_device_config`
      uses in-place Extract Method on the mixin. `ServicePingDiscoveryMixin._display_service_categories`
      becomes a 2–5-line façade. Local validation per template. Commit: `refactor(websocket):
      decompose ServicePingDiscoveryMixin Tier-3 hotspots (_display_service_categories CC=15,
      _extract_from_device_config CC=14) -> <=10`. **Sequential after T026** (same file).

### Tier 3 Validation Gate

- [ ] T049 [US3] Tier 3 / final validation gate — run **all** of the following and confirm
      green:
      ```powershell
      python -m radon cc src\ -n C
      python -m radon cc src\ -j | python -c "import sys, json; data = json.loads(sys.stdin.read()); offenders = [(f, b['name'], b['complexity']) for f, blocks in data.items() for b in blocks if b['complexity'] > 10]; print('All functions within complexity threshold.' if not offenders else offenders); sys.exit(0 if not offenders else 1)"
      python -m ruff check .
      python -m black --check .
      python -m mypy src/ --config-file pyproject.toml
      python -m pytest tests/guardrails/ tests/unit/ tests/integration/ -q
      python -m pytest --cov=src --cov-report=term-missing tests/
      ```
      First two commands MUST report zero offenders. Remaining commands MUST exit 0. Coverage
      MUST be ≥ 80% (SC-006). If any failure: fix in-place BEFORE pushing.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T050 Spot-validation smoke run (SC-007): re-run the smoke baseline captured in T003 and
      diff against the new outputs. `--menu 27` CSV MUST be byte-identical;`--menu 19` printed
      report MUST be byte-identical; TUI initial render MUST match the baseline screenshot.
      If any diff: investigate the responsible Tier task and fix on a new commit.

- [ ] T051 Inline-comment audit (SC-008): on a random sample of 3 new submodule files,
      visually confirm ≥ 95% of executable lines carry a same-line comment. If any file falls
      short: add comments on a new commit.

- [ ] T052 Action-logging audit (SC-009): on a random sample of 3 new helper classes, visually
      confirm every meaningful action has `logging.info` before and `logging.debug` after. If
      any miss: add bookends on a new commit.

- [ ] T053 No-suppression audit (FR-002 / SC-003): run
      `git diff main...feat/391-clone-device-config-to-gateway-template -- src/ | Select-String
      "noqa|pylint: disable|radon"`. Output MUST be empty.

- [ ] T054 Push final state and trigger CI:
      `git push origin feat/391-clone-device-config-to-gateway-template`. Monitor CI:
      `gh pr checks 391 --watch`. All required checks (ruff, black, mypy, radon, pytest,
      bandit, pip-audit, codeql) MUST be green.

- [ ] T055 After CodeQL finishes (~2–3 min after push), add the `auto-merge` label to PR
      #391 per the project's auto-merge policy: `gh pr edit 391 --add-label auto-merge`. Wait
      for the squash-merge to complete. Confirm `main` now contains the clone-device-config
      feature.

---

## Dependencies & Story Completion Order

```
Setup (T001–T003)
   |
   v
Tier 1 (T010–T015 in parallel) --> T016 Tier 1 Gate (push)
   |
   v
Tier 2 (T020, T021, T022, T025, T026 in parallel; T023 after T014; T024 after T013)
   |    --> T027 Tier 2 Gate (push)
   |
   v
Tier 3 (T030–T040, T042, T043, T045, T046 in parallel;
         T034 after T022; T041 after T020; T044 after T013+T024;
         T047 after T012; T048 after T026)
   |    --> T049 Tier 3 Gate
   |
   v
Polish (T050–T053) --> T054 push + CI monitor --> T055 auto-merge
```

**Same-file serialization (sequential, no [P])**:
- `src/auth/interactive_session.py`: T014 -> T023
- `src/ssh/ssh_runner.py`: T013 -> T024 -> T044
- `src/maps/maps_manager.py`: T020 -> T041
- `src/export/site_insights_exporter.py`: T022 -> T034
- `src/ui/tui.py`: T012 -> T047
- `src/websocket/service_ping_discovery.py`: T026 -> T048

## Parallel Execution Examples

**Tier 1 (all 6 files independent — full parallel)**:
```
Worker A: T010 (websocket/manager.py)
Worker B: T011 (websocket/diag_commands.py)
Worker C: T012 (ui/tui.py)
Worker D: T013 (ssh/ssh_runner.py)
Worker E: T014 (auth/interactive_session.py)
Worker F: T015 (gateway/gateway_override_analyzer.py)
```

**Tier 2 (5 parallel + 2 sequential on Tier 1 files)**:
```
Parallel:  T020, T021, T022, T025, T026
Serial:    T023 starts after T014 merges; T024 starts after T013 merges
```

**Tier 3 (most parallel; 5 sequential on earlier-tier files)**:
```
Parallel:  T030, T031, T032, T033, T035–T040, T042, T043, T045, T046
Serial:    T034 after T022; T041 after T020; T044 after T013+T024; T047 after T012; T048 after T026
```

## Implementation Strategy

- **MVP scope**: Tier 1 (T010–T016). Pushing Tier 1 alone clears the worst-grade Radon
  failures and proves the façade pattern works at scale. The PR can stay open in draft until
  Tier 2 + 3 land.
- **Incremental delivery**: each Tier ends with a push and a validation gate. If Tier 2 or
  Tier 3 reveals an unforeseen problem (e.g., a Tier 1 collaborator's API needs adjusting),
  fix-forward on a new commit — never push to a merged branch (workflow rule).
- **Commit granularity**: one commit per task. Each commit's diff is scoped to a single file
  plus its newly-created submodule, making bisect trivial if a regression surfaces.
- **Risk control**: smoke-baseline captures (T003) plus the per-task `pytest
  tests/guardrails/` run catch behavioral regressions before they reach CI.

## Format Validation

Every task line above:
- Starts with `- [ ]` checkbox: ✓
- Carries a `T###` ID: ✓
- Uses `[P]` only when parallel-safe (no shared file with another in-progress task): ✓
- Carries `[US1]`, `[US2]`, or `[US3]` story label inside user-story phases; no story label
  in Setup, Foundational, or Polish phases: ✓
- Lists file paths and new submodule paths explicitly: ✓
