# Tasks: Blind Except Handler Audit (issue 1794)

**Feature**: `1794-blind-except-audit` | **Branch**: `docs/1794-blind-except-audit` (this record) | **Date**: 2026-11-26

**GitHub Issue**: [#1794](https://github.com/jmorrison-juniper/MistHelper/issues/1794)

**Input**: Design documents from `specs/numbered/0/0/0/2/4/1/3/4/1794-blind-except-audit/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [design/research.md](design/research.md). Issue #1792 is closed and its work is in place (RC-035). Issue #3070 is closed and its guard is in place (RC-032).

## Format

`- [ ] Txxx [P?] [USn] Description`

- `[P]` marks a task that reads only, or that touches files no other task touches. No slice task carries `[P]`, because the slices share the baseline file and the publication queue is serial (AGENTS.md).
- `[USn]` names the user story that owns the task.
- Each task names its requirement IDs, its exact paths, its acceptance statement, one verification command from the repository gates table (`.github/copilot-instructions.md`, RC-031), and its status.
- Status values: `open`, `verified-present`, `partial`, or `absent`.

## Rules for every edit task

1. Use `.venv\Scripts\python.exe` for each Python command. Target Python 3.15 (FR-038).
2. Add no `# noqa` directive (FR-015). Add no `TypeError`, `AttributeError`, `NameError`, or `AssertionError` to a narrowed type (FR-010).
3. Read the caller before a `narrow` or `delete` outcome (FR-009).
4. Give each continued handler an error log with the exception type and the operation name (FR-013). Use `%s` formatting.
5. Give each changed line an inline comment (FR-036).
6. Write the Markdown and comment text in Simplified Technical English (FR-034).
7. Keep each pull request at 40 sites or fewer (FR-017).
8. Caution: a slice that changes a destructive path needs a human review before merge. Its pull request must not carry the `auto-merge` label (AGENTS.md).
9. Start each slice from a clean worktree. Do not use the working-tree copy of a file that differs from main (U-6).

## Phase 1: Baseline (User Story 2)

- [ ] T001 [US2] Measure the baseline with the pinned tools. Confirm that `main` is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` and that ruff is 0.17.6 and pylint is 4.1.4. Record the default ruff count, the `--ignore-noqa` count, and the pylint W0718 count.
  - Requirements: FR-001, FR-002, FR-003, FR-005, SC-001
  - Paths: `design/research.md` (Measured state), `pyproject.toml` (lines 206 and 209), `.github/workflows/ci.yml` (line 78)
  - Acceptance: The three counts and the two roots appear in `research.md`. The counts are measured by the commands in `design/quickstart.md` (Q-3 and Q-7). The RUF100 behavior is checked with a temporary file that the implementer deletes (U-5).
  - Verification: `python -m ruff check .` (Lint gate)
  - Status: open

- [ ] T002 [US2] Reconcile the counts. Explain each difference between the ruff count, the pylint count, and the text count by path and reason.
  - Requirements: FR-004, SC-001
  - Paths: `design/research.md` (Measured state, Local evidence)
  - Acceptance: Every difference has a path-level reason. No difference is unexplained.
  - Verification: `python -m ruff check .` (Lint gate)
  - Status: open

- [x] T003 [P] [US3] Confirm that the growth guard runs in CI.
  - Requirements: FR-006, SC-009
  - Paths: `tests/guardrails/test_blind_exception_handler_ratchet.py` (RC-032), `.github/blind-exception-handler-baseline.json` (RC-033), `.github/workflows/ci.yml` (RC-017)
  - Acceptance: The guard test passes, and the CI shards include `tests/guardrails`.
  - Verification: `python -m pytest tests/guardrails/test_blind_exception_handler_ratchet.py -q` (Tests gate)
  - Status: verified-present

- [ ] T004 [P] [US2] Inventory the inline pylint disables. Each of the 20 files holds one or more `pylint: disable=broad-exception-caught` lines (Local evidence, 57 lines). Record each disable and its site.
  - Requirements: FR-015, D-13
  - Paths: `src/foundation/runtime/time/time_utils.py`, `src/mist/access/api/api_fetch_utils.py`, `src/mist/intelligence/troubleshooting/rf_diagnostics/recording.py`, `src/mist/intelligence/troubleshooting/rf_diagnostics/spectrum.py`, `src/mist/resources/device/utility_commands.py`, `src/mist/resources/gateway/_wan2_variable_device.py`, `src/mist/resources/gateway/_wan2_variable_template.py`, `src/mist/resources/gateway/gateway_export_utils.py`, `src/mist/resources/gateway/gateway_stats_exporter.py`, `src/mist/resources/gateway/template_config.py`, `src/mist/resources/gateway/wan_probe_device_override_manager.py`, `src/mist/resources/gateway/wan2_migration_manager.py`, `src/mist/resources/inventory/csv_comparator.py`, `src/operations/execution/capture/_packet_capture_exec.py`, `src/operations/execution/capture/_packet_capture_org.py`, `src/operations/execution/capture/_packet_capture_prompts.py`, `src/operations/execution/capture/client_pcap_downloader.py`, `src/operations/execution/capture/packet_capture_download.py`, `src/operations/execution/capture/packet_capture.py`, `src/operations/execution/firmware/bulk_switch_upgrader.py`
  - Acceptance: The inventory lists 57 lines. Each `api_fetch_utils.py` disable is explained, because that file holds no `except Exception` text match. The pylint run shows whether logged handlers are reported (U-4).
  - Verification: `python -m pylint src/ --fail-under=9.5` (Code quality gate)
  - Status: open

- [ ] T005 [P] [US2] Record the excluded-tree counts and their follow-up needs.
  - Requirements: FR-032, SC-012
  - Paths: `pyproject.toml` (line 206), `design/research.md` (Measured state)
  - Acceptance: Each excluded tree has its count. mist-ops-platform 23 sites, web_portal 26, scripts 32, and maps 68 with 16 inert `noqa` lines.
  - Verification: `python -m ruff check .` (Lint gate)
  - Status: open

- [x] T006 [P] [US3] Confirm that the target route is free and that the legacy folders exist.
  - Requirements: FR-031, FR-030
  - Paths: `specs/numbered/0/0/0/2/4/1/3/4/` (new), `specs/1794-blind-except`, `specs/1794-blind-except-slice2`, `specs/1794-blind-except-handlers`
  - Acceptance: The route has no entries (RC-096). The three legacy folders exist (RC-097 to RC-099).
  - Verification: `python -m ruff check .` (Lint gate)
  - Status: verified-present

- [x] T007 [P] [US2] Confirm that each held commit is not merged, and map each held commit to its owning slice.
  - Requirements: FR-027
  - Paths: `design/research.md` (RC-104, RC-106, and RC-112 to RC-125), `plan.md` (Held commits and their owning slices)
  - Acceptance: Each held commit is not an ancestor of main, and each has one owning slice.
  - Verification: `python -m ruff check .` (Lint gate)
  - Status: verified-present

## Phase 2: Slices (User Stories 1 and 3)

Each slice task applies the six steps of the slice template. (1) List the slice sites with the BLE001 command in `quickstart.md`, Q-4. (2) Read each site and its caller, and set each outcome. (3) Apply each outcome. Add a log call where the code continues. Add a comment at each keep site. (4) Write one outcome row for each site in the pull request body. (5) Lower the count of each changed file in `.github/blind-exception-handler-baseline.json`. (6) Add the tests that FR-021 requires, and run the slice gates.

Every slice task has the same acceptance statement: the slice's ruff BLE001 count for its paths is zero (quickstart Q-5), each changed file has a lower or equal baseline count, and the unit pass count does not drop.

- [ ] T008 [US1] Slice S01. Audit `MistHelper.py` (7 sites) and `wsgi.py` (3 sites).
  - Requirements: FR-007 to FR-021, FR-036
  - Paths: `MistHelper.py`, `wsgi.py`, `.github/blind-exception-handler-baseline.json`, `changelog.d/issue-<child>-blind-except-s01.md`
  - Acceptance: The safe sweep gate passes (`python MistHelper.py --test`). Each changed `MistHelper.py` line has a comment. The hot file rule holds: one open pull request for `MistHelper.py`.
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T009 [US1] Slice S02. Audit the 34 sites in `src/mist/access/` and `src/mist/intelligence/` (20 files listed in `plan.md`, S02).
  - Requirements: FR-007 to FR-021, FR-036
  - Paths: the files of `plan.md` S02, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: `src/mist/intelligence/analytics/site/zone_analyzer.py` stays with its owner (issue comment 7) until that owner releases it.
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T010 [US1] Slice S03. Audit the 38 sites in `src/mist/networking/`, `src/mist/resources/inventory/`, `src/mist/resources/org/`, and `src/operations/wan/` (17 files in `plan.md`, S03).
  - Requirements: FR-007 to FR-021, FR-036
  - Paths: the files of `plan.md` S03, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: Each keep site has a reason. Each audited file keeps its test count.
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T011 [US1] Slice S04. Audit the 30 sites in `src/mist/realtime/` and `src/interfaces/monitoring/` (16 files in `plan.md`, S04).
  - Requirements: FR-007 to FR-021, FR-036
  - Paths: the files of `plan.md` S04, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: The ping assertion branch waits for the handoff of issue #2711 (RC-087).
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T012 [US1] Slice S05. Audit the 32 sites in `src/mist/resources/gateway/` and `src/operations/execution/ssid_consolidation/` (11 files in `plan.md`, S05).
  - Requirements: FR-007 to FR-021, FR-036
  - Paths: the files of `plan.md` S05, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: The `template_config.py` file (10 sites) keeps its three existing disables until each site is audited.
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T013 [US1] Slice S06. Audit the 27 sites in `src/foundation/persistence/` and `src/mist/resources/site/` (9 files in `plan.md`, S06). Include the held cache correction.
  - Requirements: FR-007 to FR-021, FR-027, FR-036
  - Paths: the files of `plan.md` S06, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: `database_schema_utils.py` coordinates with issue #4712 (RC-086).
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T014 [US1] Slice S07. Audit the 40 sites in `src/mist/resources/device/` (9 files in `plan.md`, S07). This slice changes the destructive reboot path (RC-043).
  - Requirements: FR-007 to FR-021, FR-036
  - Paths: the files of `plan.md` S07, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: A human reviews the merge. The pull request does not carry `auto-merge`.
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T015 [US1] Slice S08. Audit the 39 sites in `src/operations/execution/ssh/` (13 files in `plan.md`, S08). Include the held SSH command CSV commit.
  - Requirements: FR-007 to FR-021, FR-027, FR-036
  - Paths: the files of `plan.md` S08, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: The SSH command list keeps its empty fallback for file, encoding, and CSV errors. An unexpected validation error propagates. The slice records the ssh ruff counts with and without `--ignore-noqa` before the first edit (U-3).
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T016 [US1] Slice S09. Audit the 25 sites in `src/operations/execution/capture/` and `src/operations/protection/` (8 files in `plan.md`, S09).
  - Requirements: FR-007 to FR-021, FR-036
  - Paths: the files of `plan.md` S09, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: Each keep site logs with exception information through a handler that carries `SensitiveFilter` (RC-061).
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T017 [US1] Slice S10. Audit the 29 sites in `src/operations/execution/firmware/firmware_manager.py` (RC-059). This slice changes the destructive firmware path.
  - Requirements: FR-007 to FR-021, FR-036
  - Paths: `src/operations/execution/firmware/firmware_manager.py`, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: A human reviews the merge. The pull request does not carry `auto-merge`.
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T018 [US1] Slice S11. Audit the 24 sites in the other firmware files (4 files in `plan.md`, S11). Correct the `RuntimeError` handling in `running_version.py` under D-4. This slice changes the destructive firmware path.
  - Requirements: FR-007 to FR-021, FR-036
  - Paths: the files of `plan.md` S11, `src/operations/execution/firmware/running_version.py`, `tests/unit/firmware/test_running_version.py`, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: `bulk_switch_upgrader.py` keeps its one remaining handler (line 664) only with a reason. The callers of `_next_apitoken` in mistapi are read before the response check is written (U-15). The body of `listSiteDevicesStats` after line 1051 is read before the same change (U-10). A human reviews the merge.
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T019 [US1] Slice S12. Audit the first 38 sites of `src/operations/exporting/export/` (17 files in `plan.md`, S12). Include the held device-statistics and inventory commits.
  - Requirements: FR-007 to FR-021, FR-027, FR-036
  - Paths: the files of `plan.md` S12, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: The silent empty report does not occur. Each export handler that returns an empty collection logs the cause (plan.md, edge cases).
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T020 [US1] Slice S13. Audit the next 40 sites of `src/operations/exporting/export/` (13 files in `plan.md`, S13).
  - Requirements: FR-007 to FR-021, FR-036
  - Paths: the files of `plan.md` S13, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: Each keep site has a reason. Each audited file keeps its test count.
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T021 [US1] Slice S14. Audit the last 16 sites of `src/operations/exporting/export/` (11 files in `plan.md`, S14). Include the held other-device and AP-address commits.
  - Requirements: FR-007 to FR-021, FR-027, FR-036
  - Paths: the files of `plan.md` S14, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: Issue #4709 coordinates on `site_other_device_events_exporter.py`.
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T022 [US1] Slice S15. Audit the 39 sites in the first half of `src/foundation/support/refactors/` (17 files in `plan.md`, S15). Include the held anomaly and device-fetch commits.
  - Requirements: FR-007 to FR-021, FR-027, FR-036
  - Paths: the files of `plan.md` S15, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: Issue #4713 coordinates on `msp_privilege_detection.py`. Issue #4711 is closed, and its fix is verified before the slice changes `tui_launcher.py`.
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T023 [US1] Slice S16. Audit the 20 sites in `src/foundation/` (10 files in `plan.md`, S16). Include the held time, container-detection, catalog, address-normalization, and CSV-template work.
  - Requirements: FR-007 to FR-021, FR-027, FR-036
  - Paths: the files of `plan.md` S16, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: Issue #3824 hands off `zscaler_catalogue.py` before the slice changes it. The CSV-template changes are recovered from the archived session before the file changes (issue comment 61, U-7). `logger_utils.py` keeps its recursion note.
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T024 [US1] Slice S17. Audit the 6 sites in `src/interfaces/visualization/ui/` and `src/interfaces/portals/licensing_comparison/` (5 files in `plan.md`, S17).
  - Requirements: FR-007 to FR-021, FR-036
  - Paths: the files of `plan.md` S17, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: The debug saver keeps the handler at line 106 with its `logger.exception` call (RC-062).
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T025 [US1] Slice S18. Audit the first 38 sites of `src/interfaces/portals/upgrade_portal/` (11 files in `plan.md`, S18).
  - Requirements: FR-007 to FR-021, FR-036
  - Paths: the files of `plan.md` S18, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: The upgrade portal logs each keep site through its handler that carries `SensitiveFilter` (`factory.py` line 274).
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T026 [US1] Slice S19. Audit the 40 sites in `app/routes/upgrade.py` (14) and `app/wiring.py` (26). This slice changes the destructive upgrade path.
  - Requirements: FR-007 to FR-021, FR-036
  - Paths: `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py`, `src/interfaces/portals/upgrade_portal/app/wiring.py`, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: A human reviews the merge. The pull request does not carry `auto-merge`.
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T027 [US1] Slice S20. Audit the 40 sites in the middle of `src/interfaces/portals/upgrade_portal/` (19 files in `plan.md`, S20).
  - Requirements: FR-007 to FR-021, FR-036
  - Paths: the files of `plan.md` S20, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: Each keep site has a reason. Each audited file keeps its test count.
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T028 [US1] Slice S21. Audit the last 13 sites of `src/interfaces/portals/upgrade_portal/upgrade/` (7 files in `plan.md`, S21).
  - Requirements: FR-007 to FR-021, FR-036
  - Paths: the files of `plan.md` S21, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: Each keep site has a reason. The stop path keeps its cleanup behavior.
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T029 [US1] Slice S22. Audit the first 39 sites of the test tree (25 files in `plan.md`, S22). The ratchet guard file keeps its logic. Only its real handlers change.
  - Requirements: FR-033, FR-021, FR-036
  - Paths: the files of `plan.md` S22, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: `tests/guardrails/test_blind_exception_handler_ratchet.py` keeps its guard logic. Its string literals are not handlers (U-13).
  - Verification: `python -m pytest tests/guardrails/test_blind_exception_handler_ratchet.py -q` (Tests gate)
  - Status: open

- [ ] T030 [US1] Slice S23. Audit the last 21 sites of the test tree (14 files in `plan.md`, S23).
  - Requirements: FR-033, FR-021, FR-036
  - Paths: the files of `plan.md` S23, `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: Each test keeps its assertions. Each audited test file passes.
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

## Phase 3: Final gate (User Story 3)

- [ ] T031 [US3] Run the final gate pull request (S24). Add `BLE001` to the ruff select list and keep `RUF100`. Remove `W0718` from the pylint disable list. Rewrite the comment at lines 588 to 593. Update the stored-baseline test. Remove the entries at zero from the baseline file.
  - Requirements: FR-022, FR-023, FR-024, FR-025, FR-026, SC-002, SC-008, SC-009
  - Paths: `pyproject.toml` (lines 209 and 588 to 594), `documentation/quality-gates.md` (line 50), `tests/guardrails/test_blind_exception_handler_ratchet.py` (the stored-baseline test), `.github/blind-exception-handler-baseline.json`, one changelog fragment
  - Acceptance: `ruff check . --select BLE001 --ignore-noqa --statistics` reports zero (SC-002). The pylint score is 9.5 or higher (RC-128), measured before merge (U-14). The pull request body contains `Closes #1794` (D-12). The growth guard test passes with an empty baseline.
  - Verification: `python -m ruff check .` (Lint gate)
  - Status: open

## Phase 4: Coordination, tracking, and preservation

- [ ] T032 [US3] Open one issue for each slice cluster (S01 to S23) and for the final gate. Each issue names #1794 and its slice ID. Do not reopen #2833, #2834, #2835, #2836, or #2926 (D-7).
  - Requirements: FR-029, D-7
  - Paths: none (GitHub issues)
  - Acceptance: 24 new issues exist. Each one has a type label (`refactor`) and a scope label (`tests`, `MistHelper.py`, `web-portal`, or `docs`)   from the repository labels. Before the issues open, the closing comments of #2833, #2834, #2835, #2836, #2926, and #1709 are read (U-11).
    - Verification: `python -m ruff check .` (Lint gate, no file changes)
  - Status: open

- [ ] T033 [US2] File the four follow-up issues for the excluded trees (mist-ops-platform 23 sites, web_portal 26, scripts 32, and maps 68).
  - Requirements: FR-032, SC-012
  - Paths: none (GitHub issues)
  - Acceptance: Four issues exist. Each names its count and the inert `noqa` lines in maps.
    - Verification: `python -m ruff check .` (Lint gate, no file changes)
  - Status: open

- [ ] T034 [US1] Rebase each held commit onto main and recheck it inside its owning slice (`plan.md`, Held commits table). Do not publish a held commit before its slice starts.
  - Requirements: FR-027, D-6
  - Paths: the held commit targets in `plan.md` (for example `src/foundation/persistence/cache/cache_utils.py` and `src/foundation/support/utils/address_utils.py`)
  - Acceptance: Each rebased commit passes the checks of its slice. The address-normalization commit is checked against PR #4503 (RC-108).
  - Verification: `python -m pytest <changed test files> -q` (Tests gate)
  - Status: open

- [ ] T035 [US1] Preserve the held refs until a merged replacement exists. Record the replacement in each closing note.
  - Requirements: FR-028, SC-011
  - Paths: none (remote refs and commits, RC-104, RC-106, and RC-112 to RC-125)
  - Acceptance: For each held commit, either a merged replacement exists or the remote branch carries a preservation note.   No local branch is deleted before that proof. The branch names that hold the commits are read first (U-12).
    - Verification: `python -m ruff check .` (Lint gate, no file changes)
  - Status: open

- [ ] T036 [US2] Record the supersession of the legacy records. Open a cleanup issue that adds a banner to each legacy `spec.md`. Do not delete any legacy record.
  - Requirements: FR-030, D-11
  - Paths: `specs/1794-blind-except/`, `specs/1794-blind-except-slice2/`, `specs/1794-blind-except-handlers/` (read only in this task), `analysis.md` in this record
  - Acceptance: `analysis.md` names each superseded legacy record. The cleanup issue exists.
    - Verification: `python -m ruff check .` (Lint gate, no file changes)
  - Status: open

## Final tasks

- [ ] T-LOCAL-GATES [FR-037, FR-038] Run each gate in the repository gates table that applies to the changed files, then record each result in the pull request body.
  - Requirements: FR-034, FR-036, FR-037, FR-038
  - Paths: the changed files of the slice or the final gate change
  - Acceptance: Each gate reports its expected result (`.github/copilot-instructions.md`, RC-031). Each gate that does not apply names the reason.
  - Verification: the commands in `design/quickstart.md`, Q-6
  - Status: open

- [ ] T-PR [FR-029, FR-035] Commit with a Conventional Commits message, push the `<type>/<ISSUE>-<slug>` branch, and open the pull request. This record pull request body contains `Closes #1794`, as the brief requires. Each slice pull request body contains `Refs #1794`.
  - Requirements: FR-018, FR-029, FR-035, D-12
  - Paths: the changed files of the slice, the changelog fragment, and the outcome table in the body
  - Acceptance: The commit message names the type, the scope, and the issue. The commit includes the Co-authored-by trailer. The body names each local gate and its result.
  - Caution: A closing keyword closes #1794 when the pull request merges (RC-023). Reopen #1794 after the merge if the umbrella must stay open (analysis A-13).
  - Verification: `python -m ruff check .` (Lint gate)
  - Status: open

- [ ] T-REMOTE-CI [FR-020] Watch the CI run for the pull request with `gh pr checks <number> --watch`. Fix each failing check in the same branch.
  - Requirements: FR-020
  - Paths: none (CI jobs of `.github/workflows/ci.yml`, RC-017)
  - Acceptance: Every required check passes, including the STE check and CodeQL.
  - Verification: `python -m pytest tests/guardrails/test_blind_exception_handler_ratchet.py -q` (Tests gate)
  - Status: open

- [ ] T-MERGE [FR-024] Enable auto-merge only after remote CI passes and the orchestrator authorizes the merge. Squash the merge. Remove the branch and its worktree after the merge. Never enable auto-merge on a destructive path.
  - Requirements: FR-024, FR-028
  - Paths: none (the pull request and its branch)
  - Acceptance: The squash commit carries the issue reference. The branch is removed after the merge. No commit is pushed after the squash merge.
  - Caution: A commit pushed after a squash merge becomes an orphan that no pull request reaches (AGENTS.md). File a new issue and branch again from main in that case.
  - Verification: `python -m ruff check .` (Lint gate)
  - Status: open

## Dependencies and execution order

| Phase | Starts after | Notes |
| - | - | - |
| 1 (T001 to T007) | This record is merged | T001 measures the counts that every later task uses. |
| 2 (T008 to T030) | Phase 1 is complete | Serial in the order S01 to S23. Each slice lowers the baseline. |
| 3 (T031) | All slices are merged, and the ruff BLE001 count is zero | Both gates change in one pull request. |
| 4 (T032 to T036) | T002 is complete for T032 and T033. T035 starts after each held replacement merges. | Tracking and preservation. |
| Final (T-LOCAL-GATES to T-MERGE) | Each pull request | Repeated for each slice and for the final gate. |

Phase 2 slices share the baseline file. A slice that starts while another slice is open must rebase onto main first (FR-020).

## Implementation strategy

The first slice is S01 (10 sites), because it has the smallest risk and it proves the template. S07, S10, S11, and S19 change destructive paths. Their merges need a human review, and they wait until the earlier slices show that the template works.
