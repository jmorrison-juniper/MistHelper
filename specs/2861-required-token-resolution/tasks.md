# Tasks: Required token resolution

**Input**: [spec.md](spec.md) and [plan.md](plan.md).

**Tests**: Required. The original controlled failures must precede the behavior change.

## Phase 1: Setup

- [x] T001 Reserve the exact source, tests, feature documents, and fragment in the issue claim. (delivered: specs/2861-required-token-resolution/plan.md)
- [x] T002 Create the bounded specification and plan without shared SpecKit changes. (delivered: specs/2861-required-token-resolution/spec.md)
- [x] T003 Prepare isolated backend and root environments for `mist-ops-platform/tests/unit/mist/token_resolution/`. (delivered: specs/2861-required-token-resolution/quickstart.md)

## Phase 2: Foundational

- [x] T004 Create controlled provider and SDK fixtures in `mist-ops-platform/tests/unit/mist/token_resolution/conftest.py`. (delivered: mist-ops-platform/tests/unit/mist/token_resolution/conftest.py)
- [x] T005 Prove three red original cases in `mist-ops-platform/tests/unit/mist/token_resolution/test_required_resolution.py`. (delivered: specs/2861-required-token-resolution/quickstart.md)

## Phase 3: User Story 1 - Use the next usable source

**Goal**: Preserve source precedence while rejecting unusable earlier values.

**Independent Test**: Assert exact provider calls and constructor arguments.

- [x] T006 [US1] Add blank and non-string fallback tests in `mist-ops-platform/tests/unit/mist/token_resolution/test_required_resolution.py`. (delivered: mist-ops-platform/tests/unit/mist/token_resolution/test_required_resolution.py)
- [x] T007 [US1] Add direct guards and source diagnostics in `mist-ops-platform/src/shared/mist/session.py`. Covers FR-001 through FR-004 and FR-006. (delivered: mist-ops-platform/src/shared/mist/session.py)
- [x] T008 [US1] Prove exact Vault cache key, TTL, and value in `mist-ops-platform/tests/unit/mist/token_resolution/test_provider_contracts.py`. (delivered: mist-ops-platform/tests/unit/mist/token_resolution/test_provider_contracts.py)

## Phase 4: User Story 2 - Stop when no usable token exists

**Goal**: Preserve the no-token contract and stop before SDK construction.

**Independent Test**: Require zero SDK constructions and zero invalid cache writes.

- [x] T009 [US2] Add all-source rejection tests in `mist-ops-platform/tests/unit/mist/token_resolution/test_required_resolution.py`. (delivered: mist-ops-platform/tests/unit/mist/token_resolution/test_required_resolution.py)
- [x] T010 [US2] Prove secret-marker absence and checked-source diagnostics in `mist-ops-platform/tests/unit/mist/token_resolution/test_session_boundary.py`. Covers FR-005 through FR-007. (delivered: mist-ops-platform/tests/unit/mist/token_resolution/test_session_boundary.py)

## Phase 5: User Story 3 - Preserve healthy behavior

**Goal**: Preserve opaque values, provider exceptions, scope, and rate limiting.

**Independent Test**: Assert exact values, exception identity, and unchanged rate-limiter construction.

- [x] T011 [US3] Cover bytes, provider exceptions, and configured-only fallback in `mist-ops-platform/tests/unit/mist/token_resolution/test_provider_contracts.py`. Covers FR-008 and FR-009. (delivered: mist-ops-platform/tests/unit/mist/token_resolution/test_provider_contracts.py)
- [x] T012 [US3] Cover healthy bypass, SDK parameters, and rate limiting in `mist-ops-platform/tests/unit/mist/token_resolution/test_session_boundary.py`. Covers FR-002, FR-003, and FR-010. (delivered: mist-ops-platform/tests/unit/mist/token_resolution/test_session_boundary.py)

## Phase 6: Local evidence

- [x] T013 Measure focused and complete backend checks for `mist-ops-platform/src/shared/mist/session.py`. Record existing type limits. Covers FR-011, FR-012, and SC-001 through SC-005. (delivered: specs/2861-required-token-resolution/quickstart.md)
- [x] T014 Measure applicable root checks and the unchanged full test-quality ratchet. Record commands and capability limits in `specs/2861-required-token-resolution/quickstart.md`. Covers SC-006. (delivered: specs/2861-required-token-resolution/quickstart.md)
- [x] T015 Add `changelog.d/issue-2861-required-token-resolution.md` and preserve the 23-item PR template in an offline session artifact. (delivered: changelog.d/issue-2861-required-token-resolution.md)
- [x] T016 Prepare the verified feature manifest for one local commit with the required coauthor. Record the resulting SHA and clean-state proof outside the commit. (delivered: specs/2861-required-token-resolution/quickstart.md)

## Phase 7: Protected publication

- [ ] T017 Obtain the parent's full verified-main SHA grant for position 36 before publication or task-delivery completion. This condition requires the parent.

## Dependencies & Execution Order

T001 and T002 precede every source or test edit.
T003 and T004 precede T005.
T005 precedes T007.
T006 and T009 define the guard matrix for T007.
T008 and T010 through T012 prove the repaired behavior.
T013 follows all implementation and test tasks.
T014 and T015 precede T016.
T017 remains a separate authorization condition.
The post-commit changed-scope ratchet also precedes any future publication.

## Parallel Opportunities

The backend and root environment setup can run independently.
Independent read-only gates can run in parallel after the implementation is stable.
No second agent needs ownership of this small production method.

## Implementation Strategy

Prove the original failures first.
Add only the necessary guards.
Verify every reserved behavior with controlled values.
Record partial capabilities without a full-certification claim.
Preserve the repair in one clean local commit.
Do not publish without the parent grant.
