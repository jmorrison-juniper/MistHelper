# Phase 1 Data Model: downloadOrgSamlMetadata

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_ssos_sso_id_metadata.xml.md` (200 OK body) and
the SAML 2.0 metadata example included in `spec.md`.

## Entities

The endpoint returns a single SAML 2.0 `<md:EntityDescriptor>` XML document describing
the Mist-side Service Provider for one organization's SSO configuration. The document
is stored verbatim in one row -- MistHelper does *not* parse the XML at write time.

### Entity 1: `OrgSsoSamlMetadata`

One row per (org, sso) tuple. The XML body is stored as a single TEXT column; byte size
and a SHA-256 fingerprint enable change detection without re-parsing.

| Field             | Type     | Source              | PK? | FK?            | Notes |
|-------------------|----------|---------------------|-----|----------------|-------|
| `org_id`          | TEXT     | MistHelper context  | YES | sites.org_id   | UUID supplied by user; injected before write. |
| `sso_id`          | TEXT     | MistHelper context  | YES | --             | UUID supplied by user; injected before write. |
| `metadata_xml`    | TEXT     | API 200 body        | --  | --             | Verbatim UTF-8 XML document (`<md:EntityDescriptor>`). Stored unparsed. |
| `metadata_bytes`  | INTEGER  | MistHelper compute  | --  | --             | `len(metadata_xml.encode("utf-8"))`. Cheap change-detection signal. |
| `metadata_sha256` | TEXT     | MistHelper compute  | --  | --             | 64-char lowercase hex SHA-256 of the UTF-8 bytes. Detects rotation. |
| `entity_id`       | TEXT     | XML attribute       | --  | --             | Best-effort extraction of `EntityDescriptor/@entityID` for quick filtering. Nullable on parse failure -- the verbatim XML in `metadata_xml` is always authoritative. |
| `valid_until`     | TEXT     | XML attribute       | --  | --             | Best-effort extraction of `EntityDescriptor/@validUntil` (ISO 8601). Nullable on parse failure. |
| `polled_at_utc`   | TEXT     | MistHelper clock    | --  | --             | ISO 8601 UTC timestamp of the poll, for audit. |

The two optional XML-derived columns (`entity_id`, `valid_until`) are convenience
fields; both are best-effort and tolerate any parse error (the row still writes with
`NULL` for both). The authoritative copy of the metadata remains in `metadata_xml`.

## State Transitions

N/A -- this is a read-only endpoint. The underlying *SSO configuration* on the Mist
side has its own lifecycle (created via `POST /ssos`, updated via `PUT /ssos/{sso_id}`,
deleted via `DELETE /ssos/{sso_id}`), but MistHelper does not drive or model those
transitions in this menu item; it merely captures snapshots of the SAML metadata
document. Each poll overwrites the prior snapshot for the same `(org_id, sso_id)`
tuple via SQLite `INSERT OR REPLACE`. A rotation event surfaces as a change in
`metadata_sha256` between polls.

## SQLite DDL

```sql
-- One row per (org, sso). Repeated polls upsert via INSERT OR REPLACE.
CREATE TABLE IF NOT EXISTS org_sso_saml_metadata (
    org_id            TEXT     NOT NULL,
    sso_id            TEXT     NOT NULL,
    metadata_xml      TEXT,
    metadata_bytes    INTEGER,
    metadata_sha256   TEXT,
    entity_id         TEXT,
    valid_until       TEXT,
    polled_at_utc     TEXT,
    PRIMARY KEY (org_id, sso_id)
);

-- Fast lookup by SAML entityID across all stored orgs.
CREATE INDEX IF NOT EXISTS idx_org_sso_saml_metadata_entity_id
    ON org_sso_saml_metadata (entity_id);

-- Fast change-detection query: list rotations between two polls.
CREATE INDEX IF NOT EXISTS idx_org_sso_saml_metadata_sha256
    ON org_sso_saml_metadata (metadata_sha256);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the equivalent
DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`, ArangoDB via
collection upsert keyed on `(org_id, sso_id)`, Redis via the same composite namespace).
MistHelper does not run the DDL directly from the menu method.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following single entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no structural
change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # One SAML metadata XML document per (org, sso). Composite PK enables clean
    # upserts when an operator re-polls the same SSO config to detect rotation.
    'downloadOrgSamlMetadata': {                                                    # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of business UUIDs
        'primary_key': ['org_id', 'sso_id'],                                        # stable across polls of same SSO config
        'indexes': ['entity_id', 'metadata_sha256'],                                # fast filter + rotation detection
        'table': 'org_sso_saml_metadata',                                           # target SQLite table for this endpoint
    },
}
```

No MistHelper-internal sub-table key is required (unlike endpoints that flatten nested
arrays). The XML document is one logical entity and lives in one table.
