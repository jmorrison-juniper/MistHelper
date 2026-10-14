# Feature Specification: Backup restoration

**Feature Branch**: `jmorrison-juniper-backup-restoration`

**Created**: 2026-10-14

**Status**: Specified

**Input**: "start the backup restoration feature now with full guards and acceptance by user requirments for the backup restore workflow"

Issue: [#4218](https://github.com/jmorrison-juniper/MistHelper/issues/4218).

## User Scenarios & Testing

### User Story 1 - Select and preview private settings (Priority: P1)

An operator selects a menu 305 backup, the current cloud, organizations, and sites.
The operator sees identifiers, changed field counts, exclusions, dependencies, and the replacement warning.
The preview never shows settings values.

**Why this priority**: A wrong scope or an unsafe backup must never reach a settings write.

**Independent Test**: Use private fixture bundles and mocked cloud reads. Verify the preview and zero writes.

**Acceptance Scenarios**:

1. **Given** a valid private backup, **When** the operator selects owned records, **Then** the preview identifies every selected scope.
2. **Given** a corrupt, empty, public, linked, oversized, or malformed bundle, **When** selected, **Then** validation fails before writes.
3. **Given** a site outside its saved organization, **When** selected, **Then** validation fails.
4. **Given** an unknown field, ambiguous deletion, or redacted secret, **When** previewed, **Then** validation fails explicitly.
5. **Given** a valid checksum, **When** previewed, **Then** the warning explains that a checksum is not an authentic signature.

### User Story 2 - Restore with complete recovery protection (Priority: P1)

An operator types `RESTORE` after preview.
The tool verifies fresh settings and all recovery backups before it changes the first target.
It restores complete writable settings, organizations before sites, and verifies each saved result.

**Why this priority**: Recovery evidence and verified results protect a production settings operation.

**Independent Test**: Record mocked reads, backup verification, writes, and saved-state checks in order.

**Acceptance Scenarios**:

1. **Given** a confirmed plan, **When** every recovery backup verifies, **Then** the first write can occur.
2. **Given** any failed current read or recovery backup, **When** applying, **Then** zero writes occur.
3. **Given** settings or membership changed after preview, **When** applying, **Then** the tool stops and requires a new preview.
4. **Given** a failed write or saved-state check, **When** applying, **Then** no later write occurs.
5. **Given** partial completion, **When** reporting, **Then** completed, failed, and remaining scopes have exact identifiers.
6. **Given** cancellation, dry run, or incorrect confirmation, **When** submitted, **Then** zero writes occur.

### User Story 3 - Use protected graphical controls (Priority: P2)

The operator uses the protected operations portal to select backup records, preview, confirm, and inspect results.
Complete settings and credentials remain on the server.

**Why this priority**: A graphical interface must enforce the same safety rules as the numbered menu.

**Independent Test**: Complete the flow in Chromium with mocked SDK transport and real portal security middleware.

**Acceptance Scenarios**:

1. **Given** valid portal access, **When** the operator selects records, **Then** dynamic controls show only safe scope metadata.
2. **Given** another browser, an expired preview, a repeated submission, or missing request protection, **When** submitted, **Then** no write occurs.
3. **Given** a failed operation, **When** displayed, **Then** the portal shows the partial result without secret values.

### Edge Cases

- Reject duplicate JSON keys, duplicate records, invalid UUIDs, invalid timestamps, invalid counts, and non-finite numbers.
- Reject private files with another owner, links, traversal, unexpected names, or excessive size.
- Preserve each original bundle byte for byte.
- Validate all selected records before any write. Do not silently discard unsafe fields.
- Refuse ambiguous site ownership in legacy multi-organization bundles.
- Do not retry a write or attempt automatic rollback after partial completion.
- Do not claim actual user acceptance or successful production restoration from mocked tests.

## Requirements

### Functional Requirements

- **FR-001**: A separate unused destructive menu and a protected portal MUST restore selected menu 305 records.
- **FR-002**: Validation MUST check private storage, ownership, format, integrity, identifiers, and record uniqueness.
- **FR-003**: The operator MUST explicitly bind a legacy bundle to the active cloud. A checksum MUST NOT imply authenticity.
- **FR-004**: Restoration MUST cover complete writable settings, not only firmware policy fields.
- **FR-005**: Schema-defined server-managed fields MUST be excluded and disclosed as exclusions.
- **FR-006**: Unknown fields, invalid values, secret placeholders, and unsupported deletion semantics MUST fail before writes.
- **FR-007**: Fields absent from the backup MUST NOT silently retain later settings. An unproven deletion MUST stop restoration.
- **FR-008**: Each site MUST match current organization membership and unambiguous saved ownership.
- **FR-009**: A selected site MUST include its saved organization record. All organization writes MUST precede site writes.
- **FR-010**: The preview MUST show scope, replacement effects, exclusions, and counts without settings values.
- **FR-011**: Exact `RESTORE` confirmation MUST precede recovery backups and settings changes.
- **FR-012**: Fresh reads and verified complete recovery backups for every target MUST precede the first write.
- **FR-013**: The tool MUST detect stale previews, changed bundles, changed cloud context, and changed site membership.
- **FR-014**: Each write MUST pass a saved-state check. The first failure MUST stop remaining writes.
- **FR-015**: Results MUST distinguish completed, failed, and remaining targets. Unverified writes MUST NOT count as completed.
- **FR-016**: No firmware execution endpoint, device-push endpoint, or automatic change retry is permitted.
- **FR-017**: Original bundles MUST remain private and unchanged. Browser responses and logs MUST contain no settings values.

### Mist Cloud Transport Requirements

Use `getOrgSettings`, `updateOrgSettings`, `getSiteSetting`, `updateSiteSettings`, and `listOrgSites`.
Use SDK pagination for the complete membership list.
No direct HTTP or owned WebSocket transport is required.
Contract tests must prove endpoint parity, status handling, pagination completeness, and secret redaction.

### Key Entities

- **Backup bundle**: Private complete settings records with creation time, record count, and checksum.
- **Restore target**: A validated scope, saved writable settings, current snapshot, and expected saved result.
- **Restore preview**: A cloud-bound, expiring, single-use selection with sanitized effects.
- **Recovery bundle**: Verified complete current settings for every selected target.
- **Restore result**: Exact completed, failed, and remaining scope identifiers.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Each invalid-input acceptance scenario causes zero settings writes.
- **SC-002**: Every successful write follows verified recovery coverage for 100 percent of selected scopes.
- **SC-003**: Every completed scope passes a saved-state comparison.
- **SC-004**: No later scope receives a write after the first failure.
- **SC-005**: CLI and Chromium tests complete selection, preview, confirmation, completion, and partial-failure flows.
- **SC-006**: Secret fixture values appear zero times in browser responses, printed output, and application logs.
- **SC-007**: Original bundle bytes remain identical before and after every tested flow.

## Assumptions

- Complete writable-settings restoration intentionally replaces later changes within selected scopes.
- Unselected scopes remain unchanged. Server-managed fields retain current server values.
- A selected site requires selection of its saved organization to make inheritance dependencies explicit.
- Legacy bundles lack authenticated cloud provenance. The operator must confirm the active cloud and verify the bundle source externally.
- Unknown or unprovable settings behavior fails closed. It does not silently reduce the restoration scope.
- Production restoration and production firmware execution are outside development acceptance.
- The parent session owns deployment and preserves the existing persistent runtime volume.
