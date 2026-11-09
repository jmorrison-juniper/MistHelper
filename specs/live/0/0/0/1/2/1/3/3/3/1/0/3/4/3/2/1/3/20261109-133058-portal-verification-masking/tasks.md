# Tasks: Portal verification masking

## Phase 1: Setup

- [x] T001 Check live ownership for `web_portal/services/operation.py`, `web_portal/static/js/operations.js`, and dedicated test paths.

## Phase 2: Foundation

- [x] T002 Record scope and privacy limits in `spec.md` and `plan.md` within this feature directory.

## Phase 3: User Story 1

**Goal**: Mask verification display without changing validation or submission.
**Independent test**: Render the actual browser control and dispatch a synthetic answer to a mocked executor.

- [x] T003 [P] [US1] Add metadata and unchanged-text unit tests in `tests/unit/web_portal/verification_masking/test_controls.py`.
- [x] T004 [P] [US1] Add an offline browser journey in `tests/e2e/web_portal/verification_masking/test_submission.py`.
- [x] T005 [US1] Add the password display override in `web_portal/services/operation.py` and honor it in `web_portal/static/js/operations.js`.

## Phase 4: Validation and local delivery

- [x] T006 Add the unique fragment `changelog.d/2026-11-09-portal-verification-masking.md`.
- [x] T007 Run focused tests and applicable local gates for the changed production and test paths.
- [x] T008 Compare `spec.md`, `plan.md`, and `tasks.md`, then record results in `analysis.md`.
- [x] T009 Commit the explicit feature manifest locally and report the commit without publication.

## Dependencies

T001 precedes T002. T002 precedes T003 and T004. Both tests precede T005.
T005 precedes T006 and T007. T007 precedes T008. T006 and T008 precede T009.

## Parallel opportunities

T003 and T004 affect separate dedicated files and can proceed independently.
One agent performs this small change to limit cost.

## Implementation strategy

Complete the single story with synthetic input first.
Keep intermediate work uncommitted. Publish nothing while the serial slot and security publication remain held.
