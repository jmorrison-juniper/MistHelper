# Implementation Plan: The multi-site texts name one site with a singular noun

**Issue**: #3462 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

Four Python texts and one template banner put a fixed plural noun before a
list of site names. The class `OrgSiteRefusal` gets one static method that
returns the place words for a count. The three save refusals and the start
refusal format those words. The banner template sets one Boolean value from
the count of the short sites, as the fixes of #3447 and #3452 do.

## Technical context

- Python 3.13, Flask, and Jinja. No new dependency.
- No route change, no schema change, and no change to the stored plan.
- No new cloud read and no new write.
- The unit tests read the refusal class with no Flask application.
- The contract tests drive the real options page, the real save, and the
  real start route. The browser journeys drive the real options page.

## Constitution check

| Principle | Result |
| - | - |
| I. Five-item rule | Pass. The new method holds one statement. Each new test holds fewer than 25 lines. |
| II. Class-based design | Pass. The rule is a static method of the existing refusal class. |
| III. Safety first | Pass. The refusals keep their codes, their status codes, and their order. The change adds no write. |
| IV. Full pipeline | Pass. Tests, gates, a pull request, a hand merge, and a class B deploy. |
| V. Observability | Pass. The existing refusal logs do not change. |
| VI. Inline comments | Pass. Each new line carries a comment. A Jinja comment explains the rule. |
| VII. Action logging | Pass. The change adds no action. |

`MistHelper.py` does not change.

## Files

| File | Change |
| - | - |
| `src/interfaces/portals/upgrade_portal/upgrade/org_site_records.py` | The place words, the method `place_text`, and the three save refusals. |
| `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` | The second sentence of the start refusal, and the import of `OrgSiteRefusal`. |
| `src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_options.html` | The Boolean value and the two nouns of the banner. |
| `tests/unit/upgrade_portal/test_issue_3462_site_list_noun.py` | New. The place words and the whole texts for one, two, and twelve sites. |
| `tests/unit/upgrade_portal/test_org_site_records.py` | The texts of one site. |
| `tests/contract/upgrade_portal/test_org_site_records_routes.py` | The texts of one site, and new tests of the banner and the save. |
| `tests/contract/upgrade_portal/test_org_precheck_routes.py` | The start refusal of one site, and a new test of two sites. |
| `tests/contract/upgrade_portal/test_org_child_controls_routes.py` | The texts of one site. |
| `tests/e2e/upgrade_portal/test_short_inventory_read.py` | The refusal of one site and the whole banner. |
| `tests/e2e/upgrade_portal/test_org_empty_site.py` | The refusal of one site. |
| `changelog.d/issue-3462-site-list-noun.md` | New. The release note. |

## Test plan

1. Write the new tests, and change the old tests first. Run them on the old
   code, and record the red result.
2. Change the code and the template. Run the tests green.
3. Read each screenshot of the browser journeys.
4. Run the upgrade-portal contract suite and unit suite, the integration
   suite, and the guardrails. Also run each browser file that opens the
   multi-site options page.

## Gates

py_compile, ruff, black, mypy (the `MYPY_PATHS` of `ci.yml`), bandit,
vulture, interrogate, radon, and the test quality gate. Also run the STE lint
of each new Markdown file.

## Deploy

Class B deploy to port 8056 after the merge: `org_site_records.py`,
`org_upgrade.py`, and `org_options.html` from the squash commit. Then send HUP
to the 8056 master only. The new workers then load the Python modules and the
template again.
