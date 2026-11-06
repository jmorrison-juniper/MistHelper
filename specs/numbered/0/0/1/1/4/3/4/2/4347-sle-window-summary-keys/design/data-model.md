# Data Model: Stable SLE summary window keys

## Overview

This feature changes the identity of persisted records for two existing
endpoint responses. It adds no public entity, API, database migration
interface, or new response fields. The response payload remains intact; only
the exact stable identity determines which new keyed record a later export
replaces.

## Histogram Window

One histogram distribution for a selected site/scope/scope identifier/metric
and the actual time boundaries returned by `getSiteSleHistogram`.

| Identity field | Source | Validation |
|---|---|---|
| `site_id` | Selected request path identifier | Required nonempty string; selected value is authoritative. |
| `scope` | Selected request path identifier | Required nonempty string; selected value is authoritative. |
| `scope_id` | Selected request path identifier | Required nonempty string; selected value is authoritative. |
| `metric` | Selected request path identifier | Required nonempty string; selected value is authoritative. |
| `start` | Response | Required finite, nonnegative numeric boundary. |
| `end` | Response | Required finite, nonnegative numeric boundary; must not precede `start`. |

**Exact identity tuple**: `(site_id, scope, scope_id, metric, start, end)`.

The response's `data`, `x_label`, and `y_label` remain content. The response
`metric` cannot override the selected path `metric`.

## Impact-Summary Window

One impact summary for the selected site/scope/scope identifier/metric and the
actual returned window, further distinguished by the response's classifier and
failure strings.

| Identity field | Source | Validation |
|---|---|---|
| `site_id` | Selected request path identifier | Required nonempty string; selected value is authoritative. |
| `scope` | Selected request path identifier | Required nonempty string; selected value is authoritative. |
| `scope_id` | Selected request path identifier | Required nonempty string; selected value is authoritative. |
| `metric` | Selected request path identifier | Required nonempty string; selected value is authoritative. |
| `classifier` | Response | Required string; `""` is valid and preserved exactly. |
| `failure` | Response | Required string; `""` is valid and preserved exactly. |
| `start` | Response | Required finite, nonnegative numeric boundary. |
| `end` | Response | Required finite, nonnegative numeric boundary; must not precede `start`. |

**Exact identity tuple**:
`(site_id, scope, scope_id, metric, classifier, failure, start, end)`.

The response grouping arrays `ap`, `wlan`, `device_os`, `device_type`, and
`band` remain content, as do the other response values. No grouping value,
label, measurement, or generated identifier is an identity field.

## Relationships and Persistence

- One endpoint export response may contain one object or multiple normalized
  rows. Every row must have a complete identity before any row is persisted.
- Rows with different values in any exact identity field are separate keyed
  records.
- Rows with the same exact identity but updated content replace the same new
  keyed record.
- A first keyed export may coexist with any number of matching legacy records.
- Legacy SQLite rows retain their existing identifiers and values. Legacy
  ArangoDB documents retain their UUID `_key` values and content.
- There is no historical backfill, migration, deletion, re-keying, or
  deduplication. The identity marker used internally by the existing SQLite
  writer and the deterministic Arango key are derived from the exact tuples;
  neither adds a source identity field.
- Keep each endpoint's existing `auto_increment_with_unique` router type so
  ArangoDB remains the only polyglot backend for these endpoints. Do not switch
  them to `composite_pk`, which would add RedisJSON writes. The SQLite SLE
  identity path must use keyed replacement rather than the auto-increment
  strategy's legacy table-clear fallback.

## State Transitions

| State before export | Export result | Required state after export |
|---|---|---|
| No record for the identity | Valid response | Add one keyed record. |
| Legacy row/document(s) only | Valid matching response | Preserve all legacy records and add one keyed record. |
| One keyed record exists | Valid same-identity response | Replace only that keyed record with latest content. |
| One keyed record exists | Valid changed identity | Preserve the prior keyed record and add a separate keyed record. |
| Any store state | Empty response | Preserve existing no-data behavior; make no write. |
| Any store state | Any missing/invalid identity in the batch | Report validation failure and make no partial write. |

## Key Construction Constraints

- Use the existing SLE deterministic key construction and numeric-boundary
  normalization.
- Hash/encode the ordered exact tuple unambiguously; do not concatenate values
  with an ambiguous separator.
- Treat Boolean boundaries as invalid even though Python classifies `bool` as
  an integer subtype.
- Require the presence of `classifier` and `failure` independently of their
  values; empty strings are valid only for those two fields.
- Do not infer identity from optional query values because the exporter does
  not send them.
