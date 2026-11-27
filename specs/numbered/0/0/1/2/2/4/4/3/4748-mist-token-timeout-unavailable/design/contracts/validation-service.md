# Contract: Validation service

## Scope

This contract covers `AuthService.validate_token` and its private helpers in `mist-ops-platform/src/shared/services/auth.py`.

## Input

- `token` (string). The accepted shape is ASCII code points 33 to 126, with no comma and no empty value. Any other shape returns empty privileges without a request (FR-010).

## Output

- **Identity**: A `MistPrivileges` value with an email or org ids. The value holds the identity fields and the org and site scopes.
- **Invalid token**: An empty `MistPrivileges` value. The login route maps it to HTTP 401.
- **Unavailable Mist API**: A `MistApiUnavailableError`. The login route and the middleware map it to HTTP 503.

## Outcome rules

| Lookup result | Output |
| - | - |
| Token shape rejected | Invalid token. No request runs. |
| No HTTP status | Unavailable Mist API |
| HTTP 429 | Unavailable Mist API |
| HTTP 1xx, 3xx, or 5xx | Unavailable Mist API |
| HTTP 2xx without an identity object | Unavailable Mist API |
| HTTP 401, 403, or another 4xx except 429 | Invalid token |
| HTTP 2xx with an identity object | Identity |

## Side effects

- At most one request runs for each call. The request is GET `https://api.mist.com/api/v1/self`.
- The process environment is never read. The host and the token come from the arguments only (FR-008).
- Each request ends within 30 seconds (FR-011).
- The privilege cache write happens after a result. A failed lookup writes nothing, because the exception skips the write.

## Logging

- An info record names the start of the lookup before the request.
- A debug record names the outcome after the request. It holds the HTTP status code or the exception class name, never a token.
- A warning record names an unavailable Mist API. It holds the exception class name or the HTTP status code.
- No record holds the token value, the Authorization header, or a response body (FR-012).

## Error messages

- The `MistApiUnavailableError` message names the cause only, such as the HTTP status code or the exception class name.
- The message never holds the token value or a response body.
