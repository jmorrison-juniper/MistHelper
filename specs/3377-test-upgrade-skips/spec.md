# Feature Specification: The single-site upgrade journey measures every step

**Issue**: #3377
**Feature Branch**: `fix/3377-test-upgrade-skips`
**Status**: Draft
**Found by**: the user journey harness of #3200, during the verification of #3360

## Problem

Three browser tests in `tests/e2e/upgrade_portal/test_upgrade.py` skip on every
run. pytest counts a skip as a pass, so the suite reports green. It proves
nothing for these three steps.

| Test | Skip text |
| - | - |
| `test_confirm_page_keeps_the_start_locked_for_the_wrong_letter_case` | The confirm field is disabled. |
| `test_confirm_page_unlocks_the_start_after_the_exact_word` | The confirm field is disabled. |
| `test_progress_page_gives_one_state_cell_to_each_device` | The run table holds no device row. |

Two causes stop the journey. The research file holds the evidence.

1. The stand-in options view answers no `type_selections` field. Each type
   control of the options page then holds only the empty prompt, so the helper
   finds no version to pick. The plan save never occurs.
2. The journey opens its run on the first stand-in site. Seeded live runs hold
   that site, so the create call answers 409. The journey then opens a seeded
   run that the bulk tests of `test_run_controls/test_bulk.py` also read.

## User Story 1 (P1): The options page offers a version in each type control

**Acceptance scenarios**:

1. **Given** the stand-in site with one access point, one switch, and one
   gateway, **When** the operator opens the options page of a fresh run,
   **Then** each of the three type controls offers at least one version.
2. **Given** the same page, **When** the operator picks the first offered
   version in each type control and presses the save control, **Then** the
   save call answers 200 and the browser moves to the confirm page.

## User Story 2 (P1): The journey owns its own site

**Acceptance scenarios**:

1. **Given** the seeded store, **When** the journey creates its run, **Then**
   the run belongs to a site that no seeded run holds.
2. **Given** a second test of the same module, **When** it creates a run on the
   same site, **Then** the portal answers 409 and names the run of the first
   test. The journey opens that run, as the refusal instructs.
3. **Given** the journey site, **When** the operator opens the site picker,
   **Then** the picker shows the journey site as a row after the two stand-in
   sites. The first row stays the first stand-in site.

## User Story 3 (P1): A broken step fails and never skips

**Acceptance scenarios**:

1. **Given** a plan save that does not answer 200, **When** a fixture of the
   journey saves the plan, **Then** the fixture fails and names the cause.
2. **Given** a pre-check capture that does not verify, **When** the confirm
   fixture takes the capture, **Then** the fixture fails and names the cause.
3. **Given** a confirm page after a saved plan and a verified pre-check,
   **When** the confirm field is disabled, **Then** the test fails.
4. **Given** a progress page after a saved plan, **When** the run table holds
   no device row, **Then** the test fails.

## Functional requirements

- **FR-001**: The stand-in options view of a single site and of a multi-site
  row answers the three fields of the shipped `build_options_view`:
  `targets`, `versions_by_model`, and `type_selections`.
- **FR-002**: The stand-in view builds `type_selections` with the shipped
  `TypedVersionSelector`, and passes the same selections to the shipped
  `build_version_options`.
- **FR-003**: The stand-in cloud lists a third site for the single-site upgrade
  journey. The site holds no seeded run.
- **FR-004**: `test_upgrade.py` creates its run and takes its pre-check capture
  on the journey site only.
- **FR-005**: The journey fixtures and tests fail with the cause when a step
  does not complete. The only skip left is a workstation with no browser
  binary.
- **FR-006**: No product code changes.

## Out of scope

- The walk of `test_capture.py` that reads the removed control
  `upgrade-version-select-all`. Issue #3380 holds that skip.
- The seed shape of the capture records. Issue #3375 holds that gap.
- The free-text version fields of the multi-site options page. Issue #3205
  holds that gap.

## Success criteria

- **SC-001**: The new type control test fails on the old stand-in and passes
  after the repair.
- **SC-002**: `test_upgrade.py` reports 0 skips with `-rs`.
- **SC-003**: The browser suite of the upgrade portal passes. The one skip left
  is the walk of #3380.
