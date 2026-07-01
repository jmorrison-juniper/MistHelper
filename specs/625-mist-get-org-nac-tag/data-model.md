# Phase 1 Data Model: getOrgNacTag

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_nactags_nactag_id.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing one NAC (Network Access
Control) tag. NAC tags are building blocks referenced by NAC rules --
they match on attributes such as RADIUS group, certificate CN, LDAP realm,
or an ingress VLAN, and yield an action (assign VLAN, redirect, set RADIUS
attributes, etc.). MistHelper models this as a single flat row per tag; the
`type` column dictates which of the type-specific columns are populated.

### Entity 1: `NacTag`

One row per NAC tag.

| Field                    | Type    | Source                     | PK? | FK?          | Notes |
|--------------------------|---------|----------------------------|-----|--------------|-------|
| `id`                     | TEXT    | API `id`                   | YES | --           | UUID assigned by Mist. Stable for the lifetime of the tag. |
| `org_id`                 | TEXT    | API `org_id` (fallback: MistHelper context) | -- | sites.org_id | UUID. API returns it; MistHelper still injects the prompt value as a defensive fallback if the field is absent. Indexed. |
| `name`                   | TEXT    | API `name`                 | --  | --           | Human-readable tag name. Required, min length 1. Indexed. |
| `type`                   | TEXT    | API `type`                 | --  | --           | Enum: `egress_vlan_names`, `gbp_tag`, `match`, `radius_attrs`, `radius_group`, `radius_vendor_attrs`, `redirect_nacportal_id`, `session_timeout`, `username_attr`, `vlan`. Indexed. |
| `created_time`           | REAL    | API `created_time`         | --  | --           | Epoch seconds. Read-only. |
| `modified_time`          | REAL    | API `modified_time`        | --  | --           | Epoch seconds. Read-only. |
| `allow_usermac_override` | INTEGER | API `allow_usermac_override` | -- | --          | 0/1 bool. Default 0 (false). |
| `match`                  | TEXT    | API `match`                | --  | --           | Populated when `type=='match'`. Enum: `cert_cn`, `cert_eku`, `cert_issuer`, `cert_san`, `cert_serial`, `cert_sub`, `cert_template`, `client_mac`, `edr_status`, `gbp_tag`, `hostname`, `idp_role`, `ingress_vlan`, `mdm_status`, `nas_ip`, `radius_group`, `realm`, `ssid`, `user_name`, `usermac_label`. |
| `match_all`              | INTEGER | API `match_all`            | --  | --           | 0/1 bool. Applicable only when `type=='match'`. |
| `values_json`            | TEXT    | API `values` (JSON-encoded)| --  | --           | JSON array of match values when `type=='match'`. Preserves array shape in a single flat column. |
| `egress_vlan_names_json` | TEXT    | API `egress_vlan_names` (JSON-encoded) | -- | --  | JSON array of VLAN names when `type=='egress_vlan_names'`. |
| `radius_attrs_json`      | TEXT    | API `radius_attrs` (JSON-encoded) | -- | --      | JSON array of standard RADIUS attributes when `type=='radius_attrs'`. |
| `radius_group`           | TEXT    | API `radius_group`         | --  | --           | Populated when `type=='radius_group'`. |
| `radius_vendor_attrs_json` | TEXT  | API `radius_vendor_attrs` (JSON-encoded) | -- | --   | JSON array of vendor-specific RADIUS attributes when `type=='radius_vendor_attrs'`. |
| `gbp_tag_json`           | TEXT    | API `gbp_tag` (JSON-encoded) | -- | --          | JSON object when `type=='gbp_tag'`. |
| `nacportal_id`           | TEXT    | API `nacportal_id`         | --  | --           | UUID. Populated when `type=='redirect_nacportal_id'`. |
| `session_timeout`        | INTEGER | API `session_timeout`      | --  | --           | Seconds. Populated when `type=='session_timeout'`. |
| `username_attr`          | TEXT    | API `username_attr`        | --  | --           | Enum: `automatic`, `cn`, `dns`, `email`, `upn`. Populated when `type=='username_attr'`. |
| `vlan`                   | TEXT    | API `vlan`                 | --  | --           | Populated when `type=='vlan'`. |
| `polled_at_utc`          | TEXT    | MistHelper clock           | --  | --           | ISO8601 UTC timestamp of the poll, for audit. |

**Design note on JSON columns**: the response schema mixes scalar and array
fields keyed on `type`. Rather than exploding into per-type sub-tables (which
would multiply DDL for a single endpoint), MistHelper stores array/object
fields as JSON-encoded TEXT columns suffixed `_json`. This preserves full
fidelity, keeps the single-table PK model, and matches the CSV/SQLite
flattening convention used by other polymorphic Mist entities.

## State Transitions

N/A -- this is a read-only endpoint. NAC tags on the Mist side are edited
via `PUT /orgs/{org_id}/nactags/{nactag_id}` (separate spec, out of scope
here); MistHelper only captures snapshots. Each poll overwrites the prior
snapshot for the same `id` via SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- One row per NAC tag. Shared with the sibling listOrgNacTags menu (44) so
-- both list-and-single-record reads upsert into the same table.
CREATE TABLE IF NOT EXISTS org_nac_tags (
    id                        TEXT     NOT NULL,
    org_id                    TEXT,
    name                      TEXT,
    type                      TEXT,
    created_time              REAL,
    modified_time             REAL,
    allow_usermac_override    INTEGER,
    match                     TEXT,
    match_all                 INTEGER,
    values_json               TEXT,
    egress_vlan_names_json    TEXT,
    radius_attrs_json         TEXT,
    radius_group              TEXT,
    radius_vendor_attrs_json  TEXT,
    gbp_tag_json              TEXT,
    nacportal_id              TEXT,
    session_timeout           INTEGER,
    username_attr             TEXT,
    vlan                      TEXT,
    polled_at_utc             TEXT,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_org_nac_tags_org_id ON org_nac_tags (org_id);
CREATE INDEX IF NOT EXISTS idx_org_nac_tags_name   ON org_nac_tags (name);
CREATE INDEX IF NOT EXISTS idx_org_nac_tags_type   ON org_nac_tags (type);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via
`CREATE TABLE IF NOT EXISTS`, ArangoDB via collection upsert, Redis via key
namespacing). MistHelper does not run the DDL directly from the menu method.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no
structural change). If an entry for `getOrgNacTag` already exists (created
by an earlier catalog task), reuse and verify -- do not duplicate.

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Single NAC tag record, keyed by Mist-assigned UUID.
    'getOrgNacTag': {                                                              # operationId from OpenAPI
        'type': 'natural_pk',                                                      # id is a stable Mist-generated UUID
        'primary_key': ['id'],                                                     # single-column PK -- globally unique
        'indexes': ['org_id', 'name', 'type'],                                     # common filter columns for downstream queries
        'table': 'org_nac_tags',                                                   # shared with sibling listOrgNacTags menu
    },
}
```

The sibling operationId `listOrgNacTags` should point at the same table
(`org_nac_tags`) so both list and single-record reads upsert consistently.
That sibling entry is out of scope for this spec but must not be regressed by
this change.
