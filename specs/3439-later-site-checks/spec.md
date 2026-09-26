# Feature Specification: A later site check names an incomplete site list

**Issue**: #3439
**Feature Branch**: `fix/3439-later-site-checks`
**Status**: Draft
**Found by**: the design review of the #3438 fix on 2026-09-26

## Problem

Issue #3438 adds a Caution note to the site picker. The note shows when the
site list read lost a page. The later site checks read the same list again,
and they do not know about a lost page.

The portal keeps a whole site list read for one minute. After that minute,
each step reads the list again. An operator who picked a site from a whole
list can therefore meet a lost page at the next step.

If the site of the check sits on the lost page, the check refuses the site
with the wrong cause. The operator reads "no such site" or "choose sites
again", but the site exists. The portal did not read it.

Nine steps check a site against the site list.

| Step | Mode | The answer today for a site of a lost page |
| - | - | - |
| The site choice post of the site picker | Multi-site | 404 `site_not_found` |
| The inventory page of one site | Single-site | 404 and an empty site picker |
| The inventory answer of one site | Single-site | 404 `site_not_found` |
| The capture start | Single-site | 404 `site_not_found` |
| The pre-check start of one site | Multi-site | 404 `site_not_found` |
| The options page | Multi-site | 404 `sites_required` |
| The options save | Multi-site | 200, and the plan holds no site |
| The confirm page | Multi-site | 404 `sites_required` |
| The retry of a settled operation | Multi-site | 404 `sites_required` |

The run creation also reads the site list, for the site name. That read keeps
the site identifier when the read fails, so it needs no change.

## User Scenarios & Testing

### User Story 1 (P1): The single-site steps name an incomplete site list

The operator opens one site, reads its devices, and starts a capture. Each of
these steps checks the site again.

**Independent test**: Open the site picker in the single-site mode while the
site read is whole. Make the later site reads lose the page of one site. Open
that site, and start a capture of that site.

**Acceptance scenarios**:

1. **Given** a lost page that holds the site, **When** the operator opens the
   site, **Then** the error page shows the status 503. The code is
   `site_list_incomplete`. The page states that the portal did not read the
   complete site list. The page tells the operator to try again.
2. **Given** the same read, **When** a script reads the inventory answer of
   that site, **Then** the answer is 503 with the error code
   `site_list_incomplete`.
3. **Given** the same read, **When** the operator starts a capture of that
   site, **Then** no capture starts. The capture page shows the same sentence.
4. **Given** the same read, **When** the operator opens a site of a kept page,
   **Then** the inventory page shows the devices as before.
5. **Given** a whole read at the next attempt, **When** the operator reloads
   the page, **Then** the inventory page shows the devices of the site.

### User Story 2 (P1): The multi-site site choice names an incomplete site list

The operator selects several sites and presses the forward control. The post
checks each selected site again.

**Independent test**: Open the site picker in the multi-site mode while the
site read is whole. Select one site of page one and one site of page two. Make
the later site reads lose page two, and press the forward control.

**Acceptance scenarios**:

1. **Given** a check read that loses the page of a selected site, **When** the
   operator presses the forward control, **Then** the site picker opens again.
   A Caution message states that the portal did not read the complete site
   list, and it tells the operator to try again.
2. **Given** the same read, **When** a script posts the same site choice,
   **Then** the answer is 503 with the error code `site_list_incomplete`.
3. **Given** the same read, **When** the operator selects only sites of a kept
   page, **Then** the options page opens, as it does today.
4. **Given** a refused post, **When** the operator reads the site picker,
   **Then** the stored site choice does not change.

### User Story 3 (P1): The multi-site plan steps name an incomplete site list

The operator opens the options page, saves a plan, opens the confirm page, and
starts the pre-checks. A settled operation can also open a retry. Each of
these steps checks the selected sites again.

**Independent test**: Select two sites while the site read is whole, and open
the options page. Make the later site reads lose the page of one selected
site. Save the options, open the confirm page, and start a pre-check.

**Acceptance scenarios**:

1. **Given** a lost page that holds a selected site, **When** the operator
   opens the options page, **Then** the error page shows the status 503. The
   code is `site_list_incomplete`.
2. **Given** the same read, **When** the operator saves the options, **Then**
   the options page shows the sentence. The form keeps each typed value. The
   portal stores no plan and no saved options.
3. **Given** the same read, **When** the operator opens the confirm page,
   **Then** the error page shows the status 503. The saved options stay, so
   the confirm page opens after a whole read.
4. **Given** the same read, **When** the operator starts the pre-check of that
   site, **Then** no capture starts, and the portal takes no site lock. The
   confirm page shows the sentence.
5. **Given** the same read, **When** the operator opens a retry that holds
   that site, **Then** the answer is 503. The error code is
   `site_list_incomplete`. The portal selects no retry site.
6. **Given** a whole read at the next attempt, **When** the operator repeats
   the step, **Then** the step works as it does today.

### Edge Cases

- The site read loses a page, and each named site is on a kept page. The check
  passes, because a partial list still proves that each listed site exists.
- The site read is whole, and a named site is not in the list. The answer does
  not change. The site left the organization, or the request names a site of
  another organization.
- The first page of the site read fails, so the read holds no site. Each check
  refuses with the 503 answer, because the portal cannot tell whether the site
  exists.
- The device count read loses a page, and the site read is whole. Each check
  passes, because a site check reads the site records only.
- The run creation reads the site name, and that read loses the page of the
  site. The run keeps the site identifier as its name, as it does today for a
  failed read.
- The site read of the picker also loses the page. The picker then shows the
  note of issue #3438 below the message of the refused post.
- A reload repeats the check with a new cloud read, because the portal never
  keeps a read that lost a page.

## Requirements

### Functional Requirements

- **FR-001**: A later site check refuses with the status 503 and the error code
  `site_list_incomplete` when two conditions are true. The site read lost a
  page, and a named site is not in the list.
- **FR-002**: The refusal sentence is "The portal did not read the complete
  site list, so it cannot check your site choice. Try again." The heading of
  the error page is "The portal did not read the complete site list".
- **FR-003**: A page request from a browser receives the shared error page. The
  page shows the heading, the sentence, the status, the code, and the link to
  the site list.
- **FR-004**: A script request and a JSON request receive the error envelope
  with the code and the sentence.
- **FR-005**: A refused site choice post from a browser returns to the site
  picker. The picker shows the sentence as a Caution message, as the other
  picker refusals do.
- **FR-006**: A check passes when each named site is in the list, also when the
  read lost a page.
- **FR-007**: A check with a whole read keeps the answer of today when a named
  site is not in the list.
- **FR-008**: A refused check changes no stored state. It stores no site
  choice, no plan, and no saved options. It starts no capture, takes no site
  lock, and selects no retry site.
- **FR-009**: The run creation keeps the site identifier as the run name when
  the site read fails. This change keeps that rule.
- **FR-010**: Each check makes the same cloud reads as today. The change adds
  no cloud read.
- **FR-011**: The log records each refusal with the count of missing sites.
  The log holds no site record and no token.
- **FR-012**: The contract documents name the new answer of each affected
  endpoint. The status code table names the status 503.

### Key Entities

- **Site list**: the site rows of one organization, and one flag for the site
  read. The flag states whether the read is whole.
- **Later site check**: a step that reads the site list again and looks for
  each site that the request names.
- **Missing site**: a named site that the site list does not hold.

## Out of Scope

- A whole site list without a selected site lets the options save store a plan
  with no site. Issue #3441 tracks that defect.
- A transport fault of the site read at the options save answers 500. Issue
  #3393 tracks that defect.
- The page script shows each refused request with the prefix "Warning:". This
  change keeps that rule.
- The Caution note of the site picker. Issue #3438 owns that note.

## Assumptions

- The issue names a forward control of the single-site mode. No such control
  exists. The single-site forward step is the Open link of the site picker.
  That link opens the inventory page, and the inventory page runs the check.
- The status 503 fits, because the cloud read did not complete, and a later
  read can pass.
- A reload or a repeated press is the recovery step. A lost page is a short
  cloud fault, so a new read usually recovers.
- The signal word of the picker message is Caution, because a retry recovers
  the step.

## Success Criteria

- **SC-001**: Each new test of a refusal fails on the old code and passes
  after the change. Each regression test of FR-006, FR-007, and FR-010 passes
  on both code versions, because it guards the answer of today.
- **SC-002**: Each of the nine steps answers the 503 refusal for a site of a
  lost page. No step answers "no such site" or "choose sites" for that site.
- **SC-003**: Each step passes for a site of a kept page after a lost page.
- **SC-004**: A browser journey shows each refusal in each mode. A screenshot
  records each page.
- **SC-005**: Each step makes the same count of cloud reads as before the
  change.
- **SC-006**: The operator recovers each step with one reload or one repeated
  press after a whole read.