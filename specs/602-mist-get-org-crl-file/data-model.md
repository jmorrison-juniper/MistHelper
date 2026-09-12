# Phase 1 Data Model: getOrgCrlFile

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_crl.md` (200 OK body).

The 200 OK body is documented as:

```json
{
  "type": "string",
  "description": "File",
  "contentEncoding": "base64"
}
```

That is: the entire response payload is a single base64-encoded string
representing the CRL file. There is no list of entities and no nested
structure. MistHelper models this as one logical entity per fetch.

## Entities

### Entity 1: `OrgCrlSnapshot`

One row per (org, poll). Captures the metadata needed to audit CRL rotation
without bloating tabular storage with the raw bytes.

| Field              | Type     | Source              | PK? | FK?           | Notes |
|--------------------|----------|---------------------|-----|---------------|-------|
| `org_id`           | TEXT     | MistHelper context  | YES | sites.org_id  | UUID supplied by user; injected before write. |
| `fetched_at_utc`   | TEXT     | MistHelper clock    | YES | --            | ISO8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`) at the moment of the SDK call. Part of composite PK. |
| `content_encoding` | TEXT     | API doc constant    | --  | --            | Always `"base64"` for this endpoint. Captured for forward-compatibility. |
| `crl_length_bytes` | INTEGER  | derived             | --  | --            | Length of the *decoded* binary CRL in bytes. Computed via `len(base64.b64decode(raw))`. |
| `sha256`           | TEXT     | derived             | --  | --            | Lowercase hex SHA-256 of the decoded binary CRL. Enables "did the CRL rotate?" queries. |
| `blob_path`        | TEXT     | MistHelper          | --  | --            | Relative path under `data/` to the raw `.crl` blob file (e.g. `org_0a1b2c3d_crl_20260629T225100Z.crl`). |
| `http_status`      | INTEGER  | API response        | --  | --            | HTTP status from `response.status_code`. Always `200` on the happy path. Stored for audit. |

The decoded CRL bytes themselves are **not** stored in this table. They live
in a sidecar file under `data/` referenced by `blob_path`, per the research
decision in `research.md` Task 3.

## State Transitions

N/A -- this is a read-only endpoint. The underlying *CRL artifact* on the
Mist side does rotate over time as certificates are issued and revoked, but
MistHelper does not drive or model those transitions; it captures snapshots.
Each poll appends a new row to `org_crl_metadata` (composite PK on `(org_id,
fetched_at_utc)` guarantees no overwrite) and writes a new sidecar blob.

If the user wants only "did anything change since the last fetch?", a simple
post-hoc query suffices:

```sql
SELECT DISTINCT sha256
  FROM org_crl_metadata
 WHERE org_id = :org_id
 ORDER BY fetched_at_utc DESC
 LIMIT 5;
```

## SQLite DDL

```sql
-- One row per (org, poll). Captures CRL rotation history without storing
-- the raw bytes (those live in sidecar files under data/).
CREATE TABLE IF NOT EXISTS org_crl_metadata (
    org_id              TEXT     NOT NULL,
    fetched_at_utc      TEXT     NOT NULL,
    content_encoding    TEXT,
    crl_length_bytes    INTEGER,
    sha256              TEXT,
    blob_path           TEXT,
    http_status         INTEGER,
    PRIMARY KEY (org_id, fetched_at_utc)
);

CREATE INDEX IF NOT EXISTS idx_org_crl_metadata_sha256
    ON org_crl_metadata (sha256);

CREATE INDEX IF NOT EXISTS idx_org_crl_metadata_org_fetched
    ON org_crl_metadata (org_id, fetched_at_utc DESC);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT
EXISTS`, ArangoDB via collection upsert, Redis via key namespacing).
MistHelper does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no
structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Snapshot of the org's NAC Certificate Revocation List, keyed by
    # (org_id, fetched_at_utc) so every poll is preserved for rotation
    # auditing. The raw CRL blob lives as a sidecar file under data/;
    # only metadata is tabular.
    'getOrgCrlFile': {                                                              # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of business fields
        'primary_key': ['org_id', 'fetched_at_utc'],                                # uniquely identifies a snapshot
        'indexes': ['sha256'],                                                      # fast "did CRL change?" lookups
        'table': 'org_crl_metadata',                                                # target SQLite table for metadata rows
    },
}
```

No MistHelper-internal sub-table key is required because the endpoint returns
exactly one logical artifact per call (a single file blob plus its computed
metadata). The sidecar blob file is referenced from the metadata row via the
`blob_path` column; it is not registered as a separate entity in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.
