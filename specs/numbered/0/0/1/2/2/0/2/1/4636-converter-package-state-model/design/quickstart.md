# Quickstart: Compliant Converter Package and State Model

This guide gives the exact reproduction steps and the exact verification commands for issue 4636. Run the commands from the repository root in a worktree that has the locked environment. The environment comes from `.github/copilot-instructions.md`, section Language and environment.

```powershell
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

Each command below names its expected result. A result that differs means that the step failed. Stop and record the difference in `analysis.md` before you continue.

## Scenario 1: Confirm the current converter root

Purpose: Show that the converter package holds five direct children before any change.

```powershell
git ls-tree --name-only HEAD src/interfaces/portals/cisco_config_converter/
```

Expected result: Five names: `__init__.py`, `conversion.py`, `models.py`, `presentation`, and `routes.py`.

## Scenario 2: Reproduce the random portal secret

Purpose: Show the session key change that breaks review records after a restart.

```powershell
Remove-Item Env:PORTAL_SECRET_KEY -ErrorAction SilentlyContinue
python -c "print(__import__('web_portal.services.config', fromlist=['PortalConfigLoader']).PortalConfigLoader().load_config()['secret_key'])"
python -c "print(__import__('web_portal.services.config', fromlist=['PortalConfigLoader']).PortalConfigLoader().load_config()['secret_key'])"
```

Expected result: The two printed values differ. Each run creates a new random value when the variable is unset. The fallback is at `web_portal/services/config.py`, line 113, inside `PortalConfigLoader._validate_values`.

## Scenario 3: Confirm the current model module

Purpose: Show that `models.py` holds five top-level classes before the move.

```powershell
Select-String -LiteralPath src\interfaces\portals\cisco_config_converter\models.py -Pattern '^class '
```

Expected result: Five matches. The lines are 13, 21, 29, 38, and 84.

## Scenario 4: Run the baseline before any edit

Purpose: Record the baseline test result before T004 starts (task T002).

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py
python -m pytest tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py
```

Expected result: Each command prints a summary with zero failures. Record the counts in `analysis.md`.

## Scenario 5: Verify the move and the imports (task T004)

Purpose: Prove that the moved names import from `state/` and that no shim remains.

```powershell
python -m pytest tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py
git grep -n "cisco_config_converter.models"
Test-Path src\interfaces\portals\cisco_config_converter\models.py
```

Expected result: The unit test passes. The `git grep` command prints no match. `Test-Path` prints `False`.

## Scenario 6: Verify the record and transition tests (tasks T005 to T008)

Purpose: Prove the digest, expiry, approval, and transition rules.

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/state/test_state_records.py
python -m pytest tests/integration/web_portal/cisco_config_converter/state/test_state_transitions.py
```

Expected result: Eleven tests in the first module and four in the second module pass. A parametrized test counts once, as one function.

## Scenario 7: Verify the store tests (tasks T009 and T010)

Purpose: Prove fail-closed writes, read-back, seal checks, restart, and logging.

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/state/test_state_store.py
```

Expected result: Eight tests pass. No test creates a file outside its `tmp_path`.

## Scenario 8: Verify the multiworker tests (task T011)

Purpose: Prove that two processes cannot consume one approval.

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/state/test_state_multiworker.py
```

Expected result: Two tests pass. Repeat the command twenty times for SC-005. Each run must report exactly one successful consumption.

## Scenario 9: Verify the structure (tasks T003, T012, and T013)

Purpose: Prove the five-child rule for the package, the subpackages, and the test folders.

```powershell
python -m pytest tests/guardrails/test_nested_package_structure.py
python -m pytest tests/guardrails/test_move_module_guidance.py
radon cc src/interfaces/portals/cisco_config_converter -j | complexity-gate --max 10
(git ls-tree --name-only HEAD src/interfaces/portals/cisco_config_converter/state/).Count
(git ls-tree --name-only HEAD tests/integration/web_portal/cisco_config_converter/state/).Count
```

Expected result: Both guard tests pass. The complexity gate reports no block above 10. The state package count is 5. The test state folder count is 5.

## Scenario 10: Confirm the shared files stay unchanged

Purpose: Prove that no route, shared portal file, or container file changed.

```powershell
git diff --name-only origin/main -- web_portal/app.py web_portal/templates/base.html web_portal/services/config.py compose.yml .gitignore requirements.txt
```

Expected result: No output. The command prints each shared file that changed. An empty result means that no shared file changed.

## Cleanup

- Tests use `tmp_path`. Pytest removes that folder after each run.
- This change starts no container. Compose and Podman steps do not apply.
- Close the PowerShell session after Scenario 2. The `$env:PORTAL_SECRET_KEY` change ends with that session.
