# Quickstart: Backlog Handoff Recovery

This guide gives the exact checks for issue 4870. Run each check from the repository root unless it names another path. The checks TST-01 to TST-19 run in the verification phase. The checks TST-20 to TST-37 run in the final tasks or in the record review.

## Prerequisites

- The gh CLI signs in to github.com as `jmorrison-juniper`. Run the identity check in TST-01 first.
- Git is on the path. The checks use read-only Git commands only.
- The `.venv` folder holds the pinned tools for the STE gate and pytest. Run those tools on the implementer machine.
- Each gh command reads or writes GitHub. The record runs no write command in the verification phase.

## Identity and handoff facts

### TST-01 Handoff facts and identity

**Requirements**: FR-001, FR-018, FR-020

```powershell
gh api user --jq .login
gh issue view 4870 -R jmorrison-juniper/MistHelper --json comments --jq ".comments | length"
```

**Expected**: The login is `jmorrison-juniper`. The comment count is 6 before the T021 comment. The count is 7 after it.

### TST-02 Inventory rows against GitHub

**Requirements**: FR-001, FR-002, FR-013

```powershell
$handoff = gh issue view 4870 -R jmorrison-juniper/MistHelper --json comments | ConvertFrom-Json
$inventory = $handoff.comments[0].body
$rows = @([regex]::Matches($inventory, '(?m)^\| #(\d+) \| (.+?) \| (.*?) \|'))
$rows.Count
$issues = gh issue list -R jmorrison-juniper/MistHelper --state all --limit 5000 --json number,state,title,labels | ConvertFrom-Json
$states = @{}
foreach ($issue in $issues) { $states[[int]$issue.number] = $issue.state }
@($rows | Where-Object { $states[[int]$_.Groups[1].Value] -eq 'OPEN' }).Count
$titleMismatch = 0
$labelMismatch = 0
foreach ($row in $rows) {
  $issue = $issues | Where-Object { $_.number -eq [int]$row.Groups[1].Value } | Select-Object -First 1
  if ($issue.title -ne $row.Groups[2].Value.Trim()) { $titleMismatch++ }
  $inventoryLabels = @($row.Groups[3].Value -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }) | Sort-Object
  $githubLabels = @($issue.labels | ForEach-Object { $_.name }) | Sort-Object
  if (($inventoryLabels -join ',') -ne ($githubLabels -join ',')) { $labelMismatch++ }
}
"title mismatches $titleMismatch label mismatches $labelMismatch"
```

**Expected**: The row count is 127. The open row count is 126. Issue 4867 is the only closed row. Title and label mismatches are 0.

### TST-03 Open issue count

**Requirements**: FR-002, FR-013, FR-020

```powershell
gh issue list -R jmorrison-juniper/MistHelper --state open --limit 1000 --json number --jq length
```

**Expected**: The count is 166 on 2026-11-26. Later runs report the live count.

### TST-04 Open PR set

**Requirements**: FR-002, FR-004, FR-005

```powershell
gh pr list -R jmorrison-juniper/MistHelper --state open --limit 100 --json number,isDraft,mergeStateStatus | ConvertFrom-Json | ForEach-Object { "#$($_.number) draft=$($_.isDraft) $($_.mergeStateStatus)" }
```

**Expected**: Seven PRs are open. PRs 4813 and 4208 are drafts. PRs 4886 to 4890 are BEHIND.

### TST-05 Merge commits in handoff sections 7 and 8

**Requirements**: FR-001

```powershell
$pairs = '4821:b35baecde','4823:b6347ec73','4829:068643075','4830:0c89de53d','4833:7a4780e87','4834:19bec34ea','4835:a00e99c73','4836:26ac26139','4839:390f535da','4843:15da34506','4845:efb9516a5','4847:db06604d1','4849:a3e8a2e72','4850:e707ea05b','4851:cfb790b19','4852:b1307510c','4853:aa8d12e90','4855:0682fa4e8','4856:814ad904f','4857:0da644a06','4860:260f4bcf9','4802:f94c9d9dd','4803:dbc047940','4804:0bb7a8a55','4805:5cf412ee2','4846:6408635c2','4859:0a9da4c3b','4864:6eca11b88','4865:b2828ffb4','4866:a9d848c98','4806:05cafda76'
foreach ($pair in $pairs) {
  $parts = $pair.Split(':')
  $oid = gh pr view $parts[0] -R jmorrison-juniper/MistHelper --json mergeCommit --jq .mergeCommit.oid
  if ($oid -like ($parts[1] + '*')) { 'match' } else { 'mismatch ' + $parts[0] }
}
```

**Expected**: 31 lines read `match`. No line reads `mismatch`.

### TST-06 Local commit tips

**Requirements**: FR-012

```powershell
$map = (gh issue view 4870 -R jmorrison-juniper/MistHelper --json comments | ConvertFrom-Json).comments[1].body
$shas = [regex]::Matches($map, '[0-9a-f]{40}') | ForEach-Object { $_.Value } | Sort-Object -Unique
$shas.Count
foreach ($sha in $shas) {
  gh api repos/jmorrison-juniper/MistHelper/commits/$sha --jq .sha
}
```

**Expected**: The distinct count is 44. Each of the 44 lines repeats its SHA, which shows that GitHub holds each commit.

### TST-07 Recovery refs and archive tags

**Requirements**: FR-011

```powershell
$recovery = @(gh api repos/jmorrison-juniper/MistHelper/git/matching-refs/heads/recovery/ --jq ".[].ref")
$recovery.Count
@($recovery | Where-Object { $_ -match '-wip-20261122$' }).Count
$archive = @(gh api repos/jmorrison-juniper/MistHelper/git/matching-refs/tags/archive/ --paginate --jq ".[].ref")
$archive.Count
```

**Expected**: The recovery count is 63. The wip count is 6. The archive count is 169. The counts do not fall during this work.

### TST-08 Feature pointer blob

**Requirements**: FR-006

```powershell
gh api "repos/jmorrison-juniper/MistHelper/contents/.specify/feature.json?ref=main" --jq .sha
gh api "repos/jmorrison-juniper/MistHelper/contents/.specify/feature.json?ref=e707ea05ba4d48100516867fd879b706ae6e58c2" --jq .sha
```

**Expected**: Both lines show `b86bcad085666bd0aeb3ac2244c914908dc7fa70`.

### TST-09 Route helper lines

**Requirements**: FR-007

```powershell
$route = gh api "repos/jmorrison-juniper/MistHelper/contents/.specify/scripts/powershell/spec-route.ps1?ref=main" --jq .content
$lines = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($route)) -split "`r?`n"
$lines[6]
$lines[16]
$lines[33]
```

**Expected**: Line 7 sets `$Width = 8`. Line 17 sets `$base = 5`. Line 34 starts `function Resolve-SpecFeaturePath`.

### TST-10 Devtools pins

**Requirements**: FR-008

```powershell
$paths = '.github/workflows/auto-merge.yml','.github/workflows/ci.yml','.github/workflows/close-linked-issues.yml','.github/workflows/codeql.yml','.github/workflows/container-build.yml','.github/workflows/release.yml','.github/workflows/ste-lint.yml','.github/workflows/stranded-branch-report.yml','requirements-dev.txt','pyproject.toml','uv.lock'
foreach ($path in $paths) {
  $text = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String((gh api "repos/jmorrison-juniper/MistHelper/contents/$($path)?ref=main" --jq .content)))
  foreach ($match in [regex]::Matches($text, 'misthelper-devtools.*?([0-9a-f]{40})')) { $path + ' ' + $match.Groups[1].Value }
}
```

**Expected**: The Python pins name `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` in `pyproject.toml` line 123, in `requirements-dev.txt` line 197, and in `uv.lock` lines 1532 and 1586. Nine workflow lines name `79a5e45970e876f1656d69520d9635cea1aa25ef`. One line in `auto-merge.yml` names `d63a120487cecf750184cb178387cdc25c0a7635`.

### TST-11 uv pin

**Requirements**: FR-010

```powershell
gh api "repos/jmorrison-juniper/MistHelper/contents/.github/workflows/container-build.yml?ref=main" --jq .content
```

**Expected**: Decode the content. Line 92 contains `python -m pip install uv==0.13.9`. The line `"uv==0.13.9"` appears at `pyproject.toml` line 101.

### TST-12 SDK search

**Requirements**: FR-001

```powershell
$sdk = '.venv\Lib\site-packages\mistapi'
@(Get-ChildItem -LiteralPath $sdk -Recurse -Filter *.py).Count
@(Get-ChildItem -LiteralPath $sdk -Recurse -Filter *.py | Select-String -Pattern 'listOrgInvites').Count
```

**Expected**: The file count is 288. The match count is 0.

### TST-13 Main head and the latest Quality Gates runs

**Requirements**: FR-009

```powershell
gh api repos/jmorrison-juniper/MistHelper/commits/main --jq .sha
gh run list -R jmorrison-juniper/MistHelper --workflow "Quality Gates" --branch main --limit 3 --json databaseId,headSha,conclusion | ConvertFrom-Json | ForEach-Object { "$($_.databaseId) $($_.headSha.Substring(0,9)) $($_.conclusion)" }
```

**Expected**: The head SHA starts with `f03c6c9b3` on 2026-11-26. Run 45774119357 reports `success`. Later, the newest run must report `success` before any other merge starts.

### TST-14 Held-by numbers

**Requirements**: FR-001, FR-012

```powershell
$held = @(4322, 4358, 4493) + (4799..4820)
$prs = 0
$notPrs = 0
foreach ($number in $held) {
  gh pr view $number -R jmorrison-juniper/MistHelper --json state --jq .state 2>$null
  if ($LASTEXITCODE -eq 0) { $prs++ } else { $notPrs++ }
}
"PRs $prs issues $notPrs"
```

**Expected**: `PRs 19 issues 6`. The six non-PR numbers are 4807, 4808, 4809, 4810, 4811, and 4818.

### TST-15 Named issue states

**Requirements**: FR-001, FR-003, FR-013

```powershell
$issues = gh issue list -R jmorrison-juniper/MistHelper --state all --limit 5000 --json number,state | ConvertFrom-Json
$states = @{}
foreach ($issue in $issues) { $states[[int]$issue.number] = $issue.state }
foreach ($number in 3726, 4536, 4584, 4737, 3699, 4838, 4858, 4714, 4759, 4774, 4762, 4867, 4883, 4869) { "$number $($states[$number])" }
```

**Expected**: Issues 3726, 4536, 4584, 4737, 3699, 4838, 4858, and 4714 are CLOSED. Issues 4759 and 4774 are OPEN. Issues 4762 and 4867 show the live states OPEN and CLOSED. Issues 4883 and 4869 are CLOSED.

### TST-16 Commit delta

**Requirements**: FR-002

```powershell
git rev-list --count 1982b7e8412160f81cb19e8113d784a65b7853b9..HEAD
```

**Expected**: The value is 8 when the local HEAD equals main. Research row R-77 records the HEAD check.

### TST-17 Local blobs equal main blobs

**Requirements**: FR-001

```powershell
git hash-object -- .github/copilot-instructions.md AGENTS.md .specify/memory/constitution.md .specify/templates/spec-template.md .specify/templates/plan-template.md .specify/templates/tasks-template.md .specify/templates/checklist-template.md documentation/quality-gates.md .github/workflows/ci.yml .specify/scripts/powershell/spec-route.ps1 .specify/scripts/powershell/common.ps1 .specify/scripts/powershell/create-new-feature.ps1 .github/workflows/container-build.yml requirements-dev.txt pyproject.toml uv.lock requirements.txt .specify/feature.json tests/guardrails/test_container_build_trigger.py tests/guardrails/test_dependency_export.py src/operations/exporting/export/org_export_utils.py .ste-linter.toml changelog.d/README.md tests/guardrails/test_spec_route_contract.py documentation/container-deployment.md tests/guardrails/test_process_folder_structure.py
```

**Expected**: The command prints 26 blob SHAs. Each SHA matches the blob column of the remote table in design/research.md.

### TST-18 No legacy record

**Requirements**: FR-007

```powershell
gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" --jq ".tree[].path" | Select-String -Pattern '4870'
@(Get-ChildItem -LiteralPath specs -Recurse -Directory -Filter '4870-*').Count
```

**Expected**: Both results are empty or 0.

### TST-19 Route math

**Requirements**: FR-007, FR-025

```powershell
$number = 4870
$digits = @()
while ($number -gt 0) {
  $digits = @([int]($number % 5)) + $digits
  $number = [math]::Floor($number / 5)
}
while ($digits.Count -lt 8) { $digits = @(0) + $digits }
$digits -join ' '
```

**Expected**: `0 0 1 2 3 4 4 0`. This result gives the route `specs/numbered/0/0/1/2/3/4/4/0`.

## Record checks

### TST-20 STE gate

**Requirements**: FR-019, FR-003

```powershell
.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/spec.md specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/plan.md specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/tasks.md specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/analysis.md specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/data-model.md specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/quickstart.md specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/contracts/inventory-table.md specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/contracts/decision-comment.md specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/checklists/requirements.md specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/checklists/security.md
```

**Expected**: Each file scores 80 or above. The same command runs on `changelog.d/issue-4870-backlog-handoff-recovery.md` and on `.github/copilot-instructions.md` for task T029.

### TST-21 Layout guard

**Requirements**: FR-007, FR-025

```powershell
python -m pytest tests/guardrails/test_process_folder_structure.py
```

**Expected**: All tests pass. The output reports the examined count.

### TST-22 Route contract

**Requirements**: FR-007

```powershell
python -m pytest tests/guardrails/test_spec_route_contract.py
```

**Expected**: All tests pass. On a host without pwsh, the result is recorded as it is.

### TST-23 Placeholder scan

**Requirements**: FR-015, FR-003

```powershell
Get-ChildItem -LiteralPath specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery -Recurse -File -Filter *.md | Select-String -Pattern 'T[B]D|T[O]DO|to[ ]be[ ]decided|\.\.\.'
```

**Expected**: No line matches.

### TST-24 Style scan

**Requirements**: FR-019

```powershell
$semicolon = [string][char]59
Get-ChildItem -LiteralPath specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery -Recurse -File -Filter *.md | Select-String -Pattern ([regex]::Escape($semicolon)), 'n\x27t', '\x27re\b', '\x27ve\b', '\x27ll\b', 'e\.g\.', 'i\.e\.', 'etc\.'
```

**Expected**: No prose line matches. A match inside a table cell or code block requires a correction before the review ends.

### TST-25 Count check

**Requirements**: FR-002, FR-015, FR-020, FR-021

```powershell
$base = 'specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery'
(Select-String -LiteralPath "$base/design/research.md" -Pattern '^\| R-\d+ ').Count
(Select-String -LiteralPath "$base/design/research.md" -Pattern '^\| D-\d+ ').Count
(Select-String -LiteralPath "$base/design/research.md" -Pattern 'HUMAN-DECISION-REQUIRED \(H-').Count
(Select-String -LiteralPath "$base/design/research.md" -Pattern '^\| U-\d+ ').Count
```

**Expected**: 79 remote rows, 22 decisions, 4 human decisions, and 16 unverified entries. The STATUS file in META_DIR and `summary.md` report the same values.

### TST-26 Directory children

**Requirements**: FR-025

```powershell
$base = 'specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery'
Get-ChildItem -LiteralPath $base -Recurse -Directory | ForEach-Object { '{0} children={1}' -f $_.Name, @(Get-ChildItem -LiteralPath $_.FullName).Count }
@(Get-ChildItem -LiteralPath $base).Count
```

**Expected**: Each directory reports five children or fewer. The record root reports five.

### TST-27 Requirement coverage

**Requirements**: FR-001 to FR-025

```powershell
$base = 'specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery'
1..25 | ForEach-Object { 'FR-{0:000}' -f $_ } | Where-Object { -not (Select-String -LiteralPath "$base/tasks.md" -Pattern $_ -Quiet) }
```

**Expected**: No output. Each requirement ID appears in tasks.md.

### TST-28 ASCII check

**Requirements**: FR-019

```powershell
Get-ChildItem -LiteralPath specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery -Recurse -File | Select-String -Pattern '[^\x00-\x7F]'
```

**Expected**: No line matches.

## Pull request checks

### TST-29 Feature pointer unchanged

**Requirements**: FR-006

Run TST-08 before T-PR and again after the merge. Both results must show `b86bcad085666bd0aeb3ac2244c914908dc7fa70`.

### TST-30 Changelog fragment

**Requirements**: FR-024

```powershell
$fragment = 'changelog.d/issue-4870-backlog-handoff-recovery.md'
(Select-String -LiteralPath $fragment -Pattern '^### ').Count
(Select-String -LiteralPath $fragment -Pattern '^- .*4870').Count
```

**Expected**: Each count is 1.

### TST-31 Dependency export guard

**Requirements**: FR-009, FR-010

```powershell
python -m pytest tests/guardrails/test_dependency_export.py
```

**Expected**: All tests pass. Run it during T026.

### TST-32 Container build trigger guard

**Requirements**: FR-008

```powershell
python -m pytest tests/guardrails/test_container_build_trigger.py
```

**Expected**: All tests pass. Run it during T027.

### TST-33 Device-event tests

**Requirements**: FR-014

```powershell
python -m pytest tests/unit/test_device_events_52w_exporter.py tests/unit/test_device_events_52w_exporter_extended.py
```

**Expected**: All tests pass. The resume test keeps the existing rows. Write the failing test before any code change.

### TST-34 Container policy guard

**Requirements**: FR-016

```powershell
python -m pytest tests/guardrails/test_container_policy_docs.py
```

**Expected**: All tests pass. Run it during T031.

### TST-35 Secret scan

**Requirements**: FR-017

```powershell
Get-ChildItem -LiteralPath specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery -Recurse -File | Select-String -Pattern 'gh[pousr]_[A-Za-z0-9]{20,}|github_pat[_]|(password|secret|api[_-]?key)\s*[:=]\s*\S+'
```

**Expected**: No line matches.

### TST-36 Changed files in the PR

**Requirements**: FR-022

```powershell
git diff --name-only $(git merge-base origin/main HEAD) HEAD
```

**Expected**: The output lists only the record folder files and `changelog.d/issue-4870-backlog-handoff-recovery.md`.

### TST-37 Hold phrases in open PR bodies

**Requirements**: FR-023

```powershell
gh pr list -R jmorrison-juniper/MistHelper --state open --limit 100 --json number,body | ConvertFrom-Json | ForEach-Object {
  $hits = @(Select-String -InputObject $_.body -Pattern '\b(do not merge|held for|hold stands|staging hold)\b' -AllMatches)
  "PR $($_.number) hits $($hits.Count)"
}
```

**Expected**: Each open PR reports its count. A hit stops the merge until a reviewer decides it (decision D-9).

## Requirement map

| Check | Requirements |
| - | - |
| TST-01 | FR-001, FR-018, FR-020 |
| TST-02 | FR-001, FR-002, FR-013 |
| TST-03 | FR-002, FR-013, FR-020 |
| TST-04 | FR-002, FR-004, FR-005 |
| TST-05 | FR-001 |
| TST-06 | FR-012 |
| TST-07 | FR-011 |
| TST-08 | FR-006 |
| TST-09 | FR-007 |
| TST-10 | FR-008 |
| TST-11 | FR-010 |
| TST-12 | FR-001 |
| TST-13 | FR-009 |
| TST-14 | FR-001, FR-012 |
| TST-15 | FR-001, FR-003, FR-013 |
| TST-16 | FR-002 |
| TST-17 | FR-001 |
| TST-18 | FR-007 |
| TST-19 | FR-007, FR-025 |
| TST-20 | FR-003, FR-019 |
| TST-21 | FR-007, FR-025 |
| TST-22 | FR-007 |
| TST-23 | FR-003, FR-015 |
| TST-24 | FR-019 |
| TST-25 | FR-002, FR-015, FR-020, FR-021 |
| TST-26 | FR-025 |
| TST-27 | FR-001 to FR-025 |
| TST-28 | FR-019 |
| TST-29 | FR-006 |
| TST-30 | FR-024 |
| TST-31 | FR-009, FR-010 |
| TST-32 | FR-008 |
| TST-33 | FR-014 |
| TST-34 | FR-016 |
| TST-35 | FR-017 |
| TST-36 | FR-022 |
| TST-37 | FR-023 |
