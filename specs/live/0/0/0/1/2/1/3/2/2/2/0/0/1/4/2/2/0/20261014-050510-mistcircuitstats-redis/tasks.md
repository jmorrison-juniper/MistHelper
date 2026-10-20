---
description: "Implementation tasks for the MistCircuitStats Redis dashboard migration"
---

# Tasks: MistCircuitStats Redis Dashboard Migration

**Input**: Design documents in `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`

**Implementation status**: Cache-only dashboard reads are implemented. Keep refresh collection disabled until T004 and the worker tasks pass.

## Phase 1: Planning Evidence

**Purpose**: Record approved scope and current evidence before implementation.

- [x] T001 [P] Record source owner authorization, CC BY-NC-SA 4.0 license, and attribution requirements in `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/research.md`.
- [x] T002 Map the #4252 dashboard, its four bulk SDK reads, existing Redis cache, and the #4208 proposal in `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/contracts/ownership.md`.
- [x] T003 Record the production bands, 12–35+ request estimate, lab row counts, and SDK startup diagnostic in `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/research.md`.
- [ ] T004 Run an approved production-scale load test across the stated site, gateway, and port bands. Measure all four bulk reads, additional non-WAN port pages, shared token usage, full refresh duration, and failure recovery. Record the evidence and only then select the refresh interval and renewable worker lease duration in `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/contracts/redis-cache.md`.

## Phase 2: Foundational

**Purpose**: Define and test the single worker boundary.

- [ ] T005 [P] Add SDK contract tests for `listOrgSites`, `listOrgDevicesStats`, `searchOrgSwOrGwPorts`, and `getOrgInventory` in `tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py`. Cover pagination, HTTP 4xx and 5xx responses, rate limits, timeouts, malformed responses, and secret redaction.
- [ ] T006 [P] Test Redis lease election across Gunicorn processes, one active refresh, one coalesced follow-up, and disabled behavior with missing or invalid configuration in `tests/unit/wan_dashboard/test_worker.py`.
- [x] T007 Test cache-only routes, stale process-local snapshots during Redis outage, unavailable behavior without a local snapshot, and zero Mist SDK calls in `tests/integration/web_portal/wan_dashboard/test_routes.py`.

## Phase 3: User Story 1 - Review Cached WAN Status (Priority: P1)

**Goal**: Keep the #4252 dashboard canonical and serve its approved data from the shared cache only.

**Independent Test**: Use fictional snapshots for two authorized sites. Verify site filtering and confirm that page reads make zero Mist API requests.

### Tests for User Story 1

- [x] T008 [P] [US1] Add cache-only overview and site-isolation tests in `tests/integration/web_portal/wan_dashboard/test_services.py`.
- [x] T009 [P] [US1] Add browser tests for cache-only dashboard reads and unavailable detail data in `tests/e2e/web_portal/test_wan_dashboard_cache_only.py`.

### Implementation for User Story 1

- [x] T010 [US1] Change dashboard overview and detail reads to use the existing `wan-dashboard:v1:` cache in `src/interfaces/portals/wan_dashboard/services.py`. Return an explicit unavailable state when a required value is absent. Do not add a Mist SDK fallback.
- [x] T011 [US1] Keep dashboard routes cache-only and preserve the canonical #4252 route in `src/interfaces/portals/wan_dashboard/routes.py`.

## Phase 4: User Story 2 - Request a Safe Refresh (Priority: P1)

**Goal**: Let scheduled and operator-requested refreshes use one background worker.

**Independent Test**: Queue multiple requests with mocked SDK responses. Verify one worker performs the four approved bulk reads, writes the existing cache, and preserves the last valid snapshot after a failed page.

### Tests for User Story 2

- [ ] T012 [P] [US2] Test bounded pagination, the 1,000-row page limit, shared request admission, completed-page progress, and complete-snapshot publication in `tests/unit/wan_dashboard/test_worker.py`.
- [ ] T013 [P] [US2] Test that rate limits, Redis failures, failed, repeated, or incomplete pages preserve the last complete snapshot as stale, show a safe error, and publish no partial data in `tests/integration/web_portal/wan_dashboard/test_services.py`.
- [ ] T014 [P] [US2] Test that the Refresh control queues the same worker, coalesces requests into one follow-up, exposes status, and starts no route-level SDK call in `tests/e2e/web_portal/test_wan_dashboard_refresh.py`.

### Implementation for User Story 2

- [ ] T015 [US2] Add one worker that uses only the four approved bulk SDK reads and the shared Mist session in `src/interfaces/portals/wan_dashboard/worker.py`.
- [ ] T016 [US2] Make the worker the sole writer of WAN snapshot values in `src/interfaces/portals/wan_dashboard/worker.py`. Preserve the current cache namespace and TTLs in `src/interfaces/portals/wan_dashboard/services.py`.
- [ ] T017 [US2] Run the worker inside the existing web container and use a renewable Redis lease across Gunicorn processes. Keep one active run and one coalesced follow-up in `src/interfaces/portals/wan_dashboard/worker.py`. Require explicit valid application configuration and keep collection disabled until T004 passes.
- [ ] T018 [US2] Make the Refresh control enqueue worker work and show refresh state, active read phase, completed page counts, timestamps, and safe queue errors in `src/interfaces/portals/wan_dashboard/routes.py`, `src/interfaces/portals/wan_dashboard/templates/wan_dashboard/dashboard.html`, and `src/interfaces/portals/wan_dashboard/static/dashboard.js`.

## Phase 5: User Story 3 - Judge Data Freshness (Priority: P2)

**Goal**: Show the snapshot time and distinguish current, stale, partial, synthetic, and unavailable data.

**Independent Test**: Use fixed synthetic timestamps and simulated Mist or Redis failures. Verify explicit state and safe retention of the last valid snapshot.

### Tests for User Story 3

- [ ] T019 [P] [US3] Test freshness labels, process-local stale fallback during Redis outage, safe errors, and the 86,400-second maximum age in `tests/integration/web_portal/wan_dashboard/test_services.py`.
- [ ] T020 [P] [US3] Test synthetic labels and live-data separation in `tests/e2e/web_portal/test_wan_dashboard_cache_only.py`.

### Implementation for User Story 3

- [ ] T021 [US3] Return refresh state, current bulk-read phase, completed page counts, timestamps, safe error status, and complete snapshot state from the existing cache service in `src/interfaces/portals/wan_dashboard/services.py`.
- [ ] T022 [US3] Render progress, refresh errors, freshness, and unavailable states. Never present synthetic, expired, or stale values as current in `src/interfaces/portals/wan_dashboard/templates/wan_dashboard/dashboard.html` and `src/interfaces/portals/wan_dashboard/static/dashboard.js`.

## Phase 6: User Story 4 - Review Synthetic Examples (Priority: P3)

**Goal**: Keep fictional examples separate from live telemetry.

**Independent Test**: Use synthetic records without Mist credentials or network access. Verify that the portal labels them as synthetic and never uses them for live requests.

### Tests for User Story 4

- [ ] T023 [P] [US4] Test synthetic labels, offline fixtures, and live-route separation in `tests/e2e/web_portal/test_wan_dashboard_cache_only.py`.

### Implementation for User Story 4

- [ ] T024 [US4] Keep synthetic labels visible and prevent synthetic records from entering live cache values in `src/interfaces/portals/wan_dashboard/templates/wan_dashboard/dashboard.html`, `src/interfaces/portals/wan_dashboard/static/dashboard.js`, and `src/interfaces/portals/wan_dashboard/services.py`.

## Phase 7: Polish and Cross-Cutting Concerns

**Purpose**: Check safety, source attribution, and repository constraints.

- [ ] T025 Verify that only the four approved bulk SDK reads run from the worker and that per-site/per-port loops and per-port Insights calls are absent in `tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py`.
- [ ] T026 Verify that log records redact credentials and that synthetic fixtures contain no production data in `tests/unit/wan_dashboard/test_worker.py`.
- [ ] T027 Verify that the worker lease duration and refresh interval use measured T004 results in `src/interfaces/portals/wan_dashboard/worker.py`. Keep collection disabled and both values unset until then.
- [ ] T028 Verify that the implementation adds no application, service, Compose group, port, Redis service, database, or unapproved cache key in `compose.yml` and `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/contracts/redis-cache.md`.
- [ ] T029 Record source attribution and license handling for every reused source artifact in `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/research.md`.
- [ ] T030 Run the applicable tests and local quality gates from `.github/copilot-instructions.md`. Include class structure, inline comments, action logging, and documentation checks. Record exact commands and results in `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/quickstart.md`.

## Dependencies and Execution Order

### Phase Dependencies

- **Planning evidence (Phase 1)**: T001-T003 are complete. T004 is a production-only blocker for selecting the refresh interval and worker lease.
- **Foundational (Phase 2)**: T005-T007 establish the SDK and cache-only contracts.
- **User Story 1 (Phase 3)**: Depends on T005-T007. It preserves the #4252 dashboard while removing route-level Mist calls.
- **User Story 2 (Phase 4)**: Depends on T005-T007 and the cache-only boundary. T004 must pass before the schedule or lease duration is enabled.
- **User Story 3 (Phase 5)**: Depends on the cache-only service and worker state.
- **User Story 4 (Phase 6)**: Depends on the synthetic-data separation contract.
- **Polish (Phase 7)**: Depends on the accepted implementation tasks.

### User Story Dependencies

- **User Story 1 (P1)**: Uses the four bulk SDK reads and existing cache only.
- **User Story 2 (P1)**: Builds the single worker and queue on the User Story 1 cache contract.
- **User Story 3 (P2)**: Uses the snapshot state produced by User Story 2.
- **User Story 4 (P3)**: Uses synthetic records that cannot enter live cache values.
- **Per-port Insights parity**: Not a task in this feature. Issue #4330 tracks that separate scope.

### Parallel Opportunities

- T005 and T006 can run in parallel because they use separate test files.
- T008 and T009 can run in parallel after the shared cache-only contract is agreed.
- T012, T013, and T014 can run in parallel because they test separate files.
- T019 and T020 can run in parallel after the state labels are fixed.
- T023 can run alongside other browser tests after the synthetic-data contract is fixed.
- T004 must finish before a refresh interval or renewable lease duration is selected.

## Parallel Example: User Story 2

```text
Task: T012 Test bulk pagination, shared admission, and complete publication.
Task: T013 Test cache retention after incomplete refresh.
Task: T014 Test that the Refresh control queues the same worker.
```

## Implementation Strategy

### MVP First

1. Keep T001-T003 as recorded planning evidence.
2. Establish the SDK contract and cache-only route tests.
3. Move the four approved bulk reads into one worker and remove Mist calls from dashboard routes.
4. Add the Refresh queue and freshness states.
5. Run T004 before selecting any refresh interval or renewable lease.
6. Keep synthetic examples visibly separate from live cache values.

### Incremental Delivery

1. Keep dashboard reads cache-only. Return unavailable when the cache has no complete snapshot.
2. Add the single worker and route the Refresh control to its queue after T004 establishes safe timing.
3. Measure production-band API use and worker timing before enabling collection.
4. Track per-port Insights parity only in issue #4330.

## Notes

- `[P]` marks tasks that can run in parallel after their dependencies pass.
- `[US1]`, `[US2]`, and `[US3]` map tasks to the user stories in `spec.md`.
- The user authorized source reuse with attribution. Keep the source license terms with any reused material.
- This increment does not implement the worker, queue, status display, or scheduled refresh.
