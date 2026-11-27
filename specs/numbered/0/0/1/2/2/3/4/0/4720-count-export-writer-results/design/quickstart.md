# Quickstart: Count export write results

This guide gives the exact steps to reproduce issue #4720 and the exact commands that verify the fix. No live Mist call is needed. Menus 235 to 237 need a live credential, so the tests cover them with mocks.

## Prerequisites

1. Fetch the remote main branch.

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" fetch --no-tags origin main
```

2. Create a worktree for the branch. Do not use the Bash branch hook.

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" worktree add "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-fix-4720" -b fix/4720-count-export-writer-results origin/main
```

3. Set the working folder to the worktree. Install Python 3.15.2, bootstrap the environment, and activate it.

```powershell
Set-Location "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-fix-4720"
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

The bootstrap command and the Python version appear in `.github/copilot-instructions.md` (research rows 39 and 28).

## Scenario 1: Reproduce the defect before the fix

The issue reproduction steps map to the regression class. Step 1 mocks one row from the count operation. Step 2 mocks the writer result. Step 3 runs the scope entry points, which call `_run`. Step 4 checks for the success notice. Step 5 repeats the `True` and empty controls.

Run the regression class on unchanged source.

```powershell
python -m pytest tests/unit/export/test_count_exporter_workflows.py -k CountWriteOutcomes -q
```

Expected result: `7 failed, 5 passed`.

- Failing: the `False` and `None` cases for organization, site, and MSP (six cases), and the logging-order case.
- Passing: the `True` cases for organization, site, and MSP (three cases), the empty-response case, and the raised-error case.

## Scenario 2: Verify the fix

Run the same command after T002 changes `_persist`.

```powershell
python -m pytest tests/unit/export/test_count_exporter_workflows.py -k CountWriteOutcomes -q
```

Expected result: `12 passed`.

## Scenario 3: Verify the existing count tests and the contract guard

```powershell
python -m pytest tests/unit/export/test_count_exporter.py tests/contract/test_export_api_function_names.py -q
```

Expected result: all tests pass, with no edit to either file.

## Scenario 4: Verify the changelog fragment

```powershell
python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q
```

Expected result: all tests pass.

## Scenario 5: Grade the operator guide

```powershell
.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation/operator-guide.md
```

Expected result: the score is 80 or above.

## Scenario 6: Run the symbol gate

Fetch `origin/main` in the worktree, then run the gate.

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-fix-4720" fetch --no-tags origin main
symbol-diff --base origin/main src/operations/exporting/export/count_exporter.py
```

Expected result: `no module-level name changed`, with exit code 0.

## Scenario 7: Run the test-quality ratchet

Run this after the local commit of T001 to T005, and before the push.

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected result: the preflight passes. The gate prints `gate: 0 new findings vs baseline`. Do not rewrite the baseline to hide a finding.

## Scenario 8: Run the applicable local gates

Each row names one gate from the local gates table in `.github/copilot-instructions.md`, with the changed-file scope.

| Gate | Command | Expected result |
| - | - | - |
| Compile | `python -m py_compile src/operations/exporting/export/count_exporter.py` | No output |
| Lint | `python -m ruff check .` | `All checks passed` |
| Format | `python -m black --check .` | No file needs a change |
| Types | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | `Success` |
| Tests | `python -m pytest tests/unit/export/test_count_exporter_workflows.py tests/unit/export/test_count_exporter.py -q` | All tests pass |
| Coverage | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | Coverage 80 percent or above |
| Complexity | `radon cc src/operations/exporting/export -j \| complexity-gate --max 10` | No block above cyclomatic complexity 10 |
| Security lint | `bandit -c pyproject.toml -r src/operations/exporting/export -q` | No finding |
| Code quality | `pylint src/ --fail-under=9.5` | Score 9.5 or above |
| Dead code | `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | No finding |
| Docstrings | `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` | No violation, and coverage 90 percent or above |
| Menu reference | `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map` | `git status --porcelain` lists no generated file |
| Symbols | Scenario 6 | `no module-level name changed` |
| STE | Scenario 5, and `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 src/operations/exporting/export/count_exporter.py tests/unit/export/test_count_exporter_workflows.py` | Each file scores 80 or above |
| Dependency audit | Not applicable. No dependency file changes. | Not run |
| Safe sweep | Not applicable. Menus 235 to 237 are `interactive_safe`, and the safe sweep skips them. | Not run |
| Ops portal and ops platform | Not applicable. No file changes under `ops-portal/` or `mist-ops-platform/`. | Not run |

## Scenario 9: Check the record route

Run this in PowerShell 7 from the worktree root, before T-PR.

```powershell
. '.specify\scripts\powershell\spec-route.ps1'
Resolve-SpecFeaturePath -SpecsDir 'specs' -BranchName '4720-count-export-writer-results' -Number 4720
```

Expected result: `specs\numbered\0\0\1\2\2\3\4\0\4720-count-export-writer-results`.

## Scenario 10: Check the file set and the child counts

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-fix-4720" diff --name-status origin/main
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-fix-4720" diff --name-status origin/main -- tests/unit/export
(Get-ChildItem -LiteralPath "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-fix-4720\specs\numbered\0\0\1\2\2\3" -Force).Count
```

Expected results:

- The first command lists only the paths in `plan.md`. It lists no `README.md`, `MistHelper.py`, or `data_exporter.py` line.
- The second command lists only `M tests/unit/export/test_count_exporter_workflows.py`.
- The third command prints `4`. The children are 0, 2, 3, and 4.

## Scenario 11: Review the operator output

Work through `design/checklists/operator-output.md` after T002. Each item states the evidence to record.

## Cleanup after the merge

Remove the worktree and the local branch only after the squash merge lands on `main`.

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" worktree remove "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-fix-4720"
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" branch -D fix/4720-count-export-writer-results
```
