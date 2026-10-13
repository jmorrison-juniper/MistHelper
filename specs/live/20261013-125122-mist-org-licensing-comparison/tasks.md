---

description: "Implementation tasks for Mist Organization Licensing Comparison"
---

# Tasks: Mist Organization Licensing Comparison

**Input**: Design documents from `specs/live/20261013-125122-mist-org-licensing-comparison/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/licensing-comparison.md, quickstart.md

**Scope**: Plan only. Do not mark any task complete until implementation and verification occur.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Use only when tasks edit separate files and have no unfinished dependency.
- **[Story]**: Use one story label for each user story task.
- Put exact file paths in every task.
- Add evidence after implementation in this form: `(delivered: path/to/file.py)`.

## Phase 1: Setup

**Purpose**: Create the feature package within the existing application.

- [ ] T001 Create the feature package, route module, service module, blueprint template directory, and static asset directory under `src/interfaces/portals/licensing_comparison/`.
- [ ] T002 Create the focused test package under `tests/integration/web_portal/licensing_comparison/` with `__init__.py` and synthetic response fixtures.

## Phase 2: Foundational

**Purpose**: Connect the feature package to the existing portal before story work.

- [ ] T003 Register the feature blueprint in `web_portal/app.py` and add its navigation link to `web_portal/templates/base.html`.
- [ ] T004 Preserve the source dashboard layout and add stable controls for organization selection, comparison results, manual rows, purchased amounts, balances, export, and attribution in `src/interfaces/portals/licensing_comparison/templates/licensing_comparison.html`.

**Checkpoint**: The existing portal serves the feature page without a new process, service, database, Redis instance, or public port.

## Phase 3: User Story 1 - Compare organizations (Priority: P1)

**Goal**: Let operators compare license and inventory data for organizations the shared Mist session can access.

**Independent Test**: Synthetic responses for two authorized organizations produce two result rows. A failed request has an explicit error and no false zero.

### Tests for User Story 1

- [ ] T005 [P] [US1] Add tests for organization discovery, unauthorized IDs, missing sessions, HTTP 4xx responses, and HTTP 5xx responses in `tests/integration/web_portal/licensing_comparison/test_routes.py`.
- [ ] T006 [P] [US1] Add tests for license summary, site license use, inventory, partial failure, rate-limit responses, and installed SDK method availability in `tests/integration/web_portal/licensing_comparison/test_service.py`.

### Implementation for User Story 1

- [ ] T007 [US1] Implement server-side access discovery with `getSelf` and permitted `listMspOrgs` calls in `src/interfaces/portals/licensing_comparison/service.py`.
- [ ] T008 [US1] Implement organization, license, and inventory reads with `getOrgLicensesSummary`, `getOrgLicensesBySite`, and `getOrgInventory` in `src/interfaces/portals/licensing_comparison/service.py`.
- [ ] T009 [US1] Implement the page, organization-choice, and comparison routes in `src/interfaces/portals/licensing_comparison/routes.py`.
- [ ] T010 [US1] Render organization choices, per-organization statuses, license values, and inventory values in `src/interfaces/portals/licensing_comparison/templates/licensing_comparison.html` and `src/interfaces/portals/licensing_comparison/static/licensing_comparison.js`.
- [ ] T011 [US1] Send one Mist request at a time. Use `RateLimitingUtils` for pacing, wait 60 seconds after HTTP 429, and retry once in `src/interfaces/portals/licensing_comparison/service.py`.

**Checkpoint**: Authorized organizations compare independently. API failures remain visible and never appear as successful zero values.

## Phase 4: User Story 2 - Adjust license balances (Priority: P2)

**Goal**: Let operators add session-only rows and purchase values, then review remaining balances and SUB-AI components.

**Independent Test**: Valid synthetic manual and purchase values update each remaining balance. Invalid values are rejected, and bundle components remain distinct.

### Tests for User Story 2

- [ ] T012 [P] [US2] Add tests for non-negative whole-number validation and missing purchase values in `tests/integration/web_portal/licensing_comparison/test_service.py`.
- [ ] T013 [US2] Add tests for remaining balances and each SUB-AI component in `tests/integration/web_portal/licensing_comparison/test_service.py`.

### Implementation for User Story 2

- [ ] T014 [US2] Add validated manual rows and purchased amounts to browser `sessionStorage` in `src/interfaces/portals/licensing_comparison/static/licensing_comparison.js`.
- [ ] T015 [US2] Implement license balance and SUB-AI component calculations in `src/interfaces/portals/licensing_comparison/service.py`.
- [ ] T016 [US2] Render manual rows, purchased fields, validation errors, and remaining balances in `src/interfaces/portals/licensing_comparison/templates/licensing_comparison.html` and `src/interfaces/portals/licensing_comparison/static/licensing_comparison.js`.

**Checkpoint**: Manual rows and purchased values stay in the active browser session. The page does not send them to a persistent store.

## Phase 5: User Story 3 - Export the comparison (Priority: P3)

**Goal**: Let operators download a CSV that matches the displayed comparison.

**Independent Test**: A synthetic comparison export contains the displayed values, preserves unavailable values, and neutralizes formula-like text.

### Tests for User Story 3

- [ ] T017 [P] [US3] Add tests for CSV columns, source attribution, manual and purchased values, unavailable results, formula neutralization, and export failures in `tests/integration/web_portal/licensing_comparison/test_export.py`.

### Implementation for User Story 3

- [ ] T018 [US3] Implement formula-safe CSV rows, source attribution, and an explicit export through `DataExporter.write_with_format_selection` in `src/interfaces/portals/licensing_comparison/service.py`.
- [ ] T019 [US3] Add the export route and safe data-directory download response in `src/interfaces/portals/licensing_comparison/routes.py`.
- [ ] T020 [US3] Add the export action, attribution, and export status to `src/interfaces/portals/licensing_comparison/templates/licensing_comparison.html` and `src/interfaces/portals/licensing_comparison/static/licensing_comparison.js`.

**Checkpoint**: The CSV matches displayed values. The feature writes no report until the operator requests export.

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Verify portal integration, documentation, and migration boundaries.

- [ ] T021 [P] Add the feature page, navigation, stable selectors, and missing-session smoke checks to `tests/e2e/web_portal/test_portal_smoke.py`.
- [ ] T022 Update `specs/live/20261013-125122-mist-org-licensing-comparison/quickstart.md` with the final test commands and observed results.
- [ ] T023 Run focused tests, portal smoke tests, formatting, lint, type, complexity, and Bandit checks for the feature package and its tests.
- [ ] T024 Check that the feature package follows the planned layout and has no more than five direct children. Check `compose.yml`, `requirements.txt`, `requirements-dev.txt`, `MistHelper.py`, and the final diff for prohibited infrastructure or unrelated files. Permit only the planned README and release-note changes.
- [ ] T025 Add SDK transport contract tests for shared-session authentication, supported endpoint use, pagination, the single rate-limit retry, and redaction of tokens and exception text in `tests/integration/web_portal/licensing_comparison/test_transport_contract.py`.
- [ ] T026 Add browser tests for session-state persistence through page reload and in-page navigation, empty state in a new browser session, and input validation in `tests/e2e/licensing_comparison/test_session_state.py`.
- [ ] T027 Review the new code against all seven constitutional principles. Verify class-based ownership, function limits, inline comments, ASCII structured logs, action logs, and secret redaction.
- [ ] T028 Update `README.md` with a link to the comparison page. Add `changelog.d/issue-4197-mist-org-licensing-comparison.md` with an Added bullet that names issue #4197.
- [ ] T029 Run local gates, build the feature manifest, stage explicit files, commit, rebase on `origin/main`, and rerun affected gates before push.
- [ ] T030 After approval, open the implementation PR, pass CI, squash merge, wait for the main image build, verify its revision, deploy the approved image, and check health.

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No prerequisites.
- **Foundational (Phase 2)**: Depends on T001. It blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on T002-T004. It is the minimum viable feature.
- **User Story 2 (Phase 4)**: Depends on User Story 1 comparison records.
- **User Story 3 (Phase 5)**: Depends on User Story 1 result records and User Story 2 balance fields.
- **Polish (Phase 6)**: Depends on all desired user stories.

### User Story Dependencies

- **US1**: Independent after the foundational phase.
- **US2**: Depends on the comparison row and license types from US1.
- **US3**: Depends on the displayed comparison rows from US1 and balances from US2.
- **Transport contract tests (T025)**: Depend on the shared session and API service design from the foundational phase.
- **Browser state tests (T026)**: Depend on the existing portal browser test fixture and cover browser-only state.
- **Constitution review (T027)**: Depends on all implementation tasks and must pass before the implementation pull request.
- **README and release note (T028)**: Describe only the implemented behavior and name issue #4197.
- **Delivery steps (T029-T030)**: Run after implementation and its local checks. Require approval before deployment.

### Parallel Opportunities

- T005 and T006 can run in parallel because they edit separate test files.
- T013 follows T012 because both tasks edit `tests/integration/web_portal/licensing_comparison/test_service.py`.
- T017 can run in parallel with the US2 implementation because it edits a separate test file.
- T021 can run after T003 and can run beside service and export work.

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational phases.
2. Complete User Story 1 and its tests.
3. Verify accessible organization selection, license and inventory reads, and visible failures.
4. Continue to User Story 2 only after the MVP passes.

### Incremental Delivery

1. Deliver organization comparison as the first usable slice.
2. Add manual rows, purchased values, and bundle-aware balances.
3. Add CSV export after the displayed result shape is stable.
4. Run the portal smoke and project quality checks before opening an implementation pull request.

## Notes

- Every task remains unchecked because implementation has not started.
- Do not add a test file directly to an over-limit test directory. Keep feature tests under the new integration package.
- Use synthetic Mist responses. Do not use production credentials.
