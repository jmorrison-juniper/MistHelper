# Source comparison and end-to-end contract

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

## Browser acceptance

Complete overview to gateway to port to gateway to peer to overview.
Test direct links, browser back, query preservation, invalid scope, empty data, stale data, and error states.
Assert stable selectors for navigation, filters, cards, charts, tables, and detail links.
Synthetic tests assert zero collection calls and no live-store writes.
Mocked live tests assert authorization before collection and bounded refresh across concurrent users.
Retain destination screenshots and traces with secret redaction.
Every required comparison row must reference a passing assertion or remain explicitly blocked.
