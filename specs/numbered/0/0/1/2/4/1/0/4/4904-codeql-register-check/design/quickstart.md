# Quickstart: CodeQL register check fails on pull request 4888

Run each command from the repository root, unless a step says otherwise. Each step names its expected result.

## Prerequisites

- GitHub CLI authenticated for `jmorrison-juniper/MistHelper`.
- The Python environment in `.venv` of the repository.

## Step 1: Set the GitHub environment

Set these variables before each `gh` command.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## Step 2: Read the failing log

This command reads the log only.

```powershell
gh run view 45064243269 -R jmorrison-juniper/MistHelper --job 137336719141 --log | Select-String -Pattern 'ResolutionImpossible|radon 6.0.1 depends on mando'
```

Expected: two matching lines. One line reads `radon 6.0.1 depends on mando<0.8 and >=0.6`.

## Step 3: Reproduce the rule without installing

The `--dry-run` option resolves the packages and installs none of them.

```powershell
python -m pip install --dry-run "mando==0.8.2" "radon==6.0.1"
```

Expected: pip prints `ResolutionImpossible` and names `radon 6.0.1 depends on mando<0.8`.

## Step 4: Read the local radon requirement

```powershell
Select-String -LiteralPath ".venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA" -Pattern '^Requires-Dist: mando'
```

Expected: one line, `Requires-Dist: mando (<0.8,>=0.6)`.

## Step 5: Confirm the pinned blob on main

```powershell
gh api "repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=main" --jq .sha
```

Expected: `9a528bfe03a10f7bc903f5768ef26de765bbff43`.

## Step 6: Verify the change after implementation

```powershell
python -m pytest tests/guardrails/test_dependency_lock_file.py
python -m pytest tests/guardrails/test_pr_title_workflow.py
python -m pytest tests/guardrails/test_codeql_register_gate.py
python -m pytest tests/guardrails/test_dependency_export.py
```

Expected: each command reports that all tests passed. The lock guard prints the examined pin count and zero defects.

## Step 7: Check the pull requests

```powershell
gh pr view 4888 -R jmorrison-juniper/MistHelper --json state,mergedAt
gh pr list -R jmorrison-juniper/MistHelper --state open --search "mando in:title" --json number,title
```

Expected after the close: state `CLOSED` and `mergedAt` null. Expected after seven days: no open pull request for a `mando` minor or major update.
