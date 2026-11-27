# Quickstart: Preserve Repository Versions and Update the Local Main Checkout

This file gives the exact commands for each verification test (V-01 to V-15). Each command is read-only unless the step names a write to `test-artifacts\4277\`, a sibling worktree, or the record path.

## Prerequisites

- A Windows host with PowerShell, Git 2.49.0, and the GitHub CLI `gh`.
- Read access through `gh`. Set `GH_HOST` to `github.com`. Set `GH_TOKEN` from the account variable named `COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper`. Never print either value.
- The primary checkout at `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`.

## Session setup

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
$repo = 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper'
$record = 'specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions'
```

## Scenario 1: Remote main and baseline ancestry (V-01)

```powershell
rtk proxy gh api repos/jmorrison-juniper/MistHelper/git/ref/heads/main --jq .object.sha
rtk proxy git -C $repo rev-list --count origin/main ^9ba3a7e5ca8f3c371e58887531623a249510d7df
rtk proxy git -C $repo merge-base --is-ancestor 9ba3a7e5ca8f3c371e58887531623a249510d7df origin/main
```

Expected result at measurement: the GitHub main head is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The count is 313. The ancestor check exits with code 0.

## Scenario 2: Primary checkout equality (V-02)

```powershell
rtk proxy git -C $repo rev-parse HEAD
rtk proxy git -C $repo rev-parse origin/main
rtk proxy git -C $repo rev-list --count origin/main ^main
rtk proxy git -C $repo rev-list --count main ^origin/main
rtk proxy git -C $repo rev-parse --is-shallow-repository
```

Expected result: HEAD equals `origin/main`. Both counts are 0. The repository is not shallow.

## Scenario 3: PR 4404 and issue 4280 (V-03)

```powershell
rtk proxy gh api repos/jmorrison-juniper/MistHelper/pulls/4404 --jq '[.merged, .merge_commit_sha, .merged_by.login] | @tsv'
rtk proxy git -C $repo merge-base --is-ancestor 31b752f060d4d10cbe87b5880b071b6570d0b3c9 origin/main
rtk proxy gh issue view 4280 -R jmorrison-juniper/MistHelper --json state --jq .state
```

Expected result: the pull request is merged by `jmorrison-juniper`. The merge commit is an ancestor of `origin/main`. Issue 4280 is `CLOSED`.

## Scenario 4: Cited commits (V-04)

Run this loop. It prints the remote and local result for each cited commit.

```powershell
foreach ($sha in @('9ba3a7e5ca8f3c371e58887531623a249510d7df', '3ead4ec424bfbda1c3edb739c963d02604201c4a', '6e1977105d0b5c4fad2a3018f070fd601b2ada4b', '29c5489751ed84a8595cefe85f0e2aa7716b8608', '31b752f060d4d10cbe87b5880b071b6570d0b3c9', '850864931c3af94fbe5ff1c73678e0141cf3ffb4', '7d16297d4314113287c7c78851ebdfa643800278', '3cf37c7cf2ef5e9d42f9ca550172cda6ca4d0f5b', 'd89009846b648aae15ce05a36cc02f053f83cab8')) {
  $remote = rtk proxy gh api ('repos/jmorrison-juniper/MistHelper/commits/' + $sha) --jq .sha 2>$null
  $local = rtk proxy git -C $repo cat-file -t $sha 2>$null
  '{0} remote={1} local={2}' -f $sha, $remote, $local
}
```

Expected result: the three privacy commits, `7d16297d`, `3cf37c7c`, and `d8900984`, show no remote result and no local result at measurement.

## Scenario 5: Branch register (V-06)

```powershell
rtk proxy git -C $repo for-each-ref --format='%(refname) %(objectname)' refs/heads
rtk proxy git -C $repo for-each-ref --merged=main --format='%(refname)' refs/heads
rtk proxy git -C $repo for-each-ref --format='%(refname) %(objectname)' refs/remotes/origin
```

Write one row for each local head into `test-artifacts\4277\branch-register.tsv`. Each row follows the contract in `design\contracts\branch-disposition-register.md`. The row count equals the count of `refs/heads` entries from the first command.

## Scenario 6: Preservation of modified entries (V-07)

```powershell
rtk proxy git -C $repo --no-optional-locks status --porcelain
rtk proxy git -C $repo diff > test-artifacts\4277\modified-files.patch
$preserve = Join-Path $repo 'test-artifacts\4277\preserved-files'
New-Item -ItemType Directory -Force -Path $preserve | Out-Null
Get-ChildItem -LiteralPath $preserve -Recurse -File | Get-FileHash -Algorithm SHA256 | Out-File -FilePath (Join-Path $repo 'test-artifacts\4277\modified-files.sha256')
```

Copy each modified file into `test-artifacts\4277\preserved-files\` with its relative path before the hash step. Expected result: five copies and five hashes. The primary checkout keeps each file unchanged.

## Scenario 7: Zero deletion counts (V-08)

```powershell
(rtk proxy git -C $repo for-each-ref --format='%(refname)' refs/heads | Measure-Object).Count
(rtk proxy git -C $repo for-each-ref --format='%(refname)' refs/tags | Measure-Object).Count
(rtk proxy git -C $repo for-each-ref --format='%(refname)' refs/stash | Measure-Object).Count
(rtk proxy git -C $repo for-each-ref --format='%(refname)' refs/copilot-preserved | Measure-Object).Count
(rtk proxy git -C $repo for-each-ref --format='%(refname)' refs/copilot | Measure-Object).Count
(rtk proxy git -C $repo for-each-ref --format='%(refname)' refs/agents | Measure-Object).Count
(Get-ChildItem -LiteralPath (Join-Path $repo '.git\worktrees') -Force | Measure-Object).Count
```

Expected result at measurement: 330, 190, 1, 6, 1123, 434, and 33. Each count equals its count before the work.

## Scenario 8: Baseline worktree and static gates (V-09)

```powershell
rtk proxy git -C $repo worktree add --detach 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-4277-baseline' f03c6c9b36d612a48d7b9652998c2fd87dd777ca
Set-Location 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-4277-baseline'
python scripts\bootstrap_worktree.py
.venv\Scripts\python.exe -m py_compile MistHelper.py
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m black --check .
.venv\Scripts\python.exe -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
```

Expected result: each command exits with code 0. The lint command prints `All checks passed`. The format command reports no file that needs a change.

## Scenario 9: Full test shards (V-10)

```powershell
.venv\Scripts\pytest-chunks.exe -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
.venv\Scripts\pytest-chunks.exe -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

Expected result: each shard prints one summary line with zero failures. Record both lines in `design\contracts\validation-report.md`.

## Scenario 10: Safe sweep (V-11)

```powershell
.venv\Scripts\python.exe MistHelper.py --test
```

Expected result: the command exits with code 0. The Mist checks skip with a credential reason, because the baseline holds no `.env` file.

## Scenario 11: Baseline removal (V-14)

```powershell
rtk proxy git -C $repo worktree remove 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-4277-baseline'
Test-Path -LiteralPath 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-4277-baseline'
```

Expected result: the removal exits with code 0. `Test-Path` returns `False`.

## Scenario 12: Route and recovery register (V-12 and V-13)

Run this guard from the record worktree after the record is copied there:

```powershell
.venv\Scripts\python.exe -m pytest tests\guardrails\test_process_folder_structure.py
```

Count the recovery rows in the register:

```powershell
(Select-String -LiteralPath (Join-Path $record 'design\contracts\recovery-register.md') -Pattern '^\| U-' | Measure-Object).Count
```

Expected result: the guard passes. The row count is 9. Each row holds an owner and a close condition.

## Scenario 13: Record Markdown gate (T-LOCAL-GATES)

```powershell
Get-ChildItem -LiteralPath $record -Recurse -Filter *.md | ForEach-Object { & .\.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 $_.FullName }
```

Expected result: each file scores 80 or above. The command prints one score line for each file.

## Scenario 14: Pull request scope (V-15)

Run this command from the record worktree after the pull request opens:

```powershell
rtk proxy gh pr view --json files --jq '.files[].path'
```

Expected result: every path starts with the record path. No other path appears.

## Record branch, commit, and pull request

1. Fetch GitHub main with `rtk proxy git -C $repo fetch origin main`.
2. Create the record worktree from `origin/main` with `rtk proxy git -C $repo worktree add -b chore/4277-preserve-repository-versions 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-4277-record' origin/main`.
3. Run `python scripts\bootstrap_worktree.py` inside the record worktree.
4. Create the record folder with `New-Item -ItemType Directory -Force` and copy the twelve record files into it.
5. From inside the record worktree, stage only the record path with `rtk proxy git add -- specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions`.
6. Commit with a message file. The subject is `chore(specs): add repository preservation record for issue 4277`. The body is `Refs #4277`. Add the trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`.
7. Push with `rtk proxy git push -u origin chore/4277-preserve-repository-versions`.
8. Open the pull request with the command below. Its title is the subject from step 6.

```powershell
rtk proxy gh pr create --title 'chore(specs): add repository preservation record for issue 4277' --body-file test-artifacts\4277\pr-body.md --label chore --label docs --label in-progress
```
9. Watch the checks with `rtk proxy gh pr checks --watch`.
10. After every check is green and the orchestrator authorizes the merge, run `rtk proxy gh pr edit --add-label auto-merge`.

Caution: remove the record worktree only after the merge. Run `rtk proxy git worktree remove` with its full path.
