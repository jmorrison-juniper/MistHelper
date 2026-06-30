# Phase 1 Data Model: countSiteNacClientEvents

Source-of-truth response schema:
`documentation/api/sites/GET_sites_site_id_nac_clients_events_count.md` (200 JSON
schema, lines 46-100).

## Entities Returned by the Endpoint

The endpoint returns a single envelope object containing two logical entities:

### Entity 1: NAC Events Count Summary (envelope)

One row per `(site_id, distinct_attribute, query_window)` triple. Represents the
metadata for a single count query.

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `site_id` | string (UUID) | request path param | Site the count was scoped to. Foreign key to `sites.id`. |
| `distinct_attribute` | string | request query param | The NAC event field grouped on (e.g. `type`, `nas_vendor`, `auth_type`, `ssid`, `vlan`). Mirrors the API response `distinct` field. |
| `query_window_start` | integer (epoch seconds) | response `start` | Start of the queried time window. |
| `query_window_end` | integer (epoch seconds) | response `end` | End of the queried time window. |
| `query_limit` | integer | response `limit` | Maximum distinct buckets requested. |
| `total_events` | integer | response `total` | Total NAC client events counted across all buckets in the window. |
| `bucket_count` | integer | derived: `len(response.results)` | Number of distinct buckets actually returned. |
| `event_type_filter` | string (nullable) | request query param `type` | If the user filtered to a single NAC event type, that type; otherwise NULL. |
| `retrieved_at` | integer (epoch seconds) | MistHelper-local | Server-side `time.time()` at the moment of retrieval, for trend tracking across re-runs. |

**Primary key**: composite
`(site_id, distinct_attribute, query_window_start, query_window_end)`.

**Foreign keys**: `site_id` -> `sites.id` (existing MistHelper sites table).

### Entity 2: NAC Events Count Bucket (per-result row)

One row per distinct value of the chosen `distinct_attribute`. Represents one bar in
a histogram of "count of NAC events grouped by X".

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `site_id` | string (UUID) | request path param | Same as summary row -- denormalized for join-free SQL. |
| `distinct_attribute` | string | request query param | Same as summary row -- denormalized. |
| `distinct_value` | string | response `results[i].<distinct_attribute>` | The actual value of the grouped-on field for this bucket (e.g. `eap-tls`, `juniper-mist`, `1234`). |
| `count` | integer | response `results[i].count` | Number of NAC events with that value in the window. |
| `query_window_start` | integer (epoch seconds) | response `start` | Same as summary row. |
| `query_window_end` | integer (epoch seconds) | response `end` | Same as summary row. |
| `retrieved_at` | integer (epoch seconds) | MistHelper-local | Same as summary row. |

**Primary key**: composite
`(site_id, distinct_attribute, distinct_value, query_window_start, query_window_end)`.

**Foreign keys**:
- `site_id` -> `sites.id`.
- `(site_id, distinct_attribute, query_window_start, query_window_end)` ->
  summary table primary key (logical link; not enforced by SQLite because both tables
  upsert on the same run).

## State Transitions

**N/A -- read-only endpoint.** The Mist API endpoint is HTTP GET only; no state is
mutated upstream. Local SQLite rows are `INSERT OR REPLACE`d on every re-run with the
same composite key, so the only local "state" is "row absent" -> "row present and
fresh". No formal state-machine modelling is required.

## SQLite DDL

The two tables are created on first run by `DataExporter`, but the equivalent DDL is
documented here for reference and code review.

```sql
CREATE TABLE IF NOT EXISTS site_nac_client_events_count_summary (
    site_id              TEXT    NOT NULL,
    distinct_attribute   TEXT    NOT NULL,
    query_window_start   INTEGER NOT NULL,
    query_window_end     INTEGER NOT NULL,
    query_limit          INTEGER NOT NULL,
    total_events         INTEGER NOT NULL,
    bucket_count         INTEGER NOT NULL,
    event_type_filter    TEXT,
    retrieved_at         INTEGER NOT NULL,
    PRIMARY KEY (site_id, distinct_attribute, query_window_start, query_window_end)
);

CREATE INDEX IF NOT EXISTS idx_site_nac_events_count_summary_site
    ON site_nac_client_events_count_summary (site_id);
CREATE INDEX IF NOT EXISTS idx_site_nac_events_count_summary_retrieved
    ON site_nac_client_events_count_summary (retrieved_at);

CREATE TABLE IF NOT EXISTS site_nac_client_events_count_results (
    site_id              TEXT    NOT NULL,
    distinct_attribute   TEXT    NOT NULL,
    distinct_value       TEXT    NOT NULL,
    count                INTEGER NOT NULL,
    query_window_start   INTEGER NOT NULL,
    query_window_end     INTEGER NOT NULL,
    retrieved_at         INTEGER NOT NULL,
    PRIMARY KEY (
        site_id,
        distinct_attribute,
        distinct_value,
        query_window_start,
        query_window_end
    )
);

CREATE INDEX IF NOT EXISTS idx_site_nac_events_count_results_site
    ON site_nac_client_events_count_results (site_id);
CREATE INDEX IF NOT EXISTS idx_site_nac_events_count_results_value
    ON site_nac_client_events_count_results (distinct_attribute, distinct_value);
```

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Two entries are registered (one per logical table). The dictionary keys match the
operationId verbatim, with a `_summary` / `_results` suffix used by `DataExporter` to
route the two output streams.

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES["countSiteNacClientEvents_summary"] = {
    "type": "composite_pk",
    "primary_key": [
        "site_id",
        "distinct_attribute",
        "query_window_start",
        "query_window_end",
    ],
    "indexes": ["site_id", "retrieved_at"],
    "table_name": "site_nac_client_events_count_summary",
}

ENDPOINT_PRIMARY_KEY_STRATEGIES["countSiteNacClientEvents_results"] = {
    "type": "composite_pk",
    "primary_key": [
        "site_id",
        "distinct_attribute",
        "distinct_value",
        "query_window_start",
        "query_window_end",
    ],
    "indexes": ["site_id", "distinct_attribute"],
    "table_name": "site_nac_client_events_count_results",
}
```

The PR also registers the bare operationId `countSiteNacClientEvents` as an alias
pointing at the summary strategy, so `api_function_name="countSiteNacClientEvents"`
resolves cleanly from a single DataExporter call site:

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES["countSiteNacClientEvents"] = (
    ENDPOINT_PRIMARY_KEY_STRATEGIES["countSiteNacClientEvents_summary"]
)
```
