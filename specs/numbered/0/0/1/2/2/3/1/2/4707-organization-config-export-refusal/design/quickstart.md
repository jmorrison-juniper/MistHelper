# Quickstart: Organization Config Export Refusal

This guide proves the fix from the repository root of the implementation worktree. It uses the Python 3.15 environment of the repository. Every scenario runs offline with mocked sessions. No scenario needs a Mist credential or a live request.

## Prerequisites

- Precondition P-1 holds. Issue #4707 holds an explicit handover comment for the manager file.
- The branch `fix/4707-organization-config-export-refusal` is checked out in its own worktree.
- The `.venv` environment of the worktree is active. A new worktree needs `uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py` first.

## Scenario 1: Reproduce the defect with the red export tests

Run the two export tests that describe the issue scenario. Each test mocks six refused responses or one refused follow-up page.

```powershell
python -m pytest tests/unit/org/test_org_config_migration_workflow.py -q -k "test_a_partial_fetch_saves_no_bundle or test_a_partial_fetch_never_logs_completion"
```

Expected before T006: both tests fail. The current code saves one bundle with empty lists and logs `Menu 58: Export complete.`

Expected after T006: both tests pass. No bundle is saved, and no completion message is logged.

## Scenario 2: Red reader tests for the status and payload rules

```powershell
python -m pytest tests/unit/org/test_org_config_migration_conflicts.py -q -k TestConfigFetchReader
```

Expected before T005: the tests fail, because `ConfigFetchReader` does not exist.

Expected after T005: all ten reader tests pass. The status matrix verifies statuses 200 and 299, and it refuses statuses 199, 300, 403, and 503.

## Scenario 3: Red import tests for the bundle and destination gates

```powershell
python -m pytest tests/unit/org/test_org_config_migration_workflow.py -q -k "test_a_legacy_bundle_is_refused or test_an_unverified_destination_stops_before_any_create or test_a_refused_bundle_stops_before_the_prompt"
```

Expected before T007: the tests fail. The current import accepts the legacy bundle and calls the create function.

Expected after T007: each test passes. No create call occurs for a legacy bundle or an unverified destination.

## Scenario 4: Verify the SDK boundary

```powershell
python -m pytest tests/unit/org/test_org_config_migration_conflicts.py -q -k "test_each_list_call_uses_the_documented_path or test_the_sdk_paging_helper_hides_a_refused_body"
python -m pytest tests/integration/test_mistapi_sdk_compatibility.py -q
```

Expected: the endpoint parity test passes for all six list functions. The paging helper test shows that the SDK returns an empty list for a refused body. The guard test reports unresolved call sites of 10 or fewer and unverifiable call sites of 366 or fewer.

## Scenario 5: Run the affected folder

```powershell
python -m pytest tests/unit/org -q
```

Expected: every test in the folder passes. The organization name tests (`TestGetOrgName`) and the create-path tests (`TestCreateWithoutIdentifier`) pass without edits.

## Scenario 6: Safe sweep without credentials

```powershell
python MistHelper.py --test
```

Expected: each `safe` operation completes. Without `MIST_APITOKEN` or `MIST_API_TOKEN`, the Mist API checks skip with a credential reason. Menu 58 is in the `safe` category (RC-27).

## Verification commands

These commands match the Local gates table in `.github/copilot-instructions.md`. Run each gate that applies to the changed files.

```powershell
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
python -m pytest tests/unit/org/test_org_config_migration_conflicts.py tests/unit/org/test_org_config_migration_workflow.py
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
radon cc src/mist/resources/org -j | complexity-gate --max 10
bandit -c pyproject.toml -r src/mist/resources/org -q
pylint src/ --fail-under=9.5
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
pydocstyle src/ wsgi.py web_portal
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
symbol-diff --base origin/main src/mist/resources/org/org_config_migration_manager.py
ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4707-organization-config-export-refusal.md
```

Expected results: `All checks passed` for Lint, no changed file for Format, `Success` for Types, zero failures for each test command, a score of 9.5 or above for Pylint, zero findings for Vulture at confidence 70, zero violations for pydocstyle, interrogate coverage of 90 percent or above, no lost module-level name for Symbols, and a score of 80 or above for the STE gate.
