# Tasks: Capture Click Journey Qualification

**Input**: Design documents from `specs/3380-capture-click-journey/`

**Prerequisites**: `plan.md` and `spec.md`

## Phase 1: Repair the native click journey

- [x] T001 Update only the #3380 journey in
  `tests/e2e/upgrade_portal/test_capture.py` to require successful run creation.
  Check each current type control for a matching device and version. Reuse the
  existing selection and save helper.

- [x] T002 Add focused negative tests in
  `tests/unit/upgrade_portal/test_capture_click_journey.py` for refused run
  creation and unavailable versions. Confirm each failure stops before it saves
  options or starts firmware.
- [x] T003 Remove the obsolete select-all row from
  `specs/1823-upgrade-capture-portal/contracts/ui-testids.md` and reference the
  three current type controls.
- [x] T004 Add the unique issue fragment at
  `changelog.d/issue-3380-capture-click-journey.md`.

## Phase 2: Verify the bounded change

- [x] T005 Run the target browser journey with browser recordings disabled.
- [x] T006 Run the complete `test_capture.py` and `test_site_selection.py` files.
- [x] T007 Run focused quality checks and confirm zero leaked local runs or holds.
