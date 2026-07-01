# Phase 1 Data Model: getOrgStats

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-07-01

## Source

API response schema lifted from `documentation/api/orgs/GET_orgs_org_id_stats.md`
(200 OK body).

## Entities

The endpoint returns a single JSON object describing the org statistics snapshot.
MistHelper splits this into two logical entities for clean multi-backend
persistence: one summary row, and zero-or-more SLE rows (from the nested `sle`
array).

### Entity 1: `OrgStatsSummary`

One row per (org UUID, MistHelper poll timestamp).

| Field                     | Type    | Source                        | PK? | FK?                      | Notes |
|---------------------------|---------|-------------------------------|-----|--------------------------|-------|
| `id`                      | TEXT    | API `id`                      | YES | sites.org_id             | Org UUID from the response body. |
| `polled_at_utc`           | TEXT    | MistHelper clock              | YES | --                       | ISO8601 UTC timestamp of the poll; injected before write. Enables time-series retention. |
| `name`                    | TEXT    | API `name`                    | --  | --                       | Human-readable org name. |
| `msp_id`                  | TEXT    | API `msp_id`                  | --  | --                       | Parent MSP UUID if any. Read-only. |
| `alarmtemplate_id`        | TEXT    | API `alarmtemplate_id`        | --  | alarm_templates.id       | Active alarm template UUID. |
| `allow_mist`              | INTEGER | API `allow_mist`              | --  | --                       | Boolean stored as 0/1. |
| `orggroup_ids`            | TEXT    | API `orggroup_ids`            | --  | --                       | JSON-encoded array of UUID strings (preserves multiplicity in a single column). |
| `session_expiry`          | INTEGER | API `session_expiry`          | --  | --                       | Seconds until UI session expiry. |
| `num_sites`               | INTEGER | API `num_sites`               | --  | --                       | Total site count in the org. |
| `num_inventory`           | INTEGER | API `num_inventory`           | --  | --                       | Total inventory item count. |
| `num_devices`             | INTEGER | API `num_devices`             | --  | --                       | Total device count. |
| `num_devices_connected`   | INTEGER | API `num_devices_connected`   | --  | --                       | Currently-connected device count. |
| `num_devices_disconnected`| INTEGER | API `num_devices_disconnected`| --  | --                       | Currently-disconnected device count. |
| `created_time`            | REAL    | API `created_time`            | --  | --                       | Org creation epoch seconds. Read-only. |
| `modified_time`           | REAL    | API `modified_time`           | --  | --                       | Last-modified epoch seconds. Read-only. |

### Entity 2: `OrgStatsSle`

Zero-or-more rows per (org UUID, poll timestamp). Source: each element of the API
`sle` array. The array declares `uniqueItems: true`, so `path` is unique inside a
given snapshot.

| Field           | Type    | Source                        | PK? | FK?                                  | Notes |
|-----------------|---------|-------------------------------|-----|--------------------------------------|-------|
| `org_id`        | TEXT    | MistHelper context            | YES | org_stats_summary.id                 | Org UUID; injected before write. |
| `polled_at_utc` | TEXT    | MistHelper clock              | YES | org_stats_summary.polled_at_utc      | Joins to the parent summary row. |
| `path`          | TEXT    | API `sle[].path`              | YES | --                                   | SLE category (e.g. `wifi`, `wan`, `wired`). |
| `user_minutes_ok`   | REAL | API `sle[].user_minutes.ok`   | --  | --                                   | Healthy user-minutes in the window. |
| `user_minutes_total`| REAL | API `sle[].user_minutes.total`| --  | --                                   | Total user-minutes in the window. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying org state changes on the Mist
side, but MistHelper does not drive or model those transitions; it merely
captures snapshots. Each poll writes a new snapshot keyed by
`(id, polled_at_utc)`; a repeated poll inside the same UTC second (rare,
debugging) upserts via SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- Summary table: one row per (org UUID, MistHelper poll timestamp).
CREATE TABLE IF NOT EXISTS org_stats_summary (
    id                       TEXT     NOT NULL,
    polled_at_utc            TEXT     NOT NULL,
    name                     TEXT,
    msp_id                   TEXT,
    alarmtemplate_id         TEXT,
    allow_mist               INTEGER,
    orggroup_ids             TEXT,
    session_expiry           INTEGER,
    num_sites                INTEGER,
    num_inventory            INTEGER,
    num_devices              INTEGER,
    num_devices_connected    INTEGER,
    num_devices_disconnected INTEGER,
    created_time             REAL,
    modified_time            REAL,
    PRIMARY KEY (id, polled_at_utc)
);

CREATE INDEX IF NOT EXISTS idx_org_stats_summary_name
    ON org_stats_summary (name);

CREATE INDEX IF NOT EXISTS idx_org_stats_summary_polled_at_utc
    ON org_stats_summary (polled_at_utc);

-- SLE detail table: zero-or-more rows per (org UUID, poll timestamp, SLE path).
CREATE TABLE IF NOT EXISTS org_stats_sle (
    org_id              TEXT     NOT NULL,
    polled_at_utc       TEXT     NOT NULL,
    path                TEXT     NOT NULL,
    user_minutes_ok     REAL,
    user_minutes_total  REAL,
    PRIMARY KEY (org_id, polled_at_utc, path),
    FOREIGN KEY (org_id, polled_at_utc)
        REFERENCES org_stats_summary(id, polled_at_utc)
);

CREATE INDEX IF NOT EXISTS idx_org_stats_sle_path
    ON org_stats_sle (path);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT
EXISTS`, ArangoDB via collection upsert, Redis via key namespacing). MistHelper
does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Update the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry for `getOrgStats`
(currently at `MistHelper.py:4331`, using `auto_increment_with_unique`) to the
composite-key form below, and add a new MistHelper-internal key
`getOrgStatsSleRows` for the flattened SLE sub-table.

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Org statistics snapshot; one row per (org UUID, MistHelper poll timestamp).
    "getOrgStats": {                                                                # operationId from OpenAPI
        "type": "composite_pk",                                                     # PK is composite of business + time keys
        "primary_key": ["id", "polled_at_utc"],                                     # org UUID + poll timestamp
        "indexes": ["name", "polled_at_utc"],                                       # fast lookup by name or time
        "unique_constraints": [],                                                   # PK already enforces uniqueness
        "table": "org_stats_summary",                                               # target SQLite table for summary rows
        "description": "Organization-level statistics snapshot",                    # human-readable purpose
    },

    # SLE array flattened out of the parent getOrgStats response.
    "getOrgStatsSleRows": {                                                         # MistHelper-internal sub-table id
        "type": "composite_pk",                                                     # composite of summary FK + SLE path
        "primary_key": ["org_id", "polled_at_utc", "path"],                         # unique per (org, poll, SLE category)
        "indexes": ["path"],                                                        # fast lookup by SLE path
        "unique_constraints": [],                                                   # PK already enforces uniqueness
        "table": "org_stats_sle",                                                   # target SQLite table for SLE rows
        "description": "Per-SLE-path user-minutes health for an org snapshot",      # human-readable purpose
    },
}
```

The `getOrgStatsSleRows` key is a MistHelper-internal identifier (the Mist API
has no operationId for it -- it is a flattened sub-array of the parent response).
This pattern matches how MistHelper already splits other endpoints whose response
contains nested arrays (see spec 500 for the same treatment of the claim status
`details` array).
