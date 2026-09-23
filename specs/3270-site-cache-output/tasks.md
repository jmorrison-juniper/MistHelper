# Tasks: Site cache output ordering

## Phase 1: Setup

- [X] T001 Create the feature specification in specs/3270-site-cache-output/spec.md.
- [X] T002 Create the implementation plan in specs/3270-site-cache-output/plan.md.

## Phase 2: Implementation

- [X] T003 Add cache output markers and preview ordering in web_portal/services/operation.py.
- [X] T004 Add a regression test for menu 69 cache ordering in tests/unit/test_operation_output_file_discovery.py.
- [X] T005 Add a measured site-parameter guard in tests/unit/test_operation_output_file_discovery.py.

## Phase 3: Validation

- [X] T006 Run the focused unit tests for output discovery.
- [X] T007 Serve the local portal on port 9605 and capture before and after evidence for menu 69.
- [X] T008 Open the pull request and comment on issue 3270.
