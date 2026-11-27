# Contract: Login status mapping

## Scope

This contract covers `POST /auth/login` in `mist-ops-platform/src/api/routes/health.py`. The change alters which causes reach each status. The change adds no new status code and no new response field.

## Request

- **Body**: `method` (string, default `token`) and `token` (string).
- **Token rule**: The token shape check applies before any request (FR-010).

## Responses

| Outcome | HTTP status | Body detail | Causes |
| - | - | - | - |
| Success | 200 | Session envelope with `sessionId`, `operator`, and `expiresAt` | An identity object with an email or org ids |
| Invalid token | 401 | `Invalid API token` | HTTP 401, 403, another 4xx except 429, a malformed token, or an identity with no email and no org ids |
| Unavailable Mist API | 503 | `The Mist API is unreachable. Try the login again.` | No HTTP status, HTTP 429, HTTP 1xx, 3xx, or 5xx, or a 2xx response without an identity object |

## Source mapping

- HTTP 401 is raised at `mist-ops-platform/src/api/routes/health.py` L213.
- HTTP 503 is raised at `mist-ops-platform/src/api/routes/health.py` L237-241.
- The detail texts are quoted strings. Do not change them.

## Compatibility

Clients that handle HTTP 401 and HTTP 503 need no change. A throttled login now returns HTTP 503. Earlier, it returned HTTP 401.
