# Quickstart: Stranded branch preservation

Run each step in PowerShell in the order shown. Each step names the expected output. Run Step 0 in every new PowerShell session. The commands read GitHub, read git refs, and push tags. No command in this procedure deletes a branch.

## Prerequisites

- `git` with push access to `origin` for the MistHelper repository.
- The GitHub CLI signed in to `jmorrison-juniper/MistHelper`.
- The repository checkout at `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`.
- A worktree for the record branch. Do not check out a branch in the shared checkout (`AGENTS.md`).

## Step 0. Set the environment

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
$repo = 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper'
$record = Join-Path $repo 'specs\numbered\0\0\1\2\4\1\2\1\4911-stranded-branch-preservation'
```

## Step 1. Read the named rows

Expected output: `rows=505 unique=505`.

```powershell
$body = (gh issue view 4911 -R jmorrison-juniper/MistHelper --json body --jq .body | Out-String)
$names = @([regex]::Matches($body, '(?m)^\| `([^`]+)` \| (\d+) \| (\d+)') | ForEach-Object { $_.Groups[1].Value })
"rows=$($names.Count) unique=$(($names | Sort-Object -Unique).Count)"
```

## Step 2. Read the tips from GitHub

Expected output: `named_on_origin=505`. This read gives the tips for the session.

```powershell
$tips = @{}
foreach ($line in @(gh api 'repos/jmorrison-juniper/MistHelper/branches?per_page=100' --paginate --jq '.[] | .name + " " + .commit.sha')) {
  $pair = $line -split ' ', 2
  $tips[$pair[0]] = $pair[1]
}
"named_on_origin=$(@($names | Where-Object { $tips.ContainsKey($_) }).Count)"
```

## Step 3. Classify the held tips

Expected output on 2026-11-26: `held=248` and `not_held=257`.

```powershell
$prHeadCommits = @{}
foreach ($oid in @(gh pr list -R jmorrison-juniper/MistHelper --state all --limit 5000 --json headRefOid --jq '.[].headRefOid')) {
  $prHeadCommits[$oid] = 1
}
"held=$(@($names | Where-Object { $prHeadCommits.ContainsKey($tips[$_]) }).Count)"
"not_held=$(@($names | Where-Object { -not $prHeadCommits.ContainsKey($tips[$_]) }).Count)"
```

## Step 4. Check the tag names and the existing tags

Expected output: `invalid_names=0`, and `git ls-remote` prints no line. A line from `ls-remote` means a preservation tag already exists. Stop and read the line before any push.

```powershell
$invalid = @($names | Where-Object {
  git check-ref-format "refs/tags/preserve/$_" 2>$null
  $LASTEXITCODE -ne 0
})
"invalid_names=$($invalid.Count)"
git --no-pager -C $repo ls-remote --tags origin 'refs/tags/preserve/*'
```

## Step 5. Dry run the pilot

Expected output: git lists five new refs and pushes none.

```powershell
$pilot = @($names | Select-Object -First 5)
$pilotSpecs = @($pilot | ForEach-Object { $tips[$_] + ':refs/tags/preserve/' + $_ })
git --no-pager -C $repo push --dry-run origin @pilotSpecs
```

## Step 6. Push the pilot and verify it

Expected output: `pilot_verified=5 of 5`.

```powershell
git --no-pager -C $repo push origin @pilotSpecs
if ($LASTEXITCODE -ne 0) {
  'The pilot push failed. Stop the procedure and read the ledger.'
}
$remoteTags = @{}
foreach ($line in @(git --no-pager -C $repo ls-remote --tags origin 'refs/tags/preserve/*')) {
  $pair = $line -split "`t", 2
  $remoteTags[$pair[1] -replace '^refs/tags/preserve/', ''] = $pair[0]
}
"pilot_verified=$(@($pilot | Where-Object { $remoteTags[$_] -eq $tips[$_] }).Count) of $($pilot.Count)"
```

## Step 7. Check that the pilot starts no workflow run

Wait five minutes after Step 6. Expected output: no line. A line means a workflow started from a preservation tag. Stop the procedure and run Step 13 for the pilot rows.

```powershell
gh run list -R jmorrison-juniper/MistHelper --limit 30 --json headBranch,event,name,createdAt --jq '.[] | select(.headBranch | startswith("preserve/")) | "\(.createdAt) \(.event) \(.name) \(.headBranch)"'
```

## Step 8. Push the other 500 tags in batches of 50

Expected output: no `failed` line. Each batch exits with code 0. The procedure stops at the first failed batch and reads the ledger. A failed push is retried up to three times with waits of 30, 60, and 120 seconds before the stop.

Read the tips again before the batches. Expected output: `missing_branches=0`. A missing branch becomes a ledger row with the result `absent`, and the batches skip that row.

```powershell
$tips = @{}
foreach ($line in @(gh api 'repos/jmorrison-juniper/MistHelper/branches?per_page=100' --paginate --jq '.[] | .name + " " + .commit.sha')) {
  $pair = $line -split ' ', 2
  $tips[$pair[0]] = $pair[1]
}
$missing = @($names | Where-Object { -not $tips.ContainsKey($_) })
"missing_branches=$($missing.Count)"
$rest = @($names | Select-Object -Skip 5 | Where-Object { $tips.ContainsKey($_) })
$batchStarts = @(0, 50, 100, 150, 200, 250, 300, 350, 400, 450)
foreach ($start in $batchStarts) {
  $batch = @($rest | Select-Object -Skip $start -First 50)
  if ($batch.Count -eq 0) {
    break
  }
  $batchSpecs = @($batch | ForEach-Object { $tips[$_] + ':refs/tags/preserve/' + $_ })
  git --no-pager -C $repo push origin @batchSpecs
  if ($LASTEXITCODE -ne 0) {
    "failed batch starting at row $($start + 6). Stop and read the ledger."
    break
  }
}
```

## Step 9. Verify all tags and the named branch names

Expected output: `tags_verified=505 of 505` and `named_branches_still_present=505 of 505`.

```powershell
$remoteTags = @{}
foreach ($line in @(git --no-pager -C $repo ls-remote --tags origin 'refs/tags/preserve/*')) {
  $pair = $line -split "`t", 2
  $remoteTags[$pair[1] -replace '^refs/tags/preserve/', ''] = $pair[0]
}
"tags_verified=$(@($names | Where-Object { $remoteTags[$_] -eq $tips[$_] }).Count) of $($names.Count)"
$after = @{}
foreach ($line in @(gh api 'repos/jmorrison-juniper/MistHelper/branches?per_page=100' --paginate --jq '.[] | .name')) {
  $after[$line] = 1
}
"named_branches_still_present=$(@($names | Where-Object { $after.ContainsKey($_) }).Count) of $($names.Count)"
```

Post the ledger as two comments on issue 4911. Each comment holds at most 300 rows. Each row holds the fields of the ledger contract.

## Step 10. Check the guide, the fragment, the STE gate, and the guard tests

Expected output: the STE command reports a score of 80 or above for each file. The pytest command passes. The `Select-String` command prints no line. The `git diff` list contains no path under `.github/workflows/` and no `requirements-dev.txt` line.

```powershell
ste-linter --config .ste-linter.toml --min-score 80 documentation/contributing.md changelog.d/issue-4911-stranded-branch-preservation.md
python -m pytest tests/guardrails/test_changelog_fragment_policy.py tests/guardrails/test_markdown_links.py
Select-String -Path documentation/contributing.md -Pattern 'only permanent copy'
$base = git --no-pager merge-base origin/main HEAD
git --no-pager diff --name-only $base HEAD
```

## Step 11. Compare the record counts

Expected output: the two counts are equal. At the time of this draft, both counts are 72.

```powershell
$statusPath = 'C:\Users\jmorrison\.copilot\session-state\30878eb1-80d0-451d-bd0c-0b3624089852\files\spec-drafts\_meta\4911-STATUS.json'
$status = Get-Content -Raw -LiteralPath $statusPath | ConvertFrom-Json
$research = Get-Content -Raw -LiteralPath (Join-Path $record 'design\research.md')
"status_remote_checks=$(@($status.remote_checks).Count)"
"table_rows=$(@([regex]::Matches($research, '(?m)^\| RC-\d+ ')).Count)"
```

## Step 12. Count the open tracking issues

Expected output: `1` after the duplicate handling.

```powershell
gh issue list -R jmorrison-juniper/MistHelper --state open --limit 100 --json number,title --jq '[.[] | select(.title == "chore(git): a branch holds work with no pull request")] | length'
```

## Step 13. Roll back the preservation tags

Caution: this command deletes tags only. The named branches stay on origin. Use the rows that this procedure pushed. Do not add a branch name to the list.

Run the first two lines for the pilot rows only. Run the last two lines for all rows.

```powershell
$rollbackPilot = @($pilot | ForEach-Object { 'refs/tags/preserve/' + $_ })
git --no-pager -C $repo push origin --delete @rollbackPilot
$rollbackAll = @($names | ForEach-Object { 'refs/tags/preserve/' + $_ })
git --no-pager -C $repo push origin --delete @rollbackAll
```

## Step 14. Check the pull request body

Expected output: the body contains `Refs #4911` until the report names no row. The body contains `Closes #4911` after the report names no row.

```powershell
gh pr view chore/4911-stranded-branch-preservation -R jmorrison-juniper/MistHelper --json title,body --jq '.title + "\n" + .body'
```
