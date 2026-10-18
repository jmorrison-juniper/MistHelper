# Feature Specification: Site health dashboard

**Feature Branch**: `jmorrison-juniper-mistsitedashboard-planning`

**Created**: 2026-10-18

**Status**: Specified. Live integration and source reuse remain blocked.

**Input**: Issue #4232 requests the MistSiteDashboard migration. The subsequent user direction permits an independent offline implementation slice.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find an affected site (Priority: P1)

An operator compares organization service quality, selects a site, and examines its device health.

**Why this priority**: The operator must locate the affected site before an investigation.

**Independent Test**: Use synthetic sites with known scores, missing values, and disconnected devices.

**Acceptance Scenarios**:

1. **Given** authorized sites, **When** the operator searches by name, **Then** only matching authorized sites appear.
2. **Given** organization results, **When** the operator selects WiFi, Wired, or WAN, **Then** the worst 100 sites appear in metric order.
3. **Given** a selected site, **When** its health loads, **Then** separate AP, switch, and gateway cards show counts and device tables.
4. **Given** missing telemetry, **When** a card loads, **Then** it shows unavailable data, not a healthy score.

### User Story 2 - Examine service quality (Priority: P1)

An operator selects a period, examines service scores, and identifies affected items.

**Why this priority**: A score alone does not identify the cause or affected clients.

**Independent Test**: Use synthetic summary, classifier, and affected-item records with known sample totals.

**Acceptance Scenarios**:

1. **Given** valid samples, **When** a score appears, **Then** it equals the nondegraded percentage without converting missing samples to zero.
2. **Given** a selected metric, **When** the operator opens details, **Then** classifiers show impact duration, events, and affected items.
3. **Given** an affected-item table, **When** the operator exports it, **Then** the CSV contains the selected period and authorized data only.
4. **Given** a failed section, **When** the operator retries it, **Then** other sections retain their period and valid data.

### User Story 3 - Investigate devices and clients (Priority: P2)

An operator follows a device link to wireless clients, wired clients, or gateway WAN details.

**Why this priority**: These views connect an affected service to a device, client, or interface.

**Independent Test**: Follow synthetic device links without an external connection.

**Acceptance Scenarios**:

1. **Given** an AP, **When** the operator opens clients, **Then** sessions show SSID, signal, band, usage, and history.
2. **Given** a switch, **When** the operator opens clients, **Then** rows show port, VLAN, MAC, address, and available session data.
3. **Given** a gateway, **When** the operator opens WAN details, **Then** ports, VPN peers, and BGP peers appear separately.
4. **Given** a narrow screen, **When** the operator opens affected items, **Then** the dialog remains usable without hiding its close control.

### Edge Cases

- An empty site list differs from a denied request or failed request.
- A zero denominator, absent samples, and incomplete samples do not produce a healthy score.
- Unknown device state remains unknown, not disconnected or connected.
- Invalid identifiers, categories, periods, and export fields fail before collection.
- Expired access, HTTP 403, HTTP 429, HTTP 5xx, timeouts, and partial pages show explicit states.
- Site changes cancel or discard older responses. Data from another organization never replaces the current view.
- Template periods disagree with route periods in the source. Unsupported periods remain blocked until contract verification.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Operators MUST enter the dashboard through the existing portal and retain the selected organization and site.
- **FR-002**: Site selection MUST support search, empty results, and organization-scoped access.
- **FR-003**: Organization views MUST retain WiFi, Wired, and WAN tabs, metric selection, worst-100 ordering, and site links.
- **FR-004**: Site views MUST retain device cards, sortable tables, AP SSIDs, client counts, and available device details.
- **FR-005**: Service views MUST retain collapsible categories, score text, color indicators, periods, and detail links.
- **FR-006**: Classifier views MUST retain distribution, affected items, impact bars, dynamic safe columns, and CSV export.
- **FR-007**: Client and gateway views MUST preserve the workflows in User Story 3, including expandable peer tables.
- **FR-008**: Manual refresh and section retry MUST preserve filters and expose collection time, stale data, and explicit failure states.
- **FR-009**: Access restrictions MUST apply to pages, data, refresh, and export. Credentials MUST remain on the server.
- **FR-010**: The dashboard MUST use the existing application, database, and deployment group without a second database service.
- **FR-011**: The migration MUST not reuse protected source code, branding, screenshots, or assets without an approved license path.
- **FR-012**: Automated checks MUST cover units, integration, browser interactions, invalid data, failures, access, and secret redaction.
- **FR-013**: Every new browser control MUST have a stable test identifier. Failed browser flows MUST retain a screenshot or trace.
- **FR-014**: The independent offline score model MUST reject negative, noninteger, boolean, inconsistent, and partially absent sample counts.
- **FR-015**: The dashboard MUST make no Mist or device changes. A local refresh must not authorize a cloud write.

### Mist Cloud Transport Requirements

All live collection must use the installed `mistapi` SDK. No owned REST or WebSocket transport is proposed.
The method inventory and unresolved response contracts are in [API contracts](design/contracts/api.md).
Symbol availability alone does not prove permissions, pagination, response shape, or duration semantics.
Live integration requires mocked SDK contract tests for these behaviors, errors, and redaction.

### Key Entities

- **Site**: Organization-scoped identity and display name.
- **Health snapshot**: Device states and collection time for one site.
- **Service measurement**: Metric, period, sample totals, degraded samples, and availability.
- **Affected item**: Classifier-scoped device, client, interface, or application with measured impact.
- **Refresh state**: Scope, selected period, collection status, and last successful collection time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator reaches an affected site from the organization view within three selections.
- **SC-002**: All three service categories retain their selected metric and period after a successful manual refresh.
- **SC-003**: Every unavailable or failed measurement remains distinguishable from zero and 100 percent in automated scenarios.
- **SC-004**: All eight source page workflows have a mapped acceptance scenario and future browser test.
- **SC-005**: Synthetic score cases at zero, partial degradation, and complete degradation produce exact expected percentages.
- **SC-006**: Unauthorized scope and malformed input produce no collected or exported records in every negative test.

## Assumptions

- Preserve useful information order and interactions, not protected visual expression or branding.
- No automatic refresh interval is required. Source templates contain manual refresh controls but no `setInterval` timer.
- Existing portal network restrictions are not user authentication. Per-user authorization remains a separate approval gate.
- The offline score model accepts normalized integer sample counts, not unverified SDK responses.
- The original issue requests planning only. The later user direction authorizes offline implementation after this workflow.
- Planning approval, source reuse, cloud access, deployment, and shared-file ownership remain separate decisions.
