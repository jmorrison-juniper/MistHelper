# Data Model: Certificate Expiry Report

## Entity: CertificateSource

Purpose: Describes one Mist source that can produce certificate rows.

Fields:

| Field | Type | Required | Rule |
| - | - | - | - |
| `source_name` | string | Yes | Stable internal source key. |
| `operation_id` | string | Yes | Mist API operationId or `getOrgSettings` field group. |
| `scope` | string | Yes | One supported report scope. |
| `owner_field` | string | Yes | Field used to label the row owner. |
| `value_path` | string | Yes | Dot path or list path to the certificate value. |
| `value_kind` | string | Yes | `pem`, `epoch`, or `pending_epoch`. |

Supported scope values:

- `device`
- `org device cert`
- `NAC server cert`
- `SSO IdP`
- `PSK portal IdP`
- `CA cert`

Validation rules:

- The source must never expose a private key field to normalization.
- The source must preserve the source name for parse-failure notes.
- The source must produce no row when the certificate value is absent.

## Entity: CertificateRecord

Purpose: One metadata-only row in `CertificateExpiry.csv`.

Fields:

| Field | Type | Required | Rule |
| - | - | - | - |
| `org_id` | string | Yes | Organization identifier used by the report. |
| `source_name` | string | Yes | Non-sensitive source key used to keep database rows distinct. |
| `scope` | string | Yes | One supported scope value. |
| `owner_name` | string | Yes | Device name, portal name, SSO name, or source label. |
| `subject` | string | No | Subject from the parsed certificate, when available. |
| `issuer` | string | No | Issuer from the parsed certificate, when available. |
| `serial` | string | No | Certificate serial, when available. |
| `not_after` | string | No | UTC ISO 8601 date and time. Blank when unavailable. |
| `days_remaining` | integer | No | Full days remaining. Blank when `not_after` is unavailable. |
| `band` | string | Yes | `expired`, `0-30`, `31-90`, or `more than 90`. |
| `note` | string | No | `unparsable` for a parse failure, or a short source note. |

Validation rules:

- `not_after` must use UTC.
- `expired` applies when `not_after` is less than or equal to the run time.
- `0-30` applies when the certificate is not expired and has 0 through 30 full days remaining.
- `31-90` applies when the certificate has 31 through 90 full days remaining.
- `more than 90` applies when the certificate has more than 90 full days remaining.
- A failed PEM parse must produce exactly one row with note `unparsable`.
- A failed PEM parse uses band `expired` as a fail-safe risk category when no expiry date is available.
- A row must not contain `BEGIN CERTIFICATE`, `END CERTIFICATE`, `BEGIN PRIVATE KEY`, or raw PEM text.

## Entity: CertificateReport

Purpose: Carries all rows, band counts, and completeness notes for one run.

Fields:

| Field | Type | Required | Rule |
| - | - | - | - |
| `org_id` | string | Yes | Organization identifier used by the report. |
| `generated_at` | string | Yes | UTC ISO 8601 run timestamp. |
| `rows` | list of `CertificateRecord` | Yes | Metadata-only report rows. |
| `band_counts` | map | Yes | Counts for all four bands. |
| `source_counts` | map | Yes | Count of rows by source. |
| `failed_sources` | list of strings | Yes | Source names that could not be read. |

Validation rules:

- `band_counts` must include every band even when the count is zero.
- `band_counts` must match the row list exactly.
- A failed source must not stop rows from other sources.
- A failed source must be visible in the console summary.

## Normalization states

| State | Meaning | Output behavior |
| - | - | - |
| `absent` | The source did not include a certificate value. | Write no row. |
| `parsed` | A PEM value parsed successfully. | Write subject, issuer, serial, and `not_after`. |
| `epoch` | The source supplied an epoch expiry value. | Write `not_after`, `days_remaining`, and band. |
| `pending_epoch` | The source supplied a pending certificate epoch value. | Write the pending expiry row with a source note. |
| `unparsable` | The value existed but could not be parsed. | Write one row with note `unparsable` and band `expired`. |

## Source mapping

| Source | OperationId | Scope | Value |
| - | - | - | - |
| Device stats | `listOrgDevicesStats` | `device` | `cert_expiry` epoch |
| Org certificates | `listOrgCertificates` | `CA cert` | `cert` and `pending_cert` PEM |
| Org settings RadSec | `getOrgSettings` | `CA cert` | `cacerts[]` PEM |
| Org settings device cert | `getOrgSettings` | `org device cert` | `device_cert.cert` PEM |
| Org settings NAC CA | `getOrgSettings` | `CA cert` | `mist_nac.cacerts[]` PEM |
| Org settings NAC server | `getOrgSettings` | `NAC server cert` | `mist_nac.server_cert.cert` PEM |
| Org SSO | `listOrgSsos` | `SSO IdP` | `idp_cert` PEM |
| PSK portal SSO | `listOrgPskPortals` | `PSK portal IdP` | `sso.idp_cert` PEM |
| Org CRL file | `getOrgCrlFile` | None | Evidence only; no expiry row |
| NAC CRL metadata | `getOrgNacCrl` | None | Evidence only; no expiry row |
