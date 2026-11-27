# Tasks: Stranded branch preservation

**Input**: Design documents in `specs/numbered/0/0/1/2/4/1/2/1/4911-stranded-branch-preservation/`

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, and `design/contracts/preservation-tags.md`

**Tests**: This change adds no test function. Verification uses the Tests and STE rows of the Local gates table, and the ref checks in `design/quickstart.md`.

**Verification gap**: Tasks T004 to T008 change no repository file. No row of the Local gates table covers refs. Those tasks use the `git` and `gh` commands in `design/quickstart.md`. `analysis.md` records this gap.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel with other [P] tasks of its phase, because it edits a different file.
- **[Story]**: The user story that the task serves.
- **Status**: `open`, `verified-present`, `partial`, or `absent`. A status describes the state on 2026-11-26.

## Phase 1: Confirm the input (read only)

- [ ] T001 [US1] Confirm that issue 4911 names 505 rows with 505 unique names. Requirements: FR-001. Files: none. Acceptance: the row count is 505. Verification: quickstart Step 1. Status: verified-present.
- [ ] T002 [P] [US1] Confirm that all 505 named branches exist on origin. Requirements: FR-001, FR-005. Files: none. Acceptance: 505 of 505 names have a tip. Verification: quickstart Step 2. Status: verified-present.
- [ ] T003 [P] [US1] Classify each tip as held or not held by a PR head commit. Requirements: FR-001. Files: none. Acceptance: the counts are 248 held and 257 not held. Verification: quickstart Step 3. Status: verified-present.
- [ ] T004 [US1] Confirm that all 505 tag names pass the ref format check and that no preservation tag exists on origin. Requirements: FR-004. Files: none. Acceptance: 0 invalid names and 0 existing tags. Verification: quickstart Step 4. Status: verified-present.

## Phase 2: Preserve the named branches (ref writes only)

- [ ] T005 [US1] Push the preservation tags for the first five named rows as a pilot. Requirements: FR-002, FR-003, FR-006. Files: none. Acceptance: five tags exist and each points to its recorded tip. Verification: quickstart Step 5 and Step 6. Status: absent.
- [ ] T006 [US1] Confirm that the pilot tags start no workflow run. Requirements: FR-008. Files: none. Acceptance: the workflow list has no run with a `preserve/` head branch. Verification: quickstart Step 7. Status: absent.
- [ ] T007 [US1] Push the other 500 preservation tags in batches of 50. Requirements: FR-002, FR-005, FR-006, FR-007. Files: none. Acceptance: each batch exits with code 0, or the procedure stops at the failed batch. Verification: quickstart Step 8. Status: absent.
- [ ] T008 [US1] Verify all 505 tags and write the ledger to a tracking issue comment. Requirements: FR-007. Files: none. Acceptance: 505 of 505 tags point to the recorded tips. Verification: quickstart Step 9. Status: absent.

## Phase 3: Document and record the change (repository files)

- [ ] T009 [P] [US2] Update the Branch cleanup section of `documentation/contributing.md`. Requirements: FR-009, FR-010. Files: `documentation/contributing.md`. Acceptance: the section names the preservation tag, keeps the deletion warning, and drops the claim that a pull request is the only durable copy. Verification: quickstart Step 10, which runs the STE gate and the Markdown link guard. Status: absent.
- [ ] T010 [P] [US2] Add the changelog fragment `changelog.d/issue-4911-stranded-branch-preservation.md`. Requirements: FR-013. Files: `changelog.d/issue-4911-stranded-branch-preservation.md`. Acceptance: the file has one heading and one Changed bullet that names issue 4911. Verification: quickstart Step 10, which runs the changelog fragment guard. Status: absent.
- [ ] T011 [P] [US2] Copy the draft folder to `specs/numbered/0/0/1/2/4/1/2/1/4911-stranded-branch-preservation/`. Requirements: FR-011, FR-016. Files: the ten record files under the route folder. Acceptance: the repository folder holds the same files as the draft. Verification: quickstart Step 11. Status: partial. The draft exists in the session folder, and the repository copy is not created yet.

## Phase 4: Track the follow-up work (GitHub writes)

- [ ] T012 [US3] Keep issue 4911 open. Close the four duplicate tracking issues 4302, 4583, 4719, and 4818 with a link to issue 4911. Requirements: FR-015. Files: none. Acceptance: one open issue has the report title. Verification: quickstart Step 12. Status: absent.
- [ ] T013 [US3] File the upstream issue in `jmorrison-juniper/misthelper-devtools`. The issue asks for two rules. A tip that equals a PR head commit is held. A tip with a `preserve/` tag at the same commit is held. Requirements: FR-014. Files: none. Acceptance: the issue link appears in issue 4911. Verification: the issue URL in the tracking issue. Status: absent.
- [ ] T014 [US3] File the follow-up issue for branch deletion. The issue requires the verified preservation tag before each deletion. Requirements: FR-012. Files: none. Acceptance: the issue link appears in issue 4911. Verification: the issue URL in the tracking issue. Status: absent.
- [ ] T015 [US3] File the remediation issue for the folder debt. The issue names 335 children in `changelog.d` and 813 direct children in `specs`. Requirements: FR-017. Files: none. Acceptance: the issue link appears in issue 4911. Verification: the issue URL in the tracking issue. Status: absent.

## Final tasks

- [ ] T-LOCAL-GATES Run the STE gate on each changed Markdown file, and run the two guard tests. Requirements: SC-003. Files: `documentation/contributing.md`, `changelog.d/issue-4911-stranded-branch-preservation.md`, and the ten record files. Acceptance: each file scores 80 or above, and both guard test modules pass. Verification: quickstart Step 10. Status: absent.
- [ ] T-PR Commit the change with a Conventional Commits subject. Push `chore/4911-stranded-branch-preservation`. Open a pull request whose body contains `Refs #4911`. Change the body to `Closes #4911` only after the report names no row. Requirements: FR-011. Files: the files of T009 to T011. Acceptance: the pull request title passes the title guard, and the body holds the closing keyword that the report state allows. Verification: `gh pr view <number> --json title,body`. Status: absent.
- [ ] T-REMOTE-CI Watch the CI run of the pull request. Requirements: SC-003. Files: none. Acceptance: each required check passes. Verification: `gh pr checks <number> --watch`. Status: absent.
- [ ] T-MERGE Enable auto-merge after the remote CI passes and the orchestrator authorizes the merge. Requirements: FR-011. Files: none. Acceptance: the pull request merges with one squash commit. Verification: `gh pr view <number> --json state,mergedAt`. Status: absent.
