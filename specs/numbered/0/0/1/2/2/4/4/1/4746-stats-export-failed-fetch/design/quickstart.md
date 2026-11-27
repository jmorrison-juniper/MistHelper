# Quickstart: Statistics Export Processed Count After Failed Fetch

## Prerequisites

- Windows 11 with PowerShell, in the repository root or in the worktree for the branch.
- A `.venv` that the bootstrap command created. The repository instructions give the commands (`.github/copilot-instructions.md`, lines 28 to 30):

```powershell
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

- The offline checks need no Mist API credential. The tests mock every response.

Caution: Do not start a live statistics export for this check. A live run uses Mist API quota and reads a production organization.

## Reproduction Steps from the Issue

The issue gives four reproduction steps. The offline tests in Scenario 1 follow the same steps.

1. Install a mock progress emitter. The test fixture sets `PROGRESS_EMITTER` to a mock.
2. Replace the selected Mist SDK call with a synthetic HTTP 403 or HTTP 503 response. Tests 1, 2, and 5 do this.
3. Run `device_stats()` or `vpn_peer_stats()` with the real `APIDataFetcher.execute()`. The new test module uses the real fetcher.
4. Check the fetch result, the export call, and the completion event. Each test asserts these three values.

The issue records this log output for the failure case:

```text
The cloud returned HTTP 403 for listOrgDevicesStats at org offline-org
The cloud returned HTTP 503 for searchOrgPeerPathStats at org offline-org
Expected items_processed: 0
Actual items_processed: 1
```

## Scenario 1: Reproduce the defect offline

Run the new test module before the fix.

```powershell
python -m pytest tests/unit/prod_readiness/standalone/operations/exporting/stats/test_stats_export_completion.py -q
```

Expected result before the fix:

- Tests 1, 2, 3, and 5 fail. Each one asserts processed count 0, and the code emits 1.
- Test 4 fails on the missing DEBUG record "Device stats fetch finished".
- Test 6 passes. It checks the success count of 1 for `vpn_peer_stats`.

## Scenario 2: Verify the fix offline

Run the same command after T002 lands.

```powershell
python -m pytest tests/unit/prod_readiness/standalone/operations/exporting/stats/test_stats_export_completion.py -q
```

Expected result: all six tests pass.

## Scenario 3: Menu 13 wiring test

Run the existing completion test after T003 updates the stub.

```powershell
python -m pytest tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_13_device_stats.py -q
```

Expected result: every test in the module passes. `test_emits_start_and_complete` asserts processed count 1.

## Scenario 4: Regression runs of the existing exporter and fetcher tests

These runs read the reserved file. They do not edit it.

```powershell
python -m pytest tests/unit/export/test_org_device_stats_exporter.py -q
python -m pytest tests/unit/api/test_api_data_fetcher.py -q
```

Expected result: both modules pass. The cache-hit test `test_cache_hit_returns_early` passes, so the fast-mode path emits no event (FR-007).

## Scenario 5: Changelog guard

```powershell
python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q
```

Expected result: the guard accepts the file name `issue-4746-stats-export-failed-fetch.md`.

## Scenario 6: Symbol check

```powershell
symbol-diff --base origin/main src\operations\exporting\export\org_device_stats_exporter.py
```

Expected result: `no module-level name changed`, exit code 0.

## Local Gates

The table lists each gate from the local gates table of `.github/copilot-instructions.md` (lines 57 to 76), with the command for the changed files. A row marked not applicable gives its reason.

| Gate | Command | Expected result | Status for this change |
| - | - | - | - |
| Compile | `python -m py_compile MistHelper.py` | No output | Not applicable. `MistHelper.py` is unchanged. |
| Lint | `python -m ruff check .` | `All checks passed` | Applies |
| Format | `python -m black --check .` | No file needs a change | Applies |
| Types | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | `Success` | Applies. The paths come from `MYPY_PATHS` (`ci.yml`, line 93). |
| Tests | `python -m pytest tests/unit/prod_readiness/standalone/operations/exporting/stats/test_stats_export_completion.py` and `python -m pytest tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_13_device_stats.py` | All tests pass | Applies |
| Full tests | `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal` and `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal` | One summary line for each shard | Applies |
| Safe sweep | `python MistHelper.py --test` | Each safe operation completes. Without `MIST_APITOKEN` or `MIST_API_TOKEN`, the Mist API checks skip with a credential reason. | Applies. Menus 15 and 16 are safe operations (RC-25, RC-26). |
| Coverage | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | The CI shards combine the reports and require 80 percent or above | Applies |
| Test quality | Run the preflight, then the analyzer gate, as described below | `gate: 0 new findings vs baseline` | Applies. The new test module is a new API client test module. |
| Complexity | `radon cc src\operations\exporting\export -j` piped to `complexity-gate --max 10` | No block above cyclomatic complexity 10 | Applies |
| Security lint | `bandit -c pyproject.toml -r src\operations\exporting\export -q` | No finding at any severity | Applies |
| Dependency audit | `pip-audit -r requirements.txt` | No known vulnerability | Not applicable. No dependency changes. |
| Code quality | `pylint src/ --fail-under=9.5` | Score 9.5 or above | Applies |
| Dead code | `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | No finding. The paths come from `VULTURE_PATHS` (`ci.yml`, line 101). | Applies |
| Docstrings | `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` | No violation and coverage at 90 percent or above | Applies |
| Menu reference | `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map` | No changed file after the run | Not applicable. The menu titles and the menu table do not change. |
| Symbols | `symbol-diff --base origin/main src\operations\exporting\export\org_device_stats_exporter.py` | `no module-level name changed`, exit code 0 | Applies |
| STE | `ste-linter --config .ste-linter.toml --min-score 80 changelog.d\issue-4746-stats-export-failed-fetch.md` | Score 80 or above | Applies to the new fragment. The table lists other files. |
| Ops portal | The npm commands in `ops-portal/` | Each command exits 0 | Not applicable. The change does not touch `ops-portal/`. |
| Ops platform | `pytest --cov=src --cov-fail-under=56` in `mist-ops-platform/` | At least 390 tests, coverage at 56 percent or above | Not applicable. The change does not touch `mist-ops-platform/`. |

### Test quality procedure

Commit the intended tests first. Stop if a relevant staged, unstaged, or untracked change remains. Run each command separately.

```powershell
$BASE_REF = "main"
git fetch --no-tags origin "+refs/heads/${BASE_REF}:refs/remotes/origin/${BASE_REF}"
git rev-parse --verify "origin/${BASE_REF}^{commit}"
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/$BASE_REF" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected result: the analyzer reports `gate: 0 new findings vs baseline`. Do not rewrite `.github/test-quality-baseline.json` to hide a new finding.

## Cleanup

- No container starts for this change. No volume is created.
- Test evidence stays in folders that git ignores, such as `test_quality_analyzer_output\` and `test-artifacts\`.
- After the merge, remove the worktree and delete the branch.
