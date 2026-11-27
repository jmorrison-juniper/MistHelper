# Quickstart: Interrogate Gate Failure on PR #4888

These steps reproduce the failure, verify the fix, and check the state after the merge. Run the commands in PowerShell from the repository root unless a step names another folder.

## Prerequisites

- The GitHub CLI `gh` is installed and authenticated for `jmorrison-juniper/MistHelper`.
- The repository checkout is `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`.
- The fix worktree is `..\MistHelper-4901`, created by T002.

Before each `gh` command in a new PowerShell session, run these two lines.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## Scenario 1: Reproduce the failing check from the CI logs (read-only)

Step 1. Read the job summary of run 45064243269.

```powershell
gh run view 45064243269 -R jmorrison-juniper/MistHelper --json jobs
```

Expected: job `Interrogate (docstring coverage)` has conclusion `failure`. Its failed step is `Run pip install -r requirements-dev.txt`.

Step 2. Read the job log of job 137336719025.

```powershell
gh run view 45064243269 -R jmorrison-juniper/MistHelper --job 137336719025 --log
```

Expected: the log holds `ERROR: ResolutionImpossible` and `radon 6.0.1 depends on mando<0.8 and >=0.6`. The log holds no line that begins with `RESULT:`.

Step 3. Read the PR head and its changed files.

```powershell
gh pr view 4888 -R jmorrison-juniper/MistHelper --json headRefOid,files
```

Expected: `headRefOid` is `e86098cdc2b189d217805b3b4060ef609cbc37af`. The only changed file is `requirements-dev.txt`.

## Scenario 2: Reproduce the resolver conflict in a scratch environment

Create the scratch environment beside the repository, not inside it.

```powershell
python -m venv ..\resolver-check-4901
..\resolver-check-4901\Scripts\python.exe -m pip install --dry-run mando==0.8.2 radon==6.0.1
```

Expected: pip stops with `ResolutionImpossible`. The message names `radon 6.0.1 depends on mando<0.8 and >=0.6`.

Remove the scratch environment after the check.

Warning: the next command deletes the scratch folder and all files in it. Check the path before you run it.

```powershell
Remove-Item -LiteralPath ..\resolver-check-4901 -Recurse -Force
```

## Scenario 3: Check the main pins (read-only)

```powershell
$raw = gh api "repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=main" --jq .content
$text = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String(($raw -replace '\s','')))
($text -split "`n")[178]
($text -split "`n")[364]
```

Expected: line 179 reads `mando==0.7.1`. Line 365 reads `radon==6.0.1`.

## Scenario 4: Run the policy cases

Before T007, the three new cases and `test_complete_policy` fail.

```powershell
python -m pytest tests/guardrails/test_pr_title_workflow.py::TestDependabotPolicy -q
```

After T007, every case in the class passes.

## Scenario 5: Run the docstring command locally

```powershell
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90 -v
```

Expected: the final line reads `RESULT: PASSED`. The `main` run reported `RESULT: PASSED (minimum: 90.0%, actual: 99.7%)` (research R3).

## Scenario 6: Check the route and the fragment

```powershell
python -m pytest tests/guardrails/test_spec_route_contract.py -q
Get-ChildItem changelog.d -Filter 'issue-4901-*'
```

Expected: the route tests pass. The fragment listing shows one file.

## Scenario 7: Check the state after the merge (read-only)

```powershell
gh pr view 4888 -R jmorrison-juniper/MistHelper --json state,mergedAt
gh pr list -R jmorrison-juniper/MistHelper --state open --search "mando in:title" --json number,title
```

Expected: the first command reports `"state":"CLOSED"`. The second command lists no open pull request for `mando` 0.8 or later. A rejected rule appears only in a weekly Dependabot run (U-1).

## Local gates

Activate the environment first.

```powershell
.venv\Scripts\Activate.ps1
```

| Gate | Command | Applies to this change | Expected result |
|------|---------|------------------------|-----------------|
| Compile | `python -m py_compile MistHelper.py` | Yes. The constitution requires it before each commit. | No output, exit code 0 |
| Lint | `python -m ruff check .` | Yes. The changed test file is Python. | `All checks passed` |
| Format | `python -m black --check .` | Yes. The changed test file is Python. | No file needs a change |
| Changed test file | `python -m pytest tests/guardrails/test_pr_title_workflow.py -q` | Yes | All tests pass |
| Guard shard | `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal` | Yes. The shard holds the changed guard file. | One summary line, zero failures |
| Unit shard | `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal` | Yes. The copilot instructions name this shard for full tests. | One summary line, zero failures |
| Coverage | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | Yes. The changed file sits under `tests`. | Coverage at 80 percent or above |
| Test quality | The procedure in the copilot instructions, section "Test quality ratchet" | Yes. The changed file is a test. Run it after the local commit. | `gate: 0 new findings vs baseline` |
| Security lint | `bandit -c pyproject.toml -r tests\guardrails\test_pr_title_workflow.py -q` | Yes. The CI job scans the whole repository. | No finding |
| Docstrings | `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90 -v` | Confirms the failing check's own command. The changed files sit outside its paths. | `RESULT: PASSED` |
| Symbols | `symbol-diff --base origin/main tests\guardrails\test_pr_title_workflow.py` | Yes. A Python file changed. | `no module-level name changed`, exit code 0 |
| STE | `ste-linter --config .ste-linter.toml --min-score 80 changelog.d\issue-4901-interrogate-mando-pin-conflict.md` | Self-check only. The CI job grades a fixed file list. | Score 80 or above |

Not applicable to this change, because the changed files sit outside these gate paths:

- Dependency audit. `requirements.txt` is unchanged.
- Complexity, code quality, and dead code. No file under `src/` or `MistHelper.py` changed.
- Menu reference, safe sweep, ops portal, and ops platform. No menu or portal file changed.
