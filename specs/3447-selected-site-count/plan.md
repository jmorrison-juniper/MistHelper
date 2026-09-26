# Implementation Plan: The multi-site options page states the correct site noun

**Issue**: #3447 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

The note of the multi-site options page prints the count of the selected
sites and the fixed word "sites". The template sets the count and the noun
with two `set` statements. The noun is "site" for the count 1 and "sites" for
each other count. The paragraph gets the test identifier
`org-upgrade-site-count`.

## Technical context

- Python 3.13, Flask, and Jinja with the strict undefined type. No new
  dependency.
- No schema change, no route change, and no change to the stored plan.
- No new cloud call and no new page load.
- The contract tests drive the real options route with stand-in cloud reads.
  One browser journey drives the real site picker and the real options page.

## Constitution check

| Principle | Result |
| - | - |
| I. Five-item rule | Pass. The change adds two template statements. Each new test function holds fewer than 25 lines. |
| II. Class-based design | Pass. The change adds no Python source. No wrapper and no compatibility shim. |
| III. Safety first | Pass. The change adds no write. The note states the scope of the plan correctly. |
| IV. Full pipeline | Pass. Tests, gates, a pull request, a hand merge, and a class B deploy. |
| V. Observability | Pass. The route logs do not change. The template adds no action. |
| VI. Inline comments | Pass. Each new test line carries a comment. The template holds a Jinja comment that names the issue. |
| VII. Action logging | Pass. The change adds no action. The test helpers read the page only. |

`MistHelper.py` does not change.

## Files

| File | Change |
| - | - |
| `src/upgrade_portal/app/assets/templates/upgrade/org_options.html` | Two `set` statements for the count and the noun. The note prints both. The paragraph gets the test identifier. |
| `tests/contract/upgrade_portal/test_issue_3447_selected_site_count.py` | New. One site, two sites, a retry of one site, the end of that retry, and a retry of two sites. |
| `tests/e2e/upgrade_portal/test_selected_site_count.py` | New. The note in a real browser for one site and for two sites, with one screenshot each. |
| `changelog.d/issue-3447-selected-site-count.md` | New. The release note. |

## Test plan

1. Write the contract tests and the browser journey first. Run them on the
   old template, and record the red result.
2. Change the template. Run the tests green.
3. Read each screenshot of the journey.
4. Run the upgrade-portal unit suite, contract suite, integration suite, and
   the browser files that read the options page.

## Gates

py_compile, ruff, black, mypy (the `MYPY_PATHS` of `ci.yml`), pylint,
pydocstyle, interrogate, bandit, radon, vulture, and the test quality gate.
Also run the Markdown link guardrail and the STE lint of each new Markdown
file.

## Deploy

Class B deploy to port 8056 after the merge: the template only, from the
squash commit. Then send HUP to the 8056 master only.
