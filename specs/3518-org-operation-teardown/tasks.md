# Tasks: A failed multi-site journey ends each operation that it started

**Input**: The design documents in `specs/3518-org-operation-teardown/`
**Prerequisites**: plan.md, spec.md, and research.md

**Tests**: The spec asks for tests. Write each test before the code that it proves.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel, because it changes a different file.
- **[Story]**: The user story that the task serves.

## Phase 1: Red

- [X] T001 [US4] Write the direct tests in `tests/unit/upgrade_portal/test_e2e_org_operations.py`. Cover each start decision, the ledger, the tap, each teardown path, and the token read.
- [X] T002 Run the direct test file on the old code. Record the failures.

## Phase 2: The rules

- [X] T003 [US1] Write `tests/support/upgrade_portal_e2e/org_operations.py` with `OrgStartAnswer`, `OrgOperationLedger`, `OrgStartTap`, `OrgOperationCalls`, and `OrgOperationRelease`. The first T009 run added `OrgStartTap` (research Decision 1).
- [X] T004 Run the direct test file, and record the pass.

## Phase 3: The fixtures and the start step

- [X] T005 [US2] Add the fixture `org_operation_ledger` to `tests/e2e/upgrade_portal/conftest.py`. It registers the tap as a route of the context. Change `firmware_operator_page` to end each recorded operation before it closes the page.
- [X] T006 [US3] Add `START_ANSWER_TIMEOUT_MS` and the class `OrgStartSteps` with `open_progress` to `tests/e2e/upgrade_portal/test_org_start_double_click.py`. Use the new step in `OrgFormSteps.start`, in the double-click test, and in the retry test. The new class also holds `is_start_answer` and `wait_for_hold`, so each class keeps five methods or fewer.
- [X] T007 [US1] Remove `OrgJourneyCleanup.cancel_if_running` and the fixture `operator_page`. Each test of the module takes `firmware_operator_page` (FR-007).
- [X] T008 [US1] Write the journey `tests/e2e/upgrade_portal/test_org_operation_teardown.py`.

## Phase 4: Browser proof and browser green

- [X] T009 [US1] Run a temporary test in Edge that stops on purpose after the Start request. Read the server log and the next status read (SC-001). Delete the temporary test. The first run found that a handler of the answer event lost 2 of 2 bodies, so the tap replaced it. The second run, with the tap, recorded 2 of 2 starts. The status read after the teardown showed `cancelled`, and the hold check found 0 leaked holds.
- [X] T010 Run the six multi-site modules and the new journey in Edge. Record the result and the time of the teardown (SC-002 and SC-004). The first run put the double-click module first, so the missing pre-check journey failed on its order rule (issue #3537). That run also showed that a screenshot times out while a route holds a navigation, so the journey takes no screenshot during the hold. The run in file-name order passed 25 tests with the one skip of #3380, in 105.42 seconds. Each teardown after a cancel on the page took 27 to 76 ms.
- [X] T011 Run all of `tests/e2e/upgrade_portal` in Edge. Record the result and the hold check (SC-003). The run passed 318 tests with the one skip of #3380, in 929.81 seconds. The run of issue #3511 took 1455.80 seconds for 316 tests. The hold check found 0 leaked holds, and the live-run check found 0 leaked runs in 63 modules.
- [X] T012 Run py_compile, ruff, black, mypy, the test quality gate, `tests/guardrails`, and the STE linter. The first gate run found 4 new findings: no empty-body test and no malformed-JSON test in the two new test modules. The direct tests now prove an empty body and a cut body for the Start answer, the status read, and the cancel. The journey now reads the expected id with the `JOB_PATH` rule of the journeys, not with the rule under test. The gate then found 0 new findings. The direct tests pass 64 cases, the journey passed 2 tests in Edge in 18.16 seconds, and `tests/guardrails` passed 338 tests with 2 skips.

## Phase 5: Delivery

- [ ] T013 Commit the change, push the branch, and open the pull request with `Closes #3518`.
- [ ] T014 Wait for each check, CodeQL included. Merge the pull request with a squash merge and the head match.
- [ ] T015 Post the result on #3518, remove the worktree, and write the MERGED line in the coordination log.

## Dependencies

- T002 needs T001. T003 needs T002. T004 needs T003.
- T005 through T008 need T004.
- T009 through T011 need T005 through T008.
- T012 needs T011. Phase 5 needs Phase 4.
