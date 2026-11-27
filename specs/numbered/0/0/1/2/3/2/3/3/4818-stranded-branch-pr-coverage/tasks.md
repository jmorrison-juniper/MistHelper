# Tasks: Stranded branch pull request coverage

**Input**: `plan.md`, `spec.md`, and `design\` in this record folder.

**Execution order**: Run `T-LOCAL-GATES`, `T-PR`, `T-REMOTE-CI`, and `T-MERGE` first. These four tasks appear last in this file, as the template requires. Run `T004` onward only after `T-MERGE` completes. Tasks marked `[P]` may run in parallel with the task before them.

**Status values**: `open` means not started. `partial` means started with a gap. `verified-present` means the evidence exists now.

**Tick rule**: A task stays unchecked until its delivery evidence exists. Add the evidence note `(delivered: evidence location)` when the task completes.

**Repository paths**: Rollout tasks change GitHub state only. Each rollout task names the record file that holds its evidence.

## Phase 1: Evidence

- [ ] T001 [FR-001] [FR-017] Confirm the report rule and the tracker query defect from remote sources.
  - Repository paths: `specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\design\research.md` (RC-035 to RC-037, RC-053, RC-054).
  - Acceptance: The workflow blob SHA and the line numbers match research.md.
  - Verify: `gh api "repos/jmorrison-juniper/misthelper-devtools/contents/.github/workflows/reusable-stranded-branch-report.yml?ref=79a5e45970e876f1656d69520d9635cea1aa25ef" --jq .sha` returns `b8ca235c93beddef9307d797da87223a920df729`.
  - Status: verified-present.

- [ ] T002 [P] [FR-001] Record the replica count at the start of the rollout.
  - Repository paths: `specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\design\research.md` (RC-049).
  - Acceptance: The count is 537 on 2026-11-26. A later count replaces it only in the ledger comment.
  - Verify: `stranded-branch-report --repository jmorrison-juniper/MistHelper --base-branch main --min-age-days 7` prints one row for each stranded branch.
  - Status: partial. The replica count exists. The report run waits for the rollout day.

- [ ] T003 [P] [FR-011] Confirm the five open trackers before the rollout.
  - Repository paths: `specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\design\research.md` (RC-052, RC-054).
  - Acceptance: Issues 4302, 4583, 4719, 4818, and 4911 are open.
  - Verify: `gh issue list -R jmorrison-juniper/MistHelper --state open --search "in:title \"a branch holds work with no pull request\"" --json number`.
  - Status: verified-present.

## Phase 2: Pilot

- [ ] T004 [FR-001] [FR-006] [FR-019] Build the pilot list from a fresh replica run.
  - Repository paths: `specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\plan.md` (Pilot Scope).
  - Acceptance: The list has five names. Each name has the oldest head among the stranded branches with no pull request.
  - Verify: `gh pr list -R jmorrison-juniper/MistHelper --state all --head fix/3158-wip-controls --json number` returns an empty list for each pilot name.
  - Status: open. Depends on `T-MERGE`.

- [ ] T005 [FR-002] [FR-003] [FR-005] [FR-009] Create the five pilot draft pull requests.
  - Repository paths: none. GitHub state only.
  - Acceptance: Each draft has base `main`, the existing head, the title form, the body with `Refs #4818`, and the labels `chore` and `ci`.
  - Verify: `gh pr list -R jmorrison-juniper/MistHelper --state open --draft --json number,headRefName,headRefOid,title,labels`.
  - Status: open. Depends on `T004`.

- [ ] T006 [FR-007] Wait for the pilot check runs to finish.
  - Repository paths: none. GitHub state only.
  - Acceptance: No pilot check run has the status in progress.
  - Verify: `gh run list -R jmorrison-juniper/MistHelper --workflow ci.yml --limit 20 --json status,headBranch,conclusion`.
  - Status: open. Depends on `T005`.

- [ ] T007 [FR-006] [FR-010] Count the new quality-gate issues from the pilot.
  - Repository paths: none. GitHub state only.
  - Acceptance: The count compares open quality-gate issues before and after the pilot. The count appears in the pilot comment.
  - Verify: `gh issue list -R jmorrison-juniper/MistHelper --state open --label quality-gate --limit 200 --json number,title`.
  - Status: open. Depends on `T006`.

- [ ] T008 [P] [FR-004] [FR-010] Confirm that no pilot branch ref moved.
  - Repository paths: none. GitHub state only.
  - Acceptance: Each pilot branch head equals its head in the pilot list. The stop rule fires on any difference.
  - Verify: `gh api repos/jmorrison-juniper/MistHelper/branches/fix/3158-wip-controls --jq .commit.sha`. Repeat for each pilot name.
  - Status: open. Depends on `T005`.

- [ ] T009 [FR-010] Record the pilot result in one new comment on issue 4818.
  - Repository paths: none. GitHub state only.
  - Acceptance: The comment lists five pull request numbers, five head commits, the gate issue count, and the stop-rule result.
  - Verify: `gh issue view 4818 -R jmorrison-juniper/MistHelper --comments`.
  - Status: open. Depends on `T007` and `T008`.

- [ ] T010 [FR-020] Obtain the owner approval of the rollout volume.
  - Repository paths: none. GitHub state only.
  - Acceptance: The owner approves the volume in a new comment on issue 4818. This approval resolves decision D-12.
  - Verify: `gh issue view 4818 -R jmorrison-juniper/MistHelper --comments` shows the approval comment after the pilot comment.
  - Status: open. HUMAN-DECISION-REQUIRED. Depends on `T009`.

## Phase 3: Batches

- [ ] T011 [FR-001] [FR-019] Build the batch manifests from a fresh replica run.
  - Repository paths: none. GitHub state only.
  - Acceptance: The manifest has one row for each stranded branch. Each batch has ten rows, except the last batch. Rows are in oldest-head order.
  - Verify: The row count equals the replica count from `T002`.
  - Status: open. Depends on `T010`.

- [ ] T012 [P] [FR-002] [FR-003] [FR-005] [FR-008] [FR-009] Open the draft pull requests for each batch with pacing.
  - Repository paths: none. GitHub state only.
  - Acceptance: Each batch opens at most ten draft pull requests. The rate stays under 80 requests per minute and 500 requests per hour (S-2).
  - Verify: `gh pr list -R jmorrison-juniper/MistHelper --state open --draft --json number,headRefName,headRefOid`.
  - Status: open. Depends on `T011`.

- [ ] T013 [FR-005] [FR-007] Wait for each batch to finish its check runs. Confirm no label or review was added.
  - Repository paths: none. GitHub state only.
  - Acceptance: No batch check run is in progress. Each batch pull request has the labels `chore` and `ci` only.
  - Verify: `gh run list -R jmorrison-juniper/MistHelper --workflow ci.yml --limit 100 --json status,headBranch`.
  - Status: open. Depends on `T012`.

- [ ] T014 [FR-010] Record each batch in one new comment on issue 4818.
  - Repository paths: none. GitHub state only.
  - Acceptance: Each comment lists the pull request numbers and head commits of its batch.
  - Verify: `gh issue view 4818 -R jmorrison-juniper/MistHelper --comments`.
  - Status: open. Depends on `T013`.

- [ ] T015 [FR-008] Handle a secondary rate-limit response.
  - Repository paths: none. GitHub state only.
  - Acceptance: Wait 60 seconds. Retry up to three times. Stop and record the failure when the third retry fails.
  - Verify: `gh pr list -R jmorrison-juniper/MistHelper --state all --head fix/3158-wip-controls --json number` shows one pull request for each branch after a retry.
  - Status: open. Applies to `T012`.

## Phase 4: Verification and closure

- [ ] T016 [FR-001] [FR-014] Run the report after the last batch.
  - Repository paths: none. GitHub state only.
  - Acceptance: The report prints the clean message and exits with status 0.
  - Verify: `stranded-branch-report --repository jmorrison-juniper/MistHelper --base-branch main --min-age-days 7 --fail-on-find`.
  - Status: open. Depends on `T014`.

- [ ] T017 [P] [FR-003] [FR-004] Verify that each preservation pull request body uses `Refs #4818` and no closing keyword.
  - Repository paths: none. GitHub state only.
  - Acceptance: No body contains `Closes #4818`, `Fixes #4818`, or `Resolves #4818`. Each pull request head commit equals its branch head in the batch manifest (SC-002).
  - Verify: `gh pr list -R jmorrison-juniper/MistHelper --state all --search "Refs #4818" --limit 1000 --json number,body`.
  - Status: open. Depends on `T012`.

- [ ] T018 [P] [FR-004] Verify that no branch was deleted.
  - Repository paths: none. GitHub state only.
  - Acceptance: The branch count equals or exceeds the count of 598 from RC-047.
  - Verify: `gh api "repos/jmorrison-juniper/MistHelper/branches?per_page=100" --paginate --jq ".[].name"` piped to a count.
  - Status: open. Depends on `T012`.

- [ ] T019 [FR-012] Close the four duplicate trackers after authorization.
  - Repository paths: none. GitHub state only.
  - Acceptance: Issues 4302, 4583, 4719, and 4911 are closed. Each closing comment names issue 4818.
  - Verify: `gh issue view 4302 -R jmorrison-juniper/MistHelper --json state` returns `CLOSED`. Repeat for 4583, 4719, and 4911.
  - Status: open. Depends on `T016`.

- [ ] T020 [FR-011] Close issue 4818 after the report is clean and after authorization.
  - Repository paths: none. GitHub state only.
  - Acceptance: Issue 4818 is closed. The closing comment states the batch count and the report result.
  - Verify: `gh issue view 4818 -R jmorrison-juniper/MistHelper --json state` returns `CLOSED`.
  - Status: open. Depends on `T016`.

## Phase 5: Follow-up items

- [ ] T021 [FR-017] File the tracker defect in `misthelper-devtools` after authorization.
  - Repository paths: `specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\design\research.md` (RC-035 to RC-037, RC-053, RC-054).
  - Acceptance: The issue names the reusable workflow path, the query text, and the zero-result evidence.
  - Verify: `gh issue list -R jmorrison-juniper/misthelper-devtools --search "tracker" --json number,title`.
  - Status: open. Depends on `T001`.

- [ ] T022 [FR-017] File the pin drift defect in this repository after authorization.
  - Repository paths: `requirements-dev.txt` (RC-030) and `.github\workflows\ci.yml` (RC-019).
  - Acceptance: The issue names the devtools pin at `2239e7b` and the workflow pin at `79a5e45`. It names the installed version 0.6.4.
  - Verify: `gh issue list -R jmorrison-juniper/MistHelper --search "devtools pin" --json number,title`.
  - Status: open. Depends on `T001`.

- [ ] T023 [FR-015] Confirm that each local-only branch named by the owner stays off the remote.
  - Repository paths: none. GitHub state only.
  - Acceptance: Each named branch returns HTTP 404 on the remote branch API.
  - Verify: `gh api repos/jmorrison-juniper/MistHelper/branches/$name` returns HTTP 404 for each local-only name that the owner provides in `$name`.
  - Status: open. Depends on `T010`.

- [ ] T024 [FR-016] Confirm that the record change touches no workflow, test, pin, or reusable workflow.
  - Repository paths: `.github\workflows\`, `tests\guardrails\`, and `requirements-dev.txt` must show no change.
  - Acceptance: The changed path list holds only the record folder and the changelog fragment.
  - Verify: `git --no-pager -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" diff --name-only main...HEAD`.
  - Status: open. Depends on `T-PR`.

## Final tasks

- [ ] T-LOCAL-GATES [FR-013] [FR-018] Run the local gates that apply to the record files and the fragment.
  - Repository paths: the ten files under `specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\` (spec.md, plan.md, tasks.md, analysis.md, design\research.md, design\data-model.md, design\quickstart.md, design\contracts\preservation-pull-request.md, design\checklists\requirements.md, and design\checklists\rollout.md) and the fragment `changelog.d\issue-4818-stranded-branch-pr-coverage.md`. The eleven files are all Markdown.
  - Acceptance: The Markdown gate scores each file at 80 or above. Each guard prints its examined count and exits with status 0.
  - Verify: `ste-linter --config .ste-linter.toml --min-score 80` with the explicit file list in quickstart.md. Then `python -m pytest tests/guardrails/test_process_folder_structure.py -q`, `python -m pytest tests/guardrails/test_spec_route_contract.py -q`, and `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`.
  - Status: open.

- [ ] T-PR [FR-003] [FR-009] [FR-013] [FR-018] Commit the record and open the record pull request.
  - Repository paths: the record folder, the changelog fragment, and no other path.
  - Acceptance: The commit title is `docs(specs): record the stranded branch pull request plan for issue 4818`. The branch is `docs/4818-stranded-branch-pr-coverage`. The body contains `Refs #4818` and does not contain `Closes #4818` (D-8).
  - Verify: `gh pr view --json title,body,headRefName,isDraft`.
  - Status: open. Depends on `T-LOCAL-GATES`.

- [ ] T-REMOTE-CI [FR-013] Watch the CI runs on the record pull request.
  - Repository paths: none. GitHub state only.
  - Acceptance: Each required check passes on the head commit.
  - Verify: `gh pr checks --watch`.
  - Status: open. Depends on `T-PR`.

- [ ] T-MERGE [FR-013] Squash merge the record pull request after the orchestrator authorizes it.
  - Repository paths: none. GitHub state only.
  - Acceptance: The auto-merge label is added only after every check passes and the orchestrator authorizes the merge. The pull request merges as one squash commit.
  - Verify: `gh pr view --json state,mergedAt,mergeCommit`.
  - Status: open. Depends on `T-REMOTE-CI`.

## Dependencies & Execution Order

- `T-LOCAL-GATES` precedes `T-PR`. `T-PR` precedes `T-REMOTE-CI`. `T-REMOTE-CI` precedes `T-MERGE`.
- `T-MERGE` precedes `T004`. `T004` precedes `T005`. `T005` precedes `T006`, `T008`, and `T012`.
- `T007` and `T008` precede `T009`. `T009` precedes `T010`. `T010` precedes `T011`.
- `T011` precedes `T012`. `T012` precedes `T013`. `T013` precedes `T014`. `T014` precedes `T016`.
- `T016` precedes `T019` and `T020`.
- `T001` precedes `T021` and `T022`. `T010` precedes `T023`.
- `T002` and `T003` have no prerequisite. `T015` applies during `T012`.

## Coverage

Each functional requirement appears in at least one task.

- FR-001: T001, T002, T004, T011, T016
- FR-002: T005, T012
- FR-003: T005, T012, T017, T-PR
- FR-004: T008, T017, T018
- FR-005: T005, T012, T013
- FR-006: T004, T005, T007
- FR-007: T006, T013
- FR-008: T012, T015
- FR-009: T005, T012, T-PR
- FR-010: T007, T008, T009, T014
- FR-011: T003, T020
- FR-012: T019
- FR-013: T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE
- FR-014: T016
- FR-015: T023
- FR-016: T024
- FR-017: T001, T021, T022
- FR-018: T-LOCAL-GATES, T-PR
- FR-019: T004, T011
- FR-020: T010
