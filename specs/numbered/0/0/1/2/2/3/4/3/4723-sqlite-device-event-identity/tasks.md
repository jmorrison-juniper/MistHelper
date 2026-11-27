# Tasks: SQLite Device Event Identity

**Input**: Numeric record at `specs/numbered/0/0/1/2/2/3/4/3/4723-sqlite-device-event-identity/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, and `design/contracts/`.

**Tests**: Required. The constitution requires tests for each change (Principle IV and the testing rules). Each test module names the requirements it checks.

**Status values**: `open` means work is not started. `absent` means the file or change does not exist yet. `verified-present` means checked on main and present. `partial` means some parts exist.

## Format

`[ID] [P?] [Story] Description`. `[P]` marks a task that can run in parallel with other `[P]` tasks. `[Story]` names the user story from `spec.md`.

## Phase 1: Setup and verification

- [ ] T001 Verify the main head and the strategy entry.
  - Requirements: FR-018. Story: none.
  - Paths: `src/foundation/support/refactors/endpoint_primary_key_strategies.py` (lines 265 to 271).
  - Acceptance: The entry matches R5. The main head is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` when the work starts.
  - Verification: `python -m py_compile MistHelper.py`
  - Status: verified-present

- [ ] T002 Obtain the handoff for the shared writer file and the menu 21 file.
  - Requirements: FR-016, FR-018. Story: US4.
  - Paths: `src/foundation/support/refactors/sqlite_database_writer.py`, `src/operations/exporting/export/org_alarm_event_exporter.py`.
  - Acceptance: A comment on issue #4723 records the handoff. Or the open pull request list shows no pull request that edits either file. Check with `gh pr list --state open`.
  - Verification: `python -m pytest tests/unit/config/foundation/persistence/storage/db/test_sqlite_database_writer_logging.py -q`
  - Status: open

## Phase 2: Identity contract (blocks the writer)

- [ ] T003 [P] Create the package marker.
  - Requirements: FR-022. Story: none.
  - Paths: `src/foundation/persistence/device_events/__init__.py` (add).
  - Acceptance: The file holds one module docstring and no import. The package folder holds four children at the end of the work.
  - Verification: `python -m ruff check .`
  - Status: absent

- [ ] T004 Create the identity contract.
  - Requirements: FR-001, FR-002, FR-003, FR-023. Story: US1, US3.
  - Paths: `src/foundation/persistence/device_events/identity.py` (add).
  - Acceptance: Class `DeviceEventIdentity` gives `applies(api_function_name)` and `fingerprint(columns, values)`. The fingerprint follows `design/contracts/sqlite-identity-table.md`. Each new line has an inline comment.
  - Depends on: T003.
  - Verification: `python -m pytest tests/unit/db/test_device_event_identity.py -q`
  - Status: absent

- [ ] T005 Create the identity store.
  - Requirements: FR-004, FR-005, FR-006, FR-007, FR-008. Story: US1, US4.
  - Paths: `src/foundation/persistence/device_events/store.py` (add).
  - Acceptance: Class `DeviceEventIdentityStore` gives table state, DDL, `INSERT OR IGNORE`, a presence check in chunks of 500 keys, and explicit `BEGIN IMMEDIATE`, `COMMIT`, and `ROLLBACK`. Exception class `LegacyDeviceEventKeyError` names the migration command.
  - Depends on: T004.
  - Verification: `python -m pytest tests/unit/db/test_device_event_identity.py -q`
  - Status: absent

- [ ] T006 Write the identity unit tests.
  - Requirements: FR-001 to FR-008, FR-018, FR-019, FR-020, FR-023. Story: US1, US3, US4, US5.
  - Paths: `tests/unit/db/test_device_event_identity.py` (add).
  - Acceptance: Thirteen tests exist. Each test uses `tmp_path`. Each test fails before T004 and T005 exist.
  - Depends on: T004, T005.
  - Verification: `python -m pytest tests/unit/db/test_device_event_identity.py -q`
  - Status: absent

## Phase 3: Writer and menu 21 (US1, US4)

- [ ] T007 Add the identity branch to the SQLite writer.
  - Requirements: FR-004, FR-005, FR-008, FR-019. Story: US1, US4.
  - Paths: `src/foundation/support/refactors/sqlite_database_writer.py` (modify lines 246 to 262).
  - Acceptance: `_execute_database_operations` calls the identity store when `DeviceEventIdentity.applies` is True. Other endpoints keep the existing path. A legacy table returns False and logs the migration command. The writer never reaches the `DELETE FROM` branch for this endpoint (R15). Each changed line has an inline comment.
  - Depends on: T002, T005, T006.
  - Verification: `python -m pytest tests/unit/db/test_device_event_identity.py -q`
  - Status: absent

- [ ] T008 Check the write result in menu 21.
  - Requirements: FR-016. Story: US4.
  - Paths: `src/operations/exporting/export/org_alarm_event_exporter.py` (modify lines 140 to 146).
  - Acceptance: `device_events()` calls a helper. The helper logs an error and returns before the completion lines when a non-empty batch returns False. A zero-row batch skips the check. The function stays within 25 lines through the helper.
  - Depends on: T002.
  - Verification: `python -m pytest tests/unit/export/test_org_alarm_event_exporter.py -q`
  - Status: absent

- [ ] T009 Add the menu 21 tests.
  - Requirements: FR-016. Story: US4.
  - Paths: `tests/unit/export/test_org_alarm_event_exporter.py` (modify class `TestDeviceEvents`, lines 148 to 220).
  - Acceptance: Two tests exist. The first test checks that a failed write logs an error and prints no completion line. The second test checks that a zero-row batch skips the failure check.
  - Depends on: T008.
  - Verification: `python -m pytest tests/unit/export/test_org_alarm_event_exporter.py -q`
  - Status: absent

- [ ] T010 Run the compatibility tests.
  - Requirements: FR-017, FR-018. Story: US1.
  - Paths: `tests/unit/prod_readiness/standalone/operations/exporting/reports/test_exports.py`, `tests/unit/test_device_events_52w_exporter.py`, `tests/unit/test_device_events_52w_exporter_extended.py`, `tests/unit/db/test_database_schema_utils.py`, `tests/contract/test_arango_declared_indexes.py`.
  - Acceptance: Each module exits 0 without a test edit. The three-row test still stores three rows (R36).
  - Depends on: T007, T008.
  - Verification: `python -m pytest tests/unit/prod_readiness/standalone/operations/exporting/reports/test_exports.py -q`
  - Status: open

## Phase 4: Migration (US2)

- [ ] T011 Create the migration module.
  - Requirements: FR-009 to FR-015, FR-019, FR-020. Story: US2.
  - Paths: `src/foundation/persistence/device_events/legacy_migration.py` (add).
  - Acceptance: Class `LegacyDeviceEventMigration` gives the dry run through a read-only URI. It makes the backup and checks it. It requires the typed word `MIGRATE` through `InputUtils.safe_input` (R34). It runs one `BEGIN IMMEDIATE` transaction for each table. It runs count checks, then commits or discards the transaction. It returns the exit codes in `design/contracts/migration-cli.md`. The `__main__` guard constructs the class and calls its run method. The module holds no function outside a class.
  - Depends on: T005.
  - Verification: `python -m pytest tests/unit/db/test_device_event_migration.py -q`
  - Status: absent

- [ ] T012 Write the migration tests.
  - Requirements: FR-009 to FR-015. Story: US2.
  - Paths: `tests/unit/db/test_device_event_migration.py` (add).
  - Acceptance: Eight tests exist. Each test uses `tmp_path`. The backup test compares the backup row count with the source row count.
  - Depends on: T011.
  - Verification: `python -m pytest tests/unit/db/test_device_event_migration.py -q`
  - Status: absent

## Phase 5: Documentation and release note

- [ ] T013 [P] Update the operator guide.
  - Requirements: FR-021. Story: US2.
  - Paths: `documentation/operator-guide.md` (add a subsection after line 754).
  - Acceptance: The subsection explains the dry run, the backup, the typed word, the legacy table, and the Warning about lost rows.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 documentation/operator-guide.md`
  - Status: absent

- [ ] T014 [P] Update the strategy diagram.
  - Requirements: FR-021. Story: none.
  - Paths: `documentation/diagrams/core/database-strategy.md` (modify row at line 137 and add a note below the table).
  - Acceptance: The row names the SQLite identity for this endpoint. The note links the operator guide.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 documentation/diagrams/core/database-strategy.md`
  - Status: absent

- [ ] T015 [P] Update the instruction file and the README.
  - Requirements: FR-021. Story: none.
  - Paths: `.github/copilot-instructions.md` (modify lines 208 and 209), `README.md` (add one paragraph after line 18).
  - Acceptance: The instruction file states that device events use a fingerprint key in SQLite. The README paragraph names the migration command and links the operator guide.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 README.md .github/copilot-instructions.md`
  - Status: absent

- [ ] T016 Add the changelog fragment.
  - Requirements: FR-021. Story: none.
  - Paths: `changelog.d/issue-4723-sqlite-device-event-identity.md` (add).
  - Acceptance: One `###` heading. One `**Fixed**` bullet that names issue #4723. The file name follows the rule in `changelog.d/README.md` (R47).
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4723-sqlite-device-event-identity.md`
  - Status: absent

## Phase 6: Gates, pull request, CI, and merge

- [ ] T-LOCAL-GATES Run every applicable local gate.
  - Requirements: FR-022, FR-019, FR-020. Story: none. Success criteria: SC-008.
  - Paths: every changed file listed in T003 to T016.
  - Acceptance: Each applicable row of the local gates table passes (R45). The type gate uses `MYPY_PATHS` from R79. The other applicable rows are the changed test files, coverage, the test quality ratchet, and complexity. Also run bandit, pylint, vulture, pydocstyle, interrogate, the menu reference check, and symbol diff for each changed Python file. Run the STE gate on each changed Markdown file, the safe sweep, and `python -m pytest tests/guardrails`. Each gate reports its examined count.
  - Verification: `python -m ruff check .`
  - Status: open

- [ ] T-PR Commit, push, and open the pull request.
  - Requirements: FR-021. Story: none.
  - Paths: every changed file listed in T003 to T016.
  - Acceptance: The commit subject is `fix(persistence): keep each SQLite device event row`, with the trailer from the repository rules. The branch is `fix/4723-sqlite-device-event-identity`. The pull request body contains `Closes #4723` and lists each gate result from T-LOCAL-GATES.
  - Depends on: T-LOCAL-GATES.
  - Verification: `python -m py_compile MistHelper.py`
  - Status: open

- [ ] T-REMOTE-CI Watch the remote checks.
  - Requirements: none (process gate). Story: none.
  - Paths: none changed by this task.
  - Acceptance: Run `gh pr checks <number> --watch`. Each required check passes, including CodeQL. A failed check opens a new issue before a fix.
  - Depends on: T-PR.
  - Verification: `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal`
  - Status: open

- [ ] T-MERGE Enable auto-merge after review.
  - Requirements: none (process gate). Story: none.
  - Paths: `src/foundation/persistence/device_events/legacy_migration.py`.
  - Acceptance: A person reviews the migration module before merge. The orchestrator authorizes the merge. Then the `auto-merge` label is added. Auto-merge does not start before both conditions hold.
  - Depends on: T-REMOTE-CI.
  - Verification: `python MistHelper.py --test`
  - Status: open

## Dependencies and execution order

- T001 and T002 come first. T002 blocks T007 and T008.
- T003 blocks T004. T004 blocks T005 and T006. T005 blocks T007 and T011.
- T007 and T008 block T010. T008 blocks T009.
- T011 blocks T012.
- T013, T014, T015, and T016 can run in parallel after the code tasks.
- The gate, pull request, CI, and merge tasks run last, in that order.

## Requirement coverage

| Requirement | Tasks | Test or check |
| - | - | - |
| FR-001 | T004, T007 | Two-event test in T006 |
| FR-002 | T004 | Fingerprint change test in T006 |
| FR-003 | T004, T005 | Two-organization test in T006 |
| FR-004 | T005, T007 | Batch and verification tests in T006 |
| FR-005 | T005, T007 | Verification failure test in T006 |
| FR-006 | T005 | Rerun test in T006 |
| FR-007 | T005 | Identical batch test in T006 |
| FR-008 | T005, T007 | Legacy refusal test in T006 |
| FR-009 | T011 | Dry run test in T012 |
| FR-010 | T011 | Backup test in T012 |
| FR-011 | T011 | Typed word test in T012 |
| FR-012 | T011 | Distinct rows test in T012 |
| FR-013 | T011 | Count mismatch test in T012 |
| FR-014 | T011 | Identity table test in T012 |
| FR-015 | T011 | Legacy kept test in T012 |
| FR-016 | T008, T009 | Two menu 21 tests in T009 |
| FR-017 | T010 | Existing menu 97 tests in T010 |
| FR-018 | T001, T010 | Unchanged catalog and Arango contract tests in T010 |
| FR-019 | T005, T007, T011 | Writer log order test in T006. The migration dry run test in T012 checks its info and debug lines with `caplog`. |
| FR-020 | T006, T011 | ASCII log test in T006 |
| FR-021 | T013, T014, T015, T016 | STE gate on each changed Markdown file |
| FR-022 | T003 | Guardrails run in T-LOCAL-GATES |
| FR-023 | T004 | Fixed digest test in T006 |
