# Phase 1 Data Model: getMspSle

**Feature**: `587-mist-get-msp-sle`
**Date**: 2026-06-29
**Source schema**: `documentation/api/msps/GET_msps_msp_id_insights_metric.md` (200
response)

## Entities

### Entity 1: `MspSleAggregate`

Represents one SLE aggregate row at MSP scope for a single
`(msp_id, metric, time-window, interval)` combination. The response body is a single
object (not an array); MistHelper persists it as exactly one row per invocation.

| Field           | Type    | Source                  | Nullable | Notes                                                                                                                              |
|-----------------|---------|-------------------------|----------|------------------------------------------------------------------------------------------------------------------------------------|
| `msp_id`        | TEXT    | path parameter          | NO       | Composite PK part 1. Injected into the row by MistHelper before write -- the API response body does not echo this value.            |
| `metric`        | TEXT    | path parameter          | NO       | Composite PK part 2. Injected by MistHelper. The SLE metric name (e.g. `wifi-connectivity`, `wan-link-health`).                     |
| `start`         | INTEGER | response.start          | NO       | Composite PK part 3. Epoch seconds (int32). Required in upstream schema; always present in 200 response.                            |
| `end`           | INTEGER | response.end            | NO       | Composite PK part 4. Epoch seconds (int32). Required upstream.                                                                     |
| `interval`      | INTEGER | response.interval       | NO       | Composite PK part 5. Aggregation interval in seconds (int32). Required upstream.                                                   |
| `limit`         | INTEGER | response.limit          | YES      | Server-applied result-set cap. Optional in schema; logged when present.                                                            |
| `results_json`  | TEXT    | response.results        | YES      | Heterogeneous array (numbers OR objects, varies by metric) serialized to a single JSON string. May be empty (`[]`) for sparse data. |
| `sle_filter`    | TEXT    | query param `sle`       | YES      | Echo of the optional `sle` query parameter the user supplied; preserved for audit / re-query reproducibility.                       |
| `retrieved_at`  | TEXT    | MistHelper              | NO       | ISO-8601 UTC timestamp injected by `DataExporter.write_with_format_selection()` for audit. Standard column added to every export.   |

**Primary Key**: `(msp_id, metric, start, end, interval)` -- composite, all five NOT
NULL.

**Foreign Keys**: None enforced at the SQLite layer (MistHelper does not maintain
referential integrity across tables -- each endpoint table is independent).
Conceptually `msp_id` references a row in a hypothetical future `msps` table and
`metric` references a row in a hypothetical `insight_metrics` lookup table; both
relationships are implicit.

### Entity 2: `MspSleResultItem` (logical, not materialized)

Each element of the `results_json` array is one aggregation bucket for the
configured `interval`. The shape is metric-dependent:

- For scalar metrics (e.g. `ap-count`, `bytes`): a bare JSON number.
- For composite metrics (e.g. `wifi-connectivity`, `wan-link-health`): a nested JSON
  object with metric-specific keys (e.g. `numerator`, `denominator`,
  `total_clients`, `failed_clients`).

**Materialization decision**: Not exploded into rows in this spec. The variable
shape per metric would force either per-metric column divergence or a sparse
polymorphic schema; a single `results_json` column keeps every metric
round-trippable today. A future spec can add a per-metric exploder once the metric
set stabilizes.

### State Transitions

**N/A -- read-only endpoint.** The row is fully replaced on every successful
invocation via `INSERT OR REPLACE`. There is no state machine to model. The
underlying aggregate may shift slightly for an in-progress window (the current day
is still accumulating), so a user re-running the menu item against a still-open
window produces a refreshed row with the same composite key. Once the window is
closed upstream (e.g. yesterday at 23:59 UTC for a daily aggregate), the row is
effectively immutable.

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS msp_sle (
    msp_id       TEXT    NOT NULL,         -- MSP UUID from URL path
    metric       TEXT    NOT NULL,         -- SLE metric name from URL path
    start        INTEGER NOT NULL,         -- Window start epoch seconds
    end          INTEGER NOT NULL,         -- Window end epoch seconds
    interval     INTEGER NOT NULL,         -- Aggregation interval seconds
    limit        INTEGER,                  -- Optional server-side result cap
    results_json TEXT,                     -- Results array serialized as JSON
    sle_filter   TEXT,                     -- Optional sle query-param echo
    retrieved_at TEXT    NOT NULL,         -- ISO-8601 UTC fetch timestamp
    PRIMARY KEY (msp_id, metric, start, end, interval)
);

CREATE INDEX IF NOT EXISTS idx_msp_sle_msp_id
    ON msp_sle (msp_id);

CREATE INDEX IF NOT EXISTS idx_msp_sle_metric
    ON msp_sle (metric);

CREATE INDEX IF NOT EXISTS idx_msp_sle_msp_metric
    ON msp_sle (msp_id, metric);
```

The DDL is emitted automatically by `DataExporter` on first write when SQLite is
the active backend, derived from the `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry below.
The three indexes support common analyst queries: "all SLE rows for one MSP",
"compare one metric across MSPs", and "trend one metric for one MSP over time".

> **SQL note**: `limit` and `end` are SQLite reserved keywords; they must be quoted
> with double-quotes (or square brackets) in DDL and DML emitted by `DataExporter`.
> If the existing DataExporter does not already quote reserved-word column names,
> rename them to `result_limit` and `end_epoch` at implementation time to avoid
> any ambiguity. Document the chosen names in the implementation PR.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict in `MistHelper.py` (around line
1672 per `agents.md`):

```python
'getMspSle': {                                       # operationId from OpenAPI / mistapi SDK
    'type': 'composite_pk',                          # Five-column natural key
    'primary_key': [                                 # Stable across re-runs of the same window
        'msp_id',                                    # From URL path, injected by caller
        'metric',                                    # From URL path, injected by caller
        'start',                                     # From response body (required)
        'end',                                       # From response body (required)
        'interval',                                  # From response body (required)
    ],
    'indexes': [                                     # Common analyst-query support
        'msp_id',                                    # All rows for one MSP
        'metric',                                    # All rows for one metric across MSPs
        ('msp_id', 'metric'),                        # Trend rows for one MSP+metric pair
    ],
    'table_name': 'msp_sle',                         # Explicit table override (lowercase snake)
},
```

## Row Construction Contract (MistHelper-side)

The menu method must produce a single dict with the following shape before handing
it to `DataExporter.write_with_format_selection()`:

```python
import json                                          # Standard library, no new dep

msp_sle_row = {
    'msp_id': msp_identifier,                        # Path param, validated UUID
    'metric': sle_metric_name,                       # Path param, non-empty validated
    'start': response_data.get('start'),             # Required upstream; defensive .get
    'end': response_data.get('end'),                 # Required upstream
    'interval': response_data.get('interval'),       # Required upstream
    'limit': response_data.get('limit'),             # Optional; None if absent
    'results_json': json.dumps(                      # Serialize variable-shape array
        response_data.get('results') or [],          # Tolerate missing or null array
        separators=(',', ':'),                       # Compact; saves SQLite/CSV bytes
        sort_keys=False,                             # Preserve upstream ordering of buckets
    ),
    'sle_filter': sle_query_param,                   # Echo of the optional sle param
}
```

`retrieved_at` is injected by `DataExporter` -- the menu method does not populate
it manually. All response fields use `.get()` so missing keys produce `None` rather
than `KeyError`. If `start`, `end`, or `interval` come back as `None` from a
malformed upstream response, the row will be rejected by the SQLite `NOT NULL`
constraint; the menu method should log a `WARNING` and return early in that case.
