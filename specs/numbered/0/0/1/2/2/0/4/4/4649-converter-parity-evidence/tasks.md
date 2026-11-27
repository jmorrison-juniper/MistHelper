# Tasks: Close Full-Parity Evidence Gaps with Approved Dispositions

**Input**: `spec.md`, `plan.md`, and the supporting files under `design/`.

**Prerequisites**: Parity T033 depends on parity T002 and T032 (research R04). This list changes Markdown only, plus one nested audit package. No task in this list is complete.

**Rules for this list**: Each task names exact repository paths and one verification command from the local gates table. Final tasks T-PR, T-REMOTE-CI, and T-MERGE use GitHub checks, because no local gate reads a pull request. Status values are `open`, `verified-present`, `partial`, or `absent`.

**Naming**: Task IDs T001 to T012 belong to this record. Parity tasks always carry the word "parity" before their ID.

## Format

- `[P]`: The task can run in parallel. It uses different files and shares no prerequisite.
- `FR-###`: The requirement IDs in `spec.md` that the task satisfies.
- `Depends on`: The tasks that must pass first.

## Phase 1: Prerequisite Evidence

- [ ] T001 [P] Verify gate G1 with a recorded legal decision for each reuse category.
  - Requirements: FR-004, FR-006
  - Depends on: None
  - Paths: `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md`
  - Acceptance: Gate G1 lists a decision ID, a UTC date, an owner, and the scope of each reuse category. Without these items, G1 stays open.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/evidence/test_register_audit.py`
  - Status: absent. Issue #4635 is OPEN. The legal box at line 186 of the parity research file is unchecked (R07).

- [ ] T002 [P] Verify gate G3 with a recorded handover for the shared portal files.
  - Requirements: FR-006
  - Depends on: None
  - Paths: `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/portal.md`, `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md`
  - Acceptance: Gate G3 names `web_portal/app.py`, `web_portal/templates/base.html`, the owner, and the date. Without these items, G3 stays open.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/evidence/test_register_audit.py`
  - Status: absent. The handover box at line 187 is unchecked (R07). Neither shared file mentions the converter (R41, R42).

- [ ] T003 [P] Verify gate G2 payload evidence for each candidate write.
  - Requirements: FR-003, FR-006
  - Depends on: None
  - Paths: `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md`
  - Acceptance: Each of the 22 operation IDs, the 21 candidates plus `deleteOrgServicePolicy`, has a schema, a payload fixture, and a scope decision.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/evidence/test_register_audit.py`
  - Status: partial. The 22 operation IDs and the SDK signatures exist (R55 to R77). Payload evidence is pending (R10, line 11).

- [ ] T004 [P] Verify the parity task statuses against main.
  - Requirements: FR-007
  - Depends on: None
  - Paths: `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md`, `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/analysis.md`
  - Acceptance: Each parity task from T001 to T033 has one status that matches the remote checks in `design/research.md`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/evidence/test_register_audit.py`
  - Status: partial. The status table in this record holds the baseline for 33 tasks. Zero tasks are verified-present.

## Phase 2: Audit Package

- [ ] T008 [P] Add the audit package with the class `EvidenceRegisterAuditor` and 13 test functions.
  - Requirements: FR-001 to FR-013
  - Depends on: None
  - Paths: add `tests/integration/web_portal/cisco_config_converter/evidence/__init__.py`, `tests/integration/web_portal/cisco_config_converter/evidence/register_audit.py`, and `tests/integration/web_portal/cisco_config_converter/evidence/test_register_audit.py`.
  - Acceptance: Each test fails on one seeded defect. Zero-row input fails. The audit prints each count it examined. The package holds three children.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/evidence/test_register_audit.py`
  - Status: absent.

## Phase 3: Register and Analysis Refresh

- [ ] T005 Refresh the 40-row register in the parity `design/research.md` file.
  - Requirements: FR-001, FR-002, FR-003, FR-005
  - Depends on: T001, T002, T003, T004, T008
  - Paths: `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md`
  - Acceptance: The table holds 40 rows with the columns in `design/contracts/evidence-register.md`. Each row has one disposition. Each remote check ID becomes a path, a blob SHA, and a line.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/evidence/test_register_audit.py`
  - Status: absent. This record holds the baseline table with all 40 rows open.

- [ ] T006 Refresh the parity `analysis.md` file with the defect list and the consistency review.
  - Requirements: FR-011
  - Depends on: T005
  - Paths: `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/analysis.md`
  - Acceptance: Each finding has an ID, a location, and a disposition. The file keeps each dated validation result with its revision.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/evidence/test_register_audit.py`
  - Status: partial. This record holds findings F-01 to F-14 in its `analysis.md` file. The parity analysis file is unchanged.

- [ ] T007 Record owner dispositions for each unsupported row and the visual acceptance.
  - Requirements: FR-004
  - Depends on: T001, T005
  - Paths: `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md`
  - Acceptance: Each unsupported-approved row cites an OD number, an approver, a UTC approval date, and the limit text. Only an owner writes these entries.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/evidence/test_register_audit.py`
  - Status: absent. Decision D-7 is a human decision.

- [ ] T009 Add the local link check to the audit package.
  - Requirements: FR-010
  - Depends on: T008
  - Paths: `tests/integration/web_portal/cisco_config_converter/evidence/register_audit.py`, `tests/integration/web_portal/cisco_config_converter/evidence/test_register_audit.py`
  - Acceptance: Each local Markdown link in the parity record and in this record resolves. A broken link fails the audit.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/evidence/test_register_audit.py`
  - Status: absent.

## Phase 4: Guide Gate and Completion

- [ ] T010 Run the STE gate on each refreshed Markdown file.
  - Requirements: FR-011, FR-012
  - Depends on: T006, T007, T009
  - Paths: the Markdown files of the parity record and of this record
  - Acceptance: Each file scores 80 or above. The output names each file that the gate read.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 <file>`
  - Status: open.

- [ ] T011 Write the independent converter guide only after documentation approval and gate G1.
  - Requirements: FR-013
  - Depends on: T001, T007
  - Paths: add `documentation/cisco-config-converter-guide.md`
  - Acceptance: The guide holds only independently written text. It copies no source document, screenshot, or asset. Each link resolves.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 documentation/cisco-config-converter-guide.md`
  - Status: absent. No documentation approval exists (Unverified item U7). Decision D-9 is a human decision.

- [ ] T012 Update the parity status line and the completion statement only when FR-008 passes.
  - Requirements: FR-008, FR-011
  - Depends on: T006, T007, T010, T011
  - Paths: `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md` (line 7), `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/analysis.md`
  - Acceptance: The status line changes only when the audit result is pass. Otherwise the parity record keeps its partial status.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/evidence/test_register_audit.py`
  - Status: open. The completion claim is refused today (R07, R09).

## Final Tasks

- [ ] T-LOCAL-GATES Run each local gate that applies to the changed files.
  - Requirements: FR-001 to FR-013
  - Depends on: None in this pull request
  - Paths: each Markdown file in this record folder
  - Acceptance: Record each exact result in the pull request body. Run the STE gate on each file. Run the structure guard once.
  - Applicable gates, one per line:
    - STE: `ste-linter --config .ste-linter.toml --min-score 80 <file>` for each Markdown file in this record folder.
    - Tests: `python -m pytest tests/guardrails/test_process_folder_structure.py`.
  - Not applicable, one reason per line:
    - Compile, lint, format, and types: no Python file changes.
    - Full tests and coverage: no Python file changes.
    - Test quality and complexity: no test file changes.
    - Security lint and dependency audit: no Python or dependency file changes.
    - Code quality, dead code, and docstrings: no Python file changes.
    - Menu reference and symbols: no menu or Python module changes.
    - Safe sweep: no menu changes.
    - Ops portal and ops platform: no change in those trees.
  - Verification: Each applicable command exits with the expected result.
  - Status: open.

- [ ] T-PR Commit, push, and open the pull request.
  - Requirements: FR-001 to FR-013
  - Depends on: T-LOCAL-GATES
  - Paths: branch `docs/4649-converter-parity-evidence`
  - Acceptance: The commit subject is `docs(spec): record converter parity evidence gate`. The pull request title uses the same form. The body contains `Closes #4649`. The body contains a line that begins with `Caution:`, and that line states that parity task T033 stays partial. The body lists each gate result.
  - Verification: `gh pr view <pr-number> -R jmorrison-juniper/MistHelper --json title,body`. This check is remote, because no local gate reads a pull request body.
  - Status: open.

- [ ] T-REMOTE-CI Watch each remote check until it finishes.
  - Requirements: FR-001 to FR-013
  - Depends on: T-PR
  - Paths: the pull request from T-PR
  - Acceptance: Each required check reports success. CodeQL reports success before the `auto-merge` label is added.
  - Verification: `gh pr checks <pr-number> -R jmorrison-juniper/MistHelper --watch`. This check is remote.
  - Status: open.

- [ ] T-MERGE Enable auto-merge after the orchestrator authorizes the merge.
  - Requirements: FR-001 to FR-013
  - Depends on: T-REMOTE-CI and orchestrator authorization
  - Paths: the pull request from T-PR
  - Acceptance: Add the `auto-merge` label only after T-REMOTE-CI passes. The merge is a squash merge. Remove the branch and the worktree after the merge.
  - Verification: `gh pr view <pr-number> -R jmorrison-juniper/MistHelper --json autoMergeRequest,state`. This check is remote.
  - Status: open.

## Dependencies and Execution Order

| Task | Depends on | Parallel group |
| --- | --- | --- |
| T001 | None | A |
| T002 | None | A |
| T003 | None | A |
| T004 | None | A |
| T008 | None | A |
| T005 | T001, T002, T003, T004, T008 | None |
| T006 | T005 | None |
| T007 | T001, T005 | B |
| T009 | T008 | B |
| T010 | T006, T007, T009 | None |
| T011 | T001, T007 | None |
| T012 | T006, T007, T010, T011 | None |
| T-LOCAL-GATES | None in this pull request | None |
| T-PR | T-LOCAL-GATES | None |
| T-REMOTE-CI | T-PR | None |
| T-MERGE | T-REMOTE-CI and orchestrator authorization | None |

Group A holds five tasks with no shared prerequisite. Group B holds two tasks that edit different files.

## Test Plan Summary

The audit package holds 13 test functions. Each function maps to one functional requirement.

| Test function | Requirement |
| --- | --- |
| `test_register_lists_each_comparison_row_once` | FR-001 |
| `test_each_row_has_one_allowed_disposition` | FR-002 |
| `test_accepted_row_cites_blob_line_and_check` | FR-003 |
| `test_unsupported_row_requires_owner_decision_and_limit` | FR-004 |
| `test_open_row_cites_remaining_task` | FR-005 |
| `test_gate_without_decision_stays_open` | FR-006 |
| `test_task_status_uses_four_values` | FR-007 |
| `test_completion_refused_while_row_or_gate_open` | FR-008 |
| `test_audit_fails_on_missing_input_or_zero_rows` | FR-009 |
| `test_broken_local_link_fails_audit` | FR-010 |
| `test_completion_phrase_refused_while_claim_refused` | FR-011 |
| `test_secret_like_value_fails_audit` | FR-012 |
| `test_converter_guide_absent_without_approval` | FR-013 |
