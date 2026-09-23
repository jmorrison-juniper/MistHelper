# Tasks: No-output completion reasons

## Phase 1: Setup

- [X] T001 Reproduce menus 77, 78, and 82 on the local portal.
- [X] T002 Create the feature specification in specs/3193-no-output-reasons/spec.md.
- [X] T003 Create the implementation plan in specs/3193-no-output-reasons/plan.md.

## Phase 2: Implementation

- [X] T004 Add `SiteInventory.csv` to prompt cache markers in web_portal/services/operation.py.
- [X] T005 Keep menu 60 as the `SiteInventory.csv` export exception in web_portal/services/operation.py.
- [X] T006 Add regression tests in tests/unit/test_operation_output_file_discovery.py.

## Phase 3: Validation

- [X] T007 Prove the guard fails under a cache-marker mutant.
- [X] T008 Run the focused quality gates.
- [X] T009 Re-run menus 77, 78, and 82 on port 9605 and view screenshots.
- [X] T010 Open the pull request and comment on issue 3193.
