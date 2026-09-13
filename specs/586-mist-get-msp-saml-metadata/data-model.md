# Phase 1 Data Model: getMspSamlMetadata

**Feature**: `586-mist-get-msp-saml-metadata`
**Date**: 2026-06-29
**Source schema**: `documentation/api/msps/GET_msps_msp_id_ssos_sso_id_metadata.md` (200
response)

## Entities

### Entity 1: `MspSamlMetadata`

Represents the SAML Service Provider metadata for a single MSP SSO configuration. One
row per `(msp_id, sso_id)` tuple.

| Field            | Type   | Source           | Nullable | Notes                                                                                                                              |
|------------------|--------|------------------|----------|------------------------------------------------------------------------------------------------------------------------------------|
| `msp_id`         | TEXT   | path parameter   | NO       | Composite PK part 1. Injected into the row by MistHelper before write -- the API response body does not echo this value.            |
| `sso_id`         | TEXT   | path parameter   | NO       | Composite PK part 2. Injected by MistHelper before write.                                                                          |
| `acs_url`        | TEXT   | response.acs_url | YES      | Read-only. Present only when `idp_type==saml`. Example: `https://api.mist.com/api/v1/saml/llDfa13f/login`.                          |
| `entity_id`      | TEXT   | response.entity_id | YES    | Read-only. Present only when `idp_type==saml`. The SAML SP entityID URL.                                                            |
| `logout_url`     | TEXT   | response.logout_url | YES   | Read-only. Present only when `idp_type==saml`. The SAML single logout URL.                                                          |
| `metadata`       | TEXT   | response.metadata | YES     | Read-only. Raw XML SAML metadata document. May be several KB. Stored verbatim -- never re-encoded.                                  |
| `scim_base_url`  | TEXT   | response.scim_base_url | YES | Present only when `idp_type==oauth` and `scim_enabled==true`. Mutually exclusive in practice with the SAML-only fields.            |
| `retrieved_at`   | TEXT   | MistHelper       | NO       | ISO-8601 UTC timestamp injected by `DataExporter.write_with_format_selection()` for audit. Standard column added to every export.   |

**Primary Key**: `(msp_id, sso_id)` -- composite, both NOT NULL.

**Foreign Keys**: None enforced at the SQLite layer (MistHelper does not maintain
referential integrity across tables -- each endpoint table is independent). Conceptually
`msp_id` references a row in a hypothetical future `msps` table and `sso_id` references
a row in a future `msp_ssos` table; both relationships are implicit.

### State Transitions

**N/A -- read-only endpoint.** The row is fully replaced on every successful invocation
via `INSERT OR REPLACE`. There is no state machine to model. If the upstream IdP trust
is refreshed (e.g., the SAML signing certificate is rolled), the next run of the menu
item produces an updated row with the same `(msp_id, sso_id)` key, overwriting the
previous values.

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS msp_saml_metadata (
    msp_id        TEXT NOT NULL,                  -- MSP UUID from URL path
    sso_id        TEXT NOT NULL,                  -- SSO config UUID from URL path
    acs_url       TEXT,                           -- SAML Assertion Consumer Service URL
    entity_id     TEXT,                           -- SAML SP entityID
    logout_url    TEXT,                           -- SAML Single Logout URL
    metadata      TEXT,                           -- Raw XML metadata document
    scim_base_url TEXT,                           -- SCIM base URL when OAuth+SCIM
    retrieved_at  TEXT NOT NULL,                  -- ISO-8601 UTC fetch timestamp
    PRIMARY KEY (msp_id, sso_id)
);

CREATE INDEX IF NOT EXISTS idx_msp_saml_metadata_msp_id
    ON msp_saml_metadata (msp_id);
```

The DDL is emitted automatically by `DataExporter` on first write when SQLite is the
active backend, derived from the `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry below. The
`idx_msp_saml_metadata_msp_id` index supports "list all SSO configs for one MSP" lookups
without scanning the table.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict in `MistHelper.py` (around line 1672
per `agents.md`):

```python
'getMspSamlMetadata': {                          # operationId from OpenAPI / mistapi SDK
    'type': 'composite_pk',                      # Two-column natural key from URL path
    'primary_key': ['msp_id', 'sso_id'],         # Both path params, injected by caller
    'indexes': ['msp_id'],                       # Supports per-MSP enumeration queries
    'table_name': 'msp_saml_metadata',           # Explicit table override (lowercase snake)
},
```

## Row Construction Contract (MistHelper-side)

The menu method must produce a single dict with the following shape before handing it to
`DataExporter.write_with_format_selection()`:

```python
saml_metadata_row = {
    'msp_id': msp_identifier,                    # From safe_input prompt, validated UUID
    'sso_id': sso_identifier,                    # From safe_input prompt, validated UUID
    'acs_url': response_data.get('acs_url'),     # None when idp_type != saml
    'entity_id': response_data.get('entity_id'), # None when idp_type != saml
    'logout_url': response_data.get('logout_url'),
    'metadata': response_data.get('metadata'),   # Raw XML string, verbatim
    'scim_base_url': response_data.get('scim_base_url'),
}
```

`retrieved_at` is injected by `DataExporter` -- the menu method does not populate it
manually. All five response fields use `.get()` so missing keys produce `None` rather
than `KeyError`, since the OpenAPI schema marks every property as conditional.
