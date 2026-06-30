# Phase 1 Data Model: getOrgIdpProfile

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_idpprofiles_idpprofile_id.md` (200 OK
body).

## Entities

The endpoint returns a single JSON object describing one IDP (Intrusion
Detection and Prevention) profile owned by an organization. The profile carries
metadata (id, name, base_profile, timestamps) and a nested `overwrites` array
of per-rule customizations. MistHelper splits this into two logical entities
for clean multi-backend persistence.

### Entity 1: `IdpProfileSummary`

Exactly one row per (org, IDP profile). The natural key is the profile UUID
returned by the API.

| Field            | Type    | Source                 | PK? | FK?          | Notes |
|------------------|---------|------------------------|-----|--------------|-------|
| `id`             | TEXT    | API `id`               | YES | --           | Profile UUID, stable, server-assigned. |
| `org_id`         | TEXT    | API `org_id`           | --  | sites.org_id | UUID of owning org. Echoed by API; cross-checked against the caller's input. |
| `name`           | TEXT    | API `name`             | --  | --           | Human-readable label (e.g. `"relaxed"`). |
| `base_profile`   | TEXT    | API `base_profile`     | --  | --           | Enum: `critical`, `standard`, `strict`. |
| `created_time`   | REAL    | API `created_time`     | --  | --           | Epoch seconds when the profile was created. Read-only. |
| `modified_time`  | REAL    | API `modified_time`    | --  | --           | Epoch seconds of last modification. Read-only. |
| `overwrite_count`| INTEGER | len(API `overwrites`)  | --  | --           | Convenience count of overwrite rules attached to this profile. |
| `polled_at_utc`  | TEXT    | MistHelper clock       | --  | --           | ISO8601 UTC timestamp of the fetch, for audit. |

### Entity 2: `IdpProfileOverwrite`

Zero-or-more rows per (org, IDP profile). One row per element of the API
`overwrites` array. The natural key within a profile is the overwrite `name`
(Mist enforces uniqueness of rule names within a profile in the UI).

| Field              | Type    | Source                            | PK? | FK?                                       | Notes |
|--------------------|---------|-----------------------------------|-----|-------------------------------------------|-------|
| `idpprofile_id`    | TEXT    | MistHelper context (parent `id`)  | YES | org_idp_profile_summary.id                | Joins to summary. Injected before write. |
| `name`             | TEXT    | API `overwrites[].name`           | YES | --                                        | Overwrite rule name, unique within profile. |
| `action`           | TEXT    | API `overwrites[].action`         | --  | --                                        | Enum: `alert` (default), `drop`, `close`. |
| `attack_name_json` | TEXT    | API `overwrites[].matching.attack_name` | -- | --                                  | JSON-encoded string array. Flattened to one column to preserve order. |
| `dst_subnet_json`  | TEXT    | API `overwrites[].matching.dst_subnet`  | -- | --                                  | JSON-encoded string array (CIDR notation). |
| `severity_json`    | TEXT    | API `overwrites[].matching.severity`    | -- | --                                  | JSON-encoded string array (values: `critical`, `info`, `major`, `minor`). |
| `severity_count`   | INTEGER | len(API `overwrites[].matching.severity`) | -- | --                                | Convenience count for cheap filtering without parsing JSON. |
| `polled_at_utc`    | TEXT    | MistHelper clock                  | --  | --                                        | ISO8601 UTC timestamp of the fetch, for audit. |

Note: the three `*_json` columns intentionally preserve the API's array shape
as compact JSON so consumers can re-parse without losing information. The
flatten helper emits `"[]"` (not `NULL`) for absent arrays so downstream SQL
filters can rely on a consistent type.

## State Transitions

N/A -- this is a read-only endpoint. The profile and its overwrites are
managed via the corresponding PUT endpoint
(`PUT /api/v1/orgs/{org_id}/idpprofiles/{idpprofile_id}`), which is **out of
scope** per the spec. MistHelper merely captures snapshots; each fetch
overwrites the prior snapshot for the same `id` (summary) and
`(idpprofile_id, name)` (overwrite) tuples via SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- Summary table: exactly one row per IDP profile.
CREATE TABLE IF NOT EXISTS org_idp_profile_summary (
    id              TEXT     NOT NULL,
    org_id          TEXT,
    name            TEXT,
    base_profile    TEXT,
    created_time    REAL,
    modified_time   REAL,
    overwrite_count INTEGER,
    polled_at_utc   TEXT,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_idp_profile_summary_org
    ON org_idp_profile_summary (org_id);

CREATE INDEX IF NOT EXISTS idx_idp_profile_summary_name
    ON org_idp_profile_summary (name);

-- Overwrites table: zero-or-more rows per IDP profile.
CREATE TABLE IF NOT EXISTS org_idp_profile_overwrites (
    idpprofile_id     TEXT     NOT NULL,
    name              TEXT     NOT NULL,
    action            TEXT,
    attack_name_json  TEXT,
    dst_subnet_json   TEXT,
    severity_json     TEXT,
    severity_count    INTEGER,
    polled_at_utc     TEXT,
    PRIMARY KEY (idpprofile_id, name),
    FOREIGN KEY (idpprofile_id)
        REFERENCES org_idp_profile_summary(id)
);

CREATE INDEX IF NOT EXISTS idx_idp_profile_overwrites_action
    ON org_idp_profile_overwrites (action);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT
EXISTS`, ArangoDB via collection upsert, Redis via key namespacing).
MistHelper does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (near line 3923, adjacent to the existing
`listOrgIdpProfiles` entry; single insert in the dict literal, no structural
change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # New entry 1: single-profile summary row, keyed by the profile UUID.
    "getOrgIdpProfile": {                                           # operationId from OpenAPI
        "type": "natural_pk",                                       # API supplies a stable UUID
        "primary_key": ["id"],                                      # profile UUID is the natural key
        "indexes": ["org_id", "name"],                              # fast filter by owning org / name
        "unique_constraints": [],                                   # PK already enforces uniqueness
        "description": "Single Org IDP profile (summary row)",      # human-readable purpose
    },

    # New entry 2: per-rule overwrite rows produced from the nested array.
    "getOrgIdpProfileOverwrites": {                                 # MistHelper-internal sub-table id
        "type": "composite_pk",                                     # PK is parent UUID + rule name
        "primary_key": ["idpprofile_id", "name"],                   # unique within a profile
        "indexes": ["action"],                                      # fast filter by alert/drop/close
        "unique_constraints": [],                                   # PK already enforces uniqueness
        "description": "Per-rule overwrites attached to an Org IDP profile",
    },
}
```

The `getOrgIdpProfileOverwrites` key is a MistHelper-internal identifier (the
Mist API has no operationId for it -- it is a flattened sub-array of the
parent response). This pattern matches how MistHelper already splits other
endpoints whose response contains nested arrays (see the spec 500 reference
for the same `<operationId>` + `<operationId>Details` convention).
