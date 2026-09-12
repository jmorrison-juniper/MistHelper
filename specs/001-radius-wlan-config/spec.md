# Feature Specification: Bulk RADIUS WLAN Configuration

**Feature Branch**: `001-radius-wlan-config`  
**Created**: 2026-03-03  
**Status**: Draft  
**Input**: User description: "Add menu option to scan org WLANs for RADIUS authentication and configure optimal auth server timeout, retries, and fast 802.1X timer settings"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bulk Configure RADIUS WLANs Across Organization (Priority: P1)

A NOC engineer needs to standardize RADIUS authentication timing across all WLANs in the organization. Instead of configuring each WLAN individually (100+ WLANs), they want to scan the entire org, identify WLANs using RADIUS, and apply optimized settings in bulk.

**Why this priority**: This is the core value proposition - eliminating manual, repetitive configuration work across large deployments. Without bulk operation capability, engineers must use menu 102 repeatedly for each site/WLAN combination.

**Independent Test**: Can be tested by running the operation on a test organization with multiple RADIUS-enabled WLANs across different sites and verifying all are updated with a single operation.

**Acceptance Scenarios**:

1. **Given** an organization with 50 WLANs (30 using RADIUS, 20 using PSK), **When** the user runs this menu option, **Then** only the 30 RADIUS WLANs are displayed for bulk configuration.

2. **Given** a RADIUS WLAN scan result showing 15 WLANs, **When** the user confirms the bulk update, **Then** all 15 WLANs receive the specified authentication timer settings.

3. **Given** the user initiates bulk configuration, **When** they review the proposed changes, **Then** current vs proposed values are displayed for each WLAN before confirmation.

---

### User Story 2 - Preview Changes Before Apply (Priority: P1)

Before applying changes to production WLANs, the engineer needs to see exactly what will change. The system must display current settings vs. proposed settings for each WLAN.

**Why this priority**: Safety-critical for production environments. NASA/JPL defensive programming requires explicit preview and confirmation before destructive operations.

**Independent Test**: Can be tested by running the scan and verifying the preview display shows correct current values and proposed changes without actually applying them.

**Acceptance Scenarios**:

1. **Given** the scan identifies 10 RADIUS WLANs with varying current settings, **When** preview is displayed, **Then** each WLAN shows its current `auth_servers_timeout`, `auth_servers_retries`, and `fast_dot1x_timers` alongside the proposed values.

2. **Given** a WLAN already has the target settings, **When** preview is displayed, **Then** that WLAN is marked as "No changes needed" and excluded from the update batch.

---

### User Story 3 - Export Results and Audit Trail (Priority: P2)

After bulk configuration, the engineer needs documentation of what changed for audit purposes. A CSV report showing before/after values for each modified WLAN should be generated.

**Why this priority**: Important for compliance and change management, but not required for core functionality. Engineers can use existing WLAN export features as a workaround.

**Independent Test**: Can be tested by running the bulk update and verifying a CSV file is created in the data directory with before/after values.

**Acceptance Scenarios**:

1. **Given** the bulk update completes successfully, **When** the operation finishes, **Then** a CSV file is saved to `data/` with columns: WLAN name, WLAN ID, site, before timeout, after timeout, before retries, after retries, before fast_dot1x, after fast_dot1x, timestamp.

---

### Edge Cases

- What happens when a WLAN is managed by a WLAN Template (site template inheritance)?
  - Display warning that template-managed WLANs require template modification
  - Offer option to modify at template level if user confirms
- What happens when API rate limiting is encountered during bulk updates?
  - Use existing MistHelper adaptive rate limiting and retry logic
- What happens when the organization has no RADIUS-enabled WLANs?
  - Display informative message and exit gracefully
- What happens when partial failures occur (some WLANs update, others fail)?
  - Continue processing remaining WLANs
  - Report both successes and failures in summary
  - Include failed WLANs in CSV with error reason

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST scan all WLANs in the current organization using `listOrgWlans` API
- **FR-002**: System MUST filter WLANs to only those using RADIUS authentication (presence of `auth_servers`, `radsec.enabled=true`, or `auth.type` in `['eap', 'eap192']`)
- **FR-003**: System MUST display a numbered list of all identified RADIUS WLANs with current settings
- **FR-003a**: System MUST prompt user to select WLANs using flexible input: "all", single index (e.g., "3"), comma-separated indices (e.g., "1,3,5"), ranges (e.g., "1-5"), or combinations (e.g., "1,3,5-10,15")
- **FR-004**: System MUST show current vs proposed values for each WLAN before confirmation
- **FR-005**: System MUST apply these settings to all confirmed WLANs, reading target values from .env with these defaults:
  - `RADIUS_AUTH_TIMEOUT`: 3 seconds (default)
  - `RADIUS_AUTH_RETRIES`: 2 (default)
  - `RADIUS_FAST_DOT1X`: true (default)
- **FR-005a**: System MUST display the loaded .env configuration values at script startup before scanning
- **FR-005b**: System MUST display affected WLAN SSID names and target values for each setting before confirmation
- **FR-006**: System MUST require explicit "APPLY" confirmation before making changes (DESTRUCTIVE operation pattern)
- **FR-007**: System MUST differentiate between site-level WLANs and template-level WLANs
- **FR-008**: System MUST export a change report to CSV after completion
- **FR-009**: System MUST exclude WLANs that already have the target settings (no unnecessary API calls)
- **FR-010**: System MUST handle EOF gracefully in SSH/container sessions

### Key Entities

- **Organization WLAN**: A wireless network configuration that may use RADIUS/RadSec authentication. Key attributes: id, ssid, auth_servers, auth_servers_timeout, auth_servers_retries, fast_dot1x_timers, template_id
- **WLAN Template**: A configuration template that multiple WLANs inherit from. WLANs using templates require template-level modification, not direct WLAN modification.
- **Change Record**: A before/after snapshot of WLAN settings for audit trail purposes

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Engineers can configure RADIUS authentication settings for all org WLANs in under 2 minutes (vs. 30+ minutes manually)
- **SC-002**: 100% of RADIUS WLANs in an organization are identified and displayed during scan
- **SC-003**: Zero unintended WLAN modifications - only WLANs explicitly shown in preview are modified
- **SC-004**: 100% of bulk operations produce a CSV audit trail file
- **SC-005**: System gracefully handles organizations with 500+ WLANs without timeout or memory issues

## Assumptions

- The user has already authenticated with a valid Mist API session (standard MistHelper prerequisite)
- The configured API token has write permissions for WLAN configuration
- Organizations typically have fewer than 1,000 WLANs (reasonable scaling target)
- The target settings (timeout=3, retries=2, fast_dot1x=true) are sensible defaults for enterprise RADIUS deployments based on standard 802.1X best practices

## Clarifications

### Session 2026-03-03

- Q: When the scan finds RADIUS WLANs, should the user select a subset or apply to all? → A: Flexible selection supporting "all", single index, comma-separated indices, ranges (e.g., 1-5), or combinations (e.g., 1,3,5-10,15)
- Q: Should target values be hardcoded or configurable? → A: Configurable via .env with defaults (timeout=3, retries=2, fast_dot1x=true), display loaded values at runtime, show affected SSID names and target values per setting before confirmation
