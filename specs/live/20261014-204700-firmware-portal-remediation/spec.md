# Feature Specification: Firmware portal remediation

**Feature Branch**: `jmorrison-juniper-firmware-portal-remediation`

**Created**: 2026-10-14

**Status**: Specified

**Input**: Issue #4227. Repair menus 305 and 306 after PRs #4219 and #4225.

**Scope revision**: On 2026-10-14, the user selected firmware-policy-only restoration instead of complete settings restoration.
Complete private source and recovery backups remain required.
Only AP, switch, SSR, and SRX firmware policies can change during restoration.
Unrelated current settings remain unchanged.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure a verified policy (Priority: P1)

The operator selects menu 305 in its operation category. The workflow appears beside the menu list.
The operator selects named organizations, hardware models, versions, and a schedule.
The operator prepares verified backups, examines a compact table, then types CONFIGURE.

**Why this priority**: Settings changes require understandable choices and verified recovery.

**Independent Test**: Complete this flow with fixture settings and inspect every external request.

**Acceptance Scenarios**:

1. **Given** the operations page, **When** menu 305 is selected, **Then** its controls occupy the right workspace beside the left menu.
2. **Given** supported hardware catalogs, **When** a model is checked, **Then** its version selector appears with numerical descending order.
3. **Given** an AP schedule, **When** no override is supplied, **Then** every day and 02:00 are selected.
4. **Given** preparation, **When** backups remain incomplete, **Then** confirmation is hidden and no settings write occurs.
5. **Given** all backups verified, **When** CONFIGURE is entered, **Then** progress reports organization changes before site changes.

### User Story 2 - Restore firmware policies from a large private backup (Priority: P1)

The operator selects menu 306 beside the same menu list, selects a private backup and records, and examines recovery status.
The operator types RESTORE only after every recovery backup verifies.
The operator sees that restoration affects firmware policies only, not complete historical settings.

**Why this priority**: The released restore workflow rejects an existing 17,402,805-byte private backup.

**Independent Test**: Restore a generated backup above 8 MiB with more than 4,000 sites and inspect complete call order.

**Acceptance Scenarios**:

1. **Given** a valid large legacy backup, **When** it is selected, **Then** no aggregate byte or record-count threshold rejects it.
2. **Given** tampered, partial, malformed, or public backups, **When** preparation runs, **Then** it fails before a settings write.
3. **Given** verified recovery, **When** RESTORE is confirmed, **Then** organizations restore before sites with readback verification.
4. **Given** an uncertain write, **When** it fails, **Then** it is not retried automatically and partial outcomes remain visible.
5. **Given** historical unrelated settings, **When** firmware policies restore, **Then** unrelated current settings remain unchanged.
6. **Given** an absent saved policy, **When** restoration requires removal, **Then** only a proven removal contract permits the write.

### User Story 3 - Observe long operations (Priority: P2)

The operator sees preparation, verification, request waits, and completion without a raw settings dump.
Site rows sort by site name. The organization name precedes its identifier.

**Why this priority**: Large organizations require long waits without unsafe repetition or lost status.

**Independent Test**: Poll a fixture operation during simulated admission waits and after worker restart.

**Acceptance Scenarios**:

1. **Given** a run with 4,001 sites, **When** request admission requires a valid wait, **Then** progress remains readable without expiring the active run.
2. **Given** a restarted worker, **When** status is requested, **Then** the operator receives a persistent outcome or explicit interrupted state.
3. **Given** verified site backups, **When** the table renders, **Then** names sort alphabetically and no private settings appear.

### Edge Cases

- A selection changes while preparation runs, or another browser attempts to consume its token.
- A target changes after backup, membership changes, or the source bundle changes.
- A backup has duplicate keys, invalid ownership, symlinks, hard links, invalid checksums, or missing records.
- A job stops before, during, or after an uncertain settings write.
- A firmware catalog is empty, malformed, or contains versions with multiple numeric components.
- A rate limit requires a wait longer than the former ten-minute preview lifetime.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Integrate both workflows into operation categories and the existing right workspace without an iframe.
- **FR-002**: Display organization names before identifiers using existing authenticated identity information.
- **FR-003**: Display all catalog-supported models and versions for AP, switch, SSR, and SRX policies.
- **FR-004**: Reveal each version selector only for a checked model and sort versions numerically, highest first.
- **FR-005**: Default supported schedules to every day at 02:00 without adding schedules to unsupported policy types.
- **FR-006**: Separate preparation and complete verified backups from explicit confirmed apply.
- **FR-007**: Require exact CONFIGURE or RESTORE, session ownership, and one consumption per prepared operation.
- **FR-008**: Provide pollable preparation and apply progress with request-wait information and compact sorted tables.
- **FR-009**: Support more than 4,000 sites and backups above 8 MiB without arbitrary aggregate limits.
- **FR-010**: Bound untrusted parsing by record resources and structure while preserving legacy readable backup format.
- **FR-011**: Preserve private access, source integrity, complete recovery backups, freshness, and policy readback with unrelated-settings preservation.
- **FR-012**: Reuse existing request usage and admission tools, including rolling-hour usage control.
- **FR-013**: Apply all organization writes before site writes and never retry an uncertain write automatically.
- **FR-014**: Preserve status across polling and report worker interruption without silently repeating writes.
- **FR-015**: Keep settings, credentials, production backups, and logs outside UI evidence and public artifacts.
- **FR-016**: Update the operator guides, wiki, README link, acceptance mapping, and release note.
- **FR-017**: Restore only AP, switch, SSR, and SRX firmware policy fields from selected backup records.
- **FR-018**: Build required parent replacements from current unrelated siblings, never historical unrelated siblings.
- **FR-019**: Reject malformed or unproven firmware policy content without rejecting unrelated historical settings outside restoration scope.
- **FR-020**: State policy-only scope, any schedule normalization, and unsupported removal effects before confirmation.

### Mist Cloud Transport Requirements

Use existing mistapi settings methods: `getOrgSettings`, `updateOrgSettings`, `getSiteSetting`, and `updateSiteSettings`.
Reuse `listOrgSites`, `listOrgAvailableDeviceVersions`, `listOrgAvailableSsrVersions`, and `listDeviceModels`.
Read organization identity through the authenticated SDK identity or organization lookup.
Reuse the existing API usage endpoint and request control. Do not send direct HTTP requests or firmware execution requests.
Contract tests inspect exact methods, HTTP failures, request counts, write ordering, and private-value redaction.

### Key Entities

- **Prepared operation**: An owned, single-use plan with complete verified backups and sanitized progress.
- **Private bundle**: Complete settings records, creation time, count, and checksum.
- **Progress row**: Scope name, identifier, backup verification, and change outcome without settings values.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Both menus retain the left list and right workflow at desktop widths.
- **SC-002**: A 4,001-site fixture completes preparation and ordered application without missing or duplicate writes.
- **SC-003**: A valid backup larger than 17,402,805 bytes completes a verified firmware-policy roundtrip without unrelated changes.
- **SC-004**: Every failed backup, wrong confirmation, stale target, or foreign session causes zero premature writes.
- **SC-005**: Progress remains available during waits above ten minutes without permitting duplicate application.
- **SC-006**: No rendered fixture page or committed evidence contains private settings.

## Assumptions

- The parent performs connected acceptance and any deployment. This worktree changes no deployed container or production volume.
- The user confirmed Morrison House as the intended live test organization. The parent owns that live testing.
- Existing legacy backups remain readable. Their checksums prove integrity, not authenticity.
- Catalog-supported models define availability. Unsupported model/version combinations must not be invented.
- Process interruption fails closed. Recovery uses a new verified preparation, never automatic write replay.
- Menu 168 establishes construction of AP policy requests, not complete settings restoration.
- Missing or empty AP schedule choices use the menu 168 defaults and appear explicitly in the restoration preview.
- Complete settings restoration is outside the revised scope. No unknown full-settings field is guessed or written from a backup.
