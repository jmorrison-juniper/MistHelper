# Feature Specification: MistCircuitStats WAN Dashboard

**Feature Branch**: `feat/4195-mistcircuitstats-wan-dashboard`

**Created**: 2026-10-13

**Status**: Draft

**Input**: Integrate the MistCircuitStats gateway WAN dashboard into the current MistHelper portal. Preserve its layout and user workflows, use MistHelper's shared services, and do not add another database or application stack.

## User Scenarios & Testing

### User Story 1 - Review organization WAN health (Priority: P1)

A network operator opens the WAN dashboard tab and reviews gateway status and WAN port totals for an authorized Mist organization. The operator filters by site or gateway and searches the results.

**Why this priority**: The organization view is the main dashboard workflow and gives operators a useful overview before they inspect a gateway.

**Independent Test**: Load synthetic organization, site, gateway, and port data. Verify that the table shows every page of gateway records and that filters return only matching rows.

**Acceptance Scenarios**:

1. **Given** an authorized organization with gateways across multiple sites, **When** the operator opens the WAN dashboard, **Then** the dashboard shows gateway status and WAN port totals with readable site names.
2. **Given** a result set with more records than one Mist API page, **When** the operator searches or filters by site, **Then** the dashboard searches the complete result set and shows only matching gateways.
3. **Given** a Mist API rate limit, **When** the dashboard refreshes, **Then** it retains the last successful data and shows a rate-limit notice.

### User Story 2 - Inspect a gateway port (Priority: P2)

A network operator expands a gateway row to review its WAN port configuration, current counters, link details, and VPN peer paths. The operator opens a traffic chart for a port and chooses a supported time range.

**Why this priority**: Port-level details help operators identify the circuit or device that needs investigation.

**Independent Test**: Load synthetic gateway, port, and peer-path data. Verify the expanded details and traffic chart for each supported time range.

**Acceptance Scenarios**:

1. **Given** a gateway with configured WAN ports, **When** the operator expands its row, **Then** the dashboard shows each port's configuration type, VLAN, MAC address, speed, uptime, and counters when Mist provides them.
2. **Given** a gateway with VPN peer paths, **When** the operator opens its peer-path view, **Then** the dashboard shows path status and available link-quality values.
3. **Given** a selected port and a supported range of 1 hour, 6 hours, 24 hours, or 7 days, **When** the operator opens the traffic chart, **Then** the chart uses the selected range and the source dashboard's 10-minute buckets for the 1-hour range.
4. **Given** a port lacks optional configuration or statistics, **When** the operator opens its details, **Then** the dashboard identifies the missing values without hiding the remaining details.

### User Story 3 - Review WAN Insights and export data (Priority: P3)

A network operator reviews hourly bandwidth, link health, and Application Health SLE for a gateway port. The operator exports the main gateway table or per-port hourly metrics for offline review.

**Why this priority**: Insights and exports provide deeper circuit analysis and support work outside the portal.

**Independent Test**: Load synthetic insight and SLE responses. Verify all supported insight ranges and both CSV formats, including their headers and row selection.

**Acceptance Scenarios**:

1. **Given** insight data for a port, **When** the operator selects 1 hour, 6 hours, 24 hours, 3 days, or 7 days, **Then** the dashboard shows hourly average and peak Rx/Tx rates and available jitter, latency, and loss values.
2. **Given** Application Health SLE data, **When** the operator opens WAN Insights, **Then** the dashboard shows the summary, trend, impacted interfaces, and site threshold when Mist returns them.
3. **Given** a gateway table or per-port hourly view, **When** the operator exports CSV, **Then** the download contains the selected data and the documented header order.
4. **Given** a Mist API failure, **When** the operator opens or refreshes a view, **Then** the dashboard shows a clear error state and does not report an empty result as a successful response.

### Edge Cases

- Mist returns no gateways, no WAN ports, or an empty insight period.
- The organization contains more than 1,000 sites or gateways and requires pagination.
- A gateway lacks a site name, profile, gateway template, port configuration, or optional counter.
- Site, gateway, or port identifiers contain characters that require URL encoding.
- Mist returns HTTP 429, another 4xx or 5xx response, malformed data, or a timeout.
- A cache entry expires or the shared Redis service is unavailable.
- A configured token lacks access to the selected organization.
- A daylight-saving transition or site timezone changes the display of a UTC time range.
- Mist data contains text that resembles HTML, a spreadsheet formula, or a CSV delimiter.
- A previously successful response exists when a refresh fails.

## Requirements

### Functional Requirements

- **FR-001**: The MistHelper portal MUST provide a WAN dashboard tab within its existing navigation.
- **FR-002**: The dashboard MUST preserve the source dashboard's responsive organization overview, gateway table, expandable details, chart, WAN Insights, and export workflows.
- **FR-003**: The dashboard MUST allow an operator to search and filter gateways by site and gateway across the complete paginated result set.
- **FR-004**: The dashboard MUST show gateway status, WAN port totals, and readable site names for the selected authorized organization.
- **FR-005**: The dashboard MUST show available port configuration, VLAN, MAC address, speed, uptime, counters, and VPN peer-path details.
- **FR-006**: Traffic charts MUST support 1-hour, 6-hour, 24-hour, and 7-day ranges. The 1-hour range MUST retain 10-minute buckets.
- **FR-007**: WAN Insights MUST support 1-hour, 6-hour, 24-hour, 3-day, and 7-day ranges and show hourly average and peak Rx/Tx, link jitter, latency, loss, and Application Health SLE data when available.
- **FR-008**: The dashboard MUST export the main gateway table and per-port hourly metrics as CSV. The hourly export MUST retain the source's 12-column layout.
- **FR-009**: The dashboard MUST use MistHelper's configured Mist session and the supported `mistapi` SDK. It MUST not send direct HTTP requests to Mist endpoints.
- **FR-010**: The integration MUST retain 429 handling and try each authorized token no more than once per Mist SDK request. It MUST honor the existing 60-second per-token cooldown. It MUST show a notice and retain the last successful data while all tokens are on cooldown.
- **FR-011**: The dashboard MUST reuse the existing MistHelper portal, compose group, shared data services, and Redis service. It MUST NOT add another database or Redis service.
- **FR-012**: Cached organization, site, profile, and gateway-template data MUST use namespaced keys, bounded lifetimes, and the shared cache service. A cache failure MUST NOT start a second cache service or database.
- **FR-013**: The dashboard MUST identify stale, missing, empty, and failed data states. It MUST not convert a failed Mist request into a success response with empty data.
- **FR-014**: The dashboard MUST use existing portal security middleware, organization access checks, CSRF protections, and secret-redaction rules.
- **FR-015**: The dashboard MUST escape Mist-provided text before display and neutralize spreadsheet formulas in CSV output.
- **FR-016**: The dashboard MUST identify timestamps in UTC and display them using the selected site timezone when available.
- **FR-017**: New controls and result areas MUST expose stable `data-testid` values for end-to-end tests.
- **FR-018**: The integration MUST preserve source attribution and the CC BY-NC-SA 4.0 license terms. The source and target repositories both publish that license.

### Mist Cloud Transport Requirements

All Mist reads MUST use these `mistapi` methods from the source dashboard's documented request set. Use only methods required by each view and pass explicit arguments.

- `mistapi.api.v1.self.self.getSelf`
- `mistapi.api.v1.orgs.orgs.getOrg`
- `mistapi.api.v1.orgs.sites.listOrgSites`
- `mistapi.api.v1.orgs.inventory.getOrgInventory`
- `mistapi.api.v1.orgs.deviceprofiles.getOrgDeviceProfile`
- `mistapi.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate`
- `mistapi.api.v1.orgs.stats.listOrgDevicesStats`
- `mistapi.api.v1.orgs.stats.searchOrgSwOrGwPorts`
- `mistapi.api.v1.sites.devices.getSiteDevice`
- `mistapi.api.v1.sites.devices.searchSiteDevices`
- `mistapi.api.v1.sites.stats.getSiteDeviceStats`
- `mistapi.api.v1.orgs.stats.searchOrgPeerPathStats`
- `mistapi.api.v1.sites.insights.getSiteInsightMetricsForGateway`
- `mistapi.api.v1.sites.insights.getSiteInsightMetricsForDevice`
- `mistapi.api.v1.sites.sle.getSiteSleSummaryTrend`
- `mistapi.api.v1.sites.sle.listSiteSleImpactedInterfaces`
- `mistapi.api.v1.sites.sle.getSiteSleThreshold`

The documented source request set uses `getSiteInsightMetricsForGateway` for both per-port hourly metrics and table charts. These are two call shapes, not two distinct SDK methods. No Mist WebSocket transport is required.

Contract tests MUST prove the installed SDK signatures, authentication reuse, endpoint and argument parity, pagination, failure handling, retained-data messaging, and secret redaction. They MUST also prove that 4xx, 5xx, timeout, and rate-limit responses cannot appear as successful empty results.

### Key Entities

- **Organization**: A Mist organization available to the configured Mist session.
- **Site**: A location in an organization with a name, timezone, and Mist identifier.
- **Gateway**: A Mist device with site, model, status, and configuration-source details.
- **WAN Port**: A gateway interface with its configuration, counters, and link measurements.
- **Traffic Sample**: A timestamped Rx/Tx measurement for a gateway port.
- **Peer Path**: A VPN path associated with a gateway and its available health measurements.
- **WAN Insight**: A time-bounded view of bandwidth, link health, and Application Health SLE values.
- **Export**: A CSV representation of the selected gateway rows or hourly port metrics.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All three dashboard user journeys can be completed in the MistHelper portal without opening the source application.
- **SC-002**: Tests confirm that all four traffic ranges and all five WAN Insights ranges return the expected time window.
- **SC-003**: A synthetic organization with more than 1,000 records returns every eligible gateway and site in the filtered result.
- **SC-004**: Each exported hourly CSV has exactly 12 columns, and its rows match the selected gateway, port, and time range.
- **SC-005**: Every tested rate-limit or API failure shows a visible status and preserves the last successful result where one exists.
- **SC-006**: Deployment adds no database or Redis service and continues to use the existing MistHelper compose group.
- **SC-007**: Existing MistHelper portal journeys and routes pass their regression tests.
- **SC-008**: Tests prove that a request tries no more than the configured number of authorized tokens, honors the 60-second cooldown, and preserves the last successful data when all tokens are on cooldown.
- **SC-009**: The implementation pull request records source and integrated page latency for the same synthetic organization before it proposes a new latency target.

## Assumptions

- Operators use MistHelper's existing portal access policy and Mist session. This feature does not add a separate sign-in system or store a second copy of Mist credentials.
- The current organization selection controls the dashboard. Operators can select only an organization that the configured Mist session can access.
- This integration covers the base `MistCircuitStats` repository. The Redis-specific source repository has a separate migration issue and plan.
- The base source dashboard uses bounded in-process caches. The integration will use MistHelper's shared cache path where appropriate. It will not add another Redis service.
- The dashboard reads Mist data only. It does not change Mist configuration or device state.
- The source and target repositories both use CC BY-NC-SA 4.0. The implementation will retain attribution and note modifications.
- The dashboard will keep the source page structure and workflows while adopting the MistHelper portal navigation, security controls, and visual shell.
