# Quickstart: Virtual Chassis Menu Guidance

Run each command from the repository root. Use the venv interpreter `.venv\Scripts\python.exe` for pytest and the Python tools (RC-74).

Warning: do not start menu 161 or menu 162 in any step. A conversion changes the Mist cloud. Every step below runs offline.

## Prerequisites

- Python 3.15 or newer in `.venv` (RC-64).
- The branch `fix/4747-virtual-chassis-menu-options` starts from `main`.
- The four new tests exist after T002.

## Scenario 1: Reproduce the stale guidance with the new tests

Run this command before the text change (T003 to T005). The four new tests fail.

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/test_virtual_chassis.py -k "usage_notes or success_guidance or named_menus or stale_menus" -q
```

Expected result: `4 failed`. Each failure shows the stale menu number in its assertion values.

## Scenario 2: Verify the fix

Run the same command after T003, T004, and T005.

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/test_virtual_chassis.py -k "usage_notes or success_guidance or named_menus or stale_menus" -q
```

Expected result: `4 passed`.

## Scenario 3: Run the whole unit module

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/test_virtual_chassis.py -q
```

Expected result: every test passes. The existing confirmation tests and the existing API call tests keep their results.

## Scenario 4: Run the root test and the guard tests

```powershell
.venv\Scripts\python.exe -m pytest tests/test_virtual_chassis.py tests/guardrails/test_operation_registry_menu_coverage.py tests/guardrails/test_destructive_menu_docs.py -q
```

Expected result: every test passes.

## Scenario 5: Check the symbols and the generated menu pages

```powershell
symbol-diff --base origin/main src/mist/resources/device/virtual_chassis.py
.venv\Scripts\python.exe scripts/generate_menu_wiki.py
.venv\Scripts\python.exe -m scripts.menu_api_map
git status --short
```

Expected result: `symbol-diff` reports `no module-level name changed`. The `git status` output lists no generated page. A listed generated page means D-9 applies.

## Scenario 6: Check the changelog fragment

```powershell
ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4747-virtual-chassis-menu-options.md
```

Expected result: a score of 80 or above.

## Scenario 7: Review the remaining stale words by hand

```powershell
git grep -n -E "(92|93|94)" -- src/mist/resources/device/virtual_chassis.py tests/test_virtual_chassis.py
```

Expected result: no hit names a menu. Each hit must refer to a value other than a menu number. The static test (`stale_menus`) checks the same condition.

## Scenario 8: Watch the remote checks after authorization

Run this command only after the orchestrator authorizes publication (T-PR).

```powershell
gh pr checks <number> --watch
```

Expected result: each required check reports `pass` on the latest commit.
