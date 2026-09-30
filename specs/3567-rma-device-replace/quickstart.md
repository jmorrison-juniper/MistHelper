# Quickstart: RMA Device Replacement

## Local validation

Run these commands from the worktree root. Use the worktree virtual environment.

```powershell
C:\Users\jmorrison\mh-fleet\3567-rma-device-replace\.venv\Scripts\python.exe -m py_compile src\inventory\device_replace\__init__.py src\inventory\device_replace\client.py src\inventory\device_replace\models.py src\inventory\device_replace\operation.py src\inventory\device_replace\persistence.py
C:\Users\jmorrison\mh-fleet\3567-rma-device-replace\.venv\Scripts\python.exe -m ruff check src\inventory\device_replace tests\unit\inventory\device_replace
C:\Users\jmorrison\mh-fleet\3567-rma-device-replace\.venv\Scripts\python.exe -m black --check src\inventory\device_replace tests\unit\inventory\device_replace
C:\Users\jmorrison\mh-fleet\3567-rma-device-replace\.venv\Scripts\python.exe -m mypy src\inventory\device_replace --config-file pyproject.toml
C:\Users\jmorrison\mh-fleet\3567-rma-device-replace\.venv\Scripts\python.exe -m pydocstyle src\inventory\device_replace
C:\Users\jmorrison\mh-fleet\3567-rma-device-replace\.venv\Scripts\python.exe -m pytest tests\unit\inventory\device_replace -q --timeout=120
C:\Users\jmorrison\mh-fleet\3567-rma-device-replace\.venv\Scripts\python.exe -m radon cc src\inventory\device_replace -j | C:\Users\jmorrison\mh-fleet\3567-rma-device-replace\.venv\Scripts\complexity-gate.exe --max 10
C:\Users\jmorrison\mh-fleet\3567-rma-device-replace\.venv\Scripts\test-quality-analyzer.exe --gate --config .github\test-quality-config.toml --baseline .github\test-quality-baseline.json --changed-from origin/main
```

## Dry-run operator scenario

1. Start MistHelper with menu `287` after the integration pull request wires the menu.
2. Enter the old device MAC address or name.
3. Select one unassigned replacement device of the same type.
4. Confirm that the operation shows site, name, model, and type.
5. Run with `--dry-run`.
6. Type `REPLACE`.
7. Confirm that `data/rma_backups/` contains the old configuration backup.
8. Confirm that `data/DeviceReplaceLog.csv` contains `dry_run`.
9. Confirm that no replacement request was sent.

## Live destructive scenario

Warning: This operation moves configuration between Mist inventory devices. A human must review the pull request and the change record before a live run.

1. Confirm that the replacement device is claimed into the organization and unassigned.
2. Confirm that the old device is assigned to the correct site.
3. Run the operation without `--dry-run` during the approved maintenance window.
4. Type `REPLACE` only after you verify the summary.
5. Confirm that the old device becomes unassigned and the new device receives the old configuration.
