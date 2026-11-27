# Quickstart: Reproduce and verify issue 4797

**Scope**: Exact steps and commands for this issue. Each check runs in a clean worktree at the commit under test (decision D-10).

Caution: The repository working tree holds uncommitted content for two files. Run no check in that working tree (research section Local State).

## 1. Set the GitHub account for read commands

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## 2. Confirm the state of PR #4208 (gate G-1)

```powershell
gh pr view 4208 -R jmorrison-juniper/MistHelper --json state,mergedAt,headRefName
```

Expected before the merge: `state` is OPEN, `mergedAt` is null, and `headRefName` is `jmorrison-juniper-4200-migrate-mistwanperformance`.

## 3. Create worktrees outside OneDrive

Caution: A worktree under OneDrive can hold file locks. Use the paths below.

```powershell
$repo = 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper'
git -C "$repo" fetch origin jmorrison-juniper-4200-migrate-mistwanperformance
git -C "$repo" worktree add C:\Users\jmorrison\worktrees\misthelper-4797-candidate 2037e9b95e2ad3b5cc1d02ac0b48a140d5dc1473
git -C "$repo" worktree add C:\Users\jmorrison\worktrees\misthelper-4797-pr 843be63bc837513b4442dae69da9f0db922e0ed1
```

## 4. Bootstrap each worktree

A new worktree has no `.venv`. Run the bootstrap in each worktree (RC-35).

```powershell
Set-Location C:\Users\jmorrison\worktrees\misthelper-4797-pr
uv run --no-project --python 3.15.2 python scripts\bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

Repeat the same three commands in `C:\Users\jmorrison\worktrees\misthelper-4797-candidate`.

## 5. Reproduction pair on the candidate commit (expect one failed test)

```powershell
Set-Location C:\Users\jmorrison\worktrees\misthelper-4797-candidate
python -m pytest -q tests\unit\refactors\test_wlanradius_timer_manager_paths.py tests\unit\wan_performance\test_request_admission.py::test_site_request_uses_the_selected_organization_context --tb=short --show-capture=no
```

Expected: the admission test fails with `Site API request admission requires a selected organization.` (RC-23). Record the summary line.

## 6. Reproduction pair on the PR head (expect zero failed tests)

```powershell
Set-Location C:\Users\jmorrison\worktrees\misthelper-4797-pr
python -m pytest -q tests\unit\refactors\test_wlanradius_timer_manager_paths.py tests\unit\wan_performance\test_request_admission.py::test_site_request_uses_the_selected_organization_context --tb=short --show-capture=no
```

Expected: the summary line reports zero failed tests. Record the summary line.

## 7. Shard 1 on the PR head (Full tests row, line 87)

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
```

Expected: one summary line with zero failed tests. Record the passed and skipped counts.

## 8. Shard 2 on the PR head (Full tests row, line 88)

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

Expected: one summary line with zero failed tests.

## 9. Lint and Format on the follow-up branch (Lint row line 58, Format row line 59)

```powershell
python -m ruff check .
python -m black --check .
```

Expected: Ruff prints `All checks passed`. Black reports that no file needs a change.

## 10. Changed-file tests on the follow-up branch (Tests row, line 61)

```powershell
python -m pytest tests\unit\refactors\test_wlanradius_timer_manager_paths.py
```

Expected: every test in the file passes.

## 11. Test quality preflight on the follow-up branch (Test quality row, line 65)

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

Expected: the preflight passes.

## 12. Test quality analyzer after the local commit

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected: the gate line reports `gate: 0 new findings vs baseline`. Never rewrite `.github/test-quality-baseline.json` to hide a finding (RC-61).

## 13. Mutation check in a scratch worktree (task T006)

1. Create a scratch worktree from the follow-up commit.
2. In `fake_mh`, replace the `patch.object` line with `_MH.bind_root_module(fake)`. This matches main at line 45 (RC-08).
3. Run the changed-file tests from step 10.

Expected: both `previous_host_guard` cases report an error at teardown. Remove the scratch worktree after the run.

## 14. Verify main after the merge

```powershell
gh api "repos/jmorrison-juniper/MistHelper/contents/tests/unit/refactors/test_wlanradius_timer_manager_paths.py?ref=main" --jq .sha
```

Expected before the follow-up merges: `75b4bdc1abe393be8eadf50b0cbe299f23cfa458` (RC-10).

## 15. Remove the worktrees after the checks

```powershell
git -C "$repo" worktree remove C:\Users\jmorrison\worktrees\misthelper-4797-candidate
git -C "$repo" worktree remove C:\Users\jmorrison\worktrees\misthelper-4797-pr
```
