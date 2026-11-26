# Tasks: Preserve CSV Carriage Returns

## Phase 1: Setup

- [x] T001 Resolve the managed issue path in `specs/numbered/0/0/1/2/3/1/0/1/4776-csv-carriage-returns/spec.md`. (delivered: specs/numbered/0/0/1/2/3/1/0/1/4776-csv-carriage-returns/spec.md)

## Phase 2: Foundational

- [x] T002 Confirm ownership of `src/foundation/models/data/data_processing_utils.py` and `src/operations/exporting/export/data_exporter.py`. (delivered: design/research.md)

## Phase 3: User Story 1 - Preserve exported text

**Goal**: Preserve raw carriage returns and show each return in CSV output.
**Independent Test**: Export synthetic records and read the cells. Compare the source and non-CSV data.

- [x] T003 [P] [US1] Test CR, CRLF, LF, and scalar values in `tests/unit/config/foundation/models/dataproc/test_data_processing_utils.py`. (delivered: tests/unit/config/foundation/models/dataproc/test_data_processing_utils.py)
- [x] T004 [P] [US1] Test CSV cells, input preservation, and non-CSV dispatch in `tests/unit/export/test_data_exporter.py`. (delivered: tests/unit/export/test_data_exporter.py)
- [x] T005 [US1] Preserve carriage returns in `src/foundation/models/data/data_processing_utils.py`. (delivered: src/foundation/models/data/data_processing_utils.py)
- [x] T006 [US1] Escape carriage returns only on copied CSV records in `src/operations/exporting/export/data_exporter.py`. (delivered: src/operations/exporting/export/data_exporter.py)
- [x] T007 [US1] Verify raw carriage returns in SQLite using `tests/unit/db/sle_window_summary/test_backend_preservation.py`. (delivered: tests/unit/db/sle_window_summary/test_backend_preservation.py)
- [x] T008 [US1] Update dispatch expectations in `tests/unit/export/test_endpoint_family_exporter.py`. (delivered: tests/unit/export/test_endpoint_family_exporter.py)

## Phase 4: Polish

- [x] T009 Add the issue release fragment in `changelog.d/issue-4776-csv-carriage-returns.md`. (delivered: changelog.d/issue-4776-csv-carriage-returns.md)
- [x] T010 Run focused tests and applicable checks for `src/operations/exporting/export/data_exporter.py`. (delivered: tests/unit/export/test_data_exporter.py)
- [x] T011 Run an isolated container smoke as described in `design/quickstart.md`. (delivered: design/quickstart.md)
- [ ] T012 Run a staging smoke when an authorized credential source and staging organization are verified in `design/quickstart.md`. Neither is available in this worktree.

## Dependencies and Execution Order

T002 precedes source and test edits. T003 and T004 can run in parallel.
T005 through T008 follow the tests. T009 through T012 follow implementation.
User Story 1 is the complete minimum delivery.
