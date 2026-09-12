# Tasks: Complete Tier 3 Capture Output

## Phase 1: Tests that expose the defect

- [ ] T001 Extend the unit capture fixture with guest and Tier 3 records.
- [ ] T002 Add export tests for all ten stable row kinds and `details_json`.
- [ ] T003 Add table tests for Tier 3 rows, empty sections, and row caps.
- [ ] T004 Add an E2E stand-in Tier 3 capture with one row in each section.
- [ ] T005 Add browser assertions for every table and each export kind.

## Phase 2: Implementation

- [ ] T006 Extend `capture/export.py` with Tier 3 row kinds and safe detail serialization.
- [ ] T007 Extend `capture/tables.py` with guest and Tier 3 section views.
- [ ] T008 Pass the new section views through `app/routes/capture.py`.
- [ ] T009 Render the new bounded tables and Tier 2 note in `capture/capture.html`.

## Phase 3: Verification

- [ ] T010 Run targeted unit and contract tests.
- [ ] T011 Run the strict Playwright capture tests.
- [ ] T012 Run Ruff, Black, mypy, and the symbol check for changed Python files.
- [ ] T013 Build and restart only the `misthelper` container service.
- [ ] T014 Repeat the live Tier 3 Playwright journey and record screenshots and counts.
- [ ] T015 Add the final validation evidence to GitHub issue #2443.
