# Data Model: Mist WAN Performance

All fields below are proposed destination contracts.
They do not assert source Snowflake table names or confirmed API fields.
T002 and T006 must record exact mappings before implementation.

## Context and Identity

| Entity | Identity | Important fields | Validation |
| --- | --- | --- | --- |
| Site | Organization ID and site ID | Site name, region when available | Valid UUID and organization membership |
| Gateway | Organization, site, and gateway identity | Source gateway ID, confirmed device UUID when present, name, health | Preserve source MAC-like ID without inventing a UUID |
| Circuit | Organization, site, gateway, and canonical port name | Capacity, role, active state | Membership, bounded name, valid encoding |
| Peer path | Organization, site, gateway, port, peer MAC, and stable tunnel-path identity | Tunnel state and peer label | Canonical MAC and proven tunnel identity |

The source gateway route example uses `aabbccddeeff`.
A device UUID mapping must be established from verified inventory, not string conversion.
The source port example is `ge-0/0/1`. The peer example is `11:22:33:44:55:66`.
Store canonical identities and encode them only when constructing links.
Never merge peer paths based on a display label.
If no stable tunnel identity exists, stop the mapping investigation rather than inventing a key.

## Hourly Measurement

Natural identity combines organization, site, gateway, circuit or peer-path identity, and `hour_start_utc`.
Keep circuit facts and peer-path facts distinct.
Use an upsert under a unique constraint or an equivalent unique document key.

| Field group | Proposed fields | Rule |
| --- | --- | --- |
| Time | `hour_start_utc`, `collected_at_utc`, `source_window_start_utc`, `source_window_end_utc` | ISO 8601 UTC. Hour intervals are half-open |
| Bandwidth | Receive/transmit rate, configured capacity, utilization | Explicit compatible units and source interval |
| Status | Valid up duration, valid down duration, transitions | Unknown duration remains unknown |
| Quality | Packet loss, latency, jitter, path quality | Finite values with units and sample counts |
| Provenance | Live or synthetic origin, mapping version, coverage, missing reason | Synthetic records never enter live storage |

Missing, unsupported, and invalid values use a null value with a reason.
Zero is valid only when the source confirms zero.
Counter reset or zero capacity makes derived utilization unavailable.
Current snapshots must not become historical hour totals without a verified historical interval.

## Period Summary

| Field | Rule |
| --- | --- |
| Period start and end | UTC half-open daily, weekly, or monthly boundaries |
| Expected and observed coverage | Record valid durations and sample counts, not only row counts |
| Metric values | Use approved per-metric calculation and units |
| Threshold durations | Keep continuous and cumulative durations separate when completed behavior requires them |
| Calculation version | Change when an approved formula changes |

Compute summaries from canonical facts or versioned materializations in the same selected application database.
Do not average existing averages without their source weights.
Percentiles require original samples or an approved documented representation.
Missing hours break continuous runs. They do not count as healthy hours.
T006 determines weekly boundaries and partial-period semantics from completed behavior.

## Durable Storage Mapping

| Source concept | Proposed destination | Required investigation |
| --- | --- | --- |
| Snowflake dimensions | Entities in the selected current MistHelper application database | Actual field and relationship contracts |
| Hourly facts | Uniquely keyed records in that same database | Units, temporal coverage, update rules |
| Daily, weekly, monthly queries | Queries or versioned summaries in that same database | Completed behavior, aggregation parity |
| Redis historical cache | Optional expiring copies of durable records | Source key and TTL behavior |

Use feature-owned tables in the existing SQLite file or collections in the existing ArangoDB database.
Names and migrations remain design proposals until T005 and T006 finish.
Do not create both implementations as concurrently authoritative stores.
Use the active configured mode and report unsupported CSV-only history explicitly.
Proposed durable coverage is at least 31 days when storage is enabled.
Approve retention and storage capacity in T006 before release.
Cache eviction never deletes the authoritative records.

## Refresh and Cache State

Refresh identity is organization plus refresh class.
Store owner token, lease expiry, next due time, last completion, request count, cursor, and failure reason.
Transactions or compare-and-swap operations must prevent two owners from claiming the same work.
Commit facts before publishing a fresh cache view.
Keep the prior successful timestamp when a refresh fails.

Cache payloads use versioned JSON with UTC timestamps, explicit units, finite values, and data-state labels.
No pickle, credentials, or arbitrary executable payloads are permitted.
The cache and lease contract is in [wan-performance.md](contracts/wan-performance.md).

State transitions are `unavailable -> fresh -> stale`.
A failed refresh changes fresh records to stale only when the freshness interval expires.
Synthetic mode remains synthetic and cannot transition into live mode through a refresh.
A storage failure records a failure state, not a successful empty history.
