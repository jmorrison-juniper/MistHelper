# Tasks: License export failure status

## Phase 1: Setup

- [x] T001 Verify the base, reservation, and live ownership for `src/operations/exporting/export/org_admin_exporter.py`.
- [x] T002 Record scope and assumptions in `spec.md` and `plan.md` in this feature directory.

## Phase 2: Foundational safety

- [x] T003 Add socket and DNS rejection fixtures in `tests/unit/export/test_issue_4714_org_licenses_status.py`.

## Phase 3: User Story 1 - Request failures

**Goal**: Reject failed or unverified initial responses before consuming their bodies.
**Independent test**: Both endpoint branches reject 4xx, 5xx, missing, and malformed statuses without writer calls.

- [x] T004 [US1] Add initial-status regressions in `tests/unit/export/test_issue_4714_org_licenses_status.py`.
- [x] T005 [US1] Record regression failures against original `src/operations/exporting/export/org_admin_exporter.py` in session evidence.
- [x] T006 [US1] Validate status before data or pagination in `src/operations/exporting/export/org_admin_exporter.py`.

## Phase 4: User Story 2 - Write outcomes

**Goal**: Report the actual result without false file creation or completion messages.
**Independent test**: Valid empty, successful records, rejected writers, exceptions, and cancellation preserve the documented contract.

- [x] T007 [US2] Add write-result and preserved-behavior tests in `tests/unit/export/test_issue_4714_org_licenses_status.py`.
- [x] T008 [US2] Remove recovery writes and report rejection in `src/operations/exporting/export/org_admin_exporter.py`.
- [x] T009 [US2] Update obsolete empty-write expectations and response doubles in `tests/unit/export/test_org_admin_exporter.py`.

## Phase 5: Validation and local delivery

- [x] T010 Add `changelog.d/issue-4714-license-export-failure-status.md`.
- [x] T011 Run focused existing tests and applicable local gates for the three reserved Python files.
- [x] T012 Record specification consistency and limitations in `analysis.md` in this feature directory.
- [x] T013 Commit only reserved files locally with `Refs #4714` and the required co-author trailer.
- [x] T014 Export committed files, manifest, hashes, patch, commands, and results into the session evidence directory.

## Dependencies

T001 and T002 precede T003. T003 precedes T004 and T007.
T004 and T007 precede the original-source proof T005.
T005 precedes T006, T008, and T009.
T006, T008, T009, and T010 precede T011.
T011 precedes T012 and T013. T013 precedes T014.

## Parallel opportunities

The two regression groups can be designed independently after the safety fixture exists.
Source edits remain serial because both stories use the same exporter.
Read-only gates can run independently. Use no additional agents for this focused repair.

## Implementation strategy

Complete request failure safety first, then write reporting. Deliver both together as one unpublished local candidate.
Every task follows the checkbox, task identifier, optional story label, and concrete file path format.
