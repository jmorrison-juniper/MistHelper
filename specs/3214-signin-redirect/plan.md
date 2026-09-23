# Implementation Plan: Send a browser page with no session to the sign-in form

**Issue**: #3214 | **Spec**: [spec.md](spec.md)

## Design

1. Add `SIGN_IN_PAGE_PATH` and `SIGN_IN_REDIRECT_STATUS` to
   `src/upgrade_portal/runtime/identity.py`.
2. Add `_prefers_page()`. It uses the same negotiation as
   `org_upgrade._wants_html`: `best_match(("application/json", "text/html"))`,
   so JSON wins a tie. Only a GET qualifies.
3. `_refusal_for_request` returns the redirect for a page and the envelope for
   every other request.

The module imports no application module, because the factory imports the
route modules that apply the guard. The path therefore stays a constant.

## Tests

- Contract: a browser page gets 303 to `/auth/signin`, and `*/*` and
  `application/json` keep the 401 envelope (`tests/contract/upgrade_portal/test_security.py`).
- Browser: four checks of `tests/e2e/upgrade_portal/test_browser_token_signin.py`
  now require the sign-in form after sign-out, after a refused token, after an
  empty token, and with no session.

## Risks

- A browser tab that opens a JSON route by hand now gets the form. That is the
  correct reading of a page visit.
