# Quickstart: Stranded Branch Preservation

**Purpose**: Reproduce the scope, run the preservation steps, and verify each step for issue #4583.

**Repository**: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`. The record never writes to this path until task T007.

## Prerequisites

- Install `gh` and `git`. Use the account that holds write access to the repository.
- Run each command in PowerShell from the worktree of the record branch.
- Do not switch branches in a checkout that another session uses.

## Token Setup

Set both variables before each `gh` command. Do not print either value.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## Q-1 Open Pull Requests and Holds

Read the open pull requests and the files that each one changes.

```powershell
gh pr list --repo jmorrison-juniper/MistHelper --state open --json number,title,headRefName,isDraft,files
```

Expected at the snapshot: seven open pull requests, numbered #4208, #4813, #4886, #4887, #4888, #4889, and #4890.

## Q-2 Scope Check and Work Order

Run this script to print the work order. Each row is one in-scope branch. Ready rows come first, and held rows follow in order of their blocking pull request.

If `git -C <repo> cat-file -t <main SHA>` does not print `commit`, run `git -C <repo> fetch origin main` first.

```powershell
$repo = 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper'
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
$main = gh api repos/jmorrison-juniper/MistHelper/git/ref/heads/main --jq .object.sha
$nowEpoch = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$openPrs = gh pr list --repo jmorrison-juniper/MistHelper --state open --limit 100 --json number,headRefName,files | ConvertFrom-Json
$openNames = New-Object 'System.Collections.Generic.HashSet[string]'
$owners = @{}
foreach ($pr in $openPrs) {
    [void]$openNames.Add($pr.headRefName)
    foreach ($file in $pr.files) {
        if (-not $owners.ContainsKey($file.path)) {
            $owners[$file.path] = New-Object System.Collections.Generic.List[string]
        }
        $owners[$file.path].Add('#' + $pr.number)
    }
}
$allPrs = gh pr list --repo jmorrison-juniper/MistHelper --state all --limit 6000 --json headRefName,headRefOid,state | ConvertFrom-Json
$closedHeads = @{}
foreach ($pr in $allPrs) {
    if ($pr.state -ne 'OPEN') {
        if (-not $closedHeads.ContainsKey($pr.headRefName)) {
            $closedHeads[$pr.headRefName] = New-Object System.Collections.Generic.List[string]
        }
        $closedHeads[$pr.headRefName].Add($pr.headRefOid)
    }
}
$branchLines = @(gh api 'repos/jmorrison-juniper/MistHelper/branches?per_page=100' --paginate --jq '.[] | .name + " " + .commit.sha')
$stranded = New-Object System.Collections.Generic.List[object]
foreach ($line in $branchLines) {
    $fields = $line -split ' '
    $name = $fields[0]
    $sha = $fields[1]
    if ($name -eq 'main') {
        continue
    }
    if ($openNames.Contains($name)) {
        continue
    }
    if ($name.StartsWith('dependabot/') -or $name.StartsWith('gh-readonly-queue/') -or $name.StartsWith('revert-')) {
        continue
    }
    $ahead = [int]((git -C $repo rev-list --count "$main..$sha") -join '')
    if ($ahead -eq 0) {
        continue
    }
    $epoch = [int64]((git -C $repo log -1 --format=%ct $sha) -join '')
    $ageDays = [math]::Floor(($nowEpoch - $epoch) / 86400)
    if ($ageDays -lt 7) {
        continue
    }
    $isProtected = $false
    $isUnknown = $false
    if ($closedHeads.ContainsKey($name)) {
        foreach ($prHead in $closedHeads[$name]) {
            git -C $repo merge-base --is-ancestor $sha $prHead
            $exitCode = $LASTEXITCODE
            if ($exitCode -eq 0) {
                $isProtected = $true
                break
            }
            if ($exitCode -ne 1) {
                $isUnknown = $true
            }
        }
    }
    if ($isProtected -or $isUnknown) {
        continue
    }
    $behind = [int]((git -C $repo rev-list --count "$sha..$main") -join '')
    $mergeBase = (git -C $repo merge-base $main $sha) -join ''
    $files = @(git -C $repo diff --name-only $mergeBase $sha)
    $holdPrs = @($files | Where-Object { $owners.ContainsKey($_) } | ForEach-Object { $owners[$_] } | ForEach-Object { $_ } | Sort-Object -Unique)
    $lane = 'ready'
    if ($holdPrs.Count -gt 0) {
        $lane = $holdPrs[0]
    }
    $record = [pscustomobject]@{
        Name = $name
        Sha = $sha
        Ahead = $ahead
        Behind = $behind
        Age = $ageDays
        Files = $files.Count
        Lane = $lane
    }
    $stranded.Add($record)
}
$ready = @($stranded | Where-Object { $_.Lane -eq 'ready' } | Sort-Object Name)
$held = @($stranded | Where-Object { $_.Lane -ne 'ready' } | Sort-Object Lane, Name)
$order = @($ready) + @($held)
$row = 0
foreach ($item in $order) {
    $row++
    Write-Output ("$row | $($item.Name) | $($item.Sha) | $($item.Ahead) | $($item.Behind) | $($item.Age) | $($item.Files) | $($item.Lane)")
}
Write-Output ("in_scope=" + $order.Count + " ready=" + $ready.Count + " held=" + $held.Count)
```

Read the output in pages of 100 rows. Each batch starts with a new run of this script.

## Preserve One Branch

Run these steps for each ready row in order. Finish all five steps before the next row.

Step 1 creates the draft pull request. Use the exact values from the work order row.

```powershell
gh pr create --repo jmorrison-juniper/MistHelper --draft --base main --head <branch> --title "chore(git): preserve stranded branch <branch>" --body "Preservation only. The head of <branch> stays at <head SHA>. The pull request closes without merge in the same step. Refs #4583."
```

Step 2 reads the number of the new pull request.

```powershell
gh pr list --repo jmorrison-juniper/MistHelper --head <branch> --state open --json number --jq '.[0].number'
```

Step 3 closes the pull request without merge and writes the proof.

```powershell
gh pr close <number> --repo jmorrison-juniper/MistHelper --comment "Preservation proof. Branch <branch> keeps head <head SHA> on origin. This pull request closed without merge. Reopen it to review the branch. Issue #4583."
```

Warning: The option `--delete-branch` deletes the branch from origin. Never add it to the close command.

Step 4 verifies the pull request. The output must show `CLOSED`, a null `mergedAt`, the branch name, and the head SHA.

```powershell
gh pr view <number> --repo jmorrison-juniper/MistHelper --json state,mergedAt,headRefName,headRefOid,title
```

Step 5 verifies the branch. The output must equal the head SHA from the work order.

```powershell
gh api repos/jmorrison-juniper/MistHelper/git/ref/heads/<branch> --jq .object.sha
```

Pacing: Wait five seconds before the next row.

```powershell
Start-Sleep -Seconds 5
```

If a GitHub call returns HTTP 403 or 429, wait 60 seconds, then 120 seconds, then 240 seconds. After three retries, stop the run and record the row.

Caution: A failed close leaves one open preservation pull request. Close that pull request before any new create.

## Q-3 Hold Release Check

Run this check before processing a held group. Replace the number with the blocking pull request.

```powershell
gh pr view <blocking number> --repo jmorrison-juniper/MistHelper --json state,mergedAt --jq '.state'
```

The output must be `CLOSED` or `MERGED`. After the release, run Q-2 again. Each released row then moves to the ready lane.

## Q-4 Repository Guards

Run these two guard tests in the worktree of the record branch after the record files exist.

```powershell
python -m pytest tests/guardrails/test_spec_route_contract.py tests/guardrails/test_process_folder_structure.py
```

Expected result: every test passes.

## Q-5 Final Scope Check

Run Q-2 after the last batch. The final line must show `in_scope=0`.

## Q-6 Record Style Check

Run the STE linter on each Markdown file of the record in the worktree.

```powershell
ste-linter --config .ste-linter.toml --min-score 80 <record file>
```

Expected result: each file scores 80 or above.

## Q-7 Record Style and Secret Scan

Search the record for forbidden tokens. The pattern covers placeholders, semicolons, contractions, and token prefixes.

```powershell
Get-ChildItem -LiteralPath <record folder> -Recurse -File -Include *.md, *.json | Select-String -Pattern 'T[B]D|TO[D]O|to[ ]be[ ]decid|\.\.\.|n''t|\x3B|gh[pos]_|github_p[a]t_'
```

Expected result: no output.

## Q-8 Directory Count Check

Count the children of each directory in the record. Each count must be five or fewer.

```powershell
Get-ChildItem -LiteralPath <record folder> -Recurse -Directory | ForEach-Object { '{0} {1}' -f $_.FullName, @(Get-ChildItem -LiteralPath $_.FullName -Force).Count }
```

## Verification Checks

Each check has one ID. The tasks name these IDs.

| ID | Check | Method | Expected result | Covers |
| - | - | - | - | - |
| V-01 | Work order count | Q-2 | `in_scope` equals the count in the snapshot or a documented later count | FR-001, FR-002, FR-011, FR-012 |
| V-02 | Hold lanes | Q-2 `Lane` column | Held rows name the open pull request that blocks them | FR-003 |
| V-03 | One open preservation pull request | `gh pr list --state open --search "in:title preserve stranded branch"` | No result between steps | FR-004 |
| V-04 | Closed and unmerged | Q-1 verification read | `CLOSED` and null `mergedAt` | FR-005, FR-009 |
| V-05 | Proof comment | `gh pr view <number> --json comments` | One comment starts with `Preservation proof.` | FR-008 |
| V-06 | Branch head unchanged | Step 5 | Head SHA equals the work order value | FR-007, FR-009 |
| V-07 | Title pattern | Verification read | Title matches the pattern in the contract | FR-006 |
| V-08 | Body content | `gh pr view <number> --json body` | Body contains the head SHA and `Refs #4583` | FR-006 |
| V-09 | Hold release | Q-3 | `CLOSED` or `MERGED` before the held group runs | FR-013 |
| V-10 | No branch removed | `gh api repos/jmorrison-juniper/MistHelper/branches?per_page=100 --paginate` count | Count does not decrease from 598 | FR-007, SC-003 |
| V-11 | Final scope | Q-5 | `in_scope=0` | FR-012, FR-014, SC-002 |
| V-12 | Guard tests | Q-4 | All tests pass | FR-015 |
| V-13 | STE score | Q-6 | Each file scores 80 or above | FR-015 |
| V-14 | Summary length | Length of the summary text | 2500 characters or fewer | FR-018 |
| V-15 | Report issues | `gh issue list --state open --search "a branch holds work with no pull request in:title"` | Five issues at the snapshot | FR-016 |
| V-16 | Failure log | Execution log review | Each stop and backoff has one entry | FR-010 |
| V-17 | Record pull request files | `gh pr view --json files` | Each path starts with the record route | FR-014, FR-015 |
| V-18 | Remote row parity | Count of `remote_checks` and table rows | Both counts equal 54 | FR-017 |
| V-19 | Forbidden tokens | Q-7 | No output | FR-018 |

## Rollback

Reopen a closed preservation pull request to review its branch. Reopen only after the open count is zero.

```powershell
gh pr reopen <number> --repo jmorrison-juniper/MistHelper
```

Caution: A reopened pull request is open again. Close it before starting another create.

If a branch is missing, restore it from its pull request head. The push never overwrites an existing branch.

```powershell
git -C <repo> push origin <head SHA>:refs/heads/<branch>
```

Revert a merged record pull request with a new pull request that reverts the merge commit.
