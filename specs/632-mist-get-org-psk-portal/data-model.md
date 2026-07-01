# Phase 1 Data Model: getOrgPskPortal

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_pskportals_pskportal_id.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing one PSK (pre-shared key)
self-service portal in an organization. MistHelper flattens this into one row
per portal in a single output table. Nested `passphrase_rules` and `sso`
sub-objects are collapsed into dotted-prefix columns; array fields
(`required_fields`, `sso.allowed_roles`) are serialized as JSON strings inside
their column so a single flat row shape works across CSV, SQLite, and
ArangoDB/Redis backends.

### Entity 1: `PskPortal`

One row per (org, PSK portal).

| Field                                | Type    | Source                          | PK? | FK?                | Notes |
|--------------------------------------|---------|---------------------------------|-----|--------------------|-------|
| `id`                                 | TEXT    | API `id`                        | YES | --                 | Read-only UUID assigned by Mist. Stable across polls. |
| `org_id`                             | TEXT    | API `org_id` (or MistHelper ctx)| --  | sites.org_id       | UUID of the parent org. Populated by MistHelper if missing from body. Indexed. |
| `name`                               | TEXT    | API `name`                      | --  | --                 | Required by API. Indexed for lookup by portal name. |
| `ssid`                               | TEXT    | API `ssid`                      | --  | --                 | Required by API. Intended SSID for the PSK. |
| `auth`                               | TEXT    | API `auth`                      | --  | --                 | Enum: `sponsor`, `sso`. |
| `type`                               | TEXT    | API `type`                      | --  | --                 | Enum: `admin`, `byod`. |
| `role`                               | TEXT    | API `role`                      | --  | --                 | Role assigned to PSKs from this portal. |
| `bg_image_url`                       | TEXT    | API `bg_image_url`              | --  | --                 | UI background image URL. |
| `thumbnail_url`                      | TEXT    | API `thumbnail_url`             | --  | --                 | UI thumbnail image URL. |
| `template_url`                       | TEXT    | API `template_url`              | --  | --                 | UI template URL. |
| `ui_url`                             | TEXT    | API `ui_url`                    | --  | --                 | Rendered portal UI URL. |
| `cleanup_psk`                        | INTEGER | API `cleanup_psk` (0/1)         | --  | --                 | Boolean, stored 0/1 in SQLite. |
| `expire_time`                        | INTEGER | API `expire_time`               | --  | --                 | PSK expiry in minutes. |
| `expiry_notification_time`           | INTEGER | API `expiry_notification_time`  | --  | --                 | Days before expiry to notify. |
| `hide_psks_created_by_other_admins`  | INTEGER | API field (0/1)                 | --  | --                 | Boolean. Only meaningful when `type==admin`. |
| `max_usage`                          | INTEGER | API `max_usage`                 | --  | --                 | 0 = unlimited. |
| `notification_renew_url`             | TEXT    | API `notification_renew_url`    | --  | --                 | Optional renewal URL sent in notification emails. |
| `notify_expiry`                      | INTEGER | API `notify_expiry` (0/1)       | --  | --                 | Boolean. |
| `notify_on_create_or_edit`           | INTEGER | API `notify_on_create_or_edit`  | --  | --                 | Boolean, default 0. |
| `required_fields_json`               | TEXT    | JSON of API `required_fields`   | --  | --                 | Required signup fields, JSON-encoded. |
| `vlan_id_json`                       | TEXT    | JSON of API `vlan_id`           | --  | --                 | Can be single VLAN or mapping; stored as JSON. |
| `passphrase_rules_alphabets_enabled` | INTEGER | API `passphrase_rules.alphabets_enabled` | -- | --          | Boolean 0/1. |
| `passphrase_rules_length`            | INTEGER | API `passphrase_rules.length`   | --  | --                 | 8..63. |
| `passphrase_rules_min_length`        | INTEGER | API `passphrase_rules.min_length` | -- | --                | 8..63. |
| `passphrase_rules_max_length`        | INTEGER | API `passphrase_rules.max_length` | -- | --                | 8..63; must be > min_length. |
| `passphrase_rules_numerics_enabled`  | INTEGER | API `passphrase_rules.numerics_enabled` | -- | --           | Boolean 0/1. |
| `passphrase_rules_symbols`           | TEXT    | API `passphrase_rules.symbols`  | --  | --                 | Allowed symbol characters. |
| `passphrase_rules_symbols_enabled`   | INTEGER | API `passphrase_rules.symbols_enabled` | -- | --            | Boolean 0/1. |
| `sso_allowed_roles_json`             | TEXT    | JSON of API `sso.allowed_roles` | --  | --                 | Only meaningful when `auth==sso`. |
| `sso_idp_cert`                       | TEXT    | API `sso.idp_cert`              | --  | --                 | SAML IdP cert (PEM). |
| `sso_idp_sign_algo`                  | TEXT    | API `sso.idp_sign_algo`         | --  | --                 | Enum: `sha1`, `sha256`, `sha384`, `sha512`. |
| `sso_idp_sso_url`                    | TEXT    | API `sso.idp_sso_url`           | --  | --                 | IdP SSO URL. |
| `sso_issuer`                         | TEXT    | API `sso.issuer`                | --  | --                 | SAML issuer. |
| `sso_nameid_format`                  | TEXT    | API `sso.nameid_format`         | --  | --                 | SAML NameID format URI. |
| `sso_role_mapping_json`              | TEXT    | JSON of API `sso.role_mapping`  | --  | --                 | Role-name -> SSO attribute map. |
| `sso_use_sso_role_for_psk_role`      | INTEGER | API `sso.use_sso_role_for_psk_role` (0/1) | -- | --        | Boolean; when true, `role` above is ignored. |
| `created_time`                       | REAL    | API `created_time`              | --  | --                 | Epoch seconds. Read-only. |
| `modified_time`                      | REAL    | API `modified_time`             | --  | --                 | Epoch seconds. Read-only. |
| `polled_at_utc`                      | TEXT    | MistHelper clock                | --  | --                 | ISO 8601 UTC timestamp of the poll, for audit. |

## State Transitions

N/A -- this is a strictly read-only endpoint. The underlying PSK portal object on
the Mist side may transition through Mist-driven configuration edits, but
MistHelper does not drive or model those transitions; it merely captures the
current configuration snapshot. Each successful invocation of menu 89 overwrites
the prior snapshot for the same `id` via SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- One row per PSK portal.
CREATE TABLE IF NOT EXISTS org_psk_portals (
    id                                    TEXT     NOT NULL PRIMARY KEY,
    org_id                                TEXT,
    name                                  TEXT,
    ssid                                  TEXT,
    auth                                  TEXT,
    type                                  TEXT,
    role                                  TEXT,
    bg_image_url                          TEXT,
    thumbnail_url                         TEXT,
    template_url                          TEXT,
    ui_url                                TEXT,
    cleanup_psk                           INTEGER,
    expire_time                           INTEGER,
    expiry_notification_time              INTEGER,
    hide_psks_created_by_other_admins     INTEGER,
    max_usage                             INTEGER,
    notification_renew_url                TEXT,
    notify_expiry                         INTEGER,
    notify_on_create_or_edit              INTEGER,
    required_fields_json                  TEXT,
    vlan_id_json                          TEXT,
    passphrase_rules_alphabets_enabled    INTEGER,
    passphrase_rules_length               INTEGER,
    passphrase_rules_min_length           INTEGER,
    passphrase_rules_max_length           INTEGER,
    passphrase_rules_numerics_enabled     INTEGER,
    passphrase_rules_symbols              TEXT,
    passphrase_rules_symbols_enabled      INTEGER,
    sso_allowed_roles_json                TEXT,
    sso_idp_cert                          TEXT,
    sso_idp_sign_algo                     TEXT,
    sso_idp_sso_url                       TEXT,
    sso_issuer                            TEXT,
    sso_nameid_format                     TEXT,
    sso_role_mapping_json                 TEXT,
    sso_use_sso_role_for_psk_role         INTEGER,
    created_time                          REAL,
    modified_time                         REAL,
    polled_at_utc                         TEXT
);

CREATE INDEX IF NOT EXISTS idx_org_psk_portals_org_id
    ON org_psk_portals (org_id);

CREATE INDEX IF NOT EXISTS idx_org_psk_portals_name
    ON org_psk_portals (name);

CREATE INDEX IF NOT EXISTS idx_org_psk_portals_ssid
    ON org_psk_portals (ssid);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT
EXISTS`, ArangoDB via collection upsert, Redis via key namespacing). MistHelper
does not run the DDL directly from the menu method.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no structural
change to the surrounding data structure).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # PSK self-service portal configuration record; one row per portal UUID.
    'getOrgPskPortal': {                                                      # operationId from OpenAPI
        'type': 'natural_pk',                                                 # id is a stable API-assigned UUID
        'primary_key': ['id'],                                                # portal UUID uniquely identifies the row
        'indexes': ['org_id', 'name', 'ssid'],                                # fast filter by org, name, or SSID
        'table': 'org_psk_portals',                                           # target SQLite table
    },
}
```

The `id` field is marked `readOnly: true` with a `uuid` content encoding in the
Mist OpenAPI schema, which guarantees it is stable for the life of the portal
and safe to use as the sole natural primary key. `INSERT OR REPLACE INTO
org_psk_portals (id, ...) VALUES (...)` implements the upsert on each poll.
