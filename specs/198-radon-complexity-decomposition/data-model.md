# Data Model: Collaborator Class Catalog

**Feature**: 198-radon-complexity-decomposition
**Phase**: 1 (Design & Contracts)

Since this is a refactor with no schema or persistence changes, the "data model" is the catalog of new collaborator classes / dataclasses introduced by the decomposition, their single-responsibility scope, public method list, and internal state fields. ENDPOINT_PRIMARY_KEY_STRATEGIES and database schemas are explicitly unchanged (FR-013).

Entries are grouped by tier and by parent package. Each entry follows the format:

> **`Path::ClassName`** — Single-responsibility statement.
> *Public methods*: list. *State*: list (dataclass fields or `__init__` attributes).
> *Replaces*: original function / class name + CC.

---

## Tier 1 Collaborators

### websocket/polling/

> **`src/websocket/polling/state.py::PollState`** — Single immutable-by-convention container for state that travels across the polling loop (frame buffer, accumulated payload chunks, last-seen-sequence id, completion flag, error context).
> *Public methods*: none beyond dataclass `__init__`. *Fields*: `buffer: list[dict]`, `last_sequence: int | None`, `is_complete: bool`, `error: str | None`, `started_at: float`.
> *Replaces*: 8+ local variables in `WebSocketManager.wait_for_command_result`.

> **`src/websocket/polling/result_poller.py::WebSocketResultPoller`** — Owns the per-call polling loop: drains the WS channel, appends frames to `PollState.buffer`, returns when `CompletionDetector` signals done.
> *Public methods*: `poll(timeout_seconds: float) -> PollState`.
> *State*: `self.ws_channel`, `self.completion_detector`, `self.logger`.
> *Replaces*: outer loop body of `WebSocketManager.wait_for_command_result` CC=110 (~60 of the 110 branches).

> **`src/websocket/polling/completion_detector.py::CompletionDetector`** — Pure logic: given a `PollState`, decides whether polling is done (terminator frame seen, max-bytes reached, timeout, error).
> *Public methods*: `is_done(state: PollState) -> bool`, `reason(state: PollState) -> str`.
> *State*: configuration thresholds (`max_bytes`, `terminator_pattern`) injected at `__init__`.
> *Replaces*: inner termination if/elif chain of `wait_for_command_result` (~40 of the 110 branches).

### websocket/message_handlers/

> **`src/websocket/message_handlers/dispatch.py::MessageDispatchTable`** — Maps `message['type']` -> bound handler. Built once in `WebSocketManager.__init__`.
> *Public methods*: `dispatch(message: dict) -> None`, `register(message_type: str, handler: Callable[[dict], None]) -> None`.
> *State*: `self._table: dict[str, Callable[[dict], None]]`.
> *Replaces*: `WebSocketManager._on_message` CC=37 if/elif chain.

### websocket/diag/

> **`src/websocket/diag/arp_executor.py::ArpDeviceExecutor`** — Executes `arp` over a WS diag channel: parses args, formats command, awaits response, post-processes ARP table rows for display.
> *Public methods*: `execute(device_mac: str, args: dict) -> list[dict]`.
> *Replaces*: `WebSocketNetworkDiagCommands.arp_device` CC=61.

> **`src/websocket/diag/ping_executor.py::PingDeviceExecutor`** — Executes `ping` over a WS diag channel: count / size / source-vrf options, response parsing.
> *Public methods*: `execute(device_mac: str, args: dict) -> dict`.
> *Replaces*: `WebSocketNetworkDiagCommands.ping_device` CC=36.

> **`src/websocket/diag/diag_command_dispatch.py::DiagCommandDispatch`** — Maps diag command name -> executor class instance. Built once.
> *Public methods*: `dispatch(command_name: str, device_mac: str, args: dict) -> Any`.
> *Replaces*: top-level if/elif in `WebSocketNetworkDiagCommands` (class CC=50).

### ui/input_handlers/

> **`src/ui/input_handlers/keyboard_dispatch.py::KeyboardDispatchTable`** — `{key_code: handler_method}` built once in `MistHelperTUI.__init__`. Handlers are bound methods on the TUI instance.
> *Public methods*: `dispatch(key_code: KeyCode) -> None`.
> *State*: `self._table: dict[KeyCode, Callable[[KeyCode], None]]`.
> *Replaces*: `MistHelperTUI.handle_input` CC=65.

> **`src/ui/input_handlers/key_poller.py::KeyPoller`** — Wraps the non-blocking keyboard read loop (was `check_keyboard_input`). Returns one `KeyCode | None` per call. No business logic.
> *Public methods*: `poll() -> KeyCode | None`.
> *Replaces*: `MistHelperTUI.check_keyboard_input` CC=59.

> **`src/ui/input_handlers/focus_router.py::FocusRouter`** — Given a key code and current focus state, decides whether it goes to the menu pane, the parameter form, the results grid, etc.
> *Public methods*: `route(key_code: KeyCode, focus: FocusState) -> str`.
> *Replaces*: inner if/elif of `check_keyboard_input` selecting target pane.

### ui/layout/

> **`src/ui/layout/layout_builder.py::LayoutBuilder`** — Composes the top-level `Layout` object from `PaneFactory`-produced panes. Pure construction; no event handling.
> *Public methods*: `build(context: LayoutContext) -> Layout`.
> *Replaces*: `MistHelperTUI.create_layout` CC=52.

> **`src/ui/layout/pane_factory.py::PaneFactory`** — One factory method per pane (menu, results, parameter form, log tail, status bar). Each method ≤ CC 10.
> *Public methods*: `menu_pane(...)`, `results_pane(...)`, `parameter_pane(...)`, `log_pane(...)`, `status_bar(...)`.
> *Replaces*: per-pane construction blocks inside `create_layout`.

> **`src/ui/layout/results_grid_builder.py::ResultsGridBuilder`** — Builds the results table widget; column ordering / formatting only.
> *Public methods*: `build(rows: list[dict], columns: list[str]) -> Grid`.
> *Replaces*: `MistHelperTUI._create_results_grid` CC=14.

### ui/execution/

> **`src/ui/execution/item_executor.py::ItemExecutor`** — Selects the right execution strategy for the currently focused menu item (parameterless function, function-requiring-params, sub-menu, dispatcher).
> *Public methods*: `execute(item: MenuItem, context: ExecCtx) -> None`.
> *Replaces*: `MistHelperTUI.execute_current_item` CC=54.

> **`src/ui/execution/function_executor.py::FunctionExecutor`** — Invokes a chosen function, captures result, displays output (CSV path, table, raw JSON depending on return type).
> *Public methods*: `run(fn: Callable, args: dict) -> ExecResult`.
> *Replaces*: `MistHelperTUI._execute_function` CC=36.

> **`src/ui/execution/parameter_collector.py::ParameterCollector`** — Interactive collection of function arguments via the TUI parameter form.
> *Public methods*: `start(fn: Callable) -> ParameterForm`, `submit(form: ParameterForm) -> dict`.
> *Replaces*: `MistHelperTUI._start_function_execution` CC=15 + `_submit_parameter` CC=14.

### ssh/shell_execution/, multi_host/, application/, config/

> **`src/ssh/shell_execution/shell_session.py::ShellSession`** — One interactive shell channel: open, send-and-wait, drain prompt detection, close.
> *Public methods*: `open()`, `send(command: str) -> str`, `close()`.
> *State*: `self.channel`, `self.prompt_pattern`, `self.timeout`.
> *Replaces*: `EnhancedSSHRunner._execute_with_shell` CC=51.

> **`src/ssh/shell_execution/interactive_loop.py::InteractiveLoop`** — REPL-style loop wrapping a `ShellSession` for menu 175/176-style interactive runs.
> *Public methods*: `run()`. *Replaces*: `EnhancedSSHRunner._interactive_mode` CC=19.

> **`src/ssh/shell_execution/connect_strategy.py::ConnectStrategy`** — Decides key-based vs password vs agent auth and opens an SSH transport.
> *Public methods*: `connect(host: HostInfo) -> SSHClient`.
> *Replaces*: `EnhancedSSHRunner._connect` CC=15.

> **`src/ssh/multi_host/single_host_runner.py::SingleHostRunner`** — Executes one or more commands on a single host (non-interactive).
> *Public methods*: `run(host: HostInfo, commands: list[str]) -> HostResult`.
> *Replaces*: `_run_ssh_command_on_host` CC=18 + `_run_ssh_command` CC=19.

> **`src/ssh/multi_host/multi_host_runner.py::MultiHostRunner`** — Fans out `SingleHostRunner` across many hosts (thread pool).
> *Public methods*: `run(hosts: list[HostInfo], commands: list[str]) -> dict[str, HostResult]`.
> *Replaces*: `run_ssh_commands_multi_host` CC=20.

> **`src/ssh/multi_host/batch_orchestrator.py::BatchOrchestrator`** — Manages the batch lifecycle (group hosts, dispatch, aggregate, write per-host logs).
> *Public methods*: `execute(hosts, commands) -> BatchResult`.
> *Replaces*: `_run_multiple_ssh_commands` CC=23.

> **`src/ssh/multi_host/interactive_orchestrator.py::InteractiveOrchestrator`** — Interactive variant: prompts for confirmation per host group, supports skip/abort.
> *Public methods*: `execute(hosts, commands) -> InteractiveBatchResult`.
> *Replaces*: `_run_multiple_ssh_commands_interactive` CC=42.

> **`src/ssh/application/application_runner.py::ApplicationRunner`** — Top-level "run application" workflow that drives the SSH runner from a CSV-style host+command spec.
> *Public methods*: `run(spec: ApplicationSpec) -> ApplicationResult`.
> *Replaces*: `EnhancedSSHRunner.run_application` CC=64.

> **`src/ssh/config/env_config_loader.py::EnvConfigLoader`** — Reads `.env`-derived SSH config (credentials, default ports, key paths) with validation.
> *Public methods*: `load() -> SSHConfig`.
> *Replaces*: `load_ssh_config_from_env` CC=33.

> **`src/ssh/config/csv_command_loader.py::CsvCommandLoader`** — Reads `data/SSH_COMMANDS.CSV` (or root fallback), parses host/command rows, validates schema.
> *Public methods*: `load(path: pathlib.Path) -> list[CommandRow]`, `parse_list(raw: str) -> list[str]`.
> *Replaces*: `load_commands_from_csv` CC=16 + `_parse_command_list` CC=11.

### auth/session_init/

> **`src/auth/session_init/session_initializer.py::SessionInitializer`** — End-to-end Mist session bootstrap: token discovery, env validation, cloud selection, MSP detection, org pick.
> *Public methods*: `initialize() -> MistSession`.
> *Replaces*: `InteractiveSessionManager.initialize_mist_session_interactive` CC=40.

> **`src/auth/session_init/msp_org_selector.py::MspOrgSelector`** — Interactive MSP-then-org selection flow with `safe_input` prompts.
> *Public methods*: `select(msps: list[Msp]) -> tuple[Msp, Org]`.
> *Replaces*: `InteractiveSessionManager.select_msp_and_org` CC=26.

### gateway/overrides/

> **`src/gateway/overrides/wan_override_walker.py::WanOverrideWalker`** — Traverses the gateway tree to discover devices carrying WAN overrides; yields candidate override rows for the classifier.
> *Public methods*: `walk(org_id: str) -> Iterator[OverrideCandidate]`.
> *Replaces*: outer-loop body of `GatewayOverrideAnalyzer.with_wan_overrides` CC=41.

> **`src/gateway/overrides/override_classifier.py::OverrideClassifier`** — Pure logic: given an `OverrideCandidate`, classifies it (effective override, no-op shadow, template-default match, etc.).
> *Public methods*: `classify(candidate: OverrideCandidate) -> OverrideKind`.
> *Replaces*: inner if/elif of `with_wan_overrides`.

---

## Tier 2 Collaborators

### maps/plotly_viewer/

> **`src/maps/plotly_viewer/viewer_launcher.py::ViewerLauncher`** — Boots the Plotly figure window (or browser tab on Windows): figure assembly, browser detection, port selection.
> *Public methods*: `launch(figure: Figure) -> None`.
> *Replaces*: `MapsManager._launch_plotly_viewer` CC=36.

> **`src/maps/plotly_viewer/ppm_validator.py::PpmValidator`** — Validates pixels-per-meter calibration (range check + sanity warnings). *Public methods*: `validate(ppm: float) -> ValidationResult`. *Replaces*: `_validate_ppm` CC=13.

> **`src/maps/plotly_viewer/vbeacon_figure_builder.py::VbeaconFigureBuilder`** — Adds vBeacon markers and labels to a Plotly figure. *Public methods*: `add_to(figure: Figure, vbeacons: list[VBeacon]) -> None`. *Replaces*: `_add_vbeacons_to_figure` CC=13.

### export/wifi_clients/

> **`src/export/wifi_clients/client_fetcher.py::ClientFetcher`** — Fetches wifi clients for a target scope (site / org / time range). *Public methods*: `fetch(scope: Scope) -> list[Client]`.

> **`src/export/wifi_clients/client_row_builder.py::ClientRowBuilder`** — Flattens a `Client` dict into the CSV/SQLite row shape per the agreed columns. *Public methods*: `build(client: Client) -> dict`.

> **`src/export/wifi_clients/output_writer_selector.py::OutputWriterSelector`** — Routes the row stream to CSV, SQLite, or ArangoDB+Redis based on the active output mode. *Public methods*: `route(rows: Iterable[dict], filename: str) -> None`.

> *Together replace*: `WifiClientsExporter.execute` CC=30 + class CC=31.

### export/site_insights/

> **`src/export/site_insights/device_insights_collector.py::DeviceInsightsCollector`** — Per-device insight metric collection. *Public methods*: `collect(site_id: str, device_id: str) -> dict`. *Replaces*: `SiteInsightsExporter.device_insights` CC=25.

> **`src/export/site_insights/insight_metric_collector.py::InsightMetricCollector`** — Per-metric insight collection (the simpler variant). *Public methods*: `collect(site_id: str, metric: str) -> dict`. *Replaces*: `SiteInsightsExporter.insight_metrics` CC=13.

### websocket/commands/handlers/

> **`src/websocket/commands/handlers/mac_table_renderer.py::MacTableRenderer`** — Builds & prints the `show mac-table` output. *Public methods*: `render(rows: list[dict]) -> None`. *Replaces*: `WebSocketCommands.show_mac_table` CC=28 + class CC=29.

### websocket/service_ping/

> **`src/websocket/service_ping/tenant_category_renderer.py::TenantCategoryRenderer`** — Renders the tenant-category section of service-ping discovery output. *Public methods*: `render(categories: dict) -> None`. *Replaces*: `_display_tenant_categories` CC=33.

> **`src/websocket/service_ping/service_category_renderer.py::ServiceCategoryRenderer`** — Renders the service-category section (Tier 3). *Public methods*: `render(categories: dict) -> None`. *Replaces*: `_display_service_categories` CC=15.

### ssh/runner_manager/

> **`src/ssh/runner_manager/interactive_flow.py::InteractiveFlow`** — Drives the interactive flow of `SSHRunnerManager.interactive`. *Public methods*: `run() -> None`. *Replaces*: `interactive` CC=15.

> **`src/ssh/runner_manager/data_collector.py::DataCollector`** — Collects missing fields interactively. *Public methods*: `collect(known: dict) -> dict`. *Replaces*: `_collect_missing_data` CC=17.

> **`src/ssh/runner_manager/gateway_template_selector.py::GatewayTemplateSelector`** — Prompts for and resolves a gateway template ID. *Public methods*: `select(org_id: str) -> str`. *Replaces*: `_select_gateway_template` CC=18.

---

## Tier 3 Helpers (in-place private methods on existing classes)

Tier 3 introduces no new public classes. It only adds private `_verb_noun` helpers on the existing classes listed in [plan.md](plan.md#tier-3--files-with-cc-1124-lowest-risk-largest-count). Each helper:

- Has CC ≤ 10.
- Carries inline comments on every executable line.
- Has `logging.info` before / `logging.debug` after each meaningful action.
- Receives state explicitly via parameters (no module globals).
- Lives on the same class as the original method it was extracted from, unless the table in plan.md routes it into an already-existing Tier 1/2 submodule (e.g., `_validate_ppm` -> `PpmValidator`).

---

## Validation Rules

- Every collaborator class above must be reachable from its façade (i.e., the façade method calls into it). Detected by `grep` over the façade file for the new class name during PR review.
- Every collaborator class must have CC ≤ 10 at both method and class level (radon report on the new file must be empty under `-n C`).
- Every collaborator must preserve the user-facing strings and log lines from the original method byte-for-byte (FR-010).

## State Transitions

None — refactor introduces no new state machines. `PollState` is the closest thing: a flat container whose fields are mutated in-place by `WebSocketResultPoller` across iterations of one polling call, then read by `CompletionDetector`. No persistence; no transitions across calls.
