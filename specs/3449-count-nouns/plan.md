# Implementation Plan: The picker note and the history note make the noun agree with the count

**Issue**: #3449 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

The picker note and the history note print each count beside a fixed plural
noun. Each view model gets three text properties: `total_text`, `offset_text`,
and `page_size_text`. The new mixin `HistoryNoteText` gives the three
properties to the two history views. The picker view holds its own copy. Each
template prints the three texts, and each note gets a test identifier.

## Technical context

- Python 3.13, Flask, and Jinja. No new dependency.
- No route change, no schema change, and no change to a JSON body.
- No new cloud read and no new write.
- The unit tests read the view models and render the real templates with no
  Flask application.
- The contract tests drive the real picker route and the real history route.
- The browser journey drives the real pages of the browser test server.

## Constitution check

| Principle | Result |
| - | - |
| I. Five-item rule | Pass. Each new property holds one statement. Each new test holds fewer than 25 lines. |
| II. Class-based design | Pass. The rule lives in a mixin and in the picker view. No function wraps another function. |
| III. Safety first | Pass. The change adds no write, and the pages keep their controls. |
| IV. Full pipeline | Pass. Tests, gates, a pull request, a hand merge, and a class B deploy. |
| V. Observability | Pass. The existing route logs do not change. |
| VI. Inline comments | Pass. Each new line carries a comment. A Jinja comment explains each note. |
| VII. Action logging | Pass. The change adds no action. |

`MistHelper.py` does not change.

## Files

| File | Change |
| - | - |
| `src/interfaces/portals/upgrade_portal/compare/render.py` | The new mixin `HistoryNoteText`. `HistoryView` inherits it, and `__all__` names it. |
| `src/interfaces/portals/upgrade_portal/app/routes/review.py` | `HistoryPageView` inherits the mixin. |
| `src/interfaces/portals/upgrade_portal/app/routes/select.py` | `OrgPickerView` gets the three properties and a static rule. |
| `src/interfaces/portals/upgrade_portal/app/assets/templates/select/orgs.html` | The note prints the three texts and gets its test identifier. |
| `src/interfaces/portals/upgrade_portal/app/assets/templates/review/history.html` | The note prints the three texts and gets its test identifier. |
| `specs/1823-upgrade-capture-portal/contracts/ui-testids.md` | The two new identifiers. |
| `tests/unit/upgrade_portal/test_issue_3449_count_nouns.py` | New. The texts of each view, and the render of each note. |
| `tests/contract/upgrade_portal/test_select.py` | The picker note for 0, 1, and 2 matches, and for an offset of 1. |
| `tests/contract/upgrade_portal/test_history_routes.py` | The history note for 0, 1, and 2 captures, and for a page size of 1. |
| `tests/e2e/upgrade_portal/test_count_nouns_journey.py` | New. The browser journeys, with a screenshot of each note. |
| `changelog.d/issue-3449-count-nouns.md` | New. The release note. |

## Test plan

1. Write the new tests first. Run them on the old code, and record the red
   result.
2. Change the code and the templates. Run the tests green.
3. Read each screenshot of the browser journey.
4. Run the unit suite and the contract suite of the portal, the integration
   suite, and the guardrails. Also run each browser file that opens the picker
   or the history page.

## Gates

py_compile, ruff, black, mypy (the `MYPY_PATHS` of `ci.yml`), bandit,
vulture, interrogate, radon, pydocstyle, and the test quality gate. Also run
the STE lint of each new Markdown file.

## Deploy

Class B deploy to port 8056 after the merge. Copy `compare/render.py`,
`app/routes/review.py`, `app/routes/select.py`, `select/orgs.html`, and
`review/history.html` from the squash commit. Then send HUP to the 8056 master
only. The new workers then load the Python modules and the templates again.
