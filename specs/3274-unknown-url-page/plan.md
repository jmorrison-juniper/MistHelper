# Implementation Plan: Answer a browser page view of a fault with the error page

**Issue**: #3274 | **Spec**: [spec.md](spec.md)

## Summary

`handle_error` asks `wants_browser_page` which answer the client reads. A
browser page view gets `error_page`, and every other client keeps the JSON
envelope. The `Allow` header copy runs on both answers.

## Technical context

- Python 3.13, Flask 3, and Jinja with autoescape.
- `register_error_handlers` binds `handle_error` with `functools.partial` to
  each status of `ERROR_CODES`.
- `copy_allow_header` copies `valid_methods` from a refused-method fault onto
  the answer. It needs a `Response` object.
- `error_page` from #3276 and #3275 returns the rendered page text and the
  status. It passes the real session state to the header partial.
- `wants_browser_page` from #3275 returns true only for a stated preference
  for HTML with no script header. A client with no `Accept` header, with
  `Accept: */*`, or with a stylesheet or image `Accept` value reads JSON.
- `request.url_rule` is None when the router found no route for the path.

## Design

1. `factory.py`: add `make_response` to the Flask import.
2. `factory.py`: add the constants `NO_PAGE_TITLE` and `NO_PAGE_MESSAGE`. The
   JSON sentence "The portal found no such record" misleads an operator who
   typed a wrong address.
3. `factory.py`: add `error_answer(status)`. It returns `json_error` for a
   script or a JSON client. For a browser page view, it returns
   `make_response(error_page(...))`.
4. `factory.py`: add `page_wording(status)`. It returns the two new constants
   for a 404 answer with no matched route, and None for each other case.
5. `factory.py`: `handle_error` calls `error_answer`, then `copy_allow_header`.
6. `security.py`: the address hook returns `json_error(403)` itself and no
   longer raises `abort(403)`. A blocked browser then keeps the short envelope
   and gets no session cookie. The hook imports the factory late, as
   `csrf_error_response` does, because the factory imports `security.py`.

## Test plan

| Test | Proves |
| - | - |
| `tests/contract/upgrade_portal/test_unknown_url_page.py` | FR-001 to FR-009 through the test client. |
| `tests/contract/upgrade_portal/test_errors.py` | The JSON envelope stays the same for a client with no `Accept` header, and for a blocked address. |
| `tests/e2e/upgrade_portal/test_unknown_url_page.py` | The operator journeys in a real browser, with screenshots. |

Guard proof: the new contract test fails on the old handler, because the
handler answers JSON to a browser page view.

## Risks

- A test that sends `Accept: text/html` to a fault path and expects JSON now
  reads a page. The full run of the upgrade portal contract tests and unit
  tests proves the effect.
- A render fault inside the 500 handler. The page needs only the layout, the
  header partial, and the session registry. The registry raises no fault.
