# Tasks: Nested JSON Result Preview

**Input**: `specs/numbered/0/0/1/1/2/1/2/1/4036-fix-nested-json-preview/spec.md`

**Plan**: `specs/numbered/0/0/1/1/2/1/2/1/4036-fix-nested-json-preview/plan.md`

**Supporting design**: `design/research.md`, `design/data-model.md`, and `design/quickstart.md`

**Scope**: Route disambiguation, synthetic JSON route and browser coverage, SQLite and path-security compatibility, unchanged output discovery, and the issue-specific changelog fragment.

## Phase 1: Setup

**Purpose**: Confirm the existing route and test baseline before edits.

- [X] T001 Review route selection in `web_portal/routes/data.py` and existing coverage in `tests/unit/web_portal/test_preview_row_order.py` and `tests/unit/test_data_browser_path_guard.py`.

## Phase 2: Foundational

**Purpose**: No new infrastructure or dependencies are required. Flask and pytest already exist.

## Phase 3: User Story 1 - Inspect a nested JSON result (Priority: P1)

**Goal**: Preview a selected nested JSON file through the existing Results workflow.

**Independent Test**: Use synthetic `mib_generator/allowlist.json` and `mib_generator/oid_assignments.json` files. Confirm each preview shows its own contents and each download retains its source bytes.

### Tests and implementation

- [X] T002 [P] [US1] Add synthetic nested JSON route tests for both menu 243 paths in `tests/unit/web_portal/test_preview_row_order.py`. Assert preview data, pagination, and unchanged download contents.
- [X] T003 [US1] Update selection in `web_portal/routes/data.py` to retain the complete nested file path and use table selection only for an explicit SQLite file-and-table request. Retain the existing path guard and denial behavior.
- [X] T007 [US1] Add a browser regression in `tests/e2e/web_portal/test_operation_results_table.py`. Preview a temporary nested JSON file through the Results panel and confirm its contents without live Mist calls.

## Phase 4: User Story 2 - Preserve useful JSON errors (Priority: P2)

**Goal**: Distinguish invalid JSON content from a missing result.

**Independent Test**: Request separate malformed and absent nested files with synthetic fixtures.

### Tests and error behavior

- [X] T004 [US2] Add nested malformed-JSON and missing-file route assertions to `tests/unit/web_portal/test_preview_row_order.py`. Confirm each response keeps its distinct error and does not expose an internal path.

## Phase 5: User Story 3 - Retain existing preview protections (Priority: P2)

**Goal**: Retain SQLite table previews and existing file-access denials unchanged.

**Independent Test**: Use a synthetic nested SQLite database to verify its table and missing-table responses. Run the existing path-guard tests and confirm denied paths expose no file contents.

### Tests and compatibility checks

- [X] T005 [US3] Add nested SQLite table and missing-table route assertions to `tests/unit/web_portal/test_preview_row_order.py`. Run `tests/unit/test_data_browser_path_guard.py` and `tests/unit/test_operation_output_file_discovery.py` to verify path denials and unchanged output membership.

## Phase 6: Polish and cross-cutting concerns

**Purpose**: Add the issue-specific user-facing release note.

- [X] T006 [P] Add `changelog.d/issue-4036-nested-json-preview.md` with a `### Fixed` heading and one bullet naming issue #4036 and nested JSON preview in the Results panel.

## Dependencies and execution order

### Phase dependencies

- Setup must finish before implementation tasks.
- No foundational infrastructure is needed.
- User Story 1 implements the MVP after Setup.
- User Story 2 verifies the JSON error distinction after the route correction.
- User Story 3 checks compatibility after the route change.
- The changelog task can run in parallel with the route and test work after Setup.

### Task dependencies

- T002 follows T001 and precedes T003 so the regression test proves the route defect before its correction.
- T003 follows T002.
- T007 follows T003 because it verifies the corrected route through the Results panel.
- T004 follows T003 because it verifies the corrected nested JSON route errors.
- T005 follows T004 because both tasks edit the same test file.
- T006 follows T001 and is independent of T002 through T005.

## Parallel opportunities

- After T001, work on T002 and T006 in parallel because they change different files.
- Do not parallelize T002, T004, and T005 because they change `tests/unit/web_portal/test_preview_row_order.py`.
- Complete T003 before T004 and T005 so route checks cover the correction.

## Implementation strategy

### MVP first

1. Complete T001.
2. Add and run the synthetic route regression in T002.
3. Implement the route correction in T003.
4. Verify User Story 1 independently with its synthetic previews and downloads.

### Incremental delivery

1. Complete T004 to verify nested JSON errors.
2. Complete T005 to verify nested SQLite behavior, output discovery, and path denials.
3. Complete T006 to add the release fragment.
4. Retain output-list membership throughout the implementation.
