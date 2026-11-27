# Quickstart: Hardware Manifest Finalization After a File Lock

This guide gives the exact commands for this issue. Run each command from the repository root with the `.venv` of the main checkout. Install no package during these steps.

## 1. Confirm the Defect Before the Change

Run the artifact replace tests on main.

```powershell
python -m pytest tests/unit/websocket_streams/web/test_ws_artifact_replace.py
```

Before the implementation, each new case fails. The revised case TEST-10 also fails on its new assertion. The existing cases pinned at `test_ws_artifact_replace.py:98` and `:223` keep passing.

## 2. Run the Affected Suites After the Change

Run each suite. Each command must report all tests passed.

```powershell
python -m pytest tests/unit/websocket_streams/web/test_ws_artifact_replace.py
python -m pytest tests/unit/websocket_streams/web/test_ws_output_boundaries.py
python -m pytest tests/unit/websocket_streams/web/test_hardware_native_acceptance.py
python -m pytest tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py
python -m pytest tests/unit/websocket_streams/web/test_ws_orphan_retention.py
python -m pytest tests/unit/ex_hardware_inventory/test_hardware_operation.py
python -m pytest tests/integration/ex_hardware_inventory/test_hardware_cli_flow.py
```

## 3. Run the Local Gates on the Changed Files

Run each gate from the Local gates table in `.github/copilot-instructions.md` (line 50). Each gate must show its expected result.

```powershell
python -m ruff check .
python -m black --check .
python -m mypy $MYPY_PATHS --config-file pyproject.toml
symbol-diff --base origin/main src/mist/realtime/websocket_streams/web/services/operations/artifacts.py
symbol-diff --base origin/main src/operations/exporting/ex_hardware_inventory/operation.py
symbol-diff --base origin/main src/operations/exporting/ex_hardware_inventory/console.py
symbol-diff --base origin/main src/mist/realtime/websocket_streams/live/sessions/manager/factory.py
python MistHelper.py --test
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Set `MYPY_PATHS` to the value in the `MYPY_PATHS` variable of `.github/workflows/ci.yml` (line 93) before the mypy command.

## 4. Collect the Runtime Evidence (Task T019)

Warning: Do not delete a run folder during or after this procedure. The folder holds the only copy of the native replies of that run.

1. Run menu 309 for one organization that the operator authorized. Start it with `python MistHelper.py --menu 309` (`.github/copilot-instructions.md`, line 155). Follow the sign-in prompts of the menu.
2. At the preview, compare the listed switches with the expected switches. Type the confirmation phrase only when the list matches.
3. After the run ends, search the runtime log for the refused-write events.

```powershell
Select-String -Path data\script.log -Pattern 'web.artifact.batch.manifest.error|web.artifact.batch.finalize.error|web.artifact.batch.marker.error|web.artifact.replace.retry'
```

4. List the run folders. Each folder name is the run identifier.

```powershell
Get-ChildItem -Path data\websocket-streams -Directory
```

5. Read the status fields of one run manifest. Do not print the target entries.

```powershell
Get-Content -Path data\websocket-streams\<run_id>\manifest.json -Raw | ConvertFrom-Json | Select-Object status, partial, durable
```

6. Check for the finalization marker in the same run folder.

```powershell
Test-Path -Path data\websocket-streams\<run_id>\finalization-failed.json
```

7. Open Resource Monitor, select the CPU tab, expand Associated Handles, and search for `manifest.json`. Record the process name and the process identifier. Do not close a handle.

Caution: A failed finalization waits up to 6.35 seconds before it reports the failure. The run status line appears after that wait.

8. Post the results in the issue. Include the errno value, the winerror value when present, the handle result, and the run folder name. Do not post device names, serial numbers, or addresses.

## 5. Reproduce the Partial Status Without Hardware

The unit test in TEST-09 reproduces the partial status without a device. Run it after the implementation.

```powershell
python -m pytest tests/unit/ex_hardware_inventory/test_hardware_operation.py
```

## 6. Confirm the Documentation Gate

Run the guardrail tests after the operator guide and the changelog fragment change.

```powershell
python -m pytest tests/guardrails
```
