# Implementation Plan: Each isolation check of the browser test portal can fail

**Issue**: #3501 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

The change removes eight configuration values that no portal code reads. It
also removes the seven response headers that can only hold the text "0",
and the checks that read them. One new support class, `RunOwnerHeaderCheck`,
checks the run owner header, and direct tests prove each failure case.

Two new direct tests fail on the code of today. A contract test requires one
test header on a response of the test application. A unit test requires the
exact set of kept configuration keys.

## Technical context

- Python 3.13, pytest, Flask, and Playwright. No new dependency.
- No route change, no schema change, and no change to a JSON body.
- The production portal builds no test value. The two files under `src/`
  change only in their test values and in the test branch of the factory.
- The direct tests run with no browser and no network. The contract test
  uses the Flask test client.
- The browser suite runs in Microsoft Edge on this computer. The CI job "E2E
  smoke tests" runs it in Chromium.

## Constitution check

| Principle | Result |
| - | - |
| I. Five-item rule | Pass. The new class holds five members. Each method takes two parameters or fewer and holds fewer than 25 lines. The support package keeps five children, because `owner.py` replaces the `traps` package. |
| II. Class-based design | Pass. One class owns the owner check. The fixtures call it, and no function wraps it. |
| III. Safety first | Pass. The owner check still refuses a portal of another run. The validation of the dependency set still fails closed. |
| IV. Full pipeline | Pass. Tests, gates, a pull request, a hand merge, and a copy of two files into the container of port 8056. |
| V. Observability | Pass. The owner check logs before and after each check. The failure message names the header and both values. |
| VI. Inline comments | Pass. Each new line carries a comment. |
| VII. Action logging | Pass. Each new action logs before and after. |

`MistHelper.py` does not change.

## Files

| File | Change |
| - | - |
| `src/interfaces/portals/upgrade_portal/api/run_controls/models.py` | Remove seven fields, eight keys, and `trap_call_counts`. |
| `src/interfaces/portals/upgrade_portal/app/factory.py` | Write the run owner header only. |
| `tests/support/upgrade_portal_e2e/owner.py` | New. The class `RunOwnerHeaderCheck`. |
| `tests/support/upgrade_portal_e2e/__init__.py` | Build the smaller groups. Export the owner check. Stop the export of the traps and of the audit record store. |
| `tests/support/upgrade_portal_e2e/traps/` | Delete the package and its five files. |
| `tests/support/upgrade_portal_e2e/records/audit.py` | Remove the class `AuditRecordStore`. |
| `tests/support/upgrade_portal_e2e/records/__init__.py` | Stop the export of the audit record store. |
| `tests/e2e/upgrade_portal/conftest.py` | Use the owner check. Remove the header constants and the fixed session guard. |
| `tests/e2e/upgrade_portal/test_run_controls/test_isolation.py` | Require one test header. Remove the trap headers from the route answer. Repair five accepted ratchet findings. |
| `tests/contract/upgrade_portal/test_upgrade_routes/test_isolation.py` | Build the smaller groups. Add the one-header test. Name a kept field in the fail-closed test. |
| `tests/unit/upgrade_portal/test_runs/test_isolation.py` | Build the smaller groups. Remove the trap test. Add the kept-key test. Name a kept field in the fail-closed test. |
| `tests/unit/upgrade_portal/test_e2e_run_owner_header.py` | New. The direct cases of the owner check. |
| `.github/test-quality-baseline.json` | Remove the five accepted findings that the rewrite of the browser isolation module repairs. |
| `specs/2448-misthelper-performance-monitoring/artifacts/python-inventory.csv` | Remove the five rows of the deleted `traps` files. The catalog guard refuses a row that names no file. |
| `specs/2448-misthelper-performance-monitoring/artifacts/scan-summary.json` and `hook-catalog-summary.json` | Lower the file, symbol, disposition, and root counts by the values of the five removed rows. |

## Test plan

1. Write the new direct tests first. Run them on the code of today, and
   record the red result.
2. Change the two files under `src/` and the support package. Update the
   three isolation test modules and the conftest.
3. Run the direct tests, the contract tests, and the isolation browser tests
   green.
4. Run every test under `tests/e2e/upgrade_portal/`. Explain or fix each
   changed result. Run `tests/unit/upgrade_portal`,
   `tests/contract/upgrade_portal`, and `tests/guardrails`.
5. Search `src/`, `tests/`, and `wsgi_capture.py` for each removed name.

## Gates

py_compile, ruff, black, mypy (the `MYPY_PATHS` of `ci.yml`), the test
quality gate of each changed test file, and the STE lint of each new
Markdown file.

## Release note

An operator sees no change, so the change adds no fragment under
`changelog.d/`. The pull request body states this reason.

## Overlap

The draft pull request #3264 also changes `tests/e2e/upgrade_portal/conftest.py`.
This change takes the file first. Pull request #3264 rebases after this merge.

## Deploy

After the merge, copy the two files under `src/` into the container of port
8056. Confirm that no upgrade run is active. Send the hang-up signal to the
Gunicorn master of that portal only. Then compare the SHA-256 value of each
file with `main`, and read `/healthz`.