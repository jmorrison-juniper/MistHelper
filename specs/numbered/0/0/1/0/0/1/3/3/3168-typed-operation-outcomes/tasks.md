# Tasks: Typed operation outcome contract

**Input**: [spec.md](spec.md), [plan.md](plan.md), and `design/`.
**Boundary**: Contract batch only. Part of #3168.

## Phase 1: Setup

- [x] T001 Confirm the current base and preserved draft in `design/research.md`. (delivered: design/research.md)
- [x] T002 Record serial migration and the next batch in `plan.md`. (delivered: plan.md)

## Phase 2: Shared Contract

- [x] T003 Define field and state semantics in `design/contracts/handler.md`. (delivered: design/contracts/handler.md)

## Phase 3: User Story 1 - Preserve the Result

**Goal**: Preserve each explicit state independently of message wording.
**Independent test**: Construct all states and serialize their fields.

- [x] T004 [US1] Test four states, message variants, and serialization. (delivered: tests/unit/dataclasses/test_operation_outcome.py)
- [x] T005 [US1] Add frozen, slotted `OperationOutcome`. (delivered: src/foundation/models/operation_outcome.py)

## Phase 4: User Story 2 - Reject Invalid Results

**Goal**: Reject invalid states, malformed text, and field mutation.
**Independent test**: Verify exact error types and unchanged valid fields.

- [x] T006 [US2] Test invalid states, text types, blank text, and immutability. (delivered: tests/unit/dataclasses/test_operation_outcome.py)
- [x] T007 [US2] Validate state and text. (delivered: src/foundation/models/operation_outcome.py)

## Phase 5: Documentation and Verification

- [x] T008 [P] Add the contract release note. (delivered: changelog.d/issue-3168-typed-operation-outcomes.md)
- [x] T009 Run the commands in `design/quickstart.md` and record results. (delivered: analysis.md)
- [x] T010 Verify unchanged portal classification and the migration boundary. (delivered: analysis.md)

## Dependencies

T003 requires T001 and T002.
T004 and T005 require T003.
T006 and T007 require T005.
T008 requires T003 and can run beside model implementation.
T009 requires T004 through T008.
T010 requires T009.

Both stories share one model and test file. Do not edit them in parallel.
Implement the complete small contract, then verify both stories together.
Producer migration and portal replacement are later batches, not unchecked
tasks that this contract PR claims to complete.

## Phase 6: Serial Producer Batch 1 - PSK Hygiene

**Goal**: Give menu 274 an explicit outcome without changing portal classification.
**Independent test**: The PSK hygiene unit tests check completed, no-output, missing-input, failed export, and propagated fetch and export exceptions.

- [x] T011 [US1] Record the current handler inventory and caller contracts in `design/research.md`.
- [x] T012 [US1] Test PSK outcome states and preserved exceptions in `tests/unit/reports/psk_hygiene/test_operation.py`.
- [x] T013 [US1] Return `OperationOutcome` from the PSK handler in `src/mist/intelligence/reports/psk_hygiene/operation.py`.
- [x] T014 [P] [US1] Document the bounded migration in `plan.md`, `design/contracts/handler.md`, and `design/quickstart.md`.
- [x] T015 [P] [US1] Add the PSK outcome release note in `changelog.d/issue-3168-psk-hygiene-outcome.md`.
- [ ] T016 [US1] Record validation and the unchanged portal boundary in `analysis.md`.

T011 establishes the current scope. T012 precedes T013. T014 and T015 can run beside the implementation. T016 depends on all earlier tasks.
