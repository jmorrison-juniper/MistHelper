# Phase 1 Data Model: getOrgNacPortal

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Source schema**: `documentation/api/orgs/GET_orgs_org_id_nacportals_nacportal_id.md`

## Entities

The endpoint returns a single JSON object representing a NAC portal. For
SQL-friendly storage, the response is split across three flat entities tied
by the parent portal `id`.

### Entity 1 -- `org_nac_portal` (parent)

Top-level scalar configuration. One row per portal per ingest. Upserts on
`(org_id, id)`.

| Field | Type | PK | FK | Source / Notes |
|-------|------|----|----|----------------|
| `org_id` | TEXT | yes | -> orgs.id | Path parameter; injected at write time |
| `id` | TEXT | yes | -- | Portal UUID (equals path `nacportal_id`) |
| `name` | TEXT | -- | -- | Portal display name |
| `type` | TEXT | -- | -- | enum: `guest_admin`, `guest_portal`, `marvis_client` |
| `access_type` | TEXT | -- | -- | When `type==marvis_client`: enum `wireless`, `wireless+wired` |
| `ssid` | TEXT | -- | -- | Associated SSID, if any |
| `eap_type` | TEXT | -- | -- | enum: `wpa2`, `wpa3` |
| `cert_expire_time` | INTEGER | -- | -- | Days |
| `expiry_notification_time` | INTEGER | -- | -- | Days |
| `notify_expiry` | INTEGER | -- | -- | 0/1; SQLite boolean |
| `enable_telemetry` | INTEGER | -- | -- | 0/1; SQLite boolean |
| `bg_image_url` | TEXT | -- | -- | Background image URL |
| `template_url` | TEXT | -- | -- | Portal template URL |
| `thumbnail_url` | TEXT | -- | -- | readOnly |
| `tos` | TEXT | -- | -- | Terms of service text/url |
| `ui_url` | TEXT | -- | -- | Guest admin URL (readOnly) |
| `portal_authorize_url` | TEXT | -- | -- | External-auth callback URL (readOnly) |
| `portal_authorize_jwt_secret` | TEXT | -- | -- | **Sensitive**; persisted, never logged |
| `portal_sso_url` | TEXT | -- | -- | SSO ACS URL (readOnly) |
| `portal_auth` | TEXT | -- | -- | Flattened from `portal.auth` |
| `portal_expire` | INTEGER | -- | -- | Flattened from `portal.expire` |
| `portal_external_portal_url` | TEXT | -- | -- | Flattened from `portal.external_portal_url` |
| `portal_force_reconnect` | INTEGER | -- | -- | Flattened from `portal.force_reconnect` (0/1) |
| `portal_forward` | INTEGER | -- | -- | Flattened from `portal.forward` (0/1) |
| `portal_forward_url` | TEXT | -- | -- | Flattened from `portal.forward_url` |
| `portal_max_num_devices` | INTEGER | -- | -- | Flattened from `portal.max_num_devices` (0-100) |
| `portal_privacy` | INTEGER | -- | -- | Flattened from `portal.privacy` (0/1) |
| `additional_cacerts_json` | TEXT | -- | -- | JSON-encoded array of PEM certs; **sensitive** |
| `additional_nac_server_name_json` | TEXT | -- | -- | JSON-encoded list of strings |
| `ingested_at` | TEXT | -- | -- | ISO-8601 timestamp; set by `DataExporter` |

### Entity 2 -- `org_nac_portal_sso` (child, 0..1 per portal)

Single-row child capturing the `sso` sub-object. Written only when `sso` is
present and non-null in the response.

| Field | Type | PK | FK | Source / Notes |
|-------|------|----|----|----------------|
| `org_id` | TEXT | yes | -> org_nac_portal.org_id | Composite PK part |
| `nacportal_id` | TEXT | yes | -> org_nac_portal.id | Composite PK part |
| `idp_cert` | TEXT | -- | -- | **Sensitive**; persisted, never logged |
| `idp_sign_algo` | TEXT | -- | -- | enum: `sha1`, `sha256`, `sha384`, `sha512` |
| `idp_sso_url` | TEXT | -- | -- | IdP SSO endpoint |
| `issuer` | TEXT | -- | -- | SAML issuer |
| `nameid_format` | TEXT | -- | -- | e.g. `email` |
| `use_sso_role_for_cert` | INTEGER | -- | -- | 0/1 |
| `ingested_at` | TEXT | -- | -- | ISO-8601 timestamp |

### Entity 3 -- `org_nac_portal_sso_role_matching` (child, 0..N per portal)

One row per element of `sso.sso_role_matching[]`.

| Field | Type | PK | FK | Source / Notes |
|-------|------|----|----|----------------|
| `org_id` | TEXT | yes | -> org_nac_portal.org_id | Composite PK part |
| `nacportal_id` | TEXT | yes | -> org_nac_portal.id | Composite PK part |
| `match_index` | INTEGER | yes | -- | 0-based array index; stable across re-runs of the same response |
| `assigned` | TEXT | -- | -- | Role assigned on match (e.g. `user`) |
| `match` | TEXT | -- | -- | SAML attribute value to match (e.g. `Student`) |
| `ingested_at` | TEXT | -- | -- | ISO-8601 timestamp |

## State Transitions

**N/A -- read-only endpoint.** `getOrgNacPortal` is a GET that returns the
current configuration of the portal. There are no state transitions owned by
this menu item. Lifecycle transitions (create/update/delete) belong to the
sibling write endpoints documented under `POST_orgs_org_id_nacportals.md`,
`PUT_orgs_org_id_nacportals_nacportal_id.md`, and
`DELETE_orgs_org_id_nacportals_nacportal_id.md`, each of which would be a
separate, destructive-tier MistHelper spec when needed.

## SQLite DDL Snippet

```sql
-- Parent: one row per (org, portal). Upsert on (org_id, id).
CREATE TABLE IF NOT EXISTS org_nac_portal (
    org_id                            TEXT NOT NULL,
    id                                TEXT NOT NULL,
    name                              TEXT,
    type                              TEXT,
    access_type                       TEXT,
    ssid                              TEXT,
    eap_type                          TEXT,
    cert_expire_time                  INTEGER,
    expiry_notification_time          INTEGER,
    notify_expiry                     INTEGER,
    enable_telemetry                  INTEGER,
    bg_image_url                      TEXT,
    template_url                      TEXT,
    thumbnail_url                     TEXT,
    tos                               TEXT,
    ui_url                            TEXT,
    portal_authorize_url              TEXT,
    portal_authorize_jwt_secret       TEXT,
    portal_sso_url                    TEXT,
    portal_auth                       TEXT,
    portal_expire                     INTEGER,
    portal_external_portal_url        TEXT,
    portal_force_reconnect            INTEGER,
    portal_forward                    INTEGER,
    portal_forward_url                TEXT,
    portal_max_num_devices            INTEGER,
    portal_privacy                    INTEGER,
    additional_cacerts_json           TEXT,
    additional_nac_server_name_json   TEXT,
    ingested_at                       TEXT,
    PRIMARY KEY (org_id, id)
);

CREATE INDEX IF NOT EXISTS idx_org_nac_portal_name
    ON org_nac_portal(name);
CREATE INDEX IF NOT EXISTS idx_org_nac_portal_type
    ON org_nac_portal(type);
CREATE INDEX IF NOT EXISTS idx_org_nac_portal_ssid
    ON org_nac_portal(ssid);

-- Child: 0 or 1 SSO block per portal. Upsert on (org_id, nacportal_id).
CREATE TABLE IF NOT EXISTS org_nac_portal_sso (
    org_id                  TEXT NOT NULL,
    nacportal_id            TEXT NOT NULL,
    idp_cert                TEXT,
    idp_sign_algo           TEXT,
    idp_sso_url             TEXT,
    issuer                  TEXT,
    nameid_format           TEXT,
    use_sso_role_for_cert   INTEGER,
    ingested_at             TEXT,
    PRIMARY KEY (org_id, nacportal_id)
);

-- Child: 0..N role-matching rules per portal. Upsert on (org_id, nacportal_id, match_index).
CREATE TABLE IF NOT EXISTS org_nac_portal_sso_role_matching (
    org_id          TEXT NOT NULL,
    nacportal_id    TEXT NOT NULL,
    match_index     INTEGER NOT NULL,
    assigned        TEXT,
    "match"         TEXT,
    ingested_at     TEXT,
    PRIMARY KEY (org_id, nacportal_id, match_index)
);
```

DataExporter creates these tables on first write via the existing
schema-inference path; the DDL above is the canonical reference for any
manual inspection.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary
in `MistHelper.py` (near the other org-config natural-PK entries):

```python
'getOrgNacPortal': {                                        # GET single NAC portal by UUID
    'type': 'natural_pk',                                   # Mist-assigned UUID is stable
    'primary_key': ['org_id', 'id'],                        # Composite for multi-tenant safety
    'indexes': ['name', 'type', 'ssid'],                    # Common NOC lookup fields
},
```

The child tables `org_nac_portal_sso` and `org_nac_portal_sso_role_matching`
inherit their PKs from the DDL above and do not need separate entries -- the
`ENDPOINT_PRIMARY_KEY_STRATEGIES` mapping is keyed on the API operationId,
which produces a single parent row plus dependent child rows in one ingest.

## Sensitive Field Handling

The fields `portal_authorize_jwt_secret`, `additional_cacerts_json`, and
`org_nac_portal_sso.idp_cert` are sensitive but must be persisted to the
configured output backend (that is the user's stated intent for reading the
endpoint). They must NEVER appear in any log line. The action-logging
contract in the new method excludes these fields by name; only `id`, `name`,
`type`, and counts (`sso_enabled`, `role_match_count`) are eligible for log
output.
