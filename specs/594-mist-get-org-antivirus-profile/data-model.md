# Phase 1 Data Model: getOrgAntivirusProfile

**Branch**: `594-mist-get-org-antivirus-profile` | **Date**: 2026-06-29
**Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)

This document enumerates the entities returned by
`GET /api/v1/orgs/{org_id}/avprofiles/{avprofile_id}`, the SQLite DDL used by
the `DataExporter` SQLite backend, and the new
`ENDPOINT_PRIMARY_KEY_STRATEGIES` registration.

---

## Entity: `org_avprofile` (Antivirus Profile)

A single Antivirus profile owned by a Mist organization, optionally
scoped to a specific site. Returned as one JSON object by the endpoint.

### Fields

| Field             | Type                  | Source       | Nullable | Notes                                                        |
|-------------------|-----------------------|--------------|----------|--------------------------------------------------------------|
| `id`              | TEXT (uuid)           | API          | NO       | Natural primary key. Read-only.                              |
| `org_id`          | TEXT (uuid)           | API          | NO       | Foreign key -> `org.id` (logical -- no enforced FK in SQLite). Read-only. |
| `site_id`         | TEXT (uuid)           | API          | YES      | Foreign key -> `org_sites.id`. Null when profile is org-scoped only. Read-only. |
| `name`            | TEXT                  | API (required) | NO     | Operator-visible profile name.                               |
| `fallback_action` | TEXT                  | API          | YES      | Enum: `block`, `log-and-permit`, `permit`.                   |
| `max_filesize`    | INTEGER               | API          | YES      | KB. Range 20..40000. API default 10000.                      |
| `mime_whitelist`  | TEXT (JSON array)     | API          | YES      | Stored as JSON-encoded string in SQLite for backend portability. |
| `url_whitelist`   | TEXT (JSON array)     | API          | YES      | Stored as JSON-encoded string in SQLite.                     |
| `protocols`       | TEXT (JSON array)     | API          | NO       | At least one of `ftp,http,imap,pop3,smtp`. JSON-encoded.     |
| `created_time`    | REAL                  | API          | YES      | Epoch seconds. Read-only.                                    |
| `modified_time`   | REAL                  | API          | YES      | Epoch seconds. Read-only.                                    |
| `misthelper_fetched_at` | REAL            | MistHelper   | NO       | Wall-clock epoch when MistHelper fetched the row. Always populated. |

### Primary Key

- **Type**: `natural_pk`
- **Column(s)**: `id`
- **Justification**: `id` is a stable, API-provided UUID guaranteed unique
  across the organization.

### Foreign Keys (logical, not enforced)

- `org_id` -> `org.id` (the broader Mist organization record)
- `site_id` -> `org_sites.id` (when non-null)

These are documented for the ArangoDB graph backend, which will create
edges; SQLite does not enforce FK constraints across MistHelper's
multi-backend exporter.

### Indexes

- `idx_org_avprofile_org_id` on (`org_id`)
- `idx_org_avprofile_site_id` on (`site_id`)
- `idx_org_avprofile_name` on (`name`)

### State Transitions

**N/A -- read-only endpoint.** MistHelper does not mutate Antivirus
profiles via this menu item. Mutations (POST, PUT, DELETE) are explicitly
out of scope per `spec.md`.

The only "state change" observed locally is the upsert of the SQLite row
on each repeated run -- mediated by `INSERT OR REPLACE` keyed on `id`.

---

## SQLite DDL

The `DataExporter` SQLite backend executes this `CREATE TABLE IF NOT
EXISTS` statement on first write. The statement is generated from the PK
strategy entry below, not hand-written in the codebase -- it is shown here
as a reference for the expected effective schema.

```sql
CREATE TABLE IF NOT EXISTS org_avprofile (
    id                    TEXT    NOT NULL PRIMARY KEY,
    org_id                TEXT    NOT NULL,
    site_id               TEXT,
    name                  TEXT    NOT NULL,
    fallback_action       TEXT,
    max_filesize          INTEGER,
    mime_whitelist        TEXT,        -- JSON-encoded list
    url_whitelist         TEXT,        -- JSON-encoded list
    protocols             TEXT NOT NULL, -- JSON-encoded list
    created_time          REAL,
    modified_time         REAL,
    misthelper_fetched_at REAL    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_org_avprofile_org_id
    ON org_avprofile (org_id);

CREATE INDEX IF NOT EXISTS idx_org_avprofile_site_id
    ON org_avprofile (site_id);

CREATE INDEX IF NOT EXISTS idx_org_avprofile_name
    ON org_avprofile (name);
```

Repeated runs use:

```sql
INSERT OR REPLACE INTO org_avprofile (
    id, org_id, site_id, name, fallback_action, max_filesize,
    mime_whitelist, url_whitelist, protocols,
    created_time, modified_time, misthelper_fetched_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
```

---

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary
in `MistHelper.py` (currently anchored near line ~1672 per
`.github/copilot-instructions.md`):

```python
"getOrgAntivirusProfile": {              # operationId from the Mist OpenAPI doc
    "type": "natural_pk",                # API-provided UUID is stable across runs
    "primary_key": ["id"],               # The profile's UUID column
    "indexes": [                         # Speeds up cross-table joins and operator search
        "org_id",                        # Filter by org context
        "site_id",                       # Filter by site scope when set
        "name",                          # Operator-visible name lookups
    ],
    "table_name": "org_avprofile",       # Singular -- per-id detail, not list
},
```

Inline comments are mandatory per Constitution Principle VI; the entry
above ships with them.

---

## Cross-Reference

- HTTP contract: `contracts/get_org_antivirus_profile.md`
- Local run guide: `quickstart.md`
- Source enriched doc:
  `documentation/api/orgs/GET_orgs_org_id_avprofiles_avprofile_id.md`
