# Tasks: Stable SLE summary window keys

**Input**: `specs/numbered/0/0/1/1/4/3/4/2/4347-sle-window-summary-keys/`

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`,
`design/data-model.md`, and `design/quickstart.md`.

**Tests**: Tests are required by the specification and contributor rules.
Use fake API responses, temporary SQLite stores, and the Arango fake.
Do not call live Mist or production databases.

**Organization**: Tasks follow the three P1 user stories in `spec.md`.
Each task names its prerequisite task IDs and exact file paths.

## Phase 1: Setup

**Purpose**: Verify implementation scope and the structural limit before code work.

- [X] T001 Confirm open-PR ownership for every planned path. PR #4208 and PR #4619 list `README.md`; the scoped #4208 handover covers only the SLE paragraph, and the #4619 WAN paragraph remains untouched. PR #4358 owns no planned path. Verify `origin/main` is `2758fe4ee87de047bb66003a1e76d7657aae6f1b` and `tests/unit/db/sle_window_summary/` is the fifth direct child of `tests/unit/db/`. The current branch is five commits behind `origin/main`; do not rebase.

## Phase 2: Foundational

**Purpose**: Use the existing exporter, identity, persistence, and test infrastructure.

No shared code or migration prerequisite is needed. Complete T001 before any story task.

## Phase 3: User Story 1 - Repeat an export without new duplicates (Priority: P1)

**Goal**: Give each histogram and impact-summary window its exact identity and keep content changes outside that identity.

**Independent Test**: Fake each SDK response, compare exact identity tuples, vary one identity field at a time, and verify content-only changes keep the same identity.

### Tests for User Story 1

- [X] T002 [P] [US1] Test exact tuples, each identity-field variation, authoritative path dimensions, returned boundaries, content-only changes, invalid-batch safety, and empty-response behavior in `tests/unit/db/sle_window_summary/test_export_identity.py`. Use existing tests in `tests/unit/export/test_endpoint_family_exporter.py` for SDK method selection, required path arguments, and credential redaction. Prerequisite: T001.

### Implementation for User Story 1

- [X] T003 [US1] Rename `SleTrendIdentity` to `SleWindowIdentity`, then add the exact histogram identity `(site_id, scope, scope_id, metric, start, end)` and impact-summary identity `(site_id, scope, scope_id, metric, classifier, failure, start, end)` in `src/foundation/support/refactors/endpoint_primary_key_strategies.py`; preserve the existing trend identities. Prerequisite: T002.
- [X] T004 [US1] Use selected path identifiers and each response's actual `start` and `end` for the two endpoint identities in `src/operations/exporting/export/endpoint_family_exporter.py`; preserve response content and required-path-only SDK calls. Prerequisite: T003.
- [X] T005 [US1] Update the expected audit results for both exact endpoint identities in `tests/guardrails/test_endpoint_catalog.py`; retain `auto_increment_with_unique` for both strategies. Prerequisite: T003.

**Checkpoint**: The identity tests and endpoint catalog audit pass without changing either trend identity or SDK call arguments.

## Phase 4: User Story 2 - Retain all legacy data (Priority: P1)

**Goal**: Preserve every legacy SQLite row and Arango document while repeat exports replace only the new matching keyed record.

**Independent Test**: Seed temporary SQLite and Arango fakes with legacy duplicates and unrelated records, export the same identity repeatedly, and compare every legacy identifier and value.

### Tests for User Story 2

- [X] T006 [P] [US2] Add temporary SQLite and Arango-fake tests for first writes, repeat replacement, changed identities, legacy duplicates, and unrelated records in `tests/unit/db/sle_window_summary/test_backend_preservation.py`. Add a router test that proves both strategies avoid RedisJSON writes in `tests/unit/test_router.py`. Prerequisites: T001, T004.

### Implementation for User Story 2

- [X] T007 [US2] Add deterministic keyed replacement for the exact SLE identities in `src/foundation/support/refactors/sqlite_database_writer.py`; preserve legacy row identifiers and values. Prerequisite: T006.
- [X] T008 [US2] Add deterministic document keys and replacement for the exact SLE identities in `src/foundation/persistence/db/writers/arango_writer.py`; preserve legacy UUID documents and values. Prerequisite: T006.

**Checkpoint**: Repeated exports replace only the new keyed record, legacy records remain unchanged, and the router emits no RedisJSON write.

## Phase 5: User Story 3 - Preserve valid values and reject incomplete identity (Priority: P1)

**Goal**: Accept empty impact strings, reject invalid identities, and validate every row before either backend writes.

**Independent Test**: Check all four empty/nonempty classifier and failure combinations, invalid identity types, and a mixed valid/invalid batch with zero writes.

### Tests for User Story 3

- [X] T009 [US3] Test all four empty/nonempty classifier and failure combinations, missing or invalid values, nonnumeric or nonfinite or reversed boundaries, conflicting response dimensions, and zero writes to both backends for a mixed batch in `tests/unit/db/sle_window_summary/test_export_identity.py`. Prerequisites: T004, T007, T008.

### Implementation for User Story 3

- [X] T010 [US3] Validate required source strings and finite, nonnegative returned boundaries with `end` not before `start` in `src/foundation/support/refactors/endpoint_primary_key_strategies.py`; accept `""` only for string `classifier` and `failure`, without coercion or fabricated values. Prerequisite: T009.
- [X] T011 [US3] Build and validate every row identity before any persistence call in `src/operations/exporting/export/endpoint_family_exporter.py`; reject the full batch before writes when any row is invalid. Prerequisite: T010.

**Checkpoint**: Invalid data causes no partial writes, empty impact strings remain unchanged, and valid response content remains intact.

## Phase 6: Polish and Scoped Gates

**Purpose**: Add the issue-specific release note and run focused checks after all story tasks.

- [X] T012 [P] Add the detailed persistence rule to `documentation/CONTRIBUTING-MistHelper.md`, add one README paragraph after the menu 307 row, and add one `###` heading with a change bullet naming issues #4347 and #4348 in `changelog.d/issue-4347-sle-window-summary-keys.md`. Limit README text to same-window replacement and legacy row/document preservation. Do not edit WAN content, menu titles, or operation counts.
- [X] T013 Run the focused regression suite under `tests/unit/db/sle_window_summary/` and `tests/guardrails/test_endpoint_catalog.py`, with no live or production access. Prerequisites: T007, T008, T011, T012.
  ```sh
  python -m pytest \
    tests/unit/db/sle_window_summary \
    tests/guardrails/test_endpoint_catalog.py \
    tests/unit/test_router.py \
    tests/unit/export/test_endpoint_family_exporter.py \
    tests/unit/refactors/test_sqlite_database_writer.py \
    tests/unit/arango_indexes/test_preservation.py \
    tests/unit/db/test_database_schema_utils.py -q
  ```
- [X] T014 Run Ruff and Black checks on the Python targets below, including `src/foundation/support/refactors/endpoint_primary_key_strategies.py`, then run STE lint on every changed Markdown file. Prerequisite: T013.
  ```sh
  python -m ruff check \
    src/foundation/support/refactors/endpoint_primary_key_strategies.py \
    src/operations/exporting/export/endpoint_family_exporter.py \
    src/foundation/support/refactors/sqlite_database_writer.py \
    src/foundation/persistence/db/writers/arango_writer.py \
    tests/unit/db/sle_window_summary/test_export_identity.py \
    tests/unit/db/sle_window_summary/test_backend_preservation.py \
    tests/unit/test_router.py \
    tests/unit/refactors/test_sqlite_database_writer.py \
    tests/unit/arango_indexes/test_preservation.py \
    tests/guardrails/test_endpoint_catalog.py
  python -m black --check \
    src/foundation/support/refactors/endpoint_primary_key_strategies.py \
    src/operations/exporting/export/endpoint_family_exporter.py \
    src/foundation/support/refactors/sqlite_database_writer.py \
    src/foundation/persistence/db/writers/arango_writer.py \
    tests/unit/db/sle_window_summary/test_export_identity.py \
    tests/unit/db/sle_window_summary/test_backend_preservation.py \
    tests/unit/test_router.py \
    tests/unit/refactors/test_sqlite_database_writer.py \
    tests/unit/arango_indexes/test_preservation.py \
    tests/guardrails/test_endpoint_catalog.py
  ste-linter --config .ste-linter.toml --min-score 80 \
    README.md \
    documentation/CONTRIBUTING-MistHelper.md \
    specs/numbered/0/0/1/1/4/3/4/2/4347-sle-window-summary-keys/spec.md \
    specs/numbered/0/0/1/1/4/3/4/2/4347-sle-window-summary-keys/plan.md \
    specs/numbered/0/0/1/1/4/3/4/2/4347-sle-window-summary-keys/tasks.md \
    specs/numbered/0/0/1/1/4/3/4/2/4347-sle-window-summary-keys/design/checklists/requirements.md \
    specs/numbered/0/0/1/1/4/3/4/2/4347-sle-window-summary-keys/design/data-model.md \
    specs/numbered/0/0/1/1/4/3/4/2/4347-sle-window-summary-keys/design/quickstart.md \
    specs/numbered/0/0/1/1/4/3/4/2/4347-sle-window-summary-keys/design/research.md \
    changelog.d/issue-4347-sle-window-summary-keys.md
  ```
- [X] T015 Review the final diff and confirm no unrelated endpoint, identity, migration, or query behavior changed. Confirm the scoped README paragraph does not alter current WAN content and record that the #4619 response-refusal paragraph must be preserved during reconciliation. Do not rebase, push, or create a PR before the required scope report.

## Dependencies and Execution Order

### Phase Dependencies

- Setup has no task prerequisite and must finish before implementation.
- No new foundational code is required.
- User Story 1 depends on T001 and completes before User Story 2.
- User Story 2 depends on User Story 1 and completes before User Story 3.
- User Story 3 depends on the identity and persistence behavior from the earlier stories.
- Polish tasks depend on the story tasks listed in each task description.

### Task Dependency Graph

```text
T001 → T002 → T003
T003 → T004 and T005
T004 → T006
T006 → T007 and T008
T004 + T007 + T008 → T009 → T010 → T011
T012 has no prerequisite and can run in parallel with story work.
T007 + T008 + T011 + T012 → T013 → T014 → T015
```

### Parallel Opportunities

- T002 can run with other independent test preparation after T001.
- T007 and T008 can run in parallel after T006 because they modify different writer files.
- The identity and backend test modules are separate files under `tests/unit/db/sle_window_summary/`.
- Complete each story checkpoint before starting the next story.

## Implementation Strategy

### Implementation Order

1. Complete T001 and T002.
2. Complete T003 through T005 and verify the User Story 1 checkpoint.
3. Complete T006 through T008 and verify the User Story 2 checkpoint.
4. Complete T009 through T011 and verify the User Story 3 checkpoint.
5. Complete T012 through T015 and report the tested patch scope without pushing or opening a PR.

### Incremental Delivery

1. Complete User Story 1 for exact identities and stable content updates.
2. Complete User Story 2 for SQLite and Arango replacement with legacy preservation.
3. Complete User Story 3 for strict identity validation and all-batch failure safety.
4. Complete the release note and scoped gates.

## Notes

- Keep all work below the existing feature route. The feature root has four direct children, and `design/` has four direct children.
- Adding `tests/unit/db/sle_window_summary/` makes five direct children under `tests/unit/db/`.
- Keep the new test directory within that limit. Use only the two listed test modules.
- `specs/` has 795 direct children, and `changelog.d/` has 272 direct children. Record both as separate process-folder remediation work. Do not restructure either directory here.
- The user granted a scoped README handover. Preserve the existing WAN content and the README paragraph proposed by PR #4619.
- Do not add a migration, optional query parameter, identity field, or RedisJSON write.
- Recheck PR #4358 ownership before implementation. Do not edit any file that it owns.
- Do not commit, rebase, push, create a PR, merge, or modify issues before the final scope and validation report.
