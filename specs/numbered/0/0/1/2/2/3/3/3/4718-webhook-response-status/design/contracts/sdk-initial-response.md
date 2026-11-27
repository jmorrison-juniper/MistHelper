# Contract: SDK initial response

## Scope

This contract covers the initial response of two SDK calls:

- `mistapi.api.v1.orgs.webhooks.listOrgWebhooks`, defined at `.venv\Lib\site-packages\mistapi\api\v1\orgs\webhooks.py` line 17 (R76).
- `mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries`, defined in the same file at line 255 (R77).

## Input

- The exporter reads the `status_code` attribute of the response (R79).
- The exporter reads the `data` value only through `mistapi.get_all` (R78, R80, R81).
- The exporter reads no other attribute before pagination.

## Acceptance rule

Accept an initial response only when all of these statements hold:

1. The `status_code` attribute exists.
2. The value is an integer.
3. The value is not a Boolean.
4. The value is 200 or higher and 299 or lower.

Reject every other response before pagination.

## Reject outcome

- List call: return no selection. Log one error with the fixed wording in `operator-messages.md`.
- Delivery call: return from `deliveries()`. Log one error. Make zero writer calls.
- Both calls: make zero pagination calls.

## Accept outcome

- Call `mistapi.get_all` once with the same response and the resolver session.
- Continue to the empty-result notice when the result is empty.
- Continue to the write step when the result holds rows.

## Case table

| Input | Outcome |
| - | - |
| 200, 201, 204, 299 | Accept |
| 199, 300, 399, 400, 403, 404, 429, 500, 503, 600 | Reject |
| -1, 0 | Reject |
| True, False | Reject |
| "200", "403", "" | Reject |
| 200.0 | Reject |
| None | Reject |
| Attribute absent | Reject |
| List, dictionary, or object without an attribute | Reject |

## Documented responses

The Mist REST contract lists these responses (`documentation\mist-api-openapi31yaml.yaml`):

- `listOrgWebhooks`: 200, 400, 401, 403, 404, and 429 at lines 23871 to 23883.
- `searchOrgWebhooksDeliveries`: 200, 400, 401, 403, 404, and 429 at lines 24106 to 24118.

The contract lists no HTTP 500 or 503 response for either operation. The rule still rejects both codes.

## Notes

- The contract adds no field, no endpoint, and no direct HTTP call.
- The SDK sets `status_code` to None after a transport failure (`__api_response.py` lines 43 and 48, R79).
