# Redis Cache Contract: MistCircuitStats Redis Dashboard Migration

**Status**: Reuse the existing #4252 cache. Do not add a second cache policy.

## Existing Cache Baseline

Merged PR #4252 uses `RedisDashboardCache` with the shared Redis client in `src/interfaces/portals/wan_dashboard/services.py`.

| Setting | Existing value | Scope |
|---|---|---|
| `CACHE_PREFIX` | `wan-dashboard:v1:` | Existing dashboard keys |
| `SITE_TTL` | 300 seconds | Site data |
| `ENTITY_TTL` | 600 seconds | Entity data |
| `STALE_TTL` | 86,400 seconds | Last-success data |

Preserve these keys and TTLs. Do not change them in this migration. Do not reserve or create the historical `misthelper:wan:mcsr:v1:` candidate prefix.

## Ownership

- One background worker is the sole Mist API collector and sole writer of WAN snapshot values.
- Run the worker inside the existing web container. Use a renewable Redis lease to elect one active worker across Gunicorn processes.
- Do not collect Mist data or write WAN snapshots when the process does not hold the lease.
- Keep collection disabled unless `WAN_DASHBOARD_REFRESH_ENABLED` is true and `WAN_DASHBOARD_REFRESH_INTERVAL_SECONDS` and `WAN_DASHBOARD_WORKER_LEASE_SECONDS` hold positive application configuration values.
- Missing or invalid timing configuration must prevent worker startup and all Mist requests.
- Scheduled refreshes and operator refresh requests use the same worker.
- Keep one active run and at most one queued follow-up. Coalesce further Refresh requests into that follow-up.
- Dashboard routes read the existing cache only. They do not call Mist when a value is absent or unreadable.
- A route may use only its own complete process-local memory snapshot when Redis is unavailable. Mark it stale and enforce the 86,400-second maximum age.
- Do not add local file storage or another persistent store for snapshots.
- Use the existing shared Redis client. Add no Redis service, database, port, or Compose group.
- Keep request-admission keys and other feature state under their existing owners.
- Do not add a second snapshot namespace.

## Snapshot Rules

- Reuse the existing #4252 snapshot shape and keys.
- Validate organization, site, gateway, and port identity before publication.
- Publish a complete snapshot only after all required bulk pages pass validation.
- On a rate limit, failed page, incomplete dataset, Redis failure, or lease failure, preserve the last complete snapshot, mark it stale, show a safe refresh error, and publish no partial data.
- If no unexpired complete snapshot is available, report unavailable data.
- After 86,400 seconds, stop showing the snapshot, including from process-local memory.
- Display refresh state, the current bulk-read phase, completed page counts, timestamps, and a safe error status.
- Store no credentials, authorization headers, raw request objects, or secrets.
- Reject malformed or unknown-version values. Report unavailable data rather than using a silent default.

## Refresh Interval and Lease

The Redis lease mechanism is approved. Do not select its duration or set a refresh interval in this plan. The production-scale load test must measure:

- All page requests for 1,001–5,000 sites, 1,001–5,000 gateways, and 5,001–20,000 WAN ports.
- Additional non-WAN port pages.
- Total shared token usage against the current 5,000-calls-per-hour limit.
- Full refresh duration, overlapping queue requests, and recovery after worker failure.

Select the refresh interval only after the test records shared request headroom and freshness needs. Derive the renewable lease from measured refresh duration and failure recovery. Do not guess either value.

The 12–35+ request estimate applies to four bulk reads at page size 1,000 before extra non-WAN port pages. It is not a measured result.

## Outage Behavior

| Condition | Required result |
|---|---|
| Redis read fails | Report unavailable data. Do not make a fallback Mist request from a route. |
| Redis read fails, local complete snapshot exists | Show that process-local snapshot as stale while it is no more than 86,400 seconds old. Do not make a fallback Mist request. |
| Redis read fails, no local complete snapshot exists | Report unavailable data. Do not make a Mist request. |
| Redis write fails | Keep the last complete snapshot, mark it stale, and report refresh failure. |
| Value is malformed | Reject it and report unavailable data. |
| Mist page is rate limited, fails, or returns incomplete data | Preserve the last complete snapshot, mark it stale, show a safe refresh error, and publish no partial data. |
| Worker lease cannot be acquired or renewed | Stop collection and publication. Report a safe refresh error. |
| Another refresh is active | Keep one active run and one queued follow-up. Coalesce all further requests into that follow-up. |
| Snapshot exceeds 86,400 seconds | Report unavailable data. Do not label synthetic data as live. |
| Redis queue operation fails | Reject the request and show a safe queue error. Do not call Mist from the route. |

## Required Tests

- Prove that the worker is the only writer of WAN snapshot values.
- Prove that portal routes make no Mist request on cache failure.
- Prove that existing keys and 300-, 600-, and 86,400-second TTLs remain unchanged.
- Prove that rate limits, failed pages, and incomplete datasets preserve the last complete snapshot as stale and publish no partial data.
- Prove that only one leased worker runs across Gunicorn processes.
- Prove that multiple Refresh requests during one run produce one queued follow-up.
- Prove that Redis outage uses only an unexpired process-local snapshot and makes no Mist request.
- Prove that the page reports refresh state, read phase, page counts, timestamps, and safe errors.
- Prove that snapshots older than 86,400 seconds are unavailable, including in process memory.
- Prove that credentials do not enter cache values, keys, or logs.
- Record the lease duration and refresh interval only after the production-scale load test.
