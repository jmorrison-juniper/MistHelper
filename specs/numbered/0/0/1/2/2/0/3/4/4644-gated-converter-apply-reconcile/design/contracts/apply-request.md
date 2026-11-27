# Contract: Apply Request

This contract defines the request that the converter route `POST /cisco-config-converter/apply` accepts. The route is added to `ConverterRoutes.blueprint` in `routes.py` by task T012. The route stays unregistered in the web portal until gate G3 closes.

## Transport

- Method: `POST`.
- Body: JSON object with `Content-Type: application/json`.
- CSRF: The portal `CSRFProtect` guard applies, as it does for `/review` and `/export`.
- Limit: The request body holds at most 4096 bytes.

## Request Fields

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `action` | string | Yes | One of `submit`, `cancel`, or `status`. |
| `approval_id` | string | For `submit` and `cancel` | 32 lowercase hexadecimal characters. |
| `operation_id` | string | For `status` | 32 lowercase hexadecimal characters. |
| `typed_word` | string | For `submit` | Must equal `APPLY` exactly. The check is case-sensitive, with no trimming. |

Any other field causes HTTP 400.

## Behavior by Action

- `submit` checks the typed word first. It then runs the approval and backup gates. It then starts the executor. It returns the operation identifier when the run starts.
- `cancel` voids an unused approval. It refuses a consumed approval with HTTP 409.
- `status` returns the operation record for the identifier. It does not start a write.

## Responses

| Status | Meaning | Writes made |
| --- | --- | --- |
| 200 | Request accepted, or a status returned | Per the action |
| 400 | Invalid JSON, an unknown field, or a wrong typed word | None |
| 403 | No verified operator, or the family is disabled | None |
| 409 | Stale approval, consumed approval, or scope lock held | None |
| 503 | Store unavailable, or the shared secret is missing | None |

Every response carries `Cache-Control: no-store`. An error body holds a fixed code and a fixed message, and it holds no payload value.
