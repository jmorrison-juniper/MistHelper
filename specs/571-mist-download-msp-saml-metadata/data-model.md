# Phase 1 Data Model: downloadMspSamlMetadata

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response body lifted from
`documentation/api/msps/GET_msps_msp_id_ssos_sso_id_metadata.xml.md` (200 OK).

The endpoint returns a raw XML document (`Content-Type: application/xml`), not a JSON
object. MistHelper persists the document in two complementary forms: (1) the raw XML
bytes written verbatim to a `.xml` file under `data/` for downstream IdP import, and
(2) a single flattened summary row written through `DataExporter.write_with_format_selection()`
so the operation is queryable via CSV / SQLite / ArangoDB.

## Entities

The endpoint surfaces one logical entity that MistHelper persists in one SQLite table.

### Entity 1: `MspSsoSamlMetadata`

One row per (MSP, SSO config). Re-running the menu item replaces the row in place via
the composite PK upsert.

| Field               | Type    | Source                                            | PK? | FK? | Notes |
|---------------------|---------|---------------------------------------------------|-----|-----|-------|
| `msp_id`            | TEXT    | MistHelper user prompt / `MIST_MSP_ID`            | YES | --  | UUID supplied by user; injected before write. Not echoed in the API body. |
| `sso_id`            | TEXT    | MistHelper user prompt / `MIST_SSO_ID`            | YES | --  | UUID supplied by user; injected before write. Not echoed in the API body. |
| `entity_id`         | TEXT    | XML `EntityDescriptor/@entityID`                  | --  | --  | Canonical SAML Entity ID URL, e.g. `https://api.mist.com/api/v1/saml/5hdF5g/login`. |
| `valid_until`       | TEXT    | XML `EntityDescriptor/@validUntil`                | --  | --  | ISO 8601 UTC timestamp string, e.g. `2027-10-12T21:59:01Z`. |
| `nameid_format`     | TEXT    | XML `SPSSODescriptor/NameIDFormat` text           | --  | --  | e.g. `urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified`. |
| `single_logout_url` | TEXT    | XML `SingleLogoutService/@Location`               | --  | --  | HTTP-POST binding only is captured (Mist returns one entry). |
| `acs_url`           | TEXT    | XML `AssertionConsumerService/@Location`          | --  | --  | Default ACS URL (`isDefault="true"` index 0). |
| `assertions_signed` | INTEGER | XML `SPSSODescriptor/@WantAssertionsSigned`       | --  | --  | Stored as 0 or 1. |
| `authn_signed`      | INTEGER | XML `SPSSODescriptor/@AuthnRequestsSigned`        | --  | --  | Stored as 0 or 1. |
| `metadata_bytes`    | INTEGER | `len(response.data)` computed by MistHelper       | --  | --  | Length of the raw XML document in bytes. |
| `metadata_sha256`   | TEXT    | `hashlib.sha256(response.data).hexdigest()`       | --  | --  | Lowercase hex digest. Lets the operator detect cert / metadata rotation between polls. |
| `raw_xml_path`      | TEXT    | MistHelper-computed                               | --  | --  | Filesystem path of the `.xml` file dump under `data/`. |
| `polled_at_utc`     | TEXT    | MistHelper clock                                  | --  | --  | ISO 8601 UTC timestamp of the poll, for audit. |

There is no nested-array entity to split out (the API returns a single XML document, not
a list).

## State Transitions

N/A -- this is a read-only endpoint. The underlying SAML SP metadata on the Mist side
changes only when an MSP admin rotates the SP certificate or when Mist advances the
`validUntil` window (typically yearly). MistHelper does not drive or model those
transitions; it captures snapshots. Each download overwrites the prior snapshot for
the same `(msp_id, sso_id)` tuple via SQLite `INSERT OR REPLACE`. The `metadata_sha256`
column changes when (and only when) the underlying XML has rotated, giving the operator
a one-column diff signal.

## SQLite DDL

```sql
-- One row per (msp, sso) pair. Updated in place on every download.
CREATE TABLE IF NOT EXISTS msp_sso_saml_metadata (
    msp_id              TEXT     NOT NULL,
    sso_id              TEXT     NOT NULL,
    entity_id           TEXT,
    valid_until         TEXT,
    nameid_format       TEXT,
    single_logout_url   TEXT,
    acs_url             TEXT,
    assertions_signed   INTEGER,
    authn_signed        INTEGER,
    metadata_bytes      INTEGER,
    metadata_sha256     TEXT,
    raw_xml_path        TEXT,
    polled_at_utc       TEXT,
    PRIMARY KEY (msp_id, sso_id)
);

-- Fast scan for SSOs whose metadata is about to expire.
CREATE INDEX IF NOT EXISTS idx_msp_sso_saml_metadata_valid_until
    ON msp_sso_saml_metadata (valid_until);

-- Fast detection of cert/metadata rotation across polls.
CREATE INDEX IF NOT EXISTS idx_msp_sso_saml_metadata_sha256
    ON msp_sso_saml_metadata (metadata_sha256);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the equivalent
DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`, ArangoDB via
collection upsert, Redis via key namespacing). MistHelper does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following single entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # SAML SP metadata XML download for an MSP SSO configuration.
    # PK is composite of the two user-supplied UUIDs; the API body itself is XML and
    # does not echo these IDs, so MistHelper injects them before the upsert.
    'downloadMspSamlMetadata': {                                                    # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of business fields
        'primary_key': ['msp_id', 'sso_id'],                                        # supplied by user, injected pre-write
        'indexes': ['valid_until', 'metadata_sha256'],                              # expiry scan + rotation detection
        'table': 'msp_sso_saml_metadata',                                           # single target SQLite table
    },
}
```

There is no MistHelper-internal sub-table key for this endpoint because the response is
a single XML document with no nested arrays to flatten into a child table.
