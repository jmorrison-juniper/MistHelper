# Phase 1 Data Model: getOrgServicePolicy

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_servicepolicies_servicepolicy_id.md`
(200 OK body).

## Entities

The endpoint returns a single JSON object describing one org-scoped Service
Policy. MistHelper splits this into two logical entities for clean multi-backend
persistence: a parent record and a child rule table (the `ewf` array).

### Entity 1: `ServicePolicy` (parent)

One row per (org, service policy).

| Field                | Type    | Source                  | PK? | FK?                | Notes |
|----------------------|---------|-------------------------|-----|--------------------|-------|
| `id`                 | TEXT    | API `id`                | YES | --                 | UUID; canonical Mist-side stable identifier. |
| `org_id`             | TEXT    | API `org_id` / context  | --  | sites.org_id       | UUID; injected before write if the API body omits it. |
| `name`               | TEXT    | API `name`              | --  | --                 | Human-friendly policy name. |
| `action`             | TEXT    | API `action`            | --  | --                 | Enum: `allow`, `deny`. |
| `local_routing`      | INTEGER | API `local_routing`     | --  | --                 | Boolean (0/1) -- access within same VRF. |
| `path_preference`    | TEXT    | API `path_preference`   | --  | --                 | Optional WAN path steering name. |
| `services`           | TEXT    | join(API `services`, ',') | -- | --                | Comma-joined for CSV; original list preserved in ArangoDB. |
| `tenants`            | TEXT    | join(API `tenants`, ',')  | -- | --                | Comma-joined for CSV; original list preserved in ArangoDB. |
| `aamw_enabled`       | INTEGER | API `aamw.enabled`      | --  | --                 | Boolean; SRX-only sub-field flattened. |
| `aamw_profile`       | TEXT    | API `aamw.profile`      | --  | --                 | Enum: `docsonly`, `executables`, `standard`. |
| `aamw_profile_id`    | TEXT    | API `aamw.aamwprofile_id` | -- | aamwprofiles.id  | UUID; takes precedence over `aamw_profile`. |
| `antivirus_enabled`  | INTEGER | API `antivirus.enabled` | --  | --                 | Boolean; SRX-only. |
| `antivirus_profile`  | TEXT    | API `antivirus.profile` | --  | --                 | Default / noftp / httponly / custom key. |
| `antivirus_profile_id` | TEXT  | API `antivirus.avprofile_id` | -- | avprofiles.id | UUID. |
| `appqoe_enabled`     | INTEGER | API `appqoe.enabled`    | --  | --                 | Boolean; SRX-only. |
| `secintel_enabled`   | INTEGER | API `secintel.enabled`  | --  | --                 | Boolean; SRX-only. |
| `secintel_profile`   | TEXT    | API `secintel.profile`  | --  | --                 | Enum: `default`, `standard`, `strict`. |
| `secintel_profile_id`| TEXT    | API `secintel.secintelprofile_id` | -- | --        | Not a UUID field per schema; stored verbatim. |
| `ssl_proxy_enabled`  | INTEGER | API `ssl_proxy.enabled` | --  | --                 | Boolean; SRX-only. |
| `ssl_proxy_ciphers_category` | TEXT | API `ssl_proxy.ciphers_category` | -- | --  | Enum: `medium`, `strong`, `weak`. |
| `idp_enabled`        | INTEGER | API `idp.enabled`       | --  | --                 | Boolean. |
| `idp_alert_only`     | INTEGER | API `idp.alert_only`    | --  | --                 | Boolean. |
| `idp_profile`        | TEXT    | API `idp.profile`       | --  | --                 | Default `strict`; enum values or custom key. |
| `idp_profile_id`     | TEXT    | API `idp.idpprofile_id` | --  | idpprofiles.id     | UUID; takes precedence over `idp_profile`. |
| `created_time`       | REAL    | API `created_time`      | --  | --                 | Epoch seconds; read-only. |
| `modified_time`      | REAL    | API `modified_time`     | --  | --                 | Epoch seconds; read-only. |
| `ewf_rule_count`     | INTEGER | len(API `ewf`)          | --  | --                 | Convenience count of the ewf child array. |
| `polled_at_utc`      | TEXT    | MistHelper clock        | --  | --                 | ISO8601 UTC timestamp of the poll, for audit. |

### Entity 2: `ServicePolicyEwfRule` (child)

Zero or more rows per (org, service policy). Source: each element of the API
`ewf` array. The ewf array has no per-item natural key in the response schema,
so MistHelper synthesizes `rule_index` from the array position.

| Field            | Type    | Source                       | PK? | FK?                              | Notes |
|------------------|---------|------------------------------|-----|----------------------------------|-------|
| `org_id`         | TEXT    | MistHelper context           | YES | org_service_policy.org_id        | UUID. |
| `servicepolicy_id` | TEXT  | MistHelper context (parent id) | YES | org_service_policy.id          | UUID; joins to parent. |
| `rule_index`     | INTEGER | Array position (0-based)     | YES | --                               | Synthesized to disambiguate. |
| `alert_only`     | INTEGER | API ewf[].alert_only         | --  | --                               | Boolean. |
| `block_message`  | TEXT    | API ewf[].block_message      | --  | --                               | Free text; example: "Access to this URL Category has been blocked". |
| `enabled`        | INTEGER | API ewf[].enabled            | --  | --                               | Boolean. |
| `profile`        | TEXT    | API ewf[].profile            | --  | --                               | Enum: `critical`, `standard`, `strict`. |
| `polled_at_utc`  | TEXT    | MistHelper clock             | --  | --                               | ISO8601 UTC timestamp of the poll, for audit. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying *service policy object* on
the Mist side can be modified by PUT / DELETE via separate operationIds, but
MistHelper does not drive or model those transitions in this menu item; it
merely captures snapshots. Each poll overwrites the prior snapshot for the same
`id` via SQLite `INSERT OR REPLACE`, and the ewf child rows are re-inserted
against `(org_id, servicepolicy_id, rule_index)` so a shrinking rule array does
not leave orphaned rows (implementation deletes prior child rows for the same
parent before insert -- documented in the quickstart flatten helper).

## SQLite DDL

```sql
-- Parent table: one row per (org, service policy).
CREATE TABLE IF NOT EXISTS org_service_policy (
    id                          TEXT     NOT NULL,
    org_id                      TEXT,
    name                        TEXT,
    action                      TEXT,
    local_routing               INTEGER,
    path_preference             TEXT,
    services                    TEXT,
    tenants                     TEXT,
    aamw_enabled                INTEGER,
    aamw_profile                TEXT,
    aamw_profile_id             TEXT,
    antivirus_enabled           INTEGER,
    antivirus_profile           TEXT,
    antivirus_profile_id        TEXT,
    appqoe_enabled              INTEGER,
    secintel_enabled            INTEGER,
    secintel_profile            TEXT,
    secintel_profile_id         TEXT,
    ssl_proxy_enabled           INTEGER,
    ssl_proxy_ciphers_category  TEXT,
    idp_enabled                 INTEGER,
    idp_alert_only              INTEGER,
    idp_profile                 TEXT,
    idp_profile_id              TEXT,
    created_time                REAL,
    modified_time               REAL,
    ewf_rule_count              INTEGER,
    polled_at_utc               TEXT,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_org_service_policy_org_id
    ON org_service_policy (org_id);
CREATE INDEX IF NOT EXISTS idx_org_service_policy_name
    ON org_service_policy (name);
CREATE INDEX IF NOT EXISTS idx_org_service_policy_action
    ON org_service_policy (action);

-- Child table: zero-or-more rows per (org, service policy, ewf rule position).
CREATE TABLE IF NOT EXISTS org_service_policy_ewf (
    org_id            TEXT     NOT NULL,
    servicepolicy_id  TEXT     NOT NULL,
    rule_index        INTEGER  NOT NULL,
    alert_only        INTEGER,
    block_message     TEXT,
    enabled           INTEGER,
    profile           TEXT,
    polled_at_utc     TEXT,
    PRIMARY KEY (org_id, servicepolicy_id, rule_index),
    FOREIGN KEY (servicepolicy_id)
        REFERENCES org_service_policy(id)
);

CREATE INDEX IF NOT EXISTS idx_org_service_policy_ewf_profile
    ON org_service_policy_ewf (profile);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via
`CREATE TABLE IF NOT EXISTS`, ArangoDB via collection upsert, Redis via key
namespacing). MistHelper does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (two adjacent inserts in the dict literal, no
structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Parent row per org-scoped service policy, keyed by API-provided UUID.
    'getOrgServicePolicy': {                                                        # operationId from OpenAPI
        'type': 'natural_pk',                                                       # id is a stable UUID from Mist
        'primary_key': ['id'],                                                      # canonical policy identifier
        'indexes': ['org_id', 'name', 'action'],                                    # common filter columns
        'table': 'org_service_policy',                                              # target SQLite table for parent rows
    },

    # Child rows for the nested ewf rule array; synthetic rule_index disambiguates.
    'getOrgServicePolicyEwfRules': {                                                # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                     # no per-item UUID in the ewf schema
        'primary_key': ['org_id', 'servicepolicy_id', 'rule_index'],                # array position within the parent
        'indexes': ['profile'],                                                     # fast filter by ewf profile level
        'table': 'org_service_policy_ewf',                                          # target SQLite table for ewf rows
    },
}
```

The `getOrgServicePolicyEwfRules` key is a MistHelper-internal identifier (the
Mist API has no operationId for it -- it is a flattened sub-array of the parent
response). This pattern matches how MistHelper already splits other endpoints
whose response contains nested arrays.
