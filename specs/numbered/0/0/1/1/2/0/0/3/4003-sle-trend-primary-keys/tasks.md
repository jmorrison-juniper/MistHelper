# Tasks: SLE trend primary keys

**Input**: [Specification](spec.md), [plan](plan.md), and supporting documents under `design/`.

## Phase 1: Setup

- [x] T001 Confirm open issue, current main base, and exclusive file ownership before edits in `src/foundation/support/refactors/endpoint_primary_key_strategies.py`.
- [x] T002 Run the mandatory branch hook and allocate the managed numeric feature route for `spec.md`.
- [x] T003 Prepare the local environment with `scripts/bootstrap_worktree.py`.

## Phase 2: Foundation

- [x] T004 Add a shared SLE identity helper. Validate complete identifiers and finite nonnegative boundaries. End must not precede start. (delivered: src/foundation/support/refactors/endpoint_primary_key_strategies.py)

## Phase 3: User Story 1 - Repeat a trend export

**Goal**: One keyed row per complete window.
**Independent test**: Export the same fake window twice, then export another window and identifier set.

- [x] T005 [US1] Add complete request dimensions. (delivered: src/operations/exporting/export/endpoint_family_exporter.py)
- [x] T006 [US1] Define both complete composite strategies. (delivered: src/foundation/support/refactors/endpoint_primary_key_strategies.py)
- [x] T007 [US1] Use complete SLE identities without changing unrelated keys. (delivered: src/foundation/persistence/db/writers/arango_writer.py)
- [x] T008 [US1] Update exact strategy and real SDK export assertions. (delivered: tests/unit/export/test_endpoint_family_exporter.py)
- [x] T009 [US1] Prove repeated and distinct windows. (delivered: tests/unit/arango_indexes/test_preservation.py)

## Phase 4: User Story 2 - Preserve existing records

**Goal**: Preserve every legacy row and accept one new keyed row for a matching legacy window.
**Independent test**: Compare complete legacy rows before and after two new exports.

- [x] T010 [US2] Add nullable SQLite identity and unique index without rebuilding old tables. (delivered: src/foundation/support/refactors/sqlite_database_writer.py)
- [x] T011 [US2] Prove legacy and new-table replacement. (delivered: tests/unit/refactors/test_sqlite_database_writer.py)
- [x] T012 [US2] Prove UUID legacy preservation and invalid identity rejection. (delivered: tests/unit/arango_indexes/test_preservation.py)

## Phase 5: User Story 3 - Measure the complete registry

**Goal**: Report all registry entries and all confirmed summary-window candidates.
**Independent test**: The complete scan reports stable counts. Empty input and an injected defect fail.

- [x] T013 [US3] Add the complete-table guard and export replacement test. (delivered: tests/guardrails/test_endpoint_catalog.py, tests/unit/export/test_endpoint_family_exporter.py)
- [x] T014 [US3] Record both additional defects and separate issues #4347 and #4348. (delivered: design/research.md)

## Phase 6: Final validation and delivery

- [x] T015 Document the existing-data decision. (delivered: changelog.d/issue-4003-sle-trend-primary-keys.md)
- [x] T016 Run applicable focused tests and local gates from `design/quickstart.md`. Results: 1,556 tests passed, 96.54 percent changed-module coverage, and no lost symbols.
- [x] T017 Run read-only Spec Kit analysis and report the result in the PR body. All 17 requirements and success criteria have task coverage. No unresolved finding remains.
- [x] T018 Prepare the complete PR text using `.github/PULL_REQUEST_TEMPLATE.md` with exact validation evidence and the existing-data assumption. The session artifact holds the prepared body.

## Dependencies

T001 through T003 precede T004. T004 precedes US1 and US2.
US3 measurement is independent of persistence implementation.
Final validation requires all three stories.

## Parallel execution examples

Exporter and Arango test changes can proceed independently after the identity contract exists.
SQLite legacy tests can proceed independently of Arango tests.
The registry measurement can proceed independently of both writers.
This session executes the small, coupled implementation directly.

## Implementation strategy

Complete the shared identity first, then wire the export and both writers.
Prove legacy preservation before accepting the implementation.
Run the complete guard and document its additional candidate.
Human review remains outside automated delivery. Do not enable auto-merge or merge.
After implementation, commit the intended files, run the test-quality gate, and create the ready-for-review PR.
