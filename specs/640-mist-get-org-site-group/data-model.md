# Phase 1 Data Model: getOrgSiteGroup

**Feature**: `640-mist-get-org-site-group`
**Endpoint**: `GET /api/v1/orgs/{org_id}/sitegroups/{sitegroup_id}`
**Date**: 2026-06-30

## Entities

The endpoint returns exactly one entity per successful call.

### Entity: `SiteGroup`

A container object that groups multiple sites for bulk template assignment
across an organization.

| Field           | Type    | Nullable | PK | FK / Index                    | Description |
|-----------------|---------|----------|----|-------------------------------|-------------|
| `id`            | UUID    | No       | PK | -                             | Immutable Mist-assigned identifier for the site group. |
| `org_id`        | UUID    | No       | -  | FK -> `org.id`; INDEX          | Owning organization UUID. |
| `name`          | TEXT    | No       | -  | INDEX                         | Human-readable group name; required per OpenAPI schema. |
| `site_ids`      | TEXT    | Yes      | -  | -                             | `;`-delimited list of site UUIDs that belong to this group (flattened from the JSON array). Empty string when the group has no member sites. |
| `site_count`    | INTEGER | No       | -  | -                             | Derived column: `len(response['site_ids'])`. Populated at flatten time for cheap SQL analytics. |
| `created_time`  | REAL    | Yes      | -  | -                             | Epoch seconds when the group was created (read-only per API). |
| `modified_time` | REAL    | Yes      | -  | -                             | Epoch seconds of last modification (read-only per API). |
| `ingested_at`   | TEXT    | No       | -  | -                             | ISO-8601 UTC timestamp added by MistHelper at export time (audit column). |

Notes:

- `id`, `org_id`, and `site_ids[i]` are all Mist UUID strings; SQLite stores
  them as TEXT for portability.
- `site_ids` is denormalized. Consumers needing a proper many-to-many join
  can split on `;` in a view; a dedicated join table is deferred (see
  research.md Task 2 Alternatives Considered).

## Relationships

- `SiteGroup.org_id` -> `Org.id` (many-to-one). MistHelper does not enforce
  the FK at the DB layer (SQLite pragma left at defaults for the existing
  monolith), but the index supports fast org-scoped queries.
- `SiteGroup.site_ids` -> `Site.id` (many-to-many, denormalized). A future
  spec may introduce `org_site_group_members` for graph workloads.

## State Transitions

**N/A -- read-only endpoint.** `getOrgSiteGroup` is HTTP GET and cannot mutate
Mist state. State transitions for site groups (create, update, delete) are
owned by the sibling POST / PUT / DELETE endpoints under
`/api/v1/orgs/{org_id}/sitegroups`, each of which needs its own spec if
MistHelper ever chooses to expose them.

MistHelper-local lifecycle for the row:

```
(missing) --INSERT-> (fresh row) --INSERT OR REPLACE-> (upserted row)
```

Every re-run of the menu item performs an upsert keyed on `id`; there is no
soft-delete because the API has no soft-delete semantic.

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS org_site_groups (
    id             TEXT PRIMARY KEY,           -- Mist UUID, natural PK
    org_id         TEXT NOT NULL,              -- owning org UUID
    name           TEXT NOT NULL,              -- human-readable group name
    site_ids       TEXT,                       -- ';'-delimited member UUIDs
    site_count     INTEGER NOT NULL DEFAULT 0, -- derived cardinality
    created_time   REAL,                       -- epoch seconds (API)
    modified_time  REAL,                       -- epoch seconds (API)
    ingested_at    TEXT NOT NULL               -- ISO-8601 UTC at export time
);

CREATE INDEX IF NOT EXISTS idx_org_site_groups_org_id
    ON org_site_groups(org_id);

CREATE INDEX IF NOT EXISTS idx_org_site_groups_name
    ON org_site_groups(name);
```

The `DataExporter` auto-creates the table on first write, but the DDL above
is the contract Phase 2 tasks must honor when generating migration code.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add this literal dictionary entry to `ENDPOINT_PRIMARY_KEY_STRATEGIES` in
`MistHelper.py` (the strategy dictionary at approximately line 1672):

```python
'getOrgSiteGroup': {                              # SDK operationId, exact case
    'type': 'natural_pk',                         # id is an API-assigned UUID
    'primary_key': ['id'],                        # single-column PK
    'indexes': ['org_id', 'name'],                # fast org-scoped + name lookup
    'table_name': 'org_site_groups',              # SQLite / Arango collection name
    'csv_filename_template':                      # per-invocation CSV filename
        'org_site_group_{org_id}_{sitegroup_id}.csv',
    'flatten_lists': {                            # array -> delimited-string map
        'site_ids': ';',                          # semicolon keeps CSV-safe
    },
    'derived_columns': {                          # cheap aggregates at write time
        'site_count': lambda row: len(           # cardinality of member sites
            row.get('site_ids') or []             # tolerate None or missing
        ),
    },
},
```

Every line above carries an inline comment per Constitution Principle VI.
