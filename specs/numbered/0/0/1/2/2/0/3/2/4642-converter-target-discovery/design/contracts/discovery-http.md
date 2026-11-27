# Contract: Discovery HTTP interface

Scope: three read-only GET routes in the converter blueprint. The blueprint prefix is `/cisco-config-converter`. Decisions D-2, D-4, and D-5 in `design/research.md` define this contract.

## Routes

| Method | Path | Query | Purpose |
| - | - | - | - |
| GET | `/cisco-config-converter/discovery/status` | none | Connection and membership status for the operator session. |
| GET | `/cisco-config-converter/discovery/sites` | `org_id` (UUID, required) | Site list for one verified organization. |
| GET | `/cisco-config-converter/discovery/gateways` | `org_id` (UUID, required) | Gateway inventory for one verified organization. |

Each route is a GET. No CSRF token applies. Each response carries `Cache-Control: no-store` through the blueprint `after_request` hook (FR-019).

## Response Envelope

Every lookup outcome uses HTTP 200 and this envelope.

```json
{
  "check": "sites",
  "state": "verified",
  "reason": "none",
  "org_id": "3f1c9d2e-8a4b-4c6d-9e7f-0a1b2c3d4e5f",
  "pages": 1,
  "items": [
    {"id": "7a2b4c6d-1e3f-4a5b-8c9d-0e1f2a3b4c5d", "name": "Branch Site A", "duplicate_name": false}
  ]
}
```

Rules:

- `state` holds one of `verified`, `unavailable`, `denied`, or `failed` (FR-001).
- `items` holds a list only for `verified`. For each other state, `items` is null (FR-003).
- `pages` holds the count of pages that were read. It never exceeds 50 (FR-010).
- `org_id` is null for `status`.

## Example Outcomes

| Check | State | Reason | Items |
| - | - | - | - |
| status | unavailable | no_session | null |
| status | verified | none | list of `{org_id, scope, role}` entries |
| sites | denied | not_member | null |
| sites | failed | completion_unproven | null |
| gateways | verified | none | list of gateway objects, possibly empty |

## Reason Codes

| Reason | State | Meaning |
| - | - | - |
| `none` | verified | The read completed. |
| `no_session` | unavailable | The request holds no operator session. |
| `no_response` | unavailable | The SDK returned no HTTP status. |
| `rate_limited` | unavailable | Mist returned HTTP 429 after the SDK retries. |
| `service_unavailable` | unavailable | Mist returned HTTP 502, 503, or 504. |
| `unauthorized` | denied | Mist returned HTTP 401. |
| `forbidden` | denied | Mist returned HTTP 403. |
| `not_member` | denied | The privilege list holds no entry for the requested organization. |
| `not_found` | failed | Mist returned HTTP 404. |
| `client_error` | failed | Mist returned another 4xx status, including 400. |
| `server_error` | failed | Mist returned HTTP 500 or another 5xx status. |
| `unexpected_response` | failed | The payload has no expected list or privilege list. |
| `completion_unproven` | failed | A full last page came without `X-Page-Total`. |
| `page_limit_exceeded` | failed | A list needs more than 50 pages. |
| `lost_page` | failed | A later page could not be read. |
| `exception` | failed | The client raised an unexpected exception. The log holds the type name only. |

## Input Errors

An `org_id` that is not a UUID returns HTTP 400 before any SDK call:

```json
{"error": "Select an organization identifier in UUID form."}
```

Input errors use the error key `error`. Lookup outcomes use the envelope above, so a client separates a request error from a check outcome.

## Logging

Each route logs one `info` line before the check and one `debug` line after it. The lines hold the check name, the state, the reason, and the counts. The lines never hold a token, a cookie, an authorization header, or a site name (FR-016).
