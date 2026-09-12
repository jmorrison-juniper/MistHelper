# Phase 1 Data Model: countSiteDeviceLastConfig

## Endpoint response shape

The 200 response (per
`documentation/api/sites/GET_sites_site_id_devices_last_config_count.md`) is a
single JSON object with this schema:

```json
{
  "distinct": "string",
  "start":    "integer (epoch seconds)",
  "end":      "integer (epoch seconds)",
  "duration": "string (resolved request param, e.g. '1d')",
  "limit":    "integer",
  "total":    "integer (total matching records)",
  "results":  [
    { "count": "integer", "<distinct_field_value>": "string" }
  ]
}
```

The `results` array members carry one fixed key (`count`) plus one
free-form key whose name equals the value of the `distinct` request
parameter (e.g. when `distinct=hostname`, each row has a `hostname` key).
The schema marks `additionalProperties` as `string`, so the per-group key's
*value* is always a string.

## Entities

### Entity 1: `LastConfigCountSummary`

One row per (site_id, distinct, window_start, window_end) tuple. Captures
the top-level response scalars.

| Field          | Type    | PK? | FK?                          | Notes |
|----------------|---------|-----|------------------------------|-------|
| site_id        | TEXT    | yes | sites.id                     | Path parameter; UUID. |
| distinct       | TEXT    | yes | -                            | "" when the user did not supply a distinct field. |
| window_start   | INTEGER | yes | -                            | Resolved start epoch seconds. |
| window_end     | INTEGER | yes | -                            | Resolved end epoch seconds. |
| duration       | TEXT    | no  | -                            | Request-side duration string ("1d", "7d", ...). |
| limit          | INTEGER | no  | -                            | The `limit` actually sent. |
| total          | INTEGER | no  | -                            | The response `total`. |
| group_count    | INTEGER | no  | -                            | `len(results)` -- number of distinct groups returned. |
| fetched_at     | TEXT    | no  | -                            | ISO 8601 UTC timestamp set at write time. |
| api_function   | TEXT    | no  | -                            | Always `"countSiteDeviceLastConfig"`. |

### Entity 2: `LastConfigCountResult`

One row per (site_id, distinct, window_start, window_end, group_value).
Captures each `results[]` element.

| Field          | Type    | PK? | FK?                                       | Notes |
|----------------|---------|-----|-------------------------------------------|-------|
| site_id        | TEXT    | yes | sites.id, summary.site_id                 | Path parameter; UUID. |
| distinct       | TEXT    | yes | summary.distinct                          | Matches the parent summary row. |
| window_start   | INTEGER | yes | summary.window_start                      | Matches the parent summary row. |
| window_end     | INTEGER | yes | summary.window_end                        | Matches the parent summary row. |
| group_value    | TEXT    | yes | -                                         | The free-form distinct field value. "" when distinct is unset (one aggregate row). |
| count          | INTEGER | no  | -                                         | Per-group count from the API. |
| fetched_at     | TEXT    | no  | -                                         | ISO 8601 UTC timestamp set at write time. |

## State transitions

N/A -- read-only endpoint. Each invocation refreshes the rows for its
(site_id, distinct, window_start, window_end) key. There is no lifecycle,
no created/modified state, no deletion logic. Repeated runs upsert in
place via `INSERT OR REPLACE`.

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS site_device_last_config_count_summary (
    site_id       TEXT    NOT NULL,
    distinct      TEXT    NOT NULL DEFAULT '',
    window_start  INTEGER NOT NULL,
    window_end    INTEGER NOT NULL,
    duration      TEXT,
    "limit"       INTEGER,
    total         INTEGER,
    group_count   INTEGER,
    fetched_at    TEXT    NOT NULL,
    api_function  TEXT    NOT NULL,
    PRIMARY KEY (site_id, distinct, window_start, window_end)
);

CREATE INDEX IF NOT EXISTS idx_lcc_summary_site
    ON site_device_last_config_count_summary (site_id);

CREATE TABLE IF NOT EXISTS site_device_last_config_count_results (
    site_id       TEXT    NOT NULL,
    distinct      TEXT    NOT NULL DEFAULT '',
    window_start  INTEGER NOT NULL,
    window_end    INTEGER NOT NULL,
    group_value   TEXT    NOT NULL DEFAULT '',
    count         INTEGER NOT NULL,
    fetched_at    TEXT    NOT NULL,
    PRIMARY KEY (site_id, distinct, window_start, window_end, group_value),
    FOREIGN KEY (site_id, distinct, window_start, window_end)
        REFERENCES site_device_last_config_count_summary
            (site_id, distinct, window_start, window_end)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_lcc_results_site
    ON site_device_last_config_count_results (site_id);
CREATE INDEX IF NOT EXISTS idx_lcc_results_group
    ON site_device_last_config_count_results (distinct, group_value);
```

Notes:
- `"limit"` is quoted because `LIMIT` is a SQL reserved word.
- `distinct` is also a reserved word in many dialects but SQLite tolerates
  it as a column name; MistHelper's existing helpers already escape it
  consistently.
- Indexes match the most common operator query: "show me last-config counts
  for site X".

## ENDPOINT_PRIMARY_KEY_STRATEGIES entry

Add to the dictionary in `MistHelper.py` (line ~1672):

```python
"countSiteDeviceLastConfig": {                                         # SDK operationId is the dict key
    "type": "composite_pk",                                            # Time + group composite -- no stable UUID exists
    "tables": {                                                        # Two-table export pattern
        "site_device_last_config_count_summary": {                     # One row per request scope
            "primary_key": [                                           # Tuple uniquely identifies one summary row
                "site_id",                                             # From path parameter
                "distinct",                                            # Empty string when not supplied
                "window_start",                                        # Resolved epoch seconds
                "window_end",                                          # Resolved epoch seconds
            ],
            "indexes": ["site_id"],                                    # Common operator filter
        },
        "site_device_last_config_count_results": {                     # One row per distinct group value
            "primary_key": [                                           # Parent tuple plus group value
                "site_id",
                "distinct",
                "window_start",
                "window_end",
                "group_value",                                         # The per-group key value from results[]
            ],
            "indexes": ["site_id", "distinct", "group_value"],         # Filter and join targets
        },
    },
}
```

The dict entry follows the same shape as the existing
`searchOrgDeviceEvents` composite_pk entry (lines around 1672 in
`MistHelper.py`). No new dict keys are introduced.
