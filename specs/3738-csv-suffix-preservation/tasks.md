# Tasks: CSV suffix preservation

**Input**: [spec.md](spec.md), [plan.md](plan.md), and [the contract](contracts/csv-suffix.md).

## Setup

- [x] T001 Read the live issue and all comments. Reserve the nine exact paths before edits. (delivered: issue #3738 claim comment)

- [x] T002 Read the current templates and constitution. Write this feature-only specification, plan, and contract. (delivered: specs/3738-csv-suffix-preservation/)

- [x] T003 Attempt the documented bootstrap. Recover only the owned ignored environment after its recorded failure. (delivered: .venv/)

## User Story 1 - Advertised Native Output

- [x] T004 [US1] Add the native proof. (delivered: tests/integration/export/test_menu64_csv_suffix_preservation.py)

- [x] T005 [US1] Prove the mismatch with one handler, two SDK requests, and no live HTTP request. (delivered: native red proof)

- [x] T006 [US1] Change only the CSV suffix decision. (delivered: src/export/data_exporter.py)

- [x] T007 [US1] Verify the filename, merged record, metadata, notice, and counts. (delivered: native green proof)

## User Story 2 - Filename Preservation

- [x] T008 [US2] Add cases that execute the writer. (delivered: tests/unit/export/test_csv_suffix_preservation.py)

- [x] T009 [US2] Verify case, paths, Unicode, records, empty input, errors, and truncation. (delivered: owned tests)

- [x] T010 [US2] Prove uppercase failure with the original decision. Verify both controls. Restore the repair. (delivered: negative control)

## User Story 3 - Backend and Discovery Preservation

- [x] T011 [US3] Add backend and discovery tests. (delivered: tests/contract/export/test_csv_suffix_backends_and_discovery.py)

- [x] T012 [US3] Verify SQLite names, routing data, metadata, calls, and errors. (delivered: contract tests)

- [x] T013 [US3] Execute path resolution, browser services, and output scanning. (delivered: contract and native tests)

## Local Verification and Commit

- [x] T014 Run the selected exporter, output, routing, and natural-key tests. (delivered: 393 passing tests)

- [x] T015 Run local gates, guide preflight, links, and writing checks. (delivered: passing local results in plan.md)

- [x] T016 Verify source nodes, protected bytes, coverage, and generated references. (delivered: source and reference checks)

- [x] T017 Add the release note. (delivered: changelog.d/issue-3738-csv-suffix-preservation.md)

- [x] T018 Review consistency and the full template. (delivered: offline draft with 23 preserved checklist items)

- [x] T019 Remove owned temporary outputs and close each handle. (delivered: 16 absent targets and strict resource checks)

- [x] T020 Prepare the exact manifest for the local commit. (delivered: nine staged reserved paths)

## Dependencies and Scope

T001 through T003 precede all test work. T005 precedes T006. T006 precedes
the green proof. T010 must restore the repair before final gates.
T014 through T019 precede the local commit.

This task ends with a local unpublished handoff at queue position 47.
Publication and proof on a resulting main revision are not authorized tasks.

The session records the commit SHA and clean state after the local commit.
Those receipts remain outside the commit to avoid a self-referencing record.
