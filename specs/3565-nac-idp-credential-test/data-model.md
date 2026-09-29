# Data Model: NAC IDP Credential Test

## IdentityProviderChoice

Represents one selectable identity provider.

| Field | Type | Rule |
| - | - | - |
| `idp_id` | string | Required. UUID text from `mist_nac.idps[*].id` or a fallback SSO row. |
| `name` | string | Required. Display name. Falls back to the provider identifier. |
| `idp_type` | string | Optional. Human-readable provider type when Mist returns it. |
| `source` | string | Required. `mist_nac.idps` or `listOrgSsos`. |
| `realms` | tuple of strings | Optional. User realms from organization settings. |

## CredentialTestRequest

Represents one API request body.

| Field | Type | Rule |
| - | - | - |
| `idp_id` | string | Required. Must match the selected provider. |
| `username` | string | Required. Trimmed. |
| `password` | string | Required. Hidden input only. |

The request converts to a dictionary with exactly `idp_id`, `username`, and `password`.

## CredentialTestResult

Represents the safe result of one validation.

| Field | Type | Rule |
| - | - | - |
| `provider` | IdentityProviderChoice | Required. The selected provider. |
| `username` | string | Required. Safe to export. |
| `status` | string | Required. `success`, `failure`, or `unknown`. |
| `reason` | string | Optional. Error or reason from Mist. |
| `attributes` | mapping | Optional. Non-secret response fields from Mist. |
| `tested_at` | string | Required. UTC ISO 8601 time. |

## CredentialTestExportRow

Represents one row written to `NacIdpCredentialTest.csv`.

| Field | Source | Secret state |
| - | - | - |
| `tested_at` | result time | Safe |
| `idp_id` | provider identifier | Safe |
| `idp_name` | provider name | Safe |
| `idp_type` | provider type | Safe |
| `idp_source` | provider source | Safe |
| `username` | request username | Safe |
| `verdict` | result status | Safe |
| `reason` | result reason | Safe |
| `attributes` | JSON text of result attributes | Safe after password exclusion |

The export row never includes `password`.
