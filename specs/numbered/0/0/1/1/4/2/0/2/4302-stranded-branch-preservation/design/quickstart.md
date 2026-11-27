# Quickstart: Stranded Branch Preservation

## Prerequisites

- Windows PowerShell 7 or later, with `gh`, `git`, `pre-commit`, and `pytest` on the path.
- The repository checkout is read-only for verification. Run no command that writes to it.
- Set the GitHub account before each `gh` command. The value never prints.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

Set the repository variables once for the session.

```powershell
$slug = 'jmorrison-juniper/MistHelper'
$repo = 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper'
```

Define the record file set once for the gate tests. It holds the 10 record files and the changelog fragment, which is the 11 files of the change map.

```powershell
$draft = 'C:\Users\jmorrison\.copilot\session-state\30878eb1-80d0-451d-bd0c-0b3624089852\files\spec-drafts\4302'
$recordFiles = @('spec.md', 'plan.md', 'tasks.md', 'analysis.md', 'design\research.md', 'design\data-model.md', 'design\quickstart.md', 'design\contracts\branch-disposition-table.md', 'design\checklists\requirements.md', 'design\checklists\publication.md') | ForEach-Object { Join-Path $draft $_ }
```

Before the merge, the fragment and the record paths in the repository replace `$draft`. Use the repository paths of the change map for the gate tests after the T-PR task.

## Reproduce the Scope

Step 1. Read the annotated rows from #4302.

```powershell
$bodyLines = gh issue view 4302 -R $slug --json body --jq .body
$body = $bodyLines -join "`n"
$annotated = @([regex]::Matches($body, '(?m)^\| `([^`]+)` \|') | ForEach-Object { $_.Groups[1].Value })
$annotated.Count
```

Expected result: 48.

Step 2. Read the report rows from #4911.

```powershell
$reportLines = gh issue view 4911 -R $slug --json body --jq .body
$report = $reportLines -join "`n"
$rows = foreach ($match in [regex]::Matches($report, '(?m)^\| `([^`]+)` \| (\d+) \| (\d+) \|\s*$')) {
  [pscustomobject]@{
    Name = $match.Groups[1].Value
    Ahead = [int]$match.Groups[2].Value
    Age = [int]$match.Groups[3].Value
  }
}
$rows.Count
```

Expected result: 505.

Step 3. Read the head commit of every branch, and the head commit of every PR.

```powershell
$refLines = gh api "repos/$slug/git/matching-refs/heads/" --paginate --jq '.[] | .ref + " " + .object.sha'
$headOf = @{}
foreach ($line in $refLines) {
  $parts = $line -split ' '
  if ($parts.Count -eq 2) {
    $headOf[$parts[0].Substring(11)] = $parts[1]
  }
}
$prs = gh pr list -R $slug --state all --limit 5000 --json number,headRefName,headRefOid | ConvertFrom-Json
$prShas = @{}
foreach ($pr in $prs) {
  if ($pr.headRefOid) {
    $prShas[$pr.headRefOid] = $pr.number
  }
}
```

Step 4. Classify each report row.

```powershell
$prNames = @{}
foreach ($pr in $prs) { $prNames[$pr.headRefName] = 1 }
$prKept = @($rows | Where-Object { $headOf.ContainsKey($_.Name) -and $prShas.ContainsKey($headOf[$_.Name]) })
$unkept = @($rows | Where-Object { $headOf.ContainsKey($_.Name) -and -not $prShas.ContainsKey($headOf[$_.Name]) })
$sameName = @($rows | Where-Object { $prNames.ContainsKey($_.Name) })
"PR-kept: $($prKept.Count). Unkept: $($unkept.Count). Same-name PRs: $($sameName.Count)."
```

Expected result: PR-kept 248. Unkept 257. Same-name PRs 0.

Step 5. Count distinct head commits and commits ahead among unkept rows.

```powershell
$distinctUnkept = @($unkept | ForEach-Object { $headOf[$_.Name] } | Sort-Object -Unique).Count
$aheadSum = ($unkept | Measure-Object Ahead -Sum).Sum
"Distinct unkept heads: $distinctUnkept. Commits ahead: $aheadSum."
```

Expected result: 251 distinct heads, and 1059 commits ahead.

## Reproduce the Blob Classes

Step 6. Read the `main` tree once. The read returns blob SHAs for every path.

```powershell
$treeLines = gh api "repos/$slug/git/trees/main?recursive=1" --jq '.tree[] | select(.type=="blob") | .path + " " + .sha'
$mainBlob = @{}
foreach ($line in $treeLines) {
  $parts = $line -split ' '
  if ($parts.Count -eq 2) {
    $mainBlob[$parts[0]] = $parts[1]
  }
}
```

Step 7. Compare one annotated branch with `main`. Repeat for each annotated row.

```powershell
$name = 'fix/3158-wip-controls'
$basehead = 'main' + '.' * 3 + $name
$cmp = gh api "repos/$slug/compare/$basehead" --jq '{ahead: .ahead_by, behind: .behind_by, files: [.files[] | {f: .filename, s: .status, b: .sha}]}' | ConvertFrom-Json
$identical = 0
$differs = 0
$absent = 0
foreach ($file in @($cmp.files)) {
  if ($file.s -eq 'removed') {
    continue
  }
  if (-not $mainBlob.ContainsKey($file.f)) {
    $absent++
    continue
  }
  if ($mainBlob[$file.f] -eq $file.b) {
    $identical++
  } else {
    $differs++
  }
}
"ahead=$($cmp.ahead) behind=$($cmp.behind) identical=$identical differs=$differs absent=$absent"
```

Expected result for `fix/3158-wip-controls`: ahead 1, behind 688, identical 0, differs 3, absent 4.

## Reproduce the Gates

Step 8. Check the repository visibility and the open-PR overlap.

```powershell
gh repo view $slug --json visibility --jq .visibility
gh pr list -R $slug --state open --limit 500 --json number,files --jq '[.[] | select(.files | map(.path | startswith("specs/numbered/0/0/1/1/4/2/0/2")) | any) | .number] | length'
```

Expected result: PUBLIC, then 0.

Step 9. Confirm the route is absent, and confirm the ancestor child counts.

```powershell
$route = 'specs/numbered/0/0/1/1/4/2/0/2/'
@($treeLines | Where-Object { $_ -like "$route*" }).Count
```

Expected result before the record merges: 0.

## Verification Tests

Each test has one ID, one command, and one expected result. The requirement IDs refer to `spec.md`.

- TST-01 (FR-001). Count the annotated rows. Expected result: 48.
- TST-02 (FR-001, FR-003, FR-009). Run Steps 2 to 5. Expected result: 505 rows, 248 PR-kept, 257 unkept, 251 distinct heads, and 1059 commits ahead. Repeat before each batch.
- TST-03 (FR-003). Count same-name PRs for the report rows. Expected result: 0.
- TST-04 (FR-004). Run Step 8. Expected result: PUBLIC, and 0 overlapping PRs.
- TST-05 (FR-002). Run Step 7 for each annotated row. Expected result: each row equals `design/research.md`.
- TST-06 (FR-001). Compare each annotated head with the matching ref. Expected result: 47 equal heads.
- TST-07 (FR-001). Compare each annotated row's ahead and behind counts with `design/research.md`. Expected result: 47 equal rows.
- TST-08 (FR-010). Run Step 9 before the merge, then after the merge. Expected result: 0 paths before, and 1 `spec.md` after.
- TST-09 (FR-010). Count the children of each ancestor directory of the route. Expected result: each count is 5 or fewer.
- TST-10 (FR-011). Run the STE hook on the record files and the fragment.

```powershell
pre-commit run ste-linter --files $recordFiles
```

Expected result: the hook passes, and each file scores 80 or above.

- TST-11 (FR-011). Run the link check on the same files.

```powershell
pre-commit run markdown-link-check --files $recordFiles
```

Expected result: the hook passes, with zero broken links.

- TST-12 (FR-010). Run the two guard tests.

```powershell
python -m pytest tests/guardrails/test_spec_route_contract.py tests/guardrails/test_process_folder_structure.py
```

Expected result: all tests pass.

- TST-13 (FR-014). Search the record for placeholder tokens.

```powershell
$placeholderTokens = @('TB' + 'D', 'TO' + 'DO', 'to be ' + 'decided')
Select-String -Path $recordFiles -Pattern ($placeholderTokens -join '|')
Select-String -Path (Join-Path $draft 'design\research.md') -Pattern 'HUMAN-DECISION-REQUIRED' | Measure-Object
```

Expected result: no match for the first search. The second search finds 3 lines in `design/research.md`, one for each human decision (D-3, D-7, and D-10).

- TST-14 (FR-005). Check the owner comments on #4302 for the batch authorization. The owner writes the batch name in the comment.

```powershell
gh issue view 4302 -R $slug --json comments --jq '[.comments[] | select(.author.login == "jmorrison-juniper") | .body] | map(select(test("Authorize batch B[123]"))) | length'
```

Expected result: 1 or more for the batch being published. Zero means the publication step stops.

- TST-15 (FR-006, FR-012). Check each draft PR for the batch.

```powershell
gh pr view $prNumber -R $slug --json isDraft,headRefOid,labels,body,title --jq '{draft: .isDraft, head: .headRefOid, auto: ([.labels[].name] | index("auto-merge") != null), refs: (.body | contains("Refs #4302")), closes: (.body | contains("Closes #4302"))}'
```

Expected result: `draft` is true, `head` equals the recorded head, `auto` is false, `refs` is true, and `closes` is false. Set `$prNumber` to the PR number.

- TST-16 (FR-008). Compare each annotated and unkept head with the matching ref. Expected result: each head equals the recorded head.
- TST-17 (FR-005). Scan each head before its PR opens. Use the head commit, not the branch name.

```powershell
git -C $repo grep -n -I -E "BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|password *=|secret *=" $headSha
```

Expected result: no output. Any output stops the batch, and the owner handles it under the credential policy. Set `$headSha` to the head commit being scanned.

- TST-18 (FR-007). Check that each held row has no PR of the same name.

```powershell
gh pr list -R $slug --state all --head $name --json number --jq length
```

Expected result: 0 for each held row.

- TST-19 (FR-012). Check the record PR title and the closing keyword. Expected result: the title matches `^(feat|fix|chore|refactor|test|docs|ci|style|perf)(\([^)]+\))?!?: \S`, and the body contains `Refs #4302` and omits `Closes #4302`.
- TST-20 (FR-013). Count the rows in the table of `design/research.md`, and count the `remote_checks` array in STATUS. Expected result: both counts are 93.
- TST-21 (FR-011). Check the changelog fragment. Expected result: the file has one `### Added` heading and one bullet that names issue #4302.
- TST-22 (FR-015). Read the state of #4302 after the merge. Expected result: OPEN.

```powershell
gh issue view 4302 -R $slug --json state --jq .state
```

- TST-23 (FR-016). Count the open issues with the report title. The title search must use a quoted phrase.

```powershell
gh issue list -R $slug --state open --search '"a branch holds work with no pull request" in:title' --limit 100 --json number --jq length
```

Expected result: 5 before the fix (T020). Exactly 1 after the owner closes the duplicates (T021).

- TST-24 (FR-015). Check each proof comment on #4302. Expected result: the comment contains the columns of `design/contracts/branch-disposition-table.md`, and it has one row for each branch in the batch.

## Expected Result of the Full Sequence

Run TST-01 to TST-07 and TST-24 before each batch. Run TST-08 to TST-13 and TST-19 to TST-22 before the record PR merges. Run TST-14 to TST-18 for each batch. Run TST-23 after the report fix.
