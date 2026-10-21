# Feature Specification: MistCircuitStats Redis Dashboard Migration

**Feature Branch**: `jmorrison-juniper-4220-mistcircuitstats-redis-planning`

**Created**: 2026-10-14

**Reviewed**: 2026-10-20

**Status**: Partly delivered. PRs #4332 and #4337 delivered cache-only reads and the fail-closed worker. The current increment covers synthetic fixtures and offline browser states. T004 remains deferred until a scheduled maintenance window. Keep the refresh interval and worker lease unset.

**Input**: Migrate the read-only MistCircuitStats-Redis dashboard into MistHelper. Preserve its useful workflows without adding another application, database, or duplicate WAN views.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review Cached WAN Status (Priority: P1)

An operator opens the canonical MistHelper WAN dashboard and reviews authorized site and gateway data from its shared cache.

**Why this priority**: One dashboard avoids duplicate pages, collectors, and Mist API requests.

**Independent Test**: Use fictional snapshots for two sites. Verify that site filtering isolates each site and that page reads make no Mist API calls.

**Acceptance Scenarios**:

1. **Given** a valid cached snapshot, **When** an operator opens the dashboard, **Then** the page shows only data for the authorized organization.
2. **Given** snapshots for two sites, **When** an operator selects one site, **Then** the page shows no records from the other site.
3. **Given** data that the snapshot does not contain, **When** an operator opens a detail view, **Then** the page reports that data as unavailable and makes no Mist API request.

### User Story 2 - Request a Safe Refresh (Priority: P1)

An operator requests a refresh. One background worker performs the approved bulk reads and writes the shared cache.

**Why this priority**: A single worker prevents page views and refresh controls from creating duplicate API calls or cache writers.

**Independent Test**: Queue two refresh requests with mocked SDK responses. Verify that the same worker owns collection and cache writes, and that routes make no Mist API calls.

**Acceptance Scenarios**:

1. **Given** an operator selects Refresh, **When** the request is accepted, **Then** it queues work for the existing worker and returns without collecting Mist data in the route.
2. **Given** a refresh is running, **When** operators request more refreshes, **Then** one active run continues and at most one follow-up run waits in the queue.
3. **Given** all approved bulk pages are valid, **When** the worker completes, **Then** it publishes the complete snapshot to the existing cache.
4. **Given** a refresh hits a rate limit, fails, or receives incomplete data, **When** the worker ends, **Then** it keeps the last complete snapshot, marks it stale, shows a safe refresh error, and publishes no partial data.

### User Story 3 - Judge Data Freshness (Priority: P2)

An operator checks the collection time and state of cached data.

**Why this priority**: Clear status prevents operators from treating old or missing values as live.

**Independent Test**: Use fictional snapshots with fixed times and simulated Mist or Redis failures. Verify explicit state labels and safe stale-data behavior.

**Acceptance Scenarios**:

1. **Given** a successful refresh, **When** an operator views its data, **Then** the page shows its collection time and state.
2. **Given** a refresh fails, **When** a previous complete snapshot exists, **Then** the page identifies that snapshot as stale and shows a safe refresh error.
3. **Given** Redis is unavailable, **When** an operator opens the dashboard, **Then** the page shows a complete process-local snapshot as stale when one is available, or reports unavailable data, and makes no Mist API request.
4. **Given** refresh work is queued or running, **When** an operator views the dashboard, **Then** the page shows the refresh state, current bulk-read phase, completed page counts, timestamps, and a safe error status.
5. **Given** a complete snapshot is more than 24 hours old, **When** an operator opens the dashboard, **Then** the page reports unavailable data and does not show the expired snapshot.
6. **Given** a refresh fails and no complete snapshot exists, **When** an operator opens the dashboard, **Then** the page reports unavailable data and shows a safe refresh error.

### User Story 4 - Review Synthetic Examples (Priority: P3)

An operator or reviewer uses fictional examples without Mist credentials or live requests.

**Why this priority**: Synthetic data supports safe review and automated tests.

**Independent Test**: Use only fictional data. Verify that the offline example remains labeled synthetic and cannot satisfy a live request.

**Acceptance Scenarios**:

1. **Given** the offline example, **When** an operator opens it, **Then** the page identifies every record as synthetic.
2. **Given** a live request without Mist access, **When** the request fails, **Then** the page does not substitute synthetic records.
3. **Given** live data is current, stale, unavailable, or in an error state, **When** the page shows the offline example, **Then** no synthetic record appears in a live overview or live detail view.
4. **Given** automated tests use synthetic responses, **When** live dashboard routes serve their result, **Then** the synthetic response cannot satisfy the live request.

### Edge Cases

- A site, gateway, WAN port, or peer record is absent or has an invalid identifier.
- A bulk page is empty, incomplete, repeated, or interrupted by an API limit.
- A refresh stops before it validates all required pages.
- Redis is unavailable, a value cannot be decoded, or a key belongs to another feature.
- A snapshot expires while Mist is unavailable.
- Two refresh requests arrive for the same organization at once.
- Redis becomes unavailable while a complete snapshot is held in a web process.
- A process has no local complete snapshot when Redis becomes unavailable.
- More than one refresh request arrives while one refresh is running.
- The Redis worker lease cannot be acquired or renewed.
- A snapshot passes the stale TTL while it remains in process memory.
- A production load test does not establish safe refresh and lease values.
- A diagnostic appears during SDK startup even when a lab endpoint returns data.
- A source setting differs from its operations guide.
- A related proposal changes dashboard ownership or collection scope.
- A source artifact lacks attribution or violates its license terms.
- Synthetic data could be mistaken for live network data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The portal MUST keep the dashboard delivered by merged PR #4252 as the only WAN dashboard. It MUST add no duplicate view or collector.
- **FR-002**: The worker MUST use only the four existing bulk, paginated SDK reads from PR #4252: `listOrgSites`, `listOrgDevicesStats`, `searchOrgSwOrGwPorts`, and `getOrgInventory`.
- **FR-003**: This migration MUST exclude source-specific per-port Insights parity. Track that scope in issue #4330. Do not add direct HTTP or per-site/per-port request loops.
- **FR-004**: One background worker MUST be the sole Mist API collector and the sole writer of WAN snapshot data.
- **FR-005**: Dashboard routes MUST read from the existing Redis cache only. They MUST NOT make Mist API calls when a cache value is absent or invalid.
- **FR-006**: The Refresh control MUST queue work for the same background worker. It MUST NOT collect data or write snapshots in the route.
- **FR-007**: Collection MUST use the existing MistHelper `mistapi` session, organization context, shared request admission, and configured Redis client.
- **FR-008**: Preserve the existing cache TTLs: 300 seconds for site data, 600 seconds for entity data, and 86,400 seconds for stale data. Do not change them in this migration.
- **FR-009**: Keep the refresh interval unapproved until a production-scale load test measures the shared API request rate across the stated site, gateway, and port bands.
- **FR-010**: Derive the renewable worker lease from measured refresh duration and failure recovery after the production-scale load test. Do not guess a lease duration.
- **FR-011**: Treat 5,000 API calls per hour per token as the current documented Mist limit. Keep the worker inside shared request admission and the measured budget.
- **FR-012**: Treat the 12–35+ request estimate per full refresh as unmeasured. Include additional non-WAN port pages in the load test.
- **FR-013**: A rate-limited, failed, or incomplete refresh MUST preserve the last complete snapshot, mark it stale, show a safe refresh error, and publish no partial data.
- **FR-014**: The dashboard MUST distinguish current, stale, synthetic, and unavailable data. It MUST NOT expose a partial snapshot.
- **FR-015**: A static, fictional example MUST remain visibly separate from live data in current, stale, unavailable, and error states. It MUST NOT enter the live cache or satisfy a live request.
- **FR-016**: Preserve MistCircuitStats-Redis provenance and its CC BY-NC-SA 4.0 license. The repository owner has authorized reuse with documented attribution.
- **FR-017**: Add no application, service, Compose group, public port, Redis service, or application database.
- **FR-018**: Record lab evidence and its limits. A lab query returned 67 port rows, 7 WAN rows, and 2 gateway MACs. This is not production evidence.
- **FR-019**: Record the SDK startup token-validation diagnostic that occurred despite a successful lab endpoint response. Do not include credentials or identifiers.
- **FR-020**: Treat PR #4208 as a proposal only. Do not edit its files or rely on its unmerged behavior.
- **FR-021**: Run the worker inside the existing web container. Use a renewable Redis lease to elect one active worker across Gunicorn processes. A process without the lease MUST NOT collect Mist data or write WAN snapshots.
- **FR-022**: While one refresh is running, keep at most one queued follow-up. Coalesce additional refresh requests into that follow-up.
- **FR-023**: Show refresh state, current bulk-read phase, completed page counts, timestamps, and a safe error status.
- **FR-024**: When Redis is unavailable, show a complete process-local snapshot as stale if the serving process has one. Otherwise report unavailable data. Dashboard requests MUST NOT call Mist.
- **FR-025**: Treat 86,400 seconds as the maximum snapshot age. After that limit, report unavailable data, including when a process-local snapshot remains in memory.
- **FR-026**: Treat a failed lease acquisition, lease renewal, or Redis queue operation as a refresh failure. Do not start another collector or publish data without the lease.
- **FR-027**: Keep collection disabled unless `WAN_DASHBOARD_LOAD_TEST_APPROVED` and `WAN_DASHBOARD_REFRESH_ENABLED` are true, and `WAN_DASHBOARD_REFRESH_INTERVAL_SECONDS` and `WAN_DASHBOARD_WORKER_LEASE_SECONDS` are positive application configuration values. Missing or invalid values MUST fail closed. Do not set these values before T004 passes during a scheduled maintenance window.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- Use only the four existing bulk SDK operations listed in FR-002.
- Use the shared `mistapi` session and shared request admission. Do not add direct HTTP.
- Use a page limit of 1,000. Record each admitted SDK request in the shared rate-limit system.
- Contract tests MUST cover pagination, duplicate records, partial pages, 4xx and 5xx responses, rate limits, timeouts, and secret redaction.
- Per-port Insights parity is outside this migration. Issue #4330 tracks its separate contract review.

### Key Entities *(include if feature involves data)*

- **Organization**: MistHelper-authorized organization that contains the sites and gateways in the dashboard.
- **Site**: An organization location that groups gateways and network records.
- **Gateway**: A site device that supplies WAN port and insight records.
- **WAN Port Observation**: A gateway port record returned by the existing bulk port read, with its source values and collection time.
- **Gateway Record**: A gateway record returned by the existing bulk gateway and inventory reads.
- **Snapshot**: A validated set of existing bulk-read results held under the current dashboard cache contract.
- **Refresh Request**: An operator request queued for the one background worker.
- **Refresh Result**: A complete, partial, failed, or skipped refresh with a safe reason and admitted request count.
- **Source Artifact**: Source documentation or software with provenance and license metadata.

Source-specific per-port Insights observations are not entities in this migration. Issue #4330 owns that future scope.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Dashboard page reads make zero Mist API requests.
- **SC-002**: One worker owns all approved collection and WAN snapshot writes for the dashboard.
- **SC-003**: During the production-scale load test, the measured request total stays within the shared 5,000-calls-per-hour-per-token limit.
- **SC-004**: The cache retains its existing 300-second site, 600-second entity, and 86,400-second stale TTLs.
- **SC-005**: Every simulated rate limit, collection failure, incomplete page, or cache failure preserves the last complete snapshot as stale with a safe error, or reports unavailable data. No partial snapshot is published.
- **SC-006**: Automated tests use no production credentials and label every synthetic result.
- **SC-007**: The change adds zero applications, services, Compose groups, published ports, Redis services, or application databases.
- **SC-008**: Every reused source artifact carries documented provenance and CC BY-NC-SA 4.0 attribution.
- **SC-009**: Concurrent refresh requests produce no more than one active run and one queued follow-up across Gunicorn processes.
- **SC-010**: Dashboard status exposes the refresh state, active read phase, completed page counts, timestamps, and safe error status.
- **SC-011**: Redis outage behavior makes no Mist request and shows only an unexpired complete process-local snapshot when one is available.
- **SC-012**: Without explicit load-test approval, refresh enablement, and valid timing values, the worker makes zero Mist API requests and reports a safe disabled state.
- **SC-013**: Offline browser tests cover stale, unavailable, and refresh-error states with fictional data and make zero Mist API requests.

## Assumptions

- Target users are MistHelper network operators who already have permission to view the selected organization.
- MistHelper remains the only application entry point and keeps its existing portal, Compose group, API session, and storage configuration.
- PR #4252 is the canonical dashboard, shared SDK collection, and Redis cache. Issue #4195 is closed.
- Draft PR #4208 remains a proposal. Do not edit its files.
- The production bands are 1,001–5,000 sites, 1,001–5,000 gateways, and 5,001–20,000 WAN ports.
- The rough 12–35+ calls per full refresh is an estimate for four bulk reads at a page size of 1,000. It is not a measured production result and excludes additional non-WAN port pages.
- A read-only lab query returned 67 port rows, 7 WAN rows, and 2 gateway MACs. The lab result is not production evidence.
- The SDK logged a token-validation error during startup despite a successful endpoint response. Resolve or explain this diagnostic before treating the lab as authentication evidence.
- The MistCircuitStats-Redis owner authorized reuse with documented attribution. Preserve the source provenance and CC BY-NC-SA 4.0 constraints.
- Issue #4330 tracks source-specific per-port Insights parity outside this migration. Do not add its request path here.
- The refresh interval and renewable worker lease remain unapproved until T004 runs during a scheduled maintenance window.
- A process-local memory snapshot is the only Redis-outage fallback in this plan. The serving Gunicorn process uses it only when it holds a complete snapshot from an earlier successful read. No local file or new persistent store is added.
- The offline example is fixed fictional presentation content. It is not an API response, cache value, or fallback for live data.
