# Tasks: Traceback log redaction

**Input**: [Specification](spec.md), [plan](plan.md), and the documents under `design/`.

## Phase 1: Setup

- [x] T001 Verify current main, clean status, and complete PR ownership for the paths in `plan.md`. (delivered: design/checklists/requirements.md)
- [x] T002 Restore the locked environment without credential changes and reproduce the portal leak. (delivered: design/research.md)

## Phase 2: Foundational

- [x] T003 Complete the bounded specification and design in `spec.md` and `plan.md`. (delivered: spec.md)

## Phase 3: User Story 1 - Safe Failure Reports

- [x] T004 [P] [US1] Add direct and chained exception regressions in `tests/unit/test_logger_utils.py`. (delivered: tests/unit/test_logger_utils.py)
- [x] T005 [P] [US1] Add real portal exception regressions in `tests/unit/upgrade_portal/test_logging_contract.py`. (delivered: tests/unit/upgrade_portal/test_logging_contract.py)
- [x] T006 [US1] Prove the new tests fail against unchanged `src/foundation/support/utils/logger_utils.py`. (delivered: analysis.md)
- [x] T007 [US1] Sanitize rendered exception text and safe failure diagnostics in `src/foundation/support/utils/logger_utils.py`. (delivered: src/foundation/support/utils/logger_utils.py)

## Phase 4: User Story 2 - Several Handlers

- [x] T008 [US2] Cover cached text and handler order in `tests/unit/test_logger_utils.py` and `tests/unit/upgrade_portal/test_logging_contract.py`. (delivered: tests/unit/test_logger_utils.py, tests/unit/upgrade_portal/test_logging_contract.py)
- [x] T009 [US2] Confirm the cache protection in `src/foundation/support/utils/logger_utils.py` preserves safe text and exception objects. (delivered: src/foundation/support/utils/logger_utils.py)

## Phase 5: Final Verification

- [x] T010 Run focused tests and file gates. Record commands, results, and limitations in `analysis.md`. (delivered: analysis.md)
- [x] T011 Add `changelog.d/issue-4704-traceback-log-redaction.md` and analyze requirement coverage in `analysis.md`. (delivered: changelog.d/issue-4704-traceback-log-redaction.md, analysis.md)
- [x] T012 Commit the explicit file manifest with `Refs #4704`. Run the committed test-quality gate. Record evidence in `analysis.md`. (delivered: analysis.md, local commit f9189122e)

## Dependencies

T001 through T003 precede the regression work.
T004 and T005 can run independently because they own different files.
T006 requires both regression files.
T007 requires the failing proof.
T008 and T009 reuse the regression setup and follow T007.
T010 through T012 require both user stories.

## Independent Checks

US1 checks direct failures and linked failures through both handlers.
US2 checks complete output after an earlier handler has formatted the record.
Both stories are required for the local repair.

## Implementation Strategy

Write the failing regression cases first.
Repair the shared filter once.
Preserve the existing portal handler and callers.
Optional commit hooks remain deferred to the final local commit.
Publication remains held.

## Phase 6: Independent Findings

- [x] T013 [US1] Prove safe-chain corruption through the real handler in `tests/unit/upgrade_portal/test_logging_contract.py`. (delivered: tests/unit/upgrade_portal/test_logging_contract.py)
- [x] T014 [US1] Prove authorization value leakage and ordinary credential behavior in `tests/unit/test_logger_utils.py` and `tests/unit/upgrade_portal/test_logging_contract.py`. (delivered: tests/unit/test_logger_utils.py)
- [x] T015 [US1] Repair line-bounded credential matching and complete authorization values in `src/foundation/support/utils/logger_utils.py`. (delivered: src/foundation/support/utils/logger_utils.py)
- [x] T016 Add `changelog.d/issue-4705-authorization-log-redaction.md`, validate the repair, and record exact results in `analysis.md`. (delivered: changelog.d/issue-4705-authorization-log-redaction.md, analysis.md)
- [x] T017 Commit the follow-up locally with references to both issues and run the committed-difference test-quality gate. (delivered: local commit 0934e5b43, analysis.md)

T013 and T014 precede T015. T016 requires T015. T017 requires T016.

## Phase 7: Structured Authorization Values

- [x] T018 [US1] Reproduce Digest and AWS4 leaks in both existing test files. (delivered: tests/unit/test_logger_utils.py, tests/unit/upgrade_portal/test_logging_contract.py)
- [x] T019 [US1] Redact the complete header line in `src/foundation/support/utils/logger_utils.py`, without crossing CR or LF. (delivered: src/foundation/support/utils/logger_utils.py)
- [x] T020 Validate, update the unique #4705 changelog and `analysis.md`, and commit locally with both issue references. (delivered: local commit 219f18a60, analysis.md)

T018 precedes T019. T020 requires T019.

## Phase 8: Verification URL Extension

- [x] T021 Add dedicated synthetic URL regressions, including real portal output and earlier exception formatting. (delivered: tests/unit/utils/test_logger_verification_urls.py)
- [x] T022 Prove the URL cases fail, then extend only the owned logging source. (delivered: src/foundation/support/utils/logger_utils.py, analysis.md)
- [x] T023 Run focused gates, record limitations, and preserve the local integration handoff. (delivered: analysis.md, local commit 455b85e)

T021 precedes T022. T023 requires T022.
FR-015 maps to T021 and T022. FR-016 maps to T021 and T023.
FR-017 and FR-018 map to T021 and T023.

## Phase 9: URL Punctuation

- [x] T024 Prove leading and embedded punctuation leaks with synthetic values and the real SDK URI builder. (delivered: tests/unit/utils/test_logger_verification_urls.py)
- [x] T025 Use whitespace-only suffix boundaries in the owned filter. (delivered: src/foundation/support/utils/logger_utils.py)
- [ ] T026 Validate punctuation protection and record the restricted integration handoff.

T024 precedes T025. T026 requires T025. These tasks refine FR-015 and FR-016.
