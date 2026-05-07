# Tasks: Quality Gate Exception Remediation

**Input**: Design documents from `specs/189-quality-gate-remediation/`
**Branch**: `chore/189-quality-gate-remediation`
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md) | **Data Model**: [data-model.md](data-model.md) | **Quickstart**: [quickstart.md](quickstart.md)

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story this task belongs to (US1–US6)
- Exact file paths included in all descriptions

---

## Phase 1: Setup (Baseline Capture)

**Purpose**: Capture before-state metrics and verify toolchain before any code changes.
These tasks produce the SC-005 reference point (total suppression count) and confirm
exact line numbers from research.md are still accurate.

- [X] T001 Activate venv (`.venv\Scripts\Activate.ps1`) and verify all quality gate tools are runnable: `python -m py_compile --version`, `python -m ruff --version`, `bandit --version`, `mypy --version`
- [X] T002 [P] Capture baseline suppression count: `(Select-String -Path MistHelper.py,starlink_dashboard.py,'src\**\*.py' -Pattern '# type: ignore|# noqa|# nosec' | Measure-Object).Count` — record result for SC-005 comparison at end
- [X] T003 [P] Verify `os.system` locations in MistHelper.py: `Select-String -Path MistHelper.py -Pattern 'os\.system' | Select-Object LineNumber, Line` — confirm exactly 2 results near lines 35543/35545
- [X] T004 [P] Verify B101 production assert count in MistHelper.py: `Select-String -Path MistHelper.py -Pattern 'nosec B101' | Measure-Object` — confirm 25 (or adjusted count) before replacement

**Checkpoint**: Baseline metrics captured. Proceed to user story implementation.

---

## Phase 2: User Story 1 — Enable Stale-Suppression Detection (Priority: P1) 🎯 MVP

**Goal**: Add `warn_unused_ignores = true` to pyproject.toml so mypy automatically flags
`# type: ignore` annotations that are no longer needed as the codebase gains type coverage.

**Independent Test**: Run `mypy --config-file pyproject.toml MistHelper.py` after the change
and confirm mypy reports "unused-ignore" notes. A still-needed annotation must NOT be flagged.

- [X] T005 [US1] Change `warn_unused_ignores = false` to `warn_unused_ignores = true` at line 126 in `pyproject.toml` under the `[tool.mypy]` section
- [X] T006 [US1] Run `mypy --config-file pyproject.toml MistHelper.py 2>&1 | Select-String 'unused-ignore' | Select-Object -First 5` to confirm detection is active and at least one stale annotation surfaces (SC-006 verified)

**Checkpoint**: US1 complete — `warn_unused_ignores` is live and surfacing stale annotations.

---

## Phase 3: User Story 2 — Remove Dead Code and Phantom Import Suppressions (Priority: P1)

**Goal**: Delete the dead variable `title_color` and resolve the unused PyQt6 import
suppressions in `starlink_dashboard.py`. Zero F841 and F401 violations after changes.

**Independent Test**: `ruff check starlink_dashboard.py` reports no F841 or F401 violations.
Dashboard launches and operates correctly.

- [X] T007 [P] [US2] Delete the dead variable line `title_color = "#9AA0A6"  # noqa: F841` at line 1007 in `starlink_dashboard.py` (ruff F841 confirmed; surrounding elif branches do not reference this value)
- [X] T008 [P] [US2] Remove unused imports `QColor`, `QIcon`, `QPalette` from the import line at line 261 in `starlink_dashboard.py`; keep `QFont` (14 confirmed references); delete the `# noqa: F401` annotation from that line
- [X] T009 [US2] Delete the entire `QProgressBar` import line at line 273 in `starlink_dashboard.py` (zero references confirmed in research.md)
- [X] T010 [US2] Run `python -m ruff check starlink_dashboard.py` and `python -m py_compile starlink_dashboard.py` to verify zero F841/F401 violations and clean syntax (SC-003)

**Checkpoint**: US2 complete — `starlink_dashboard.py` has no dead variable or phantom import suppressions.

---

## Phase 4: User Story 3 — Replace os.system Calls with Secure subprocess Invocation (Priority: P1)

**Goal**: Replace both `os.system()` calls in `MistHelper.py` with `subprocess.run()` using
the list-form invocation (no `shell=True`), then remove the `# nosec B605 B607` annotations.

**Independent Test**: `bandit -r MistHelper.py --tests B605` reports "No issues identified."
Full test suite passes with no behavioral change.

- [X] T011 [US3] Verify `import subprocess` is present in `MistHelper.py` imports; add it if absent (stdlib, no new dependency)
- [X] T012 [P] [US3] Replace `os.system("cls")  # nosec B605 B607` at line 35543 in `MistHelper.py` with `subprocess.run(["cmd.exe", "/c", "cls"], check=False)` — Windows-specific, cmd.exe built-in requires shell wrapper
- [X] T013 [US3] Replace `os.system("clear")  # nosec B605 B607` at line 35545 in `MistHelper.py` with `subprocess.run(["clear"], check=False)` — Linux/Mac standalone executable, no shell needed
- [X] T014 [US3] Run `Select-String -Path MistHelper.py -Pattern 'os\.system'` to confirm zero remaining calls; run `bandit -r MistHelper.py --tests B605 2>&1 | Select-String 'Issue|No issues'` to verify SC-001; run `python -m py_compile MistHelper.py`

**Checkpoint**: US3 complete — both `os.system` calls replaced; zero B605 findings.

---

## Phase 5: P1 Gate Check (US1 + US2 + US3)

**Purpose**: Verify all three P1 stories meet their success criteria before starting P2 work.

- [X] T015 Run full P1 gate battery and confirm all pass: `python -m py_compile MistHelper.py` (SC-009), `python -m ruff check MistHelper.py`, `python -m ruff check starlink_dashboard.py` (SC-003), `bandit -r MistHelper.py` (SC-001), `mypy --config-file pyproject.toml MistHelper.py 2>&1 | Select-String 'error:|unused-ignore' | Select-Object -First 20` (SC-006)

**Checkpoint**: P1 gate green. Begin P2 user story work.

---

## Phase 6: User Story 4 — Replace Production-Critical Asserts with Explicit Raises (Priority: P2)

**Goal**: Replace all 20 confirmed B101-suppressed production `assert` statements in
`MistHelper.py` (listed in research.md) with explicit `ValueError` or `RuntimeError` raises
containing descriptive messages. Remove all `# nosec B101` annotations.

**Independent Test**: `bandit -r MistHelper.py --tests B101` reports "No issues identified."
Full test suite passes with no behavioral regression.

- [X] T016 [US4] Replace B101 API session and site/device resolution asserts at lines 3166, 5677, 5730 in `MistHelper.py` with explicit `ValueError` raises (e.g., `if not condition: raise ValueError("apisession_cls should be set for retry logic")`); remove `# nosec B101`
- [X] T017 [US4] Replace B101 database cursor/connection asserts at lines 10947, 10963, 11000, 11029, 11030 in `MistHelper.py` with explicit `RuntimeError` raises (e.g., `if self.cursor is None: raise RuntimeError("Database cursor not initialized")`); remove `# nosec B101`
- [X] T018 [US4] Handle special Pylance-narrowing assert at line 25221 in `MistHelper.py`: replace `assert self.selected_template is not None  # Type narrowing for Pylance` with `if self.selected_template is None: raise ValueError("Template not selected")` — this pattern satisfies both FR-006 and Pylance control-flow narrowing; remove `# nosec B101`
- [X] T019 [US4] Replace B101 template-selection asserts at lines 25236, 25352, 25406, 25492 in `MistHelper.py` with explicit `ValueError` raises (e.g., `if self.selected_template is None: raise ValueError("Template must be selected")`); remove `# nosec B101`
- [X] T020 [US4] Replace B101 WLAN-selection assert at line 39243 and SSH client asserts at lines 45588, 45698, 45752 in `MistHelper.py` with explicit `RuntimeError` raises (e.g., `if self.client is None: raise RuntimeError("No active SSH connection")`); remove `# nosec B101`
- [X] T021 [US4] Replace B101 SSH runner assert at line 46429 and credential validation asserts at lines 47488, 47489 in `MistHelper.py` with explicit `RuntimeError`/`ValueError` raises; remove `# nosec B101`
- [X] T022 [US4] Run `Select-String -Path MistHelper.py -Pattern 'nosec B101'` to confirm zero remaining; run `bandit -r MistHelper.py --tests B101 2>&1 | Select-String 'Issue|No issues'` (SC-002); run `python -m py_compile MistHelper.py` (SC-009); run `python MistHelper.py --test` (skip 14, 18, 63-65, 90-100) to confirm no behavioral regression (SC-007)

**Checkpoint**: US4 complete — all 20 production asserts replaced with explicit raises; zero B101 findings.

---

## Phase 7: User Story 5 — Replace Magic HTTP Status Code with Named Constant (Priority: P2)

**Goal**: Replace `status_code != 200` at line 1062 in `src/network/routing_utils.py` with
`status_code != requests.codes.ok`, eliminating the magic number.

**Independent Test**: `ruff check src/network/routing_utils.py` reports no PLR2004 on line 1062.
Routing behavior is functionally identical.

- [X] T023 [P] [US5] Replace `status_code != 200` with `status_code != requests.codes.ok` at line 1062 in `src/network/routing_utils.py`; confirm `import requests` is already present (research.md confirms it is); remove `# noqa: PLR2004` annotation from that line
- [X] T024 [US5] Run `python -m ruff check src/network/routing_utils.py` to verify no PLR2004 on line 1062 (SC-004); run `Select-String -Path src/network/routing_utils.py -Pattern '!= 200|requests.codes.ok' | Select-Object LineNumber, Line` to confirm the replacement

**Checkpoint**: US5 complete — magic number eliminated; named constant in place.

---

## Phase 8: P2 Gate Check (US4 + US5)

**Purpose**: Verify all P2 stories meet their success criteria before starting P3 refactoring.

- [X] T025 Run full P2 gate battery and confirm all pass: `python -m py_compile MistHelper.py` (SC-009), `python -m ruff check MistHelper.py`, `python -m ruff check src/network/routing_utils.py` (SC-004), `bandit -r MistHelper.py` (SC-001, SC-002), `python MistHelper.py --test` (skip 14, 18, 63-65, 90-100) (SC-007)

**Checkpoint**: P2 gate green. Begin P3 PLR0913 refactoring.

---

## Phase 9: User Story 6 — Refactor Over-Parameterized Functions to Config Dataclasses (Priority: P3)

**Goal**: Refactor all PLR0913-suppressed functions (6+ parameters) to accept stdlib `@dataclass`
config objects. One dataclass per function (or shared where signatures are identical). All call
sites updated in the same commit as each function. Run `python MistHelper.py --test` after
each individual function refactor before proceeding to the next.

**Independent Test**: Each refactored function can be tested independently. `ruff check` on
each file reports no PLR0913 for the refactored functions. Full test suite passes after all refactors.

---

### Phase 9a: csv_comparator.py Refactor (Independent — Different File)

- [X] T026 [P] [US6] Define `ComparisonItemConfig` dataclass in `src/inventory/csv_comparator.py` co-located with its class (per data-model.md: 8 fields — `device`, `device_serial`, `mist_address`, `comparison_address`, `comparison_result`, `week_key`, `mismatch_type`, `validation_result`); add `from dataclasses import dataclass` and `from typing import Any` imports
- [X] T027 [US6] Refactor `_build_mismatch_item` at line 1085 in `src/inventory/csv_comparator.py` to accept a single `ComparisonItemConfig` parameter; update all call sites in the same file to construct and pass the dataclass; remove `# noqa: PLR0913`
- [X] T028 [US6] Refactor `_build_diff_item` at line 1128 in `src/inventory/csv_comparator.py` to accept `ComparisonItemConfig` (shared with `_build_mismatch_item`); update all call sites; remove `# noqa: PLR0913`
- [X] T029 [US6] Run `python -m ruff check src/inventory/csv_comparator.py` (no PLR0913 for refactored functions, SC-008) and `python MistHelper.py --test` (skip 14, 18, 63-65, 90-100) to verify no regression

---

### Phase 9b: routing_utils.py Refactors (Independent — Different File, Parallelizable with 9a)

- [X] T030 [P] [US6] Define `RoutingTableContext` dataclass in `src/network/routing_utils.py` co-located with its class (per data-model.md: 6 fields — `websocket_manager`, `session_id`, `device_id`, `device_info`, `payload`, `debug_mode`); add `from dataclasses import dataclass` and `from typing import Any` imports if not present
- [X] T031 [US6] Refactor `_process_routing_table_results` at line 1451 in `src/network/routing_utils.py` to accept `RoutingTableContext`; update all call sites; remove `# noqa: PLR0913`
- [X] T032 [US6] Refactor `_display_routing_table_output` at line 1480 in `src/network/routing_utils.py` to accept `RoutingTableContext` plus a separate `result` argument (keep `result` explicit, not in the dataclass, to preserve single-responsibility between process and display); update all call sites; remove `# noqa: PLR0913`
- [X] T033 [P] [US6] Define `SsrRouteQuery` dataclass in `src/network/routing_utils.py` (per data-model.md: 8 string filter fields — `protocol_input`, `prefix_input`, `vrf_input`, `neighbor_input`, `route_direction`, `node_input`, `interval_input`, `duration_input`)
- [X] T034 [US6] Refactor `_build_ssr_payload` at line 1656 in `src/network/routing_utils.py` to accept `SsrRouteQuery`; update all call sites; remove `# noqa: PLR0913`
- [X] T035 [US6] Inspect signatures of `_process_ssr_route_results` at line 1779 and `_display_ssr_route_output` at line 1811 in `src/network/routing_utils.py`; if shared parameter subset >= 5 fields, define `SsrRouteContext` dataclass per data-model.md placeholder; if signatures diverge significantly, create two separate dataclasses (`SsrProcessContext`, `SsrDisplayContext`); refactor both functions; update all call sites; remove `# noqa: PLR0913`
- [X] T036 [US6] Run `python -m ruff check src/network/routing_utils.py` (no PLR0913 for refactored functions, SC-008) and `python MistHelper.py --test` (skip 14, 18, 63-65, 90-100) to verify no regression

---

### Phase 9c: MistHelper.py PLR0913 Refactors (Sequential — Hot File, One at a Time)

- [X] T037 [US6] Find all `SiteDataFetcher(` call sites in `MistHelper.py` (`Select-String -Path MistHelper.py -Pattern 'SiteDataFetcher\(' | Select-Object LineNumber, Line`); define `SiteDataFetcherConfig` dataclass in `MistHelper.py` co-located with `SiteDataFetcher` class (per data-model.md: `fetch_function`, `filename`, `description`, `device_type="all"`, `site_id=None`, `device_id=None`); refactor `__init__` at line 5626 to accept the config object; update all call sites in the same commit; remove `# noqa: PLR0913`
- [X] T038 [US6] Run `python MistHelper.py --test` (skip 14, 18, 63-65, 90-100) and `python -m ruff check MistHelper.py` after T037 to confirm no regression before next function
- [X] T039 [US6] Inspect `_report_rf_template_results` at line 26054 in `MistHelper.py`; read its full parameter list; find all call sites (`Select-String -Path MistHelper.py -Pattern '_report_rf_template_results\(' | Select-Object LineNumber, Line`); define a named config dataclass (e.g., `RfTemplateResultsConfig`) co-located with its class; refactor function to accept the config; update all call sites; remove `# noqa: PLR0913`
- [X] T040 [US6] Run `python MistHelper.py --test` (skip 14, 18, 63-65, 90-100) and `python -m ruff check MistHelper.py` after T039 to confirm no regression before next function
- [X] T041 [US6] Inspect `_enrich_device_context` at line 38816 in `MistHelper.py`; read its full parameter list; find all call sites (`Select-String -Path MistHelper.py -Pattern '_enrich_device_context\(' | Select-Object LineNumber, Line`); define a named config dataclass (e.g., `DeviceContextConfig`) co-located with its class; refactor function to accept the config; update all call sites; remove `# noqa: PLR0913`
- [X] T042 [US6] Run `python MistHelper.py --test` (skip 14, 18, 63-65, 90-100) and `python -m ruff check MistHelper.py` after T041 to confirm no regression before next function
- [X] T043 [US6] Inspect the function at line 44107 in `MistHelper.py`; read its name and full parameter list; find all call sites; define an appropriately named config dataclass co-located with its class; refactor function to accept the config; update all call sites; remove `# noqa: PLR0913`
- [X] T044 [US6] Run `python MistHelper.py --test` (skip 14, 18, 63-65, 90-100) and `python -m ruff check MistHelper.py` after T043 to confirm no regression

**Checkpoint**: US6 complete — all PLR0913-flagged functions refactored to dataclass config objects; full test suite green.

---

## Phase 10: P3 Gate Check (all PLR0913 refactors)

**Purpose**: Verify the complete US6 work meets SC-007 and SC-008 before stale cleanup.

- [X] T045 Run full Phase 2 gate per plan.md task 2.8: `python -m ruff check src/inventory/csv_comparator.py` (no PLR0913, SC-008), `python -m ruff check src/network/routing_utils.py` (no PLR0913, SC-008), `python -m ruff check MistHelper.py`, `bandit -r MistHelper.py` (SC-001, SC-002), `python MistHelper.py --test` (skip 14, 18, 63-65, 90-100) (SC-007)

**Checkpoint**: P3 gate green. Proceed to stale annotation cleanup (requires US1 merged/active).

---

## Phase 11: Stale Annotation Cleanup (Requires US1 Complete)

**Purpose**: Use the `warn_unused_ignores = true` setting (enabled in US1) to systematically
remove `# type: ignore` annotations that have become unnecessary as the codebase has gained
type coverage. This phase MUST run after Phase 2 (US1) is committed.

**Independent Test**: Suppression count is measurably lower than Phase 1 baseline (SC-005).
Full test suite passes after all annotation removals.

- [X] T046 Run `mypy --config-file pyproject.toml MistHelper.py 2>&1 | Select-String 'unused-ignore'` and capture all "unused-ignore" warnings; also run against `src/` modules; record every file, line number, and annotation flagged
- [X] T047 For each "unused-ignore" warning: read the annotation and verify it is truly stale (not a load-bearing suppression for a third-party library with incomplete stubs); remove only confirmed stale `# type: ignore` annotations from their source files; keep any that guard genuine third-party stub gaps with a short justification comment
- [X] T048 Run `python -m py_compile MistHelper.py` and `python MistHelper.py --test` (skip 14, 18, 63-65, 90-100) to confirm no regression from annotation removals; re-run suppression count (`Select-String -Path MistHelper.py,starlink_dashboard.py,'src\**\*.py' -Pattern '# type: ignore|# noqa|# nosec' | Measure-Object`) and verify count is lower than Phase 1 baseline (SC-005)

**Checkpoint**: Stale annotations removed; SC-005 satisfied.

---

## Phase 12: Polish & Final Gate

**Purpose**: Update documentation, run the complete final gate battery, confirm all success
criteria are met, and prepare the branch for PR.

- [X] T049 Verify final suppression count across `MistHelper.py`, `starlink_dashboard.py`, and `src/**/*.py` is strictly lower than the baseline captured in T002 (SC-005 final verification)
- [X] T050 Update `CHANGELOG.md` with a version entry (format `YY.MM.DD.HH.MM` UTC) for `chore/189-quality-gate-remediation` documenting: `warn_unused_ignores` enabled, dead code/imports removed from `starlink_dashboard.py`, `os.system` replaced with `subprocess.run`, 20 production asserts replaced with explicit raises, magic HTTP constant replaced, PLR0913 functions refactored to dataclass config objects
- [X] T051 Run the complete final gate battery and confirm all pass: `python -m py_compile MistHelper.py` (SC-009), `python -m ruff check MistHelper.py`, `python -m ruff check starlink_dashboard.py` (SC-003), `python -m ruff check src/inventory/csv_comparator.py` (SC-008), `python -m ruff check src/network/routing_utils.py` (SC-004, SC-008), `bandit -r MistHelper.py` (SC-001, SC-002), `mypy --config-file pyproject.toml MistHelper.py` (SC-006), `python MistHelper.py --test` skip 14 18 63-65 90-100 (SC-007)

**Checkpoint**: All 9 success criteria met. Branch is ready for PR.

---

## Dependency Graph

```text
T001─T002─T003─T004 (baseline capture, parallel)
         │
         ▼
   T005─T006 (US1: pyproject.toml) ──────────────────► T046─T047─T048 (Phase 11 stale cleanup)
   T007─T008─T009─T010 (US2: starlink_dashboard.py)
   T011─T012─T013─T014 (US3: os.system)
         │
         ▼
        T015 (P1 Gate) ───────────────────────────────────────────────────┐
         │                                                                  │
         ▼                                                                  │
   T016─T017─T018─T019─T020─T021─T022 (US4: B101 asserts)                 │
   T023─T024 (US5: magic constant)                                         │
         │                                                                  │
         ▼                                                                  │
        T025 (P2 Gate)                                                      │
         │                                                                  │
         ▼                                                                  │
   T026─T027─T028─T029 (US6 9a: csv_comparator.py, parallel with 9b)       │
   T030─T031─T032─T033─T034─T035─T036 (US6 9b: routing_utils.py)          │
   T037─T038─T039─T040─T041─T042─T043─T044 (US6 9c: MistHelper.py)        │
         │                                                                  │
         ▼                                                                  │
        T045 (P3 Gate) ◄─────────────────────────────────────────────────┘
         │
         ▼
   T046─T047─T048 (Phase 11: stale cleanup)
         │
         ▼
   T049─T050─T051 (Phase 12: polish & final gate)
```

**Parallel opportunities per phase**:
- **Phase 1**: T002, T003, T004 run simultaneously (different queries, no dependencies)
- **Phase 3**: T007 and T008 are independent edits on separate lines of `starlink_dashboard.py`
- **Phases 2, 3, 4**: US1, US2, US3 can proceed in parallel (different files, no cross-dependencies)
- **Phase 9**: Phase 9a (csv_comparator.py) and Phase 9b (routing_utils.py) run fully in parallel with each other; Phase 9c (MistHelper.py) is sequential within itself
- **T023 (US5)** is parallelizable with the US4 assert work (different file)

---

## Implementation Strategy

**MVP scope** (minimum to merge with value): Phase 2 (US1) alone — one line, zero risk, immediate
ROI for ongoing type annotation work. Can be merged as a standalone micro-PR.

**Recommended execution order**:
1. **Immediately valuable and trivially safe**: US1 (T005-T006), US2 (T007-T010), US5 (T023-T024) — can batch into one PR
2. **Security improvement**: US3 (T011-T014) — os.system replacement, own PR or bundled with above
3. **Largest P1 batch**: US4 (T016-T022) — 20 assert replacements, own PR due to size
4. **Architecture work**: US6 (T026-T044) — one PR per file (3 PRs: csv_comparator, routing_utils, MistHelper)
5. **Cleanup pass**: Phase 11 stale annotations — own PR after US1 merged and `warn_unused_ignores` is active in CI

**Total task count**: 51
**Tasks by user story**:
- US1: 2 tasks
- US2: 4 tasks
- US3: 4 tasks
- US4: 7 tasks
- US5: 2 tasks
- US6: 19 tasks
- Gates + setup + polish: 13 tasks
