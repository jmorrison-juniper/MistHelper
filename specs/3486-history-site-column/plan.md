# Implementation Plan: The Captures table of the history with no site names the site of each row

**Issue**: #3486 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

The Captures table of the history with no site shows no site. A new class,
`HistoryCaptureColumns`, holds the column rule of the table. It gives the
column flag, the column count, and the second sentence of the caption.

`page_rows` adds the site text and the site test identifier to each row. The
template prints a Site header and a site cell when the flag is true. The
stylesheet holds a second width set for the table of ten columns.

## Technical context

- Python 3.13, Flask, Jinja, and CSS. No new dependency.
- No route change, no schema change, and no change to a JSON body.
- No new cloud read, no new store read, and no new write.
- The unit tests read the class, the row builder, and the stylesheet. They
  render the real template with no Flask application.
- The contract tests drive the real history route with a capture list of two
  sites.
- The browser journey drives the real history page of the browser test server.

## Constitution check

| Principle | Result |
| - | - |
| I. Five-item rule | Pass. The new class holds one field and three properties. Each new function takes five parameters or fewer and holds fewer than 25 lines. |
| II. Class-based design | Pass. The column rule lives in its own class. The rename removes no call site and adds no wrapper. |
| III. Safety first | Pass. The change adds no write, and the page keeps its controls. |
| IV. Full pipeline | Pass. Tests, gates, a pull request, a hand merge, and a class B deploy. |
| V. Observability | Pass. `page_rows` logs before and after it builds the rows. |
| VI. Inline comments | Pass. Each new line carries a comment. A Jinja comment explains the column. |
| VII. Action logging | Pass. The row build is the only new action, and it logs. |

`MistHelper.py` does not change.

## Files

| File | Change |
| - | - |
| `src/interfaces/portals/upgrade_portal/app/routes/review.py` | The rename to `record_site_label`. The new constant `SITE_TEST_ID_PREFIX`. `page_rows` adds the site text and the site test identifier. The new class `HistoryCaptureColumns`. `history_page` gives the template one instance as `history_columns`. |
| `src/interfaces/portals/upgrade_portal/app/assets/templates/review/history.html` | The table class, the Site header, the site cell, the caption, and the span of the empty row. |
| `src/interfaces/portals/upgrade_portal/app/assets/static/css/portal.css` | The width set of ten columns, and the clip rule of the site cell. |
| `specs/1823-upgrade-capture-portal/contracts/ui-testids.md` | One new row for `history-site-{capture_id}`. |
| `tests/unit/upgrade_portal/test_issue_3486_history_site_column.py` | New. The column class, the rows, the render, and the stylesheet rules. |
| `tests/contract/upgrade_portal/test_history_routes.py` | The Site column of the page with no site over two sites. No Site column on the page of one site. |
| `tests/e2e/upgrade_portal/test_history_site_column_journey.py` | New. The browser journeys, with a screenshot of each page. |
| `changelog.d/issue-3486-history-site-column.md` | New. The release note. |

## Test plan

1. Write the new tests first. Run them on the old code, and record the red
   result.
2. Change the code, the template, and the stylesheet. Run the tests green.
3. Read each screenshot of the browser journey.
4. Run the unit suite and the contract suite of the portal, the integration
   suite, and the guardrails. Also run each browser file that opens the
   history page. Keep the files of the folder `test_run_controls` together.

## Gates

py_compile, ruff, black, mypy (the `MYPY_PATHS` of `ci.yml`), bandit,
vulture, interrogate, radon, pydocstyle, pylint, and the test quality gate.
Also run the STE lint of each new Markdown file.

## Deploy

Do a class B deploy to port 8056 after the merge. Copy these three files from
the squash commit: `app/routes/review.py`, `review/history.html`, and
`static/css/portal.css`.

Then send HUP to the 8056 master only. The new workers load the Python module
and the template again. The stylesheet is a static file. The portal sends it
with `Cache-Control: no-store`, so the next page load reads the new file.
