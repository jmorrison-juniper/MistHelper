# Quickstart: Stale and Bulk Run Controls

**Feature**: `specs/2447-stale-bulk-run-controls/` | **Date**: 2026-09-11

Run these sections in order.

Warning: do not start a Morrison House firmware upgrade during automated
validation. A live upgrade can interrupt network service.

## 1. Confirm the Branch and Base

```powershell
git fetch origin main
$branch = git branch --show-current
$headRevision = git rev-parse HEAD
$mainRevision = git rev-parse origin/main
if ($branch -ne "fix/2447-stale-bulk-run-controls") {
    throw "The active branch does not own issue 2447."
}
if ($headRevision -ne $mainRevision) {
    throw "The branch does not start at current origin/main."
}
```

The branch now starts at current `origin/main`. The prior clean-branch blocker
does not apply.

## 2. Claim Issue 2447

```powershell
gh issue view 2447 --json state,assignees,labels,url
gh issue edit 2447 --add-assignee "@me" --add-label "in-progress"
$issue = gh issue view 2447 --json state,assignees,labels,url |
    ConvertFrom-Json
if ($issue.state -ne "OPEN") {
    throw "Issue 2447 is not open."
}
if ($issue.labels.name -notcontains "in-progress") {
    throw "Issue 2447 does not have the in-progress label."
}
```

Confirm that no other active owner claims the implementation. Stop when the
issue shows a conflicting owner without a recorded handoff.

## 3. Load the Complete Feature Manifest

```powershell
$manifestPath = "specs\2447-stale-bulk-run-controls\feature-files.txt"
$manifest = Get-Content $manifestPath |
    Where-Object { $_.Trim() } |
    ForEach-Object { $_.Trim().Replace("\", "/") }
if ($manifest.Count -ne 79) {
    throw "The feature manifest must contain 79 planned paths."
}
$duplicates = $manifest | Group-Object | Where-Object { $_.Count -gt 1 }
if ($duplicates) {
    throw "The feature manifest contains a duplicate path."
}
```

The manifest already lists every planned source, asset, test, README,
documentation, changelog, specification, constitution, and metadata path.

No workflow file edit is planned. If implementation needs one, add the exact
workflow path to the manifest before its first edit.

Update the manifest before the feature changes any additional path. Do not add
an unrelated pre-existing file.

## 4. Check Tracked and Untracked Feature Changes

Include committed branch changes, staged changes, unstaged changes, and
untracked files.

```powershell
$base = git merge-base HEAD origin/main
$committed = git diff --name-only --diff-filter=ACMRD $base HEAD
$working = git diff --name-only --diff-filter=ACMRD
$staged = git diff --cached --name-only --diff-filter=ACMRD
$untracked = git ls-files --others --exclude-standard
$trackedChanged = @(
    $committed
    $working
    $staged
) |
    ForEach-Object { $_.Replace("\", "/") } |
    Sort-Object -Unique
$untracked = $untracked |
    ForEach-Object { $_.Replace("\", "/") } |
    Sort-Object -Unique
$unlistedTracked = $trackedChanged |
    Where-Object { $manifest -notcontains $_ }
if ($unlistedTracked) {
    throw "A tracked feature change is outside the manifest: $unlistedTracked"
}
$featureChanged = @(
    $trackedChanged
    ($untracked | Where-Object { $manifest -contains $_ })
) | Sort-Object -Unique
$unrelatedUntrackedBaseline = @(
    $untracked | Where-Object { $manifest -notcontains $_ }
)
```

Review `$unrelatedUntrackedBaseline`. Confirm that each path existed before
this feature work and is unrelated. Do not add those paths to the manifest.

Keep `$featureChanged` for every gate and staging check.

## 5. Check Active Branches and File Overlap

```powershell
git worktree list --porcelain
git branch --format="%(refname:short) %(worktreepath)"
$openPullRequests = gh pr list --state open --limit 100 `
    --json number,headRefName,files | ConvertFrom-Json
$overlap = foreach ($pullRequest in $openPullRequests) {
    $shared = $pullRequest.files.path |
        Where-Object { $manifest -contains $_ }
    if ($shared) {
        [pscustomobject]@{
            number = $pullRequest.number
            branch = $pullRequest.headRefName
            files = $shared
        }
    }
}
if ($overlap) {
    $overlap | Format-Table -AutoSize
    throw "An open pull request overlaps the feature manifest."
}
```

Confirm that no other worktree uses this branch. Confirm that no active branch
claims issue 2447. Complete this check before the first source or test edit.

## 6. Back Up the Operational Store

Create the backup before an action schema or persistence change.

```powershell
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupRoot = "data\backups\upgrade-runs-$stamp"
New-Item -ItemType Directory -Force $backupRoot
podman exec misthelper-arangodb arangodump `
  --server.endpoint tcp://127.0.0.1:9529 `
  --server.username root `
  --server.password "$env:ARANGO_ROOT_PASSWORD" `
  --output-directory "/tmp/upgrade-runs-$stamp"
podman cp "misthelper-arangodb:/tmp/upgrade-runs-$stamp" $backupRoot
Get-ChildItem $backupRoot -Recurse
```

Warning: stop if the backup fails or contains no collection data. A store
rollback needs a verified copy.

Record the backup path and creation time in the implementation log.

## 7. Validate the Package Structure

Run the repository structural analyzer against each changed Python package.

Confirm these new packages:

```text
src/upgrade_portal/api/run_controls/
src/upgrade_portal/api/run_controls/services/
src/upgrade_portal/persistence/actions/
tests/integration/upgrade_portal/run_controls/
tests/support/upgrade_portal_e2e/
tests/support/upgrade_portal_e2e/records/
tests/support/upgrade_portal_e2e/traps/
```

Confirm that each new directory has no more than five children.

Confirm these exact child budgets:

| Package | Direct children |
| - | -: |
| `src/upgrade_portal/api/run_controls` | 5 |
| `src/upgrade_portal/api/run_controls/services` | 5 |
| `src/upgrade_portal/persistence/actions` | 5 |
| `tests/unit/upgrade_portal/test_runs` | 5 |
| `tests/contract/upgrade_portal/test_upgrade_routes` | 5 |
| `tests/e2e/upgrade_portal/test_run_controls` | 5 |
| `tests/integration/upgrade_portal/run_controls` | 5 |
| `tests/support/upgrade_portal_e2e` | 5 |
| `tests/support/upgrade_portal_e2e/records` | 5 |
| `tests/support/upgrade_portal_e2e/traps` | 5 |

Confirm that these existing files remain surgical integration points:

```text
src/upgrade_portal/runtime/signals.py
src/upgrade_portal/app/routes/review.py
src/upgrade_portal/app/routes/upgrade.py
src/upgrade_portal/app/factory.py
src/upgrade_portal/app/wiring.py
```

Confirm that no new direct child entered a grandfathered noncompliant parent.
Confirm that `runtime/runs.py` remains unchanged and supplies the terminal
authority.

## 8. Prove the Canonical Terminal Set

Run the focused unit and contract tests.

The tests must prove:

- `RunStateMachine.TERMINAL` is the only run terminal set.
- `runtime/signals.py` defines no `TERMINAL_RUN_STATES`.
- `app/routes/review.py` defines no `FINISHED_RUN_STATES`.
- `cancelled` is terminal for stop, history, stale, and live-run decisions.

## 9. Prove Isolation Before Browser Use

```powershell
$env:UPGRADE_PORTAL_E2E_STRICT = "1"
.venv\Scripts\python.exe -m pytest `
  tests\unit\upgrade_portal\test_runs\test_isolation.py `
  tests\contract\upgrade_portal\test_upgrade_routes\test_isolation.py -v
```

Do not run Chromium before this command passes.

The tests must prove:

- Factory overrides install before route registration.
- ArangoDB, Redis, cloud, and file traps are active.
- The child environment contains no production credential.
- The child uses loopback port 1 sentinels.
- Each server receives a unique port and artifact directory.
- E2E responses contain the expected test run header.

## 10. Run Targeted Tests

### Unit

```powershell
.venv\Scripts\python.exe -m pytest `
  tests\unit\upgrade_portal\test_runs -v
```

### Contract

```powershell
.venv\Scripts\python.exe -m pytest `
  tests\contract\upgrade_portal\test_upgrade_routes -v
```

### Integration

```powershell
.venv\Scripts\python.exe -m pytest `
  tests\integration\upgrade_portal\run_controls -v
```

The integration tests must cover outcome-only writes, action finalization,
lease takeover, interrupted claims, pending-item resumption, and no repeated
mutation.

Fix a feature-caused failure in this feature. If a failure is unrelated,
create one GitHub issue before a separate repair.

## 11. Record Persistent Baselines

Record these read-only ArangoDB counts before the complete browser suite:

- Total nonfinal runs.
- Total run identifiers that start with `e2e-`.
- Total E2E action records.
- Total E2E audit rows.

Record the query text, count, and time in the implementation log.

## 12. Run the Complete Browser Suite

All isolation traps must remain active.

```powershell
$env:UPGRADE_PORTAL_E2E_STRICT = "1"
.venv\Scripts\python.exe -m pytest tests\e2e\upgrade_portal -v
```

The complete suite must pass. A targeted browser run is not a substitute.

Each response must contain the expected
`X-MistHelper-E2E-Run-ID` value.

## 13. Compare Persistent Counts

Run the section 11 queries immediately after the complete suite.

Every count must equal its baseline. If a count changes, stop deployment and
create a GitHub issue before cleanup or repair.

## 14. Run the Recovery Drill

Restore the verified backup to an isolated ArangoDB target.

Verify:

1. The run and action collection counts match the backup.
2. The action composite and actor indexes exist.
3. Sample action records refer to existing run records.
4. No restore command targets the production database.

Record the isolated target, commands, counts, and result.

## 15. Confirm Retention

Confirm that the feature installs no automatic action cleanup.

Confirm that action records remain for the lifetime of their referenced run
records. Record the policy in the operator documentation.

## 16. Run Deterministic Performance Measurements

```powershell
.venv\Scripts\python.exe -m pytest `
  tests\integration\upgrade_portal\run_controls\test_performance.py -v
```

Required results:

- The maximum 50-row history time is less than 1 second.
- The maximum 50-run no-cloud batch time is less than 5 seconds.
- The no-cloud batch records zero cloud calls.

## 17. Run Gates for Changed Python Files

```powershell
$python = $featureChanged | Where-Object { $_ -like "*.py" }
.venv\Scripts\python.exe -m py_compile @python
.venv\Scripts\python.exe -m ruff check @python
.venv\Scripts\python.exe -m black --check @python
.venv\Scripts\python.exe -m mypy @python --config-file pyproject.toml
.venv\Scripts\python.exe -m pylint --rcfile=pyproject.toml @python
.venv\Scripts\python.exe -m radon cc -s -a -nc @python
.venv\Scripts\python.exe -m vulture @python --min-confidence 70
.venv\Scripts\python.exe -m pydocstyle @python
.venv\Scripts\python.exe -m interrogate -c pyproject.toml @python
```

Run the applicable pytest tests for each source file. Record the source path,
test path, and result.

## 18. Run Gates for Changed JavaScript Files

```powershell
$javascript = $featureChanged | Where-Object { $_ -like "*.js" }
foreach ($file in $javascript) {
    node --check $file
}
.venv\Scripts\python.exe -m pytest `
  tests\unit\upgrade_portal\test_runs\test_staleness.py -v
```

The complete browser suite supplies the remaining behavior coverage.

## 19. Run Repository Gates

Run the existing CI-equivalent commands that apply to the manifest. Include
syntax, Ruff, Black, mypy, pytest, Bandit, dependency audit, pylint, radon,
vulture, pydocstyle, interrogate, and Playwright.

Do not add a new quality tool.

## 20. Review Comments and Logs

Review each changed executable line for the required inline reason comment.

Review each meaningful action for an `info` log before it and a `debug` log
after it. Keep all logs ASCII and free of credentials.

## 21. Grade Feature Prose

```powershell
$files = Get-ChildItem "specs\2447-stale-bulk-run-controls" `
  -Recurse -Filter "*.md"
$files += Get-Item ".specify\memory\constitution.md"
foreach ($file in $files) {
    .venv\Scripts\python.exe -m tools.ste_linter `
      --min-score 80 $file.FullName
}
```

Every file must score 80 or more.

## 22. Recheck and Stage Every Feature File

```powershell
$untrackedNow = git ls-files --others --exclude-standard |
    ForEach-Object { $_.Replace("\", "/") } |
    Sort-Object -Unique
$outsideNow = @(
    $untrackedNow | Where-Object { $manifest -notcontains $_ }
)
$newOutsideUntracked = Compare-Object `
    $unrelatedUntrackedBaseline $outsideNow |
    Where-Object { $_.SideIndicator -eq "=>" }
if ($newOutsideUntracked) {
    throw "A new untracked path is outside the feature manifest."
}
$base = git merge-base HEAD origin/main
$featureChanged = @(
    git diff --name-only --diff-filter=ACMRD $base HEAD
    git diff --name-only --diff-filter=ACMRD
    git diff --cached --name-only --diff-filter=ACMRD
    ($untrackedNow | Where-Object { $manifest -contains $_ })
) | ForEach-Object { $_.Replace("\", "/") } |
    Sort-Object -Unique
$unlistedFeatureChange = $featureChanged |
    Where-Object { $manifest -notcontains $_ }
if ($unlistedFeatureChange) {
    throw "A feature change is outside the manifest: $unlistedFeatureChange"
}
git add -A --pathspec-from-file=$manifestPath
$stagedAfterAdd = git diff --cached --name-only --diff-filter=ACMRD |
    ForEach-Object { $_.Replace("\", "/") } |
    Sort-Object -Unique
$missingFromStage = $featureChanged |
    Where-Object { $stagedAfterAdd -notcontains $_ }
$unexpectedStage = $stagedAfterAdd |
    Where-Object { $manifest -notcontains $_ }
if ($missingFromStage) {
    throw "A changed feature file is not staged: $missingFromStage"
}
if ($unexpectedStage) {
    throw "A staged file is outside the feature manifest: $unexpectedStage"
}
```

This command stages deleted, modified, and untracked feature files. It leaves
unrelated worktree files unstaged.

## 23. Commit and Rebase

```powershell
$version = Get-Date -AsUTC -Format "yy.MM.dd.HH.mm"
git commit -m "version $version - add stale and bulk run controls" `
  -m "Closes #2447" `
  -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git fetch origin main
git rebase origin/main
```

After the rebase, rerun each affected local gate. If conflict repair changes a
feature file, update the manifest, stage all manifest paths, verify staging,
and commit the repair.

## 24. Push and Open the Pull Request

```powershell
git push --force-with-lease origin fix/2447-stale-bulk-run-controls
$prBodyPath = Join-Path $env:TEMP "misthelper-2447-pr-body.md"
Copy-Item ".github\PULL_REQUEST_TEMPLATE.md" $prBodyPath
# Complete every required field in $prBodyPath before the next command.
gh pr create `
  --base main `
  --head fix/2447-stale-bulk-run-controls `
  --title "fix(upgrade-portal): add stale and bulk run controls" `
  --body-file $prBodyPath
```

Do not push directly to `main`.

The pull request description must include:

- `Closes #2447`.
- A link to `specs/2447-stale-bulk-run-controls/spec.md`.
- A complete changed-file summary.
- Acceptance criteria and test evidence.
- Local gate results.
- Current CI status.
- Security results.
- UI screenshots or traces, when applicable.
- Deployment notes.
- Rollback notes.
- Every applicable item from `.github/PULL_REQUEST_TEMPLATE.md`.

Add `bug`, `web-portal`, and `in-progress`.

## 25. Pass CI, Add Auto-Merge, and Squash Merge

Wait for required human approval and all required pull request checks,
including CodeQL.

Repair only feature-caused failures in this feature. After approval and green
CI, add the `auto-merge` label. Confirm that the repository selects a squash
merge.

```powershell
$prNumber = gh pr view fix/2447-stale-bulk-run-controls `
    --json number --jq ".number"
gh pr checks $prNumber --watch
gh pr edit $prNumber --add-label auto-merge
gh pr view $prNumber --json mergeStateStatus,labels
```

Record the merged commit:

```powershell
git fetch origin main
$mergedRevision = git rev-parse origin/main
```

## 26. Wait for the Main Image

Wait for `.github/workflows/container-build.yml` that uses
`$mergedRevision`. Do not use a run from the feature branch.

```powershell
$mainBuild = gh run list `
  --workflow container-build.yml `
  --branch main `
  --commit $mergedRevision `
  --limit 1 `
  --json databaseId,headSha,status,conclusion |
    ConvertFrom-Json
if (-not $mainBuild -or $mainBuild.headSha -ne $mergedRevision) {
    throw "No main container build exists for the merged revision."
}
gh run watch $mainBuild.databaseId --exit-status
```

## 27. Verify the Exact Image Revision

```powershell
podman pull ghcr.io/jmorrison-juniper/misthelper:latest
$imageRevision = podman image inspect `
  ghcr.io/jmorrison-juniper/misthelper:latest `
  --format '{{ index .Labels "org.opencontainers.image.revision" }}'
if ($imageRevision -ne $mergedRevision) {
    throw "The image revision does not match the merged revision."
}
```

Stop deployment when the values differ.

## 28. Deploy and Check Health

```powershell
.\scripts\compose.ps1 up -d --no-deps misthelper
podman ps --filter "name=misthelper-app"
Invoke-WebRequest http://127.0.0.1:8056/healthz
Invoke-WebRequest http://127.0.0.1:8056/readyz
```

The container must be healthy. Both portal checks must succeed.

## 29. Validate the Local Portal

Open `http://127.0.0.1:8056/history`.

Confirm:

1. The history and run pages agree on stale state.
2. Hidden stored identifiers leave the selection during preview.
3. Reconciliation opens without a bulk preview.
4. The dialog shows exact server counts.
5. The result shows one durable outcome for each requested run.
6. An interrupted claimed item reports `processing_interrupted`.
7. A recovered action repeats no mutation.

Do not confirm a firmware action.

## 30. Optional Morrison House Verification

Run this section only after all prior sections pass.

Warning: the live check can reboot the Morrison House SRX. The reboot can
interrupt network service.

Require this separate phrase:

```text
MORRISON HOUSE SRX LIVE VERIFY
```

If the phrase does not match, record `skipped`. If it matches, use the existing
single-run workflow and its normal firmware confirmation.

Never use a bulk action for the live firmware write.
