# Tasks: The browser trail guard reads the checkout trail from the root guard

**Input**: The design documents in `specs/3512-trail-guard-order/`
**Prerequisites**: plan.md, spec.md, and research.md

**Tests**: The spec asks for tests. Write each test before the code that it proves.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel, because it changes a different file.
- **[Story]**: The user story that the task serves.

## Phase 1: Red

- [x] T001 [US2] Write three direct tests in `tests/unit/upgrade_portal/test_e2e_audit_trail_isolation.py`. The tests cover a build with no checkout trail, a late build from the root guard, and a build with no root guard.
- [x] T002 Run the direct test file on the old code. Record the three failures (SC-004).
- [x] T003 [US1] Run `test_existing.py` alone in Edge on the old code. Record the path of the guard line of #3498 (SC-001).

## Phase 2: Implementation

- [x] T004 [US2] Change `tests/support/upgrade_portal_e2e/records/audit.py`: make `checkout_trail` required, add `NO_ROOT_GUARD`, and add the builder `for_session`.
- [x] T005 [US1] Change the fixture `checkout_audit_trail_guard` in `tests/e2e/upgrade_portal/conftest.py`, so it names the root guard and calls the builder.
- [x] T006 [US3] Change the child call in `build_stand_in_app`, so it names `lock.audit_trail_path()` explicitly.
- [x] T007 Run the direct test file, and record the pass (SC-004).

## Phase 3: Browser green

- [x] T008 Run `test_existing.py` alone in Edge (SC-001 and SC-005).
- [x] T009 Run `test_capture.py` and `test_existing.py` together in Edge (SC-002).
- [x] T010 Run `test_audit_log_journey.py` alone in Edge.
- [x] T011 Run all of `tests/e2e/upgrade_portal` in Edge (SC-003).
- [x] T012 Run py_compile, ruff, black, mypy, the test quality gate, `tests/guardrails`, and the STE linter.

## Phase 4: Delivery

- [ ] T013 Commit the change, push the branch, and open the pull request with `Closes #3512`.
- [ ] T014 Wait for each check and CodeQL, then merge the pull request.
- [ ] T015 Post the result on issue #3512, and remove the worktree.

## Dependencies

- Phase 1 comes before Phase 2, because each test must fail first.
- T004 comes before T005 and T006, because both calls need the new signature.
- Phase 3 comes after Phase 2.
- T011 comes after T008, T009, and T010, because the full run takes the longest time.

## Notes

The red runs used the old code on the branch at `8c4e948e`.

- The direct test file gave 3 failed and 10 passed in 5.40 s.
- `test_existing.py` alone gave 11 passed in 39.54 s. The guard line of #3498 named `<basetemp>\test_the_run_page_holds_the_re0\site-lock-trail\upgrade_takeover_audit.jsonl`.

The green runs used the new code.

- The direct tests of the isolation class and of the root guard gave 25 passed in 1.85 s.
- `test_existing.py` alone gave 11 passed in 31.89 s. Both guard lines named `<worktree>\data\upgrade_takeover_audit.jsonl`.
- The full browser run gave 316 passed and 1 skipped (#3380) in 798.38 s. The server sent 5,513 responses, the same count as the full run of #3507.
