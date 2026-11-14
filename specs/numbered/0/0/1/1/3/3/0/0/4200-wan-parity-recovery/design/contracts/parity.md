# Source comparison and end-to-end contract

## Authorized original runtime examination

T054 executed the pinned original at `2d1c2199fa1e31c129ef1e051c5389349a207785`.
The later user grant permits isolated execution and internal captures, not protected implementation or asset imports.
It supersedes earlier unexecuted or rights-blocked observations below.
Original tests and independent operator scenarios remain separate.
The full original suite passed 137 tests with five warnings and no skips.
The final read-only source/harness run took 8.51 seconds.
No live Mist, Redis, Snowflake, production launcher, or production store was used.

The review recorded 101 observation/action entries across three browser passes, not 101 successful assertions.
The first 60-entry pass includes a fixture-shape HTTP 500 and three driver/control failures.
The next 22 entries correct SLE setup and region clicking and inspect chart controls.
The last 19 entries use populated independent SLE data, table controls, keyboard focus, and actual chart state changes.
The final pass was repeated with a read-only harness.
Private captures use 1280x900, 1440x1100, and 390x844 viewports.
Public theme CSS was served locally. External browser requests and Google Fonts were blocked.
This is not a pixel-equivalence baseline or complete production integration proof.

| Record | Source rows | Executed action and result | Limit |
| --- | --- | --- | --- |
| R01 | P01-P04, P38, P42, P48 | Overview, gateway, encoded port, and peer pages rendered. Gateway/port/peer links and browser history worked. | Source identity mapping and every live field are not accepted. |
| R02 | P29-P32 | All four ranges were selected on overview, port, and peer. Auto-refresh toggled. A coordinate click selected a region and exposed its breadcrumb. | Selecting a label does not prove complete range data. The site dropdown exposed no choices with the production-shaped `DimSite` collection. |
| R03 | P25, P27, P35, P38 | Gateway ports advanced to another page. SLE filtering committed with Enter. Three CSV downloads contained 10 congestion rows, seven alerts, and one degraded site. | Gateway sort controls were absent. Exported fields and ranking are source observations, not accepted SDK semantics. |
| R04 | P33-P34 | Corrected independent SLE data rendered summary/histogram charts, two classifier entries, seven gateways, seven interfaces, and one peer. Return navigation worked. | Source minute/percentage labels and classifier calculations do not establish API units or valid formulas. |
| R05 | P27, P33-P34 | Gateway/interface SLE tables changed lexical order and advanced from five rows to two. The peer filter removed its row. | Gateway/interface inputs are page controls, not column filters. A one-row peer table cannot prove meaningful sorting. |
| R06 | P28, P39, P43, P45 | Overview, gateway, port, and peer chart inventories were captured. Port zoom changed axes, reset restored them, pan changed mode, and a box drag changed bounds. PNG download succeeded. | Legend clicks hit the toolbar. Five tested legend coordinates remained covered. Share, clipboard, and external Plotly navigation were not activated. |
| R07 | P21-P23, P40, P45 | Missing detail and partial-peer cases rendered unavailable text alongside zero-shaped fields or gauges. Empty/loading scenarios showed loading text. | These defaults are not valid destination measurement semantics. The cache-metadata stale scenario did not establish a complete source stale-state contract. |
| R08 | P20, P28, P49-P50 | Desktop/narrow captures, 120 Tab presses across four pages, original test results, and destination browser assertions were recorded separately. | Narrow overview/gateway/port captures overflowed. Peer did not. Focus traversal is not proof that every chart is keyboard-operable. |

Evidence root: `test-artifacts/wan-performance/original-review/runtime/`.
The original logs are `original-tests-initial.log`, `original-tests-final-isolation.log`, and `original-tests-readonly-harness.log`.
Browser records are `browser-observations-first-cycle.json`, `browser-followup.json`, and `browser-remaining.json`.
Screenshots, three CSVs, and `original-native-plot-download.png` remain private ignored evidence.
The initial SLE 500 came from the independent harness's incorrect summary shape, not an established application defect.
An SVG locator could not click the region through Plotly's overlay. Real pointer coordinates resolved that driver limitation.
The final harness corrected its impacted-table response keys before populated table examination.
None of these setup corrections changed the original checkout or entered the product.
No source implementation, fixture, screenshot, or protected asset entered tracked destination files.

### Actionable remaining work

T012/T032/T036 still include buildable destination interaction work.
Implement independent zoom/reset, visible point inspection, and optional PNG controls over verified retained projections.
Use failing keyboard/browser tests and preserve exact gaps, scope, units, and accessible tables.
Add independently labeled sorting and display pagination to bounded raw SLE results without guessing API pagination or score ordering.
These items need destination design and implementation, not a new rights grant or live service.
Do not classify them as external blockers.

Region aggregates, role/failover ranking, SLE score meanings, and source-equivalent quality statistics still need exact contracts.
Real historical inventory, 13-month history, retention/capacity/completeness, and backfill still lack proof.
Live production dependency testing and hosted/owner acceptance remain outside this local assignment.
Keep issue #4200 open and the publication hold unchanged.

## Latest independent destination coverage

T055 adds independently designed discrete plots to the retained views.
`test_retained_plots_preserve_gaps_zero_missing_values_and_unit_boundaries` verifies bucket offsets, measured zero, absent metrics, and exact unit groups.
Constant and extreme finite values have separate regression cases.
Unavailable or entirely missing values produce no fabricated points.
`test_retained_plot_renders_present_values_without_missing_value_zeros` proves the existing one-read scope and no raw reads or writes.
The three-viewport retained-window browser journey verifies visible plots, exact values, absent connecting lines, and responsive layout.
The plot uses collection metadata and UTC bucket positions, not invented source metric timestamps.
This is a destination-only projection view, not source chart equivalence.

T052 adds exact cached-site navigation, not a complete site catalog or source-equivalent selector.
`test_cached_site_csv_cannot_include_other_cached_sites` verifies selected-site export scope.
Unknown and case-sensitive site identifiers have separate route assertions.

T053 adds independent `6h`, `12h`, `24h`, and `7d` UTC views for one full detail identity.
Each half-open interval ends before the current UTC hour and reads at most 168 retained hourly projections.
`test_retained_view_reads_exact_identity_without_filling_missing_hours` exercises actual temporary SQLite boundary reads.
`test_retained_view_rejects_invalid_repository_results` rejects duplicate, foreign, synthetic, and out-of-window records.
`test_retained_peer_window_refuses_ambiguous_path_scope` proves ambiguous peer routes cannot read arbitrary history.
Route tests distinguish empty data, missing stores, and failed reads without sample reads, writes, or API requests.
Organization and site aggregate windows remain explicitly unavailable. They do not fan out across identities.
The current-cache table and its CSV export remain independent of the selected retained window.
`test_browser_cached_site_and_retained_window_journey` covers site, gateway, port, peer, and overview navigation at all three viewports.
The mobile assertion reproduced unwrapped peer-identity overflow. Text wrapping repairs it without changing identifiers.
These views do not calculate aggregates, infer elapsed coverage, interpolate, or backfill missing hours.
Bucket presence never proves measurement completeness, healthy service, source time semantics, or source parity.

The independent SLE page supersedes the earlier evidence-only SLE assessment below.
It does not establish source parity.
The detailed inventory preserves its frozen destination observations.
The [current acceptance audit](../../analysis.md) records later controls and their remaining source-equivalence gaps.
`test_sle_get_is_cache_only_and_post_uses_supported_signature` proves cached-site scope and the installed SDK argument shape.
`test_sle_uses_actual_refresh_lease_without_releasing_cooldown` exercises the actual lease class with a mocked Redis client.
This is protocol evidence, not proof of two real processes or live Redis.
HTTP 403, 429, and 500 responses remain errors. A lost lease prevents the second API request.
Disabled metrics and foreign sites cannot trigger an impacted-gateway request.
Malformed rows, non-finite numbers, mismatched metrics, and oversized pages fail explicitly.
SLE duration units, aggregation, historical coverage, and response completeness remain unverified.

`test_browser_sle_explicit_inspection` exercises the independent form, results, unknown-unit labels, partial-page message, and return navigation.
`test_browser_cached_table_controls` exercises pagination, filtering, lexical sorting, and CSV download.
Both run at 1440x1100, 1280x800, and 390x844, with document overflow assertions.
These are destination usability checks, not protected source screenshots or visual comparisons.

`test_table_filter_keeps_full_scoped_history_and_csv_identity` separates table filtering from detail history and CSV scope.
`test_table_paginates_and_exports_all_matching_rows` verifies a complete cached export across display pages.
Formula-prefix tests preserve numeric values and neutralize dangerous text.
`test_cached_controls_preserve_scope_and_reject_foreign_cache` rejects another organization's cache.

`test_peer_mos_summary_preserves_retained_missing_units` stores old and new hours in temporary SQLite before summary calculation.
It covers either input order, same-day hours, cross-day merges, and documented summary units.
The route regression verifies a displayed score after an earlier missing unknown-unit record.
Incompatible measured units still fail. Old records remain unchanged.

## Inventory rules

Create one row for each visible element, action, metric, state, and navigation transition.
Use source documentation, page definitions, tests, and runtime observations only where permitted.
Pin every source reference to the reviewed commit.
Map rows to destination selectors and assertions. Do not mark a page complete because it loads.

| Journey | Source route | Required comparison subjects |
| --- | --- | --- |
| Overview | `/` | Scope filters, site/circuit summaries, ranking, status indicators, charts, tables, detail links |
| Gateway | `/gateway/{gateway}?site_id={site}` | Identity, health, WAN ports, peer paths, breadcrumbs, scope preservation |
| WAN port | `/port/{site}/{encoded-port}?gateway_id={gateway}` | Encoded identity, utilization, receive/transmit bandwidth, capacity, history |
| VPN peer | `/vpn/{site}/{encoded-peer}` | Peer identity, loss, latency, jitter, tunnel details, missing history |

The [source and destination discovery](discovery.md) records 15 surface groups, static call paths, and SDK incompatibilities.
P01-P20 are seed rows. P21-P50 expand those rows across every reviewed static surface, including explicit unknowns and test gaps.
The inventory is complete only for the inspected static evidence. Runtime and visual acceptance remain unverified.

Destination routes may differ but must preserve tested equivalent identifiers and navigation.
The gateway identifier representation requires explicit source-to-destination mapping, not an assumed UUID/MAC substitution.

## Functional comparison

Cover metric units, precision, ordering, thresholds, window controls, filters, defaults, sorting, pagination, drilldowns, and exports if source evidence establishes them.
Also cover refresh, loading, empty, stale, error, denied-access, and unavailable-contract states.
Inventory source behavior before deciding which optional controls exist.
Every source TODO receives a separate desired-goal row, not a completed-feature row.

## Visual comparison

Review navigation structure, page hierarchy, KPI order, panel grouping, chart axes, legends, colors, labels, tables, spacing, and typography.
Record each intentional MistHelper adaptation with its reason and approval.
At 1440-by-1100, every required layout region must have a reviewed equivalent.
At destination narrow viewports, controls must remain reachable without overlapping text or hidden actions.
No pixel-difference threshold is defined until permissible source captures and a stable rendering baseline exist.

## Evidence safety

Do not copy proprietary code, screenshots, or fixtures without written rights.
Do not launch the source with live credentials, Snowflake, Redis, background workers, or public ports.
A future approved source preview must block external requests and collection and use independently authored data.
Source and destination runs must remain isolated.
Do not add a second product service to enable comparison.
Without permitted source runtime evidence, report descriptive comparison only and leave runtime visual parity blocked.

## Data and transport gates

Before each new live feature, record exact supported SDK method and explicit arguments.
Verify response units, timestamps, pagination, scope, rate limits, and 4xx/5xx behavior with independent test inputs.
Do not use generic insights or peer search as proof of explicit peer time-series support.
Record scope and timestamp limitations of current snapshots.
No new direct HTTP transport is authorized.

### Verified organization-stat fields

The installed SDK exposes `searchOrgSwOrGwPorts` with `device_type`, `mac`, `port_id`, `limit`, and `search_after`.
The `stats_gateway_port` schema defines scalar `loss`, `jitter`, and `latency` fields without units or metric timestamps.
Store those port values as raw poll samples and do not assign units.

The installed SDK exposes `searchOrgPeerPathStats` with gateway, site, type, time-bound, duration, limit, and cursor filters.
It does not expose a peer-port filter, so filter the returned bounded rows by the full peer identity.
The `vpn_peer_stat` schema defines scalar `loss` in percent and `latency` and `jitter` in milliseconds.
The schema bounds MOS from zero through five and gives `last_seen` as peer observation time.
These bounds do not define quality categories, metric sample time, or historical aggregation.
Store each selected peer scalar at poll time and keep `last_seen` separate.
Reject duplicate rows for one full peer identity because the schema gives no metric timestamp.
These contracts support current scalar samples, not source time series, complete history, or backfill.

### Verified gateway insight fields

The installed SDK exposes `getSiteInsightMetricsForGateway(mist_session, site_id, device_id, metrics, ...)`.
Request `rx_bps` and `tx_bps` in separate calls.
The OpenAPI response field `response_device_metrics.results` contains string or integer values.
The `rt` field contains string timestamps aligned by array index with `results`.
The schema does not require `rt`, so a missing or misaligned timestamp cannot become a historical sample.
Preserve the API timestamp as sample time and keep collection time as separate poll metadata.
Do not infer sample values, units, or coverage when the response omits required evidence.

### Existing refresh and isolation prerequisites

The existing live service reads the server-selected organization and admitted API session.
The request ledger accounts for each send against the authentication fingerprint and organization.
Its configured ceiling is 5,000 requests per hour, and a configured Redis outage fails closed.
Each snapshot endpoint reads at most five pages of 100 rows and marks partial coverage.
The refresh lease lasts 300 seconds, and the snapshot cache expires after 3,600 seconds.
These limits describe the current integration and do not prove complete inventory or justify a new retry policy.
Keep synthetic previews separate from collection, live storage, and live status.

## Browser acceptance

Complete overview to gateway to port to gateway to peer to overview.
Test direct links, browser back, query preservation, invalid scope, empty data, stale data, and error states.
Assert stable selectors for navigation, filters, cards, charts, tables, and detail links.
Synthetic tests assert zero collection calls and no live-store writes.
Mocked live tests assert authorization before collection and bounded refresh across concurrent users.
Retain destination screenshots and traces with secret redaction.
Every required comparison row must reference a passing assertion or remain explicitly blocked.

## Seed inventory

This table completes the static inventory tasks T003 and T007-T010 for the reviewed documents, pages, and tests.
It does not establish runtime acceptance or source visual approval.
All source references below use revision `2d1c2199fa1e31c129ef1e051c5389349a207785`.
Earlier destination observations use product revision `1a408c9511d8b32662d201068f2f54196f643450`.
Documented means described by source documentation, not runtime-verified.
Goal means requested in ProjectGoals, not proven completed behavior.
Each row still needs exact source locations, destination assertions, and a reviewer decision.

| Row | Source reference and classification | Destination evidence | Remaining acceptance task |
| --- | --- | --- | --- |
| P01 | docs/screens.md: overview, documented | `overview.html`, `wan-overview` | T007, T011 |
| P02 | docs/screens.md: gateway health/ports/peers, documented | `gateway.html`, `wan-gateway` | T008, T011 |
| P03 | docs/screens.md: encoded port and bandwidth, documented | `port.html`, `wan-port` | T009, T011 |
| P04 | docs/screens.md: encoded peer and tunnel details, documented | `vpn_peer.html`, `wan-peer` | T010, T011 |
| P05 | ProjectGoals.md: current utilization and configurable top-N, goal | `wan-top-congested-circuits` exists in offline overview | T013-T014, T019-T022 |
| P06 | ProjectGoals.md: thresholds and overrides, goal | Threshold observation and duration sections exist in `live.html` | T013-T016 |
| P07 | ProjectGoals.md: continuous/cumulative duration, goal | `wan-live-congestion-duration` is sample-based | T015-T016 |
| P08 | ProjectGoals.md: status/flaps/availability, goal | `wan-live-link-event-summary` exists; coverage unverified | T017-T018 |
| P09 | ProjectGoals.md: primary/secondary failure, goal | Role mapping and comparison unverified | T019-T022 |
| P10 | ProjectGoals.md: loss/latency/jitter statistics, goal | Peer scalar units are verified; poll-time samples do not prove source time-series parity | T023-T024 |
| P11 | TODO.md: peer and port time-series collection; method bodies also exist but remain unverified | Supported organization-stat filters and response fields are verified; no source time-series or peer-port query exists | T003-T004, T023 |
| P12 | ProjectGoals.md: SLE health scores and trends, goal | Source-to-destination field/score mapping unverified | T025-T026 |
| P13 | ProjectGoals.md: SLE impacts and classifiers, goal | Required drilldown chain unverified | T025-T026 |
| P14 | ProjectGoals.md: region/site/circuit/hour dimensions, goal | Region/role effective-time mapping unverified | T013, T027-T028 |
| P15 | ProjectGoals.md: 3h/12h/24h and calendar windows, goal | `wan-calendar-summaries` exists; requested coverage unverified | T027-T028 |
| P16 | ProjectGoals.md: 13-month history, goal | Retention/backfill/completeness unverified | T029-T030 |
| P17 | ProjectGoals.md: executive/engineering/SLE views, goal | Audience parity unverified | T031-T032 |
| P18 | ProjectGoals.md: exportable top-offender tables, goal | Export behavior unverified | T003, T031-T032 |
| P19 | ProjectGoals.md: region-to-site-to-circuit drilldown, goal | Complete navigation chain unverified | T007-T012, T031-T032 |
| P20 | docs/screens.md: synthetic captures at 1440-by-1100, documented | Destination synthetic pages exist; visual approval absent | T033-T036 |

For P01-P04, enumerate every control rather than using one page row as acceptance.
The detailed rows below use pinned documentation, active page definitions, source test names, and destination assertions.
They classify a visible source surface separately from a completed source behavior.
No source image, fixture, or code was copied.

## Detailed source-to-destination inventory

Source references use revision `2d1c2199fa1e31c129ef1e051c5389349a207785`.
Destination behavior uses the candidate source at `d7a706d71cf13661cf33e5b4a96ddafd79b6b67b`.
Destination test names identify independent synthetic or mocked assertions.
They do not establish source runtime behavior or visual parity.

| Row | Source evidence and classification | Visible item, action, metric, state, or transition | Destination selector and assertion | Decision |
| --- | --- | --- | --- | --- |
| P21 | D01, active overview code | Site health summary | `wan-overview-status`, `wan-overview-kpis`; offline route tests | Synthetic content only. Population and denominator remain unknown. |
| P22 | D01, active overview code | Gateway state, circuit summary, and failovers | `wan-overview-kpis`, `wan-top-congested-circuits`; live state tests | Live snapshots exist. Historical failover behavior remains unverified. |
| P23 | D01, D03, active overview code | Current alerts and degraded sites | `wan-active-alerts`, `wan-sle-degraded-sites`; offline route tests | Selectors exist in synthetic preview. Scope and alert rules remain unknown. |
| P24 | D02, active overview code | Ranked table with rank, site, port, speed, utilization, and status | `wan-top-congested-circuits`, `wan-gateway-link`, `wan-port-link` | Destination renders a synthetic table and links. Ranking and precision are not accepted. |
| P25 | D02, active overview code | Ten-row pagination | No destination pagination selector or control | Not implemented. No live pagination behavior is claimed. |
| P26 | D03, active overview code | Alert and degraded-SLE tables | `wan-active-alerts`, `wan-sle-degraded-sites` | Synthetic panels exist. Live SLE data is not established. |
| P27 | D03, active overview code | SLE table sorting and filtering | No destination sorting or filtering control | Not implemented. Source scope and classifier rules remain unknown. |
| P28 | D04, active overview code | Region, utilization, trends, throughput, gateway bandwidth, and VPN quality charts | `wan-region-summary-chart`, `wan-utilization-distribution-chart`, `wan-overview-trends`, `wan-site-charts` | Synthetic charts exist. Source axes, units, series, and missing-history rules remain unverified. |
| P29 | D05, active overview code | Site selector | `wan-site-controls` contains a disabled synthetic selector. Live gateway form has `wan-live-gateway-site` text input. | A live site identifier input exists, but it does not match the source selector. |
| P30 | D05, active overview code | 6-hour, 12-hour, 24-hour, and 7-day range controls with a 24-hour default | `wan-site-controls` contains a disabled 24-hour synthetic value | Source ranges are documented. Live controls are not implemented. Keep the 3-hour goal separate. |
| P31 | D05, D15, active overview code | Overview auto-refresh and status interval | `wan-site-controls`; background worker tests | Source intervals are 60 and 10 seconds. Destination worker uses bounded 300-second refresh and 10-second lease retry. |
| P32 | D06, active route code | Region-to-site-to-circuit drilldown and breadcrumbs | `wan-gateway-link`, `wan-port-link`, `wan-peer-link`, `wan-back-link` | Gateway, port, and peer routes exist. Region and site list transitions do not. |
| P33 | D07, active overview code | SLE summary, histogram, and classifiers | `wan-sle-degraded-sites` only | No destination SLE detail route or verified data contract exists. |
| P34 | D07, active overview code | Impacted gateways, interfaces, applications, and peers | No destination impact-detail selector | Not implemented. SDK and field contracts remain unverified. |
| P35 | D08, active overview code | CSV export for congestion, alerts, and degraded SLE | No destination export control | Not implemented. Source callback presence does not prove a working download. |
| P36 | D09, active gateway page | Gateway ID, site, status, and last-seen time | `wan-gateway-health`, `wan-gateway-kpis` | Offline values are synthetic. Live field units and time meaning remain unverified. |
| P37 | D09, active gateway page | Port and peer counts, CPU, memory, and uptime | `wan-gateway-kpis`, `wan-port-table`, `wan-peer-table` | Source lists these fields. The destination does not show them or verify their units. |
| P38 | D10, active gateway page | WAN-port and VPN-peer tables and detail links | `wan-port-table`, `wan-peer-table`, `wan-port-link`, `wan-peer-link` | Synthetic navigation is tested. Full identity and source row coverage remain unverified. |
| P39 | D10, active gateway page | Gateway bandwidth and device-metric charts with 24-hour coverage | `wan-gateway-charts` | Synthetic charts exist. Source units and 24-hour completeness remain unknown. |
| P40 | D11, active port page | Port status and utilization gauge | `wan-port-kpis`, `wan-port-gauges` | Offline values are synthetic. The live scalar contract does not establish utilization units. |
| P41 | D11, active port page | Current statistics and port configuration | `wan-port-current-statistics`, `wan-port-configuration` | Synthetic panels exist. Capacity, role, provider, address, and MTU mappings remain unverified. |
| P42 | D11, active route code | Encoded interface path and gateway/site query scope | `/wan-performance/port/{site}/{encoded-port}`; `test_port_route_preserves_an_encoded_slash_and_bandwidth_units` | Encoded slash preservation and fixture scope have offline assertions. Source and live field parity remain open. |
| P43 | D12, active port page | Receive and transmit bandwidth history | `wan-port-charts` | Offline charts exist. The supported SDK does not provide the source historical method. |
| P44 | D12, active port page | Unicast, multicast, broadcast, drops, and CRC counters | `wan-port-packet-statistics`, `wan-port-error-counters`; destination-only `wan-calendar-summaries` | Synthetic panels exist. Counter semantics and any source equivalent for calendar summaries remain unknown. |
| P45 | D13, active peer page | Loss, latency, jitter, and MOS gauges and history | `wan-peer-kpis`, `wan-peer-gauges`, `wan-peer-charts` | Current scalar units and MOS bounds are documented. MOS quality categories and source history remain unknown. |
| P46 | D14, active peer page | Peer path identity, addresses, type, tunnel name, and MTU | `wan-peer-details` | Synthetic fields exist. The live response does not verify each source field. |
| P47 | D14, active peer page | Uptime, bytes, and packets | `wan-peer-statistics` | Synthetic fields exist. Live field contracts and counter semantics remain unknown. |
| P48 | D14, active route code | Peer route and tunnel-path identity | Live peer links include site, MAC, and path key. Offline peer route tests cover site and MAC. | Full path identity is retained in live scope. The source field mapping remains unverified. |
| P49 | `tests/test_detail_pages.py:217-366`, source test intent | Populated, missing, raising-provider, gateway lookup, duplicate-peer, and encoded-link cases | `test_wan_performance_offline.py`, `test_wan_performance_live.py` | Source tests were inspected, not run. Destination tests use independent data. |
| P50 | `tests/test_views.py:48-347`, source test intent | Ranking, availability ranking, chronic offenders, current alerts, and serialized fields | `test_wan_performance_live.py` and offline preview tests | Source tests were inspected, not run. Destination ranking and availability parity remain blocked. |

### Audience requirements for T031

These are goals in `ProjectGoals.md`, not proof of completed source behavior.
The destination selectors identify available preview content only.

| Audience | Source goal | Destination inventory | Decision |
| --- | --- | --- | --- |
| Executive | Trends, top offenders, and SLE health scores | `wan-overview-trends`, `wan-top-congested-circuits`, `wan-sle-degraded-sites` | Map the goal. Audience controls, approved rankings, and live SLE scores are absent. |
| Engineering | Live congestion and quality, circuit drilldown, availability, flaps, and chronic offenders | Live snapshot routes, `wan-port-link`, `wan-peer-link`, and `wan-calendar-summaries` | Current snapshots and navigation exist. Historical availability and chronic ranking remain unknown. |
| SLE health | Gateway, application, and WAN-link scores with impact analysis | `wan-sle-degraded-sites` | No verified score mapping, filters, or impact drilldown exists. |

### Descriptive layout inventory for T034

The source screen guide documents four synthetic routes and a 1440-by-1100 capture.
It names a Bootstrap DARKLY theme and disables the production CDN during capture.
Source captures were not opened, copied, or compared because written rights are absent.

| Subject | Pinned source evidence | Destination observation | Status |
| --- | --- | --- | --- |
| Page hierarchy | `docs/screens.md`, Overview, Gateway, WAN port, and VPN peer | Overview, gateway, port, and peer sections use stable page selectors | Descriptive mapping only. No visual approval exists. |
| Colors and type | `docs/screens.md`; source theme is Darkly | Page CSS defines dark panels, pink accents, cyan values, muted text, and a clamped heading size | Source style values and pixel comparison remain unknown. |
| Charts | D04, D10, D12, and D13 | SVG charts use grid lines, axes, series, reference lines, labels, and legends | Source axis and color equivalence is not established. |
| Tables | D02, D03, D08, D10, D11, and D12 | Destination panels use responsive tables. Source pagination, sorting, filters, and exports lack equivalent controls. | Behavior differences are listed above. |
| Responsive layout | Source capture documents 1440-by-1100 only | Destination CSS uses 1100, 760, and 480 pixel breakpoints | Source narrow-screen behavior is unknown. Destination tests cover 1440 and 390 pixels. |
| Keyboard and overlap | Source visual evidence is unavailable | Offline browser tests tab to links, activate them, check selectors, and reject overlapping regions | Destination behavior is tested. Source comparison remains blocked. |

### Shared refresh and Redis evidence for T037-T039

These bounds are observed in MistHelper code and tests.
They do not authorize a new request rate or prove source scheduling parity.

## Original-application exploration plan

The renewed request requires original-application execution, not only a static inventory.
Source runtime and capture rights remain unverified. Every row below is unexecuted.
Use independently authored data after rights approval and a verified outbound network block.
Record each observed result and retained evidence beside its comparison row.

| Surface | Required interactions and states | Existing implementation tasks |
| --- | --- | --- |
| Overview | Select every site and time range. Toggle refresh. Follow health, circuit, region, gateway, and alert links. Check empty and failed states. | T007, T011-T012, T021-T022 |
| Tables and reports | Sort and filter each column. Traverse first, last, and empty pages. Export each supported table. Verify selected scope and spreadsheet-safe text. | T019-T022, T031-T032 |
| Charts | Hover each series. Select and reset ranges. Toggle legends. Compare empty, partial, missing, and stale series without inferred coverage. | T013-T016, T023-T024, T027-T028 |
| Region and site | Traverse region, site, circuit, and breadcrumb links. Verify reverse navigation, selected time, and absent membership. | T012-T014, T027-T028 |
| Gateway | Inspect identity, CPU, memory, uptime, port and peer tables, bandwidth, and device charts. Follow every detail link. | T008, T011-T012, T021 |
| Encoded port | Inspect status, capacity, role, utilization, configuration, rates, packet counters, and errors. Test encoded slashes and invalid scope. | T009, T014-T022 |
| VPN peer | Inspect path identity, quality, MOS, tunnel details, counters, uptime, and history. Separate observed values from unavailable metric timestamps. | T010, T023-T024 |
| SLE | Inspect summaries, histograms, classifiers, impacted entities, and each detail transition. Verify scope, units, errors, and absent contracts. | T025-T026 |
| Accessibility | Traverse each control with Tab and activate it with Enter. Use browser Back and Forward. Repeat all three documented viewport sizes. | T034-T036, T040-T042 |
| Refresh and failures | Repeat refresh, induce read and store failures, verify stale labels, and stop all workers. Do not initialize production clients. | T037-T042 |

For each interaction, record the initial state, action, visible result, local request, error, and evidence path.
A visible button without a working callback is a failed or unavailable option.
Do not translate source defaults or fallback zeros into accepted measurement contracts.
Implement verified differences with failing independent tests through the existing task pairs.
Keep rights, data semantics, historical acceptance, and publication as separate decisions.

### Supported SLE gateway drilldown candidate

The installed SDK exposes `sites.sle.listSiteSleImpactedGateways`.
Its arguments are session, site ID, scope, scope ID, metric, optional start, end, duration, and classifier.
The bundled OpenAPI restricts this operation to `scope="site"`.
Use the site ID as scope ID and obtain metric names from `sites.sle.listSiteSlesMetrics`.
That catalog returns separate `supported` and `enabled` arrays.
Do not treat example metric names as enabled for every site.

An independent mocked SDK call verified the gateway URL and explicit start, end, and classifier forwarding.
It returned the mock response unchanged and made no network request.
This proves SDK request construction only, not application authorization, response validation, or error handling.

The impacted-gateway response includes gateway identity fields, degraded, total, duration, and pagination metadata.
Its example does not establish duration units, score normalization, historical completeness, or source-equivalent drilldown behavior.
The SDK signature provides no page or limit argument despite response pagination fields.
Do not claim complete results or implement guessed pagination arguments.
T025 can use this supported entry point for further field-contract verification.
T026 still requires approved interpretation, scoped response validation, failure tests, and source comparison before presentation wiring.

The separate `sites.stats.getSiteGatewayMetrics(session, site_id)` returns configuration-success and version-compliance scores.
It is not the historical bandwidth operation assumed by the source wrapper.
The absent `sites.insights.getSiteGatewayMetrics` symbol must not be replaced with this unrelated stats call.

| Behavior | Current MistHelper policy | Evidence |
| --- | --- | --- |
| Worker ownership | One organization key uses atomic `NX` acquisition and a 600-second lease. Renew and release scripts compare the owner token. | `test_background_refresh.py::test_worker_threads_follow_shared_organization_lease_protocol`, `test_worker_does_not_release_a_lease_after_ownership_changes` |
| Contention retry | A worker retries a denied lease after 10 seconds. A successful owner refreshes every 300 seconds. | `test_worker_retries_lease_acquisition_after_the_configured_wait`; constants in `background_refresh.py` |
| Refresh failure | The worker logs the failure and continues its bounded schedule. The test stops it after one failed refresh. | `test_worker_refresh_failure_stops_cleanly` |
| Optional worker | The portal starts the worker only when shared request admission and history are available. No local-lock fallback starts API collection. | `test_portal_starts_worker_with_shared_admission_and_history`, `test_portal_skips_worker_when_shared_admission_is_disabled` |
| Request admission | A rolling 5,000-request-per-hour limit is scoped to the authentication fingerprint and organization. Redis failure rejects the request. | `test_request_admission.py`; existing E8 evidence |
| Selected refresh lease | The organization-scoped lease lasts 300 seconds. Ownership and remaining TTL are checked before collection. | `test_refresh_store.py::test_only_one_org_refresh_wins`, `test_expired_or_replaced_lease_refuses_next_call` |
| Snapshot cache | Live snapshots use an organization key and a 3,600-second TTL. Synthetic or wrong-organization content is rejected. | `test_refresh_store.py::test_cache_keys_are_separate_and_preserve_provenance`, `test_synthetic_or_wrong_org_cannot_be_cached` |
| Bounded reads | Each snapshot endpoint reads at most five pages of 100 rows and marks partial coverage. | `snapshot_client.py`; partial-coverage unit tests |
| Stale and error states | Cached live pages show stale state. Redis, API, and missing-history failures do not become success-shaped empty data. | `test_wan_performance_live.py::test_all_live_journeys_read_cache_without_live_calls`, stale and failure cases |

No verified refresh-policy failure requires a production-code repair.
The tests above prove bounded ownership, retry, and failure behavior with mocks.
They do not use a production Redis store or a live Mist session.

## Required assertion matrix

| Scenario | Required assertion | Evidence destination |
| --- | --- | --- |
| Four-way navigation | Correct identity, query preservation, back navigation, and return path | Offline browser tests |
| Synthetic preview | Origin visible on every page, zero live calls, zero live-store writes | Offline unit and browser tests |
| Authorized live mode | Authorization precedes collection; site/gateway/port/peer scope matches | Live service and browser tests |
| Wrong scope or identifier | Denial or explicit input error with zero collection | Live browser tests |
| Empty or stale records | Visible state, absent-value reason, no invented metrics | Both browser modes |
| Interval gaps | Unknown time remains unknown; no fabricated duration or uptime | Domain and history tests |
| API 4xx/5xx/429 | Explicit errors and bounded retry/admission behavior | Collection tests |
| Store or optional cache outage | No success-shaped fallback; unrelated portal remains usable | Integration and browser tests |
| Visual hierarchy | Reviewed panels, labels, chart semantics, ordering, and keyboard behavior | Destination browser evidence |
| Exportable rankings | Approved scope, units, ordering, and missing-value treatment | Audience browser tests |

Each execution record must identify assertion IDs, result, source row, destination revision, and evidence path.
An unavailable contract is a recorded blocker, not a passing substitute for full functionality.
