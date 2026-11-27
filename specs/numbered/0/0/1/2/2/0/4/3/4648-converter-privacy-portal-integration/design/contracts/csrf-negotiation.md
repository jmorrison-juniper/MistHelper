# Contract: CSRF and Content Negotiation

## Shared answer rule

The shared handler answers each CSRF failure. Source: `web_portal/services/config.py` lines 317 to 330.

- The answer is JSON when the path starts with `/api/`, or when `Accept` prefers `application/json`. Source: lines 333 to 338.
- Otherwise the answer is the Flask-WTF error page from `error.get_response()` (line 321).
- Both forms return status 400. The JSON form uses status 400 at line 328.

Decision D-6 keeps the shared handler. A converter-specific handler would change shared request handling.

## Matrix

| Request | Accept | Expected status | Expected body |
| - | - | - | - |
| POST `/cisco-config-converter/preview` without a token | `application/json` | 400 | JSON with `error`, `code` set to `csrf_expired`, and `detail` |
| POST `/cisco-config-converter/preview` without a token | `text/html` or absent | 400 | Flask-WTF HTML error page |
| POST `/cisco-config-converter/review` without a token | `application/json` | 400 | JSON with `error` and `code` set to `csrf_expired` |
| POST `/cisco-config-converter/export` without a token | `application/json` | 400 | JSON with `error` and `code` set to `csrf_expired` |
| POST `/cisco-config-converter/review` with a token and a JSON list | `application/json` | 400 | JSON with `error` set to "Submit a valid JSON proposal." (routes.py lines 130 to 145) |
| POST a test-only `/api/` route without a token | any | 400 | JSON with `code` set to `csrf_expired` (line 335) |
| POST `/cisco-config-converter` without the trailing slash | any | 308 redirect | No body parse |
| POST `/cisco-config-converter/preview` above 16 MiB plus 16 KiB | any | 413 | No body parse (routes.py line 36) |

## Forbidden changes

- A converter-specific CSRF handler.
- A change to the `Accept` rule for paths outside the converter prefix.

## Evidence

Tests `test_converter_post_without_token_returns_400`, `test_json_client_gets_csrf_expired_answer`, `test_html_client_gets_html_csrf_answer`, `test_api_prefix_keeps_json_csrf_answer`, `test_prefix_without_slash_redirects_before_parse`, and `test_oversize_converter_body_returns_413` cover each row.
