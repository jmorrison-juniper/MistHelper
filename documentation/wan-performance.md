# WAN Performance

Open **WAN Performance Preview** in the existing portal navigation.
The overview links to the gateway, WAN port, and VPN peer.
Each detail page has a return link.
The existing portal access controls protect these pages.

## Synthetic data

Each page identifies its records as synthetic.
The preview creates no Mist, database, Redis, or background refresh client.
Synthetic records do not enter the configured application store.
The preview does not represent the state of a production network.

The WAN port shows one synthetic measurement hour and calendar summaries.
The periods use UTC days, ISO weeks that start on Monday, and calendar months.
Each interval includes its start and excludes its end.
Observed hours count distinct records, not measured duration.
Missing hours do not count as healthy hours.
Missing values remain absent rather than zero.

Daily means use available hourly values.
Weekly and monthly means give each available daily mean equal weight.
This preserves the source calendar calculation.
It is not a sample-weighted mean or a duration-weighted mean.
Maxima use the largest available hourly value.
The preview does not calculate percentiles, availability, congestion duration, or live utilization.

The independent implementation uses behavior reviewed at source commit
`2d1c2199fa1e31c129ef1e051c5389349a207785`.
The relevant source files are `docs/screens.md`, `docs/operations.md`, and `src/aggregators/time_aggregator.py`.
No source code, fixtures, screenshots, or other assets were copied.

## VPN snapshot validation

The collection boundary validates fields from the bundled
[VPN peer API schema](api/orgs/GET_orgs_org_id_stats_vpn_peers_search.md).
Latency and jitter use milliseconds.
Loss uses percent, from 0 through 100.
MOS uses a score from 0 through 5.
The validator preserves measured zero and rejects invalid values.
An absent value remains unknown.
The validator does not infer an hourly interval, coverage, utilization, or availability.
This boundary makes no API call and is not connected to the preview.

## Live integration limits

Select **Open live snapshots** from the preview.
Live pages use the existing portal authorization and server-selected organization.
Page reads use the recent snapshot cache, without a Mist request.
Select **Refresh current snapshots** to request new data.
The existing portal CSRF protection applies to this form.

Shared admission defaults to `auto` when application storage is configured.
Restart every worker after configuration changes.
Set `WAN_SHARED_ADMISSION=true` to require admission even without automatic storage detection.
The explicit `false` setting preserves legacy transport behavior and prevents WAN refresh.
The existing Redis and database credentials must be configured.
The common Mist session transport then applies shared request admission.
An absent session, unsupported transport, missing store, or Redis outage prevents refresh.
An unsupported session transport or incomplete admission configuration does not stop portal startup.
The portal logs the limitation, and live refresh returns an unavailable response.
Common API session initialization still refuses an unaccounted transport.
No automatic background worker starts.

### Request bounds

One organization can start one WAN refresh every 300 seconds.
Overview refresh requests one page of 100 gateway ports and one page of 100 VPN paths.
It makes no gateway discovery or insight request.
Selected gateway refresh also discovers that gateway, reads the metric catalog, and requests two single-metric pages.
From a gateway page, refresh selects that exact site and gateway MAC.
Filtered discovery permits two rows to detect an ambiguous match and requires exactly one matching returned device.
The overview lists every distinct gateway returned in its cached pages.
To select another known gateway, enter its site ID and MAC in the optional overview fields.
Both selectors remain under the server-selected organization and use verified SDK filters.
Selected port and peer pages must match the returned gateway and site.
The maximum is two SDK calls for overview refresh and six for selected gateway refresh.
Admitted transport makes no automatic retry.
Gateway discovery uses the returned device UUID, never a UUID derived from its MAC.
Each insight request covers one completed UTC hour, with `limit=1` and `page=1`.
The catalog must confirm the scope, type, unit, interval, and max-age.
Two separate metric requests avoid an undocumented multi-metric mapping.
The response must align zero or one timestamp with the same number of values in the requested window.
An empty aligned series remains unknown, while valid port and peer observations remain available.
The collector never follows a `next` URL.
A page with more results reports partial coverage.
The cooldown remains after success or failure.
No release operation can bypass it.

Port utilization uses `stats_gateway_port.speed`, documented in Mbps, and `rx_bps` and `tx_bps`, documented in bit/s.
Each direction divides its current rate by the reported speed multiplied by 1,000,000.
The result is a point-in-time percentage, not measured time above a threshold.
Missing or invalid capacity and rates remain unknown, with invalid inputs reported in the log.
The collector does not clamp percentages or infer full-hour coverage from a snapshot.
Persisted directional percentages support observation counts above 70%, 80%, and 90%.
Daily, weekly, and monthly reports show counts and the longest run of adjacent observed hours.
An equal value does not exceed the threshold.
Missing, unknown, and non-exceeding hours break a run.
Each report shows valid observation hours against expected calendar hours.
These counts describe retained snapshots, not cumulative or continuous congestion duration.
Port state uses the current boolean `up` field.
VPN details also show the current active-path flag, gateway-reported uptime in seconds, and last-seen time in UTC.
These fields describe the cached observation, not availability minutes, flap counts, or continuous coverage.
Missing or invalid state metadata remains unknown and does not enter historical numeric aggregates.

The common transport also counts actual requests across workers.
Its rolling Redis ledger permits at most 5,000 attempts per authentication fingerprint in 3,600 seconds.
The same atomic reservation also limits each organization to 5,000 attempts, across different authentication values.
These local ceilings are conservative migration admission limits.
Org URLs supply their organization identity.
Site requests use the selected session context and fail when that identity is absent.
Pagination, normal operations, fast-mode calls, and SDK retries use that same transport.
The ledger stores a SHA-256 fingerprint, not the authentication value.
Redis time supplies the rolling-window clock.
Admission fails closed when Redis is unavailable.

With shared admission enabled, transport retries are disabled.
HTTP 429 stops before the SDK starts an automatic retry or waits on `Retry-After`.
Each connection and read timeout has a 30-second maximum.
Existing timeout and retry behavior remains unchanged when the setting is false.
Every configured process uses automatic admission unless explicitly disabled.
Calls from other applications or unconfigured sessions are outside this ledger.
SDK authentication bootstrap requests occur before shared transport configuration and remain outside this ledger.
Token and cookie authentication share the organization ceiling.
The ledger hashes authentication headers without retaining or logging their values.

### Configured history

The public repository follows the active DataExporter output selection.
SQLite selection uses the same configured database path.
The SQLite file must already exist.
CSV selection uses an isolated collection in the already configured ArangoDB application database.
CSV-only mode has no history repository.
The repository never creates another database or mirrors WAN history into Redis.

Upserts use the complete identity and UTC observation hour as the natural key.
SQLite batches use one transaction.
ArangoDB batches use one streaming transaction and stable document keys.
The repository rejects synthetic records before any write.
Storage failures remain explicit.
The recent cache changes only after the history transaction succeeds.

Port and peer hours retain the last collected observation.
Gateway hours retain the validated hourly insight samples and catalog units.
This is a migration design decision, not proof of a full-hour average.
The actual collection timestamp remains in every record.
Rates use `rx_bps` and `tx_bps`, never cumulative byte counters.
Peer path keys include the remote site, remote port, and VPN type.
Their derived key is not a claimed source tunnel identifier.

Detail pages read a bounded 31-day window and show daily, weekly, and monthly observation summaries.
The port detail has a separate CSRF-protected, operator-triggered insight refresh.
It requires the exact site, gateway, and port identity from the validated cached page.
It shares the organization cooldown and request ledger with every other WAN refresh.
It permits four SDK calls: exact gateway discovery, metric catalog, receive rate, and transmit rate.
Each metric request selects the actual gateway UUID and exact `port_id`.
Each request covers one completed UTC hour with `limit=1` and `page=1`.
Catalog checks require gateway scope, `bit/s`, a 3,600-second interval, and sufficient `max_age`.
Response checks require aligned timestamps and values, the exact window, and no next page.
Empty aligned series remain unknown.
The selected application store retains these port rate records without replacing the current snapshot.
Natural-key upserts replace an existing row for the same port and UTC hour.
The insight row contains rates only, not utilization derived from current link speed.
This operation does not request earlier pages or promise complete hourly coverage.
This read window is not a retention period.
WAN code does not delete application history or change existing TimeSeries retention.
Unknown values and missing hours never become healthy observations.

### Cache isolation and failure

Org cooldown keys use `misthelper:wan:v1:refresh:<org_id>`.
Recent snapshot keys use `misthelper:wan:v1:snapshot:<org_id>`, with a 3,600-second TTL.
The shared request ledger uses `misthelper:api:v1:requests:<authentication_fingerprint>`.
Organization ledgers use `misthelper:api:v1:org:<org_id>`.
Ledger keys expire after 3,601 seconds without another admitted request.
These TTLs are conservative migration decisions, not source cache parity.

Snapshots older than five minutes have a stale label.
Cache errors render an unavailable state without starting a live request.
Refresh errors return HTTP 503 and preserve the previous cache.
History errors do not appear as successful empty history.
An unavailable history connection preserves readable cached detail views but prevents a new refresh.

### Unsupported source semantics

This review examined source revision `2d1c2199fa1e31c129ef1e051c5389349a207785`.
Its `ProjectGoals.md` requires hourly availability, transition counts, quality statistics, elapsed threshold hours, and 13-month history.
Observation counts do not satisfy elapsed threshold hours or complete-hour quality statistics.
The bounded 31-day detail read does not satisfy the 13-month reporting requirement.
No verified source contract establishes 13-month backfill or historical VPN metric samples.
Gateway insights do supply timestamped samples within each catalog metric's supported `max_age`.
The gateway insight operation also accepts `port_id` for a selected interface.
Current scoped refresh uses its two single-metric insight calls for the selected gateway.
Adding two port insight calls to that refresh would exceed its six-call ceiling.
A separate selected-port workflow uses four calls for discovery, catalog, and two metrics.
It collects only one completed catalog-supported hour, not 13-month backfill.
The migration does not infer historical link capacity from current port speed.
The live view supports verified directional snapshot utilization, not full-hour utilization averages.
Snapshot status and sparse hourly observations cannot establish historical availability or congestion duration.
Device-event search supports time bounds and type filters.
Its response supplies free-form event types, not verified WAN up/down transition values.
The documented examples describe DNS and tunnel provisioning, not link transitions.
The port `last_flapped` field does not establish timestamp units or a flap-count history.
VPN peer search supports `start`, `end`, and `duration`.
The collector already requests `duration="1h"` within its existing call ceiling.
The resolved `vpn_peer_stat` response schema describes latency and jitter as last sampled values.
Its rows have `last_seen`, but no measurement `timestamp`.
The public `VpnPeersStatsExample` has no measurement timestamp either.
Peer observation time does not establish the sample time of each metric.
The existing exporter primary-key strategy names `timestamp`, `from_device`, and `to_device`.
Those application fields do not establish a source response contract.
No verified response establishes historical VPN samples for normalization into source hours.
The source quality calculator defines p95 using sorted samples and a zero-based index of `floor(0.95 * count)`.
For fewer than 20 samples, it substitutes the maximum as an approximation.
This convention does not establish a complete source sampling window.
The portal retains one observation per identity and hour, not every raw quality sample.
Its calendar summaries therefore report observed means and maxima, not a source hourly p95.
The source status calculator assumes constant state when events are absent.
It also identifies transitions through `UP` and `DOWN` substrings in free-form event types.
Neither assumption proves complete event coverage or a verified WAN transition mapping.
The migration does not use these assumptions to calculate availability or flap counts.
The source `TODO.md` explicitly describes current VPN statistics as point-in-time data.
Its historical VPN method, storage, and dashboard tasks remain unchecked.
The bundled OpenAPI defines a generic device-insight operation with a metric path parameter.
It does not verify the proposed VPN metric name, per-peer filters, or peer-series mapping.
The generic operation alone does not establish VPN metric timestamps.
The insight response does not define how multiple requested metric names map to its single result sequence.
Gateway refresh supports any selected organization gateway through exact filtered discovery.
The cached gateway list reflects bounded port and peer pages, not a complete organization inventory.
Complete organization-wide gateway history and historical VPN coverage remain unimplemented.
The source documentation and implementations disagree about some metric and missing-data behavior.
These limits prevent full source acceptance.

The preview adds no database, Snowflake connection, service, Compose group, public port, or credential store.
PR #4205 has a separate, unmerged WAN implementation.
This preview does not use that implementation.
