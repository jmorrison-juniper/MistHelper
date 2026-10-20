# WAN Feature Ownership: MistCircuitStats Redis Dashboard

**Status**: User-approved planning boundary, reviewed 2026-10-20. This PR changes no product files.

## Canonical Owner

Merged PR #4252 owns the MistCircuitStats WAN dashboard at `/wan-dashboard`, its shared Mist SDK collection, and its existing Redis cache. Issue #4195 is closed. Keep #4252 as the target.

Draft PR #4208 and issue #4200 remain proposals. Do not edit #4208 files or treat its implementation as merged behavior.

## Approved #4220 Scope

| Capability | Owner and contract |
|---|---|
| WAN dashboard | Keep the #4252 dashboard as the only dashboard. |
| Bulk collection | Use only the four #4252 paginated SDK reads: `listOrgSites`, `listOrgDevicesStats`, `searchOrgSwOrGwPorts`, and `getOrgInventory`. |
| Background refresh | Run one worker in the existing web container. Use a renewable Redis lease to elect one active Gunicorn process. |
| Dashboard reads | Read the existing Redis cache only. On Redis outage, use an unexpired complete process-local snapshot as stale when available. Otherwise report unavailable data. Never make Mist calls from a route. |
| Refresh control | Queue the same worker. Keep one active run and one queued follow-up. Coalesce further requests. |
| Refresh status | Show state, active bulk-read phase, completed page counts, timestamps, and safe error status. |
| Failed refresh | Preserve the last complete snapshot as stale, show a safe error, and publish no partial data. |
| Redis | Reuse `wan-dashboard:v1:` and preserve the 300-second site, 600-second entity, and 86,400-second stale TTLs. |
| Stale limit | After 86,400 seconds, report unavailable data, including when the snapshot remains in process memory. |
| Request admission | Use the #4252 shared `mistapi` session and request-admission path. |
| Per-port Insights parity | Excluded from #4220. Tracked by issue #4330. |
| Source reuse | The source owner authorized reuse with documented attribution. Preserve the CC BY-NC-SA 4.0 license. |

## Existing Data Boundary

The #4252 overview uses the four bulk reads in the table. Its current detail service also calls per-device and per-port SDK methods. The #4220 worker does not add or retain route-level calls for those details.

The dashboard reports unavailable when the four approved bulk results do not contain the requested detail. It does not call Mist as a fallback. Do not port the source per-site or per-port request loops. Do not add per-port Insights calls.

A process-local snapshot fallback contains only a complete snapshot from an earlier successful read. It adds no file or persistent store.

## Proposed Product Paths

These paths are for future implementation only. This planning PR changes none of them.

| Purpose | Proposed path |
|---|---|
| Single worker and refresh queue | `src/interfaces/portals/wan_dashboard/worker.py` |
| Existing cache and service boundary | `src/interfaces/portals/wan_dashboard/services.py` |
| Cache-only route and refresh queue endpoint | `src/interfaces/portals/wan_dashboard/routes.py` |
| Refresh control | `src/interfaces/portals/wan_dashboard/templates/wan_dashboard/dashboard.html` and `src/interfaces/portals/wan_dashboard/static/dashboard.js` |
| Worker unit tests | `tests/unit/wan_dashboard/test_worker.py` |
| Portal integration tests | `tests/integration/web_portal/wan_dashboard/` |
| Browser tests | `tests/e2e/web_portal/` |

## Production Gate

The user supplied production bands of 1,001–5,000 sites, 1,001–5,000 gateways, and 5,001–20,000 WAN ports. The rough estimate is 12–35+ requests per full refresh for four bulk reads with page size 1,000, before additional non-WAN port pages. This is not a measured result.

Current Mist documentation states 5,000 API calls per hour per token. Keep shared admission. The Redis lease mechanism is approved, but do not set its duration or the refresh interval until production-scale load testing measures total token use, complete refresh time, and failure recovery.

## Implementation Gate

1. Keep the #4252 dashboard as the only dashboard and use its existing cache.
2. Use one worker inside the existing web container. Elect one active Gunicorn process with a renewable Redis lease.
3. Keep one active refresh and at most one queued follow-up. Coalesce further requests.
4. Use only the four approved bulk SDK reads.
5. Keep dashboard routes cache-only. On Redis outage, show an unexpired process-local complete snapshot as stale when available, or report unavailable data.
6. Preserve the current Redis namespace and TTLs. Enforce 86,400 seconds as the maximum snapshot age.
7. Preserve the last complete snapshot on every refresh failure. Show safe errors and publish no partial data.
8. Display refresh state, current read phase, completed page counts, timestamps, and safe error status.
9. Complete production-scale load testing before selecting the refresh interval or renewable worker lease duration.
10. Keep per-port Insights parity in issue #4330.
11. Preserve source provenance and CC BY-NC-SA 4.0 attribution for any reused artifact.
