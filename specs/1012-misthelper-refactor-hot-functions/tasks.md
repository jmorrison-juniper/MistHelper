# Tasks: MistHelper.py Refactor — Hot-Functions Bounded Bundle

**Input**: Design documents from `specs/1012-misthelper-refactor-hot-functions/`
**Prerequisites**: plan.md (loaded), spec.md (loaded), research.md (loaded), data-model.md (loaded), quickstart.md (loaded), contracts/ (loaded — extraction-pr-contract.md, di-slot-rename-contract.md, breadcrumb-audit-contract.md, compliance-gate-contract.md)

**Tests**: No new automated tests are added. Existing 15 CI functional jobs (matrix build, ruff, mypy, pylint, compliance analyzer, refactor analyzer smoke, unit tests, integration tests, end-to-end smoke) provide the mergeability contract per FR-011 / compliance-gate-contract.md. Adding new unit tests is explicitly out of scope per the "Non-Contracts" section of the extraction-pr-contract.

**Organization**: Tasks are grouped by user story to enable per-action traceability. All three user stories ship in a single bounded PR per FR-014 / extraction-pr-contract.md; the phase structure below preserves per-story auditability of the diff.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other [P] tasks in the same phase (different files, no dependencies on incomplete tasks).
- **[Story]**: Which user story this task belongs to (US1 = Action 1 tqdm skip-pin; US2 = Action 2 is_debug_mode; US3 = Action 3 connection_pool_executor).
- Every task references the SC and FR clauses it satisfies.

## Path Conventions

Single-project layout (per plan.md structure). All paths are repo-relative; absolute repo root is `c:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\`.

---

## Phase 1: Setup (Branch + Pre-flight)

**Purpose**: Prepare the working branch, verify the analyzer catalog is fresh, and confirm baselines before touching source.

- [ ] T001 Verify `main` is at the post-1011 head and pull latest: `git fetch origin main && git checkout main && git pull` (satisfies quickstart.md Prerequisite 1).
- [ ] T002 Create feature branch: `git checkout -b 1012-misthelper-refactor-hot-functions origin/main` (satisfies quickstart.md Branch Setup).
- [ ] T003 [P] Install pre-commit hooks: `pre-commit install` (satisfies quickstart.md Prerequisite 4 and enforces the Black + Ruff pre-push gate per `feedback_prepush_black_ruff.md`).
- [ ] T004 [P] Regenerate analyzer catalog to confirm all three targets are still valid: `python -m tools.refactor_analyzer > refactor_candidates.md`, then `grep -E "is_debug_mode|execute_with_connection_pool_management|tqdm" refactor_candidates.md` (satisfies quickstart.md Prerequisite 2, FR-010).
- [ ] T005 [P] Confirm `gh` CLI authentication: `gh auth status && gh pr view --json mergeStateStatus 2>/dev/null || true` (satisfies quickstart.md Prerequisite 3, `feedback_no_admin_bypass.md`).
- [ ] T006 Capture baseline compliance snapshot for the pre/post grade table: `python -m tools.compliance_analyzer --repo-wide > /tmp/1012_pre.txt` and record grades for `MistHelper.py`, `src/export/site_export_utils.py`, `src/gateway/gateway_export_utils.py`, `src/gateway/gateway_stats_exporter.py`, `src/gateway/overrides/_deps.py`, `src/gateway/overrides/device_data_fetcher.py` (satisfies compliance-gate-contract.md Per-File Grade Contract, SC-007).

**Checkpoint**: Branch checked out, hooks installed, analyzer confirms targets, baseline captured.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Confirm no in-progress diff exists, verify caller counts for the extractions, and pre-audit wrapper-deletion safety. **CRITICAL**: No extraction/deletion work in Phases 3-5 may begin until this phase is complete.

- [ ] T007 Verify caller count for `is_debug_mode()` primary target = 12: `git grep -n "is_debug_mode()" MistHelper.py | wc -l` (satisfies data-model.md ExtractionCandidate.validation_rules, SC-002).
- [ ] T008 Verify caller count for `EnvironmentUtils.is_debug_mode` wrapper = 0 (pre-delete grep audit per research.md Decision 1 / clarification Q1): `grep -R "EnvironmentUtils\.is_debug_mode" src/ MistHelper.py tests/ *.py *.md *.toml .github/ 2>/dev/null | grep -v "def is_debug_mode" | wc -l` (satisfies SC-011, FR-003).
- [ ] T009 Verify caller count for `execute_with_connection_pool_management(` = 7: `grep -Rn "execute_with_connection_pool_management(" src/ MistHelper.py | grep -v "^.*def " | wc -l` (satisfies data-model.md ExtractionCandidate.validation_rules, SC-003).
- [ ] T010 Verify DI-slot occurrence counts: `grep -Rn "is_debug_mode_fn" src/ MistHelper.py | wc -l` (expect 6) and `grep -Rn "connection_pool_fn" src/ MistHelper.py | wc -l` (expect 6) (satisfies di-slot-rename-contract.md, SC-005).
- [ ] T011 Confirm the tqdm fallback shim at `MistHelper.py:635` is untouched by any pending edit (byte-check): `sed -n '630,645p' MistHelper.py > /tmp/1012_tqdm_pre.txt` (satisfies data-model.md SkipPinnedSymbol.invariants, SC-001).

**Checkpoint**: All caller counts match the manifest (12, 0, 7, 6, 6). Baselines locked in. User story implementation may now begin.

---

## Phase 3: User Story 1 — Action 1 tqdm Skip-Pin (Priority: P1)

**Goal**: Land a mandatory NOTE breadcrumb at `MistHelper.py:635` documenting that the tqdm fallback shim is intentionally not extracted (bootstrap-critical for `GlobalImportManager` rebind pattern). Optionally invoke the analyzer's `--skip` CLI flag for a belt-and-suspenders pin.

**Independent Test**: `grep -n "tqdm extracted to SKIP_ALWAYS" MistHelper.py` returns exactly 1 hit at approximately line 635, AND `diff /tmp/1012_tqdm_pre.txt <(sed -n '630,645p' MistHelper.py)` shows only the added NOTE line (no shim source changes).

### Implementation for User Story 1

- [ ] T012 [US1] Locate the tqdm fallback shim block at `MistHelper.py:635` and insert the pinned extraction-template NOTE immediately above the shim: `# NOTE: tqdm extracted to SKIP_ALWAYS (bootstrap-critical). See specs/1012-misthelper-refactor-hot-functions/spec.md.` (satisfies SC-001, SC-014, FR-024, breadcrumb-audit-contract.md manifest row E1).
- [ ] T013 [US1] Verify the tqdm shim source code is byte-identical to the pre-edit snapshot except for the added NOTE line: `diff /tmp/1012_tqdm_pre.txt <(sed -n '631,646p' MistHelper.py)` (satisfies data-model.md SkipPinnedSymbol.validation_rules, SC-001).
- [ ] T014 [P] [US1] If the analyzer exposes a `--skip` CLI flag, persist the tqdm skip-pin: `python -m tools.refactor_analyzer --skip tqdm --help 2>/dev/null && python -m tools.refactor_analyzer --skip tqdm || echo "analyzer --skip flag not present; NOTE-only pin satisfies SC-001 per research.md Decision 7"` (satisfies FR-018, research.md Decision 7).

**Checkpoint**: US1 (Action 1) diff = exactly 1 NOTE line added to MistHelper.py at line ~635. Zero shim source changes. Breadcrumb grep-verifiable.

---

## Phase 4: User Story 2 — Action 2 `is_debug_mode` Extraction (Priority: P1)

**Goal**: Extract `def is_debug_mode()` at `MistHelper.py:318-320` to `src/refactors/is_debug_mode.py` as `IsDebugMode.check` (`@staticmethod`), delete the module-level function AND the zero-caller `EnvironmentUtils.is_debug_mode` wrapper at `MistHelper.py:5891-5900`, rewrite all 12 callsites, and rename the DI slot `is_debug_mode_fn` -> `check_fn` at 6 occurrences with a single pinned NOTE breadcrumb at the module-level slot in `src/export/site_export_utils.py`.

**Independent Test**: `grep -Rn "is_debug_mode(" src/ MistHelper.py` returns 0 hits (function calls), `grep -Rn "is_debug_mode_fn" src/ MistHelper.py` returns 0 hits (old DI slot), `grep -Rn "IsDebugMode.check" src/ MistHelper.py` returns 12+ hits (rewritten callsites + wiring), and `python -c "import MistHelper"` succeeds.

### Implementation for User Story 2

- [ ] T015 [US2] Create the new module `src/refactors/is_debug_mode.py` with `class IsDebugMode` containing a single `@staticmethod check() -> bool` copying the origin's body verbatim; include a module docstring referencing the spec, `from __future__ import annotations`, and inline comments every 5-10 lines per Constitution VI (satisfies SC-002, FR-005, research.md Decision 2, data-model.md TargetModule + TargetClass, quickstart.md Step 2a).
- [ ] T016 [US2] Add the import statement `from src.refactors.is_debug_mode import IsDebugMode` to the appropriate import block near the top of `MistHelper.py` (satisfies data-model.md Callsite.invariants, quickstart.md Step 2c).
- [ ] T017 [US2] Rewrite the 12 `is_debug_mode()` callsites in `MistHelper.py` -> `IsDebugMode.check()` (found via `git grep -n "is_debug_mode()" MistHelper.py`; expected sites include L13372, L13661, L18053, L18074, L18203, L18234, L18266, L18501, L18516 and 3 additional matches — rewrite until `git grep` returns zero function-call hits) (satisfies SC-002, FR-003, extraction-pr-contract.md diff-shape invariant 4, quickstart.md Step 2d).
- [ ] T018 [US2] Delete `def is_debug_mode():` at `MistHelper.py:318-320` and replace with the pinned extraction-template NOTE: `# NOTE: is_debug_mode extracted to IsDebugMode.check. See specs/1012-misthelper-refactor-hot-functions/spec.md.` (satisfies SC-002, SC-014, FR-024, breadcrumb-audit-contract.md manifest row E2, quickstart.md Step 2b).
- [ ] T019 [US2] Delete the `EnvironmentUtils.is_debug_mode` wrapper at `MistHelper.py:5891-5900` entirely (no NOTE required at this site — SC-011 documents the deletion audit trail via the spec itself) (satisfies SC-011, FR-003, research.md Decision 1, quickstart.md Step 2b).
- [ ] T020 [P] [US2] Rename `is_debug_mode_fn` -> `check_fn` at 5 occurrences in `src/export/site_export_utils.py` (L32 module-level slot, L52 dataclass field / global list, L64 assignment LHS/RHS, L76 assignment LHS/RHS, L337 function-body reference) and add exactly ONE pinned rename-template NOTE at the module-level slot declaration (L32) using the bare symbol form: `# NOTE: renamed from is_debug_mode; wiring source IsDebugMode.check at MistHelper.py:13372.` — the remaining 4 rename occurrences (L52/L64/L76/L337) do NOT carry additional NOTE lines (spec mandates 1 NOTE per DI cluster) (satisfies SC-005, SC-014, FR-024, di-slot-rename-contract.md Rename A rows 1-5, breadcrumb-audit-contract.md cluster R-A).
- [ ] T021 [US2] Rewrite the kwarg key at `MistHelper.py:13372` from `is_debug_mode_fn=<callable>` to `check_fn=IsDebugMode.check`. This site is a rename occurrence but does NOT carry an additional NOTE breadcrumb — the cluster's canonical NOTE lives on the module-level slot in `src/export/site_export_utils.py:32` (per spec's 1-NOTE-per-cluster rule) (satisfies SC-005, di-slot-rename-contract.md Rename A row 6, quickstart.md Step 2e).
- [ ] T022 [US2] Verify Phase 4 grep contract: `grep -Rn "is_debug_mode(" src/ MistHelper.py` expect 0, `grep -Rn "is_debug_mode_fn" src/ MistHelper.py` expect 0, `grep -Rn "IsDebugMode.check" src/ MistHelper.py` expect >=13 (12 callsites + wiring), `grep -Rn "EnvironmentUtils\.is_debug_mode" src/ MistHelper.py` expect 0 (satisfies SC-002, SC-005, SC-011, extraction-pr-contract.md merge-condition invariants, quickstart.md Step 2f).

**Checkpoint**: US2 (Action 2) closed. 12 callsites rewritten, function + wrapper deleted, 6 rename occurrences landed with pinned NOTE breadcrumbs.

---

## Phase 5: User Story 3 — Action 3 `execute_with_connection_pool_management` Extraction (Priority: P1)

**Goal**: Extract the public function plus 3 private `_pool_*` helpers at `MistHelper.py:7503-7576` to `src/refactors/connection_pool_executor.py` as `ConnectionPoolExecutor.execute` (public) + 3 private static methods, all `@staticmethod`, rewrite all 7 callsites across 3 files, and rename the DI slot `connection_pool_fn` -> `execute_fn` at 6 occurrences with a single pinned NOTE breadcrumb at the module-level slot in `src/gateway/overrides/_deps.py`.

**Independent Test**: `grep -Rn "execute_with_connection_pool_management(" src/ MistHelper.py` returns 0 hits, `grep -Rn "connection_pool_fn" src/ MistHelper.py` returns 0 hits, `grep -Rn "ConnectionPoolExecutor.execute" src/ MistHelper.py` returns 7+ hits, `python -c "import MistHelper"` succeeds, and the CI integration suites (gateway + export paths) remain green.

### Implementation for User Story 3

- [ ] T023 [US3] Create the new module `src/refactors/connection_pool_executor.py` with `class ConnectionPoolExecutor` containing 4 `@staticmethod` members: public `execute()` (copy origin signature verbatim; adjust internal calls to reference the private static helpers) plus 3 private static methods carrying the exact origin helper names from `MistHelper.py:7503-7576`. Include module docstring referencing the spec, `from __future__ import annotations`, inline comments every 5-10 lines per Constitution VI, and preserve original `[EXECUTE]` / `[SUCCESS]` / `[FAILURE]` action-log prefixes verbatim per Constitution VII (satisfies SC-003, FR-005, research.md Decisions 2 + 8, data-model.md TargetModule + TargetClass, quickstart.md Step 3a).
- [ ] T024 [P] [US3] Add the import statement `from src.refactors.connection_pool_executor import ConnectionPoolExecutor` to `src/gateway/gateway_export_utils.py` (satisfies data-model.md Callsite.invariants).
- [ ] T025 [P] [US3] Add the import statement `from src.refactors.connection_pool_executor import ConnectionPoolExecutor` to `src/gateway/gateway_stats_exporter.py` (satisfies data-model.md Callsite.invariants).
- [ ] T026 [US3] Add the import statement `from src.refactors.connection_pool_executor import ConnectionPoolExecutor` to the appropriate import block in `MistHelper.py` (satisfies data-model.md Callsite.invariants, quickstart.md Step 3c).
- [ ] T027 [US3] Rewrite the 4 `execute_with_connection_pool_management(...)` callsites in `MistHelper.py` at L6309, L10076, L15399, L15564 -> `ConnectionPoolExecutor.execute(...)` preserving arguments verbatim (satisfies SC-003, FR-003, extraction-pr-contract.md diff-shape invariant 4, quickstart.md Step 3d).
- [ ] T028 [P] [US3] Rewrite the 2 callsites in `src/gateway/gateway_export_utils.py` at L48 and L550 -> `ConnectionPoolExecutor.execute(...)` preserving arguments verbatim (satisfies SC-003, extraction-pr-contract.md diff-shape invariant 4, quickstart.md Step 3d).
- [ ] T029 [P] [US3] Rewrite the 1 callsite in `src/gateway/gateway_stats_exporter.py` at L32 -> `ConnectionPoolExecutor.execute(...)` preserving arguments verbatim (satisfies SC-003, extraction-pr-contract.md diff-shape invariant 4, quickstart.md Step 3d).
- [ ] T030 [US3] Delete the public function `def execute_with_connection_pool_management(...)` plus its 3 private `_pool_*` helpers at `MistHelper.py:7503-7576` and replace with the pinned extraction-template NOTE: `# NOTE: execute_with_connection_pool_management extracted to ConnectionPoolExecutor.execute. See specs/1012-misthelper-refactor-hot-functions/spec.md.` (satisfies SC-003, SC-014, FR-024, breadcrumb-audit-contract.md manifest row E3, quickstart.md Step 3b).
- [ ] T031 [P] [US3] Rename `connection_pool_fn` -> `execute_fn` at 4 occurrences in `src/gateway/overrides/_deps.py` (L18 module-level slot, L33 dataclass field / global list, L41 assignment LHS/RHS, L49 assignment LHS/RHS) and add exactly ONE pinned rename-template NOTE at the module-level slot declaration (L18) using the bare symbol form: `# NOTE: renamed from execute_with_connection_pool_management; wiring source ConnectionPoolExecutor.execute at MistHelper.py:15564.` — the remaining 3 rename occurrences (L33/L41/L49) do NOT carry additional NOTE lines (spec mandates 1 NOTE per DI cluster) (satisfies SC-005, SC-014, FR-024, di-slot-rename-contract.md Rename B rows 1-4, breadcrumb-audit-contract.md cluster R-B).
- [ ] T032 [P] [US3] Rename `connection_pool_fn` -> `execute_fn` at `src/gateway/overrides/device_data_fetcher.py:40`. This site is a rename occurrence but does NOT carry a NOTE breadcrumb — the cluster's canonical NOTE lives on the module-level slot in `src/gateway/overrides/_deps.py:18` (per spec's 1-NOTE-per-cluster rule) (satisfies SC-005, di-slot-rename-contract.md Rename B row 5).
- [ ] T033 [US3] Rewrite the kwarg key at `MistHelper.py:15564` from `connection_pool_fn=<callable>` to `execute_fn=ConnectionPoolExecutor.execute`. This site is a rename occurrence but does NOT carry an additional NOTE breadcrumb — the cluster's canonical NOTE lives on the module-level slot in `src/gateway/overrides/_deps.py:18` (per spec's 1-NOTE-per-cluster rule) (satisfies SC-005, di-slot-rename-contract.md Rename B row 6, quickstart.md Step 3e).
- [ ] T034 [US3] Verify Phase 5 grep contract: `grep -Rn "execute_with_connection_pool_management(" src/ MistHelper.py` expect 0, `grep -Rn "connection_pool_fn" src/ MistHelper.py` expect 0, `grep -Rn "ConnectionPoolExecutor.execute" src/ MistHelper.py` expect >=8 (7 callsites + wiring), and `python -c "import MistHelper"` succeeds (satisfies SC-003, SC-005, extraction-pr-contract.md merge-condition invariants, quickstart.md Step 3f).

**Checkpoint**: US3 (Action 3) closed. 7 callsites rewritten across 3 files, public function + 3 helpers deleted, 6 rename occurrences landed with pinned NOTE breadcrumbs.

---

## Phase 6: Polish & Cross-Cutting Concerns (Verification, Compliance, Ship)

**Purpose**: SC-014 breadcrumb audit, pre-push format gate, compliance verification, commit, PR, monitor, merge, post-merge housekeeping.

### Breadcrumb Audit (SC-014)

- [ ] T035 Run the full breadcrumb-audit grep sweep: `grep -R "specs/1012-misthelper-refactor-hot-functions/spec.md" src/ MistHelper.py` expect exactly 3 hits (E1 at MistHelper.py:~635, E2 at MistHelper.py:~318, E3 at MistHelper.py:~7503); `grep -R "renamed from is_debug_mode" src/ MistHelper.py` expect exactly 1 hit (at `src/export/site_export_utils.py:32`); `grep -R "renamed from execute_with_connection_pool_management" src/ MistHelper.py` expect exactly 1 hit (at `src/gateway/overrides/_deps.py:18`) (satisfies SC-014, breadcrumb-audit-contract.md verification-grep-commands, quickstart.md Step 4).
- [ ] T036 Verify per-file rename NOTE counts: `grep -c "renamed from is_debug_mode" src/export/site_export_utils.py` expect 1, `grep -c "renamed from is_debug_mode" MistHelper.py` expect 0, `grep -c "renamed from execute_with_connection_pool_management" src/gateway/overrides/_deps.py` expect 1, `grep -c "renamed from execute_with_connection_pool_management" src/gateway/overrides/device_data_fetcher.py` expect 0, `grep -c "renamed from execute_with_connection_pool_management" MistHelper.py` expect 0 (satisfies SC-014, breadcrumb-audit-contract.md per-file counts). Also verify zero survivors of the old DI-slot names: `grep -R "is_debug_mode_fn" src/ MistHelper.py` expect 0, `grep -R "connection_pool_fn" src/ MistHelper.py` expect 0.

### Local Pre-Push Gate (feedback_prepush_black_ruff.md)

- [ ] T037 [P] Run Black check: `black --check src/ MistHelper.py` (expect zero diff — satisfies compliance-gate-contract.md pre-push-local-gate, `feedback_prepush_black_ruff.md`, quickstart.md Step 5).
- [ ] T038 [P] Run Ruff lint: `ruff check src/ MistHelper.py` (expect zero issues — satisfies compliance-gate-contract.md pre-push-local-gate).
- [ ] T039 [P] Run Ruff format check: `ruff format --check src/ MistHelper.py` (expect zero diff — satisfies compliance-gate-contract.md pre-push-local-gate).

### Compliance Verification

- [ ] T040 [P] Verify new file `src/refactors/is_debug_mode.py` grades A+/100: `python -m tools.compliance_analyzer src/refactors/is_debug_mode.py` (satisfies SC-007, FR-011, compliance-gate-contract.md per-file grade contract, quickstart.md Step 6).
- [ ] T041 [P] Verify new file `src/refactors/connection_pool_executor.py` grades A+/100: `python -m tools.compliance_analyzer src/refactors/connection_pool_executor.py` (satisfies SC-007, FR-011, compliance-gate-contract.md per-file grade contract).
- [ ] T042 Run aggregate compliance: `python -m tools.compliance_analyzer --repo-wide` (expect `>=99.6/A+` — satisfies SC-007, FR-011, compliance-gate-contract.md aggregate threshold).
- [ ] T043 Run pylint aggregate: `pylint src/ MistHelper.py` (expect `>=8.74/10` — satisfies SC-007, FR-011, compliance-gate-contract.md pylint threshold).
- [ ] T044 Build the pre/post grade table for the PR body by comparing `/tmp/1012_pre.txt` (from T006) against the T042 post-PR output for each of the 6 touched files + 2 new files (satisfies compliance-gate-contract.md per-file grade contract PR-body inclusion).
- [ ] T045 Verify zero open `guideline_flags` on both new files (no `missing_inline_comments`, no `missing_action_logging`, no `raw_input_call`, no `non_ascii_logs`, no *new* `oversize_25_lines`) by inspecting the T040/T041 analyzer output (satisfies compliance-gate-contract.md guideline-flag-resolution, Constitution VI + VII NON-NEGOTIABLE, FR-006).

### Commit & Push

- [ ] T046 Stage the edit surface: `git add MistHelper.py src/refactors/is_debug_mode.py src/refactors/connection_pool_executor.py src/export/site_export_utils.py src/gateway/gateway_export_utils.py src/gateway/gateway_stats_exporter.py src/gateway/overrides/_deps.py src/gateway/overrides/device_data_fetcher.py` (satisfies extraction-pr-contract.md diff-shape invariants).
- [ ] T047 Create a single squashed commit: `git commit -m "refactor(1012): bundle hot-functions extractions (tqdm skip-pin + is_debug_mode + connection_pool_executor)"` (satisfies FR-014, extraction-pr-contract.md single-PR atomicity, quickstart.md Step 7).
- [ ] T048 Push the branch: `git push -u origin 1012-misthelper-refactor-hot-functions` (satisfies quickstart.md Step 7).

### PR Open & Monitor

- [ ] T049 Open the PR using `gh pr create` with the title `refactor(1012): hot-functions bounded bundle (SC-001/002/003)` and a body enumerating Summary (3 actions), Edit Surface (2 new files, 19 callsite rewrites, 12 DI-slot renames, 6 breadcrumbs, zero shims), Compliance table from T044, Verification link to quickstart.md, and Constitution PASS statement (satisfies FR-014, extraction-pr-contract.md, quickstart.md Step 8).
- [ ] T050 Monitor CI: `gh pr checks --watch` — wait for all 15 functional jobs to report green (satisfies FR-011, SC-006, compliance-gate-contract.md CI job contract, quickstart.md Step 9).
- [ ] T051 Verify `mergeStateStatus: CLEAN` before merging: `gh pr view --json mergeStateStatus` — if BLOCKED/DIRTY/BEHIND, investigate root cause per `feedback_no_admin_bypass.md`; do NOT reach for `--admin` reflexively; SKIPPED conditional jobs are not blocking (satisfies FR-011, `feedback_no_admin_bypass.md`, quickstart.md Step 9).
- [ ] T052 Merge the PR once CLEAN: `gh pr merge --squash --delete-branch` (satisfies extraction-pr-contract.md single-PR atomicity, quickstart.md Step 9).

### Post-Merge Housekeeping

- [ ] T053 Regenerate the analyzer catalog against the new `main` head: `git checkout main && git pull && python -m tools.refactor_analyzer > refactor_candidates.md` (satisfies FR-010, quickstart.md Step 10).
- [ ] T054 Commit and push the regenerated catalog: `git add refactor_candidates.md && git commit -m "chore: regenerate refactor_candidates.md post-1012 merge" && git push` (satisfies FR-010, quickstart.md Step 10).
- [ ] T055 Confirm the 1012 initiative is closed and any follow-on hot-bucket work is scoped by a new `1013-*` initiative (satisfies plan.md "What This Plan Does NOT Do" boundary).

**Checkpoint**: PR merged, refactor catalog updated, initiative closed.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — can start immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1 completion. BLOCKS all user stories.
- **Phase 3 (US1 tqdm skip-pin)**: Depends on Phase 2. Trivial diff; only touches `MistHelper.py:635`.
- **Phase 4 (US2 is_debug_mode)**: Depends on Phase 2. Touches `MistHelper.py` + `src/refactors/is_debug_mode.py` + `src/export/site_export_utils.py`.
- **Phase 5 (US3 connection_pool_executor)**: Depends on Phase 2. Touches `MistHelper.py` + `src/refactors/connection_pool_executor.py` + `src/gateway/*` + `src/gateway/overrides/_deps.py` + `src/gateway/overrides/device_data_fetcher.py`.
- **Phase 6 (Polish)**: Depends on Phase 3 + Phase 4 + Phase 5 all complete (single bounded PR per FR-014).

### Within-Story Task Dependencies

**Phase 3 (US1)**:
- T012 -> T013 (verify after adding NOTE)
- T014 independent [P]

**Phase 4 (US2)**:
- T015 (create module) -> T016 (add import) -> T017 (rewrite callsites) -> T018 (delete origin + breadcrumb)
- T019 (delete wrapper) can run in parallel with T018 (different lines in same file, but sequential edit is safer to avoid line-number drift)
- T020 (site_export_utils.py renames) [P] — independent file
- T021 (MistHelper.py:13372 kwarg rename) depends on T015 (needs `IsDebugMode.check` to reference)
- T022 (verify) depends on T017 + T018 + T019 + T020 + T021

**Phase 5 (US3)**:
- T023 (create module) -> T024 [P], T025 [P], T026 (add imports in 3 files)
- T027, T028 [P], T029 [P] (rewrite 7 callsites) all depend on T023-T026
- T030 (delete origin + breadcrumb) depends on T027 + T028 + T029
- T031 [P], T032 [P] (renames in _deps.py + device_data_fetcher.py) — independent files, can run parallel to T027-T029
- T033 (MistHelper.py:15564 kwarg rewrite + rename) depends on T023 (needs `ConnectionPoolExecutor.execute` to reference)
- T034 (verify) depends on T027 + T028 + T029 + T030 + T031 + T032 + T033

**Phase 6**:
- T035 + T036 (breadcrumb audit) after all Phases 3-5
- T037-T039 [P] (pre-push gate) after T035-T036
- T040-T041 [P] (per-file compliance) after T037-T039
- T042, T043 (aggregate compliance + pylint) after T040-T041
- T044 (grade table) after T042
- T045 (guideline flags) after T040-T041
- T046 -> T047 -> T048 (stage, commit, push)
- T049 -> T050 -> T051 -> T052 (PR create, monitor, verify clean, merge)
- T053 -> T054 -> T055 (post-merge)

### Parallel Opportunities

- **Phase 1**: T003, T004, T005 can run in parallel after T002.
- **Phase 3**: T014 can run in parallel with T012/T013.
- **Phase 4**: T020 (site_export_utils.py edits) parallel to T017-T019 (MistHelper.py edits).
- **Phase 5**: T024, T025 parallel to T026 (all 3 add-import edits are in different files); T028, T029 parallel to T027 (callsite rewrites in different files); T031, T032 parallel to T027-T030 (rename edits in different files from the extraction).
- **Phase 6**: T037-T039 (Black + Ruff triple) run in parallel; T040 + T041 (per-file compliance) run in parallel.

---

## Parallel Example: Phase 5 (User Story 3)

```bash
# After T023 creates ConnectionPoolExecutor, launch imports in parallel:
Task: "T024 Add import to src/gateway/gateway_export_utils.py"
Task: "T025 Add import to src/gateway/gateway_stats_exporter.py"
Task: "T026 Add import to MistHelper.py"

# After imports land, launch callsite rewrites in parallel (different files):
Task: "T028 Rewrite 2 callsites in src/gateway/gateway_export_utils.py:48,550"
Task: "T029 Rewrite 1 callsite in src/gateway/gateway_stats_exporter.py:32"
# T027 rewrites 4 callsites in MistHelper.py — must run alongside but sequenced within MistHelper.py edits

# DI-slot renames in parallel (different files):
Task: "T031 Rename 4 occurrences in src/gateway/overrides/_deps.py"
Task: "T032 Rename 1 occurrence in src/gateway/overrides/device_data_fetcher.py:40"
```

---

## Implementation Strategy

### Bounded Single-PR Delivery (Not Serial MVP)

Unlike 1010/1011's per-candidate serial workflow, this initiative bundles three actions into one atomic PR per FR-014 / extraction-pr-contract.md / research.md Decision 6. There is no meaningful "MVP subset" — the three actions were bundled precisely because splitting them would either (a) recreate the wrapper-shim pattern FR-003 prohibits (splitting Action 2's extract from its wrapper delete leaves dead code on `main`), (b) leave orphaned private helpers in `MistHelper.py` (splitting Action 3's public extract from its 3 private helpers), or (c) waste CI cycles on functionally-trivial single-action PRs (Action 1's zero-extraction NOTE).

**Sequencing recommendation** (single contributor, one branch):

1. Complete **Phase 1 + Phase 2** (setup + foundational verification).
2. Execute **Phase 3** first (US1 tqdm skip-pin — trivial single NOTE edit; establishes the branch has committed work).
3. Execute **Phase 4** (US2 is_debug_mode extraction — mostly self-contained to MistHelper.py + one external file).
4. Execute **Phase 5** (US3 connection_pool_executor — touches 4 files beyond MistHelper.py; higher review surface).
5. Complete **Phase 6** (verify, format, comply, commit, push, PR, monitor, merge, post-merge).

### Parallel Team Strategy (if multiple contributors)

The single-PR requirement (FR-014) constrains parallel team work: only one branch can hold the atomic diff. However, within the branch, distinct contributors can work concurrently:

- Contributor A: Phase 3 (US1) + Phase 4 T015-T019 (US2 MistHelper-side edits)
- Contributor B: Phase 4 T020 (US2 site_export_utils.py renames) + Phase 5 T023 + T031/T032 (US3 module + external renames)
- Contributor C: Phase 5 T024-T029 (US3 imports + callsite rewrites)
- All contributors converge for Phase 6.

### Rollback Plan (extraction-pr-contract.md)

If any post-merge signal indicates regression, open a single revert PR restoring the pre-1012 state; do NOT attempt partial rollback (partial rollback would recreate the wrapper-shim state FR-003 prohibits).

---

## Notes

- Every task references at least one Success Criterion (SC-001..SC-014) and one Functional Requirement (FR-001..FR-024) it satisfies. Traceability is grep-verifiable in this file: `grep -Ec "SC-[0-9]+" tasks.md` and `grep -Ec "FR-[0-9]+" tasks.md`.
- [P] tasks = different files, no dependencies on incomplete tasks in the same phase.
- [US1/US2/US3] labels map task to specific user story for per-action auditability of the atomic diff.
- Every extraction/deletion site and every DI-rename site MUST carry its pinned NOTE breadcrumb before Phase 6 verification runs — otherwise T035/T036 will fail the grep-count contract.
- Commit granularity: the branch may accumulate multiple work-in-progress commits during Phases 3-5; T047 squashes them into a single atomic commit at PR creation time per FR-014.
- No `--admin` merge bypass unless failure has been triaged per `feedback_no_admin_bypass.md`; SKIPPED conditional jobs are NOT blocking.
- Pre-push Black + Ruff gate (T037-T039) is MANDATORY before T048 push per `feedback_prepush_black_ruff.md`.
- The two new files under `src/refactors/` MUST land A+/100 (T040, T041); pre-existing non-A+ files are NOT required to reach A+ as a side effect of touching them (FR-019 carry-forward).
