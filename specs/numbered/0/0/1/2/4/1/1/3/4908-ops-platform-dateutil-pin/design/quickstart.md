# Quickstart: Ops platform dateutil pin (issue #4908)

This file gives the exact reproduction steps and the exact verification commands for issue #4908. Run each command from the stated folder.

## Prerequisites

- GitHub CLI access. Set the host and the token in the same shell before each `gh` command.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

- A fix worktree of the repository for every edit. Do not edit the read-only checkout.
- A Python 3.15 environment in the worktree. CI uses Python 3.15 (RC-04).

## 1. Reproduce the failure (read-only)

Step 1. Read the failing job and its conclusion.

```powershell
$run = gh run view 45064318582 -R jmorrison-juniper/MistHelper --json jobs | ConvertFrom-Json
$run.jobs | Where-Object { $_.name -eq 'pytest (ops platform)' } | Select-Object name, conclusion
```

Expected result: the job `pytest (ops platform)` has the conclusion `failure`.

Step 2. Read the conflict lines from the failed log.

```powershell
gh run view 45064318582 -R jmorrison-juniper/MistHelper --log-failed | Select-String -Pattern 'ResolutionImpossible|celery 5.7.0 depends on'
```

Expected result: two lines. One line names `ResolutionImpossible`. The other line names `celery 5.7.0 depends on python-dateutil==2.9.0.post0`.

Step 3. Read line 157 of the ops requirements file on `main`.

```powershell
$text = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String((gh api "repos/jmorrison-juniper/MistHelper/contents/mist-ops-platform/requirements.txt?ref=main" --jq .content)))
($text -split "`n")[156]
```

Expected result: `python-dateutil==2.9.0.post0`.

Step 4. Reproduce the pip conflict on the PR head. Run this in a separate worktree, not in the checkout that holds your edits.

```powershell
git worktree add ..\misthelper-4908-repro 4be9d2e76a4d21df95305cf2b0ef4941fb4f4b82
Set-Location ..\misthelper-4908-repro\mist-ops-platform
python -m pip install --dry-run -r requirements.txt
```

Expected result: pip stops with `ResolutionImpossible`. It names `python-dateutil==4.0.0` and `celery 5.7.0`.

Caution: a leftover worktree holds a checkout. Remove it after the reproduction with `git worktree remove ..\misthelper-4908-repro`.

## 2. Verify the change (fix worktree)

Run each command from the root of the fix worktree.

```powershell
python -m py_compile tests/guardrails/test_dependency_declaration_parity.py
python -m ruff check .
python -m black --check .
python -m pytest tests/guardrails/test_dependency_declaration_parity.py
symbol-diff --base origin/main tests/guardrails/test_dependency_declaration_parity.py
bandit -c pyproject.toml -r tests/guardrails/test_dependency_declaration_parity.py -q
radon cc tests/guardrails/test_dependency_declaration_parity.py -j | complexity-gate --max 10
check-citations src tests
ste-linter --config .ste-linter.toml --min-score 80 documentation/quality-gates.md changelog.d/issue-4908-ops-platform-dateutil-pin.md
```

Expected results:

- `py_compile` prints no output.
- `ruff` prints `All checks passed`.
- `black` reports no file that needs a change.
- `pytest` passes all nine cases of the guard module.
- `symbol-diff` prints `no module-level name changed`.
- `bandit` reports no finding.
- `complexity-gate` reports no block above 10.
- `check-citations` reports no unresolved citation.
- `ste-linter` scores each file at 80 or above.

## 3. Verify the test quality gate

Run the preflight first. It checks the procedure against the live job.

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

Commit the intended change first. Then run the analyzer against `main`.

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected result: `gate: 0 new findings vs baseline`.

## 4. Verify the Dependabot rule

```powershell
python -m pytest tests/guardrails/test_dependency_declaration_parity.py -k dependabot
```

Expected result: six selected tests pass. One test reads the real configuration. Five test cases check the drift rules.

## 5. Verify the ops platform gate

Run this in `mist-ops-platform` after the install step succeeds on the fix worktree.

```powershell
pytest --cov=src --cov-fail-under=56
```

Expected result: at least 390 tests are collected, and coverage is 56 percent or above.

## 6. Post-merge checks (read-only)

Step 1. Read the number of the fix pull request from the fix worktree.

```powershell
gh pr view --json number --jq .number
```

Step 2. Watch the checks of the fix pull request.

```powershell
gh pr checks --watch
```

Expected result: `pytest (ops platform)` reports `pass`.

Step 3. After the next weekly Dependabot run, read the open python-dateutil pull requests.

```powershell
gh pr list -R jmorrison-juniper/MistHelper --state open --search "python-dateutil" --json number,title
```

Expected result: no pull request proposes a python-dateutil major update. This check verifies U-1.
