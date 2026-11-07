# Tasks: Capture Request Dependencies

**Input**: [spec.md](spec.md), [plan.md](plan.md), and supporting files under `design/`.

## Phase 1: Setup

- [x] T001 Verify the fresh `main` baseline and run the offline provider tests in `tests/integration/upgrade_portal/issue_3834/`, `tests/integration/upgrade_portal/issue_3977/`, and `tests/unit/upgrade_portal/test_phase2_phase3_route_connections.py`.

## Phase 2: Foundational

- [x] T002 [US1] Add offline regression tests for the normal factory capture route, authenticated session binding, missing authentication, and unavailable storage in `tests/integration/upgrade_portal/issue_4653/test_capture_request_dependencies.py`.

## Phase 3: User Story 1 - Start a pre-upgrade capture

**Goal**: Start captures through authenticated request resources, or refuse safely before capture work.

**Independent test**: Run `tests/integration/upgrade_portal/issue_4653/test_capture_request_dependencies.py` with fake operator sessions, fake database routers, and fake capture services.

- [x] T003 [US1] Add lazy `CaptureService` construction and request caching to `src/interfaces/portals/upgrade_portal/app/wiring.py`.
- [x] T004 [US1] Defer invalid startup capture services and resolve the request service in `src/interfaces/portals/upgrade_portal/app/wiring.py` and `src/interfaces/portals/upgrade_portal/app/routes/capture.py`.
- [x] T005 [P] [US1] Document the capture dependency behavior in `documentation/upgrade_capture_portal.md` and `changelog.d/issue-4653-capture-request-dependencies.md`.

## Phase 4: Polish

- [x] T006 Run the focused provider and capture tests, changed-file lint and format checks, type checks, and Markdown checks. Record each command and result in the task report.

## Dependencies

- T001 is complete and independent.
- T002 must pass before T003 and T004.
- T003 must pass before T004.
- T005 can run in parallel with T003 and T004.
- T006 depends on T002 through T005.

## Parallel Opportunities

- T005 edits only documentation and the release fragment. It can run independently after the spec is approved.
- T003 and T004 touch related service wiring and route behavior. Keep them sequential to preserve the request lifecycle contract.

## Implementation Strategy

Implement User Story 1 as the minimum complete change. First add the offline regression tests. Then build and use the request-scoped service. Finally update documentation and run the focused quality gates.
