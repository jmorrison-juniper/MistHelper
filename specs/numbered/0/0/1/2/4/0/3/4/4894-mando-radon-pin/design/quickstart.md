# Quickstart: Keep mando inside the radon requirement

These steps reproduce issue #4894 and run each check for the fix. Run each command from the repository root unless a step names another folder. Use a new worktree for the fix branch.

Before each `gh` command, set the GitHub host and token. The token comes from the account variable.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## 1. Read the failing log lines

```powershell
gh run view 45064243269 -R jmorrison-juniper/MistHelper --log-failed | Select-String -Pattern 'ResolutionImpossible|radon 6.0.1 depends on mando'
```

Expected: two matching lines. The lines name the resolver error and the radon requirement on mando below 0.8.

## 2. Reproduce the resolver failure on the pull request head

```powershell
git worktree add --detach ..\MistHelper-4894-head e86098cdc2b189d217805b3b4060ef609cbc37af
cd ..\MistHelper-4894-head
python -m venv .venv
.venv\Scripts\python.exe -m pip install --dry-run -r requirements-dev.txt
```

Expected: the output ends with `ERROR: ResolutionImpossible`. The conflict text names radon 6.0.1 and mando 0.8.2.

## 3. Confirm that main resolves

```powershell
git worktree add --detach ..\MistHelper-4894-main origin/main
cd ..\MistHelper-4894-main
python -m venv .venv
.venv\Scripts\python.exe -m pip install --dry-run -r requirements-dev.txt
```

Expected: the command exits 0 and reports no conflict.

Warning: removing a worktree deletes its uncommitted files. Remove a worktree only after its work is saved or committed.

## 4. Run the two new guard tests

Run this command in the fix branch worktree.

```powershell
python -m pytest tests/guardrails/test_dependency_export.py::TestDependabotPipIgnore
```

Expected before the ignore entry exists: both tests fail. Expected after the ignore entry exists: both tests pass.

## 5. Run the whole export guard file

```powershell
python -m pytest tests/guardrails/test_dependency_export.py
```

Expected: every test passes. The export test reports zero defects.

## 6. Run lint and format

```powershell
python -m ruff check .
python -m black --check .
```

Expected: the lint command prints `All checks passed`. The format command reports no file that needs a change.

## 7. Run the security lint on the changed test file

```powershell
bandit -c pyproject.toml -r tests/guardrails/test_dependency_export.py -q
```

Expected: no finding at any severity.

## 8. Run the coverage command

```powershell
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
```

Expected: the coverage report shows 80 percent or above.

## 9. Run the symbol gate on the changed test file

```powershell
symbol-diff --base origin/main tests/guardrails/test_dependency_export.py
```

Expected: exit code 0. Record the output in the pull request body.

## 10. Run the two full-test commands

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

Expected: each command prints one summary line for each shard, and each shard passes.

## 11. Run the STE gate on each changed Markdown file

```powershell
ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4894-mando-radon-pin.md
Get-ChildItem -Recurse -Filter *.md specs/numbered/0/0/1/2/4/0/3/4/4894-mando-radon-pin | ForEach-Object { ste-linter --config .ste-linter.toml --min-score 80 $_.FullName }
```

Expected: each file scores 80 or above.

## 12. Run the test quality gate after the local commit

```powershell
$BASE_REF = "main"
git fetch --no-tags origin "+refs/heads/${BASE_REF}:refs/remotes/origin/${BASE_REF}"
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/$BASE_REF" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected: the output includes `gate: 0 new findings vs baseline`.

## 13. Confirm the change scope

```powershell
git diff --name-only origin/main
```

Expected: only the paths in the change map of plan.md.

## 14. Watch the CI checks on the fix branch

```powershell
gh pr checks --watch -R jmorrison-juniper/MistHelper
```

Expected: each check reports success.

- `Dependency lock and exports`
- `pytest (coverage gate)`
- The four `pytest coverage shard` checks
- `Ruff (ops platform)`
- The 15 required contexts

## 15. Confirm the closure of pull request #4888

```powershell
gh pr view 4888 -R jmorrison-juniper/MistHelper --json state,mergedAt
```

Expected: the state is CLOSED and the merge time is null.
