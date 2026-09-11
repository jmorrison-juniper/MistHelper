# Tasks: Search Organization Other-Device Events

**Input**: Design documents from `specs/868-mist-search-org-other-device-events/`
**Prerequisites**: `plan.md` and `spec.md`
**Branch**: `feat/1376-search-org-other-device-events`

## Phase 1: Setup

- [X] T001 Confirm menu 261 is the target slot on current `origin/main`.
- [X] T002 Verify the installed SDK callable and prompt requirements.
- [X] T003 Check the existing primary-key strategy for `searchOrgOtherDeviceEvents`.

## Phase 2: Foundational

- [X] T004 Add the optional filter prompt map to `OrgSearchExporter`.
- [X] T005 Add the `OrgSearchExporter.other_device_events()` entry point.
- [X] T006 Move the menu registration to 261 and update the operation registry.

## Phase 3: User Story 1 - Read-only data retrieval

**Goal**: A NOC engineer can search organization other-device events and export
the rows through the standard backend selector.

**Independent Test**: Mock the organization resolver and SDK, then assert one
API call, typed filter forwarding, prompt order, test-mode prompt skipping, and
safe menu registration.

- [X] T007 [US1] Test optional filter forwarding for the SDK call.
- [X] T008 [US1] Test documented prompt order and invalid limit handling.
- [X] T009 [US1] Test menu 261 registration and the composite event key.
- [X] T010 [US1] Test unattended `--test` mode with no prompt reads.

## Phase 4: Documentation and Validation

- [X] T011 Update README, CHANGELOG, and menu highlight text.
- [X] T012 Regenerate `documentation/menu_reference.md` and
  `documentation/wiki/Menu-Reference.md`.
- [ ] T013 Run focused tests and required quality gates.
- [ ] T014 Commit, push, create the PR, wait for checks, rebase if needed, and
  merge.
