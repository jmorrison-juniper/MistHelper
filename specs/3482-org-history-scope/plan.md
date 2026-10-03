# Implementation Plan: The capture history with no site names every site

**Issue**: #3482 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

The history page with no site names the site of its first row. The new frozen
class `HistoryScope` holds the scope of the request. It gives the first
sentence of the note, the holder words of the count sentence, and the first
sentence of the table caption. The route passes the scope to the template as
`history_scope`, and the template no longer reads `site_name`.

## Technical context

- Python 3.13, Flask, and Jinja. No new dependency.
- No route change, no schema change, and no change to a JSON body.
- No new cloud read, no new store read, and no new write.
- The unit tests read the class and render the real template with no Flask
  application.
- The contract tests drive the real history route with a capture list of two
  sites.
- The browser journey drives the real history page of the browser test server.

## Constitution check

| Principle | Result |
| - | - |
| I. Five-item rule | Pass. The class holds two fields, one class method, and three properties. Each member holds fewer than 25 lines. |
| II. Class-based design | Pass. The rule lives in one class. No function wraps another function. |
| III. Safety first | Pass. The change adds no write, and the page keeps its controls. |
| IV. Full pipeline | Pass. Tests, gates, a pull request, a hand merge, and a class B deploy. |
| V. Observability | Pass. The class method logs before and after it reads the site name. |
| VI. Inline comments | Pass. Each new line carries a comment. A Jinja comment explains the scope texts. |
| VII. Action logging | Pass. The only new action is the read of the site name, and it logs. |

`MistHelper.py` does not change.

## Files

| File | Change |
| - | - |
| `src/interfaces/portals/upgrade_portal/app/routes/review.py` | The new class `HistoryScope`. The route passes `history_scope` in place of `site_name`. The docstring of `read_site_name` states the new call. |
| `src/interfaces/portals/upgrade_portal/app/assets/templates/review/history.html` | The note and the caption print the three scope texts. The variable list names `history_scope`. |
| `tests/unit/upgrade_portal/test_issue_3482_history_scope.py` | New. The texts of each scope, and the render of the note and the caption. |
| `tests/unit/upgrade_portal/test_issue_3449_count_nouns.py` | The render of one site passes a scope in place of `site_name`. |
| `tests/unit/upgrade_portal/test_history_view.py` | The render passes a scope in place of `site_name`. |
| `tests/e2e/upgrade_portal/test_history_layout.py` | The render passes a scope in place of `site_name`. |
| `tests/contract/upgrade_portal/test_history_routes.py` | The note and the caption of the page with no site over two sites. The note of one site. |
| `tests/e2e/upgrade_portal/test_history_scope_journey.py` | New. The browser journeys, with a screenshot of each page. |
| `changelog.d/issue-3482-org-history-scope.md` | New. The release note. |

## Test plan

1. Write the new tests first. Run them on the old code, and record the red
   result.
2. Change the code and the template. Run the tests green.
3. Read each screenshot of the browser journey.
4. Run the unit suite and the contract suite of the portal, the integration
   suite, and the guardrails. Also run each browser file that opens the
   history page.

## Gates

py_compile, ruff, black, mypy (the `MYPY_PATHS` of `ci.yml`), bandit,
vulture, interrogate, radon, pydocstyle, pylint, and the test quality gate.
Also run the STE lint of each new Markdown file.

## Deploy

Class B deploy to port 8056 after the merge. Copy `app/routes/review.py` and
`review/history.html` from the squash commit. Then send HUP to the 8056 master
only. The new workers then load the Python module and the template again.
