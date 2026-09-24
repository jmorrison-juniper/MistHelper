# Tasks: Answer a browser page view of a fault with the error page

**Issue**: #3274 | **Plan**: [plan.md](plan.md)

- [x] T001 Contract test for an unknown path, a refused method, an unexpected fault, each bound status, and the JSON clients.
- [x] T002 Guard proof: T001 fails on the old handler.
- [x] T003 Add `error_answer`, `page_wording`, and the two wording constants to `factory.py`.
- [x] T004 Call `error_answer` from `handle_error`, and keep the `Allow` header copy.
- [x] T005 Return the short envelope from the address hook of `security.py`, and prove that the old abort path fails FR-009.
- [x] T006 Browser test for the operator journeys, with screenshots.
- [x] T007 Run the upgrade portal contract tests and the unit tests for regressions.
