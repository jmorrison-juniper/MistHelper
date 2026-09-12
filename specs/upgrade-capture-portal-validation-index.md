# Upgrade capture portal validation index

## Purpose

This index records the user workflow, the browser evidence, and the validation state for each related SpecKit package. A checked task does not prove a user workflow. A passing browser journey or a targeted non-browser test supplies the proof.

## Status terms

- **Pass**: The required workflow has direct and current proof.
- **Partial**: Some required workflows have proof, but one or more goals need more proof or implementation.
- **Fail**: A required workflow does not work or does not exist.
- **Historical**: A later package replaces this package.

## Feature index

| SpecKit package | Role | Main user workflows | Browser evidence | Status | Remaining gap or defect |
|---|---|---|---|---|---|
| `1823-capture-upgrade-portal` | Early portal design | Select a site, capture data, compare captures, and start an upgrade. | The later portal browser suite covers the shared workflows. | **Historical** | `1823-upgrade-capture-portal` replaces conflicting architecture and contracts. |
| `1823-upgrade-capture-portal` | Primary portal specification | Sign in, select an organization and site, control the site lock, capture data, compare captures, configure an upgrade, confirm it, monitor it, stop it, and review history. | `test_signin.py`, `test_site_selection.py`, `test_capture.py`, `test_capture_identifier_paint.py`, `test_comparison.py`, `test_upgrade.py`, `test_stop.py`, `test_history.py`, and `test_two_operators.py`. | **Partial** | The isolated suite passes. A complete live upgrade remains outside this audit. Issue #1992 tracks live-site rehearsal proof. |
| `1824-browser-session-upgrades` | Browser token sessions | Enter a Mist token in the browser, create an operator session, use that token for Mist reads, and clear it at sign-out. | `test_signin.py` proves the controls and session boundaries. | **Partial** | The isolated server injects an environment-token identity. Issue #2472 tracks the missing browser-token-to-Mist-request proof. |
| `1992-upgrade-rehearsal` | Safe rehearsal harness | Run upgrade gates, timing, stop propagation, and cloud stand-ins without a firmware write. | No browser proof is required. The rehearsal unit tests prove the harness behavior. | **Pass** | Issue #1992 still tracks a separate live-site scenario. |
| `2443-tier3-capture-datapoints` | Tier 3 capture detail | Request Tier 3, show guest and detail sections, distinguish empty and unavailable sections, and download matching CSV and JSON rows. | `test_capture_tier3.py` opens the stored Tier 3 page and verifies rows, states, and export parity. Contract tests verify field detail and filtering. | **Partial** | A live Tier 3 run exposed the numeric digest defect in issue #2471. The repair has unit proof but needs container and live proof. |
| `2447-confirmation-navigation` | Confirmation navigation | Open a prepared run, find the confirmation control, and reach the typed confirmation gate. | `test_upgrade.py` drives the prepared-run link and confirmation page. | **Pass** | No current browser gap is known. |
| `2447-cancel-restart-workflow` | Stop and retry lifecycle | Stop an active run, start a fresh retry, and return through the required pre-check path. | `test_stop.py` and `test_run_controls/test_existing.py` cover stop and existing retry controls. | **Partial** | The complete fresh retry journey still needs direct browser proof. Issue #2447 tracks lifecycle failures. |
| `2447-stale-bulk-run-controls` | Stale and bulk run controls | Show stale age, reconcile state, preview a bulk action, cancel or retry selected runs, and isolate concurrent operators. | `test_run_controls/test_stale.py`, `test_run_controls/test_bulk.py`, and `test_run_controls/test_isolation.py` cover stale display, bulk preview, bulk cancel, bulk retry, reconciliation, and operator isolation. | **Partial** | The browser journeys pass. The open tasks of `tasks.md` remain. Issue #2447 tracks this work. |
| `991-upgrade-version-defaults` | Per-type version defaults | Show separate AP, switch, and gateway defaults, remove the global default, and apply configured defaults. | `test_upgrade.py` verifies the per-type controls and the removed global control. | **Partial** | Unit tests prove environment overrides. A browser test does not start the server with each override. |

## Current validation evidence

- The complete isolated Playwright suite passed: 203 tests passed and 4 tests skipped.
- The suite includes two Tier 3 browser tests for rows, section states, and export parity.
- The multi-operator Playwright tests passed: 19 tests passed.
- The bulk preview, isolation, and stale browser tests passed: 26 tests passed.
- The capture storage tests passed: 63 tests passed.
- The stop signal tests passed: 29 tests passed.
- The complete non-browser portal suite passed: 4,196 tests passed.
- A live read-only Tier 3 capture reached all cloud read groups. Storage verification failed because ArangoDB changed `0.0` to `0`.
- Issue #2471 records the storage failure and the conflicting history state.

## Defect: the browser tests leaked the site lock

The run-control browser tests took the site lock and released no lock. The lock
lives in the process-owned lock store, so it outlived the test that took it.

The next operator then read 400 `confirmation_required` from the lock route. The
fixture of `test_two_operators.py` turned that status into a skip, and pytest
reports a skip as a pass. The suite reported success while 22 tests proved
nothing.

The counts show the size of the loss. Before the repair the suite reported 180
passed, 26 skipped, and 1 error. After the repair it reports 203 passed, 4
skipped, and no error.

`tests/e2e/upgrade_portal/test_run_controls/conftest.py` holds the repair. The
`site_lock` fixture takes each lock and releases every lock after the test. The
fixture asks for `page`, so it releases the lock before the browser closes.

Warning: a direct lock call leaks the site and can cause the loss of the test
proof, because the next test then reports a silent skip. Each browser test that
takes the site lock must use this fixture.

## Remaining skips

Four conditional skips remain. Each one names a state of the run, never a defect.

| Test | Reason |
|---|---|
| `test_capture.py:736` | The run create answered 409, so no fresh run key exists. |
| `test_upgrade.py:654` and `test_upgrade.py:666` | The confirm field is disabled, because the run holds no verified pre-check capture. |
| `test_upgrade.py:719` | The run table holds no device row. |

## Required completion work

1. Add a browser-token test that proves a Mist request uses the token from the browser session.
2. Add a complete browser retry journey from a stopped or failed run to a fresh pre-check.
3. Build the digest repair into the local container.
4. Run a new live read-only Tier 3 capture and require the `verified` state.
5. Confirm that history never reports `complete` for an unverified capture.
6. Remove the four conditional skips above, so each one becomes direct proof.
7. Complete the open tasks of `specs/2447-stale-bulk-run-controls/tasks.md`.
