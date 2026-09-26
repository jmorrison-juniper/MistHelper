# Implementation Plan: The multi-site check result uses correct grammar for each count

**Issue**: #3453 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

The method `OrgReconcileCheck._summary` writes the result of each check of an
uncertain child job. Its first sentence and its unread sentence use the
fixed noun "devices". The first sentence becomes "The target version runs on
M of T devices". The unread sentence becomes "The portal could not read U of
T devices". A new static method returns "device" for the total 1 and
"devices" for each other total. The summary method becomes a class method,
so it can call the noun method.

## Technical context

- Python 3.13 and Flask. No new dependency.
- No schema change, no route change, and no change to the stored fields.
- No new cloud call and no new write.
- The unit tests drive the real check class with stored records. The
  contract test drives the real check route. The browser journey drives the
  real progress page.

## Constitution check

| Principle | Result |
| - | - |
| I. Five-item rule | Pass. The summary method keeps four decisions. The new method holds one line. Each new test holds fewer than 25 lines. |
| II. Class-based design | Pass. The new rule is a static method of the check class. No wrapper and no compatibility shim. |
| III. Safety first | Pass. The change adds no write. The proof rule does not change. |
| IV. Full pipeline | Pass. Tests, gates, a pull request, a hand merge, and a class B deploy. |
| V. Observability | Pass. The verdict logs do not change. |
| VI. Inline comments | Pass. Each changed line and each new test line carries a comment. |
| VII. Action logging | Pass. The summary method is a pure text rule, so it adds no action. |

`MistHelper.py` does not change.

## Files

| File | Change |
| - | - |
| `src/upgrade_portal/upgrade/org_reconcile.py` | The new first sentence, the new unread sentence, and the static noun method. |
| `tests/unit/upgrade_portal/test_issue_3453_reconcile_summary.py` | New. The whole text for a child job of one device and of three devices. |
| `tests/contract/upgrade_portal/test_org_child_controls_routes.py` | The stored text of a real check. |
| `tests/e2e/upgrade_portal/test_org_recovery_controls.py` | The page text of a real check. The run passes `--basetemp`, so a reviewer can read each screenshot. |
| `tests/unit/firmware/test_aggregate_child_controls.py` | The stand-in text only. |
| `tests/unit/upgrade_portal/test_org_child_controls.py` | The stand-in text only. |
| `changelog.d/issue-3453-reconcile-summary-grammar.md` | New. The release note. |

## Test plan

1. Write the unit tests, and change the contract and browser text first. Run
   them on the old code, and record the red result.
2. Change the check class. Run the tests green.
3. Read the screenshots of the browser journey.
4. Run the upgrade-portal unit suite, contract suite, and integration suite.
   Also run the firmware unit tests and the browser file of the recovery
   controls.

## Gates

py_compile, ruff, black, mypy (the `MYPY_PATHS` of `ci.yml`), pylint,
pydocstyle, interrogate, bandit, radon, vulture, and the test quality gate.
Also run the Markdown link guardrail and the STE lint of each new Markdown
file.

## Deploy

Class B deploy to port 8056 after the merge: `org_reconcile.py` only, from the
squash commit. Then send HUP to the 8056 master only, because the workers
import the module at the start.