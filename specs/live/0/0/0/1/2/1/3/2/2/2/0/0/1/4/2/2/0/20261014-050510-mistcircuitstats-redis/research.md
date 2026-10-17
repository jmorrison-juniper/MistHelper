# Research: MistCircuitStats Redis Dashboard Migration

**Date**: 2026-10-14
**Status**: Planning evidence. Source implementation and license compatibility remain unverified.

## Decision 1: Treat the source behavior as documented, not proven

**Decision**: Use the source README, operations guide, and implementation review as evidence with separate confidence. Record conflicts instead of choosing the guide or code value without review.

**Rationale**: The source guide describes a 300-second worker interval and a cache TTL of three intervals. The implementation review reports a 300-second interval and a 31-day TTL. The guide and implementation therefore disagree on cache expiry.

## Verified Source Implementation Facts

The source `worker.py` implementation review reports these values and behaviors:

| Item | Guide | Implementation review | Target decision |
|---|---|---|---|
| `WORKER_INTERVAL` | 300 seconds by default | 300 seconds by default | Verify the target refresh interval against shared API admission. |
| `PARALLEL_WORKERS` | Default 5 | Default 4 | Do not copy either value without a bounded-concurrency review. |
| Cache TTL | Three worker intervals, or 900 seconds at the default interval | 31 days | Do not adopt either value until freshness and outage needs set a target TTL. |
| `STALE_THRESHOLD` | Documented source setting | 600 seconds | Treat as a source value, not a MistHelper policy. |
| Incremental refresh | Documented source behavior | Implemented | Verify record replacement and partial-failure semantics before reuse. |
| Cached on startup | Documented source behavior | Implemented | Verify which cache states the application accepts at startup. |

The source insight path uses direct `requests.get` calls, extracts token headers manually, and requests `rx_bps` and `tx_bps` by `port_id` with `interval=3600` over a seven-day window. Do not port this transport. The Mist SDK request and response contract remains unproven, and the insight response mismatch blocks implementation.

The review does not establish the implementation status of `SKIP_ENRICHMENT`, token rotation, API host settings, organization settings, or every pagination and enrichment path. Keep those items open in T001.

**Alternatives considered**:

- Treat each documented setting as working behavior. Rejected because the issue explicitly requires implementation verification.
- Drop source behavior from scope. Rejected because it would remove the reason for the migration.

**Bounded investigation**: Before implementation, compare each source setting and worker path with its source code, tests, and operations guide. Record whether it is implemented, tested, incomplete, or a TODO.

## Decision 2: Use one owner for overlapping WAN views

**Decision**: Use one canonical portal view and one collection owner for each gateway, port, peer, and insight data set. Reuse a landed #4195 or #4200 feature when it satisfies the requirement. Add only verified gaps.

**Rationale**: Issue #4195 covers MistCircuitStats WAN views. Issue #4200 and open PR #4208 cover WAN overview, gateway, port, peer, offline preview, live collection, request admission, and history. PR #4208 targets `main` but remains open. Neither issue or PR is assumed to be merged.

**Alternatives considered**:

- Build another complete WAN dashboard and collector. Rejected because it duplicates pages and Mist API requests.
- Assume PR #4208 will merge unchanged. Rejected because its implementation is not on `main` and its acceptance may change.

**Bounded investigation**: At implementation start, compare the source workflows with the accepted and landed scope of #4195 and #4200. Write one ownership table for each view and each Mist API data set. Stop if two owners remain.

## Decision 3: Reuse the existing Redis service only for transient state

**Decision**: Add no Redis service. If the overlap review proves a separate cache is needed, use the existing Redis service and a versioned `misthelper:wan:mcsr:v1:` key namespace. Set cache expiry from the approved refresh interval and record the exact value in implementation documentation.

**Rationale**: MistHelper already has Redis in its Compose group. The source guide and implementation review report different TTLs, so neither value sets the target cache policy. A second service or database would violate issue #4220.

**Alternatives considered**:

- Add a source-specific Redis container. Rejected because MistHelper must keep one Compose group and Redis service.
- Store snapshots in a second database. Rejected because the feature must use existing application storage.
- Reuse keys without a feature namespace. Rejected because another writer could overwrite values or apply a different TTL.

**Bounded investigation**: Before implementation, verify Redis module support, existing retention behavior, payload limits, namespace conventions, and which component owns refresh locks. Confirm that snapshot cache data is not treated as durable history.

## Decision 4: Keep portal reads separate from live collection

**Decision**: Portal reads use an accepted cache or existing stored snapshot. They do not make fallback Mist calls when a cache read fails. A worker or explicit operator action may refresh data only through shared MistHelper request admission.

**Rationale**: This prevents page views from multiplying API calls and avoids hidden requests that bypass shared rate limits. It also keeps failures visible.

**Alternatives considered**:

- Fetch live data from each page request. Rejected because multiple users could create duplicate requests and exceed the shared request budget.
- Silently show synthetic data on a live-path failure. Rejected because operators could mistake example data for live telemetry.

**Bounded investigation**: Confirm the project's worker scheduling and Redis lease patterns. Define how one worker owns a refresh, how an interrupted refresh is recorded, and how stale data is presented.

## Decision 5: Use current SDK contracts as candidates only

**Decision**: Use the current repository OpenAPI file to create a candidate request map. Verify each method against the source implementation and the installed `mistapi` signatures before implementation.

**Rationale**: OpenAPI 3.1.0 version 2609.1.0, dated 2026-09-07, contains candidate operations for org sites, site devices, gateway metrics, gateway insights, and peer-path statistics. An operation's presence does not prove that it matches the source's actual request.

**Candidate operations found**:

| SDK operation ID | OpenAPI method and path | Known parameters from current document |
|---|---|---|
| `listOrgSites` | `GET /api/v1/orgs/{org_id}/sites` | `limit`, `page` references |
| `listSiteDevices` | `GET /api/v1/sites/{site_id}/devices` | `type`, `name`, `limit`, `page` |
| `getSiteGatewayMetrics` | `GET /api/v1/sites/{site_id}/stats/gateways/metrics` | No operation-level parameters listed |
| `getSiteInsightMetricsForGateway` | `GET /api/v1/sites/{site_id}/insights/gateway/{device_id}/stats` | `metrics`, `port_id`, time window, interval, and pagination references |
| `countOrgPeerPathStats` | `GET /api/v1/orgs/{org_id}/stats/vpn_peers/count` | `distinct`, time window, and limit references |
| `searchOrgPeerPathStats` | `GET /api/v1/orgs/{org_id}/stats/vpn_peers/search` | `mac`, `site_id`, `type`, time window, sort, and pagination references |

**Alternatives considered**:

- Call undocumented routes directly. Rejected because MistHelper requires a working SDK method when one exists.
- Select API methods from operation names alone. Rejected because request arguments, output fields, and source parity are not proven.

**Bounded investigation**: Verify the resolved OpenAPI parameter references, response schemas, SDK signatures, pagination behavior, and source call arguments for each accepted journey. Remove candidates that the source does not use.

## Decision 6: Preserve source provenance and avoid code transfer

**Decision**: Record source and CC BY-NC-SA 4.0 provenance. Write new code. Reuse code only after maintainers approve license terms, attribution, and ShareAlike obligations.

**Rationale**: The source license may conflict with MistHelper distribution terms. A README or operations guide does not grant permission to copy code or assets.

**Alternatives considered**:

- Copy source code or screenshots before review. Rejected because rights and license compatibility are not confirmed.
- Omit source attribution. Rejected because it loses provenance and does not resolve license obligations.

**Bounded investigation**: Ask the repository maintainers to decide whether any source code, assets, or screenshots may be reused. Until then, copy none of them.

## Decision 7: Keep synthetic preview data isolated

**Decision**: Retain only independently created fictional test records and screenshots. Label every offline preview as synthetic and ensure live requests never fall back to that data.

**Rationale**: The issue identifies screenshot data as fictional offline data. The distinction must remain visible in tests and UI behavior.

**Alternatives considered**:

- Reuse source screenshots as live examples. Rejected because they contain fictional data and may have separate license restrictions.
- Use production exports for test fixtures. Rejected because tests must not use production credentials or data.

**Bounded investigation**: Inspect source preview artifacts only to identify expected behavior. Do not copy image files or fixture payloads without approval.

## Unresolved Evidence

- Exact source SDK methods, arguments, response fields, and pagination are not established by the supplied summary.
- The implementation review confirms selected worker facts, but does not verify `SKIP_ENRICHMENT`, token rotation, API host settings, organization settings, or every pagination and enrichment path.
- PR #4208 is the proposed canonical owner for shared WAN pages, collection, request admission, cache, and offline preview. It remains open and is not merged. Issue #4195 remains active, so owners must confirm the mapping before implementation.
- The status of the source license's compatibility with MistHelper remains unknown.
- The source worker's refresh lease, startup cache selection, and partial-refresh rules are not established.
- The source insight call uses a direct HTTP path. The selected SDK method's response does not yet prove the expected `rx_bps`, `tx_bps`, `port_id`, interval, and seven-day window contract.
- Redis namespace, serialization, refresh lock, payload size, target TTL, and outage details need confirmation against current MistHelper Redis policy.
