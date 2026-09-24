# Tasks: Answer an unknown run ID with a 404 error page

**Issue**: #3276 | **Plan**: [plan.md](plan.md)

- [x] T001 Contract test for the three pages with an unknown run ID, an escaped run ID, and a known run.
- [x] T002 Guard proof: T001 fails on the old routes.
- [x] T003 Add `ERROR_PAGE_TEMPLATE` and `error_page` to `factory.py`.
- [x] T004 Add `run_page_not_found` to `routes/upgrade.py`, and call it from the three page routes.
- [x] T005 Add the `data-testid` values to `error.html`.
- [x] T006 Browser test for the operator journey, with a screenshot.
- [x] T007 Run the upgrade portal contract tests and the unit tests for regressions.
