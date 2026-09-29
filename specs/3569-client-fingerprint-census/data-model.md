# Data Model: Client Device Fingerprint Census

## Entity: DistinctField

| Field | Type | Rule |
| - | - | - |
| `value` | string | One of `family`, `model`, `os`, or `os_type`. |
| `label` | string | Human-readable label shown in the prompt. |

## Entity: FingerprintCensusRow

| Field | Type | Rule |
| - | - | - |
| `site_id` | string | The selected Mist site identifier. |
| `site_name` | string | The selected Mist site name. |
| `distinct` | string | The selected distinct field. |
| `value` | string | The result property value, or `Unknown` when the API omits it. |
| `count` | integer | The number of clients in that group. |

## Validation Rules

1. Reject a distinct value that is not in the OpenAPI enum.
2. Convert missing or empty result properties to `Unknown`.
3. Convert missing or non-numeric counts to `0`.
4. Sort display rows by `count` descending, then `value` ascending.
5. Limit console rows to 20.

## Empty State

An empty response has no `results`. The operation writes `ClientFingerprintCensus.csv` with headers only and prints `The client fingerprint census is empty for this site.`
