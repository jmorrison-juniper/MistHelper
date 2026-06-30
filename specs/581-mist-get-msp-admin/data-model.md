# Phase 1 Data Model: getMspAdmin

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/msps/GET_msps_msp_id_admins_admin_id.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing one MSP administrator. MistHelper
splits this into two logical entities for clean multi-backend persistence and SQL
queryability.

### Entity 1: `MspAdmin`

One row per (MSP, admin).

| Field                   | Type    | Source                | PK? | FK?            | Notes |
|-------------------------|---------|-----------------------|-----|----------------|-------|
| `msp_id`                | TEXT    | MistHelper context    | YES | --             | UUID supplied by user / URL path; injected before write. |
| `admin_id`              | TEXT    | API `admin_id`        | YES | --             | UUID, server-assigned, read-only. |
| `email`                 | TEXT    | API `email`           | --  | --             | Absent for Org API Token admins. PII -- written to backends, never to logs. |
| `first_name`            | TEXT    | API `first_name`      | --  | --             | PII -- write only. |
| `last_name`             | TEXT    | API `last_name`       | --  | --             | PII -- write only. |
| `name`                  | TEXT    | API `name`            | --  | --             | Only populated for Org API Token admins. |
| `phone`                 | TEXT    | API `phone`           | --  | --             | PII -- write only. |
| `phone2`                | TEXT    | API `phone2`          | --  | --             | PII -- write only. |
| `enable_two_factor`     | INTEGER | API `enable_two_factor` | -- | --             | 0/1 from boolean. Read-only on the API side. |
| `two_factor_verified`   | INTEGER | API `two_factor_verified` | -- | --           | 0/1 from boolean. Read-only on the API side. |
| `oauth_google`          | INTEGER | API `oauth_google`    | --  | --             | 0/1 from boolean. Read-only on the API side. |
| `via_sso`               | INTEGER | API `via_sso`         | --  | --             | 0/1 from boolean. Read-only on the API side. |
| `compliance_status`     | TEXT    | API `compliance_status` | --  | --           | Enum: `blocked`, `restricted`. |
| `expire_time`           | INTEGER | API `expire_time`     | --  | --             | Epoch seconds. |
| `hours`                 | INTEGER | API `hours`           | --  | --             | Invite validity window (1-168, default 24). |
| `no_tracking`           | INTEGER | API `no_tracking`     | --  | --             | Nullable boolean -> NULL / 0 / 1. EU privacy flag. |
| `password_modified_time`| REAL    | API `password_modified_time` | -- | --        | Epoch seconds. |
| `session_expiry`        | INTEGER | API `session_expiry`  | --  | --             | Minutes (10-20160), read-only. |
| `tags`                  | TEXT    | API `tags`            | --  | --             | JSON-encoded list, read-only. |
| `privilege_count`       | INTEGER | len(API `privileges`) | --  | --             | Convenience count for fast filtering. |
| `polled_at_utc`         | TEXT    | MistHelper clock      | --  | --             | ISO8601 UTC timestamp of the poll, for audit. |

### Entity 2: `MspAdminPrivilege`

Zero-or-more rows per (MSP, admin). One row per element of the response's
`privileges` array.

| Field            | Type    | Source                                                  | PK? | FK?                              | Notes |
|------------------|---------|---------------------------------------------------------|-----|----------------------------------|-------|
| `msp_id`         | TEXT    | MistHelper context                                      | YES | msp_admins.msp_id                | URL path value. |
| `admin_id`       | TEXT    | MistHelper context (from parent)                        | YES | msp_admins.admin_id              | Parent admin UUID. |
| `scope`          | TEXT    | API privileges[].scope                                  | YES | --                               | Enum: `msp`, `org`, `orggroup`, `site`, `sitegroup`. |
| `scope_target`   | TEXT    | MistHelper-injected scope-specific id                   | YES | --                               | See `_flatten_admin_privileges` rule below. |
| `role`           | TEXT    | API privileges[].role                                   | --  | --                               | Enum: `admin`, `helpdesk`, `installer`, `read`, `write`. |
| `name`           | TEXT    | API privileges[].name                                   | --  | --                               | Org/site/MSP display name, read-only. |
| `org_id`         | TEXT    | API privileges[].org_id                                 | --  | --                               | Present when scope=org. |
| `org_name`       | TEXT    | API privileges[].org_name                               | --  | --                               | Read-only display name. |
| `site_id`        | TEXT    | API privileges[].site_id                                | --  | --                               | Present when scope=site. |
| `msp_name`       | TEXT    | API privileges[].msp_name                               | --  | --                               | Read-only display name. |
| `msp_url`        | TEXT    | API privileges[].msp_url                                | --  | --                               | Custom URL (Advanced tier only), read-only. |
| `msp_logo_url`   | TEXT    | API privileges[].msp_logo_url                           | --  | --                               | Logo URL (Advanced tier only), read-only. |
| `sitegroup_ids`  | TEXT    | API privileges[].sitegroup_ids                          | --  | --                               | JSON-encoded list of UUIDs. |
| `orggroup_ids`   | TEXT    | API privileges[].orggroup_ids                           | --  | --                               | JSON-encoded list of UUIDs. |
| `views`          | TEXT    | API privileges[].views                                  | --  | --                               | JSON-encoded list of custom UI views. |
| `polled_at_utc`  | TEXT    | MistHelper clock                                        | --  | --                               | ISO8601 UTC timestamp. |

**`scope_target` derivation rule** (implemented in `_flatten_admin_privileges`):

| scope value  | scope_target source                              |
|--------------|--------------------------------------------------|
| `msp`        | `privileges[].msp_id`                            |
| `org`        | `privileges[].org_id`                            |
| `site`       | `privileges[].site_id`                           |
| `sitegroup`  | first element of `privileges[].sitegroup_ids`    |
| `orggroup`   | first element of `privileges[].orggroup_ids`     |

Group-scoped admins (`sitegroup` / `orggroup`) with multiple group IDs are flattened
to one row per group ID, with `scope_target` set to each group ID in turn -- preserving
the natural PK uniqueness contract.

## State Transitions

N/A -- this is a read-only endpoint. The underlying admin record on the Mist side
transitions through invite -> active -> revoked, but MistHelper does not drive or
model those transitions; it merely captures snapshots. Each poll overwrites the prior
snapshot for the same `(msp_id, admin_id)` tuple (and child privilege rows) via
SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- Summary table: one row per (MSP, admin).
CREATE TABLE IF NOT EXISTS msp_admins (
    msp_id                  TEXT     NOT NULL,
    admin_id                TEXT     NOT NULL,
    email                   TEXT,
    first_name              TEXT,
    last_name               TEXT,
    name                    TEXT,
    phone                   TEXT,
    phone2                  TEXT,
    enable_two_factor       INTEGER,
    two_factor_verified     INTEGER,
    oauth_google            INTEGER,
    via_sso                 INTEGER,
    compliance_status       TEXT,
    expire_time             INTEGER,
    hours                   INTEGER,
    no_tracking             INTEGER,
    password_modified_time  REAL,
    session_expiry          INTEGER,
    tags                    TEXT,
    privilege_count         INTEGER,
    polled_at_utc           TEXT,
    PRIMARY KEY (msp_id, admin_id)
);

CREATE INDEX IF NOT EXISTS idx_msp_admins_email
    ON msp_admins (email);
CREATE INDEX IF NOT EXISTS idx_msp_admins_compliance
    ON msp_admins (compliance_status);

-- Detail table: zero-or-more rows per (MSP, admin, scope, scope_target).
CREATE TABLE IF NOT EXISTS msp_admin_privileges (
    msp_id           TEXT NOT NULL,
    admin_id         TEXT NOT NULL,
    scope            TEXT NOT NULL,
    scope_target     TEXT NOT NULL,
    role             TEXT,
    name             TEXT,
    org_id           TEXT,
    org_name         TEXT,
    site_id          TEXT,
    msp_name         TEXT,
    msp_url          TEXT,
    msp_logo_url     TEXT,
    sitegroup_ids    TEXT,
    orggroup_ids     TEXT,
    views            TEXT,
    polled_at_utc    TEXT,
    PRIMARY KEY (msp_id, admin_id, scope, scope_target),
    FOREIGN KEY (msp_id, admin_id)
        REFERENCES msp_admins(msp_id, admin_id)
);

CREATE INDEX IF NOT EXISTS idx_msp_admin_privileges_org
    ON msp_admin_privileges (org_id);
CREATE INDEX IF NOT EXISTS idx_msp_admin_privileges_site
    ON msp_admin_privileges (site_id);
CREATE INDEX IF NOT EXISTS idx_msp_admin_privileges_role
    ON msp_admin_privileges (role);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`,
ArangoDB via collection upsert, Redis via key namespacing). MistHelper does not run
the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no structural
change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Summary row per (MSP, admin), keyed by the two URL path UUIDs.
    'getMspAdmin': {                                                                # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of business fields
        'primary_key': ['msp_id', 'admin_id'],                                      # stable URL path identifiers
        'indexes': ['email', 'compliance_status'],                                  # fast filter by email + compliance
        'table': 'msp_admins',                                                      # target SQLite table for summary
    },

    # Per-privilege rows produced from the response's `privileges` array.
    'getMspAdminPrivileges': {                                                      # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                     # composite of parent FK + scope key
        'primary_key': ['msp_id', 'admin_id', 'scope', 'scope_target'],             # unique per privilege grant
        'indexes': ['org_id', 'site_id', 'role'],                                   # support common operator queries
        'table': 'msp_admin_privileges',                                            # target SQLite table for privileges
    },
}
```

The `getMspAdminPrivileges` key is a MistHelper-internal identifier (the Mist API
has no operationId for it -- it is a flattened sub-array of the parent response).
This pattern matches how MistHelper already splits other endpoints whose response
contains nested arrays.
