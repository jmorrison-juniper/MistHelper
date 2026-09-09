# Tasks: searchOrgDevices

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, and `contracts/search_org_devices.md`

## Phase 1: Foundation

- [X] T001 Confirm the endpoint SDK path and select menu 249.
- [X] T002 Confirm the existing `searchOrgDevices` composite primary-key strategy.
- [X] T003 Register menu 249 as a safe operation.

## Phase 2: User Story 1 - Read-only device search (P1)

- [X] T004 [US1] Add `OrgSearchExporter.devices` in `src/export/org_search_exporter.py`.
- [X] T005 [US1] Add menu 249 in `MistHelper.py`.
- [X] T006 [US1] Add endpoint binding, pagination, persistence, empty-result, and error tests.
- [X] T007 [US1] Update the README, changelog, and generated menu reference.

## Phase 3: Validation and delivery

- [X] T008 Run focused tests and repository quality gates.
- [ ] T009 Commit the implementation with issue reference.
- [ ] T010 Push the branch and create the pull request.
- [ ] T011 Merge the pull request after required checks pass.
