# Implementation Plan: The multi-site confirm page names one site for a plan of one site

**Issue**: #3452 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

The template `upgrade/org_confirm.html` states the scope of the upgrade in the
Warning and in two pre-check buttons. Each text uses a fixed plural form. The
template now sets one Boolean value from the count of the saved sites. For one
site, each text names one site. For two or more sites, each text keeps a
plural scope.

## Technical context

- Python 3.13, Flask, and Jinja. No new dependency.
- No route change, no schema change, and no change to the stored plan.
- No new cloud read and no new write.
- The contract tests drive the real options save and the real confirm route.
  The browser journeys drive the real site picker and the real confirm page.

## Constitution check

| Principle | Result |
| - | - |
| I. Five-item rule | Pass. Each new test holds fewer than 25 lines. |
| II. Class-based design | Pass. No Python code changes in `src/`. |
| III. Safety first | Pass. The Warning keeps its signal word and its second sentence. The change adds no write. |
| IV. Full pipeline | Pass. Tests, gates, a pull request, a hand merge, and a class B deploy. |
| V. Observability | Pass. No log changes. |
| VI. Inline comments | Pass. Each new test line carries a comment. A Jinja comment explains the rule. |
| VII. Action logging | Pass. The template adds no action. |

`MistHelper.py` does not change.

## Files

| File | Change |
| - | - |
| `src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_confirm.html` | The Boolean value, the three texts, and the test identifier of the Warning. |
| `tests/contract/upgrade_portal/test_issue_3452_confirm_scope_text.py` | New. The whole texts for one site, two sites, and a retry of one site. |
| `tests/e2e/upgrade_portal/test_selected_site_count.py` | The one-site journey reads the new texts. The two-site journey continues to the confirm page. |
| `changelog.d/issue-3452-confirm-scope-text.md` | New. The release note. |

## Test plan

1. Write the contract tests, and change the browser journeys first. Run them
   on the old template, and record the red result.
2. Change the template. Run the tests green.
3. Read each screenshot of the browser journeys.
4. Run the upgrade-portal contract suite and unit suite, the integration
   suite, and the guardrails. Also run each browser file that opens the
   confirm page.

## Gates

py_compile, ruff, black, mypy (the `MYPY_PATHS` of `ci.yml`), bandit,
vulture, interrogate, and the test quality gate. Also run the STE lint of
each new Markdown file.

## Deploy

Class B deploy to port 8056 after the merge: `org_confirm.html` only, from the
squash commit. Then send HUP to the 8056 master only, because the workers
keep the templates in a cache.