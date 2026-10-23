# Tasks: WAN VPN Update Response

**Input**: `specs/numbered/0/0/1/2/0/0/0/4/4379-wan-vpn-update-response/spec.md`

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/contracts/update-response.md`, and `design/quickstart.md`

## Phase 1: Setup

No project setup is required. Use the repository test environment and existing Mist SDK dependency.

## Phase 2: Foundational

No shared infrastructure is required. The change uses the current VPN manager and SDK response.

## Phase 3: User Story 1 - Trust VPN update results (Priority: P1)

**Goal**: Report VPN updates as successful only when Mist returns a 2xx status.

**Independent Test**: Mock the SDK read and update calls. Verify that rejected responses produce no success message and accepted responses retain the current path count.

- [x] T001 [US1] Add tests for mocked HTTP refusal, missing status, accepted responses, SDK exceptions, and stopping later updates in `tests/unit/test_wan_hub_group_manager.py`. (delivered: `tests/unit/test_wan_hub_group_manager.py`)
- [x] T002 [US1] Check `updateOrgVpn` status and fail non-2xx responses in `src/operations/wan/wan_hub_group_manager.py`. (delivered: `src/operations/wan/wan_hub_group_manager.py`)
- [x] T003 [P] [US1] Add the issue release note in `changelog.d/issue-4379-wan-vpn-update-response.md`. (delivered: `changelog.d/issue-4379-wan-vpn-update-response.md`)

## Phase 4: Polish

- [x] T004 Run the focused tests, compile, lint, format, and applicable type checks. Record exact results in `specs/numbered/0/0/1/2/0/0/0/4/4379-wan-vpn-update-response/design/quickstart.md`. (delivered: `specs/numbered/0/0/1/2/0/0/0/4/4379-wan-vpn-update-response/design/quickstart.md`)

## Dependencies & Execution Order

- T001 must fail before T002 changes the manager.
- T003 has no dependency on the test or source tasks.
- T004 depends on T001, T002, and T003.

## Parallel Opportunities

- T003 can run in parallel with T001 because it changes a separate file.

## Implementation Strategy

Complete User Story 1 as the full scope. Add tests first, verify that the refusal test fails, implement the status check, then run all targeted gates.
