# Tasks: Site Lock Safety for Uncertain Submissions

**Input**: Numeric record at `/specs/numbered/0/0/1/0/4/4/0/1/3726-site-lock-safety/`.

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](design/research.md), [data-model.md](design/data-model.md), [submission certainty contract](design/contracts/submission-certainty.md), [quickstart.md](design/quickstart.md).

**Tests**: The user requested testing and repair. Write focused offline tests before changing behavior.

## Phase 1: Setup

**Purpose**: Confirm that the feature uses existing dependencies and test fixtures.

- [X] T001 Confirm that `pyproject.toml` and `requirements.txt` need no dependency changes, and use the existing focused test modules listed in `plan.md`.

## Phase 2: Foundational

**Purpose**: Define one shared submission-certainty contract before each consumer uses refusal evidence.

- [X] T005 Create `SubmissionCertainty` with documented refusal candidates, conflict checks, refusal predicate, and settlement helper in `src/foundation/support/submission_certainty.py`.

## Phase 3: User Story 1 - Prevent a duplicate upgrade (Priority: P1)

**Goal**: Keep each site locked and block retry while a firmware submission result remains uncertain.

**Independent Test**: Offline submission and route tests prove that transport failures, server errors, malformed successes, missing identities, and unlisted statuses cannot release a site lock or enable a repeated submission.

### Tests for User Story 1

- [X] T002 [P] [US1] Add offline tests for documented refusals, conflicting identities and accepted targets, HTTP 429, undocumented statuses, HTTP 5xx, malformed successes and refusal bodies, and missing identities. Exercise the real device and organization normalizers in `tests/unit/firmware/test_aggregate_upgrade_service.py`.
- [X] T002a [US1] Check discarded device list bodies, malformed or mismatched raw JSON, and valid refusal bodies through the real normalizer. Prove that uncertain replies block another submission without a browser or network.
- [X] T002b [US1] Persist body-verification proof through JSON save and reload. Test legacy refusal locks, cancellation lists, summary counts, and mismatched success identities offline.
- [X] T003 [P] [US1] Add lock-retention tests for ambiguous replies and conflicting legacy rejected records, and prove that a known not-submitted child can settle, in `tests/unit/upgrade_portal/test_org_upgrade_lock_release.py`.
- [X] T004 [P] [US1] Test that a returned HTTP 503 keeps the uncertainty marker and blocks a repeated submission in `tests/contract/upgrade_portal/test_org_upgrade_routes.py`.

### Implementation for User Story 1

- [X] T006 [US1] Use `SubmissionCertainty` to classify only accepted replies with required identities as `accepted`, documented refusals without conflicting evidence as `rejected`, and all other replies as `submission_unknown` in `src/operations/execution/firmware/aggregate_upgrade_service.py`.
- [X] T007 [US1] Require documented refusal evidence without conflicting identity or accepted-target evidence before a rejected child can settle, release a site lock, pass retry eligibility, or count as fully failed in `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`.

## Phase 4: User Story 2 - Release a lock after a proven refusal (Priority: P2)

**Goal**: Use the same refusal evidence for cancellation reporting and lock release.

**Independent Test**: Offline cancellation tests prove that documented refusal statuses mean no cloud job exists only when no identity or accepted target conflicts. Status 429, undocumented statuses, server errors, and missing evidence remain uncertain.

### Tests for User Story 2

- [X] T008 [P] [US2] Update cancellation outcome tests for documented refusal statuses, 429, undocumented statuses, and conflicting legacy evidence in `tests/unit/upgrade_portal/test_org_cancel_outcomes.py`.

### Implementation for User Story 2

- [X] T009 [US2] Use `SubmissionCertainty` and saved child evidence for cancellation refusal decisions in `src/interfaces/portals/upgrade_portal/upgrade/org_cancel_outcomes.py`.

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Record the user-visible safety change and validate every affected path.

- [X] T010 [P] Add the issue-specific release note in `changelog.d/issue-3726-site-lock-safety.md`.
- [X] T011 Run focused tests, Ruff, Black, type checks, and symbol checks on changed Python files. Record exact results and intentional new symbols in the pull request.
- [X] T012 Review the final change against `spec.md`, `design/contracts/submission-certainty.md`, and the issue's human-review requirement. Keep `needs-human-review`. Confirm that no live firmware request, production lock change, approval, merge, or auto-merge action occurred.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Complete before story work. It confirms the existing test boundary and no dependency changes.
- **Foundational (Phase 2)**: Complete T005 after Setup and before each consumer uses the shared predicate.
- **User Story 1 (Phase 3)**: Depends on Setup and T005. Tests T002-T004 can be written in parallel. Implement T006 and T007 after the shared predicate exists.
- **User Story 2 (Phase 4)**: Depends on T005 because cancellation uses the shared predicate.
- **Polish (Phase 5)**: Run after both stories. The release-note edit can run in parallel with test implementation.

### User Story Dependencies

- **User Story 1 (P1)**: Independent after Setup. It protects uncertain outcomes and blocks duplicate submissions.
- **User Story 2 (P2)**: Depends on the shared refusal predicate from User Story 1. It keeps cancellation reporting consistent with lock release.

### Parallel Opportunities

- T002, T003, T004, and T008 edit different test files and can proceed in parallel.
- T010 can proceed while implementation tasks use separate files.
- T011 requires all test and implementation tasks to finish.

## Implementation Strategy

### MVP First

1. Complete T001.
2. Write T002-T004 and verify that they fail for the unsafe behavior.
3. Implement T005-T007 and validate User Story 1.
4. Implement T008-T009 and validate User Story 2.
5. Complete T010-T012 and prepare one issue-specific pull request for human review.

### Incremental Delivery

1. Deliver the P1 lock-retention and retry-blocking behavior.
2. Deliver the P2 cancellation consistency using the same refusal predicate.
3. Run all focused checks and retain the `needs-human-review` label until a human reviews the destructive-path change.
