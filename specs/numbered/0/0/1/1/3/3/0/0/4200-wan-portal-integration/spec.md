# Feature Specification: WAN Performance portal integration

**Feature Branch**: `feat/4200-wan-portal-integration` (planned)
**Record**: `specs/numbered/0/0/1/1/3/3/0/0/4200-wan-portal-integration/`
**Created**: 2026-11-26
**Status**: Draft
**Issue**: #4200 (keep open until acceptance)
**Depends on**: PR #4208 (draft, DIRTY), PR #4629 (merged), PR #4291 (merged)
**Input**: Integrate the MistWANPerformance dashboard into the MistHelper web portal.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the WAN overview in the existing portal (Priority: P1)

A network operator opens the WAN Performance overview from the existing MistHelper portal navigation. The overview shows circuit utilization, congestion, availability, path quality, packet loss, latency, and jitter for the selected organization.

**Why this priority**: The overview is the entry point for every other WAN journey. Without it, no operator can start an investigation.

**Independent Test**: Start the portal with live configuration and open the overview page. The page shows a live value, a stale value, or an explicit "no data" state for each metric.

**Acceptance Scenarios**:

1. **Given** live access is configured, **When** the operator opens the overview page, **Then** the page shows live metric cards.
2. **Given** the Mist API returns an error, **When** the operator opens the overview page, **Then** the page shows an error state.

---

### User Story 2 - Inspect a gateway and its WAN ports (Priority: P1)

A network operator selects a gateway from the overview and opens the gateway page. The page lists the WAN ports of that gateway with their latest metrics.

**Why this priority**: The gateway page is the main drill-down path from the overview.

**Independent Test**: Open the gateway page for one gateway identifier. The page lists each WAN port with its identifier and latest metric.

**Acceptance Scenarios**:

1. **Given** a valid site and gateway identifier, **When** the operator opens the gateway page, **Then** each WAN port row shows its identifier and metric values.
2. **Given** an invalid gateway identifier, **When** the operator opens the gateway page, **Then** the page rejects the identifier and makes no Mist API call.

---

### User Story 3 - Inspect a WAN port (Priority: P1)

A network operator opens one WAN port from the gateway page. The page shows the port metrics and its current state.

**Why this priority**: Port-level evidence is required to confirm a circuit problem.

**Independent Test**: Open the WAN port page for one port identifier. The page shows the port name and the latest metric values.

**Acceptance Scenarios**:

1. **Given** a port with a current snapshot, **When** the operator opens the WAN port page, **Then** the page shows metric values in UTC.
2. **Given** a port with no current snapshot, **When** the operator opens the WAN port page, **Then** the page shows "no data" and no zero value.

---

### User Story 4 - Inspect a VPN peer (Priority: P1)

A network operator opens a VPN peer path from the overview or from a gateway page. The page shows the latest loss, latency, and jitter values for that peer path.

**Why this priority**: VPN peer health is part of the source journey set and the acceptance criteria.

**Independent Test**: Open the VPN peer page for one peer identifier. The page shows the latest values and states that historical peer series are unavailable.

**Acceptance Scenarios**:

1. **Given** a valid peer identifier, **When** the operator opens the VPN peer page, **Then** the page shows the latest loss, latency, and jitter values.
2. **Given** a historical peer series request, **When** the operator opens the VPN peer page, **Then** the page shows the gap text from FR-019.

---

### User Story 5 - Review stored hourly history and summaries (Priority: P2)

A network operator reviews stored hourly observations and daily, weekly, and monthly summaries for one scope.

**Why this priority**: Summaries support trend review, but they depend on stored data that exists only after collection runs.

**Independent Test**: Load a fixed set of hourly rows from the configured store and check each summary value against a hand calculation.

**Acceptance Scenarios**:

1. **Given** 24 complete hourly rows for one day, **When** the summary is computed, **Then** the daily value equals the hand-calculated value.
2. **Given** no stored rows for the scope, **When** the summary is requested, **Then** the page shows "no history" and no average.

---

### User Story 6 - Use the synthetic preview with clear labels (Priority: P2)

A user opens the synthetic preview to learn the layout without a live Mist connection. Every value on the page is marked as synthetic.

**Why this priority**: The preview supports training and layout review. It must never pass as live data.

**Independent Test**: Open each synthetic preview page with no live configuration. Every metric value carries the synthetic label.

**Acceptance Scenarios**:

1. **Given** no live configuration, **When** the user opens a synthetic preview page, **Then** a banner states that the data is synthetic.
2. **Given** a synthetic record, **When** the live page renders the same scope, **Then** the live page does not show the synthetic record.

---

### Edge Cases

- A site identifier is missing from the request. The page shows the missing-site state and makes no call.
- A gateway has no WAN port rows. The gateway page shows "no ports".
- A port has no history rows. The WAN port page shows "no history".
- A Mist API response returns HTTP 429. The refresh stops and the page shows the rate-limit state.
- A Mist API response returns HTTP 5xx. The page shows the API error state.
- A Mist API response includes a `next` URL. The page reads one page only and reports the page bound.
- The Redis service is down during a background refresh. The refresh stops and the page shows stale data.
- The Redis service is down during an operator read. The read uses the bounded local ceiling from D-4.
- The configured store is down during a summary request. The page shows the store state and no average.
- A peer identifier contains a path component. The request is rejected before any Mist call.
- A synthetic record reaches the live page. The record is dropped and the page logs an error line.

### Functional Requirements

- **FR-001**: The feature MUST classify each source page, route, and metric as completed, marker, goal, or unverified before any parity claim.
- **FR-002**: The portal MUST show the WAN Performance navigation item only when `wan_performance.live.overview` is registered and `WAN_PERFORMANCE_NAV_ENABLED` is true.
- **FR-003**: The portal MUST provide the overview, gateway, WAN port, and VPN peer pages, with source identifiers and query names preserved.
- **FR-004**: Synthetic preview routes MUST live under `/wan-performance/preview/`. Each synthetic page MUST show a banner and mark each record with `data_origin` set to `synthetic`.
- **FR-005**: Live pages MUST show utilization, congestion, availability, path quality, packet loss, latency, and jitter. A missing value MUST show "no data", never zero.
- **FR-006**: Time values MUST use UTC. Summaries MUST derive from stored hourly rows with equal weights.
- **FR-007**: The portal MUST validate site, device, port, and peer identifiers with `IdentityValidator` before any Mist call or store query.
- **FR-008**: The feature MUST call Mist only through the mistapi functions in `contracts/mist-api-calls.md`.
- **FR-009**: Each Mist request MUST respect these bounds: 100 records per page, 2 peer rows, and 5000 requests per rolling hour per credential. The feature MUST set urllib3 retries to zero. Each overview request MUST make at most 2 gateway calls.
- **FR-010**: Background refresh MUST be off by default. One worker MUST hold the lease for each organization. The worker MUST stop when the portal stops.
- **FR-011**: Historical rows MUST use the configured store only, with natural keys. The feature MUST NOT add a second application database.
- **FR-012**: Redis keys MUST use only the `misthelper:api:v1:` and `misthelper:wan:v1:` namespaces. Failure behavior MUST follow D-4.
- **FR-013**: The feature MUST reuse the portal `SecurityMiddleware` allowlist and CSRF protection. The feature MUST NOT add a token store.
- **FR-014**: No secret value MUST appear in logs, pages, errors, or tests. The Redis password MUST come from configuration only.
- **FR-015**: Each failure case MUST show a named state. Failure cases are API 4xx and 5xx, HTTP 429, a missing site, missing history, a Redis outage, and a store outage. No state MUST show a server error page.
- **FR-016**: Each new interactive element MUST carry a stable `data-testid` attribute.
- **FR-017**: Browser tests MUST cover this journey: overview, gateway, WAN port, VPN peer, overview.
- **FR-018**: The `/wan-dashboard` routes, responses, and tests MUST remain unchanged.
- **FR-019**: Historical VPN peer metrics, WAN SLE scores, 13-month history, and p95 values MUST show an explicit unsupported state until a verified contract exists.
- **FR-020**: The feature MUST cite MistWANPerformance revision `2d1c2199` as a behavior reference only. The feature MUST NOT copy source code, fixtures, or screenshots without an approved D-1 decision.
- **FR-021**: The feature MUST update `documentation/wan-performance.md` and add `changelog.d/issue-4200-wan-portal-integration.md`.

### Mist Cloud Transport Requirements

- `searchOrgSwOrGwPorts` (R120) supplies WAN port rows for an organization.
- `searchOrgPeerPathStats` (R119) supplies VPN peer statistics. The call uses `mac`, `site_id`, `duration`, and `limit`.
- `listOrgDevicesStats` (R121) supplies device inventory with running state.
- `getSiteInsightMetricsForGateway` (R122) supplies gateway metrics for one site and device.
- `getSiteInsightMetricsForDevice` (R123) is optional. It is used only when a verified metric name requires it.
- No owned WebSocket transport is required. The feature makes no direct HTTP request to a Mist endpoint.

### Key Entities

- **Site**: One Mist site. Natural key: `site_id`.
- **Gateway**: One gateway device in a site. Natural key: `device_id`.
- **WAN port**: One port on a gateway. Natural key: site, device, and port name.
- **VPN peer path**: One peer path. Natural key: organization, peer MAC, and site scope.
- **Hourly observation**: One metric value for one entity and one UTC hour. Natural key: entity key plus hour.
- **Summary**: One daily, weekly, or monthly value derived from hourly observations.
- **Snapshot**: The latest current values for one scope, with a UTC capture time.
- **Refresh lease**: The owner record for one organization refresh. Key: `misthelper:wan:v1:refresh:{org_id}`.
- **Synthetic record**: One fixed sample value. Field: `data_origin` set to `synthetic`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The source inventory has zero unclassified rows.
- **SC-002**: Each FR maps to at least one task and at least one test in `analysis.md`.
- **SC-003**: The five-step browser journey passes in one test command.
- **SC-004**: Ten controlled inputs produce the expected utilization, quality, and hourly values.
- **SC-005**: Tests find zero synthetic values rendered on a live page.
- **SC-006**: A Redis outage test stops the background refresh and shows a stale state.
- **SC-007**: A mocked overview request makes at most two gateway calls.
- **SC-008**: The compose diff adds zero services and zero published ports.

## Assumptions

- The operator has a configured Mist API session through the existing portal session.
- The configured store already exists and holds the operator's history.
- Redis is optional for operator reads and required for background refresh.
- The 31-day read bound in D-2 is acceptable for the first release.
- The mistapi pin `mistapi>=0.64.0,<0.65` remains in force for this feature.
- PR 4208 remains the owner of its branch until the owner resolves the conflicts (D-11).

## Out of Scope

- Source CLI collection and aggregation functions that remain unimplemented stubs.
- Executive, engineering, and SLE views (D-3). PR 4208 SLE route at `live_routes.py` line 259 is out of scope.
- Replacement pages at `live_routes.py` line 260 onward. The replacement contract stays in the legacy record (R26) until a later issue.
- 13-month retention, backfill, and purge (D-2).
- Snowflake connections and any second application database.
- New containers, new services, and new published ports.
- Copies of source code, fixtures, or screenshots (D-1).

## Clarifications

### Session 2026-11-26

- Q: May the team copy source code from MistWANPerformance? A: No. Use an independent implementation. Any copy needs the D-1 human decision.
- Q: Does this planning record close issue #4200? A: No. The issue stays open until acceptance (D-13).
- Q: Which routes do the new pages use? A: Live pages use `/wan-performance/live/`. Synthetic pages use `/wan-performance/preview/` (D-6).
- Q: Is background refresh on by default? A: No. Operators enable it with `WAN_BACKGROUND_REFRESH=true` (D-5).
- Q: Does PR 4208 become the base for the feature? A: No. Main is the base, and PR 4208 changes are ported (D-11).
