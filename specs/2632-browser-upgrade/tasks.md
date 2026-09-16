# Tasks: Browser upgrade start journey

**Input**: Design documents from `specs/2632-browser-upgrade/`

**Prerequisites**: `plan.md` and `spec.md`

**Tests**: The issue requires browser, unit, and contract validation.

## Phase 1: Setup

- [x] T001 Read GitHub issue #2632 and issue #2615. Evidence: issue details show the reserved-domain guard and the browser hang report.
- [x] T002 Create the isolated worktree `..\MistHelper-2632-browser-upgrade`. Evidence: worktree boots with mistapi 0.64.0.
- [x] T003 Install Chromium for Playwright in the worktree. Evidence: `python -m playwright install chromium` completed.

---

## Phase 2: Foundational

- [x] T004 [US1] Reproduce the current reachable-operator behavior. Evidence: the suite finished and did not hang on the current branch.
- [x] T005 [US2] Confirm the default operator remains reserved. Evidence: `STAND_IN_EMAIL` stays `e2e.operator@example.invalid`.
- [x] T006 [US3] Confirm the E2E timeout guard exists. Evidence: `tests/e2e/conftest.py` applies 120 seconds.

---

## Phase 3: User Story 1 - Measure the start path (Priority: P1)

**Goal**: The browser suite clicks the start button and proves the start route.

**Independent Test**: `python -m pytest tests/e2e/upgrade_portal/test_upgrade.py::TestUpgradeStart -q --no-cov`

- [x] T007 [US1] Add a start-ready seeded run in `tests/e2e/upgrade_portal/conftest.py`. Evidence: the seed writes `e2e-start-ready-run-0001`.
- [x] T008 [US1] Add `TestUpgradeStart` in `tests/e2e/upgrade_portal/test_upgrade.py`. Evidence: the test asserts the 202 start response.
- [x] T009 [US1] Verify the new start test. Evidence: the targeted browser test passed.

---

## Phase 4: User Story 2 - Keep reserved addresses safe (Priority: P2)

**Goal**: Read-only browser tests keep the reserved operator. Write-path tests use the firmware operator fixture.

**Independent Test**: Run the full browser suite and inspect pass and skip counts.

- [x] T010 [US2] Keep `STAND_IN_EMAIL` unchanged in `tests/e2e/upgrade_portal/conftest.py`. Evidence: no default reachable address is committed.
- [x] T011 [US2] Use `firmware_operator_page` for the start proof. Evidence: the test fixture carries `FIRMWARE_EMAIL`.

---

## Phase 5: User Story 3 - Bound future hangs (Priority: P3)

**Goal**: A future browser hang fails within 120 seconds.

**Independent Test**: Run E2E tests and confirm the timeout plug-in loads.

- [x] T012 [US3] Keep the E2E timeout guard active in `tests/e2e/conftest.py`. Evidence: pytest lists `timeout-2.4.0`.
- [x] T013 [US3] Include the timeout result in the pull request body. Evidence: local gate output names the plug-in.

---

## Phase 6: Validation and Delivery

- [x] T014 Run `python -m ruff check .`. Evidence: ruff reported all checks passed.
- [x] T015 Run `python -m black --check .`. Evidence: black reported 1516 files left unchanged.
- [x] T016 Run `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`. Evidence: mypy reported no issues in 466 source files.
- [x] T017 Run `python -m pytest tests/e2e -q`. Evidence: 239 passed and 4 skipped in 375.19 seconds.
- [x] T018 Run `python -m pytest tests/unit/upgrade_portal tests/contract/upgrade_portal -q`. Evidence: 4215 passed in 17534.63 seconds.
- [x] T019 Create the release-note fragment in `changelog.d/issue-2632-browser-upgrade.md`. Evidence: the fragment has one `Fixed` heading.
- [ ] T020 Commit, push, open the pull request, wait for checks, and merge.

## Dependencies & Execution Order

- T001 through T003 must finish before code changes.
- T004 through T006 must finish before browser test changes.
- T007 must finish before T008.
- T008 must finish before T009 and T017.
- T014 through T018 must pass before T020.

## Parallel Opportunities

- T014 and T015 can run in sequence only because they read the full tree.
- T017 and T018 can run separately after the code change.
