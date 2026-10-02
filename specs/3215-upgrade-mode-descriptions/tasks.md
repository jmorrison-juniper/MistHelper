# Tasks: Upgrade mode descriptions

**Input**: [spec.md](spec.md) and [plan.md](plan.md).

**Prerequisites**: The live claim, complete open pull request file lists, and the current behavior trace.

## Phase 1: Setup

- [x] T001 Verify and claim issue #3215 with the exact file reservation. (delivered: specs/3215-upgrade-mode-descriptions/plan.md)
- [x] T002 Trace the current routes, pre-check adoption, post-check modes, and comparison rules. (delivered: specs/3215-upgrade-mode-descriptions/plan.md)
- [x] T003 Create the file-only specification and plan without shared metadata changes. (delivered: specs/3215-upgrade-mode-descriptions/spec.md)

## Phase 2: Foundational Tests

- [x] T004 [P] Add real offline rendering contracts. (delivered: tests/contract/upgrade_portal/test_mode_descriptions.py)
- [x] T005 [P] Add isolated Chromium journeys. (delivered: tests/e2e/upgrade_portal/test_mode_descriptions_journey.py)
- [x] T006 Record red failures for the false claim on both rendered pages. (delivered: specs/3215-upgrade-mode-descriptions/implementation.md)

## Phase 3: User Story 1 - Understand each upgrade mode

- [x] T007 [US1] Replace the mode descriptions. (delivered: src/upgrade_portal/app/assets/templates/select/mode.html)
- [x] T008 [US1] Verify both descriptions, captures, mode values, and form actions. (delivered: tests/contract/upgrade_portal/test_mode_descriptions.py)

## Phase 4: User Story 2 - Understand the selected site's workflow

- [x] T009 [US2] Replace the active-mode description. (delivered: src/upgrade_portal/app/assets/templates/select/sites.html)
- [x] T010 [US2] Verify single-site navigation and zero, one, and two selected-site states. (delivered: tests/e2e/upgrade_portal/test_mode_descriptions_journey.py)

## Phase 5: Quality and Analysis

- [x] T011 Run local commands and record their results and missing capabilities. (delivered: specs/3215-upgrade-mode-descriptions/implementation.md)
- [x] T012 Add the release note. (delivered: changelog.d/issue-3215-upgrade-mode-descriptions.md)
- [x] T013 Analyze requirement coverage and unchanged behavior. (delivered: specs/3215-upgrade-mode-descriptions/analysis.md)
- [x] T014 Prepare the exact file manifest for the local commit. (delivered: specs/3215-upgrade-mode-descriptions/implementation.md)

## Dependencies & Execution Order

T001 to T003 establish the claim and specification before implementation.
T004 and T005 can proceed independently.
T006 requires both test modules and precedes T007 and T009.
T008 requires T007, and T010 requires T009.

T011 requires both stories.
T013 requires the specification, plan, tasks, and quality evidence.
T014 requires the delivered files and their recorded evidence.

Commit the exact manifest after the local review.
Report the clean local SHA to the parent after the commit.

## Publication Boundary

Publication is not authorized.
The parent must grant an explicit, fully verified main SHA after the preceding repair.
Any later delivery requires a fresh rebase, repeated local gates, complete PR evidence, protected merge, and exact-main proof.

## Local Refresh on 2026-10-02

- [x] T015 Preserve the original commit and rebase only on the authorized immutable base. (delivered: specs/3215-upgrade-mode-descriptions/implementation.md)
- [x] T016 Describe current per-device model choices and both AP routing cases. (delivered: src/upgrade_portal/app/assets/templates/select/mode.html)
- [x] T017 Retain the browser import skip and prove strict and owner failure paths. (delivered: tests/e2e/upgrade_portal/test_mode_descriptions_journey.py)
- [x] T018 Repeat real rendering, all six Chromium cases, full collection, and applicable local gates. (delivered: specs/3215-upgrade-mode-descriptions/implementation.md)
- [x] T019 Record skipped cases and the current 23-item offline review requirement. (delivered: specs/3215-upgrade-mode-descriptions/analysis.md)

The clean committed-tree analyzer and full ratchet run after the new local commit.
Their session reports must state the measured counts and all new findings.
The parent receives the clean SHA and those results.
This local refresh does not authorize publication or delivery.
