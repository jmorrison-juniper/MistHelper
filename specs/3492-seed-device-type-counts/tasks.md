# Tasks: The browser seed captures hold the counts of a real capture

**Issue**: #3492 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Tests**: Each new test of the count map and of the device type phrase must
fail on the old seed. The row height test of three widths can pass on the old
seed, because the short fallback text fits the row. Each test task comes
before its code task.

## Phase 1: Setup

- [x] T001 Create the worktree `MistHelper-i3492` from `main`, and run
  `scripts/bootstrap_worktree.py`. Move the branch to `main` at `e4e8faba`,
  which holds the repair of #3486.
- [x] T002 Write `spec.md`, `research.md`, `plan.md`, and
  `checklists/requirements.md` in `specs/3492-seed-device-type-counts/`.
- [x] T003 File issue #3494 for the state gap of the seed device index. The
  research of this issue found it.

## Phase 2: User Story 2 (the direct test)

- [x] T004 Write `tests/e2e/upgrade_portal/test_seed_counts.py`. For each of
  the five seeds, build a count map with the shipped builder from the lists
  of the seed. Compare the result with the count map of the seed. Replace the
  builder with a marker, and read the marker in each seed. Read the guest
  count of the Tier 3 seed.

## Phase 3: User Stories 1 and 3 (the browser journey)

- [x] T005 Write `tests/e2e/upgrade_portal/test_history_device_types_journey.py`.
  Open `/history?limit=200`. Read the text and the `title` attribute of the
  Device types cell of each seed row. Read the Clients cell of the Tier 3
  row. Measure the height of each seed row at 1024, 1280, and 1440 pixels.
  Log the width that each phrase needs and the width that each cell gives.
  Save a screenshot of each width.
- [x] T006 Run T004 and T005 on the old seed. Record the red result in this
  file.

**Red result (T006)**: On 2026-09-27 in Microsoft Edge, the old seed gave 14
failures and 3 passes in 36.23 seconds. The 12 cases of the direct test
failed. The phrase test and the Clients test of the journey failed. The 3
row height cases passed, because the short fallback text fits the row.

## Phase 4: The seed change

- [x] T007 In `tests/e2e/upgrade_portal/conftest.py`, add the helper
  `stand_in_counts`. It reads the builder through the module name at call
  time. Add the action logs.
- [x] T008 In `stand_in_capture`, replace the hand-written count map with a
  call to the helper. In `stand_in_tier3_capture`, call the helper again after
  the guest list.

## Phase 5: Proof

- [x] T009 Run T004 and T005 on the new seed. Read each screenshot. Record the
  green result and the measured widths in this file and in research R4.

**Green result (T009)**: The new seed gave 17 passes in 16.54 seconds. The
screenshots showed the phrase in each seed row, and the Tier 3 row read 4
clients. Each row stood on one line.

The page of one site uses a second width set, so the row height test then
added that page. That run gave 20 passes in 20.03 seconds. The three new
cases ran on the new seed only. They measure the row height, which the old
seed also met. Research R4 holds the six measures. The phrase clips at each
width on each page, and issue #3495 holds that finding.
- [x] T010 Run every test under `tests/e2e/upgrade_portal/`. Explain or fix
  each changed result. Record the result in this file.

**Folder result (T010)**: The run in Edge gave 297 passes and 19 skips in
1102.72 seconds. No test failed. One skip is the known skip at
`test_capture.py:745`, which issue #3380 holds. The other 18 skips are in
`test_two_operators.py`, and each one reads a 400 answer from the lock route.

This change did not cause those 18 skips. The file alone gave 19 passes in
88.24 seconds. With `test_run_controls` before it, the pair gave 45 passes in
120 seconds. A retry test leaves the site lock, and the sign-in tests between
the two files took more than the 300 seconds of the lock cooldown. Issue
#3497 holds the lock leak. Issue #3496 holds the slow sign-in check. The CI
smoke job on `main` gave 413 passes and 1 skip, because its gap is shorter.
- [x] T011 Run the gates. Record the result in this file.

**Gate result (T011)**: `py_compile`, `ruff`, and `black` passed on the three
changed test files. `mypy` with the `MYPY_PATHS` list of the CI workflow gave
no issue in 528 source files. The test quality gate first found one weak
assertion in the clients test, because it does not count a Playwright
`expect` call. The test now compares one mapping of the counted texts. The
gate then gave 0 new findings in 2 files, and the two files gave 20 passes in
29.07 seconds.
- [ ] T012 Open the pull request. Merge it by hand after each check passes.
- [ ] T013 Comment on #3492 with the result. No deploy is necessary.

## Dependencies

- T002 comes before T004.
- T004 and T005 come before T006.
- T006 comes before T007 and T008.
- T007 and T008 come before T009.
- T009 comes before T010 and T011.
- T010 and T011 come before T012, and T012 comes before T013.
