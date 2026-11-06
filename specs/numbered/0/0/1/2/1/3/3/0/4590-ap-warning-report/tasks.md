# Tasks: AP warning report

**Input**: [spec.md](spec.md), [plan.md](plan.md), and the documents under `design/`.

## Phase 1: Setup

- [x] T001 Confirm SDK evidence and isolated paths in design/research.md. (delivered: design/research.md)
- [x] T002 Define report identity and validation rules in design/data-model.md. (delivered: design/data-model.md)

## Phase 2: Foundation

- [x] T003 Add the isolated package at src/operations/exporting/ap_warning_report/__init__.py. (delivered: src/operations/exporting/ap_warning_report/__init__.py)
- [x] T004 Implement validated SDK pagination in src/operations/exporting/ap_warning_report/client.py. (delivered: src/operations/exporting/ap_warning_report/client.py)
- [x] T016 Add the independent natural key in src/foundation/support/refactors/endpoint_primary_key_strategies.py and verify tests/integration/ap_warning_report/test_sqlite.py. (delivered: tests/integration/ap_warning_report/test_sqlite.py)

## Phase 3: User Story 1 - Find AP trouble codes

**Independent test**: Match connected and disconnected error APs while excluding APs without nonzero codes.

- [x] T005 [US1] Test filtering, MAC joins, empty evidence, and assignment in tests/unit/ap_warning_report/test_rows.py. (delivered: tests/unit/ap_warning_report/test_rows.py)
- [x] T006 [US1] Build inventory-led rows in src/operations/exporting/ap_warning_report/rows.py. (delivered: src/operations/exporting/ap_warning_report/rows.py)
- [x] T007 [US1] Add the export callable in src/operations/exporting/ap_warning_report/operation.py. (delivered: src/operations/exporting/ap_warning_report/operation.py)

## Phase 4: User Story 3 - Recognize incomplete reads

**Independent test**: Fail any required source or later page and confirm zero output writes.

- [x] T008 [P] [US3] Test HTTP 4xx, HTTP 5xx, malformed pages, and missing pages in tests/unit/ap_warning_report/test_client.py. (delivered: tests/unit/ap_warning_report/test_client.py)
- [x] T009 [US3] Test canceled organization selection and output failures in tests/unit/ap_warning_report/test_operation.py. (delivered: tests/unit/ap_warning_report/test_operation.py)
- [x] T010 [US3] Verify real CSV persistence with mocked SDK responses in tests/integration/ap_warning_report/test_export.py. (delivered: tests/integration/ap_warning_report/test_export.py)

## Phase 5: User Story 2 - Understand each code

**Independent test**: Resolve zero-padded known codes and preserve unknown codes without invented definitions.

- [x] T011 [P] [US2] Test code normalization and definition validation in tests/unit/ap_warning_report/test_codes.py. (delivered: tests/unit/ap_warning_report/test_codes.py)
- [x] T012 [US2] Implement definitions and UTC observation times in src/operations/exporting/ap_warning_report/codes.py. (delivered: src/operations/exporting/ap_warning_report/codes.py)

## Phase 6: Validation and preservation

- [x] T013 Run the applicable isolated gates from design/quickstart.md and record evidence in analysis.md. (delivered: analysis.md)
- [x] T014 Add the unique fragment at changelog.d/issue-4590-ap-warning-report.md. (delivered: changelog.d/issue-4590-ap-warning-report.md)
- [x] T015 Commit only feature-owned files and update the existing session automation. (delivered: src/operations/exporting/ap_warning_report/operation.py)

## Phase 7: Deferred menu integration

The user requires pull request #4208 to merge before the shared documentation changes.
Keep these tasks unchecked until that condition holds.

- [ ] T017 Register the next unused final number in MistHelper.py and src/foundation/support/utils/operation_registry.py.
- [ ] T018 Update README.md and .github/copilot-instructions.md, then regenerate documentation/menu_reference.md and the API map.
- [ ] T019 Test the final menu callable and portal visibility in tests/guardrails and tests/e2e.
- [ ] T020 Run final integration gates and record the results in analysis.md.

## Dependencies and execution order

T001 and T002 precede T003 and T004.
T005 through T012 depend on the foundation.
T006 and T012 precede T007.
T010 requires the completed client, row builder, and export callable.
T013 follows all isolated implementation and tests.
T015 follows T013 and T014.
T016 requires a separate ownership check but does not require the merge.
T017 through T020 require the merge of pull request #4208.

## Parallel examples

The row, client, and dictionary tests use separate files and can be authored independently.
The output integration test requires all report components.

## Implementation strategy

Deliver the report package and mocked tests first.
Preserve the verified independent work without registering an incomplete menu.
After the ownership blocker ends, complete the menu and documentation as one integration change.
