# Phase 1 Data Model: GetOrgNacPortalSamlMetadata

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_nacportals_nacportal_id_saml_metadata.md`
(200 OK body).

## Entities

The endpoint returns a single flat JSON object describing the SAML
Service-Provider metadata for one NAC portal. MistHelper models this as one
logical entity persisted to one table.

### Entity 1: `NacPortalSamlMetadata`

One row per (org, NAC portal).

| Field           | Type    | Source                    | PK? | FK?                       | Notes |
|-----------------|---------|---------------------------|-----|---------------------------|-------|
| `org_id`        | TEXT    | MistHelper context (user prompt) | YES | `org_nac_portals.org_id` (logical) | UUID supplied by user; injected before write. Not present in API body. |
| `nacportal_id`  | TEXT    | MistHelper context (user prompt) | YES | `org_nac_portals.id` (logical)     | UUID supplied by user; injected before write. Not present in API body. |
| `acs_url`       | TEXT    | API `acs_url`             | --  | --                        | Assertion Consumer Service URL. Present when parent portal `idp_type == saml`. |
| `entity_id`     | TEXT    | API `entity_id`           | --  | --                        | SP entity ID URL. Present when `idp_type == saml`. |
| `logout_url`    | TEXT    | API `logout_url`          | --  | --                        | Single Logout URL. Present when `idp_type == saml`. |
| `metadata`      | TEXT    | API `metadata`            | --  | --                        | Embedded SP XML metadata document (a few KB typical). Stored verbatim; never logged. |
| `metadata_len`  | INTEGER | len(API `metadata`)       | --  | --                        | Convenience length used in DEBUG log summaries and downstream sanity checks. |
| `scim_base_url` | TEXT    | API `scim_base_url`       | --  | --                        | SCIM base URL. Present when `idp_type == oauth` and `scim_enabled == true`. Mutually exclusive with SAML fields. |
| `idp_flavor`    | TEXT    | Derived by MistHelper     | --  | --                        | `"saml"` if any of `acs_url`/`entity_id`/`logout_url`/`metadata` are present; `"oauth"` if `scim_base_url` is present; else `"unknown"`. |
| `polled_at_utc` | TEXT    | MistHelper clock          | --  | --                        | ISO8601 UTC timestamp of the poll, for audit. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying NAC portal on the Mist
side may have its SAML configuration rotated (certificate renewal, entity_id
change, etc.), but MistHelper does not drive or model those transitions; it
merely captures the current snapshot. Each poll overwrites the prior snapshot
for the same `(org_id, nacportal_id)` tuple via SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- One row per (org, NAC portal). SAML metadata for the portal, in whichever
-- flavor the portal is configured for (SAML or OAuth+SCIM).
CREATE TABLE IF NOT EXISTS org_nac_portal_saml_metadata (
    org_id          TEXT     NOT NULL,
    nacportal_id    TEXT     NOT NULL,
    acs_url         TEXT,
    entity_id       TEXT,
    logout_url      TEXT,
    metadata        TEXT,
    metadata_len    INTEGER,
    scim_base_url   TEXT,
    idp_flavor      TEXT,
    polled_at_utc   TEXT,
    PRIMARY KEY (org_id, nacportal_id)
);

CREATE INDEX IF NOT EXISTS idx_nac_portal_saml_entity_id
    ON org_nac_portal_saml_metadata (entity_id);

CREATE INDEX IF NOT EXISTS idx_nac_portal_saml_idp_flavor
    ON org_nac_portal_saml_metadata (idp_flavor);
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

    # SAML Service-Provider metadata for a specific NAC portal in a
    # specific org. Composite key of (org_id, nacportal_id) because the
    # response body contains neither identifier -- both come from the
    # MistHelper user prompt and are injected into the row before write.
    'getOrgNacPortalSamlMetadata': {                                            # operationId from OpenAPI
        'type': 'composite_pk',                                                 # PK is composite of two business fields
        'primary_key': ['org_id', 'nacportal_id'],                              # stable across polls of the same portal
        'indexes': ['entity_id', 'idp_flavor'],                                 # fast lookup by SAML entity ID and by portal flavor
        'table': 'org_nac_portal_saml_metadata',                                # target SQLite table
    },
}
```

No additional MistHelper-internal sub-table keys are needed -- the response is
a flat object with no nested arrays.
