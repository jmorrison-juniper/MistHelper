# Feature Specification: Full guest migration parity

**Feature Branch**: `jmorrison-juniper-guest-migration-parity-specification`

**Created**: 2026-11-05

**Status**: Draft

**Input**: User description: "can we rebuild a new full e2e specit workflow to get us back on track and define all the remaining steps including comparison to the original repo to make sure we have captured the look and feel and al functionality when brining into misthelper??"

This record defines the full future migration. This change delivers planning only.
The current implementation remains the tested offline projection selected by the user.
The plan does not approve live guest reads, cloud writes, deployment, or a merge.
It excludes SiteDashboard and every other migration.

Tracking: [planning issue #4588](https://github.com/jmorrison-juniper/MistHelper/issues/4588),
[original planning #4231](https://github.com/jmorrison-juniper/MistHelper/issues/4231),
and [implementation #4278](https://github.com/jmorrison-juniper/MistHelper/issues/4278).
These links do not close an issue.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review the selected guest network (Priority: P1)

An operator reaches guest authorizations from the existing MistHelper portal.
The operator selects an organization, site, and applicable guest WLAN before reviewing authorization records.

**Why this priority**: A wrong scope can expose data or change another network.

**Independent Test**: Use fictional networks to test navigation, selection, review, search, and failure states without a cloud write.

**Acceptance Scenarios**:

1. **Given** permitted access, **When** the operator selects a site and WLAN, **Then** only matching records appear.
2. **Given** an unavailable session, **When** the page opens, **Then** it explains the cause and disables unavailable actions.
3. **Given** missing authorization or expiration observations, **When** records appear, **Then** unknown values remain unknown.
4. **Given** a changed site, **When** an older request completes, **Then** it cannot replace the new scope or enable actions.

### User Story 2 - Grant and manage one authorization (Priority: P2)

An approved operator can add, edit supported details, extend, and revoke access after reviewing the exact requested change.

**Why this priority**: These actions change network access and need verified contracts and operator approval.

**Independent Test**: Supply mocked responses for each action and assert the exact scope, confirmation, payload, and observed result.

**Acceptance Scenarios**:

1. **Given** approved access and supported fields, **When** the operator confirms a grant, **Then** one exact-scope request occurs.
2. **Given** a canceled or wrong confirmation, **When** submission stops, **Then** no write occurs.
3. **Given** a timeout after dispatch, **When** the result appears, **Then** it says unknown and does not automatically repeat the write.
4. **Given** an unsupported duration or field, **When** validation runs, **Then** the page rejects it before dispatch.

### User Story 3 - Review and import a CSV batch (Priority: P2)

An approved operator downloads an example, selects a CSV file, reviews every resolved scope, and confirms the reviewed batch.

**Why this priority**: A batch can change several networks and must not conceal invalid rows or partial results.

**Independent Test**: Use fictional rows and mocked outcomes to test parsing, preview, confirmation, duplicate rules, and recovery.

**Acceptance Scenarios**:

1. **Given** a valid CSV, **When** preview completes, **Then** each row has a resolved scope or an explicit rejection.
2. **Given** an ambiguous site name or SSID, **When** mapping runs, **Then** no row silently selects a target.
3. **Given** mixed dispatch outcomes, **When** processing stops, **Then** successful, rejected, unknown, and unstarted rows remain distinct.
4. **Given** a changed file or scope, **When** an old confirmation is submitted, **Then** the batch sends no write.

### User Story 4 - Compare the original and target interfaces (Priority: P1)

The reviewer compares the source layout, controls, workflows, and states with the planned target and approves only documented deviations.

**Why this priority**: A list of backend methods does not prove visual or functional parity.

**Independent Test**: Render fictional source and target scenarios at declared viewports and compare paired screenshots and interaction assertions.

**Acceptance Scenarios**:

1. **Given** the pinned source, **When** reviewers inspect the inventory, **Then** each source feature has a disposition, requirement, task, and test.
2. **Given** paired fixtures, **When** visual comparison runs, **Then** differences outside approved regions cause failure or a review gate.
3. **Given** an absent target guest UI, **When** this plan reports evidence, **Then** target visual parity remains UNVERIFIED.

### User Story 5 - Operate and recover the shared application (Priority: P3)

An operator uses one application and the existing data services, receives truthful audit results, and can return to the offline boundary.

**Why this priority**: Deployment and recovery must not create another stack or corrupt shared records.

**Independent Test**: Use isolated stores and mocked requests to test restart, audit failure, backup, recovery, and other portal pages.

**Acceptance Scenarios**:

1. **Given** an audit failure before dispatch, **When** submission is requested, **Then** the operation stops without a cloud write.
2. **Given** an audit failure after dispatch, **When** the outcome appears, **Then** it reports the uncertainty and uses the approved recovery procedure.
3. **Given** a feature shutdown, **When** recovery runs, **Then** existing portal pages and the offline projection still work.

### Edge Cases

- Missing credentials, denied scope, expired CSRF token, and forged proxy headers must not permit a write.
- Equal SSIDs, duplicate site names, org WLAN assignments, failed discovery, and delayed responses must not broaden scope.
- Invalid MACs, mixed separators, malformed timestamps, and absent observations require explicit results.
- CSV quoting, escaped quotes, embedded newlines, BOM, CRLF, missing headers, extra fields, and formula strings require tests.
- Rate limits, server rejection, malformed responses, partial batches, worker restarts, and lost audit records require distinct outcomes.
- Keyboard-only input, reduced motion, phone overflow, long values, and empty search results require accessible states.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST use the existing portal navigation and show its current organization, site, and WLAN scope.
- **FR-002**: Connection review MUST show unavailable, testing, connected, and failed states without selecting the first organization automatically.
- **FR-003**: Discovery MUST show sorted, enabled guest-portal WLANs that actually apply to the selected site, including template and sitegroup assignments.
- **FR-004**: Site search MUST match name and address. Scope changes MUST clear dependent records, dialogs, and confirmations.
- **FR-005**: Authorization review MUST preserve available records, sorting, and detail access without treating an export as a live page.
- **FR-006**: Status review MUST distinguish active, expired, expiring, and unknown observations and display truthful totals and remaining time.
- **FR-007**: Guest filtering MUST support permitted MAC, name, email, company, custom fields, sponsor, and creator values without exposing disallowed data.
- **FR-008**: Client search MUST support MAC, hostname, IP, and discovered SSID matching, with loading, no-result, and failed states.
- **FR-009**: Add MUST provide device entry, permitted guest details, optional client selection, cancellation, and confirmed submission.
- **FR-010**: Detail views MUST preserve company, custom fields, sponsor, and creator semantics where supported and permitted.
- **FR-011**: Duration input and presets MUST reject unsupported values and explain unavailable source presets before a write.
- **FR-012**: Edit MUST keep the MAC fixed and change only verified writable fields. Unsupported name editing MUST remain unavailable.
- **FR-013**: Extension MUST explain whether the duration starts now or adds to existing expiry, using a verified contract.
- **FR-014**: Revoke MUST use a verified exact-scope operation and verify the resulting observation without promising unsupported zero-minute semantics.
- **FR-015**: CSV download MUST supply documented headers and fictional examples with supported fields and durations.
- **FR-016**: CSV preview MUST account for every input row, parse supported CSV syntax, and show a bounded preview and complete validation results.
- **FR-017**: CSV mapping MUST resolve organization, site, and WLAN unambiguously within approved scope before confirmation.
- **FR-018**: CSV processing MUST apply approved byte, row, field, duplicate, and request limits. This plan MUST NOT invent these limits.
- **FR-019**: Import MUST show progress and per-row outcomes, preserve partial results, prevent repeated confirmation, and explain recovery.
- **FR-020**: Maintainers MUST approve the operator access model before live reads or writes become available.
- **FR-021**: Every write MUST require an exact typed confirmation bound to the reviewed actor, action, payload, scope, and batch revision.
- **FR-022**: Every cloud operation MUST use a verified SDK method. No failed site call may silently use organization scope.
- **FR-023**: Errors MUST remain visible and safe. Rejections, unavailable observations, rate limits, and unknown write outcomes MUST remain distinct.
- **FR-024**: Audit behavior MUST follow an approved durability, retention, privacy, and post-dispatch failure policy.
- **FR-025**: The feature MUST use the existing application and shared data services. It MUST add no standalone database or Compose group.
- **FR-026**: Dependencies and configuration MUST reconcile with the target instead of copying the source dependency or token setup.
- **FR-027**: The target MUST preserve the inventoried visual hierarchy, layout, and control relationships except for approved deviations.
- **FR-028**: The target MUST support responsive and keyboard-accessible workflows, meaningful focus, labels, errors, and noncolor status cues.
- **FR-029**: The tested offline projection MUST retain its exact public shape, masking, input checks, and unknown values.
- **FR-030**: Every inventory row and remaining requirement MUST map to tasks, test IDs, and observable acceptance evidence.
- **FR-031**: Documentation MUST explain supported workflows, approved deviations, cutover, backup, recovery, and operator approval.
- **FR-032**: Reuse MUST retain applicable source attribution, license links, change notices, noncommercial, and share-alike requirements.
- **FR-033**: Loading, empty, canceled, failed, and stale states MUST not retain another scope or falsely report success.
- **FR-034**: Notification support MUST have an explicit disposition. No hidden backend notification option may become enabled by accident.
- **FR-035**: Health, restart, configuration, and release behavior MUST use MistHelper ownership and must not disrupt another portal or data service.

The [parity inventory](design/contracts/parity.md) provides source evidence and the acceptance mapping.
The [decision register](design/research.md#decision-register) blocks implementation where approval or contract evidence is absent.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Only the existing `mistapi` session may make future REST requests.
The [API contract](design/contracts/api.md) names each source method, target candidate, and unresolved behavior.
No WebSocket or direct HTTP exception is needed.
Local SDK inspection proves method signatures, not live cloud behavior.
All future tests use mocked responses and forbidden live-session construction.

### Key Entities *(include if feature involves data)*

- **Scope**: The permitted organization, site, WLAN, and operator context.
- **Authorization observation**: A source record, its explicit status, its expiry, and permitted detail fields.
- **Reviewed change**: An exact action and payload tied to scope and confirmation.
- **Import batch**: Validated rows with resolved scope, confirmation revision, and individual outcomes.
- **Audit event**: Approved minimal evidence of intent, dispatch, observation, and recovery.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every measured source feature has one disposition and at least one requirement, task, test ID, and acceptance result.
- **SC-002**: Every wrong, canceled, stale, denied, or unsupported submission sends zero writes.
- **SC-003**: Every batch row appears exactly once in the final outcome accounting, including unknown and unstarted rows.
- **SC-004**: Reviewers approve every visual difference or reject the release. No unreviewed difference counts as parity.
- **SC-005**: Every missing observation remains unknown. No operation invents a successful cloud result.
- **SC-006**: The feature adds zero applications, databases, or Compose groups. Existing workflows retain their regression acceptance.
- **SC-007**: All remaining requirements have testable task acceptance before implementation starts.

## Assumptions

The user confirmed authorship and control of the source and authorized its use.
Source-rights permission is resolved, not an open gate. This record does not invent a relicense.
The source pin equals the previous baseline, so there is no source history difference between those two references.
The parent worktree and its uncommitted drafts remain untouched.
The merged old planning record remains historical context, not the fresh feature destination.
Access, CSV limits, audit policy, theme integration, notification support, and conflicting cloud semantics remain implementation gates.
The plan can finish with these gates explicit. Their presence does not authorize assumptions or production work.

## Clarifications

### Session 2026-11-05

No new question was necessary to complete planning.
The user already resolved source authorship, use permission, the offline-only current boundary, and the full future specification scope.
The scan found access, API semantics, CSV policy, audit policy, theme integration, and notification decisions.
These remain explicit implementation gates with alternatives in the decision register.
No answer was invented and no unresolved policy became an enabling default.
