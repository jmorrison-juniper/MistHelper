# Feature Specification: WAN migration parity recovery

**Feature Branch**: `jmorrison-juniper-4200-migrate-mistwanperformance`

**Created**: 2026-11-05

**Status**: Draft. Bounded collection and poll-sample storage are implemented. Source parity, retention, backfill, and full acceptance remain open.

**Input**: Rebuild the end-to-end Spec Kit workflow for issue #4200, including original-repository comparison, appearance, and complete functionality.

## User Scenarios & Testing

### User Story 1 - Compare all four journeys (Priority: P1)

Operators need the original overview, gateway, WAN-port, and VPN-peer journeys in one MistHelper portal.

**Why this priority**: A migration cannot be accepted without a complete comparison inventory.

**Independent Test**: Trace each source journey to a destination page, comparison record, and browser assertion.

**Acceptance Scenarios**:

1. **Given** a pinned source revision, **When** reviewers examine each journey, **Then** every control, metric, state, and transition has a comparison row.
2. **Given** documented source TODOs, **When** reviewers classify functionality, **Then** incomplete source work remains distinct from completed behavior.
3. **Given** absent copying rights, **When** reviewers compare appearance, **Then** they record observations without importing source code, images, or fixtures.

### User Story 2 - Investigate performance and failures (Priority: P1)

Operators need trustworthy utilization, congestion, status, failover, and availability views.

**Why this priority**: False completeness or incorrect duration can produce incorrect operational decisions.

**Independent Test**: Use independently authored observations with known intervals, gaps, capacity, and role changes.

**Acceptance Scenarios**:

1. **Given** verified capacity and complete intervals, **When** an operator selects a circuit, **Then** utilization and threshold durations match expected values.
2. **Given** incomplete event coverage, **When** an operator examines availability, **Then** the page identifies unavailable results instead of inventing uptime.
3. **Given** verified primary and secondary roles, **When** failover occurs, **Then** the active circuit and primary comparison remain visible.

### User Story 3 - Investigate path quality and SLE (Priority: P1)

Operators need packet loss, latency, jitter, SLE scores, and impact navigation with defined meanings.

**Why this priority**: Current snapshots do not establish historical quality or service experience.

**Independent Test**: Verify historical calculations and impact navigation against approved field and sampling contracts.

**Acceptance Scenarios**:

1. **Given** timestamped quality samples, **When** an operator selects a window, **Then** mean, maximum, and p95 follow approved sampling rules.
2. **Given** no historical peer contract, **When** an operator requests history, **Then** the page states that history is unavailable.
3. **Given** verified SLE mappings, **When** an operator selects an impact, **Then** the destination preserves site, gateway, interface, and time scope.

### User Story 4 - Examine history and audience views (Priority: P2)

Operators and leadership need scoped reports without confusing sparse observations with complete historical measurements.

**Why this priority**: Reporting needs consistent dimensions, coverage, and time boundaries.

**Independent Test**: Compare region, site, circuit, and time results against independently calculated expectations.

**Acceptance Scenarios**:

1. **Given** verified time contracts, **When** users select 3h, 12h, 24h, day, week, or month, **Then** boundaries and coverage are explicit.
2. **Given** a verified 13-month storage contract, **When** users select that history, **Then** the report distinguishes retained, absent, and incomplete intervals.
3. **Given** approved audience requirements, **When** users switch views, **Then** dimensions, filters, and summaries match the approved comparison rows.

### User Story 5 - Use safe integrated journeys (Priority: P1)

Users need consistent authorization, offline isolation, errors, and bounded refresh across the portal.

**Why this priority**: Migration must not compromise existing operations or leak credentials.

**Independent Test**: Complete authorized and denied journeys without production credentials or external browser requests.

**Acceptance Scenarios**:

1. **Given** synthetic preview data, **When** users navigate every page, **Then** each page identifies synthetic data and performs no live collection.
2. **Given** denied access or invalid identifiers, **When** a user opens a detail link, **Then** the portal denies access without collection or disclosure.
3. **Given** throttling or storage failure, **When** refresh runs, **Then** bounded retries and explicit unavailable states preserve existing portal operation.

### Edge Cases

- Empty organizations, removed gateways, encoded port names, peer identity changes, and wrong-site detail links.
- Zero or absent capacity, counter resets, duplicate observations, out-of-order samples, and missing timestamps.
- Partial hours, boundary samples, leap days, month changes, unknown circuit roles, and missing region membership.
- Missing history, stale snapshots, service outages, authorization expiry, and repeated refresh requests.
- Narrow screens, keyboard navigation, empty charts, loading states, errors, and missing visual comparison permission.

## Requirements

### Functional Requirements

- **FR-001**: Inventory every source journey, control, metric, layout region, query value, and navigation transition at a pinned revision.
- **FR-002**: Classify each inventory row as completed source behavior, source TODO, desired goal, or unverified behavior.
- **FR-003**: Preserve the four journeys, identifiers, filters, links, and visual hierarchy through reviewed destination equivalents.
- **FR-004**: Define utilization, capacity, congestion, configurable thresholds, and continuous versus cumulative duration before implementation.
- **FR-005**: Define status transitions, flap counting, availability, primary/secondary roles, failover, and ranking before implementation.
- **FR-006**: Define loss, latency, jitter, timestamps, mean, maximum, p95, sampling, and missing-data rules before implementation. Store each sample by full identity and source timestamp. Treat an unchanged replay as a no-op, keep its first collection time, and reject changed source data without replacing the sample. Keep scalar poll observations distinct when their timestamps differ.
- **FR-007**: Define SLE score meaning, classifiers, impact fields, entity mappings, and time scope before implementation.
- **FR-008**: Define region, site, circuit, hourly aggregation, short windows, calendar boundaries, weighting, and coverage. Keep the existing hourly projection rules unchanged. Keep raw samples separate, and do not claim complete coverage.
- **FR-009**: Define 13-month history, backfill, retention, capacity, completeness, and absent-history behavior without a second database. Keep this contract open until evidence proves those properties. Do not claim 13-month history without proof. Preserve existing rows and do not expire samples before a retention policy is approved.
- **FR-010**: Define executive, engineering, and SLE views from verified audience requirements.
- **FR-011**: Reuse existing portal authorization, API sessions, configured storage, and shared request limits.
- **FR-012**: Prohibit additional web services, public ports, Compose groups, databases, Snowflake, or Redis services.
- **FR-013**: Keep synthetic records isolated from live storage, collection, and status labels.
- **FR-014**: Test authorization, validation, missing data, stale data, API failures, throttling, storage failures, and refresh bounds.
- **FR-015**: Retain approved browser evidence and map every accepted comparison row to a test and reviewer decision.
- **FR-016**: Keep unsupported contracts blocked and preserve draft status until every required acceptance row has evidence.

### Mist Cloud Transport Requirements

Use supported `mistapi` methods. Do not derive methods from source endpoint strings.
The contract inventory must name each exact SDK function, signature, scope, response fields, and failure behavior before use.
Existing snapshot and insight methods require a new pinned compatibility review.
This specification authorizes no new transport or live request.

### Key Entities

- **Comparison row**: Source revision, journey, element, classification, destination, contract, test, evidence, and decision.
- **Observation**: Scoped identity, measurement, unit, timestamp, origin, and coverage.
- **Raw sample**: Full identity, metric, unit, UTC sample timestamp, collection time, timestamp source, origin, and coverage. Distinct poll timestamps remain distinct samples. Replays use full identity and sample time. Keep unchanged source data once, and reject changed data at an existing key.
- **Circuit membership**: Region, site, gateway, port, role, capacity, and effective interval.
- **Reporting window**: UTC boundaries, grain, sample coverage, and calculation policy.
- **Acceptance decision**: Reviewer, evidence revision, result, deviation, and approval.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All four journeys have a complete comparison inventory with zero unclassified rows.
- **SC-002**: Every required completed source behavior has a passing test or an explicitly approved deviation.
- **SC-003**: Every metric displays a verified value, an explicit missing value, or an explicit unsupported state.
- **SC-004**: All accepted calculations match independently calculated expectations, including gaps and boundary cases.
- **SC-005**: All four browser journeys pass navigation, state, layout, and authorization checks without production credentials.
- **SC-006**: Every required visual row has reviewed evidence or remains blocked by a named evidence limitation.
- **SC-007**: No new service, port, database, token store, or synthetic-to-live data path exists.
- **SC-008**: Final acceptance uses the exact tested revision and leaves zero unexplained required gaps.

## Assumptions

- This record replaces the execution sequence, not the historical planning record or original acceptance requirements.
- Existing PR work is provisional until current evidence establishes its behavior.
- Source goals do not prove completed features. Source TODOs are not accepted functionality.
- Written copying rights remain absent. Read-only source comparison does not grant reproduction rights.
- A fresh plan does not authorize merge, deployment, production requests, or automatic implementation of blocked contracts.
- Each scalar poll uses its UTC collection time as its sample timestamp. Time-series responses retain their API timestamps.
- The peer schema bounds MOS from zero through five. Retain the scalar score without quality categories or inferred metric timestamps.
- Retained missing metrics with unknown units remain readable beside later documented values. Do not reinterpret incompatible measured units.
- Independent live SLE inspection uses only cached sites, enabled catalog metrics, a fixed one-hour query, and explicit unknown duration units.
- Destination table controls operate on authorized cached identities only. They do not establish source ordering, complete inventory, or ranking.
- New per-poll sample storage is additive. Existing hourly records remain available, and hourly values derive from samples.
- The existing hourly projection keeps its current calculations. A stored hour does not replace timestamped samples or prove complete coverage.
- Retention, capacity, historical completeness, and backfill remain unverified. No 13-month history guarantee is claimed.
