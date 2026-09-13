# Phase 1 Data Model: getOrgMxEdgeUpgrade

This file defines the entities, fields, types, and primary keys produced
by the `getOrgMxEdgeUpgrade` endpoint, plus the SQLite DDL and the
`ENDPOINT_PRIMARY_KEY_STRATEGIES` registration MistHelper will use to
upsert results cleanly.

The endpoint is **read-only** (HTTP GET). All entities below are
**append-or-replace** on natural keys; there are no state-machine
transitions in MistHelper itself. The Mist API server owns the lifecycle of
the upgrade job; MistHelper merely snapshots the current state at the time
of the call.

---

## Entities

### Entity 1: MxEdgeUpgradeSummary

Represents the upgrade job as a whole: identity, target version, overall
status, timing, and aggregate counts. Exactly one row per `(org_id,
upgrade_id)`.

| Field              | Type     | Required | Source                          | Notes                                                                 |
|--------------------|----------|----------|---------------------------------|-----------------------------------------------------------------------|
| `org_id`           | TEXT     | yes      | injected from prompt            | Mist organization UUID. Part of natural PK.                           |
| `upgrade_id`       | TEXT     | yes      | response top-level `id`         | Upgrade job UUID. Part of natural PK.                                 |
| `target_version`   | TEXT     | no       | response `target_version`       | Firmware version the job is upgrading to (semver-like string).        |
| `status`           | TEXT     | no       | response `status`               | One of e.g. `created`, `inprogress`, `completed`, `cancelled`.        |
| `strategy`         | TEXT     | no       | response `strategy`             | Roll-out strategy, e.g. `serial`, `parallel`.                         |
| `start_time`       | INTEGER  | no       | response `start_time`           | Epoch seconds when the job started.                                   |
| `end_time`         | INTEGER  | no       | response `end_time`             | Epoch seconds when the job finished, NULL while in-progress.          |
| `created_time`     | INTEGER  | no       | response `created_time`         | Epoch seconds when the job record was created.                        |
| `modified_time`    | INTEGER  | no       | response `modified_time`        | Epoch seconds of the last server-side mutation.                       |
| `total_count`      | INTEGER  | no       | derived: `len(progress)`        | Count of Mist Edges in the job (cached for fast CSV/SQL reads).       |
| `completed_count`  | INTEGER  | no       | derived: count of `status="completed"` | Count of Mist Edges that finished successfully.                |
| `failed_count`     | INTEGER  | no       | derived: count of `status="failed"`    | Count of Mist Edges that failed in this job.                   |
| `fetched_at`       | INTEGER  | yes      | injected: `time.time()` at fetch | Epoch seconds when MistHelper fetched the row.                       |

**Primary key**: `(org_id, upgrade_id)` -- `natural_pk`.
**Foreign keys**: `org_id` references the `org` entity managed by sister
endpoints (no enforced FK in SQLite -- referential integrity is logical).
**State transitions**: N/A -- read-only snapshot.

### Entity 2: MxEdgeUpgradeProgress

Represents the per-Mist-Edge progress slice inside the upgrade job. Zero or
more rows per `(org_id, upgrade_id)`; exactly one row per
`(org_id, upgrade_id, mxedge_id)`.

| Field            | Type    | Required | Source                                   | Notes                                                              |
|------------------|---------|----------|------------------------------------------|--------------------------------------------------------------------|
| `org_id`         | TEXT    | yes      | injected from prompt                     | Part of composite PK.                                              |
| `upgrade_id`     | TEXT    | yes      | response top-level `id`                  | Part of composite PK.                                              |
| `mxedge_id`      | TEXT    | yes      | response `progress[i].mxedge_id`         | Per-edge UUID. Part of composite PK.                               |
| `mxedge_name`    | TEXT    | no       | response `progress[i].name`              | Human-readable hostname for the Mist Edge.                         |
| `current_version`| TEXT    | no       | response `progress[i].current_version`   | Firmware version currently installed on this edge.                 |
| `status`         | TEXT    | no       | response `progress[i].status`            | Per-edge status, e.g. `pending`, `downloading`, `upgrading`, `completed`, `failed`. |
| `progress_pct`   | INTEGER | no       | response `progress[i].progress`          | 0-100 completion percentage on this edge.                          |
| `started_at`     | INTEGER | no       | response `progress[i].start_time`        | Epoch seconds when this edge began its slice.                      |
| `ended_at`       | INTEGER | no       | response `progress[i].end_time`          | Epoch seconds when this edge finished its slice.                   |
| `error_message`  | TEXT    | no       | response `progress[i].error`             | Plain-English failure reason if `status="failed"`, else NULL.      |
| `fetched_at`     | INTEGER | yes      | injected: `time.time()` at fetch         | Epoch seconds when MistHelper fetched the row.                     |

**Primary key**: `(org_id, upgrade_id, mxedge_id)` -- `composite_pk`.
**Foreign keys**: `(org_id, upgrade_id)` logically references
`MxEdgeUpgradeSummary`; `mxedge_id` logically references rows produced by
`listOrgMxEdges` (no enforced FK).
**State transitions**: N/A -- read-only snapshot. The server-side state
machine (`pending -> downloading -> upgrading -> completed | failed`)
is owned by the Mist API; MistHelper records whatever state is current at
fetch time.

Note: exact response field names may vary slightly across mistapi SDK
versions because no OpenAPI document covers this endpoint at the time of
writing. The flattener tolerates missing keys via `dict.get(...)`
defaults and never crashes on schema drift; unknown keys are logged at
DEBUG and dropped.

---

## SQLite DDL

The schema is created lazily by `DataExporter` on first run; the equivalent
canonical DDL is reproduced here for reference and for manual database
inspection.

```sql
-- Upgrade job summary (one row per upgrade)
CREATE TABLE IF NOT EXISTS org_mx_edge_upgrade_summary (
    org_id           TEXT    NOT NULL,
    upgrade_id       TEXT    NOT NULL,
    target_version   TEXT,
    status           TEXT,
    strategy         TEXT,
    start_time       INTEGER,
    end_time         INTEGER,
    created_time     INTEGER,
    modified_time    INTEGER,
    total_count      INTEGER,
    completed_count  INTEGER,
    failed_count     INTEGER,
    fetched_at       INTEGER NOT NULL,
    PRIMARY KEY (org_id, upgrade_id)
);

CREATE INDEX IF NOT EXISTS idx_org_mx_edge_upgrade_summary_status
    ON org_mx_edge_upgrade_summary (status);
CREATE INDEX IF NOT EXISTS idx_org_mx_edge_upgrade_summary_modified
    ON org_mx_edge_upgrade_summary (modified_time DESC);

-- Per-Mist-Edge progress (zero or more rows per upgrade)
CREATE TABLE IF NOT EXISTS org_mx_edge_upgrade_progress (
    org_id          TEXT    NOT NULL,
    upgrade_id      TEXT    NOT NULL,
    mxedge_id       TEXT    NOT NULL,
    mxedge_name     TEXT,
    current_version TEXT,
    status          TEXT,
    progress_pct    INTEGER,
    started_at      INTEGER,
    ended_at        INTEGER,
    error_message   TEXT,
    fetched_at      INTEGER NOT NULL,
    PRIMARY KEY (org_id, upgrade_id, mxedge_id)
);

CREATE INDEX IF NOT EXISTS idx_org_mx_edge_upgrade_progress_mxedge
    ON org_mx_edge_upgrade_progress (mxedge_id);
CREATE INDEX IF NOT EXISTS idx_org_mx_edge_upgrade_progress_status
    ON org_mx_edge_upgrade_progress (status);
```

Upserts use `INSERT OR REPLACE` on the natural / composite keys above, so
running the menu item repeatedly while the upgrade progresses safely
overwrites stale rows.

---

## ENDPOINT_PRIMARY_KEY_STRATEGIES entry

The following entry is added to the `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary at the documented location in `MistHelper.py` (line ~1672 in
the current revision). One operationId key maps to a small list describing
both output tables, matching the multi-table form already used by other
summary/detail menu items.

```python
"getOrgMxEdgeUpgrade": {
    # Summary table -- one row per (org, upgrade_id)
    "summary": {
        "type": "natural_pk",
        "primary_key": ["org_id", "upgrade_id"],
        "table": "org_mx_edge_upgrade_summary",
        "indexes": ["status", "modified_time"],
    },
    # Per-edge progress table -- one row per (org, upgrade_id, mxedge_id)
    "progress": {
        "type": "composite_pk",
        "primary_key": ["org_id", "upgrade_id", "mxedge_id"],
        "table": "org_mx_edge_upgrade_progress",
        "indexes": ["mxedge_id", "status"],
    },
},
```

`DataExporter.write_with_format_selection()` resolves the strategy by
matching `api_function_name="getOrgMxEdgeUpgrade"` against this dict and
selecting the correct sub-entry based on the `filename` suffix
(`_summary` vs `_progress`). The flat single-strategy form is *not* used
here because two granularities are produced.
