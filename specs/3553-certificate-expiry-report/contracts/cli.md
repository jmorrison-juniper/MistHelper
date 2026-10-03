# Contract: Menu 272 Certificate Expiry Report

## Entry point

Menu 272 runs:

```text
src.mist.intelligence.reports.certificate_expiry.operation.CertificateExpiryReport.run
```

The operation is read-only and safe. It must not prompt during `--test`.

## Runtime dependencies

`operation.py` must resolve shared dependencies through:

```text
src.foundation.runtime.config.source_dependency_resolver.SourceDependencyResolver
```

Required resolver usage:

- `SourceDependencyResolver.ConfigUtils.get_cached_or_prompted_org_id()`
- `SourceDependencyResolver.apisession`
- `SourceDependencyResolver.DataExporter.write_with_format_selection()`

## Mist API reads

The client must read these operations when the configured session and organization permit them.

| OperationId | Path | Purpose |
| - | - | - |
| `listOrgDevicesStats` | `GET /api/v1/orgs/{org_id}/stats/devices` | Device `cert_expiry` values. |
| `getOrgSettings` | `GET /api/v1/orgs/{org_id}/setting` | RadSec, device certificate, NAC CA, and NAC server certificate fields. |
| `listOrgCertificates` | `GET /api/v1/orgs/{org_id}/cert` | Organization CA certificate data. |
| `listOrgSsos` | `GET /api/v1/orgs/{org_id}/ssos` | Organization SSO IdP certificates. |
| `listOrgPskPortals` | `GET /api/v1/orgs/{org_id}/pskportals` | PSK portal SSO IdP certificates. |
| `getOrgCrlFile` | `GET /api/v1/orgs/{org_id}/crl` | CRL availability evidence. No expiry row is emitted. |
| `getOrgNacCrl` | `GET /api/v1/orgs/{org_id}/setting/mist_nac_crls` | NAC CRL metadata evidence. No expiry row is emitted. |

The implementation must inspect installed SDK signatures before it writes these calls.

## Output contract

File:

```text
data/CertificateExpiry.csv
```

Exporter call:

```text
SourceDependencyResolver.DataExporter.write_with_format_selection(
    rows,
    "CertificateExpiry.csv",
    api_function_name="certificate_expiry_report",
    fieldnames=CertificateExpiryRecord.column_names(),
)
```

Required columns:

| Column | Required | Meaning |
| - | - | - |
| `org_id` | Yes | Organization identifier. |
| `source_name` | Yes | Non-sensitive source key used to keep database rows distinct. |
| `scope` | Yes | Certificate scope. |
| `owner_name` | Yes | Device, portal, SSO, or source name. |
| `subject` | No | Parsed certificate subject. |
| `issuer` | No | Parsed certificate issuer. |
| `serial` | No | Parsed certificate serial. |
| `not_after` | No | UTC ISO 8601 expiry date and time. |
| `days_remaining` | No | Full days remaining. |
| `band` | Yes | Expiry band. |
| `note` | No | Parse or source note. |

## Console contract

The operation must print one console summary line for each band and log the same line:

```text
Certificate expiry band expired: <count>
Certificate expiry band 0-30: <count>
Certificate expiry band 31-90: <count>
Certificate expiry band more than 90: <count>
```

It must also name failed sources separately. A failed source is not an empty source.

## Privacy contract

The report must not write or log these values:

- PEM certificate bodies.
- Private key text.
- Private key passwords.
- LDAP bind passwords.
- OAuth private keys.

Allowed certificate-derived values:

- Subject.
- Issuer.
- Serial.
- Expiry date.
- Days remaining.
- Band.
- Parse note.

## Test contract

Unit tests must use synthetic fixtures and must not make network calls.

Required test groups:

1. Band boundaries for expired, `0-30`, `31-90`, and `more than 90`.
2. PEM parse success with `cryptography`.
3. PEM parse failure creates one `unparsable` row.
4. Epoch `cert_expiry` normalization.
5. Pending certificate expiry normalization.
6. Privacy check for PEM bodies and private key-like text.
7. Operation uses `SourceDependencyResolver` for session, organization, and exporter.
8. Console band counts match CSV row counts.
