# Phase 1 Data Model: GetOrgTemplate

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-07-01

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_templates_template_id.md` (200 OK
body).

## Entities

The endpoint returns a single JSON object describing one WLAN template in an
organization. MistHelper splits it into two logical entities for clean multi-
backend persistence: the parent template row, and the flattened scope-mapping
rows extracted from `applies` and `exceptions`.

### Entity 1: `WlanTemplate`

Exactly one row per template UUID.

| Field                    | Type    | Source                        | PK? | FK?          | Notes |
|--------------------------|---------|-------------------------------|-----|--------------|-------|
| `id`                     | TEXT    | API `id`                      | YES | --           | Template UUID; stable natural key. |
| `org_id`                 | TEXT    | API `org_id`                  | --  | orgs.id      | Owning org UUID. Indexed. |
| `name`                   | TEXT    | API `name`                    | --  | --           | Required per schema. Indexed. |
| `filter_by_deviceprofile`| INTEGER | API `filter_by_deviceprofile` | --  | --           | Boolean stored as 0/1. |
| `deviceprofile_ids_json` | TEXT    | JSON(API `deviceprofile_ids`) | --  | --           | JSON-encoded string of the UUID array. Preserves order and lets SQL clients still see the list; individual device-profile joins are out of scope for this menu. |
| `applies_org_id`         | TEXT    | API `applies.org_id`          | --  | orgs.id      | Optional; present when the template applies to the whole org. |
| `applies_site_count`     | INTEGER | len(API `applies.site_ids`)   | --  | --           | Convenience count for quick summary queries. |
| `applies_sitegroup_count`| INTEGER | len(API `applies.sitegroup_ids`) | -- | --         | Convenience count. |
| `exceptions_site_count`  | INTEGER | len(API `exceptions.site_ids`)| --  | --           | Convenience count. |
| `exceptions_sitegroup_count` | INTEGER | len(API `exceptions.sitegroup_ids`) | -- | --  | Convenience count. |
| `created_time`           | REAL    | API `created_time`            | --  | --           | Epoch seconds; read-only from Mist. |
| `modified_time`          | REAL    | API `modified_time`           | --  | --           | Epoch seconds; read-only from Mist. |
| `polled_at_utc`          | TEXT    | MistHelper clock              | --  | --           | ISO8601 UTC timestamp of the fetch, for audit. |

### Entity 2: `WlanTemplateScope`

Zero-or-more rows per template. Rows are emitted for every element of
`applies.site_ids`, `applies.sitegroup_ids`, `exceptions.site_ids`, and
`exceptions.sitegroup_ids`. The `scope_type` column distinguishes source and
kind.

| Field         | Type | Source                              | PK? | FK?                     | Notes |
|---------------|------|-------------------------------------|-----|-------------------------|-------|
| `template_id` | TEXT | MistHelper context (parent `id`)    | YES | org_wlan_templates.id   | Joins to parent row. |
| `scope_type`  | TEXT | MistHelper flattener                | YES | --                      | Enum: `applies_site`, `applies_sitegroup`, `exceptions_site`, `exceptions_sitegroup`. |
| `scope_id`    | TEXT | API `applies.site_ids[i]` etc.      | YES | sites.id / sitegroups.id| UUID of the referenced site or sitegroup. Indexed. |
| `polled_at_utc` | TEXT | MistHelper clock                  | --  | --                      | ISO8601 UTC timestamp of the fetch, for audit. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying template on the Mist side
transitions through create -> update -> delete lifecycle events, but
MistHelper does not drive or model those transitions here; it merely captures
snapshots. Each poll overwrites the prior snapshot for the same template `id`
(parent) and `(template_id, scope_type, scope_id)` tuple (child) via SQLite
`INSERT OR REPLACE`.

## SQLite DDL

```sql
-- Parent table: one row per WLAN template UUID.
CREATE TABLE IF NOT EXISTS org_wlan_templates (
    id                          TEXT     NOT NULL,
    org_id                      TEXT     NOT NULL,
    name                        TEXT     NOT NULL,
    filter_by_deviceprofile     INTEGER,
    deviceprofile_ids_json      TEXT,
    applies_org_id              TEXT,
    applies_site_count          INTEGER,
    applies_sitegroup_count     INTEGER,
    exceptions_site_count       INTEGER,
    exceptions_sitegroup_count  INTEGER,
    created_time                REAL,
    modified_time               REAL,
    polled_at_utc               TEXT,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_wlan_templates_org_id
    ON org_wlan_templates (org_id);

CREATE INDEX IF NOT EXISTS idx_wlan_templates_name
    ON org_wlan_templates (name);

-- Child table: zero-or-more rows per template covering applies/exceptions.
CREATE TABLE IF NOT EXISTS org_wlan_template_scopes (
    template_id     TEXT     NOT NULL,
    scope_type      TEXT     NOT NULL,
    scope_id        TEXT     NOT NULL,
    polled_at_utc   TEXT,
    PRIMARY KEY (template_id, scope_type, scope_id),
    FOREIGN KEY (template_id) REFERENCES org_wlan_templates(id)
);

CREATE INDEX IF NOT EXISTS idx_wlan_template_scopes_scope_type
    ON org_wlan_template_scopes (scope_type);

CREATE INDEX IF NOT EXISTS idx_wlan_template_scopes_scope_id
    ON org_wlan_template_scopes (scope_id);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT
EXISTS`, ArangoDB via collection upsert, Redis via key namespacing).
MistHelper does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing
`ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in `MistHelper.py` (two inserts
in the dict literal, no structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Parent WLAN-template row, keyed by the Mist-supplied template UUID.
    'getOrgTemplate': {                                                          # operationId from OpenAPI
        'type': 'natural_pk',                                                    # stable UUID supplied by Mist
        'primary_key': ['id'],                                                   # single-column PK on the template UUID
        'indexes': ['org_id', 'name'],                                           # common filter columns
        'table': 'org_wlan_templates',                                           # target SQLite table for parent rows
    },

    # Flattened scope rows extracted from applies / exceptions arrays.
    'getOrgTemplateScopes': {                                                    # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                  # composite of parent FK + scope discriminator + scope UUID
        'primary_key': ['template_id', 'scope_type', 'scope_id'],                # uniquely identifies one scope-mapping row
        'indexes': ['scope_type', 'scope_id'],                                   # fast filter by discriminator or by target UUID
        'table': 'org_wlan_template_scopes',                                     # target SQLite table for scope rows
    },
}
```

The `getOrgTemplateScopes` key is a MistHelper-internal identifier (Mist has
no operationId for the flattened sub-arrays -- they are nested inside the
parent response). This pattern matches how MistHelper already splits other
endpoints whose response contains nested arrays (see the license-detail
example in spec 500).
