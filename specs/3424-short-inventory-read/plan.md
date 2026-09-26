# Implementation Plan: A short inventory read never looks complete

**Issue**: #3424 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

Carry the partial reasons of the inventory read to the options pages and to
the save. Each options page shows a Caution banner when a view holds a
reason. The single-site save raises a new refusal on a short read. The
multi-site save names each short site with the #3389 refusal class. The
empty-read rule of #3389 does not change.

The code review added a page walk. `read_every_page` checks the status and the
body of each later page, so a lost later page becomes a named reason (D8). The
row copy runs inside the guarded block (D9).

## Technical context

- Python 3.13, Flask, and Jinja with the strict undefined type. No new
  dependency.
- No schema change and no change to the stored plan or the run record.
- No new cloud call. A short read at the save skips the version read.
- `contracts/http-api.md` needs no change, because the single-site refusal
  keeps the code `bad_option`.

## Files

| File | Change |
| - | - |
| `src/upgrade_portal/upgrade/options.py` | `InventoryRead.is_short`. `PartialInventoryError` and `ERROR_PARTIAL_INVENTORY`. The view reports `partial_reasons`. The record refuses a short read. `_read_paged` uses the page walk and copies the rows inside the guarded block. |
| `src/upgrade_portal/capture/devices.py` | New `read_every_page` and `_page_records`. The walk names a lost later page with the reason `page_count_mismatch`. |
| `src/upgrade_portal/upgrade/org_site_records.py` | `SHORT_MESSAGE`. `OrgSiteRecords` collects each short site and refuses in the order of D6. |
| `src/upgrade_portal/app/routes/upgrade.py` | `options_view` and `options_page` pass `partial_reasons` to the page. |
| `src/upgrade_portal/app/routes/org_upgrade.py` | `_site_view_gap` finds an empty view or a short view. `_site_option_record` turns a short read into the short marker. `options_page` names each short site. |
| `src/upgrade_portal/app/assets/templates/upgrade/options.html` | The single-site banner. |
| `src/upgrade_portal/app/assets/templates/upgrade/org_options.html` | The multi-site banner. |
| `tests/unit/upgrade_portal/test_upgrade_options.py` | The short read of the view and of the record. A lost later page with a real SDK answer. |
| `tests/unit/upgrade_portal/test_capture_devices.py` | The page walk with a real SDK answer. |
| `tests/support/sdk_pages.py` | New. A real SDK answer with page headers, and a session that answers the planned later pages. |
| `tests/unit/upgrade_portal/test_org_site_records.py` | The short site, the refusal order, and a retry. |
| `tests/contract/upgrade_portal/test_upgrade_options.py` | The single-site banner and refusal through the Flask routes. |
| `tests/contract/upgrade_portal/test_org_site_records_routes.py` | The multi-site banner and refusal through the Flask routes. |
| `tests/contract/upgrade_portal/test_org_child_controls_routes.py` | A retry save refuses a site whose view read was short. |
| `tests/e2e/upgrade_portal/short_read_seeds.py` | New. The short site and its operator. |
| `tests/e2e/upgrade_portal/conftest.py` | The short site, its stand-in reads, its operator, and its page fixture. |
| `tests/e2e/upgrade_portal/test_short_inventory_read.py` | New. The banner, the refusal, and the recovery in a real browser, in each mode. |
| `changelog.d/issue-3424-short-inventory-read.md` | New. The release note. |

## Test plan

1. Write the unit tests and the contract tests first. Run them on the old
   code, and record the red result.
2. Add the code change. Run the tests green.
3. Add the browser journeys. Read each screenshot.
4. Run the upgrade-portal unit suite, contract suite, and browser suite.

## Gates

py_compile, ruff, black, mypy (the `MYPY_PATHS` of `ci.yml`), pylint,
pydocstyle, interrogate, bandit, radon, vulture, the test quality gate, and
the STE lint of each new Markdown file.

## Deploy

Class B deploy to port 8056 after the merge: the five source files and the
two templates, from the squash commit. Then HUP the 8056 master only.
