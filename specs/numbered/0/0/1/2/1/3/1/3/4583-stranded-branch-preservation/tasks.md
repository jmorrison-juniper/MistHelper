# Tasks: Stranded Branch Preservation

**Input**: Numeric record at `specs/numbered/0/0/1/2/1/3/1/3/4583-stranded-branch-preservation/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, `design/quickstart.md`, and `design/contracts/preservation-pull-request.md`.

**Format**: `- [ ]` open, `- [x]` verified. Each line names requirement IDs, paths, acceptance, verification, and status. No task carries `[P]`, because each write changes shared GitHub state. Tasks run in the order given. Tasks that change no repository file verify with the checks in `design/quickstart.md`.

**Status values**: `open`, `verified-present`, `partial`, or `absent`.

## Phase 1: Evidence

**Purpose**: Establish the facts that the record depends on. These tasks finished before this record was written.

- [x] T001 [FR-001] Read issue #4583 body, labels, and comments. Paths: none. Acceptance: `design/research.md` section "Branch Evidence for the Issue Body" lists the 52 body names. Verify: `gh issue view 4583 -R jmorrison-juniper/MistHelper --json body,labels,comments`. Status: verified-present.
- [x] T002 [FR-016] Identify the five open report issues that share the title. Paths: `design/data-model.md` section "ReportIssue". Acceptance: five open issues are listed. Verify: V-15 command in `design/quickstart.md`. Status: verified-present.
- [x] T003 [FR-002] Read the report rule at commit 79a5e45 in the misthelper-devtools repository. Paths: `design/research.md` rows R36 to R40. Acceptance: each rule row cites one line. Verify: `gh api repos/jmorrison-juniper/misthelper-devtools/contents/src/misthelper_devtools/stranded_branch_report.py?ref=79a5e45970e876f1656d69520d9635cea1aa25ef`. Status: verified-present.
- [x] T004 [FR-001, FR-003] Emulate the report rule over 597 branches. Paths: `design/data-model.md` section "Snapshot Counts". Acceptance: 543 in scope, 441 ready, and 102 held. Verify: Q-2 in `design/quickstart.md`, check V-01. Status: verified-present.
- [x] T005 [FR-017] Verify the 54 remote claims on main, on the sibling repository, and on pull request heads. Paths: `design/research.md` section "Remote Verification". Acceptance: 54 rows exist, and each row has a result. Verify: V-18. Status: verified-present.
- [x] T006 [FR-015] Confirm that no legacy record and no route folder exist. Paths: `design/research.md` rows R32 and R33. Acceptance: both claims show `absent`. Verify: `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`. Status: verified-present.

## Phase 2: Record Placement

- [ ] T007 [FR-015, FR-017] Place the ten record files in the route folder on branch `chore/4583-stranded-branch-preservation`. Paths: `specs/numbered/0/0/1/2/1/3/1/3/4583-stranded-branch-preservation/spec.md`, `plan.md`, `tasks.md`, `analysis.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, `design/contracts/preservation-pull-request.md`, `design/checklists/requirements.md`, and `design/checklists/safety.md`. Acceptance: no other path changes. Verify: V-12 guard tests after the placement. Status: open.

## Phase 3: Scope and Preservation

- [ ] T008 [FR-001, FR-002, FR-011, FR-012] Run Q-2 and keep the work order before the first write. Paths: none. Acceptance: the output lists the in-scope rows, and the counts match the snapshot or a documented later count. Verify: V-01. Status: open.
- [ ] T009 [FR-003] Run Q-1 and confirm each open pull request and the files it changes. Paths: none. Acceptance: the lanes in the work order match the open pull requests. Verify: V-02. Status: open.
- [ ] T010 [FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010] Preserve ready batch W01, the first 50 ready rows. Paths: none. Acceptance: each row shows `CLOSED`, a null `mergedAt`, the snapshot head SHA, and an existing branch. Verify: V-03, V-04, V-05, V-06, V-07, and V-08 for each row. Status: open.
- [ ] T011 [FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010] Preserve ready batch W02, the next 50 ready rows. Paths: none. Acceptance: same as T010. Verify: same as T010. Status: open.
- [ ] T012 [FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010] Preserve ready batch W03, the next 50 ready rows. Paths: none. Acceptance: same as T010. Verify: same as T010. Status: open.
- [ ] T013 [FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010] Preserve ready batch W04, the next 50 ready rows. Paths: none. Acceptance: same as T010. Verify: same as T010. Status: open.
- [ ] T014 [FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010] Preserve ready batch W05, the next 50 ready rows. Paths: none. Acceptance: same as T010. Verify: same as T010. Status: open.
- [ ] T015 [FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010] Preserve ready batch W06, the next 50 ready rows. Paths: none. Acceptance: same as T010. Verify: same as T010. Status: open.
- [ ] T016 [FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010] Preserve ready batch W07, the next 50 ready rows. Paths: none. Acceptance: same as T010. Verify: same as T010. Status: open.
- [ ] T017 [FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010] Preserve ready batch W08, the next 50 ready rows. Paths: none. Acceptance: same as T010. Verify: same as T010. Status: open.
- [ ] T018 [FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010] Preserve ready batch W09, the remaining ready rows. Paths: none. Acceptance: same as T010, and no ready row remains. Verify: same as T010. Status: open.
- [ ] T019 [FR-003, FR-013] Release check, then preserve held group H-4813 (12 rows held by #4813). Paths: none. Acceptance: #4813 has state `CLOSED` or `MERGED` before the group runs. Verify: V-09, then the checks of T010 for each row. Status: open.
- [ ] T020 [FR-003, FR-013] Release check, then preserve held group H-4886 (3 rows held by #4886). Paths: none. Acceptance: #4886 has state `CLOSED` or `MERGED` before the group runs. Verify: V-09, then the checks of T010 for each row. Status: open.
- [ ] T021 [FR-003, FR-013] Release check, then preserve held group H-4887 (4 rows held by #4887). Paths: none. Acceptance: #4887 has state `CLOSED` or `MERGED` before the group runs. Verify: V-09, then the checks of T010 for each row. Status: open.
- [ ] T022 [FR-003, FR-013] Release check, then preserve held group H-4888 (21 rows held by #4888). Paths: none. Acceptance: #4888 has state `CLOSED` or `MERGED` before the group runs. Verify: V-09, then the checks of T010 for each row. Status: open.
- [ ] T023 [FR-003, FR-013] Release check, then preserve held group H-4208 (62 rows held by #4208) in batches of 50. Paths: none. Acceptance: #4208 has state `CLOSED` or `MERGED` before the group runs. Verify: V-09, then the checks of T010 for each row. Status: open.

## Phase 4: Closure

- [ ] T024 [FR-012, FR-014] Run Q-5 after the last batch. Paths: none. Acceptance: `in_scope=0`. If a row remains, return to the batch task that covers it. Verify: V-11. Status: open.
- [ ] T025 [FR-010] Review the execution log for each stop and each backoff. Paths: none. Acceptance: each event has one entry. Verify: V-16. Status: open.
- [ ] T026 [FR-016] File a separate issue for the duplicate report defect. Paths: none. Acceptance: the issue title is `CI: Stranded Branch Report -- title search opens duplicate report issues`. The body names #4302, #4583, #4719, #4818, #4911, and rows R41 to R43. Verify: V-15 before and after the defect fix. Status: open.
- [ ] T027 [FR-018] Post the summary comment on issue #4583. Paths: none. Acceptance: the summary has 2500 characters or fewer, and it names the record folder. Verify: V-14. Status: open.

## Final Tasks

- [ ] T-LOCAL-GATES [FR-015, FR-017, FR-018] Run the local gates on the ten record files. Paths: the ten record files listed in T007. Acceptance: Q-4 passes. Q-6 scores each file at 80 or above. Q-7 prints no output. Q-8 counts five or fewer children. V-18 and V-19 pass. Verify: Q-4 in `design/quickstart.md`. Status: open.
- [ ] T-PR [FR-014, FR-015] Commit the record, push `chore/4583-stranded-branch-preservation`, and open the pull request. Paths: the ten record files listed in T007. Acceptance: the commit subject is `docs(specs): add stranded branch preservation record`, the body contains `Closes #4583`, and V-17 passes. Verify: `gh pr view <number> --repo jmorrison-juniper/MistHelper --json files,title,body`. Status: open.
- [ ] T-REMOTE-CI [FR-014] Watch the pull request checks until every required check passes. Paths: none. Acceptance: each required check reports success. Verify: `gh pr checks <number> --repo jmorrison-juniper/MistHelper --watch`. Status: open.
- [ ] T-MERGE [FR-014] Enable auto-merge after T024 and T-REMOTE-CI pass, and after the coordinating agent authorizes the merge. Paths: none. Acceptance: the pull request merges by squash, and issue #4583 closes only after V-11 passes. Verify: V-11 and `gh pr view <number> --repo jmorrison-juniper/MistHelper --json state,mergedAt`. Status: open.

## Dependencies and Execution Order

- T001 to T006 are complete. T007 depends on them.
- T008 depends on T001 to T006. T009 depends on T008.
- T010 to T018 run in order, after T009. Each ready batch waits for the batch before it.
- T019 to T023 run after T018. Each held group waits for its release check.
- T024 depends on T010 to T023. T025 to T027 depend on T024.
- T-LOCAL-GATES depends on T007 and T024. T-PR depends on T-LOCAL-GATES. T-REMOTE-CI depends on T-PR. T-MERGE depends on T-REMOTE-CI and T024.

## Coverage Note

Every requirement from FR-001 to FR-018 maps to at least one task. Each mapping appears in `analysis.md` section "Coverage Summary".
