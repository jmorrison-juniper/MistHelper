# Phase 1 Data Model: getOrgUserMac

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-07-01

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_usermacs_usermac_id.md` (200 OK body).

## Entities

The endpoint returns a single JSON object representing one user-MAC assignment
record within an organization. MistHelper flattens this into a single row of
one logical entity.

### Entity 1: `UserMac`

One row per user-MAC record.

| Field           | Type    | Source              | PK? | FK?           | Notes |
|-----------------|---------|---------------------|-----|---------------|-------|
| `id`            | TEXT    | API `id`            | YES | --            | UUID assigned by Mist. Read-only. Primary key. |
| `org_id`        | TEXT    | MistHelper context  | --  | sites.org_id  | Injected by MistHelper (the API does not echo it in the body). Part of the unique `(org_id, mac)` index. |
| `mac`           | TEXT    | API `mac`           | --  | --            | Only non-local-admin MACs accepted (per API doc). The single required field in the response schema. Part of the unique `(org_id, mac)` index. |
| `name`          | TEXT    | API `name`          | --  | --            | Human-readable name (e.g. `Printer2`). Nullable. |
| `notes`         | TEXT    | API `notes`         | --  | --            | Free-text notes. Nullable. |
| `labels`        | TEXT    | API `labels` (array)| --  | --            | Stored as a pipe-delimited string (e.g. `byod|flr1`) for CSV/SQLite compatibility. Nullable. |
| `labels_count`  | INTEGER | len(API `labels`)   | --  | --            | Convenience count for SQL filters. |
| `radius_group`  | TEXT    | API `radius_group`  | --  | --            | RADIUS group name (e.g. `VIP`). Nullable. Indexed. |
| `vlan`          | TEXT    | API `vlan`          | --  | --            | VLAN ID stored as string (API returns string, e.g. `"30"`). Nullable. Indexed. |
| `fetched_at_utc`| TEXT    | MistHelper clock    | --  | --            | ISO8601 UTC timestamp of the fetch, for audit. |

## State Transitions

N/A -- this is a read-only endpoint. User-MAC records mutate on the Mist side
through the sibling `PUT` / `DELETE` operations
(`PUT /api/v1/orgs/{org_id}/usermacs/{usermac_id}` etc., which are out of
scope per spec.md). MistHelper only captures snapshots. Each fetch overwrites
the prior snapshot for the same `id` via SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- User-MAC assignments: one row per (org, usermac_id).
CREATE TABLE IF NOT EXISTS org_usermacs (
    id              TEXT     NOT NULL,           -- Mist UUID, natural PK
    org_id          TEXT     NOT NULL,           -- injected by MistHelper
    mac             TEXT     NOT NULL,           -- device MAC (non-local-admin)
    name            TEXT,                        -- human-readable name
    notes           TEXT,                        -- free-text notes
    labels          TEXT,                        -- pipe-delimited tag list
    labels_count    INTEGER,                     -- convenience count
    radius_group    TEXT,                        -- RADIUS group name
    vlan            TEXT,                        -- VLAN ID (string per API)
    fetched_at_utc  TEXT,                        -- ISO8601 poll timestamp
    PRIMARY KEY (id)
);

-- Business-rule uniqueness: a MAC exists at most once per org.
CREATE UNIQUE INDEX IF NOT EXISTS uq_org_usermacs_org_mac
    ON org_usermacs (org_id, mac);

-- Filter accelerators for common NAC analytics queries.
CREATE INDEX IF NOT EXISTS idx_org_usermacs_org
    ON org_usermacs (org_id);

CREATE INDEX IF NOT EXISTS idx_org_usermacs_radius_group
    ON org_usermacs (radius_group);

CREATE INDEX IF NOT EXISTS idx_org_usermacs_vlan
    ON org_usermacs (vlan);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via
`CREATE TABLE IF NOT EXISTS`, ArangoDB via collection upsert, Redis via key
namespacing). MistHelper does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no
structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Single user-MAC record within an org, keyed by Mist UUID.
    'getOrgUserMac': {                                                              # operationId from OpenAPI
        'type': 'natural_pk',                                                       # Mist provides a stable UUID
        'primary_key': ['id'],                                                      # Mist UUID from response body
        'indexes': ['org_id', 'mac', 'radius_group', 'vlan'],                       # NAC analytics filter columns
        'unique_indexes': [['org_id', 'mac']],                                      # a MAC exists at most once per org
        'table': 'org_usermacs',                                                    # target SQLite table
    },
}
```

Notes:

- The `unique_indexes` key follows the convention already used by other
  MistHelper endpoints that need a secondary uniqueness guarantee beyond the
  natural PK. If the current MistHelper codebase does not yet honor
  `unique_indexes`, that support is added in the same PR by extending the
  existing SQLite DDL emitter (a small, additive change).
- `org_id` is not part of the response body; MistHelper injects it from the
  caller context before the write. This mirrors how other single-object
  reads in MistHelper enrich rows with the requesting org for later joins.
