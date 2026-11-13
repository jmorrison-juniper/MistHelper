# Tasks: Reject Profiles from Failed Responses

**Input**: Numeric record at `specs/numbered/0/0/1/2/1/2/2/4/4564-wan-vpn-profile-503/`.

**Prerequisites**: `plan.md` and `spec.md`. Supporting documents are in `design/`.

## Phase 1: Setup

No project setup is required. The existing Python environment and test structure support this change.

## Phase 2: Foundational

No shared infrastructure change is required.

## Phase 3: User Story 1 - Use Profiles from Successful Requests (Priority: P1)

**Goal**: Keep response data from failed requests out of the WAN VPN workflow.

**Independent Test**: Mock an HTTP 503 response with a valid-looking profile array. Verify that the builder returns no profiles and does not create a VPN.

### Tests for User Story 1

- [x] T001 [US1] Add a native SDK HTTP 503 response regression test in `tests/unit/test_wan_vpn_builder.py`.

### Implementation for User Story 1

- [x] T002 [US1] Reject unsuccessful SDK responses before reading profile data in `src/operations/wan/wan_vpn_builder.py`.
- [x] T003 [P] [US1] Add the issue release note in `changelog.d/issue-4564-wan-vpn-profile-503.md`.

## Phase 4: Polish and Verification

- [x] T004 Run the WAN VPN builder unit tests and applicable lint, format, and documentation checks for the changed files.

## Dependencies and Execution Order

- T001 precedes T002 so the regression test proves the failure before the code fix.
- T003 can run independently because it changes a separate file.
- T004 follows T001, T002, and T003.

## Parallel Opportunities

- T003 can run in parallel with T001 and T002.

## Implementation Strategy

1. Add and run the failing HTTP 503 regression test.
2. Reject unsuccessful responses before the builder reads their data.
3. Add the issue release note.
4. Run the independent test and quality checks.

The MVP is User Story 1. Its acceptance criteria are the failed-response rejection and the preserved successful-response behavior.
