# Tasks: Required Device Identity for Inventory Failure Records

**Input**: Design documents from `specs/numbered/0/0/0/4/2/0/0/3/2753-csv-device-id-validation/`.

**Prerequisites**: `plan.md`, `spec.md`, and the supporting documents in `design/`.

**Tests**: Add behavior and scan-guard tests before changing the comparator.

## Phase 1: Setup

- [x] T001 Confirm the selected comparator source and test paths are not reserved in `src/mist/resources/inventory/csv_comparator.py` and `tests/unit/test_csv_comparator.py`. (delivered: open pull request path check)
- [x] T002 Record the bounded requirements and design in `specs/numbered/0/0/0/4/2/0/0/3/2753-csv-device-id-validation/`. (delivered: `spec.md`, `plan.md`, and `design/`)

## Phase 2: Foundational

- [x] T003 Add scanner detection tests and a guard test in `tests/guardrails/test_issue_2753_csv_device_id_scan.py`. (delivered: `tests/guardrails/test_issue_2753_csv_device_id_scan.py`)
- [x] T004 Add missing, blank, non-string, and valid device ID behavior tests in `tests/unit/test_csv_comparator.py`. (delivered: `tests/unit/test_csv_comparator.py`)

## Phase 3: User Story 1 - Identify every failed device record (Priority: P1)

**Goal**: Refuse to write an inventory failure row without a valid device ID.

**Independent Test**: Run `python -m pytest tests/unit/test_csv_comparator.py tests/guardrails/test_issue_2753_csv_device_id_scan.py`.

### Tests

- [x] T005 Prove the scan detects the empty-string device ID default in `scripts/scan_2753.py`. (delivered: synthetic AST mutation test)
- [x] T006 Prove the guard reports its file count and fails on a controlled default reintroduction in `tests/guardrails/test_issue_2753_csv_device_id_scan.py`. (delivered: guard mutation test detects a reintroduced default)

### Implementation

- [x] T007 Add required device ID validation to both failure-record paths in `src/mist/resources/inventory/csv_comparator.py`. (delivered: shared validator used by both paths)
- [x] T008 Add the bounded scan command in `scripts/scan_2753.py`. (delivered: scan reports one file and zero defaults)
- [x] T009 Add the issue release note in `changelog.d/issue-2753-csv-device-id-validation.md`. (delivered: unique issue fragment)

## Phase 4: Polish and Cross-Cutting Concerns

- [x] T010 Run the focused tests and the controlled scan mutation described in `specs/numbered/0/0/0/4/2/0/0/3/2753-csv-device-id-validation/design/quickstart.md`. (delivered: 124 focused tests passed; the synthetic mutation was detected)
- [x] T011 Run applicable local gates and both test-quality ratchets without changing `.github/test-quality-baseline.json`. (delivered: 124 tests passed, module coverage is 93%, all applicable gates passed, and both ratchets reported zero new findings)
- [x] T012 Analyze `specs/numbered/0/0/0/4/2/0/0/3/2753-csv-device-id-validation/spec.md`, `plan.md`, and `tasks.md`. (delivered: manual review found complete requirement coverage and no conflicts; the prerequisite script could not run because `pwsh` is unavailable)

## Dependencies and Execution Order

- T003 and T004 define the expected failures before implementation.
- T005 and T006 depend on the scanner test boundary from T003.
- T007 and T008 depend on their failing tests.
- T009 depends on the user-visible behavior change.
- T010 and T011 depend on implementation completion.
- T012 depends on complete specification, plan, and task records.

## Parallel Opportunities

- T003 and T004 use different test files and can be prepared independently.
- Production validation and scan implementation affect different files after their tests exist.

## Implementation Strategy

Complete User Story 1 as one bounded increment. Keep the scan limited to the selected comparator defaults. Do not repair other candidates from the issue manifest.
