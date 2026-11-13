# Source and destination discovery

**Reviewed**: 2026-11-05

**Purpose**: Give implementers concrete carryover evidence without importing source code or assets.

## Evidence boundaries

Source revision: `2d1c2199fa1e31c129ef1e051c5389349a207785`.
The [pinned source tree](https://github.com/jmorrison-juniper/MistWANPerformance/tree/2d1c2199fa1e31c129ef1e051c5389349a207785)
is the reference for source paths and line numbers.
Destination product revision: `1a408c9511d8b32662d201068f2f54196f643450`.
Document-only commits do not change that product baseline.
This review uses GitHub read-only source inspection and local destination inspection.
It does not run the source, contact Mist, connect stores, or reproduce images.

Implemented source code means a body or callback exists.
It does not mean its dependencies work or that a browser journey passes.
Source test names identify coverage intent, not results from an executed test run.
All runtime, visual, and live-data acceptance remains unverified.

## Active source page routing

Source references use `src/dashboard/app.py` unless another file is named.
`pages/` and `data_provider.py` paths are relative to source `src/dashboard/`.
Destination package paths below are relative to `src/interfaces/wan_performance/`, unless they begin with `web_portal/`.

| Evidence | Finding | Migration consequence |
| --- | --- | --- |
| Lines 393-413, 2601-2642 | The URL callback selects overview, gateway, port, and peer pages | Test routing and direct links, not page classes alone |
| Lines 97-100, 4008-4048 | Detail routes use gateway, port, and VPN page builders | Inventory those builders and their callbacks |
| Lines 2641-2642 | The default route invokes the app's overview builder | Do not substitute the separate OverviewPage layout for active-route evidence |
| Lines 2620-2632 | Gateway context uses site query values; port context uses gateway query values | Preserve complete scope across links |
| Lines 2630, 2638 | Port and peer path values are decoded | Test encoded slashes, colons, and exactly-once decoding |
| Lines 3167-3344 | Detail callbacks use shared data-shaping functions | Follow shaping and provider dependencies before claiming field support |

Do not count unused or duplicate page definitions as additional completed journeys.
Do not reproduce the source's default routing behavior without testing MistHelper's existing route policy.

## Source UI and behavior inventory

These are source-defined surfaces. Destination completeness remains a separate decision.

| ID | Source location | Carryover subject | Required verification |
| --- | --- | --- | --- |
| D01 | app.py:415-1238, 2688-2814 | Overview site health, gateway state, circuit summary, failovers, and alerts | Define each population, denominator, and missing-data state |
| D02 | app.py:731-804 | Congested circuit table with rank, site, port link, speed, utilization, and status; ten-row pages | Ranking, precision, navigation, and empty rows |
| D03 | app.py:825-892 | Alert and degraded-SLE sections; SLE table sorting and filtering | Scope, table behavior, classifier meaning, and access |
| D04 | app.py:965-1217 | Region, utilization, trends, throughput, gateway bandwidth, and VPN quality charts | Axes, units, series, selection, and missing history |
| D05 | app.py:1090-1149 | Site selector, 6h/12h/24h/7-day selector, default 24h, time-series auto-refresh initially off | Distinguish these source UI ranges from the 3h project goal |
| D06 | app.py:1258-1492, 3348-3428 | Region/site/circuit drilldown and breadcrumbs | Preserve selected scope and reverse navigation |
| D07 | app.py:1494-2476, 3437-3473 | Site SLE detail, summary, histogram, classifiers, impacted gateways/interfaces, and peers | Verify actual SDK data and all drilldown transitions |
| D08 | app.py:3482-3561 | CSV handlers for congestion, alerts, and degraded SLE | Column contract, selected scope, empty export, and safe spreadsheet content |
| D09 | pages/gateway.py:117-188 | Gateway identity, site, status, last seen, ports up/down, peers, CPU, memory, uptime | Verify field source and units |
| D10 | pages/gateway.py:190-342 | WAN-port and VPN-peer tables; gateway bandwidth and device-metric charts | Links, identity, all series, and 24-hour chart coverage |
| D11 | pages/port.py:195-340 | Port status, utilization gauge, current statistics, and configuration | Capacity, role, provider, addresses, MTU, and unknown values |
| D12 | pages/port.py:342-468 | Bandwidth history, packet statistics, and errors | Receive/transmit totals, unicast/multicast/broadcast, drops, CRC, and counter meaning |
| D13 | pages/vpn_peer.py:205-313 | Loss, latency, jitter, and MOS gauges plus quality history | MOS is a separate carryover subject, not implied by the three other metrics |
| D14 | pages/vpn_peer.py:315-417; pages/detail_data.py:593-648 | Path identity, addresses, type, tunnel name, MTU, uptime, bytes, and packets | Preserve peer-path discrimination and verify missing-field display |
| D15 | app.py:57, 551-557; page interval controls | App overview refresh is 60 seconds; status interval is 10 seconds | These are source behavior, not authorization for MistHelper request rates |

The source application selects Bootstrap's DARKLY theme at app.py:105.
This identifies a visual dependency, not permission to copy source assets or an instruction to replace MistHelper's global theme.
T034 must compare page-local visual hierarchy within the host portal.

Region and site export buttons exist at app.py:1271 and 1328.
Static callback inspection found only the three D08 export handlers in this module.
The region/site buttons are not proven functioning downloads.
Do not classify a visible button as implemented behavior without tracing its handler.

Packet, error, and byte counters need reset and timestamp semantics.
Do not turn cumulative counters into rates without a verified sampling interval.
Do not infer MOS from latency, loss, or jitter unless an approved calculation contract establishes it.
Do not adopt source thresholds or default zeros merely because they render a gauge.

D01-D08 and D15 inform T007, T011-T012, T031-T032, T034, and T037.
D09-D10 inform T008. D11-D12 inform T009. D13-D14 inform T010 and T023-T024.
All rows need destination assertions under T011, T021, T026, T032, T035, or T040 before acceptance.
The inventory does not declare any field accepted or authorize adding an unsupported metric.

## Source collection and historical dependencies

The `api/mist_client.py` references below are relative to the pinned source tree's `src/` directory, not MistHelper.

| Evidence | Observed behavior | Acceptance consequence |
| --- | --- | --- |
| src/main.py:73-127 | CLI collection and aggregation contain TODO bodies | Do not accept CLI orchestration as working collection |
| data_provider.py:1426-1490 | Port history reads cache, then invokes a source API method, then can return empty data | Trace the called SDK symbol and distinguish failure from no history |
| data_provider.py:1492-1549 | Peer history follows a similar provider path | Provider presence does not establish historical peer samples |
| api/mist_client.py:1197-1290 | A gateway history method body exists and calls `getSiteGatewayMetrics` | The installed destination SDK lacks that symbol |
| api/mist_client.py:1292-1394 | A peer history body calls device insights with peer filter arguments | Installed method signature does not accept those peer arguments |
| api/mist_client.py:1237-1238 | Source derives a device UUID from a MAC | Preserve destination discovery of the actual UUID, not this derivation |
| pages/detail_data.py:465-531, 593-646 | Several absent metrics become zeros; broad failures become empty page data | Preserve layout intent, but retain explicit missing/error behavior in MistHelper |

The earlier TODO classification is incomplete.
There are source method bodies, not only TODOs, at the same pinned revision.
Their SDK incompatibilities prevent a claim that they provide working history.
Record this as implemented-but-unverified source behavior.
Do not implement guessed replacement endpoints or reproduce source fallback behavior.

## Installed SDK compatibility evidence

Local inspection used `mistapi` 0.64.1 without creating a session or making a request.
Signature inspection establishes callable names and arguments only.
It does not prove a metric exists or that returned fields have the required meaning.

| SDK surface | Verified signature facts | Remaining evidence |
| --- | --- | --- |
| sites.insights.getSiteGatewayMetrics | Symbol absent | Source port-history call is not portable as written |
| sites.insights.getSiteInsightMetricsForGateway | Requires site ID, device ID, and metrics; interval is a string | Supported metric catalog, units, identity, and sample shape |
| sites.insights.getSiteInsightMetricsForDevice | Requires site ID, metric, device MAC; no peer_mac or peer_port_id arguments | Do not forward source peer filters; prove a supported alternative or remain blocked |
| orgs.stats.searchOrgPeerPathStats | Supports org, gateway MAC, site, type, bounds/duration, limit, and search_after; no peer-port filter | Timestamp semantics and historical completeness |
| orgs.stats.searchOrgSwOrGwPorts | Supports org, device type, gateway MAC, port ID, limit, and search_after | Snapshot coverage and scoped identity |
| sites.sle summary/histogram/threshold | Require site, scope, scope ID, and metric; summary/histogram have time bounds but no interval argument | Discover supported metrics and response interval/score meaning |
| sites.sle impact summary/gateways/interfaces | Require scoped identity and metric; support classifier and time bounds | Classifier values, entity links, score units, and completeness |

The inspected SLE functions are `getSiteSleSummary`, `getSiteSleHistogram`, `getSiteSleThreshold`,
`getSiteSleImpactSummary`, `listSiteSleImpactedGateways`, and `listSiteSleImpactedInterfaces`.
Do not pass source generic aggregation arguments into functions that do not declare them.
Recheck against the locked environment before implementation.

## Organization-stat response schemas

The bundled `stats_gateway_port` schema defines scalar `loss`, `jitter`, and `latency` fields.
It describes them as last-sampled values but does not define their units or a metric timestamp.
Keep these values as raw poll samples and do not assign units.

The bundled `vpn_peer_stat` schema defines scalar `loss`, `latency`, `jitter`, and `mos` fields.
It defines loss in percent and latency and jitter in milliseconds.
It describes MOS as a quality measure without a scale.
Its `last_seen` field uses epoch seconds and describes peer observation time, not metric sample time.
Do not treat these scalar fields as a peer time series or as historical backfill.

## Existing MistHelper integration facts

These are implementation observations, not end-to-end acceptance.

| Destination location | Current behavior | Required follow-through |
| --- | --- | --- |
| web_portal/app.py:187-222 | WAN blueprint registers in the existing Flask application | Preserve other blueprints and ownership handoffs |
| web_portal/templates/base.html | Navigation targets the live overview behind WAN navigation configuration | Test discoverability and intentional offline/live separation |
| presentation/routes.py: overview and detail routes | Synthetic pages use a fixed preview provider and scoped identity checks | Verify no live client or store writes across all pages |
| presentation/live_routes.py:LivePages.service | Reads server-selected organization and existing API session; requires admitted transport | Verify actual portal access middleware and unauthorized behavior |
| presentation/live_routes.py:LivePages.render | Reads cached data without starting collection | Test explicit refresh separately from GET navigation |
| integration/history_repository.py:HistorySelection.open | SQLite selection reuses configured database path; csv selection chooses configured ArangoDB | Do not assume csv means a new CSV history store |
| domain/calendar.py:CalendarWindow | Implements a 13-calendar-month query range; maximum history bound is 397 days | This does not prove retention, backfill, or complete 13-month measurements |
| domain/calendar.py:CalendarPeriod | Contains 3h/12h/24h and daily/weekly/monthly window calculations | Verify UI exposure and sample weighting independently |
| integration/refresh_store.py | Org refresh lease uses 300 seconds; snapshot TTL uses 3600 seconds | Test multiworker ownership, expiry, failure, and stale display |
| collection/request_admission.py:RequestLedger | Rolling request limit is 5000/hour per authentication fingerprint and org; ledger TTL is 3601 seconds | Verify coverage across shared sessions and retry attempts |
| collection/snapshot_client.py:SnapshotClient | Snapshot reads at most five 100-row pages per endpoint; partial coverage is explicit | Do not present bounded pages as complete organization inventory |

Existing cache keys use `misthelper:wan:v1:refresh:{org_id}` and `misthelper:wan:v1:snapshot:{org_id}`.
The shared admission ledger uses `misthelper:api:v1:requests:{fingerprint}` and `misthelper:api:v1:org:{org_id}`.
These are inspected existing keys, not proposed or newly approved cache contracts.
Do not record real fingerprint values or credentials.

The current integration target is `web_portal/`, the existing Flask portal.
This review does not authorize moving the feature into the separate npm `ops-portal/` frontend.
Any change of portal target needs a separate explicit decision before implementation.

## Source test evidence

`tests/test_detail_pages.py:217-366` defines populated, missing, and raising-provider detail tests.
It also tests gateway ID/MAC lookup, unknown gateway handling, duplicate peers, encoded links, and unique component IDs.
`tests/test_views.py:48-347` defines ranking, availability ranking, chronic offenders, current-state alerts, and serialized fields.
These tests were inspected, not executed.
No source fixtures or expected payloads were copied.
Destination tests must use independently authored data and verify the actual accepted contracts.

## Implementation readiness packet

Before a developer starts a carryover item, attach:

1. A source location, active call path, and completed/goal/unverified classification.
2. The destination route, selector, identity, and exact changed-file ownership.
3. Verified SDK signature, units, sample timestamp, error behavior, and request budget.
4. An independent expected result and failing unit, integration, and browser assertions.
5. Approved visual evidence, deviations, validation results, and remaining acceptance blockers.

Pending discovery includes full layout order and visual style values, exact CSV columns and scope,
source worker scheduling, historical schema/retention, SDK field catalogs, and portal authorization middleware.
None of these subjects is resolved by the inventory alone.
