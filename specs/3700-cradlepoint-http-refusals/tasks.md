---
description: "Bounded local tasks for issue 3700"
---

# Tasks: Cradlepoint HTTP refusals

**Input**: [spec.md](spec.md), [plan.md](plan.md), and the documents under `design/`.

**Prerequisites**: Complete live ownership checks and an owned Python `3.13` environment.

**Tests**: Native response and preservation tests are mandatory for this repair.

**Organization**: Tasks correspond to the three independent user stories.

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Verify the exact reservation and feature-only specification.
  Record the mandatory hook failure. (delivered: specs/3700-cradlepoint-http-refusals/plan.md)
- [x] T002 Verify the unchanged exporter and all 15 existing tests.
  Preserve recovery evidence. (delivered: specs/3700-cradlepoint-http-refusals/design/verification.md)

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T003 Write native response tests.
  (delivered: tests/unit/export/cradlepoint_http_refusals/test_native_responses.py)
- [x] T004 Prove that unchanged source fails all native refusal and absent-transport cases.
  (delivered: specs/3700-cradlepoint-http-refusals/design/verification.md)

## Phase 3: User Story 1 - Report a refused request (Priority: P1)

- [x] T005 [US1] Add the bounded status guard.
  (delivered: src/export/org_cradlepoint_connection_exporter.py)
- [x] T006 [US1] Verify exact-status diagnostics, zero callbacks, and zero live requests.
  (delivered: tests/unit/export/cradlepoint_http_refusals/test_native_responses.py)

## Phase 4: User Story 2 - Preserve a successful integration status (Priority: P2)

- [x] T007 [US2] Give existing positive response doubles explicit HTTP `200`.
  (delivered: tests/unit/export/test_org_cradlepoint_connection_exporter.py)
- [x] T008 [US2] Verify native HTTP `200` rows, integration errors, metadata, and empty bodies.
  (delivered: tests/unit/export/cradlepoint_http_refusals/test_native_responses.py)

## Phase 5: User Story 3 - Report an unavailable transport status (Priority: P3)

- [x] T009 [US3] Verify native `APIResponse(None, url)` and unusable statuses.
  (delivered: tests/unit/export/cradlepoint_http_refusals/test_native_responses.py)

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T010 Verify complete changed-method statement and branch coverage.
  (delivered: specs/3700-cradlepoint-http-refusals/design/verification.md)
- [x] T011 Run applicable configured gates without changing settings or suppressions.
  (delivered: specs/3700-cradlepoint-http-refusals/design/verification.md)
- [x] T012 Add the unique release note and verification evidence.
  (delivered: changelog.d/issue-3700-cradlepoint-http-refusals.md)
- [x] T013 Prepare the reserved-file commit inputs and required coauthor.
  The session artifacts hold the commit message and offline draft.
  (delivered: specs/3700-cradlepoint-http-refusals/plan.md)
- [x] T014 Define the mandatory post-commit preflight and changed-scope comparison.
  The handoff must report the actual result after the commit.
  (delivered: specs/3700-cradlepoint-http-refusals/design/verification.md)
- [ ] T015 Keep remote publication, protected merge, and actual-main verification deferred.
  Only the coordinator's explicit verified-main SHA grant releases these tasks.

## Dependencies & Execution Order

T003 and T004 require T001 and T002.
T005 requires the unchanged-source failure proof.
T006 through T009 require the guard.
T010 through T012 require the completed behavior tests.
The actual local commit requires successful applicable local gates.
The actual post-commit comparison requires that commit and a clean relevant worktree.
T015 remains deferred regardless of a local gate result.

## Implementation Strategy

First prove the native defect without changing production behavior.
Then add the smallest status-only decision in the existing semantic class.
Preserve all unrelated source and baseline finding identities.
Finish the local commit and report the evidence to the coordinator.
