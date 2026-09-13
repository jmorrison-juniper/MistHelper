# Phase 1 Data Model: getOrgNacRule

**Feature**: 624-mist-get-org-nac-rule
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Contract**: [contracts/get_org_nac_rule.md](./contracts/get_org_nac_rule.md)

This document captures the entities, fields, primary keys, foreign keys, state
model, SQLite DDL, and `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry for the
single-object response of `getOrgNacRule`.

---

## Entities

The endpoint returns exactly one entity: a `nac_rule`. It has two nested
sub-objects (`matching` and `not_matching`) which share the same schema
(`nac_rule_matching`). MistHelper flattens both sub-objects into the parent
row with `matching_` and `not_matching_` column prefixes. Array-typed fields
(`apply_tags`, `matching_family`, `matching_mfg`, etc.) are serialized to
semicolon-delimited strings (`"a;b;c"`) so a single CSV row / SQLite row
holds the whole rule.

### Entity: `org_nac_rule`

| Field | Type | PK / FK | Nullable | Description |
|-------|------|---------|----------|-------------|
| `id` | TEXT (UUID) | PRIMARY KEY | NO | Unique ID of the NAC rule in the Mist Organization (from API `id`) |
| `org_id` | TEXT (UUID) | FK -> `org.id` | NO | Owning organization (from API `org_id`; falls back to prompted value if API omits it) |
| `name` | TEXT | | NO | Rule name (required by schema) |
| `action` | TEXT | | NO | `allow` or `block` (required by schema) |
| `enabled` | INTEGER (bool) | | NO | 1 if rule enabled, 0 otherwise (default 1) |
| `order` | INTEGER | | YES | Rule priority; lower number = higher priority |
| `guest_auth_state` | TEXT | | YES | `authorized` or `unknown`; only meaningful for guest-portal rules |
| `apply_tags` | TEXT | | YES | Semicolon-joined list of tag UUIDs to inject into Access-Accept |
| `created_time` | REAL | | YES | Epoch seconds when rule was created (API readOnly) |
| `modified_time` | REAL | | YES | Epoch seconds when rule was last modified (API readOnly) |
| `matching_auth_type` | TEXT | | YES | Match on auth type: `cert`, `device-auth`, `eap-teap`, `eap-tls`, `eap-ttls`, `idp`, `mab`, `eap-peap` |
| `matching_family` | TEXT | | YES | Semicolon-joined device families to match |
| `matching_mfg` | TEXT | | YES | Semicolon-joined manufacturers to match |
| `matching_model` | TEXT | | YES | Semicolon-joined models to match |
| `matching_os_type` | TEXT | | YES | Semicolon-joined OS types to match |
| `matching_vendor` | TEXT | | YES | Semicolon-joined vendors to match |
| `matching_nactags` | TEXT | | YES | Semicolon-joined NAC tag UUIDs to match |
| `matching_port_types` | TEXT | | YES | Semicolon-joined port types (`wired`, `wireless`) |
| `matching_site_ids` | TEXT | | YES | Semicolon-joined site UUIDs to match |
| `matching_sitegroup_ids` | TEXT | | YES | Semicolon-joined sitegroup UUIDs to match |
| `not_matching_auth_type` | TEXT | | YES | Negated version of matching_auth_type |
| `not_matching_family` | TEXT | | YES | Negated version of matching_family |
| `not_matching_mfg` | TEXT | | YES | Negated version of matching_mfg |
| `not_matching_model` | TEXT | | YES | Negated version of matching_model |
| `not_matching_os_type` | TEXT | | YES | Negated version of matching_os_type |
| `not_matching_vendor` | TEXT | | YES | Negated version of matching_vendor |
| `not_matching_nactags` | TEXT | | YES | Negated version of matching_nactags |
| `not_matching_port_types` | TEXT | | YES | Negated version of matching_port_types |
| `not_matching_site_ids` | TEXT | | YES | Negated version of matching_site_ids |
| `not_matching_sitegroup_ids` | TEXT | | YES | Negated version of matching_sitegroup_ids |
| `misthelper_fetched_at` | REAL | | NO | Epoch seconds when MistHelper wrote this row (audit) |

### Referential integrity

- `org_id` foreign-key references the `org` table (populated by the sites /
  org-info menus). SQLite `FOREIGN KEY` is declared but not enforced by
  default; NOC users can query "list rules per org" via join.
- Elements of `apply_tags`, `matching_nactags`, `not_matching_nactags` are
  UUIDs of NAC tags managed via `listOrgNacTags` (adjacent menu). The
  semicolon-joined string is treated as opaque here; a dedicated
  many-to-many table would over-engineer this feature.
- Elements of `matching_site_ids` and `not_matching_site_ids` reference
  `site.id` from the sites tables.
- Elements of `matching_sitegroup_ids` and `not_matching_sitegroup_ids`
  reference `org_sitegroup.id` from the sitegroups tables.

## State Transitions

**N/A -- read-only endpoint.** `getOrgNacRule` is a pure GET. MistHelper
never mutates the rule; it only snapshots current state. Rule lifecycle
transitions (create, update, enable/disable, reorder, delete) are the
responsibility of separate PUT/POST/DELETE endpoints, each of which
belongs in its own future spec.

The only "state" MistHelper itself tracks is:

- `misthelper_fetched_at` -- appended per row on write.
- SQLite upsert semantics: `INSERT OR REPLACE` overwrites the previous
  snapshot of the same `id`, so re-running the menu item yields the
  latest state without duplicate rows.

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS org_nac_rule (
    id                          TEXT    PRIMARY KEY,
    org_id                      TEXT    NOT NULL,
    name                        TEXT    NOT NULL,
    action                      TEXT    NOT NULL,
    enabled                     INTEGER NOT NULL DEFAULT 1,
    "order"                     INTEGER,
    guest_auth_state            TEXT,
    apply_tags                  TEXT,
    created_time                REAL,
    modified_time               REAL,
    matching_auth_type          TEXT,
    matching_family             TEXT,
    matching_mfg                TEXT,
    matching_model              TEXT,
    matching_os_type            TEXT,
    matching_vendor             TEXT,
    matching_nactags            TEXT,
    matching_port_types         TEXT,
    matching_site_ids           TEXT,
    matching_sitegroup_ids      TEXT,
    not_matching_auth_type      TEXT,
    not_matching_family         TEXT,
    not_matching_mfg            TEXT,
    not_matching_model          TEXT,
    not_matching_os_type        TEXT,
    not_matching_vendor         TEXT,
    not_matching_nactags        TEXT,
    not_matching_port_types     TEXT,
    not_matching_site_ids       TEXT,
    not_matching_sitegroup_ids  TEXT,
    misthelper_fetched_at       REAL    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_org_nac_rule_org_id  ON org_nac_rule(org_id);
CREATE INDEX IF NOT EXISTS idx_org_nac_rule_name    ON org_nac_rule(name);
CREATE INDEX IF NOT EXISTS idx_org_nac_rule_action  ON org_nac_rule(action);
CREATE INDEX IF NOT EXISTS idx_org_nac_rule_enabled ON org_nac_rule(enabled);
```

Notes:
- `order` is quoted because it is a SQLite reserved word.
- Boolean `enabled` is stored as INTEGER (0/1) per SQLite convention; the
  flatten step converts Python `True`/`False` -> `1`/`0`.
- Epoch timestamps are stored as REAL (SQLite has no dedicated timestamp
  type); Python `float()` cast on the raw number is sufficient.
- The table is created lazily on first write by the existing
  `DataExporter` SQLite backend using the columns present in the flat
  dict; the DDL above documents the target shape.

## `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry

Add the following key to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (near the other `natural_pk` entries for
config objects):

```python
'getOrgNacRule': {                     # OperationId as declared by Mist OpenAPI + mistapi SDK
    'type': 'natural_pk',              # Rule id is a stable UUID assigned by Mist Cloud
    'primary_key': ['id'],             # Single-column PK (readOnly, uuid)
    'indexes': [                       # Secondary indexes for common NOC queries
        'org_id',                      # Filter by owning org
        'name',                        # Human-readable lookup
        'action',                      # Filter by allow / block
        'enabled',                     # Filter enabled vs disabled rules
    ],
},
```

The `DataExporter` SQLite backend reads this entry to (a) know the
`INSERT OR REPLACE` clause to emit and (b) create the secondary indexes
on first write.
