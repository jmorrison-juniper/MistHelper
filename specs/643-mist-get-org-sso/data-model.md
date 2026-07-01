# Phase 1 Data Model: getOrgSso

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_ssos_sso_id.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing one SSO configuration.
MistHelper splits this into up to three logical entities for clean multi-backend
persistence: one summary row plus two RADIUS server sub-tables that are only
populated when `idp_type=mxedge_proxy`.

### Entity 1: `OrgSso`

One row per SSO record. Wide sparse table -- IdP-specific fields are NULL when
`idp_type` does not use them.

| Field                        | Type    | Source                     | PK? | FK?          | Notes |
|------------------------------|---------|----------------------------|-----|--------------|-------|
| `id`                         | TEXT    | API `id`                   | YES | --           | Mist-assigned UUID; stable across polls. |
| `org_id`                     | TEXT    | API `org_id`               | --  | sites.org_id | Parent organization UUID. |
| `site_id`                    | TEXT    | API `site_id`              | --  | sites.id     | Present for site-scoped SSOs, else NULL. |
| `msp_id`                     | TEXT    | API `msp_id`               | --  | --           | Present for MSP-scoped SSOs, else NULL. |
| `name`                       | TEXT    | API `name`                 | --  | --           | **Required** per schema. |
| `idp_type`                   | TEXT    | API `idp_type`             | --  | --           | Enum: `saml`, `ldap`, `mxedge_proxy`, `oauth`, `openroaming`. Indexed. |
| `domain`                     | TEXT    | API `domain`               | --  | --           | Mist-generated SAML URL slug. |
| `created_time`               | REAL    | API `created_time`         | --  | --           | Epoch seconds. |
| `modified_time`              | REAL    | API `modified_time`        | --  | --           | Epoch seconds. |
| `custom_logout_url`          | TEXT    | API `custom_logout_url`    | --  | --           | SAML only. |
| `default_role`               | TEXT    | API `default_role`         | --  | --           | SAML only. |
| `idp_cert`                   | TEXT    | API `idp_cert`             | --  | --           | SAML only. **SECRET** -- persisted, never logged. |
| `idp_sign_algo`              | TEXT    | API `idp_sign_algo`        | --  | --           | SAML only. Enum: sha1/256/384/512. |
| `idp_sso_url`                | TEXT    | API `idp_sso_url`          | --  | --           | SAML only. |
| `ignore_unmatched_roles`     | INTEGER | API `ignore_unmatched_roles` | -- | --          | SAML only. 0/1 bool. |
| `issuer`                     | TEXT    | API `issuer`               | --  | --           | SAML only. |
| `nameid_format`              | TEXT    | API `nameid_format`        | --  | --           | SAML only. Enum: email/unspecified. |
| `role_attr_extraction`       | TEXT    | API `role_attr_extraction` | --  | --           | SAML only. |
| `role_attr_from`             | TEXT    | API `role_attr_from`       | --  | --           | SAML only. Default "Role". |
| `ldap_base_dn`               | TEXT    | API `ldap_base_dn`         | --  | --           | LDAP only. |
| `ldap_bind_dn`               | TEXT    | API `ldap_bind_dn`         | --  | --           | LDAP only. |
| `ldap_bind_password`         | TEXT    | API `ldap_bind_password`   | --  | --           | LDAP only. **SECRET**. |
| `ldap_cacerts`               | TEXT    | JSON(API `ldap_cacerts`)   | --  | --           | LDAP only. JSON array as text. |
| `ldap_client_cert`           | TEXT    | API `ldap_client_cert`     | --  | --           | LDAP only. |
| `ldap_client_key`            | TEXT    | API `ldap_client_key`      | --  | --           | LDAP only. **SECRET**. |
| `ldap_group_attr`            | TEXT    | API `ldap_group_attr`      | --  | --           | LDAP only. Default `memberOf`. |
| `ldap_group_dn`              | TEXT    | API `ldap_group_dn`        | --  | --           | LDAP only. |
| `ldap_resolve_groups`        | INTEGER | API `ldap_resolve_groups`  | --  | --           | LDAP only. 0/1 bool. |
| `ldap_server_hosts`          | TEXT    | JSON(API `ldap_server_hosts`) | -- | --          | LDAP only. JSON array as text. |
| `ldap_type`                  | TEXT    | API `ldap_type`            | --  | --           | LDAP only. Enum: azure/custom/google/okta/ping_identity. |
| `ldap_user_filter`           | TEXT    | API `ldap_user_filter`     | --  | --           | LDAP only. |
| `group_filter`               | TEXT    | API `group_filter`         | --  | --           | LDAP custom only. |
| `member_filter`              | TEXT    | API `member_filter`        | --  | --           | LDAP custom only. |
| `oauth_cc_client_id`         | TEXT    | API `oauth_cc_client_id`   | --  | --           | OAuth only. |
| `oauth_cc_client_secret`     | TEXT    | API `oauth_cc_client_secret` | -- | --          | OAuth only. **SECRET**. |
| `oauth_discovery_url`        | TEXT    | API `oauth_discovery_url`  | --  | --           | OAuth only. |
| `oauth_ping_identity_region` | TEXT    | API `oauth_ping_identity_region` | -- | --      | OAuth only. |
| `oauth_provider_domain`      | TEXT    | API `oauth_provider_domain` | -- | --           | OAuth Okta only. |
| `oauth_ropc_client_id`       | TEXT    | API `oauth_ropc_client_id` | --  | --           | OAuth ROPC only. |
| `oauth_ropc_client_secret`   | TEXT    | API `oauth_ropc_client_secret` | -- | --         | OAuth ROPC only. **SECRET**. |
| `oauth_tenant_id`            | TEXT    | API `oauth_tenant_id`      | --  | --           | OAuth only. |
| `oauth_type`                 | TEXT    | API `oauth_type`           | --  | --           | OAuth only. Enum: azure/azure-gov/okta/ping_identity. |
| `scim_enabled`               | INTEGER | API `scim_enabled`         | --  | --           | OAuth only. 0/1 bool. |
| `scim_secret_token`          | TEXT    | API `scim_secret_token`    | --  | --           | OAuth only. **SECRET**. |
| `mxedge_proxy_mxcluster_id`  | TEXT    | API `mxedge_proxy.mxcluster_id` | -- | --        | mxedge_proxy only. |
| `mxedge_proxy_operator_name` | TEXT    | API `mxedge_proxy.operator_name` | -- | --       | mxedge_proxy only. |
| `mxedge_proxy_proxy_hosts`   | TEXT    | JSON(API `mxedge_proxy.proxy_hosts`) | -- | --   | mxedge_proxy only. JSON array as text. |
| `mxedge_proxy_ssids`         | TEXT    | JSON(API `mxedge_proxy.ssids`) | -- | --         | mxedge_proxy only. JSON array as text. |
| `openroaming_ssids`          | TEXT    | JSON(API `openroaming.ssids`) | -- | --          | openroaming only. JSON array as text. |
| `openroaming_wba_cert`       | TEXT    | API `openroaming.wba_cert` | --  | --           | openroaming only. **SECRET**. |
| `fetched_at_utc`             | TEXT    | MistHelper clock           | --  | --           | ISO8601 UTC timestamp of the fetch, for audit. |

### Entity 2: `OrgSsoMxedgeProxyAuthServer`

Zero or more rows per SSO when `idp_type=mxedge_proxy`. Source: each element of
`mxedge_proxy.auth_servers[]`.

| Field                            | Type    | Source                | PK? | FK?                    | Notes |
|----------------------------------|---------|-----------------------|-----|------------------------|-------|
| `sso_id`                         | TEXT    | parent record `id`    | YES | org_sso.id             | Injected from parent before write. |
| `host`                           | TEXT    | API `host`            | YES | --                     | RADIUS server IP or hostname. |
| `port`                           | INTEGER | API `port`            | YES | --                     | Default 1812. |
| `secret`                         | TEXT    | API `secret`          | --  | --                     | **SECRET** -- RADIUS shared secret. |
| `timeout`                        | INTEGER | API `timeout`         | --  | --                     | Seconds; default 5. |
| `retry`                          | INTEGER | API `retry`           | --  | --                     | Default 2. |
| `require_message_authenticator`  | INTEGER | API `require_message_authenticator` | -- | --       | 0/1 bool. Default 0. |
| `fetched_at_utc`                 | TEXT    | MistHelper clock      | --  | --                     | Audit timestamp. |

### Entity 3: `OrgSsoMxedgeProxyAcctServer`

Zero or more rows per SSO when `idp_type=mxedge_proxy`. Source: each element of
`mxedge_proxy.acct_servers[]`.

| Field           | Type    | Source              | PK? | FK?         | Notes |
|-----------------|---------|---------------------|-----|-------------|-------|
| `sso_id`        | TEXT    | parent record `id`  | YES | org_sso.id  | Injected from parent before write. |
| `host`          | TEXT    | API `host`          | YES | --          | RADIUS accounting server IP or hostname. |
| `port`          | INTEGER | API `port`          | YES | --          | Default 1813. |
| `secret`        | TEXT    | API `secret`        | --  | --          | **SECRET** -- RADIUS shared secret. |
| `fetched_at_utc`| TEXT    | MistHelper clock    | --  | --          | Audit timestamp. |

## State Transitions

N/A -- read-only endpoint. Each poll overwrites the prior snapshot for the same
`id` via `INSERT OR REPLACE` (natural PK). RADIUS sub-array rows are also
upserted by `(sso_id, host, port)`. MistHelper does not model or drive SSO
lifecycle -- separate PUT/DELETE endpoints (out of scope for this spec) handle
mutations.

## SQLite DDL

```sql
-- Summary table: one row per SSO record, keyed by Mist UUID.
CREATE TABLE IF NOT EXISTS org_sso (
    id                              TEXT     NOT NULL PRIMARY KEY,
    org_id                          TEXT,
    site_id                         TEXT,
    msp_id                          TEXT,
    name                            TEXT     NOT NULL,
    idp_type                        TEXT,
    domain                          TEXT,
    created_time                    REAL,
    modified_time                   REAL,
    custom_logout_url               TEXT,
    default_role                    TEXT,
    idp_cert                        TEXT,
    idp_sign_algo                   TEXT,
    idp_sso_url                     TEXT,
    ignore_unmatched_roles          INTEGER,
    issuer                          TEXT,
    nameid_format                   TEXT,
    role_attr_extraction            TEXT,
    role_attr_from                  TEXT,
    ldap_base_dn                    TEXT,
    ldap_bind_dn                    TEXT,
    ldap_bind_password              TEXT,
    ldap_cacerts                    TEXT,
    ldap_client_cert                TEXT,
    ldap_client_key                 TEXT,
    ldap_group_attr                 TEXT,
    ldap_group_dn                   TEXT,
    ldap_resolve_groups             INTEGER,
    ldap_server_hosts               TEXT,
    ldap_type                       TEXT,
    ldap_user_filter                TEXT,
    group_filter                    TEXT,
    member_filter                   TEXT,
    oauth_cc_client_id              TEXT,
    oauth_cc_client_secret          TEXT,
    oauth_discovery_url             TEXT,
    oauth_ping_identity_region      TEXT,
    oauth_provider_domain           TEXT,
    oauth_ropc_client_id            TEXT,
    oauth_ropc_client_secret        TEXT,
    oauth_tenant_id                 TEXT,
    oauth_type                      TEXT,
    scim_enabled                    INTEGER,
    scim_secret_token               TEXT,
    mxedge_proxy_mxcluster_id       TEXT,
    mxedge_proxy_operator_name      TEXT,
    mxedge_proxy_proxy_hosts        TEXT,
    mxedge_proxy_ssids              TEXT,
    openroaming_ssids               TEXT,
    openroaming_wba_cert            TEXT,
    fetched_at_utc                  TEXT
);

CREATE INDEX IF NOT EXISTS idx_org_sso_org_id   ON org_sso (org_id);
CREATE INDEX IF NOT EXISTS idx_org_sso_name     ON org_sso (name);
CREATE INDEX IF NOT EXISTS idx_org_sso_idp_type ON org_sso (idp_type);

-- RADIUS auth server sub-table (only populated when idp_type=mxedge_proxy).
CREATE TABLE IF NOT EXISTS org_sso_mxedge_proxy_auth_servers (
    sso_id                          TEXT     NOT NULL,
    host                            TEXT     NOT NULL,
    port                            INTEGER  NOT NULL,
    secret                          TEXT,
    timeout                         INTEGER,
    retry                           INTEGER,
    require_message_authenticator   INTEGER,
    fetched_at_utc                  TEXT,
    PRIMARY KEY (sso_id, host, port),
    FOREIGN KEY (sso_id) REFERENCES org_sso(id)
);

CREATE INDEX IF NOT EXISTS idx_org_sso_auth_servers_sso_id
    ON org_sso_mxedge_proxy_auth_servers (sso_id);

-- RADIUS accounting server sub-table (only populated when idp_type=mxedge_proxy).
CREATE TABLE IF NOT EXISTS org_sso_mxedge_proxy_acct_servers (
    sso_id                          TEXT     NOT NULL,
    host                            TEXT     NOT NULL,
    port                            INTEGER  NOT NULL,
    secret                          TEXT,
    fetched_at_utc                  TEXT,
    PRIMARY KEY (sso_id, host, port),
    FOREIGN KEY (sso_id) REFERENCES org_sso(id)
);

CREATE INDEX IF NOT EXISTS idx_org_sso_acct_servers_sso_id
    ON org_sso_mxedge_proxy_acct_servers (sso_id);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT
EXISTS`, ArangoDB via collection upsert, Redis via key namespacing). MistHelper
does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following three entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (dict-literal inserts, no structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # SSO summary row, keyed by the Mist-assigned SSO UUID.
    'getOrgSso': {                                                                  # operationId from OpenAPI
        'type': 'natural_pk',                                                       # Mist-assigned stable UUID
        'primary_key': ['id'],                                                      # single-column PK
        'indexes': ['org_id', 'name', 'idp_type'],                                  # fast filters used by the UI
        'table': 'org_sso',                                                         # target SQLite table
    },

    # RADIUS auth servers under mxedge_proxy (variable-length array).
    'getOrgSsoMxedgeProxyAuthServers': {                                            # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                     # composite of parent + endpoint
        'primary_key': ['sso_id', 'host', 'port'],                                  # unique per SSO/host/port
        'indexes': ['sso_id'],                                                      # fast child lookup
        'table': 'org_sso_mxedge_proxy_auth_servers',                               # target SQLite table
    },

    # RADIUS accounting servers under mxedge_proxy (variable-length array).
    'getOrgSsoMxedgeProxyAcctServers': {                                            # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                     # composite of parent + endpoint
        'primary_key': ['sso_id', 'host', 'port'],                                  # unique per SSO/host/port
        'indexes': ['sso_id'],                                                      # fast child lookup
        'table': 'org_sso_mxedge_proxy_acct_servers',                               # target SQLite table
    },
}
```

The `getOrgSsoMxedgeProxyAuthServers` and `getOrgSsoMxedgeProxyAcctServers`
keys are MistHelper-internal identifiers -- the Mist API has no separate
operationId for them; they are flattened sub-arrays of the parent `getOrgSso`
response. This pattern matches how MistHelper already splits other endpoints
whose response contains nested arrays.
