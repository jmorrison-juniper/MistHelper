# Tasks: Laptop Branch Archive Verification

**Input**: Design documents in `specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/`

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, `design/contracts/archive-ref-verification.md`, and `design/quickstart.md`

**Tests**: The tests are the checks TC-01 to TC-15 in `design/quickstart.md`. Every check reads origin or the local refs. No check changes a branch.

**Ownership**: Do not modify `.specify/feature.json`, `README.md`, or `CHANGELOG.md`. Add each file by its explicit path.

**Environment**: Run each command from the repository root with the `.venv` of the main checkout active.

## Format: `[ID] [P?] [Requirements] Description`

- **[P]**: The task edits different files from the other [P] tasks of its phase.
- **Requirements**: The FR and SC IDs that the task serves.
- **Status** values: `open`, `verified-present`, `partial`, or `absent`. `absent` means the repository does not hold the file yet.
- Drafts outside the repository do not count as delivered.

## Phase 1: Verification Evidence

The tasks run in order, because they write to the same two files.

- **T001** [FR-001, FR-003, SC-001] Verify the 491 archive refs on origin and record each full tip. Files: `design/data-model.md`, `design/research.md`. Acceptance: The archive listing returns 491 names that match the issue. Each tip appears in the table. Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/design/data-model.md`. Evidence: TC-01, TC-03. Status: verified-present.
- **T002** [FR-002, SC-002] Verify the 6 rescue branches on origin and the parent count of each commit. Files: `design/research.md`. Acceptance: Six branches exist. Each commit has one parent. Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/design/research.md`. Evidence: TC-02. Status: verified-present.
- **T003** [FR-004, SC-003] Classify the counterpart state of each listed name. Files: `design/data-model.md`. Acceptance: The states total 489 none, 1 differs, 6 self, and 1 not applicable. Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/design/data-model.md`. Evidence: TC-04. Status: verified-present.
- **T004** [FR-005, FR-006, SC-003] Record the count split and the difference from the issue count of 497. Files: `analysis.md`, `design/research.md`. Acceptance: The record states 491 archive refs, 6 rescue branches, and the sum 497. Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/analysis.md`. Evidence: TC-05. Status: verified-present.
- **T005** [FR-007, FR-008, SC-005] Cross-check the local refs with read-only git commands. Files: `design/research.md`. Acceptance: The record states 330 local heads, 491 remote-tracking archive refs, and 10 archived names with local branches. No ref changes. Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/design/research.md`. Evidence: TC-06. Status: verified-present.
- **T006** [FR-009] Confirm that every command in the quickstart is a GET request or a local read. Files: `design/quickstart.md`. Acceptance: The command list holds no write command. Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/design/quickstart.md`. Evidence: TC-07. Status: verified-present.
- **T007** [FR-010, SC-004] List each unverified claim with its reason. Confirm that the remote check count equals the row count of the remote table. Files: `design/research.md`. Acceptance: The Unverified list gives each claim and reason. Both counts equal 39. Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/design/research.md`. Evidence: TC-10, TC-15. Status: verified-present.
- **T008** [FR-011] Record the deletion of archive refs as decision D-8, with the human decision marker. Files: `design/research.md`. Acceptance: D-8 carries the marker and names the rerun TC-01 to TC-05. Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/design/research.md`. Evidence: TC-11. Status: verified-present.
- **T009** [FR-012] Verify the route and the child counts of each directory on main. Files: `plan.md`, `design/research.md`. Acceptance: RC-23 to RC-26 match the route table in the plan. Verification: `python -m pytest tests/guardrails`. Evidence: TC-08. Status: verified-present.

## Phase 2: Authoring

- **T010** [P] [FR-001, FR-004, FR-010, FR-013, FR-015] Author `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` in the record folder. Files: `specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/spec.md`, `plan.md`, `tasks.md`, and `analysis.md`. Acceptance: Each file follows the headings of its template. Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/tasks.md`. Evidence: RC-18 to RC-20. Status: absent.
- **T011** [P] [FR-003, FR-012, FR-013] Author the five design files and the contract. Files: `design/research.md`, `design/data-model.md`, `design/quickstart.md`, `design/contracts/archive-ref-verification.md`, and `design/checklists/requirements.md`. Acceptance: The `design` folder holds five children. Each file has no placeholder. Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/design/quickstart.md`. Evidence: TC-09, TC-12. Status: absent.
- **T012** [P] [FR-014] Create the changelog fragment. Files: `changelog.d/issue-4868-laptop-branch-archive.md`. Text: a level-three heading `### Laptop branch archive verification record`, then one bullet `- **Added**: Specification record that verifies the laptop branch archive on origin. Issue #4868.` Acceptance: The name and shape follow `changelog.d/README.md`. Verification: `python -m pytest tests/guardrails`. Evidence: TC-14. Status: absent.
- **T013** [FR-012] Track the changelog debt in a separate issue. Files: none. Acceptance: The orchestrator opens an issue. It states the count of 335 direct children and the remediation. Verification: `python -m pytest tests/guardrails`. Evidence: RC-28. Status: open.
- **T014** [FR-011, SC-001] Rerun TC-01 to TC-05 before merge and before any cleanup decision. Files: `design/research.md`. Acceptance: Each count equals the recorded value, or the record gets an update. Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/design/research.md`. Evidence: TC-01 to TC-05. Status: open.

## Phase 3: Final Gates

- **T-LOCAL-GATES** [FR-013, FR-015, SC-006] Run the STE gate on each Markdown file of the change, then the guardrails and the advisory audit. Files: all files of the change. Acceptance: Each file scores 80 or above. The guardrails pass. The audit result is reported. Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/spec.md specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/plan.md specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/tasks.md specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/analysis.md specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/design/research.md specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/design/data-model.md specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/design/quickstart.md specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/design/contracts/archive-ref-verification.md specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/design/checklists/requirements.md changelog.d/issue-4868-laptop-branch-archive.md`. Evidence: TC-13, TC-14, RC-15, RC-17. Status: open.
- **T-PR** [FR-001 to FR-015] Commit with the subject `docs(specs): record laptop branch archive verification`. Push the branch `docs/4868-laptop-branch-archive`. Open a pull request whose body contains `Closes #4868`. Files: every file of the change. Acceptance: The title passes the Conventional Commits check. Verification: `python -m pytest tests/guardrails`. Status: open.
- **T-REMOTE-CI** [SC-004, SC-006] Watch the required checks of the pull request with `gh pr checks --watch`. Files: none. Acceptance: Each required check passes on the latest commit. Verification: `gh pr checks --watch`. Status: open.
- **T-MERGE** [FR-011] Enable auto-merge after remote CI passes and the orchestrator authorizes the merge. Files: none. Acceptance: The pull request carries the `auto-merge` label. No archive ref changes. Verification: `gh pr view --json autoMergeRequest`. Status: open.
