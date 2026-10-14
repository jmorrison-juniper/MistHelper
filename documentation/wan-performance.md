# WAN Performance preview

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

Live metrics, durable history, cache refresh, and shared request admission remain unavailable.
The source documentation and implementations disagree about utilization units and missing availability.
The configured export writer does not establish a WAN history query or retention contract.
The current API quota cache is process-local.
Live integration must resolve these contracts before it starts requests.

The preview adds no database, Snowflake connection, service, Compose group, public port, or credential store.
PR #4205 has a separate, unmerged WAN implementation.
This preview does not use that implementation.
