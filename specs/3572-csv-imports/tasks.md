# Tasks: CSV imports for PSKs, user MACs, and assets

**Input**: `specs/3572-csv-imports/spec.md`, `plan.md`, `research.md`, and `data-model.md`

## Phase 1 - Package foundations

- [x] T001 Create `src/inventory/csv_imports/__init__.py` with the public operation export.
- [x] T002 Create `src/inventory/csv_imports/model.py` with import definitions, CSV parsing, validation, preview masking, confirmation parsing, and result-row helpers.
- [x] T003 Create `src/inventory/csv_imports/client.py` with a `CsvImportClient` class that calls the five SDK `*File` functions.
- [x] T004 Create `src/inventory/csv_imports/operation.py` with `CsvImportOperation.run()` and dependency seams for tests.

## Phase 2 - Tests

- [x] T005 Create `tests/unit/inventory/csv_imports/__init__.py`.
- [x] T006 Add model tests for missing required columns, preview masking, confirmation parsing, and result rows.
- [x] T007 Add one client contract test for each multipart import type.
- [x] T008 Add operation tests that prove dry run and wrong confirmation send no request, and that `CsvImportLog.csv` is written.
- [x] T009 Add a log-capture test that proves a PSK passphrase never appears in a log line.

## Phase 3 - Documentation and wiring

- [x] T010 Create `specs/3572-csv-imports/wiring.md` with every section required by the fleet contract.
- [x] T011 Mark the `MistHelper.py` registration, `OperationRegistry` entry, primary key strategy, README, generated menu reference, and category table changes as deferred to the integration pull request.
- [x] T012 Create `changelog.d/issue-3572-csv-imports.md` with one `### Added` heading and one issue-named bullet.
- [x] T013 Create `specs/3572-csv-imports/pr-body.md` for the draft pull request.

## Phase 4 - Validation and analysis

- [ ] T014 Run py_compile, ruff, black, mypy, pydocstyle, pytest, vulture, and interrogate on the owned package and tests.
- [ ] T015 Run SpecKit analysis, repair findings, and commit the repair.

## Deferred integration tasks

- [ ] D001 Register menu 292 in `MistHelper.py`. Deferred because the fleet contract forbids edits to `MistHelper.py`.
- [ ] D002 Add menu 292 to `src/utils/operation_registry.py` as `destructive`. Deferred because the fleet contract forbids edits to `operation_registry.py`.
- [ ] D003 Add generated menu references and README operation count updates. Deferred because the fleet contract forbids these files.
- [ ] D004 Add any endpoint primary key strategy required by the integration pull request. Deferred because this feature writes an audit CSV directly and the contract forbids edits to `endpoint_primary_key_strategies.py`.
