# Feature Specification: Upstream New Endpoints (mistapi v0.60–0.62)

**Feature Branch**: `upstream-new-endpoints`
**Created**: 2026-06-11
**Status**: Draft
**Input**: Add new menu operations for mistapi v0.60–0.62 endpoints (NAC CoA, SSO admin deletion, MxEdge upgrades, auto-map assignment, channel scores, IoT search, Zigbee join)

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Export RF Channel Scores (Priority: P1)

A NOC engineer selects a site and exports channel quality scores to CSV/SQLite to identify RF interference or poor channel assignments across APs.

**Why this priority**: Safe read-only export, immediate diagnostic value for RF troubleshooting — the most common NOC task.

**Independent Test**: Select a site, run the operation, verify CSV output contains channel, score, and AP identifiers.

**Acceptance Scenarios**:

1. **Given** user selects a site, **When** they run "Export Site Channel Scores," **Then** channel scores for all bands are exported with AP name/MAC, channel, and score columns.
2. **Given** the site has no APs, **When** user runs the operation, **Then** a clear message says "No channel score data found for this site" and no empty file is created.

---

### User Story 2 — Search Site IoT Endpoints (Priority: P1)

A NOC engineer searches for IoT endpoints (BLE/Zigbee devices) discovered at a site to inventory connected IoT infrastructure.

**Why this priority**: Safe read-only export, supports IoT-enabled campus deployments which are increasingly common.

**Independent Test**: Select a site, run the search, verify output lists IoT endpoint MAC, type, and last-seen timestamp.

**Acceptance Scenarios**:

1. **Given** a site with IoT endpoints, **When** user runs "Search Site IoT Endpoints," **Then** results include endpoint MAC, type, name, and last-seen time.
2. **Given** a site with no IoT endpoints, **When** user runs the operation, **Then** message says "No IoT endpoints found for this site."

---

### User Story 3 — Force NAC Client CoA (Priority: P2)

A NOC engineer forces a Change-of-Authorization on one or more NAC clients to immediately apply updated network access policies without waiting for session timeout. Available at both org and site scope.

**Why this priority**: Interactive management action that solves a real pain point — policy changes taking effect only after session timeout.

**Independent Test**: Select org-level or site-level CoA, provide client MAC(s), confirm the action, verify API success response.

**Acceptance Scenarios**:

1. **Given** a NAC client MAC, **When** user runs "Send NAC Client CoA (Org)," **Then** CoA is triggered and confirmation message shows success/failure per client.
2. **Given** user runs site-level CoA, **When** they select a site and provide MAC(s), **Then** CoA is scoped to that site only.
3. **Given** an invalid MAC, **When** user submits it, **Then** a clear error message is shown without crashing.

---

### User Story 4 — Start Site Auto-Map Assignment (Priority: P2)

A NOC engineer triggers automatic AP-to-floor-map assignment for a site, checks status, applies results, or clears assignments. This automates the tedious manual process of dragging APs onto floor plans.

**Why this priority**: Interactive feature that saves significant manual effort during site deployments.

**Independent Test**: Select a site, start auto-map, check status, apply or clear results.

**Acceptance Scenarios**:

1. **Given** a site with uploaded maps and unplaced APs, **When** user runs "Start Auto-Map Assignment," **Then** the auto-assignment process begins and a job status is returned.
2. **Given** an in-progress auto-map job, **When** user checks status, **Then** current progress and results are displayed.
3. **Given** completed auto-map results, **When** user chooses "Apply," **Then** AP placements are committed to the map.
4. **Given** completed auto-map results, **When** user chooses "Clear," **Then** proposed placements are discarded without changes.

---

### User Story 5 — Enable Zigbee Join on Site Devices (Priority: P3)

A NOC engineer enables Zigbee join mode on APs at a site to allow new Zigbee devices to pair.

**Why this priority**: Niche IoT feature, lower frequency of use.

**Independent Test**: Select a site, run the operation, verify confirmation of Zigbee join enablement.

**Acceptance Scenarios**:

1. **Given** a site with Zigbee-capable APs, **When** user runs "Enable Zigbee Join," **Then** join mode is enabled and confirmation shows affected APs.
2. **Given** a site with no Zigbee-capable APs, **When** user runs the operation, **Then** a clear message explains no eligible APs were found.

---

### User Story 6 — Delete SSO Admin Accounts (Priority: P3)

A NOC engineer removes SSO admin accounts from an org or MSP. This is a **destructive** operation requiring explicit typed confirmation.

**Why this priority**: Administrative housekeeping, infrequent but important for security hygiene. Destructive — lowest priority for implementation.

**Independent Test**: List SSO admins, select one, type 'DELETE' confirmation, verify removal and audit log entry.

**Acceptance Scenarios**:

1. **Given** an org with SSO admins, **When** user selects "Delete Org SSO Admins" and types 'DELETE' to confirm, **Then** the selected admin is removed and success message is shown.
2. **Given** user does not type 'DELETE' correctly, **When** confirmation fails, **Then** operation is cancelled with "Operation cancelled" message.
3. **Given** an MSP context, **When** user selects "Delete MSP SSO Admins," **Then** the same confirmation flow applies at MSP scope.

---

### User Story 7 — MxEdge Upgrade Management (Priority: P3)

A NOC engineer manages Mist Edge firmware upgrades at org or site level — listing available versions, initiating upgrades, and checking upgrade status.

**Why this priority**: Important for lifecycle management but less frequent than daily operations.

**Independent Test**: List available MxEdge firmware versions, initiate upgrade on a test MxEdge, verify status tracking.

**Acceptance Scenarios**:

1. **Given** MxEdges in an org, **When** user lists available firmware versions, **Then** versions are displayed with release dates and compatibility info.
2. **Given** a selected MxEdge and target version, **When** user initiates upgrade with confirmation, **Then** upgrade job is created and status is trackable.

---

### Edge Cases

- What happens when the Mist API returns a 429 (rate limit) during a CoA batch? → Retry with adaptive delay per existing rate-limit logic.
- What happens when auto-map assignment is started on a site with no floor maps? → API returns error; display clear message to user.
- What happens when SSO admin deletion targets the last admin? → API may reject; display the API error clearly.
- What happens when CoA is sent for a client that is no longer connected? → API returns status; display per-client result.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST add channel score export as a safe org export (menu 1–59 range).
- **FR-002**: System MUST add IoT endpoint search as a safe org export (menu 1–59 range).
- **FR-003**: System MUST add NAC Client CoA (org + site) as interactive operations (menu 124–150 range).
- **FR-004**: System MUST add auto-map assignment (start/status/apply/clear) as interactive operations (menu 60–96 range).
- **FR-005**: System MUST add Zigbee join enablement as an interactive operation (menu 60–96 range).
- **FR-006**: System MUST add SSO admin deletion (org + MSP) as destructive operations (menu 154+ range) with typed 'DELETE' confirmation.
- **FR-007**: System MUST add MxEdge upgrade lifecycle operations in the appropriate menu range (destructive actions in 154+ with confirmation).
- **FR-008**: Every new operation MUST have a primary key strategy defined in `ENDPOINT_PRIMARY_KEY_STRATEGIES` before implementation.
- **FR-009**: Every new operation MUST use `safe_input()` for all user input.
- **FR-010**: Every new operation MUST export data via `DataExporter.write_with_format_selection()`.
- **FR-011**: Every new operation MUST include inline comments on every executable line and action logging before/after every API call.
- **FR-012**: README.md operation count MUST be updated to reflect new total.
- **FR-013**: CHANGELOG.md MUST be updated with new version entry listing all added operations.
- **FR-014**: User-facing prompts and messages MUST use clear, jargon-free language suitable for junior NOC engineers.

### Key Entities

- **NAC Client**: Network client authenticated via 802.1X/RADIUS. Key attributes: MAC address, username, VLAN, policy, auth status.
- **SSO Admin**: Administrator account provisioned via Single Sign-On. Key attributes: admin ID, name, email, role, SSO provider.
- **MxEdge**: Mist Edge appliance. Key attributes: device ID, MAC, model, current firmware version, site assignment.
- **Floor Map**: Site floor plan for AP placement. Key attributes: map ID, name, site ID, dimensions.
- **IoT Endpoint**: BLE/Zigbee device discovered by APs. Key attributes: MAC, type, name, last-seen timestamp.
- **Channel Score**: RF channel quality metric per AP/band. Key attributes: AP MAC, band, channel, score.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All new menu operations complete successfully against a live Mist org/site with valid API credentials.
- **SC-002**: CSV/SQLite output from export operations contains correct columns matching API response fields.
- **SC-003**: Destructive operations (SSO deletion) cannot execute without exact typed confirmation string.
- **SC-004**: All new operations handle API errors gracefully — no unhandled exceptions, clear error messages displayed.
- **SC-005**: README operation count accurately reflects new total after all operations are added.
- **SC-006**: A junior NOC engineer can understand and use each new operation without external documentation beyond the menu prompt text.

## Assumptions

- mistapi SDK v0.62+ is installed and provides all referenced endpoint methods.
- Existing MistHelper patterns (menu dispatch, `DataExporter`, `safe_input()`, adaptive rate limiting) are reused without modification.
- MxEdge upgrade operations follow the same confirmation patterns as existing firmware upgrade operations (menu 154–157).
- Auto-map assignment is a multi-step workflow (start → status → apply/clear) exposed as separate sub-menu options or a guided flow within a single menu operation.
- MSP-level operations (delete MSP SSO admins) are only available when MistHelper is configured with MSP-level API credentials.
- Menu numbers will be assigned during implementation based on available slots in each range.

## Menu Number Allocation (Proposed)

| Range | Operation | Menu # (TBD) |
| - | - | - |
| 1–59 (Safe Export) | Export Site Channel Scores | Next available |
| 1–59 (Safe Export) | Search Site IoT Endpoints | Next available |
| 60–96 (Interactive) | Start Site Auto-Map Assignment | Next available |
| 60–96 (Interactive) | Check Auto-Map Status | Next available |
| 60–96 (Interactive) | Apply Auto-Map Results | Next available |
| 60–96 (Interactive) | Clear Auto-Map Results | Next available |
| 60–96 (Interactive) | Enable Zigbee Join on Site Devices | Next available |
| 124–150 (Interactive Mgmt) | Send NAC Client CoA (Org) | Next available |
| 124–150 (Interactive Mgmt) | Send NAC Client CoA (Site) | Next available |
| 154+ (Destructive) | Delete Org SSO Admins | Next available |
| 154+ (Destructive) | Delete MSP SSO Admins | Next available |
| 154+ (Destructive) | MxEdge Upgrade (Org) | Next available |
| 154+ (Destructive) | MxEdge Upgrade (Site) | Next available |
