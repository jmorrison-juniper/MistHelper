# Feature Specification: Close the multi-site Start button on the first click

**Issue**: #3242
**Feature Branch**: `fix/3242-org-start-double-click`
**Status**: Implemented
**Found by**: the multi-site journey of #3200, finding F-upj-multisite-010

## Problem

The Start button of the multi-site confirm page stays open after the first
click. A double click sends two `POST /api/org-upgrades` requests. The server
refuses the second request, so only one job starts. The confirm page then
shows the refusal "This confirmed request already started an organization
upgrade." The word CONFIRM stays in the field, the Start button stays open,
and the page shows no link to the job that started.

Warning: the operator can think that no job started. The operator can then
leave a firmware job that runs, or try the upgrade again.

The single-site pages close each start button while the request runs. The
multi-site forms do not.

## User Story 1 (P1): One click sends one request

**Acceptance scenarios**:

1. **Given** the confirm page with the word CONFIRM in the field, **When** the
   operator double-clicks Start, **Then** the browser sends one start request,
   and the progress page of the job opens.
2. **Given** a multi-site form, **When** the operator sends the form, **Then**
   its submit button and its typed-word field stay closed until the answer
   arrives.
3. **Given** the options page, **When** the operator double-clicks Review,
   **Then** the browser sends one options request.

## User Story 2 (P1): A replay refusal links to the job that started

**Acceptance scenarios**:

1. **Given** a confirmed request that already started a job, **When** the
   server refuses a second start, **Then** the refusal names the job and links
   to its progress page.
2. **Given** that refusal, **When** the page shows it, **Then** the Start button
   and the typed-word field stay closed, and the field holds no typed word.
3. **Given** the link, **When** the operator opens it, **Then** the progress
   page of the job opens.
4. **Given** a replay refusal after an unknown cloud answer, **When** the page
   shows it, **Then** the refusal states that the outcome is unknown, and the
   Start button stays closed.

## User Story 3 (P2): Another refusal still permits a new try

**Acceptance scenarios**:

1. **Given** a refusal with another code, such as a cloud fault, **When** the
   page shows it, **Then** the typed-word gate decides the state of the Start
   button again.

## Functional requirements

- **FR-001**: The page script closes each open submit button and each open
  typed-word field of a multi-site form before it sends the request.
- **FR-002**: The page script ignores a second submit of a form while the
  first request of that form runs.
- **FR-003**: The 409 refusal `org_upgrade_already_submitted` carries
  `details.upgrade_id` and `details.next` when the server knows the job. The
  value of `next` is the progress page `/upgrade/org/jobs/<upgrade_id>`.
- **FR-004**: The aggregate path names the operation of the saved plan only
  when the durable record shows a start. The legacy access point path names
  the cloud job of the browser marker.
- **FR-005**: If the browser marker holds no job identifier, the refusal
  states that the cloud answer is unknown, and it names the cure.
- **FR-006**: The page builds the job link from real nodes. The page accepts
  only a relative path to a progress page of this portal.
- **FR-007**: A replay refusal keeps the form closed and clears the typed word.
  Any other refusal opens the closed controls again and applies each
  typed-word gate.
- **FR-008**: The browser log names the error code and the status only.
- **FR-009**: If the browser restores a page from its back-forward cache after
  a form of that page sent a request, the page loads again from the server.

## Out of scope

- The lock refusal of #3224. That issue can use the same `details.next` rule.
- Two browser tabs that send the legacy access point request at the same
  moment. The research file records this risk.

## Success criteria

- **SC-001**: A browser test counts one start request after a double click.
- **SC-002**: A browser test opens the job page from the link of a real replay
  refusal.
- **SC-003**: Contract tests prove the job details on both server paths.
