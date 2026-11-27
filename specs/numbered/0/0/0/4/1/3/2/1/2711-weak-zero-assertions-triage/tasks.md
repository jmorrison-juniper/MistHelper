# Tasks: Weak zero-assertion triage

**Input**: Numeric record `specs/numbered/0/0/0/4/1/3/2/1/2711-weak-zero-assertions-triage/`. Supporting paths: `design/research.md`, `design/quickstart.md`, `design/data-model.md`, `design/contracts/baseline-entry.md`, `design/checklists/requirements.md`.

**Format**: `[ID] [P?] [Requirement IDs] Title`. The `[P]` marker means the preparation step can run in parallel. Merge slices one at a time.

**Status values**: open, verified-present, partial, or absent.

**Verification commands** come from the local gates table and the test-quality ratchet in `.github/copilot-instructions.md`:

- VC-A: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
- VC-B: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/$BASE_REF" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
- VC-G: `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides`
- VC-P: `python -m pytest <test file>`

---

## Phase 1: Confirm the authority

- [ ] **T001** Confirm the pinned analyzer. `[FR-001]` Status: verified-present.
  - Paths: `requirements-dev.txt` (line 197), `.venv\Lib\site-packages\misthelper_devtools-0.6.4.dist-info\direct_url.json` (line 1).
  - Acceptance: The installed commit equals `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`. Stop when the commit differs.
  - Verification: VC-G.

- [ ] **T002** Generate the current analyzer report. `[FR-001, FR-002]` Status: open. Depends on T001.
  - Paths: `.github/test-quality-config.toml`, `.github/test-quality-baseline.json`. The report goes to `test_quality_analyzer_output/` (git-ignored).
  - Acceptance: The gate prints `gate_scope` and `gate: 0 new findings vs baseline`. The count of current `weak_zero_assertions` findings is recorded in `analysis.md`. Correct the record if it differs from 244.
  - Verification: VC-A.

- [ ] **T003** [P] Verify helper-based and self-assert cases. `[FR-002, FR-007]` Status: partial. The classification exists. The helper bodies are not read.
  - Paths: `tests/contract/upgrade_portal/test_no_credential_leak.py`, `tests/integration/test_next5_compatibility_paths.py`, `tests/unit/maps/standalone/interfaces/portals/test_favicon.py`, `tests/unit/upgrade_portal/test_capture_start_lock_grant.py`, `tests/unit/utils/test_zscaler_catalogue.py`, `tests/test_upgrade_portal_audit.py`, `tests/unit/test_ssh_host_key_tofu.py`.
  - Acceptance: Each helper-based entry names the helper line that asserts. An entry without an asserting helper moves to the zero-construct family.
  - Verification: VC-P on `tests/unit/utils/test_zscaler_catalogue.py`.

## Phase 2: Remove stale entries

- [ ] **T004** Remove stale baseline entries in one serial pull request. `[FR-002, FR-003]` Status: open. Depends on T002.
  - Paths: `.github/test-quality-baseline.json`.
  - Acceptance: The full-suite write command removes the 313 stale `weak_zero_assertions` entries. Those 313 entries include the 12 entries for `tests/unit/test_bulk_switch_upgrader.py`. Every other rule keeps its entries. The total entry count falls from 733 to 420.
  - Caution: The write command rewrites every rule. Restore each entry outside `weak_zero_assertions` before the commit.
  - Verification: VC-A.

- [ ] **T005** [P] File the upstream detector issue. `[FR-006]` Status: open.
  - Paths: none in this repository. Upstream file: `src/misthelper_devtools/test_quality_analyzer/detection/weak_assertion.py` in `jmorrison-juniper/misthelper-devtools`.
  - Acceptance: One issue names three families with counts: mock call-count 99, helper assertion 20, Playwright expect 10. It asks the detector to key baseline entries by function name. It gives one example per family. Record the issue URL in a comment on #2711.
  - Verification: VC-A, rerun after the pin changes.

## Phase 3: Repair zero-construct tests

Each slice merges alone. Each slice regenerates the baseline only after a rebase on `main`. A slice touches no baseline entry except through the write command.

- [ ] **T006** Repair slice R01, config and models. `[FR-004, FR-005]` Status: open. Depends on T004.
  - Paths: `tests/unit/config/standalone/foundation/models/core/test_telemetry.py` (2 entries), `tests/unit/config/standalone/foundation/support/quality/cross_domain/test_site_auto_upgrade.py` (7 entries).
  - Acceptance: Each entry gains one behavior assertion. Each repaired test fails under its in-memory mutation control.
  - Verification: VC-P on each path.

- [ ] **T007** Repair slice R02, exporters. `[FR-004, FR-005]` Status: open. Depends on T004.
  - Paths: `tests/unit/export/test_org_device_stats_exporter.py` (1), `tests/unit/export/test_org_template_exporter.py` (1, line 76), `tests/unit/export/test_site_device_exporter.py` (3), `tests/unit/inventory/test_org_device_inventory_msp.py` (2).
  - Acceptance: Same as T006. Each changed line keeps an inline comment.
  - Verification: VC-P on `tests/unit/export/test_org_template_exporter.py`.

- [ ] **T008** Repair slice R03, issue 2971 status tests. `[FR-004, FR-005]` Status: open. Depends on T004.
  - Paths: `tests/unit/maps/standalone/interfaces/ui/test_issue_2971_status_final.py` (3), `tests/unit/maps/standalone/interfaces/ui/test_issue_2971_status_slice5.py` (3), `tests/unit/test_issue_2971_census_repairs.py` (4). The census tests call a helper. Read the helper before repair.
  - Acceptance: Same as T006.
  - Verification: VC-P on `tests/unit/test_issue_2971_census_repairs.py`.

- [ ] **T009** Repair slice R04, Marvis resources. `[FR-004, FR-005]` Status: open. Depends on T004.
  - Paths: `tests/unit/marvis/mist/resources/site/test_site_config_manager_extended.py` (6), `tests/unit/marvis/standalone/mist/resources/device/test_device_utility_commands.py` (6).
  - Acceptance: Same as T006.
  - Verification: VC-P on `tests/unit/marvis/standalone/mist/resources/device/test_device_utility_commands.py`.

- [ ] **T010** Repair slice R05, Marvis intelligence. `[FR-004, FR-005]` Status: open. Depends on T004.
  - Paths: `tests/unit/marvis/mist/intelligence/troubleshooting/core/test_marvis_troubleshoot_utils_extended.py` (2), `tests/unit/marvis/standalone/mist/intelligence/reports/test_e911_bssid.py` (2), `tests/unit/marvis/standalone/mist/intelligence/reports/test_standalone_offline_device_reporter.py` (1).
  - Acceptance: Same as T006.
  - Verification: VC-P on `tests/unit/marvis/standalone/mist/intelligence/reports/test_e911_bssid.py`.

- [ ] **T011** Repair slice R06, device, routing, and transport. `[FR-004, FR-005]` Status: open. Depends on T004.
  - Paths: `tests/unit/device/test_ap_profile_migration_manager.py` (2), `tests/unit/test_routing_utils.py` (2), `tests/unit/utils/test_zscaler_probe_transport.py` (2).
  - Acceptance: Same as T006. For the transport file, check the close-call contract, not the mock count alone.
  - Verification: VC-P on `tests/unit/utils/test_zscaler_probe_transport.py`.

- [ ] **T012** Repair slice R07, shutdown, SSH, TUI, WLAN timer, and ping. `[FR-004, FR-005]` Status: open. Depends on T004.
  - Paths: `tests/unit/web_portal/test_portal_graceful_shutdown.py` (4), `tests/unit/ssh/test_ssh_runner_manager_extended.py` (1), `tests/unit/ui/test_tui_runner.py` (1), `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` (1), `tests/unit/websocket/test_service_ping_manager.py` (1).
  - Acceptance: Same as T006.
  - Verification: VC-P on `tests/unit/web_portal/test_portal_graceful_shutdown.py`.

- [ ] **T013** Repair slice R08, packet capture. `[FR-004, FR-005]` Status: open. Depends on T004.
  - Paths: `tests/unit/prod_readiness/standalone/operations/execution/capture/test_packet_capture.py` (14).
  - Acceptance: Same as T006.
  - Verification: VC-P on the same path.

- [ ] **T014** Repair slice R09, firmware upgraders. `[FR-004, FR-005]` Status: open. Depends on T004.
  - Paths: `tests/unit/prod_readiness/standalone/operations/execution/firmware/test_bulk_ap_upgrader.py` (11), `tests/unit/prod_readiness/standalone/operations/execution/firmware/test_org_ap_upgrader.py` (5), `tests/unit/prod_readiness/operations/execution/firmware/upgraders/manager/platform/test_firmware_manager_ssr.py` (1).
  - Acceptance: Same as T006.
  - Verification: VC-P on `tests/unit/prod_readiness/standalone/operations/execution/firmware/test_bulk_ap_upgrader.py`.

- [ ] **T015** Repair slice R10, SSID templates. `[FR-004, FR-005]` Status: open. Depends on T004.
  - Paths: `tests/unit/prod_readiness/standalone/operations/execution/ssid/test_ssid_template_consolidation.py` (27).
  - Acceptance: Same as T006. Split the work into two pull requests when the file exceeds 400 changed lines.
  - Verification: VC-P on the same path.

## Phase 4: Retire repaired entries

- [ ] **T016** Remove retired entries after the last repair slice. `[FR-003, FR-013]` Status: open. Depends on T006 to T015.
  - Paths: `.github/test-quality-baseline.json`.
  - Acceptance: The weak-zero entry count equals 129. The 129 remaining entries are detector gaps. Other rules keep their entries.
  - Verification: VC-A.

## Phase 5: Final gates and merge

- [ ] **T-LOCAL-GATES** Run every local gate for each changed file. `[FR-011]` Status: open.
  - Commands:
    - VC-G, then VC-P on each changed test file.
    - `python -m ruff check .`. Expect `All checks passed`.
    - `python -m black --check .`. Expect no file to change.
    - `python -m mypy $MYPY_PATHS --config-file pyproject.toml`. Read `MYPY_PATHS` from `.github/workflows/ci.yml`.
    - `symbol-diff --base origin/main <file>`. Expect `no module-level name changed`.
    - VC-B, and VC-A before push.
  - Acceptance: Each command exits 0. The pull request body lists each result. A repaired test shows its mutation-control result.
  - Verification: VC-B.

- [ ] **T-PR** Open one pull request per slice. `[FR-009, FR-010]` Status: open.
  - Commit: a Conventional Commits subject, such as `test(export): assert the template failure path`. Branch: `test/2711-<slice-slug>`.
  - Body: `Part of #2711` for each slice. Only the final pull request uses `Closes #2711`. Include the changed-file list and the local gate results.
  - Acceptance: The title passes the Conventional Commits check. The file overlap check finds no open pull request that touches the same file.
  - Caution: A `Closes #2711` line in an early pull request closes the umbrella issue at merge. The owner can reopen it.
  - Verification: VC-B on the pull request branch.

- [ ] **T-REMOTE-CI** Watch the remote checks. `[FR-012]` Status: open.
  - Acceptance: The job `Test quality ratchet (gate)` reports success. CodeQL reports success before the `auto-merge` label is added.
  - Verification: VC-A on the pull request head.

- [ ] **T-MERGE** Merge each slice in serial order. `[FR-013]` Status: open. Runs only after T-REMOTE-CI passes and the orchestrator authorizes the merge.
  - Acceptance: One squash commit lands on `main`. The main `Quality Gates` run passes. The branch and the worktree are removed. The final pull request closes #2711 only when SC-003 holds.
  - Verification: VC-A on the merged `main`.
