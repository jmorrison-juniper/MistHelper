# Tasks: SpecKit Task Audit Link and Legend Classification

**Input**: Numeric record `specs/numbered/0/0/1/2/2/3/0/3/4703-speckit-audit-markdown-links/`.

**Prerequisites**: plan.md (required), spec.md (required), design/research.md, design/data-model.md, design/quickstart.md, and design/contracts/speckit-audit-report.md.

**Format**: Each task names its requirement IDs, its exact paths, its acceptance statement, its verification command, and its status. An open task uses an empty box. A done task uses a box with an x. Status values are open, verified-present, partial, and absent. A done task cites its evidence with the `delivered:` label at the end of the line.

## Phase 1: Verify the current state

- [x] T001 [P] [FR-003] Verify the devtools pin on `main`. Path: requirements-dev.txt line 197. Acceptance: the pin names commit 2239e7bd. Verification: quickstart QS-02. Status: verified-present. delivered: design/research.md
- [x] T002 [P] [FR-001] [FR-002] Verify the repair in the pinned upstream source. Path: misthelper-devtools src/misthelper_devtools/speckit_task_audit.py lines 318 and 428. Acceptance: the exclusions and the line report exist at commit 2239e7bd. Verification: quickstart QS-06. Status: verified-present. delivered: design/research.md
- [x] T003 [P] [FR-001] Verify the audit output on `main`. Path: .github/workflows/ci.yml line 750. Acceptance: run 45774119357 reports zero malformed markers. Verification: quickstart QS-04. Status: verified-present. delivered: design/research.md

## Phase 2: Change the repository

- [ ] T004 [P] [FR-001] [FR-002] [FR-003] Append two regression tests to tests/guardrails/test_process_folder_structure.py after line 278. Acceptance: the negative test expects zero markers for the legend and link lines. The positive test expects one marker with the line tuple (3,). Verification: python -m pytest tests/guardrails/test_process_folder_structure.py -q. Status: open.
- [ ] T005 [P] [FR-002] Update documentation/quality-gates.md. Acceptance: one table row and one paragraph describe the audit job, its masked step, and its report lines. Verification: ste-linter --config .ste-linter.toml --min-score 80 documentation/quality-gates.md. Status: open.
- [ ] T006 [P] [FR-001] [FR-002] Add changelog.d/issue-4703-speckit-audit-markdown-links.md. Acceptance: one heading and one Fixed bullet name issue #4703. Verification: python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q. Status: open.
- [ ] T007 [P] Requirement: none, process record. Add this record folder at specs/numbered/0/0/1/2/2/3/0/3/4703-speckit-audit-markdown-links/. Acceptance: the folder holds the layout in plan.md. Verification: python -m pytest tests/guardrails/test_process_folder_structure.py -q. Status: open.

## Phase 3: Gate, publish, and merge

- [ ] T-LOCAL-GATES [FR-001] [FR-002] [FR-003] Run every applicable gate in the plan.md Gate Map. Depends on T004, T005, T006, and T007. Acceptance: each applicable gate exits with its expected result. Verification: the plan.md Gate Map. Status: open.
- [ ] T-PR [FR-001] [FR-002] [FR-003] Commit, push, and open the pull request. Depends on T-LOCAL-GATES. Acceptance: the branch is fix/4703-speckit-audit-markdown-links, the title uses Conventional Commits, and the body holds the line Closes #4703. Verification: gh pr view with the JSON field body, for the pull request that T-PR opens. Status: open.
- [ ] T-REMOTE-CI [FR-001] [FR-002] [FR-003] Watch remote CI on the pull request. Depends on T-PR. Acceptance: each required check passes, and the SpecKit task audit job reports zero malformed markers. Verification: gh pr checks with the --watch option, for the pull request that T-PR opens. Status: open.
- [ ] T-MERGE [FR-001] [FR-002] [FR-003] Enable auto-merge. Depends on T-REMOTE-CI and on orchestrator authorization. Acceptance: one squash commit reaches `main`, and issue #4703 closes. Verification: gh pr view with the JSON fields state and mergedAt. Status: open.

## Dependencies and Execution Order

- T001, T002, and T003 are complete. They need no further work.
- T004, T005, T006, and T007 touch different files. They can run in parallel.
- T-LOCAL-GATES waits for T004, T005, T006, and T007.
- T-PR waits for T-LOCAL-GATES.
- T-REMOTE-CI waits for T-PR.
- T-MERGE waits for T-REMOTE-CI and for orchestrator authorization.

## Notes

- The verification of T001 to T003 uses read-only GitHub commands. The local gate table covers local files only.
- The process tasks change no repository path. Each names its branch or its pull request.
- Warning: A commit pushed after the squash merge does not reach `main`. Open a new issue for later work instead.
- Caution: Do not add a `paths-ignore` filter to the Quality Gates workflow. A required check then never reports.
- Caution: Do not edit a sample line in a tasks file to silence the audit. The regression test uses its own copy of the text.
