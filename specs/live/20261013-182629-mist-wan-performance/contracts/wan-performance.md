# Contract: Mist WAN Performance

This contract proposes destination behavior.
Source routes are documented. Exact SDK and storage contracts remain investigation prerequisites.

## Routes and Navigation

| Source journey | Proposed MistHelper route | Required context |
| --- | --- | --- |
| `/` | `/wan-performance/` | Current configured organization |
| `/gateway/<gateway_id>?site_id=<site_id>` | `/wan-performance/gateway/<gateway_id>?site_id=<site_id>` | Gateway and site |
| `/port/<site_id>/<port_name>?gateway_id=<gateway_id>` | `/wan-performance/port/<site_id>/<port_name>?gateway_id=<gateway_id>` | Site, exact port name, gateway |
| `/vpn/<site_id>/<peer_mac>` | `/wan-performance/vpn/<site_id>/<peer_mac>` | Site and peer MAC |

The blueprint must preserve encoded port slashes and peer colons through route resolution and URL generation.
Test `ge-0%2F0%2F1` and `11%3A22%3A33%3A44%3A55%3A66` directly.
Use a path-aware port route with strict validation after one decoding step.
Reject traversal, control characters, empty names, excessive length, and conflicting membership.
Do not double-decode input.

Gateway links preserve `site_id`. Port links preserve `gateway_id`.
All pages retain the selected time window and parent navigation.
The destination prefix is intentional. Do not replace the existing MistHelper `/` route or add root aliases.

The shared allowlist, CSRF rules, headers, local assets, and theme remain effective.
An address outside the allowlist receives HTTP 403.
Invalid input receives HTTP 400. An unknown entity receives HTTP 404.
Unavailable collection or history has a visible state and reason, not a server-error page.
No browser receives the Mist token or database credentials.

## Page and Selector Contract

| Page | Information order to verify in T003 | Stable selector values |
| --- | --- | --- |
| Shared | Current navigation, context, freshness, period controls, return links | `nav-wan-performance`, `wan-context`, `wan-data-state`, `wan-period-filter`, `wan-back-link` |
| Overview | Summary cards, circuit and site summaries, quality charts, detail links | `wan-overview`, `wan-utilization`, `wan-congestion`, `wan-availability`, `wan-path-quality`, `wan-gateway-link` |
| Gateway | Identity, health summary, WAN ports, peer paths | `wan-gateway`, `wan-gateway-health`, `wan-port-table`, `wan-port-link`, `wan-peer-link` |
| WAN port | Identity, utilization, receive/transmit bandwidth, historical detail | `wan-port`, `wan-utilization-chart`, `wan-bandwidth-chart`, `wan-history` |
| VPN peer | Identity, loss, latency, jitter, tunnel details | `wan-peer`, `wan-loss`, `wan-latency`, `wan-jitter`, `wan-tunnel-table` |

Use these values in `data-testid`.
Repeated links carry separate entity data attributes for unambiguous selection.
Add selectors for every interactive filter, chart control, and detail link identified in T003.
The proposed information order does not replace an approved source layout inventory.
Compare four reference captures at 1440 by 1100 pixels and at a 390-pixel viewport.
Preserve visual hierarchy and metric grouping, not exact source theme colors.
Record an approved difference for each intentional layout change.

## History and Measurement Contract

Use the identities, units, and missing-data rules in [data-model.md](../data-model.md).
All views read the same selected application store and UTC interval.
Display sample coverage and last successful collection time.
Daily, weekly, and monthly calculations require verified completed behavior in T006.

Redis's proposed history-copy TTL is 2,678,400 seconds, which is 31 days.
That value preserves the documented cache window, not a confirmed Snowflake retention period.
Renew expiry only when a record is rewritten with approved current content.
A read must not extend a key's life.
Do not guarantee a complete month when only part of that month is available.
No historical import or stable export route is authorized.
T008 records confirmed export behavior or an explicit exclusion.

## Redis Isolation and Ownership

Use only the existing configured Redis service and credentials.
The feature owns keys beginning with `misthelper:wan-performance:v1:`.
The proposed shape is `misthelper:wan-performance:v1:<org_id>:<kind>:<identity_digest>`.
The digest covers canonical site, gateway, port, peer-path, period, and mode values as applicable.
Separate kinds are `view`, `history`, and `refresh-status`.
These are destination proposals, not source key formats.

- `view` keys expire after 300 seconds. A cache hit never triggers another cloud collection.
- `history` keys expire after 31 days. Durable history remains in the selected application database.
- `refresh-status` keys expire after 600 seconds. Durable owner state remains in the selected database.
- Payloads use UTF-8 JSON with a schema version, UTC timestamps, units, coverage, and provenance.
- Reject unknown versions, invalid identity, nonfinite numbers, and corrupt JSON. Log the reason and read the authoritative store.

Only the feature integration layer writes these keys.
Tests prove organization and synthetic/live isolation.
Do not use `FLUSHDB`, broad deletion, or another feature's key prefix.
No separate Redis database number, service, or new password setting is needed.
Cache failures log a reason and leave durable reads available.
If the durable store also fails, report unavailable data.
Never obtain page data by making an uncontrolled direct cloud request after cache failure.

## Refresh and Shared Rate Limits

The following bounds are proposed defaults, not verified source scheduler semantics.
T007 and T009 must approve them before implementation.

| Control | Proposed bound | Verification |
| --- | --- | --- |
| Current refresh | Due every 300 seconds, with one queued run per organization | Duplicate browser and worker test |
| Hourly reporting | Completed UTC hour becomes due five minutes after its end | Verify historical endpoint coverage, not relabeled current data |
| Ownership | One active owner per organization, database lease of 120 seconds, renewal every 30 seconds | Expiry, takeover, and stale-owner rejection |
| Concurrency | One SDK request in flight per WAN owner | Count concurrent requests |
| Work budget | At most 100 attempts per run, at most 600 seconds | Pagination cursor persists for later runs |
| WAN allowance | At most 10 percent of the verified hourly organization allowance | Shared ledger includes existing operations |
| Reserved allowance | Leave at least 20 percent of the verified allowance for other work | Pause WAN work before reserve is consumed |
| Request and retry | Proposed 20-second request deadline and at most three total attempts | Verify actual SDK timeout/retry controls |

Admission must occur before every SDK request, pagination request, and retry.
All existing runtime callers must coordinate with the shared quota owner.
Use current session and retry settings through an approved shared integration.
Do not trust the process-local cache as a cross-process ledger.
Do not bypass admission through fast mode or an SDK internal retry.
If admission accounting cannot be proven, keep WAN refresh disabled.

Honor verified server quota metadata and HTTP 429 retry timing.
Use bounded exponential backoff with jitter, from one through 60 seconds, for retryable failures.
If a server delay exceeds the work deadline, retain the cursor and schedule later work.
HTTP 401 and 403 stop live work with a credential or access reason.
HTTP 5xx, timeouts, and malformed responses do not publish fresh empty history.

The existing application lifecycle starts and stops the owner.
No new service, public port, or Compose group is required.
Worker startup, reloader startup, shutdown, and lease expiry must not duplicate work.
If coordinated admission or the durable lease fails, pause collection and report the cause.
Redis outage alone does not remove durable ownership or request-admission protection.
Resume only with valid ownership and budget.

## Offline and Failure Contract

Offline fixtures are independently authored, historical, and explicitly synthetic.
Each page carries the synthetic label. Connection indicators must not claim live connectivity.
Offline mode starts no Mist client, Redis connection, database connection, or refresh worker.
Fixtures never enter live cache or durable history.

Unit tests cover calculations and time boundaries.
Integration tests cover selected-store writes and reads, expiry, failures, and coordinated requests.
E2E tests cover all four journeys, direct links, selectors, access denial, missing data, and return navigation.
Retain a screenshot or trace for every failed browser journey under ignored test artifacts.
Do not use production credentials.
