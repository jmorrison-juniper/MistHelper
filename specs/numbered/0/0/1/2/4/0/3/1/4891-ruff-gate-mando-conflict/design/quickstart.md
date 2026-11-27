# Quickstart: Ruff (lint) check failure from the mando 0.8.2 pin

Each command is read-only unless the section says otherwise. Set the GitHub account before each `gh` command:

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## 1. Reproduce the failure

- QS-01. Read the issue facts.

```powershell
gh issue view 4891 -R jmorrison-juniper/MistHelper --json number,title,body,state,labels,comments,createdAt,updatedAt,author
```

Expected: the title `CI: quality-gate `ruff` failed (PR #4888)`, state OPEN, and the gate `ruff`.

- QS-02. Read the failed-step log of the Ruff (lint) check.

```powershell
gh run view 45064243269 -R jmorrison-juniper/MistHelper --job 137336719229 --log-failed
```

Expected: these two lines, with the timestamp 2026-11-22T20:07:26.5519430Z on the first line:

```text
ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2 because these package versions have conflicting dependencies.
    radon 6.0.1 depends on mando<0.8 and >=0.6
```

The log ends with `##[error]Process completed with exit code 1.`

- QS-03. Read the step table of the Ruff (lint) check.

```powershell
gh run view 45064243269 -R jmorrison-juniper/MistHelper --json jobs --jq '.jobs[] | select(.name == "Ruff (lint)") | .steps[] | {number, name, conclusion}'
```

Expected: step 5 `Run pip install -r requirements-dev.txt` has conclusion `failure`. Step 6 `Ruff lint` has conclusion `skipped`.

- QS-04. Count the resolver conflict across the failed jobs.

```powershell
gh run view 45064243269 -R jmorrison-juniper/MistHelper --log-failed | Select-String -Pattern "conflicting dependencies"
```

Expected: 26 matching lines, one for each job in section 2 except the last two rows.

## 2. Failed jobs in run 45064243269

The run has 28 failed jobs. The last two rows do not show the conflict. Their aggregator steps read an upstream result (RV-13, RV-14).

| Job name | Job ID | Failing step or steps |
| --- | --- | --- |
| Vulture (dead code) | 137336718674 | Run pip install -r requirements-dev.txt |
| Quality exclusion drift (advisory) | 137336718972 | Run pip install -r requirements-dev.txt |
| Diagram reference lint | 137336718990 | Run python -m pip install -r requirements-dev.txt |
| Radon (complexity) | 137336719006 | Run pip install -r requirements-dev.txt |
| Interrogate (docstring coverage) | 137336719025 | Run pip install -r requirements-dev.txt |
| Test quality ratchet (gate) | 137336719038 | Run pip install -r requirements-dev.txt |
| Citation reference lint | 137336719093 | Run python -m pip install -r requirements-dev.txt |
| Dependency lock and exports | 137336719111 | Run pip install -r requirements-dev.txt |
| CodeQL verdict register check | 137336719141 | Run python -m pip install -r requirements-dev.txt |
| Bandit (security) | 137336719159 | Run pip install -r requirements-dev.txt |
| pydocstyle (docstring style) | 137336719204 | Run pip install -r requirements-dev.txt |
| Ruff (lint) | 137336719229 | Run pip install -r requirements-dev.txt |
| Ruff (ops platform) | 137336719241 | Install ruff |
| SpecKit task audit (advisory) | 137336719307 | Run python -m pip install -r requirements-dev.txt |
| pip-audit (CVE scan) | 137338084755 | Run pip install -r requirements-dev.txt |
| mypy (strict) | 137338084785 | Install dependencies |
| E2E shard (upgrade-portal) | 137338442186 | Install dependencies |
| Pylint (score gate) | 137338442217 | Install dependencies |
| pytest coverage shard (upgrade-contracts) | 137338442226 | Install dependencies |
| E2E shard (web-portal) | 137338442234 | Install dependencies, Upload backup restoration browser evidence, and Upload firmware policy comparison browser evidence |
| pytest coverage shard (upgrade-units) | 137338442235 | Install dependencies |
| pytest coverage shard (root-units) | 137338442288 | Install dependencies |
| pytest coverage shard (root-and-contracts) | 137338442294 | Install dependencies |
| E2E shard (websockets-tab) | 137338442334 | Install dependencies |
| pytest (coverage gate) | 137338980629 | Verify dependency lock job (aggregator, reads the dependency_lock result) |
| E2E smoke tests | 137339065340 | Verify E2E shards (aggregator, reads the playwright_shards result) |
| Upgrade portal journeys | 137339161249 | Install dependencies, and Upload upgrade portal journey evidence |
| Black (format check) | 137339161296 | Run pip install -r requirements-dev.txt |

Two other workflows fail with the same resolver conflict at step `Install test dependencies`. They are `Native Windows timeout budget` (run 45064235051) and `Windows audit report` (run 45064235097).

## 3. Confirm the pins on main

- QS-05. Read the jobs of the main run for commit f03c6c9.

```powershell
gh run view 45774119357 -R jmorrison-juniper/MistHelper --json jobs --jq '.jobs[] | select(.name | test("^(Ruff|Dependency lock)")) | "\(.name) -> \(.conclusion)"'
```

Expected: `Ruff (lint) -> success`, `Ruff (ops platform) -> success`, and `Dependency lock and exports -> success`.

- QS-06. Read line 179 of `requirements-dev.txt` on main.

```powershell
$c = gh api "repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=main" --jq ".content"
$lines = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(($c -replace '\s',''))) -split "`n"
$lines[178]
```

Expected: `mando==0.7.1`.

## 4. Local verification commands (QS-07)

Run these commands in the worktree of the fix branch. Each command comes from the local gates table (RV-48) or the procedure that the table names (RV-49, RV-50).

| Gate | Command | Expected result |
| --- | --- | --- |
| Lint | `python -m ruff check .` | `All checks passed` |
| Format | `python -m black --check .` | No file needs a change |
| Tests | `python -m pytest tests/guardrails/test_dependency_export.py` | All cases pass. The output prints the count of pip ignore entries, which is 1. |
| Tests (fragment) | `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` | All cases pass |
| Symbols | `symbol-diff --base origin/main tests/guardrails/test_dependency_export.py` | `no module-level name changed`, exit code 0 |
| Test quality preflight | `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` | All cases pass |
| Test quality | `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` | `gate: 0 new findings vs baseline` |
| Full tests | `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal` | One summary line for each shard, with no failure |

Run the test-quality preflight and the test-quality gate after the commit (RV-49). Fetch `origin/main` before the gate, with the fetch command in the test-quality section of `.github/copilot-instructions.md`.

Not applicable: Compile, Types, Safe sweep, Coverage, Complexity, Security lint, Dependency audit, Code quality, Dead code, Docstrings, Menu reference, STE, Ops portal, and Ops platform. The reasons are in `design\research.md`, section 8.

## 5. Remote verification commands (QS-09)

After the push, run the following command and wait for the checks to finish.

```powershell
gh pr checks $FIX_PR -R jmorrison-juniper/MistHelper --watch
```

Expected: Ruff (lint), Dependency lock and exports, each pytest coverage shard, Conventional Commits PR title, and CodeQL report success.

## 6. Checks after the merge (QS-08)

- QS-08. Read the state of PR #4888. This read is the only check on PR #4888 in this change.

```powershell
gh pr view 4888 -R jmorrison-juniper/MistHelper --json number,state,mergedAt,headRefName
```

Expected at merge time: `state` is OPEN, `headRefName` is `dependabot/pip/mando-0.8.2`, and `mergedAt` is null. Record the value on issue #4891 (T-MERGE step 4). Do not change PR #4888.

- Confirm that the fix pull request is merged and that issue #4891 is closed.

```powershell
gh pr view $FIX_PR -R jmorrison-juniper/MistHelper --json state,mergedAt
gh issue view 4891 -R jmorrison-juniper/MistHelper --json state
```

Expected: the pull request state is MERGED with a `mergedAt` value. The issue state is CLOSED.
