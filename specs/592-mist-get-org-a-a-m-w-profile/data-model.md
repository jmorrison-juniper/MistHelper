# Phase 1 Data Model: getOrgAAMWProfile

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_aamwprofiles_aamwprofile_id.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing one Advanced Anti-Malware (SkyATP)
profile. MistHelper splits this into two logical entities for clean multi-backend
persistence: a flat summary row and zero-or-more flattened `categories[]` sub-rows.

### Entity 1: `AAMWProfileSummary`

One row per profile UUID.

| Field               | Type    | Source                | PK? | FK?                   | Notes |
|---------------------|---------|-----------------------|-----|-----------------------|-------|
| `id`                | TEXT    | API `id`              | YES | --                    | Profile UUID (`uuid` contentEncoding). Stable identifier across polls. |
| `org_id`            | TEXT    | API `org_id`          | --  | sites.org_id          | Owning org UUID; also injected by MistHelper as a defensive default if absent. |
| `site_id`           | TEXT    | API `site_id`         | --  | sites.id              | Optional site scope; may be NULL. |
| `name`              | TEXT    | API `name`            | --  | --                    | Display name (e.g. `aamw-custom`). |
| `fallback_action`   | TEXT    | API `fallback_action` | --  | --                    | Enum: `block`, `permit`. |
| `file_action`       | TEXT    | API `file_action`     | --  | --                    | Enum: `block`, `permit`. |
| `verdict_threshold` | INTEGER | API `verdict_threshold` | -- | --                   | 1..10, default 8. |
| `created_time`      | REAL    | API `created_time`    | --  | --                    | Epoch seconds, readOnly. |
| `modified_time`     | REAL    | API `modified_time`   | --  | --                    | Epoch seconds, readOnly. |
| `category_count`    | INTEGER | len(API `categories`) | --  | --                    | Convenience count of the categories array. |
| `polled_at_utc`     | TEXT    | MistHelper clock      | --  | --                    | ISO8601 UTC timestamp of the read, for audit. |

### Entity 2: `AAMWProfileCategory`

Zero or more rows per profile UUID -- one per element of the API `categories[]` array.

| Field              | Type    | Source                            | PK? | FK?                              | Notes |
|--------------------|---------|-----------------------------------|-----|----------------------------------|-------|
| `aamwprofile_id`   | TEXT    | API `id` (parent profile)         | YES | org_aamw_profile_summary.id      | Joins to summary. |
| `category`         | TEXT    | API `categories[].category`       | YES | --                               | Enum: `archive`, `document`, `pdf`, `executable`, `rich_application`, `library`, `os_package`, `mobile`, `java`, `configuration`, `script`. Unique within a profile. |
| `hash_lookup_only` | INTEGER | API `categories[].hash_lookup_only` | -- | --                              | 0 or 1 (SQLite bool). Default 0. |
| `org_id`           | TEXT    | MistHelper context                | --  | sites.org_id                     | Stored for fast org-scoped filtering. |
| `polled_at_utc`    | TEXT    | MistHelper clock                  | --  | --                               | ISO8601 UTC timestamp of the read, for audit. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying profile on the Mist side can be
edited via `PUT /api/v1/orgs/{org_id}/aamwprofiles/{aamwprofile_id}` (a separate spec
when needed), but MistHelper does not drive or model those transitions. Each poll
overwrites the prior snapshot for the same `id` (summary) and
`(aamwprofile_id, category)` (categories) tuple via SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- Summary table: one row per profile UUID.
CREATE TABLE IF NOT EXISTS org_aamw_profile_summary (
    id                  TEXT     NOT NULL,
    org_id              TEXT,
    site_id             TEXT,
    name                TEXT,
    fallback_action     TEXT,
    file_action         TEXT,
    verdict_threshold   INTEGER,
    created_time        REAL,
    modified_time       REAL,
    category_count      INTEGER,
    polled_at_utc       TEXT,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_aamw_profile_summary_org
    ON org_aamw_profile_summary (org_id);
CREATE INDEX IF NOT EXISTS idx_aamw_profile_summary_site
    ON org_aamw_profile_summary (site_id);
CREATE INDEX IF NOT EXISTS idx_aamw_profile_summary_name
    ON org_aamw_profile_summary (name);

-- Categories table: zero-or-more rows per profile UUID.
CREATE TABLE IF NOT EXISTS org_aamw_profile_categories (
    aamwprofile_id      TEXT     NOT NULL,
    category            TEXT     NOT NULL,
    hash_lookup_only    INTEGER  DEFAULT 0,
    org_id              TEXT,
    polled_at_utc       TEXT,
    PRIMARY KEY (aamwprofile_id, category),
    FOREIGN KEY (aamwprofile_id)
        REFERENCES org_aamw_profile_summary(id)
);

CREATE INDEX IF NOT EXISTS idx_aamw_profile_categories_org
    ON org_aamw_profile_categories (org_id);
CREATE INDEX IF NOT EXISTS idx_aamw_profile_categories_category
    ON org_aamw_profile_categories (category);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the equivalent
DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`, ArangoDB via
collection upsert, Redis via key namespacing). MistHelper does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Single AAMW profile, keyed by its Mist-supplied UUID.
    'getOrgAAMWProfile': {                                                          # operationId from OpenAPI
        'type': 'natural_pk',                                                       # API supplies a stable UUID for the profile
        'primary_key': ['id'],                                                      # the profile's own UUID
        'indexes': ['org_id', 'site_id', 'name'],                                   # fast filter by parent scope and human name
        'table': 'org_aamw_profile_summary',                                        # target SQLite table for summary rows
    },

    # Flattened per-category sub-array from the same response.
    'getOrgAAMWProfileCategories': {                                                # MistHelper-internal sub-table identifier
        'type': 'composite_pk',                                                     # composite of FK to summary + category enum
        'primary_key': ['aamwprofile_id', 'category'],                              # one row per (profile, category) pair
        'indexes': ['org_id', 'category'],                                          # fast lookup by org and by category enum
        'table': 'org_aamw_profile_categories',                                     # target SQLite table for category rows
    },
}
```

The `getOrgAAMWProfileCategories` key is a MistHelper-internal identifier (the Mist API
has no operationId for it -- it is a flattened sub-array of the parent response). This
pattern matches how MistHelper already splits other endpoints whose response body
contains a nested array (see the license-claim-status precedent in spec 500).
