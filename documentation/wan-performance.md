# WAN Performance

Select **WAN Performance** in the existing portal navigation.
The tab opens the read-only live overview.
Select **Open the isolated synthetic preview** to view the four source-shaped sample pages.
The overview links to the gateway, WAN port, and VPN peer.
Each detail page has a return link.
The existing portal access controls protect these pages.

## Synthetic data

Each page identifies its records as synthetic.
The preview creates no Mist, database, Redis, or background refresh client.
Synthetic records do not enter the configured application store.
The preview does not represent the state of a production network.

The synthetic overview, gateway, WAN-port, and VPN-peer pages show the current destination layout.
They use independent sample data for KPI cards, tables, gauges, and charts.
The WAN port shows one synthetic measurement hour and calendar summaries.
The periods use UTC days, ISO weeks that start on Monday, and calendar months.
Each interval includes its start and excludes its end.
Observed hours count distinct records, not measured duration.
Missing hours do not count as healthy hours.
Missing values remain absent rather than zero.

Daily means use available hourly values.
Weekly and monthly means give each available daily mean equal weight.
This rule gives each available calendar day equal weight.
It is not a sample-weighted mean or a duration-weighted mean.
Maxima use the largest available hourly value.
The preview does not calculate percentiles, availability, congestion duration, or live utilization.

## Destination screenshot evidence

Browser tests capture the four destination pages under `test-artifacts/wan-performance/`.
The tests use a 1440-pixel width and a 1100-pixel viewport.
The screenshots show only MistHelper pages with a synthetic-state banner.
The overview uses two columns for summary tables and charts.
Single-chart detail views use the available content width.
Migrated history summaries stay collapsed until the operator opens them.

These images do not compare the source interface.
Source rights and comparison evidence remain unverified, so these images do not prove visual parity.

| Page | Destination image size | Visible destination content |
| - | - | - |
| Overview | 1440 x 2352 | The 25 KPI cards, three tables, charts, and site controls show 12.5 percent utilization and 1.0 Gbps total bandwidth. |
| Gateway | 1440 x 1100 | Six KPI cards, two tables, and two charts show 125 Mbps receive, 50 Mbps transmit, 0.25 percent loss, 33.3 ms latency, and 4.5 ms jitter. |
| WAN port | 1440 x 1377 | Six KPI cards, a utilization gauge, detail tables, a bandwidth chart, and collapsed history show the selected port and its synthetic values. |
| VPN peer | 1440 x 1378 | Six KPI cards, three scale-defined gauges, a quality chart, and two detail tables show peer identity and an unscaled MOS value. |

The MistHelper shell and synthetic-state banner add shared navigation and state labels.
The sample data does not establish live connectivity, availability, or congestion duration.

The independent implementation uses behavior reviewed at source commit
`2d1c2199fa1e31c129ef1e051c5389349a207785`.
The relevant source files are `docs/screens.md`, `docs/operations.md`, and `src/aggregators/time_aggregator.py`.
No source code, fixtures, screenshots, or other assets were copied.

## VPN snapshot validation

The collection boundary validates fields from the bundled
[VPN peer API schema](api/orgs/GET_orgs_org_id_stats_vpn_peers_search.md).
Latency and jitter use milliseconds.
Loss uses percent, from 0 through 100.
The schema defines no MOS scale, so the preview displays MOS as a raw value and does not use a gauge.
The validator preserves measured zero and rejects invalid values.
An absent value remains unknown.
The validator does not infer an hourly interval, coverage, utilization, or availability.
This boundary makes no API call and is not connected to the preview.

## Live integration limits

The feature package is `src/interfaces/wan_performance/`, beside the shared portal package.
This placement keeps the portal package within the repository's five-child limit.

The portal tab opens live snapshots.
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
Set `WAN_BACKGROUND_REFRESH=false` to disable the worker.
The default is true when the Mist session, shared Redis admission, and selected history store are ready.
Each portal process starts a worker thread, but a Redis lease elects one process for the organization.
The elected process runs an immediate bounded refresh, then waits 300 seconds after each attempt.
The worker uses the same request ledger, five-minute organization cooldown, cache, and configured history store as manual refresh.
It never creates a second database or Redis service.
An unclean process exit leaves a 600-second lease, so another process waits for expiry before it can refresh.

The source refresh worker polls bulk port data without a fixed cycle delay and orders work by stale site.
The source dashboard precomputer writes five whole-dashboard result groups every 20 seconds.
This portal instead reads at most 100 ports and 100 VPN paths per cycle, then refreshes one organization every 300 seconds.
It computes selected-identity history summaries when a detail page opens.
It does not publish whole-organization precomputed dashboard groups.
The MistHelper collector has no complete all-site source dataset, so whole-organization summaries from its bounded pages would be incomplete.
The source's continuous poll rate and full-site cache coverage are not migrated.
The configured request ledger, bounded page size, and history store keep this worker inside the MistHelper deployment model.

### Request bounds

One organization can start one WAN refresh every 300 seconds.
Overview refresh requests one page of 100 gateway ports and one page of 100 VPN paths.
It makes no gateway discovery or insight request.
Selected gateway refresh also discovers that gateway, reads the metric catalog, and requests one combined rate page.
From a gateway page, refresh selects that exact site and gateway MAC.
Filtered discovery permits two rows to detect an ambiguous match and requires exactly one matching returned device.
The overview lists every distinct gateway returned in its cached pages.
To select another known gateway, enter its site ID and MAC in the optional overview fields.
Both selectors remain under the server-selected organization and use verified SDK filters.
Selected port and peer pages must match the returned gateway and site.
Overview refresh permits at most ten stats requests, with five pages per endpoint.
Selected gateway refresh permits at most fourteen requests, including gateway discovery, the metric catalog, and two separate rate requests.
Admitted transport makes no automatic retry.
Gateway discovery uses the returned device UUID, never a UUID derived from its MAC.
Each gateway rate request covers one completed UTC hour, with `limit=1` and `page=1`.
Selected-port rate requests use a 10-minute interval and align at most six timestamps with named rate arrays.
The catalog must confirm the scope, type, unit, interval, and max-age.
The collector sends separate bounded `rx_bps` and `tx_bps` requests.
The collector rejects unnamed or misaligned rate arrays.
An empty aligned series remains unknown, while valid port and peer observations remain available.
The insight collector never follows a `next` URL.
A page with more results reports partial coverage.
The cooldown remains after success or failure.
No release operation can bypass it.

Port utilization uses `stats_gateway_port.speed`, documented in Mbps, and `rx_bps` and `tx_bps`, documented in bit/s.
Each direction divides each rate sample by the reported speed multiplied by 1,000,000.
`utilization_pct` stores the larger directional percentage at each 10-minute sample.
The local hourly p95 uses a floor-index rule and the maximum when it has fewer than 20 samples.
Daily p95 summarizes hourly p95 values.
Local weekly and monthly p95 use the maximum daily p95.
Missing rates or capacity keep utilization unknown.
The six sample intervals estimate threshold occupancy in 10-minute units.
The collector reports congestion minutes only when all six utilization samples are known.
Missing or invalid capacity and rates remain unknown, with invalid inputs reported in the log.
The collector does not clamp percentages or infer full-hour coverage from a snapshot.
Persisted directional percentages support observation counts above 70%, 80%, and 90%.
Daily, weekly, and monthly reports show counts and the longest run of adjacent observed hours.
An equal value does not exceed the threshold.
Missing, unknown, and non-exceeding hours break a run.
Each report shows valid observation hours against expected calendar hours.
These counts describe retained snapshots, not cumulative or continuous congestion duration.
Selected-port refresh searches gateway device events for `GW_PORT_UP`, `GW_PORT_DOWN`, `GW_WAN_UP`, and `GW_WAN_DOWN`.
It filters events to the selected gateway and matches the port identifier or event text.
The event search follows at most five pages of 100 records.
An event search beyond that bound marks status minutes and flap count unknown.
The local status summary leaves time before the first matching event unknown.
It holds each event state until the next event or the hour end.
When no matching event exists, the current cached port state represents the full hour.
Flap count equals the number of matched transition events.
Period summaries sum known up/down minutes and event counts, and show complete event hours against expected hours.
The up percentage uses known minutes only.
Port and peer snapshots also retain an explicit boolean `up` observation.
Their sampled-state summaries still report known states and changes between adjacent observed hours.
Gaps break sampled-state transitions.
Port state also appears as the current boolean `up` field.
VPN details also show the current active-path flag, gateway-reported uptime in seconds, and last-seen time in UTC.
These fields describe the cached observation, not availability minutes or continuous coverage.
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

Port and peer snapshot hours retain the last collected observation.
Gateway hours retain the validated hourly insight samples and catalog units.
This is a migration design decision, not proof of a full-hour average.
The actual collection timestamp remains in every record.
Rates use `rx_bps` and `tx_bps`, never cumulative byte counters.
Peer path keys include the remote site, remote port, and VPN type.
Their derived key is not a claimed source tunnel identifier.

Detail pages query up to thirteen calendar months of retained history and show daily, weekly, and monthly summaries.
The query bound is 397 days and at most 9,528 hourly records for one identity.
This limit bounds reads. It does not change MistHelper storage retention.
Daily summaries show mean, maximum, and observed p95 across retained hourly values.
For selected-port utilization, each hourly value is the p95 of its raw 10-minute samples.
The local p95 uses a floor-index rule and the maximum when it has fewer than 20 observations.
Local weekly and monthly p95 values use the maximum daily p95.
Loss, jitter, and latency retain one average per selected hour.
Their p95 summarizes retained hourly values, not source raw within-hour quality samples.
Detail pages also show rolling 3-hour, 12-hour, and 24-hour summaries ending at the latest retained observation.
Each rolling window reports its observed record count, mean, maximum, and observed p95.
This anchor avoids presenting stale retained data as a current measurement.
The port detail has a separate CSRF-protected, operator-triggered insight refresh.
It requires the exact site, gateway, and port identity from the validated cached page.
It shares the organization cooldown and request ledger with every other WAN refresh.
It permits at most fourteen SDK calls: gateway discovery, metric catalog, two rate requests, five port-stat pages, and five event pages.
Each rate request selects the actual gateway UUID and exact `port_id`.
Rate requests cover one completed UTC hour with `interval=10m` and at most six aligned samples.
Catalog checks require gateway scope, a supported rate unit, a 600-second interval, and sufficient `max_age`.
The port-stat request uses `searchOrgSwOrGwPorts` with the selected gateway and port.
The API schema defines scalar `loss`, `jitter`, and `latency` fields but does not define their units.
The application retains each scalar as a raw poll sample and does not assign a unit.
The selected application store retains port rate, utilization, raw quality, congestion, and event-derived records without replacing the current snapshot.
Each live poll is stored separately with its full identity and UTC sample time.
SQLite stores raw samples in `wan_performance_samples`, and ArangoDB uses the matching collection.
Hourly records keep their existing replacement behavior, and repeated polls in one hour remain distinct samples.
The application sets no sample expiry and makes no retention or backfill guarantee.
Natural-key upserts replace an existing row for the same port and UTC hour.
The record derives utilization from the cached Mbps speed and six aligned rate samples.
It does not request earlier rate windows or promise complete 13-month coverage.
The peer detail has a separate CSRF-protected refresh for one cached peer path.
It searches `searchOrgPeerPathStats` with the supported gateway and site filters.
The collector follows at most five `search_after` pages, then matches the full peer identity locally.
The API schema defines scalar peer `loss` in percent and `latency` and `jitter` in milliseconds.
The schema describes MOS as a quality measure but gives no display scale or metric timestamp.
The collector stores each scalar as a raw poll sample and keeps epoch-second `last_seen` separate.
It preserves a partial state when the page limit leaves results unseen.
It rejects duplicate rows for one full path because the response has no sample timestamp to disambiguate them.
This read window is not a retention period.
WAN code does not delete application history or change existing TimeSeries retention.
Unknown values and missing hours never become healthy observations.

### Cache isolation and failure

Org cooldown keys use `misthelper:wan:v1:refresh:<org_id>`.
Worker election keys use `misthelper:wan:v1:worker:<org_id>` with a 600-second lease.
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
Sample-based threshold durations and raw within-hour utilization p95 are implemented for a selected collected hour.
Average loss, jitter, and latency do not retain the source raw quality samples.
The detail query spans thirteen calendar months in the selected MistHelper history store.
It reads records that the application already retained and does not backfill missing records.
The history horizon does not prove complete 13-month availability or hourly coverage.
The source `data_provider.py` calls `api_client.get_vpn_peer_metrics_timeseries` for peer detail.
The source `detail_data.py` passes site, device, peer MAC, start, and end to that provider.
The source `mist_client.py` requests `vpn_peer-metrics` with peer MAC, local port, remote port, interval, start, and end.
The bundled OpenAPI does not define this source response contract.
Gateway insights do supply timestamped samples within each catalog metric's supported `max_age`.
The gateway insight operation also accepts `port_id` for a selected interface.
The existing MistHelper WAN Dashboard reads `wan_link_health` through `getSiteInsightMetricsForDevice`.
The bundled OpenAPI and installed SDK do not establish that metric as a supported request contract.
The selected-port workflow uses `searchOrgSwOrGwPorts` for documented scalar fields.
The bounded page collector uses at most five pages for each organization-stat search.
The selected-port workflow uses up to five event pages.
It collects only one completed hour, not 13-month backfill.
The migration uses cached link capacity to derive utilization from aligned 10-minute rate samples.
The live event query returned the four source WAN event types with timestamp and port fields.
It records known up/down minutes and matched transition counts for one completed hour.
The local no-event fallback uses the cached current state for the full selected hour.
When events exist, time before the first event remains unknown.
The event search has a five-page cap and cannot prove historical availability across gaps.
The port `last_flapped` field does not establish timestamp units or a flap-count history.
VPN peer search supports `start`, `end`, and `duration`.
The collector already requests `duration="1h"` within its existing call ceiling.
The resolved `vpn_peer_stat` schema defines scalar `loss`, `latency`, `jitter`, and `mos` fields.
It gives percent units for loss and millisecond units for latency and jitter.
It describes MOS as a quality measure but gives no scale.
Its rows have epoch-second `last_seen`, but no metric `timestamp`.
The public `VpnPeersStatsExample` has no measurement timestamp either.
Peer observation time does not establish the sample time of each metric.
The existing exporter primary-key strategy names `timestamp`, `from_device`, and `to_device`.
Those application fields do not establish a source response contract.
The source peer method defines requested time-series fields, but the bundled API schema omits its response contract.
The separate peer-stat schema supports raw scalar values, not timestamped quality history.
The source `QualityCollector.get_wan_edge_stats` reads `wan_interfaces` from `getSiteDeviceStats`.
It calculates gateway WAN-interface p95 from `loss_samples`, `jitter_samples`, and `latency_samples`.
It falls back to scalar loss, jitter, and latency fields when those sample arrays are absent.
This gateway-wide WAN-interface quality series differs from the peer-specific detail chart.
The local observed p95 uses a floor-index rule on retained WAN observations.
MistHelper retains one hourly projection per identity and each raw poll sample separately.
The local raw-utilization p95 uses a floor-index rule on six 10-minute rate values.
These calculations do not establish source weighting or p95 semantics.
The organization-stat schemas do not timestamp port or peer quality scalars.
These scalars cannot support historical raw-sample quality percentiles.
The application retains each scalar quality poll separately and does not claim that polling reconstructs past samples.
The bounded event page cap can leave an hour incomplete.
The bundled OpenAPI defines a generic device-insight operation with a metric path parameter.
Its response schema pairs string `rt` timestamps with numeric `results` values.
It does not list `vpn_peer-metrics`, the peer filters, or source-shaped timestamped metric rows.
The installed `getSiteInsightMetricsForDevice` wrapper also lacks `peer_mac` and `peer_port_id` arguments.
The migration therefore uses `APISession.mist_get` through the shared admitted Mist session.
Its query carries the exact source metric name and peer, local-port, and remote-port filters.
The source wrapper expects `results` rows with timestamp, loss, latency, jitter, and MOS fields.
The verified SDK signature does not accept those peer and port filters.
The implementation does not send this unsupported request or infer a peer time series from scalar stats.
Gateway refresh supports any selected organization gateway through exact filtered discovery.
The cached gateway list reflects bounded port and peer pages, not a complete organization inventory.
Complete organization-wide gateway history and VPN history beyond individually refreshed hours remain unimplemented.
The source documentation and implementations disagree about some metric and missing-data behavior.
The 13-month history view does not backfill missing hours or restore data that Mist no longer retains.

### Browser evidence

The web-portal CI shard uploads the `wan-performance-browser-evidence` artifact.
It contains four synthetic page captures and two completed navigation captures from `test-artifacts/wan-performance/`.
The page files are `wan-overview-destination.png`, `wan-gateway-destination.png`, `port-destination.png`, and `peer-destination.png`.
The navigation files are `port-journey.png` and `peer-journey.png`.
These captures contain synthetic data only. They do not verify live API response mapping or full source parity.
The upload warns when no capture exists.

The preview adds no database, Snowflake connection, service, Compose group, public port, or credential store.
PR #4205 has a separate, unmerged WAN implementation.
This preview does not use that implementation.
