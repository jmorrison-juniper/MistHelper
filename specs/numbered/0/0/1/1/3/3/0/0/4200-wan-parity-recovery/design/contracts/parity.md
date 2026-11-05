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

## Seed inventory

This table starts the exhaustive inventory. It does not complete T003 or T007-T010.
All source references below use revision `2d1c2199fa1e31c129ef1e051c5389349a207785`.
Destination observations use product revision `1a408c9511d8b32662d201068f2f54196f643450`.
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
| P10 | ProjectGoals.md: loss/latency/jitter statistics, goal | Current peer and history controls exist; sample contract unverified | T023-T024 |
| P11 | TODO.md: peer and port time-series collection, incomplete source work | Generic insights do not establish source TODO completion | T003-T004, T023 |
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
Inspect source README, page definitions, tests, and operational documentation read-only to determine completed behavior.
Source imagery is not imported. Source fixture data is not reused.

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
