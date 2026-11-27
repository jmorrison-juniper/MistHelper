# Quickstart: Dependabot mando pin for the dependency_lock job

## Prerequisites

- Windows PowerShell in the repository root.
- The GitHub CLI `gh` is installed and signed in to the account named by `COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper`.
- Run the two environment lines before each `gh` command in this file.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## Scenario 1: Read the failed step and the resolver error (read-only)

This scenario reproduces the failure from the CI log. It runs one GET request.

```powershell
gh run view 45064243269 -R jmorrison-juniper/MistHelper --job 137336719111 --log-failed | Select-String -Pattern 'ResolutionImpossible|conflicting dependencies'
```

Expected output: a line that contains `ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2`, and a line that contains `ERROR: ResolutionImpossible`.

## Scenario 2: Read the job conclusions (read-only)

```powershell
gh api repos/jmorrison-juniper/MistHelper/actions/jobs/137336719111 --jq .conclusion
gh api repos/jmorrison-juniper/MistHelper/actions/jobs/139753527647 --jq .conclusion
```

Expected output: `failure` on the first line, and `success` on the second line.

## Scenario 3: Read the files of pull request #4888 (read-only)

```powershell
gh pr view 4888 -R jmorrison-juniper/MistHelper --json files --jq '.files[].path'
```

Expected output: `requirements-dev.txt`.

## Scenario 4: Read the radon constraint from the local environment

```powershell
Select-String -LiteralPath '.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA' -Pattern '^Requires-Dist: mando'
```

Expected output: line 31, `Requires-Dist: mando (<0.8,>=0.6)`.

## Scenario 5: Read the pins on main (read-only)

```powershell
gh api "repos/jmorrison-juniper/MistHelper/git/blobs/9a528bfe03a10f7bc903f5768ef26de765bbff43" --jq .size
```

Expected output: `9526`, the byte size of `requirements-dev.txt` on `main`. Decode the `content` field to read the pin lines. Expected: `mando==0.7.1` at line 179 and `radon==6.0.1` at line 365.

## Scenario 6: Run the guards in the implementation phase

Run these commands from the fix worktree after T003 to T007.

```powershell
python -m pytest tests/guardrails/test_pr_title_workflow.py
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
python -m pytest tests/guardrails/test_dependency_lock_file.py tests/guardrails/test_dependency_export.py tests/guardrails/test_dependency_lock_workflow.py
```

Expected output: each command reports that all selected tests pass.

## Scenario 7: Check the merged state (after the merge)

```powershell
gh pr view 4888 -R jmorrison-juniper/MistHelper --json state --jq .state
```

Expected output: `CLOSED`. Run this check only after the orchestrator authorizes the closure.
