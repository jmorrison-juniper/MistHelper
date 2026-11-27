# Feature Specification: Refresh guest migration parity planning

**Feature Branch**: Not created by this run. The orchestrator assigns the app-managed branch.

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4588 asks for a fresh, evidence-backed Spec Kit plan for the full guest authorization migration. The plan stops before product implementation.

## Terms

- **Source**: The MistGuestAuthorizations project at the pinned commit `0213240c`.
- **Target**: The MistHelper Flask web portal at main commit `f03c6c9b`.
- **Authorization record**: A Mist guest authorization resource.
- **Scope**: The organization, site, and WLAN that one action may affect.
- **Observation**: A status read from Mist for one authorization record.
- **Gate**: A decision that blocks implementation until an approver accepts it.
- **Offline projection**: The masked, read-only record in `src/interfaces/portals/guest_authorizations.py`.

## Purpose and boundary

This record refreshes the planning for the full migration. It replaces the legacy record for issue 4588. The legacy folder is retired, backed up outside the repository, and listed in the pull request body. It adds no product code, no asset, and no live request.

- The current implementation remains the offline projection.
- This plan does not approve live guest reads, cloud writes, deployment, or a merge.
- This plan excludes the SiteDashboard migration and every other migration.
- Target visual parity remains UNVERIFIED until implementation evidence exists.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review the selected network (Priority: P1)

An operator opens guest authorizations from the existing portal. The operator selects an organization, a site, and a guest WLAN. Then the operator reviews only the authorization records for that scope.

**Why this priority**: A wrong scope can expose data or change another network.

**Independent Test**: Use fictional networks. Test navigation, selection, review, search, and failure states. Send no write.

**Acceptance Scenarios**:

1. **Given** permitted access, **When** the operator selects a site and WLAN, **Then** only matching records appear.
2. **Given** an unavailable session, **When** the page opens, **Then** the page explains the cause and disables each unavailable action.
3. **Given** a missing authorization or expiry value, **When** a record appears, **Then** the value stays unknown.
4. **Given** a changed site, **When** an older response arrives, **Then** the response cannot replace the new scope or enable an action.

### User Story 2 - Grant and manage one authorization (Priority: P2)

An approved operator grants access to one device. The operator can also update supported details and extend access. Each change needs a review and a typed word.

**Why this priority**: These actions change device access in the cloud. They need verified contracts and operator approval.

**Independent Test**: Mock each dispatch and each observation. Prove that wrong, canceled, stale, and denied operations send no write.

**Acceptance Scenarios**:

1. **Given** approved access and supported fields, **When** the operator confirms a grant, **Then** one exact-scope request occurs.
2. **Given** a canceled or wrong typed word, **When** submission stops, **Then** no write occurs.
3. **Given** a timeout after dispatch, **When** the result appears, **Then** the result says unknown and no automatic repeat occurs.
4. **Given** an unsupported duration or field, **When** validation runs, **Then** the portal rejects the change before dispatch.

### User Story 3 - Review and import a CSV batch (Priority: P2)

An approved operator downloads the template, selects a CSV file, reviews each resolved scope, and confirms the batch.

**Why this priority**: One batch can change several networks. It must not hide invalid rows or partial results.

**Independent Test**: Use fictional rows and mocked outcomes. Test parsing, preview, confirmation, duplicates, and recovery.

**Acceptance Scenarios**:

1. **Given** a valid CSV file, **When** the preview completes, **Then** each row has a resolved scope or an explicit rejection.
2. **Given** an ambiguous site name or SSID, **When** mapping runs, **Then** no row selects a target by default.
3. **Given** mixed dispatch outcomes, **When** processing stops, **Then** the successful, rejected, unknown, and unstarted rows stay separate.
4. **Given** a changed file or scope, **When** an old confirmation arrives, **Then** the batch sends no write.

### User Story 4 - Compare the source and target interfaces (Priority: P1)

A reviewer compares the source layout, controls, workflows, and states with the planned target. The reviewer approves only documented deviations.

**Why this priority**: A list of backend methods does not prove visual or functional parity.

**Independent Test**: Render fictional source and target scenarios at the declared viewports. Compare paired screenshots and interaction assertions.

**Acceptance Scenarios**:

1. **Given** the pinned source, **When** a reviewer reads the inventory, **Then** each source feature has a disposition, a requirement, a task, and a test.
2. **Given** paired fixtures, **When** the visual comparison runs, **Then** each difference outside an approved region causes a failure or a review gate.
3. **Given** no target guest page, **When** this plan reports evidence, **Then** the target visual parity stays UNVERIFIED.

### User Story 5 - Operate and recover the shared application (Priority: P3)

An operator uses one application and the existing data services. The operator receives truthful audit results. The operator can return to the offline boundary.

**Why this priority**: Deployment and recovery must not create a second stack or damage shared records.

**Independent Test**: Use isolated stores and mocked requests. Test restart, audit failure, backup, recovery, and the other portal pages.

**Acceptance Scenarios**:

1. **Given** an audit failure before dispatch, **When** submission is requested, **Then** the operation stops without a cloud write.
2. **Given** an audit failure after dispatch, **When** the outcome appears, **Then** the portal reports the uncertainty and follows the approved recovery steps.
3. **Given** a feature shutdown, **When** recovery runs, **Then** the other portal pages and the offline projection still work.

### Edge Cases

- Missing credentials, denied scope, an expired CSRF token, and forged proxy headers never permit a write.
- Equal SSIDs, duplicate site names, organization WLAN assignments, failed discovery, and delayed responses never widen the scope.
- Invalid MAC addresses, mixed separators, malformed timestamps, and absent observations need explicit results.
- CSV quoting, escaped quotes, embedded newlines, BOM, CRLF, missing headers, extra fields, and formula text need tests.
- Rate limits, server rejection, malformed responses, partial batches, worker restarts, and lost audit records need distinct outcomes.
- Keyboard use, reduced motion, narrow screens, long values, and empty search results need accessible states.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST appear as a tab in the existing portal navigation. It MUST show the current organization, site, and WLAN scope.
- **FR-002**: The connection view MUST show unavailable, testing, connected, and failed states. It MUST NOT select an organization automatically.
- **FR-003**: Discovery MUST list only enabled portal WLANs that apply to the selected site. Template and site-group assignments count.
- **FR-004**: Site search MUST match name and address without regard to case. A scope change MUST clear each dependent record, dialog, and confirmation.
- **FR-005**: The authorization list MUST keep the available records, a stable sort, and detail access. An export MUST NOT act as a live page.
- **FR-006**: Status MUST separate active, expired, expiring, and unknown observations. Totals MUST describe only the records that were read.
- **FR-007**: Filtering MUST cover the approved fields only. Filtering MUST NOT expose a disallowed value.
- **FR-008**: Client search MUST match MAC, hostname, IP, and SSID. It MUST show loading, no-result, and failed states.
- **FR-009**: Add MUST accept a device MAC address, approved details, and an optional client selection. It MUST support cancel and confirmed submission.
- **FR-010**: Detail views MUST keep company, custom fields, and sponsor values where the schema permits them. The actor reference MUST NOT come from client text (D-6).
- **FR-011**: Duration input MUST accept integer minutes from 0 to 259200. It MUST reject any other value before dispatch (D-7).
- **FR-012**: Edit MUST keep the MAC address fixed. It MUST change only writable fields and MUST NOT send read-only fields (D-9).
- **FR-013**: Extension MUST state whether the duration starts now or adds to the existing expiry. It MUST use a verified contract (D-8).
- **FR-014**: Revoke MUST use a verified exact-scope operation. It MUST stay unavailable until the verification passes (D-8).
- **FR-015**: The CSV download MUST supply the ten declared headers and fictional examples.
- **FR-016**: The CSV preview MUST account for every input row. It MUST show a bounded preview and complete validation results.
- **FR-017**: CSV mapping MUST resolve the organization, site, and WLAN without ambiguity before confirmation.
- **FR-018**: CSV processing MUST apply the bounds in D-11. The bounds are 1 MiB, 1000 data rows, and ten declared headers.
- **FR-019**: Import MUST show progress and per-row outcomes. It MUST keep partial results and block a repeated confirmation.
- **FR-020**: The operator access model MUST be approved before any live read or write (D-6).
- **FR-021**: Each write MUST require a typed word bound to the actor, action, payload, scope, and batch revision (D-14).
- **FR-022**: Each cloud operation MUST use a verified mistapi method with explicit scope. A failed site call MUST NOT use organization scope.
- **FR-023**: Errors MUST stay visible and safe. Rejections, unavailable observations, rate limits, and unknown write outcomes MUST stay distinct.
- **FR-024**: Audit records MUST follow the approved durability, retention, privacy, and post-dispatch failure rules (D-12).
- **FR-025**: The feature MUST use the existing application and the existing data services. It MUST add no standalone database and no Compose group.
- **FR-026**: Dependencies and configuration MUST reuse the target setup. The feature MUST NOT copy the source token setup or the source dependency pins.
- **FR-027**: The target MUST keep the inventoried layout, order, and control relationships. Each deviation MUST be approved (D-13).
- **FR-028**: The target MUST support responsive, keyboard-accessible workflows with labels, focus, errors, and noncolor status cues.
- **FR-029**: The offline projection MUST keep its exact public shape, masking, input checks, and unknown values.
- **FR-030**: Each inventory row and each requirement MUST map to tasks and test evidence.
- **FR-031**: Documentation MUST explain the supported workflows, the approved deviations, cutover, backup, recovery, and operator approval.
- **FR-032**: Reuse MUST keep the source credit, the license and change notices, the noncommercial terms, and the share-alike terms (D-5).
- **FR-033**: Loading, empty, canceled, failed, and stale states MUST NOT keep another scope. They MUST NOT claim success.
- **FR-034**: The notification option MUST stay off. No hidden backend option may enable the notification option (D-10).
- **FR-035**: Health, restart, configuration, and release behavior MUST use the target ownership. They MUST NOT disrupt another portal page or data service.

The [parity inventory](design/contracts/parity.md) provides the source evidence and the acceptance mapping. The [decision register](design/research.md#7-decision-register) lists each gate and its approver.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- The future feature uses these mistapi methods. The [SDK contract](design/contracts/api.md) lists each one:
  - `listSiteAllGuestAuthorizations` for reads.
  - `getSiteGuestAuthorization` for reconciliation.
  - `updateSiteGuestAuthorization` for grants, edits, and extensions.
  - `deleteSiteGuestAuthorization` for revoke, which stays disabled until D-8 passes.
  - `listSiteWirelessClientsStats` for client search.
- Direct HTTP to a Mist REST endpoint is prohibited when a mistapi method exists.
- No owned WebSocket transport is required. The plan names no WebSocket path.
- Contract-test evidence covers SDK sufficiency, SDK authentication, SDK endpoint parity, failure safety, and secret redaction. Tests use mocked responses only.
- Local SDK inspection proves method signatures. It does not prove live cloud behavior.

### Key Entities *(include if feature involves data)*

- **Scope**: The permitted organization, site, WLAN, and operator reference.
- **Authorization observation**: One record read from Mist, with its status, expiry, and permitted fields.
- **Reviewed change**: One exact action and payload, tied to a scope and a typed word.
- **Import batch**: Validated rows with resolved scope, a confirmation revision, and one outcome per row.
- **Audit record**: The approved minimal evidence of intent, dispatch, observation, and recovery.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every measured source feature has one disposition and at least one requirement, task, test ID, and acceptance result.
- **SC-002**: Every wrong, canceled, stale, denied, or unsupported submission sends zero writes.
- **SC-003**: Each batch row appears exactly once in the final outcome, including unknown and unstarted rows.
- **SC-004**: Reviewers approve every visual difference, or they reject the release. No unreviewed difference counts as parity.
- **SC-005**: Each missing observation stays unknown. No operation invents a successful cloud result.
- **SC-006**: The feature adds zero applications, databases, and Compose groups. Existing workflows keep their regression acceptance.
- **SC-007**: Every requirement has a testable task acceptance before implementation starts.

## Assumptions

- The user confirmed authorship and control of the source and authorized its use. The issue states this. The license terms still apply (D-5).
- The source pin is `0213240c`, which matches GitHub main. The local source clone is stale.
- The target pin is `f03c6c9b`. Each target evidence file matches its GitHub blob.
- The planning change edits Markdown only. It changes no Python file, no configuration, no dependency, and no workflow.
- PR 4208 owns the shared portal files until it closes or the owner hands them over (D-4).
- Access (D-6) and licensing (D-5) need a human decision. The register records the other decisions with reasons. Each decision names its approver and its risk.

## Clarifications

### Session 2026-11-26

- **Q1 (issue body and comment of 2026-11-05)**: The migration target is the existing MistHelper Flask web portal. **Answer recorded.** The target is the portal.
- **Q2 (comment of 2026-11-06 and comment of 2026-11-08)**: Which issue tracks the implementation? **Answer**: Issue #4231 tracks the full migration. Issue #4278 stays open as the workflow child (D-2). GitHub reports #4278 open, not closed.
- **Q3 (issue body)**: Is the source authorship confirmed? **Answer recorded.** The user confirmed authorship and authorized use.
- **Q4 (issue body)**: May live guest data or writes be enabled by this plan? **Answer recorded.** No. The plan keeps the offline projection only.
- **Q5 (comment of 2026-11-21)**: Does the planning record conflict with issue #4869? **Answer**: No. This record uses route `0/0/1/2/1/3/2/3`. Issue #4869 uses route `0/0/1/2/3/4/3/4`.
- **Q6 (issue body)**: Should the PR merge automatically? **Answer recorded.** No. The orchestrator authorizes each merge.
- **Q7 (comment of 2026-11-08 and the brief)**: The owner asks to keep #4588 open for review. The brief requires the body keyword `Closes #4588`. **Open item.** The pull request body needs the keyword. The orchestrator decides the merge time (analysis F12).

## Out of scope

- The SiteDashboard migration and every other migration.
- Product code, enabled routes, live Mist sessions, and cloud writes.
- Copying source images, source CSS, or source markup.
- Relicensing the source or the target.
- Merging the planning PR, building an image, or deploying a container.
