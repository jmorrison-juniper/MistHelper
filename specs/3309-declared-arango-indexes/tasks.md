# Tasks: Declared ArangoDB indexes

**Input**: [spec.md](spec.md), [plan.md](plan.md), and the [design contract](design/contracts/indexes.md).

**Tests**: Required. Run the failing tests against the unchanged writer before implementation.

## Phase 1: Setup

- [x] T001 Verify the issue claim and exact file reservation. (delivered: `specs/3309-declared-arango-indexes/design/validation.md`)
- [x] T002 Complete the specification and checklist. (delivered: `specs/3309-declared-arango-indexes/spec.md`, `checklists/requirements.md`)
- [x] T003 Complete the plan, research, data model, and contract. (delivered: `specs/3309-declared-arango-indexes/plan.md`, `design/`)

## Phase 2: Foundational

- [x] T004 Add strict fake SDK handles and real writer construction. (delivered: `tests/unit/arango_indexes/fakes.py`, `conftest.py`)
- [x] T005 Record failing unchanged-writer index tests. (delivered: `tests/unit/arango_indexes/test_declared_indexes.py`)

## Phase 3: User Story 1 - Use the declared indexes

**Independent Test**: Compare exact ordered requests before import and zero repeated requests after a complete check.

- [x] T006 [US1] Test real strategies and declaration changes. (delivered: `tests/unit/arango_indexes/test_declared_indexes.py`)
- [x] T007 [US1] Add semantic normalization and index state classes. (delivered: `src/db/database_schema_utils.py`)
- [x] T008 [US1] Consume the strategy indexes through the existing collection path. (delivered: `src/db/arango_writer.py`)
- [x] T009 [US1] Test exact SDK requests and equal-index responses. (delivered: `tests/contract/test_arango_declared_indexes.py`)

## Phase 4: User Story 2 - Report a failure and retry

**Independent Test**: Fail an index, compare zero imports, then verify all unconfirmed retry requests.

- [x] T010 [US2] Test driver errors, transport errors, and retry. (delivered: `tests/unit/arango_indexes/test_retry_concurrency.py`)
- [x] T011 [US2] Add explicit diagnostics and complete-check confirmation. (delivered: `src/db/database_schema_utils.py`)
- [x] T012 [US2] Verify the existing single and dual router failure results. (delivered: `tests/contract/test_arango_declared_indexes.py`)
- [x] T013 [US2] Prove unchanged keys, values, counts, imports, and batching. (delivered: `tests/unit/arango_indexes/test_preservation.py`)

## Phase 5: User Story 3 - Coordinate concurrent writers

**Independent Test**: Block an initial request and verify one complete index request set across concurrent same-scope writers.

- [x] T014 [US3] Test concurrent writes, retry, and independent scopes. (delivered: `tests/unit/arango_indexes/test_retry_concurrency.py`)
- [x] T015 [US3] Share the guard and invalidate recreated collections. (delivered: `src/db/database_schema_utils.py`, `src/db/arango_writer.py`)

## Phase 6: Validation and delivery

- [x] T016 Prove equal-index reuse and the query plan in an owned store. (delivered: `tests/integration/test_arango_declared_indexes_live.py`)
- [x] T017 Update the database guide and release note. (delivered: `documentation/diagrams/core/database-strategy.md`, `changelog.d/issue-3309-declared-arango-indexes.md`)
- [x] T018 Record the local quality and writing results. (delivered: `specs/3309-declared-arango-indexes/design/validation.md`)
- [x] T019 Analyze requirement coverage. (delivered: `specs/3309-declared-arango-indexes/design/validation.md`)
- [ ] T020 Commit the verified exact file set locally and report the clean revision. The coordinator receives the receipt after verification.
- [ ] T021 Await the coordinator's verified-main grant before remote work. This task remains blocked until that explicit grant.
- [ ] T022 After the grant, rebase, repeat local evidence, complete the protected exact-head merge, and test the exact actual main revision.

## Dependencies & Execution Order

T004 requires the completed specification and plan.
T005 requires T004.
T007 and T008 require the failing unchanged-writer evidence from T005.
T009 requires the writer integration from T008.
T011 requires the failure tests from T010.
T014 requires the real writer fixture from T004.
T015 requires the concurrency tests from T014.
T016 and T018 require the complete implementation.
T020 requires local evidence and the final analysis.
T021 requires T020 and the separate coordinator grant.
T022 requires T021.

## Parallel Opportunities

The declared-index, failure, and preservation test files can progress independently after T004.
The quality checks and isolated database check can run independently after implementation.
Edits to the two production files remain sequential.

## Implementation Strategy

Complete the specification and the failing writer test first.
Implement the declared-index path and its complete-check cache.
Prove failure, retry, and shared-scope concurrency before local delivery.
Treat an unavailable live store as unmeasured.
Stop at the verified local commit until the coordinator grants remote work.
