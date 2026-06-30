# Phase 1 Data Model: downloadOrgNacPortalSamlMetadata

**Branch**: `572-mist-download-org-nac-portal-saml-metadata`
**Date**: 2026-06-29
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)

## Overview

The upstream response is a single opaque XML document (a SAML 2.0
`<md:EntityDescriptor>` for the NAC portal's Service Provider role). For
storage purposes MistHelper treats the response as **one logical entity** --
the SAML metadata record for `(org_id, nacportal_id)` -- and stores it as a
single SQLite row plus a sidecar `.xml` file on disk. The two SAML
attributes most useful for operator queries (`entity_id`, `valid_until`)
are parsed out and indexed.

## Entities

### Entity 1: `OrgNacPortalSamlMetadata`

Represents the SAML SP metadata document for one NAC portal in one
organization. There is exactly one such document per `(org_id,
nacportal_id)` at any moment in time; re-downloading replaces it.

#### Fields

| Field            | Type    | Required | Source / Derivation                                                                  |
|------------------|---------|----------|--------------------------------------------------------------------------------------|
| `org_id`         | TEXT    | Yes      | User prompt (defaulted from `MIST_ORG_ID`). Mist UUID.                               |
| `nacportal_id`   | TEXT    | Yes      | User prompt. Mist UUID.                                                              |
| `entity_id`      | TEXT    | No       | Parsed from XML `EntityDescriptor/@entityID` (typically a `https://api.mist.com/...` URL). |
| `valid_until`    | TEXT    | No       | Parsed from XML `EntityDescriptor/@validUntil` (ISO-8601 UTC, e.g. `2027-10-12T21:59:01Z`). |
| `metadata_bytes` | INTEGER | Yes      | Length of the raw XML body in bytes.                                                 |
| `metadata_xml`   | TEXT    | Yes      | Verbatim XML body returned by the API. Stored for offline re-use / IdP import.       |
| `xml_file_path`  | TEXT    | Yes      | Absolute path of the sidecar `.xml` file under `data/`.                              |
| `retrieved_at`   | TEXT    | Yes      | ISO-8601 UTC timestamp recorded by MistHelper at fetch time.                         |

#### Primary Key

- **Strategy**: `natural_pk`
- **Columns**: `(org_id, nacportal_id)`

#### Foreign Keys (logical, not enforced by SQLite)

- `org_id` -> `orgs.id` (the org inventory table populated by `listOrgs`).
- `nacportal_id` -> `org_nac_portals.id` (the table populated by
  `listOrgNacPortals`, operationId `listOrgNacPortals`).

These are documented relationships only; the SQLite schema does not
declare `FOREIGN KEY` constraints because MistHelper's tables are
populated independently and may be partial.

#### Indexes

- Primary key index on `(org_id, nacportal_id)` (automatic).
- Secondary index on `entity_id` for cross-portal lookup when an operator
  has an IdP-side `entityID` in hand.
- Secondary index on `valid_until` to surface metadata documents that are
  approaching expiry.

## State Transitions

**N/A -- read-only endpoint.** The upstream resource has no MistHelper-side
lifecycle. Each invocation performs an idempotent upsert: the existing
row (if any) is replaced with fresh data; nothing is deleted or marked
inactive.

## SQLite DDL

The table is created on first run by `DataExporter.write_with_format_selection()`
using the schema below (the existing DataExporter infrastructure derives
column types from the first-row Python types):

```sql
CREATE TABLE IF NOT EXISTS org_nac_portal_saml_metadata (
    org_id          TEXT    NOT NULL,
    nacportal_id    TEXT    NOT NULL,
    entity_id       TEXT,
    valid_until     TEXT,
    metadata_bytes  INTEGER NOT NULL,
    metadata_xml    TEXT    NOT NULL,
    xml_file_path   TEXT    NOT NULL,
    retrieved_at    TEXT    NOT NULL,
    PRIMARY KEY (org_id, nacportal_id)
);

CREATE INDEX IF NOT EXISTS idx_org_nac_portal_saml_metadata_entity_id
    ON org_nac_portal_saml_metadata (entity_id);

CREATE INDEX IF NOT EXISTS idx_org_nac_portal_saml_metadata_valid_until
    ON org_nac_portal_saml_metadata (valid_until);
```

Upsert semantics on re-run are handled by `INSERT OR REPLACE` driven by
the registered PK strategy below.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (alphabetical insertion within the
`downloadOrg*` cluster):

```python
'downloadOrgNacPortalSamlMetadata': {  # Mist GET /orgs/{org_id}/nacportals/{nacportal_id}/saml_metadata.xml
    'type': 'natural_pk',                    # Stable per-portal artifact; overwrite on refresh
    'primary_key': ['org_id', 'nacportal_id'],  # Tuple uniquely identifies one SAML SP document
    'indexes': ['entity_id', 'valid_until'],    # Cross-portal lookup + expiry surveillance
    'table': 'org_nac_portal_saml_metadata',    # SQLite destination (see DDL above)
},
```

## Row-Construction Notes

The single row written by the new menu method is constructed as follows
(pseudocode, kept compact for plan reference -- real implementation lives
in `MistHelper.py` and carries inline comments on every executable line per
Constitution VI):

```python
# Parse only the two attributes we index; never log the raw XML body
from xml.etree import ElementTree as ET
root = ET.fromstring(metadata_xml)                       # Parse the SAML document
entity_id   = root.attrib.get('entityID')                # Top-level SP identifier
valid_until = root.attrib.get('validUntil')              # Document expiry (UTC)

row = {
    'org_id':         org_id,                            # From prompt / .env
    'nacportal_id':   nacportal_id,                      # From prompt
    'entity_id':      entity_id,                         # Parsed above
    'valid_until':    valid_until,                       # Parsed above
    'metadata_bytes': len(metadata_xml.encode('utf-8')), # Byte count for observability
    'metadata_xml':   metadata_xml,                      # Verbatim body for SQLite storage
    'xml_file_path':  xml_path,                          # Sidecar file written under data/
    'retrieved_at':   datetime.now(timezone.utc).isoformat(timespec='seconds'),
}
```

The row is then passed to
`DataExporter.write_with_format_selection([row], base_filename,
api_function_name="downloadOrgNacPortalSamlMetadata")` which fans the
single record out to CSV, SQLite, or ArangoDB+Redis according to the
configured backend.
