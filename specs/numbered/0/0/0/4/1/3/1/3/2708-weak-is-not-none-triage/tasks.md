# Tasks: Test quality: triage weak_is_not_none findings

**Input**: `spec.md`, `plan.md`, `analysis.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, and `design/checklists/requirements.md`. The `contracts/` folder is omitted, as `plan.md` states.

**Tests**: Each slice task adds no new test file. Each slice task repairs assertions in an existing test file. Each repair carries a controlled failing run (FR-004).

**Organization**: Tasks run in order. The slices A to H run one at a time (decision D-10).

## Format

`[ID] [P?] [Requirement] Description`

- **[P]**: The task reads files only. It can run in parallel with other read-only tasks.
- **Status**: `open`, `verified-present`, `partial`, or `absent`.
- **Lines**: Lines come from the baseline. Each line is a weak guard on main, or a stale entry.
- **Verification**: Run each command from the repository root, unless the task names another folder.

## Phase 1: Verify the base

- [ ] T001 [P] [FR-001] [SC-001] Confirm the analyzer count on main.
  - **Files**: none modified. Reads `.github/test-quality-config.toml` and `.github/test-quality-baseline.json`.
  - **Acceptance**: The gate summary gives the `weak_is_not_none` count, the scope line, and the new-findings line. The record names the commit before any edit. The expected baseline count is 84 entries.
  - **Verification**: `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides`, then `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`.
  - **Status**: open.

- [ ] T002 [P] [FR-006] Confirm the 19 stale entries on the analyzer report.
  - **Files**: none modified.
  - **Acceptance**: The report has no `weak_is_not_none` finding at these lines:
    - `mist-ops-platform/tests/unit/api/test_session_security.py` at lines 155 and 366.
    - `mist-ops-platform/tests/unit/mist/test_api_result.py` at line 59.
    - `tests/guardrails/test_src_public_symbol_preservation.py` at line 120.
    - `tests/maps/test_plotly_heatmap_renderer.py` at line 68.
    - `tests/maps/test_plotly_map_figure_builder.py` at line 70.
    - `tests/unit/config/foundation/support/refactors/network/clients/test_service_ping_launcher.py` at line 84.
    - `tests/unit/config/standalone/foundation/persistence/database/test_retention.py` at line 184.
    - `tests/unit/config/standalone/foundation/persistence/redis/test_redis_json_writer.py` at line 51.
    - `tests/unit/config/standalone/foundation/support/quality/imports/test_no_mistapi_stub_leak.py` at line 26.
    - `tests/unit/prod_readiness/standalone/operations/wan/test_wan_hub_group_manager.py` at line 373.
    - `tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py` at lines 373 and 387.
    - `tests/unit/refactors/test_tui_launcher.py` at line 31.
    - `tests/unit/site/address_audit/test_audit_engine.py` at line 353.
    - `tests/unit/ui/test_function_executor.py` at line 65.
    - `tests/unit/upgrade_portal/test_signals.py` at line 431.
    - `tests/unit/websocket/polling/test_completion_detector.py` at line 606.
    - `tests/unit/websocket/polling/test_result_combiner.py` at line 114.
  - **Verification**: Read the analyzer `report.json` from the T001 run. Filter on `rule_id` equal to `weak_is_not_none`.
  - **Status**: verified-present. Main holds no weak guard at these lines (research rows 52 to 135).

## Phase 2: Repair slices

Each slice runs tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. Each slice runs T017 after its repairs.

- [ ] T003 [FR-002] [FR-004] Slice A. Repair seven redundant guards in the mist-ops-platform tests.
  - **Files**: `mist-ops-platform/tests/unit/api/test_token_refresh_route.py` (line 64), `mist-ops-platform/tests/unit/mist/test_deploy_calls.py` (line 90), `mist-ops-platform/tests/unit/mist/test_final_sdk_verification.py` (line 39), `mist-ops-platform/tests/unit/mist/test_firmware.py` (line 123), `mist-ops-platform/tests/unit/mist/test_response_consumers.py` (line 82), `mist-ops-platform/tests/unit/shared/test_session_store.py` (line 64), `mist-ops-platform/tests/unit/worker/checks/test_post_checks.py` (line 155).
  - **Acceptance**: Each line holds one exact check on the same line. The later exact check in each test stays. Each guard fails for one controlled wrong value.
  - **Verification**: From `mist-ops-platform`, run `python -m pytest tests/unit/mist/test_deploy_calls.py` for each file. Use the file path from that folder.
  - **Status**: absent. Main holds the weak guard at each line.

- [ ] T004 [FR-002] [FR-004] Slice B. Repair six guards that have an archived candidate.
  - **Files**: `mist-ops-platform/tests/contract/test_api_contracts.py` (lines 66 and 151), `mist-ops-platform/tests/integration/test_e2e_smoke.py` (lines 26, 27, 32, and 55).
  - **Acceptance**: Each guard becomes an exact value, type, or identity check. The archived commit `de809907ca89e576ff11fa3fb7d123cc6b7e8ecc` is reference evidence only (decision D-6). Its content is not copied.
  - **Verification**: From `mist-ops-platform`, run `python -m pytest tests/contract/test_api_contracts.py` and `python -m pytest tests/integration/test_e2e_smoke.py`.
  - **Status**: partial. The archived commit exists on GitHub and is not on main. The preserved e2e candidate blob is absent on GitHub.

- [ ] T005 [FR-002] [FR-004] Slice C. Repair nine guards in the contract and integration tests.
  - **Files**: `tests/contract/test_mib_matches_catalog.py` (122), `tests/contract/upgrade_portal/test_capture_start.py` (762), `tests/contract/upgrade_portal/test_capture_start_returns_lock_grant.py` (463), `tests/contract/upgrade_portal/test_org_scope.py` (691 and 708), `tests/integration/test_aggregate_upgrade_flow.py` (124), `tests/integration/upgrade_portal/run_controls/test_actions.py` (106, 192, and 210).
  - **Acceptance**: Each line holds one exact check. Line 210 uses the archived repair as reference only (decision D-6).
  - **Verification**: Run `python -m pytest <file>` for each file. For line 210, run the file with `-k` on the test name `test_atomic_success_can_insert_one_retry_run_with_its_outcome`.
  - **Status**: partial. Line 210 has an archived candidate blob that is absent on GitHub. The other lines are absent.

- [ ] T006 [FR-002] [FR-004] Slice D. Repair four guards in the maps tests.
  - **Files**: `tests/maps/test_browser_opener.py` (202), `tests/maps/test_plotly_heatmap_renderer.py` (42 and 53), `tests/test_audit_analyzer.py` (98).
  - **Acceptance**: Each line holds one exact check on the same line.
  - **Verification**: Run `python -m pytest <file>` for each file.
  - **Status**: absent.

- [ ] T007 [FR-002] [FR-004] Slice E. Repair seven guards in the upgrade portal unit tests.
  - **Files**: `tests/unit/upgrade_portal/test_confirm_warning.py` (241), `tests/unit/upgrade_portal/test_inventory_address.py` (196), `tests/unit/upgrade_portal/test_lock_record_empty_run.py` (179), `tests/unit/upgrade_portal/test_run_adopts_precheck.py` (145), `tests/unit/upgrade_portal/test_runs/test_actions.py` (395), `tests/unit/upgrade_portal/test_stale_statistics.py` (241 and 253).
  - **Acceptance**: Each line holds one exact check on the same line.
  - **Verification**: Run `python -m pytest <file>` for each file.
  - **Status**: absent.

- [ ] T008 [FR-002] [FR-004] Slice F. Repair seven guards in the other unit tests.
  - **Files**: `tests/unit/config/foundation/support/refactors/network/launchers/test_maps_manager_launcher.py` (76), `tests/unit/device/test_ap_profile_migration_manager.py` (245), `tests/unit/ssh/config/test_env_loader_wave9.py` (340), `tests/unit/ssh/test_ssh_runner_manager_extended.py` (215), `tests/unit/marvis/mist/resources/site/test_site_config_manager.py` (63), `tests/unit/ui/test_results_grid_builder.py` (131), `tests/unit/websocket/test_manager_thread_join.py` (90).
  - **Acceptance**: Each line holds one exact check on the same line.
  - **Verification**: Run `python -m pytest <file>` for each file.
  - **Status**: absent.

- [ ] T009 [FR-002] [FR-004] Slice G. Repair seven guards in four files that have confirmed gaps.
  - **Files**: `tests/unit/config/standalone/foundation/persistence/database/test_data_browser_path_guard.py` (113 and 125), `tests/unit/marvis/standalone/mist/intelligence/reports/test_e911_bssid.py` (493 and 546), `tests/unit/config/standalone/foundation/persistence/redis/test_redis_writer.py` (55), `tests/unit/prod_readiness/standalone/operations/execution/firmware/test_bulk_ap_upgrader.py` (1389 and 1398).
  - **Acceptance**: Lines 125, 546, 55, 1389, and 1398 hold exact values from the controlled wrong value runs in the issue comments. The other two lines hold exact checks. The start time tests use a fixed clock.
  - **Verification**: Run `python -m pytest <file>` for each file.
  - **Status**: absent.

- [ ] T010 [FR-002] [FR-004] Slice H. Repair five guards that have a local candidate.
  - **Files**: `tests/unit/test_csv_comparator.py` (145 and 147), `tests/unit/websocket/polling/test_message_router.py` (480), `tests/unit/site/address_audit/test_ui_geocoder_profile_cleanup.py` (64), `tests/unit/marvis/standalone/mist/resources/device/test_device_utility_commands.py` (231).
  - **Acceptance**: Each line holds one exact check. The candidate blobs `5cddd34e58a73e20f062ab3a98900a9f21bde39e`, `d92499a42ba5c9b2ec940156957601e732052043`, and `06755cf64eef0f5a85aa5d245f2fe942092b2088` are absent on GitHub. The branch tip `d3a1483d7a9d966c8d5b476682fdf14765d4b88d` is reference evidence only.
  - **Verification**: Run `python -m pytest <file>` for each file. For `test_message_router.py`, record the root logger effect (risk R-9).
  - **Status**: partial. The device test repair blob `cd471d933954032388114597a68861e7441350e2` is on GitHub, not on main.

## Phase 3: Holds

Each hold stays open until the owner releases the file. Do not start a hold task before its release.

- [ ] T011 [FR-008] Hold H-1. Registry validation tests.
  - **Files**: `mist-ops-platform/tests/unit/mist/test_registry_validation.py` (36, 49, 59, and 69).
  - **Blocker**: The preserved #2746 branch overlaps this file. Issue #4583 tracks that branch. Issue #2746 is open.
  - **Acceptance**: The owner releases the file. Then each line holds one exact check.
  - **Verification**: From `mist-ops-platform`, run `python -m pytest tests/unit/mist/test_registry_validation.py`.
  - **Status**: open.

- [ ] T012 [FR-008] Hold H-2. Viewer callback tests.
  - **Files**: `tests/maps/test_viewer_callbacks_wave_a.py` (134 and 181), `tests/maps/test_viewer_callbacks_wave_e2.py` (174 and 178).
  - **Blocker**: Issue #4731 reserves both files. Commit `2238c75f9c1a84ce67c9190ba180a12c724190d8` holds the e2 repair on GitHub. It is not on main.
  - **Acceptance**: The owner releases both files. Then each line holds one exact check.
  - **Verification**: Run `python -m pytest <file>` for each file.
  - **Status**: partial.

- [ ] T013 [FR-008] Hold H-3. Inventory tests.
  - **Files**: `tests/unit/inventory/test_org_device_inventory_msp.py` (342).
  - **Blocker**: Issue #4708 reserves this file. Its candidate blob `841d9397b48a13138dea65278a6f76ced8e904d1` is absent on GitHub.
  - **Acceptance**: The owner releases the file. Then the line holds one exact table check.
  - **Verification**: Run `python -m pytest tests/unit/inventory/test_org_device_inventory_msp.py`.
  - **Status**: open.

- [ ] T014 [FR-008] Hold H-4. Credential session tests.
  - **Files**: `tests/contract/upgrade_portal/test_no_credential_leak.py` (633 and 657).
  - **Blocker**: Issue #3714 is open. Its credential design needs a human decision (D-16). The candidate blob `9ffad21cf6b9a1ecf27e2cf43b62dcb2b97358b1` is absent on GitHub.
  - **Acceptance**: A human decision releases the file. Then both lines hold one exact check.
  - **Verification**: Run `python -m pytest tests/contract/upgrade_portal/test_no_credential_leak.py`.
  - **Status**: open.

## Phase 4: Unclassified findings

- [ ] T015 [FR-001] Unclassified U-1. Compose deployment test.
  - **Files**: `tests/integration/test_compose_deploy.py` (36).
  - **Acceptance**: The test runs with `COMPOSE_TEST=1` and running compose services (decision D-14). Without that run, the status stays open. A skipped test is not a pass.
  - **Verification**: Run the compose group procedure from `.github/copilot-instructions.md` with the naming policy. Then run `python -m pytest tests/integration/test_compose_deploy.py`.
  - **Status**: open.

- [ ] T016 [FR-001] Unclassified U-2. WAN launcher test.
  - **Files**: `tests/unit/config/foundation/support/refactors/network/launchers/test_wan2_migration_launcher.py` (96).
  - **Acceptance**: Read the test. If a later exact check covers the value, use the S method. Otherwise use the R method. Record the choice in the pull request body.
  - **Verification**: Run `python -m pytest tests/unit/config/foundation/support/refactors/network/launchers/test_wan2_migration_launcher.py`.
  - **Status**: open.

## Phase 5: Baseline and upstream

- [ ] T017 [FR-006] [FR-007] Update the baseline after each slice.
  - **Files**: `.github/test-quality-baseline.json`.
  - **Acceptance**: Run the analyzer write command once per slice. The diff removes entries only for repaired and stale lines. The diff adds no entry. A recorded shift keeps the same rule, file, category, and explanation.
  - **Verification**: `test-quality-analyzer --write-baseline --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`, then `git diff -- .github/test-quality-baseline.json`.
  - **Status**: open.

- [ ] T018 [FR-005] File the upstream analyzer issue.
  - **Files**: none in this repository.
  - **Acceptance**: The issue in `misthelper-devtools` names the config key `weak_assert_not_none` and the emitted rule ID `weak_is_not_none`. It attaches the T001 analyzer output. The issue link appears in the first slice pull request body.
  - **Verification**: Open the issue with `gh issue view <number> -R jmorrison-juniper/misthelper-devtools`.
  - **Status**: open.

## Final tasks (repeat for each slice A to H)

- [ ] T-LOCAL-GATES Run each applicable local gate on the changed files.
  - **Requirement**: FR-011.
  - **Gates that run**: compile, lint, format, the changed test file, Bandit, and `symbol-diff`. Mist-ops-platform files also run the CI correctness selector.
  - **Commands**: Run each command for each changed file:
    - `python -m py_compile <file>`
    - `ruff check <file>`
    - `black --check <file>`
    - `python -m pytest <file>`
    - `bandit -c pyproject.toml -r <file> -q`
    - `symbol-diff --base origin/main <file>`
  - **Mist-ops commands**: From the `mist-ops-platform` folder, run `ruff check . --select F,B,E9 --ignore F401,B008,B905 --output-format=concise` for each mist-ops-platform file.
  - **Gates that do not apply**: mypy (`MYPY_PATHS` excludes tests, `ci.yml` line 93). Vulture (`VULTURE_PATHS` excludes tests, `ci.yml` line 101). Pydocstyle and interrogate (src paths only). Pylint, radon, and pip-audit (no source or dependency change). Menu reference, safe sweep, and ops portal (no menu or portal change). STE (no Markdown change). Changelog (decision D-12).
  - **Test quality**: Run the preflight, then the changed-scope gate after the commit, then the full gate before push. The procedure is `.github/copilot-instructions.md` line 95.
  - **Status**: open.

- [ ] T-PR Create the child issue, commit, push, and open the pull request.
  - **Requirement**: FR-009, FR-010, FR-013.
  - **Child issue**: Create one issue for the slice before its branch. Use the labels chore, tests, and in-progress (constitution line 487). Claim it first (constitution line 500).
  - **Branch**: `chore/2708-weak-is-not-none-<slice letter>`. For example, `chore/2708-weak-is-not-none-a`.
  - **Commit**: The commit uses the Conventional Commits format. Its body names `Closes #<child issue>`. The final slice also names `Closes #2708`. The commit carries the co-author trailer.
  - **Pull request body**: The body gives a closing reference to the child issue (constitution line 519) and `Part of #2708`. It lists the changed files, each finding with its mutation result, and each gate result. It gives the baseline diff summary, the reason for no changelog fragment, and the rollback note from `plan.md`.
  - **Rule**: Do not bypass hooks. Stop and report when a hook fails (risk R-7). Do not force-push.
  - **Status**: open.

- [ ] T-REMOTE-CI Watch the required checks.
  - **Requirement**: FR-012, SC-005.
  - **Command**: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`.
  - **Acceptance**: Each required check passes on the final commit. The `test_quality_gate` job passes (`ci.yml` line 602).
  - **Status**: open.

- [ ] T-MERGE Merge the slice.
  - **Requirement**: FR-012.
  - **Acceptance**: The orchestrator authorizes the merge. The branch rebases on current main. The auto-merge label is added only after each check passes. The container build does not run (decision D-11). Remove the branch after the merge.
  - **Status**: open.
