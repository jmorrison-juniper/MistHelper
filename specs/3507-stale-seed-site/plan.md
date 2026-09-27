# Implementation Plan: The two stale seed runs move to a site of their own

**Issue**: #3507
**Branch**: `fix/3507-stale-seed-site`
**Spec**: [spec.md](./spec.md)
**Research**: [research.md](./research.md)

## Summary

Move the two stale seed runs off the first site, onto a site that only they use.
Put the stale seed in one module with the class `StaleRunSeeds`.
Change the fixture `scheduled_run_page`, so a missing schedule region fails instead of a skip.
Add a direct test that reads each seeded run and fails when a live seed run holds a listed site.

## Technical Context

- **Language**: Python 3.13
- **Test tools**: pytest, pytest-playwright, and Microsoft Edge through `--browser-channel msedge`
- **Scope**: Test code only. No portal code changes, so the change needs no deploy and no release note.
- **Performance goal**: The direct tests finish in less than 10 seconds, with the import of the browser conftest.

## Constitution Check

| Rule | Result |
| - | - |
| Class-based design, no wrappers | Pass. `StaleRunSeeds` holds the seed, with four methods. |
| Five-Item Rule | Pass. Each new function holds 5 parameters or fewer, and 25 lines or fewer. |
| Inline comments and action logging | Pass. Each new line carries a comment. The seed write logs before and after. |
| Safe > Fast | Pass. The change replaces a skip with a failure. |
| STE | Pass. Each Markdown file must score 80 or more with 0 errors. |

## Project Structure

```text
tests/e2e/upgrade_portal/
  stale_run_seeds.py                      NEW: the stale site, the two run keys, and StaleRunSeeds
  conftest.py                             CHANGED: calls StaleRunSeeds.write, drops the old records and keys
  test_run_controls/test_bulk.py          CHANGED: imports the keys, takes the lock of the stale site
  test_run_controls/test_existing.py      CHANGED: a missing schedule region fails and names the run
tests/unit/upgrade_portal/
  test_e2e_seed_run_sites.py              NEW: the seed-site guard and its decision tests
  test_e2e_stale_run_seeds.py             NEW: the direct tests of StaleRunSeeds
```

## Design

### The class `StaleRunSeeds`

| Method | Result |
| - | - |
| `pre_cloud_record(org_id)` | The run `e2e-stale-precloud-0001` in `awaiting_confirmation`, on the stale site. |
| `stopping_record(org_id)` | The run `e2e-stale-stopping-0001` in `stopping`, on the stale site. |
| `records(org_id)` | Both records, in write order. |
| `write(upgrade, org_id)` | Saves both records, and reports True only when the store accepts both. |

Each record keeps every field of the old record.
Each record adds `site_name`, because a real run stores the name of its site.

### The seed-site guard

The module `test_e2e_seed_run_sites.py` holds three parts.

1. A recording store and a stand-in application. The seed writer of the conftest saves each record into the store.
2. The function `live_runs_on_listed_sites(records, listed)`. It returns one line for each live run on a listed site.
3. Three tests. One test reads the real seed. Two tests prove the decision with synthetic lists.

### The fixture `scheduled_run_page`

The fixture reads the state that the page shows through the test identifier `upgrade-state`.
It raises `AssertionError` with the run key and that state.

## Test Strategy

| Step | Command | Expected result |
| - | - | - |
| Red, direct | `pytest tests/unit/upgrade_portal/test_e2e_seed_run_sites.py tests/unit/upgrade_portal/test_e2e_stale_run_seeds.py` | The guard names both stale seed runs. The seed test reports a collection error. |
| Red, browser | `pytest tests/e2e/upgrade_portal/test_run_controls/test_existing.py` in Edge | 0 skips. The fixture of FR-004 reports the two old skips as errors. |
| Green, direct | The same direct command | Each test passes. |
| Green, browser | `test_existing.py` alone, `test_bulk.py` alone, `test_run_controls`, and the whole folder | SC-001 to SC-004. |
| Gates | py_compile, ruff, black, mypy, the test quality gate, `tests/guardrails`, and the STE linter | Each gate passes. |

## Risks

| Risk | Mitigation |
| - | - |
| A route refuses a site that the cloud does not list. | The bulk retry site and the lifecycle site already prove the lock route and the history page. The browser run proves the bulk cancel and the reconcile. |
| A module now meets a free first site, and it builds a run that it leaves live. | The full browser run proves the default order. The known case of `test_capture.py` gets its own issue. |
| The import of the browser conftest slows the unit shard. | The import takes about 5 seconds, one time for each interpreter. |
