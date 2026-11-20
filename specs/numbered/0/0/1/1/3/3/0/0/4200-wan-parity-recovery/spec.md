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

### User Story 6 - Use explicit replacement contracts (Priority: P1)

Operators need useful, defined behavior when original contracts or historical evidence are absent.

**Independent Test**: Compare independently designed reports with hand-calculated expectations and clearly labeled synthetic historical records.

**Acceptance Scenarios**:

1. **Given** retained hourly projections, **When** users request observation statistics, **Then** values follow the named replacement policy without claiming source sampling semantics.
2. **Given** missing measurements, **When** users inspect thresholds or percentiles, **Then** missing values remain absent and observation counts never become elapsed coverage.
3. **Given** thirteen months of independent synthetic records, **When** validation exercises isolated storage, **Then** evidence identifies synthetic provenance and does not claim production retention.
4. **Given** cached or retained observations, **When** users select an exact metric and unit, **Then** numeric ranking preserves full identities and stable ties.
5. **Given** operator metadata, **When** users declare an effective interval, **Then** the interface labels declaration provenance without changing network configuration.
6. **Given** an archive, **When** users request import, **Then** synthetic records remain isolated and live writes require trusted review and preserve existing observations.

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
- **FR-017**: Version replacement behavior separately from source behavior. Distinguish observed source facts, independently designed rules, operator declarations, and synthetic evidence.
- **FR-018**: Summarize one full identity, metric, and unit from present hourly projections with equal observation weights and a nearest-rank p95.
- **FR-019**: Permit an integer observation threshold from zero through 100, defaulting to 80. Count strict exceedances and adjacent above-threshold hour keys without claiming duration.
- **FR-020**: Validate thirteen calendar months with independently authored synthetic records, exact boundaries, identity isolation, missing periods, and preserved provenance.
- **FR-021**: Define replacement ranking, declared metadata, backfill eligibility, and acceptance policies before their implementation. Missing network facts remain explicit input requirements.
- **FR-022**: Rank existing scoped observations numerically by an exact metric/unit pair. Preserve stable identity/time ties, missing states, and a twenty-row display bound without new acquisition.
- **FR-023**: Validate operator-declared capacity, region, and role with full identity and UTC effective intervals. Preserve declaration provenance and provide explicit process-lifetime and export states.
- **FR-024**: Validate bounded version-one projection archives before import. Separate synthetic storage and require trusted digest review and typed confirmation for atomic, non-replacing live imports.

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
- **SC-009**: Observation reports preserve zero, missing values, exact metric units, and full identity with no additional acquisition or history reads.
- **SC-010**: Replacement threshold and percentile results match hand-calculated boundaries, sparse hours, ties, and extreme finite numbers.
- **SC-011**: Synthetic historical validation reports actual record counts and scope results, distinguishing temporary SQLite execution from mocked Arango evidence.
- **SC-012**: Ranking tests prove numeric order, stable ties, zero/missing/unit separation, route scope, and unchanged request/read counts.
- **SC-013**: Declaration tests reject invalid capacity, timestamps, identities, and confirmation. Browser interactions preserve declared metadata without network operations.
- **SC-014**: Archive tests prove bounded decoding, exact provenance and identity, namespace separation, trusted-review admission, atomic conflict rejection, and unchanged existing records.

## Assumptions

- The later user direction authorizes independently designed replacements, not invented source contracts, production records, or historical completeness.
- The version-one replacement contract is [defined separately](design/contracts/replacements.md).
- Replacement observation statistics weight each present hourly projection equally. They are not raw-sample, duration-weighted, or source-equivalent statistics.
- Replacement threshold runs describe adjacent observed UTC hour keys, not continuous measured time.
- New verified commits may receive uniquely named remote recovery copies. The existing PR branch and publication hold remain unchanged.
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
- Cached-site navigation uses only site identifiers present in the selected organization's cached pages. It does not claim complete site inventory.
- Independent 6-hour, 12-hour, 24-hour, and 7-day UTC views show retained hourly observations for one verified detail identity.
- Retained windows end at the current UTC hour boundary and exclude the current hour. Missing buckets remain missing, not measured healthy time.
- Independently designed retained plots show discrete hourly projection values for one identity, metric, and unit.
  Keep missing hours as gaps and missing values absent. Preserve measured zero and separate incompatible units.
  Label the UTC bucket axis, collection time, and unknown measurement completeness.
  Do not imply source metric timestamps, continuous measurements, source-equivalent charts, or interpolated history.
- Independent retained-plot controls may zoom and move the visible UTC bucket interval, inspect exact points, reset the view, and download a local PNG.
  Keep the original retained interval, metric units, raw values, and accessible table unchanged.
  Client-side controls must make no collection or history request and must show rendering failures explicitly.
- Each retained metric plot may independently hide or show its rendered points through an accessible button.
  Keep the UTC view, vertical extent, other plots, exact table, and missing reasons unchanged.
  View reset must not override the operator's visibility choice. A hidden plot and its PNG must state that the operator hid its points.
  This is not a multi-series source legend, a data filter, or a claim that observations are absent.
- Independent rectangle selection may identify already rendered visible points within inclusive plot-coordinate boundaries.
  Pointer dragging and keyboard percentage inputs must use the same bounds and preserve exact bucket, collection, metric, unit, and identity metadata.
  Keep all table rows, missing values, other figures, and request counts unchanged. Do not calculate an aggregate or infer source polygon semantics.
  Clear the selection when the UTC view or visibility changes. Reject invalid bounds explicitly, without replacing a previous valid selection.
- A selected gateway may display already cached discovery fields for CPU usage, memory usage, device uptime, and last observation.
  Use documented percentages, seconds since boot, and observation epoch seconds. Do not derive CPU usage from idle time.
  Require exact organization, site, gateway, and device-type membership. Preserve zero and explicit missing or invalid fields.
  These fields have no source metric sampling time and do not enter hourly projections, samples, exports, or availability calculations.
- Independent raw SLE controls may sort gateway MAC, name, or model text and display five returned rows per page.
  Preserve response order for equal text, missing numeric values, site/metric scope, and explicit unknown units and completeness.
  Source order remains available. Display controls must not submit the form or request additional API pages.
- Organization and site windows do not combine identity histories. They report unavailable history until the operator selects one gateway, port, or peer.
- New per-poll sample storage is additive. Existing hourly records remain available, and hourly values derive from samples.
- The existing hourly projection keeps its current calculations. A stored hour does not replace timestamped samples or prove complete coverage.
- Retention, capacity, historical completeness, and backfill remain unverified. No 13-month history guarantee is claimed.
