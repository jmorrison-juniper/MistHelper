# Quickstart: Split the Juniper RMA and export packages

Run each command from the repository root on a clean worktree of the feature branch. Run each command on its own line. The commands use Windows PowerShell syntax, and each command has a stated expected result.

## Step 1: Measure the ratchet guard

Run the guard and print its scope message.

```powershell
python -m pytest tests/guardrails/test_nested_package_structure.py -k ratchet -s
```

Expected before the change: `nested_package_scope: 190 directories examined, 33 violations, 236 total excess`.

Expected after the change: `nested_package_scope: 206 directories examined, 30 violations, 190 total excess`.

## Step 2: Confirm the guard passes

```powershell
python -m pytest tests/guardrails/test_nested_package_structure.py -q
```

Expected result: all tests pass. A failure names each unknown violation, each stale entry, and each increased count.

## Step 3: Search for old paths in live files (Old paths row)

This command finds each old export module path. It excludes the new packages, `data_exporter.py`, and the dated records.

```powershell
git grep -n -P "exporting[/.]export[/.](?!(org|site|wan|generic|data_exporter)\b)[a-z_0-9]+" -- . ":(exclude)specs" ":(exclude)changelog.d" ":(exclude).specify/bugs" ":(exclude)CHANGELOG.md" ":(exclude)tests/guardrails/test_performance_hook_catalog.py" ":(exclude)tests/guardrails/test_nested_package_structure.py"
```

This command finds each old Juniper RMA module path.

```powershell
git grep -n -P "exporting[/.]juniper_rma[/.](model|workflows)[/.](asset|service_request|export_rows|reference_rows|request_rows|case_reads|reference_reads|juniper_menu_support|lookup|asset_lookup)\b" -- . ":(exclude)specs" ":(exclude)changelog.d" ":(exclude).specify/bugs" ":(exclude)CHANGELOG.md"
```

Expected result: each command prints no line.

## Step 4: Search for old logger names (Action logging check)

```powershell
git grep -n -E 'getLogger\("src\.operations\.exporting\.(export|juniper_rma)\.' -- . ':(exclude)specs' ':(exclude)changelog.d'
```

Expected result: no line. Each logger uses `__name__`, so the search covers literal logger names only.

## Step 5: Import each moved module at its new path (Import smoke row)

The loop reads the table in `plan.md`, section A. For each row, it imports the new dotted path. It then confirms that the old dotted path fails to import.

```powershell
$plan = Get-Content -LiteralPath 'specs\numbered\0\0\1\1\3\1\3\3\4168-split-rma-and-export-packages\plan.md'
$rows = $plan | Where-Object { $_ -match '^\| \d+ \| src/operations/exporting/' }
foreach ($row in $rows) {
    $cells = $row.Split('|') | ForEach-Object { $_.Trim() }
    $oldName = ($cells[2] -replace '\.py$', '') -replace '/', '.'
    $newName = ($cells[3] -replace '\.py$', '') -replace '/', '.'
    $newName = $newName -replace '\.__init__$', ''
    python -c "import $newName"
    if ($LASTEXITCODE -ne 0) { "IMPORT FAILED: $newName" }
    python -c "import $oldName" 2>$null
    if ($LASTEXITCODE -eq 0) { "OLD PATH STILL IMPORTS: $oldName" }
}
```

Expected result: the loop prints no line. Each new path imports, and no old path imports.

## Step 6: Resolve each changed resolver entry

Open `src/foundation/runtime/config/source_dependency_resolver.py`. Find its resolution method, and call that method for each of the 8 changed module strings. Use the class name in each entry as the input. Record each resolved module path. Each resolved path names the new dotted path. The entry for `DataExporter` keeps `src.operations.exporting.export.data_exporter`.

## Step 7: Check symbols in each changed Python file

```powershell
symbol-diff --base origin/main src/operations/exporting/export/org/config/org_site_exporter.py
```

Run the command for each changed Python file at its new path. Expected result: `no module-level name changed` and exit code 0.

## Step 8: Run the local gates

Run each gate that applies to the changed files. Use the commands in `.github/copilot-instructions.md`, section Local gates, with these values.

- Compile: `python -m py_compile MistHelper.py`
- Lint: `python -m ruff check .` (expected result: `All checks passed`)
- Format: `python -m black --check .`
- Types: `python -m mypy $MYPY_PATHS --config-file pyproject.toml`, where `MYPY_PATHS` comes from `.github/workflows/ci.yml`
- Guard tests: `python -m pytest tests/guardrails -q`
- Move-module table: `python -m pytest tests/guardrails/test_move_module_guidance.py -q`
- Changed test files: `python -m pytest tests/unit/export tests/unit/juniper_rma tests/unit/prod_readiness tests/unit/web_portal tests/integration/export tests/e2e/web_portal -q`
- Safe sweep: `python MistHelper.py --test`
- Menu reference: `python scripts/generate_menu_wiki.py`, then `python -m scripts.menu_api_map`, each run twice
- Complexity: `radon cc src/operations/exporting -j` piped to `complexity-gate --max 10`
- Security lint: `bandit -c pyproject.toml -r src/operations/exporting -q`
- Code quality: `pylint src/ --fail-under=9.5`
- Dead code: `vulture $VULTURE_PATHS --min-confidence 70`, where `VULTURE_PATHS` comes from `.github/workflows/ci.yml`
- Docstrings: `pydocstyle $PYDOCSTYLE_PATHS` and `interrogate $INTERROGATE_PATHS --fail-under 90`, with the paths from `.github/workflows/ci.yml`
- Symbols: the command in step 7 for each changed Python file
- Full tests: the two `pytest-chunks` commands in `.github/copilot-instructions.md`, section Local gates

The gates for `ops-portal` and `mist-ops-platform` do not apply, because this change does not edit those folders. The STE gate does not apply, because no file in its list changes.
