# Tasks: Runtime Dependency Refresh

**Input**: Numeric record at `specs/numbered/0/0/1/2/1/4/4/2/4622-runtime-dependency-refresh/`.

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), `design/research.md`, `design/data-model.md`, and `design/quickstart.md`.

**Tests**: Use the existing dependency and SDK checks. Do not add test files.

## Phase 1: Setup

**Purpose**: Confirm the requested refresh and its boundaries.

No separate setup task is required. The parent owns the dependency changes.

## Phase 2: Foundational

**Purpose**: Resolve the dependency set and create consistent exports.

- [x] T001 Resolve the 23 requested runtime updates from `requirements.txt` in `uv.lock`, including required transitive packages. (delivered: `uv.lock`, commit `598a897`)
- [x] T002 Generate `requirements.txt` and `requirements-dev.txt` from `uv.lock`. (delivered: `requirements.txt`, `requirements-dev.txt`, commit `598a897`)

## Phase 3: User Story 1 - Use refreshed runtime packages (Priority: P1)

**Goal**: Install the requested runtime package versions from matching exports.

**Independent Test**: Pass the dependency export, lock, declaration parity, and SDK checks.

### Tests for User Story 1

- [x] T003 [US1] Validate exports, lock, declaration parity, and SDK compatibility with `tests/guardrails/test_dependency_export.py`, `tests/guardrails/test_dependency_lock_file.py`, `tests/guardrails/test_dependency_declaration_parity.py`, and `tests/integration/test_mistapi_sdk_compatibility.py`. Parent-reported result: 28 passed.

## Phase 4: User Story 2 - Keep platform support intact (Priority: P1)

**Goal**: Preserve all existing platform conditions and verify the completed refresh.

**Independent Test**: Confirm all 11 platform markers remain exact and all required validation checks pass.

### Validation for User Story 2

- [x] T004 [US2] Confirm all 11 platform markers and 107 retained pins remain exact in the exports from `uv.lock`. The new dateutil version replaces its `six` dependency with `tzdata`.
- [x] T005 [US2] Run database, dashboard, release-note, audit, package consistency, import, and Linux resolver checks for `uv.lock`, both dependency exports, and `changelog.d/issue-4622-runtime-dependency-refresh.md`. Parent-reported result: 316 passed, one skipped because the test requires pull request context. Audit, package consistency, imports, and Linux resolution passed.
- [x] T006 [P] [US2] Add the unique issue release note in `changelog.d/issue-4622-runtime-dependency-refresh.md`. (delivered: `changelog.d/issue-4622-runtime-dependency-refresh.md`, commit `598a897`)

## Phase 5: Polish and Release

**Purpose**: Publish the completed work after branch and check validation.

- [ ] T007 Rebase the feature branch on current `main` and open the pull request with `.github/PULL_REQUEST_TEMPLATE.md`. Include the test results and link issue #4622.
- [ ] T008 Enable squash auto-merge only after all required checks and CodeQL pass on the current `main` base. Check `.github/workflows/ci.yml` and `.github/workflows/codeql.yml` for the required workflows.

## Dependencies and Execution Order

### Phase Dependencies

- **Setup**: No separate task is required.
- **Foundational**: T001 precedes T002. Both tasks are complete in parent commit `598a897`.
- **User Story 1**: T003 follows T001 and T002.
- **User Story 2**: T004 follows T001 and T002. T005 follows T003 and T004. T006 is independent of test execution.
- **Release**: T007 follows T001 through T006. T008 follows T007 and green required checks.

### User Story Dependencies

- **User Story 1 (P1)**: Depends on the resolved lock and generated exports.
- **User Story 2 (P1)**: Depends on the same lock and exports. It can be checked independently from the installation story.

### Parallel Opportunities

- T006 can proceed independently from the validation tasks because it writes a separate release-note file.
- T004 can run alongside T003 after the lock and exports are ready.

## Implementation Strategy

### MVP

Use User Story 1 as the MVP. Its lock, exports, and 28 passing dependency and SDK tests are complete.

### Incremental Delivery

1. Complete dependency resolution and both exports.
2. Verify platform markers and the complete local validation set.
3. Rebase and publish the pull request.
4. Enable squash auto-merge only after required checks and CodeQL pass on current `main`.

## Notes

- The parent reports 344 passed tests and one skipped test across the final run.
- This agent created specification documents only. The parent owns dependency changes, validation, commit, pull request, and merge.
