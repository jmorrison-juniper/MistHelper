# Tasks: Fail Closed on VPN Inventory Errors

**Input**: Numeric record for issue #4792.

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](design/research.md), [data-model.md](design/data-model.md), [quickstart.md](design/quickstart.md)

## Phase 1: Setup

**Purpose**: Confirm that the existing test setup can cover the issue without a live organization.

- [x] T001 Confirm the documented focused test module and synthetic-only scope in `design/quickstart.md` (delivered: `design/quickstart.md`).

## Phase 2: Foundational

**Purpose**: Preserve the existing SDK session and operator confirmation boundary.

- [x] T002 Confirm that the issue specification preserves the existing typed confirmation and forbids live Mist calls in `spec.md` (delivered: `spec.md`).

## Phase 3: User Story 1 - Protect VPN creation when inventory is incomplete (Priority: P1)

**Goal**: Stop the builder before the name prompt when a complete VPN inventory is unavailable, while allowing a complete empty inventory.

**Independent Test**: Use synthetic SDK responses to verify complete empty inventory, failed and malformed pages, pagination failure, and zero creation calls after an inventory failure.

### Tests for User Story 1

- [x] T003 [US1] Cover FR-001 and FR-005 with mocked tests for empty success, failed status, malformed data, pagination failure, and the stop-before-create path. Retain the duplicate-name test for FR-003 in `tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py` (delivered: `tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py`).

### Implementation for User Story 1

- [x] T004 [US1] Implement FR-001 by validating each VPN response page and distinguishing complete empty inventory from unavailable inventory in `src/operations/wan/wan_vpn_builder.py` (delivered: `src/operations/wan/wan_vpn_builder.py`).
- [x] T005 [US1] Implement FR-002 and preserve FR-004 by stopping before the name prompt and typed confirmation when VPN inventory is unavailable in `src/operations/wan/wan_vpn_builder.py` (delivered: `src/operations/wan/wan_vpn_builder.py`).
- [x] T006 [P] [US1] Add the issue-specific release note in `changelog.d/issue-4792-wan-vpn-list-failure.md` (delivered: `changelog.d/issue-4792-wan-vpn-list-failure.md`).

## Phase 4: Polish and Validation

**Purpose**: Verify the behavior and preserve the existing builder interface.

- [x] T007 Run the focused tests, compile check, Ruff, and Black commands from `design/quickstart.md` for the modified Python files (delivered: `tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py`).

## Dependencies and Execution Order

### Phase Dependencies

- **Setup**: Complete before user story work. Existing test infrastructure is used.
- **Foundational**: Complete before user story work. The Mist session and typed confirmation remain unchanged.
- **User Story 1**: Depends on Setup and Foundational. T003 must fail before T004 and T005 implement the fix. T006 can run in parallel with T003.
- **Polish**: Depends on all User Story 1 tasks.

### Parallel Opportunities

- T006 can run in parallel with T003 because it uses a different file.
- T004 and T005 both change the source module and must run in order.

### Parallel Example: User Story 1

```text
Task: Add mocked regression tests in tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py
Task: Add the issue-specific release note in changelog.d/issue-4792-wan-vpn-list-failure.md
```

## Implementation Strategy

Complete User Story 1 as the MVP. First prove the regression with mocks, then validate full VPN pagination and stop on incomplete inventory. Run the focused checks. Do not run live VPN integration tests.
