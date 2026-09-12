# Phase 1 Data Model: getOrgApiToken

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_apitokens_apitoken_id.md` (200 OK
body).

## Entities

The endpoint returns a single JSON object describing one Organization API
Token. MistHelper splits this into two logical entities for clean multi-
backend persistence: a summary row (one per token), and a fan-out of
privilege entries.

### Entity 1: `OrgApiToken`

One row per token. Reuses the existing `org_api_tokens` SQLite table that
backs menu 47's `listOrgApiTokens` export.

| Field          | Type     | Source                  | PK? | FK?                | Notes |
|----------------|----------|-------------------------|-----|--------------------|-------|
| `id`           | TEXT     | API `id`                | YES | --                 | UUID. Globally unique. Stable for lifetime of the token. |
| `org_id`       | TEXT     | API `org_id` (echoed from path) | -- | sites.org_id    | UUID. Indexed for per-org filtering. |
| `name`         | TEXT     | API `name`              | --  | --                 | Human label. Indexed. |
| `created_by`   | TEXT     | API `created_by`        | --  | --                 | Creator email; null if creator was deleted. |
| `created_time` | REAL     | API `created_time`      | --  | --                 | Epoch seconds. |
| `key`          | TEXT     | API `key`               | --  | --                 | Obfuscated preview only (e.g. `1qkb...QQCL`). Treated as sensitive: written to backend, never logged. |
| `last_used`    | REAL     | API `last_used`         | --  | --                 | Epoch seconds; null if never used. |
| `src_ips_csv`  | TEXT     | join(API `src_ips`, `,`)| --  | --                 | Convenience comma-joined string of allowed source IPs/CIDRs. |
| `privileges_count` | INTEGER | len(API `privileges`)| --  | --                 | Convenience count of the fan-out array. |
| `polled_at_utc`| TEXT     | MistHelper clock        | --  | --                 | ISO8601 UTC timestamp of the API call, for audit. |

### Entity 2: `OrgApiTokenPrivilege`

One row per element of `privileges[]`. The Mist OpenAPI declares
`minItems: 1` and `uniqueItems: true`, so every token has at least one
privilege row and no `(scope, scope_target)` collision occurs.

| Field           | Type    | Source                          | PK? | FK?                          | Notes |
|-----------------|---------|---------------------------------|-----|------------------------------|-------|
| `token_id`      | TEXT    | parent `id`                     | YES | org_api_tokens.id            | UUID. Joins to the summary table. |
| `scope`         | TEXT    | API `privileges[].scope`        | YES | --                           | Enum: `org`, `site`, `sitegroup`, `orgsites`. |
| `scope_target`  | TEXT    | API `privileges[].org_id` / `site_id` / `sitegroup_id`, or literal `"orgsites"` for `scope=orgsites` | YES | --     | The inner UUID matching `scope`. For `scope=orgsites` the literal string `"orgsites"` is stored so the PK column is never NULL. |
| `role`          | TEXT    | API `privileges[].role`         | --  | --                           | Enum: `admin`, `helpdesk`, `installer`, `read`, `write`. |
| `views_csv`     | TEXT    | join(API `privileges[].views`, `,`) | -- | --                       | Comma-joined custom UI views; empty string if absent. |
| `view_legacy`   | TEXT    | API `privileges[].view`         | --  | --                           | Deprecated single-view field; captured for forward audit, may be NULL. |
| `polled_at_utc` | TEXT    | MistHelper clock                | --  | --                           | ISO8601 UTC timestamp of the API call, for audit. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying Mist token may change
state (renamed, privileges edited, `last_used` advancing) but MistHelper does
not drive those transitions; it captures snapshots. Each poll overwrites the
prior row for the same `id` (summary) and same `(token_id, scope,
scope_target)` (privilege) via SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- Summary table: one row per organization API token. Shared with menu 47
-- (listOrgApiTokens) -- CREATE TABLE IF NOT EXISTS is idempotent so both
-- operations writing in either order is safe.
CREATE TABLE IF NOT EXISTS org_api_tokens (
    id                  TEXT     NOT NULL,
    org_id              TEXT,
    name                TEXT,
    created_by          TEXT,
    created_time        REAL,
    key                 TEXT,
    last_used           REAL,
    src_ips_csv         TEXT,
    privileges_count    INTEGER,
    polled_at_utc       TEXT,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_org_api_tokens_org_id
    ON org_api_tokens (org_id);
CREATE INDEX IF NOT EXISTS idx_org_api_tokens_name
    ON org_api_tokens (name);

-- Privileges fan-out table: one row per (token, scope, scope_target).
CREATE TABLE IF NOT EXISTS org_api_token_privileges (
    token_id            TEXT     NOT NULL,
    scope               TEXT     NOT NULL,
    scope_target        TEXT     NOT NULL,
    role                TEXT,
    views_csv           TEXT,
    view_legacy         TEXT,
    polled_at_utc       TEXT,
    PRIMARY KEY (token_id, scope, scope_target),
    FOREIGN KEY (token_id) REFERENCES org_api_tokens(id)
);

CREATE INDEX IF NOT EXISTS idx_org_api_token_privileges_scope
    ON org_api_token_privileges (scope);
CREATE INDEX IF NOT EXISTS idx_org_api_token_privileges_role
    ON org_api_token_privileges (role);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT
EXISTS`, ArangoDB via collection upsert, Redis via key namespacing).
MistHelper does not run this DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (near line 4626, immediately after the existing
`listOrgApiTokens` entry). Inline comments on every executable line per
Constitution Principle VI.

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Single-token GET. Same shape as listOrgApiTokens so the two ops share
    # the org_api_tokens SQLite table and upsert by token UUID.
    "getOrgApiToken": {                                                         # operationId from OpenAPI
        "type": "natural_pk",                                                   # token id is a stable UUID
        "primary_key": ["id"],                                                  # globally unique across orgs
        "indexes": ["org_id", "name"],                                          # speed up per-org and by-name lookups
        "unique_constraints": [],                                               # PK alone is sufficient
        "description": "Single organization API token detail (menu 195)",       # human-readable docstring
    },

    # Per-privilege fan-out emitted alongside the summary row. MistHelper-
    # internal id; the Mist API has no operationId for the sub-array.
    "getOrgApiTokenPrivileges": {                                               # MistHelper-internal sub-table id
        "type": "composite_pk",                                                 # uniquely identified by (token, scope, target)
        "primary_key": ["token_id", "scope", "scope_target"],                   # OpenAPI declares uniqueItems on the array
        "indexes": ["scope", "role"],                                           # support common ad-hoc filters
        "unique_constraints": [],                                               # PK alone is sufficient
        "description": "Privilege rows fanned out from getOrgApiToken (menu 195)",  # human-readable docstring
    },
}
```

The `getOrgApiTokenPrivileges` key is a MistHelper-internal identifier (the
Mist API has no operationId for it -- it is a flattened sub-array of the
parent response). This pattern matches how MistHelper already splits other
endpoints whose response contains nested arrays (see
`getOrgLicenseAsyncClaimStatusDetails` in spec 500).
