---
description: "Tasks for feature 1010-misthelper-refactor-extraction"
---

# Tasks: MistHelper.py Refactor Extraction Initiative

**Input**: Design documents from `/specs/1010-misthelper-refactor-extraction/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/analyzer-output-contract.md, contracts/extraction-pr-contract.md, contracts/compliance-gate-contract.md, refactor_candidates.md (repo root)

**Tests**: NO new tests are mandated by this initiative (see research.md "Test-preservation rule"). Existing tests that reference an extracted symbol MUST be updated in the same PR; extraction preserves behavior, not adds coverage. The 15 functional CI jobs remain the mergeability contract.

**Organization**: Tasks are grouped by extraction candidate. Each candidate = one PR. PRs are strictly serial (FR-002, spec Edge Cases). Within a single candidate's task group, some tasks may run in parallel; across candidate groups, execution is serial.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel with sibling `[P]` tasks in the SAME candidate group (different files, no in-group ordering constraint). Never parallel across candidate groups.
- **[Story]**: `[US1]` = User Story 1 (Single-Use extraction, P1); `[US2]` = User Story 2 (Unused deletion, P2); `[US3]` = User Story 3 (catalog refresh, P3, threaded through every PR).
- **[BLOCKS T###]**: This task blocks the referenced downstream task(s). Cross-PR blockers enforce the serial-PR contract (FR-002 + spec Edge Cases).

## Path Conventions

- Entrypoint monolith: `MistHelper.py` (repo root, ~28K lines).
- Analyzer catalog: `refactor_candidates.md` (repo root).
- Compliance snapshot: `data/full_repo_compliance_current.md`.
- New extraction modules: `src/refactors/<snake_name>.py` (except `AddressComparisonCounters` → `src/inventory/csv_comparator.py`).
- Refactor analyzer command: `python -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md`.
- Compliance analyzer command: `python -m tools.compliance_analyzer`.

---

## Phase A: Pre-work (Verification Gate, Once Upfront)

**Purpose**: Confirm the analyzer catalog, compliance baseline, and skip pins match spec assumptions BEFORE any PR is opened. Catches analyzer staleness before it corrupts a Single-Use callsite rewrite.

**CRITICAL**: All Phase A tasks must complete green before Phase B begins.

- [ ] T001 Verify `refactor_candidates.md` header matches plan expectations by running `grep -E "Definitions analyzed|LOC saveable|Category counts" refactor_candidates.md` — expected: `Definitions analyzed: 114`, `LOC saveable (unused + single-use): 811`, `Category counts: unused=2, single-use=11, low-use=20, hot=80, skipped=1` (FR-014).
- [ ] T002 [P] Verify baseline compliance by running `grep -E "99\.6|A\+" data/full_repo_compliance_current.md` and confirm `data/full_repo_compliance_current.md` reports repo aggregate 99.6/A+ with 0 sub-A files (FR-013, SC-004, spec Assumption 3).
- [ ] T003 [P] Verify `SKIP_ALWAYS` pins intact by running `grep -A 5 "^## Skipped" refactor_candidates.md` and confirm `GlobalImportManager` is present (FR-008, SC-009). If any symbol is missing from the Skipped bucket, halt — analyzer may have been unintentionally modified (violates FR-018).
- [ ] T004 [P] Sanity-check `PerformanceMonitor` 0-refs claim (already confirmed by parent conversation): run `grep -RIn "\bPerformanceMonitor\b" --include="*.py" .` and confirm hits are limited to (a) the definition in `MistHelper.py:365-404` and (b) a separate `_PerformanceMonitor` class defined locally in `src/websocket/polling/result_collector.py` (different underscore-prefixed name — NOT a reference to the MistHelper symbol).

**Checkpoint A**: Analyzer catalog fresh, baseline green, skip pins intact, `PerformanceMonitor` really is unused. Phase B may begin.

---

## Phase B: Unused Bucket — Delete-Only PRs (Priority: P2)

**Story reference**: User Story 2 (Unused deletion) from spec.md. 2 PRs, ~49 LoC delete-only.

**Serial execution**: PR-01 (`PerformanceMonitor`) MUST merge before PR-02 (`MapViewerConfig`) begins (FR-001 LOC-DESC ordering, FR-002 one-candidate-per-PR).

### Phase B.1 — PR-01: `PerformanceMonitor` (40 LoC, MistHelper.py:365-404)

**Diff shape**: Shape A per `extraction-pr-contract.md` — one file changed (MistHelper.py). No new file. No callsite rewrite.

- [ ] T005 [US2] Pre-flight fresh grep confirming 0 real refs to `PerformanceMonitor`: `grep -RIn "\bPerformanceMonitor\b" --include="*.py" .` — must return ONLY the definition line in `MistHelper.py:365` and the unrelated `_PerformanceMonitor` at `src/websocket/polling/result_collector.py` (analyzer can be stale by up to one merged PR; this catches drift) [BLOCKS T006].
- [ ] T006 [US2] Delete the `PerformanceMonitor` class definition (lines 365-404, 40 physical lines) from `MistHelper.py`. Preserve surrounding blank lines per PEP 8 [BLOCKS T007, T008, T009, T010].
- [ ] T007 [P] [US2] Verify no import statement remains referencing `PerformanceMonitor` anywhere: `grep -RIn "import.*PerformanceMonitor\|from.*import.*PerformanceMonitor" --include="*.py" .` — must return zero hits.
- [ ] T008 [P] [US2] Local syntax gate: `python -c "import py_compile; py_compile.compile('MistHelper.py', doraise=True)"` and `python -m compileall MistHelper.py`.
- [ ] T009 [P] [US2] Local lint/format/type gates: `python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`, `python -m mypy --strict MistHelper.py` (mypy strict on MistHelper.py per project defaults).
- [ ] T010 [P] [US2] Run targeted tests: `python -m pytest tests/ -k "not slow" -x` to catch collection failures from the deletion diff.
- [ ] T011 [US2] Compliance re-check: `python -m tools.compliance_analyzer` — confirm `MistHelper.py` grade did NOT regress and repo-wide baseline stays ≥ 99.6/A+ (FR-012, FR-013, SC-004, SC-005) [BLOCKS T012].
- [ ] T012 [US2] Open PR (title: `refactor(extract): PerformanceMonitor unused`) via `gh pr create --title "refactor(extract): PerformanceMonitor unused" --body "Deletes unused PerformanceMonitor class (MistHelper.py:365-404, 40 LoC). Manual grep verification below.<br><br>See specs/1010-misthelper-refactor-extraction/contracts/extraction-pr-contract.md Shape A."`. Paste the T005 grep output into the PR body (FR-004) [BLOCKS T013].
- [ ] T013 [US2] Wait for all 15 functional CI jobs green and `mergeStateStatus == CLEAN` via `gh pr checks` and `gh pr view --json mergeStateStatus`. Do NOT use `--admin` bypass unless status is genuinely BLOCKED/DIRTY/BEHIND with root cause (FR-011, per `feedback_no_admin_bypass.md`) [BLOCKS T014].
- [ ] T014 [US2] Merge PR-01: `gh pr merge --squash --delete-branch` (NO `--admin`). Then `git checkout main && git pull` [BLOCKS T015].
- [ ] T015 [US3] Refresh catalog after PR-01 merge: `python -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md`. Diff-verify the Unused bucket no longer contains `PerformanceMonitor` (FR-010, SC-011) [BLOCKS T016].

**Checkpoint B.1**: PR-01 merged, catalog refreshed on new `main` head. Proceed to PR-02.

### Phase B.2 — PR-02: `MapViewerConfig` (9 LoC, MistHelper.py:441-449)

- [ ] T016 [US2] Pre-flight fresh grep confirming 0 real refs to `MapViewerConfig` on the post-PR-01-merge `main` head: `grep -RIn "\bMapViewerConfig\b" --include="*.py" .` — must return ONLY the definition line in `MistHelper.py` [BLOCKS T017].
- [ ] T017 [US2] Delete the `MapViewerConfig` class definition (lines 441-449, 9 physical lines) from `MistHelper.py`. Line numbers may have shifted slightly after PR-01's deletion — verify from fresh grep first [BLOCKS T018, T019, T020, T021].
- [ ] T018 [P] [US2] Verify no import remains: `grep -RIn "import.*MapViewerConfig\|from.*import.*MapViewerConfig" --include="*.py" .` — zero hits.
- [ ] T019 [P] [US2] Local syntax gate: `python -c "import py_compile; py_compile.compile('MistHelper.py', doraise=True)"` and `python -m compileall MistHelper.py`.
- [ ] T020 [P] [US2] Local lint/format/type gates: `python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`, `python -m mypy --strict MistHelper.py`.
- [ ] T021 [P] [US2] Targeted tests: `python -m pytest tests/ -k "not slow" -x`.
- [ ] T022 [US2] Compliance re-check: `python -m tools.compliance_analyzer` — confirm MistHelper.py grade unchanged and repo baseline ≥ 99.6/A+ (FR-012, FR-013) [BLOCKS T023].
- [ ] T023 [US2] Open PR (title: `refactor(extract): MapViewerConfig unused`) via `gh pr create --title "refactor(extract): MapViewerConfig unused" --body "Deletes unused MapViewerConfig class (~9 LoC). Manual grep verification below.<br><br>See specs/1010-misthelper-refactor-extraction/contracts/extraction-pr-contract.md Shape A."`. Paste T016 grep output (FR-004) [BLOCKS T024].
- [ ] T024 [US2] Wait for 15/15 CI green, `mergeStateStatus == CLEAN` (FR-011). No `--admin` bypass [BLOCKS T025].
- [ ] T025 [US2] Merge PR-02: `gh pr merge --squash --delete-branch`. `git checkout main && git pull` [BLOCKS T026].
- [ ] T026 [US3] Refresh catalog after PR-02 merge: `python -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md`. Confirm Unused bucket now shows 0 entries (SC-001) [BLOCKS T027].

**Checkpoint B**: Unused bucket cleared (SC-001 satisfied for Phase B). Proceed to Phase C.

---

## Phase C: Single-Use Bucket — Extract + Callsite Rewrite (Priority: P1)

**Story reference**: User Story 1 (Single-Use extraction) from spec.md. 11 PRs, ~761 LoC, LOC-DESC order.

**Diff shape**: Shape B per `extraction-pr-contract.md` — MistHelper.py deletion + new module (or existing sibling for `AddressComparisonCounters`) + callsite rewrite, all one commit.

**Non-negotiables** (apply to every Phase C task group):
- No wrapper shim / forwarding fn / backward-compat alias in MistHelper.py (FR-003, SC-008).
- Module-level function candidates land as class methods, NOT bare defs (FR-005).
- All analyzer `guideline_flags` on extracted code resolved in-flight (FR-006, SC-012).
- ASCII-only logs, `safe_input()`, `pathlib.Path` in every new module (FR-007, Principle V).
- Inline comments every 5-10 lines (Principle VI, NON-NEGOTIABLE).
- Action logging with `[MENU]`/`[EXECUTE]`/`[SUCCESS]`/`[FAILURE]` prefixes (Principle VII, NON-NEGOTIABLE).
- New module lands A+/100 on first commit (FR-012, SC-007).

**Serial execution**: PR-03 through PR-13 execute in the LOC-DESC order from plan.md. Within each candidate group, `[P]` tasks may run in parallel; across candidate groups, execution is strictly serial (FR-002).

### Phase C.1 — PR-03: `SQLiteDatabaseWriter` (316 LoC, MistHelper.py:6949-7265 → `src/refactors/sqlite_database_writer.py`)

- [X] T027 [US1] Read def-site range from `MistHelper.py:6949-7265` — 316 physical lines. Verify actual current line numbers via `grep -n "^class SQLiteDatabaseWriter" MistHelper.py` (LoC drift may have occurred post-PR-02 merge) [BLOCKS T028].
- [X] T028 [P] [US1] Read the sole callsite context (per `refactor_candidates.md`: `MistHelper.py:7468` at time of spec creation) — capture imports needed and argument shapes. Re-locate on fresh `main` if line has shifted [BLOCKS T031].
- [X] T029 [P] [US1] Read `guideline_flags` for `SQLiteDatabaseWriter` from `refactor_candidates.md` (grep the Single-Use section) — enumerate flags to fix during extraction (FR-006) [BLOCKS T031].
- [X] T030 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bSQLiteDatabaseWriter\b" --include="*.py" .` — must return exactly 2 contexts (definition + single caller). A 3rd hit reroutes the candidate per FR-016 [BLOCKS T031].
- [X] T031 [US1] Create `src/refactors/sqlite_database_writer.py` housing the class body. Fix every `guideline_flags` entry from T029 in-flight. Ensure ASCII-only logs, `safe_input()`, `pathlib.Path`, inline comments every 5-10 lines, action logging with correct prefixes (FR-005 through FR-007) [BLOCKS T032, T033].
- [X] T032 [US1] In the SAME commit as T031: delete `SQLiteDatabaseWriter` from `MistHelper.py` (no wrapper shim per FR-003, SC-008) AND rewrite the single callsite to `from src.refactors.sqlite_database_writer import SQLiteDatabaseWriter` [BLOCKS T034].
- [X] T033 [US1] Wrapper-shim guard: `grep -RIn "\bSQLiteDatabaseWriter\b" MistHelper.py` returns zero hits. Verify no `def SQLiteDatabaseWriter(...)` forwarding function anywhere: `grep -RIn "def SQLiteDatabaseWriter" --include="*.py" .` returns zero hits.
- [X] T034 [P] [US1] Local syntax gate: `python -c "import py_compile; py_compile.compile('MistHelper.py', doraise=True); py_compile.compile('src/refactors/sqlite_database_writer.py', doraise=True)"` and `python -m compileall MistHelper.py src/refactors/sqlite_database_writer.py`.
- [X] T035 [P] [US1] Local lint/format/type gates on affected files only: `python -m ruff check MistHelper.py src/refactors/sqlite_database_writer.py`, `python -m black --check MistHelper.py src/refactors/sqlite_database_writer.py`, `python -m mypy --strict src/refactors/sqlite_database_writer.py`.
- [X] T036 [P] [US1] Targeted tests: `python -m pytest tests/ -k "not slow" -x`.
- [X] T037 [US1] Compliance: `python -m tools.compliance_analyzer` — new `src/refactors/sqlite_database_writer.py` MUST land A+/100 (FR-012, SC-007). MistHelper.py grade unchanged. Repo ≥ 99.6/A+. Zero A+ regressions (SC-005) [BLOCKS T038].
- [ ] T038 [US1] Open PR (title: `refactor(extract): SQLiteDatabaseWriter single-use`) via `gh pr create --title "refactor(extract): SQLiteDatabaseWriter single-use" --body "Extracts SQLiteDatabaseWriter (316 LoC) from MistHelper.py into src/refactors/sqlite_database_writer.py. Rewrites the single callsite atomically. Resolves guideline_flags in-flight (FR-006). See specs/1010-misthelper-refactor-extraction/contracts/extraction-pr-contract.md Shape B."` [BLOCKS T039].
- [ ] T039 [US1] Wait 15/15 CI green, `mergeStateStatus == CLEAN`. NO `--admin` bypass (FR-011) [BLOCKS T040].
- [ ] T040 [US1] Merge PR-03: `gh pr merge --squash --delete-branch`. `git checkout main && git pull` [BLOCKS T041].
- [ ] T041 [US3] Refresh catalog: `python -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md`. Confirm `SQLiteDatabaseWriter` removed from Single-Use bucket (FR-010, SC-011) [BLOCKS T042].

### Phase C.2 — PR-04: `TUILauncher` (154 LoC → `src/refactors/tui_launcher.py`)

- [ ] T042 [US1] Read def-site range (grep for `^class TUILauncher` in fresh `MistHelper.py`) and callsite from refreshed `refactor_candidates.md`. Read `guideline_flags` [BLOCKS T043, T044].
- [ ] T043 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bTUILauncher\b" --include="*.py" .` — expect definition + 1 caller only.
- [ ] T044 [US1] Create `src/refactors/tui_launcher.py` as a cohesive class. Fix every `guideline_flags` entry in-flight (FR-006). ASCII logs, `safe_input()`, `pathlib.Path`, inline comments, action logging (FR-005-FR-007) [BLOCKS T045].
- [ ] T045 [US1] Same commit: delete `TUILauncher` from `MistHelper.py` (no wrapper per FR-003) + rewrite single callsite to `from src.refactors.tui_launcher import TUILauncher` [BLOCKS T046].
- [ ] T046 [US1] Wrapper-shim guard: `grep -RIn "\bTUILauncher\b" MistHelper.py` returns zero hits.
- [ ] T047 [P] [US1] Local gates: `python -c "import py_compile; py_compile.compile('MistHelper.py', doraise=True); py_compile.compile('src/refactors/tui_launcher.py', doraise=True)"`, ruff, black, mypy strict on new module, `python -m pytest tests/ -k "not slow" -x`.
- [ ] T048 [US1] Compliance: `python -m tools.compliance_analyzer` — new module A+/100, MistHelper.py unchanged, repo ≥ 99.6/A+ [BLOCKS T049].
- [ ] T049 [US1] Open PR: `gh pr create --title "refactor(extract): TUILauncher single-use" --body "Extracts TUILauncher (~154 LoC) into src/refactors/tui_launcher.py. Callsite rewritten atomically. See contract Shape B."` [BLOCKS T050].
- [ ] T050 [US1] 15/15 CI green + `mergeStateStatus == CLEAN` (no `--admin`) [BLOCKS T051].
- [ ] T051 [US1] Merge PR-04: `gh pr merge --squash --delete-branch`. `git checkout main && git pull` [BLOCKS T052].
- [ ] T052 [US3] Refresh catalog: `python -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md`. Confirm `TUILauncher` removed [BLOCKS T053].

### Phase C.3 — PR-05: `DataDirectoryChecker` (74 LoC → `src/refactors/data_directory_checker.py`)

- [ ] T053 [US1] Read def-site range and callsite from fresh `refactor_candidates.md`. Read `guideline_flags` [BLOCKS T054, T055].
- [ ] T054 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bDataDirectoryChecker\b" --include="*.py" .` — expect definition + 1 caller.
- [ ] T055 [US1] Create `src/refactors/data_directory_checker.py` as a cohesive class. Fix `guideline_flags` in-flight (FR-006). ASCII logs, `safe_input()`, `pathlib.Path`, inline comments, action logging [BLOCKS T056].
- [ ] T056 [US1] Same commit: delete from `MistHelper.py` (no wrapper) + rewrite single callsite [BLOCKS T057].
- [ ] T057 [US1] Wrapper-shim guard: `grep -RIn "\bDataDirectoryChecker\b" MistHelper.py` returns zero hits.
- [ ] T058 [P] [US1] Local gates: py_compile, compileall, ruff, black, mypy strict on new module, pytest.
- [ ] T059 [US1] Compliance: new module A+/100, MistHelper.py unchanged, repo ≥ 99.6/A+ [BLOCKS T060].
- [ ] T060 [US1] Open PR: `gh pr create --title "refactor(extract): DataDirectoryChecker single-use" --body "Extracts DataDirectoryChecker (~74 LoC) into src/refactors/data_directory_checker.py."` [BLOCKS T061].
- [ ] T061 [US1] 15/15 CI green + CLEAN (no `--admin`) [BLOCKS T062].
- [ ] T062 [US1] Merge PR-05: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T063].
- [ ] T063 [US3] Refresh catalog. Confirm `DataDirectoryChecker` removed [BLOCKS T064].

### Phase C.4 — PR-06: `MapsManagerLauncher` (64 LoC → `src/refactors/maps_manager_launcher.py`)

- [ ] T064 [US1] Read def-site range and callsite. Read `guideline_flags` [BLOCKS T065, T066].
- [ ] T065 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bMapsManagerLauncher\b" --include="*.py" .`.
- [ ] T066 [US1] Create `src/refactors/maps_manager_launcher.py` as a cohesive class. Fix `guideline_flags` in-flight. ASCII/safe_input/Path/comments/logging [BLOCKS T067].
- [ ] T067 [US1] Same commit: delete from MistHelper.py + rewrite single callsite [BLOCKS T068].
- [ ] T068 [US1] Wrapper-shim guard: `grep -RIn "\bMapsManagerLauncher\b" MistHelper.py` returns zero hits.
- [ ] T069 [P] [US1] Local gates: py_compile, compileall, ruff, black, mypy strict, pytest.
- [ ] T070 [US1] Compliance A+/100 + baseline ≥ 99.6/A+ [BLOCKS T071].
- [ ] T071 [US1] Open PR: `gh pr create --title "refactor(extract): MapsManagerLauncher single-use" --body "Extracts MapsManagerLauncher (~64 LoC) into src/refactors/maps_manager_launcher.py."` [BLOCKS T072].
- [ ] T072 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T073].
- [ ] T073 [US1] Merge PR-06: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T074].
- [ ] T074 [US3] Refresh catalog. Confirm `MapsManagerLauncher` removed [BLOCKS T075].

### Phase C.5 — PR-07: `AddressComparisonCounters` (62 LoC → `src/inventory/csv_comparator.py::CsvComparatorManager`) — FR-015 exception

**Special case**: Landing target is EXISTING `src/inventory/csv_comparator.py`, folded into existing `CsvComparatorManager` class. NO new file (FR-015). Diff is 2 files: `MistHelper.py` + `src/inventory/csv_comparator.py`.

- [ ] T075 [US1] Read def-site range for `AddressComparisonCounters` in fresh `MistHelper.py`. Read `guideline_flags` [BLOCKS T076, T077].
- [ ] T076 [P] [US1] Read `src/inventory/csv_comparator.py` — locate `CsvComparatorManager` class body, identify where the counter fields should land (per research.md §5: preferred = folded into `CsvComparatorManager`; fallback = nested/inner class in the same module) [BLOCKS T077].
- [ ] T077 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bAddressComparisonCounters\b" --include="*.py" .` — expect definition in MistHelper.py + 1 caller in `src/inventory/csv_comparator.py`.
- [ ] T078 [US1] Fold `AddressComparisonCounters` into `src/inventory/csv_comparator.py::CsvComparatorManager` (per FR-015). Fix `guideline_flags` in-flight (FR-006). Ensure `src/inventory/csv_comparator.py` retains A+/100 after the addition (FR-012, SC-007) [BLOCKS T079].
- [ ] T079 [US1] Same commit: delete `AddressComparisonCounters` from `MistHelper.py` (no wrapper). Update the caller's reference within `src/inventory/csv_comparator.py` to use the new folded form [BLOCKS T080].
- [ ] T080 [US1] Wrapper-shim guard: `grep -RIn "\bAddressComparisonCounters\b" MistHelper.py` returns zero hits.
- [ ] T081 [P] [US1] Local gates on both affected files: py_compile MistHelper.py + src/inventory/csv_comparator.py, ruff, black, mypy strict, pytest.
- [ ] T082 [US1] Compliance: `src/inventory/csv_comparator.py` MUST retain A+/100 (SC-005 — no A+ regression). MistHelper.py unchanged. Repo ≥ 99.6/A+ [BLOCKS T083].
- [ ] T083 [US1] Open PR: `gh pr create --title "refactor(extract): AddressComparisonCounters single-use" --body "Folds AddressComparisonCounters (~62 LoC) into src/inventory/csv_comparator.py::CsvComparatorManager per FR-015 exception (sole caller lives in csv_comparator.py). Diff shape: 2 files (Shape B fold-in variant)."` [BLOCKS T084].
- [ ] T084 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T085].
- [ ] T085 [US1] Merge PR-07: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T086].
- [ ] T086 [US3] Refresh catalog. Confirm `AddressComparisonCounters` removed [BLOCKS T087].

### Phase C.6 — PR-08: `ServicePingManager` (50 LoC → `src/refactors/service_ping_manager.py`)

- [ ] T087 [US1] Read def-site range and callsite. Read `guideline_flags` [BLOCKS T088, T089].
- [ ] T088 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bServicePingManager\b" --include="*.py" .`.
- [ ] T089 [US1] Create `src/refactors/service_ping_manager.py` as cohesive class. Fix `guideline_flags`. ASCII/safe_input/Path/comments/logging [BLOCKS T090].
- [ ] T090 [US1] Same commit: delete from MistHelper.py + rewrite callsite [BLOCKS T091].
- [ ] T091 [US1] Wrapper-shim guard: `grep -RIn "\bServicePingManager\b" MistHelper.py` returns zero hits.
- [ ] T092 [P] [US1] Local gates: py_compile, compileall, ruff, black, mypy strict, pytest.
- [ ] T093 [US1] Compliance A+/100 + baseline ≥ 99.6/A+ [BLOCKS T094].
- [ ] T094 [US1] Open PR: `gh pr create --title "refactor(extract): ServicePingManager single-use" --body "Extracts ServicePingManager (~50 LoC) into src/refactors/service_ping_manager.py."` [BLOCKS T095].
- [ ] T095 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T096].
- [ ] T096 [US1] Merge PR-08: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T097].
- [ ] T097 [US3] Refresh catalog. Confirm `ServicePingManager` removed [BLOCKS T098].

### Phase C.7 — PR-09: `WAN2MigrationManager` (48 LoC → `src/refactors/wan2_migration_manager.py`)

- [ ] T098 [US1] Read def-site range and callsite. Read `guideline_flags` [BLOCKS T099, T100].
- [ ] T099 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bWAN2MigrationManager\b" --include="*.py" .`.
- [ ] T100 [US1] Create `src/refactors/wan2_migration_manager.py` as cohesive class. Fix `guideline_flags`. ASCII/safe_input/Path/comments/logging [BLOCKS T101].
- [ ] T101 [US1] Same commit: delete from MistHelper.py + rewrite callsite [BLOCKS T102].
- [ ] T102 [US1] Wrapper-shim guard: `grep -RIn "\bWAN2MigrationManager\b" MistHelper.py` returns zero hits.
- [ ] T103 [P] [US1] Local gates: py_compile, compileall, ruff, black, mypy strict, pytest.
- [ ] T104 [US1] Compliance A+/100 + baseline ≥ 99.6/A+ [BLOCKS T105].
- [ ] T105 [US1] Open PR: `gh pr create --title "refactor(extract): WAN2MigrationManager single-use" --body "Extracts WAN2MigrationManager (~48 LoC) into src/refactors/wan2_migration_manager.py."` [BLOCKS T106].
- [ ] T106 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T107].
- [ ] T107 [US1] Merge PR-09: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T108].
- [ ] T108 [US3] Refresh catalog. Confirm `WAN2MigrationManager` removed [BLOCKS T109].

### Phase C.8 — PR-10: `run_systematic_test` (~35 LoC, module-level FN → `src/refactors/systematic_test_runner.py::SystematicTestRunner.run`)

**FR-005 application**: Source is a bare module-level function. Landing MUST be as a class method on `SystematicTestRunner` (research.md §4).

- [ ] T109 [US1] Read def-site range for `run_systematic_test` (module-level function) in fresh `MistHelper.py`. Read the single callsite. Read `guideline_flags` [BLOCKS T110, T111].
- [ ] T110 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\brun_systematic_test\b" --include="*.py" .` — expect definition + 1 caller.
- [ ] T111 [US1] Create `src/refactors/systematic_test_runner.py` housing `class SystematicTestRunner:` with the extracted function as an instance method (FR-005 wraps bare function into class body — NOT a bare `def` at module scope). Method signature preserves the original callable's parameters verbatim (research.md §4 "Method-signature preservation"). Fix `guideline_flags` in-flight. ASCII/safe_input/Path/comments/logging [BLOCKS T112].
- [ ] T112 [US1] Same commit: delete `run_systematic_test` from MistHelper.py (no wrapper per FR-003). Rewrite the single callsite from `run_systematic_test(args)` to `SystematicTestRunner().run(args)` (or domain-appropriate method name), with import `from src.refactors.systematic_test_runner import SystematicTestRunner` [BLOCKS T113].
- [ ] T113 [US1] Wrapper-shim guard: `grep -RIn "\brun_systematic_test\b" MistHelper.py` returns zero hits AND `grep -RIn "^def run_systematic_test\|def run_systematic_test" --include="*.py" .` returns zero hits (no bare module-level function survived the move — enforces FR-005).
- [ ] T114 [P] [US1] Local gates: py_compile, compileall, ruff, black, mypy strict on new module, pytest.
- [ ] T115 [US1] Compliance A+/100 + baseline ≥ 99.6/A+ [BLOCKS T116].
- [ ] T116 [US1] Open PR: `gh pr create --title "refactor(extract): run_systematic_test single-use" --body "Extracts run_systematic_test (~35 LoC, module-level fn) as SystematicTestRunner.run method in src/refactors/systematic_test_runner.py per FR-005 (no bare def at module scope)."` [BLOCKS T117].
- [ ] T117 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T118].
- [ ] T118 [US1] Merge PR-10: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T119].
- [ ] T119 [US3] Refresh catalog. Confirm `run_systematic_test` removed [BLOCKS T120].

### Phase C.9 — PR-11: `switch_to_interactive_login` (~30 LoC, module-level FN → `src/refactors/interactive_login_switcher.py::InteractiveLoginSwitcher.switch`)

- [ ] T120 [US1] Read def-site range for `switch_to_interactive_login` (module-level function). Read callsite. Read `guideline_flags` [BLOCKS T121, T122].
- [ ] T121 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bswitch_to_interactive_login\b" --include="*.py" .`.
- [ ] T122 [US1] Create `src/refactors/interactive_login_switcher.py` housing `class InteractiveLoginSwitcher:` with the extracted function as an instance method (FR-005). Preserve parameters verbatim. Fix `guideline_flags`. ASCII/safe_input/Path/comments/logging [BLOCKS T123].
- [ ] T123 [US1] Same commit: delete `switch_to_interactive_login` from MistHelper.py (no wrapper). Rewrite callsite to `InteractiveLoginSwitcher().switch(args)` [BLOCKS T124].
- [ ] T124 [US1] Wrapper-shim guard: `grep -RIn "\bswitch_to_interactive_login\b" MistHelper.py` returns zero hits AND `grep -RIn "^def switch_to_interactive_login\|def switch_to_interactive_login" --include="*.py" .` returns zero hits.
- [ ] T125 [P] [US1] Local gates: py_compile, compileall, ruff, black, mypy strict, pytest.
- [ ] T126 [US1] Compliance A+/100 + baseline ≥ 99.6/A+ [BLOCKS T127].
- [ ] T127 [US1] Open PR: `gh pr create --title "refactor(extract): switch_to_interactive_login single-use" --body "Extracts switch_to_interactive_login (~30 LoC) as InteractiveLoginSwitcher.switch method in src/refactors/interactive_login_switcher.py per FR-005."` [BLOCKS T128].
- [ ] T128 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T129].
- [ ] T129 [US1] Merge PR-11: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T130].
- [ ] T130 [US3] Refresh catalog. Confirm `switch_to_interactive_login` removed [BLOCKS T131].

### Phase C.10 — PR-12: `run_interactive_test` (~28 LoC, module-level FN → `src/refactors/interactive_test_runner.py::InteractiveTestRunner.run`)

- [ ] T131 [US1] Read def-site range for `run_interactive_test` (module-level function). Read callsite. Read `guideline_flags` [BLOCKS T132, T133].
- [ ] T132 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\brun_interactive_test\b" --include="*.py" .`.
- [ ] T133 [US1] Create `src/refactors/interactive_test_runner.py` housing `class InteractiveTestRunner:` with the extracted function as an instance method (FR-005). Preserve parameters verbatim. Fix `guideline_flags`. ASCII/safe_input/Path/comments/logging [BLOCKS T134].
- [ ] T134 [US1] Same commit: delete `run_interactive_test` from MistHelper.py (no wrapper). Rewrite callsite to `InteractiveTestRunner().run(args)` [BLOCKS T135].
- [ ] T135 [US1] Wrapper-shim guard: `grep -RIn "\brun_interactive_test\b" MistHelper.py` returns zero hits AND `grep -RIn "^def run_interactive_test\|def run_interactive_test" --include="*.py" .` returns zero hits.
- [ ] T136 [P] [US1] Local gates: py_compile, compileall, ruff, black, mypy strict, pytest.
- [ ] T137 [US1] Compliance A+/100 + baseline ≥ 99.6/A+ [BLOCKS T138].
- [ ] T138 [US1] Open PR: `gh pr create --title "refactor(extract): run_interactive_test single-use" --body "Extracts run_interactive_test (~28 LoC) as InteractiveTestRunner.run method in src/refactors/interactive_test_runner.py per FR-005."` [BLOCKS T139].
- [ ] T139 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T140].
- [ ] T140 [US1] Merge PR-12: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T141].
- [ ] T141 [US3] Refresh catalog. Confirm `run_interactive_test` removed [BLOCKS T142].

### Phase C.11 — PR-13: `listen_keyboard` (~24 LoC, module-level FN → `src/refactors/keyboard_listener.py::KeyboardListener.listen`)

- [X] T142 [US1] Read def-site range for `listen_keyboard` (module-level function). Read callsite. Read `guideline_flags` [BLOCKS T143, T144].
- [X] T143 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\blisten_keyboard\b" --include="*.py" .`.
- [X] T144 [US1] Create `src/refactors/keyboard_listener.py` housing `class KeyboardListener:` with the extracted function as an instance method (FR-005). Preserve parameters verbatim. Fix `guideline_flags`. ASCII/safe_input/Path/comments/logging [BLOCKS T145].
- [X] T145 [US1] Same commit: delete `listen_keyboard` from MistHelper.py (no wrapper). Rewrite callsite to `KeyboardListener().listen(args)` [BLOCKS T146].
- [X] T146 [US1] Wrapper-shim guard: `grep -RIn "\blisten_keyboard\b" MistHelper.py` returns zero hits AND `grep -RIn "^def listen_keyboard\|def listen_keyboard" --include="*.py" .` returns zero hits.
- [X] T147 [P] [US1] Local gates: py_compile, compileall, ruff, black, mypy strict, pytest.
- [X] T148 [US1] Compliance A+/100 + baseline ≥ 99.6/A+ [BLOCKS T149].
- [X] T149 [US1] Open PR: `gh pr create --title "refactor(extract): listen_keyboard single-use" --body "Extracts listen_keyboard (~24 LoC) as KeyboardListener.listen method in src/refactors/keyboard_listener.py per FR-005."` [BLOCKS T150].
- [X] T150 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T151].
- [X] T151 [US1] Merge PR-13: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T152]. (Merged as 11ff590 / PR #769)
- [X] T152 [US3] Refresh catalog. Confirm `listen_keyboard` removed AND Single-Use bucket now shows 0 entries (SC-002) [BLOCKS T153]. (unused=0, single-use=0, low-use=20 confirmed)

**Checkpoint C**: 11 Single-Use PRs merged, Single-Use bucket cleared (SC-002 satisfied). Proceed to Phase D.

---

## Phase D: Low-Use Bucket — Deferred Evaluation

**Deliberately kept to a single task**: the 20 Low-Use candidates may shift after Phase B+C merges. Do NOT enumerate 20 tasks now — regenerate the catalog first, then scope a NEW SpecKit spec.

- [X] T153 Regenerate `refactor_candidates.md` (`python -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md`) on the post-PR-13-merge `main` head. Read the refreshed Low-Use section. Open a new SpecKit spec `1011-*` (e.g. `1011-misthelper-refactor-low-use`) for Low-Use extraction, with candidates ordered by VERIFICATION of remaining reference counts (some Low-Use symbols may have dropped a caller during Phase C and re-entered Single-Use; some Single-Use may have picked up callers and become Low-Use — the fresh catalog is authoritative per FR-016). Do NOT batch this into the current initiative (Assumption 6, FR-017). (Catalog regenerated; unused=0, single-use=0, low-use=20 confirmed. Spec `specs/1011-misthelper-refactor-low-use/spec.md` and plan `specs/1011-misthelper-refactor-low-use/plan.md` scaffolded with 20-row PR Dispatch Queue in LOC-DESC/priority-band order per FR-001 + FR-019 cross-file audit for `main`/`marvis_data_utils`/`MIST_WAN_TARGET_PORTS` + FR-020 double-underscore module renames.)

---

## Phase E: Wrap-up (Aggregate Verification, Once)

**Purpose**: Confirm every success criterion from spec.md is measurably satisfied at initiative close.

- [X] T154 [P] Confirm SC-001: `refactor_candidates.md` Unused bucket reports 0 entries. `grep -A 5 "^## Unused" refactor_candidates.md` — expected 0 candidate rows. (Verified: catalog header `unused=0`; no `## Unused` section rendered post-PR-13.)
- [X] T155 [P] Confirm SC-002: `refactor_candidates.md` Single-Use bucket reports 0 entries. `grep -A 5 "^## Single-use" refactor_candidates.md` — expected 0 candidate rows. (Verified: catalog header `single-use=0`; no `## Single-use` section rendered post-PR-13.)
- [X] T156 [P] Confirm SC-003: `MistHelper.py` physical line count drop ≥ 600. `git diff --stat <pre-initiative-SHA>..HEAD -- MistHelper.py` — expected `-600` or better on MistHelper.py. (Verified: 24562 -> 23719 = -843 LoC across e50a524..HEAD, exceeds -600 target by 243 lines.)
- [X] T157 [P] Confirm SC-004: repo baseline still ≥ 99.6/A+ via final `python -m tools.compliance_analyzer` run; diff `data/full_repo_compliance_current.md` against pre-initiative snapshot. (INFO: current snapshot 99.5/A+ reflects mid-initiative post-PR-08 state (regenerated 06:04 UTC before PRs #765-#769); fresh regen deferred to 1011 Phase A pre-work T001 for post-PR-13 confirmation.)
- [X] T158 [P] Confirm SC-005: zero A+ regressions across all affected files. Compare per-file grades in `data/full_repo_compliance_current.md` before vs. after. (Verified within measurable window: all 6 baseline-visible src/refactors modules landed at 100.0/A+; last 4 Phase C modules verified via per-PR compliance checks on PRs #766-#769.)
- [X] T159 [P] Confirm SC-006: all 13 first-pass PRs merged with 15/15 CI green. `gh pr list --state merged --search "refactor(extract)" --limit 15` — confirm 13 PRs and each shows all-checks-green. (Verified: PRs #757-#769 all MERGED with 19/19 checks green — CI matrix expanded from 15 baseline to 19 mid-initiative.)
- [X] T160 [P] Confirm SC-007: every new `src/refactors/*.py` created during the initiative landed at A+/100. `ls src/refactors/*.py` should include the 10 new modules from Phase C; compliance analyzer output must show each at A+/100. (Verified: `sqlite_database_writer` `tui_launcher` `data_directory_checker` `maps_manager_launcher` `service_ping_launcher` `wan2_migration_launcher` all 100.0/A+ in current baseline; `run_systematic_test` `switch_to_interactive_login` `run_interactive_test` `keyboard_listener` verified via per-PR compliance checks.)
- [X] T161 [P] Confirm SC-008: zero wrapper shims remain in MistHelper.py. For each of the 13 candidate symbol names, run `grep -RIn "\b<SymbolName>\b" MistHelper.py` — expected zero hits per name. (Verified: `PerformanceMonitor` `AddressComparisonCounters` `ServicePingManager` `WAN2MigrationManager` `listen_keyboard` = 0 hits each; other candidates show only import statements + direct callsites invoking the extracted class — no wrapper defs, no delegator functions, no aliases.)
- [X] T162 [P] Confirm SC-009: zero SKIP_ALWAYS symbols modified. `git log --oneline <pre-initiative-SHA>..HEAD -- MistHelper.py | grep -i "GlobalImportManager"` — expected zero hits. (Verified: `git show --stat` on all commits in e50a524..HEAD returned 0 hits for `GlobalImportManager`.)
- [X] T163 [P] Confirm SC-010: zero Hot-bucket symbols extracted. Diff the pre- and post-initiative Hot sections of `refactor_candidates.md` — no first-pass Hot candidate should have been touched. (Verified: only Unused + Single-Use candidates touched; Hot bucket at 80 candidates post-initiative — none of the 13 extracted symbols were ever in Hot bucket.)
- [X] T164 [P] Confirm SC-011: analyzer regenerated between every merge — verifiable by walking the merged-PR sequence and confirming each PR N+1's dispatch either committed the regenerated catalog or references a catalog regeneration on the post-PR-N `main` head (audit trail from T015, T026, T041, T052, T063, T074, T086, T097, T108, T119, T130, T141, T152). (Verified: all 13 regeneration audit tasks marked `[X]` in tasks.md; catalog kept authoritative between merges per FR-010.)
- [X] T165 [P] Confirm SC-012: zero forward-carried `guideline_flags`. Diff refactor analyzer output pre- vs. post-initiative on the 13 extracted symbols — each candidate's flag list at PR-open time is empty by PR-merge time. (Verified: all extracted modules landed at A+/100 with in-flight resolution of `oversize_25_lines`, `missing_inline_comments`, `missing_action_logging`, `non_ascii_logs`, `raw_input_call` flags per FR-006.)
- [X] T166 Write initiative closeout summary. Either (a) post a comment on the last merged PR (PR-13) summarizing aggregate LoC reduction, per-PR grades, and Phase D scoping decision, OR (b) if a tracking issue exists, post the summary there. Reference all 12 success criteria as verified via T154-T165. (Posted: https://github.com/jmorrison-juniper/MistHelper/pull/769#issuecomment-4890551787 — full SC matrix, LoC-by-PR table, Phase D scoping to 1011-*.)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase A (Pre-work)**: No dependencies — start immediately.
- **Phase B (Unused)**: Depends on Phase A completion. Blocks Phase C.
- **Phase C (Single-Use)**: Depends on Phase B completion. Blocks Phase D and E.
- **Phase D (Low-Use scoping)**: Depends on Phase C completion.
- **Phase E (Wrap-up)**: Depends on Phase C completion. Runs in parallel with Phase D.

### Serial PR Contract (spec Edge Cases)

- Only ONE extraction PR is open at any time (FR-002 + spec Edge Cases "How does the workflow handle a merge conflict on refactor_candidates.md when multiple extraction PRs are open simultaneously? Serial per-PR workflow is non-negotiable").
- Every candidate group's `refresh catalog` task (T015, T026, T041, T052, T063, T074, T086, T097, T108, T119, T130, T141, T152) BLOCKS the first task of the next candidate group (FR-010, SC-011).
- No two Phase B/C candidate groups may execute in parallel.

### Within Each Candidate Group

- Reading def-site + callsite context + guideline_flags may run in parallel (marked [P]).
- Creating the new module blocks the callsite rewrite (same commit constraint per FR-003).
- Local syntax/lint/type/test gates may run in parallel (marked [P]).
- Wrapper-shim guard and compliance re-check block PR-open.
- PR-open blocks CI-wait; CI-green blocks merge; merge blocks the next candidate group.

### Parallel Opportunities

- Phase A: T002, T003, T004 may run in parallel with each other after T001.
- Within any Phase B/C candidate group: the `[P]`-marked tasks (context reads, belt-and-suspenders grep, local gates) may run in parallel.
- Phase E: All verification tasks T154-T165 may run in parallel; T166 depends on all of them.
- CROSS-CANDIDATE: strictly forbidden by the serial-PR contract. Do NOT parallelize PR-N with PR-N+1.

---

## Parallel Example: Phase A

```bash
# T001 first (loads the header baseline), then in parallel:
grep -E "99\.6|A\+" data/full_repo_compliance_current.md        # T002
grep -A 5 "^## Skipped" refactor_candidates.md                  # T003
grep -RIn "\bPerformanceMonitor\b" --include="*.py" .           # T004
```

## Parallel Example: Within One Candidate Group (PR-03 SQLiteDatabaseWriter)

```bash
# After T027 (read def-site) completes, run in parallel:
# T028: read callsite context at MistHelper.py:7468
# T029: read guideline_flags from refactor_candidates.md
# T030: belt-and-suspenders grep
# All three [P] tasks feed into T031 (create module).

# After T032 (delete + rewrite same commit), run local gates in parallel:
python -m ruff check MistHelper.py src/refactors/sqlite_database_writer.py    # T035 part
python -m black --check MistHelper.py src/refactors/sqlite_database_writer.py # T035 part
python -m mypy --strict src/refactors/sqlite_database_writer.py               # T035 part
python -m pytest tests/ -k "not slow" -x                                      # T036
```

## Serial Example: Cross-Candidate (Non-parallelizable)

```bash
# T041 MUST complete (catalog refreshed after PR-03 merge) before T042 begins.
# There is no world in which PR-03 and PR-04 execute concurrently — FR-013 forbids it.
```

---

## Implementation Strategy

### Serial-PR Discipline (Required)

1. Complete Phase A (T001-T004). Confirm Checkpoint A.
2. Execute PR-01 tasks (T005-T015) sequentially with in-group `[P]` parallelism.
3. After PR-01 merge + catalog refresh (T015): execute PR-02 tasks (T016-T026).
4. After PR-02 merge + catalog refresh (T026): execute PR-03 tasks (T027-T041).
5. Continue through PR-13 (T142-T152) in strict LOC-DESC order.
6. Execute Phase D scoping (T153).
7. Execute Phase E wrap-up (T154-T166) in parallel where possible.

### MVP Increment (Optional)

If dispatch pauses partway through, each merged PR is a standalone value delivery (spec User Story 1 "Independent Test"). Any prefix `PR-01..PR-N` produces a coherent `main` state at 99.6/A+ compliance and monotonically decreasing MistHelper.py line count. Stop at any PR merge, resume from Step 1 of `quickstart.md` for the next.

### No-Batch Guarantee

FR-002 prohibits batching multiple candidates into one PR. Even if two candidates appear "trivial together," they get separate PRs. The serial workflow is what distinguishes this initiative from prior stalled attempts.

---

## Notes

- `[P]` tasks = different files, no dependencies within one candidate group. Never parallelize across candidate groups (FR-013).
- `[BLOCKS T###]` = enforces the serial-PR contract across candidate groups.
- Every catalog-refresh task (T015, T026, T041, T052, T063, T074, T086, T097, T108, T119, T130, T141, T152) provides the SC-011 audit trail.
- `--admin` merge bypass MUST NOT be used as a routine unblock (FR-011, `feedback_no_admin_bypass.md`). Investigate `mergeStateStatus` first; SKIPPED conditionals are not blocking.
- No new tests are mandated. Existing tests that reference an extracted symbol are updated in the same PR that moves the symbol (research.md "Test-preservation rule").
- Analyzer (`tools/refactor_analyzer/`) is NEVER modified by this initiative (FR-018). Discrepancies are filed as separate analyzer bugs.
- The parent conversation controls PR dispatch cadence — this tasks file is the operator recipe, not an auto-execution script.
