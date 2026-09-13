# Phase 1 Data Model: getMspOrgGroup

**Feature**: 585-mist-get-msp-org-group
**Source schema**: `documentation/api/msps/GET_msps_msp_id_orggroups_orggroup_id.md` (200 response)

This document defines the entities returned by `GET
/api/v1/msps/{msp_id}/orggroups/{orggroup_id}`, the SQLite schema that captures them,
and the `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration that enables idempotent upserts.

---

## Entities

### Entity 1: `MspOrgGroup`

Represents a single MSP-managed Organization Group: a named grouping of one or more
Mist Orgs that an MSP administers as a unit.

| Field | Type | Required | Description | Notes |
|-------|------|----------|-------------|-------|
| `id` | string (uuid) | yes (server-issued) | Unique ID of the org group in the Mist tenant | **Primary key** |
| `msp_id` | string (uuid) | yes (server-issued) | UUID of the parent MSP | **Foreign key** to `msps.id` (conceptual; MistHelper does not currently materialize an `msps` table for this spec) |
| `name` | string | yes | Display name of the org group | Required by the OpenAPI schema |
| `org_ids` | array of string (uuid) | optional | Member Org UUIDs | Normalized into `msp_org_group_members` (one row per element); the array itself is not stored in `msp_org_groups` |
| `created_time` | number (epoch seconds) | server-issued | Creation timestamp | `readOnly` |
| `modified_time` | number (epoch seconds) | server-issued | Last-modified timestamp | `readOnly`; used downstream to detect staleness |

**Primary Key**: `id` (UUID, server-issued, stable across reads)
**Foreign Keys**: `msp_id` references the MSP entity (no local `msps` table created
by this spec; the column is informational and indexed for filtering).
**Uniqueness Constraints**: `id` is globally unique; `(msp_id, name)` is unique in
practice but is not enforced as a SQL UNIQUE because the Mist API itself does not
guarantee it and adding a UNIQUE constraint would break upsert semantics on rename.

### Entity 2: `MspOrgGroupMember` (derived / normalized)

Represents a single `(orggroup_id, org_id)` membership edge derived from the
`org_ids[]` array on the parent `MspOrgGroup`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orggroup_id` | string (uuid) | yes | Parent org-group UUID -- FK to `msp_org_groups.id` |
| `org_id` | string (uuid) | yes | Member Mist Org UUID |
| `ingested_at` | text (ISO-8601) | yes (client-stamped) | When MistHelper ingested this edge; used for staleness audits |

**Primary Key**: composite `(orggroup_id, org_id)`
**Foreign Keys**: `orggroup_id` -> `msp_org_groups.id` (logical, not enforced as
`FOREIGN KEY` to avoid SQLite cascade pitfalls during partial re-ingests).

---

## State Transitions

**N/A -- read-only endpoint.** `getMspOrgGroup` is a single GET; the local model is a
materialized snapshot of upstream state. Every successful call replaces the existing
row(s) for the queried `orggroup_id` via `INSERT OR REPLACE`. There are no lifecycle
states (pending / active / archived) tracked by MistHelper for this entity in this
spec; write operations (POST / PUT / DELETE) on the same path are explicitly **Out of
Scope** per spec.md.

---

## SQLite DDL

The following tables are created by `DataExporter` on first run. The DDL below is
illustrative -- the `DataExporter` adapter generates equivalent SQL from the PK
strategy entry.

```sql
-- Summary table: one row per MSP org group
CREATE TABLE IF NOT EXISTS msp_org_groups (
    id              TEXT PRIMARY KEY,                 -- Mist-issued UUID for the org group
    msp_id          TEXT NOT NULL,                    -- Parent MSP UUID; informational FK
    name            TEXT NOT NULL,                    -- Display name (required by API schema)
    created_time    REAL,                             -- Epoch seconds; server-issued
    modified_time   REAL,                             -- Epoch seconds; server-issued
    member_org_count INTEGER NOT NULL DEFAULT 0,      -- Cached len(org_ids); convenience column
    ingested_at     TEXT NOT NULL                     -- ISO-8601 timestamp of local ingest
);

CREATE INDEX IF NOT EXISTS idx_msp_org_groups_msp_id
    ON msp_org_groups(msp_id);                        -- Fast lookup by parent MSP

CREATE INDEX IF NOT EXISTS idx_msp_org_groups_name
    ON msp_org_groups(name);                          -- Fast lookup by display name

-- Edge table: one row per (org-group, member-org) pair
CREATE TABLE IF NOT EXISTS msp_org_group_members (
    orggroup_id   TEXT NOT NULL,                      -- FK (logical) to msp_org_groups.id
    org_id        TEXT NOT NULL,                      -- Member Mist Org UUID
    ingested_at   TEXT NOT NULL,                      -- ISO-8601 timestamp of local ingest
    PRIMARY KEY (orggroup_id, org_id)                 -- Composite PK guarantees idempotent re-ingest
);

CREATE INDEX IF NOT EXISTS idx_msp_org_group_members_orggroup_id
    ON msp_org_group_members(orggroup_id);            -- Fast "members of this group" queries
```

**Upsert semantics**: Both tables use `INSERT OR REPLACE` on their declared primary
key, matching MistHelper's universal idempotent-ingest contract.

---

## `ENDPOINT_PRIMARY_KEY_STRATEGIES` Entry

The following dict entry is added to `ENDPOINT_PRIMARY_KEY_STRATEGIES` in
`MistHelper.py` (the dictionary lives near line ~1672 in the current monolith). Each
line carries the mandatory inline comment per Constitution Principle VI.

```python
'getMspOrgGroup': {                                      # Operation ID -- exact match to mistapi SDK function name
    'type': 'natural_pk',                                # Stable server-issued UUID present in the response
    'primary_key': ['id'],                               # Single-column PK on the org-group UUID
    'indexes': ['msp_id', 'name'],                       # Speeds up "groups for MSP X" and "lookup by name"
    'table_name': 'msp_org_groups',                      # Target SQLite table for the summary row
    'related_tables': {                                  # Normalized child table for the org_ids[] array
        'msp_org_group_members': {                       # Edge-table key in the same registry
            'type': 'composite_pk',                      # Identity is the (orggroup, org) pair
            'primary_key': ['orggroup_id', 'org_id'],    # Composite ensures idempotent re-ingest of edges
            'indexes': ['orggroup_id'],                  # Fast "members of this group" reads
        },
    },
},
```

---

## Multi-Backend Mapping

| Backend | Summary | Members |
|---------|---------|---------|
| **CSV** | `data/msp_org_group_<msp_id>_<orggroup_id>.csv` (1 row) | `data/msp_org_group_members_<orggroup_id>.csv` (N rows) |
| **SQLite** | `msp_org_groups` table (upsert by `id`) | `msp_org_group_members` table (upsert by `(orggroup_id, org_id)`) |
| **ArangoDB** | Document collection `msp_org_groups` keyed by `id` | Edge collection `msp_org_group_members` between `msp_org_groups` and `orgs` |
| **Redis** | Cache key `msp_org_group:<orggroup_id>` (TTL per existing cache policy) | Not cached (low-cardinality, derived from summary) |

All four backends are written through a single call to
`DataExporter.write_with_format_selection(data, filename, api_function_name='getMspOrgGroup')`
-- the adapter dispatches by the active backend without further branching in the menu
method.
