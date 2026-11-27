# Data Model: Report a Mist transport fault as an unavailable Mist API

This feature adds no table, no stored key, and no persistent entity. The entities below describe the runtime values of one privilege lookup.

## Entities

### SuppliedToken

- **Source**: The `token` field of the login body, or the token that the middleware reads from a session store entry.
- **Natural key**: None. The token value is the input.
- **Attributes**: The token value (secret), and its source.
- **Rules**: The token shape check runs before any request (FR-010). The token never appears in a log record or a result (FR-012).

### ValidationSession

- **Type**: `TokenValidationSession`, a subclass of `mistapi.APISession`.
- **Attributes**: The host `api.mist.com`, one token in the Authorization header, a 30-second timeout for each request, and no value from the process environment.
- **Lifetime**: One privilege lookup.

### ValidationResponse

- **Source**: `ApiResult` in `mist-ops-platform/src/shared/mist/endpoints.py`.
- **Attributes**: `status_code` (integer or None), `data` (a dictionary or a list of rows), and `success` (a boolean).
- **Rule**: `success` is False when `status_code` is None (FR-015).

### IdentityObject

- **Source**: The JSON body of GET `/api/v1/self`. The OpenAPI file defines the body as the `Admin` response (`documentation/mist-api-openapi31yaml.yaml` L25490 and L60588).
- **Attributes used**: `email`, `first_name`, `last_name`, and `privileges`. Each privilege row holds `scope`, `org_id`, `site_id`, `msp_id`, and `name`.
- **Rule**: The registry entry `self_identity` returns the object as one row (FR-014).

### PrivilegeLookupOutcome

- **Identity**: A `MistPrivileges` value with an email or org ids.
- **Invalid token**: An empty `MistPrivileges` value. The login route answers HTTP 401.
- **Unavailable Mist API**: A `MistApiUnavailableError`. The login route answers HTTP 503.

## State transitions

| From | Condition | To | Login HTTP status | Lookup result |
| - | - | - | - | - |
| Received | The token has a rejected shape | Invalid | 401 | Empty privileges. No request runs. |
| Received | The token has an accepted shape | Requested | None yet | One request runs with a 30-second timeout. |
| Requested | No HTTP status (timeout, connection error, proxy error, or a dropped exception) | Unavailable | 503 | `MistApiUnavailableError` |
| Requested | HTTP 429 | Unavailable | 503 | `MistApiUnavailableError` |
| Requested | HTTP 1xx, 3xx, or 5xx | Unavailable | 503 | `MistApiUnavailableError` |
| Requested | HTTP 2xx without an identity object | Unavailable | 503 | `MistApiUnavailableError` |
| Requested | HTTP 401, 403, or another 4xx except 429 | Invalid | 401 | Empty privileges |
| Requested | HTTP 2xx with an identity object | Identity | 200 when the identity has an email or org ids | Privileges parsed |
| Identity | No email and no org ids | Invalid | 401 | The login route rejects the identity (`health.py` L212-213) |

## Natural keys and persistence

- The login route stores organizations by the Mist organization identifier. This feature adds no key.
- The Redis privilege cache key stays `mist_priv:` followed by a SHA-256 digest of the token (`auth.py` L61, `privilege_cache_key`). This feature keeps the key format.
