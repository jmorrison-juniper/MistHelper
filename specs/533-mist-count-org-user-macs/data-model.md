# Phase 1 Data Model: countOrgUserMacs

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)
**Endpoint**: `GET /api/v1/orgs/{org_id}/usermacs/count`

## Overview

The `countOrgUserMacs` endpoint returns aggregate counts of user-MAC records, grouped
by a single distinct attribute (`mac`, `name`, `labels`, or `org_id`), optionally
filtered by a time window. The response is one JSON object containing the window
metadata plus a `results[]` array of per-group counts.

For local persistence MistHelper splits the response into two normalized entities:

1. **UserMacsCountEnvelope** -- one row per invocation, carries totals + window.
2. **UserMacsCountResult** -- one row per `results[]` item.

## Entity: UserMacsCountEnvelope

| Field | Type | Source (response path) | Notes |
|-------|------|------------------------|-------|
| `misthelper_internal_id` | INTEGER PK AUTOINCREMENT | local | Surrogate PK for the envelope row. |
| `org_id` | TEXT NOT NULL | from prompt | Path parameter echoed into the row for joinability. |
| `distinct` | TEXT NOT NULL | from prompt | Echoed; constrained to enum `mac \| name \| labels \| org_id`. |
| `total` | INTEGER | `$.total` | Total matching user-MAC entries before `limit`. |
| `limit_applied` | INTEGER | `$.limit` | Limit echoed by the API (1-1000). |
| `window_start` | INTEGER | `$.start` | Epoch seconds (nullable when caller omits). |
| `window_end` | INTEGER | `$.end` | Epoch seconds (nullable when caller omits). |
| `fetched_at` | INTEGER NOT NULL | local | Epoch seconds at fetch time. |

**Primary key**: surrogate `misthelper_internal_id` (autoincrement).
**Unique constraint**: `(org_id, distinct, window_start, window_end)` so the same
window upserts cleanly when re-queried.
**Foreign keys**: none (org_id is conceptually a foreign key to `org_sites.org_id` but
not enforced at the SQLite level to keep the export idempotent across schema versions).

### State transitions

N/A -- read-only endpoint. Each fetch is a snapshot; rows are upserted, not mutated.

## Entity: UserMacsCountResult

| Field | Type | Source (response path) | Notes |
|-------|------|------------------------|-------|
| `org_id` | TEXT NOT NULL | from prompt | Echoed for joinability. |
| `distinct` | TEXT NOT NULL | from prompt | Echoed; identifies which attribute the row groups by. |
| `group_value` | TEXT NOT NULL | `$.results[*].<distinct>` | The value of the distinct attribute for this group (MAC string, name string, label string, or org_id UUID). |
| `count` | INTEGER NOT NULL | `$.results[*].count` | Number of user-MAC records in the group. |
| `window_start` | INTEGER | `$.start` | Epoch seconds (nullable). |
| `window_end` | INTEGER | `$.end` | Epoch seconds (nullable). |
| `fetched_at` | INTEGER NOT NULL | local | Epoch seconds at fetch time. |

**Primary key**: composite `(org_id, distinct, group_value, window_start, window_end)`.
**Foreign keys**: conceptually `org_id` -> `org_sites.org_id`; not enforced at DDL.
**Indexes**: `org_id`, `(org_id, distinct)`, `group_value`.

### State transitions

N/A -- read-only endpoint.

### Reference: underlying user_mac object schema

The `documentation/api/orgs/GET_orgs_org_id_usermacs_count.md` schema names the
items as `title: user_mac` with full fields (id, mac, labels, name, notes, radius_group,
vlan). For the count endpoint these fields are not all returned per row; only the
selected `distinct` attribute plus a `count` integer appear. The full `user_mac` shape
is captured by the related `searchOrgUserMacs` operation.

## SQLite DDL

```sql
-- Envelope: one row per fetch, idempotent on (org_id, distinct, window_start, window_end)
CREATE TABLE IF NOT EXISTS org_usermacs_count_envelope (
    misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id        TEXT    NOT NULL,
    distinct      TEXT    NOT NULL CHECK (distinct IN ('mac', 'name', 'labels', 'org_id')),
    total         INTEGER,
    limit_applied INTEGER,
    window_start  INTEGER,
    window_end    INTEGER,
    fetched_at    INTEGER NOT NULL,
    UNIQUE (org_id, distinct, window_start, window_end)
);

CREATE INDEX IF NOT EXISTS idx_usermacs_count_env_org
    ON org_usermacs_count_envelope (org_id);

-- Detail: one row per distinct group value within the (org, distinct, window) tuple
CREATE TABLE IF NOT EXISTS org_usermacs_count_results (
    org_id        TEXT    NOT NULL,
    distinct      TEXT    NOT NULL CHECK (distinct IN ('mac', 'name', 'labels', 'org_id')),
    group_value   TEXT    NOT NULL,
    count         INTEGER NOT NULL,
    window_start  INTEGER,
    window_end    INTEGER,
    fetched_at    INTEGER NOT NULL,
    PRIMARY KEY (org_id, distinct, group_value, window_start, window_end)
);

CREATE INDEX IF NOT EXISTS idx_usermacs_count_results_org
    ON org_usermacs_count_results (org_id);
CREATE INDEX IF NOT EXISTS idx_usermacs_count_results_org_distinct
    ON org_usermacs_count_results (org_id, distinct);
CREATE INDEX IF NOT EXISTS idx_usermacs_count_results_value
    ON org_usermacs_count_results (group_value);
```

Note: SQLite treats `distinct` as a non-reserved identifier in column position, but
some drivers warn. If a driver warning appears at implementation time the column is
quoted (`"distinct"`) in DDL and DML; no schema change required.

## ENDPOINT_PRIMARY_KEY_STRATEGIES entry

Add to the dictionary in `MistHelper.py` (canonical location around line ~1672):

```python
'countOrgUserMacs': {                             # operationId from OpenAPI spec
    'type': 'composite_pk',                       # aggregate rows: natural composite identity
    'primary_key': [                              # tuple uniquely identifies a per-group row
        'org_id',                                 # path parameter echoed onto every row
        'distinct',                               # attribute the row groups by
        'group_value',                            # the actual distinct value (MAC / name / ...)
        'window_start',                           # epoch seconds, nullable
        'window_end',                             # epoch seconds, nullable
    ],
    'indexes': [                                  # secondary lookups commonly used by NOC
        'org_id',
        ('org_id', 'distinct'),
        'group_value',
    ],
    'envelope_table': 'org_usermacs_count_envelope',     # companion summary table
    'detail_table': 'org_usermacs_count_results',        # companion detail table
},
```

The envelope table is registered implicitly via the `envelope_table` key, which
`DataExporter` uses to emit the summary row with its own UNIQUE-based upsert.

## Validation rules (enforced before SDK call)

- `org_id` MUST match the Mist UUID regex
  `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`.
- `distinct` MUST be one of `{mac, name, labels, org_id}`.
- `limit`, if provided, MUST parse as a positive integer <=1000.
- `start` / `end`, if provided, MUST be epoch integers or Mist relative time strings
  matching `^(-?\d+[smhdw]|now)$`.

Failures log a `WARNING` and return early without invoking the SDK.
