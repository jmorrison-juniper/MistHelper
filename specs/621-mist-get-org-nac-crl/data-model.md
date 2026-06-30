# Phase 1 Data Model: getOrgNacCrl

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_setting_mist_nac_crls.md` (200 OK body).

## Entities

The endpoint returns a single JSON object with one top-level `results` array. Each
element of that array is a `nac_crl_file` record. MistHelper persists this as a
single flat table with one row per CRL file. There are no nested arrays inside the
file record, so no split into parent/child tables is required.

### Entity 1: `NacCrlFile`

One row per uploaded CRL file per org.

| Field            | Type     | Source                | PK? | FK?           | Notes |
|------------------|----------|-----------------------|-----|---------------|-------|
| `id`             | TEXT     | API `results[].id`    | YES | --            | UUID. Globally unique; the canonical Mist-side identifier referenced by the companion DELETE endpoint. |
| `org_id`         | TEXT     | MistHelper context    | --  | sites.org_id  | UUID supplied by the user; injected before write. Indexed. |
| `name`           | TEXT     | API `results[].name`  | --  | --            | Issuer name for the CRL file. Human-readable, editable on upload. Indexed. |
| `url`            | TEXT     | API `results[].url`   | --  | --            | Download URL for the uploaded CRL file. |
| `created_time`   | REAL     | API `results[].created_time`  | -- | --      | Epoch seconds when the file was uploaded. Read-only. |
| `modified_time`  | REAL     | API `results[].modified_time` | -- | --      | Epoch seconds when the file was last modified. Read-only. |
| `polled_at_utc`  | TEXT     | MistHelper clock      | --  | --            | ISO8601 UTC timestamp of the poll, for audit trail. |

### Entity inventory summary

| Entity        | Cardinality per call | PK strategy   | Storage table        |
|---------------|----------------------|---------------|----------------------|
| `NacCrlFile`  | 0..N (typically <=10)| `natural_pk`  | `org_nac_crl_files`  |

## State Transitions

N/A -- this is a read-only endpoint. The underlying CRL files transition through
upload (`POST /orgs/{org_id}/setting/mist_nac_crls`), modification (re-upload of
the same issuer), and deletion (`DELETE
/orgs/{org_id}/setting/mist_nac_crls/{naccrl_id}`) on the Mist side. MistHelper
does not drive or model those transitions; it merely captures snapshots. Each
poll overwrites the prior snapshot for the same `id` via SQLite `INSERT OR
REPLACE`. Rows for CRLs that were deleted upstream remain in the local SQLite
table until manually pruned -- the menu item does not perform reconciliation
deletes (out of scope per spec.md "Out of Scope" section).

## SQLite DDL

```sql
-- CRL file table: one row per uploaded CRL file across all orgs.
CREATE TABLE IF NOT EXISTS org_nac_crl_files (
    id              TEXT     NOT NULL,
    org_id          TEXT,
    name            TEXT,
    url             TEXT,
    created_time    REAL,
    modified_time   REAL,
    polled_at_utc   TEXT,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_org_nac_crl_files_org_id
    ON org_nac_crl_files (org_id);

CREATE INDEX IF NOT EXISTS idx_org_nac_crl_files_name
    ON org_nac_crl_files (name);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT
EXISTS`, ArangoDB via collection upsert, Redis via key namespacing). MistHelper
does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py`. Single insert in the dict literal -- no structural
change to the dictionary itself.

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Uploaded CRL files for Mist NAC, listed by getOrgNacCrl.
    'getOrgNacCrl': {                                                               # operationId from OpenAPI
        'type': 'natural_pk',                                                       # API supplies a stable UUID
        'primary_key': ['id'],                                                      # Mist-side UUID is globally unique
        'indexes': ['org_id', 'name'],                                              # fast filter by org and by issuer name
        'table': 'org_nac_crl_files',                                               # target SQLite table
    },
}
```

`org_id` is included as an indexed column (not a PK column) because the Mist UUID
in `id` is already globally unique across orgs, while `org_id` is still a useful
filter for queries that scope to a single org.
