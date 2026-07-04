---

description: "Task list for feature 1009-compliance-backlog-remediation"
---

# Tasks: Compliance Backlog Remediation

**Feature branch**: `1009-compliance-backlog-remediation`
**Input**: Design documents from `specs/1009-compliance-backlog-remediation/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/per-file-pr.md`, `contracts/backlog-refresh.md`, `contracts/done-definition.md`, `quickstart.md`
**Backlog source of truth**: `data/compliance_backlog.tsv` (99 files, ranked by `Total` desc; ties broken by `critical` desc, then `high` desc, then `score` asc)

---

## Serial Execution Reminder

**NO `[P]` MARKERS APPEAR IN THIS FILE — AND THAT IS INTENTIONAL.**

This feature is strictly serial per `plan.md`:

- Exactly one remediation PR (`RemediationPR` in `data-model.md`) may be in the `opened` or `gates_green` state at any given moment.
- Only one T-task in this list may be `in progress` at a time. The next T-task MUST NOT start until the previous PR is `squash_merged` (see `contracts/done-definition.md`).
- Parallelization is a merge-conflict and analyzer-drift risk that this feature explicitly rejects. Do not attempt to "fan out" tasks even if capacity is available.
- All 13 CI gates (Ruff, Black, mypy strict, Pylint, pytest coverage, Bandit, Vulture, pydocstyle, Interrogate, pip-audit, Radon, CodeQL, E2E smoke) MUST be green before merge. `--admin` merge MUST NOT be used to bypass a red gate.

---

## Refresh-Cadence Gate

Every 5 successful merges, backlog rank drift MUST be reconciled before continuing.

- Refresh checkpoints `R05`, `R10`, `R15`, ..., `R95` are interleaved after `T005`, `T010`, `T015`, ..., `T095` respectively.
- At each `Rxx` checkpoint:
  1. Re-run the full-repo analyzer per `contracts/backlog-refresh.md`.
  2. Regenerate `data/compliance_backlog.tsv`.
  3. Compare the new top of the backlog against the current position in this list.
  4. If ranks 6..99 have shifted, the remaining T-tasks below the checkpoint MUST be reordered in place to match the new ranking (task IDs stay stable; the file paths, grades, scores, and Total values are rewritten to the fresh values). Record the reorder as a commit on the feature branch.
  5. If ranks 6..99 are unchanged (or only files already merged have dropped off), continue without reordering.
- A refresh checkpoint is NOT a PR. It is a backlog bookkeeping step against `data/compliance_backlog.tsv` on the feature branch.

---

## Format: `[ID] Description`

- **[ID]**: Sequential task ID. `T001..T099` are per-file remediation PRs (in backlog rank order). `R05..R95` are backlog refresh checkpoints. `T100` is the final success gate.
- Each `Txxx` task references the file's Windows-style path from the backlog verbatim.
- Each `Txxx` task references `contracts/per-file-pr.md` for the full 7-step recipe rather than re-listing it.
- **Target**: A+ (100.0). **Acceptable floor**: A (>=94.0). Anything below 94.0 is a merge blocker (see `contracts/done-definition.md`).
- **Branch name pattern**: `refactor/compliance-<rank-3-digit>-<slug>` where `<slug>` is the file's stem, with non-`[A-Za-z0-9_-]` characters replaced by `_`. For `__init__.py` files, `<slug>` is the parent package name.

---

## Phase 1: Provenance Gate (T001 prerequisite ONLY)

**Purpose**: Resolve the untracked-file question for rank 1 before any refactor begins.

- [ ] **GATE-T001-PROVENANCE** Before starting T001, confirm the FR-015 / `research.md` R6 / `quickstart.md` provenance decision for `src\mist_ideas_analyzer\__init__.py` has been recorded and executed. This file is currently untracked in git (see repo `git status`). The three options from R6 are: (a) commit as-is under the current authorship, (b) rewrite/replace under a documented authorship, or (c) delete and remove from the backlog entirely. Do **NOT** open the T001 branch until one of (a)/(b)/(c) is recorded in the feature branch's history. If option (c) is chosen, T001 is deleted from this task list and every subsequent task shifts up by one rank (with branch names re-derived accordingly) via an `R00` refresh commit.

---

## Phase 2: Per-File Remediation PRs (Serial, T001..T099)

Follow `contracts/per-file-pr.md` for each task. Every task below expands to: baseline scan -> branch -> refactor to A+/100 (floor A/>=94) -> verification scan -> 4 local gates -> push -> 13 CI gates -> `gh pr merge --squash --delete-branch`.

- [ ] T001 Refactor `src\mist_ideas_analyzer\__init__.py` (rank 1, current F/54.0, 45 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-001-mist_ideas_analyzer`. Follow `contracts/per-file-pr.md`. **Blocked by GATE-T001-PROVENANCE.**
- [ ] T002 Refactor `src\site\site_config_manager.py` (rank 2, current D/66.0, 29 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-002-site_config_manager`. Follow `contracts/per-file-pr.md`.
- [ ] T003 Refactor `src\analytics\zone_analyzer.py` (rank 3, current D/65.0, 26 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-003-zone_analyzer`. Follow `contracts/per-file-pr.md`.
- [ ] T004 Refactor `src\inventory\csv_comparator.py` (rank 4, current D/64.0, 26 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-004-csv_comparator`. Follow `contracts/per-file-pr.md`.
- [ ] T005 Refactor `src\device\prompt_utils.py` (rank 5, current D/66.0, 25 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-005-prompt_utils`. Follow `contracts/per-file-pr.md`.

- [ ] **R05** Backlog Refresh Checkpoint (after 5 merges). Follow `contracts/backlog-refresh.md`: rerun the full-repo analyzer, regenerate `data/compliance_backlog.tsv`, and if ranks 6..99 have shifted, reorder T006..T099 in this file to match the new ranking (task IDs stay stable; paths/grades/scores/totals are rewritten).

- [ ] T006 Refactor `src\gateway\template_config.py` (rank 6, current D/65.0, 25 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-006-template_config`. Follow `contracts/per-file-pr.md`.
- [ ] T007 Refactor `src\reports\e911_bssid.py` (rank 7, current D/65.0, 23 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-007-e911_bssid`. Follow `contracts/per-file-pr.md`.
- [X] T008 Refactor `src\maps\launcher\_viewer_drawing.py` (rank 8, current C/73.0, 22 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-008-_viewer_drawing`. Follow `contracts/per-file-pr.md`.
- [ ] T009 Refactor `src\maps\_maps_wizard.py` (rank 9, current D/64.0, 22 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-009-_maps_wizard`. Follow `contracts/per-file-pr.md`.
- [ ] T010 Refactor `src\maps\launcher\_viewer_refresh.py` (rank 10, current D+/67.0, 21 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-010-_viewer_refresh`. Follow `contracts/per-file-pr.md`.

- [ ] **R10** Backlog Refresh Checkpoint (after 10 merges). Follow `contracts/backlog-refresh.md`: rerun the full-repo analyzer, regenerate `data/compliance_backlog.tsv`, and reorder remaining tasks if ranks 11..99 have shifted.

- [ ] T011 Refactor `src\firmware\bulk_switch_upgrader.py` (rank 11, current D+/69.0, 21 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-011-bulk_switch_upgrader`. Follow `contracts/per-file-pr.md`.
- [ ] T012 Refactor `src\maps\launcher\_viewer_ui.py` (rank 12, current C-/72.0, 21 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-012-_viewer_ui`. Follow `contracts/per-file-pr.md`.
- [ ] T013 Refactor `src\ssh\batch\interactive_batch_executor.py` (rank 13, current D+/69.0, 19 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-013-interactive_batch_executor`. Follow `contracts/per-file-pr.md`.
- [ ] T014 Refactor `src\websocket\service_ping_discovery.py` (rank 14, current D/65.0, 19 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-014-service_ping_discovery`. Follow `contracts/per-file-pr.md`.
- [ ] T015 Refactor `src\device\virtual_chassis.py` (rank 15, current C-/70.0, 18 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-015-virtual_chassis`. Follow `contracts/per-file-pr.md`.

- [ ] **R15** Backlog Refresh Checkpoint (after 15 merges). Follow `contracts/backlog-refresh.md`: rerun the full-repo analyzer, regenerate `data/compliance_backlog.tsv`, and reorder remaining tasks if ranks 16..99 have shifted.

- [ ] T016 Refactor `src\gateway\wan2_migration_manager.py` (rank 16, current D/66.0, 18 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-016-wan2_migration_manager`. Follow `contracts/per-file-pr.md`.
- [ ] T017 Refactor `src\maps\launcher\_viewer_url_switch.py` (rank 17, current C-/71.0, 17 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-017-_viewer_url_switch`. Follow `contracts/per-file-pr.md`.
- [ ] T018 Refactor `src\maps\_maps_coverage.py` (rank 18, current D/63.0, 16 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-018-_maps_coverage`. Follow `contracts/per-file-pr.md`.
- [ ] T019 Refactor `src\inventory\org_device_inventory_msp.py` (rank 19, current D+/68.0, 16 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-019-org_device_inventory_msp`. Follow `contracts/per-file-pr.md`.
- [ ] T020 Refactor `src\wan_vpn_builder.py` (rank 20, current D+/69.0, 16 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-020-wan_vpn_builder`. Follow `contracts/per-file-pr.md`.

- [ ] **R20** Backlog Refresh Checkpoint (after 20 merges). Follow `contracts/backlog-refresh.md`: rerun the full-repo analyzer, regenerate `data/compliance_backlog.tsv`, and reorder remaining tasks if ranks 21..99 have shifted.

- [ ] T021 Refactor `src\site\address_audit\audit_engine.py` (rank 21, current C-/72.0, 15 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-021-audit_engine`. Follow `contracts/per-file-pr.md`.
- [ ] T022 Refactor `src\export\site_export_utils.py` (rank 22, current D+/67.0, 15 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-022-site_export_utils`. Follow `contracts/per-file-pr.md`.
- [ ] T023 Refactor `src\ssid_consolidation\_ssid_template_phase1.py` (rank 23, current D+/68.0, 15 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-023-_ssid_template_phase1`. Follow `contracts/per-file-pr.md`.
- [ ] T024 Refactor `src\ssh\ssh_runner.py` (rank 24, current D+/68.0, 14 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-024-ssh_runner`. Follow `contracts/per-file-pr.md`.
- [ ] T025 Refactor `src\analytics\site_analytics_configurator.py` (rank 25, current C-/70.0, 14 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-025-site_analytics_configurator`. Follow `contracts/per-file-pr.md`.

- [ ] **R25** Backlog Refresh Checkpoint (after 25 merges). Follow `contracts/backlog-refresh.md`: rerun the full-repo analyzer, regenerate `data/compliance_backlog.tsv`, and reorder remaining tasks if ranks 26..97 have shifted.

- [ ] T026 Refactor `src\db\redis_writer.py` (rank 26, current C-/70.0, 14 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-026-redis_writer`. Follow `contracts/per-file-pr.md`.
- [ ] T027 Refactor `src\maps\_maps_testing.py` (rank 27, current C-/70.0, 14 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-027-_maps_testing`. Follow `contracts/per-file-pr.md`.
- [ ] T028 Refactor `src\websocket\service_ping_manager.py` (rank 28, current C-/70.0, 14 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-028-service_ping_manager`. Follow `contracts/per-file-pr.md`.
- [ ] T029 Refactor `src\maps\_plotly_viewer.py` (rank 29, current D+/67.0, 13 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-029-_plotly_viewer`. Follow `contracts/per-file-pr.md`.
- [ ] T030 Refactor `src\gateway\wan_probe_device_override_manager.py` (rank 30, current C-/71.0, 13 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-030-wan_probe_device_override_manager`. Follow `contracts/per-file-pr.md`.

- [ ] **R30** Backlog Refresh Checkpoint (after 30 merges). Follow `contracts/backlog-refresh.md`: rerun the full-repo analyzer, regenerate `data/compliance_backlog.tsv`, and reorder remaining tasks if ranks 31..97 have shifted.

- [ ] T031 Refactor `src\capture\multi_ap_scan_workflow.py` (rank 31, current C+/77.0, 13 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-031-multi_ap_scan_workflow`. Follow `contracts/per-file-pr.md`.
- [ ] T032 Refactor `src\maps\launcher\_viewer_clone.py` (rank 32, current C+/77.0, 13 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-032-_viewer_clone`. Follow `contracts/per-file-pr.md`.
- [ ] T033 Refactor `src\ssh\batch\multi_host_runner.py` (rank 33, current C/73.0, 12 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-033-multi_host_runner`. Follow `contracts/per-file-pr.md`.
- [ ] T034 Refactor `src\db\arango_writer.py` (rank 34, current C/75.0, 12 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-034-arango_writer`. Follow `contracts/per-file-pr.md`.
- [ ] T035 Refactor `src\ssh\ssh_runner_manager.py` (rank 35, current C/75.0, 12 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-035-ssh_runner_manager`. Follow `contracts/per-file-pr.md`.

- [ ] **R35** Backlog Refresh Checkpoint (after 35 merges). Follow `contracts/backlog-refresh.md`: rerun the full-repo analyzer, regenerate `data/compliance_backlog.tsv`, and reorder remaining tasks if ranks 36..97 have shifted.

- [ ] T036 Refactor `src\maps\_maps_backup.py` (rank 36, current D/65.0, 11 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-036-_maps_backup`. Follow `contracts/per-file-pr.md`.
- [ ] T037 Refactor `src\ssh\runtime\app_runner.py` (rank 37, current D+/68.0, 11 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-037-app_runner`. Follow `contracts/per-file-pr.md`.
- [ ] T038 Refactor `src\gateway\gateway_export_utils.py` (rank 38, current D+/69.0, 11 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-038-gateway_export_utils`. Follow `contracts/per-file-pr.md`.
- [ ] T039 Refactor `src\troubleshooting\marvis_troubleshoot_utils.py` (rank 39, current C-/72.0, 11 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-039-marvis_troubleshoot_utils`. Follow `contracts/per-file-pr.md`.
- [ ] T040 Refactor `src\capture\packet_capture_download.py` (rank 40, current C/75.0, 11 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-040-packet_capture_download`. Follow `contracts/per-file-pr.md`.

- [ ] **R40** Backlog Refresh Checkpoint (after 40 merges). Follow `contracts/backlog-refresh.md`: rerun the full-repo analyzer, regenerate `data/compliance_backlog.tsv`, and reorder remaining tasks if ranks 41..97 have shifted.

- [ ] T041 Refactor `src\inventory\org_device_inventory_summary.py` (rank 41, current C+/79.0, 10 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-041-org_device_inventory_summary`. Follow `contracts/per-file-pr.md`.
- [ ] T042 Refactor `src\gateway\gateway_stats_exporter.py` (rank 42, current C/75.0, 9 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-042-gateway_stats_exporter`. Follow `contracts/per-file-pr.md`.
- [ ] T043 Refactor `src\maps\plotly_map_figure_builder.py` (rank 43, current C/75.0, 9 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-043-plotly_map_figure_builder`. Follow `contracts/per-file-pr.md`.
- [ ] T044 Refactor `src\analytics\site_inventory_health_analyzer.py` (rank 44, current C+/78.0, 9 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-044-site_inventory_health_analyzer`. Follow `contracts/per-file-pr.md`.
- [ ] T045 Refactor `src\marvis\marvis_utils.py` (rank 45, current C+/78.0, 9 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-045-marvis_utils`. Follow `contracts/per-file-pr.md`.

- [ ] **R45** Backlog Refresh Checkpoint (after 45 merges). Follow `contracts/backlog-refresh.md`: rerun the full-repo analyzer, regenerate `data/compliance_backlog.tsv`, and reorder remaining tasks if ranks 46..97 have shifted.

- [ ] T046 Refactor `src\websocket\manager.py` (rank 46, current C+/78.0, 9 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-046-manager`. Follow `contracts/per-file-pr.md`.
- [ ] T047 Refactor `src\maps\launcher\_viewer_site_switch.py` (rank 47, current B/83.0, 9 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-047-_viewer_site_switch`. Follow `contracts/per-file-pr.md`.
- [ ] T048 Refactor `src\websocket\polling\completion_detector.py` (rank 48, current B/84.0, 9 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-048-completion_detector`. Follow `contracts/per-file-pr.md`.
- [X] T049 Refactor `src\ssh\batch\host_runner.py` (rank 49, current C-/72.0, 8 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-049-host_runner`. Follow `contracts/per-file-pr.md`.
- [ ] T050 Refactor `src\troubleshooting\interactive_test_runner.py` (rank 50, current C/75.0, 8 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-050-interactive_test_runner`. Follow `contracts/per-file-pr.md`.

- [ ] **R50** Backlog Refresh Checkpoint (after 50 merges). Follow `contracts/backlog-refresh.md`: rerun the full-repo analyzer, regenerate `data/compliance_backlog.tsv`, and reorder remaining tasks if ranks 51..97 have shifted.

- [ ] T051 Refactor `src\websocket\diagnostics\arp_executor.py` (rank 51, current B-/80.0, 8 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-051-arp_executor`. Follow `contracts/per-file-pr.md`.
- [ ] T052 Refactor `src\site\address_audit\address_resolver.py` (rank 52, current B/86.0, 8 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-052-address_resolver`. Follow `contracts/per-file-pr.md`.
- [ ] T053 Refactor `src\websocket\commands.py` (rank 53, current B/86.0, 8 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-053-commands`. Follow `contracts/per-file-pr.md`.
- [ ] T054 Refactor `src\refactors\serial_cc\security_events.py` (rank 54, current C/75.0, 7 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-054-security_events`. Follow `contracts/per-file-pr.md`.
- [ ] T055 Refactor `src\audit\analyzer.py` (rank 55, current B-/80.0, 7 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-055-analyzer`. Follow `contracts/per-file-pr.md`.

- [ ] **R55** Backlog Refresh Checkpoint (after 55 merges). Follow `contracts/backlog-refresh.md`: rerun the full-repo analyzer, regenerate `data/compliance_backlog.tsv`, and reorder remaining tasks if ranks 56..97 have shifted.

- [ ] T056 Refactor `src\gateway\device_template_cloner.py` (rank 56, current B/84.0, 7 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-056-device_template_cloner`. Follow `contracts/per-file-pr.md`.
- [ ] T057 Refactor `src\maps\_maps_clone.py` (rank 57, current B/84.0, 7 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-057-_maps_clone`. Follow `contracts/per-file-pr.md`.
- [ ] T058 Refactor `src\ssid_consolidation\_ssid_template_phase2.py` (rank 58, current B/84.0, 7 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-058-_ssid_template_phase2`. Follow `contracts/per-file-pr.md`.
- [ ] T059 Refactor `src\refactors\serial_cc\switch_vc_stats.py` (rank 59, current B/85.0, 7 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-059-switch_vc_stats`. Follow `contracts/per-file-pr.md`.
- [ ] T060 Refactor `src\api\tenant_fetch.py` (rank 60, current B+/88.0, 7 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-060-tenant_fetch`. Follow `contracts/per-file-pr.md`.

- [ ] **R60** Backlog Refresh Checkpoint (after 60 merges). Follow `contracts/backlog-refresh.md`: rerun the full-repo analyzer, regenerate `data/compliance_backlog.tsv`, and reorder remaining tasks if ranks 61..97 have shifted.

- [ ] T061 Refactor `src\ui\layout\results_grid_builder.py` (rank 61, current B+/88.0, 7 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-061-results_grid_builder`. Follow `contracts/per-file-pr.md`.
- [ ] T062 Refactor `src\maps\plotly_heatmap_renderer.py` (rank 62, current C/73.0, 6 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-062-plotly_heatmap_renderer`. Follow `contracts/per-file-pr.md`.
- [ ] T063 Refactor `src\utils\rate_limiting.py` (rank 63, current C/75.0, 6 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-063-rate_limiting`. Follow `contracts/per-file-pr.md`.
- [ ] T064 Refactor `src\export\site_insights\device_metric_operation.py` (rank 64, current C+/79.0, 6 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-064-device_metric_operation`. Follow `contracts/per-file-pr.md`.
- [ ] T065 Refactor `src\websocket\diagnostics\ping_executor.py` (rank 65, current C+/79.0, 6 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-065-ping_executor`. Follow `contracts/per-file-pr.md`.

- [ ] **R65** Backlog Refresh Checkpoint (after 65 merges). Follow `contracts/backlog-refresh.md`: rerun the full-repo analyzer, regenerate `data/compliance_backlog.tsv`, and reorder remaining tasks if ranks 66..97 have shifted.

- [ ] T066 Refactor `src\maps\_maps_matplotlib.py` (rank 66, current B-/82.0, 6 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-066-_maps_matplotlib`. Follow `contracts/per-file-pr.md`.
- [ ] T067 Refactor `src\maps\plotly_map_callback_manager.py` (rank 67, current B-/82.0, 6 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-067-plotly_map_callback_manager`. Follow `contracts/per-file-pr.md`.
- [ ] T068 Refactor `src\audit\time_parser.py` (rank 68, current B/85.0, 6 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-068-time_parser`. Follow `contracts/per-file-pr.md`.
- [ ] T069 Refactor `src\export\wifi_clients_exporter.py` (rank 69, current B/86.0, 6 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-069-wifi_clients_exporter`. Follow `contracts/per-file-pr.md`.
- [ ] T070 Refactor `src\ssh\connection\connector.py` (rank 70, current B/86.0, 6 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-070-connector`. Follow `contracts/per-file-pr.md`.

- [ ] **R70** Backlog Refresh Checkpoint (after 70 merges). Follow `contracts/backlog-refresh.md`: rerun the full-repo analyzer, regenerate `data/compliance_backlog.tsv`, and reorder remaining tasks if ranks 71..97 have shifted.

- [ ] T071 Refactor `src\site\address_audit\ui_geocoder.py` (rank 71, current B+/88.0, 6 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-071-ui_geocoder`. Follow `contracts/per-file-pr.md`.
- [ ] T072 Refactor `src\ssh\shell_execution\shell_executor.py` (rank 72, current B+/88.0, 6 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-072-shell_executor`. Follow `contracts/per-file-pr.md`.
- [ ] T073 Refactor `src\maps\_flask_viewer.py` (rank 73, current C/74.0, 5 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-073-_flask_viewer`. Follow `contracts/per-file-pr.md`.
- [ ] T074 Refactor `src\org_data_collector.py` (rank 74, current B-/82.0, 5 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-074-org_data_collector`. Follow `contracts/per-file-pr.md`.
- [ ] T075 Refactor `src\websocket\polling\result_combiner.py` (rank 75, current B/83.0, 5 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-075-result_combiner`. Follow `contracts/per-file-pr.md`.

- [ ] **R75** Backlog Refresh Checkpoint (after 75 merges). Follow `contracts/backlog-refresh.md`: rerun the full-repo analyzer, regenerate `data/compliance_backlog.tsv`, and reorder remaining tasks if ranks 76..97 have shifted.

- [ ] T076 Refactor `src\db\router.py` (rank 76, current B/84.0, 5 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-076-router`. Follow `contracts/per-file-pr.md`.
- [ ] T077 Refactor `src\ssid_consolidation\_ssid_template_phase3.py` (rank 77, current B/86.0, 5 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-077-_ssid_template_phase3`. Follow `contracts/per-file-pr.md`.
- [ ] T078 Refactor `src\ssid_consolidation\_ssid_template_phase45.py` (rank 78, current B/86.0, 5 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-078-_ssid_template_phase45`. Follow `contracts/per-file-pr.md`.
- [ ] T079 Refactor `src\refactors\serial_cc\start_site_client_capture_wireless.py` (rank 79, current B+/88.0, 5 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-079-start_site_client_capture_wireless`. Follow `contracts/per-file-pr.md`.
- [ ] T080 Refactor `src\refactors\serial_cc\start_site_scan_capture.py` (rank 80, current B+/88.0, 5 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-080-start_site_scan_capture`. Follow `contracts/per-file-pr.md`.

- [ ] **R80** Backlog Refresh Checkpoint (after 80 merges). Follow `contracts/backlog-refresh.md`: rerun the full-repo analyzer, regenerate `data/compliance_backlog.tsv`, and reorder remaining tasks if ranks 81..97 have shifted.

- [ ] T081 Refactor `src\ui\execution\item_executor.py` (rank 81, current B+/88.0, 5 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-081-item_executor`. Follow `contracts/per-file-pr.md`.
- [ ] T082 Refactor `src\bootstrap\dependency_check.py` (rank 82, current A-/90.0, 5 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-082-dependency_check`. Follow `contracts/per-file-pr.md`.
- [ ] T083 Refactor `src\websocket\polling\message_router.py` (rank 83, current A-/90.0, 5 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-083-message_router`. Follow `contracts/per-file-pr.md`.
- [ ] T084 Refactor `src\export\device_events_52w_exporter.py` (rank 84, current B/84.0, 4 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-084-device_events_52w_exporter`. Follow `contracts/per-file-pr.md`.
- [ ] T085 Refactor `src\export\site_insights_exporter.py` (rank 85, current B/84.0, 4 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-085-site_insights_exporter`. Follow `contracts/per-file-pr.md`.

- [ ] **R85** Backlog Refresh Checkpoint (after 85 merges). Follow `contracts/backlog-refresh.md`: rerun the full-repo analyzer, regenerate `data/compliance_backlog.tsv`, and reorder remaining tasks if ranks 86..97 have shifted.

- [ ] T086 Refactor `src\maps\plotly_map_templates.py` (rank 86, current B/84.0, 4 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-086-plotly_map_templates`. Follow `contracts/per-file-pr.md`.
- [ ] T087 Refactor `src\bootstrap\package_installer.py` (rank 87, current B+/89.0, 4 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-087-package_installer`. Follow `contracts/per-file-pr.md`.
- [ ] T088 Refactor `src\refactors\serial_cc\site_client_insights.py` (rank 88, current B+/89.0, 4 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-088-site_client_insights`. Follow `contracts/per-file-pr.md`.
- [ ] T089 Refactor `src\websocket\polling\result_collector.py` (rank 89, current B+/89.0, 4 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-089-result_collector`. Follow `contracts/per-file-pr.md`.
- [ ] T090 Refactor `src\wan_hub_group_manager.py` (rank 90, current B+/88.0, 3 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-090-wan_hub_group_manager`. Follow `contracts/per-file-pr.md`.

- [ ] **R90** Backlog Refresh Checkpoint (after 90 merges). Follow `contracts/backlog-refresh.md`: rerun the full-repo analyzer, regenerate `data/compliance_backlog.tsv`, and reorder remaining tasks if ranks 91..97 have shifted.

- [ ] T091 Refactor `src\export\site_insights\site_metric_operation.py` (rank 91, current A-/91.0, 3 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-091-site_metric_operation`. Follow `contracts/per-file-pr.md`.
- [ ] T092 Refactor `src\maps\plotly_map_serializer.py` (rank 92, current B+/88.0, 2 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-092-plotly_map_serializer`. Follow `contracts/per-file-pr.md`.
- [ ] T093 Refactor `src\capture\org_capture_workflow.py` (rank 93, current A-/91.0, 2 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-093-org_capture_workflow`. Follow `contracts/per-file-pr.md`.
- [ ] T094 Refactor `src\capture\site_capture_loop.py` (rank 94, current A-/91.0, 2 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-094-site_capture_loop`. Follow `contracts/per-file-pr.md`.
- [ ] T095 Refactor `src\db\retention.py` (rank 95, current A-/91.0, 2 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-095-retention`. Follow `contracts/per-file-pr.md`.

- [ ] **R95** Backlog Refresh Checkpoint (after 95 merges). Follow `contracts/backlog-refresh.md`: rerun the full-repo analyzer, regenerate `data/compliance_backlog.tsv`, and reorder remaining tasks if ranks 96..97 have shifted.

- [ ] T096 Refactor `src\gateway\overrides\_deps.py` (rank 96, current A-/91.0, 2 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-096-_deps`. Follow `contracts/per-file-pr.md`.
- [ ] T097 Refactor `src\maps\_maps_utils.py` (rank 97, current A-/91.0, 2 issues) to A+/100.0 (floor A/>=94). Branch: `refactor/compliance-097-_maps_utils`. Follow `contracts/per-file-pr.md`.

---

## Phase 3: Success Gate

- [ ] **T100** Rerun the full-repo compliance analyzer (`py -m tools.compliance_analyzer -o compliance_report.md -q`) and verify all three exit conditions:
  1. Overall repo grade is `>=A` (score `>=94.0`).
  2. Every path that appeared in `data/compliance_backlog.tsv` at any point in this feature is now `>=A/94.0` on a fresh scan.
  3. No file that was already at `A+/100.0` at the start of this feature has regressed below `A/94.0`.

  If any of the three conditions fails, identify the offending file(s), append them as new T-tasks (`T101`, `T102`, ...) using the same per-file recipe, and rerun `T100` until all three pass. Only then may the feature be closed and the branch merged.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Provenance Gate)** MUST complete before T001 begins. No other task is blocked by Phase 1.
- **Phase 2 (T001..T099 + R05..R95)** is strictly serial. Each `Txxx` blocks the next `Txxx`. Each `Rxx` blocks every `Txxx` that follows it in the list until the refresh is reconciled (see Refresh-Cadence Gate above).
- **Phase 3 (T100)** MUST NOT start until T099 (or the final surviving T-task after any R-refresh reorderings) is `squash_merged`.

### Task-Level Dependencies

- T001 -> T002 -> T003 -> T004 -> T005 -> R05 -> T006 -> ... -> T095 -> R95 -> T096 -> T097 -> T098 -> T099 -> T100.
- No task in this list may be batched, parallelized, or reordered locally without a corresponding `Rxx` refresh checkpoint acknowledging the reorder.

### No Parallel Opportunities

Deliberately none. See Serial Execution Reminder above.

---

## Implementation Strategy

### Cadence (per `plan.md`)

1. Pick the top unresolved row of `data/compliance_backlog.tsv`.
2. Open exactly one PR per `contracts/per-file-pr.md`.
3. Wait for all 13 CI gates to be green.
4. Squash-merge with branch delete.
5. Every 5 merges, refresh the backlog (`Rxx`) and reorder if needed.
6. Repeat until T099.
7. Run T100 (success gate). If green, close the feature.

### MVP Definition

There is no partial MVP for this feature. The "product" is the feature-complete Phase 3 success gate (T100 green). Partial progress delivers per-file value but the feature is not "done" until T100 passes.

---

## Notes

- No `[P]` marker appears anywhere in this list. Adding one is a spec violation.
- Task IDs are stable across refresh reorderings; the *content* of `Txxx` (path/grade/score/total/branch name) is what gets rewritten when `Rxx` detects rank drift.
- Windows-style paths (`src\...\...`) are preserved verbatim from `data/compliance_backlog.tsv` per the user's instruction. Convert to POSIX only at command-invocation time if a specific tool requires it.
- Commit after each merge; refresh checkpoints commit their regenerated `data/compliance_backlog.tsv` on the feature branch.
- `--admin` merge is NOT a bypass for red gates. Any red gate is a merge blocker per `contracts/done-definition.md`.
- Suppression markers (`# noqa: STRUCT-*`, `# noqa: CONV-*`, `# type: ignore`, `# pragma: no cover`) MUST NOT be introduced by any task in this list.
