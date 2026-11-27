# Quickstart: HTTP 4xx Test-Quality Findings

## Prerequisites

- A feature worktree on branch `test/2746-http-4xx-baseline`.
- The pinned analyzer installed in `.venv`.
- A folder outside the repository for complete reports. This record uses the session files folder.

## Step 1. Confirm the pin

Run this read-only command from the repository root.

```powershell
Select-String -Path requirements-dev.txt -Pattern 'misthelper-devtools @'
```

Expected result: line 197 names commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.

## Step 2. Count the 4xx baseline entries

```powershell
(Get-Content -Raw .github\test-quality-baseline.json | ConvertFrom-Json | Where-Object { $_.rule_id -eq 'missing_fm_http_4xx' }).Count
```

Expected result before task T004: 38.

## Step 3. Run the preflight

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

Expected result: one test passes. Four inputs are read and validated.

## Step 4. Run the complete report

Write the report to a folder outside the repository.

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --report C:\Users\jmorrison\.copilot\session-state\30878eb1-80d0-451d-bd0c-0b3624089852\files\complete-report.json
```

Expected result: the output ends with `gate: 0 new findings vs baseline`.

## Step 5. List the class B entries absent from the report

Read `complete-report.json` and compare each `missing_fm_http_4xx` finding with the baseline entries. Each class B entry that has no matching finding is a removal candidate. Record each candidate in `analysis.md`.

## Step 6. Remove the confirmed candidates

Use the edit tool on `.github/test-quality-baseline.json`. Remove each confirmed candidate by its five-part key. Change no other entry.

## Step 7. Check the diff

```powershell
git diff --numstat origin/main -- .github/test-quality-baseline.json
```

Expected result: the first number is 0. The diff adds no line.

## Step 8. Repeat the count

Run the Step 2 command again.

Expected result after task T004 if the class table holds: 14. The count is 38 minus the 24 class B entries.

## Step 9. Repeat the complete report

Run the Step 4 command again. Expected result: `gate: 0 new findings vs baseline`.

## Step 10. Run the class C test modules

```powershell
python -m pytest tests/unit/refactors/test_wlanradius_timer_manager_paths.py tests/unit/org/test_org_config_migration_workflow.py
```

Expected result: all tests in both modules pass.

## Step 11. Run the guardrail tests

```powershell
python -m pytest tests/guardrails
```

Expected result: all tests pass.
