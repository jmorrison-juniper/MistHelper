# Contract: Browser sign-in HTTP interface

This contract covers the web portal on port 8055. It defines three paths: `/auth/signin`, `/auth/twofactor`, and `/auth/signout`. The capture portal on port 8056 keeps its own contract.

## Routes

| Method | Path | Purpose | Request fields | Success answer | Refusal answer |
| - | - | - | - | - | - |
| GET | `/auth/signin` | Show the sign-in form | None | HTML page, status 200 | None |
| POST | `/auth/signin` | Run the password step | `email`, `password`, `host` | Browser: 303 to `/auth/twofactor` when a 2FA code is required, or 303 to `/` when the sign-in completes. Script: 200 with `{"next": "/auth/twofactor"}` or `{"next": "/"}`. | 400 `bad_credentials`, 429 `rate_limited`, 503 `network_fault`, or 409 `run_active` |
| GET | `/auth/twofactor` | Show the 2FA form | None | HTML page, status 200. With no pending sign-in, the page shows the `two_factor_expired` sentence and a link to `/auth/signin`. | None |
| POST | `/auth/twofactor` | Run the 2FA step | `code` | Browser: 303 to `/`. Script: 200 with `{"next": "/"}`. | 400 `bad_two_factor_code`, 400 `two_factor_expired`, 429 `rate_limited`, or 503 `network_fault` |
| POST | `/auth/signout` | End the process session | None | Browser: 303 to `/auth/signin`. Script: 200 with `{"next": "/auth/signin"}`. | 409 `run_active` |

The `host` field takes one value from the catalog. An empty or unknown value uses the default host, and the portal logs one warning (T019).

## Browser or script answer

- A request that accepts `text/html` and does not accept `application/json` gets the redirect.
- Any other request gets the JSON body.
- A redirect uses status 303, so the browser reads the next page with GET.

## Refusal body

A refusal answers JSON with two fields. The `error` field holds one sentence from the failure table in `spec.md`. The `code` field holds the code of that sentence.

```json
{"error": "The portal could not authenticate you. Check the email address and the password, then try again.", "code": "bad_credentials"}
```

```json
{"error": "The portal could not accept that code. Type the current code from your authenticator application, then try again.", "code": "bad_two_factor_code"}
```

## Response headers

- Every sign-in response carries `Cache-Control: no-store`.
- The browser identifier cookie is `misthelper_browser`. The value is a random token of 32 bytes. The cookie carries the flags `HttpOnly` and `SameSite=Lax`. The cookie carries `Secure` only when the request uses HTTPS. The cookie has no expiry date.

## Protection

- Every POST needs the CSRF token. The token comes from the form field `csrf_token`, or from the header `X-CSRFToken`. The existing CSRF protection answers a missing or wrong token. A script caller gets the existing JSON envelope with `code` set to `csrf_expired` (`web_portal/services/config.py`, `_register_csrf_error_handler`, R-08).
- The existing allowlist runs before every route. A blocked address gets 403 (R-09).
- No response, header, or cookie echoes the values of `email`, `password`, or `code`.

## Examples

Request body of the password step, sent as JSON, with the fields `email`, `password`, and `host`. Response for an account that requires a 2FA code:

```json
{"next": "/auth/twofactor"}
```

Request body of the 2FA step, with the field `code`. Response after the sign-in completes:

```json
{"next": "/"}
```
