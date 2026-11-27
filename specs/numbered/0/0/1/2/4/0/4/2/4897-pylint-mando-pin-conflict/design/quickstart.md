# Quickstart: Pylint gate failure from the mando 0.8.2 pin

Run the environment lines before each `gh` command in a new PowerShell session. Each line sets one value. Do not print the token value.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

Scenarios 1 and 2 are read-only. Scenarios 3 to 5 are for the implementer. They change files only in a worktree or in the fix branch.

## Scenario 1: Reproduce the failed check (read-only)

Step 1. List the failed jobs of run 45064243269. Expect 28 names, including `Pylint (score gate)`.

```powershell
gh run view 45064243269 -R jmorrison-juniper/MistHelper --json jobs --jq '.jobs[] | select(.conclusion == "failure") | .name'
```

Step 2. Read the step table of job 137338442217. Expect `Install dependencies` as `failure` and `Run Pylint` as `skipped`.

```powershell
gh api repos/jmorrison-juniper/MistHelper/actions/jobs/137338442217 --jq '[.steps[] | {name, conclusion}]'
```

Step 3. Read the failed log. Expect the resolution error and the radon 6.0.1 line.

```powershell
gh run view 45064243269 -R jmorrison-juniper/MistHelper --job 137338442217 --log-failed | Select-String -Pattern 'Cannot install|radon 6.0.1 depends|ResolutionImpossible'
```

Caution: the full failed log holds about 980 lines. Filter it before you read it, and do not paste the full log into a review.

Step 4. Read the issue body. Expect the gate name, the pull request number, and the commit `5bb4b385`.

```powershell
gh issue view 4897 -R jmorrison-juniper/MistHelper --json body --jq '.body'
```

## Scenario 2: Confirm the requirement pins (read-only)

Step 1. Read the mando pin on the pull request branch. Expect `mando==0.8.2`.

```powershell
$headContent = gh api "repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=dependabot/pip/mando-0.8.2" --jq '.content'
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($headContent)) -split "`n" | Select-String -Pattern '^(mando|radon)=='
```

Step 2. Read the same two pins on main. Expect `mando==0.7.1` and `radon==6.0.1`.

```powershell
$mainContent = gh api "repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=main" --jq '.content'
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($mainContent)) -split "`n" | Select-String -Pattern '^(mando|radon)=='
```

Step 3. Read the radon requirement from the installed metadata. Expect `Requires-Dist: mando (<0.8,>=0.6)`.

```powershell
Select-String -LiteralPath '.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA' -Pattern '^Requires-Dist: mando'
```

## Scenario 3: Prove the red state of the new test (implementer)

Step 1. Fetch the pull request branch. The fetch changes local refs only.

```powershell
git fetch origin dependabot/pip/mando-0.8.2
```

Step 2. Create a worktree at the pull request head commit. Do not change the branch in the main checkout.

```powershell
git worktree add ..\MistHelper-4897-red e86098cdc2b189d217805b3b4060ef609cbc37af
```

Step 3. Copy the new test module from the fix branch into the worktree. The test reads `requirements-dev.txt` from the worktree root.

```powershell
Copy-Item -LiteralPath '..\MistHelper-4897-fix\tests\guardrails\test_dependency_lock_file.py' -Destination '..\MistHelper-4897-red\tests\guardrails\test_dependency_lock_file.py' -Force
```

Step 4. Run the new test in the worktree. Expect one failure. The message names radon and `mando==0.8.2`.

```powershell
Set-Location -LiteralPath '..\MistHelper-4897-red'
python -m pytest tests/guardrails/test_dependency_lock_file.py::test_pinned_mando_satisfies_radon_requirement -q
Set-Location -LiteralPath '..\MistHelper-4897-fix'
```

Step 5. After you copy the red output into the pull request body, remove the worktree.

```powershell
git worktree remove ..\MistHelper-4897-red
```

## Scenario 4: Run the local gates (implementer)

Run each command from the fix branch worktree. A gate that does not apply to the changed files carries a stated reason in the pull request body.

```powershell
python -m py_compile tests/guardrails/test_dependency_lock_file.py
python -m py_compile tests/guardrails/test_pr_title_workflow.py
python -m ruff check .
python -m black --check .
python -m pytest tests/guardrails/test_dependency_lock_file.py -q
python -m pytest tests/guardrails/test_pr_title_workflow.py -q
python -m pytest tests/guardrails/test_dependency_export.py -q
python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q
uv lock --check
bandit -c pyproject.toml -q tests/guardrails/test_dependency_lock_file.py
ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md
symbol-diff --base origin/main tests/guardrails/test_dependency_lock_file.py
symbol-diff --base origin/main tests/guardrails/test_pr_title_workflow.py
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

Read the paths for the next two gates from `.github/workflows/ci.yml`. Run mypy against the value of `MYPY_PATHS` from the mypy job, with `--config-file pyproject.toml`. Run pydocstyle and interrogate against the values of `PYDOCSTYLE_PATHS` and `INTERROGATE_PATHS` from the same workflow. Expect `Success` from mypy, no violation from pydocstyle, and coverage of 90 percent or above from interrogate.

The test quality gate follows the procedure in `.github/copilot-instructions.md`, section Test quality ratchet. Run the preflight first, then the required check, then the full-suite check.

## Scenario 5: Watch CI on the fix branch (implementer)

Step 1. Watch the checks of the current branch until they finish.

```powershell
gh pr checks --watch
```

Step 2. Read the conclusion of the check `Pylint (score gate)`. Expect `SUCCESS`.

```powershell
gh pr view --json statusCheckRollup --jq '.statusCheckRollup[] | select(.name == "Pylint (score gate)") | .conclusion'
```

Step 3. Search the failed logs of the latest Quality Gates run for the resolution error. Expect no output.

```powershell
$runId = gh run list --workflow "Quality Gates" --branch fix/4897-pylint-mando-pin --limit 1 --json databaseId --jq '.[0].databaseId'
gh run view $runId --log-failed | Select-String -Pattern 'ResolutionImpossible'
```

## Scenario 6: Check the closure of pull request #4888 (implementer)

Run this command after the fix merges and the orchestrator authorizes the closure. Expect `CLOSED`.

```powershell
gh pr view 4888 -R jmorrison-juniper/MistHelper --json state --jq '.state'
```
