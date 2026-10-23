# Tasks: Reject Conflicting Mist Token Values

**Input**: Numeric record at `specs/numbered/0/0/0/4/2/4/2/1/2861-token-conflict/`.

**Prerequisites**: `plan.md`, `spec.md`, and `design/quickstart.md`.

## Phase 1: Setup

**Purpose**: Confirm the bounded issue scope and existing code paths.

- [x] T001 Review approved #2861 token policy and active PR file ownership in `specs/numbered/0/0/0/4/2/4/2/1/2861-token-conflict/spec.md` (delivered: `spec.md`).

## Phase 2: Foundational

**Purpose**: Define normalization and refusal behavior before authentication.

- [x] T002 Record token-list normalization and the no-network boundary in `specs/numbered/0/0/0/4/2/4/2/1/2861-token-conflict/design/data-model.md` (delivered: `design/data-model.md`).

## Phase 3: User Story 1 - Prevent ambiguous Mist identity (Priority: P1)

**Goal**: Reject conflicting token variables without hiding a valid single-token configuration.

**Independent Test**: Run the credential preflight unit tests. Each token input case must pass without a Mist API call.

### Tests and implementation

- [x] T003 [US1] Normalize both token variables, reject differing non-empty lists, and select a usable canonical or legacy list in `MistHelper.py` (delivered: `MistHelper.py`).
- [x] T004 [US1] Cover conflicts, equal values, either variable alone, delimiter-only canonical input, login mode, secret redaction, and refusal before organization or session setup in `tests/unit/test_credential_preflight.py` (delivered: `tests/unit/test_credential_preflight.py`).
- [x] T005 [P] [US1] Record the user-visible refusal in `changelog.d/issue-2861-mist-token-conflict.md` (delivered: `changelog.d/issue-2861-mist-token-conflict.md`).

## Phase 4: Polish and Validation

**Purpose**: Verify the delivered scope and quality gates.

- [x] T006 Run the quickstart checks and the test-quality ratchet for the committed test change in `specs/numbered/0/0/0/4/2/4/2/1/2861-token-conflict/design/quickstart.md` (delivered: `design/quickstart.md`).
- [x] T007 Add the reviewer requirements checklist in `specs/numbered/0/0/0/4/2/4/2/1/2861-token-conflict/design/checklists/requirements.md` (delivered: `design/checklists/requirements.md`).

## Dependencies and Execution Order

- T001 and T002 establish scope and behavior before the story tasks.
- T003 and T004 are coupled through the same token parser and test contract.
- T005 is independent after the behavior is defined.
- T006 and T007 depend on the source, tests, and documentation.

## Parallel Opportunities

- T005 can proceed while T003 and T004 are implemented, because it changes a separate file.
- No parallel source changes are planned.

## Implementation Strategy

Deliver User Story 1 as the minimum complete slice. Validate local behavior and quality gates. Keep the branch local until the coordinator approves the final review artifacts and pull request body.
