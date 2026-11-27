# Tasks: Stranded Branch Preservation

**Input**: Design documents in `specs/numbered/0/0/1/2/2/3/3/4/4719-stranded-branch-preservation/`

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, `design/contracts/branch-inventory.md`, and `design/quickstart.md`

**Tests**: The checks TC-01 to TC-12 in `design/quickstart.md` verify these tasks. No code test applies.

**Status values**: `verified-present`, `partial`, `open`, or `absent`. A checked box marks a task that this record verified.

## Format

- **[P]**: The task runs in parallel. It changes no branch or file that another parallel task changes.
- **Requirements**: The FR and SC IDs that the task serves.
- **Paths**: Exact repository paths. For a GitHub state task, the ref paths name the branches. The branch list is in `design/data-model.md`.
- **Verify**: The check that proves the task.
- **Local gates**: The local gates table names no check for GitHub state. Each GitHub task uses its quickstart check. Task T-LOCAL-GATES runs the guardrail suite, which the move-a-module gate table names.

## Phase 1: Verification (complete in this record, except T006)

- [X] T001 [P] [FR-001, FR-002] Verify that all 51 branch heads exist on GitHub. Verify that no pull request holds a listed head. Paths: the branch refs under `refs/heads/` for the 51 branches listed in `design/data-model.md`. Verify: TC-01 and TC-02. Acceptance: 51 of 51 heads exist. 49 of 49 recorded heads equal the owner comment values. No pull request holds a listed head. Status: verified-present.
- [X] T002 [P] [FR-001] Record each branch commit count, commit subject list, and changed path count from the local clone. Paths: `design/data-model.md` inventory table. Verify: TC-01. Acceptance: 51 rows. Commit total 66. Path entry total 515. The privacy-held branch shows a count only. Status: verified-present.
- [X] T003 [P] [FR-009] Verify the five open duplicate tracking issues and the title search defect. Paths: `design/research.md` sources S-03 and S-06. Verify: TC-09. Acceptance: five open issues carry the tracking title. The workflow title search returns no match. The plain-word search returns all five. Status: verified-present.
- [X] T004 [P] [FR-009, FR-010] Verify the upstream workflow defect and the pin. Paths: `misthelper-devtools:.github/workflows/reusable-stranded-branch-report.yml` at the pin and on `main`. Verify: TC-10. Acceptance: both blob SHAs equal `b8ca235c93beddef9307d797da87223a920df729`. The search line is 156. The latest tag is `v0.6.4`. Status: verified-present.
- [X] T005 [P] [FR-012] Verify the route on `main`. Paths: `specs/numbered/0/0/1/2/2/3/3/4/`. Verify: TC-11. Acceptance: the leaf is absent. The parent `3/3` holds 4 children, so one child is allowed. Status: verified-present.
- [X] T006 [P] [FR-008] Verify that the two local-only branches have no remote copy. Paths: `refs/heads/jmorrison-juniper-issue-triage-overlap-analysis` and `refs/heads/jmorrison-juniper-ssh-telemetry-test-repair`. Verify: TC-08. Acceptance: both remote refs are absent. Local existence is not verified in this clone. Status: partial.
- [X] T007 [P] [FR-014] Verify each cited line on `main` from its blob. Paths: the 31 document and workflow rows in `design/research.md`. Verify: TC-12. Acceptance: each line matches its cited text. Status: verified-present.

## Phase 2: Preservation (blocked by owner gates)

- [ ] T010 [FR-004] The owner releases the publication hold in a written comment on issue #4719. Paths: none (GitHub issue #4719). Verify: TC-04. Acceptance: the release comment time precedes the first preservation pull request. Status: open.
- [ ] T011 [FR-003, FR-005] Open 46 draft preservation pull requests for batch 1. Paths: the branch refs under `refs/heads/` for the 46 batch 1 rows in `design/data-model.md`. Each body names the branch, the full head SHA, and issue #4719. Verify: TC-03 and TC-05. Acceptance: 46 draft pull requests exist. Each head SHA equals the inventory. No branch changed. Status: open. Depends on T010.
- [ ] T012 [FR-007] Open the four batch 2 draft preservation pull requests after the owner reconciles pull requests #4208 and #4813. Paths: `refs/heads/recovery/3213-handoff-20261004`, `refs/heads/jmorrison-juniper-issue-2746`, `refs/heads/jmorrison-juniper-local-build-revision`, and `refs/heads/recovery/3699-handoff-20261004`. Verify: TC-07. Acceptance: the owner comment names the reconciliation. Status: open. Depends on T011.
- [ ] T013 [FR-006] The owner completes a privacy review of `recovery/2977-handoff-20261004`. Then open one draft preservation pull request for it. Paths: `refs/heads/recovery/2977-handoff-20261004`. Verify: TC-06. Acceptance: the owner review comment exists. The pull request body holds no source content and no path name. Status: open. Depends on T010.
- [ ] T014 [FR-008] The owner verifies the two local-only branches in their own clone. Push a branch only after the owner approves it. Paths: `refs/heads/jmorrison-juniper-issue-triage-overlap-analysis` and `refs/heads/jmorrison-juniper-ssh-telemetry-test-repair`. Verify: TC-08. Acceptance: the owner comment confirms each head SHA. Status: open.
- [ ] T015 [FR-015] Create a separate record that inventories the 434 archive rows and the 20 other rows of issue #4911. Paths: a new record under the managed route for its own issue number. Verify: TC-01. Acceptance: the separate record exists and lists all 454 rows. Status: open.
- [ ] T020 [FR-009] Open a defect issue in `misthelper-devtools` for the title search. Paths: `misthelper-devtools:.github/workflows/reusable-stranded-branch-report.yml` at line 156. The reproduction is in `design/quickstart.md`. Verify: TC-09. Acceptance: the issue exists in `misthelper-devtools`. Status: open.
- [ ] T021 [FR-010] Move both workflow pins to a released tag that contains the T020 fix. Paths: `.github/workflows/stranded-branch-report.yml` at line 47 and `.github/workflows/close-linked-issues.yml` at line 50. Verify: TC-10. Acceptance: both pins name the new tag. The weekly report names no branch whose current head has a pull request. Status: open. Depends on T020.
- [ ] T022 [FR-011] Close the duplicate tracking issues 4302, 4583, 4818, and 4911 after owner approval. Keep one canonical open issue. Paths: GitHub issues only. Verify: TC-10. Acceptance: exactly one open issue carries the tracking title. Status: open. Depends on T021.

## Phase 3: Final gates and delivery

- [ ] T-LOCAL-GATES [FR-012, FR-016] Run the applicable local gates on the record branch. Paths: `specs/numbered/0/0/1/2/2/3/3/4/4719-stranded-branch-preservation/` and `changelog.d/issue-4719-stranded-branch-preservation.md`. Verify: TC-11 and TC-12. Acceptance: the guardrail suite shows no new failure compared with a baseline run on `main`. The text checks report no finding. Status: open.
- [ ] T-PR [FR-013] Commit with the title `chore(ci): record the stranded branch preservation plan`. Push `chore/4719-stranded-branch-preservation`. Open the pull request with the closing line `Closes #4719`, the file summary, and the gate results. Paths: the eleven record and fragment files named in `plan.md`. Verify: TC-11. Acceptance: the title passes the title check. The body names the constitution steps 10 to 12 result. Status: open. Depends on T-LOCAL-GATES.
- [ ] T-REMOTE-CI [FR-013] Watch the record pull request checks with `gh pr checks --watch`. Paths: none (GitHub checks). Verify: TC-11. Acceptance: every required check passes. Status: open. Depends on T-PR.
- [ ] T-MERGE [FR-013] Add the `auto-merge` label after the checks pass and the orchestrator authorizes the merge. Squash-merge the pull request. Remove the branch and its worktree. Paths: none (GitHub pull request). Verify: the `main` tree holds the record folder. Acceptance: one squash commit reaches `main`. Status: open. Depends on T-REMOTE-CI.

## Dependencies and execution order

- T010 precedes T011, T013, and T014.
- T011 precedes T012.
- T020 precedes T021. T021 precedes T022.
- T-LOCAL-GATES precedes T-PR. T-PR precedes T-REMOTE-CI. T-REMOTE-CI precedes T-MERGE.
- T015 has no prerequisite in this record.

## Parallel opportunities

- Tasks T001 to T007 run in parallel. Each reads GitHub or the clone, and none writes.
- Within T011, the 46 branch pull requests open in parallel batches. Keep rate limits under the GitHub limit.
