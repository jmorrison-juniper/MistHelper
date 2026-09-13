# Phase 1 Data Model: getOrgPsk

**Feature**: 631-mist-get-org-psk
**Date**: 2026-06-30
**Source of truth**: `documentation/api/orgs/GET_orgs_org_id_psks_psk_id.md`

## Entity: `OrgPskDetail`

The endpoint returns a single PSK (Pre-Shared Key) object. It is the same shape
as one element of the `listOrgPsks` array response, but fetched by explicit ID.

### Fields

| Field                         | JSON Type              | SQLite Type | Nullable | Notes |
|-------------------------------|------------------------|-------------|----------|-------|
| `id`                          | string (uuid)          | TEXT        | No       | **PRIMARY KEY**. Server-assigned. `readOnly`. |
| `org_id`                      | string (uuid)          | TEXT        | No       | FK -> `orgs.id`. `readOnly`. Indexed. |
| `site_id`                     | string (uuid)          | TEXT        | Yes      | FK -> `sites.id`. `readOnly`. Present when PSK is site-scoped. Indexed. |
| `name`                        | string                 | TEXT        | No       | Required per schema. |
| `ssid`                        | string                 | TEXT        | No       | Required per schema. Indexed. |
| `passphrase`                  | string (8-64 chars)    | TEXT        | No       | Required per schema. **SECRET** -- never logged. |
| `old_passphrase`              | string                 | TEXT        | Yes      | Previous passphrase after rotation. **SECRET** -- never logged. |
| `usage`                       | string enum            | TEXT        | Yes      | One of `macs`, `multi`, `single`. |
| `mac`                         | string                 | TEXT        | Yes      | Bound MAC when `usage=single`. |
| `macs`                        | array<string>          | TEXT (JSON) | Yes      | List of MACs / patterns when `usage=macs`. Serialized as JSON string in SQLite. |
| `max_usage`                   | integer                | INTEGER     | Yes      | Default 0 (unlimited). Org-only. |
| `vlan_id`                     | object                 | TEXT (JSON) | Yes      | VLAN spec object. Serialized as JSON. |
| `role`                        | string (0-32)          | TEXT        | Yes      | Optional role label. |
| `email`                       | string                 | TEXT        | Yes      | Notification recipient. |
| `notify_expiry`               | boolean                | INTEGER     | Yes      | Default `false`. |
| `notify_on_create_or_edit`    | boolean                | INTEGER     | Yes      | |
| `expire_time`                 | integer (int32, epoch) | INTEGER     | Yes      | Null = no expiration. |
| `expiry_notification_time`    | integer (int32, days)  | INTEGER     | Yes      | Days before expiry to notify. |
| `admin_sso_id`                | string                 | TEXT        | Yes      | Portal-created PSK SSO id. `readOnly`. |
| `created_time`                | number (epoch)         | REAL        | Yes      | `readOnly`. |
| `modified_time`               | number (epoch)         | REAL        | Yes      | `readOnly`. |

### Primary Key

- **Type**: Natural primary key
- **Column**: `id` (server-assigned UUID)
- **Rationale**: The Mist API guarantees `id` is stable and globally unique
  across the organization. `INSERT OR REPLACE` on this key gives clean
  upserts.

### Foreign Keys

- `org_id` -> logical FK to `orgs.id` (SQLite does not enforce; ArangoDB
  edge collection `PSKBelongsToOrg` handles the graph relation per spec 188).
- `site_id` -> logical FK to `sites.id` when non-null (ArangoDB edge
  `PSKBelongsToSite` per spec 188).

### State Transitions

**N/A -- read-only endpoint.** This operation retrieves a snapshot of an
existing PSK. The PSK itself has a lifecycle (create -> [rotate] -> [expire]
-> delete) driven by POST/PUT/DELETE endpoints that are OUT OF SCOPE for
this spec (see spec.md Out of Scope section). No client-side state machine
is required for this GET operation.

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS org_psk_detail (
    id                       TEXT PRIMARY KEY,
    org_id                   TEXT NOT NULL,
    site_id                  TEXT,
    name                     TEXT NOT NULL,
    ssid                     TEXT NOT NULL,
    passphrase               TEXT NOT NULL,
    old_passphrase           TEXT,
    usage                    TEXT,
    mac                      TEXT,
    macs                     TEXT,
    max_usage                INTEGER DEFAULT 0,
    vlan_id                  TEXT,
    role                     TEXT,
    email                    TEXT,
    notify_expiry            INTEGER DEFAULT 0,
    notify_on_create_or_edit INTEGER,
    expire_time              INTEGER,
    expiry_notification_time INTEGER,
    admin_sso_id             TEXT,
    created_time             REAL,
    modified_time            REAL
);

CREATE INDEX IF NOT EXISTS idx_org_psk_detail_org_id  ON org_psk_detail(org_id);
CREATE INDEX IF NOT EXISTS idx_org_psk_detail_site_id ON org_psk_detail(site_id);
CREATE INDEX IF NOT EXISTS idx_org_psk_detail_ssid    ON org_psk_detail(ssid);
```

The DataExporter creates this table lazily on first write; no migration script
is required. Boolean fields (`notify_expiry`, `notify_on_create_or_edit`) are
stored as 0/1 integers per SQLite convention. Array (`macs`) and object
(`vlan_id`) fields are JSON-serialized to TEXT so a single row survives all
three backends without a schema fork.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py` (adjacent to the existing `"listOrgPsks"` entry at line ~3103):

```python
"getOrgPsk": {                        # Single-record PSK fetch by ID (menu 96)
    "type": "natural_pk",             # Server-assigned UUID is stable
    "primary_key": ["id"],            # PSK UUID -> row identity
    "indexes": ["org_id",             # Scope lookups by organization
                "site_id",            # Scope lookups by site
                "ssid"],              # Operators search by network name
    "table_name": "org_psk_detail",   # SQLite / CSV artifact name
    "description": "getOrgPsk single-record fetch; upsert by id",
},
```

Every executable line above carries an inline comment per Constitution
Principle VI (NON-NEGOTIABLE Inline Comments). The dictionary entry itself is
one insertion; no other lines of the dictionary are modified.
