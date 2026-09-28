# Implementation Plan: The capture walk ends each run that it builds

**Issue**: #3511
**Branch**: `fix/3511-walk-live-run`
**Spec**: [spec.md](./spec.md)
**Research**: [research.md](./research.md)

## Summary

The walk and the refusal test of `test_capture.py` record each run key in a run ledger.
The teardown of `walking_page` cancels each live run of the ledger, and then it releases the site.
The refusal test requires 201 for its first create call, and it checks that the refusal names its own run.
A new check reads the run history of each site of the picker after each browser module.
It fails the module that left a new live run, and it names the run, its state, and its site.

## Technical Context

- **Language**: Python 3.13
- **Test tools**: pytest, pytest-playwright, and Microsoft Edge through `--browser-channel msedge`
- **Scope**: Test code only. No portal code changes, so the change needs no deploy and no release note.
- **Performance goal**: The scans of the check add less than 10 seconds to a full browser run (SC-004).

## Constitution Check

| Rule | Result |
| - | - |
| Class-based design, no wrappers | Pass. The check lives in three classes. The walk teardown follows the helper form of `test_existing.py`. |
| No legacy compatibility shims | Pass. The refusal test drops the 409 path of its first call. No old path stays. |
| Five-Item Rule | Pass. Each new method takes 5 parameters or fewer and holds fewer than 25 lines. |
| Inline comments and action logging | Pass. Each new line carries a comment. Each read and each decision logs before and after. |
| Safe > Fast | Pass. An unreadable answer fails the check. The check never reads a failure as "no live run". |
| STE | Pass. Each Markdown file must score 80 or more with 0 errors. |

## Project Structure

```text
tests/support/upgrade_portal_e2e/
  live_runs.py                      NEW: LiveRun, SiteRunScan, SiteRunReader, LiveRunCheck
tests/e2e/upgrade_portal/
  conftest.py                       CHANGED: the module check, the portal state, the summary line
  test_capture.py                   CHANGED: the run ledger, the walk teardown, the refusal test
tests/unit/upgrade_portal/
  test_e2e_live_runs.py             NEW: direct tests of the check
  test_e2e_site_lock.py             CHANGED: one direct test of a ledger with a live run and a final run
```

## Design

### The module `live_runs.py`

| Class | Role |
| - | - |
| `LiveRun` | A frozen, ordered record of one live run: `site_id`, `run_id`, and `state`. `from_row(site_id, row)` calls the portal helper `run_is_live`, so the rule has one copy (FR-005). |
| `SiteRunScan` | A frozen record of one scan: the live runs, the count of rows, the count of sites, and the time in milliseconds. |
| `SiteRunReader` | Reads the history of each site through a loopback opener with no proxy. `scan(site_ids)` times the read and returns a `SiteRunScan`. |
| `LiveRunCheck` | Compares one scan with the live runs before the module. It names each leak, writes one record, and builds the summary line. |

The reader obeys these rules.

1. It asks for 200 rows for each page, which is the largest page of the route.
2. It reads the next page while a page is full, and it moves the offset by the length of the page.
3. It stops with a failure after 50 pages, so a wrong answer cannot start an endless read (FR-006).
4. It skips a row that is not an object, as `site_run_records` of the portal does.
5. It fails on a refusal, an unreachable portal, a body that is not a JSON object, and a body with no run list. Each message names the call (FR-007).

The check compares by run key. A run that was live before the module is not a leak of the module, even if its state changed.

### The module check in `conftest.py`

| Item | Change |
| - | - |
| `LIVE_RUN_STATE` | New state: `running` and `live`. `capture_portal_server` sets `running` after the start and clears it before the stop. |
| `LIVE_RUN_KEY` and `LIVE_RUN_RECORD` | New stash key and new record name. The record holds one line for each module (FR-008). |
| `module_live_run_check` | New autouse fixture of module scope. At teardown, it reads the live runs of the earlier scan, scans again, and stores the new scan. Then it writes the record and fails on a leak. |
| `pytest_terminal_summary` | Prints the summary line of the check when a check ran. |

An autouse fixture of module scope tears down after each test fixture of the module.
The portal fixture has session scope, so the portal still runs at that time.
If no test started the portal, the check sends no call.

### The walk teardown in `test_capture.py`

| Item | Change |
| - | - |
| `run_ledger` | New fixture. It gives each test an empty ledger. |
| `walking_page` | Takes the ledger. The teardown ends each live run of the ledger in a `try` block, and releases the site in the `finally` block (FR-002). |
| `_end_the_walk_runs` | New helper. An empty ledger sends no call. A page with no token fails, and the message names `csrf-meta` and #3511. Otherwise `SiteRelease.end_runs` cancels each live run. |
| The walk | Records the run key after the options page opens (FR-001). |
| The refusal test | Requires 201 for the first create call, and a 503 still skips. It records the key, and it checks that the refusal names that run (FR-003). |

The cancel route refuses a call only when another operator holds the site.
So the teardown cancels first, while this browser still holds the site, and then it gives the site back.

## Test Strategy

| Step | Command | Expected result |
| - | - | - |
| Red, direct | `pytest tests/unit/upgrade_portal/test_e2e_live_runs.py` | The import of `live_runs` fails, so each test fails. |
| Green, direct | The same command, and `test_e2e_site_lock.py` | Each test passes. |
| Red, browser | `test_capture.py` alone in Edge, with the check and with the old walk teardown | The check fails the module, and it names the run of the walk (SC-002). |
| Green, browser | `test_capture.py` and `test_existing.py` together in Edge | Each create call of `test_existing.py` answers 201 (SC-001). |
| Green, full | The whole folder `tests/e2e/upgrade_portal` in Edge | 316 passed, 1 skipped (#3380), and 0 leaked live runs (SC-003 and SC-004). |
| Gates | py_compile, ruff, black, mypy, the test quality gate, `tests/guardrails`, and the STE linter | Each gate passes. |

## Risks

| Risk | Mitigation |
| - | - |
| Another module leaks a live run, so the full run fails. | FR-009 applies. The module ends its run with the ledger of #3497. If the fix is large, a new issue holds it. |
| A seed on a site of the picker is live, so the first module fails. | The failure is correct, because such a seed blocks a create. The rule of #3507 keeps each live seed off the picker. |
| The scan reads a foreign portal. | The server fixture refuses a stray listener before the start, and the check runs only after this run started its portal. |
| The scan slows the run. | Five sites need five reads for each module. The record holds the time of each scan, and SC-004 bounds the total. |
