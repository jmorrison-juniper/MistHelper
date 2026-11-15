# Tasks: Timestamp validation

**Input**: [spec.md](spec.md), [plan.md](plan.md), and `design/`.

## Phase 1: Setup

- [x] T001 Prepare the local environment for `tests/guardrails/test_spec_route_contract.py`. (delivered: tests/guardrails/test_spec_route_contract.py)

## Phase 2: Foundational

- [x] T002 Reproduce issue #4796 against `.specify/scripts/powershell/spec-route.ps1`. (delivered: .specify/scripts/powershell/spec-route.ps1)

## Phase 3: User Story 1 - Reject invalid timestamps

**Goal**: Reject invalid timestamps without creating a feature destination.
**Independent Test**: Invalid hours, minutes, seconds, and dates fail.

- [x] T003 [US1] Add invalid time boundary cases in `tests/guardrails/test_spec_route_contract.py`. (delivered: tests/guardrails/test_spec_route_contract.py)
- [x] T004 [US1] Reject normalized timestamps in `.specify/scripts/powershell/spec-route.ps1`. (delivered: .specify/scripts/powershell/spec-route.ps1)

## Phase 4: User Story 2 - Preserve valid timestamp routes

**Goal**: Retain routes for valid labels.
**Independent Test**: Boundary routes match independently calculated values.

- [x] T005 [US2] Add valid time boundary cases in `tests/guardrails/test_spec_route_contract.py`. (delivered: tests/guardrails/test_spec_route_contract.py)

## Phase 5: Polish

- [x] T006 Add the issue release fragment in `changelog.d/issue-4796-timestamp-validation.md`. (delivered: changelog.d/issue-4796-timestamp-validation.md)
- [x] T007 Run the route contract and quality checks for `tests/guardrails/test_spec_route_contract.py`. (delivered: tests/guardrails/test_spec_route_contract.py)
- [x] T008 Run an isolated container smoke test for `.specify/scripts/powershell/spec-route.ps1`. (delivered: .specify/scripts/powershell/spec-route.ps1)

## Dependencies and Execution Order

Setup precedes the reproduction. T003 precedes T004. T005 verifies route preservation after T004.
The release fragment can be written independently. The final checks follow the implementation.
The MVP is User Story 1. User Story 2 verifies compatibility.

## Parallel Opportunities

T006 can run independently of the route changes. The test edits share a file and run serially.

## Implementation Strategy

Reproduce the failure, add boundary cases, repair validation, and verify both stories.
