# Phase 1 Data Model: getOrgSamlMetadata

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_ssos_sso_id_metadata.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing the SAML/SSO metadata for a
specific SSO configuration within an organization. MistHelper persists this as one
row in one table.

### Entity 1: `SsoSamlMetadata`

Exactly one row per (org, SSO configuration).

| Field           | Type    | Source                | PK? | FK?                        | Notes |
|-----------------|---------|-----------------------|-----|----------------------------|-------|
| `org_id`        | TEXT    | MistHelper context    | YES | sites.org_id               | UUID supplied by user; injected before write (not in response body). |
| `sso_id`        | TEXT    | MistHelper context    | YES | org_ssos.id                | UUID supplied by user; injected before write (not in response body). |
| `acs_url`       | TEXT    | API `acs_url`         | --  | --                         | SAML SP Assertion Consumer Service URL. Present when `idp_type == "saml"`. |
| `entity_id`     | TEXT    | API `entity_id`       | --  | --                         | SAML SP entity identifier. Present when `idp_type == "saml"`. Indexed. |
| `logout_url`    | TEXT    | API `logout_url`      | --  | --                         | SAML SP single-logout URL. Present when `idp_type == "saml"`. |
| `metadata`      | TEXT    | API `metadata`        | --  | --                         | Full SAML SP metadata as a single multi-line XML string. Preserved byte-for-byte for round-trip to IdP tooling. |
| `metadata_bytes`| INTEGER | len(API `metadata`)   | --  | --                         | Convenience length in bytes of the `metadata` XML blob, so SQL queries can filter empty vs populated rows without scanning the blob column. |
| `scim_base_url` | TEXT    | API `scim_base_url`   | --  | --                         | SCIM provisioning base URL. Present only when `idp_type == "oauth"` AND `scim_enabled == true`. NULL for SAML-only configs. |
| `polled_at_utc` | TEXT    | MistHelper clock      | --  | --                         | ISO8601 UTC timestamp of the poll, for audit. |

Every column except the two PK columns and `polled_at_utc` is nullable, because a
single Mist SSO configuration is either SAML-typed (populates the `acs_url`,
`entity_id`, `logout_url`, `metadata` fields and leaves `scim_base_url` NULL) or
OAuth+SCIM-typed (populates only `scim_base_url` and leaves the SAML fields NULL).
The schema accommodates both without splitting into two tables, because the natural
key `(org_id, sso_id)` is identical for both variants.

## State Transitions

N/A -- this is a read-only endpoint. The underlying SSO configuration on the Mist
side can be edited (via unrelated PUT/PATCH endpoints), which will cause the
`metadata` XML blob to change on the next poll. MistHelper does not drive or model
those transitions; it merely captures the current snapshot. Each poll overwrites
the prior snapshot for the same `(org_id, sso_id)` tuple via SQLite
`INSERT OR REPLACE`.

## SQLite DDL

```sql
-- Metadata row: exactly one per (org, SSO configuration).
CREATE TABLE IF NOT EXISTS org_sso_saml_metadata (
    org_id           TEXT     NOT NULL,
    sso_id           TEXT     NOT NULL,
    acs_url          TEXT,
    entity_id        TEXT,
    logout_url       TEXT,
    metadata         TEXT,
    metadata_bytes   INTEGER,
    scim_base_url    TEXT,
    polled_at_utc    TEXT,
    PRIMARY KEY (org_id, sso_id)
);

CREATE INDEX IF NOT EXISTS idx_org_sso_saml_metadata_entity_id
    ON org_sso_saml_metadata (entity_id);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`,
ArangoDB via collection upsert, Redis via key namespacing). MistHelper does not run
the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following single entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no structural
change):

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # SAML/SSO metadata: exactly one row per (org, SSO configuration).
    'getOrgSamlMetadata': {                                                         # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of two UUID business fields
        'primary_key': ['org_id', 'sso_id'],                                        # stable natural key from request context
        'indexes': ['entity_id'],                                                   # fast lookup by SAML SP entity ID
        'table': 'org_sso_saml_metadata',                                           # target SQLite table
    },
}
```

No MistHelper-internal sub-table identifier is required for this endpoint because
the response contains no nested arrays -- it is a flat five-field object that maps
to exactly one row per (org, SSO).
