# Implementation Plan: Answer a refused browser form post with an error page

**Issue**: #3275 | **Spec**: [spec.md](spec.md)

## Summary

Move the rule that separates a browser page from a script into `factory.py`.
The token check reads that rule. A browser form post gets `error_page` with a
link back to the form, and every other client keeps the JSON envelope.

## Technical context

- Python 3.13, Flask 3, `flask-wtf`, and Jinja with autoescape.
- `error_page` from #3276 renders `error.html` from the same code and message
  tables as `json_error`.
- `security.py` imports the factory late, inside `csrf_error_response`,
  because `factory.py` imports `security.py` while it loads.
- `routes/auth.py` and `routes/select.py` each hold the same rule in
  `wants_browser_page`. A unit test reads `auth.SCRIPT_HEADER` and
  `auth.wants_browser_page`.
- The portal sends `Referrer-Policy: strict-origin-when-cross-origin`. So a
  same-origin form post carries the whole address of the form page.

## Design

1. `factory.py`: add the constants `BROWSER_MIME`, `SCRIPT_MIME`,
   `SCRIPT_HEADER`, and `SCRIPT_HEADER_VALUE`. Add `wants_browser_page()` with
   the rule of the two route modules.
2. `factory.py`: add `form_return_path()`. It reads `request.referrer`. It
   returns the path and the query only when the host matches the request host,
   the path starts with one slash, and the URL map answers `GET` for the path.
3. `factory.py`: `error_page` takes a fifth argument, `back_path`. The template
   draws the link back only when the value is set. `error_page` also passes
   `signed_in` from `identity.current_session()`, because the header partial
   reads a missing value as true.
4. `security.py`: `csrf_error_response` answers `error_page` for a browser
   page, and `json_error` for every other client.
5. `routes/auth.py` and `routes/select.py`: import `wants_browser_page` from the
   factory, and remove the local copies. `auth.py` keeps `BROWSER_MIME`,
   because its sign-in page answer names that type.
6. `error.html`: add the link back with the `data-testid` value
   `error-back-link`.

## Test plan

| Test | Proves |
| - | - |
| `tests/contract/upgrade_portal/test_csrf_error_page.py` | FR-001 to FR-008 through the test client. |
| `tests/unit/upgrade_portal/test_auth.py` | The moved rule keeps its current answers. |
| `tests/e2e/upgrade_portal/test_csrf_error_page.py` | The two operator journeys in a real browser, with screenshots. |

Guard proof: the new contract test fails on the old handler, because the
handler answers JSON to a browser form post.

## Risks

- A test that posts with `Accept: text/html` and no token, and that expects
  JSON, now reads a page. The search of `tests/` found none. The full run of the
  upgrade portal contract tests proves it.
- The `Referer` header comes from the client. The path check refuses another
  host, a path with two leading slashes, and a path that the URL map does not
  serve for `GET`. Jinja escapes the value in the `href` attribute.
