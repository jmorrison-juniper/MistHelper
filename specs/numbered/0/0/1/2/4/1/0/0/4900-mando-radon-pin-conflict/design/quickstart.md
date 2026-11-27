# Quickstart: Mando Pin Conflict Behind the pydocstyle Gate Failure

## Prerequisites

- Windows PowerShell with the GitHub CLI (`gh`) signed in to the account in `COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper`.
- A worktree of the repository, created from `origin/main`.
- The `.venv` of that worktree, created by the bootstrap command in the Language and environment section of `.github/copilot-instructions.md`.

## Scenario 1: Reproduce the failure from the CI logs (read-only)

Set the account for each `gh` command. Run these two lines first.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

Read the failing job log.

```powershell
gh run view 45064243269 -R jmorrison-juniper/MistHelper --job 137336719204 --log-failed
```

Expected: the log contains `Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2`, `radon 6.0.1 depends on mando<0.8 and >=0.6`, and `ResolutionImpossible`.

Read the step conclusions of the failing job.

```powershell
gh run view 45064243269 -R jmorrison-juniper/MistHelper --json jobs --jq '.jobs[] | select(.databaseId == 137336719204) | .steps[] | {name, conclusion}'
```

Expected: `Run pip install -r requirements-dev.txt` shows failure. `Check docstring conventions` shows skipped.

Read the passing pydocstyle job on main.

```powershell
gh run view 45774119357 -R jmorrison-juniper/MistHelper --json jobs --jq '.jobs[] | select(.name == "pydocstyle (docstring style)") | {name, conclusion}'
```

Expected: the job shows success.

Read the mando pin on the failed pull request head.

```powershell
gh api "repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=e86098cdc2b189d217805b3b4060ef609cbc37af" --jq ".sha"
```

Expected: `cd76ee824467ddade56342190a0d8181ee55d3d0`.

Read the radon dependency in the local environment.

```powershell
Select-String -LiteralPath .venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA -Pattern "Requires-Dist: mando"
```

Expected: the line `Requires-Dist: mando (<0.8,>=0.6)`.

## Scenario 2: Claim the issue and create the branch (implementer)

Add the status label before the branch exists.

```powershell
gh issue edit 4900 -R jmorrison-juniper/MistHelper --add-label in-progress
```

Create the worktree from the current main head.

```powershell
git worktree add ..\MistHelper-fix-4900 -b fix/4900-mando-radon-pin-conflict origin/main
```

Expected: the new worktree holds `requirements-dev.txt` with `mando==0.7.1` on line 179.

## Scenario 3: Local gates for the changed files

Run the lint and format gates.

```powershell
python -m ruff check .
python -m black --check .
```

Expected: `All checks passed`, and black reports that no file needs a change.

Run the three test files that cover the changes, and the route test.

```powershell
python -m pytest tests/guardrails/test_pr_title_workflow.py
python -m pytest tests/guardrails/test_dependency_export.py
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
python -m pytest tests/guardrails/test_spec_route_contract.py
```

Expected: each command reports that all tests pass. The export guard prints `examined 2 files` and `0 defects`.

Run the docstring gates.

```powershell
pydocstyle src/ wsgi.py web_portal
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90 -v
```

Expected: pydocstyle prints no violation. Interrogate reports 90 percent or above.

Run the symbol gate for the changed test module.

```powershell
symbol-diff --base origin/main tests/guardrails/test_pr_title_workflow.py
```

Expected: `no module-level name changed`, with exit code 0.

Run the STE gate for each changed Markdown file.

```powershell
$record = 'specs\numbered\0\0\1\2\4\1\0\0\4900-mando-radon-pin-conflict'
Get-ChildItem -LiteralPath $record -Recurse -Filter *.md | ForEach-Object { .venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 $_.FullName }
.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 changelog.d\issue-4900-mando-radon-pin-conflict.md
```

Expected: each file scores 80 or above.

## Scenario 4: Test quality gate (after the local commit, before the push)

Commit the intended files first. Then run the preflight and the gate.

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected: the gate line reads `gate: 0 new findings vs baseline`.

## Scenario 5: Remote checks and changed files (after the push)

Watch the checks of the branch pull request.

```powershell
gh pr checks --watch -R jmorrison-juniper/MistHelper
```

Expected: every check that Scenario 1 lists as failed now shows success.

List the changed files of the branch pull request.

```powershell
gh pr view --json files --jq ".files[].path" -R jmorrison-juniper/MistHelper
```

Expected: the list holds the changed files of T002 to T005 and none of the files that FR-006 forbids.

## Scenario 6: Close pull request 4888 (after the merge, with orchestrator authorization)

Read the state of pull request 4888.

```powershell
gh pr view 4888 -R jmorrison-juniper/MistHelper --json state --jq .state
```

Close the pull request with the preservation proof, and delete its branch. Run this command only after the orchestrator authorizes the close.

```powershell
gh pr close 4888 -R jmorrison-juniper/MistHelper --delete-branch --comment "Declined: radon 6.0.1 requires mando below 0.8. Commit e86098cd keeps the diff. Main pins mando 0.7.1 (blob 9a528bfe03a10f7bc903f5768ef26de765bbff43)."
```

Expected: the state reads `CLOSED`.

Caution: `--delete-branch` removes the branch reference only. Commit e86098cd stays recoverable by its SHA.

## Scenario 7: Route check

The route for issue 4900 comes from base-5 digits. The digits are 0 0 1 2 4 1 0 0. Read `.specify/scripts/powershell/spec-route.ps1` lines 7, 17, 31, and 51 to confirm the rule. The record folder must sit at `specs\numbered\0\0\1\2\4\1\0\0\4900-mando-radon-pin-conflict`.
