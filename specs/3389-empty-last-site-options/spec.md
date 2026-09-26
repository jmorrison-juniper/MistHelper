# Feature Specification: An empty site never replaces the choices of the operator

**Issue**: #3389
**Feature Branch**: `fix/3389-empty-last-site-options`
**Status**: Draft
**Found by**: the review of pull request #3391 on 2026-09-25

## Problem

The multi-site save builds one option record for each selected site. The
route keeps the options of the last site only. A site with no device answers
an empty record, because `build_options_record` returns `{}` when the
inventory read finds no device. If that site is the last site, the plan gets
the default options. The operator chose a canary plan, but the plan then
upgrades all devices at one time.

A failed inventory read gives the same empty record. The route then drops the
devices of that site from the plan, and no message tells the operator.

The Sites page lets the operator select a site with zero devices. An operator
can therefore cause the fault with no cloud failure.

## User Story 1 (P1): An empty site stops the save and names the site

**Acceptance scenarios**:

1. **Given** two selected sites, and the last site holds no device, **When**
   the operator saves a canary plan, **Then** the save stops, and the message
   names the empty site.
2. **Given** the same two sites in the other order, **When** the operator saves
   the plan, **Then** the save stops with the same message.
3. **Given** a site whose inventory read fails, **When** the operator saves the
   plan, **Then** the save stops, and the message names that site.
4. **Given** a refused save, **When** a test reads the store and the browser
   session, **Then** the test finds no plan and no saved options.

## User Story 2 (P1): A site with no planned device stops the save

**Acceptance scenarios**:

1. **Given** two selected sites, and the second site holds only a device type
   that the operator did not check, **When** the operator saves the plan,
   **Then** the save stops, and the message names that site.
2. **Given** selected sites that all hold no planned device, **When** the
   operator saves the plan, **Then** the save stops with the old message. That
   message names the "Device types to upgrade" control.

## User Story 3 (P1): The operator recovers in the browser

**Acceptance scenarios**:

1. **Given** the multi-site mode with a stand-in site and an empty site,
   **When** the operator presses Review, **Then** the flash message names the
   empty site.
2. **Given** that message, **When** the operator clears the empty site on the
   Sites page and presses Review again, **Then** the confirm page opens.

## User Story 4 (P1): A retry keeps its narrow plan

A code review of this change found the case. A retry of issue #3247 chooses
the sites of its failed devices. The Sites page ends the retry, so a refusal
that sends the operator to that page adds the healthy devices to the plan
again.

**Acceptance scenarios**:

1. **Given** a retry of a failed switch at site A and a failed access point at
   site B, **When** the operator clears the Switches type and presses Review,
   **Then** the confirm page opens, and the plan holds the access point only.
2. **Given** the same retry, and the failed switch left site A before the
   save, **When** the operator saves the plan, **Then** the plan holds the
   access point only.
3. **Given** a retry, and a site answers an empty record, **When** the
   operator saves the plan, **Then** the save stops with the FR-002 message.
4. **Given** a retry, and the view read of a site fails at the save, **When**
   the operator saves the plan, **Then** the save stops with the FR-002
   message. No retry device goes out of the plan with no message.

## Functional requirements

- **FR-001**: The save keeps the options of each site that answers a record.
  An empty record never replaces the options.
- **FR-002**: If a selected site answers an empty record, the save stops. The
  message names each such site and tells the operator the next step.
- **FR-003**: If a selected site answers a record with no target, and another
  site holds a target, the save stops. The message names each such site.
- **FR-004**: If no selected site holds a target, the old refusal stays.
- **FR-005**: A refused save writes no plan and no saved options.
- **FR-006**: The message shows the name of each site. A site with no name
  shows its identifier. If the name read fails, each site shows its
  identifier. The message shows ten names at most, and then it states the
  count of the other sites.
- **FR-007**: The single-site save keeps its rule for an empty record.
- **FR-008**: A retry save never applies the FR-003 refusal. A retry save
  applies the FR-002 refusal and the FR-004 refusal.
- **FR-009**: If the device view of a selected site holds no device, that site
  answers an empty record. The save then applies the FR-002 refusal, in a
  retry too.

## Out of scope

- A checked device type with an empty version field. Issue #3394 covers
  that case.
- The site list, the schedule, and the phases on the confirm page. Issue #3222
  covers those items.
- A retry site with no planned device stays in the saved operation, in the
  pre-check gate, and in the lock scope. Issue #3396 covers that case.

## Success criteria

- **SC-001**: Each new contract test fails on the old code and passes after the
  change.
- **SC-002**: The browser journey shows the refusal and the recovery, and a
  screenshot records each page.
