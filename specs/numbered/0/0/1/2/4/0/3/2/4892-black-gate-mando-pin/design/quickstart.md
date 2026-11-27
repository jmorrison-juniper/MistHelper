# Quickstart: Reproduce and Verify Issue 4892

Run each command from the repository root unless a step says otherwise.

Warning: use read-only `gh` commands for reproduction. The reproduction steps write nothing to GitHub.

## Set the GitHub account

Run this line before each `gh` command. Each PowerShell call starts a new process.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## Reproduce the failure

1. Read the steps of the Black job in run 45064243269.

```powershell
gh run view 45064243269 -R jmorrison-juniper/MistHelper --json jobs
```

Expected: the job named `Black (format check)` lists step 5, `Run pip install -r requirements-dev.txt`, with conclusion `failure`. Step 6, `Black format check`, has conclusion `skipped` (R-52).

2. Read the failed-step log of job 137339161296 and search for the resolver error.

```powershell
gh run view --job 137339161296 -R jmorrison-juniper/MistHelper --log-failed
```

Expected: log line 585 names `mando==0.8.2` (R-53). Log line 598 holds `ResolutionImpossible` (R-54).

3. Read the pin on the pull request head.

```powershell
gh api "repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=e86098cdc2b189d217805b3b4060ef609cbc37af" --jq .content
```

Store the returned base64 text in `$base64`. Then run `[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($base64))`. Expected: line 179 is `mando==0.8.2` (R-02).

4. Read the Black job on main.

```powershell
gh run view 45774119357 -R jmorrison-juniper/MistHelper --json jobs
```

Expected: the job named `Black (format check)` has conclusion `success` (R-56).

5. Read the radon metadata. Open https://pypi.org/pypi/radon/6.0.1/json. Expected: `requires_dist` holds `mando (<0.8,>=0.6)` (R-46).

## Verify the change

Run each command after the change is in place. Expected results come from `plan.md`, section Gate Applicability.

```powershell
python -m pytest tests\guardrails\test_dependency_lock_file.py
python -m pytest tests\guardrails\test_changelog_fragment_policy.py
python -m black --check .
python -m ruff check .
python -m py_compile MistHelper.py
bandit -c pyproject.toml -r . -q
```

Expected: pytest reports all tests passed. Black reports that no file needs a change. Ruff reports `All checks passed`. py_compile prints nothing. Bandit prints no finding.

Run the STE gate on the ten record files and the fragment:

```powershell
$record = 'specs\numbered\0\0\1\2\4\0\3\2\4892-black-gate-mando-pin'
ste-linter --config .ste-linter.toml --min-score 80 "$record\spec.md" "$record\plan.md" "$record\tasks.md" "$record\analysis.md" "$record\design\research.md" "$record\design\data-model.md" "$record\design\quickstart.md" "$record\design\contracts\dependabot-mando-ignore.md" "$record\design\checklists\requirements.md" "$record\design\checklists\dependency-policy.md" changelog.d\issue-4892-black-gate-mando-pin.md
```

Expected: each file scores 80 or above.

Run the second shard of the full tests (R-69):

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

Expected: one summary line for each shard, with no failed chunk.

Run the test quality gate after the local commit. The command block at `.github\copilot-instructions.md` line 124 gives this command (R-68):

```powershell
$BASE_REF = "main"
test-quality-analyzer --gate `
  --config .github/test-quality-config.toml `
  --baseline .github/test-quality-baseline.json `
  --changed-from "origin/$BASE_REF" `
  --full-gate-path .github/workflows/ci.yml `
  --full-gate-path requirements-dev.txt
```

Run the symbol gate on the changed test module (R-67):

```powershell
symbol-diff --base origin/main tests\guardrails\test_dependency_lock_file.py
```

Expected: no module-level name is lost. Added names are listed in the pull request body.
