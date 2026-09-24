# Implementation Plan: Answer an unknown run ID with a 404 error page

**Issue**: #3276 | **Spec**: [spec.md](spec.md)

## Summary

Add one builder for the HTML error page beside `json_error` in `factory.py`.
The three run pages call it when the store holds no run with the ID.

## Technical context

- Python 3.13, Flask 3, and Jinja with autoescape.
- `factory.py` owns `ERROR_CODES`, `ERROR_MESSAGES`, and `json_error`. The new
  builder reads the same two tables, so a page and an envelope share one code
  and one sentence for each status.
- `routes/upgrade.py` already imports `json_error` from `..factory`. So the new
  import adds no new module edge.
- `create_run` writes the record before it answers the run ID. So a missing
  record on a run page always means an unknown run ID, never a new run.
- The multi-site job writes its records through the same `run_store()`.

## Design

1. `factory.py`: add `ERROR_PAGE_TEMPLATE = "error.html"` and the function
   `error_page(status, code, message, title)`. It renders the template with the
   four values and answers the status.
2. `routes/upgrade.py`: add `RUN_NOT_FOUND_TITLE`, the sentence
   `RUN_PAGE_NOT_FOUND_MESSAGE`, and the function `run_page_not_found(run_id)`.
   The three page routes call it when `load_run` answers None.
3. `error.html`: add a `data-testid` value to the heading, the sentence, the
   status code, the error code, and the link. A browser test can then read
   each part.

## Test plan

| Test | Proves |
| - | - |
| `tests/contract/upgrade_portal/test_upgrade_routes/test_unknown_run_pages.py` | FR-001 to FR-005 and FR-007 for the three pages. |
| `tests/e2e/upgrade_portal/test_unknown_run_page.py` | The operator journey in a real browser, with a screenshot. |

Guard proof: the new contract test fails on the old routes, because each page
answers 200.

## Risks

- A test that opens a run page with no seeded record now reads 404. The
  search of `tests/` found no such test. The full run of the upgrade portal
  contract tests proves it.
