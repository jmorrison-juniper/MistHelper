# Quickstart: Exported cell values stay out of DEBUG logs

Run each command from the root of the worktree. Use the PowerShell shell of the repository. Each command names its expected result.

## Prerequisites

1. Confirm that pull request #4813 merged. Expected: `"state":"MERGED"`.

```text
gh pr view 4813 -R jmorrison-juniper/MistHelper --json state,mergedAt
```

2. Create the worktree and the branch from `main`.

```text
git worktree add ..\MistHelper-fix-4775 -b fix/4775-csv-exporter-aggregate-logging main
```

3. Create the environment in the new worktree.

```text
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

## Reproduce the leak before the fix

1. Run the shared writer absence tests. Expected: two failures. The assertion output shows a marker value in the captured DEBUG text.

```text
python -m pytest tests/unit/export/test_data_exporter.py -q -k "no_cell_values or count_only"
```

2. Run the device, site, and parse-failure absence tests. Expected: three failures.

```text
python -m pytest tests/unit/test_org_inventory_exporter_helpers.py tests/unit/export/test_sites_by_ap_model_exporter.py tests/unit/export/test_site_device_exporter.py -q -k "no_device_values or error_type_only or no_inventory_values"
```

## Verify the fix

1. Run the four targeted test files. Expected: every test passes.

```text
python -m pytest tests/unit/export/test_data_exporter.py tests/unit/test_org_inventory_exporter_helpers.py tests/unit/export/test_sites_by_ap_model_exporter.py tests/unit/export/test_site_device_exporter.py -q
```

2. Search the four exporter files for the removed patterns. Expected: no output.

```text
Select-String -Path src\operations\exporting\export\data_exporter.py,src\operations\exporting\export\org_inventory_exporter.py,src\operations\exporting\export\sites_by_ap_model_exporter.py,src\operations\exporting\export\site_device_exporter.py -Pattern 'get_string|Row %s written|Enriched device|split address .%s.'
```

3. List the changed paths against `main`. Expected: the ten paths in `plan.md`.

```text
git diff --name-only origin/main
```

## Local gates

Each gate applies to the changed files. Run each gate after the commit. The expected result follows each command.

1. Compile. Expected: no output.

```text
python -m py_compile MistHelper.py
python -m py_compile src\operations\exporting\export\data_exporter.py src\operations\exporting\export\org_inventory_exporter.py src\operations\exporting\export\sites_by_ap_model_exporter.py src\operations\exporting\export\site_device_exporter.py
```

2. Lint. Expected: `All checks passed`.

```text
python -m ruff check .
```

3. Format. Expected: no file needs a change.

```text
python -m black --check .
```

4. Types. Expected: `Success`.

```text
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
```

5. Targeted tests. Expected: every test passes. The command is the one in "Verify the fix", step 1.

6. Full tests. Expected: one summary line for each shard.

```text
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

7. Safe sweep. Expected: each safe operation completes. The Mist checks skip with a credential reason.

```text
python MistHelper.py --test
```

8. Coverage. Expected: 80 percent or above.

```text
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
```

9. Test quality preflight. Expected: the live guide tests pass.

```text
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

10. Test quality analyzer. Run it after the commit. Expected: `gate: 0 new findings vs baseline`.

```text
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

11. Complexity. Expected: no block above complexity 10.

```text
radon cc src/operations/exporting/export -j | complexity-gate --max 10
```

12. Security lint. Expected: no finding.

```text
bandit -c pyproject.toml -r src/operations/exporting/export -q
```

13. Code quality. Expected: score 9.5 or above.

```text
pylint src/ --fail-under=9.5
```

14. Dead code. Expected: no finding.

```text
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
```

15. Docstrings. Expected: no violation, and coverage of 90 percent or above.

```text
pydocstyle src/ wsgi.py web_portal
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
```

16. Menu reference. Expected: no generated file changes after the run.

```text
python scripts/generate_menu_wiki.py
python -m scripts.menu_api_map
git status --short
```

17. Symbols. Run the command for each changed Python file. Expected: no unintended module-level change. The two PrettyTable removals in `org_inventory_exporter.py` and `site_device_exporter.py` are intended (D-15).

```text
symbol-diff --base origin/main src\operations\exporting\export\data_exporter.py
```

18. STE. Expected: each file scores 80 or above.

```text
.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\security.md changelog.d\issue-4775-csv-exporter-aggregate-logging.md
Get-ChildItem -Recurse -Filter *.md specs\numbered\0\0\1\2\3\1\0\0\4775-csv-exporter-aggregate-logging | ForEach-Object { .venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 $_.FullName }
```

19. Guardrails. Expected: no failure. The changelog policy guard and the process folder baseline read the changed folders.

```text
python -m pytest tests/guardrails -q
```

20. Dependency audit, Ops portal, and Ops platform. Not applicable. No requirement file changes, and no file under `ops-portal/` or `mist-ops-platform/` changes.
