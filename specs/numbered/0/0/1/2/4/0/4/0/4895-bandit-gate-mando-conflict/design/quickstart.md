# Quickstart: Bandit Gate Dependency Conflict

Use these commands to reproduce the failure and to check the fix. Each GitHub command is read-only. Run the two environment lines in the same PowerShell session before the first GitHub command.

## Setup

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

Warning: never print `GH_TOKEN`. A printed token exposes the account to anyone who reads the output.

## Reproduce the Failure

### Q1. Issue facts

```powershell
gh issue view 4895 -R jmorrison-juniper/MistHelper --json number,title,state,labels
```

Expected: `state` is `OPEN`. The labels are `bug`, `ci`, and `quality-gate`.

### Q2. Pull request facts

```powershell
gh pr view 4888 -R jmorrison-juniper/MistHelper --json state,headRefOid,files
```

Expected: `state` is `OPEN`. `headRefOid` is `e86098cdc2b189d217805b3b4060ef609cbc37af`. The only changed file is `requirements-dev.txt`.

### Q3. Conflict lines in the failed log

```powershell
gh run view 45064243269 -R jmorrison-juniper/MistHelper --job 137336719159 --log-failed | Select-String -Pattern 'ResolutionImpossible|Cannot install|mando==0\.8\.2'
```

Expected: a line that reads `ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2 because these package versions have conflicting dependencies.` Also expected: a line that reads `ERROR: ResolutionImpossible`.

### Q4. Step conclusions of the Bandit job

```powershell
$run = gh run view 45064243269 -R jmorrison-juniper/MistHelper --json jobs | ConvertFrom-Json
$job = $run.jobs | Where-Object { $_.databaseId -eq 137336719159 }
$job.steps | Select-Object number, name, conclusion
```

Expected: step 5, `Run pip install -r requirements-dev.txt`, has the conclusion `failure`. Steps 6 and 7 have the conclusion `skipped`.

### Q5. Pins on main

```powershell
gh api -H "Accept: application/vnd.github.raw+json" "repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=main" | Select-String -Pattern '^mando==|^radon=='
```

Expected: the lines `mando==0.7.1` and `radon==6.0.1`.

### Q6. Pins on the PR head

```powershell
gh api -H "Accept: application/vnd.github.raw+json" "repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=e86098cdc2b189d217805b3b4060ef609cbc37af" | Select-String -Pattern '^mando==|^radon=='
```

Expected: the lines `mando==0.8.2` and `radon==6.0.1`.

### Q7. Constraint in the installed package

Run this command from the repository root. The relative path needs that working directory.

```powershell
Select-String -LiteralPath '.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA' -Pattern '^Requires-Dist: mando'
```

Expected: `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA:31:Requires-Dist: mando (<0.8,>=0.6)`.

### Q8. Constraint upstream

```powershell
(Invoke-RestMethod -Uri 'https://pypi.org/pypi/radon/6.0.1/json').info.requires_dist
```

Expected: a list that includes `mando (<0.8,>=0.6)`.

### Q9. Count of failed jobs

```powershell
$run = gh run view 45064243269 -R jmorrison-juniper/MistHelper --json jobs | ConvertFrom-Json
$run.jobs | Where-Object { $_.conclusion -eq 'failure' } | Measure-Object | Select-Object -ExpandProperty Count
```

Expected: the count 28.

### Q10. Health of main

```powershell
gh run view 45774119357 -R jmorrison-juniper/MistHelper --json conclusion,headSha
```

Expected: `conclusion` is `success`. `headSha` is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

### Q11. The cited commit

```powershell
gh api repos/jmorrison-juniper/MistHelper/commits/5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 --jq .commit.message
```

Expected: `Merge e86098cdc2b189d217805b3b4060ef609cbc37af into 00d9a16e998b0cb5e10b6ed77da0fa909670d64f`.

## After the Fix

Run these commands from the worktree root, with the `.venv` of that worktree.

### Q12. Guard cases for the radon boundary

```powershell
python -m pytest tests/guardrails/test_dependency_declaration_parity.py
```

Expected: every test passes. The list includes `test_radon_boundary_rejects_mando_0_8_2` and `test_pinned_mando_satisfies_installed_radon`.

### Q13. Dependabot policy snapshot

```powershell
python -m pytest tests/guardrails/test_pr_title_workflow.py
```

Expected: `TestDependabotPolicy::test_complete_policy` passes.

### Q14. Proof that the real-file case fails on the PR head

Copy the repository to a scratch folder outside the repository tree. In the copy only, set line 179 of `requirements-dev.txt` to `mando==0.8.2`. Then run the real-file case in the copy.

```powershell
python -m pytest tests/guardrails/test_dependency_declaration_parity.py -k pinned_mando
```

Expected: the test fails. The failure message names `mando 0.8.2` and the radon requirement `mando (<0.8,>=0.6)`. Delete the scratch copy after the run.

### Q15. Bandit gate locally

```powershell
bandit -c pyproject.toml -r . -q
```

Expected: no output and exit code 0.

### Q16. Style gate for the record

```powershell
$record = 'specs\numbered\0\0\1\2\4\0\4\0\4895-bandit-gate-mando-conflict'
ste-linter --config .ste-linter.toml --min-score 80 "$record\spec.md" "$record\plan.md" "$record\tasks.md" "$record\analysis.md" "$record\design\research.md" "$record\design\data-model.md" "$record\design\quickstart.md" "$record\design\checklists\requirements.md"
```

Expected: each file scores 80 or above.

### Q17. Pull request state after the merge

```powershell
gh pr view 4888 -R jmorrison-juniper/MistHelper --json state
```

Expected: `state` is `CLOSED` after T-MERGE.
