# Phase 1 Data Model: getOrgApplicationList

Branch: `597-mist-get-org-application-list`
Date: 2026-06-29
Endpoint: `GET /api/v1/orgs/{org_id}/wxtags/apps`
Reference schema: `documentation/api/orgs/GET_orgs_org_id_wxtags_apps.md`

## Entities

The endpoint returns a single entity collection: a flat array of
`WxTagApplication` records. There are no nested objects or sub-resources.

### Entity: WxTagApplication

The pre-defined application signature used by WxTags and WxRules for traffic
classification.

| Field    | Type   | Required | Source              | Notes                                                                  |
|----------|--------|----------|---------------------|------------------------------------------------------------------------|
| `org_id` | string (UUID) | Yes (added)   | Path parameter       | Enriched onto every row by MistHelper before persistence. Not part of the upstream payload. |
| `group`  | string | Yes (API) | Response body        | High-level category, e.g. `"Emails"`, `"Streaming"`, `"Social"`.       |
| `key`    | string | Yes (API) | Response body        | Stable machine identifier within the group, e.g. `"gmail"`, `"netflix"`. |
| `name`   | string | Yes (API) | Response body        | Human-readable display label, e.g. `"Gmail - web/app"`.                |

#### Primary Key

Composite: `(org_id, group, key)`.

Rationale:
- The upstream payload has no `id` field, so a natural single-column PK is unavailable.
- `key` alone is not guaranteed unique across `group` boundaries within an org.
- `(group, key)` alone is not guaranteed unique across orgs in a multi-tenant SQLite
  installation.
- The composite `(org_id, group, key)` is stable, deterministic, and supports clean
  `INSERT OR REPLACE` upserts on repeated runs.

#### Foreign Keys

- `org_id` references the logical `orgs` table populated by `listOrgs` /
  `listOrgSites` exports. No FK constraint is enforced at the SQLite level (consistent
  with the rest of MistHelper's loose schema policy), but the relationship is
  documented for ArangoDB graph edges in spec 188 and downstream joins.

#### Secondary Indexes

- `name` -- supports the common NOC-engineer query "find me the app whose name
  contains 'zoom'" without forcing a full table scan.

## State Transitions

**N/A -- read-only endpoint.** `getOrgApplicationList` exposes the Mist Cloud's
internal application-signature catalog; MistHelper consumes the snapshot at call time
and writes it to local storage. There are no client-side state transitions, no
lifecycle stages, and no edit semantics. Each invocation is an idempotent read that
either overwrites (CSV) or upserts (SQLite / ArangoDB) the existing rows.

## SQLite DDL

The exact DDL is materialized at runtime by `DataExporter` from the registered
primary-key strategy. The equivalent hand-rolled schema is:

```sql
CREATE TABLE IF NOT EXISTS org_wxtag_applications (
    org_id TEXT NOT NULL,
    "group" TEXT NOT NULL,
    "key"   TEXT NOT NULL,
    name    TEXT NOT NULL,
    PRIMARY KEY (org_id, "group", "key")
);

CREATE INDEX IF NOT EXISTS idx_org_wxtag_applications_name
    ON org_wxtag_applications (name);
```

Notes:
- `group` and `key` are reserved-ish identifiers in SQL; they are double-quoted in DDL
  and parameterized everywhere else. `DataExporter` already quotes column names
  defensively when emitting DDL, so the registered strategy needs no special escaping.
- All columns are `TEXT NOT NULL`; the Mist API marks `group`, `key`, and `name` as
  required, and the enriched `org_id` is always supplied by MistHelper before write.
- The `INSERT OR REPLACE` upsert path provided by `DataExporter` for `composite_pk`
  strategies handles re-runs without duplicate-key violations.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py` (currently around line 1672):

```python
'getOrgApplicationList': {
    'type': 'composite_pk',
    'primary_key': ['org_id', 'group', 'key'],
    'indexes': ['name'],
},
```

Every line above carries an inline comment in the actual implementation per
Constitution Principle VI -- e.g.:

```python
'getOrgApplicationList': {  # WxTag application catalog: array of {group, key, name}
    'type': 'composite_pk',  # No upstream id field; identity is (org_id, group, key)
    'primary_key': ['org_id', 'group', 'key'],  # org_id enriched client-side
    'indexes': ['name'],  # Support fuzzy "find by display name" lookups
},
```

## Cross-Backend Notes

- **CSV**: One row per `WxTagApplication`, four columns
  (`org_id, group, key, name`), header row included by default.
- **SQLite**: Single table `org_wxtag_applications` per the DDL above. Upsert via
  `INSERT OR REPLACE` on composite PK.
- **ArangoDB + Redis** (per spec 188): Vertex collection `org_wxtag_applications`;
  document `_key` derived as `<org_id>__<group>__<key>` (double-underscore separator
  is the project convention). No edges are introduced by this endpoint; future specs
  may add edges from `wxtags -> org_wxtag_applications` keyed on `key`.
