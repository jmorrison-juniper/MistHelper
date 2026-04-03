---

description: "Task list for Audit - Export zone information (Menu #52)"
---

# Tasks: Audit - Export zone information (Menu #52)

**Input**: Design documents in specs/101-audit-menu-52-export-zone-information/ (spec.md, plan.md, research.md, data-model.md, contracts/)
**Prerequisites**: plan.md (required), spec.md (required), research.md (recommended before implementation), data-model.md, contracts/

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create research/design artifacts and developer quickstart so implementation is deterministic.

- [ ] T001 Create research.md resolving empty-output semantics, flattening strategy, string parsing heuristics, and SQLite typing at specs/101-audit-menu-52-export-zone-information/research.md
- [ ] T002 [P] Create data-model.md with Zone entity attributes, CSV header canonical order, and SQLite table schema at specs/101-audit-menu-52-export-zone-information/data-model.md
- [ ] T003 [P] Create contracts/cli-export-zone-info.md documenting CLI flags, format override, and output path at specs/101-audit-menu-52-export-zone-information/contracts/cli-export-zone-info.md
- [ ] T004 [P] Create contracts/module-export-api.md documenting function signatures for SiteExportUtils._export_data and DataExporter.write_with_format_selection at specs/101-audit-menu-52-export-zone-information/contracts/module-export-api.md
- [ ] T005 [P] Create quickstart.md with developer instructions for running exporter locally and running tests at specs/101-audit-menu-52-export-zone-information/quickstart.md
- [ ] T006 [P] Update agent context using .specify/scripts/powershell/update-agent-context.ps1 - ensure new decisions (flattening, sqlite typing) are included; document changes in specs/101-audit-menu-52-export-zone-information/agent-context-update.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Code-level, repository-wide changes that MUST be completed before user-story work.

- [ ] T007 Modify DataExporter._validate_write_inputs to treat an explicit empty list as a valid input and allow creating a header-only CSV or a documented informational CSV in misthelper/data_export/data_exporter.py
- [ ] T008 [P] Ensure SiteExportUtils._export_data (misthelper/exporters.py) and callers pass api_call.__name__ (api_function_name) through to DataExporter.write_with_format_selection and SQLiteDatabaseWriter (update all call sites in MistHelper.py and misthelper/exporters.py)
- [ ] T009 [P] Add an explicit optional config flag and codepath to DataProcessingUtils to disable auto-parsing of stringified JSON by default; implement conservative parsing only when flag enabled in misthelper/data_export/processing.py
- [ ] T010 Harden list-of-dicts flattening: implement deterministic indexed-limit behavior with configurable MAX_INDEXED (default 3) and JSON-overflow column fallback in misthelper/data_export/processing.py
- [ ] T011 Update DatabaseSchemaUtils to accept explicit api_function_name and avoid call-stack inference; document table naming and column casing conventions in misthelper/data_export/database_schema_utils.py
- [ ] T012 Update SQLiteDatabaseWriter in misthelper/data_export/db_writer.py to preserve Python None => SQL NULL and preserve obvious numeric/boolean typing where safe; add safe fallback to TEXT for ambiguous cases
- [ ] T013 [P] Add detailed debug logging at key points (API fetch start/finish, flattening summary, write start/finish) in misthelper/data_export/* (data_exporter.py, processing.py, db_writer.py)
- [ ] T014 Add error-safe emergency/partial save behavior in DataExporter.save_data_to_output so rate-limited/exceptional responses still persist partial data to data/ with clear filename suffix (e.g., .partial) in misthelper/data_export/data_exporter.py
- [ ] T015 Create or update configuration constants and defaults for export behavior (DEFAULT_OUTPUT_DIR=data/, DEFAULT_SQLITE_DB=data/mist_data.db, MAX_INDEXED_LIST_ITEMS=3) in misthelper/config.py or similar
- [ ] T016 Add a migration note in specs/101-audit-menu-52-export-zone-information/quickstart.md describing flattening column changes and backward compatibility guidance

**Checkpoint**: Once foundational tasks complete, user-story implementation can begin.

---

## Phase 3: User Story 1 - Export site zones to CSV (Priority: P1) 🎯 MVP

**Goal**: Produce a stable, escape-safe CSV for site zones written to data/SiteZones.csv (or configured filename) including deterministic flattened columns and correct empty-output behaviour.

**Independent Test**: Run SiteExportUtils._export_data(api_call=mistapi.api.v1.sites.zones.listSiteZones, format_override='csv') against mocked API that returns representative zone objects and verify data/SiteZones.csv exists, header row is present, and rows match expected flattened fields.

### Tests for User Story 1

- [ ] T017 [P] [US1] Add unit test tests/unit/test_sitezones_empty_output.py verifying DataExporter.save_data_to_output([], filename) creates header-only CSV when fields provided and informational CSV when no fields (use temp dir)
- [ ] T018 [P] [US1] Add unit test tests/unit/test_sitezones_flattening.py for DataProcessingUtils.flatten_nested_fields demonstrating deterministic columns for nested dicts and lists-of-dicts
- [ ] T019 [P] [US1] Add unit test tests/unit/test_sitezones_escape_multiline.py for DataProcessingUtils.escape_multiline ensuring newlines are escaped and lists become comma-strings

### Implementation for User Story 1

- [ ] T020 [US1] Implement CSV header computation and write logic (use get_unique_keys + stable ordering) in misthelper/data_export/data_exporter.py (function: _write_csv_format)
- [ ] T021 [US1] Ensure DataExporter._validate_write_inputs allows explicit empty list to write header-only CSV and returns True on successful file creation in misthelper/data_export/data_exporter.py (depends on T007)
- [ ] T022 [US1] Wire CSV path/filename creation to DEFAULT_OUTPUT_DIR and ensure cross-platform path handling in misthelper/data_export/data_exporter.py (depends on T015)
- [ ] T023 [US1] Add an integration test tests/integration/test_sitezones_csv_pipeline.py that runs the full pipeline (API fetch -> processing -> CSV write) using mocked API responses and temp data dir

**Checkpoint**: User Story 1 should be independently verifiable by running the unit + integration tests above.

---

## Phase 4: User Story 2 - Export site zones to SQLite (Priority: P2)

**Goal**: Export zones into a SQLite table (SiteZones) with stable schema, correct primary-key/upsert behavior, and preserved NULLs/types (per Phase 0 decision).

**Independent Test**: Run exporter with format_override='sqlite' against a mocked zone dataset and verify a SQLite DB exists at configured path with SiteZones table, expected columns, and upsert behavior for repeated runs.

### Tests for User Story 2

- [ ] T024 [P] [US2] Add unit test tests/unit/test_sitezones_sqlite_writer_types.py verifying None->NULL, numeric/boolean typing preservation, and fallback to TEXT
- [ ] T025 [P] [US2] Add unit test tests/unit/test_sitezones_sqlite_upsert.py verifying INSERT OR REPLACE behavior for natural primary key (id) and delete+insert behavior for auto-increment fallback

### Implementation for User Story 2

- [ ] T026 [US2] Implement SQLite table creation and schema selection logic using DatabaseSchemaUtils.get_endpoint_strategy in misthelper/data_export/db_writer.py (depends on T011)
- [ ] T027 [US2] Implement typed value binding (None=>NULL, int/float=>INTEGER/REAL, bool=>INTEGER 0/1 or native boolean if supported) and upsert/insert strategy in misthelper/data_export/db_writer.py (depends on T012)
- [ ] T028 [US2] Add integration test tests/integration/test_sitezones_sqlite_pipeline.py that runs full pipeline against mocked API and an in-memory or temp-file SQLite DB to validate table columns and upsert behavior
- [ ] T029 [US2] Add a contract test tests/contract/test_sitezones_contract.py asserting DatabaseSchemaUtils.get_endpoint_strategy('listSiteZones', fields) returns expected natural key strategy (id) (depends on T011 and T008)

**Checkpoint**: User Story 2 should be independently verifiable via unit + integration tests and the contract test.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, CI, and cleanup after user stories are implemented.

- [ ] T030 [P] Update docs/ and README with export behavior changes and quickstart validation at docs/export-zone-information.md (or update specs/101-audit-menu-52-export-zone-information/quickstart.md)
- [ ] T031 [P] Add/modify CI workflow (.github/workflows/ci.yaml) to run new tests (unit + integration) and ensure database write permissions in runner
- [ ] T032 [P] Run static analysis (lint) and fix issues in changed files (misthelper/data_export/*, misthelper/exporters.py, MistHelper.py)
- [ ] T033 [P] Tag tasks completed in CHANGELOG and include migration notes for downstream consumers at specs/101-audit-menu-52-export-zone-information/migration-notes.md
- [ ] T034 Create final acceptance checklist in specs/101-audit-menu-52-export-zone-information/acceptance-checklist.md listing AC-1.1..AC-6.3 and link to tests that verify them

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1): T001..T006 — no external dependencies, start here
- Foundational (Phase 2): T007..T016 — depends on Setup completion
- User Stories (Phase 3+): T017..T029 — depend on Foundational completion
- Polish (Final Phase): T030..T034 — depend on User Stories completion

### Story Order & Dependencies

- User Story 1 (P1) - CSV export: depends on Foundational tasks (T007,T010,T015) and should be delivered as MVP
- User Story 2 (P2) - SQLite export: depends on Foundational tasks (T008,T011,T012,T015) and on US1 only for shared utilities, but is independently testable

### Within-Story Ordering

- Tests for a story (e.g., T017..T019 for US1) should be created before or alongside implementation and must pass before marking story complete
- Implement processing & writer changes before integration tests

### Parallel Opportunities

- T002, T003, T004, T005, T006 (docs/design tasks) can run in parallel [P]
- Logging, config updates, and repository lints (T013, T015, T032) can be parallelized [P]
- Unit tests across different concerns (flattening, sqlite typing, escape) can be written in parallel [P]
- US1 and US2 implementation tasks can proceed in parallel after Foundational completion if teams are available; otherwise implement US1 (CSV) first as MVP

---

## Parallel Example: User Story 1 (CSV)

- [ ] T017 [P] [US1] tests/unit/test_sitezones_empty_output.py
- [ ] T018 [P] [US1] tests/unit/test_sitezones_flattening.py
- [ ] T019 [P] [US1] tests/unit/test_sitezones_escape_multiline.py

Run these tests in parallel to validate CSV behaviors while a developer implements T020..T023.

---

## Implementation Strategy

MVP First (User Story 1 only):

1. Complete Setup tasks (T001..T006)
2. Complete Foundational tasks (T007..T016)
3. Implement User Story 1 (T017..T023), verify tests pass
4. Stop and validate: if CSV export is correct, publish MVP and resume US2

Incremental Delivery:

- After MVP, implement US2 (T024..T029) to add SQLite support and upsert behavior
- Run integration tests and CI (T030..T031)

---

## Summary Report

- Path to generated tasks.md: specs/101-audit-menu-52-export-zone-information/tasks.md
- Total task count: 34
- Task count per user story:
  - Setup/Design (Phase 1): 6 tasks (T001..T006)
  - Foundational (Phase 2): 10 tasks (T007..T016)
  - User Story 1 (US1): 7 tasks (T017..T023)
  - User Story 2 (US2): 6 tasks (T024..T029)
  - Polish & Cross-Cutting: 5 tasks (T030..T034)
- Parallel opportunities identified: doc tasks (T002..T006), logging/config/lint tasks (T013,T015,T032), unit tests per story
- Independent test criteria for each story: included under each User Story section (see above)
- Suggested MVP scope: User Story 1 (CSV export) only (T017..T023)

## Format validation

All tasks follow the checklist format: "- [ ] T### [P?] [US?] Description with file path". Each task includes an explicit file path where code/docs should be added or modified.

---

Generated-by: speckit.tasks
