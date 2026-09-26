# Implementation Plan: An empty site never replaces the choices of the operator

**Issue**: #3389 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

Collect the record of each selected site in a new class. Keep the options of
each site that answers. Stop the save when a site answers an empty record, or
when a site holds no planned device while another site holds one. Name each
such site in the message. A retry of issue #3247 skips the second refusal. A
site whose device view holds no device answers an empty record, so a failed
view read stops a retry save too.

## Technical context

- Python 3.13, Flask, and the shipped option mapper. No new dependency.
- No schema change and no change to the stored plan.
- The single-site save does not change.

## Files

| File | Change |
| - | - |
| `src/upgrade_portal/upgrade/org_site_records.py` | New. `OrgSiteRecords` and `OrgSiteRefusal`. |
| `src/upgrade_portal/app/routes/org_upgrade.py` | `_aggregate_option_record` uses the class. `_site_labels` reads the names. `_site_option_record` returns the empty record for an empty view. |
| `tests/unit/upgrade_portal/test_org_site_records.py` | New. The rules of the class and the name cap. |
| `tests/contract/upgrade_portal/test_org_site_records_routes.py` | New. The save route with real Flask and the shipped build. A failed view read. |
| `tests/e2e/upgrade_portal/empty_site_seeds.py` | New. The empty site and its operator. |
| `tests/e2e/upgrade_portal/conftest.py` | The empty site, its operator, and its page fixture. |
| `tests/e2e/upgrade_portal/test_org_empty_site.py` | New. The refusal and the recovery in a real browser. |
| `tests/contract/upgrade_portal/test_org_child_controls_routes.py` | Two retry saves that the second refusal must not stop. A retry save with a failed view read. |
| `tests/e2e/upgrade_portal/test_org_recovery_controls.py` | A retry with one cleared type in a real browser. |
| `changelog.d/issue-3389-empty-last-site-options.md` | New. The release note. |

## Test plan

1. Write the unit tests and the contract tests first. Run them on the old code,
   and record the red result.
2. Add the class and the route change. Run the tests green.
3. Add the browser journey. Read each screenshot.
4. Run the portal suites and the browser suite of the upgrade portal.

## Gates

py_compile, ruff, black, mypy, pylint, pydocstyle, interrogate, bandit, radon,
vulture, the test quality gate, and the STE lint.
