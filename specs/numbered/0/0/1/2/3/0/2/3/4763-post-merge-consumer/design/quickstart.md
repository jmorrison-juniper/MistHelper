# Quickstart: Main workflow recovery

Use these steps to repeat the evidence and run the local gates. Do not print any environment variable value.

## 1. Prerequisites

Run these two lines before each `gh` command in this file.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

Each command below reads GitHub. Do not comment, label, edit, close, merge, or create anything on GitHub with these commands.

## 2. Read the shared workflow lines (T004)

Decode the shared file at the pinned commit and print the enable branch with line numbers.

```powershell
$b64 = gh api "repos/jmorrison-juniper/misthelper-devtools/contents/.github/workflows/reusable-auto-merge.yml?ref=d63a120487cecf750184cb178387cdc25c0a7635" --jq ".content"
$text = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String(($b64 -replace '\s', '')))
$lines = $text -split "`n"
233..240 | ForEach-Object { '{0,4}: {1}' -f ($_ + 1), $lines[$_].TrimEnd("`r") }
```

## 3. Evidence queries

Replace `<run-id>` with a run ID from the evidence table in `design/research.md`.

H-01. Delayed path. Confirm a pending request in a labeled run.

```powershell
gh run view <run-id> -R jmorrison-juniper/MistHelper --log | Select-String -CaseSensitive -Pattern 'Verified pull request \d+: (merged|enabled)\.'
```

H-02. Job results for one run, including the dispatch job and the close job.

```powershell
gh run view <run-id> -R jmorrison-juniper/MistHelper --json event,headBranch,jobs
```

H-03. Immediate path for one run. Expect one `merged` line and four `Started` lines.

```powershell
gh run view <run-id> -R jmorrison-juniper/MistHelper --log | Select-String -CaseSensitive -Pattern 'Verified pull request \d+: merged\.|Started [a-z-]+\.yml on main\.'
```

H-04. Scheduled coverage. List the scheduled runs, then read one run.

```powershell
gh run list -R jmorrison-juniper/MistHelper --workflow auto-merge.yml --event schedule --limit 100 --json databaseId,createdAt,headSha,conclusion
gh run view <run-id> -R jmorrison-juniper/MistHelper --log | Select-String -CaseSensitive -Pattern 'Started [a-z-]+\.yml on main\.|already covers the tip\.'
```

H-05. Evidence filter. List the pull request runs, then apply H-02 and H-03 to each run. A run without a `Verified pull request` line is not merge evidence. A `workflow_dispatch` run of a main workflow without a `Started` line from the dispatch job is not recovery evidence.

```powershell
gh run list -R jmorrison-juniper/MistHelper --workflow auto-merge.yml --event pull_request --limit 400 --json databaseId,conclusion,createdAt,headBranch
```

H-06. Workflow-file block. Run 43800244711 logged the block for pull request 4816.

```powershell
gh run view 43800244711 -R jmorrison-juniper/MistHelper --log | Select-String -CaseSensitive -Pattern 'edits a workflow file'
```

Pull request facts for one merge:

```powershell
gh pr view <number> -R jmorrison-juniper/MistHelper --json number,state,mergedAt,mergedBy,mergeCommit,headRefName
```

Current tip of `main`:

```powershell
gh api "repos/jmorrison-juniper/MistHelper/commits/main" --jq ".sha"
```

Baseline failure. Run 42920503087 skipped the dispatch job before the pin change.

```powershell
gh run view 42920503087 -R jmorrison-juniper/MistHelper --json jobs
```

## 4. Delayed path procedure (T011)

1. List the labeled pull request runs with H-05. Note each run that GitHub created while its checks ran.
2. Run H-01 on that run. Record the run ID and the time of the `enabled` line.
3. Run H-02 on that run. The dispatch job must show `skipped`.
4. Read the pull request after the merge. Record the merge time and the merge commit.
5. Find the next closed run or scheduled run that GitHub created within six hours after the merge.
6. Run H-03 or H-04 on that run. Each main workflow must show a start or a coverage line for the merge commit.
7. Write one evidence row with the fields in `design/contracts/evidence-record.md`.

Caution: Do not add a label early or push a commit only to create a pending request. Wait for a natural pending case.

## 5. Local gates for this record (T-LOCAL-GATES)

```powershell
python -m pytest tests/guardrails/test_spec_route_contract.py tests/guardrails/test_process_folder_structure.py tests/guardrails/test_auto_merge_issue_close.py
```

The route test file needs `pwsh` on the search path. Each command exits with status 0 when all its tests pass.

## 6. Closure (T012)

Use `design/checklists/acceptance.md`. The orchestrator closes issue #4763 only when every acceptance item shows a checked box and the orchestrator approves the closure.

```powershell
gh issue close 4763 -R jmorrison-juniper/MistHelper
```
