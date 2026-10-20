# Tasks: Preserve First Retry Failure Evidence

**Input**: Numeric record at `specs/numbered/0/0/0/4/2/0/0/2/2752-gateway-retry-evidence/`.

**Prerequisites**: `plan.md` and `spec.md`.

## Phase 1: Setup

**Purpose**: Record the bounded implementation and test scope.

- [x] T001 Confirm the source and test paths in `specs/numbered/0/0/0/4/2/0/0/2/2752-gateway-retry-evidence/plan.md` (delivered: `specs/numbered/0/0/0/4/2/0/0/2/2752-gateway-retry-evidence/plan.md`)

## Phase 2: User Story 1 - Diagnose a failed gateway read (Priority: P1)

**Goal**: Preserve the first request failure after a later retry fallback.

**Independent Test**: Mock each API method. Confirm the final retry diagnostic contains the first failure and the returned value remains unchanged.

### Tests

- [x] T002 [P] [US1] Add a mocked first-failure and fallback test in `tests/unit/api/test_api_fetch_utils.py` (delivered: `tests/unit/api/test_api_fetch_utils.py`).
- [x] T003 [P] [US1] Add a mocked first-failure and fallback test in `tests/unit/export/test_gateway_test_exporter.py` (delivered: `tests/unit/export/test_gateway_test_exporter.py`).

### Implementation

- [x] T004 [US1] Preserve the first request exception in gateway config retries in `src/mist/access/api/api_fetch_utils.py` (delivered: `src/mist/access/api/api_fetch_utils.py`).
- [x] T005 [US1] Preserve the first exception in synthetic test retries in `src/operations/exporting/export/gateway_test_exporter.py` (delivered: `src/operations/exporting/export/gateway_test_exporter.py`).
- [x] T006 [US1] Add the unique issue release note in `changelog.d/issue-2752-gateway-retry-evidence.md` (delivered: `changelog.d/issue-2752-gateway-retry-evidence.md`).

## Dependencies and Execution Order

- T002 and T003 can run in parallel because they edit different test files.
- T004 depends on T002. T005 depends on T003.
- T006 can run in parallel with the implementation tasks.
- Complete the user story after both tests pass and you verify each listed file.

## Implementation Strategy

1. Add mocked tests that fail when a later fallback replaces the first failure.
2. Update each retry helper to carry the first exception into its final diagnostic.
3. Run the targeted tests and the required local gates.
4. Keep successful values, failure values, retry counts, and backoff delays unchanged.
