# Feature Specification: MistCircuitStats Redis Dashboard Migration

**Feature Branch**: `3993-mistcircuitstats-redis`

**Created**: 2026-10-14

**Reviewed**: 2026-10-18

**Status**: Draft. Product implementation remains blocked by the recorded approval gates.

**Input**: Migrate the read-only MistCircuitStats-Redis dashboard into MistHelper. Preserve its useful workflows without adding another application, database, or duplicate WAN views.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review Site WAN Status (Priority: P1)

An operator opens the existing MistHelper portal and reviews supported gateway WAN status across authorized sites. The operator uses one canonical WAN overview.

**Why this priority**: Operators need one place to check network status. Duplicate pages or collectors increase load and confuse results.

**Independent Test**: With synthetic records for multiple sites, verify that the overview shows only authorized sites and identifies each record as synthetic.

**Acceptance Scenarios**:

1. **Given** authorized sites with gateway records, **When** an operator filters by site, **Then** the overview shows matching gateways and no other site data.
2. **Given** a gateway with supported WAN port records, **When** an operator opens its details, **Then** the portal shows the available traffic and peer-path views once.
3. **Given** a related migration provides a view, **When** operators plan this migration, **Then** they reuse or extend that view instead of creating a duplicate.

### User Story 2 - Judge Data Freshness (Priority: P2)

An operator checks when gateway, port, and peer data last refreshed. The operator can distinguish current data, stale data, partial data, and a refresh failure.

**Why this priority**: Cached values can remain visible when Mist or Redis is unavailable. Clear freshness helps operators avoid treating old values as live.

**Independent Test**: Use synthetic snapshots with known collection times and simulated API or Redis failures. Verify the portal labels freshness and retains no false live status.

**Acceptance Scenarios**:

1. **Given** a successful refresh, **When** an operator views a record, **Then** its collection time and data state are visible.
2. **Given** a refresh fails, **When** an operator views the dashboard, **Then** the last valid snapshot remains identifiable as stale or partial.
3. **Given** that Redis is unavailable, **When** an operator requests dashboard data, **Then** the portal follows a documented safe failure policy and reports the unavailable data.

### User Story 3 - Review Offline Examples (Priority: P3)

An operator or reviewer opens an offline preview and uses example data without Mist credentials or a live Mist request.

**Why this priority**: Offline examples support safe review and test work without access to production network data.

**Independent Test**: Run the preview with network access disabled. Verify that it uses fictional data and labels every result as synthetic.

**Acceptance Scenarios**:

1. **Given** an offline preview, **When** an operator opens a site or gateway, **Then** the page states that its data is fictional.
2. **Given** a live data request, **When** Mist access is missing, **Then** the portal does not substitute synthetic records for live results.

### Edge Cases

- A site, gateway, WAN port, peer, or insight record is absent or has an invalid identifier.
- A paginated response is empty, incomplete, repeated, or interrupted by an API limit.
- A refresh stops after updating only part of a site's records.
- Redis is unavailable, a value cannot be decoded, or a cache key belongs to another feature.
- A snapshot expires while Mist is unavailable.
- Two refresh triggers arrive for the same organization at once.
- A source setting has no documented default, or its implementation differs from its operations guide.
- A related migration is still open, changes ownership, or adds the same collector or view.
- The source license does not permit the proposed reuse of code, assets, or documentation.
- A screenshot or preview file could be mistaken for live network data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The portal MUST expose one canonical view for each supported WAN dashboard journey. It MUST reuse a view owned by another migration when that view meets the requirement.
- **FR-002**: The portal MUST support each uncovered multi-site gateway, WAN port, traffic, VPN peer-path, and gateway insight view. It MUST NOT duplicate views from issues #4195 and #4200.
- **FR-003**: The dashboard MUST identify the collection time and whether displayed data is current, stale, partial, synthetic, or unavailable.
- **FR-004**: A failed refresh MUST NOT replace a valid snapshot with incomplete or invalid data.
- **FR-005**: The refresh process MUST use bounded pagination, concurrency, and Mist API request admission shared with MistHelper.
- **FR-006**: A Mist API or Redis failure MUST produce an explicit state. The dashboard MUST NOT present stale or synthetic data as live.
- **FR-007**: If MistHelper reuses its Redis service, the design MUST define the feature-owned key namespace and key owner. Before implementation, it MUST also define TTL, serialization, versioning, and outage behavior.
- **FR-008**: The source guide and implementation report different cache TTL values. The implementation MUST verify the worker interval and TTL, record the discrepancy, and select values that meet MistHelper request and freshness limits.
- **FR-009**: The implementation MUST verify each documented source setting against its implementation and tests before it adopts that setting. Documentation alone MUST NOT establish completed behavior.
- **FR-010**: The implementation MUST use working methods in the Mist API SDK. The final method and parameter map MUST match the source implementation and verified SDK contracts. Candidate requests are listed in `contracts/mist-api.md`.
- **FR-011**: The implementation MUST use MistHelper's current API session, organization context, shared rate-limit admission, and configured storage. It MUST NOT create a second API client or token store.
- **FR-012**: The change MUST NOT add another application, Compose group, web service, public port, Redis service, or application database.
- **FR-013**: Offline screenshots and fixtures MUST contain fictional data and MUST remain visibly separate from live telemetry.
- **FR-014**: The project MUST preserve the source provenance and CC BY-NC-SA 4.0 license. It MUST NOT copy or adapt source code, tests, fixtures, screenshots, or assets without explicit rights confirmation.
- **FR-015**: The plan and tasks MUST identify verification files for cache isolation, expiry, decoding, partial refresh, API failures, request limits, secret redaction, and synthetic-data separation.
- **FR-016**: The plan and implementation MUST define shared dashboard ownership across #4195, #4200, and #4220. Reuse the dashboard delivered by merged PR #4252. Treat open draft PR #4208 as proposed behavior only.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- No source request has been confirmed for implementation. Candidate methods and paths appear in `contracts/mist-api.md`.
- The current OpenAPI contract source is `documentation/mist-api-openapi31json.json`, version 2609.1.0, dated 2026-09-07. The final request map remains unverified until it is compared with the source implementation and current SDK signatures. Record any unsupported or undocumented request as an implementation blocker.
- Use the SDK methods named by the verified request map. Do not add direct HTTP requests when a working SDK method exists.
- The feature owns no WebSocket transport. Use a working SDK method whenever one exists. Add no direct HTTP path without verified evidence that the SDK cannot meet the required contract.
- Contract tests MUST prove SDK authentication, endpoint and parameter parity, request admission, API failure safety, cache failure safety, and secret redaction. If an SDK gap is claimed, a test MUST demonstrate the gap before any transport alternative is proposed.
- The merged dashboard's SDK signature tests prove method availability and the shared-session parameter only. They do not prove the source Insights request or response contract.

### Key Entities *(include if feature involves data)*

- **Organization**: MistHelper-authorized organization that contains the sites and gateways in the dashboard.
- **Site**: An organization location that groups gateways and network records.
- **Gateway**: A site device that supplies WAN port and insight records.
- **WAN Port Observation**: A gateway port record with a metric, value, unit, and collection time.
- **Peer Path Observation**: A VPN peer-path record associated with an organization or site and its collection time.
- **Gateway Insight**: A supported gateway health or traffic record with its source metric and collection time.
- **Snapshot**: A bounded set of observations with an owner, source state, schema version, collection time, and expiry.
- **Refresh Result**: A complete, partial, failed, or skipped refresh with a reason and request count.
- **Source Artifact**: Source documentation or software with provenance and license metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can reach each accepted dashboard journey from the existing MistHelper portal without opening a second application.
- **SC-002**: Every displayed record in the test set has an organization, site, gateway or peer identity, collection time, and data-state label.
- **SC-003**: Every documented source journey that passes the ownership review has an acceptance test. No journey rejected as a duplicate has a second page or collector.
- **SC-004**: For each simulated Mist, Redis, pagination, or partial-refresh failure, the operator sees an explicit state and no invalid replacement snapshot.
- **SC-005**: Automated tests complete without production credentials and distinguish every synthetic result from live data.
- **SC-006**: The final change adds zero application services, Compose groups, published ports, Redis services, or application databases.
- **SC-007**: Every reused source artifact has approved provenance and license handling before it enters the product.

## Assumptions

- Target users are MistHelper network operators who already have permission to view the selected organization.
- MistHelper remains the only application entry point and keeps its existing portal, Compose group, API session, and storage configuration.
- The source guide describes a 300-second default worker interval and a cache TTL of three worker intervals. A source implementation review reports a 31-day TTL. Treat this mismatch as unresolved until the source and target cache policies are compared.
- Issue #4195 is closed through merged PR #4252. Its WAN dashboard is existing product behavior, not an unmerged dependency.
- Issue #4200 and draft PR #4208 remain open. Reconcile their proposed scope with the existing dashboard before assigning any unique #4220 behavior.
- No unique #4220 product path, refresh owner, or Redis policy has approval. Existing dashboard cache values do not approve a second cache.
- The source license is CC BY-NC-SA 4.0. Rights confirmation remains absent for copied or adapted code, tests, fixtures, screenshots, and assets.
- Source settings remain unverified unless this specification records source implementation and test evidence. The source review reports a 300-second worker interval, a 600-second stale threshold, incremental refresh, and cached-on-startup behavior.
- The current MistHelper OpenAPI file gives candidate contracts. Source-to-SDK method parity remains an investigation task.
