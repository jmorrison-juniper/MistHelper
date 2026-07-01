# Phase 1 Data Model: getOrgSsoRole

**Feature**: 644-mist-get-org-sso-role
**Endpoint**: `GET /api/v1/orgs/{org_id}/ssoroles/{ssorole_id}`
**Source schema**: `documentation/api/orgs/GET_orgs_org_id_ssoroles_ssorole_id.md`

## Entities

The 200 response is a single `sso_role` object containing an inline `privileges`
array. MistHelper flattens this into two related entities.

### Entity 1: `org_sso_role_summary`

One row per SSO role. Captures the role-level metadata.

| Field           | Type       | Nullable | Notes                                                 |
|-----------------|------------|----------|-------------------------------------------------------|
| `org_id`        | TEXT       | No       | Foreign scope -- supplied by the user, not the API.   |
| `id`            | TEXT (UUID)| No       | Role UUID (`readOnly`).                               |
| `name`          | TEXT       | No       | Human-readable role name (required by API).           |
| `for_site`      | INTEGER    | Yes      | 0/1 boolean (`readOnly`). NULL when API omits.        |
| `msp_id`        | TEXT (UUID)| Yes      | Present when the org lives under an MSP (`readOnly`). |
| `created_time`  | REAL       | Yes      | Epoch seconds (`readOnly`).                           |
| `modified_time` | REAL       | Yes      | Epoch seconds (`readOnly`).                           |
| `privilege_count` | INTEGER  | No       | Denormalized count of associated privileges.          |
| `misthelper_fetched_at` | TEXT | No     | ISO-8601 UTC timestamp of the export run.             |

**Primary Key**: `(org_id, id)` -- composite natural key (strategy type `natural_pk`).
**Foreign Keys**: None enforced (SQLite pragma left default); `org_id` is a logical
FK to the org context; `id` is a logical FK to `org_sso_role_privileges.ssorole_id`.

### Entity 2: `org_sso_role_privileges`

Zero or more rows per SSO role. One row per privilege entry inside the role's
`privileges` array.

| Field              | Type    | Nullable | Notes                                                                 |
|--------------------|---------|----------|-----------------------------------------------------------------------|
| `org_id`           | TEXT    | No       | Parent org (denormalized for namespacing).                            |
| `ssorole_id`       | TEXT    | No       | Parent SSO role UUID.                                                 |
| `scope`            | TEXT    | No       | Enum: `org`, `site`, `sitegroup`, `orgsites`.                         |
| `scope_target_id`  | TEXT    | Yes      | Denormalized `org_id` / `site_id` / `sitegroup_id` per `scope`. NULL for `orgsites`. |
| `role`             | TEXT    | No       | Enum: `admin`, `helpdesk`, `installer`, `read`, `write`.              |
| `views`            | TEXT    | Yes      | Comma-joined subset of custom UI-view enum values.                    |
| `view_legacy`      | TEXT    | Yes      | Deprecated single `view` field, kept for backward compatibility.      |
| `misthelper_fetched_at` | TEXT | No    | ISO-8601 UTC timestamp of the export run.                             |

**Primary Key**: `(org_id, ssorole_id, scope, scope_target_id, role)` -- composite
natural key (strategy type `composite_pk`). `scope_target_id` participates in the key
so a role can hold two different privileges at the same scope-type but different
targets (e.g. `read` on site A and `write` on site B).
**Foreign Keys**: Logical FK on `(org_id, ssorole_id)` -> `org_sso_role_summary(org_id, id)`.

## State Transitions

**N/A -- read-only endpoint.** `getOrgSsoRole` is a pure GET with no side effects.
Row state on disk transitions only via successful re-runs (INSERT OR REPLACE) or via
external SQLite manipulation, both of which are outside the endpoint contract.

## SQLite DDL

Emitted lazily by `DataExporter` on first write. The DDL below is the canonical
target; `DatabaseSchemaUtils` may add additional columns when the API introduces new
fields (schema evolution is additive).

```sql
CREATE TABLE IF NOT EXISTS org_sso_role_summary (
    org_id                TEXT    NOT NULL,
    id                    TEXT    NOT NULL,
    name                  TEXT    NOT NULL,
    for_site              INTEGER,
    msp_id                TEXT,
    created_time          REAL,
    modified_time         REAL,
    privilege_count       INTEGER NOT NULL,
    misthelper_fetched_at TEXT    NOT NULL,
    PRIMARY KEY (org_id, id)
);

CREATE INDEX IF NOT EXISTS idx_org_sso_role_summary_name
    ON org_sso_role_summary(name);

CREATE TABLE IF NOT EXISTS org_sso_role_privileges (
    org_id                TEXT NOT NULL,
    ssorole_id            TEXT NOT NULL,
    scope                 TEXT NOT NULL,
    scope_target_id       TEXT,
    role                  TEXT NOT NULL,
    views                 TEXT,
    view_legacy           TEXT,
    misthelper_fetched_at TEXT NOT NULL,
    PRIMARY KEY (org_id, ssorole_id, scope, scope_target_id, role)
);

CREATE INDEX IF NOT EXISTS idx_org_sso_role_privileges_role
    ON org_sso_role_privileges(role);
CREATE INDEX IF NOT EXISTS idx_org_sso_role_privileges_scope
    ON org_sso_role_privileges(scope);
```

## `ENDPOINT_PRIMARY_KEY_STRATEGIES` Entry

Add the following entries to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict in
`MistHelper.py` (near line ~1672). The `getOrgSsoRole` operationId maps to two
logical output tables, both keyed by natural composite columns.

```python
'getOrgSsoRole': {
    'type': 'natural_pk',
    'primary_key': ['org_id', 'id'],
    'indexes': ['name'],
    'table_name': 'org_sso_role_summary',
    'child_tables': {
        'org_sso_role_privileges': {
            'type': 'composite_pk',
            'primary_key': [
                'org_id',
                'ssorole_id',
                'scope',
                'scope_target_id',
                'role',
            ],
            'indexes': ['role', 'scope'],
        },
    },
},
```

Notes on the entry:

- `type: 'natural_pk'` reflects the parent-table strategy; the child table declares
  its own `composite_pk` because its identity is defined by the tuple, not by a
  single stable UUID.
- `indexes` covers the two most likely user filters: role name (summary table) and
  role/scope enum values (privileges table).
- `child_tables` mirrors the existing convention used by other multi-table
  exporters (see the reference plan for `getOrgLicenseAsyncClaimStatus`).
