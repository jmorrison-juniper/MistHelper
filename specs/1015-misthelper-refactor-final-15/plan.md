# Implementation Plan: MistHelper Refactor — Final 15 (All Remaining Analyzer Candidates)

**Branch**: `1015-misthelper-refactor-final-15` | **Date**: 2026-07-09 | **Spec**: [`spec.md`](./spec.md)
**Input**: Feature specification from `/specs/1015-misthelper-refactor-final-15/spec.md`

## Summary

Retire the 15 remaining `MistHelper.py` extraction candidates surfaced by `tools/refactor_analyzer/` at commit `8523596` — 3 Single-use, 2 Low-use, 10 Hot — as fifteen atomic Cat E cross-package extraction PRs, one candidate per PR, in the bucket-first (Single-use -> Low-use -> Hot descending-by-LOC) order fixed in the spec's Dispatch Queue. Every hot class with runtime deps lands under **Pattern 1 constructor injection** (`__init__(self, **deps)`, kwargs spelled out at every callsite; NO factories, NO cached module-level instance, NO `sys.modules` self-resolution, NO shims or facades). Module-level constants (T-02, T-03, T-15) land as bare module-level assignments in a semantically appropriate submodule; pure static helpers stay `@staticmethod`. Every `mh = importlib.import_module("MistHelper")` + `mh.<Name>` lazy-import in `src/` is eliminated in the same commit as the body move. `menu_actions` and `GlobalImportManager` are excluded per FR-010 / FR-009. Initiative closes with `refactor_candidates.md` showing only those two entries.

## Technical Context

**Language/Version**: Python 3.13+ (constitution technology-constraint)
**Primary Dependencies**: `mistapi 0.59+`, `tqdm`, `PrettyTable`, project-internal `src/*` packages (`src.api.apisession`, `src.time.time_utils`, `src.refactors.is_debug_mode`, etc.)
**Storage**: N/A (refactor initiative — data flow unchanged)
**Testing**: `python MistHelper.py --test` (functional smoke suite; 15 CI jobs); pre-push `black --check` + `ruff check` gate per `feedback_prepush_black_ruff.md`
**Target Platform**: Windows 11 local dev + Linux container (podman `ghcr.io/jmorrison-juniper/misthelper:latest`)
**Project Type**: Single-project CLI (Python entrypoint `MistHelper.py` + `src/` package tree)
**Performance Goals**: No behavior change — extractions are byte-for-byte semantic equivalents post-move; `python MistHelper.py --test` must report 0 failed / exit 0 modulo the `test_menu_196_dispatches_to_async_claim_exporter` flake (E-7)
**Constraints**: Repo-wide compliance floor >= 99.6/A+ per merge (SC-003); every new file at A+/100 (SC-006); `MistHelper.py` pylint non-regressing (SC-015); zero new mypy strict violations (SC-019); zero new SKIPPED CI conditionals (SC-016); one open PR at a time (FR-023); `--admin` merge bypass prohibited as routine unblock (FR-015 / `feedback_no_admin_bypass.md`)
**Scale/Scope**: 15 PRs, ~4,271 LoC removed from `MistHelper.py` (dominated by T-04 `ENDPOINT_PRIMARY_KEY_STRATEGIES` at 2,327 LoC); SC-002 target >= 3,500 LoC net drop; 17 `src/` files touched for the highest-refs candidate T-09 (`InputUtils`, 195 refs)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Cross-check against `.specify/memory/constitution.md` v1.4.0 (all seven Core Principles + Technology Constraints + Multi-Agent Git Workflow):

| Principle | Compliance | Notes |
|---|---|---|
| I. Five-Item Rule | PASS | Every new module lands classes/methods <= 25 lines, <= 5 params; oversize-flagged candidates (T-04, T-06, T-07, T-08, T-10) carry mandatory in-flight decomposition per FR-006 / E-2 / E-10. |
| II. Class-Based Architecture (No Wrappers) | PASS | Pattern 1 constructor injection preserves class-based ownership; FR-003 explicitly prohibits wrapper shims, forwarding functions, re-export modules, delegators, pointers, and backward-compat aliases (SC-007). Module-level constants (T-02, T-03, T-15) are pure data — not wrappers. |
| III. Safety-First (NON-NEGOTIABLE) | PASS | T-09 (`InputUtils`) carries `raw_input_call` flag — FR-006 requires in-flight remediation to `InputUtils.safe_input()`. No destructive-operation code paths modified. |
| IV. Full Deployment Pipeline (NON-NEGOTIABLE) | PASS | Every PR runs `python -m py_compile MistHelper.py` implicitly via `python MistHelper.py --test` gate; merged main triggers container rebuild via `container-build.yml`. |
| V. Observability & Logging | PASS | FR-006 remediates `non_ascii_logs` (T-04, T-08) and `missing_action_logging` (T-01, T-02, T-03, T-05, T-11, T-14, T-15) in-flight. Every new module uses `%s` formatting per constitution VII. |
| VI. Inline Comments (NON-NEGOTIABLE) | PASS | FR-006 remediates `missing_inline_comments` (T-02, T-04, T-06, T-10, T-11, T-13, T-15) in-flight. New modules land with inline comment on every executable line. |
| VII. Action Logging (NON-NEGOTIABLE) | PASS | FR-006 remediates `missing_action_logging` flags in-flight; every method in every new module lands with `logging.info` before / `logging.debug` after envelopes. |
| Complexity-Driven SpecKit Escalation | PASS | Multi-file, multi-class initiative — spec authored (FR-021: no new features / CLI flags / behavior). |
| Multi-Agent Git Workflow | PASS | Branch pattern `refactor/1015-tNN-<slug>` off `main`; squash-merge; one open PR at a time (FR-023); no branching from feature branches. |

**Gate result**: PASS. No violations. Complexity Tracking table empty.

## Project Structure

### Documentation (this feature)

```text
specs/1015-misthelper-refactor-final-15/
├── spec.md              # Feature specification (authored 2026-07-09)
├── plan.md              # This file (/speckit.plan output)
├── checklists/
│   └── requirements.md  # 26 items, all passing pre-plan
└── tasks.md             # /speckit.tasks output (15 tasks, one per Dispatch Queue row)
```

Research, data-model, quickstart, and contracts artifacts are NOT produced for this initiative. Rationale documented in Phase 0 below.

### Source Code (repository root)

```text
MistHelper.py                              # Entrypoint — 15 symbols excised across the initiative
src/
├── api/                                   # apisession, api_core_fetch_utils (deps injected into hot classes)
├── config/                                # NEW landing dir for T-12 (ConfigUtils)  -- may already exist as fold-in target
│   └── config_utils.py                    # T-12 lands here
├── data/                                  # NEW landing dir for T-10 (DataProcessingUtils)
│   └── data_processing_utils.py           # T-10 lands here
├── device/
│   ├── prompt_utils.py                    # existing (52 KB) -- E-1 review: fold T-07 in OR override to src/ui/prompt_utils.py
│   └── virtual_chassis.py                 # T-11 folds into existing class body
├── export/
│   ├── data_exporter.py                   # T-08 lands here
│   └── org_inventory_exporter.py          # T-06 lands here
├── refactors/                             # fallback landing when no closer semantic fit exists
│   ├── device_data_fetcher.py             # T-01 folds into DeviceDataFetcherManager or dataclass (per E-1)
│   ├── endpoint__primary__key__strategies.py     # T-04 (2327 LoC) lands here (or src/api/*.py per E-1)
│   ├── fast__mode__max__concurrent__connections.py       # T-02
│   ├── fast__mode__use__connection__aware__threading.py  # T-03
│   ├── mist_site_exclude_prefix.py        # T-15
│   ├── detect_msp_privileges.py           # T-05 (or src/msp/*.py per E-1)
│   └── ... (existing modules unchanged)
├── ui/
│   ├── input_utils.py                     # T-09 lands here (existing src/utils/input_utils.py, E-1 review at dispatch)
│   └── prompt_utils.py                    # T-07 candidate landing (existing src/device/prompt_utils.py, E-1 review)
├── utils/
│   ├── file_path_utils.py                 # T-13 lands here
│   └── tqdm_wrapper.py                    # T-14 lands here (or src/ui/*.py per E-1)
tests/
└── (test files converted per FR-030 in same commit as each extraction PR)
```

**Structure Decision**: Single-project layout (constitution technology). New landings prefer domain-fitting semantic packages (`src/export/`, `src/ui/`, `src/device/`, `src/data/`, `src/config/`, `src/utils/`) over the `src/refactors/` fallback. Two directories (`src/config/`, `src/data/`) do not yet exist and will be created at dispatch time if T-10 / T-12 land there rather than folding into another module (E-1 dispatch-time choice). Every landing decision is recorded in the PR description per E-1 / FR-029.

## Architecture Strategy

### Guiding Principles (durable user directive — DO NOT DEVIATE)

1. **Pattern 1 constructor injection is the ONLY landing pattern for hot classes with runtime deps.** Every extracted hot class exposes `def __init__(self, **deps)` where every dependency is a **required kwarg**. The 14 typical DI kwargs (subset per class) are: `apisession`, `PromptUtils`, `ConfigUtils`, `DataProcessingUtils`, `DataExporter`, `TimeUtils`, `EnhancedSSHRunner`, `InsightMetricsUtils`, `PacketCaptureManager`, `APICoreFetchUtils`, `check_fn=IsDebugMode.check`, `PrettyTable`, `tqdm`, `mistapi`. Every callsite constructs the instance inline with the full kwargs list spelled out. **NO factory helpers. NO cached module-level instance. NO `sys.modules` self-resolution. NO delegators/shims/pointers. NO backwards-compat facades.**
2. **Cat A facade removal** — delete the class entirely, rewrite every callsite. Applies only if a candidate reclassifies to Cat A mid-initiative (0 Cat A at initiative start per spec).
3. **Cat E pure module extraction** — for module-level constants and pure single-use symbols with no runtime deps, land as bare module-level assignments or plain `@staticmethod` collections in `src/refactors/<name>.py` (or a semantically appropriate submodule) and rewrite import paths.
4. **No wrapper shim, forwarding function, re-export module, delegator, pointer, helper, or backward-compat alias may survive in `MistHelper.py`** (SC-007). Only a single-line NOTE breadcrumb is left at the deletion site (FR-007 / SC-012).
5. **Every `mh = importlib.import_module("MistHelper")` + `mh.<Name>` lazy-import pattern is eliminated** for the extracted symbol in the same commit (SC-009). This pattern was tolerated during 1014's transition and is now retired.

### Per-Bucket Implementation Approach

**Bucket A — Single-use (T-01, T-02, T-03) — Queue-head validation, 1 caller each**

Purpose: warm up the workflow at the minimum blast radius before touching Low-use and Hot candidates.

- **T-01 (`DeviceFetchConfig`, class, 9 LoC, 1 ref)**: Fold as top-level `@dataclass` into `src/refactors/device_data_fetcher.py` (E-1 override: fold into `DeviceDataFetcherManager` class body ONLY if the class's public surface would benefit from a nested config; default is top-level dataclass). Sole callsite at `src/refactors/device_data_fetcher.py:49` rewritten in same commit. Remediate `missing_action_logging` in-flight.
- **T-02 (`FAST_MODE_MAX_CONCURRENT_CONNECTIONS`, assignment, 3 LoC, 1 ref)**: Module-level constant at `src/refactors/fast__mode__max__concurrent__connections.py` (E-14: bare module-level constant, ignore analyzer's `Suggested class` `FastModeMaxConcurrentConnectionsManager` naming hint). Prefer fold into an existing fast-mode constants module in the destination package if one exists. Remediate `missing_inline_comments` + `missing_action_logging` in-flight (constant carries no methods — flag remediation is exercised on the read-side documentation).
- **T-03 (`FAST_MODE_USE_CONNECTION_AWARE_THREADING`, assignment, 3 LoC, 1 ref)**: Same landing pattern as T-02. Consider co-locating with T-02 in the same destination file if the fold-in target exists.

**Bucket B — Low-use (T-04, T-05) — 2 callers each**

Purpose: prove the 2-callsite atomic-rewire pattern; T-04 is the largest LOC win in the whole initiative and reclaims 2,327 lines from `MistHelper.py` early.

- **T-04 (`ENDPOINT_PRIMARY_KEY_STRATEGIES`, assignment, 2327 LoC, 2 refs)**: Land at `src/refactors/endpoint__primary__key__strategies.py` OR domain-fit under `src/api/*.py` (per E-1; the dict is intimately tied to the primary-key strategy layer that the constitution's "Adding New Menu Operations" section already codifies). PR description records E-1 rationale. **Substantial internal decomposition required per E-10**: 2,327 lines of dict entries stay as data but any embedded lambdas / callables must be split into `@staticmethod` methods <= 25 lines. Remediate `oversize_25_lines`, `missing_inline_comments`, `missing_action_logging`, and `non_ascii_logs` flags in-flight. **Dispatch this task early (position 4 in the queue) to reclaim the LoC.**
- **T-05 (`detect_msp_privileges`, function, 25 LoC, 2 refs)**: Land at `src/refactors/detect_msp_privileges.py` OR `src/msp/*.py` (new package, per E-1). Remediate `missing_action_logging` in-flight.

**Bucket C — Hot (T-06 through T-15) — >= 4 refs, >= 1 `src/` caller each**

Purpose: complete the initiative. Ordered descending by LOC (per FR-026): T-06 -> T-07 -> T-08 -> T-10 -> T-11 -> T-09 -> T-12 -> T-13 -> T-14 -> T-15.

Every candidate here follows **Pattern 1 constructor injection** if it has runtime deps (`apisession`, `logger`, config accessors, etc.). Applies to: T-06, T-07, T-08, T-09, T-10, T-11, T-12, T-13. Applies partially to T-14 (`tqdm` wrapper — trivial deps, likely stays a bare function). T-15 is a pure module-level constant (E-14).

- **T-06 (`OrgInventoryExporter`, class, 686 LoC, 102 refs)**: Land at `src/export/org_inventory_exporter.py`. Pattern 1 constructor. Method decomposition mandatory (`oversize_25_lines`) — 686 -> N methods each <= 25 lines. Remediate `missing_inline_comments` in-flight. 102 callsites rewritten to `from src.export.org_inventory_exporter import OrgInventoryExporter` + inline instantiation with kwargs.
- **T-07 (`PromptUtils`, class, 441 LoC, 96 refs)**: Land at `src/ui/prompt_utils.py`. **E-1 collision check at dispatch**: `src/device/prompt_utils.py` already exists at ~52 KB — verify whether that file is a related-but-distinct symbol or a stale forward. If collision, either co-locate in `src/device/prompt_utils.py` (fold-in) or leave `src/device/` untouched and land at `src/ui/prompt_utils.py`. Decision recorded in PR description. Pattern 1 constructor. Decompose per `oversize_25_lines`.
- **T-08 (`DataExporter`, class, 345 LoC, 118 refs)**: Land at `src/export/data_exporter.py`. Pattern 1 constructor. Remediate `oversize_25_lines` + `non_ascii_logs` in-flight (constitution V). 118 callsites — the second-highest refs count.
- **T-10 (`DataProcessingUtils`, class, 158 LoC, 69 refs)**: Land at `src/data/data_processing_utils.py` (create `src/data/` if not present). Pattern 1 constructor. Remediate `oversize_25_lines`, `missing_inline_comments`, `hardcoded_separator` (use `os.sep` / `pathlib.Path` per constitution technology-constraint).
- **T-11 (`VirtualChassisManager`, class, 78 LoC, 104 refs)**: Fold into existing `src/device/virtual_chassis.py` (E-1: existing 53 KB module is the natural home). Pattern 1 constructor. Remediate `oversize_25_lines`, `missing_inline_comments`, `missing_action_logging` in-flight. Fold must not regress `src/device/virtual_chassis.py` below A+/100 (FR-022).
- **T-09 (`InputUtils`, class, 74 LoC, 195 refs)**: Land at `src/ui/input_utils.py`. **E-1 collision check at dispatch**: `src/utils/input_utils.py` already exists at ~4.6 KB — determine whether to fold, replace, or override the landing to `src/ui/input_utils.py`. **195 refs across 17 files — the highest-refs candidate in the initiative.** Pre-dispatch `grep -rn "InputUtils" src/ tests/` recorded in PR description (FR-013 / FR-027). Pattern 1 constructor. Remediate `oversize_25_lines` + `raw_input_call` (in-flight rewrite to `safe_input()` per constitution III).
- **T-12 (`ConfigUtils`, class, 70 LoC, 102 refs)**: Land at `src/config/config_utils.py` (create `src/config/` if not present). Pattern 1 constructor. Remediate `oversize_25_lines`.
- **T-13 (`FilePathUtils`, class, 46 LoC, 50 refs)**: Land at `src/utils/file_path_utils.py`. Pattern 1 constructor (or `@staticmethod` collection if no runtime deps — verify at dispatch). Remediate `oversize_25_lines` + `missing_inline_comments`.
- **T-14 (`tqdm`, function, 3 LoC, 51 refs)**: Land at `src/utils/tqdm_wrapper.py` OR domain-fit under `src/ui/*.py` (E-1). E-12 clarification: NOT `SKIP_ALWAYS` here; the 1012 skip-pin was per-initiative. Remediate `missing_action_logging` in-flight. This is a 3-line wrapper — expect a Pattern-1-style constructor is NOT required (trivial deps).
- **T-15 (`MIST_SITE_EXCLUDE_PREFIX`, assignment, 3 LoC, 11 refs)**: Bare module-level constant at `src/refactors/mist_site_exclude_prefix.py` OR fold into an existing constants module in `src/gateway/*.py` (E-1 / E-14). Remediate `missing_inline_comments` + `missing_action_logging` in-flight.

## Dependency Graph Between Tasks

Most of the 15 tasks are **independent** — different symbols in different regions of `MistHelper.py`, different callsite sets. A few overlapping-callsite risks warrant coordination but no serial gating beyond FR-023 (one open PR at a time):

**Overlap risks noted (not blockers — mitigated by FR-023 and dispatch-time grep audit)**:

- **T-07 (PromptUtils) <-> T-11 (VirtualChassisManager)**: `src/device/virtual_chassis.py` (T-11 landing) and `src/device/prompt_utils.py` (T-07 potential collision landing) are in the same directory. If T-07 folds into `src/device/prompt_utils.py`, both PRs touch `src/device/`. Serial merges (per FR-023) plus fresh grep at each dispatch avoid conflict.
- **T-09 (InputUtils, 195 refs, 17 files) <-> every other Hot task**: `InputUtils.safe_input()` is called from many Hot-bucket classes' method bodies. If T-09 lands BEFORE another Hot class, that class's extraction PR must use the new `from src.ui.input_utils import InputUtils` path. If T-09 lands AFTER, the callsite table for T-09 must include the freshly-landed Hot class's file. Either order works; the dispatch-time grep audit ensures both directions are covered. **Recommendation**: dispatch T-09 late in the Hot bucket (position 11 of 15) — as spec's Dispatch Queue already sequences — so Hot classes T-06/T-07/T-08/T-10/T-11 that precede it can bundle their `InputUtils` uses into their own atomic rewires.
- **T-08 (DataExporter, 118 refs) <-> T-06 (OrgInventoryExporter, 102 refs)**: `OrgInventoryExporter` likely calls `DataExporter.write_with_format_selection()` (constitution's canonical export pattern). Whichever lands first passes the freshly-landed class to the second via Pattern 1 kwargs (`DataExporter` kwarg to `OrgInventoryExporter.__init__`, per the 14 typical DI kwargs).
- **T-04 (ENDPOINT_PRIMARY_KEY_STRATEGIES) <-> T-08 (DataExporter)**: Constitution's "Adding New Menu Operations" flow makes T-04 an input to `DataExporter`. If T-08 lands first, T-08's `__init__` needs an import of the still-in-MistHelper.py `ENDPOINT_PRIMARY_KEY_STRATEGIES` — routed via constructor injection (`primary_key_strategies=ENDPOINT_PRIMARY_KEY_STRATEGIES` kwarg). If T-04 lands first, T-08 imports from the new landing module directly. Dispatch T-04 EARLY (position 4) — the spec already sequences it there — to eliminate this coupling before Hot bucket starts.
- **T-15 (MIST_SITE_EXCLUDE_PREFIX)**: Referenced from `src/gateway/*.py` and MistHelper.py. Independent of every other task.

**Fully independent** (no shared callsite files at spec time): T-01, T-02, T-03, T-05, T-13, T-14.

**Sequencing rationale (matches spec's Dispatch Queue exactly)**:

1. T-01 -> T-02 -> T-03: warm up (1 callsite each, minimum risk).
2. T-04 early (position 4): reclaim 2,327 LoC and remove the T-04 <-> T-08 coupling before Hot bucket.
3. T-05: exercises new-package creation (`src/msp/`) at low risk.
4. Hot descending-by-LOC: T-06, T-07, T-08, T-10, T-11, T-09, T-12, T-13, T-14, T-15.

## Workflow Per Task (identical structure — /speckit.tasks will emit one task row per Dispatch Queue entry)

For **each** of T-01 through T-15:

1. **Branch**: `git checkout -b refactor/1015-tNN-<slug>` off latest `main`.
2. **Pre-dispatch audit**: `grep -rn "<Name>" src/ tests/ MistHelper.py` -> record file:line callsite table in PR description (FR-013 / FR-027).
3. **Implement**:
   - Create (or select) landing module per spec's Dispatch Queue + E-1 override rationale.
   - Move body verbatim; then remediate `guideline_flags` in-flight (FR-006 / FR-008).
   - For hot classes with runtime deps: apply **Pattern 1 constructor injection** (`__init__(self, **deps)` — required kwargs, spelled out at every callsite; NO factory, NO cached instance, NO `sys.modules` self-resolution, NO shim, NO facade).
   - Delete original body from `MistHelper.py`.
   - Add mandatory single-line NOTE breadcrumb at deletion site: `# NOTE: <Name> extracted to <new-module-path>::<Name>. See specs/1015-misthelper-refactor-final-15/spec.md.` (FR-007 / SC-012).
   - Rewrite every `MistHelper.py` callsite in same commit.
   - Rewrite every `src/` / `tests/` callsite in same commit — including elimination of every `mh = importlib.import_module("MistHelper")` + `mh.<Name>` lazy-import for this symbol (SC-009).
   - Convert existing tests to new import path + Pattern 1 construction contract (FR-030).
4. **Import-graph health check** (FR-028 / SC-018): `python -c "import <landing_module>; print('OK')"` must succeed without traversing `MistHelper.py`. If genuine cycle remains, inject Pattern 1 DI surface at the cycle boundary. NO `mh.<name>` lazy import in the new module.
5. **Pre-push local gate** (`feedback_prepush_black_ruff.md`):
   ```
   black src/ MistHelper.py tools/
   ruff check src/ MistHelper.py tools/
   python MistHelper.py --test    # expect 0 failed, exit 0 (E-7 flake exempt)
   ```
6. **Commit**: `refactor(1015): <what> (T-NN, Cat E)`.
7. **Push + open PR** against `main` (via `git push` + web URL if EMU blocks `gh pr create` per spec Assumptions).
8. **Wait for CI**: all 15 functional jobs green + `mergeStateStatus: CLEAN` + `black --check` clean + `ruff check` clean.
9. **Merge**: `gh pr merge --squash --delete-branch` — **never `--admin`** as routine unblock (`feedback_no_admin_bypass.md`). SKIPPED conditionals are NOT blocking (E-9).
10. **Post-merge**:
    - `git checkout main && git pull`.
    - Regenerate: `python -m tools.refactor_analyzer` -> writes fresh `refactor_candidates.md`.
    - Commit as `chore(1015): regenerate refactor_candidates.md after T-NN merge` on `main` (may piggyback in the next task's branch or land as a standalone commit per prior initiative practice).
    - Verify T-NN symbol is absent from every bucket in the fresh catalog.
11. **Advance**: next task in bucket-first order.

## Quality Gates (aggregate across the initiative)

| Gate | Enforcement | Traceability |
|---|---|---|
| 15 functional CI jobs green | Per PR | FR-015 / SC-005 |
| `mergeStateStatus: CLEAN` | Per PR | FR-015 / `feedback_no_admin_bypass.md` |
| `black --check` clean | Per PR (pre-push + CI) | FR-015 / SC-005 / SC-013 / `feedback_prepush_black_ruff.md` |
| `ruff check` clean | Per PR (pre-push + CI) | FR-015 / SC-005 / SC-013 / `feedback_prepush_black_ruff.md` |
| `python MistHelper.py --test` = 0 failed / exit 0 | Per PR | FR-015 / SC-005 / SC-013 (E-7 flake exempt) |
| Repo aggregate compliance >= 99.6/A+ | Per PR | SC-003 / FR-017 |
| Every new module A+/100 | Per PR | SC-006 / FR-016 |
| No A+ file regresses below A+ | Per PR | SC-004 / FR-022 |
| `MistHelper.py` pylint non-regressing | Per PR | SC-015 / FR-018 |
| Zero new mypy strict violations | Per PR | SC-019 / FR-031 |
| Zero new SKIPPED CI conditionals | Per PR | SC-016 / FR-019 |
| Zero `mh.<Name>` remainders for extracted symbol | Per PR (post-merge grep) | SC-009 |
| Zero wrapper shim / facade / delegator in `MistHelper.py` | Per PR + final | SC-007 |
| Exactly one NOTE breadcrumb per deletion site | Per PR | SC-012 / FR-007 |
| Callsite table in PR description | Per PR | SC-017 / FR-027 |
| Analyzer regenerated after every merge | Per merged PR | SC-010 / FR-014 |
| One open PR at a time | Sequenced dispatch | FR-023 |
| Every analyzer `guideline_flag` on extracted symbol resolved in-flight | Per PR | SC-011 / FR-006 |
| No `menu_actions` diff | Per PR + final | SC-020 / FR-010 |
| No `GlobalImportManager` diff | Per PR + final | SC-021 / FR-009 |
| MistHelper.py LoC -3,500 by initiative close | Cumulative | SC-002 |
| Final catalog shows only `menu_actions` + `GlobalImportManager` | Final | SC-001 / FR-024 / FR-032 |
| Final-state summary in last PR or follow-up docs commit | Final | SC-022 |

## Rollback Strategy

**Per-PR rollback (rare — expected only on merged regression)**:

1. Identify the merged PR causing the regression (`gh pr list --state merged --search "1015"` + `git bisect` if needed).
2. Open a revert PR: `gh pr create --title "revert(1015): revert T-NN <slug>" --body "Reverts #<PR>. Root cause: <one-line>."` — do NOT rebase or force-push.
3. Merge the revert PR with the same quality gates (all 15 green, `mergeStateStatus: CLEAN`, `black --check` + `ruff check` clean, `python MistHelper.py --test` clean).
4. Re-run `python -m tools.refactor_analyzer` — the reverted symbol reappears in the catalog.
5. File a follow-up issue capturing the root cause; the reverted candidate stays in this initiative's Dispatch Queue and is re-attempted with the root cause fixed.
6. The initiative's SC-001 / SC-002 targets are re-evaluated only at final closure — a temporary revert does not close the initiative.

**Mid-PR rollback (branch-local, no merge)**:

- `git reset --hard origin/main` on the refactor branch.
- Re-run pre-push gate before re-pushing.
- No cross-branch impact.

**Never**:

- Force-push to `main`.
- Amend a merged commit.
- Use `--admin` merge bypass to paper over a failing CI job (`feedback_no_admin_bypass.md`).
- Leave a `mh.<Name>` lazy-import in place as a "temporary" backward-compat bridge (SC-009 — zero remainders permitted).
- Introduce a wrapper shim / delegator / facade / re-export module as a rollback lever (SC-007 — zero remainders permitted).

**Full-initiative rollback (worst case, expected never)**:

If the aggregate compliance floor (SC-003) drifts below 99.6/A+ due to a compounding sequence of extractions:

1. Pause new dispatches.
2. Diagnose which merged PR(s) contributed to the drift (per-file compliance-score diff against pre-initiative baseline).
3. Revert the offending PR(s) via standard revert-PR flow.
4. Resume dispatch from the queue position immediately after the last clean PR.

The initiative is stateless across dispatches: every PR is independently revertable and no PR blocks any other PR's revert.

## Phase 0: Outline & Research

**Decision: Skip standalone research.md.**

Rationale: 1015 is the direct successor to 1010/1011/1012/1013/1014, all of which have merged, closed, and shipped. Every unknown that could apply to 1015 has been resolved by predecessor initiatives:

| Prior unknown | Resolved by |
|---|---|
| Cat E cross-package extraction workflow | 1014 (18 Cat E PRs merged) |
| Cat A facade removal workflow | 1013 + 1014 (10 Cat A PRs merged) |
| Pattern 1 constructor injection | 1013 (established) + 1014 (applied 18x) |
| `mh = importlib.import_module("MistHelper")` elimination | 1014 (pattern retired for every extracted symbol) |
| Serial-PR dispatch with `--squash` merges | 1010/1011/1012/1013/1014 (56+ merged PRs) |
| Analyzer regeneration cadence | 1010-1014 (established `chore(NNNN): regenerate ...` convention) |
| `python MistHelper.py --test` flake `test_menu_196_dispatches_to_async_claim_exporter` | 1014 (E-7 exemption established) |
| Pre-push `black --check` + `ruff check` gate | `feedback_prepush_black_ruff.md` (user memory) |
| `--admin` merge bypass prohibition | `feedback_no_admin_bypass.md` (user memory) |

The 14 typical DI kwargs enumerated in the user directive are the exact set observed in merged 1013/1014 PRs. No further research is required to dispatch T-01.

**Output**: (implicit — this plan.md encodes every decision that a research.md would have surfaced)

## Phase 1: Design & Contracts

**Decision: Skip data-model.md, contracts/, quickstart.md.**

Rationale:

- **data-model.md**: 1015 introduces no new entities. Every extracted symbol preserves its runtime behavior byte-for-byte modulo `guideline_flags` remediation. The spec's "Key Entities" section already captures the workflow-level entities (Extraction Candidate, Callsite, Callsite Table, Dispatch Queue, Reclassification, Pattern 1). No further data modelling is required.
- **contracts/**: 1015 exposes no new public interfaces. `FR-021` explicitly prohibits new features, new commands, new CLI flags, or user-facing behavior changes. Every Pattern 1 `__init__(self, **deps)` signature is an internal construction contract, not a public API contract — enumerated in the spec's Key Entities under "Pattern 1 (Constructor Injection)".
- **quickstart.md**: The Workflow-Per-Task section above IS the quickstart. Duplicating it into a separate file adds no signal.

**Agent context update**: The plan reference between the `<!-- SPECKIT START -->` and `<!-- SPECKIT END -->` markers in `.github/copilot-instructions.md` will be updated to point to this plan file on request. Not performed automatically as part of this /speckit.plan run — flagged for the caller.

**Output**: (this plan.md is the complete Phase 1 artifact for a pure-refactor initiative with no new entities, no new interfaces, and no new user-facing behavior)

## Complexity Tracking

*Empty — no Constitution Check violations.*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
