# Contracts: Upgrade Pre-Check and Post-Check Portal

**Feature**: 1823-upgrade-capture-portal
**Date**: 2026-08-19

## Files

| File | Subject |
| --- | --- |
| `http-api.md` | Every browser endpoint and every JSON endpoint |
| `upgrade-service.md` | The Python seam at `src/firmware/upgrade_service.py` |
| `site-lock.md` | The Redis lock protocol across worker processes |
| `ui-testids.md` | The stable test identifier on every control a test drives |

## Rules that apply to every contract

### Cross-site request forgery

Every request that changes state carries a token.

- The server renders the token into a meta tag named `csrf-token`.
- The browser reads the tag and sends the value in the `X-CSRFToken` header.
- A request without a valid token receives `400` with the error code
  `csrf_missing`.
- A `GET` request never changes state, so a `GET` request needs no token.

### Error envelope

Every JSON error uses one shape. No other shape is allowed.

```json
{
  "error": {
    "code": "site_locked",
    "message": "Another operator holds this site.",
    "details": { "actor_email": "person@example.com" }
  }
}
```

Rules for the envelope.

1. `code` is a fixed lower-case string. A test asserts on `code`, never on
   `message`.
2. `message` is one plain sentence for the operator. It never holds a stack trace,
   a token, or a password.
3. `details` is optional and holds no credential value.

### Authentication

Every endpoint except the sign-in pages requires a signed-in session. A request
without a session receives `401` with the code `not_authenticated`. The portal
refers to a stored credential by its variable name only. The portal never shows,
logs, or stores a password value or a token value (FR-009).

### Content type

Every JSON endpoint accepts and returns `application/json`. Every page endpoint
returns `text/html`.

### Status codes

| Code | Meaning in this portal |
| --- | --- |
| 200 | The request succeeded |
| 202 | The portal accepted long work and started it in the background |
| 400 | The request was malformed, or a confirmation word was wrong |
| 401 | No signed-in session |
| 403 | The session may not act on this organization or site |
| 404 | No such run, capture, site, or organization |
| 409 | Another operator holds the site lock |
| 429 | The cloud rate limit stopped the portal |
| 500 | An unexpected fault. The message stays plain. |
