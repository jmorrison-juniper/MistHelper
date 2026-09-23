# Tasks: Send a browser page with no session to the sign-in form

**Issue**: #3214 | **Plan**: [plan.md](plan.md)

- [x] T001 Add the two constants and `_prefers_page` in `src/upgrade_portal/runtime/identity.py`.
- [x] T002 Return the redirect in `_refusal_for_request` for a browser page.
- [x] T003 Contract tests for the redirect and for the kept envelope.
- [x] T004 Update the four browser checks of the sign-in journeys.
- [x] T005 Guard proof: the redirect test fails on the old code.
