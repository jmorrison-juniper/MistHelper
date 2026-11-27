# Quickstart: WLAN fixture host teardown

Run these commands from the repository root on the implementation branch. The authoring phase ran none of them (brief rule 2). Each scenario names the task that uses it.

## Prerequisites

- Windows 11 PowerShell for the commands below. The POSIX form appears in Scenario 2.
- The repository `.venv` exists (R-39). Activate it with `.venv\Scripts\Activate.ps1` before Scenario 5.
- The environment defines `COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper`. Never print its value.
- Set the GitHub variables before each `gh` command:

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## Scenario 1: Read the defect and the route (evidence R-01 to R-03)

Read the blob SHA of the main path. Expected result: `e13bf10b66a6cdf43b9904f9c0eda8fd11eb421c` (R-01).

```powershell
gh api "repos/jmorrison-juniper/MistHelper/contents/tests/unit/refactors/test_wlanradius_timer_manager_paths.py?ref=main" --jq ".sha"
```

Read the issue path. Expected result: HTTP 404 (R-02). The issue reproduction command uses this stale path. Do not run that command.

```powershell
gh api "repos/jmorrison-juniper/MistHelper/contents/tests/unit/config/foundation/support/refactors/network/configuration/test_wlanradius_timer_manager_paths.py?ref=main" --jq ".sha"
```

Check the route with the repository script. Expected result: `specs\numbered\0\0\1\2\0\4\3\2\4492-wlan-fixture-host-teardown` (R-51, R-52).

```powershell
. .specify\scripts\powershell\spec-route.ps1
Resolve-SpecFeaturePath -SpecsDir specs -BranchName 4492-wlan-fixture-host-teardown -Number 4492
```

## Scenario 2: Three-node sequence (T003, T004)

Run the WLAN module, then the two named tests. Expected result after the fix: the summary line shows `passed` and no `failed` count.

```powershell
.venv\Scripts\python.exe -m pytest -q tests\unit\refactors\test_wlanradius_timer_manager_paths.py tests\unit\refactors\test_initialize_mist_session.py::TestMhModule::test_returns_misthelper_module tests\unit\refactors\test_tui_launcher.py::TestGetDebugMode::test_returns_false_when_args_absent
```

The POSIX form uses the same IDs with forward slashes.

```bash
.venv/bin/python -m pytest -q tests/unit/refactors/test_wlanradius_timer_manager_paths.py tests/unit/refactors/test_initialize_mist_session.py::TestMhModule::test_returns_misthelper_module tests/unit/refactors/test_tui_launcher.py::TestGetDebugMode::test_returns_false_when_args_absent
```

## Scenario 3: Fixture block check (T001)

Count the three expected lines. Expected result: 3. The lines are the two log calls and the `patch.object` call.

```powershell
Select-String -LiteralPath tests\unit\refactors\test_wlanradius_timer_manager_paths.py -Pattern 'Binding the fake MistHelper host|Restored the previous resolver host|patch.object\(_MH, "_root_module", fake\)' | Measure-Object | Select-Object -ExpandProperty Count
```

Count the removed call. Expected result: 0.

```powershell
Select-String -LiteralPath tests\unit\refactors\test_wlanradius_timer_manager_paths.py -Pattern 'bind_root_module' | Measure-Object | Select-Object -ExpandProperty Count
```

Review each changed line. Each line needs an inline comment (FR-005).

## Scenario 4: Mutation proof (T004)

Run this scenario in the working tree only. Do not commit the mutation.

1. Delete the `patch.object(_MH, "_root_module", fake),` line from the `with (` block.
2. Run Scenario 2. Expected result: two failed tests, `test_returns_misthelper_module` and `test_returns_false_when_args_absent`.
3. Restore the deleted line. Run Scenario 3 again. Expected result: 3 and 0.

Caution: a mutation left in the working tree makes the named tests fail. Restore the line before Scenario 5.

## Scenario 5: Local gates for the changed file (T-LOCAL-GATES)

```powershell
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m black --check .
.venv\Scripts\python.exe -m pytest tests\unit\refactors\test_wlanradius_timer_manager_paths.py -q
symbol-diff --base origin/main tests\unit\refactors\test_wlanradius_timer_manager_paths.py
```

Expected results: `All checks passed`, `No file needs a change`, no failed tests, and `no module-level name changed` with exit code 0.

## Scenario 6: Test quality gate (T002, T-LOCAL-GATES)

Commit the three intended paths locally first. The analyzer reads committed differences. The procedure is in the test quality ratchet section (R-59, which starts at copilot-instructions line 95).

```powershell
git fetch --no-tags origin "+refs/heads/main:refs/remotes/origin/main"
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Expected results: the preflight passes. Both analyzer runs print `gate: 0 new findings vs baseline`.

## Scenario 7: Full shards (T005, T006)

Run the unit shard in sorted order. This run takes about twenty minutes. The CI root-units run took 1080.82 seconds (R-41).

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
```

Run the second shard.

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

Expected result: each shard prints one summary line with no failed count.

## Scenario 8: Diff scope (T-LOCAL-GATES, FR-003)

```powershell
git diff --name-only $(git merge-base origin/main HEAD) HEAD
```

Expected result: the test file, the baseline file, and only the files under `specs/numbered/0/0/1/2/0/4/3/2/4492-wlan-fixture-host-teardown/`. No path under `src/` appears.

## Scenario 9: Pull request and CI evidence (T-PR, T-REMOTE-CI, T-MERGE)

Find the pull request number from the branch name. Use the variable in the next commands.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
$pr = gh pr list -R jmorrison-juniper/MistHelper --head fix/4492-wlan-fixture-host-teardown --json number --jq ".[0].number"
```

Read the body. Expected result: the body contains `Closes #4492`.

```powershell
gh pr view $pr -R jmorrison-juniper/MistHelper --json body --jq ".body"
```

Watch the checks. Expected result: each required check reports success.

```powershell
gh pr checks $pr -R jmorrison-juniper/MistHelper --watch
```

After the merge, read the latest main run of the CI workflow. Expected result: success, with the root-units shard passing.

```powershell
gh run list -R jmorrison-juniper/MistHelper --branch main --workflow ci.yml --limit 1 --json databaseId,conclusion,headSha
```
