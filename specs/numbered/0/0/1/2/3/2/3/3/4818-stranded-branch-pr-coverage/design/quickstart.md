# Quickstart: Stranded branch pull request coverage

This guide gives the exact commands to reproduce the evidence and to verify the rollout. Run each command in PowerShell from the repository root. The repository root is `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`.

## Prerequisites

- Install `gh` and authenticate as the `jmorrison-juniper` account.
- Activate the repository environment before the report command runs.
- Set the GitHub host and the token before each `gh` command in this guide.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

```powershell
.venv\Scripts\Activate.ps1
```

## Scenario 1: Reproduce the remote checks

Each command returns the blob SHA of one remote path. Compare each result with research.md.

```powershell
gh api "repos/jmorrison-juniper/MistHelper/contents/AGENTS.md?ref=main" --jq .sha
gh api "repos/jmorrison-juniper/MistHelper/contents/.github/workflows/stranded-branch-report.yml?ref=main" --jq .sha
gh api "repos/jmorrison-juniper/MistHelper/contents/.github/workflows/ci.yml?ref=main" --jq .sha
gh api "repos/jmorrison-juniper/MistHelper/contents/documentation/contributing.md?ref=main" --jq .sha
gh api "repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=main" --jq .sha
```

The route leaf must return no entry:

```powershell
gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" --jq '.tree[] | select(.path | startswith("specs/numbered/0/0/1/2/3/2/3/3")) | .path'
```

The reusable workflow in `misthelper-devtools` at the pinned commit:

```powershell
gh api "repos/jmorrison-juniper/misthelper-devtools/contents/.github/workflows/reusable-stranded-branch-report.yml?ref=79a5e45970e876f1656d69520d9635cea1aa25ef" --jq .sha
```

## Scenario 2: Reproduce the duplicate tracker defect

The reusable query returns zero open trackers:

```powershell
gh issue list -R jmorrison-juniper/MistHelper --state open --search "chore(git): a branch holds work with no pull request in:title" --limit 100 --json number,title
```

The quoted phrase returns five open trackers:

```powershell
gh issue list -R jmorrison-juniper/MistHelper --state open --search 'in:title "a branch holds work with no pull request"' --limit 100 --json number,title
```

## Scenario 3: Run the replica

The replica follows the report rule. It uses read-only API calls only. The first command lists every remote branch name:

```powershell
$names = @(gh api "repos/jmorrison-juniper/MistHelper/branches?per_page=100" --paginate --jq ".[].name")
Write-Output ("BRANCHES=" + $names.Count)
```

For each name except `main`, the second command reads the compare result. Its `ahead_by` field counts the commits above `main`:

```powershell
foreach ($name in $names) {
    $ahead = gh api "repos/jmorrison-juniper/MistHelper/compare/main...$name" --jq .ahead_by
    Write-Output ("$name`t$ahead")
}
```

The class of each branch follows the rule in research.md R2. A branch with `ahead_by` of zero is `not-ahead`. A branch with an open pull request head is `protected-open`. A branch younger than seven days is `quiet`. A branch that a closed pull request holds is `protected-closed`. All other branches are `stranded`.

## Scenario 4: Run the report

The installed report reads the same rule. It prints one row for each stranded branch.

```powershell
stranded-branch-report --repository jmorrison-juniper/MistHelper --base-branch main --min-age-days 7
```

The rollout verification uses the exit code:

```powershell
stranded-branch-report --repository jmorrison-juniper/MistHelper --base-branch main --min-age-days 7 --fail-on-find
```

Expected result after the rollout: the report prints the clean message and the exit code is 0.

## Scenario 5: Read the branch evidence

These commands read local objects only. They never change the working tree.

```powershell
git --no-pager -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" rev-list --count main..recovery/4358-pre-reconstruction-20261113
git --no-pager -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" log --no-merges --format="%h %ad %s" --date=short main..recovery/4358-pre-reconstruction-20261113
git --no-pager -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" diff --name-only main...recovery/4358-pre-reconstruction-20261113
```

Use the same three commands for each branch in research.md. Replace the branch name with the branch in the row.

## Scenario 6: Count the quality-gate issues

```powershell
gh issue list -R jmorrison-juniper/MistHelper --state open --label quality-gate --limit 200 --json number,title
```

The count before the pilot is 18 (RC-051). Record the count in the pilot comment.

## Scenario 7: Create one preservation pull request

Set the branch name and its head commit before the create call. Read the head commit from the branch API:

```powershell
$branch = 'fix/3158-wip-controls'
$head = gh api "repos/jmorrison-juniper/MistHelper/branches/$branch" --jq .commit.sha
Write-Output ("HEAD=" + $head)
```

Build the body from the contract in `design\contracts\preservation-pull-request.md`:

```powershell
$body = @"
Refs #4818

Preservation only. Do not merge this pull request.

Branch: $branch
Head commit: $head
"@
```

Create the draft pull request:

```powershell
gh pr create -R jmorrison-juniper/MistHelper --draft --base main --head $branch --title "chore(git): preserve the head of $branch" --body $body --label chore --label ci
```

Verify the new pull request:

```powershell
gh pr list -R jmorrison-juniper/MistHelper --state open --draft --head $branch --json number,headRefName,headRefOid,title,labels
```

The field `headRefOid` must equal `$head`.

## Scenario 8: Verify the rollout

Check the body keywords. The count must be zero:

```powershell
$prs = @(gh pr list -R jmorrison-juniper/MistHelper --state all --search "Refs #4818" --limit 1000 --json number,body | ConvertFrom-Json)
$bad = @($prs | Where-Object { $_.body -match 'Closes #4818|Fixes #4818|Resolves #4818' })
Write-Output ("BAD_CLOSING_KEYWORDS=" + $bad.Count)
```

Check the branch count. The count must equal or exceed 598 (RC-047):

```powershell
$after = @(gh api "repos/jmorrison-juniper/MistHelper/branches?per_page=100" --paginate --jq ".[].name")
Write-Output ("BRANCHES_AFTER=" + $after.Count)
```

Check the repository visibility. The result must be `public` for the cost statement to hold (RC-050):

```powershell
gh api repos/jmorrison-juniper/MistHelper --jq .visibility
```

## Scenario 9: Run the local gates

The Markdown gate scores each record file. Each file must score 80 or above:

```powershell
ste-linter --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\spec.md specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\plan.md specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\tasks.md specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\analysis.md specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\design\research.md specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\design\data-model.md specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\design\quickstart.md specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\design\contracts\preservation-pull-request.md specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\design\checklists\requirements.md specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\design\checklists\rollout.md changelog.d\issue-4818-stranded-branch-pr-coverage.md
```

The guards run next. Each command prints the examined count and exits with status 0:

```powershell
python -m pytest tests/guardrails/test_process_folder_structure.py -q
python -m pytest tests/guardrails/test_spec_route_contract.py -q
python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q
```

## Scenario 10: Close the trackers

Run this only after the report exits with status 0 and the owner authorizes the closure:

```powershell
gh issue close 4302 -R jmorrison-juniper/MistHelper --comment "Duplicate of issue 4818. Closed after the stranded branch report returned no branch."
```

Repeat the command for issues 4583, 4719, and 4911. Then close issue 4818 with a comment that states the batch count.

Caution: The report comments only on an open tracker. Confirm the report result before each closure.

## Rollback

Warning: Deleting a branch that has no pull request removes its only copy. Do not delete any branch during rollback.

To close a pull request created in error, find its number from the branch name first:

```powershell
$branch = 'fix/3158-wip-controls'
$pr = gh pr list -R jmorrison-juniper/MistHelper --state open --head $branch --json number --jq '.[0].number'
```

Add a comment that gives the reason before the close:

```powershell
gh pr comment $pr -R jmorrison-juniper/MistHelper --body "Closed in error. The head remains readable through this pull request."
```

Then close the pull request:

```powershell
gh pr close $pr -R jmorrison-juniper/MistHelper
```
