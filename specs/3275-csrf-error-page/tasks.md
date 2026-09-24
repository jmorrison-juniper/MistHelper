# Tasks: Answer a refused browser form post with an error page

**Issue**: #3275 | **Plan**: [plan.md](plan.md)

- [x] T001 Contract test for a browser form post, the link back, the refused referrers, the script, and a JSON client.
- [x] T002 Guard proof: T001 fails on the old handler.
- [x] T003 Move `wants_browser_page` and its four constants into `factory.py`, and read it from `auth.py` and `select.py`.
- [x] T004 Add `form_return_path` and the `back_path` argument of `error_page` to `factory.py`.
- [x] T005 Answer `error_page` from `csrf_error_response` for a browser page.
- [x] T006 Add the link back to `error.html`.
- [x] T007 Browser test for the two operator journeys, with screenshots.
- [x] T008 Run the upgrade portal contract tests and the unit tests for regressions.
