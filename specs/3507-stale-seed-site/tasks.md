# Tasks: The two stale seed runs move to a site of their own

**Input**: The design documents in `specs/3507-stale-seed-site/`
**Prerequisites**: plan.md, spec.md, and research.md

**Tests**: The spec asks for tests. Write each test before the code that it proves.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel, because it changes a different file.
- **[Story]**: The user story that the task serves.

## Phase 1: Red

- [x] T001 [P] [US4] Write the seed-site guard and its decision tests in `tests/unit/upgrade_portal/test_e2e_seed_run_sites.py`.
- [x] T002 [P] [US2] Write the direct tests of `StaleRunSeeds` in `tests/unit/upgrade_portal/test_e2e_stale_run_seeds.py`.
- [x] T003 [US3] Change the fixture `scheduled_run_page` in `test_run_controls/test_existing.py`, so a missing schedule region fails (FR-004).
- [x] T004 Run the two direct test files. Record the guard failure that names both stale seed runs, and the collection error (SC-005).
- [x] T005 Run `test_existing.py` alone in Edge. Record 0 skips and the two new errors (SC-006).

## Phase 2: Implementation

- [x] T006 [US2] Add `tests/e2e/upgrade_portal/stale_run_seeds.py` with the stale site, the two run keys, and `StaleRunSeeds`.
- [x] T007 [US1] Change `tests/e2e/upgrade_portal/conftest.py`, so the seed writer calls `StaleRunSeeds.write` and the old records and keys go away.
- [x] T008 [US2] Change `test_run_controls/test_bulk.py`, so it imports the keys and takes the lock of the stale site (FR-003).
- [x] T009 [US1] Correct the comment of the 409 path and the module text of `test_existing.py`.
- [x] T010 Run the two direct test files, and record the pass (SC-005).

## Phase 3: Browser green

- [x] T011 Run `test_existing.py` alone in Edge (SC-001).
- [x] T012 Run `test_bulk.py` alone in Edge (SC-002).
- [x] T013 Run the folder `test_run_controls` in Edge (SC-003).
- [x] T014 Run `test_capture.py` and `test_existing.py` together, and record the 409 path for the new issue.
- [x] T015 Run all of `tests/e2e/upgrade_portal` in Edge (SC-004).
- [x] T016 Run py_compile, ruff, black, mypy, the test quality gate, `tests/guardrails`, and the STE linter.

## Phase 4: Delivery

- [x] T017 File the issue for the live run that `test_capture.py` leaves on the first site. Issue #3511 holds it.
- [ ] T018 Commit the change, push the branch, and open the pull request with `Closes #3507`.
- [ ] T019 Wait for each check and CodeQL, then merge the pull request.
- [ ] T020 Post the result on issue #3507, and remove the worktree.

## Dependencies

- Phase 1 comes before Phase 2, because each test must fail first.
- T003 comes before T005, because the red browser run proves the new fixture.
- T006 comes before T007 and T008, because both files import the new module.
- Phase 3 comes after Phase 2.
- T014 comes before T017, because the issue needs the evidence.

## Notes

The first run of the test quality gate reported 5 new findings.

- Four findings came from `test_bulk.py`. The edit moved 4 known baseline findings by 9 lines, and the baseline keys each finding by its line.
- The fifth finding named a missing empty-input case in `test_e2e_stale_run_seeds.py`.

The repair added a plain assertion to each of the 4 bulk tests, and it added a test for an empty record. The repair then removed the 4 entries of `test_bulk.py` from `.github/test-quality-baseline.json`. The second run of the gate reported 0 new findings.
