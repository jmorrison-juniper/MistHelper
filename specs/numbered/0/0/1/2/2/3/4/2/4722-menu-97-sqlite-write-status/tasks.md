# Tasks: Menu 97 SQLite Write Status

**Input**: Numeric record for issue 4722 at `specs/numbered/0/0/1/2/2/3/4/2/4722-menu-97-sqlite-write-status/`. Read `spec.md` and `plan.md` first.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, `design/contracts/`.

## Format

Each task names its status. The status values are `open`, `verified-present`, `partial`, and `absent`. The `[P]` marker means the task can run in parallel with other `[P]` tasks. A task that has no marker runs in order.

## Phase 1: Precondition

### T001 - Confirm file ownership and record the baseline

- **Requirements**: FR-008
- **Files**: `src/operations/exporting/export/data_exporter.py`, `tests/unit/export/test_data_exporter.py`
- **Acceptance**: Open PR #4813 has merged, or the owner gives a handover for both files. The baseline tests for the module pass before any edit.
- **Verification**: Run `gh pr list -R jmorrison-juniper/MistHelper --state open --json number,headRefName,files` as a read-only check. Then run `python -m pytest tests/unit/export/test_data_exporter.py`.
- **Status**: open

## Phase 2: Verify Existing Behavior on Remote Main

These tasks confirm behavior that already exists. They add no code.

### T002 - Verify the first-batch SQLite stop

- **Requirements**: FR-001
- **Files**: `src/operations/exporting/export/device_events_52w_exporter.py` (lines 252 to 263 and 303 to 305), `tests/unit/test_device_events_52w_exporter_extended.py` (line 574)
- **Acceptance**: The helper raises when the writer returns False. The first-batch branch raises before any checkpoint write. The existing test exists on remote main at line 574.
- **Verification**: `python -m pytest tests/unit/test_device_events_52w_exporter_extended.py`
- **Status**: verified-present

### T003 - Verify the later-batch stop, checkpoint, and completion rules

- **Requirements**: FR-002, FR-003
- **Files**: `src/operations/exporting/export/device_events_52w_exporter.py` (lines 96 to 97, 117 to 118, 323 to 325, 330 to 340). `tests/unit/test_device_events_52w_exporter_extended.py` (lines 574 to 594, 597 to 622).
- **Acceptance**: A False result on a later batch raises before the checkpoint advances. Completion and checkpoint removal run only after the streaming loop ends.
- **Verification**: `python -m pytest tests/unit/test_device_events_52w_exporter_extended.py`
- **Status**: verified-present

### T004 - Verify the default writer result for partial batches

- **Requirements**: FR-007
- **Files**: `src/foundation/support/refactors/sqlite_database_writer.py` (lines 459 to 475), `tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py` (lines 636 to 655)
- **Acceptance**: The writer returns True for a partial batch when the caller sets no flag. The existing test asserts this result.
- **Verification**: `python -m pytest tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py`
- **Status**: verified-present

### T005 - Verify the CSV and empty-result contracts

- **Requirements**: FR-009
- **Files**: `src/operations/exporting/export/device_events_52w_exporter.py` (lines 120 to 125 and 363 to 368), `tests/unit/test_device_events_52w_exporter.py` (lines 8 to 31), `tests/unit/test_device_events_52w_exporter_extended.py` (lines 236 to 249 and 263 to 271)
- **Acceptance**: The CSV path and the empty-result path keep their current calls. The existing tests assert these calls.
- **Verification**: `python -m pytest tests/unit/test_device_events_52w_exporter.py`
- **Status**: verified-present

## Phase 3: Tests First

Write these tests before any implementation task. Each new test must fail before the change. A failure that comes from a missing keyword argument counts as a failure.

### T006 [P] - Writer full-batch tests (TC-01 to TC-04)

- **Requirements**: FR-004, FR-005
- **Files**: `tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py` (append after line 655)
- **Acceptance**: TC-01 asserts that a partial batch with the flag returns False and logs the discard line. TC-02 asserts that the table holds no row of the rejected batch. TC-03 asserts that rows of earlier batches remain. TC-04 asserts that a fully stored batch with the flag returns True. The existing writer tests stay unchanged.
- **Verification**: `python -m pytest tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py`
- **Status**: absent

### T007 - DataExporter full-batch tests (TC-05 to TC-07)

- **Requirements**: FR-008
- **Files**: `tests/unit/export/test_data_exporter.py` (append a new class after the last class). Start only after T001 passes.
- **Acceptance**: TC-05 asserts that the SQLite writer receives `require_full_batch=True`. TC-06 asserts that a SQLite request without the flag uses `_dispatch_format_write`. TC-07 asserts that a writer exception returns False and logs an error that names the table.
- **Verification**: `python -m pytest tests/unit/export/test_data_exporter.py`
- **Status**: absent

### T008 - Exporter request tests (TC-08 and TC-09)

- **Requirements**: FR-006, FR-009
- **Files**: `tests/unit/test_device_events_52w_exporter_extended.py` (append at the end of the module)
- **Acceptance**: TC-08 asserts that the initial and streamed SQLite writes both request `require_full_batch=True`. TC-09 asserts that the CSV path and the empty-result path do not request it.
- **Verification**: `python -m pytest tests/unit/test_device_events_52w_exporter_extended.py`
- **Status**: absent

### T009 - Real-writer partial and complete export tests (TC-10 and TC-11)

- **Requirements**: FR-002, FR-003, FR-004, FR-005
- **Files**: `tests/unit/test_device_events_52w_exporter_extended.py` (append after T008 tests)
- **Acceptance**: TC-10 uses the real `DataExporter` and the real SQLite writer. A trigger rejects one event in the fourth page. The export raises RuntimeError. The checkpoint keeps the continuation token of the third page. The table holds no row of the fourth page. No completion message is logged. TC-11 runs the same sequence with no rejected row. The export completes, and the checkpoint file is removed. Both tests set `MISTHELPER_STANDALONE` to `true`, so the polyglot mirror opens no network connection.
- **Verification**: `python -m pytest tests/unit/test_device_events_52w_exporter_extended.py`
- **Status**: absent

## Phase 4: Implementation

### T010 [P] - Add the full-batch option

- **Requirements**: FR-004, FR-006
- **Files**: `src/foundation/models/dataclasses/export_backend_options.py`
- **Acceptance**: `ExportBackendOptions` gains `require_full_batch: bool = False` with an inline comment. The module docstring lists the new field. Its contract is in `design/contracts/export-backend-options.md`.
- **Verification**: `python -m pytest tests/unit/export/test_data_exporter.py`
- **Status**: absent

### T011 [P] - Add the writer flag and the discard path

- **Requirements**: FR-004, FR-005, FR-007
- **Files**: `src/foundation/support/refactors/sqlite_database_writer.py`
- **Acceptance**: `write` accepts `require_full_batch: bool = False` and passes it to `_execute_database_operations`. That method passes it to `_finish_batch`. `_finish_batch` calls the new `_reject_partial_batch` when the flag is set and a row is rejected. `_reject_partial_batch` logs one error line and calls `_rollback_transaction`, then returns False. `_finish_batch` stays at or below 25 lines. The contract is in `design/contracts/writer-full-batch.md`.
- **Verification**: `python -m pytest tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py`
- **Status**: absent

### T012 - Add the DataExporter full-batch branch

- **Requirements**: FR-004, FR-008
- **Files**: `src/operations/exporting/export/data_exporter.py`
- **Acceptance**: `write_with_format_selection` calls `_write_full_batch_sqlite` when `opts.require_full_batch` is set and the format is sqlite. Otherwise it calls `_dispatch_format_write` as before. `_write_full_batch_sqlite` calls `_write_sqlite_format` with `require_full_batch=True`. It catches an exception, logs an error that names the table, and returns False. `_write_sqlite_format` gains the `require_full_batch` argument with a default of False.
- **Verification**: `python -m pytest tests/unit/export/test_data_exporter.py`
- **Status**: absent

### T013 - Request full-batch writes from the 52-week exporter

- **Requirements**: FR-006
- **Files**: `src/operations/exporting/export/device_events_52w_exporter.py` (lines 252 to 263)
- **Acceptance**: `_write_sqlite_batch` builds `ExportBackendOptions(format_override=_SQLITE_FORMAT, require_full_batch=True)`. The error text and the RuntimeError stay unchanged. The contract is in `design/contracts/device-events-52w-sqlite-write.md`.
- **Verification**: `python -m pytest tests/unit/test_device_events_52w_exporter_extended.py`
- **Status**: partial

### T014 [P] - Add the release-note fragment

- **Requirements**: FR-010
- **Files**: `changelog.d/issue-4722-partial-batch.md` (new)
- **Acceptance**: The file holds one heading, one Fixed bullet, and the text "Issue #4722". It has no version stamp. It passes the changelog guard.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: absent

## Phase 5: Delivery

### T-LOCAL-GATES - Run every applicable local gate

- **Requirements**: FR-001 to FR-010
- **Files**: every file in the change map of `plan.md`
- **Acceptance**: Each applicable gate from the Local gates table of `.github/copilot-instructions.md` exits 0. The run records the count for each gate. The full-suite shards, coverage, test quality, complexity, security, symbol, and STE gates run. Dependency audit, Ops portal, Ops platform, and menu reference gates are not applicable. The pull request body gives the reason for each gate that does not apply.
- **Verification**: `python -m ruff check .`
- **Status**: open

### T-PR - Commit, push, and open the pull request

- **Requirements**: FR-010
- **Files**: the change map of `plan.md`
- **Acceptance**: A worktree holds branch `fix/4722-sqlite-partial-batch` from `origin/main`. The commit subject is `fix(export): stop menu 97 SQLite export on a partial batch`. The commit body names `Closes #4722` and `Refs #4721` and `Refs #4723`. The body ends with the Co-authored-by trailer. The pull request title uses the same subject. The pull request body follows `.github/PULL_REQUEST_TEMPLATE.md` and names the linked spec issue.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: open

### T-REMOTE-CI - Watch the required checks

- **Requirements**: SC-006
- **Files**: the pull request created in T-PR
- **Acceptance**: `gh pr checks <number> --watch` reports every required check as passed. CodeQL passes before the `auto-merge` label is added.
- **Verification**: `python -m pytest tests/unit/test_device_events_52w_exporter_extended.py`
- **Status**: open

### T-MERGE - Enable auto-merge after authorization

- **Requirements**: SC-006
- **Files**: the pull request created in T-PR
- **Acceptance**: The orchestrator authorizes the merge. The serial merge slot is held for this pull request. The `auto-merge` label is added after every required check passes. The squash merge closes issue 4722. The branch and the worktree are removed. The owner then runs Principle IV steps 10 through 12.
- **Verification**: `python -m ruff check .`
- **Status**: open

## Dependencies and Execution Order

- T001 must finish before T007 and T012.
- T002 to T005 are read-only checks. They can run at any time.
- T006, T007, T008, and T009 must finish before T010 to T013. The tests fail first.
- T010 must finish before T012 and T013.
- T011 must finish before T012.
- T014 runs in parallel with the other implementation tasks.
- T-LOCAL-GATES starts after T006 to T014 pass.
- T-PR starts after T-LOCAL-GATES passes.
- T-REMOTE-CI starts after T-PR opens the pull request.
- T-MERGE starts after T-REMOTE-CI passes and the orchestrator authorizes it.

## Requirement Coverage

| Requirement | Tasks | Tests | Notes |
| - | - | - | - |
| FR-001 | T002 | Existing first-batch test (line 574), TC-08 | Verified on remote main. |
| FR-002 | T003 | Existing later-batch test (line 597), TC-10 | Verified on remote main. |
| FR-003 | T003 | Existing tests (lines 574 and 597), TC-10, TC-11 | Verified on remote main. |
| FR-004 | T006, T010, T011, T012 | TC-01, TC-04, TC-05, TC-10 | Absent on remote main. |
| FR-005 | T006, T011 | TC-02, TC-03, TC-10 | Absent on remote main. |
| FR-006 | T008, T013 | TC-08, TC-09 | Absent on remote main. |
| FR-007 | T004 | Existing writer test (line 636) | Verified on remote main. Keep it. |
| FR-008 | T007, T012 | TC-05, TC-06, TC-07 | Absent on remote main. |
| FR-009 | T005 | Existing CSV tests, TC-09 | Verified on remote main. Keep it. |
| FR-010 | T014 | Changelog guard test | Absent on remote main. |

## Test Case Map

| Test | Module | Task | Purpose |
| - | - | - | - |
| TC-01 | `test_sqlite_database_writer.py` | T006 | Partial batch with the flag returns False and logs the discard line. |
| TC-02 | `test_sqlite_database_writer.py` | T006 | A rejected batch stores no row. |
| TC-03 | `test_sqlite_database_writer.py` | T006 | Rows of earlier batches remain after a rejected batch. |
| TC-04 | `test_sqlite_database_writer.py` | T006 | A fully stored batch with the flag returns True. |
| TC-05 | `test_data_exporter.py` | T007 | The writer receives the flag for a SQLite full-batch request. |
| TC-06 | `test_data_exporter.py` | T007 | A SQLite request without the flag uses the dispatch path. |
| TC-07 | `test_data_exporter.py` | T007 | A writer exception returns False and logs an error. |
| TC-08 | `test_device_events_52w_exporter_extended.py` | T008 | Initial and streamed SQLite writes request the flag. |
| TC-09 | `test_device_events_52w_exporter_extended.py` | T008 | CSV and empty-result writes do not request the flag. |
| TC-10 | `test_device_events_52w_exporter_extended.py` | T009 | A rejected later batch stops the export and keeps the checkpoint. |
| TC-11 | `test_device_events_52w_exporter_extended.py` | T009 | A complete export removes the checkpoint and logs completion. |
