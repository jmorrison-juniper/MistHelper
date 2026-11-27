# Quickstart: Operator Guide Operation Count

This page gives the exact steps to reproduce the stale count, to prove the guard, and to run each local gate for this change. Run each command from the root of the worktree for `docs/4915-operator-guide-count`.

## Prerequisites

1. Create the worktree for `docs/4915-operator-guide-count` from `main`.
2. Bootstrap the environment: `uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py` (R-54, R-55).
3. Activate the environment: `.venv\Scripts\Activate.ps1`.

## Scenario 1: Reproduce the stale count (read only)

```powershell
Select-String -Path documentation\operator-guide.md -Pattern '303 operations'
Select-String -Path documentation\menu_reference.md -Pattern '308 actionable'
```

Expected: line 13 of the operator guide matches, and line 6 of the menu reference matches (R-01, R-03).

## Scenario 2: Red run of the guard test, before the guide edit

```powershell
python -m pytest tests\guardrails\test_destructive_menu_docs.py -q
```

Expected: one failure in `test_operator_guide_defers_the_count_to_the_menu_reference`. The failure message names `303 operations` and `numbered 1 to 304`.

## Scenario 3: Green run of the guard test, after the guide edit

Run the command from Scenario 2 again after T003.

Expected: each test in the module passes. The guard test logs the number of checked count phrases, and that number is zero.

## Scenario 4: STE gate and link check

```powershell
ste-linter --config .ste-linter.toml --min-score 80 --no-dictionary documentation\operator-guide.md changelog.d\issue-4915-operator-guide-count.md tests\guardrails\test_destructive_menu_docs.py specs\numbered\0\0\1\2\4\1\3\0\4915-operator-guide-count\spec.md specs\numbered\0\0\1\2\4\1\3\0\4915-operator-guide-count\plan.md specs\numbered\0\0\1\2\4\1\3\0\4915-operator-guide-count\tasks.md specs\numbered\0\0\1\2\4\1\3\0\4915-operator-guide-count\analysis.md specs\numbered\0\0\1\2\4\1\3\0\4915-operator-guide-count\design\research.md specs\numbered\0\0\1\2\4\1\3\0\4915-operator-guide-count\design\data-model.md specs\numbered\0\0\1\2\4\1\3\0\4915-operator-guide-count\design\quickstart.md specs\numbered\0\0\1\2\4\1\3\0\4915-operator-guide-count\design\checklists\requirements.md
markdown-link-check --exclude "documentation/wiki/**" documentation\operator-guide.md changelog.d\issue-4915-operator-guide-count.md
```

Expected: each file scores 80 or above (R-48). Run the first command again without `--no-dictionary` when a user dictionary exists. The link check reports no broken link (R-50).

## Scenario 5: Release-note guard

```powershell
python -m pytest tests\guardrails\test_changelog_fragment_policy.py -q
```

Expected: all tests pass. The guard accepts the name `issue-4915-operator-guide-count.md` (R-78) and the Fixed type (R-77). CI runs this guard in its own step (R-42).

## Scenario 6: Generated pages stay unchanged (FR-004)

```powershell
python scripts\generate_menu_wiki.py
python -m scripts.menu_api_map --check
git diff --quiet -- documentation/menu_reference.md documentation/wiki/Menu-Reference.md
$LASTEXITCODE
```

Expected: the generator and the drift check finish without error. The last command prints `0`. The continuous integration job uses the same comparison (R-40, R-61). If the generator changes a page, stop and report that page (D-7).

## Scenario 7: Record placement guards (FR-008)

```powershell
python -m pytest tests\guardrails\test_process_folder_structure.py tests\guardrails\test_spec_route_contract.py -q
```

Expected: all tests pass. The specs structure guard (R-79) and the spec route contract guard (R-80) accept the record at the route.

## Scenario 8: Neighboring guards that read the operator guide (FR-006)

```powershell
python -m pytest tests\guardrails\test_hardware_shell_lock_docs.py tests\guardrails\test_metrics_gateway_container_contract.py -q
```

Expected: all tests pass. These guards read the operator guide (R-75, R-76). They read other sections, so the deleted sentence does not affect them.

If any guard in `tests\guardrails` fails, compare its name with the Windows failures that issue #4917 reports (source: GitHub issue view in `design/research.md`, Sources). A failure that issue #4917 does not list blocks the change.

## Scenario 9: Lint, format, security, and symbols

```powershell
python -m ruff check .
python -m black --check .
python -m ruff format --check tests\guardrails\test_destructive_menu_docs.py
bandit -c pyproject.toml -r tests\guardrails\test_destructive_menu_docs.py -q
symbol-diff --base origin/main tests\guardrails\test_destructive_menu_docs.py
```

Expected: ruff prints `All checks passed`. Black reports no file that needs a change. The ruff format check passes (R-51). Bandit reports no finding (R-70). The symbol gate prints `no module-level name changed` and exits with code 0 (R-67).

Mypy, pydocstyle, interrogate, and vulture do not run on the test file, because their CI scopes exclude tests (R-43, R-44, R-45, R-46).

## Scenario 10: Test quality ratchet (after the local commit, before the push)

Run the commands in the Test quality ratchet section of `.github/copilot-instructions.md` (R-69). Set `$BASE_REF` to `main`, and run each command in order. Expected: the gate prints `gate: 0 new findings vs baseline`.
