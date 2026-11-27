# Quickstart: Vulture Gate Mando Radon Conflict

This guide gives the exact steps to reproduce the failure and the exact commands to verify the fix. Each code block holds one command per line.

## Reproduce the Failure From the CI Logs

Read-only. Run these lines in one PowerShell session.

```powershell
$env:GH_HOST = "github.com"
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh run view 45064243269 -R jmorrison-juniper/MistHelper --job 137336718674 --log-failed | Select-String -Pattern "ResolutionImpossible", "Cannot install", "depends on mando"
```

Expected result: three lines. The first line reports `Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2`. The second line reports `radon 6.0.1 depends on mando<0.8 and >=0.6`. The third line reports `ResolutionImpossible`.

Find the failed step of the job:

```powershell
(gh api repos/jmorrison-juniper/MistHelper/actions/jobs/137336718674 | ConvertFrom-Json).steps | Where-Object conclusion -eq "failure" | Select-Object number, name
```

Expected result: step 4, `Run pip install -r requirements-dev.txt`.

## Confirm the Pin Conflict

Read the radon requirement from the local installed metadata. This check only reads files.

```powershell
Select-String -LiteralPath ".venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA" -Pattern "^Requires-Dist: mando"
```

Expected result: `Requires-Dist: mando (<0.8,>=0.6)` at line 31.

Read the pinned `mando` version on `main`:

```powershell
$mainRaw = gh api "repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=main" --jq ".content"
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String(($mainRaw -replace "\s",""))) -split "`n" | Select-String -Pattern "^mando==", "^radon=="
```

Expected result: `mando==0.7.1` at line 179 and `radon==6.0.1` at line 365.

Read the pinned `mando` version in the failing merge commit:

```powershell
$mergeRaw = gh api "repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71" --jq ".content"
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String(($mergeRaw -replace "\s",""))) -split "`n" | Select-String -Pattern "^mando=="
```

Expected result: `mando==0.8.2` at line 179.

Read the upstream radon requirement on its default branch:

```powershell
$radonRaw = gh api repos/rubik/radon/contents/pyproject.toml --jq ".content"
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String(($radonRaw -replace "\s",""))) -split "`n" | Select-String -Pattern "mando"
```

Expected result: `mando = ">=0.6,<0.8"` at line 11.

## Verify the Local Gates

Run these commands from the root of the fix branch. Each command is listed in the local gates table of `.github/copilot-instructions.md`.

```powershell
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
python -m pytest tests/guardrails/test_pr_title_workflow.py
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
python -m pytest tests/guardrails/test_complexity_gate_limit.py
bandit -c pyproject.toml -r tests/guardrails/test_pr_title_workflow.py -q
symbol-diff --base origin/main tests/guardrails/test_pr_title_workflow.py
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
ste-linter --config .ste-linter.toml --min-score 80 documentation/quality-gates.md changelog.d/issue-4899-mando-radon-pin.md
```

Expected results:

| Command | Expected result |
| - | - |
| `python -m py_compile MistHelper.py` | No output |
| `python -m ruff check .` | `All checks passed` |
| `python -m black --check .` | No file needs a change |
| `python -m pytest tests/guardrails/test_pr_title_workflow.py` | All tests pass, including the two new cases |
| `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` | All tests pass |
| `python -m pytest tests/guardrails/test_complexity_gate_limit.py` | All tests pass |
| `bandit -c pyproject.toml -r tests/guardrails/test_pr_title_workflow.py -q` | No finding |
| `symbol-diff --base origin/main tests/guardrails/test_pr_title_workflow.py` | `no module-level name changed`, exit code 0 |
| `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | No finding |
| `ste-linter` with the two files of the block above | Each file scores 80 or above |

Run the test quality ratchet after the local commit and before the push. Stop at the first failed command.

```powershell
$BASE_REF = "main"
git fetch --no-tags origin "+refs/heads/${BASE_REF}:refs/remotes/origin/${BASE_REF}"
git rev-parse --verify "origin/${BASE_REF}^{commit}"
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/$BASE_REF" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected result: the last command prints `gate: 0 new findings vs baseline`.

## Gates That Do Not Apply

The CI environment in the failed log of run 45064243269 lists the paths of each gate. The changed files fall outside these gates.

- Types (`mypy`): `MYPY_PATHS` lists product paths only. The changed test module is outside them.
- Complexity (`radon cc`): `RADON_PATHS` does not list the changed test module.
- Coverage, code quality (`pylint`), and the safe sweep: no product file under `src/` or `MistHelper.py` changes.
- Dependency audit (`pip-audit -r requirements.txt`): `requirements.txt` does not change.
- Docstrings (`pydocstyle` and `interrogate`): `PYDOCSTYLE_PATHS` and `INTERROGATE_PATHS` list product paths only.
- Menu reference and portal gates: no menu, portal, or `ops-portal/` file changes.

## Verify the Fix Pull Request

Watch the checks of the fix pull request from its branch:

```powershell
gh pr checks --watch
```

Read the latest run of the branch and check the two jobs and the resolver text:

```powershell
$runId = (gh run list --branch fix/4899-vulture-gate-mando-radon-conflict --limit 1 --json databaseId | ConvertFrom-Json)[0].databaseId
(gh run view $runId -R jmorrison-juniper/MistHelper --json jobs | ConvertFrom-Json).jobs | Where-Object { $_.name -match "Vulture|Dependency lock" } | Select-Object name, conclusion
gh run view $runId -R jmorrison-juniper/MistHelper --log-failed | Select-String -Pattern "ResolutionImpossible"
```

Expected result: both jobs show `success`. The last command prints no line (TEST-006, TEST-007, TEST-008).

## Verify the Record and the Diff

Run the record check from the record folder. It confirms the check name, job ID, run ID, step name, and resolver text (TEST-009).

```powershell
Select-String -Path "design\research.md" -Pattern "Vulture \(dead code\)", "137336718674", "45064243269", "Run pip install -r requirements-dev.txt", "ResolutionImpossible"
```

Check the changed paths of the fix branch (TEST-010):

```powershell
git diff --name-status origin/main
```

Expected result: the four changed files and the eight record files. No other path appears.

## Verify After the Merge

Read the state of pull request #4888 (TEST-011):

```powershell
gh pr view 4888 -R jmorrison-juniper/MistHelper --json state,mergedAt
```

Expected result: `"state":"CLOSED"`.

List the pull requests for `mando` after the merge (SC-004). Expected result: the next weekly pip run creates no pull request for `mando` 0.8 or later.

```powershell
gh pr list -R jmorrison-juniper/MistHelper --state all --search "mando" --json number,title,state,createdAt
```
