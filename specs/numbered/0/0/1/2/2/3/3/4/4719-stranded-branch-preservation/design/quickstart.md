# Quickstart: Stranded Branch Preservation

This file gives the exact reproduction steps and the verification checks for issue #4719. Every command is read-only, except the preservation steps that tasks T011 to T013 and T021 name.

## Prerequisites

- PowerShell on Windows 11, `gh` with an authenticated account, and `git`.
- The local clone at `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`.
- The owner release of the publication hold, before any step that opens a pull request.

Set the account variables. Never print the token value.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
$repo = 'jmorrison-juniper/MistHelper'
$repoLocal = 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper'
```

## Step 1: Read the issue facts

```powershell
gh issue view 4719 -R $repo --json title,state,labels,createdAt,updatedAt,comments
```

Expected: the title is "chore(git): a branch holds work with no pull request", the state is OPEN, and the comment count is 25.

## Step 2: Read the current main commit

```powershell
$mainSha = (gh api "repos/$repo/git/ref/heads/main" --jq .object.sha).Trim()
$mainSha
```

Expected at the time of this record: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

## Step 3: Define the 51 branches

```powershell
$branches = @(
    'fix/3158-wip-controls',
    'fix/3168-structured-signals',
    'fix/3183-status-fallback',
    'fix/3222-confirm-details',
    'jmorrison-jnpr-snmp-fallback-delivery',
    'fix/3506-site-lock-logs',
    'recovery/2863-handoff-20261004',
    'recovery/2711-handoff-20261004',
    'recovery/3575-handoff-20261004',
    'recovery/3700-handoff-20261004',
    'recovery/3701-handoff-20261004',
    'recovery/2752-handoff-20261004',
    'recovery/2861-handoff-20261004',
    'recovery/2977-handoff-20261004',
    'recovery/3213-handoff-20261004',
    'recovery/3326-handoff-20261004',
    'recovery/3329-handoff-20261004',
    'recovery/3295-handoff-20261004',
    'recovery/3728-handoff-20261004',
    'recovery/3436-handoff-20261004',
    'recovery/3699-handoff-20261004',
    'recovery/3375-handoff-20261004',
    'recovery/3158-handoff-20261004',
    'recovery/3743-handoff-20261004',
    'recovery/3491-handoff-20261004',
    'recovery/2747-handoff-20261004',
    'recovery/3745-handoff-20261004',
    'recovery/3749-handoff-20261004',
    'recovery/3161-handoff-20261004',
    'recovery/3388-handoff-20261004',
    'recovery/3380-handoff-20261004',
    'recovery/3761-handoff-20261004',
    'recovery/3760-handoff-20261004',
    'recovery/3769-handoff-20261004',
    'recovery/2708-handoff-20261004',
    'recovery/3818-handoff-20261004',
    'recovery/3738-handoff-20261004',
    'docs/3818-campaign-stop-20261004',
    'fix/3292-isolate-retry-e2e-sites',
    'jmorrison-juniper-startup-dependency-reassessment',
    'jmorrison-juniper-fix-2863-identifier-defaults-batch-1',
    'jmorrison-juniper-assessment-4026',
    'jmorrison-juniper-issue-3416-lint-pattern',
    'jmorrison-juniper-false-success-family-4028',
    'jmorrison-jnpr-test-4035-menu-92-selection-result',
    'jmorrison-juniper-issue-2746',
    'jmorrison-juniper-coordinate-issue-work',
    'jmorrison-juniper-issue-4269-runtime-nested-feature-identity-in-speck-4a6090',
    'jmorrison-juniper-issue-2747-wan-probe-test-quality',
    'jmorrison-juniper-fix-4494-csrf-warning-prefix',
    'jmorrison-juniper-local-build-revision'
)
$branches.Count
```

Expected: 51.

## Step 4: Read each head and the local commit data

```powershell
foreach ($name in $branches) {
    $head = (gh api "repos/$repo/git/ref/heads/$name" --jq .object.sha).Trim()
    $ahead = (git -C $repoLocal rev-list --count "$mainSha..$head").Trim()
    $base = (git -C $repoLocal merge-base $mainSha $head).Trim()
    $paths = @(git -C $repoLocal diff --name-only $base $head).Count
    "$name | $($head.Substring(0, 8)) | ahead=$ahead | paths=$paths"
}
```

Expected: 51 rows. The ahead values add up to 66. The path entries add up to 515. The privacy-held branch `recovery/2977-handoff-20261004` prints counts only. Do not list its paths or subjects.

## Step 5: Read the commit subjects

```powershell
git -C $repoLocal log --format=%h%x20%s "$mainSha..$head"
```

Run this for each branch except `recovery/2977-handoff-20261004`. Expected: the subjects match `design/data-model.md`.

## Step 6: Check for pull requests that hold a head

```powershell
$pulls = gh pr list -R $repo --state all --limit 5000 --json number,headRefName,headRefOid,state | ConvertFrom-Json
$held = @($pulls | Where-Object { $branches -contains $_.headRefName })
$held.Count
```

Expected: 0 before batch 1. A nonzero count means the branch already has a pull request. Record the number and the state of each holder.

## Step 7: Check the tracking issues and the title search

```powershell
$query = 'chore(git): a branch holds work with no pull request in:title'
$titleMatches = gh issue list -R $repo --state open --search $query --limit 100 --json number,title | ConvertFrom-Json
$titleMatches.Count
$plain = gh issue list -R $repo --state open --search 'holds work with no pull request in:title' --limit 100 --json number | ConvertFrom-Json
$plain.number -join ' '
```

Expected: the first count is 0. The second command prints `4911 4818 4719 4583 4302`. The workflow query misses the open issues. The plain query finds them.

## Step 8: Check the route on main

```powershell
$tree = gh api "repos/$repo/git/trees/main?recursive=1" | ConvertFrom-Json
$leafEntries = @($tree.tree | Where-Object { $_.path -like 'specs/numbered/0/0/1/2/2/3/3/4/*' })
$leafEntries.Count
$parentChildren = @($tree.tree | Where-Object { $_.path -like 'specs/numbered/0/0/1/2/2/3/3/*' } | ForEach-Object { ($_.path.Substring('specs/numbered/0/0/1/2/2/3/3/'.Length) -split '/')[0] } | Sort-Object -Unique)
$parentChildren.Count
```

Expected: the leaf count is 0. The parent child count is 4, so one child is allowed.

## Step 9: Check the upstream workflow pin

```powershell
$devRepo = 'jmorrison-juniper/misthelper-devtools'
$pin = '79a5e45970e876f1656d69520d9635cea1aa25ef'
$devTree = gh api "repos/$devRepo/git/trees/$pin?recursive=1" | ConvertFrom-Json
$devEntry = $devTree.tree | Where-Object { $_.path -eq '.github/workflows/reusable-stranded-branch-report.yml' }
$devEntry.sha
$devBlob = gh api "repos/$devRepo/git/blobs/$($devEntry.sha)" --jq .content
$devText = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(($devBlob -replace '\s', '')))
$devText -split "`n" | Select-String -SimpleMatch '--search "${TITLE} in:title"' | Select-Object -First 1 -ExpandProperty LineNumber
```

Expected: the blob SHA is `b8ca235c93beddef9307d797da87223a920df729`, and the search line is 156.

## Step 10: Check the record files

Run these checks in the record folder. The folder is the draft folder until the record branch exists. Run the forbidden-token scan from the drafting brief on the record folder. Expected: no match.

```powershell
$recordDir = 'C:\Users\jmorrison\.copilot\session-state\30878eb1-80d0-451d-bd0c-0b3624089852\files\spec-drafts\4719'
Get-ChildItem -Path $recordDir -Recurse -Filter *.md | Select-String -Pattern ([string][char]59)
(Get-ChildItem -Path $recordDir -Force | Measure-Object).Count
(Get-ChildItem -Path (Join-Path $recordDir 'design') -Force | Measure-Object).Count
```

Expected: no output from the first two commands. The root holds 5 children. The design folder holds 5 children.

## Step 11: Run the guardrail suite on the record branch

```powershell
python -m pytest tests/guardrails -q
```

Run this command in the record worktree, not in the main checkout. Run the same command on `main` first, and save the failing test names outside the repository. Expected: no failing test that did not fail on `main`.

## Verification checks

| Check | Procedure | Expected result | Requirements |
| - | - | - | - |
| TC-01 | Steps 3 and 4 count the rows, commits, and paths. Read the 454 extra rows of issue #4911 from its body. | 51 rows. 66 commits. 515 path entries. 454 extra rows recorded. | FR-001, FR-015 |
| TC-02 | Step 6 counts pull requests that hold a head. | 0 before batch 1. | FR-002 |
| TC-03 | After task T011, run `gh pr list -R $repo --state open --json number,headRefName,body,isDraft` and check each body. | 46 draft pull requests. Each body names its branch, its full head SHA, and issue #4719. | FR-003 |
| TC-04 | Read the comments of issue #4719 with `gh issue view 4719 -R $repo --json comments`. Compare the release comment time with the first pull request creation time. | The release comment time precedes the first pull request. | FR-004 |
| TC-05 | After each batch, rerun step 4 for the batch branches. | 0 head changes. Each head equals the inventory. | FR-005 |
| TC-06 | Search the record for the privacy-held branch. | The record holds only the head SHA, the count, and the privacy statement for `recovery/2977-handoff-20261004`. No path name or subject appears. | FR-006 |
| TC-07 | Step 6 for the four deferred branches, before the owner reconciliation comment. | 0 pull requests for `recovery/3213-handoff-20261004`, `jmorrison-juniper-issue-2746`, `jmorrison-juniper-local-build-revision`, and `recovery/3699-handoff-20261004` before task T012. | FR-007 |
| TC-08 | Check both local-only branches on GitHub and in the clone. | No remote ref. No local ref in this clone. | FR-008 |
| TC-09 | Step 7 runs both searches. | The workflow query returns 0. The plain query returns 4911, 4818, 4719, 4583, and 4302. | FR-009 |
| TC-10 | Step 9 reads the pin. After task T021, read the new pins in both workflow files. After task T022, count open issues with the tracking title. | Before T021, the blob is `b8ca235c93beddef9307d797da87223a920df729`. After T021, the pins name the new tag. After T022, exactly 1 open tracking issue. | FR-010, FR-011 |
| TC-11 | Step 8 checks the route. Step 11 runs the guardrail suite. Read the title check result of the pull request. | Leaf count 0. Parent child count 4 before the record and 5 after it. No new guardrail failure. The title check passes. | FR-012, FR-013 |
| TC-12 | Step 10 runs the text checks. Count the rows in `design/research.md` whose first cell is a number. Compare that count with the `remote_checks` count in the status file. | 0 forbidden tokens. 0 semicolons. 96 remote rows and 96 `remote_checks` entries. Each cited line matches its blob text. | FR-014, FR-016 |

## Warnings

Warning: Do not run a command that deletes a branch, force-pushes a branch, or rewrites history. Each step in this quickstart is read-only, except the preservation steps that the owner gates allow.

Caution: Each gh request counts against the GitHub rate limit. Wait 60 seconds after an HTTP 403 or 429 response, and retry up to three times.
