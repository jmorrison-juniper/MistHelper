# Implementation Plan: MistCircuitStats Redis Dashboard Migration

**Branch**: `jmorrison-juniper-4220-mistcircuitstats-redis-planning` | **Date**: 2026-10-20 | **Spec**: [spec.md](spec.md)

**Input**: Existing managed feature record for issue #4220.

**Status**: The first worker increment is implemented. Collection remains disabled until production-scale load testing approves its timing and load-test gate.

## Summary

Keep the dashboard from merged PR #4252 as the canonical MistCircuitStats WAN dashboard. Make its dashboard routes cache-only. Run one background worker inside the existing web container. Use a renewable Redis lease to elect one active worker across Gunicorn processes. The Refresh control queues work for that same worker.

The worker reuses only #4252's four bulk, paginated SDK reads: `listOrgSites`, `listOrgDevicesStats`, `searchOrgSwOrGwPorts`, and `getOrgInventory`. It uses the existing `mistapi` session, shared request admission, Redis client, namespace, and TTLs. It does not add per-site or per-port request loops. Source-specific per-port Insights parity is outside this migration and is tracked by issue #4330.

Keep collection disabled unless `WAN_DASHBOARD_LOAD_TEST_APPROVED` and `WAN_DASHBOARD_REFRESH_ENABLED` are true, and both timing values are positive. Missing or invalid configuration fails closed. Do not set these values before the production load test. Allow one active refresh and at most one queued follow-up. Coalesce additional Refresh requests into that follow-up. If a rate limit, API failure, incomplete page, Redis failure, or lease failure stops a refresh, keep the last complete snapshot, mark it stale, show a safe refresh error, and publish no partial data. Dashboard status shows the refresh state, current bulk-read phase, completed page counts, timestamps, and safe error status.

When Redis is unavailable, a serving Gunicorn process may use only its own complete in-memory snapshot from an earlier successful read. Mark that snapshot stale. If the process has no complete snapshot, report unavailable data. This process-local fallback adds no file or persistent store, makes no Mist request, and cannot extend the 86,400-second maximum snapshot age.

The user's production bands are 1,001–5,000 sites, 1,001–5,000 gateways, and 5,001–20,000 WAN ports. A rough estimate for four bulk reads at page size 1,000 is 12–35+ requests per full refresh, before additional non-WAN port pages. This estimate is not measured production evidence. The current documented Mist limit is 5,000 calls per hour per token. Keep the refresh interval unapproved until a production-scale load test measures total shared usage. Derive the renewable worker lease from that test.

The source owner authorized reuse with documented attribution. Record MistCircuitStats-Redis provenance and its CC BY-NC-SA 4.0 license. This PR copies no source code or assets.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing `mistapi` SDK, Flask portal, shared Redis client, and existing dashboard services. Add no dependency.

**Storage**: Reuse the `wan-dashboard:v1:` cache from #4252. Preserve the 300-second site TTL, 600-second entity TTL, and 86,400-second stale TTL. Add no cache namespace or database.

**Testing**: Use pytest, the existing portal test client, and Playwright. Use mocked Mist responses and fictional records. Do not use production credentials.

**Target Platform**: Existing MistHelper web portal and Compose group on Windows, macOS, and Linux.

**Project Type**: Existing Python web portal. Add no application or service.

**Performance Goals**: Stay within shared Mist request admission and the documented 5,000-calls-per-hour-per-token limit. Measure actual production-band request counts before selecting the refresh interval or worker lease.

**Constraints**: Use only the four existing bulk SDK reads. Keep routes cache-only. One worker inside the existing web container owns collection and WAN snapshot writes through a renewable Redis lease across Gunicorn processes. Keep #4208 as an unmerged proposal and do not edit its files. Do not add direct HTTP, per-site/per-port loops, a second Redis service, local persistent snapshot storage, or a second database.

**Scale/Scope**: Test 1,001–5,000 sites, 1,001–5,000 gateways, and 5,001–20,000 WAN ports. Include additional non-WAN port pages. Treat the 12–35+ request estimate as unmeasured.

## Constitution Check

### Before Research

- **Managed record**: Update the existing grouped `specs/live/` record. Do not create another feature directory or change `.specify/feature.json`.
- **Implementation boundary**: Change only the existing #4252 dashboard package and its tests. Keep the refresh schedule disabled and the worker lease duration unset until production-scale testing.
- **Portal owner**: Reuse the canonical dashboard delivered by #4252. Do not edit #4208 files.
- **API access**: Use the existing `mistapi` session and shared request admission. Do not add direct HTTP or another token store.
- **Collection owner**: One background worker performs the four approved bulk reads and writes WAN snapshots. Routes make no Mist API calls.
- **Worker election**: Run the worker in the existing web container. Use a renewable Redis lease to elect one collector across Gunicorn processes.
- **Fail-closed configuration**: Keep collection disabled unless `WAN_DASHBOARD_LOAD_TEST_APPROVED` and `WAN_DASHBOARD_REFRESH_ENABLED` are true and both timing keys hold positive application configuration values. Missing or invalid values prevent worker startup and Mist requests.
- **Refresh coalescing**: Keep one active refresh and at most one queued follow-up. Coalesce additional operator requests into the queued follow-up.
- **Failure safety**: A rate limit, failed read, incomplete dataset, Redis error, or lost lease keeps the last complete snapshot, marks it stale, shows a safe error, and publishes no partial data.
- **Refresh status**: Show refresh state, active bulk-read phase, completed page counts, timestamps, and a safe error status.
- **Redis outage**: Use a complete process-local memory snapshot as stale only when the serving process has one. Otherwise show unavailable data. Make no Mist request.
- **Refresh action**: The Refresh control queues the same worker. It does not collect data or write snapshots.
- **Cache safety**: Reuse `wan-dashboard:v1:` and preserve its current TTLs. Treat 86,400 seconds as the maximum age, including for process-local memory. Do not add a second namespace or writer.
- **Load safety**: Keep refresh interval and lease unapproved until production-scale load testing confirms the shared request budget.
- **Source rights**: The source owner authorized reuse with attribution. Preserve the CC BY-NC-SA 4.0 license and provenance.
- **Testing**: Use mocked Mist responses and fictional data. Test pagination, shared admission, cache-only reads, worker serialization, partial failure, and secret redaction.

**Gate result**: The cache-only route and fail-closed worker increments pass focused tests. Production-scale load testing remains a prerequisite for enabling collection and selecting interval and lease values. Synthetic-data labeling remains open.

### After Design

- The #4252 dashboard remains the only WAN dashboard.
- Only the four existing bulk and paginated SDK reads feed the scheduled snapshot.
- A Refresh request enters the same worker queue as a scheduled refresh.
- Redis lease election allows only one Gunicorn process to collect or write snapshots.
- Additional Refresh requests during a run coalesce into one queued follow-up.
- Dashboard routes read the existing cache only.
- A rate-limited, failed, or incomplete refresh preserves the last complete snapshot as stale, reports a safe error, and publishes no partial data.
- Redis outage may use an unexpired process-local complete snapshot as stale. Without one, the page reports unavailable data and makes no Mist request.
- Status includes refresh state, the active read phase, completed page counts, timestamps, and safe error information.
- Preserve the existing site, entity, and stale-data TTLs. Do not show data after the 86,400-second maximum age.
- Do not select a refresh interval or renewable lease before the production-scale load test.
- Per-port Insights parity remains in issue #4330.
- Keep the lab query and SDK startup diagnostic as limited evidence, not production proof.

## Phase 0: Research

See [research.md](research.md). It records the user-approved scope, source provenance, API request budget, production bands, estimate limits, and lab caveat.

## Phase 1: Design and Contracts

See [data-model.md](data-model.md), [contracts/mist-api.md](contracts/mist-api.md), [contracts/redis-cache.md](contracts/redis-cache.md), [contracts/ownership.md](contracts/ownership.md), and [quickstart.md](quickstart.md).

### Design Decisions

1. **Canonical dashboard**: Keep the dashboard and shared SDK collection from #4252. Do not add a competing route or collector.
2. **Four bulk reads**: Use only the four existing paginated reads named in the Summary. Use a page size of 1,000 and shared request admission.
3. **One leased worker**: Run the worker inside the existing web container. A renewable Redis lease elects one Gunicorn process as the sole collector and snapshot writer. Run no collection without the lease.
4. **Refresh coalescing**: Keep one active run and at most one queued follow-up. Coalesce further operator requests into the follow-up.
5. **Cache-only portal**: Dashboard routes read the shared cache or an unexpired process-local complete snapshot marked stale. They make no Mist request. Report unavailable data when neither snapshot is available.
6. **Failure and progress state**: Never publish partial data. On a rate limit, failed page, incomplete dataset, Redis failure, or lease failure, retain the last complete snapshot as stale and show a safe error. Show refresh state, current read phase, completed page counts, and timestamps.
7. **Existing cache policy**: Preserve `wan-dashboard:v1:` and the 300-, 600-, and 86,400-second TTLs. The stale TTL is the maximum snapshot age, including for process-local memory. Add no new namespace or persistent local store.
8. **Fail-closed configuration**: Keep collection disabled unless `WAN_DASHBOARD_LOAD_TEST_APPROVED` and `WAN_DASHBOARD_REFRESH_ENABLED` are true and both timing keys hold positive application configuration values.
9. **Unapproved timing**: The lease mechanism is approved, but its duration and the refresh interval remain unset until the production-scale load test measures full refresh time, shared request usage, and failure recovery.
10. **Insights boundary**: Exclude source-specific per-port Insights parity. Issue #4330 owns that future contract review.
11. **Source attribution**: Record the source repository, pinned evidence revision, owner authorization, and CC BY-NC-SA 4.0 license. Copy no source artifacts in this PR.

## Product Paths

These paths define the approved implementation boundary. Reuse the existing #4252 package and do not create a competing portal.

```text
src/interfaces/portals/wan_dashboard/
├── routes.py
├── services/
│   ├── __init__.py
│   └── worker.py
├── static/dashboard.js
└── templates/wan_dashboard/dashboard.html

tests/unit/wan_dashboard/test_worker.py
tests/integration/web_portal/wan_dashboard/
tests/e2e/web_portal/
```

`services/worker.py` runs inside the existing web container. A renewable Redis lease elects one Gunicorn process to own the worker and shared refresh queue. `routes.py` and the dashboard page read snapshots and queue refresh requests. Preserve the existing Redis cache and the #4252 SDK operations. Tests use mocked Mist responses and synthetic records.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Cache-only dashboard increment | Routes stop collecting Mist data and serve only complete cached snapshots. The Refresh control stays disabled until production load approval and valid timing configuration exist. | Keeping route-level collection would violate the single-worker design. No second dashboard, cache, service, or database is required. |
