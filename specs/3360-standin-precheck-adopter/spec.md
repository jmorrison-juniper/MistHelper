# Feature Specification: The browser test store adopts only a standalone pre-check

**Issue**: #3360
**Feature Branch**: `fix/3360-standin-precheck-adopter`
**Status**: Draft
**Found by**: the user journey harness of #3244

## Problem

The browser tests replace the pre-check adopter with a stand-in. The stand-in
is `newest_precheck` in `tests/support/upgrade_portal_e2e/records/portal.py`.
It does not obey two rules of the shipped reader `latest_standalone_precheck`.

| Rule | Shipped reader | Stand-in |
| - | - | - |
| The capture names no run | Required (`run_id == ""`) | Not checked |
| The newest capture wins | The newest start time | The last stored capture |

The multi-site pre-check card therefore shows the seeded capture
`e2e-capture-tier3-0001`. The run `e2e-run-0001` owns that capture, so the
shipped portal never adopts it.

No browser journey can prove the standalone filter of Delta H3 (FR-103). If a
change removes that filter from the shipped reader, no journey reports it.

## User Story 1 (P1): The stand-in adopts the same capture as the shipped reader

**Acceptance scenarios**:

1. **Given** a site with one verified pre-check that a run owns, **When** the
   stand-in reads the site, **Then** it returns an empty value.
2. **Given** a site with one verified standalone pre-check, **When** the
   stand-in reads the site, **Then** it returns that capture.
3. **Given** a site with two verified standalone pre-checks, where the store
   holds the older capture last, **When** the stand-in reads the site, **Then**
   it returns the capture with the newest start time.
4. **Given** a site with one pre-check that holds no `run_id` field, **When**
   the stand-in reads the site, **Then** it returns an empty value. The shipped
   query compares the field with an empty text, and a missing field does not
   match.
5. **Given** a site with a standalone post-check, a standalone pre-check that
   is not verified, or a standalone pre-check of another site, **When** the
   stand-in reads the site, **Then** it returns an empty value, as before.
6. **Given** two verified standalone pre-checks with the same start time,
   **When** the stand-in reads the site, **Then** it returns the capture that
   the store holds last.

## User Story 2 (P1): The multi-site pre-check card shows no capture that a run owns

**Acceptance scenarios**:

1. **Given** the seeded store, **When** the operator opens the multi-site
   confirmation page for both stand-in sites, **Then** the row of the first
   site is ready. Its capture cell names no capture that a run owns.
2. **Given** the same page, **When** the operator presses the button for the
   missing pre-checks, **Then** the page starts a capture for the second site
   only, as before.

## Functional requirements

- **FR-001**: The stand-in accepts a capture only when its `run_id` field holds
  an empty text.
- **FR-002**: The stand-in returns the match with the newest `started_at`
  value. If two matches hold the same value, it returns the match that the
  store holds last.
- **FR-003**: The browser seeds hold one verified standalone pre-check for the
  first stand-in site. Its start time is after the seeded pre-check and before
  the seeded post-check. The first choice and the last choice of each capture
  picker therefore stay the same.
- **FR-004**: The multi-site pre-check journey proves that the card shows no
  capture that a run owns.
- **FR-005**: No product code changes.

## Out of scope

- The tier of the adopted pre-check. Issue #3353 holds that gap.
- The field that tells a verified capture. The stand-in reads
  `capture_status`, and the shipped reader reads `state`. Issue #3375 holds
  that gap.

## Success criteria

- **SC-001**: A unit test proves each scenario of user story 1. The old
  stand-in fails the scenarios of the run filter and of the order.
- **SC-002**: The browser journey fails on the old stand-in, because the card
  names `e2e-capture-tier3-0001`. The journey passes after the repair. Each
  screenshot is read.
- **SC-003**: The browser suite of the upgrade portal passes.
