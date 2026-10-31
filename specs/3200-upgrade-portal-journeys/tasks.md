# Tasks: Upgrade portal journey harness

**Input**: `spec.md`, `plan.md`, `data-model.md`, `research.md`, `quickstart.md`, `contracts/`

**Scope**: Use only loopback services and stand-in cloud data. Do not start a live upgrade or contact Mist Cloud.

## Phase 1: Setup

**Purpose**: Verify the local journey entry point and its opt-in rule.

- [x] T001 Verify the default skip and opt-in behavior in `tests/e2e/upgrade_portal/journeys/conftest.py`.

## Phase 2: Foundational

**Purpose**: Provide a controlled stand-in status for browser journeys without Playwright route interception.

- [x] T002 Add a test-only status control to `tests/e2e/upgrade_portal/conftest.py` and `tests/e2e/upgrade_portal/journeys/conftest.py`.

## Phase 3: User Story 1 - Drive multi-site upgrades to completion (Priority: P1)

**Goal**: Complete each multi-site family combination through the local stand-in cloud.

**Independent Test**: Each selected family shows a completed child and a completed aggregate status in the browser.

- [x] T003 [US1] Replace status route interception with stand-in cloud status control in `tests/e2e/upgrade_portal/journeys/test_upj_multisite_journeys.py`.
- [x] T004 [US1] Assert completed child records for each family combination in `tests/e2e/upgrade_portal/journeys/test_upj_multisite_journeys.py`.

## Phase 4: User Story 2 - Drive single-site upgrades to completion (Priority: P1)

**Goal**: Complete a single-site upgrade after the operator starts it.

**Independent Test**: The browser journey reaches the completed run state through the local stand-in cloud.

- [x] T005 [US2] Drive and assert the completed single-site run in `tests/e2e/upgrade_portal/journeys/test_upj_single_site_journeys.py`.

## Phase 5: User Story 3 - Publish current parity evidence (Priority: P1)

**Goal**: Match every capability in the inventory to a mode status, journey, and issue when needed.

**Independent Test**: The matrix has all 54 capability identifiers, valid mode statuses, and an issue for each gap.

- [x] T006 [US3] Refresh per-mode evidence for C01 through C54 in `tests/e2e/upgrade_portal/journeys/parity_matrix.json`.
- [x] T007 [US3] Align the readable matrix with the JSON inventory in `specs/3200-upgrade-portal-journeys/parity-matrix.md`.

## Phase 6: User Story 4 - Prove safety rules under faults (Priority: P2)

**Goal**: Show that refusal, replay, and lock faults cannot start an unsafe second write.

**Independent Test**: Each fault journey records the refusal, keeps the write count safe, and reports zero trap hits.

- [x] T008 [US4] Add fault checks for lock, replay, and refusal paths in `tests/e2e/upgrade_portal/journeys/test_upj_multisite_journeys.py`.
- [x] T009 [US4] Verify fault outcomes and write counts in `tests/e2e/upgrade_portal/journeys/test_upj_multisite_journeys.py`.

## Phase 7: User Story 5 - Prove device faults and recovery (Priority: P2)

**Goal**: Record cloud-read and empty-version failures without changing product behavior.

**Independent Test**: The #3393 fault keeps the plan absent, and the #3394 case names the dropped checked family.

- [x] T010 [US5] Add a local stand-in cloud read-fault journey for #3393 in `tests/e2e/upgrade_portal/journeys/test_upj_multisite_journeys.py`.
- [x] T011 [US5] Assert the stored plan for an empty checked-family version in `tests/contract/upgrade_portal/test_org_upgrade_routes.py`.

## Phase 8: User Story 6 - Inspect journey artifacts (Priority: P2)

**Goal**: Give an engineer enough local evidence to inspect each journey result.

**Independent Test**: The runner links each outcome to its screenshot, step record, and error evidence.

- [x] T012 [US6] Verify recorder output for passed and failed journeys in `tests/e2e/upgrade_portal/journeys/evidence.py`.
- [x] T013 [US6] Verify the run index and outcome counts in `tests/e2e/upgrade_portal/journeys/run_journeys.py`.

## Phase 9: User Story 7 - Measure journey performance (Priority: P3)

**Goal**: Rank slow pages and API calls in the local performance report.

**Independent Test**: The report lists ranked page and API samples with measured timing values.

- [x] T014 [US7] Add ranked page and API timing entries to `tests/e2e/upgrade_portal/journeys/test_performance_journeys.py`.
- [x] T015 [US7] Assert ranking order and report shape in `tests/e2e/upgrade_portal/journeys/test_performance_journeys.py`.

## Phase 10: User Story 8 - Prove cross-cutting journeys (Priority: P3)

**Goal**: Check accessibility, recovery, and layout across the shared portal pages.

**Independent Test**: The journey checks pass, or each confirmed product defect has its own linked issue.

- [x] T016 [US8] Recognize implicit labels in `tests/e2e/upgrade_portal/journeys/test_crosscut_journeys.py`.
- [x] T017 [US8] Select an enabled reboot control before the invalid-value check in `tests/e2e/upgrade_portal/journeys/test_upj_multisite_journeys.py`.
- [x] T018 [US8] Identify each failing narrow viewport and record a separate issue in `tests/e2e/upgrade_portal/journeys/test_crosscut_journeys.py`.
- [x] T019 [US8] Map each strict cross-cutting xfail to its issue in `tests/e2e/upgrade_portal/journeys/test_crosscut_journeys.py`.

## Final Phase: Polish and cross-cutting work

**Purpose**: Publish a validated stage and keep the remaining work visible.

- [x] T020 Add a bounded journey job to `.github/workflows/ci.yml`. Run the isolated harness after the shared browser gate, then upload its reports and screenshots.
- [x] T021 Run the targeted gates and record exact results in `specs/3200-upgrade-portal-journeys/quickstart.md` and `changelog.d/issue-3200-upgrade-portal-e2e-parity.md`.

## Dependencies and execution order

- Setup and foundational work must finish before the user stories.
- User Stories 1 and 2 depend on the status control in T002.
- User Story 3 can run beside User Stories 1 and 2.
- User Story 7 can run beside User Story 3 because it changes separate files.
- User Stories 4, 5, and 8 depend on their test fixtures and issue records.
- Polish work follows the selected user stories. T020 runs after the shared browser gate.

## Parallel opportunities

- T006 and T014 use separate files and can proceed in parallel.
- T016 and T017 use separate test files and can proceed in parallel.
- User Story 3 and User Story 7 can proceed while the journey control is built.

## Implementation strategy

1. Complete T001 and T002.
2. Deliver User Stories 1 and 2 as the minimum journey proof.
3. Refresh the parity and performance evidence.
4. Complete fault and cross-cutting checks.
5. Add the bounded CI job after the shared browser gate.

## Notes

- Keep each browser request on loopback.
- Do not use a Mist credential or a production store.
- Do not change product behavior for #3394 without its required human review.
- Keep #3200 open until every acceptance criterion passes.
