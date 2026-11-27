# Quickstart: Reproduce and Verify Issue 4779

Use these steps to reproduce the issue and to verify the repair. Run each command from PowerShell.

## Prerequisites

- A Windows 11 host with the publication worktree at `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-feat-4773`.
- The worktree `.venv` interpreter. If `.venv` is absent, run the bootstrap in `documentation/development-setup.md` lines 178 to 186. The bootstrap command is `python scripts/bootstrap_worktree.py`.
- The read-only GitHub token from the account variable named in the brief.

## Step 1: Confirm that GitHub main lacks the CLI

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh api "repos/jmorrison-juniper/MistHelper/contents/src/mist/realtime/websocket_streams/web/services/operations/hardware/cli.py?ref=main" --jq .sha
```

Expected before publication: a `Not Found` error (HTTP 404). Research row R-03 records this result.

## Step 2: Confirm the local commit

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" cat-file -t 8140bb37c
```

Expected: `commit`. The commit exists in the local object store only.

## Step 3: Reproduce the three regression cases

```powershell
Set-Location "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-feat-4773"
.venv\Scripts\python.exe -m pytest -q tests/unit/websocket_streams/web/hardware/test_cli.py -k never_retries --tb=short
```

Expected on the committed code: three passed. The issue reports three failures. Record the actual output in T001. The static reading of `cli.py` predicts a pass.

## Step 4: Check the removed patterns after the repair

```powershell
Select-String -Path "src\mist\realtime\websocket_streams\web\services\operations\hardware\cli.py" -Pattern "except Exception"
Select-String -Path "src\mist\realtime\websocket_streams\web\services\operations\hardware\cli.py" -Pattern "Admitted:"
```

Expected after the repair: no output from either command (SC-003, check C-4).

## Step 5: Check the caution texts after the repair

```powershell
Select-String -Path "src\mist\realtime\websocket_streams\web\services\operations\hardware\cli.py" -Pattern "may have started|may still be active"
```

Expected after the repair: at least two matching lines. One line holds the uncertain caution and one holds the admitted caution.

## Step 6: Run the full CLI test module after the repair

```powershell
.venv\Scripts\python.exe -m pytest -q tests/unit/websocket_streams/web/hardware/test_cli.py --tb=short
```

Expected: every case passes. Record the total count in T-LOCAL-GATES.

## Step 7: Verify the pushed commit (after T-PR)

```powershell
$worktree = "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-feat-4773"
$pushedSha = (git -C $worktree rev-parse HEAD).Trim()
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
$tree = (gh api "repos/jmorrison-juniper/MistHelper/git/trees/$pushedSha?recursive=1" | ConvertFrom-Json).tree
$tree | Where-Object { $_.path -match 'operations/hardware/cli.py|operations/hardware/preset.py|hardware/test_cli.py|operator-guide.md|changelog.d/issue-4773' } | ForEach-Object { Write-Output ($_.path + " " + $_.sha) }
```

Expected: five lines, one for each changed file, each with a blob SHA (check C-2 and SC-004).

## Step 8: Check the pull request body (after T-PR)

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh pr view -R jmorrison-juniper/MistHelper --json body --jq .body
```

Run the command from the publication worktree. It reads the pull request for the current branch. Expected: the body contains `Closes #4779` and `Refs #4773` (check C-1).

## Cleanup

These steps create no temporary file and start no container. Test evidence, when a gate writes it, stays under the git-ignored `test-artifacts/` folder.
