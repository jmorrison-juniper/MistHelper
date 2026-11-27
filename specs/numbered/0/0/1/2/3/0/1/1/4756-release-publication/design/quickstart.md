# Quickstart: Release Publication

Run Scenarios 1 to 10 as the implementer. Run Scenarios 11 to 15 as the owner. Each scenario states the expected result. Read `spec.md` first.

## Shell Rules

- Run the two environment lines in the same shell before each `gh` command.
- Never print the value of an environment variable whose name contains TOKEN, KEY, SECRET, or PASSWORD.
- Set `$STAMP` before any later scenario. Set `$TAG` from `$STAMP`. Set `$MERGE_SHA` after the merge.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

```powershell
$REPO = 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper'
$WORKTREE = 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-release-4756'
```

## Scenario 1: Preflight Reads (T001)

Expected results: the main head is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (RC-01). The release branch list is empty (RC-05). PR 4208 is open (RC-19). The fragment count is 334 (RC-15). Each hold pull request reports its state.

```powershell
gh api repos/jmorrison-juniper/MistHelper/git/refs/heads/main --jq .object.sha
gh pr view 4208 --repo jmorrison-juniper/MistHelper --json state,mergedAt
gh api repos/jmorrison-juniper/MistHelper/git/matching-refs/heads/release/4756 --jq '.[].ref'
$tree = gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" | ConvertFrom-Json
@($tree.tree | Where-Object { $_.path -match '^changelog\.d/.+\.md$' -and $_.path -ne 'changelog.d/README.md' }).Count
```

```powershell
foreach ($number in @(4741, 4701, 4659, 4619, 4617, 4615, 4607, 4605, 4547, 4493, 4404, 4358, 4322, 4208)) {
    gh pr view $number --repo jmorrison-juniper/MistHelper --json number,state --jq '(.number | tostring) + " " + .state'
}
```

## Scenario 2: Release Stamp (T003)

Expected results: the comparison prints `True`. The tag query prints nothing, which proves that no tag matches the release tag (RC-04).

```powershell
$STAMP = (Get-Date).ToUniversalTime().ToString('yy.MM.dd.HH.mm')
$TAG = 'v' + $STAMP
$DATE = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
$STAMP -gt '26.11.21.06.27'
gh api "repos/jmorrison-juniper/MistHelper/git/matching-refs/tags/$TAG" --jq '.[].ref'
```

## Scenario 3: Worktree and Bootstrap (T002)

Expected results: the worktree holds the new branch at `origin/main`. The bootstrap command finishes without error.

```powershell
git -C $REPO fetch --no-tags origin main
git -C $REPO worktree add $WORKTREE -b release/4756-release-publication origin/main
Set-Location $WORKTREE
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

## Scenario 4: Section and Deletion (T004 to T006)

Follow these steps in order.

1. Read each `changelog.d/*.md` file except `README.md`, in ordinal name order.
2. Write one level-three entry for each fragment. Keep the bullets unchanged. Change only the count of number signs in the heading when it differs from three.
3. Rewrite each relative link so that it resolves from the repository root. Keep the link text and any anchor.
4. Write the section text to `test-artifacts\release-4756\section.md`.
5. Insert the section after line 14 of `CHANGELOG.md`. Keep the Unreleased heading at line 13 and leave its section empty.
6. Delete the collected fragments in batches of 100. Keep `README.md`.

Run the deletion step with this block after step 6 is ready.

```powershell
$collected = @(Get-ChildItem -Path (Join-Path $WORKTREE 'changelog.d') -Filter '*.md' | Where-Object { $_.Name -ne 'README.md' } | ForEach-Object { $_.FullName })
$collected.Count
$batchIndexes = 0..[Math]::Floor(($collected.Count - 1) / 100)
foreach ($batchIndex in $batchIndexes) {
    $start = $batchIndex * 100
    $last = [Math]::Min($start + 99, $collected.Count - 1)
    git -C $WORKTREE rm --quiet -- $collected[$start..$last]
}
```

Expected results: the first count equals the entry count in the section. After deletion, `changelog.d/` holds `README.md` only.

## Scenario 5: Local Gates (T-LOCAL-GATES)

Expected results: each command exits with zero, and each test reports a pass.

```powershell
Set-Location $WORKTREE
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
python -m pytest tests/guardrails/test_markdown_links.py
python -m pytest tests/contract/test_release_body_workflow.py
```

## Scenario 6: Reconciliation (TEST-4)

Expected results: the changed paths are `CHANGELOG.md` and the deleted fragments only. `pyproject.toml` does not appear. The reconciliation output in `test-artifacts\release-4756\reconcile.txt` reports zero differences for the count, the verbatim text, the empty Unreleased section, the stamp order, and the absent tag.

```powershell
git -C $WORKTREE diff --name-status origin/main
git -C $WORKTREE diff --name-only origin/main -- changelog.d
```

## Scenario 7: Commit and Push (T-PR)

The commit message file holds this text. The first line is `chore(release): prepare release` followed by the release tag. The second line is blank. The third line is `Closes #4756`. The fourth line is blank. The last line is the trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`.

Expected results: the commit changes `CHANGELOG.md` and removes the fragments. The push creates the remote branch without force.

```powershell
git -C $WORKTREE add -- CHANGELOG.md
git -C $WORKTREE add -u -- changelog.d
git -C $WORKTREE commit -F test-artifacts\release-4756\commit-message.txt
git -C $WORKTREE push -u origin release/4756-release-publication
```

## Scenario 8: Pull Request (T-PR)

The pull request body file holds the fragment count, the gate results, the reconciliation summary, and the template answers. Template items 36 and 38 state that they do not apply, with the reason.

Expected results: the pull request opens against `main` with the labels `chore` and `docs`.

```powershell
gh pr create --repo jmorrison-juniper/MistHelper --base main --head release/4756-release-publication --title "chore(release): prepare release $TAG" --body-file test-artifacts\release-4756\pr-body.md --label chore --label docs
$PR = gh pr view release/4756-release-publication --repo jmorrison-juniper/MistHelper --json number --jq .number
$PR
```

## Scenario 9: Remote Checks (T-REMOTE-CI)

Expected results: all 15 required checks report success on the head commit (RC-22).

```powershell
gh pr checks $PR --repo jmorrison-juniper/MistHelper --watch
gh pr checks $PR --repo jmorrison-juniper/MistHelper
```

## Scenario 10: Merge (T-MERGE)

Run this scenario only after the orchestrator authorizes the merge. Repeat Scenario 1 first. If the fragment count changed, repeat Scenarios 4 to 7 on a rebased branch.

Expected results: the label starts the squash merge. The state becomes `MERGED`, and the merge commit SHA is printed.

```powershell
gh pr edit $PR --repo jmorrison-juniper/MistHelper --add-label auto-merge
gh pr view $PR --repo jmorrison-juniper/MistHelper --json state,mergeCommit --jq '.state + " " + (.mergeCommit.oid // "")'
```

## Scenario 11: Owner Tag (OWN-001)

The owner sets `$STAMP` to the stamp in the CHANGELOG heading on `main`. Then the owner sets `$TAG` from it. The owner also sets `$PR` to the release pull request number from Scenario 8.

Expected results: the peeled line for the tag names `$MERGE_SHA`. The tag push starts `release.yml` (RC-23).

```powershell
$MERGE_SHA = gh pr view $PR --repo jmorrison-juniper/MistHelper --json mergeCommit --jq .mergeCommit.oid
git -C $REPO fetch --tags origin
git -C $REPO tag -a $TAG $MERGE_SHA -m "Release $TAG"
git -C $REPO push origin $TAG
git ls-remote --tags origin $TAG
```

## Scenario 12: Release Workflow (OWN-002)

Expected results: the command exits with zero, and the run conclusion is success.

```powershell
$RUN_ID = gh run list --repo jmorrison-juniper/MistHelper --workflow release.yml --limit 1 --json databaseId --jq '.[0].databaseId'
gh run watch $RUN_ID --repo jmorrison-juniper/MistHelper --exit-status
```

## Scenario 13: Assets (OWN-003)

Expected results: the output lists one wheel, one source archive, and one ZIP named with the stamp.

```powershell
gh release view $TAG --repo jmorrison-juniper/MistHelper --json assets --jq '.assets[].name'
```

## Scenario 14: Container Tags and Labels (OWN-004)

Expected results: the two digests are equal. The revision label equals `$MERGE_SHA`. The version label value is recorded for the owner report (U-3).

```powershell
podman pull ghcr.io/jmorrison-juniper/misthelper:$STAMP
podman pull ghcr.io/jmorrison-juniper/misthelper:latest
podman image inspect ghcr.io/jmorrison-juniper/misthelper:$STAMP --format '{{.Digest}}'
podman image inspect ghcr.io/jmorrison-juniper/misthelper:latest --format '{{.Digest}}'
podman image inspect ghcr.io/jmorrison-juniper/misthelper:$STAMP --format '{{index .Config.Labels "org.opencontainers.image.revision"}}'
podman image inspect ghcr.io/jmorrison-juniper/misthelper:$STAMP --format '{{index .Config.Labels "org.opencontainers.image.version"}}'
```

## Scenario 15: Title and Body (OWN-005)

The owner writes the summary in `$SUMMARY`. The summary has 12 words or fewer.

Expected results: the title starts with `$TAG`, a space, a hyphen, and a space. The body contains the compare link and the CHANGELOG link.

```powershell
gh release edit $TAG --repo jmorrison-juniper/MistHelper --title "$TAG - $SUMMARY"
gh release view $TAG --repo jmorrison-juniper/MistHelper --json name,body --jq '.name'
gh release view $TAG --repo jmorrison-juniper/MistHelper --json body --jq '.body'
```

## Rollback Reads

Read these values before any rollback step. A rollback step follows `spec.md` and `plan.md`.

```powershell
git ls-remote --tags origin $TAG
gh release view $TAG --repo jmorrison-juniper/MistHelper --json isDraft,isPrerelease
```
