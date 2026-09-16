# Tasks: Phantom Mist SDK Calls

**Input**: Design documents from `specs\2717-phantom-sdk-calls\`

**Prerequisites**: `plan.md`, `spec.md`

**Tests**: Tests are required by issue #2717.

## Phase 1: Setup

- [x] T001 Read issue #2717 and add the `in-progress` label. (delivered: GitHub issue #2717)
- [x] T002 Create `fix/2717-phantom-sdk-calls` from current `origin/main`. (delivered: worktree `..\MistHelper-2717-phantom-sdk`)
- [x] T003 Verify `mistapi` version 0.64.0 and `getSiteInfo` signature. (delivered: command output)

## Phase 2: Specification

- [x] T004 Create `specs\2717-phantom-sdk-calls\spec.md`. (delivered: specs\2717-phantom-sdk-calls\spec.md)
- [x] T005 Create `specs\2717-phantom-sdk-calls\plan.md`. (delivered: specs\2717-phantom-sdk-calls\plan.md)
- [x] T006 Create `specs\2717-phantom-sdk-calls\tasks.md`. (delivered: specs\2717-phantom-sdk-calls\tasks.md)

## Phase 3: User Story 1 - Resolve the site name

**Goal**: Each targeted path uses `getSiteInfo` and returns the known site name.

**Independent Test**: Run the five unit test files named in the plan.

- [x] T007 [US1] Repair `src\device\virtual_chassis.py`. (delivered: src\device\virtual_chassis.py)
- [x] T008 [US1] Repair `src\export\site_anomaly_exporter.py`. (delivered: src\export\site_anomaly_exporter.py)
- [x] T009 [US1] Repair `src\export\site_insights\device_metric_operation.py`. (delivered: src\export\site_insights\device_metric_operation.py)
- [x] T010 [US1] Repair `src\export\site_insights\site_metric_operation.py`. (delivered: src\export\site_insights\site_metric_operation.py)
- [x] T011 [US1] Repair `src\refactors\serial_cc\site_client_insights.py`. (delivered: src\refactors\serial_cc\site_client_insights.py)
- [x] T012 [US1] Add five mocked known-site tests. (delivered: tests\unit\*)

## Phase 4: User Story 2 - Report lookup faults

**Goal**: A Mist API site lookup fault appears in logs with the site identifier.

**Independent Test**: Run a unit test that injects HTTP status 503.

- [x] T013 [US2] Replace silent handlers with logged fault handling. (delivered: five source files)
- [x] T014 [US2] Add an API fault test that asserts an error log. (delivered: tests\unit\export\site_insights\test_site_metric_operation_wave9.py)

## Phase 5: Validation and Delivery

- [x] T015 Run full requested local gates. (delivered: command output)
- [x] T016 Prove no phantom `src` calls remain. (delivered: empty grep output)
- [x] T017 Create `changelog.d\issue-2717-phantom-sdk-calls.md`. (delivered: changelog.d\issue-2717-phantom-sdk-calls.md)
- [ ] T018 Commit, push, open the pull request, and wait for checks. (pending: pull request)
- [ ] T019 Verify merge and issue closure. (pending: merge)

## Dependencies & Execution Order

- Phase 1 blocks all implementation work.
- Phase 2 records the agreed scope before edits.
- Phase 3 blocks Phase 4 because the handlers sit around the repaired calls.
- Phase 5 runs after all source and test changes.
