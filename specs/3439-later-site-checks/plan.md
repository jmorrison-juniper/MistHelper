# Implementation Plan: A later site check names an incomplete site list

**Issue**: #3439 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

Each later site check reads the site list again. A read that lost a page can
leave out a site that exists. The check then refuses that site as unknown.

The change adds the class `SiteListIncompleteError`. A check raises this error
when a named site is not in a site list that lost a page. An error handler of
the application answers the error with the status 503 and the code
`site_list_incomplete`. A browser page receives the shared error page. A script
receives the error envelope.

The site choice post of the multi-site picker does not raise. It returns the
503 envelope to `PickerRefusal`, so a browser returns to the site picker with a
Caution message.

If the site list is whole, each check keeps the answer of today.

## Technical context

- Python 3.13, Flask, and Jinja. No new dependency.
- No schema change. No change to the stored plan, the saved options, or the
  run record.
- No new cloud call. Each check makes the same reads as before.

In the browser tests, one request header asks for a lost page. Only the
stand-in reader for the organization of this test reads that header. That
reader then loses page two of the site read. The portal code does not read the
header.

## Constitution check

| Principle | Result |
| - | - |
| I. Five-item rule | Pass. Each new function holds fewer than 25 lines and fewer than 5 parameters. `SiteList` holds five members. |
| II. Class-based design | Pass. The error class owns its raise rule. No wrapper and no compatibility shim. |
| III. Safety first | Pass. A refused check writes nothing. It starts no capture and takes no site lock. |
| IV. Full pipeline | Pass. Tests, gates, a pull request, a hand merge, and a class B deploy. |
| V. Observability | Pass. Each refusal writes one warning with the count of missing sites. |
| VI. Inline comments | Pass. Each touched line carries a comment. |
| VII. Action logging | Pass. Each new check logs before and after the action. |

The file `MistHelper.py` does not change.

## Files

| File | Change |
| - | - |
| `src/upgrade_portal/app/routes/select.py` | Three new constants, `SiteListIncompleteError`, `SiteList.missing_sites`, and the error handler. `find_site` raises the error. The new `site_set_refusal` holds the site check of `site_choice_refusal`. |
| `src/upgrade_portal/app/routes/org_upgrade.py` | `selected_rows` raises the error for a site list that lost a page. |
| `src/upgrade_portal/app/assets/templates/error.html` | The template comment names the status 503 in the list of status codes. |
| `specs/1823-upgrade-capture-portal/contracts/http-api.md` | The 503 answer of the inventory page, the inventory answer, and the capture start. |
| `specs/1823-upgrade-capture-portal/contracts/README.md` | A 503 row in the status code table. |
| `tests/unit/upgrade_portal/test_issue_3439_site_checks.py` | New. The missing-site rule, the raise rule, `find_site`, `site_set_refusal`, and `selected_rows`. |
| `tests/contract/upgrade_portal/test_issue_3439_later_site_checks.py` | New. Each of the nine steps, the kept-page pass, the whole-list answers, and the no-change checks. |
| `tests/e2e/upgrade_portal/later_check_seeds.py` | New. The organization, the operator, the three sites, and the settled operation of the retry journey. |
| `tests/e2e/upgrade_portal/conftest.py` | The later-check session, the header rule of the stand-in reader, the device series of the three sites, the operator, the retry seed, and the page fixture. |
| `tests/e2e/upgrade_portal/test_later_site_checks.py` | New. The journeys in a real browser, in each mode. |
| `changelog.d/issue-3439-later-site-checks.md` | New. The release note. |

The files `capture.py`, `org_precheck.py`, `org_controls.py`, and `upgrade.py`
do not change. They reach the new rule through `find_site` and
`selected_rows`.

## Design artifacts

- The file [research.md](research.md) holds the measured facts and the
  decisions.
- The file [data-model.md](data-model.md) holds the changed type, the new error
  type, and the error answer.
- The file [quickstart.md](quickstart.md) holds the validation steps.
- The contract change goes into the shared portal contract,
  `specs/1823-upgrade-capture-portal/contracts/`. The multi-site endpoints have
  no contract file, so the file [spec.md](spec.md) states their answers.

## Test plan

1. Write the unit tests and the contract tests first. Run them on the old code,
   and record the red result.
2. Add the code change. Run the tests again, and record the green result.
3. Add the browser journeys. Read each screenshot.
4. Run the unit suite, the contract suite, the integration suite, and the
   browser suite of the upgrade portal.
5. Count the cloud reads of each step before and after the change (SC-005).

## Gates

Run py_compile, ruff, black, mypy (the `MYPY_PATHS` of `ci.yml`), pylint,
pydocstyle, interrogate, bandit, radon, vulture, and the test quality gate.
Run the STE lint on each new Markdown file.

## Deploy

After the merge, do a class B deploy to port 8056. Copy `select.py`,
`org_upgrade.py`, and `error.html` from the squash commit. Then send HUP to
the 8056 master only.