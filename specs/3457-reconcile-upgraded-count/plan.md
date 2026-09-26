# Implementation Plan: A child job that the check proves counts its devices as upgraded

**Issue**: #3457 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

The function that builds the child counts reads only the stored cloud answer.
A child job that the check proves holds an empty cloud answer, so its counts
stay 0. The device reader of the child job gets two methods. One method
reports whether the check proved the child job. The other method returns the
upgraded count and the failed count of a proven child job. The count function
uses these methods for a proven child job only.

## Technical context

- Python 3.13, Flask, and Jinja. No new dependency.
- No route change, no schema change, and no change to the stored record.
- No new cloud read and no new write.
- The unit tests read the device reader and the summary with no Flask
  application.
- The contract tests drive the real check route, the real progress page, and
  the real status route.
- The browser journey drives the real check from the progress page.

## Constitution check

| Principle | Result |
| - | - |
| I. Five-item rule | Pass. Each new method holds three statements or fewer. The count function stays below 25 lines. |
| II. Class-based design | Pass. The rule lives in the existing device reader class. |
| III. Safety first | Pass. The change adds no write, and the stored proof does not change. |
| IV. Full pipeline | Pass. Tests, gates, a pull request, a hand merge, and a class B deploy. |
| V. Observability | Pass. A debug record names each proven child job and its counts. |
| VI. Inline comments | Pass. Each new line carries a comment. |
| VII. Action logging | Pass. The change adds no action. The debug record states the result. |

`MistHelper.py` does not change.

## Files

| File | Change |
| - | - |
| `src/upgrade_portal/upgrade/org_devices.py` | The methods `is_proven` and `proven_counts` of `OrgChildDevices`. |
| `src/upgrade_portal/app/routes/org_upgrade.py` | `_aggregate_child_counts` returns the proven counts for a proven child job. |
| `tests/unit/upgrade_portal/test_issue_3457_reconcile_upgraded_count.py` | New. The proof rule, the counts, and the summary. |
| `tests/contract/upgrade_portal/test_org_child_controls_routes.py` | The counts of the page and the status answer after each check. |
| `tests/e2e/upgrade_portal/test_org_recovery_controls.py` | The child rows and the operation block after the check. |
| `changelog.d/issue-3457-reconcile-upgraded-count.md` | New. The release note. |

## Test plan

1. Write the new tests first. Run them on the old code, and record the red
   result.
2. Change the code. Run the tests green.
3. Read the screenshot `reconcile-after.png` of the browser journey.
4. Run the upgrade-portal contract suite and unit suite, the integration
   suite, and the guardrails. Also run each browser file of the multi-site
   progress page.

## Gates

py_compile, ruff, black, mypy (the `MYPY_PATHS` of `ci.yml`), bandit,
vulture, interrogate, radon, and the test quality gate. Also run the STE lint
of each new Markdown file.

## Deploy

Class B deploy to port 8056 after the merge: `org_devices.py` and
`org_upgrade.py` from the squash commit. Then send HUP to the 8056 master
only. The new workers then load the two modules again.
