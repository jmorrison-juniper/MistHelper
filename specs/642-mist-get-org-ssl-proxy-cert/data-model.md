# Phase 1 Data Model: getOrgSslProxyCert

## Entity: OrgSslProxyCert

The endpoint returns exactly one entity per organisation: the SSL proxy
inspection certificate installed at the org level for use by SRX gateways
performing SSL/TLS interception.

### Fields

| Field           | Type            | Source                                 | Notes |
|-----------------|-----------------|----------------------------------------|-------|
| `org_id`        | string (UUID)   | Injected by MistHelper from the caller-supplied path parameter | Primary key; **not** part of the raw API response body -- MistHelper adds it during flatten so the row is self-describing. |
| `cert`          | text (PEM)      | `response.data.cert`                   | Full PEM-encoded X.509 certificate: begins `-----BEGIN CERTIFICATE-----`, ends `-----END CERTIFICATE-----`. May be `NULL` if the org has no SSL proxy cert configured (empty response body or missing `cert` key). |
| `cert_len`      | integer         | `len(response.data.cert)` (derived)    | Byte length of the PEM string. Convenience column for quick "is this deployed?" checks without loading the whole cert. Populated during flatten; `0` if `cert` is `NULL`. |
| `fetched_at`    | text (ISO-8601) | MistHelper timestamp at fetch time     | UTC ISO-8601 string produced via `datetime.now(timezone.utc).isoformat()`. Not part of the natural PK; documents when the row was last refreshed. |

Notes on the API surface:

- Only `cert` is defined by the OpenAPI response schema.
- `org_id`, `cert_len`, and `fetched_at` are MistHelper-added envelope
  fields consistent with the pattern used by other single-object org
  exports.

### Primary Key(s)

- **Natural primary key**: `(org_id,)`. One SSL proxy cert per organisation.

### Foreign Keys

- `org_id` logically references the `orgs.id` value from
  `listOrgSites` / `getOrg` exports. MistHelper does not enforce this
  as a database-level `FOREIGN KEY` constraint (consistent with other
  org-scoped tables) but downstream analytics can `JOIN` on it.

### State Transitions

**N/A -- read-only endpoint.** The MistHelper menu item only reads the
current cert. Upsert on re-fetch replaces the row atomically via
`INSERT OR REPLACE`. There is no MistHelper-side lifecycle; the cert is
created / rotated / deleted on the Mist Cloud side by out-of-band admin
action, and this menu simply reflects the current value.

### SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS org_ssl_proxy_cert (
    org_id      TEXT NOT NULL,
    cert        TEXT,
    cert_len    INTEGER NOT NULL DEFAULT 0,
    fetched_at  TEXT NOT NULL,
    PRIMARY KEY (org_id)
);

CREATE INDEX IF NOT EXISTS idx_org_ssl_proxy_cert_org_id
    ON org_ssl_proxy_cert (org_id);
```

The DDL is emitted automatically by `DatabaseSchemaUtils.build_ddl_from_data`
using the shape of the first flattened row plus the strategy dict below.
The DDL block above is documentary; do not hand-execute it.

### ENDPOINT_PRIMARY_KEY_STRATEGIES entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary
in `MistHelper.py` (dictionary is defined around line ~1672):

```python
'getOrgSslProxyCert': {                                   # OpenAPI operationId, matches SDK function name
    'type': 'natural_pk',                                 # One cert per org -> deterministic natural key
    'primary_key': ['org_id'],                            # Caller-supplied path param; MistHelper injects into the flattened row
    'indexes': ['org_id'],                                # Only column worth indexing on this single-row table
},
```

### Flatten contract

The MistHelper flatten step produces a list of exactly one dict (or an
empty list if the API returned no cert). Shape:

```python
[
    {
        "org_id":     "<uuid-from-caller>",           # Injected; not in raw response
        "cert":       "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
        "cert_len":   1234,                            # len(cert) or 0
        "fetched_at": "2026-06-30T23:15:04+00:00",    # UTC ISO-8601
    }
]
```

A list is returned (rather than a single dict) so the row can be passed
directly into `DataExporter.write_with_format_selection(data=rows,
filename=..., api_function_name="getOrgSslProxyCert")` without a
special-case single-row code path.
