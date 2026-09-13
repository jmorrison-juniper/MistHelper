# Phase 1 Data Model: getMspSso

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/msps/GET_msps_msp_id_ssos_sso_id.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing one MSP-scoped SSO/IdP
configuration. MistHelper persists this as a single flattened row in the
`msp_ssos` table. Deeply nested sub-objects (`mxedge_proxy`, `openroaming`) are
serialized as JSON strings into dedicated TEXT columns to preserve structure
without forcing additional normalization tables for a single-record read.

### Entity 1: `MspSso`

One row per SSO `id`. Sourced 1:1 from the API response body unless noted.

| Field                       | Type    | Source / Notes |
|-----------------------------|---------|----------------|
| `id`                        | TEXT    | API `id` (UUID). **PRIMARY KEY**. Server-issued, globally unique, stable. |
| `msp_id`                    | TEXT    | API `msp_id` (UUID). Indexed. Read-only. |
| `org_id`                    | TEXT    | API `org_id` (UUID, may be NULL when SSO is MSP-scoped only). Indexed. Read-only. |
| `site_id`                   | TEXT    | API `site_id` (UUID, may be NULL). Read-only. |
| `name`                      | TEXT    | API `name`. Required by API schema. Indexed. |
| `idp_type`                  | TEXT    | API `idp_type` enum: `saml`/`ldap`/`mxedge_proxy`/`oauth`/`openroaming`. Indexed. |
| `domain`                    | TEXT    | API `domain`. Read-only. Used in SAML ACS/SLO URLs. |
| `created_time`              | REAL    | API `created_time` (epoch seconds). Read-only. |
| `modified_time`             | REAL    | API `modified_time` (epoch seconds). Read-only. |
| `custom_logout_url`         | TEXT    | API. SAML only. |
| `default_role`              | TEXT    | API. SAML only. |
| `idp_cert`                  | TEXT    | API. SAML only. **Sensitive** -- stored, never logged. |
| `idp_sign_algo`             | TEXT    | API. SAML only. Enum: `sha1`/`sha256`/`sha384`/`sha512`. |
| `idp_sso_url`               | TEXT    | API. SAML only. |
| `ignore_unmatched_roles`    | INTEGER | API. SAML only. SQLite boolean (0/1). |
| `issuer`                    | TEXT    | API. SAML only. |
| `nameid_format`             | TEXT    | API. SAML only. Enum: `email`/`unspecified`. |
| `role_attr_extraction`      | TEXT    | API. SAML only. |
| `role_attr_from`            | TEXT    | API. SAML only. Defaults to `Role`. |
| `ldap_base_dn`              | TEXT    | API. LDAP only. |
| `ldap_bind_dn`              | TEXT    | API. LDAP only. |
| `ldap_bind_password`        | TEXT    | API. LDAP only. **Sensitive** -- stored, never logged. |
| `ldap_cacerts_json`         | TEXT    | API `ldap_cacerts` array -> JSON string. LDAP only. **Sensitive**. |
| `ldap_client_cert`          | TEXT    | API. LDAP only. **Sensitive**. |
| `ldap_client_key`           | TEXT    | API. LDAP only. **Sensitive** -- stored, never logged. |
| `ldap_group_attr`           | TEXT    | API. LDAP custom only. Defaults to `memberOf`. |
| `ldap_group_dn`             | TEXT    | API. LDAP custom only. Defaults to `base_dn`. |
| `ldap_resolve_groups`       | INTEGER | API. LDAP only. SQLite boolean. |
| `ldap_server_hosts_json`    | TEXT    | API `ldap_server_hosts` array -> JSON string. |
| `ldap_type`                 | TEXT    | API. LDAP only. Enum: `azure`/`custom`/`google`/`okta`/`ping_identity`. |
| `ldap_user_filter`          | TEXT    | API. LDAP custom only. |
| `group_filter`              | TEXT    | API. LDAP custom only. |
| `member_filter`             | TEXT    | API. LDAP custom only. |
| `oauth_cc_client_id`        | TEXT    | API. OAuth only. |
| `oauth_cc_client_secret`    | TEXT    | API. OAuth only. **Sensitive** -- stored, never logged. |
| `oauth_discovery_url`       | TEXT    | API. OAuth only. |
| `oauth_ping_identity_region`| TEXT    | API. OAuth only. Enum: `us`/`ca`/`eu`/`asia`/`au`. |
| `oauth_provider_domain`     | TEXT    | API. OAuth only. |
| `oauth_ropc_client_id`      | TEXT    | API. OAuth only. |
| `oauth_ropc_client_secret`  | TEXT    | API. OAuth only. **Sensitive**. |
| `oauth_tenant_id`           | TEXT    | API. OAuth only. |
| `oauth_type`                | TEXT    | API. OAuth only. Enum: `azure`/`azure-gov`/`okta`/`ping_identity`. |
| `scim_enabled`              | INTEGER | API. OAuth only. SQLite boolean. |
| `scim_secret_token`         | TEXT    | API. OAuth only. **Sensitive** -- stored, never logged. |
| `mxedge_proxy_json`         | TEXT    | API `mxedge_proxy` object -> JSON string. mxedge_proxy only. Contains nested `auth_servers`/`acct_servers` with RADIUS `secret` values -- **Sensitive**. |
| `openroaming_json`          | TEXT    | API `openroaming` object -> JSON string. OpenRoaming only. Contains `wba_cert`. |
| `polled_at_utc`             | TEXT    | MistHelper clock. ISO8601 UTC timestamp of the read, for audit. |

### Sensitive Fields Summary (logging exclusion list)

The following columns hold credentials, certificates, or signed material and
MUST be excluded from every `INFO`/`DEBUG`/`WARNING` log line:

- `idp_cert`
- `ldap_bind_password`
- `ldap_cacerts_json`
- `ldap_client_cert`
- `ldap_client_key`
- `oauth_cc_client_secret`
- `oauth_ropc_client_secret`
- `scim_secret_token`
- `mxedge_proxy_json` (contains RADIUS shared secrets)
- `openroaming_json` (contains `wba_cert`)

Only `id`, `name`, `idp_type`, `msp_id`, and `org_id` appear in the after-call
`DEBUG` summary. Persistence to the configured backend is unaffected; the
restriction applies to log output only.

## State Transitions

N/A -- this is a read-only endpoint. The underlying SSO configuration may be
mutated by MSP admins through Mist's UI or PUT/POST/DELETE endpoints, but
MistHelper merely captures point-in-time snapshots. Each read overwrites the
prior row for the same `id` via SQLite `INSERT OR REPLACE`, with `polled_at_utc`
recording when the snapshot was taken.

## SQLite DDL

```sql
-- Single row per SSO id. Shared by every invocation of menu 59 across MSPs.
CREATE TABLE IF NOT EXISTS msp_ssos (
    id                          TEXT     NOT NULL,
    msp_id                      TEXT,
    org_id                      TEXT,
    site_id                     TEXT,
    name                        TEXT,
    idp_type                    TEXT,
    domain                      TEXT,
    created_time                REAL,
    modified_time               REAL,
    custom_logout_url           TEXT,
    default_role                TEXT,
    idp_cert                    TEXT,
    idp_sign_algo               TEXT,
    idp_sso_url                 TEXT,
    ignore_unmatched_roles      INTEGER,
    issuer                      TEXT,
    nameid_format               TEXT,
    role_attr_extraction        TEXT,
    role_attr_from              TEXT,
    ldap_base_dn                TEXT,
    ldap_bind_dn                TEXT,
    ldap_bind_password          TEXT,
    ldap_cacerts_json           TEXT,
    ldap_client_cert            TEXT,
    ldap_client_key             TEXT,
    ldap_group_attr             TEXT,
    ldap_group_dn               TEXT,
    ldap_resolve_groups         INTEGER,
    ldap_server_hosts_json      TEXT,
    ldap_type                   TEXT,
    ldap_user_filter            TEXT,
    group_filter                TEXT,
    member_filter               TEXT,
    oauth_cc_client_id          TEXT,
    oauth_cc_client_secret      TEXT,
    oauth_discovery_url         TEXT,
    oauth_ping_identity_region  TEXT,
    oauth_provider_domain       TEXT,
    oauth_ropc_client_id        TEXT,
    oauth_ropc_client_secret    TEXT,
    oauth_tenant_id             TEXT,
    oauth_type                  TEXT,
    scim_enabled                INTEGER,
    scim_secret_token           TEXT,
    mxedge_proxy_json           TEXT,
    openroaming_json            TEXT,
    polled_at_utc               TEXT,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_msp_ssos_msp_id    ON msp_ssos (msp_id);
CREATE INDEX IF NOT EXISTS idx_msp_ssos_org_id    ON msp_ssos (org_id);
CREATE INDEX IF NOT EXISTS idx_msp_ssos_name      ON msp_ssos (name);
CREATE INDEX IF NOT EXISTS idx_msp_ssos_idp_type  ON msp_ssos (idp_type);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT
EXISTS`, ArangoDB via collection upsert, Redis via key namespacing). MistHelper
does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no structural
change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Single SSO config row per natural Mist UUID, shared across all MSPs.
    'getMspSso': {                                                              # operationId from OpenAPI
        'type': 'natural_pk',                                                   # server-issued stable UUID
        'primary_key': ['id'],                                                  # the SSO UUID returned in the body
        'indexes': ['msp_id', 'org_id', 'name', 'idp_type'],                    # common NOC query columns
        'table': 'msp_ssos',                                                    # target SQLite table
    },
}
```

The key `'getMspSso'` is the OpenAPI `operationId` exactly as documented in
`documentation/api/msps/GET_msps_msp_id_ssos_sso_id.md`. The DataExporter
looks this string up when persisting rows produced by the menu method.
