---

description: "Task list for site lock refusal logging"

---

# Tasks: Site Lock Refusal Logging

**Input**: Numeric record at `specs/numbered/0/0/1/0/3/0/1/1/3506-site-lock-refusal-logging/`.

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](design/research.md), [site-lock-logging.md](design/contracts/site-lock-logging.md), [quickstart.md](design/quickstart.md).

**Tests**: Required by the specification and project constitution.

**Organization**: Tasks follow the independent P1 user story.

## Phase 1: Setup

**Purpose**: Confirm the scope and existing test boundary.

- [x] T001 Check the current lock route and refusal contract in `src/interfaces/portals/upgrade_portal/app/routes/select.py`.
- [x] T002 [P] Check the current lock refusal rules in `src/interfaces/portals/upgrade_portal/runtime/lock.py`.

## Phase 2: Foundational

**Purpose**: Establish structural guard expectations before implementation.

- [x] T003 Add a counting guard and missing-log failure proof in `tests/guardrails/test_site_lock_refusal_logging.py`.

## Phase 3: User Story 1 - Diagnose a refused site lock (Priority: P1)

**Goal**: Give engineers reliable lock action and refusal records without changing lock behavior or exposing sensitive data.

**Independent Test**: Run the contract and unit lock tests, then run the structural guard. Check structured record values and unchanged response outcomes.

### Tests for User Story 1

- [x] T004 [P] [US1] Assert route refusal and success records in `tests/contract/upgrade_portal/test_lock.py`.
- [x] T005 [P] [US1] Assert the six previously silent lock-module refusals in `tests/unit/upgrade_portal/test_lock.py`.

### Implementation for User Story 1

- [x] T006 [US1] Add structured action and refusal records to `src/interfaces/portals/upgrade_portal/app/routes/select.py`.
- [x] T007 [US1] Add structured records before the six silent refusal raises in `src/interfaces/portals/upgrade_portal/runtime/lock.py`.

## Phase 4: Polish and Cross-Cutting Concerns

**Purpose**: Validate the complete behavior and publish the issue note.

- [x] T008 [P] Add the issue release note in `changelog.d/issue-3506-site-lock-refusal-logging.md`.
- [ ] T009 Run the documented tests and applicable lint, format, type, complexity, symbol, and security gates.
- [ ] T010 Track a separate issue to reduce the existing direct-file count in `changelog.d/` after release processing.
- [ ] T011 Complete the remote deployment pipeline only after the user authorizes remote and production actions.

## Dependencies and Execution Order

### Phase Dependencies

- Setup tasks need no prior task.
- Foundational task T003 follows the setup checks and blocks implementation.
- User Story 1 follows T003. Its two test tasks can run in parallel because they edit different files.
- Route and lock module changes can run in parallel after the guard and tests define the expected records.
- Polish tasks follow implementation.

### User Story Dependencies

- User Story 1 has no dependency on another story.

### Parallel Opportunities

- T001 and T002 can run in parallel.
- T004 and T005 can run in parallel.
- T006 and T007 can run in parallel after the expected behavior is established.
- T008 can run in parallel with source and test changes.

## Parallel Example: User Story 1

```text
Task: Add route log assertions in tests/contract/upgrade_portal/test_lock.py
Task: Add lock-module log assertions in tests/unit/upgrade_portal/test_lock.py
```

## Implementation Strategy

Complete the P1 story as one increment. Run the contract and unit tests, then the counting guard. Run all applicable local quality gates before the change is considered complete.

## Notes

- Each task names its file path.
- Keep tests based on fake lock stores.
- Do not call Mist Cloud or use production credentials or stores.
