# Research: Split tests/unit into domain packages

## 1. Scope And Method

The baseline is GitHub `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, read on 2026-11-26. The local checkout is at the same commit. Remote evidence outranks local evidence (brief rule 5).

Read in full: `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, the four Spec Kit templates, `.specify/scripts/powershell/spec-route.ps1`, the legacy `spec.md`, `plan.md`, `tasks.md`, `design/quickstart.md`, and `design/checklists/requirements.md`.

Read in part: legacy `design/research.md` (2,039 lines) by heading outline, lines 213 to 265, and lines 1931 to 2039. Legacy `design/standalone-test-map.md` (1,222 lines) by heading outline, lines 693 to 760, lines 848 to 880, and lines 1190 to 1222. The unread lines hold per-row claims. This record does not carry those rows forward. It checks the outcome on `main` instead.

Reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`: its file list and line counts were read. Its content was not copied.

Not read in this run: `documentation/quality-gates.md`, `architecture.md`, `development-setup.md`, `container-deployment.md`, and `operator-guide.md`. The `HEAD` reference inventory in section 6 shows that none of these files names a `tests/unit` path. The Mist API OpenAPI file and the `mistapi` SDK do not apply, because no API call changes.

No skill was loaded. No Podman, storage, or Juniper device question applies. No `web_fetch` call was made.

## 2. Remote Verification

Each row is one remote check. The count of 44 rows matches `remote_checks` in the STATUS file. Result values are `present`, `absent`, `partial`, or `stale`. Line numbers come from decoded remote files on `main`.

| ID | Claim | Path | Ref | Blob or tree SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Root `tests/unit/` holds 50 distinct direct children | `tests/unit` | main | tree `fc987db0` | partial | 0 |
| RC-02 | Root marker exists | `tests/unit/__init__.py` | main | blob `e69de29b` | present | 0 |
| RC-03 | Container `config` exists | `tests/unit/config` | main | tree `91225209` | present | 0 |
| RC-04 | Container `marvis` exists | `tests/unit/marvis` | main | tree `b869e97e` | present | 0 |
| RC-05 | Container `maps` exists | `tests/unit/maps` | main | tree `d6b80fc6` | present | 0 |
| RC-06 | Container `prod_readiness` exists | `tests/unit/prod_readiness` | main | tree `319fea9c` | present | 0 |
| RC-07 | Juniper RMA leftover at root (22 files) | `tests/unit/juniper_rma` | main | tree `30dcceed` | partial | 0 |
| RC-08 | `upgrade_portal` remains at root (176 files) | `tests/unit/upgrade_portal` | main | tree `4a51282e` | present | 0 |
| RC-09 | Analytics module remains at source | `tests/unit/analytics/test_insight_metrics_utils.py` | main | blob `7fedd110` | present | 0 |
| RC-10 | `output_defaults` package remains at source | `tests/unit/container/output_defaults` | main | tree `766d1a73` | present | 0 |
| RC-11 | `test_session.py` uses package-relative imports | `tests/unit/container/output_defaults/test_session.py` | main | blob `4c4bc48b` | present | 15 |
| RC-12 | Packet capture module at destination | `tests/unit/prod_readiness/standalone/operations/execution/capture/test_packet_capture.py` | main | blob `e1a369fd` | present | 0 |
| RC-13 | Retention module at destination | `tests/unit/config/foundation/persistence/storage/db/test_retention_redis_scan.py` | main | blob `e9643340` | present | 0 |
| RC-14 | Cisco converter test at destination | `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py` | main | blob `31a84e37` | present | 0 |
| RC-15 | RMA fixture loader at destination | `tests/unit/prod_readiness/operations/exporting/juniper_rma/fixtures/read_replies.py` | main | blob `d08ad387` | present | 0 |
| RC-16 | Fast-mode module left the root | `tests/unit/test_fast_mode_flag.py` | main | none | absent | 0 |
| RC-17 | Credential-redaction module left the root | `tests/unit/security/test_credential_redaction.py` | main | none | absent | 0 |
| RC-18 | Open PR #4208 adds a root child that is not on main | `tests/unit/wan_performance` | main | none | absent | 0 |
| RC-19 | CI selects `tests/unit` | `.github/workflows/ci.yml` | main | blob `d51efbc1` | present | 263 |
| RC-20 | CI ignores `tests/unit/upgrade_portal` | `.github/workflows/ci.yml` | main | blob `d51efbc1` | present | 264 |
| RC-21 | CI selects `tests/unit/upgrade_portal` | `.github/workflows/ci.yml` | main | blob `d51efbc1` | present | 267 |
| RC-22 | CI runs `tests/unit/scripts/test_script_imports.py` | `.github/workflows/ci.yml` | main | blob `d51efbc1` | present | 303 |
| RC-23 | `testpaths` names `tests/unit/upgrade_portal` | `pyproject.toml` | main | blob `eca34c82` | present | 516 |
| RC-24 | E402 exceptions name root modules | `pyproject.toml` | main | blob `eca34c82` | partial | 269 |
| RC-25 | Instructions name the `upgrade_portal` split path | `.github/copilot-instructions.md` | main | blob `f1ec2a46` | present | 87 |
| RC-26 | Instructions name the output-scan test path | `.github/copilot-instructions.md` | main | blob `f1ec2a46` | present | 255 |
| RC-27 | Quality baseline names 624 `tests/unit/` `file_path` values | `.github/test-quality-baseline.json` | main | blob `512da22b` | present | 0 |
| RC-28 | Process folder baseline exists | `tests/guardrails/process_folder_baseline.json` | main | blob `f3eb8a7b` | present | 0 |
| RC-29 | Move guard exists | `tests/guardrails/test_move_module_guidance.py` | main | blob `ae163b79` | present | 0 |
| RC-30 | Relocation test remains at root | `tests/unit/troubleshooting/test_module_relocation.py` | main | blob `3dfd70f5` | present | 0 |
| RC-31 | Output-scan test remains under `web_portal` | `tests/unit/web_portal/test_output_scan_runtime_files.py` | main | blob `a8e9d4c0` | present | 0 |
| RC-32 | Script import test remains under `scripts` | `tests/unit/scripts/test_script_imports.py` | main | blob `df2c2a7f` | present | 0 |
| RC-33 | Held CLI shell test remains in place | `tests/unit/ssh/test_cli_shell_manager.py` | main | blob `02417ebf` | present | 0 |
| RC-34 | Held 52-week exporter test remains at root | `tests/unit/test_device_events_52w_exporter.py` | main | blob `de5aa5a8` | present | 0 |
| RC-35 | Held WLAN timer test remains in place | `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` | main | blob `e13bf10b` | present | 0 |
| RC-36 | Held backend preservation test remains in place | `tests/unit/db/sle_window_summary/test_backend_preservation.py` | main | blob `38670362` | present | 0 |
| RC-37 | Held data exporter test remains in place | `tests/unit/export/test_data_exporter.py` | main | blob `8e91cbe4` | present | 0 |
| RC-38 | Legacy 4142 record folder exists on main | `specs/numbered/0/0/1/1/3/0/3/2/4142-unit-test-domain-packages` | main | tree `d6bbbbc7` | present | 0 |
| RC-39 | Legacy plan claims 155 root entries | `specs/numbered/0/0/1/1/3/0/3/2/4142-unit-test-domain-packages/plan.md` | main | blob `a0c4045d` | stale | 31 |
| RC-40 | Issue 3519 plan row C-1 records the debt | `specs/numbered/0/0/1/0/3/0/3/4/3519-juniper-rma-correlation/plan.md` | main | blob `030bac7d` | present | 178 |
| RC-41 | Issue 3519 task T054 defers the remediation issue | `specs/numbered/0/0/1/0/3/0/3/4/3519-juniper-rma-correlation/tasks.md` | main | blob `3f00eb4d` | present | 191 |
| RC-42 | Legacy candidate base commit exists | commit `31b752f060d4d10cbe87b5880b071b6570d0b3c9` | commit API | none | present | 0 |
| RC-43 | PR #4358 merge commit exists | commit `2a6a5844698aeb180fea353e0243034890774565` | commit API | none | present | 0 |
| RC-44 | Changelog fragment rule exists | `changelog.d/README.md` | main | blob `fcbde10e` | present | 0 |

Notes on the table:

- RC-11 proves that a package-relative import works inside a moved package (D-4).
- RC-18 is the new root child that PR #4208 adds. The PR owner must place it inside a grouping directory before merge.
- RC-27 counts the lines that begin with `"file_path": "tests/unit/`. The file holds 8,066 lines.

## 3. Local Observations

- Local `HEAD` equals `main` (`f03c6c9`). The local branch is `main`.
- The local `tests/unit/` directory holds 73 entries. One is `__pycache__`, which is excluded. The result is 72 direct entries.
- Of the 72 entries, 50 are tracked on `main`. The other 22 are untracked directories: `arango_indexes`, `audit`, `auth`, `benchmarks`, `bootstrap`, `cache`, `capture`, `data`, `dataproc`, `firmware_policy`, `firmware_policy_jobs`, `helpers`, `input`, `juniper_skills`, `metrics_gateway`, `mib_generator`, `output`, `serial_cc`, `ste_linter`, `time`, `tools`, and `validation`.
- No tracked name is missing locally.
- The local tree holds 33 directories with six or more children. The `main` tree holds 30 directories under `tests/unit/` with six or more children. The difference comes from untracked files. For example, local `gateway` holds 10 children and `main` holds 8. Local `reports` holds 14 and `main` holds 3.
- No batch counts or moves an untracked entry. Warning: a cleanup of those untracked entries deletes local-only files. This issue does not clean them.

## 4. Holds And Ownership Evidence

Each hold follows the rule in `plan.md` section "Holds". Evidence dates are 2026-11-26 unless stated.

| Hold | Evidence | Decision |
| - | - | - |
| H-1 | PR #4208 is OPEN and draft. It changes 82 files, 23 of them under `tests/unit/`. Its file list holds `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`, eight `tests/unit/wan_dashboard/wan_performance/` files, and fourteen new `tests/unit/wan_performance/` files. Its body does not name issue #4142. | Hold |
| H-2 | PR #4813 is OPEN and draft. Its file list holds `tests/unit/config/foundation/models/dataproc/test_data_processing_utils.py`, `tests/unit/db/sle_window_summary/test_backend_preservation.py`, `tests/unit/export/test_data_exporter.py`, and `tests/unit/export/test_endpoint_family_exporter.py`. | Hold three paths. The `dataproc` path already sits under a container. |
| H-3 | Issue #4721 is OPEN. Its text names `tests/unit/test_device_events_52w_exporter_extended.py` as an existing test. Its proposed repair adds `tests/unit/export/test_device_events_checkpoint_recovery.py`. Its scope includes the root exporter tests. | Hold both root files. Plan the new file inside the export group. |
| H-4 | Issue #2747 comment claims only `tests/unit/ssh/test_cli_shell_manager.py`. Issue #2746 states the same file set. Both issues are OPEN. | Hold the one exact path. |
| H-5 | Issue #4133 is OPEN. Its comment describes a session-only candidate that changes `tests/unit/test_menu_entry_metadata.py`. | Hold the path. |
| H-6 | Issue #2711 is OPEN, titled "triage weak_zero_assertions findings". The legacy record names `test_parameter_collector.py` as reserved. | Hold the path until the owner confirms. |
| H-7 | Issue #4008 is OPEN, titled "isolate Marvis alarm handling modules". Its command names all `tests/unit/marvis/actions/` tests. | Hold the directory. |
| H-8 | Issue #2746 is OPEN. The legacy record names `test_issue_2971_census_repairs.py` as in its scope. The issue text was not checked for this exact file. | Hold conservatively (unverified, section 9). |

Not holds:

- Issue #2753 names paths as inventory items in its findings table. Its owner claims no path. The paths move with a reference update.
- Issue #4126 lists findings in `juniper_rma` files. It claims no path.
- Issue #2752 is CLOSED. The legacy hold on `upgrade_portal` is stale.
- PR #4287, PR #4317, PR #4323, and PR #4226 do not appear among the open pull requests that change a `tests/` path, so they hold no path.
- The seven open pull requests on 2026-11-26 do not change `.github/workflows/ci.yml` or `pyproject.toml`. The legacy CI hold is stale.

## 5. Decisions

Each decision has alternatives, a choice, a reason, and a risk. No decision needs a human (`human_decision_required` is false for all ten).

**D-1. Keep the four containers.** Alternatives: keep the flat root packages (50 children stay), use numbered buckets (names do not help engineers), or re-root the tree (merged paths move again). Chosen: keep `config`, `marvis`, `maps`, and `prod_readiness`. Reason: PR #4358 already merged them, and they match the source packages. Risk: container names do not match the source tree one to one. Mitigation: each container lists its domain groups in `plan.md`.

**D-2. Use four hold types.** Alternatives: keep every legacy hold, which blocks most work without evidence. Or hold only pull requests, which ignores planned edits. Chosen: hold on pull request ownership (H-1, H-2), on exact claims (H-4), and on planned edits named in an open issue scope (H-3, H-5 to H-8). Inventory mentions hold nothing. Reason: the legacy holds lacked evidence for most issues. Risk: an open issue edits a moved file after the batch starts. Mitigation: T003 refreshes the holds before each batch, and a rebase precedes each move.

**D-3. Move `analytics/test_insight_metrics_utils.py` now.** Alternatives: keep the file at root to preserve a historical link in issue #3300, or move it and let the link go stale. Chosen: move it. Reason: FR-001 needs the root to shrink, and FR-004 keeps historical text unchanged. Keeping the file at root blocks FR-001. A shim or alias is forbidden by `AGENTS.md`. Risk: a dead link in a historical record. Mitigation: record the dead link in `analysis.md`.

**D-4. Move the whole `output_defaults` package.** Alternatives: keep four files at source, as the legacy record did, or move the package as one unit. Chosen: move the package. Reason: RC-11 shows that `test_session.py` imports from its own package with `from . import`. A whole-package move keeps those imports valid. The legacy reason for keeping files at source does not hold (ledger S-8).

**D-5. Place the root `org` package in `marvis/standalone/mist/resources/org/`.** Alternatives: place it in `marvis/mist/resources/org/`, which would make six children. Place it in `marvis/mist/access/org/`, which does not match its subject. Or restructure `resources`, which moves merged paths again. Chosen: the standalone group, which already holds two `org` tests. Reason: it keeps the resources subject and respects the five-child limit. Risk: a package in a `standalone` tree. Mitigation: `plan.md` names the group and records the reason.

**D-6. Create `marvis/mist/realtime/`.** Alternatives: place `websocket`, `websocket_streams`, and `actions` under `intelligence` (full) or `resources` (full), or under `maps/interfaces` (full). Chosen: `marvis/mist/realtime/` as the fourth child of `marvis/mist/`. Reason: `marvis/mist/` has one free slot, and the three packages share the event and stream subject. Risk: a reader may expect WebSocket code under `maps`. Mitigation: the group name names the subject.

**D-7. Update CI and `pyproject.toml` selectors in the same batch.** Alternatives: wait for a PR owner (the legacy hold) or update in the same batch. Chosen: update in the same batch, because no open pull request changes `.github/workflows/ci.yml` or `pyproject.toml` (section 4). Risk: a CI selector breaks. Mitigation: T-REMOTE-CI runs before merge.

**D-8. Leave production comments and build-file comments unchanged.** Alternatives: update the four `src/` and `web_portal/` comments and the two build-file comments in this issue, or track them in a follow-up issue. Chosen: follow-up issue. Reason: FR-007 keeps product files unchanged. A change to `Dockerfile` or `Containerfile` starts a container build. `Containerfile` and `Dockerfile` already name a path that no longer exists (`tests/unit/container/test_build_files_match.py`), so the defect predates this issue. Risk: the comments name moved paths until the follow-up lands. Mitigation: the follow-up issue lists each comment with its line.

**D-9. Use topic groups with five children or fewer.** Alternatives: alphabetical buckets, one group per module, or hashing by file name. Chosen: topic groups, named by the subject of the tests. Reason: topic groups help engineers find tests (User Story 1). Risk: a topic split changes the test layout within a package. Mitigation: each split task records its node IDs before and after.

**D-10. Keep `tests/unit/__init__.py` at root.** Alternatives: remove the marker, or move it into a container. Chosen: keep it as the fifth root child. Reason: `tests.unit` is a package with import references. The marker removal needs a separate import study. Risk: none for the final count, because five children meet FR-001.

## 6. Reference Inventory

The inventory uses `git grep -c "tests/unit" HEAD` outside `specs/` and `changelog.d/`. It found 33 files. It also found 31 files inside `tests/unit/` that contain the text. The search misses the backslash form, which `.github/copilot-instructions.md` line 87 uses. T004 repeats the search with the backslash form.

| File | Hits | Class | Action | Task |
| - | - | - | - | - |
| `.github/copilot-handoff.md` | 11 | Historical handoff | Unchanged | none |
| `.github/copilot-instructions.md` | 1 (line 255), plus line 87 | Active | Update | T050, T051 |
| `.github/test-quality-baseline.json` | 1,304 | Active | Update `file_path` and `related_source` per moved file | T028, split rule step 8 |
| `.github/workflows/ci.yml` | 6 (lines 96, 99, 263, 264, 267, 303) | Active | Update | T033, T038, T050 |
| `.github/workflows/container-build.yml` | 1 | Directory only | Unchanged | none |
| `.specify/bugs/menu-93-inventory-output/assessment.md` | 4 | Historical record | Unchanged | none |
| `.specify/bugs/menu-93-inventory-output/fix.md` | 22 | Historical record | Unchanged | none |
| `.specify/templates/tasks-template.md` | 1 | Generic template | Unchanged | none |
| `CHANGELOG.md` | 180 | Historical record | Unchanged | none |
| `Containerfile` | 1 | Build comment, stale before this issue | Unchanged (D-8) | follow-up issue |
| `Dockerfile` | 1 | Build comment, stale before this issue | Unchanged (D-8) | follow-up issue |
| `documentation/development-tooling-migration.md` | 3 | Historical record | Unchanged | none |
| `documentation/diagrams/infrastructure/deployment-pipeline.md` | 1 | Active | Update when it names a moved path | T070 |
| `documentation/release-notes.md` | 3 | Historical record | Unchanged | none |
| `documentation/wiki/Container-Setup.md` | 1 | Path remains valid | Unchanged | none |
| `documentation/wiki/Testing.md` | 1 | Directory only | Unchanged | none |
| `mist-ops-platform/tests/unit/worker/test_entity_id_evidence.py` | 1 | Other project | Excluded | none |
| `pyproject.toml` | 11 | Active | Update lines 269, 271, 275, 516 | T028, T050 |
| `src/interfaces/portals/upgrade_portal/capture/export.py` | 1 (line 23) | Production comment | Unchanged (D-8) | follow-up issue |
| `src/mist/resources/org/org_synthetic_probes_manager.py` | 1 (line 450) | Production comment | Unchanged (D-8) | follow-up issue |
| `src/operations/execution/firmware/upgrade_service.py` | 1 (line 20) | Production comment | Unchanged (D-8) | follow-up issue |
| `tests/e2e/upgrade_portal/conftest.py` | 1 (line 2881) | Active comment | Update | T054 |
| `tests/e2e/upgrade_portal/test_alert_prefix_space.py` | 1 | Active | Update | T054 |
| `tests/e2e/upgrade_portal/test_capture_identifier_paint.py` | 1 | Active | Update | T054 |
| `tests/e2e/upgrade_portal/test_narrow_action_cells.py` | 1 | Active | Update | T054 |
| `tests/e2e/web_portal/juniper_browser_harness.py` | 1 | Active | Update | T070 |
| `tests/guardrails/test_container_build_trigger.py` | 3 | Directory only | Unchanged | none |
| `tests/guardrails/test_e2e_shard_partition.py` | 1 | Active | Update when it names a moved path | T070 |
| `tests/guardrails/test_guard_proof_audit.py` | 1 | Active | Update when it names a moved path | T070 |
| `tests/guardrails/test_move_module_guidance.py` | 1 | Pattern text, no moved path | Unchanged | none |
| `tests/support/rehearsal/clock.py` | 1 (line 10) | Active docstring | Update | T054 |
| `tests/tools/test_quality_analyzer/test_golden_repo.py` | 1 (line 15) | Active when read | Update when read | T036 |
| `web_portal/services/output_scan.py` | 1 (line 111) | Production comment | Unchanged (D-8) | follow-up issue |

The `documentation/quality-gates.md` file does not appear in this inventory. It names no `tests/unit` path.

## 7. Legacy Claim Ledger

The legacy record exists on `main` at RC-38. Its claims are drafts. This ledger checks each claim against `main`. Counts: verified 8, stale 8, absent 2.

| ID | Legacy claim | Remote evidence | Result |
| - | - | - | - |
| V-1 | Candidate base `31b752f` exists | RC-42 | verified |
| V-2 | Four containers exist | RC-03 to RC-06 | verified |
| V-3 | Four legacy destinations exist | RC-12 to RC-15 | verified |
| V-4 | Two legacy sources are absent | RC-16, RC-17 | verified |
| V-5 | Issue #4142 stays open | Issue state OPEN | verified |
| V-6 | PR #4208 is open and draft | PR state OPEN, draft | verified |
| V-7 | The legacy record folder exists | RC-38 | verified |
| V-8 | Debt C-1 and task T054 exist | RC-40, RC-41 | verified |
| S-1 | Root holds 155 entries (`plan.md` line 31, `plan.md` line 35, `research.md` line 217 says 158) | RC-01 says 50 | stale |
| S-2 | Gate result is "pass with staged work" (`plan.md` line 44) | Root holds 50, and FR-001 is unmet | stale |
| S-3 | PR #4358 remains open and draft (issue comments dated 2026-10-30 and 2026-11-09) | PR #4358 is MERGED on 2026-11-13 | stale |
| S-4 | PR #4208 owns `.github/workflows/ci.yml` | PR #4208 changes no `.github` file | stale |
| S-5 | `juniper_rma` holds 34 tracked files (issue comment dated 2026-11-09) | RC-07 says 22 | stale |
| S-6 | PR #4287 owns `tests/unit/dataclasses/test_service_measurement.py` | No open pull request lists a `tests/unit/dataclasses` path | stale |
| S-7 | Issue #2752 reserves `tests/unit/upgrade_portal/` | Issue #2752 is CLOSED | stale |
| S-8 | Four `output_defaults` files stay at source because of relative imports | RC-11 shows that a whole-package move keeps the imports valid | stale |
| A-1 | Destination `prod_readiness/operations/exporting/container/output_defaults/` exists in the plan | Not on main, and the source remains (RC-10) | absent |
| A-2 | Destination `maps/interfaces/portals/upgrade_portal/` exists in the plan | Not on main | absent |

## 8. Sources

Remote sources (read-only, GitHub API and `gh`):

- Issue #4142 body and seven comments. Issues #2711, #2746, #2747, #2752, #2753, #3519, #4008, #4126, #4133, #4139, #4721, #4734, and #4750 (state, and text scans for `tests/unit`).
- Pull requests #4208, #4813, #4358, #4650, #4322, #4493, and the open pull request list with file lists. The search for "4142" returned #4650, #4358, #4322, #4493, and #4208.
- Git trees, blobs, and commits listed in section 2.

Local sources (read-only): the files listed in section 1, the legacy record under `specs/numbered/0/0/1/1/3/0/3/2/4142-unit-test-domain-packages/`, and the tracked tree at `HEAD`.

## 9. Unverified

- U-1: Legacy node-ID counts, 30,651 candidate IDs and 30,645 inventory IDs. Reason: no test run is permitted for this record, and the counts describe commit `816f42ba`, not `main`.
- U-2: Legacy test results, 13,823 passed and 11 skipped. Reason: same as U-1.
- U-3: Legacy guard counts, 1,428 Python test files and 2,573 source files. Reason: the guards were not run.
- U-4: Legacy test-quality counts, 1,253 files, 400 findings, and 733 baseline records. Reason: the analyzer was not run.
- U-5: Legacy end-to-end collection count, 3,513 items. Reason: the collection was not run.
- U-6: Legacy "active session claims". Reason: session claims are not visible to this agent, so no source checks them. T003 requires the coordinator to confirm them before each batch.
- U-7: Issue #2746 names `tests/unit/test_issue_2971_census_repairs.py` in its scope. Reason: the issue body and comments were scanned for `tests/unit` lines, and this exact file was not confirmed. H-8 applies conservatively.
- U-8: The merged PR #4358 body records "T069 complete". Reason: the body was not read. Only its state, merge time, and title were read.
- U-9: `tests/unit/marvis/actions/` is part of issue #4008's scope. Reason: only one command line naming the directory was read. H-7 applies conservatively.
