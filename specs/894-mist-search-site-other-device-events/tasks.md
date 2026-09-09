# Tasks: Search Site Other Device Events

**Input**: Design documents from `specs/894-mist-search-site-other-device-events/`
**Prerequisites**: `plan.md` and `spec.md`
**Branch**: `feat/1402-search-site-other-device-events`

## Phase 1: Setup

- [X] T001 Confirm menu 250 is the next free operation slot in `MistHelper.py`.
- [X] T002 Verify the installed SDK signature and module path.
- [X] T003 Add focused exporter test scaffolding.

## Phase 2: Foundational

- [X] T004 Verify the existing `searchSiteOtherDeviceEvents` composite primary-key entry.
- [X] T005 Add the exporter module with site resolution, SDK paging, flattening, and persistence.
- [X] T006 Register the exporter import and menu 250 handler.

## Phase 3: User Story 1 - Read-only data retrieval

**Goal**: A NOC engineer can select a site and export other-device event rows.

**Independent Test**: Mock the site resolver and SDK, then assert one API call,
pagination, output routing, and clean handling of an empty response.

- [X] T007 [US1] Test empty response handling.
- [X] T008 [US1] Test flattening and DataExporter routing.
- [X] T009 [US1] Test site resolution and SDK call arguments.
- [X] T010 [US1] Test SDK failure logging without a menu traceback.

## Phase 4: Documentation and Validation

- [X] T011 Update README operation count and menu description.
- [X] T012 Update the generated menu reference.
- [X] T013 Add the CHANGELOG entry for issue #1402.
- [X] T014 Run focused tests and required quality gates.
- [ ] T015 Commit, push, create the PR, and merge after required checks pass.
- [ ] T016 Mark SQL todo `mist-get-1402` done after delivery, or blocked with
  the exact blocker.

## Dependencies

- T001 and T002 precede T005 and T006.
- T005 precedes T007 through T010.
- T006 precedes T009.
- T007 through T010 precede T011 through T015.
- T015 precedes T016.
