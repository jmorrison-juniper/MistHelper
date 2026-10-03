# Tasks: WIP target controls

**Input**: Design documents from `specs/3158-wip-target-controls/`.

**Prerequisites**: [plan.md](plan.md) and [spec.md](spec.md).

**Tests**: The assignment requires native, route, and browser acceptance proofs.

**Organization**: Tasks follow the three user stories and the bounded local preparation.

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Verify the live release and exact scope before edits. (delivered: specs/3158-wip-target-controls/plan.md)
- [x] T002 Record SpecKit hook limits and complete the feature-only spec, plan, and tasks. (delivered: specs/3158-wip-target-controls/.spec-context.json)
- [x] T003 Reproduce current shipped-browser controls and actual handler outputs before product edits. (delivered: specs/3158-wip-target-controls/plan.md)

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T004 Add controlled native SDK, temporary writer, network, and cleanup boundaries. (delivered: tests/support/wip_target_controls/native.py)
- [x] T005 Add the owned shipped portal and browser support. (delivered: tests/support/wip_target_controls/portal.py, tests/support/wip_target_controls/browser.py)
- [x] T006 Run acceptance against unchanged product files and retain counted red evidence. (delivered: specs/3158-wip-target-controls/plan.md)

## Phase 3: User Story 1 - Read the category caution (Priority: P1)

**Goal**: Show the category caution before execution without changing safety decisions.

**Independent Test**: Select three WIP rows, then one normal row. Remove warning metadata and require acceptance to fail.

- [x] T007 [US1] Add category and safety proofs. (delivered: tests/unit/web_portal/wip_target_controls/test_metadata.py)
- [x] T008 [US1] Add caution browser proofs. (delivered: tests/e2e/wip_target_controls/test_controls.py)
- [x] T009 [US1] Derive WIP presentation metadata. (delivered: web_portal/services/operation.py)
- [x] T010 [US1] Render and reset the caution. (delivered: web_portal/static/js/operations.js, web_portal/templates/operations.html)

## Phase 4: User Story 2 - Select a site and switch (Priority: P1)

**Goal**: Send both real handler answers and produce the actual selected switch result.

**Independent Test**: Select a site and switch, run menu 63, and count exactly one virtual chassis call.

- [x] T011 [US2] Add the real handler output contract. (delivered: tests/contract/web_portal/wip_target_controls/test_handler_outputs.py)
- [x] T012 [US2] Add target, keyboard, failure, stale selection, and recovery proofs. (delivered: tests/e2e/wip_target_controls/test_failure_recovery.py)
- [x] T013 [US2] Complete menu 63 descriptors. (delivered: web_portal/services/operation.py)
- [x] T014 [US2] Preserve required Run gates and reset stale targets. (delivered: web_portal/static/js/operations.js)

## Phase 5: User Story 3 - Preserve site-only client exports (Priority: P2)

**Goal**: Preserve the current controls and prove the actual client results, not site cache side effects.

**Independent Test**: Run menus 64 and 65 through actual CLI handler and local writer boundaries.

- [x] T015 [US3] Prove both actual client exports. (delivered: tests/contract/web_portal/wip_target_controls/test_handler_outputs.py)
- [x] T016 [US3] Prove single Site controls and non-WIP recovery. (delivered: tests/e2e/wip_target_controls/test_controls.py)

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T017 Add the bounded release note. (delivered: changelog.d/issue-3158-wip-target-controls.md)
- [x] T018 Run the combined native, route, browser, safety, refusal, empty-reason, and logging selectors. (delivered: tests/e2e/wip_target_controls/test_controls.py)
- [x] T019 Run applicable local gates and direct negative guards without baseline or exclusion changes. (delivered: tests/unit/web_portal/wip_target_controls/test_metadata.py)
- [x] T020 Verify owned cleanup and record honest private template evidence before the local commit. (delivered: specs/3158-wip-target-controls/tasks.md)

## Dependencies & Execution Order

T001 through T003 precede T004 and T005.
T004 and T005 precede T006.
The red proof in T006 precedes T009, T010, T013, and T014.
The caution and target tests can be written independently.
The real handler contract depends on the native support, not on product edits.
T018 and T019 follow all implementation tasks.
T020 follows the complete local checks and cleanup.
The local commit and its committed-scope receipt follow this verified preparation.
Publication is not a task in this local preparation.

## Verified Local Evidence

The pre-edit causal selector reported three required-control and caution failures with ten passing preservation controls.
The direct metadata HTTP proof reported two readiness failures with two passing controls before its repair.
The final combined collection passed 971 cases with zero skips and 33 recorded warnings.
The separate owned collection passed 46 cases with resource warnings treated as errors.
The actual operation service measured 90.96 percent statement-and-branch coverage.
The complete unchanged-baseline gate checked 1,015 discovered files and reported zero new findings.
It parsed 967 files, skipped 48 files under existing policy, and reported zero parse errors.
The six-input, three-guide preflight passed.
The normal dependency audit aborted before its audit because the copied temporary interpreter could not start.
The complete strict hashed alternative audited 105 applicable native runtime packages, skipped zero, and found zero vulnerabilities.
The Git-only development tool remains outside that runtime audit.
STE scores passed the default threshold, but dictionary coverage remains unavailable and partial.
The original filename acceptance remains unresolved in the separate issue #3738.
No publication, protected merge, or actual-main local proof belongs to this preparation.

## Parallel Opportunities

The unit metadata tests and native handler contract use separate files.
The browser controls and browser failure tests use separate files after the support exists.
Product edits remain under one owner.

## Implementation Strategy

Prove the current gaps first.
Complete the existing metadata and presentation without changing source handler behavior.
Run the complete bounded proof and required local gates.
Retain the local commit and wait for the parent publication grant.
