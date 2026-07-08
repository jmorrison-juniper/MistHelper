---
description: "Tasks for feature 1011-misthelper-refactor-low-use"
---

# Tasks: MistHelper.py Refactor Extraction - Low-Use Second Pass

**Input**: Design documents from `/specs/1011-misthelper-refactor-low-use/`
**Prerequisites**: plan.md, spec.md; predecessor tasks.md at `specs/1010-misthelper-refactor-extraction/tasks.md`; live analyzer catalog at `refactor_candidates.md` (repo root)

**Tests**: NO new tests are mandated (carry-forward from 1010 research.md "Test-preservation rule"). Existing tests referencing an extracted symbol are updated in the same PR that moves it. The 15 functional CI jobs are the mergeability contract (FR-011).

**Organization**: Tasks are grouped by extraction candidate. Each Low-Use candidate = one PR (FR-002). PRs execute strictly serially (FR-002 + spec Edge Cases). Within a single candidate group, some tasks may run in parallel; across candidate groups execution is serial and gated by the catalog-refresh task (FR-010, SC-010).

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: May run in parallel with sibling `[P]` tasks in the SAME candidate group. Never parallel across candidate groups.
- **[Story]**: `[US1]` = User Story 1 (single-file Low-Use extraction, P1); `[US2]` = User Story 2 (cross-file Low-Use extraction, P2); `[US3]` = User Story 3 (catalog refresh, P3, threaded through every PR).
- **[BLOCKS T###]**: This task blocks the referenced downstream task(s). Cross-PR blockers enforce the serial-PR contract.

## Path Conventions

- Entrypoint monolith: `MistHelper.py` (repo root).
- Analyzer catalog: `refactor_candidates.md` (repo root, regenerated after every merge).
- Compliance snapshot: `data/full_repo_compliance_current.md`.
- New extraction modules: `src/refactors/<snake_name>.py` (17 of 20 candidates).
- Shared-destination class file: `src/firmware/firmware_manager.py` (three FR-015 candidates: `FirmwareUpgradeStatusChecker`, `BulkAPFirmwareUpgrader`, `BulkSwitchFirmwareUpgrader`).
- Refactor analyzer command: `python -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md`.
- Compliance analyzer command: `python -m tools.compliance_analyzer`.

---

## Phase A: Pre-work (Verification Gate, Once Upfront)

**Purpose**: Confirm the analyzer catalog, compliance baseline, skip pins, and branch base match spec/plan assumptions BEFORE any PR is opened. Catches drift between the 1010 close and 1011 kickoff.

**CRITICAL**: All Phase A tasks must complete green before Phase B begins.

- [ ] T001 Refresh the analyzer catalog on fresh post-PR-13-merge `main` head: `git checkout main && git pull && python -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md`. Confirm header via `grep -E "Definitions analyzed|LOC saveable|Category counts" refactor_candidates.md` — expected: `Category counts: unused=0, single-use=0, low-use=20, hot=80, skipped=1` (FR-010, plan Summary) [BLOCKS T006].
- [ ] T002 [P] Verify baseline compliance: `grep -E "99\.6|A\+" data/full_repo_compliance_current.md` — confirm repo aggregate 99.6/A+ with 0 sub-A files (FR-013, SC-003, SC-004).
- [ ] T003 [P] Verify `SKIP_ALWAYS` pins intact: `grep -A 5 "^## Skipped" refactor_candidates.md` — confirm `GlobalImportManager` remains pinned. Any missing symbol halts the initiative (FR-008, SC-008, FR-018).
- [ ] T004 [P] Verify branch base: `git rev-parse --abbrev-ref HEAD` is `main`, `git status` is clean, and `git log --oneline -5` shows the PR-13 merge as HEAD ancestor (spec Predecessor Context).
- [ ] T005 [P] Verify no Hot-bucket source symbol is queued: `grep -A 2 "^## Hot" refactor_candidates.md | head -20` — confirm the 20 Low-Use candidates listed in plan.md PR Dispatch Queue do NOT appear in the Hot bucket (FR-009, SC-009).

**Checkpoint A**: Catalog fresh, baseline green, skip pins intact, branch base is post-PR-13-merge `main`, no Hot source symbols queued. Phase B may begin.

---

## Phase B: Low-Use Extractions (20 PRs, LOC-DESC within priority band)

**Story reference**: User Story 1 (single-file, P1) for 17 PRs; User Story 2 (cross-file, P2) for 3 PRs (PR-26 `main`, PR-27 `marvis_data_utils`, PR-32 `MIST_WAN_TARGET_PORTS`). User Story 3 (catalog refresh) threaded through every PR.

**Non-negotiables** (apply to every candidate group in Phase B):

- No wrapper shim, forwarding function, or backward-compat alias in `MistHelper.py` (FR-003, SC-007).
- Module-level function candidates land as class-body methods, not bare defs (FR-005; applies to PR-23, PR-24, PR-26).
- Module-level assignment candidates land as class-body attributes on a cohesive class in the new module (FR-005; applies to PR-25 and PRs 27-32).
- All analyzer `guideline_flags` on extracted code resolved in-flight (FR-006, SC-011). Explicit callouts: `raw_input_call` on `WLANRadiusTimerManager` (PR-14) rewritten to `safe_input()`; `oversize_25_lines` + `missing_inline_comments` + `non_ascii_logs` on `FirmwareUpgradeStatusChecker` (PR-19) decomposed into <=25-line methods with 5-10-line comment cadence and ASCII log strings.
- ASCII-only logs, `safe_input()`, `pathlib.Path` in every new/receiving module (FR-007, Principle V).
- Inline comments every 5-10 lines (Principle VI, NON-NEGOTIABLE).
- Action logging with `[MENU]`/`[EXECUTE]`/`[SUCCESS]`/`[FAILURE]` prefixes on every non-trivial action (Principle VII, NON-NEGOTIABLE).
- New module lands A+/100 on first commit; existing receiving module (`src/firmware/firmware_manager.py`) stays A+/100 after each fold-in (FR-012, SC-006, SC-013).
- Double-underscore analyzer-suggested module names renamed to single-underscore during landing; rename rationale recorded in the PR description (FR-020; applies to PRs 28-32).
- Cross-file callsite rewrites in PR-26/PR-27/PR-32 include the external file in the SAME commit, and post-merge grep audit confirms zero stale references (FR-019, SC-012).
- 15/15 functional CI green; no `--admin` bypass except with documented BLOCKED/DIRTY/BEHIND `mergeStateStatus` (FR-011, SC-005, per `feedback_no_admin_bypass.md`).
- After every merge: `git checkout main && git pull` then regenerate `refactor_candidates.md` before dispatching the next PR (FR-010, SC-010). This refresh task BLOCKS the first task of the next candidate group.

**Serial execution**: PR-14 through PR-33 execute in the order specified in plan.md PR Dispatch Queue. Within each candidate group, `[P]` tasks may run in parallel; across candidate groups, execution is strictly serial (FR-002).

---

### Phase B.1 - PR-14: `WLANRadiusTimerManager` (class, 787 LoC, refs `MistHelper.py:20044, 21515`) -> `src/refactors/wlanradius_timer_manager.py`

**Guideline flags to resolve**: `raw_input_call` (rewrite to `safe_input()` per FR-006/FR-007). Additional flags per fresh catalog.

- [ ] T006 [US1] Read def-site range: `grep -n "^class WLANRadiusTimerManager" MistHelper.py` (LoC drift may have occurred since spec creation); read the ~787 physical lines starting at the located def-site [BLOCKS T009].
- [ ] T007 [P] [US1] Read both callsite contexts (`MistHelper.py:20044` and `MistHelper.py:21515` at spec creation; re-locate on fresh `main`) — capture imports and argument shapes [BLOCKS T009].
- [ ] T008 [P] [US1] Read `guideline_flags` for `WLANRadiusTimerManager` from fresh `refactor_candidates.md`; belt-and-suspenders grep `grep -RIn "\bWLANRadiusTimerManager\b" --include="*.py" .` expects definition + 2-3 callers only. A 4th hit reroutes per FR-016 [BLOCKS T009].
- [ ] T009 [US1] Create `src/refactors/wlanradius_timer_manager.py` housing the class body. Rewrite every `input()` to `safe_input()`. Fix every remaining `guideline_flags` entry. ASCII logs, `pathlib.Path`, inline comments every 5-10 lines, action logging with correct prefixes (FR-005-FR-007) [BLOCKS T010].
- [ ] T010 [US1] SAME commit: delete `WLANRadiusTimerManager` from `MistHelper.py` (no wrapper per FR-003) AND rewrite BOTH callsites at `MistHelper.py:20044` and `MistHelper.py:21515` to `from src.refactors.wlanradius_timer_manager import WLANRadiusTimerManager` [BLOCKS T011].
- [ ] T011 [US1] Wrapper-shim guard: `grep -RIn "\bWLANRadiusTimerManager\b" MistHelper.py` returns zero hits; `grep -RIn "def WLANRadiusTimerManager" --include="*.py" .` returns zero hits.
- [ ] T012 [P] [US1] Local gates: `python -c "import py_compile; py_compile.compile('MistHelper.py', doraise=True); py_compile.compile('src/refactors/wlanradius_timer_manager.py', doraise=True)"`, `python -m ruff check MistHelper.py src/refactors/wlanradius_timer_manager.py`, `python -m black --check MistHelper.py src/refactors/wlanradius_timer_manager.py`, `python -m mypy --strict src/refactors/wlanradius_timer_manager.py`, `python -m pytest tests/ -k "not slow" -x`.
- [ ] T013 [US1] Compliance: `python -m tools.compliance_analyzer` — new `src/refactors/wlanradius_timer_manager.py` MUST land A+/100 (FR-012, SC-006). `MistHelper.py` grade unchanged. Repo >= 99.6/A+ (FR-013, SC-003, SC-004) [BLOCKS T014].
- [ ] T014 [US1] Open PR: `gh pr create --title "refactor(extract): WLANRadiusTimerManager low-use" --body "Extracts WLANRadiusTimerManager (~787 LoC) from MistHelper.py into src/refactors/wlanradius_timer_manager.py. Rewrites 2 callsites atomically. Resolves raw_input_call via safe_input() rewrite (FR-006, FR-007). See specs/1011-misthelper-refactor-low-use/plan.md PR-14."` [BLOCKS T015].
- [ ] T015 [US1] Wait 15/15 CI green + `mergeStateStatus == CLEAN` via `gh pr checks` / `gh pr view --json mergeStateStatus`. NO `--admin` bypass unless genuinely BLOCKED/DIRTY/BEHIND with root cause (FR-011) [BLOCKS T016].
- [ ] T016 [US1] Merge PR-14: `gh pr merge --squash --delete-branch`. Then `git checkout main && git pull` [BLOCKS T017].
- [ ] T017 [US3] Refresh catalog: `python -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md`. Diff-verify `WLANRadiusTimerManager` no longer appears in the Low-Use bucket (FR-010, SC-010) [BLOCKS T018].

### Phase B.2 - PR-15: `WANProbeConfigManager` (class, 473 LoC, refs `MistHelper.py:21720`) -> `src/refactors/wanprobe_config_manager.py`

- [ ] T018 [US1] Read def-site (`grep -n "^class WANProbeConfigManager" MistHelper.py`), callsite context, and `guideline_flags` from fresh catalog [BLOCKS T020].
- [ ] T019 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bWANProbeConfigManager\b" --include="*.py" .` — expect definition + 2 callers.
- [ ] T020 [US1] Create `src/refactors/wanprobe_config_manager.py` as cohesive class. Fix every `guideline_flags` in-flight. ASCII/safe_input/Path/comments/logging (FR-005-FR-007) [BLOCKS T021].
- [ ] T021 [US1] SAME commit: delete from `MistHelper.py` (no wrapper) + rewrite all 2 callsites to import from `src.refactors.wanprobe_config_manager` [BLOCKS T022].
- [ ] T022 [US1] Wrapper-shim guard: `grep -RIn "\bWANProbeConfigManager\b" MistHelper.py` returns zero hits.
- [ ] T023 [P] [US1] Local gates: py_compile, ruff, black, mypy strict on new module, pytest.
- [ ] T024 [US1] Compliance A+/100 + baseline >= 99.6/A+ [BLOCKS T025].
- [ ] T025 [US1] Open PR: `gh pr create --title "refactor(extract): WANProbeConfigManager low-use" --body "Extracts WANProbeConfigManager (~473 LoC) into src/refactors/wanprobe_config_manager.py. See plan.md PR-15."` [BLOCKS T026].
- [ ] T026 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T027].
- [ ] T027 [US1] Merge PR-15: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T028].
- [ ] T028 [US3] Refresh catalog. Confirm `WANProbeConfigManager` removed from Low-Use bucket [BLOCKS T029].

### Phase B.3 - PR-16: `AnomalyMetricsDiscovery` (class, 91 LoC, refs `MistHelper.py:12994`) -> `src/refactors/anomaly_metrics_discovery.py`

- [ ] T029 [US1] Read def-site, callsite context, `guideline_flags` [BLOCKS T031].
- [ ] T030 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bAnomalyMetricsDiscovery\b" --include="*.py" .` — expect definition + 2 callers.
- [ ] T031 [US1] Create `src/refactors/anomaly_metrics_discovery.py` as cohesive class. Fix `guideline_flags`. ASCII/safe_input/Path/comments/logging [BLOCKS T032].
- [ ] T032 [US1] SAME commit: delete from `MistHelper.py` + rewrite both callsites [BLOCKS T033].
- [ ] T033 [US1] Wrapper-shim guard: `grep -RIn "\bAnomalyMetricsDiscovery\b" MistHelper.py` returns zero hits.
- [ ] T034 [P] [US1] Local gates: py_compile, ruff, black, mypy strict, pytest.
- [ ] T035 [US1] Compliance A+/100 + baseline >= 99.6/A+ [BLOCKS T036].
- [ ] T036 [US1] Open PR: `gh pr create --title "refactor(extract): AnomalyMetricsDiscovery low-use" --body "Extracts AnomalyMetricsDiscovery (~91 LoC) into src/refactors/anomaly_metrics_discovery.py. See plan.md PR-16."` [BLOCKS T037].
- [ ] T037 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T038].
- [ ] T038 [US1] Merge PR-16: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T039].
- [ ] T039 [US3] Refresh catalog. Confirm `AnomalyMetricsDiscovery` removed [BLOCKS T040].

### Phase B.4 - PR-17: `DeviceDataFetcher` (class, 68 LoC, refs `MistHelper.py:15292, 15309, 15325`) -> `src/refactors/device_data_fetcher.py`

- [ ] T040 [US1] Read def-site and all THREE callsite contexts, `guideline_flags` [BLOCKS T042].
- [ ] T041 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bDeviceDataFetcher\b" --include="*.py" .` — expect definition + 3 callers.
- [ ] T042 [US1] Create `src/refactors/device_data_fetcher.py` as cohesive class. Fix `guideline_flags`. ASCII/safe_input/Path/comments/logging [BLOCKS T043].
- [ ] T043 [US1] SAME commit: delete from `MistHelper.py` + rewrite ALL THREE callsites (15292, 15309, 15325) atomically [BLOCKS T044].
- [ ] T044 [US1] Wrapper-shim guard: `grep -RIn "\bDeviceDataFetcher\b" MistHelper.py` returns zero hits.
- [ ] T045 [P] [US1] Local gates: py_compile, ruff, black, mypy strict, pytest.
- [ ] T046 [US1] Compliance A+/100 + baseline >= 99.6/A+ [BLOCKS T047].
- [ ] T047 [US1] Open PR: `gh pr create --title "refactor(extract): DeviceDataFetcher low-use" --body "Extracts DeviceDataFetcher (~68 LoC) into src/refactors/device_data_fetcher.py. Rewrites 3 callsites atomically. See plan.md PR-17."` [BLOCKS T048].
- [ ] T048 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T049].
- [ ] T049 [US1] Merge PR-17: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T050].
- [ ] T050 [US3] Refresh catalog. Confirm `DeviceDataFetcher` removed [BLOCKS T051].

### Phase B.5 - PR-18: `InventoryCSVComparator` (class, 47 LoC, refs `MistHelper.py:16488, 21541`) -> `src/refactors/inventory_csvcomparator.py`

- [ ] T051 [US1] Read def-site and both callsite contexts, `guideline_flags` [BLOCKS T053].
- [ ] T052 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bInventoryCSVComparator\b" --include="*.py" .` — expect definition + 2-3 callers.
- [ ] T053 [US1] Create `src/refactors/inventory_csvcomparator.py` as cohesive class. Fix `guideline_flags`. ASCII/safe_input/Path/comments/logging [BLOCKS T054].
- [ ] T054 [US1] SAME commit: delete from `MistHelper.py` + rewrite both callsites [BLOCKS T055].
- [ ] T055 [US1] Wrapper-shim guard: `grep -RIn "\bInventoryCSVComparator\b" MistHelper.py` returns zero hits.
- [ ] T056 [P] [US1] Local gates: py_compile, ruff, black, mypy strict, pytest.
- [ ] T057 [US1] Compliance A+/100 + baseline >= 99.6/A+ [BLOCKS T058].
- [ ] T058 [US1] Open PR: `gh pr create --title "refactor(extract): InventoryCSVComparator low-use" --body "Extracts InventoryCSVComparator (~47 LoC) into src/refactors/inventory_csvcomparator.py. See plan.md PR-18."` [BLOCKS T059].
- [ ] T059 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T060].
- [ ] T060 [US1] Merge PR-18: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T061].
- [ ] T061 [US3] Refresh catalog. Confirm `InventoryCSVComparator` removed [BLOCKS T062].

### Phase B.6 - PR-19: `FirmwareUpgradeStatusChecker` (class, 958 LoC, FR-015 fold-in) -> `src/firmware/firmware_manager.py::FirmwareManager`

**Special case (FR-015)**: Landing target is EXISTING `src/firmware/firmware_manager.py` — NO new file. Fold in as methods on `FirmwareManager`. Guideline flags to resolve: `oversize_25_lines` (decompose into <=25-line methods with <=5 params per FR-006), `missing_inline_comments` (5-10-line cadence), `non_ascii_logs` (rewrite to ASCII). `src/firmware/firmware_manager.py` MUST retain A+/100 after fold-in (SC-013).

- [ ] T062 [US1] Read def-site for `FirmwareUpgradeStatusChecker` in fresh `MistHelper.py` (~958 lines). Read `guideline_flags` [BLOCKS T064, T065].
- [ ] T063 [P] [US1] Read `src/firmware/firmware_manager.py` — locate `FirmwareManager` class body, identify where the checker methods should land. Confirm existing A+/100 grade for that file pre-PR [BLOCKS T065].
- [ ] T064 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bFirmwareUpgradeStatusChecker\b" --include="*.py" .` — expect definition in `MistHelper.py` + 2 callers in `src/firmware/firmware_manager.py:1746, 1753`.
- [ ] T065 [US1] Fold `FirmwareUpgradeStatusChecker` into `src/firmware/firmware_manager.py::FirmwareManager` (FR-015). Decompose oversized methods into <=25-line units with <=5 params (FR-006). Add inline comments every 5-10 lines. Rewrite all non-ASCII log strings. Ensure `src/firmware/firmware_manager.py` retains A+/100 after the addition (FR-012, SC-013) [BLOCKS T066].
- [ ] T066 [US1] SAME commit: delete `FirmwareUpgradeStatusChecker` from `MistHelper.py` (no wrapper). Rewrite the 2 caller references at `src/firmware/firmware_manager.py:1746, 1753` to use the folded methods [BLOCKS T067].
- [ ] T067 [US1] Wrapper-shim guard: `grep -RIn "\bFirmwareUpgradeStatusChecker\b" MistHelper.py` returns zero hits.
- [ ] T068 [P] [US1] Local gates on both affected files: py_compile MistHelper.py + firmware_manager.py, ruff, black, mypy strict, pytest.
- [ ] T069 [US1] Compliance: `src/firmware/firmware_manager.py` MUST retain A+/100 (SC-013 — no A+ regression on receiving file). `MistHelper.py` unchanged. Repo >= 99.6/A+ [BLOCKS T070].
- [ ] T070 [US1] Open PR: `gh pr create --title "refactor(extract): FirmwareUpgradeStatusChecker low-use (FR-015 fold-in)" --body "Folds FirmwareUpgradeStatusChecker (~958 LoC) into src/firmware/firmware_manager.py::FirmwareManager per FR-015 (sole callers already live there). Decomposes oversized methods to <=25 lines with 5-10-line comment cadence and ASCII log strings (FR-006). See plan.md PR-19."` [BLOCKS T071].
- [ ] T071 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T072].
- [ ] T072 [US1] Merge PR-19: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T073].
- [ ] T073 [US3] Refresh catalog. Confirm `FirmwareUpgradeStatusChecker` removed. Confirm `src/firmware/firmware_manager.py` grade unchanged in compliance snapshot [BLOCKS T074].

### Phase B.7 - PR-20: `DeviceConfigTemplateClonerManager` (class, 27 LoC, refs `MistHelper.py:21922`) -> `src/refactors/device_config_template_cloner_manager.py`

- [ ] T074 [US1] Read def-site and callsite contexts, `guideline_flags` [BLOCKS T076].
- [ ] T075 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bDeviceConfigTemplateClonerManager\b" --include="*.py" .` — expect definition + 2 callers.
- [ ] T076 [US1] Create `src/refactors/device_config_template_cloner_manager.py` as cohesive class. Fix `guideline_flags`. ASCII/safe_input/Path/comments/logging [BLOCKS T077].
- [ ] T077 [US1] SAME commit: delete from `MistHelper.py` + rewrite both callsites [BLOCKS T078].
- [ ] T078 [US1] Wrapper-shim guard: `grep -RIn "\bDeviceConfigTemplateClonerManager\b" MistHelper.py` returns zero hits.
- [ ] T079 [P] [US1] Local gates: py_compile, ruff, black, mypy strict, pytest.
- [ ] T080 [US1] Compliance A+/100 + baseline >= 99.6/A+ [BLOCKS T081].
- [ ] T081 [US1] Open PR: `gh pr create --title "refactor(extract): DeviceConfigTemplateClonerManager low-use" --body "Extracts DeviceConfigTemplateClonerManager (~27 LoC) into src/refactors/device_config_template_cloner_manager.py. See plan.md PR-20."` [BLOCKS T082].
- [ ] T082 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T083].
- [ ] T083 [US1] Merge PR-20: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T084].
- [ ] T084 [US3] Refresh catalog. Confirm `DeviceConfigTemplateClonerManager` removed [BLOCKS T085].

### Phase B.8 - PR-21: `WANProbeDeviceOverrideManager` (class, 23 LoC, refs `MistHelper.py:21724`) -> `src/refactors/wanprobe_device_override_manager.py`

- [ ] T085 [US1] Read def-site and callsite contexts, `guideline_flags` [BLOCKS T087].
- [ ] T086 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bWANProbeDeviceOverrideManager\b" --include="*.py" .` — expect definition + 2 callers.
- [ ] T087 [US1] Create `src/refactors/wanprobe_device_override_manager.py` as cohesive class. Fix `guideline_flags`. ASCII/safe_input/Path/comments/logging [BLOCKS T088].
- [ ] T088 [US1] SAME commit: delete from `MistHelper.py` + rewrite both callsites [BLOCKS T089].
- [ ] T089 [US1] Wrapper-shim guard: `grep -RIn "\bWANProbeDeviceOverrideManager\b" MistHelper.py` returns zero hits.
- [ ] T090 [P] [US1] Local gates: py_compile, ruff, black, mypy strict, pytest.
- [ ] T091 [US1] Compliance A+/100 + baseline >= 99.6/A+ [BLOCKS T092].
- [ ] T092 [US1] Open PR: `gh pr create --title "refactor(extract): WANProbeDeviceOverrideManager low-use" --body "Extracts WANProbeDeviceOverrideManager (~23 LoC) into src/refactors/wanprobe_device_override_manager.py. See plan.md PR-21."` [BLOCKS T093].
- [ ] T093 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T094].
- [ ] T094 [US1] Merge PR-21: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T095].
- [ ] T095 [US3] Refresh catalog. Confirm `WANProbeDeviceOverrideManager` removed [BLOCKS T096].

### Phase B.9 - PR-22: `BulkAPFirmwareUpgrader` (class, 32 LoC, FR-015 fold-in) -> `src/firmware/firmware_manager.py::FirmwareManager`

**Special case (FR-015)**: Fold-in variant, NO new file. `src/firmware/firmware_manager.py` MUST retain A+/100 (SC-013).

- [ ] T096 [US1] Read def-site for `BulkAPFirmwareUpgrader` in fresh `MistHelper.py`. Read `guideline_flags` [BLOCKS T098, T099].
- [ ] T097 [P] [US1] Read `src/firmware/firmware_manager.py::FirmwareManager` — confirm existing A+/100 grade pre-PR; identify insertion point for the bulk AP upgrader methods.
- [ ] T098 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bBulkAPFirmwareUpgrader\b" --include="*.py" .` — expect definition + 2 callers in `firmware_manager.py:1733, 1736`.
- [ ] T099 [US1] Fold `BulkAPFirmwareUpgrader` into `FirmwareManager` (FR-015). Fix `guideline_flags`. ASCII/safe_input/Path/comments/logging. Ensure `firmware_manager.py` retains A+/100 [BLOCKS T100].
- [ ] T100 [US1] SAME commit: delete from `MistHelper.py` + rewrite both caller references in `firmware_manager.py:1733, 1736` to the folded methods [BLOCKS T101].
- [ ] T101 [US1] Wrapper-shim guard: `grep -RIn "\bBulkAPFirmwareUpgrader\b" MistHelper.py` returns zero hits.
- [ ] T102 [P] [US1] Local gates on both affected files: py_compile, ruff, black, mypy strict, pytest.
- [ ] T103 [US1] Compliance: `firmware_manager.py` A+/100 preserved (SC-013). Baseline >= 99.6/A+ [BLOCKS T104].
- [ ] T104 [US1] Open PR: `gh pr create --title "refactor(extract): BulkAPFirmwareUpgrader low-use (FR-015 fold-in)" --body "Folds BulkAPFirmwareUpgrader (~32 LoC) into src/firmware/firmware_manager.py::FirmwareManager per FR-015. See plan.md PR-22."` [BLOCKS T105].
- [ ] T105 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T106].
- [ ] T106 [US1] Merge PR-22: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T107].
- [ ] T107 [US3] Refresh catalog. Confirm `BulkAPFirmwareUpgrader` removed. Confirm `firmware_manager.py` grade unchanged [BLOCKS T108].

### Phase B.10 - PR-23: `initialize_mist_session_interactive` (fn, 18 LoC, refs `MistHelper.py:2237, 19356, 23190`) -> `src/refactors/initialize_mist_session_interactive.py` (fn->method per FR-005)

- [ ] T108 [US1] Read def-site and all THREE callsite contexts, `guideline_flags` [BLOCKS T110].
- [ ] T109 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\binitialize_mist_session_interactive\b" --include="*.py" .` — expect definition + 3 callers.
- [ ] T110 [US1] Create `src/refactors/initialize_mist_session_interactive.py`. Land the function as a class-body method on a cohesive class (FR-005) — NOT as a bare `def`. Fix `guideline_flags`. ASCII/safe_input/Path/comments/logging [BLOCKS T111].
- [ ] T111 [US1] SAME commit: delete the module-level `def initialize_mist_session_interactive` from `MistHelper.py` + rewrite ALL THREE callsites (2237, 19356, 23190) to invoke the class method [BLOCKS T112].
- [ ] T112 [US1] Wrapper-shim guard: `grep -RIn "\binitialize_mist_session_interactive\b" MistHelper.py` returns zero hits; `grep -n "^def initialize_mist_session_interactive" MistHelper.py` returns zero hits (bare-def guard).
- [ ] T113 [P] [US1] Local gates: py_compile, ruff, black, mypy strict, pytest.
- [ ] T114 [US1] Compliance A+/100 + baseline >= 99.6/A+ [BLOCKS T115].
- [ ] T115 [US1] Open PR: `gh pr create --title "refactor(extract): initialize_mist_session_interactive low-use" --body "Extracts initialize_mist_session_interactive (~18 LoC) into src/refactors/initialize_mist_session_interactive.py as a class-body method per FR-005. Rewrites 3 callsites. See plan.md PR-23."` [BLOCKS T116].
- [ ] T116 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T117].
- [ ] T117 [US1] Merge PR-23: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T118].
- [ ] T118 [US3] Refresh catalog. Confirm `initialize_mist_session_interactive` removed [BLOCKS T119].

### Phase B.11 - PR-24: `initialize_mist_session` (fn, 18 LoC, refs `MistHelper.py:23195, 23258`) -> `src/refactors/initialize_mist_session.py` (fn->method per FR-005)

- [ ] T119 [US1] Read def-site and both callsite contexts, `guideline_flags` [BLOCKS T121].
- [ ] T120 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\binitialize_mist_session\b" --include="*.py" .` — expect definition + 2 callers (note: distinct from `initialize_mist_session_interactive`).
- [ ] T121 [US1] Create `src/refactors/initialize_mist_session.py`. Land as class-body method (FR-005). Fix `guideline_flags`. ASCII/safe_input/Path/comments/logging [BLOCKS T122].
- [ ] T122 [US1] SAME commit: delete from `MistHelper.py` + rewrite both callsites (23195, 23258) [BLOCKS T123].
- [ ] T123 [US1] Wrapper-shim guard: `grep -n "^def initialize_mist_session\b" MistHelper.py` returns zero hits (bare-def guard).
- [ ] T124 [P] [US1] Local gates: py_compile, ruff, black, mypy strict, pytest.
- [ ] T125 [US1] Compliance A+/100 + baseline >= 99.6/A+ [BLOCKS T126].
- [ ] T126 [US1] Open PR: `gh pr create --title "refactor(extract): initialize_mist_session low-use" --body "Extracts initialize_mist_session (~18 LoC) into src/refactors/initialize_mist_session.py as a class-body method per FR-005. See plan.md PR-24."` [BLOCKS T127].
- [ ] T127 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T128].
- [ ] T128 [US1] Merge PR-24: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T129].
- [ ] T129 [US3] Refresh catalog. Confirm `initialize_mist_session` removed [BLOCKS T130].

### Phase B.12 - PR-25: `PACKAGE_IMPORT_MAP` (assignment, 13 LoC, refs `MistHelper.py:354, 538`) -> `src/refactors/package_import_map.py` (assignment->class-body attribute per FR-005)

- [ ] T130 [US1] Read def-site and both callsite contexts, `guideline_flags` [BLOCKS T132].
- [ ] T131 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bPACKAGE_IMPORT_MAP\b" --include="*.py" .` — expect definition + 2 callers.
- [ ] T132 [US1] Create `src/refactors/package_import_map.py`. Land the mapping as a class-body attribute (or classmethod-returning) on a cohesive class per FR-005 — NOT as a bare module-level `PACKAGE_IMPORT_MAP = ...`. Fix `guideline_flags`. ASCII/Path/comments/logging [BLOCKS T133].
- [ ] T133 [US1] SAME commit: delete from `MistHelper.py` + rewrite both callsites (354, 538) [BLOCKS T134].
- [ ] T134 [US1] Wrapper-shim guard: `grep -n "^PACKAGE_IMPORT_MAP\s*=" MistHelper.py` returns zero hits (module-scope-attribute guard).
- [ ] T135 [P] [US1] Local gates: py_compile, ruff, black, mypy strict, pytest.
- [ ] T136 [US1] Compliance A+/100 + baseline >= 99.6/A+ [BLOCKS T137].
- [ ] T137 [US1] Open PR: `gh pr create --title "refactor(extract): PACKAGE_IMPORT_MAP low-use" --body "Extracts PACKAGE_IMPORT_MAP (~13 LoC) into src/refactors/package_import_map.py as a class-body attribute per FR-005. See plan.md PR-25."` [BLOCKS T138].
- [ ] T138 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T139].
- [ ] T139 [US1] Merge PR-25: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T140].
- [ ] T140 [US3] Refresh catalog. Confirm `PACKAGE_IMPORT_MAP` removed [BLOCKS T141].

### Phase B.13 - PR-26: `main` (fn, 12 LoC, cross-file P2, refs `MistHelper.py:23700 + src/maps/maps_manager.py:2794`) -> `src/refactors/main.py` (fn->method per FR-005; FR-019 cross-file audit)

**P2 special case**: Cross-file callsite. Diff touches THREE files atomically: new module, `MistHelper.py`, `src/maps/maps_manager.py`. Post-merge grep audit required (FR-019, SC-012).

- [ ] T141 [US2] Read def-site in `MistHelper.py:23700` and BOTH callsite contexts including external caller `src/maps/maps_manager.py:2794`, `guideline_flags` [BLOCKS T143].
- [ ] T142 [P] [US2] Belt-and-suspenders grep: `grep -RIn "\bmain\b" --include="*.py" MistHelper.py src/maps/` — expect definition + 1 caller in `maps_manager.py:2794` (note: `main` is a common word; scope grep to affected files only, and inspect each hit for actual reference to this specific `main`).
- [ ] T143 [US2] Create `src/refactors/main.py`. Land as class-body method (FR-005). Fix `guideline_flags`. ASCII/safe_input/Path/comments/logging [BLOCKS T144].
- [ ] T144 [US2] SAME commit: delete `def main` from `MistHelper.py`, rewrite the internal callsite at `MistHelper.py:23700`, AND rewrite the external callsite at `src/maps/maps_manager.py:2794` to import from `src.refactors.main`. All three file edits in ONE commit (FR-003 atomicity) [BLOCKS T145].
- [ ] T145 [US2] Wrapper-shim guard: `grep -n "^def main\b" MistHelper.py` returns zero hits (bare-def guard).
- [ ] T146 [P] [US2] Local gates on all three affected files: py_compile MistHelper.py + main.py + maps_manager.py, ruff, black, mypy strict on new module, pytest.
- [ ] T147 [US2] Compliance: new module A+/100. `MistHelper.py` unchanged. `src/maps/maps_manager.py` grade unchanged (external caller compliance preserved per spec Edge Case). Baseline >= 99.6/A+ [BLOCKS T148].
- [ ] T148 [US2] Open PR: `gh pr create --title "refactor(extract): main low-use (P2 cross-file)" --body "Extracts main (~12 LoC) into src/refactors/main.py as a class-body method per FR-005. Rewrites cross-file callsite in src/maps/maps_manager.py:2794 atomically (FR-019). See plan.md PR-26."` [BLOCKS T149].
- [ ] T149 [US2] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T150].
- [ ] T150 [US2] Merge PR-26: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T151].
- [ ] T151 [US2] FR-019 post-merge grep audit: `grep -RIn "\bmain\b" src/maps/maps_manager.py` — confirm no stale reference to the deleted `MistHelper.main`; the sole remaining hit imports from `src.refactors.main`. Paste audit output in the PR retro comment [BLOCKS T152].
- [ ] T152 [US3] Refresh catalog. Confirm `main` removed from Low-Use bucket [BLOCKS T153].

### Phase B.14 - PR-27: `marvis_data_utils` (assignment, 4 LoC, cross-file P2, refs `MistHelper.py:6594, 15736 + src/troubleshooting/marvis_troubleshoot_utils.py:21`) -> `src/refactors/marvis_data_utils.py` (assignment->class-body attribute per FR-005; FR-019 cross-file audit)

- [ ] T153 [US2] Read def-site and all three callsite contexts including external caller `marvis_troubleshoot_utils.py:21`, `guideline_flags` [BLOCKS T155].
- [ ] T154 [P] [US2] Belt-and-suspenders grep: `grep -RIn "\bmarvis_data_utils\b" --include="*.py" .` — expect definition + 3 callers across 2 files.
- [ ] T155 [US2] Create `src/refactors/marvis_data_utils.py`. Land the assignment as a class-body attribute per FR-005. Fix `guideline_flags`. ASCII/Path/comments/logging [BLOCKS T156].
- [ ] T156 [US2] SAME commit: delete from `MistHelper.py`, rewrite internal callsites at `MistHelper.py:6594, 15736`, AND rewrite external callsite at `src/troubleshooting/marvis_troubleshoot_utils.py:21`. All edits in ONE commit (FR-003) [BLOCKS T157].
- [ ] T157 [US2] Wrapper-shim guard: `grep -n "^marvis_data_utils\s*=" MistHelper.py` returns zero hits.
- [ ] T158 [P] [US2] Local gates on all three affected files: py_compile, ruff, black, mypy strict on new module, pytest.
- [ ] T159 [US2] Compliance: new module A+/100. `MistHelper.py` unchanged. `src/troubleshooting/marvis_troubleshoot_utils.py` grade unchanged. Baseline >= 99.6/A+ [BLOCKS T160].
- [ ] T160 [US2] Open PR: `gh pr create --title "refactor(extract): marvis_data_utils low-use (P2 cross-file)" --body "Extracts marvis_data_utils (~4 LoC) into src/refactors/marvis_data_utils.py as class-body attribute per FR-005. Rewrites cross-file callsite in src/troubleshooting/marvis_troubleshoot_utils.py:21 atomically (FR-019). See plan.md PR-27."` [BLOCKS T161].
- [ ] T161 [US2] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T162].
- [ ] T162 [US2] Merge PR-27: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T163].
- [ ] T163 [US2] FR-019 post-merge grep audit: `grep -RIn "\bmarvis_data_utils\b" src/troubleshooting/` — confirm sole remaining reference imports from `src.refactors.marvis_data_utils`; paste audit output in PR retro comment [BLOCKS T164].
- [ ] T164 [US3] Refresh catalog. Confirm `marvis_data_utils` removed [BLOCKS T165].

### Phase B.15 - PR-28: `FAST_MODE_BACKOFF_MULTIPLIER` (assignment, 3 LoC, refs `MistHelper.py:1969, 9980, 15409`) -> `src/refactors/fast_mode_backoff_multiplier.py` (FR-020 rename from `fast__mode__backoff__multiplier.py`; assignment->class-body attribute per FR-005)

- [ ] T165 [US1] Read def-site and all THREE callsite contexts, `guideline_flags`. Confirm analyzer's suggested filename uses double-underscore separators; the landing filename MUST be single-underscore per FR-020 [BLOCKS T167].
- [ ] T166 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bFAST_MODE_BACKOFF_MULTIPLIER\b" --include="*.py" .` — expect definition + 3 callers.
- [ ] T167 [US1] Create `src/refactors/fast_mode_backoff_multiplier.py` (SINGLE-underscore filename per FR-020). Land as class-body attribute per FR-005. Record rename rationale in PR body. ASCII/Path/comments/logging [BLOCKS T168].
- [ ] T168 [US1] SAME commit: delete from `MistHelper.py` + rewrite ALL THREE callsites (1969, 9980, 15409) [BLOCKS T169].
- [ ] T169 [US1] Wrapper-shim guard: `grep -n "^FAST_MODE_BACKOFF_MULTIPLIER\s*=" MistHelper.py` returns zero hits. FR-020 verify: `test ! -f src/refactors/fast__mode__backoff__multiplier.py` (double-underscore file must NOT exist).
- [ ] T170 [P] [US1] Local gates: py_compile, ruff, black, mypy strict, pytest.
- [ ] T171 [US1] Compliance A+/100 + baseline >= 99.6/A+ [BLOCKS T172].
- [ ] T172 [US1] Open PR: `gh pr create --title "refactor(extract): FAST_MODE_BACKOFF_MULTIPLIER low-use" --body "Extracts FAST_MODE_BACKOFF_MULTIPLIER (~3 LoC) into src/refactors/fast_mode_backoff_multiplier.py as class-body attribute per FR-005. FR-020: renamed from analyzer-suggested fast__mode__backoff__multiplier.py to single-underscore per PEP 8. See plan.md PR-28."` [BLOCKS T173].
- [ ] T173 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T174].
- [ ] T174 [US1] Merge PR-28: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T175].
- [ ] T175 [US3] Refresh catalog. Confirm `FAST_MODE_BACKOFF_MULTIPLIER` removed [BLOCKS T176].

### Phase B.16 - PR-29: `FAST_MODE_DEVICES_PER_THREAD` (assignment, 3 LoC, refs `MistHelper.py:1972, 7470`) -> `src/refactors/fast_mode_devices_per_thread.py` (FR-020 rename; assignment->class-body attribute per FR-005)

- [ ] T176 [US1] Read def-site and both callsite contexts, `guideline_flags`. Confirm FR-020 rename need [BLOCKS T178].
- [ ] T177 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bFAST_MODE_DEVICES_PER_THREAD\b" --include="*.py" .` — expect definition + 2 callers.
- [ ] T178 [US1] Create `src/refactors/fast_mode_devices_per_thread.py` (single-underscore per FR-020). Class-body attribute per FR-005. ASCII/Path/comments/logging [BLOCKS T179].
- [ ] T179 [US1] SAME commit: delete from `MistHelper.py` + rewrite both callsites (1972, 7470) [BLOCKS T180].
- [ ] T180 [US1] Wrapper-shim guard: `grep -n "^FAST_MODE_DEVICES_PER_THREAD\s*=" MistHelper.py` returns zero hits. FR-020 verify: `test ! -f src/refactors/fast__mode__devices__per__thread.py`.
- [ ] T181 [P] [US1] Local gates: py_compile, ruff, black, mypy strict, pytest.
- [ ] T182 [US1] Compliance A+/100 + baseline >= 99.6/A+ [BLOCKS T183].
- [ ] T183 [US1] Open PR: `gh pr create --title "refactor(extract): FAST_MODE_DEVICES_PER_THREAD low-use" --body "Extracts FAST_MODE_DEVICES_PER_THREAD (~3 LoC) into src/refactors/fast_mode_devices_per_thread.py per FR-005 + FR-020. See plan.md PR-29."` [BLOCKS T184].
- [ ] T184 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T185].
- [ ] T185 [US1] Merge PR-29: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T186].
- [ ] T186 [US3] Refresh catalog. Confirm `FAST_MODE_DEVICES_PER_THREAD` removed [BLOCKS T187].

### Phase B.17 - PR-30: `FAST_MODE_SEQUENTIAL_MAX_RETRIES` (assignment, 3 LoC, refs `MistHelper.py:1977, 15549`) -> `src/refactors/fast_mode_sequential_max_retries.py` (FR-020 rename; class-body attribute per FR-005)

- [ ] T187 [US1] Read def-site and both callsite contexts, `guideline_flags`. Confirm FR-020 rename need [BLOCKS T189].
- [ ] T188 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bFAST_MODE_SEQUENTIAL_MAX_RETRIES\b" --include="*.py" .` — expect definition + 2 callers.
- [ ] T189 [US1] Create `src/refactors/fast_mode_sequential_max_retries.py` (single-underscore per FR-020). Class-body attribute per FR-005. ASCII/Path/comments/logging [BLOCKS T190].
- [ ] T190 [US1] SAME commit: delete from `MistHelper.py` + rewrite both callsites (1977, 15549) [BLOCKS T191].
- [ ] T191 [US1] Wrapper-shim guard: `grep -n "^FAST_MODE_SEQUENTIAL_MAX_RETRIES\s*=" MistHelper.py` returns zero hits. FR-020 verify: `test ! -f src/refactors/fast__mode__sequential__max__retries.py`.
- [ ] T192 [P] [US1] Local gates: py_compile, ruff, black, mypy strict, pytest.
- [ ] T193 [US1] Compliance A+/100 + baseline >= 99.6/A+ [BLOCKS T194].
- [ ] T194 [US1] Open PR: `gh pr create --title "refactor(extract): FAST_MODE_SEQUENTIAL_MAX_RETRIES low-use" --body "Extracts FAST_MODE_SEQUENTIAL_MAX_RETRIES (~3 LoC) into src/refactors/fast_mode_sequential_max_retries.py per FR-005 + FR-020. See plan.md PR-30."` [BLOCKS T195].
- [ ] T195 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T196].
- [ ] T196 [US1] Merge PR-30: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T197].
- [ ] T197 [US3] Refresh catalog. Confirm `FAST_MODE_SEQUENTIAL_MAX_RETRIES` removed [BLOCKS T198].

### Phase B.18 - PR-31: `FAST_MODE_USE_CONNECTION_AWARE_THREADING` (assignment, 3 LoC, refs `MistHelper.py:1984, 7460`) -> `src/refactors/fast_mode_use_connection_aware_threading.py` (FR-020 rename; class-body attribute per FR-005)

- [ ] T198 [US1] Read def-site and both callsite contexts, `guideline_flags`. Confirm FR-020 rename need [BLOCKS T200].
- [ ] T199 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bFAST_MODE_USE_CONNECTION_AWARE_THREADING\b" --include="*.py" .` — expect definition + 2 callers.
- [ ] T200 [US1] Create `src/refactors/fast_mode_use_connection_aware_threading.py` (single-underscore per FR-020). Class-body attribute per FR-005. ASCII/Path/comments/logging [BLOCKS T201].
- [ ] T201 [US1] SAME commit: delete from `MistHelper.py` + rewrite both callsites (1984, 7460) [BLOCKS T202].
- [ ] T202 [US1] Wrapper-shim guard: `grep -n "^FAST_MODE_USE_CONNECTION_AWARE_THREADING\s*=" MistHelper.py` returns zero hits. FR-020 verify: `test ! -f src/refactors/fast__mode__use__connection__aware__threading.py`.
- [ ] T203 [P] [US1] Local gates: py_compile, ruff, black, mypy strict, pytest.
- [ ] T204 [US1] Compliance A+/100 + baseline >= 99.6/A+ [BLOCKS T205].
- [ ] T205 [US1] Open PR: `gh pr create --title "refactor(extract): FAST_MODE_USE_CONNECTION_AWARE_THREADING low-use" --body "Extracts FAST_MODE_USE_CONNECTION_AWARE_THREADING (~3 LoC) into src/refactors/fast_mode_use_connection_aware_threading.py per FR-005 + FR-020. See plan.md PR-31."` [BLOCKS T206].
- [ ] T206 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T207].
- [ ] T207 [US1] Merge PR-31: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T208].
- [ ] T208 [US3] Refresh catalog. Confirm `FAST_MODE_USE_CONNECTION_AWARE_THREADING` removed [BLOCKS T209].

### Phase B.19 - PR-32: `MIST_WAN_TARGET_PORTS` (assignment, 3 LoC, cross-file P2, refs `MistHelper.py:1992, 15638 + src/gateway/gateway_export_utils.py:51`) -> `src/refactors/mist_wan_target_ports.py` (FR-020 rename; FR-019 cross-file audit; class-body attribute per FR-005)

- [ ] T209 [US2] Read def-site and all three callsite contexts including external caller `gateway_export_utils.py:51`, `guideline_flags`. Confirm FR-020 rename need [BLOCKS T211].
- [ ] T210 [P] [US2] Belt-and-suspenders grep: `grep -RIn "\bMIST_WAN_TARGET_PORTS\b" --include="*.py" .` — expect definition + 3 callers across 2 files.
- [ ] T211 [US2] Create `src/refactors/mist_wan_target_ports.py` (single-underscore per FR-020). Class-body attribute per FR-005. ASCII/Path/comments/logging [BLOCKS T212].
- [ ] T212 [US2] SAME commit: delete from `MistHelper.py`, rewrite internal callsites at `MistHelper.py:1992, 15638`, AND rewrite external callsite at `src/gateway/gateway_export_utils.py:51`. All edits in ONE commit (FR-003) [BLOCKS T213].
- [ ] T213 [US2] Wrapper-shim guard: `grep -n "^MIST_WAN_TARGET_PORTS\s*=" MistHelper.py` returns zero hits. FR-020 verify: `test ! -f src/refactors/mist__wan__target__ports.py`.
- [ ] T214 [P] [US2] Local gates on all three affected files: py_compile, ruff, black, mypy strict on new module, pytest.
- [ ] T215 [US2] Compliance: new module A+/100. `MistHelper.py` unchanged. `src/gateway/gateway_export_utils.py` grade unchanged. Baseline >= 99.6/A+ [BLOCKS T216].
- [ ] T216 [US2] Open PR: `gh pr create --title "refactor(extract): MIST_WAN_TARGET_PORTS low-use (P2 cross-file)" --body "Extracts MIST_WAN_TARGET_PORTS (~3 LoC) into src/refactors/mist_wan_target_ports.py as class-body attribute per FR-005. FR-020 rename applied. Rewrites cross-file callsite in src/gateway/gateway_export_utils.py:51 atomically (FR-019). See plan.md PR-32."` [BLOCKS T217].
- [ ] T217 [US2] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T218].
- [ ] T218 [US2] Merge PR-32: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T219].
- [ ] T219 [US2] FR-019 post-merge grep audit: `grep -RIn "\bMIST_WAN_TARGET_PORTS\b" src/gateway/` — confirm sole remaining reference imports from `src.refactors.mist_wan_target_ports`; paste audit output in PR retro comment [BLOCKS T220].
- [ ] T220 [US3] Refresh catalog. Confirm `MIST_WAN_TARGET_PORTS` removed [BLOCKS T221].

### Phase B.20 - PR-33: `BulkSwitchFirmwareUpgrader` (class, 19 LoC, FR-015 fold-in) -> `src/firmware/firmware_manager.py::FirmwareManager`

**Special case (FR-015)**: Fold-in variant, NO new file. `src/firmware/firmware_manager.py` MUST retain A+/100 (SC-013). This is the final Low-Use extraction; upon merge, SC-001 is satisfied.

- [ ] T221 [US1] Read def-site for `BulkSwitchFirmwareUpgrader` in fresh `MistHelper.py`. Read `guideline_flags` [BLOCKS T223, T224].
- [ ] T222 [P] [US1] Read `src/firmware/firmware_manager.py::FirmwareManager` — confirm existing A+/100 grade pre-PR; identify insertion point.
- [ ] T223 [P] [US1] Belt-and-suspenders grep: `grep -RIn "\bBulkSwitchFirmwareUpgrader\b" --include="*.py" .` — expect definition + 2 callers in `firmware_manager.py:1832, 1833`.
- [ ] T224 [US1] Fold `BulkSwitchFirmwareUpgrader` into `FirmwareManager` (FR-015). Fix `guideline_flags`. ASCII/safe_input/Path/comments/logging. Ensure `firmware_manager.py` retains A+/100 [BLOCKS T225].
- [ ] T225 [US1] SAME commit: delete from `MistHelper.py` + rewrite both caller references in `firmware_manager.py:1832, 1833` to the folded methods [BLOCKS T226].
- [ ] T226 [US1] Wrapper-shim guard: `grep -RIn "\bBulkSwitchFirmwareUpgrader\b" MistHelper.py` returns zero hits.
- [ ] T227 [P] [US1] Local gates on both affected files: py_compile, ruff, black, mypy strict, pytest.
- [ ] T228 [US1] Compliance: `firmware_manager.py` A+/100 preserved (SC-013). Baseline >= 99.6/A+ [BLOCKS T229].
- [ ] T229 [US1] Open PR: `gh pr create --title "refactor(extract): BulkSwitchFirmwareUpgrader low-use (FR-015 fold-in, final)" --body "Folds BulkSwitchFirmwareUpgrader (~19 LoC) into src/firmware/firmware_manager.py::FirmwareManager per FR-015. Final Low-Use extraction — SC-001 satisfied upon merge. See plan.md PR-33."` [BLOCKS T230].
- [ ] T230 [US1] 15/15 CI + CLEAN (no `--admin`) [BLOCKS T231].
- [ ] T231 [US1] Merge PR-33: `gh pr merge --squash --delete-branch`. Pull main [BLOCKS T232].
- [ ] T232 [US3] Refresh catalog. Confirm `BulkSwitchFirmwareUpgrader` removed AND Low-Use bucket now shows 0 entries (SC-001) [BLOCKS T233].

**Checkpoint B**: Low-Use bucket cleared (SC-001 satisfied). All 20 PRs merged serially with catalog refreshed between each. Proceed to Phase C.

---

## Phase C: Aggregate Verification (SC-001..SC-013)

**Purpose**: Verify every measurable outcome from spec.md Success Criteria against the final post-PR-33-merge `main` state. Runs after ALL 20 PRs merge; tasks may run in parallel (all [P]).

- [ ] T233 [P] SC-001 verify: `grep -A 2 "^## Low-Use" refactor_candidates.md` — confirm 0 entries OR documented Limitations rationale for any legitimate deferral (Hot reclassification mid-flight).
- [ ] T234 [P] SC-002 verify: `wc -l MistHelper.py` — confirm physical line count dropped by >= 2,500 lines relative to pre-initiative baseline (post-PR-13-merge snapshot).
- [ ] T235 [P] SC-003 verify: `grep -E "99\.6|A\+" data/full_repo_compliance_current.md` — confirm repo aggregate >= 99.6/A+ at every intermediate main-branch state (walk the merge sequence via `git log --oneline` and spot-check compliance snapshots).
- [ ] T236 [P] SC-004 verify: cross-reference pre- and post-initiative compliance snapshots — confirm zero A+ files regressed below A+.
- [ ] T237 [P] SC-005 verify: `gh pr list --state merged --search "refactor(extract)" --limit 25` — for each of PRs #14-#33, confirm merge occurred with 15/15 CI green. Any `--admin`-bypassed merge must have documented BLOCKED/DIRTY/BEHIND `mergeStateStatus` root cause in the PR body.
- [ ] T238 [P] SC-006 verify: enumerate every new file under `src/refactors/` created during PRs #14-#33 (17 expected: `wlanradius_timer_manager.py`, `wanprobe_config_manager.py`, `anomaly_metrics_discovery.py`, `device_data_fetcher.py`, `inventory_csvcomparator.py`, `device_config_template_cloner_manager.py`, `wanprobe_device_override_manager.py`, `initialize_mist_session_interactive.py`, `initialize_mist_session.py`, `package_import_map.py`, `main.py`, `marvis_data_utils.py`, `fast_mode_backoff_multiplier.py`, `fast_mode_devices_per_thread.py`, `fast_mode_sequential_max_retries.py`, `fast_mode_use_connection_aware_threading.py`, `mist_wan_target_ports.py`) — confirm each scores A+/100 in `data/full_repo_compliance_current.md`.
- [ ] T239 [P] SC-007 verify: `grep -RIn "\b\(WLANRadiusTimerManager\|WANProbeConfigManager\|AnomalyMetricsDiscovery\|DeviceDataFetcher\|InventoryCSVComparator\|FirmwareUpgradeStatusChecker\|DeviceConfigTemplateClonerManager\|WANProbeDeviceOverrideManager\|BulkAPFirmwareUpgrader\|initialize_mist_session_interactive\|initialize_mist_session\|PACKAGE_IMPORT_MAP\|marvis_data_utils\|FAST_MODE_BACKOFF_MULTIPLIER\|FAST_MODE_DEVICES_PER_THREAD\|FAST_MODE_SEQUENTIAL_MAX_RETRIES\|FAST_MODE_USE_CONNECTION_AWARE_THREADING\|MIST_WAN_TARGET_PORTS\|BulkSwitchFirmwareUpgrader\)\b" MistHelper.py` — must return ZERO hits. Also grep for wrapper `def <name>` in `MistHelper.py` — zero hits.
- [ ] T240 [P] SC-008 verify: `grep -A 5 "^## Skipped" refactor_candidates.md` — confirm `GlobalImportManager` still pinned; `git log --all --oneline --grep "GlobalImportManager"` between initiative kickoff and completion returns no modifying commits attributable to this initiative.
- [ ] T241 [P] SC-009 verify: cross-reference the 20 merged extraction PRs against the Hot bucket snapshot taken at initiative kickoff — confirm zero Hot source symbols were extracted (destination classes may be Hot per FR-009).
- [ ] T242 [P] SC-010 verify: walk the merged-PR sequence `#14..#33` via `gh pr list --state merged --search "refactor(extract)"` — confirm each PR's merge commit was followed by a `refactor_candidates.md` regeneration commit or verified regeneration on the next PR branch (catalog refresh trail).
- [ ] T243 [P] SC-011 verify: `git log --all --oneline --grep "guideline_flags"` and `git log -p specs/1011-misthelper-refactor-low-use/` — confirm each analyzer-flagged `guideline_flag` on extracted code was resolved within its extraction PR (spot-check PR-14 `raw_input_call`, PR-19 `oversize_25_lines`/`missing_inline_comments`/`non_ascii_logs`).
- [ ] T244 [P] SC-012 verify (FR-019 cross-file audit trail): `grep -RIn "\bmain\b" src/maps/maps_manager.py`, `grep -RIn "\bmarvis_data_utils\b" src/troubleshooting/`, `grep -RIn "\bMIST_WAN_TARGET_PORTS\b" src/gateway/` — confirm each remaining hit imports from `src.refactors.*` and none reference deleted `MistHelper.py` symbols. Confirm PR-26, PR-27, PR-32 retro comments each contain the audit output.
- [ ] T245 [P] SC-013 verify: `grep -E "src/firmware/firmware_manager\.py" data/full_repo_compliance_current.md` — confirm `src/firmware/firmware_manager.py` retains A+/100 after receiving all THREE fold-ins (PR-19, PR-22, PR-33).
- [ ] T246 After T233-T245 all green, tag the initiative complete: append a "1011 completion note" entry to `refactor_candidates.md` Limitations section (or the appropriate audit trail location) summarizing the 20-PR merge count, LoC drop, catalog transitions (any Low-Use -> Hot reclassifications), and the final Low-Use bucket state.

**Checkpoint C**: All 13 Success Criteria verified. Initiative 1011 complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase A (Pre-work)**: No dependencies — start immediately after 1010 close.
- **Phase B (Low-Use extractions)**: Depends on Phase A completion. Each Phase B.N group depends on Phase B.(N-1)'s catalog-refresh task.
- **Phase C (Aggregate verification)**: Depends on Phase B.20 (PR-33 merge + catalog refresh) completion.

### Serial PR Contract (spec Edge Cases, FR-002)

- Only ONE extraction PR is open at any time.
- Every candidate group's `refresh catalog` task (T017, T028, T039, T050, T061, T073, T084, T095, T107, T118, T129, T140, T152, T164, T175, T186, T197, T208, T220, T232) BLOCKS the first task of the next candidate group (FR-010, SC-010).
- No two Phase B candidate groups may execute in parallel.

### Within Each Candidate Group

- Reading def-site + callsite context + `guideline_flags` + belt-and-suspenders grep may run in parallel (marked [P]).
- Creating/folding the target module blocks the callsite rewrite (same commit constraint per FR-003).
- Local syntax/lint/type/test gates may run in parallel (marked [P]).
- Wrapper-shim guard and compliance re-check block PR-open.
- PR-open blocks CI-wait; CI-green blocks merge; merge blocks catalog refresh; catalog refresh blocks the next candidate group.
- For P2 cross-file PRs (PR-26, PR-27, PR-32), the FR-019 post-merge grep audit is a mandatory task between the pull-main step and the catalog-refresh step.

### Parallel Opportunities

- Phase A: T002, T003, T004, T005 may run in parallel after T001.
- Within any Phase B candidate group: the `[P]`-marked context reads, belt-and-suspenders grep, and local gate tasks may run in parallel.
- Phase C: All verification tasks T233-T245 may run in parallel; T246 depends on all of them.
- CROSS-CANDIDATE: strictly forbidden by the serial-PR contract. Do NOT parallelize PR-N with PR-N+1.

---

## Parallel Example: Phase A

```bash
# T001 first (refreshes catalog on fresh main), then in parallel:
grep -E "99\.6|A\+" data/full_repo_compliance_current.md        # T002
grep -A 5 "^## Skipped" refactor_candidates.md                  # T003
git status && git log --oneline -5                              # T004
grep -A 2 "^## Hot" refactor_candidates.md | head -20           # T005
```

## Parallel Example: Within One Candidate Group (PR-14 WLANRadiusTimerManager)

```bash
# After T006 (read def-site) completes, run in parallel:
# T007: read callsite contexts at MistHelper.py:20044 and :21515
# T008: read guideline_flags + belt-and-suspenders grep
# Both [P] tasks feed into T009 (create module + resolve raw_input_call).

# After T010 (delete + rewrite both callsites in same commit), run local gates in parallel:
python -m ruff check MistHelper.py src/refactors/wlanradius_timer_manager.py      # T012 part
python -m black --check MistHelper.py src/refactors/wlanradius_timer_manager.py   # T012 part
python -m mypy --strict src/refactors/wlanradius_timer_manager.py                 # T012 part
python -m pytest tests/ -k "not slow" -x                                          # T012 part
```

## Serial Example: Cross-Candidate (Non-parallelizable)

```bash
# T017 MUST complete (catalog refreshed after PR-14 merge) before T018 begins.
# PR-14 and PR-15 never execute concurrently — FR-002 forbids it.
```

---

## Implementation Strategy

### Serial-PR Discipline (Required)

1. Complete Phase A (T001-T005). Confirm Checkpoint A.
2. Execute PR-14 tasks (T006-T017) sequentially with in-group `[P]` parallelism.
3. After PR-14 merge + catalog refresh (T017): execute PR-15 tasks (T018-T028).
4. Continue through PR-33 (T221-T232) in the plan.md PR Dispatch Queue order.
5. Between merges, always refresh `refactor_candidates.md` and re-derive line numbers from the fresh catalog — line numbers listed in this file are the snapshot at spec/plan creation and WILL drift.
6. If the fresh catalog shows a Low-Use candidate has reclassified to Unused, reroute to a delete-only PR (FR-016 + 1010 Unused workflow). If reclassified to Hot, defer per FR-009/FR-016 and update SC-002 rationale.
7. Execute Phase C aggregate verification (T233-T246) once PR-33 is merged.

### MVP Increment (Optional)

Each merged PR delivers standalone value (spec User Story 1/2 "Independent Test"). Any prefix `PR-14..PR-N` yields a coherent `main` state at 99.6/A+ compliance with monotonically decreasing `MistHelper.py` line count. Dispatch may pause at any post-merge catalog-refresh checkpoint and resume from the next PR.

### No-Batch Guarantee

FR-002 prohibits batching multiple candidates into one PR. Even if two candidates appear "trivial together" (e.g. the four `FAST_MODE_*` constants), they get separate PRs. The serial workflow is what distinguishes this initiative from prior stalled attempts and preserves the SC-010 catalog audit trail.

### Cross-File PR Discipline (P2 only)

PR-26 (`main`), PR-27 (`marvis_data_utils`), and PR-32 (`MIST_WAN_TARGET_PORTS`) each touch a file outside `MistHelper.py` in the same commit as the extraction. The FR-019 post-merge grep audit is a hard gate — it BLOCKS the catalog-refresh task, and its output MUST be pasted into the PR retro comment as SC-012 acceptance evidence.

### FR-015 Fold-In Discipline

PR-19 (`FirmwareUpgradeStatusChecker`), PR-22 (`BulkAPFirmwareUpgrader`), and PR-33 (`BulkSwitchFirmwareUpgrader`) fold into `src/firmware/firmware_manager.py::FirmwareManager` rather than creating new `src/refactors/` modules. `firmware_manager.py`'s A+/100 grade MUST be preserved after each fold-in (SC-013); a single fold-in that regresses that file below A+ is a merge blocker.

### FR-020 Rename Discipline

PRs 28-32 land at single-underscore module paths (e.g. `fast_mode_backoff_multiplier.py`), NOT the analyzer's double-underscore suggestion. The rename rationale MUST appear in every affected PR description. Wrapper-shim guards for these PRs include a `test ! -f <double-underscore-path>` check to catch accidental double-underscore files.

---

## Notes

- `[P]` tasks = different files, no dependencies within one candidate group. Never parallelize across candidate groups (FR-002).
- `[BLOCKS T###]` = enforces the serial-PR contract across candidate groups. The catalog-refresh task at the end of each group is the pivot that BLOCKS the first task of the next group.
- Every catalog-refresh task provides the SC-010 audit trail. Missing refresh -> initiative fails SC-010.
- `--admin` merge bypass MUST NOT be used as a routine unblock (FR-011, `feedback_no_admin_bypass.md`). Investigate `mergeStateStatus` first; SKIPPED conditionals are not blocking.
- No new tests are mandated. Existing tests that reference an extracted symbol are updated in the same PR (carry-forward from 1010 research.md "Test-preservation rule").
- Analyzer (`tools/refactor_analyzer/`) is NEVER modified by this initiative (FR-018). Discrepancies are filed as separate analyzer bugs.
- Line numbers and LoC figures in this file reflect the plan.md PR Dispatch Queue snapshot at spec creation. Fresh analyzer output at PR dispatch time is authoritative — line numbers may drift as prior PRs land, and reference counts may shift per FR-016 (Low-Use -> Unused or Low-Use -> Hot reclassification handled by rerouting or deferring, respectively).
- The parent conversation controls PR dispatch cadence — this tasks file is the operator recipe, not an auto-execution script.
