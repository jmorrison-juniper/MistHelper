# Feature Specification: Site read refusal

**Issue**: #3393

**Feature Branch**: `jmorrison-juniper-fix-org-upgrade-cloud-read` (merged by PR 4413)

**Created**: 2026-10-23 (date of PR 4413)

**Updated**: 2026-11-26

**Status**: Record complete. The repair is on `main`. Issue review is open.

**Input**: Runtime fault: a `RequestException` from the site list read answers HTTP 500 at the multi-site options save. Operators need a cloud refusal with recovery steps.

## Current state on main

PR 4413 merged the repair on 2026-10-28. Main head is `f03c6c9b`. The save, the options page, and the confirmation page catch `RequestException` and answer 503 with the envelope in `design/contracts/refusal.md`. The contract tests inject the exception at the reader seam. Analysis A-1 shows that the SDK converts a transport fault into a response with no status, so the production path needs proof. Tasks T007 and T008 close that gap.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Save after a cloud failure (Priority: P1)

An operator saves multi-site upgrade options after a cloud read fails. The portal names the cloud read. The operator saves again without changing the form.

**Why this priority**: The operator needs a clear answer during a change window. A 500 answer hides the cause.

**Independent Test**: Raise a transport fault at the site list read during a save with two selected sites.

**Acceptance Scenarios**:

1. **Given** entered options and a transport fault at the site list read, **When** the operator saves, **Then** the portal answers 503 with code `org_upgrade_site_read_failed` and the recovery message.
2. **Given** a refused save, **When** the operator reads the form, **Then** each entered value remains and no plan exists.
3. **Given** a restored cloud connection, **When** the operator repeats the save, **Then** the portal saves the validated plan.

### User Story 2 - Read an affected page (Priority: P2)

An operator opens the options page or the confirmation page while the site list read fails. The portal reports the temporary cloud failure.

**Why this priority**: Each affected page needs the same explanation for the same failure.

**Independent Test**: Raise a transport fault when each page opens.

**Acceptance Scenarios**:

1. **Given** a valid selection, **When** either page cannot read the sites, **Then** the portal answers 503 with the same envelope.
2. **Given** an existing plan, **When** the confirmation read fails, **Then** the portal keeps the plan and its saved options.

### User Story 3 - Name the cloud below the SDK (Priority: P2, out of scope for this record)

An operator saves after a connection fault that the SDK converts into a partial read. The save then names each site as holding no device. Analysis A-2 records this defect. A later issue owns the change. T008 supplies the evidence for that issue.

## Edge Cases

- A connection error and a timeout receive the same refusal.
- A refused replacement save keeps the earlier saved options and plan.
- A site that is missing from the site list keeps the existing 404 refusal.
- Invalid options keep the existing 400 refusal.
- A successful read keeps the existing confirmation flow.
- Transport error details stay out of every response.
- A transport fault below the SDK boundary becomes a partial read, not an exception (analysis A-1).
- An empty device view for a selected site answers the unread-site refusal (400), not the 503 envelope (analysis A-2).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The save, the options page, and the confirmation page must return 503 for a transport fault at the site list read.
- **FR-002**: Each 503 refusal must name the cloud read and tell the operator to try again.
- **FR-003**: A failed save must create no plan, no nonce, and no saved options.
- **FR-004**: The options form must keep each entered value after a refused asynchronous save.
- **FR-005**: A refused replacement or a failed page read must keep the earlier plan and the signed browser state.
- **FR-006**: Successful reads, input validation, and the missing-site refusal must keep their current answers.
- **FR-007**: Tests must use local mocks and must start no firmware operation and no live cloud request.
- **FR-008**: The repair must not change the device family rules of issue 3394.
- **FR-009**: Each line that the repair adds must carry an inline comment, as the constitution requires.
- **FR-010**: No response may contain transport exception text, a token, or a submitted option value.
- **FR-011**: A transport fault below the SDK boundary must have a documented answer for the save and both pages.

### Mist Cloud Transport Requirements

- The site list read calls mistapi `listOrgSites` from `mistapi.api.v1.orgs.sites` (`.venv\Lib\site-packages\mistapi\api\v1\orgs\sites.py` line 17).
- The device count read calls mistapi `listOrgSiteStats` from `mistapi.api.v1.orgs.stats` (`stats.py` line 1308).
- Both reads use `default_cloud_read` (`src/interfaces/portals/upgrade_portal/app/routes/select.py` lines 357 to 397).
- No owned transport exists. The repair adds no direct HTTP call.
- The SDK does not raise a transport fault for these reads (`mistapi\__api_request.py` lines 225 to 258). Contract evidence for that behavior is required by FR-011 and T008.
- Failure safety, redaction, and the store state are covered by the contract tests in `tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py`.

### Key Entities

- **Selection**: The signed organization identifier and the ordered site identifiers. The active context reads them (`org_upgrade.py` line 487).
- **Options**: The validated operator choices in the signed browser session. A refused save writes none of them.
- **Plan**: The durable aggregate operation. The save writes it only after the site read succeeds (`org_upgrade.py` line 1301).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three affected actions return the 503 refusal for a connection error and for a timeout in the contract tests.
- **SC-002**: A failed save creates zero plans and changes zero saved-option fields.
- **SC-003**: The browser keeps every entered option after a refused save.
- **SC-004**: A successful repeated save reaches confirmation with the original choices.

## Out of Scope

- Issue 3394, the silent drop of a checked device family (analysis A-5).
- The retry route in `org_controls.py` (analysis A-4). A separate issue owns it.
- The text of the unread-site refusal (analysis A-2). A separate issue owns it after T008.
- Any firmware start, live Mist call, or container run in this record.
- Changes to `select.py`, `factory.py`, or the mistapi package.
- A README or operator guide entry (analysis A-9).

## Assumptions

- Status 503 follows the cloud-failure convention of the module (RC-20).
- The refusal text is the shipped text (RC-08). It names the cloud read and gives a recovery step.
- The pinned mistapi version is 0.64.1 (RC-59, RC-76).
- The SDK behavior in the mistapi source is the production behavior. T008 must confirm it.
- A human reviews each change to the save path before merge, because the path starts firmware writes (D-2).

## Clarifications

### Session 2026-11-26

- Q: Reuse the legacy record folder or create a new folder? A: Reuse the slug `site-read-refusal` after verification (D-1).
- Q: Close issue 3393 after the verified merge? A: No. Keep it open until human review (D-2).
- Q: Use 502 or 503 for the transport fault? A: Use 503 (D-3).
- Q: Put the handlers in `select.py` or at the route boundary? A: At the route boundary (D-4).
- Q: Replace the shipped message with the example text in the issue? A: No (D-5).
- Q: Put the retry caller in this record? A: No. A separate issue owns it (D-6).
- Q: Repair issue 3394 in this record? A: No (D-7).
