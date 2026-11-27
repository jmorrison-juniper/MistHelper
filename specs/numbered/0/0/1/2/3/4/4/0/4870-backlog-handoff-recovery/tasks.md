# Tasks: Backlog Handoff Recovery

**Input**: Numeric record `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/`.

**Prerequisites**: plan.md (required), spec.md (required), design/research.md, design/data-model.md, design/quickstart.md, and the two contracts under design/contracts/.

**Verification rule**: Each task names one command from the STE row of the local gates table, run on each file the task changes. Each task also names its check in `design/quickstart.md`. The checks run on the record, not on the product code.

**Status values**: `verified-present`, `partial`, `absent`, or `open`. A status of `open` means that work remains.

**Format**: `[P]` marks a task that can run in parallel with other `[P]` tasks. Requirement IDs refer to `spec.md`.

## Phase 1: Verify the handoff against GitHub main

### T001 [P] Verify the handoff facts and comments

- **Requirements**: FR-001, FR-021
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: The body and six comments match the handoff text. The labels `chore` and `docs` exist.
- **Verification**: STE row on the file above. Check TST-01.
- **Status**: verified-present

### T002 [P] Verify the inventory rows against GitHub

- **Requirements**: FR-001, FR-002, FR-013
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/contracts/inventory-table.md`
- **Acceptance**: All 127 rows match the titles and label sets. 126 rows are OPEN. Issue 4867 is CLOSED.
- **Verification**: STE row on the file above. Check TST-02.
- **Status**: partial

### T003 [P] Count the open issues and list the issues outside the inventory

- **Requirements**: FR-002
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: The open count is 166. The 40 issues outside the inventory are listed by number.
- **Verification**: STE row on the file above. Check TST-03.
- **Status**: partial

### T004 [P] Verify the open PR set and the named PR states

- **Requirements**: FR-001, FR-002, FR-004, FR-005
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: Seven PRs are open. PRs 4813 and 4208 are drafts. The five Dependabot PRs are listed.
- **Verification**: STE row on the file above. Check TST-04.
- **Status**: partial

### T005 [P] Verify the 31 merge commits in handoff sections 7 and 8

- **Requirements**: FR-001
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: Each of the 31 merge SHA prefixes matches its PR.
- **Verification**: STE row on the file above. Check TST-05.
- **Status**: verified-present

### T006 [P] Verify the 127 local commit tips

- **Requirements**: FR-012
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: The 127 rows give 44 distinct SHAs. All 44 resolve on GitHub.
- **Verification**: STE row on the file above. Check TST-06.
- **Status**: verified-present

### T007 [P] Verify the recovery refs and the archive tags

- **Requirements**: FR-011
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: 63 recovery refs exist, and 6 MistHelper refs end in `-wip-20261122`. 169 archive tags exist. The 47 new tags stay unnamed.
- **Verification**: STE row on the file above. Check TST-07.
- **Status**: partial

### T008 [P] Verify the feature pointer blob

- **Requirements**: FR-006
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: Blob b86bcad0 on main equals the parent blob of PR 4846.
- **Verification**: STE row on the file above. Check TST-08.
- **Status**: verified-present

### T009 [P] Verify the route helper and the route math

- **Requirements**: FR-007, FR-025
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`, `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/data-model.md`
- **Acceptance**: `Resolve-SpecFeaturePath` sits at line 34 of `.specify/scripts/powershell/spec-route.ps1`. Issue 4870 maps to 0/0/1/2/3/4/4/0.
- **Verification**: STE row on both files. Checks TST-09 and TST-19.
- **Status**: verified-present

### T010 [P] Verify the devtools pins and the workflow uses lines

- **Requirements**: FR-008
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: The three Python pins name 2239e7bd. Nine uses lines name 79a5e459. One uses line names d63a1204.
- **Verification**: STE row on the file above. Check TST-10.
- **Status**: partial

### T011 [P] Verify the uv pin and its guard

- **Requirements**: FR-010
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: `container-build.yml` line 92 and `pyproject.toml` line 101 pin `uv==0.13.9`.
- **Verification**: STE row on the file above. Check TST-11.
- **Status**: verified-present

### T012 [P] Verify the mistapi invite claim

- **Requirements**: FR-001
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: `listOrgInvites` is absent from the 288 SDK files. The export skips the call at `org_export_utils.py` lines 726 to 735.
- **Verification**: STE row on the file above. Check TST-12.
- **Status**: verified-present

### T013 [P] Verify the main head and the latest Quality Gates run

- **Requirements**: FR-009
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: Main head is f03c6c9b3. Quality Gates run 45774119357 completed with success.
- **Verification**: STE row on the file above. Check TST-13.
- **Status**: verified-present

### T014 [P] Verify the held-by PR numbers

- **Requirements**: FR-001, FR-012
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: Of the 25 held-by numbers, 19 are PRs (18 merged and 4813 OPEN). Six are issues.
- **Verification**: STE row on the file above. Check TST-14.
- **Status**: partial

### T015 [P] Verify the named issue states and the stale claims

- **Requirements**: FR-001, FR-003
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: Ten named states match. Issues 4762 and 4867 are stale in the handoff.
- **Verification**: STE row on the file above. Check TST-15.
- **Status**: partial

### T016 [P] Verify the commit count and its delta

- **Requirements**: FR-002
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: Main holds 2535 commits, eight ahead of 1982b7e84.
- **Verification**: STE row on the file above. Check TST-16.
- **Status**: verified-present

### T017 [P] Verify that the cited local files equal their main blobs

- **Requirements**: FR-001
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: All 26 cited local files match their main blob SHAs.
- **Verification**: STE row on the file above. Check TST-17.
- **Status**: verified-present

### T018 [P] Verify that no legacy record exists

- **Requirements**: FR-007
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: No folder starts with `4870-` on main or in the local specs tree.
- **Verification**: STE row on the file above. Check TST-18.
- **Status**: verified-present

## Phase 2: Record the decisions

### T019 Record the 22 decisions with alternatives, reasons, and risks

- **Requirements**: FR-003, FR-015, FR-019
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: Each decision row has alternatives, a reason, a risk, and a human flag.
- **Verification**: STE row on the file above. Checks TST-20, TST-23, TST-24, and TST-28.
- **Status**: verified-present

### T020 Record the four human decisions

- **Requirements**: FR-015
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`, `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/analysis.md`
- **Acceptance**: The list names H-1 to H-4, each with options and a recommended option.
- **Verification**: STE row on both files. Check TST-25.
- **Status**: verified-present

## Phase 3: Actions that need GitHub writes or owner input

### T021 Post the state comment and the decision comment on issue 4870

- **Requirements**: FR-018, FR-020
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/contracts/decision-comment.md`
- **Acceptance**: The identity check passes first. The comment follows the decision-comment contract. The comment count rises by one.
- **Verification**: STE row on the file above. Check TST-01.
- **Status**: open

### T022 Update the handoff body

- **Requirements**: FR-002, FR-003, FR-020
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/contracts/inventory-table.md`, `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: Sections 9, 11, 12, and 13 read as superseded. The body shows 166 open issues, seven open PRs, 63 recovery refs, and 169 archive tags.
- **Verification**: STE row on both files. Checks TST-03, TST-04, and TST-25.
- **Status**: open

### T023 Refresh the inventory

- **Requirements**: FR-002, FR-013
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/contracts/inventory-table.md`
- **Acceptance**: Issue 4867 leaves the open rows. The 40 issues outside the inventory get a category each.
- **Verification**: STE row on the file above. Checks TST-02 and TST-03.
- **Status**: open

### T024 Triage the unclassified rows and the new open issues

- **Requirements**: FR-013
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/analysis.md`
- **Acceptance**: Issues 4837, 4863, and 4868 get a category. The 37 new issues get a category each.
- **Verification**: STE row on the file above. Check TST-15.
- **Status**: open

### T025 Fix issues 4721 and 4722 in one branch

- **Requirements**: FR-014
- **Files**: `src/operations/exporting/export/device_events_52w_exporter.py`, `MistHelper.py`, `tests/unit/test_device_events_52w_exporter.py`, `tests/unit/test_device_events_52w_exporter_extended.py`
- **Acceptance**: The resume path keeps the existing device-event rows. Menu 97 reports a failure when the SQLite write fails.
- **Verification**: Tests row, `python -m pytest tests/unit/test_device_events_52w_exporter.py`. Check TST-33.
- **Status**: open

### T026 Refresh the Dependabot PRs 4886 to 4890

- **Requirements**: FR-009, FR-010
- **Files**: `requirements.txt`, `requirements-dev.txt`, `uv.lock`, `pyproject.toml`, `.github/workflows/container-build.yml`
- **Acceptance**: No PR merges while a gate fails. Each pip PR follows the section 5 steps.
- **Verification**: Tests row, `python -m pytest tests/guardrails/test_dependency_export.py`. Check TST-31.
- **Status**: open

### T027 Align the devtools pins to 2239e7bd

- **Requirements**: FR-008
- **Files**: `.github/workflows/auto-merge.yml`, `.github/workflows/ci.yml`, `.github/workflows/close-linked-issues.yml`, `.github/workflows/codeql.yml`, `.github/workflows/container-build.yml`, `.github/workflows/release.yml`, `.github/workflows/ste-lint.yml`, `.github/workflows/stranded-branch-report.yml`
- **Acceptance**: All ten uses lines name 2239e7bd. The three Python pins still name 2239e7bd.
- **Verification**: Tests row, `python -m pytest tests/guardrails/test_container_build_trigger.py`. Check TST-32. Then T-REMOTE-CI.
- **Status**: open

### T028 Review the recovery refs and the archive tags

- **Requirements**: FR-011
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/data-model.md`
- **Acceptance**: Each of the 63 recovery refs and 169 archive tags has a review decision. No ref is deleted before its decision.
- **Verification**: STE row on the file above. Check TST-07.
- **Status**: open

### T029 Correct the mistapi floor in the instruction file

- **Requirements**: FR-019
- **Files**: `.github/copilot-instructions.md`
- **Acceptance**: Line 21 names the floor in `pyproject.toml`, which is `mistapi>=0.64.1,<0.65`.
- **Verification**: STE row on the file above. Check TST-20.
- **Status**: open

### T030 Apply the hold-phrase rule to the open PR bodies

- **Requirements**: FR-023
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: The four phrases of decision D-9 match as whole words in each open PR body. The matches are recorded.
- **Verification**: STE row on the file above. Check TST-37.
- **Status**: open

### T031 Keep the Podman volumes

- **Requirements**: FR-016
- **Files**: `documentation/container-deployment.md`
- **Acceptance**: No command prunes a volume. A test volume is removed only by its exact name.
- **Verification**: Tests row, `python -m pytest tests/guardrails/test_container_policy_docs.py`. Check TST-34.
- **Status**: open

### T032 Ask human decision H-1 about staging

- **Requirements**: FR-004, FR-015
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: The user supplies staging credentials, or confirms the hold. The answer appears in the decision comment.
- **Verification**: STE row on the file above. Check TST-25.
- **Status**: open (human decision H-1)

### T033 Ask human decision H-2 about licensing

- **Requirements**: FR-015
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: The owner records the licensing decision for issue 4635.
- **Verification**: STE row on the file above. Check TST-25.
- **Status**: open (human decision H-2)

### T034 Ask human decision H-3 about PR 4208

- **Requirements**: FR-005, FR-015
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: The owner decides whether to continue or close PR 4208.
- **Verification**: STE row on the file above. Check TST-25.
- **Status**: open (human decision H-3)

### T035 Ask human decision H-4 about the secret file

- **Requirements**: FR-015, FR-017
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: The owner names a destination for the `.env` file of worktree live-deploy-aa0762d.
- **Verification**: STE row on the file above. Check TST-25.
- **Status**: open (human decision H-4)

### T036 Verify the coordinator laptop claims on that host

- **Requirements**: FR-021, FR-022
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: Each entry U-01 to U-03 is verified on that host, or it stays with its reason.
- **Verification**: STE row on the file above. Check TST-25.
- **Status**: open

### T037 Copy the cleanup archive to durable storage

- **Requirements**: FR-022
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`
- **Acceptance**: The owner names a durable location. The archive folder exists there before the laptop cleanup starts.
- **Verification**: STE row on the file above. Check TST-25.
- **Status**: open

### T038 Scope the first slice of issue 1794

- **Requirements**: FR-013
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/analysis.md`
- **Acceptance**: The first module and the order of the three preserved slices are recorded.
- **Verification**: STE row on the file above. Check TST-25.
- **Status**: open

## Phase 4: Final tasks

### T-LOCAL-GATES Run the local gates for the record

- **Requirements**: FR-007, FR-019, FR-025
- **Files**: `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/spec.md`, `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/plan.md`, `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/tasks.md`, `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/analysis.md`, `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md`, `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/data-model.md`, `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/quickstart.md`, `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/contracts/inventory-table.md`, `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/contracts/decision-comment.md`, `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/checklists/requirements.md`, `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/checklists/security.md`, `changelog.d/issue-4870-backlog-handoff-recovery.md`
- **Acceptance**: Each Markdown file scores 80 or above. The layout guard and the route contract test pass.
- **Verification**: STE row on each Markdown file. Tests rows, `python -m pytest tests/guardrails/test_process_folder_structure.py` and `python -m pytest tests/guardrails/test_spec_route_contract.py`. Checks TST-20 to TST-28.
- **Status**: open

### T-PR Open the pull request

- **Requirements**: FR-006, FR-022, FR-024
- **Files**: The eleven record files listed under T-LOCAL-GATES, and `changelog.d/issue-4870-backlog-handoff-recovery.md`
- **Acceptance**: The branch `chore/4870-backlog-handoff-recovery` starts from main. The commit subject is `docs(specs): add backlog handoff recovery record for issue 4870`. The PR body contains `Closes #4870`, the gate results, and the file list. The feature pointer blob stays at b86bcad0.
- **Verification**: STE row on the changelog fragment. Tests row, `python -m pytest tests/guardrails/test_process_folder_structure.py`. Checks TST-29, TST-30, and TST-36.
- **Status**: open

### T-REMOTE-CI Watch the CI run

- **Requirements**: FR-009
- **Files**: `.github/workflows/ci.yml`, `.github/workflows/ste-lint.yml`, `.github/workflows/pull-request-title.yml`, `.github/workflows/codeql.yml`
- **Acceptance**: Each required check reports success on the PR head. The PR title check passes.
- **Verification**: STE row on the Markdown files of the record. Check TST-13.
- **Status**: open

### T-MERGE Squash merge after authorization

- **Requirements**: FR-009
- **Files**: The record files and the changelog fragment named under T-PR. This task adds no file.
- **Acceptance**: The orchestrator authorizes the merge. The merge uses `--match-head-commit`. The next Quality Gates run on the new main head succeeds before any other merge starts.
- **Verification**: Tests row, `python -m pytest tests/guardrails/test_process_folder_structure.py`, run on the new main head. Check TST-13.
- **Status**: open

## Requirement coverage

Each FR maps to at least one task and at least one check.

| Requirement | Tasks | Checks |
| - | - | - |
| FR-001 | T001 to T018 | TST-01 to TST-18 |
| FR-002 | T002, T003, T004, T016, T022, T023 | TST-02, TST-03, TST-04, TST-16 |
| FR-003 | T015, T019, T022 | TST-15, TST-20 |
| FR-004 | T004, T032 | TST-04, TST-25 |
| FR-005 | T004, T034 | TST-04, TST-25 |
| FR-006 | T008, T-PR | TST-08, TST-29 |
| FR-007 | T009, T018, T-LOCAL-GATES | TST-09, TST-19, TST-22 |
| FR-008 | T010, T027 | TST-10, TST-32 |
| FR-009 | T013, T026, T-REMOTE-CI, T-MERGE | TST-13, TST-31 |
| FR-010 | T011, T026 | TST-11, TST-31 |
| FR-011 | T007, T028 | TST-07 |
| FR-012 | T006, T014 | TST-06, TST-14 |
| FR-013 | T002, T023, T024, T038 | TST-02, TST-03, TST-15 |
| FR-014 | T025 | TST-33 |
| FR-015 | T019, T020, T032 to T035 | TST-23, TST-25 |
| FR-016 | T031 | TST-34 |
| FR-017 | T035 | TST-35 |
| FR-018 | T021, T022, T023 | TST-01 |
| FR-019 | T019, T029, T-LOCAL-GATES | TST-20 |
| FR-020 | T021, T022 | TST-01, TST-25 |
| FR-021 | T001, T036 | TST-25 |
| FR-022 | T036, T037, T-PR | TST-36 |
| FR-023 | T030 | TST-37 |
| FR-024 | T-PR | TST-30 |
| FR-025 | T009, T-LOCAL-GATES | TST-19, TST-26 |

## Task counts

- Total tasks: 42. Of these, 18 verify the handoff, 2 record decisions, 18 need action or owner input, and 4 are final tasks.
- Status counts: 13 verified-present, 7 partial, and 22 open. The partial tasks are T002, T003, T004, T007, T010, T014, and T015.
