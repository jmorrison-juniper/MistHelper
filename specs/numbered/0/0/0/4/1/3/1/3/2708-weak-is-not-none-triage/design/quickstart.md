# Quickstart: Test quality: triage weak_is_not_none findings

These steps reproduce the triage and run the gates for one slice. Run each command from the repository root, unless a step names another folder. Each command reads the repository. Only the slice steps change files.

## Prerequisites

1. Open PowerShell in the repository root.
2. In a new worktree, create the venv with the bootstrap command in `.github/copilot-instructions.md`. Then run `.venv\Scripts\Activate.ps1`.
3. Set the GitHub variables for each `gh` command in the same PowerShell process. The token value is never printed.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## Scenario 1: Confirm the issue

```powershell
gh issue view 2708 -R jmorrison-juniper/MistHelper --json number,title,state,labels
```

Expected result: the issue is open. The title is `Test quality: triage weak_is_not_none findings`.

## Scenario 2: Confirm the base commit and the baseline count

```powershell
gh api repos/jmorrison-juniper/MistHelper/commits/main --jq .sha
```

Expected result at record time: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

```powershell
(Get-Content -LiteralPath .github\test-quality-baseline.json -Raw | ConvertFrom-Json | Where-Object { $_.rule_id -eq 'weak_is_not_none' }).Count
```

Expected result: 84.

## Scenario 3: Confirm one finding on main

```powershell
gh api "repos/jmorrison-juniper/MistHelper/contents/tests/unit/test_csv_comparator.py?ref=main" --jq .content
```

Decode the base64 text in PowerShell with `[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($content))`. Read line 145. Expected result: `assert counters.start_time is not None`.

## Scenario 4: Run the analyzer preflight and the gate

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

Expected result: the preflight passes. It reads the required inputs.

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Expected result: the summary states the checked count. The line `gate: 0 new findings vs baseline` appears on a clean base.

## Scenario 5: Show that a repaired guard fails

Use a scratch file outside the repository. Load the test with one wrong value in memory. Expected result: the original line passes the wrong value. The repaired line fails it at the repaired line number. The scratch file is removed after the run.

## Scenario 6: Confirm that a repaired line has no weak guard

```powershell
Select-String -LiteralPath tests\unit\test_csv_comparator.py -Pattern 'is not None'
```

Expected result after the slice: no match on the repaired lines.

## Scenario 7: Run the local gates for one slice

Run each command for each changed file. Replace `<file>` with the changed path.

```powershell
python -m py_compile <file>
ruff check <file>
black --check <file>
python -m pytest <file>
bandit -c pyproject.toml -r <file> -q
symbol-diff --base origin/main <file>
```

## Scenario 8: Run the mist-ops-platform gates

Run from the `mist-ops-platform` folder. Use the path relative to that folder.

```powershell
Set-Location mist-ops-platform
python -m pytest tests/unit/mist/test_registry_validation.py
ruff check . --select F,B,E9 --ignore F401,B008,B905 --output-format=concise
Set-Location ..
```

## Scenario 9: Update the baseline and review the diff

```powershell
test-quality-analyzer --write-baseline --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
git diff --stat -- .github/test-quality-baseline.json
git diff -- .github/test-quality-baseline.json
```

Expected result: the diff removes entries only for repaired or stale lines. The diff adds no entry, except a recorded shift with the same rule, file, category, and explanation.

## Scenario 10: Run the changed-scope gate after the commit

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected result: `gate: 0 new findings vs baseline`. Run the full gate of Scenario 4 before each push.

## Scenario 11: Watch the remote checks

```powershell
gh pr checks <number> -R jmorrison-juniper/MistHelper --watch
```

Expected result: each required check passes on the final commit. The `test_quality_gate` check passes.
