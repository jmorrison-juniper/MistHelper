# Implementation Plan: The site picker and the reconciliation read name a lost page

**Issue**: #3438 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

The picker read walks each page with `read_every_page`, and it names a fault
of the first page with `guard_page_count`. The read returns a `DeviceRead`,
and the cache keeps a whole read only. `build_site_rows` returns a new
`SiteList` with one flag for each read. The site picker shows a Caution note
for each flag, in both modes. The site list answer adds the two flags.

The reconciliation reader walks each page of the statistics read. Each target
with no fresh row after a lost page holds unavailable evidence, so the service
reports `cloud_evidence_unavailable`.

## Technical context

- Python 3.13, Flask, and Jinja with the strict undefined type. No new
  dependency.
- No schema change. No change to the stored plan or to the run record.
- No new cloud call. A whole read makes one call for each page, as before.
- The browser harness answers reconciliation through a scripted seam. Unit
  tests and one full-path service test cover the reader.

## Constitution check

| Principle | Result |
| - | - |
| I. Five-item rule | Pass. Each new function holds fewer than 25 lines and fewer than 5 parameters. |
| II. Class-based design | Pass. `SiteList` is a frozen class. No wrapper and no compatibility shim. |
| III. Safety first | Pass. The change adds no write. The reconciliation change marks more targets unavailable, which blocks a false success. |
| IV. Full pipeline | Pass. Tests, gates, a pull request, a hand merge, and a class B deploy. |
| V. Observability | Pass. Each lost read writes one warning with the read name and the reason code. |
| VI. Inline comments | Pass. Each touched line carries a comment. |
| VII. Action logging | Pass. Each new read logs before and after the action. |

`MistHelper.py` does not change.

## Files

| File | Change |
| - | - |
| `src/upgrade_portal/app/routes/select.py` | `collect_pages` walks each page and returns a `DeviceRead`. `default_cloud_read` returns a `DeviceRead` and keeps a whole read only. New `SiteList`. `build_site_rows` returns a `SiteList`. `sites_page`, `site_choice_refusal`, and `list_sites` read the new type. |
| `src/upgrade_portal/app/routes/org_upgrade.py` | `selected_rows` and `_site_labels` read `SiteList.rows`. |
| `src/upgrade_portal/app/assets/templates/select/sites.html` | The two Caution notes. |
| `src/upgrade_portal/api/run_controls/routes.py` | The reader walks each page. Each target of a lost page holds unavailable evidence. New `_target_id` helper. |
| `specs/1823-upgrade-capture-portal/contracts/http-api.md` | The two new fields of the site list answer. |
| `tests/unit/upgrade_portal/test_issue_3438_picker_pages.py` | New. The page walk, the cache rule, the flags, the notes, and the answer fields. |
| `tests/unit/upgrade_portal/test_issue_3438_reconcile_pages.py` | New. The reader walk with real SDK answers, and one full-path service test. |
| `tests/unit/upgrade_portal/test_org_picker.py` | Remove the two floor tests. The new picker test file replaces them. |
| `tests/unit/upgrade_portal/test_cloud_cache.py` | The `collect_pages` stand-in returns a `DeviceRead`. |
| `tests/unit/upgrade_portal/test_site_stats_evidence_reader.py` | A real SDK answer replaces the `get_all` stand-in. |
| `tests/e2e/upgrade_portal/lost_page_seeds.py` | New. The lost-page organization and its operator. |
| `tests/e2e/upgrade_portal/conftest.py` | The lost-page session, the real read for that organization, the operator, and the page fixture. |
| `tests/e2e/upgrade_portal/test_lost_site_page.py` | New. The notes in a real browser, in each mode. |
| `changelog.d/issue-3438-picker-reconcile-pages.md` | New. The release note. |

## Design artifacts

- [data-model.md](data-model.md) holds the three types of this change.
- [quickstart.md](quickstart.md) holds the validation steps.
- The contract change goes into the shared portal contract,
  `specs/1823-upgrade-capture-portal/contracts/http-api.md`. This feature adds
  no second copy of that contract.

## Test plan

1. Write the unit tests first. Run them on the old code, and record the red
   result.
2. Add the code change. Run the tests green.
3. Add the browser journeys. Read each screenshot.
4. Run the upgrade-portal unit suite, contract suite, integration suite, and
   browser suite.

## Gates

py_compile, ruff, black, mypy (the `MYPY_PATHS` of `ci.yml`), pylint,
pydocstyle, interrogate, bandit, radon, vulture, the test quality gate, and
the STE lint of each new Markdown file.

## Deploy

Class B deploy to port 8056 after the merge: the three source files and the
template, from the squash commit. Then HUP the 8056 master only.
