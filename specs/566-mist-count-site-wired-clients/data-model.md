# Phase 1 Data Model: countSiteWiredClients

Maps the JSON response of `GET /api/v1/sites/{site_id}/wired_clients/count`
into MistHelper's storage layer (CSV / SQLite / ArangoDB+Redis).

Source schema reference:
`documentation/api/sites/GET_sites_site_id_wired_clients_count.md` (lines
49-103). The 200 response is a single JSON object with five top-level
scalar fields plus a `results` array.

## Entities

### Entity 1 -- `count_site_wired_clients` (one summary row per call)

Persisted to the SQLite table `count_site_wired_clients` and to the CSV
file `data/count_site_wired_clients.csv`. One row is appended per
invocation (snapshot semantics).

| Field | Type | Required | Source | Notes |
| - | - | - | - | - |
| `misthelper_internal_id` | INTEGER PK AUTOINCREMENT | Yes | DataExporter | Synthetic surrogate key (PK strategy `auto_increment_with_unique`). |
| `site_id` | TEXT | Yes | path param | UUID of the queried site (FK to `sites.id`). |
| `org_id` | TEXT | Yes | `.env` | UUID of the owning org (FK to `orgs.id`). Recorded for graph linkage / multi-tenant reporting. |
| `distinct` | TEXT | Yes | response `distinct` | The field the aggregate is bucketed by (`mac`, `device_mac`, `port_id`, `vlan`, ...). Indexed. |
| `total` | INTEGER | Yes | response `total` | Total count returned by the API for the requested window. |
| `start` | INTEGER | Yes | response `start` | Window start (epoch seconds). |
| `end` | INTEGER | Yes | response `end` | Window end (epoch seconds). |
| `limit` | INTEGER | Yes | response `limit` | Max number of result buckets returned by the API. |
| `duration` | TEXT | No | user / API default `"1d"` | Echo of the duration the user supplied; useful for trend queries. |
| `mac_filter` | TEXT | No | user | Optional `mac` query param if set. |
| `device_mac_filter` | TEXT | No | user | Optional `device_mac` query param if set. |
| `port_id_filter` | TEXT | No | user | Optional `port_id` query param if set. |
| `vlan_filter` | TEXT | No | user | Optional `vlan` query param if set. |
| `results_row_count` | INTEGER | Yes | derived `len(results)` | Number of bucket rows written to the detail table for this call. |
| `captured_at` | TEXT (ISO 8601) | Yes | local clock | Snapshot timestamp written by `DataExporter` for trend joins. |

**Primary Key**: `misthelper_internal_id` (auto-increment).
**Foreign Keys**: `site_id` -> `sites.id`; `org_id` -> `orgs.id` (logical;
SQLite does not enforce unless `PRAGMA foreign_keys = ON`).
**Indexes**: `site_id`, `distinct`.

### Entity 2 -- `count_site_wired_clients_results` (N detail rows per call)

Persisted to the SQLite table `count_site_wired_clients_results` and to
the CSV file `data/count_site_wired_clients_results.csv`. One row per
bucket in the API's `results` array. Linked back to the summary row by
`parent_internal_id`.

| Field | Type | Required | Source | Notes |
| - | - | - | - | - |
| `misthelper_internal_id` | INTEGER PK AUTOINCREMENT | Yes | DataExporter | Synthetic surrogate key. |
| `parent_internal_id` | INTEGER | Yes | summary row | FK to `count_site_wired_clients.misthelper_internal_id`. |
| `site_id` | TEXT | Yes | path param | Duplicated for query convenience. Indexed. |
| `distinct` | TEXT | Yes | summary | Echo of the bucket dimension name (`mac`, `vlan`, ...). |
| `distinct_value` | TEXT | Yes | response `results[].<distinct field>` | The actual bucketed value (e.g. specific MAC, VLAN ID, port name). |
| `count` | INTEGER | Yes | response `results[].count` | Number of wired clients matching this bucket. |
| `captured_at` | TEXT (ISO 8601) | Yes | local clock | Mirrors the summary row for stand-alone queryability. |

**Primary Key**: `misthelper_internal_id` (auto-increment).
**Foreign Keys**: `parent_internal_id` ->
`count_site_wired_clients.misthelper_internal_id`; `site_id` -> `sites.id`.
**Indexes**: `parent_internal_id`, `site_id`, `distinct`.

## State Transitions

**N/A -- read-only endpoint.** The Mist API operation is HTTP GET with no
server-side side effect. Locally, each MistHelper invocation appends a new
summary row and N new detail rows; no row is ever updated or deleted by
this menu item. Operators who want to prune historical snapshots use the
generic SQLite housekeeping operations already exposed under the
maintenance menu cluster.

## SQLite DDL Snippet

`DataExporter` issues `CREATE TABLE IF NOT EXISTS` on first run based on the
registered PK strategy plus the column names observed in the flattened
output. The equivalent hand-written DDL is:

```sql
CREATE TABLE IF NOT EXISTS count_site_wired_clients (
    misthelper_internal_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id                  TEXT NOT NULL,
    org_id                   TEXT,
    distinct                 TEXT NOT NULL,
    total                    INTEGER NOT NULL,
    start                    INTEGER NOT NULL,
    end                      INTEGER NOT NULL,
    limit                    INTEGER NOT NULL,
    duration                 TEXT,
    mac_filter               TEXT,
    device_mac_filter        TEXT,
    port_id_filter           TEXT,
    vlan_filter              TEXT,
    results_row_count        INTEGER NOT NULL,
    captured_at              TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_count_site_wired_clients_site_id
    ON count_site_wired_clients (site_id);

CREATE INDEX IF NOT EXISTS ix_count_site_wired_clients_distinct
    ON count_site_wired_clients (distinct);

CREATE TABLE IF NOT EXISTS count_site_wired_clients_results (
    misthelper_internal_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_internal_id       INTEGER NOT NULL,
    site_id                  TEXT NOT NULL,
    distinct                 TEXT NOT NULL,
    distinct_value           TEXT,
    count                    INTEGER NOT NULL,
    captured_at              TEXT NOT NULL,
    FOREIGN KEY (parent_internal_id)
        REFERENCES count_site_wired_clients (misthelper_internal_id)
);

CREATE INDEX IF NOT EXISTS ix_count_site_wired_clients_results_parent
    ON count_site_wired_clients_results (parent_internal_id);

CREATE INDEX IF NOT EXISTS ix_count_site_wired_clients_results_site
    ON count_site_wired_clients_results (site_id);

CREATE INDEX IF NOT EXISTS ix_count_site_wired_clients_results_distinct
    ON count_site_wired_clients_results (distinct);
```

Note: `distinct`, `start`, `end`, and `limit` are SQL reserved-ish
keywords. SQLite accepts them as column identifiers without quoting, but
the code that builds the SQL statements must use parameterized inserts (as
`DataExporter` already does); ad-hoc users querying the table by hand
should wrap reserved names in double quotes (`SELECT "limit" FROM ...`).

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Insert near the existing `countOrgWiredClients` entry at
`MistHelper.py:~4561` so the related strategies stay alphabetically and
semantically grouped:

```python
"countSiteWiredClients": {                               # New strategy for site-scope wired client counts.
    "type": "auto_increment_with_unique",                # Aggregate snapshot with no stable natural key.
    "primary_key": ["misthelper_internal_id"],           # Synthetic surrogate so repeated runs do not collide.
    "indexes": ["site_id", "distinct"],                  # Common filter fields for downstream reporting.
    "unique_constraints": [],                            # No uniqueness invariants on aggregates.
    "description": "Site-scope wired client count aggregates",  # Human-readable label surfaced by --list-strategies.
},
```

The companion detail table is created implicitly by `DataExporter` from
the list-of-dicts shape returned by the flatten step; it does not need its
own `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry because the existing
"sub-collection" handling (already used by the other count endpoints)
inherits the parent's strategy.
