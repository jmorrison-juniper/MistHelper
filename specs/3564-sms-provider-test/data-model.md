# Data Model: Test the guest portal SMS provider

## SmsProvider

| Field | Type | Rule |
| - | - | - |
| `key` | string | One of `twilio`, `smsglobal`, or `telstra`. |
| `label` | string | Human-readable provider name. |
| `operation_id` | string | OpenAPI operation identifier. |
| `body_fields` | list | Ordered fields sent to Mist. |
| `secret_fields` | set | Fields collected with hidden input. |

## SmsProviderPromptValues

| Field | Type | Rule |
| - | - | - |
| `provider` | `SmsProvider` | Required. |
| `destination` | string | Required `to` number. |
| `values` | dict | Contains provider-specific values before body creation. |

Validation rules:

- Public fields use `InputUtils.safe_input`.
- Secret fields use hidden input.
- Empty required fields stop the operation before an API request.

## SmsProviderRequest

| Field | Type | Rule |
| - | - | - |
| `provider` | `SmsProvider` | Required. |
| `body` | dict | Must match the provider OpenAPI body keys. |

Validation rules:

- Twilio body keys are `from`, `to`, `twilio_auth_token`, and `twilio_sid`.
- SMSGlobal body keys are `smsglobal_api_key`, `smsglobal_api_secret`, and `to`.
- Telstra body keys are `telstra_client_id`, `telstra_client_secret`, and `to`.

## SmsProviderResult

| Field | Type | Rule |
| - | - | - |
| `provider` | string | Provider label. |
| `destination` | string | Destination phone number. |
| `verdict` | string | `accepted` for 2xx, otherwise `failed`. |
| `http_status` | integer or empty | HTTP status returned by Mist. |
| `response_text` | string | Short response text with no credentials. |
| `tested_at` | string | UTC ISO 8601 timestamp. |

Validation rules:

- The row must not contain provider credentials.
- The row is the only exported record for one confirmed run.
