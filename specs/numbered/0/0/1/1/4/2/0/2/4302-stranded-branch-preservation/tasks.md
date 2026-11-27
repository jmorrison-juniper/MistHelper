# Tasks: Stranded Branch Preservation

**Input**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, and `design/contracts/branch-disposition-table.md`.

**Environment**: Set the GitHub account before each `gh` command. Use the two commands in `design/quickstart.md`.

**Rule**: Do not switch the working tree to a branch. Do not change a branch ref. Do not delete a branch.

## Format

- `[P]`: The task may run in parallel with other `[P]` tasks of its phase.
- `[FR-###]`: The requirements that the task serves.
- Each task names one verification ID from `design/quickstart.md`.
- Status is one of `open`, `verified-present`, `partial`, or `absent`.

## Batch Membership

The refs below use the `refs/heads/` prefix. Each name is an exact branch name.

- Hold H1 (human review): `fix/3222-confirm-details`, `jmorrison-juniper-fix-2863-identifier-defaults-batch-1`, `recovery/2863-handoff-20261004`.
- Hold H2 (owner reservation): `recovery/2711-handoff-20261004`, `recovery/3575-handoff-20261004`, `recovery/3700-handoff-20261004`, `recovery/2977-handoff-20261004`, `recovery/2747-handoff-20261004`, `jmorrison-jnpr-snmp-fallback-delivery`.
- Hold H3 (owner documentation review): `jmorrison-juniper-assessment-4026`, `recovery/2752-handoff-20261004`, `recovery/2861-handoff-20261004`.
- Batch B1 (11 refs): `fix/3158-wip-controls`, `fix/3168-structured-signals`, `fix/3183-status-fallback`, `fix/3506-site-lock-logs`, `fix/3292-isolate-retry-e2e-sites`, `jmorrison-juniper-startup-dependency-reassessment`, `jmorrison-juniper-issue-3416-lint-pattern`, `jmorrison-juniper-false-success-family-4028`, `jmorrison-jnpr-test-4035-menu-92-selection-result`, `jmorrison-juniper-issue-2746`, `jmorrison-juniper-coordinate-issue-work`.
- Batch B2 (23 refs): `recovery/3701-handoff-20261004`, `recovery/3213-handoff-20261004`, `recovery/3326-handoff-20261004`, `recovery/3329-handoff-20261004`, `recovery/3295-handoff-20261004`, `recovery/3728-handoff-20261004`, `recovery/3436-handoff-20261004`, `recovery/3699-handoff-20261004`, `recovery/3375-handoff-20261004`, `recovery/3158-handoff-20261004`, `recovery/3743-handoff-20261004`, `recovery/3491-handoff-20261004`, `recovery/3745-handoff-20261004`, `recovery/3749-handoff-20261004`, `recovery/3161-handoff-20261004`, `recovery/3388-handoff-20261004`, `recovery/3380-handoff-20261004`, `recovery/3761-handoff-20261004`, `recovery/3760-handoff-20261004`, `recovery/3769-handoff-20261004`, `recovery/2708-handoff-20261004`, `recovery/3818-handoff-20261004`, `recovery/3738-handoff-20261004`.
- Batch B3 (1 ref): `docs/3818-campaign-stop-20261004`.
- Group N (210 unkept new rows): not scheduled. The owner selects them under decision D-3.

## Phase 1: Verified Evidence

- [x] T001 [P] [FR-001, FR-013] Verify the 48 annotated rows and the 505 rows of report #4911. Paths: the 47 present refs above and `fix/3417-snmp-base-oid`, plus issue #4911. Acceptance: counts match `design/research.md`. Verification: TST-01, TST-02. Status: verified-present.
- [x] T002 [P] [FR-002] Verify blob classes for the 47 present annotated rows. Paths: the 47 refs and the `main` tree. Acceptance: each row count matches `design/research.md`. Verification: TST-05. Status: verified-present.
- [x] T003 [P] [FR-003] Verify PR-kept classification. Paths: PR head commits from `gh pr list`. Acceptance: no report row has a PR of the same name, and 248 rows are PR-kept. Verification: TST-02, TST-03. Status: verified-present.
- [x] T004 [P] [FR-004] Verify repository visibility and open-PR overlap. Paths: repository `jmorrison-juniper/MistHelper`. Acceptance: visibility is PUBLIC, and no open PR touches the record route. Verification: TST-04. Status: verified-present.
- [x] T005 [P] [FR-010] Verify the route and the ancestor child counts. Paths: `specs/numbered/0/0/1/1/4/2/0/2` (absent), `specs/numbered/0/0/1/1` (five children), `specs/numbered/0/0/1/1/4` (three children). Verification: TST-08, TST-09. Status: verified-present.
- [x] T006 [P] [FR-011] Verify the gate configuration. Paths: `.ste-linter.toml` and `.pre-commit-config.yaml`. Acceptance: the hooks `ste-linter` and `markdown-link-check` exist. Verification: TST-10. Status: verified-present.

## Phase 2: Gates

- [ ] T007 [FR-005] Record the owner authorization for each batch on #4302. Paths: comments on issue #4302. Acceptance: one comment per batch names the batch and its refs. Blocked by: decision D-3 (HUMAN-DECISION-REQUIRED). Verification: TST-14. Status: open.
- [ ] T008 [FR-005] Scan the 11 batch B1 heads. Paths: the B1 refs. Acceptance: each head has one recorded scan result, with its head commit. Blocked by: T007. Verification: TST-17. Status: open.
- [ ] T009 [FR-005] Scan the 23 batch B2 heads. Paths: the B2 refs. Acceptance: each head has one recorded scan result, with its head commit. Blocked by: T007. Verification: TST-17. Status: open.
- [ ] T010 [FR-005] Scan the batch B3 head, including `documentation/handoffs/issue-3818-campaign-stop-2026-10-04.md` on that head. Paths: `docs/3818-campaign-stop-20261004`. Acceptance: the scan result is recorded with the head commit. Blocked by: T007. Verification: TST-17. Status: open.
- [ ] T011 [FR-007] Record the human review of hold H1. Paths: the three H1 refs. Acceptance: the review result is recorded on #4302 (decision D-7). Blocked by: human review (HUMAN-DECISION-REQUIRED). Verification: TST-18. Status: open.
- [ ] T012 [FR-007] Record the owner review of documentation deltas for hold H3. Paths: the three H3 refs. Acceptance: the owner comment is recorded on #4302 (decision D-9). Verification: TST-18. Status: open.
- [ ] T013 [FR-007] Record the holder release for hold H2. Paths: the six H2 refs. Acceptance: each holder releases in writing, or the row stays on hold (decision D-8). Verification: TST-18. Status: open.

## Phase 3: Publication and Proof

- [ ] T014 [FR-006] Open draft PRs for batch B1. Paths: the 11 B1 refs. Acceptance: each PR is a draft, its head equals the recorded head, it has no auto-merge label, and its body contains `Refs #4302`. Blocked by: T007, T008. Verification: TST-15. Status: open.
- [ ] T015 [FR-006] Open draft PRs for batch B2. Paths: the 23 B2 refs. Acceptance: the same checks as T014 pass. Blocked by: T007, T009. Verification: TST-15. Status: open.
- [ ] T016 [FR-006] Open a draft PR for batch B3. Paths: `docs/3818-campaign-stop-20261004`. Acceptance: the same checks as T014 pass. Blocked by: T007, T010. Verification: TST-15. Status: open.
- [ ] T017 [FR-008] Check that every ref keeps its recorded head after each step. Paths: the 47 present annotated refs. Acceptance: each head equals the value in `design/research.md`. Verification: TST-16. Status: open.
- [ ] T018 [FR-009] Recount the report scope after each step. Paths: issue #4911 and the matching refs. Acceptance: the counts are written into the proof comment (T019). Verification: TST-02. Status: open.
- [ ] T019 [FR-015] Post a proof comment on #4302 after each batch. Paths: comments on issue #4302. Acceptance: the comment follows `design/contracts/branch-disposition-table.md`, and earlier comments stay unchanged. Verification: TST-24. Status: open.
- [ ] T020 [FR-016] Open a separate issue for the duplicate tracking-issue defect (decision D-11). Paths: `.github/workflows/stranded-branch-report.yml` on `main`, and the title search at line 156 of the shared workflow. Acceptance: the new issue number appears in the proof comment. Verification: TST-23 (five open issues before the fix). Status: open.
- [ ] T021 [FR-016] Owner closes the duplicate tracking issues `#4583`, `#4719`, `#4818`, and `#4911` after the T020 fix. Acceptance: exactly one open issue carries the report title. Blocked by: T020. Verification: TST-23. Status: open.
- [ ] T022 [FR-005] Owner selects batches from group N under decision D-3. Acceptance: the selection is recorded on #4302, and each selected batch repeats T008 and T014. Blocked by: owner decision (HUMAN-DECISION-REQUIRED). Verification: TST-14. Status: open.

## Phase 4: Record Delivery

- [ ] T-LOCAL-GATES [FR-010, FR-011, FR-013, FR-014] Run TST-08, TST-09, TST-10, TST-11, TST-12, TST-13, TST-20, and TST-21 on the 10 record files and the changelog fragment. Acceptance: each test passes, and the counts are recorded in the PR body. Status: open.
- [ ] T-PR [FR-012] Create branch `docs/4302-stranded-branch-preservation` from `main`. Commit the 10 record files and `changelog.d/issue-4302-stranded-branch-preservation.md`. Title: `docs(ci): add stranded branch preservation record`. The body contains `Refs #4302` and omits `Closes #4302` (decision D-10). Verification: TST-19. Status: open.
- [ ] T-REMOTE-CI [FR-012] Watch the PR checks until each one passes. Verification: `gh pr checks` with `--watch` on the PR number. Status: open.
- [ ] T-MERGE [FR-015] Add the `auto-merge` label only after the checks pass and the orchestrator authorizes the merge. Squash-merge the PR, and keep #4302 open. Verification: TST-22. Status: open.
