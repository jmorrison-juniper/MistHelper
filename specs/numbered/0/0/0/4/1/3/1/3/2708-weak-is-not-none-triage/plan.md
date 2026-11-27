# Implementation Plan: Test quality: triage weak_is_not_none findings

**Branch**: `chore/2708-weak-is-not-none-triage` | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/0/4/1/3/1/3/2708-weak-is-not-none-triage/spec.md`

**Input**: Numeric specification route `specs/numbered/0/0/0/4/1/3/1/3`. The route is the base-5 form of 2708, padded to eight digits. Source: `.specify/scripts/powershell/spec-route.ps1` line 7.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, and checklists under `design/`.

## Summary

Issue #2708 asks for a triage of `weak_is_not_none` findings. The plan classifies all 84 baseline entries on main. It repairs the weak guards in place with exact checks. It holds the files that open owners reserve. It removes the stale entries after analyzer confirmation. The change edits test files only.

## Technical Context

**Language/Version**: Python 3.15 for the repository. The local venv runs the tests.

**Primary Dependencies**: `pytest`, `ruff`, `black`, `bandit`, and the `misthelper-devtools` package. The package supplies `test-quality-analyzer` and `symbol-diff`. The installed package is version 0.6.4. Its pinned commit is `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` in `requirements-dev.txt` line 197.

**Storage**: The baseline file `.github/test-quality-baseline.json`. It holds 733 entries in total and 84 entries for `weak_is_not_none`.

**Testing**: Changed test files run with `pytest`. The analyzer runs as a gate with the documented procedure in `.github/copilot-instructions.md` line 95.

**Target Platform**: Windows 11 for local runs. GitHub Actions for the required checks.

**Project Type**: Test-only change in one repository.

**Performance Goals**: Not applicable. The change adds no runtime path.

**Constraints**: Analyzer identity uses the line number. Each repair keeps the line count. Serial merges only. Holds apply to reserved files.

**Scale/Scope**: 84 baseline entries in 62 files. 65 weak guards are present on main. 19 entries are stale. 8 slices and 4 holds carry the work. The size class is L. Each present weak guard gets one controlled failing run, so the planned proof count is 65.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Rule | Result | Reason |
| - | - | - |
| Principle I, five-item rule (constitution line 38) | Pass | The feature root holds five children. The `design` folder holds four children. The route uses a managed root (constitution line 57). |
| Principle IV, deployment pipeline (constitution line 143) | Pass with exception | Steps 10 to 12 do not apply. `container-build.yml` triggers on product paths only (line 6). Decision D-11 records this. |
| Principle VI, inline comments (constitution line 204) | Pass by requirement | FR-010 requires an inline comment on each changed test line. |
| Principle VII, action logging (constitution line 235) | Not applicable | The change edits assertions. It adds no production action and no logging call. The review gate wording at constitution line 553 is analysis item A-19. |
| PR checklist, closing reference (constitution line 519) | Pass with exception | Each slice closes its child issue. The final slice closes #2708. Decision D-9. |
| Release notes, one fragment per change (constitution line 409) | Conflict, resolved | `changelog.d/README.md` line 58 exempts an internal-only change. Decision D-12 records the choice. Analysis lists the conflict for maintainer review. |
| Principles II, III, and V | Not applicable | The change adds no class, no input path, and no log text. Test classes keep their structure. |
| AGENTS overlap check (AGENTS.md line 244) | Pass by requirement | Each slice runs the open pull request overlap check before branch creation. |
| AGENTS file declaration (AGENTS.md line 246) | Pass by requirement | Each slice lists its files in its task before editing. |
| AGENTS no push to another agent branch (AGENTS.md line 254) | Pass by requirement | Preserved branches are evidence only. Decision D-6 records the rule. |
| AGENTS test must fail (AGENTS.md line 136) | Pass by requirement | FR-004 requires a controlled failing run for each repaired guard. |
| AGENTS specification threshold (AGENTS.md line 348) | Pass | The change touches more than three files. This record is the specification. |
| Mist API and mistapi | Not applicable | No REST request changes. The local installed `mistapi` version is 0.64.1 (`.venv/Lib/site-packages/mistapi-0.64.1.dist-info`). |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/0/4/1/3/1/3/2708-weak-is-not-none-triage/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    checklists/
      requirements.md
```

The `contracts/` folder is omitted. No interface contract applies. The change adds no menu, CLI, output column, or API shape.

### Source Code (repository root)

The change touches test files and one baseline file. No source file changes. No production package changes. The file-by-file change map below lists each path.

**Structure Decision**: The change uses the existing test tree. No new directory is created.

## Change Map

Each path is a modify. No path is added or deleted. The baseline file changes only through the analyzer command in T017.

| Slice | Task | Repository path (modify) | Lines (finding) |
| - | - | - | - |
| A | T003 | `mist-ops-platform/tests/unit/api/test_token_refresh_route.py` | 64 (S) |
| A | T003 | `mist-ops-platform/tests/unit/mist/test_deploy_calls.py` | 90 (S) |
| A | T003 | `mist-ops-platform/tests/unit/mist/test_final_sdk_verification.py` | 39 (S) |
| A | T003 | `mist-ops-platform/tests/unit/mist/test_firmware.py` | 123 (S) |
| A | T003 | `mist-ops-platform/tests/unit/mist/test_response_consumers.py` | 82 (S) |
| A | T003 | `mist-ops-platform/tests/unit/shared/test_session_store.py` | 64 (S) |
| A | T003 | `mist-ops-platform/tests/unit/worker/checks/test_post_checks.py` | 155 (S) |
| B | T004 | `mist-ops-platform/tests/contract/test_api_contracts.py` | 66, 151 (RC) |
| B | T004 | `mist-ops-platform/tests/integration/test_e2e_smoke.py` | 26, 27, 32, 55 (RC) |
| C | T005 | `tests/contract/test_mib_matches_catalog.py` | 122 (S) |
| C | T005 | `tests/contract/upgrade_portal/test_capture_start.py` | 762 (S) |
| C | T005 | `tests/contract/upgrade_portal/test_capture_start_returns_lock_grant.py` | 463 (S) |
| C | T005 | `tests/contract/upgrade_portal/test_org_scope.py` | 691, 708 (S) |
| C | T005 | `tests/integration/test_aggregate_upgrade_flow.py` | 124 (S) |
| C | T005 | `tests/integration/upgrade_portal/run_controls/test_actions.py` | 106, 192 (S), 210 (RC) |
| D | T006 | `tests/maps/test_browser_opener.py` | 202 (S) |
| D | T006 | `tests/maps/test_plotly_heatmap_renderer.py` | 42, 53 (S) |
| D | T006 | `tests/test_audit_analyzer.py` | 98 (S) |
| E | T007 | `tests/unit/upgrade_portal/test_confirm_warning.py` | 241 (S) |
| E | T007 | `tests/unit/upgrade_portal/test_inventory_address.py` | 196 (S) |
| E | T007 | `tests/unit/upgrade_portal/test_lock_record_empty_run.py` | 179 (S) |
| E | T007 | `tests/unit/upgrade_portal/test_run_adopts_precheck.py` | 145 (S) |
| E | T007 | `tests/unit/upgrade_portal/test_runs/test_actions.py` | 395 (S) |
| E | T007 | `tests/unit/upgrade_portal/test_stale_statistics.py` | 241, 253 (S) |
| F | T008 | `tests/unit/config/foundation/support/refactors/network/launchers/test_maps_manager_launcher.py` | 76 (S) |
| F | T008 | `tests/unit/device/test_ap_profile_migration_manager.py` | 245 (S) |
| F | T008 | `tests/unit/ssh/config/test_env_loader_wave9.py` | 340 (S) |
| F | T008 | `tests/unit/ssh/test_ssh_runner_manager_extended.py` | 215 (S) |
| F | T008 | `tests/unit/marvis/mist/resources/site/test_site_config_manager.py` | 63 (S) |
| F | T008 | `tests/unit/ui/test_results_grid_builder.py` | 131 (S) |
| F | T008 | `tests/unit/websocket/test_manager_thread_join.py` | 90 (S) |
| G | T009 | `tests/unit/config/standalone/foundation/persistence/database/test_data_browser_path_guard.py` | 113 (S), 125 (R) |
| G | T009 | `tests/unit/marvis/standalone/mist/intelligence/reports/test_e911_bssid.py` | 493 (S), 546 (R) |
| G | T009 | `tests/unit/config/standalone/foundation/persistence/redis/test_redis_writer.py` | 55 (R) |
| G | T009 | `tests/unit/prod_readiness/standalone/operations/execution/firmware/test_bulk_ap_upgrader.py` | 1389, 1398 (R) |
| H | T010 | `tests/unit/test_csv_comparator.py` | 145, 147 (RC) |
| H | T010 | `tests/unit/websocket/polling/test_message_router.py` | 480 (RC) |
| H | T010 | `tests/unit/site/address_audit/test_ui_geocoder_profile_cleanup.py` | 64 (RC) |
| H | T010 | `tests/unit/marvis/standalone/mist/resources/device/test_device_utility_commands.py` | 231 (RC) |
| Hold | T011 | `mist-ops-platform/tests/unit/mist/test_registry_validation.py` | 36, 49, 59, 69 (H) |
| Hold | T012 | `tests/maps/test_viewer_callbacks_wave_a.py` | 134, 181 (H) |
| Hold | T012 | `tests/maps/test_viewer_callbacks_wave_e2.py` | 174, 178 (H) |
| Hold | T013 | `tests/unit/inventory/test_org_device_inventory_msp.py` | 342 (H) |
| Hold | T014 | `tests/contract/upgrade_portal/test_no_credential_leak.py` | 633, 657 (H) |
| Open | T015 | `tests/integration/test_compose_deploy.py` | 36 (U) |
| Open | T016 | `tests/unit/config/foundation/support/refactors/network/launchers/test_wan2_migration_launcher.py` | 96 (U) |
| Baseline | T017 | `.github/test-quality-baseline.json` | Analyzer command only |

The 19 stale entries have no file change. Task T002 lists them.

## Implementation Outline

1. Verify the base and the analyzer count (T001). Confirm the 19 stale entries (T002).
2. Repair each slice in order A to H. Each slice runs its local gates, opens one pull request, passes the remote checks, and merges. Each slice updates the baseline with the analyzer command (T017).
3. Keep the holds (T011 to T014) closed until each owner releases its file.
4. Resolve the two unclassified findings (T015, T016) after the analyzer run.
5. File the upstream analyzer issue (T018) for the config key mismatch.

## Risks and Mitigations

- **R-1, line identity shift**: Caution: a line count change moves later findings in the file. The gate then reports them as new. Mitigation: FR-003 and decision D-2. The baseline diff must show only the recorded shifts.
- **R-2, baseline conflicts**: Each slice edits the baseline JSON. Mitigation: serial merges. Each slice regenerates the baseline after its rebase.
- **R-3, count drift**: The per-line check may differ from the analyzer. Mitigation: T001 and T002 decide the count before any edit.
- **R-4, compose-gated test**: The test skips unless `COMPOSE_TEST=1` is set. Mitigation: decision D-14. The record does not count a skip as a pass.
- **R-5, ownership conflict**: An open issue or pull request reserves four files. Mitigation: holds T011 to T014 and decision D-5.
- **R-6, automatic issue closure**: A pull request that closes #2708 closes it on merge. Mitigation: each slice closes its own child issue. Only the final slice closes #2708 (decision D-9).
- **R-7, hook safety**: Caution: an owner reported that the hook directory resolves inside the main checkout. Mitigation: do not bypass hooks. Stop and report when a hook fails.
- **R-8, config key mismatch**: The config key `weak_assert_not_none` does not match the emitted rule ID. Mitigation: no config change in this repository (decision D-4). Task T018 files the upstream issue.
- **R-9, root logger leak**: The message router test changes the root logger level. Mitigation: keep the existing isolation. Issue #4728 tracks the defect.
- **R-10, unavailable candidates**: Preserved candidates are not on main. Mitigation: derive each repair from main (decision D-6).

## Rollback

1. For a slice that breaks main, open a revert pull request for the slice merge commit.
2. The revert restores `.github/test-quality-baseline.json` with the slice commit.
3. Do not force-push to main.
4. When a gate fails after merge, open an issue with the full error output. Title it for its cause.

## Complexity Tracking

None. The Constitution Check has no violation that needs justification.
