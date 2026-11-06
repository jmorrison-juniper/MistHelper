# Tasks: Preserve Rate-Limit State on HTTP Failure

**Input**: Plan and design documents in `specs/numbered/0/0/1/2/1/4/2/1/4611-rate-limit-refresh/`.

**Prerequisites**: `spec.md`, `plan.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`.

## Phase 1: Setup

**Purpose**: Confirm the isolated test environment and exact file scope.

- [X] T001 Confirm the worktree is clean outside the issue-owned files and verify `src/foundation/support/utils/rate_limiting.py` and `tests/unit/test_rate_limiting.py` remain unowned by an open pull request.

## Phase 2: Foundational

**Purpose**: Prepare local native SDK response fixtures without network access.

- [X] T002 Add a local native SDK response builder in `tests/unit/test_rate_limiting.py` for missing, failed, and successful HTTP responses.

## Phase 3: User Story 1 - Preserve the Last Valid Quota (Priority: P1)

**Goal**: Keep cached quota state unchanged after a failed usage response.

**Independent Test**: Run the native HTTP 403 and HTTP 503 cases in `tests/unit/test_rate_limiting.py` and verify that each case fails before the fix and passes after it.

### Tests for User Story 1

- [X] T003 [US1] Add native missing-response, HTTP 403, and HTTP 503 tests in `tests/unit/test_rate_limiting.py` that assert all cache fields stay unchanged and a warning appears.

### Implementation for User Story 1

- [X] T004 [US1] Validate the SDK HTTP status before reading response data in `src/foundation/support/utils/rate_limiting.py`, and preserve the cache on missing or non-success responses.

## Phase 4: User Story 2 - Refresh Quota After Success (Priority: P2)

**Goal**: Keep successful usage refresh behavior unchanged.

**Independent Test**: Run the native HTTP 200 case in `tests/unit/test_rate_limiting.py` and verify returned usage values and refresh metadata enter the cache.

### Tests for User Story 2

- [X] T005 [US2] Add a native HTTP 200 success test in `tests/unit/test_rate_limiting.py` that checks usage, limit, refresh time, request count, and initialization state.

### Implementation for User Story 2

- [X] T006 [US2] Confirm the accepted-status path retains the existing cache updates in `src/foundation/support/utils/rate_limiting.py`.

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Record the behavior and run the required local gates.

- [X] T007 [P] Add the issue-specific release note in `changelog.d/issue-4611-rate-limit-refresh-http-status.md`.
- [X] T008 Run the focused tests, format and lint checks, and test-quality ratchet for `tests/unit/test_rate_limiting.py`.
- [X] T009 Verify the native response tests make no network request and confirm the explicit file manifest before commit in `tests/unit/test_rate_limiting.py`.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup**: T001 confirms that the intended files remain safe to edit.
- **Foundational**: T002 provides response objects for both user stories.
- **User Story 1**: T003 must fail before T004 changes production behavior.
- **User Story 2**: T005 and T006 verify that success still refreshes the cache.
- **Polish**: T007 through T009 follow both stories.

### User Story Dependencies

- **User Story 1 (P1)**: Depends on the response fixture. It has no dependency on User Story 2.
- **User Story 2 (P2)**: Uses the same fixture and verifies the existing successful behavior.

### Parallel Opportunities

- T007 changes a separate changelog file and can run alongside test work after ownership confirmation.
- T008 and T009 require the completed source and tests.

## Implementation Strategy

### MVP First

1. Add native failure tests and verify that they fail against the current implementation.
2. Reject failed statuses before any cache write.
3. Run the independent failure tests and confirm that the cache remains unchanged.

### Incremental Delivery

1. Complete User Story 1 as the minimum safe fix.
2. Complete User Story 2 to prove successful refresh behavior remains intact.
3. Add the release note and run the documented quality gates.

## Notes

- Do not use Mist credentials or make a live request.
- Preserve the existing test-quality baseline.
- Keep `.specify/feature.json` unchanged because it selects another feature.
