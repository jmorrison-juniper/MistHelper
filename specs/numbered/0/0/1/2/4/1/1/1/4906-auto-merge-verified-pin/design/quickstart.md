# Quickstart: Reproduce and Verify Issue 4906

Run these two lines before each `gh` command. Shell state does not persist between commands.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## Part 1: Reproduce the failure (read only)

### Step 1. Read the failed log lines

```powershell
gh run view 45064239338 -R jmorrison-juniper/MistHelper --log-failed | Select-String -Pattern "FAILED tests|1 failed, 2345 passed|coverage shards finished with failure"
```

Expected output:

- `FAILED tests/guardrails/test_auto_merge_issue_close.py::TestAutoMergeJob::test_merge_recovery_uses_the_verified_shared_commit`
- `= 1 failed, 2345 passed, 18 skipped, 5 xfailed, 1 warning in 305.79s (0:05:05) =`
- `::error::The coverage shards finished with failure.`

### Step 2. Read the failing checks on the pull request

```powershell
gh pr checks 4886 -R jmorrison-juniper/MistHelper
```

Expected: `pytest (coverage gate)` and `pytest coverage shard (root-and-contracts)` report `fail`.

### Step 3. Read the pin on main

```powershell
$raw = gh api "repos/jmorrison-juniper/MistHelper/contents/.github/workflows/auto-merge.yml?ref=main" --jq .content
$text = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(($raw -replace '\s', '')))
$text -split "`n" | Select-Object -Index 60
```

Expected: line 61 names `reusable-auto-merge.yml@d63a120487cecf750184cb178387cdc25c0a7635`.

### Step 4. Read the verified commit on main

```powershell
$raw = gh api "repos/jmorrison-juniper/MistHelper/contents/tests/guardrails/test_auto_merge_issue_close.py?ref=main" --jq .content
$text = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(($raw -replace '\s', '')))
$text -split "`n" | Select-Object -Index 45
```

Expected: line 46 is `VERIFIED_MERGE_RECOVERY_COMMIT = "d63a120487cecf750184cb178387cdc25c0a7635"`.

### Step 5. Read the pin on the pull request head

```powershell
$raw = gh api "repos/jmorrison-juniper/MistHelper/contents/.github/workflows/auto-merge.yml?ref=9e70001433bae97055b6bbe2825a345c0674273e" --jq .content
$text = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(($raw -replace '\s', '')))
$text -split "`n" | Select-Object -Index 60
```

Expected: line 61 names `reusable-auto-merge.yml@2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.

## Part 2: Confirm the reviewed evidence (read only)

### Step 6. Compare the blob SHA of the reusable workflow at both commits

```powershell
gh api "repos/jmorrison-juniper/misthelper-devtools/contents/.github/workflows/reusable-auto-merge.yml?ref=d63a120487cecf750184cb178387cdc25c0a7635" --jq .sha
gh api "repos/jmorrison-juniper/misthelper-devtools/contents/.github/workflows/reusable-auto-merge.yml?ref=2239e7bd468fd27e40c43f2b87fcd35a2e49672b" --jq .sha
```

Expected: both lines print `08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8`.

### Step 7. Read the check runs at the new upstream commit

```powershell
gh api "repos/jmorrison-juniper/misthelper-devtools/commits/2239e7bd468fd27e40c43f2b87fcd35a2e49672b/check-runs" --jq '.check_runs[].conclusion'
```

Expected: each line prints `success`.

## Part 3: Apply and verify the change (implementation session)

### Step 8. Create the worktree and bootstrap its environment

```powershell
git fetch origin main
git worktree add ..\MistHelper-fix-4906 -b fix/4906-auto-merge-verified-pin origin/main
Set-Location ..\MistHelper-fix-4906
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

A new worktree holds no `.venv`, so the bootstrap runs once in this worktree. Run every later step inside the new worktree folder.

### Step 9. Apply tasks T002 and T003

- Line 61 of `.github/workflows/auto-merge.yml` names `reusable-auto-merge.yml@2239e7bd468fd27e40c43f2b87fcd35a2e49672b` and keeps `# Verified post-merge dispatch`.
- Line 46 of `tests/guardrails/test_auto_merge_issue_close.py` names `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`. Add the two comment lines above it and the inline comment `# Verified: same blob as d63a120` on the same line.

### Step 10. Run the guard file

```powershell
python -m pytest tests/guardrails/test_auto_merge_issue_close.py
```

Expected: `17 passed`.

Optional before-fix check: in a separate worktree, run `gh pr checkout 4886` and the same command. Expected: `1 failed, 16 passed`.

### Step 11. Run lint, format, and compile

```powershell
python -m ruff check .
python -m black --check .
python -m py_compile MistHelper.py
```

Expected: `All checks passed`, then `No file needs a change`, then no output.

### Step 12. Run symbol and security checks on the changed guard file

```powershell
symbol-diff --base origin/main tests/guardrails/test_auto_merge_issue_close.py
bandit -c pyproject.toml -r tests/guardrails/test_auto_merge_issue_close.py -q
```

Expected: `no module-level name changed` with exit code 0, and no Bandit finding.

### Step 13. Run the test-quality analyzer after the local commit

Commit the intended files first. Then run the command from `.github/copilot-instructions.md` lines 127 to 131 with `BASE_REF` set to `main`:

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected: the line `gate: 0 new findings vs baseline` reports zero findings.

### Step 14. Run the record guards (task T005)

```powershell
python -m pytest tests/guardrails/test_process_folder_structure.py
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
python -m pytest tests/guardrails/test_spec_route_contract.py
```

Expected: each command passes. The third command calls PowerShell. Run it where `pwsh` is available.

### Step 15. Run the writing-style check on the record

```powershell
$files = Get-ChildItem specs\numbered\0\0\1\2\4\1\1\1\4906-auto-merge-verified-pin -Recurse -Filter *.md | ForEach-Object { $_.FullName }
ste-linter --config .ste-linter.toml --min-score 80 $files
```

Expected: each file scores 80 or above.

### Step 16. Run the citation lint and the advisory task audit

```powershell
check-citations src tests
speckit-task-audit
```

Expected: `check-citations` exits with code 0. CI ignores the exit code of `speckit-task-audit` (`.github/workflows/ci.yml` line 750).

### Step 17. Search for the old commit

```powershell
git grep -n d63a120487cecf750184cb178387cdc25c0a7635
```

Expected: matches appear only under `specs/numbered/0/0/1/2/4/1/1/1/4906-auto-merge-verified-pin/`. The pin and the verified commit no longer name it.

## Part 4: Publish and merge (tasks T-PR, T-REMOTE-CI, and T-MERGE)

### Step 18. Commit, push, and open the replacement pull request

```powershell
git add .github/workflows/auto-merge.yml tests/guardrails/test_auto_merge_issue_close.py specs/numbered/0/0/1/2/4/1/1/1/4906-auto-merge-verified-pin
git commit -m "fix(ci): pin the verified auto-merge commit" -m "Closes #4906" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
git push --force-with-lease -u origin fix/4906-auto-merge-verified-pin
gh pr create -R jmorrison-juniper/MistHelper --base main --head fix/4906-auto-merge-verified-pin --title "fix(ci): pin the verified auto-merge commit" --body "Closes #4906. Supersedes pull request 4886. No changelog fragment: the change is internal only. Local gate results and the blob evidence are in the spec record."
```

Expected: the pull request title passes the `Conventional Commits PR title` check.

### Step 19. Watch the remote CI run

```powershell
gh pr checks -R jmorrison-juniper/MistHelper --watch
```

Run this command in the fix worktree, so the current branch names the pull request. Expected: every required check passes. Stop and report each failed check that the guard does not cause.

### Step 20. Verify main after the merge

Repeat steps 3 and 4 with `?ref=main`. Expected: line 61 and line 46 both name `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`. Then run the guard file on a fresh checkout of main. Expected: `17 passed`.

Remove the worktree and the local branch after the merge. Run these commands from the main checkout.

```powershell
git worktree remove ..\MistHelper-fix-4906
git branch -d fix/4906-auto-merge-verified-pin
```

Caution: `gh pr close` removes the open update from the queue, and reopening needs an authorization. Run the close only after the replacement merges.

```powershell
gh pr close 4886 -R jmorrison-juniper/MistHelper --comment "Superseded by the merged replacement pull request for issue 4906. Each file examined on main: .github/workflows/auto-merge.yml and tests/guardrails/test_auto_merge_issue_close.py."
```
