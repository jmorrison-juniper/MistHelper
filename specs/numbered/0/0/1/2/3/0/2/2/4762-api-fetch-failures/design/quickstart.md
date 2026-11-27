# Quickstart: API Fetch Failures

Run every command from the root of the worktree for branch `fix/4762-api-fetch-failures`. Use the `.venv` of that worktree. Section "Language and environment" of `.github/copilot-instructions.md` states the setup. `documentation/development-setup.md` lines 32 to 40 match the steps below.

## Setup

1. Create the worktree from `origin/main`. Section "Branch" of `AGENTS.md` states the rule for worktrees.
2. Install Python 3.15.2 and create the environment:

```powershell
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

## Reproduce the Defect Before the Change

These commands show the failing cases before any source change.

1. Run the unit tests for the fetch helpers:

```powershell
python -m pytest tests/unit/api/test_api_core_fetch_utils.py
```

Expected result: cases U-5 to U-11 fail. The helpers return an empty list or a partial list. They do not raise.

2. Run the integration tests for the callers:

```powershell
python -m pytest tests/integration/export/test_api_fetch_enrichment.py
```

Expected result: each case that uses `APICoreFetchUtils.APIFetchError` fails with `AttributeError`. Each case that asserts a warning fails.

## Verify Each Implementation Task

Run the matching command after each task. Each command must print `no module-level name changed` and exit with code 0.

```powershell
symbol-diff --base origin/main src/mist/access/api/api_core_fetch_utils.py
symbol-diff --base origin/main src/mist/intelligence/reports/switch_scorecard/site_lookup.py
symbol-diff --base origin/main src/mist/intelligence/reports/offline_device_reporter.py
symbol-diff --base origin/main src/operations/exporting/export/site_device_exporter.py
symbol-diff --base origin/main src/operations/exporting/export/sites_by_ap_model_exporter.py
symbol-diff --base origin/main src/operations/exporting/export/org_inventory_exporter.py
symbol-diff --base origin/main src/operations/exporting/export/msp_inventory_exporter.py
```

Run the tests for the new release note after task T010:

```powershell
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
```

## Local Gates (T-LOCAL-GATES)

Each gate below comes from the local gates table of `.github/copilot-instructions.md` (row R112). Each command names the changed files or the package of the changed files.

| Gate | Command | Expected result |
| - | - | - |
| Lint | `python -m ruff check .` | `All checks passed` |
| Format | `python -m black --check .` | No file needs a change |
| Types | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | `Success` |
| Tests | `python -m pytest tests/unit/api/test_api_core_fetch_utils.py` and `python -m pytest tests/integration/export/test_api_fetch_enrichment.py` | All tests pass |
| Tests for callers | `python -m pytest tests/unit/export/test_site_device_exporter.py tests/unit/export/test_sites_by_ap_model_exporter.py tests/unit/export/test_msp_inventory_exporter.py tests/unit/test_org_inventory_exporter_helpers.py tests/unit/ui/test_prompt_utils.py tests/unit/marvis/mist/intelligence/reports/device_health/test_offline_device_reporter.py` | All tests pass |
| Full tests | `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal` and `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal` | One summary line for each shard |
| Coverage | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | 80 percent or above |
| Test quality, preflight | `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` | The inputs are readable |
| Test quality, changed files | The command in the next subsection, after the local commit | `gate: 0 new findings vs baseline` |
| Complexity | `radon cc src/mist/access/api -j \| complexity-gate --max 10`, then the same command for `src/operations/exporting/export` and `src/mist/intelligence/reports` | No block above cyclomatic complexity 10 |
| Security lint | `bandit -c pyproject.toml -r src/mist/access/api -q`, then the same command for `src/operations/exporting/export` and `src/mist/intelligence/reports` | No finding |
| Dependency audit | Not applicable | No dependency file changes. `requirements.txt` keeps `mistapi==0.64.1` (row R66). |
| Code quality | `pylint src/ --fail-under=9.5` | Score 9.5 or above |
| Dead code | `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | No finding |
| Docstrings | `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` | No violation, and coverage 90 percent or above |
| Menu reference | Not applicable | No menu is added or changed |
| Symbols | The seven commands in the previous section | `no module-level name changed`, exit code 0 |
| STE | Not applicable | The changed files are not in the file list of `.github/workflows/ste-lint.yml` (row R123) |
| Ops portal and ops platform | Not applicable | No file under `ops-portal/` or `mist-ops-platform/` changes |
| Safe sweep | `python MistHelper.py --test` | Each safe operation completes. Without a token, the Mist checks skip. |
| Compile | Not applicable as a separate command | The table row names `MistHelper.py` only. The pytest runs import each changed module. |

### Test Quality Command

Run this command after the local commit and before the push. Section "Test quality ratchet" of `.github/copilot-instructions.md` (row R113 cites the table row) states the procedure.

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

## Pull Request (T-PR)

1. Write the commit message in this form. Include the Co-authored-by trailer unless the user asks otherwise.

```text
fix(api): raise APIFetchError for failed site and inventory reads

Closes #4762

Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>
```

2. Open the pull request with the title `fix(api): raise APIFetchError for failed site and inventory reads`. The body contains `Closes #4762`. The body lists each local gate and its result.

## Remote CI (T-REMOTE-CI)

1. Run the full-suite test-quality command. It omits the changed-from option:

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

2. Run `gh pr checks` with the `--watch` option and the pull request number from T-PR. Wait for CodeQL before you add the `auto-merge` label. Section "Pull request" of `AGENTS.md` states the rule.

## Merge and Post-Merge Checks (T-MERGE)

1. After the orchestrator authorizes the merge, squash-merge the pull request.
2. Run the unit test module on the merged `main` checkout:

```powershell
python -m pytest tests/unit/api/test_api_core_fetch_utils.py
```

3. The orchestrator checks the container build. The build runs on the merged revision (constitution Principle IV, row R117). The image revision label must equal the merge commit SHA. The orchestrator then runs the deployment and the health check.

## Cleanup

- These commands start no container. No container, volume, or network needs removal.
- After the merge, remove the worktree and the branch. Section "Merge" of `AGENTS.md` states the rule.
