# Feature Specification: Batch target site snapshot

**Feature Branch**: `fix/4923-batch-site-snapshot`

**Issue**: #4923, "Perf: the batch target resolver reads the full site list again for each site"

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4923 (author `jmorrison-juniper`, labels `refactor` and `web-portal`, state open) reports that each site check reads the full organization site list.

## Clarifications

### Session 2026-11-26

- Q: Which object keeps the site snapshot? A: The batch target service of one organization. The shared picker keeps its current behavior. See D-1 in `design/research.md`.
- Q: How long does a site snapshot stay valid? A: 300 seconds. The portal scope decision uses the same lifetime. See D-2 in `design/research.md`.
- Q: Does a discovery read the organization again? A: Yes. Each discovery replaces the site snapshot. Site checks reuse it. See D-3 in `design/research.md`.
- Q: What does a site check do when the organization read fails? A: It raises the picker error and keeps no older rows. See D-5 in `design/research.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the organization once for each preview (Priority: P1)

An operator previews a Multi Site action for an organization with many sites. The portal reads the organization site list once. Each site check uses that list.

**Why this priority**: The current code reads the full site list once for each site. A large organization uses many requests for one preview. Mist limits each API token to 5000 API calls each hour.

**Independent Test**: Run the batch preview tests with a fake Mist harness. The harness counts each organization read. One organization of three sites gives one read.

**Acceptance Scenarios**:

1. **Given** an organization with three sites, **When** the operator previews targets for each site, **Then** the portal reads the organization site list one time.
2. **Given** a discovery ran within 300 seconds, **When** the browser requests a site target, **Then** the portal does not read the organization again.
3. **Given** five browser requests start with no site snapshot, **When** each request checks its site, **Then** the portal sends one organization read.

---

### User Story 2 - Read each organization once in an MSP preview (Priority: P1)

An MSP operator previews one action across several organizations. Each organization keeps its own site snapshot. The portal reads each organization one time for the preview and the start of the run.

**Why this priority**: Each organization in scope repeats the full read for each of its sites. An MSP login multiplies that cost by the number of organizations.

**Independent Test**: Run the MSP integration test with three organizations. Each organization appears once in the read list.

**Acceptance Scenarios**:

1. **Given** organizations A, B, and C, **When** the operator previews and starts a run, **Then** the portal reads each organization once.
2. **Given** organization C returns an HTTP error, **When** the operator previews, **Then** A and B still return rows, and C is reported as unread.

---

### User Story 3 - Refuse foreign sites and failed reads (Priority: P2)

A site that belongs to another organization is refused before any device read. A failed organization read raises the picker error. The portal does not use older rows.

**Why this priority**: The site check protects the portal from site identifiers outside the organization. The check must keep failing closed when it uses the snapshot.

**Independent Test**: Request targets for a foreign site. Make the organization read fail after the snapshot lifetime ends.

**Acceptance Scenarios**:

1. **Given** a site outside organization O, **When** targets are requested for it, **Then** the portal refuses the request and reads no device.
2. **Given** the site snapshot expired, **When** a site check runs and the organization read fails, **Then** the check raises the picker error.

### Edge Cases

- What happens when a site is added in Mist after the snapshot? A new discovery includes the site. A site check that reuses an older snapshot refuses the site for up to 300 seconds.
- Caution: a site removed in Mist can pass the site check for up to 300 seconds. Each later device read then fails with the Mist error that the picker reports.
- What happens when an organization has no sites? The empty list is a valid snapshot. Site checks reuse it and refuse each site without a new read.
- What happens after the portal restarts? The snapshot starts empty. The first site check reads the organization.
- What happens when Mist returns HTTP 429 during a read? The picker raises `picker_request_failed`. The snapshot clears, and the site check fails.
- What happens when several threads check sites at the same time? One thread reads the organization. The other threads wait and reuse the result.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The batch target service MUST read the organization site list once for each discovery, not once for each site check.
- **FR-002**: Each discovery MUST read the organization site list again and replace the site snapshot with the new rows.
- **FR-003**: A site check MUST reuse the site snapshot while the snapshot is 300 seconds old or younger.
- **FR-004**: A site check MUST read the organization site list again when the site snapshot is absent or older than 300 seconds.
- **FR-005**: Concurrent site checks that need a read MUST share one organization read.
- **FR-006**: A failed organization read MUST clear the site snapshot and MUST raise the picker error.
- **FR-007**: A site that is not part of the organization MUST be refused before any device or resource read.
- **FR-008**: Discovery and site-check responses MUST keep the fields `rows`, `total_count`, `complete`, `reason`, `excluded`, and `scope`.
- **FR-009**: The change MUST add one release-note fragment named `issue-4923-batch-site-snapshot.md`.
- **FR-010**: Each new or changed read MUST log an info event before the read and a debug event after it.
- **FR-011**: The change MUST NOT add a direct module to `src/mist/realtime/websocket_streams/intake/pickers/` or a top-level name to `related.py`.
- **FR-012**: The change MUST NOT change the behavior of `StreamPickerService.sites()` for its other callers.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- The feature uses one mistapi method, `mistapi.api.v1.orgs.sites.listOrgSites`, through `StreamPickerService.sites()`.
- The change adds no SDK call and no direct HTTP request to a Mist endpoint.
- The feature owns no WebSocket transport. The transport insufficiency tests do not apply.

### Key Entities *(include if feature involves data)*

- **Organization site snapshot**: The complete site rows of one organization, the time of the read, and the picker that made the read. One snapshot exists for each batch target service. The natural key is the organization identifier.
- **Site row**: One site returned by Mist. The natural key is the site identifier `id`. The label comes from `name`, and the detail comes from the address fields.
- **Site check**: A membership decision for one site identifier against the site snapshot.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A preview of one organization with N sites reads the organization site list one time. The current code reads it N + 1 times.
- **SC-002**: An MSP preview of three organizations reads each organization one time. The start of the run adds no read.
- **SC-003**: Each existing batch target test passes without a change to its expected rows or refusals.
- **SC-004**: Each planned test passes, and each named local gate reports its expected result.
- **SC-005**: No failed organization read returns rows from an earlier read.

## Assumptions

- The web UI runs one Gunicorn worker with four threads (`wsgi.py`, line 4). One process holds each site snapshot, and the lock covers all four threads.
- The app keeps one service bundle for each process. Route handlers resolve it with `ServiceRequest.current()` (`routes/pickers.py`, line 25).
- The picker returns complete rows or raises an error. The page reader rejects incomplete pages (`intake/pickers/records.py`, lines 26 to 52).
- Mist accepts a page limit of 1000. The OpenAPI schema sets no maximum for `limit` (`documentation/mist-api-openapi31yaml.yaml`, line 59742). Live acceptance is unverified.
- A 300-second lifetime gives acceptable staleness for membership checks. Decision D-2 in `design/research.md` records this trade-off.

## Out of Scope *(Non-Goals)*

- Device reads and status reads. The 30-second device cache and the status reads keep their current behavior.
- The shared picker cache of `StreamPickerService`. Its other callers keep their current reads.
- The browser request shape, the concurrency of five requests, and the route contract.
- The shared request admission rule across processes. Issue #4921 tracks that rule.
- Moving the classes out of `related.py`. That split is separate remediation debt.
- The Mist SDK pin text in `.github/copilot-instructions.md`. The drift is recorded in `analysis.md`.
- Live Mist validation. The spec author made no live Mist call.
