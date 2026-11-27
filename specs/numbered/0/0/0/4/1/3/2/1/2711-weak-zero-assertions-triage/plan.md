# Implementation Plan: Weak zero-assertion triage

**Branch**: `chore/2711-weak-zero-assertions` | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/0/4/1/3/2/1/2711-weak-zero-assertions-triage/spec.md`

**Input**: Numeric specification from `/specs/numbered/0/0/0/4/1/3/2/1/2711-weak-zero-assertions-triage/spec.md`. The eight route digits are the base-5 encoding of 2711 (`41321`), padded with zeros.

This record keeps `spec.md`, `plan.md`, and `tasks.md` at the feature root. Supporting artifacts sit under `design/`. The feature root holds five children, and no other directory holds more than five.

## Summary

The baseline holds 557 `weak_zero_assertions` entries. Triage sorts each entry into one of three groups: stale, detector gap, or zero construct. The work removes 313 stale entries, repairs 115 tests that assert nothing, and routes 129 detector-gap entries upstream. Each repair pull request covers one domain slice and merges in serial order.

## Technical Context

**Language/Version**: Python 3.15 or newer, from `pyproject.toml` (`>=3.15`).

**Primary Dependencies**: `misthelper-devtools` pinned at commit `2239e7bd` (version 0.6.4), `pytest`, `ruff`, `black`, `mypy`, `mistapi` 0.64.1 installed in `.venv` for mocked tests.

**Storage**: Not applicable. The baseline is a JSON file in `.github/`.

**Testing**: `pytest` for each changed test file. The analyzer runs in full-suite form and in changed-from form.

**Target Platform**: Windows 11 development hosts and Linux CI runners.

**Project Type**: Test-only maintenance. Product code does not change.

**Performance Goals**: Each slice finishes its local gates within one working session.

**Constraints**: The baseline keys include line numbers. Each edit above a flagged test changes that test's key. The write command rewrites all rules.

**Scale/Scope**: 27 test files for repairs, 121 files in the current baseline, 1 baseline file, and 10 repair slices.

## Constitution Check

*Gate: passes before research. Rechecked after the design artifacts.*

Each principle in `.specify/memory/constitution.md` (version 1.9.0) has one result.

| Principle | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | The record folder adds one route folder under `specs/numbered/`. The feature root holds five children. No product directory gains a child. |
| II. Class-Based Architecture | Pass | The change adds no function or class to product code. Test assertions inside existing test classes do not add wrappers. |
| III. Safety-First | Pass | The change adds no destructive operation and no input path. Test controls use in-memory mutations only. |
| IV. Full Deployment Pipeline | Pass with plan | T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run for each slice in order. |
| V. Observability and Logging | Pass | Test edits keep ASCII text. The change adds no log call to product code. |
| VI. Inline Comments | Pass with condition | Each changed test line carries an inline comment that gives its purpose. |
| VII. Action Logging | Pass with reason | The change adds only test assertions. It adds no action to product code. Existing helper logs stay in place. |
| Technology: mistapi | Not applicable | No Mist request is added or changed. |
| Technology: WebSocket transport | Not applicable | No transport is owned or changed. |
| Technology: package manager | Pass | No dependency changes. The pin in `requirements-dev.txt` stays unchanged. |
| Technology: test containers | Not applicable | The local gates run without a container. |
| Technology: file paths | Pass | Test code uses existing helpers. The record uses no path joins. |
| Governance: compliance review | Pass with plan | Each pull request names the principles that it touches. |
| Escalation: SpecKit | Required | The work touches more than three files and more than two test classes. |

**Gate result**: Pass. No unresolved violation remains.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/0/4/1/3/2/1/2711-weak-zero-assertions-triage/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      baseline-entry.md
    checklists/
      requirements.md
```

The route `0/0/0/4/1/3/2/1` comes from base-5 encoding of 2711. The reference route `0/0/1/2/4/1/4/0` for issue 4920 uses the same method.

### Change file map

| Path | Action | Task | Reason |
| - | - | - | - |
| `.github/test-quality-baseline.json` | Modify | T004, T016 | Remove stale weak-zero entries. Remove repaired entries at the end. |
| `tests/unit/config/standalone/foundation/models/core/test_telemetry.py` | Modify | T006 | Repair zero-construct tests. |
| `tests/unit/config/standalone/foundation/support/quality/cross_domain/test_site_auto_upgrade.py` | Modify | T006 | Repair zero-construct tests. |
| `tests/unit/export/test_org_device_stats_exporter.py` | Modify | T007 | Repair zero-construct test. |
| `tests/unit/export/test_org_template_exporter.py` | Modify | T007 | Repair zero-construct test at line 76. |
| `tests/unit/export/test_site_device_exporter.py` | Modify | T007 | Repair zero-construct tests. |
| `tests/unit/inventory/test_org_device_inventory_msp.py` | Modify | T007 | Repair zero-construct tests. |
| `tests/unit/maps/standalone/interfaces/ui/test_issue_2971_status_final.py` | Modify | T008 | Repair zero-construct tests. |
| `tests/unit/maps/standalone/interfaces/ui/test_issue_2971_status_slice5.py` | Modify | T008 | Repair zero-construct tests. |
| `tests/unit/test_issue_2971_census_repairs.py` | Modify | T008 | Repair zero-construct tests. |
| `tests/unit/marvis/mist/resources/site/test_site_config_manager_extended.py` | Modify | T009 | Repair zero-construct tests. |
| `tests/unit/marvis/standalone/mist/resources/device/test_device_utility_commands.py` | Modify | T009 | Repair zero-construct tests. |
| `tests/unit/marvis/mist/intelligence/troubleshooting/core/test_marvis_troubleshoot_utils_extended.py` | Modify | T010 | Repair zero-construct tests. |
| `tests/unit/marvis/standalone/mist/intelligence/reports/test_e911_bssid.py` | Modify | T010 | Repair zero-construct tests. |
| `tests/unit/marvis/standalone/mist/intelligence/reports/test_standalone_offline_device_reporter.py` | Modify | T010 | Repair zero-construct test. |
| `tests/unit/device/test_ap_profile_migration_manager.py` | Modify | T011 | Repair zero-construct tests. |
| `tests/unit/test_routing_utils.py` | Modify | T011 | Repair zero-construct tests. |
| `tests/unit/utils/test_zscaler_probe_transport.py` | Modify | T011 | Repair zero-construct tests. |
| `tests/unit/web_portal/test_portal_graceful_shutdown.py` | Modify | T012 | Repair zero-construct tests. |
| `tests/unit/ssh/test_ssh_runner_manager_extended.py` | Modify | T012 | Repair zero-construct test. |
| `tests/unit/ui/test_tui_runner.py` | Modify | T012 | Repair zero-construct test. |
| `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` | Modify | T012 | Repair zero-construct test. |
| `tests/unit/websocket/test_service_ping_manager.py` | Modify | T012 | Repair zero-construct test. |
| `tests/unit/prod_readiness/standalone/operations/execution/capture/test_packet_capture.py` | Modify | T013 | Repair zero-construct tests. |
| `tests/unit/prod_readiness/standalone/operations/execution/firmware/test_bulk_ap_upgrader.py` | Modify | T014 | Repair zero-construct tests. |
| `tests/unit/prod_readiness/standalone/operations/execution/firmware/test_org_ap_upgrader.py` | Modify | T014 | Repair zero-construct tests. |
| `tests/unit/prod_readiness/operations/execution/firmware/upgraders/manager/platform/test_firmware_manager_ssr.py` | Modify | T014 | Repair zero-construct test. |
| `tests/unit/prod_readiness/standalone/operations/execution/ssid/test_ssid_template_consolidation.py` | Modify | T015 | Repair 27 zero-construct tests. |

Files not changed: `.github/test-quality-config.toml`, `requirements-dev.txt`, `.github/workflows/ci.yml`, `documentation/quality-gates.md`, and every product file under `src/`. No `changelog.d/` fragment is added, because test-only work has no user-visible change.

### Supporting artifacts

The `contracts/` folder holds one file. It documents the baseline entry format, because that format is the interface between the analyzer and the repository. The `checklists/` folder holds one file, the specification quality checklist.

## Architecture

### Disposition model

Each baseline entry receives one disposition. The disposition decides the task that owns the entry.

| Disposition | Count in the current triage | Owner task | Action |
| - | -: | - | - |
| Stale, counted by the analyzer | 284 | T004 | Remove through the write command. |
| Stale, self-assert in TestCase | 17 | T004 | Remove through the write command. |
| Stale, missing file | 12 | T004 | Remove through the write command. |
| Detector gap, mock call-count | 99 | T005 | Route upstream. Keep the entry. |
| Detector gap, helper assertion | 20 | T005 | Read the helper. Route upstream. Keep the entry. |
| Detector gap, Playwright expect | 10 | T005 | Route upstream. Keep the entry. |
| Zero construct | 115 | T006 to T015 | Repair with behavior assertions. |

The counts come from a read-only classification of the local files, which equal the `main` blobs for all 120 present files. T002 confirms the counts with the analyzer report.

### Serial merge order

1. T001 confirms the pinned analyzer.
2. T002 generates the analyzer report.
3. T004 removes stale entries in one pull request.
4. T005 files the upstream detector issue.
5. Repair slices T006 to T015 merge one at a time. Each slice rebases on `main`. Each slice regenerates the baseline with the full-suite write command.
6. T016 removes the entries that the repairs retired.

Caution: Parallel slices conflict on the baseline file, because the baseline is one shared record. Merge the slices one at a time.

### Test repair pattern

Each repaired test checks one observable result of the code under test. The check uses the returned value, a written record, or a call argument. The change adds no `assert True`, no empty test body, and no deletion. Each added line carries an inline comment.

## Dependencies

- `misthelper-devtools` at commit `2239e7bd` supplies `test-quality-analyzer`. The pin does not change in this work.
- `pytest-timeout`, `pytest-cov`, and `pytest-playwright` come from the existing lock. No new package is added.
- The upstream detector change depends on the `misthelper-devtools` owner. It does not block slices T006 to T015.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| The write command removes entries for other rules. | Another issue loses its accepted findings. | Restore each entry outside `weak_zero_assertions`. The PR checks the rule counts before and after. |
| A repair shifts a later flagged function. | The gate reports a new finding. | Run the changed-from gate after each edit. Re-key the shifted entry in the same serial pull request. |
| A helper holds the assertions. | A repair adds a redundant check. | Read the helper body before repair. Reclassify the entry as a detector gap when the helper asserts. |
| A local analyzer predates the pin. | A false new finding appears. | Run T001 before T002. Stop when the installed commit differs from `2239e7bd`. |
| A slice overlaps an open pull request. | A merge conflict or a lost change. | Check open pull requests for each file before the slice starts. |
| A closing keyword closes the issue early. | The campaign appears done. | Use `Part of #2711` in each slice body. Use a closing keyword only in the final pull request. |

Caution: A repaired test can share state with another test. Run each changed file alone and in its module order.

## Rollback

1. Revert the slice commit with a new commit on `main`. Do not force-push.
2. For a baseline rewrite, restore `.github/test-quality-baseline.json` from the previous `main` blob in a new commit.
3. Reopen the affected slice file in the disposition table. Its entry returns to the open state.
4. Record the rollback in a comment on #2711.
