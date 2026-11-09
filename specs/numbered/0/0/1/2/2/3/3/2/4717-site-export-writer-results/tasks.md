# Tasks: Site export write results

## Phase 1: Setup

- [x] T001 Verify the base, reservation, and open pull request ownership for the paths in `plan.md`.

## Phase 2: Foundation

- [x] T002 Reproduce the two failures with the independent synthetic test and preserve the results in the session artifacts.

## Phase 3: User Story 1

**Goal**: Report failed writes without false success messages.

**Independent test**: Both site exports report an error for a failed writer and retain all successful and edge-case contracts.

- [x] T003 [US1] Add explicit writer-result and edge-case coverage in `tests/unit/export/test_site_asset_and_events_exporters.py`.
- [x] T004 [P] [US1] Check the writer result in `src/operations/exporting/export/site_application_list_exporter.py`.
- [x] T005 [P] [US1] Check the writer result in `src/operations/exporting/export/site_system_events_exporter.py`.

## Phase 4: Verification and Local Delivery

- [x] T006 Run synthetic tests and applicable local checks for the three paths in `plan.md`.
- [x] T007 Add `changelog.d/issue-4717-site-export-writer-results.md` and compare the requirements with the implementation.
- [x] T008 Prepare local commit and review export commands for the paths in `plan.md`.

## Dependencies and Execution

T001 precedes T002. T002 precedes T003. T003 precedes T004 and T005.
T004 and T005 can run independently because they modify different files.
T006 follows both repairs. T007 follows verification. T008 follows all other tasks.
One owner executes the tasks serially to preserve the shared test reservation.
Optional intermediate commit hooks remain unused.

## Verification Results

The independent baseline produced two failed cases and six passing controls.
The combined independent and shared tests passed all 43 cases in both file orders.
Each run recorded zero socket, DNS, and SQLite attempts.
The guard denial test rejected each intentional service attempt.
The structural, changelog, and test-quality input guards produced 29 passes and one expected skip.
The skipped changelog test requires a pull request event. Publication remains on hold.
The source-wide Pylint gate passed at 9.92/10.
The targeted Pylint diagnostic reported four existing findings and scored 9.49/10.
The same findings appear on the base, where each source file scores 9.43/10.
Targeted lint, format, types, compile, security, complexity, docstrings, symbols, STE, and link checks passed.
The precommit test-quality scan examined one test file and reported zero new findings.
The session artifacts preserve the exact commands and complete output.
The complete rename-aware ownership check examined 692 paths across 27 stable pull requests and found no overlap.
