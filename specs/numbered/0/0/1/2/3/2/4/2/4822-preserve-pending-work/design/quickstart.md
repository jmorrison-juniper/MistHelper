# Quickstart: Preserve Pending Work Before Branch Cleanup

Run each command from the repository root. Set the GitHub account before each `gh` command. Each command reads state and writes nothing, except where a step names a write.

## Step 1: Set the GitHub account

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## Step 2: Read the issue

```powershell
gh issue view 4822 -R jmorrison-juniper/MistHelper --json number,title,state,labels,comments
```

Expected result: The state is OPEN. The labels are `chore` and `tests`. Three owner comments appear.

## Step 3: Inventory the snapshot tags

```powershell
git for-each-ref refs/tags/recovery/4822 --format="%(refname) %(objectname) %(objecttype)"
```

Expected result: Nine lines. Each line names a commit.

## Step 4: Inventory the recovery branches

```powershell
$branches = @('chore/2746-recovered-specification', 'fix/2977-recovered-content-dedup', 'feat/4631-recovered-offline-preview', 'docs/4822-recovered-vmm-export')
foreach ($branch in $branches) {
    git rev-parse --verify ("refs/heads/" + $branch)
    git rev-list --count ("main.." + $branch)
    git rev-list --count ($branch + "..main")
    git merge-base main $branch
}
```

Expected result: Each tip begins with its identifier in `design/research.md`. Each merge base is `b7a18b7ead7b1de5882bcd288203c015b1eef792`. The first count is 1, and the second count is 42.

## Step 5: Classify each snapshot file against main

```powershell
$snapshots = @('2f549a95ec402c12787ed1020bc4bcc238427178', '3507045565bcee50be0e3043f6435fe1f6b7be23', '2b10a07f4580567f2e35091bd6c0f5cc53482db1', '6c66f04c21d219cbf936f6c5a03bab891f74dafc', '61eec0829b28db796901d95aff2472020eef1b53', '69a51a9c63dcd3ee372e84dc3bc2ebc98f61c022', '6256c776a7e466d7b95e97196df5a52c51a19545', '61de973cfd6375898b7bb9319ca08ad49240f247', 'f4d8922b838e6f83f428e3bcb7171584638d410e')
foreach ($snapshot in $snapshots) {
    foreach ($path in git diff-tree -r --no-commit-id --name-only $snapshot) {
        $snapshotBlob = git rev-parse ($snapshot + ":" + $path)
        $mainBlob = git rev-parse --verify --quiet ("main:" + $path)
        if (-not $mainBlob) { "absent: " + $path } elseif ($mainBlob -eq $snapshotBlob) { "identical: " + $path } else { "different: " + $path }
    }
}
```

Expected result: Totals match the snapshot table in `design/research.md`. Each `different` or `absent` line names a pending change.

## Step 6: Compare the two Labs snapshots

```powershell
$first = '2b10a07f4580567f2e35091bd6c0f5cc53482db1'
$second = '6c66f04c21d219cbf936f6c5a03bab891f74dafc'
foreach ($path in git diff-tree -r --no-commit-id --name-only $first) {
    if ((git rev-parse ($first + ":" + $path)) -eq (git rev-parse --verify --quiet ($second + ":" + $path))) { "identical: " + $path } else { "different: " + $path }
}
```

Expected result: Twenty-nine `identical` lines and no `different` line.

## Step 7: Check the remote recovery copies

```powershell
gh api repos/jmorrison-juniper/MistHelper/branches/chore/2746-recovered-specification
gh api repos/jmorrison-juniper/MistHelper/git/matching-refs/tags/recovery/4822
gh api repos/jmorrison-juniper/MistHelper/commits/c06ea6ce1bb58a0881719b728677cae9573562c7
gh api repos/jmorrison-juniper/MistHelper/compare/b7a18b7ead7b1de5882bcd288203c015b1eef792...f03c6c9b36d612a48d7b9652998c2fd87dd777ca
```

Expected result: The branch lookup returns HTTP 404. The tag list is empty. The commit lookup returns HTTP 422. The compare status is `ahead` with zero commits behind.

## Step 8: Read the worktree registrations and admin directories

```powershell
git worktree list --porcelain
Get-ChildItem -Force .git\worktrees
```

Expected result: Thirty-four registrations, including the main checkout. Two registrations are prunable. Their admin directories remain.

## Step 9: Confirm that the merge candidates are merged by git

```powershell
git rev-list --count main..feat/4631-offline-jvd-preview
git merge-base --is-ancestor feat/4631-offline-jvd-preview main
git rev-list --count main..agents/ok-make-that-change-then-reun-that-report
git merge-base --is-ancestor agents/ok-make-that-change-then-reun-that-report main
```

Expected result: Each count is 0. Each ancestor command exits with code 0.

## Step 10: Run the record gates

```powershell
.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/spec.md specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/plan.md specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/tasks.md specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/analysis.md specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/design/research.md specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/design/data-model.md specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/design/quickstart.md specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/design/checklists/requirements.md specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/design/checklists/recovery.md
python -m pytest tests/guardrails/test_spec_route_contract.py tests/guardrails/test_process_folder_structure.py
```

Expected result: Each file scores 80 or above. Both guard tests pass. Run the linter in each mode that `documentation/quality-gates.md` describes.

## Step 11: Run the focused offline test on the main export

```powershell
New-Item -ItemType Directory -Force test-artifacts\4822\main | Out-Null
git archive --format=tar main | tar -x -C test-artifacts\4822\main
Set-Location test-artifacts\4822\main
python -B -m pytest -p no:cacheprovider -q -rs tests/unit/juniper_docs/test_content_dedup.py
Set-Location ..\..\..
```

Expected result: No failure. The command runs inside the export folder, with the existing `.venv` active. Step 11 writes only inside `test-artifacts`.
