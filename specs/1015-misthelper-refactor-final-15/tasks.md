# Tasks: MistHelper Refactor — Final 15 (All Remaining Analyzer Candidates)

**Feature Branch**: `1015-misthelper-refactor-final-15`
**Spec**: [`spec.md`](./spec.md)
**Plan**: [`plan.md`](./plan.md)
**Catalog snapshot**: `refactor_candidates.md` regenerated 2026-07-09 against `origin/main` at commit `8523596`.

## Overview

Fifteen atomic **Cat E fresh cross-package extraction** PRs — one candidate per PR — clearing every remaining actionable entry from the analyzer catalog (excluding `menu_actions` and `GlobalImportManager` per FR-010 / FR-009). Dispatch order mirrors the Dispatch Queue in the spec (bucket-first: Single-use → Low-use → Hot descending-by-LOC).

**Bucket distribution**: 3 Single-use, 2 Low-use, 10 Hot. **Category distribution**: 15 Cat E, 0 Cat A, 0 Cat B.

**Task-ID scheme**: `T-01` through `T-15` are the semantic task IDs pinned by the spec's Dispatch Queue. The dispatch *position* (1..15) differs from the task ID number for T-09/T-10/T-11 within the Hot bucket where descending-LOC ordering rearranges the semantic IDs. Position column below is the canonical execution order.

**Pattern 1 (Constructor Injection)** is the ONLY landing pattern for hot classes with runtime deps. Every extracted class exposes `__init__(self, **deps)` with required kwargs spelled out at every callsite. NO factory helpers, NO cached module-level instance, NO `sys.modules` self-resolution, NO delegators / shims / pointers / facades. Module-level constants (T-02, T-03, T-15) land as bare assignments.

## Common Per-Task Acceptance Criteria

Every task (T-01..T-15) MUST satisfy the following gates before merge — enforced per PR:

- [ ] Landing module created (or fold-in target selected per E-1) and body moved verbatim, then `guideline_flags` remediated in-flight (FR-006 / FR-008).
- [ ] Zero wrapper shim / forwarding function / re-export module / delegator / pointer / helper / backward-compat alias survives in `MistHelper.py` (SC-007 / FR-003).
- [ ] Single-line NOTE breadcrumb left at deletion site matching template `# NOTE: <Name> extracted to <new-module-path>::<Name>. See specs/1015-misthelper-refactor-final-15/spec.md.` (FR-007 / SC-012).
- [ ] Every `MistHelper.py` callsite rewritten in same commit (FR-005).
- [ ] Every `src/` and `tests/` callsite rewritten in same commit; zero `mh = importlib.import_module("MistHelper")` + `mh.<Name>` remainders for extracted symbol (SC-009).
- [ ] Callsite table recorded in PR description (MistHelper.py count + `src/` file:line list + `tests/` file:line list) per FR-027 / SC-017.
- [ ] Pre-push local gate passes on refactor branch:
  - [ ] `black --check src/ MistHelper.py tools/` clean.
  - [ ] `ruff check src/ MistHelper.py tools/` clean.
  - [ ] `python MistHelper.py --test` reports 0 failed / exit 0 (modulo `test_menu_196_dispatches_to_async_claim_exporter` flake per E-7).
- [ ] Import-graph health verified: `python -c "import <landing_module>; print('OK')"` succeeds without traversing `MistHelper.py` (FR-028 / SC-018).
- [ ] Post-merge callsite count matches the pre-dispatch grep audit (zero stale references — verifiable via `grep -rn "<Name>" .` against merged `main`).
- [ ] 15 functional CI jobs green + `mergeStateStatus: CLEAN` (FR-015 / SC-005). Merge is squash + delete-branch; NO `--admin` bypass as routine unblock (`feedback_no_admin_bypass.md`).
- [ ] Repo aggregate compliance ≥ 99.6/A+ post-merge; new module scores A+/100; no A+ file regresses (SC-003 / SC-004 / SC-006 / FR-016 / FR-017 / FR-022).
- [ ] `MistHelper.py` pylint score non-regressing (SC-015 / FR-018).
- [ ] Zero new mypy strict violations, zero new SKIPPED CI conditionals (SC-019 / SC-016 / FR-031 / FR-019).
- [ ] Existing tests converted to new import path + Pattern 1 construction contract in same commit (FR-030 / SC-023).
- [ ] Analyzer regenerated post-merge (`python -m tools.refactor_analyzer`) and committed as `chore(1015): regenerate refactor_candidates.md after T-NN merge` (may piggyback on next task's branch per prior initiative practice) — FR-014 / SC-010.

---

## Bucket A — Single-use (T-01, T-02, T-03) — 1 caller each, queue-head validation

### T-01: Extract `DeviceFetchConfig` to `src/refactors/device_data_fetcher.py`

- **Dispatch position**: 1 of 15
- **Symbol**: `DeviceFetchConfig`
- **Symbol type**: class (small dataclass, 9 LOC)
- **Refactor category**: Cat E (fresh cross-package extraction) — Single-use bucket
- **LOC reclaimed from MistHelper.py**: 9
- **Callsite count**: 1 ref (`src/refactors/device_data_fetcher.py:49`)
- **Landing module**: `src/refactors/device_data_fetcher.py` — fold as top-level `@dataclass` (E-1 override: fold into `DeviceDataFetcherManager` class body ONLY if the class's public surface benefits from a nested config)
- **Branch**: `refactor/1015-t01-device-fetch-config`
- **Commit message template**: `refactor(1015): extract DeviceFetchConfig to src/refactors/device_data_fetcher.py (T-01, Cat E)`
- **Analyzer flags to resolve in-flight**: `missing_action_logging`
- **Dependencies**: none — fully independent.
- **Task-specific acceptance criteria** (in addition to Common gates above):
  - [ ] Sole callsite at `src/refactors/device_data_fetcher.py:49` rewritten to reference the new dataclass at its new home.
  - [ ] `missing_action_logging` flag resolved via `logging.info` / `logging.debug` envelopes on any consuming method touched by the move.
  - [ ] NOTE breadcrumb left in `MistHelper.py` at prior `DeviceFetchConfig` deletion site.
  - [ ] No delegator / shim / re-export left in `MistHelper.py`.

---

### T-02: Extract `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` to `src/refactors/fast__mode__max__concurrent__connections.py`

- **Dispatch position**: 2 of 15
- **Symbol**: `FAST_MODE_MAX_CONCURRENT_CONNECTIONS`
- **Symbol type**: constant (module-level assignment, 3 LOC)
- **Refactor category**: Cat E — Single-use bucket
- **LOC reclaimed from MistHelper.py**: 3
- **Callsite count**: 1 ref
- **Landing module**: `src/refactors/fast__mode__max__concurrent__connections.py` (bare module-level constant per E-14; MAY fold into an existing fast-mode constants module if one exists in the destination package — E-1 override recorded in PR description). Analyzer's `Suggested class` `FastModeMaxConcurrentConnectionsManager` is a naming hint only — NOT a required class wrapper.
- **Branch**: `refactor/1015-t02-fast-mode-max-concurrent-connections`
- **Commit message template**: `refactor(1015): extract FAST_MODE_MAX_CONCURRENT_CONNECTIONS to src/refactors/fast__mode__max__concurrent__connections.py (T-02, Cat E)`
- **Analyzer flags to resolve in-flight**: `missing_inline_comments`, `missing_action_logging`
- **Dependencies**: none — fully independent. MAY co-locate with T-03 in same destination file if fold-in target exists.
- **Task-specific acceptance criteria**:
  - [ ] Landing is a bare module-level constant (E-14) — NO wrapper class.
  - [ ] `missing_inline_comments` resolved via inline comments on the constant declaration line and any documentation context.
  - [ ] `missing_action_logging` resolved on the read-side (any consumer method touched by the callsite rewrite gets `logging.info` / `logging.debug` envelopes).
  - [ ] NOTE breadcrumb at prior definition site.

---

### T-03: Extract `FAST_MODE_USE_CONNECTION_AWARE_THREADING` to `src/refactors/fast__mode__use__connection__aware__threading.py`

- **Dispatch position**: 3 of 15
- **Symbol**: `FAST_MODE_USE_CONNECTION_AWARE_THREADING`
- **Symbol type**: constant (module-level assignment, 3 LOC)
- **Refactor category**: Cat E — Single-use bucket
- **LOC reclaimed from MistHelper.py**: 3
- **Callsite count**: 1 ref
- **Landing module**: `src/refactors/fast__mode__use__connection__aware__threading.py` (bare module-level constant per E-14; MAY co-locate with T-02 in a shared fast-mode constants module — E-1 override recorded).
- **Branch**: `refactor/1015-t03-fast-mode-use-connection-aware-threading`
- **Commit message template**: `refactor(1015): extract FAST_MODE_USE_CONNECTION_AWARE_THREADING to src/refactors/fast__mode__use__connection__aware__threading.py (T-03, Cat E)`
- **Analyzer flags to resolve in-flight**: `missing_action_logging`
- **Dependencies**: none — fully independent. Consider co-locating with T-02 if a fast-mode constants module is chosen.
- **Task-specific acceptance criteria**:
  - [ ] Landing is a bare module-level constant (E-14).
  - [ ] `missing_action_logging` resolved on the read-side of consumers touched by the rewrite.
  - [ ] NOTE breadcrumb at prior definition site.

---

## Bucket B — Low-use (T-04, T-05) — 2 callers each

### T-04: Extract `ENDPOINT_PRIMARY_KEY_STRATEGIES` to `src/refactors/endpoint__primary__key__strategies.py`

- **Dispatch position**: 4 of 15 — **largest LOC win in the entire initiative; dispatch early to reclaim 2,327 lines and eliminate T-04↔T-08 coupling before Hot bucket starts** (per plan.md dependency graph).
- **Symbol**: `ENDPOINT_PRIMARY_KEY_STRATEGIES`
- **Symbol type**: constant (module-level assignment / dict, 2327 LOC — the initiative's largest LoC line-item)
- **Refactor category**: Cat E — Low-use bucket
- **LOC reclaimed from MistHelper.py**: 2327
- **Callsite count**: 2 refs
- **Landing module**: `src/refactors/endpoint__primary__key__strategies.py` OR a domain-fitting `src/api/*.py` submodule (per E-1; the dict is intimately tied to the primary-key strategy layer in the constitution's "Adding New Menu Operations" flow — PR description records the E-1 override rationale in one sentence).
- **Branch**: `refactor/1015-t04-endpoint-primary-key-strategies`
- **Commit message template**: `refactor(1015): extract ENDPOINT_PRIMARY_KEY_STRATEGIES to <landing-path> (T-04, Cat E)`
- **Analyzer flags to resolve in-flight**: `oversize_25_lines`, `missing_inline_comments`, `missing_action_logging`, `non_ascii_logs`
- **Dependencies**: **T-04 → T-08 ordering coupling**. If T-04 lands first (spec's chosen order), T-08 can `from src.refactors.endpoint__primary__key__strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES` directly. If T-08 dispatches first, T-08's `__init__` must accept a `primary_key_strategies` kwarg pointing at the still-in-MistHelper.py symbol — added coupling to avoid. **Spec sequences T-04 at position 4 specifically to eliminate this coupling before Hot bucket begins.**
- **Task-specific acceptance criteria**:
  - [ ] Atomic single-PR move (no split across multiple PRs per E-10).
  - [ ] `oversize_25_lines` remediated via method decomposition — the 2,327-line dict body stays as data, but any embedded lambdas / callables split into `@staticmethod` methods ≤ 25 lines (per E-10 / FR-006).
  - [ ] `missing_inline_comments` remediated — inline comment on every executable line in the new module.
  - [ ] `missing_action_logging` remediated on any accessor / helper methods surfaced during decomposition.
  - [ ] `non_ascii_logs` remediated — all log literals ASCII-only.
  - [ ] Both 2 MistHelper.py callsites rewritten in same commit.
  - [ ] NOTE breadcrumb at prior definition site.
  - [ ] LoC reduction of ≥ 2,327 lines confirmed against `MistHelper.py` diff.

---

### T-05: Extract `detect_msp_privileges` to `src/refactors/detect_msp_privileges.py`

- **Dispatch position**: 5 of 15
- **Symbol**: `detect_msp_privileges`
- **Symbol type**: function (25 LOC)
- **Refactor category**: Cat E — Low-use bucket
- **LOC reclaimed from MistHelper.py**: 25
- **Callsite count**: 2 refs
- **Landing module**: `src/refactors/detect_msp_privileges.py` OR a new domain-fitting `src/msp/*.py` package (per E-1; creating a new `src/msp/` package is acceptable if the analyzer-suggested fallback is a poor semantic fit — rationale recorded in PR description).
- **Branch**: `refactor/1015-t05-detect-msp-privileges`
- **Commit message template**: `refactor(1015): extract detect_msp_privileges to <landing-path> (T-05, Cat E)`
- **Analyzer flags to resolve in-flight**: `missing_action_logging`
- **Dependencies**: none — fully independent. Exercises new-package creation (`src/msp/`) at low risk if that landing is chosen.
- **Task-specific acceptance criteria**:
  - [ ] Function landing at top-level of new module (or `src/msp/*.py` if new package created).
  - [ ] Method body kept ≤ 25 lines (already ≤ 25 per catalog; verify post-move).
  - [ ] `missing_action_logging` resolved via `logging.info` / `logging.debug` envelopes.
  - [ ] Both 2 callsites rewritten in same commit.
  - [ ] NOTE breadcrumb at prior definition site.

---

## Bucket C — Hot (10 tasks, descending by LOC) — 11 to 195 refs each, ≥ 1 `src/` caller each

### T-06: Extract `OrgInventoryExporter` to `src/export/org_inventory_exporter.py`

- **Dispatch position**: 6 of 15 — **highest-LOC Hot candidate, dispatched first in Hot bucket per FR-026 descending-by-LOC ordering.**
- **Symbol**: `OrgInventoryExporter`
- **Symbol type**: class (Pattern 1 Hot — runtime deps, `apisession` + peers)
- **Refactor category**: Cat E — Hot bucket
- **LOC reclaimed from MistHelper.py**: 686
- **Callsite count**: 102 refs (MistHelper.py + `src/` combined)
- **Landing module**: `src/export/org_inventory_exporter.py`
- **Branch**: `refactor/1015-t06-org-inventory-exporter`
- **Commit message template**: `refactor(1015): extract OrgInventoryExporter to src/export/org_inventory_exporter.py (T-06, Cat E)`
- **Analyzer flags to resolve in-flight**: `oversize_25_lines`, `missing_inline_comments`
- **Dependencies**: **Coupling with T-08 (DataExporter)** — `OrgInventoryExporter` likely calls `DataExporter.write_with_format_selection()`. Whichever of T-06 / T-08 lands second constructs the first via Pattern 1 kwargs (`data_exporter=DataExporter(**data_exporter_kwargs)` at every `OrgInventoryExporter` callsite). Spec dispatches T-06 first (position 6) then T-08 (position 8) — T-08 will see the freshly-landed `OrgInventoryExporter` via `from src.export.org_inventory_exporter import OrgInventoryExporter`.
- **Task-specific acceptance criteria**:
  - [ ] Pattern 1 constructor injection: `__init__(self, **deps)` with required kwargs (subset of the 14 canonical DI kwargs — apisession, PromptUtils, ConfigUtils, DataProcessingUtils, DataExporter, TimeUtils, EnhancedSSHRunner, InsightMetricsUtils, PacketCaptureManager, APICoreFetchUtils, check_fn=IsDebugMode.check, PrettyTable, tqdm, mistapi).
  - [ ] Every one of 102 callsites constructs the instance inline with the full kwargs list spelled out — NO factory, NO cached instance, NO `sys.modules` self-resolution.
  - [ ] `oversize_25_lines` remediated via method decomposition: 686 LoC split into methods each ≤ 25 lines.
  - [ ] `missing_inline_comments` remediated — inline comment on every executable line in new module.
  - [ ] Every `mh = importlib.import_module("MistHelper")` + `mh.OrgInventoryExporter` lazy-import in `src/` eliminated in same commit (SC-009).
  - [ ] Callsite table in PR description enumerates all 102 file:line refs.
  - [ ] Tests converted to new import path + Pattern 1 kwarg construction (FR-030 / SC-023).

---

### T-07: Extract `PromptUtils` to `src/ui/prompt_utils.py`

- **Dispatch position**: 7 of 15
- **Symbol**: `PromptUtils`
- **Symbol type**: class (Pattern 1 Hot — runtime deps)
- **Refactor category**: Cat E — Hot bucket
- **LOC reclaimed from MistHelper.py**: 441
- **Callsite count**: 96 refs
- **Landing module**: `src/ui/prompt_utils.py` — **E-1 collision check at dispatch**: `src/device/prompt_utils.py` already exists at ~52 KB. Verify whether that file is a related-but-distinct symbol or a stale forward. If collision, EITHER co-locate in `src/device/prompt_utils.py` (fold-in — must NOT regress that file below A+/100 per FR-022) OR leave `src/device/` untouched and land at `src/ui/prompt_utils.py`. E-1 rationale recorded in PR description.
- **Branch**: `refactor/1015-t07-prompt-utils`
- **Commit message template**: `refactor(1015): extract PromptUtils to <landing-path> (T-07, Cat E)`
- **Analyzer flags to resolve in-flight**: `oversize_25_lines`
- **Dependencies**: **T-07 ↔ T-11 overlap in `src/device/`** — if T-07 folds into `src/device/prompt_utils.py`, both T-07 and T-11 (VirtualChassisManager, folding into `src/device/virtual_chassis.py`) touch the same directory. **Not a merge blocker** — FR-023 (one open PR at a time) + dispatch-time grep audit + serial merges resolve any conflict. If T-07 lands at `src/ui/prompt_utils.py` instead, this overlap goes away entirely.
- **Task-specific acceptance criteria**:
  - [ ] E-1 collision-check decision recorded in PR description (co-locate vs. new-module landing).
  - [ ] Pattern 1 constructor injection with required kwargs; every callsite constructs inline.
  - [ ] `oversize_25_lines` remediated via method decomposition — 441 LoC split into methods ≤ 25 lines.
  - [ ] Every `mh.PromptUtils` lazy-import in `src/` eliminated.
  - [ ] 96 callsites enumerated in PR description callsite table.
  - [ ] If fold-in to `src/device/prompt_utils.py`: that file's compliance score remains A+/100 (FR-022).
  - [ ] Tests converted to new import path + Pattern 1 kwarg construction.

---

### T-08: Extract `DataExporter` to `src/export/data_exporter.py`

- **Dispatch position**: 8 of 15
- **Symbol**: `DataExporter`
- **Symbol type**: class (Pattern 1 Hot — runtime deps)
- **Refactor category**: Cat E — Hot bucket
- **LOC reclaimed from MistHelper.py**: 345
- **Callsite count**: 118 refs — **second-highest ref count in the initiative** (after T-09 InputUtils at 195).
- **Landing module**: `src/export/data_exporter.py`
- **Branch**: `refactor/1015-t08-data-exporter`
- **Commit message template**: `refactor(1015): extract DataExporter to src/export/data_exporter.py (T-08, Cat E)`
- **Analyzer flags to resolve in-flight**: `oversize_25_lines`, `non_ascii_logs`
- **Dependencies**:
  - **T-04 → T-08 ordering** (see T-04): T-04 dispatched first at position 4 ensures `ENDPOINT_PRIMARY_KEY_STRATEGIES` is already at its new home when T-08 lands. T-08 imports the constant directly from the new landing module — no coupling to MistHelper.py residual.
  - **T-06 ↔ T-08** (see T-06): T-06 dispatched first at position 6. T-08 injects the already-landed `OrgInventoryExporter` via Pattern 1 kwargs when its methods orchestrate exports.
- **Task-specific acceptance criteria**:
  - [ ] Pattern 1 constructor injection with required kwargs (including `primary_key_strategies` if the strategy dict is passed as a kwarg, OR the module-level `from src.refactors.endpoint__primary__key__strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES` import inside `data_exporter.py`).
  - [ ] `oversize_25_lines` remediated via method decomposition — 345 LoC → methods ≤ 25 lines.
  - [ ] `non_ascii_logs` remediated — every log literal ASCII-only (constitution V).
  - [ ] Every `mh.DataExporter` lazy-import in `src/` eliminated.
  - [ ] 118 callsites enumerated in PR description callsite table.
  - [ ] Tests converted.

---

### T-10: Extract `DataProcessingUtils` to `src/data/data_processing_utils.py`

- **Dispatch position**: 9 of 15
- **Symbol**: `DataProcessingUtils`
- **Symbol type**: class (Pattern 1 Hot — runtime deps)
- **Refactor category**: Cat E — Hot bucket
- **LOC reclaimed from MistHelper.py**: 158
- **Callsite count**: 69 refs
- **Landing module**: `src/data/data_processing_utils.py` — creates `src/data/` package if not already present.
- **Branch**: `refactor/1015-t10-data-processing-utils`
- **Commit message template**: `refactor(1015): extract DataProcessingUtils to src/data/data_processing_utils.py (T-10, Cat E)`
- **Analyzer flags to resolve in-flight**: `oversize_25_lines`, `missing_inline_comments`, `hardcoded_separator`
- **Dependencies**: none direct — fully independent of T-11 despite ordering-adjacency. May be consumed as a Pattern 1 kwarg by other Hot classes (`DataProcessingUtils` is one of the 14 canonical DI kwargs); those consuming classes will pick up the new import path when they extract.
- **Task-specific acceptance criteria**:
  - [ ] `src/data/` package created (with `__init__.py`) if not already present.
  - [ ] Pattern 1 constructor injection with required kwargs.
  - [ ] `oversize_25_lines` remediated via decomposition — 158 LoC → methods ≤ 25 lines.
  - [ ] `missing_inline_comments` remediated.
  - [ ] `hardcoded_separator` remediated — replace hardcoded `/` or `\\` with `os.sep` or `pathlib.Path` idioms (constitution technology-constraint).
  - [ ] Every `mh.DataProcessingUtils` lazy-import in `src/` eliminated.
  - [ ] 69 callsites enumerated in PR description callsite table.
  - [ ] Tests converted.

---

### T-11: Fold `VirtualChassisManager` into `src/device/virtual_chassis.py`

- **Dispatch position**: 10 of 15
- **Symbol**: `VirtualChassisManager`
- **Symbol type**: class (Pattern 1 Hot — runtime deps)
- **Refactor category**: Cat E — Hot bucket (fold-in)
- **LOC reclaimed from MistHelper.py**: 78
- **Callsite count**: 104 refs
- **Landing module**: `src/device/virtual_chassis.py` — **fold into existing module** (existing 53 KB module is the natural home per E-1).
- **Branch**: `refactor/1015-t11-virtual-chassis-manager`
- **Commit message template**: `refactor(1015): fold VirtualChassisManager into src/device/virtual_chassis.py (T-11, Cat E)`
- **Analyzer flags to resolve in-flight**: `oversize_25_lines`, `missing_inline_comments`, `missing_action_logging`
- **Dependencies**: **T-07 ↔ T-11 overlap in `src/device/`** — if T-07 (PromptUtils) also lands in `src/device/`, both PRs touch the same directory. Spec dispatches T-07 at position 7 and T-11 at position 10 — T-07's PR is merged before T-11 opens (FR-023 serial dispatch). Fresh grep at T-11 dispatch time reflects any T-07 landing.
- **Task-specific acceptance criteria**:
  - [ ] Fold-in target `src/device/virtual_chassis.py` retains A+/100 after fold (FR-022) — verify with per-file compliance score check pre/post merge.
  - [ ] Pattern 1 constructor injection with required kwargs.
  - [ ] `oversize_25_lines` remediated — 78 LoC → methods ≤ 25 lines.
  - [ ] `missing_inline_comments` remediated.
  - [ ] `missing_action_logging` remediated on every method.
  - [ ] Every `mh.VirtualChassisManager` lazy-import in `src/` eliminated.
  - [ ] 104 callsites enumerated in PR description callsite table.
  - [ ] Tests converted.

---

### T-09: Extract `InputUtils` to `src/ui/input_utils.py`

- **Dispatch position**: 11 of 15 — **highest-refs candidate in the initiative (195 refs across 17 files); dispatched late in Hot bucket per plan.md so that preceding Hot classes (T-06/T-07/T-08/T-10/T-11) bundle their `InputUtils` uses into their own atomic rewires** rather than requiring a T-09-late catch-up.
- **Symbol**: `InputUtils`
- **Symbol type**: class (Pattern 1 Hot — runtime deps; safety-first NON-NEGOTIABLE per constitution III)
- **Refactor category**: Cat E — Hot bucket
- **LOC reclaimed from MistHelper.py**: 74
- **Callsite count**: 195 refs across 17 files — **highest ref count in the initiative.**
- **Landing module**: `src/ui/input_utils.py` — **E-1 collision check at dispatch**: `src/utils/input_utils.py` already exists at ~4.6 KB. Determine whether to fold, replace, or override landing to `src/ui/input_utils.py`. E-1 rationale recorded in PR description.
- **Branch**: `refactor/1015-t09-input-utils`
- **Commit message template**: `refactor(1015): extract InputUtils to <landing-path> (T-09, Cat E)`
- **Analyzer flags to resolve in-flight**: `oversize_25_lines`, `raw_input_call`
- **Dependencies**: **T-09 broadly touches Hot-bucket predecessor callsites**. Every Hot class that lands before T-09 (T-06, T-07, T-08, T-10, T-11) SHOULD rewire its own `InputUtils.safe_input()` uses to the eventual `from src.ui.input_utils import InputUtils` path in-flight — reducing T-09's callsite fanout at dispatch. Either order works; the dispatch-time grep audit at T-09 must include every freshly-landed Hot class.
- **Task-specific acceptance criteria**:
  - [ ] E-1 collision-check decision recorded in PR description (fold vs. new-landing).
  - [ ] Pre-dispatch `grep -rn "InputUtils" src/ tests/ MistHelper.py` recorded verbatim in PR description (FR-013 / FR-027) — expect ~195 hits.
  - [ ] Pattern 1 constructor injection with required kwargs.
  - [ ] `oversize_25_lines` remediated — 74 LoC → methods ≤ 25 lines.
  - [ ] `raw_input_call` remediated — every raw `input()` in the extracted body rewritten to `InputUtils.safe_input()` per constitution III (safety-first NON-NEGOTIABLE).
  - [ ] Every `mh.InputUtils` lazy-import in `src/` eliminated.
  - [ ] All 195 callsites across 17 files enumerated in PR description callsite table.
  - [ ] Tests converted to new import path + Pattern 1 kwarg construction (SC-023 — verify `grep -rn "InputUtils" tests/` shows zero old-path matches post-merge).

---

### T-12: Extract `ConfigUtils` to `src/config/config_utils.py`

- **Dispatch position**: 12 of 15
- **Symbol**: `ConfigUtils`
- **Symbol type**: class (Pattern 1 Hot — runtime deps)
- **Refactor category**: Cat E — Hot bucket
- **LOC reclaimed from MistHelper.py**: 70
- **Callsite count**: 102 refs
- **Landing module**: `src/config/config_utils.py` — creates `src/config/` package if not already present.
- **Branch**: `refactor/1015-t12-config-utils`
- **Commit message template**: `refactor(1015): extract ConfigUtils to src/config/config_utils.py (T-12, Cat E)`
- **Analyzer flags to resolve in-flight**: `oversize_25_lines`
- **Dependencies**: none direct — fully independent. May be consumed as a Pattern 1 kwarg by other Hot classes (`ConfigUtils` is one of the 14 canonical DI kwargs); consumers that already extracted before T-12 will need to be updated to the new import path in T-12's commit.
- **Task-specific acceptance criteria**:
  - [ ] `src/config/` package created (with `__init__.py`) if not already present.
  - [ ] Pattern 1 constructor injection with required kwargs.
  - [ ] `oversize_25_lines` remediated — 70 LoC → methods ≤ 25 lines.
  - [ ] Every `mh.ConfigUtils` lazy-import in `src/` eliminated.
  - [ ] 102 callsites enumerated in PR description callsite table.
  - [ ] Tests converted.

---

### T-13: Extract `FilePathUtils` to `src/utils/file_path_utils.py`

- **Dispatch position**: 13 of 15
- **Symbol**: `FilePathUtils`
- **Symbol type**: class (Pattern 1 Hot if runtime deps present; else `@staticmethod` collection — verify at dispatch)
- **Refactor category**: Cat E — Hot bucket
- **LOC reclaimed from MistHelper.py**: 46
- **Callsite count**: 50 refs
- **Landing module**: `src/utils/file_path_utils.py`
- **Branch**: `refactor/1015-t13-file-path-utils`
- **Commit message template**: `refactor(1015): extract FilePathUtils to src/utils/file_path_utils.py (T-13, Cat E)`
- **Analyzer flags to resolve in-flight**: `oversize_25_lines`, `missing_inline_comments`
- **Dependencies**: none — fully independent.
- **Task-specific acceptance criteria**:
  - [ ] Landing pattern verified at dispatch: Pattern 1 constructor if runtime deps; `@staticmethod` collection if pure.
  - [ ] `oversize_25_lines` remediated — 46 LoC → methods ≤ 25 lines.
  - [ ] `missing_inline_comments` remediated.
  - [ ] Every `mh.FilePathUtils` lazy-import in `src/` eliminated.
  - [ ] 50 callsites enumerated in PR description callsite table.
  - [ ] Tests converted.

---

### T-14: Extract `tqdm` wrapper to `src/utils/tqdm_wrapper.py`

- **Dispatch position**: 14 of 15
- **Symbol**: `tqdm` (the wrapper function, not the third-party library)
- **Symbol type**: function (3 LOC bare wrapper)
- **Refactor category**: Cat E — Hot bucket. **E-12 clarification**: NOT in `SKIP_ALWAYS` for this initiative — the 1012 skip-pin was per-initiative and does NOT carry over.
- **LOC reclaimed from MistHelper.py**: 3
- **Callsite count**: 51 refs
- **Landing module**: `src/utils/tqdm_wrapper.py` — OR domain-fit under `src/ui/*.py` per E-1 (rationale recorded in PR description).
- **Branch**: `refactor/1015-t14-tqdm-wrapper`
- **Commit message template**: `refactor(1015): extract tqdm wrapper to <landing-path> (T-14, Cat E)`
- **Analyzer flags to resolve in-flight**: `missing_action_logging`
- **Dependencies**: none — fully independent. Trivial deps → Pattern 1 constructor NOT required (bare function landing).
- **Task-specific acceptance criteria**:
  - [ ] Landing as bare module-level function (no Pattern 1 constructor needed for trivial 3-line wrapper).
  - [ ] E-12 verified: FR-009's `SKIP_ALWAYS` exclusion does NOT apply here — T-14 explicitly targets `tqdm` per this initiative's scope.
  - [ ] `missing_action_logging` remediated on the wrapper via `logging.info` / `logging.debug` envelopes.
  - [ ] Every `mh.tqdm` lazy-import in `src/` eliminated.
  - [ ] All 51 callsites enumerated in PR description callsite table.
  - [ ] Tests converted.

---

### T-15: Extract `MIST_SITE_EXCLUDE_PREFIX` to `src/refactors/mist_site_exclude_prefix.py`

- **Dispatch position**: 15 of 15 — **final PR of the initiative; last-merge PR carries the FR-024 / SC-022 final-state summary in its description (or a follow-up docs commit).**
- **Symbol**: `MIST_SITE_EXCLUDE_PREFIX`
- **Symbol type**: constant (module-level assignment, 3 LOC)
- **Refactor category**: Cat E — Hot bucket
- **LOC reclaimed from MistHelper.py**: 3
- **Callsite count**: 11 refs (across MistHelper.py + `src/gateway/*.py`)
- **Landing module**: `src/refactors/mist_site_exclude_prefix.py` — OR fold into an existing constants module in `src/gateway/*.py` per E-1 / E-14 (rationale recorded).
- **Branch**: `refactor/1015-t15-mist-site-exclude-prefix`
- **Commit message template**: `refactor(1015): extract MIST_SITE_EXCLUDE_PREFIX to <landing-path> (T-15, Cat E)`
- **Analyzer flags to resolve in-flight**: `missing_inline_comments`, `missing_action_logging`
- **Dependencies**: none — fully independent of every other task.
- **Task-specific acceptance criteria**:
  - [ ] Landing as bare module-level constant per E-14 (no wrapper class).
  - [ ] `missing_inline_comments` remediated — inline comment on constant declaration and context.
  - [ ] `missing_action_logging` remediated on read-side consumers touched by the rewrite.
  - [ ] Every `mh.MIST_SITE_EXCLUDE_PREFIX` reference in `src/gateway/*.py` (or elsewhere) rewritten to import from new location.
  - [ ] All 11 callsites enumerated in PR description callsite table.
  - [ ] **Final-state summary (SC-022) recorded in this PR description OR follow-up docs commit**: (a) count of PRs merged (target: 15), (b) final `MistHelper.py` LoC + pylint score, (c) final aggregate compliance score, (d) list of any deferred candidates + rationale, (e) confirmation that regenerated `refactor_candidates.md` on `main` shows only `menu_actions` + `GlobalImportManager`.

---

## Dependencies Summary

Mirrors plan.md's Dependency Graph exactly:

**Fully independent** (no shared callsite files at spec time): T-01, T-02, T-03, T-05, T-13, T-14.

**Coordinated overlap risks** (not blockers — mitigated by FR-023 serial dispatch + dispatch-time grep audit):

- **T-07 ↔ T-11** — both potentially touch `src/device/`. T-07 dispatched first (position 7); T-11 later (position 10) refreshes grep before its own dispatch.
- **T-04 → T-08 ordering** — T-04 dispatched at position 4 to eliminate the `ENDPOINT_PRIMARY_KEY_STRATEGIES` MistHelper.py residual before T-08 (position 8) needs it.
- **T-06 ↔ T-08** — Pattern 1 kwarg coupling (`data_exporter` kwarg on `OrgInventoryExporter`). Spec dispatches T-06 first (position 6) so T-08 (position 8) picks up the already-landed class via `from src.export.org_inventory_exporter import OrgInventoryExporter`.
- **T-09 broad fanout** — 195 refs across 17 files; Hot classes that precede T-09 (T-06/T-07/T-08/T-10/T-11) SHOULD bundle their `InputUtils.safe_input()` migrations in-flight so T-09's dispatch grep sees a reduced (but still comprehensive) callsite set.

**Serial dispatch invariant** (FR-023): at most one extraction PR open at any time. Analyzer regenerated after every merge (FR-014 / SC-010). Dispatch order is bucket-first (Single-use → Low-use → Hot) then descending-by-LOC within Hot.

---

## Dispatch Order Summary

| Position | Task | Symbol | Kind | Bucket | LOC | Refs | Landing |
|---:|:---:|---|:-:|:---|---:|---:|---|
| 1  | T-01 | `DeviceFetchConfig` | class | Single-use | 9 | 1 | `src/refactors/device_data_fetcher.py` |
| 2  | T-02 | `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` | constant | Single-use | 3 | 1 | `src/refactors/fast__mode__max__concurrent__connections.py` |
| 3  | T-03 | `FAST_MODE_USE_CONNECTION_AWARE_THREADING` | constant | Single-use | 3 | 1 | `src/refactors/fast__mode__use__connection__aware__threading.py` |
| 4  | T-04 | `ENDPOINT_PRIMARY_KEY_STRATEGIES` | constant | Low-use | 2327 | 2 | `src/refactors/endpoint__primary__key__strategies.py` (or `src/api/*.py`) |
| 5  | T-05 | `detect_msp_privileges` | function | Low-use | 25 | 2 | `src/refactors/detect_msp_privileges.py` (or `src/msp/*.py`) |
| 6  | T-06 | `OrgInventoryExporter` | class (Pattern 1) | Hot | 686 | 102 | `src/export/org_inventory_exporter.py` |
| 7  | T-07 | `PromptUtils` | class (Pattern 1) | Hot | 441 | 96 | `src/ui/prompt_utils.py` (E-1 collision) |
| 8  | T-08 | `DataExporter` | class (Pattern 1) | Hot | 345 | 118 | `src/export/data_exporter.py` |
| 9  | T-10 | `DataProcessingUtils` | class (Pattern 1) | Hot | 158 | 69 | `src/data/data_processing_utils.py` |
| 10 | T-11 | `VirtualChassisManager` | class (Pattern 1) | Hot | 78 | 104 | `src/device/virtual_chassis.py` (fold-in) |
| 11 | T-09 | `InputUtils` | class (Pattern 1) | Hot | 74 | 195 | `src/ui/input_utils.py` (E-1 collision) |
| 12 | T-12 | `ConfigUtils` | class (Pattern 1) | Hot | 70 | 102 | `src/config/config_utils.py` |
| 13 | T-13 | `FilePathUtils` | class (Pattern 1 or static) | Hot | 46 | 50 | `src/utils/file_path_utils.py` |
| 14 | T-14 | `tqdm` (wrapper) | function | Hot | 3 | 51 | `src/utils/tqdm_wrapper.py` (or `src/ui/*.py`) |
| 15 | T-15 | `MIST_SITE_EXCLUDE_PREFIX` | constant | Hot | 3 | 11 | `src/refactors/mist_site_exclude_prefix.py` (or `src/gateway/*.py`) |

**Cumulative LOC reclaimed**: 4,271 (target per SC-002: ≥ 3,500 net drop after class-body overhead retention).

**Initiative closure**: When T-15 (or the final reclassified equivalent) merges and `refactor_candidates.md` is regenerated one final time, the report shows only `menu_actions` + `GlobalImportManager` (per SC-001 / FR-024 / FR-032). No further MistHelper.py refactor initiative is planned.
