# Quickstart: Test quality: repair remaining missing_fm_http_4xx findings

Run each scenario from the repository root in the implementing environment. Use the Python 3.15 environment from `requirements-dev.txt`. The commands below use PowerShell. Use the record folder `specs\numbered\0\0\0\4\1\4\4\2\2747-test-quality-fm-http-4xx\` for the record paths.

## Scenario 1: Preflight guard (T002)

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

Expected result: one test passes. The output reports four inputs read and validated.

## Scenario 2: Census (T003)

```powershell
test-quality-analyzer --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --report test-artifacts/2747/census-4xx.json --summary test-artifacts/2747/census-4xx.md --log-level ERROR
```

Expected result: both files exist under `test-artifacts/2747/`. The JSON report holds the keys `findings` and `stale_baseline_entries`.

## Scenario 3: Count the 4xx rows (T004)

Count the 4xx findings:

```powershell
Get-Content -Raw test-artifacts\2747\census-4xx.json | ConvertFrom-Json | Select-Object -ExpandProperty findings | Where-Object rule_id -eq 'missing_fm_http_4xx' | Measure-Object | Select-Object -ExpandProperty Count
```

Count the stale 4xx entries:

```powershell
Get-Content -Raw test-artifacts\2747\census-4xx.json | ConvertFrom-Json | Select-Object -ExpandProperty stale_baseline_entries | Where-Object { $_ -match 'missing_fm_http_4xx' } | Measure-Object | Select-Object -ExpandProperty Count
```

Expected result: each command prints one number. Record both numbers in the Census summary of `analysis.md`.

## Scenario 4: Triage table check (T005)

```powershell
(Select-String -Path specs\numbered\0\0\0\4\1\4\4\2\2747-test-quality-fm-http-4xx\analysis.md -Pattern '^\| \d+ \|').Count
```

Expected result: the number equals 38 plus each census finding that has no baseline entry.

## Scenario 5: Pin and census after the upstream release (T009 and T010)

Show the pin line:

```powershell
Select-String -Path requirements-dev.txt -Pattern '^misthelper-devtools'
```

Expected result: the line names the released commit. Then rerun Scenario 2 with the output names `census-after.json` and `census-after.md`. Then run the gate:

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Expected result: the output reports zero new findings and zero parse errors.

## Scenario 6: Write the baseline and restore non-4xx entries (T012)

```powershell
test-quality-analyzer --write-baseline --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Count the added entries (expected result: zero):

```powershell
git diff -U0 -- .github/test-quality-baseline.json | Select-String -Pattern '^\+\s+"rule_id":' | Measure-Object | Select-Object -ExpandProperty Count
```

Count the removed entries by rule (expected result: only `missing_fm_http_4xx` rows, or restored rows for other rules):

```powershell
git diff -U0 -- .github/test-quality-baseline.json | Select-String -Pattern '^-\s+"rule_id":' | ForEach-Object { $_.Line.Trim() } | Group-Object | Select-Object Count, Name
```

Restore each removed non-4xx entry with the `edit` tool. Rerun the count. The removed rows for other rules must read zero.

Caution: `--write-baseline` removes stale entries for every rule. A restore step is required before the commit.

## Scenario 7: Per-file gates (T013)

Run each command for each changed test module and each record file. Replace `<changed file>` with the path:

```powershell
python -m ruff check <changed file>
python -m black --check <changed file>
python -m py_compile <changed file>
python -m pytest <changed file> -q
symbol-diff --base origin/main <changed file>
python -m mypy $MYPY_PATHS --config-file pyproject.toml
Select-String -Path <changed file> -Pattern 'opt-in|noqa|nosec|type: ignore'
```

Read `MYPY_PATHS` from `.github/workflows/ci.yml` before the mypy command.

Expected results:

- Ruff prints `All checks passed`.
- Black prints `would be left unchanged`.
- py_compile prints no output.
- pytest reports every test as passed.
- symbol-diff prints `no module-level name changed` and exits with zero.
- mypy prints `Success`.
- The marker search returns no match.

For each record file, run the STE check:

```powershell
ste-linter --config .ste-linter.toml --min-score 80 <record file>
```

Expected result: each file scores 80 or above.

## Scenario 8: Repository gates (T-LOCAL-GATES)

Commit the intended files first. Then run the changed-scope gate and the full gate:

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
git diff --check
```

Expected results: both analyzer gates print zero new findings. `git diff --check` exits with zero.

## Scenario 9: Mutation proof for a family F1 test (T011)

Run the new test on unmodified code:

```powershell
python -m pytest <test module> -q -k <new test name>
```

Expected result: the test passes.

Then run a script from `test-artifacts/2747/` that patches the status guard in memory and runs the same test. Expected result: the test fails at the refusal assertion. The script is not committed.

## Scenario 10: Remote checks (T-REMOTE-CI)

```powershell
gh pr checks <number> -R jmorrison-juniper/MistHelper --watch
```

Expected result: each required check passes on the head commit.
