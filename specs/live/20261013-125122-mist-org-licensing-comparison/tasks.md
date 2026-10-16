---

description: "Implementation tasks for Mist Organization Licensing Comparison"
---

# Tasks: Mist Organization Licensing Comparison

**Input**: Design documents from `specs/live/20261013-125122-mist-org-licensing-comparison/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/licensing-comparison.md, quickstart.md

**Scope**: Implementation and portal registration are complete. Pull request #4245 awaits final CI and the authorized squash merge.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Use only when tasks edit separate files and have no unfinished dependency.
- **[Story]**: Use one story label for each user story task.
- Put exact file paths in every task.
- Add evidence after implementation in this form: `(delivered: path/to/file.py)`.

## Phase 1: Setup

**Purpose**: Create the feature package within the existing application.

- [x] T001 Create the feature package, route module, service module, blueprint template directory, and static asset directory under `src/interfaces/portals/licensing_comparison/`. (delivered: `src/interfaces/portals/licensing_comparison/`)
- [x] T002 Create the focused test package under `tests/integration/web_portal/licensing_comparison/` with `__init__.py` and synthetic response fixtures. (delivered: `tests/integration/web_portal/licensing_comparison/test_service.py`)

## Phase 2: Foundational

**Purpose**: Connect the feature package to the existing portal before story work.

- [x] T003 Register the feature blueprint in `web_portal/app.py` and add its navigation link to `web_portal/templates/base.html`. (delivered: `web_portal/app.py`, `web_portal/templates/base.html`)
- [x] T004 Add controls for organization selection, comparison results, manual rows, purchased amounts, balances, export, and attribution in `src/interfaces/portals/licensing_comparison/templates/licensing_comparison.html`. (delivered: `src/interfaces/portals/licensing_comparison/templates/licensing_comparison.html`)

**Checkpoint**: The existing portal serves the feature page without a new process, service, database, Redis instance, or public port.

## Phase 3: User Story 1 - Compare organizations (Priority: P1)

**Goal**: Let operators compare license and inventory data for organizations the shared Mist session can access.

**Independent Test**: Synthetic responses for two authorized organizations produce two result rows. A failed request has an explicit error and no false zero.

### Tests for User Story 1

- [x] T005 [P] [US1] Add tests for organization discovery, unauthorized IDs, missing sessions, HTTP 4xx responses, and HTTP 5xx responses in `tests/integration/web_portal/licensing_comparison/test_routes.py`. (delivered: `tests/integration/web_portal/licensing_comparison/test_routes.py`)
- [x] T006 [P] [US1] Add tests for license summary, site license use, inventory, partial failure, rate-limit responses, and installed SDK method availability in `tests/integration/web_portal/licensing_comparison/test_service.py`. (delivered: `tests/integration/web_portal/licensing_comparison/test_service.py`)

### Implementation for User Story 1

- [x] T007 [US1] Implement server-side access discovery with `getSelf` and permitted `listMspOrgs` calls in `src/interfaces/portals/licensing_comparison/service.py`. (delivered: `src/interfaces/portals/licensing_comparison/service.py`)
- [x] T008 [US1] Implement organization, license, and paged inventory reads with `getOrgLicensesSummary`, `getOrgLicensesBySite`, and `getOrgInventory` in `src/interfaces/portals/licensing_comparison/service.py`. (delivered: `src/interfaces/portals/licensing_comparison/service.py`)
- [x] T009 [US1] Implement the page, organization-choice, and comparison routes in `src/interfaces/portals/licensing_comparison/routes.py`. (delivered: `src/interfaces/portals/licensing_comparison/routes.py`)
- [x] T010 [US1] Render organization choices, per-organization statuses, license values, and inventory values in `src/interfaces/portals/licensing_comparison/templates/licensing_comparison.html` and `src/interfaces/portals/licensing_comparison/static/licensing_comparison.js`. (delivered: `src/interfaces/portals/licensing_comparison/templates/licensing_comparison.html`)
- [x] T011 [US1] Send one Mist request at a time. Use `RateLimitingUtils` for pacing, wait 60 seconds after HTTP 429, and retry once in `src/interfaces/portals/licensing_comparison/service.py`. (delivered: `src/interfaces/portals/licensing_comparison/service.py`)

**Checkpoint**: Authorized organizations compare independently. API failures remain visible and never appear as successful zero values.

## Phase 4: User Story 2 - Adjust license balances (Priority: P2)

**Goal**: Let operators add session-only rows and purchase values, then review remaining balances and SUB-AI components.

**Independent Test**: Valid synthetic manual and purchase values update each remaining balance. Invalid values are rejected, and bundle components remain distinct.

### Tests for User Story 2

- [x] T012 [P] [US2] Add tests for non-negative whole-number validation and missing purchase values in `tests/integration/web_portal/licensing_comparison/test_service.py`. (delivered: `tests/integration/web_portal/licensing_comparison/test_service.py`)
- [x] T013 [US2] Add tests for remaining balances and each SUB-AI component in `tests/integration/web_portal/licensing_comparison/test_service.py`. (delivered: `tests/integration/web_portal/licensing_comparison/test_service.py`)

### Implementation for User Story 2

- [x] T014 [US2] Add validated manual rows and purchased amounts to browser `sessionStorage` in `src/interfaces/portals/licensing_comparison/static/licensing_comparison.js`. (delivered: `src/interfaces/portals/licensing_comparison/static/licensing_comparison.js`)
- [x] T015 [US2] Implement license balance and catalog-based bundle component calculations in `src/interfaces/portals/licensing_comparison/service.py`. (delivered: `src/interfaces/portals/licensing_comparison/service.py`)
- [x] T016 [US2] Render manual rows, purchased fields, validation errors, and remaining balances in `src/interfaces/portals/licensing_comparison/templates/licensing_comparison.html` and `src/interfaces/portals/licensing_comparison/static/licensing_comparison.js`. (delivered: `src/interfaces/portals/licensing_comparison/templates/licensing_comparison.html`)

**Checkpoint**: Manual rows and purchased values stay in the active browser session. The page does not send them to a persistent store.

## Phase 5: User Story 3 - Export the comparison (Priority: P3)

**Goal**: Let operators download a CSV that matches the displayed comparison.

**Independent Test**: A synthetic comparison export contains the displayed values, preserves unavailable values, and neutralizes formula-like text.

### Tests for User Story 3

- [x] T017 [P] [US3] Add tests for CSV columns, source attribution, manual and purchased values, unavailable results, formula neutralization, and export failures in `tests/integration/web_portal/licensing_comparison/test_export.py`. (delivered: `tests/integration/web_portal/licensing_comparison/test_export.py`)

### Implementation for User Story 3

- [x] T018 [US3] Implement formula-safe CSV rows, source attribution, and an explicit export through `DataExporter.write_with_format_selection` in `src/interfaces/portals/licensing_comparison/service.py`. (delivered: `src/interfaces/portals/licensing_comparison/service.py`)
- [x] T019 [US3] Add the export route and safe data-directory download response in `src/interfaces/portals/licensing_comparison/routes.py`. (delivered: `src/interfaces/portals/licensing_comparison/routes.py`)
- [x] T020 [US3] Add the export action, attribution, and export status to `src/interfaces/portals/licensing_comparison/templates/licensing_comparison.html` and `src/interfaces/portals/licensing_comparison/static/licensing_comparison.js`. (delivered: `src/interfaces/portals/licensing_comparison/templates/licensing_comparison.html`)

**Checkpoint**: The CSV matches displayed values. The feature writes no report until the operator requests export.

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Verify portal integration, documentation, and migration boundaries.

- [x] T021 [P] Add the feature page, navigation, stable selectors, and missing-session smoke checks to `tests/e2e/web_portal/test_portal_smoke.py`. (delivered: `tests/e2e/web_portal/test_portal_smoke.py`)
- [x] T022 Update `specs/live/20261013-125122-mist-org-licensing-comparison/quickstart.md` with isolated test commands and observed results. (delivered: `specs/live/20261013-125122-mist-org-licensing-comparison/quickstart.md`)
- [x] T023 Rerun focused tests, portal smoke tests, formatting, lint, type, complexity, and Bandit checks after the service refactor. (52 tests passed at 93.05 percent feature coverage; Ruff, Black, Mypy, complexity, and Bandit passed.)
- [x] T024 Check the feature package layout, infrastructure files, and final scope. (Five direct Python modules pass the package guard. Infrastructure files remain unchanged. Portal registration follows the narrow handoff.)
- [x] T025 Add SDK transport contract tests for shared-session authentication, supported endpoint use, pagination, the single rate-limit retry, and redaction of tokens and exception text in `tests/integration/web_portal/licensing_comparison/test_transport_contract.py`. (delivered: `tests/integration/web_portal/licensing_comparison/test_transport_contract.py`)
- [x] T026 Add browser tests for session-state persistence through page reload and in-page navigation, empty state in a new browser session, and input validation in `tests/e2e/web_portal/licensing_comparison/test_session_state.py`. (delivered: `tests/e2e/web_portal/licensing_comparison/test_session_state.py`)
- [x] T027 Review the new code against all seven constitutional principles. Verify class-based ownership, function limits, inline comments, ASCII structured logs, action logs, and secret redaction. (Class responsibilities and function limits pass. API and export actions use parameterized ASCII logs. Transport tests verify secret redaction. No production deployment occurred.)
- [x] T028 Update `README.md` with a link to the comparison page. Add `documentation/licensing-comparison.md` and `changelog.d/issue-4197-mist-org-licensing-comparison.md` with an Added bullet that names issue #4197. (delivered: `README.md`, `documentation/licensing-comparison.md`, `changelog.d/issue-4197-mist-org-licensing-comparison.md`)
- [x] T029 Run local gates, build the feature manifest, stage explicit files, commit, rebase on `origin/main`, and rerun affected gates before push. (Two commits are rebased on `origin/main`. Focused tests, coverage, Ruff, Black, Mypy, complexity, Bandit, STE, and the committed test-quality gate passed.)
- [x] T031 Resolve CI package and template regressions for issue #4197. Keep feature navigation conditional on route registration, place E2E tests under the existing portal package, and keep the feature within five direct Python modules. (101 focused tests passed. The nested package and E2E package guards passed. Coverage is 93.05 percent.)
- [ ] T030 Complete final CI and the authorized squash merge for implementation PR #4245. Image verification, deployment, and health checks remain outside the current authorization.

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

## Implementation Boundary

- The feature owns `src/interfaces/portals/licensing_comparison/__init__.py`, `routes.py`, `service.py`, `static/licensing_comparison.css`, `static/licensing_comparison.js`, and `templates/licensing_comparison.html`.
- The feature owns `tests/integration/web_portal/licensing_comparison/__init__.py`, `test_export.py`, `test_routes.py`, `test_service.py`, and `test_transport_contract.py`.
- The feature owns `tests/e2e/web_portal/licensing_comparison/conftest.py`, `test_routes.py`, and `test_session_state.py`.
- The feature owns `documentation/licensing-comparison-attribution.md`, `documentation/licensing-comparison.md`, this task record, and `quickstart.md`.
- The narrow handoff authorizes this feature to register its blueprint and navigation link in `web_portal/app.py` and `web_portal/templates/base.html`. Keep all existing WAN changes from draft PR #4208.
- The feature does not own `compose.yml`, `requirements.txt`, `requirements-dev.txt`, or `MistHelper.py`.
- T003 and T021 are complete under the narrow handoff. The changes add licensing registration and smoke coverage without removing or rewriting WAN behavior from draft PR #4208.
- T023 is complete. The focused tests and listed local quality gates passed after the service refactor.
- T027 is complete. No production deployment occurred because T030 requires approval.
- T024 passed. The package guard counts five direct Python modules. The E2E root keeps its five existing entries, and no database, Redis service, or port was added.
- T028 is complete. The page is registered and the README and release note describe the delivered feature.
- T029 is complete. T030 remains open for final CI and the authorized merge. No deployment is authorized.
- Use synthetic Mist responses. Do not use production credentials.

## Rebase Verification

The implementation rebased cleanly onto `096f12a59` from `origin/main`. The local environment initially held `mistapi` 0.64.0.
Seven checks failed because that installed SDK lacked methods required by the merged SDK repair.
Installing `mistapi==0.64.1` restored those methods without a dependency-manifest change.
The same selected tests then reported `256 passed in 3.42s`, with 93.05 percent feature coverage.
Ruff, Black, the CI mypy command, Bandit, and the complexity gate passed.
The mypy command checked 850 source files. Black checked 17 Python files.
No licensing, WAN, or shared portal code changed during this rebase.
