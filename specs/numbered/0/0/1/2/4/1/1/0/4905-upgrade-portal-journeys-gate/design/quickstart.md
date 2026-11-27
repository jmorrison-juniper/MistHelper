# Quickstart: Reproduce and verify issue 4905

This file gives the exact commands for the reproduction and the verification of issue 4905. The reproduction commands are read-only. Each `gh` command needs the two environment lines in section 1 in the same shell.

## 1. Set the GitHub environment

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## 2. Read the issue

```powershell
gh issue view 4905 -R jmorrison-juniper/MistHelper --json number,title,state,labels
```

Expected result: `state` is `OPEN`. The labels are `bug`, `ci`, and `quality-gate` (R-71).

## 3. Read the steps of the failed job

```powershell
gh api repos/jmorrison-juniper/MistHelper/actions/jobs/137339161249 --jq '.steps[] | {number, name, conclusion}'
```

Expected result: step 4, `Install dependencies`, has the conclusion `failure` (R-62). Step 6, `Run isolated upgrade portal journeys`, has the conclusion `skipped`.

## 4. Read the pip error lines from the failed run

```powershell
gh run view 45064243269 -R jmorrison-juniper/MistHelper --log-failed | Select-String -Pattern "ResolutionImpossible|radon 6.0.1 depends|Cannot install -r requirements-dev.txt"
```

Expected result: the output lists the same error lines from 26 failed jobs. Each job prints the same three lines:

- `ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2 because these package versions have conflicting dependencies.`
- `    radon 6.0.1 depends on mando<0.8 and >=0.6`
- `ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts`

## 5. Read the pins on the pull request head

```powershell
$encoded = (gh api "repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=dependabot/pip/mando-0.8.2" --jq ".content") -join ""
$text = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String(($encoded -replace "\s", "")))
$text -split "`n" | Select-String -Pattern "^mando==|^radon=="
```

Expected result: `mando==0.8.2` and `radon==6.0.1` (R-04, R-05).

## 6. Read the pins on main

Replace the `ref` value in the command in section 5 with `main`.

Expected result: `mando==0.7.1` and `radon==6.0.1` (R-01, R-02).

## 7. Read the radon requirement from the local environment

```powershell
Select-String -LiteralPath ".venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA" -Pattern "^Requires-Dist: mando"
```

Expected result: `Requires-Dist: mando (<0.8,>=0.6)` (R-66).

## 8. Read the newest radon release from PyPI

```powershell
$radon = Invoke-RestMethod -Uri "https://pypi.org/pypi/radon/json"
$radon.info.version
$radon.info.requires_dist
```

Expected result: the version is `6.0.1`. The requirement list holds `mando (<0.8,>=0.6)` (R-64, R-65).

## 9. Read the journeys gate on main

```powershell
gh api repos/jmorrison-juniper/MistHelper/actions/runs/45774119357/jobs --jq '.jobs[] | select(.name == "Upgrade portal journeys") | .conclusion'
```

Expected result: `success` (R-63).

## 10. Verify the change after implementation

Run these commands in the worktree of the fix branch. Each command comes from the local gates table or from a named guard test.

```powershell
python -m pytest tests/guardrails/test_pr_title_workflow.py
python -m pytest tests/guardrails/test_upgrade_portal_journey_ci.py
python -m pytest tests/guardrails/test_dependency_export.py
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
python -m pytest tests/guardrails/test_spec_route_contract.py
python -m ruff check .
python -m black --check .
bandit -c pyproject.toml -r tests/guardrails -q
symbol-diff --base origin/main tests/guardrails/test_pr_title_workflow.py
```

Expected result: each pytest command exits with code 0. Ruff prints `All checks passed`. Black reports no file that needs a change. Bandit prints no finding. Symbol-diff prints `no module-level name changed`.

Run the guardrail shard of the full suite. Use the second command of the local gates list (R-45):

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

Expected result: one summary line for each shard, and no failed chunk (R-44).

Run the test quality ratchet after the local commit. Use the command from the test quality ratchet section:

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected result: `gate: 0 new findings vs baseline`.

Run the STE gate on each Markdown file of the record and on the fragment. Use the command of the STE row (R-46):

```powershell
ste-linter --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\2\4\1\1\0\4905-upgrade-portal-journeys-gate\spec.md specs\numbered\0\0\1\2\4\1\1\0\4905-upgrade-portal-journeys-gate\plan.md specs\numbered\0\0\1\2\4\1\1\0\4905-upgrade-portal-journeys-gate\tasks.md specs\numbered\0\0\1\2\4\1\1\0\4905-upgrade-portal-journeys-gate\analysis.md specs\numbered\0\0\1\2\4\1\1\0\4905-upgrade-portal-journeys-gate\design\research.md specs\numbered\0\0\1\2\4\1\1\0\4905-upgrade-portal-journeys-gate\design\data-model.md specs\numbered\0\0\1\2\4\1\1\0\4905-upgrade-portal-journeys-gate\design\quickstart.md specs\numbered\0\0\1\2\4\1\1\0\4905-upgrade-portal-journeys-gate\design\contracts\dependabot-pip-ignore.md specs\numbered\0\0\1\2\4\1\1\0\4905-upgrade-portal-journeys-gate\design\checklists\requirements.md specs\numbered\0\0\1\2\4\1\1\0\4905-upgrade-portal-journeys-gate\design\checklists\ci-gate.md specs\numbered\0\0\1\2\4\1\1\0\4905-upgrade-portal-journeys-gate\design\checklists\dependency-pin.md changelog.d\issue-4905-upgrade-portal-journeys-gate.md
```

Expected result: each file scores 80 or above.

## 11. Optional local reproduction of the resolver error

Run this only in a separate worktree of commit `e86098cdc2b189d217805b3b4060ef609cbc37af`. A dry run still reads the package index. It installs no package.

```powershell
git worktree add ..\MistHelper-pr4888 e86098cdc2b189d217805b3b4060ef609cbc37af
cd ..\MistHelper-pr4888
python -m pip install --dry-run -r requirements.txt -r requirements-dev.txt
```

Expected result: pip ends with `ResolutionImpossible`. Research did not run this command (rule 2 of the brief), so the result is an expectation for the implementer to confirm.

## 12. Check the closure after the merge

These commands read the state only. Run them after the orchestrator authorizes the closure (U-2).

```powershell
gh pr view 4888 -R jmorrison-juniper/MistHelper --json state,headRefOid
gh issue list -R jmorrison-juniper/MistHelper --label quality-gate --state open --json number,title
```

Expected result after closure: the pull request state is `CLOSED`. Its head remains `e86098cdc2b189d217805b3b4060ef609cbc37af`. The open gate issues no longer include issues 4891 to 4905 (R-72).
