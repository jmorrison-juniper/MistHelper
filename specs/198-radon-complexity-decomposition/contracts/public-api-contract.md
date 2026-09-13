# Contract: Preserved Public API Surface

**Feature**: 198-radon-complexity-decomposition
**Phase**: 1 (Design & Contracts)

This contract enumerates every public symbol in `src/` that MUST remain unchanged across this refactor (FR-006). Any rename, signature change, or relocation of these symbols breaks the contract and constitutes a regression.

"Public" here means: imported from outside `src/` (by `MistHelper.py`, `wsgi.py`, `web_portal/`, `tests/`, or other top-level modules), or named without a leading underscore on a class that is so imported.

The list is grouped by the façade file that owns the symbol. The agent MUST run the verification grep listed at the bottom of this document before each tier push to confirm no contract member has been silently dropped, renamed, or moved.

---

## src/websocket/manager.py — `WebSocketManager`

Public methods that must keep their name and signature:

- `__init__(self, ...)` — constructor signature preserved
- `wait_for_command_result(self, ...)` — return shape preserved (dict / list as today)
- `connect(self, ...)`
- `disconnect(self, ...)`
- `send_command(self, ...)`
- `register_handler(self, ...)` (if present)

Internal implementation moves to `src/websocket/polling/` and `src/websocket/message_handlers/`; the public surface above is the façade.

---

## src/websocket/diag_commands.py — `WebSocketNetworkDiagCommands`

- `__init__(self, ...)`
- `arp_device(self, device_mac: str, ...)`
- `ping_device(self, device_mac: str, ...)`
- Any other top-level command method without a leading underscore

Internal implementation moves to `src/websocket/diag/`.

---

## src/websocket/commands.py — `WebSocketCommands`

- `__init__(self, ...)`
- `show_mac_table(self, ...)`
- Other public `show_*` methods on this class

Internal implementation moves to `src/websocket/commands/handlers/`.

---

## src/websocket/service_ping_discovery.py — `ServicePingDiscoveryMixin`

- All public mixin methods used by classes that mix it in. (Grep verified pre-push.)

Internal implementation moves to `src/websocket/service_ping/`.

---

## src/ui/tui.py — `MistHelperTUI`

- `__init__(self, ...)`
- `run(self, ...)`
- `handle_input(self, key)`
- `check_keyboard_input(self, ...)`
- `execute_current_item(self, ...)`
- `create_layout(self, ...)`

Internal implementation moves to `src/ui/input_handlers/`, `src/ui/layout/`, `src/ui/execution/`, `src/ui/formatting/`.

---

## src/ssh/ssh_runner.py — `EnhancedSSHRunner`

- `__init__(self, ...)`
- `connect(self, ...)`
- `disconnect(self, ...)`
- `run_application(self, ...)`
- `run_ssh_commands_multi_host(self, ...)`
- `load_ssh_config_from_env(self, ...)` (or `EnvConfigLoader.load()` if hoisted; if hoisted, a thin backward-compatible classmethod stays on `EnhancedSSHRunner`)
- `load_commands_from_csv(self, ...)`

Internal implementation moves to `src/ssh/shell_execution/`, `src/ssh/multi_host/`, `src/ssh/application/`, `src/ssh/config/`.

---

## src/ssh/ssh_runner_manager.py — `SSHRunnerManager`

- `__init__(self, ...)`
- `interactive(self, ...)`

Internal implementation moves to `src/ssh/runner_manager/`.

---

## src/auth/interactive_session.py — `InteractiveSessionManager`

- `__init__(self, ...)`
- `initialize_mist_session_interactive(self, ...)`
- `select_msp_and_org(self, ...)`

Internal implementation moves to `src/auth/session_init/`.

---

## src/gateway/gateway_override_analyzer.py — `GatewayOverrideAnalyzer`

- `__init__(self, ...)`
- `with_wan_overrides(self, ...)`

Internal implementation moves to `src/gateway/overrides/`.

---

## src/maps/maps_manager.py — `MapsManager`

- `__init__(self, ...)`
- All public methods on `MapsManager` (the dispatcher uses many — full enumeration via grep)

Internal implementation moves to `src/maps/plotly_viewer/`.

---

## src/export/wifi_clients_exporter.py — `WifiClientsExporter`

- `__init__(self, ...)`
- `execute(self, ...)`

Internal implementation moves to `src/export/wifi_clients/`.

---

## src/export/site_insights_exporter.py — `SiteInsightsExporter`

- `__init__(self, ...)`
- `device_insights(self, ...)`
- `insight_metrics(self, ...)`

Internal implementation moves to `src/export/site_insights/`.

---

## All other affected classes (Tier 3, in-place)

`SiteInventoryHealthAnalyzer`, `UVRuntimeHelper`, `MultiApScanCaptureWorkflow`, `SiteExportUtils`, `GatewayExportUtils`, `GatewayStatsExporter`, `WAN2MigrationManager`, `WANProbeDeviceOverrideManager`, `OrgDeviceInventoryMSPOrchestrator`, `OrgDeviceInventorySummaryCore`, `SiteConfigManager`, `InteractiveTestRunner`, `MarvisTroubleshootUtils` — all public methods preserved; only private `_helper` methods are added.

---

## Verification Procedure (run before each tier push)

```powershell
# 1. Capture the current public surface of every façade file
$facades = @(
  "src/websocket/manager.py",
  "src/websocket/diag_commands.py",
  "src/websocket/commands.py",
  "src/websocket/service_ping_discovery.py",
  "src/ui/tui.py",
  "src/ssh/ssh_runner.py",
  "src/ssh/ssh_runner_manager.py",
  "src/auth/interactive_session.py",
  "src/gateway/gateway_override_analyzer.py",
  "src/maps/maps_manager.py",
  "src/export/wifi_clients_exporter.py",
  "src/export/site_insights_exporter.py"
)
foreach ($f in $facades) {
  Write-Host "=== $f ==="
  Select-String -Path $f -Pattern "^(class |    def )(?!_)" | ForEach-Object { $_.Line.Trim() }
}

# 2. Diff against the same capture taken before the tier began.
# Any removed or renamed public symbol is a contract violation that MUST be fixed before push.

# 3. External consumer grep — any import of a moved private helper from outside src/
git grep -n "from src\." -- 'MistHelper.py' 'wsgi.py' 'web_portal/' 'tests/'
```

---

## Acceptance Criteria

- Every public symbol enumerated above can be imported from its original module path with its original name after the refactor.
- The constructor signature of every façade class accepts the same arguments as before (positional and keyword).
- Every public method returns the same shape (dict / list / object) as before; new fields may be added only if existing fields are preserved.
- No public method becomes a coroutine if it was synchronous before (and vice versa).
- `tests/guardrails/` and `tests/unit/` pass without test signature changes.

This contract is the binary gate for the refactor — if any line above is violated, the offending commit MUST be reverted and rewritten before tier push.
