# Tasks: Reject Failed HTTP Data in Rogue DHCP Scans

**Input**: Numeric record at `specs/numbered/0/0/1/2/1/2/2/0/4560-rogue-dhcp-http-response/`.

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, and `design/quickstart.md`.

## Phase 1: Setup

No project setup is required. The worktree environment is ready.

## Phase 2: Foundational

No shared infrastructure changes are required.

## Phase 3: User Story 1 - Trust only successful scan responses (Priority: P1)

**Goal**: Prevent failed Mist responses from becoming rogue DHCP findings.

**Independent Test**: Provide a mocked failed response with a valid-looking alarm. Verify that pagination does not read it and the scan reports the request failure.

### Tests for User Story 1

- [X] T001 [US1] Add mocked 4xx and 5xx response tests to `tests/unit/security/rogue_dhcp/test_scanner.py`. Verify that failed response data does not reach pagination and that a successful response still yields a finding. (delivered: `tests/unit/security/rogue_dhcp/test_scanner.py`)

### Implementation for User Story 1

- [X] T002 [US1] Validate SDK response status before pagination in `src/operations/protection/security/rogue_dhcp/scanner.py`. Preserve list-based test doubles and allow only integer 2xx statuses on SDK response objects. (delivered: `src/operations/protection/security/rogue_dhcp/scanner.py`)
- [X] T003 [P] [US1] Add the issue-specific release note to `changelog.d/issue-4560-rogue-dhcp-http-503-data.md`. (delivered: `changelog.d/issue-4560-rogue-dhcp-http-503-data.md`)
- [X] T004 [US1] Run the focused scanner tests, Ruff, and Black checks for the changed Python files. (verified: pytest, Ruff, and Black passed)
- [X] T005 [US1] Replace opaque full-pagination with per-page status and body validation. Add regression tests for a later 503 body, a malformed later body, and a successful later page. (verified: 43 scanner tests pass, and the installed SDK reproducer rejects the later 503 offline)
- [X] T006 [US1] Add operator-report tests for failed site names, incomplete exports, and incomplete empty results. (delivered: `tests/unit/security/rogue_dhcp/test_operation.py`)
- [X] T007 [US1] Mark partial exports as incomplete and do not report an incomplete empty scan as clean. (delivered: `src/operations/protection/security/rogue_dhcp/operation.py`)
- [X] T008 [US1] Run the focused scanner and operation tests. (verified: 58 tests passed)

## Dependencies & Execution Order

### Phase Dependencies

- Setup and foundational work have no tasks because this change needs no new infrastructure.
- User Story 1 tests come before the scanner change.
- The changelog fragment can be written in parallel with the test and scanner work.
- Final validation depends on the scanner change and the changelog fragment.

### User Story Dependencies

- User Story 1 is independent and is the full MVP.

### Parallel Opportunities

- T003 can run in parallel with T001 and T002 because it changes a separate file.

## Implementation Strategy

1. Add tests that fail for 4xx and 5xx responses.
2. Reject failed SDK responses before pagination.
3. Add tests that reject misleading messages for incomplete scans.
4. Mark partial findings as partial and suppress clean results when sites failed.
5. Add the issue-specific release note and run focused tests and Python quality checks.

## Notes

- Do not use a production credential or call Mist.
- The scanner must report request failures rather than present them as clean results.
