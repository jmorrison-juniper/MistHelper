---

description: "Task list for the Org AP Upgrader Compliance Refactor (specs/1006-org-ap-upgrader-compliance)"
---

# Tasks: Org AP Upgrader Compliance Refactor

**Input**: Design documents from `specs/1006-org-ap-upgrader-compliance/`
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/constructor.md`

**Feature branch**: `refactor/org-ap-upgrader-compliance` (already checked out).

**Tests**: NOT added. No pre-existing unit test file for `src/firmware/org_ap_upgrader.py` exists and NG-001 forbids creating one. The compliance analyzer, `ruff`, `black --check`, `mypy --strict`, `py_compile`, and the byte-identity diff against MistHelper.py are the sole gates.

**Organization**: Tasks are grouped by phase. Every task's verification gate is the six-command block below unless noted otherwise.

**Prior-art reference**: `specs/1005-firmware-manager-compliance/tasks.md` (PR #580, 43 tasks, all merged at A+/100.0). This file mirrors that proven shape.

## Standing Verification Gate (applies to every task in this file)

Every task in this file is not complete until ALL SIX commands report clean:

```bash
python -m py_compile src/firmware/org_ap_upgrader.py                       # exit 0
python -m ruff check src/firmware/org_ap_upgrader.py                       # zero errors, zero warnings
python -m black --check src/firmware/org_ap_upgrader.py                    # zero reformat needed
python -m mypy --strict src/firmware/org_ap_upgrader.py                    # zero errors
python -m tools.compliance_analyzer src/firmware/org_ap_upgrader.py        # score trends toward 100.0 / A+
git diff main..HEAD -- MistHelper.py                                       # EMPTY output (byte-identity)
```

Any task that regresses ruff / black / mypy / py_compile is reverted before moving on. Compliance score is expected to climb monotonically; a within-task dip is only acceptable if the very next task recovers it. The final target is exactly **100.0 / A+** with zero HIGH / zero MEDIUM / zero LOW findings across every analyzer rule bucket. `git diff main..HEAD -- MistHelper.py` must be **empty** for the entire duration of the refactor — no exceptions.

If `pytest tests/unit/` contains any tests that import `src.firmware.org_ap_upgrader`, they must also pass on every task. Currently zero such tests exist (NG-001), so this check is a spot-grep only.

## Format: `[ID] [P?] Description`

- **[P]**: Task edits a file that no concurrent task is also editing. Because ~100% of this refactor lives in `src/firmware/org_ap_upgrader.py`, [P] appears sparingly (only baseline/artifact capture and the final read-only verification tasks).
- Every task lists the exact file path being edited.
- Every task has a "Done when:" line stating the acceptance criterion for that task in isolation.

## Path Conventions

- Repository root is the current working directory.
- **Sole edit target**: `src/firmware/org_ap_upgrader.py` (2393 lines pre-refactor, ~3800 lines post-refactor).
- **Zero permitted off-file diffs**: `MistHelper.py` at lines 20237-20314 must remain byte-identical (FR-018, SC-007). Any drift is a scope violation — halt and revert.
- Optional plan reference update: `.github/copilot-instructions.md` between the SPECKIT markers.
- Artifact drop directory: `specs/1006-org-ap-upgrader-compliance/artifacts/` (pre-populated with `baseline_compliance_report.md` and `baseline_lint.txt`).

## AGENTS.md Non-Negotiables (apply inside every implementation task)

1. Every NEW or EDITED executable line must carry an inline `# WHY: <intent>` comment explaining why the line exists (not what it does) — Constitution VI, FR-005.
2. Every NEW operation (I/O, mutation, branch, API call, file op) must be bracketed by `logging.info(...)` BEFORE and `logging.debug(...)` AFTER with a result summary — Constitution VII, FR-012.
3. All log strings must be ASCII-only and use lazy `%s` / `%d` form — no f-strings inside `logging.*` calls (FR-013).
4. No wrapper / delegator / alias / shim helpers (FR-011). Any extracted helper must do real work.
5. No `# noqa`, `# type: ignore`, or `# pragma: no cover` markers as substitutes for real structural fixes (FR-015).
6. No analyzer threshold relaxation — the target is 100.0 / A+ against the stock analyzer configuration.
7. Zero MistHelper.py diff. Zero. Not a comment, not a whitespace, not a blank line.
8. Every helper is `<=25` executable lines, `<=5` blocks, `<=5` parameters, CC `<=5`, nesting depth `<=4`.

If a task's diff would introduce a violation of items 1-8, the task is not complete.

---

## Phase 1: Setup (Baseline Capture)

**Purpose**: Freeze the pre-refactor test-runnability baseline so every subsequent task can be measured against a known starting point. The compliance baseline is already captured at `specs/1006-org-ap-upgrader-compliance/artifacts/baseline_compliance_report.md` — do not modify it. No source code is changed in this phase.

- [X] **T-001** [P] Capture pre-refactor lint / compile / type baseline by running `python -m py_compile src/firmware/org_ap_upgrader.py`, `python -m ruff check src/firmware/org_ap_upgrader.py`, `python -m black --check src/firmware/org_ap_upgrader.py`, and `python -m mypy --strict src/firmware/org_ap_upgrader.py` in sequence. Save combined stdout+stderr to `specs/1006-org-ap-upgrader-compliance/artifacts/baseline_toolchain.txt`. Confirm each tool's exit code.
  - **Done when:** file records exit codes for all four tools; any pre-refactor tool failure is documented (baseline may not be clean under mypy --strict — this is expected and does not block the refactor).
- [X] **T-002** [P] Capture pre-refactor unit-test runnability by running `python -m pytest tests/unit/ -k org_ap_upgrader --collect-only` and saving output to `specs/1006-org-ap-upgrader-compliance/artifacts/baseline_pytest.txt`. Expected outcome: zero tests collected (NG-001 forbids creating new tests, and no pre-existing tests reference this module).
  - **Done when:** artifact file confirms `no tests ran` or equivalent zero-collection status; if any tests are found, list them here and confirm none are modified during the refactor.
- [X] **T-003** [P] Enumerate every MistHelper.py callsite by running `grep -n "from src\.firmware\.org_ap_upgrader" MistHelper.py` and saving output to `specs/1006-org-ap-upgrader-compliance/artifacts/callsites.txt`. Confirm exactly four import lines at 20247, 20269, 20289, 20305 and confirm four `_Impl(...)` construction blocks in the same neighborhood. Any additional callsite discovered here is a scope violation and blocks Phase 3.
  - **Done when:** callsites.txt matches the four expected lines exactly. Also record the full 20237-20314 line range as a `git blame`-style snapshot for later byte-identity verification.
- [X] **T-004** [P] Verify the artifact directory exists (`specs/1006-org-ap-upgrader-compliance/artifacts/`) and already contains `baseline_compliance_report.md` and `baseline_lint.txt`. Confirm write access by touching `specs/1006-org-ap-upgrader-compliance/artifacts/.gitkeep` if not already present. This unblocks Phase 8 artifact drops.
  - **Done when:** `ls` on the artifacts directory succeeds and shows the pre-existing baseline files; no other change to that directory is made yet.

**Checkpoint**: Baselines locked. Every later task compares against these artifacts. `git diff main..HEAD -- MistHelper.py` is empty (nothing changed yet).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Introduce the `OrgAPUpgraderConfig` dataclass. This is `T-DATACLASS` (labeled per user request). It BLOCKS the `__init__` kwargs-passthrough migration (Phase 3) AND every downstream helper extraction that reads collaborators via `self._config.*`. Nothing else in the refactor can begin until this task lands cleanly.

**CRITICAL**: No structural work can begin until this phase is complete.

- [X] **T-005** [T-DATACLASS] Add the `OrgAPUpgraderConfig` frozen dataclass to `src/firmware/org_ap_upgrader.py` per `data-model.md`. Placement: below the module imports and above the `OrgLevelAPFirmwareUpgrader` class at line 41. Requirements:
  - Decorator: `@dataclass(frozen=True, slots=True, kw_only=True)`.
  - Eleven fields matching the pre-refactor 11-parameter `__init__` 1:1 (see `data-model.md` field-mapping table): `org_id: str`, `apisession: Any`, `dry_run: bool = False`, `safe_input_fn: Optional[Any] = None`, `check_stop_fn: Optional[Any] = None`, `get_org_id_fn: Optional[Any] = None`, `fetch_sites_fn: Optional[Any] = None`, `write_results_fn: Optional[Any] = None`, `is_debug_fn: Optional[Any] = None`, `msp_privileges: Optional[list[Any]] = None`, `selected_msp: Optional[dict[str, Any]] = None`.
  - Add `__post_init__` per `data-model.md` "Validation Rules" table: `isinstance(org_id, str)` (empty allowed for MSP-select callsites at 20289/20305), `apisession is not None`, permissive `bool(dry_run)` coercion via `object.__setattr__`, each `*_fn` `None` or `callable(...)`, `msp_privileges` normalized from `None` to `[]` via `object.__setattr__`, `selected_msp` `None` or `dict`.
  - Every field declaration and every executable line inside `__post_init__` carries a `# WHY: <intent>` inline comment (fields count as executable lines for the analyzer).
  - Imports: add `from dataclasses import dataclass` and `from typing import Optional` if not already present. `Any` is already imported.
  - Verification: `python -m py_compile src/firmware/org_ap_upgrader.py` exits 0; `python -m ruff check src/firmware/org_ap_upgrader.py` clean; `python -c "from src.firmware.org_ap_upgrader import OrgAPUpgraderConfig; print(list(OrgAPUpgraderConfig.__dataclass_fields__))"` prints all eleven field names.
  - **Done when:** `OrgAPUpgraderConfig` is importable at module level; `__post_init__` rejects the seven invalid cases from `data-model.md` "Failure-Mode Diagnostics"; no analyzer regression is introduced (pre-refactor 11-param `__init__` is still present at line 41 and still flagged — that is expected and cleared in Phase 3); `git diff main..HEAD -- MistHelper.py` is still empty.

**Checkpoint**: `OrgAPUpgraderConfig` exists and is importable. `__init__` still has its pre-refactor 11-parameter shape (unchanged). Phase 3 kwargs-passthrough migration can now proceed.

---

## Phase 3: Constructor Migration (Kwargs-Passthrough per contracts/constructor.md)

**Goal**: Reshape `OrgLevelAPFirmwareUpgrader.__init__` from 11 parameters / 45 lines / STRUCT-PARAMS + STRUCT-LENGTH violation to `def __init__(self, **cfg: Any) -> None` (1 formal parameter, `<=15` executable lines). Preserve every module-side effect and pre-refactor `self.<attr>` surface via a `_apply_config_to_attributes()` helper (research.md R-1).

**Independent Test**: `python -m tools.compliance_analyzer src/firmware/org_ap_upgrader.py` shows `__init__` no longer flagged for STRUCT-PARAMS or STRUCT-LENGTH. All four MistHelper.py callsites (20247/20269/20289/20305) succeed under `python -m py_compile` with zero diff. Direct positional invocation `OrgLevelAPFirmwareUpgrader("org", session)` raises `TypeError` (contract C-2). Kwargs invocation with all four callsite shapes (11-kwarg, 9-kwarg, 5-kwarg with `org_id=""`, 3-kwarg with `org_id=""`) succeeds (contracts C-1, C-3, C-4, C-5, C-6).

- [X] **T-006** Add module-level (or class-level, per implementer's choice — must be `<=25` lines, CC `<=5`) private helper `_apply_config_to_attributes(self) -> None` to `src/firmware/org_ap_upgrader.py`. Body: reads each field from `self._config` and sets the corresponding pre-refactor attribute (`self.org_id = self._config.org_id`, `self.apisession = self._config.apisession`, `self.dry_run = self._config.dry_run`, `self.safe_input_fn = self._config.safe_input_fn or self._default_safe_input`, ... same pattern for the other five `*_fn` hooks with their pre-refactor `_default_*` fallbacks, `self.msp_privileges = self._config.msp_privileges`, `self.selected_msp = self._config.selected_msp`). This preserves the pre-refactor `self.<attr>` surface every downstream helper reads today, so no other helper needs to change simultaneously. Every executable line carries a `# WHY:` inline comment. Bracket with `logging.info("Applying config to instance attributes for org %s", self._config.org_id)` at entry and `logging.debug("Applied %d config fields to instance", 11)` at exit. Ceiling: `<=25` lines, `<=5` params (this one has 1), `<=5` blocks, `<=4` nesting, CC `<=5`.
  - **Done when:** helper exists; calling it inside `__init__` rebinds all eleven pre-refactor attribute names; ruff+black+py_compile clean; no new analyzer violations introduced; MistHelper.py still byte-identical.
- [X] **T-007** Rewrite `OrgLevelAPFirmwareUpgrader.__init__` in `src/firmware/org_ap_upgrader.py` line 41 to the exact shape shown in `data-model.md` "Usage — Consumer Side": signature is `def __init__(self, **cfg: Any) -> None`; body is exactly 6 executable lines — `logging.info(...)`, `self._config = OrgAPUpgraderConfig(**cfg)`, `self._apply_config_to_attributes()`, `self._init_selection_state()`, `self._init_device_state()`, `self._init_results_state()`, `logging.debug(...)`. Each line carries a `# WHY:` inline comment. **Delete** the pre-existing `# pylint: disable=too-many-arguments` marker on the pre-refactor line 41 signature (FR-015). **Delete** the pre-existing module-level `# pylint: disable=too-many-lines,logging-fstring-interpolation` at line 9 (the `too-many-lines` half is scoped out and the `logging-fstring-interpolation` half is rendered moot by R-8 lazy-format conversion in Phase 7). Also add the two read-only properties `org_id`, `apisession`, and `dry_run` from `data-model.md` "Usage — Consumer Side" so downstream helpers that already read `self.org_id` / `self.apisession` / `self.dry_run` continue to work byte-identically — note that `_apply_config_to_attributes()` already assigns these as instance attributes, so the properties may be omitted if the attribute assignment is preferred; pick one strategy and apply it uniformly. Every helper method in the file that reads `self.safe_input_fn` / `self.check_stop_fn` / etc. continues to work unchanged because `_apply_config_to_attributes()` reassigns those names. This task DEPENDS ON T-005 + T-006.
  - **Done when:** `__init__` body is `<=15` executable lines with 1 formal parameter (`**cfg`); analyzer no longer reports STRUCT-PARAMS or STRUCT-LENGTH on `__init__` at line 41; two `# pylint: disable` markers are removed from the file; ruff + black + mypy --strict + py_compile all exit 0; `git diff main..HEAD -- MistHelper.py` is empty; all four MistHelper.py callsites succeed under a REPL smoke that calls each with its pre-refactor kwargs shape.

**Checkpoint**: `__init__` is `<=15` executable lines with 1 formal parameter. STRUCT-PARAMS clears. STRUCT-LENGTH clears on `__init__`. Both `# pylint: disable` suppressions are gone. Score climbs materially. Downstream method bodies continue to read collaborators via the same `self.<attr>` names as pre-refactor. All four MistHelper.py callsites are functional and byte-identical.

---

## Phase 4: STRUCT-LENGTH Remediation (10 Remaining Offenders)

**Goal**: Bring each of the ten remaining STRUCT-LENGTH offenders (all except `__init__` which cleared in Phase 3) to `<=25` executable lines, `<=5` blocks, CC `<=5`, nesting `<=4` by applying the **PCPP pattern** (Prepare / Compute / Present / Persist) plus named phase helpers (research.md R-3, R-4). Each orchestrator ends as a 4-8 line sequence of helper calls; each helper is `<=25` lines with `# WHY:` comments on every executable line and `logging.info` before / `logging.debug` after brackets.

**Independent Test**: For each of the ten offenders, `python -m tools.compliance_analyzer src/firmware/org_ap_upgrader.py` shows the method removed from the flagged-offenders list. Every MistHelper.py callsite dry-run smoke reaches identical prompt sequences vs. the pre-refactor branch (FR-003).

**Rule for every task in this phase**: apply PCPP; helpers named `_prepare_<action>_context`, `_compute_<action>_plan`, `_present_<action>_preview`, `_persist_<action>_results` (omit any slice that would be `<=3` executable lines — inline it, per FR-011). Where R-4 defines named phase helpers (`_msp_phase_*`, `_org_phase_*`, `_canary_phase_*`, `_upgrade_phase_*`), use those names in preference to generic PCPP names. Every helper carries `# WHY:` on every executable line + `logging.info` before / `logging.debug` after brackets. Every helper `<=25` lines / `<=5` blocks / CC `<=5` / nesting `<=4` / `<=5` parameters. The public method is rewritten as a thin orchestrator whose executable lines also carry `# WHY:` comments. Every `input(...)` in touched code paths is routed through `safe_input(..., context="org-ap-upgrader.<kebab-tag>")`. Every filesystem path uses `os.path.join(...)` or `pathlib.Path(...)`.

Tasks are ordered by pre-refactor line number (offenders enumerated in `plan.md` bullet 3). All edit `src/firmware/org_ap_upgrader.py` sequentially — no [P] because same file.

- [X] **T-008** Decompose `_execute_msp_mode` at pre-refactor line 178 (28 executable lines, STRUCT-LENGTH). Apply R-4 MSP phase helpers: `_msp_phase_fetch` (calls `_fetch_msp_orgs`), `_msp_phase_confirm` (wraps `_confirm_msp_orgs`), `_msp_phase_iterate` (drives the per-org loop). Rewrite `_execute_msp_mode` as a 4-6 line orchestrator that calls the three phase helpers in strict pre-refactor order. Preserve every prompt string, CSV output path, and API call byte-for-byte.
  - **Done when:** analyzer shows `_execute_msp_mode` at `<=25` executable lines with no flags; every phase helper is `<=25` lines / `<=5` blocks / CC `<=5`; MistHelper.py diff empty.
- [X] **T-009** Decompose `_confirm_msp_orgs` at pre-refactor line 232 (31 executable lines, STRUCT-LENGTH) via PCPP: `_prepare_msp_confirm_context`, `_compute_msp_confirm_selection`, `_present_msp_confirm_preview`, `_persist_msp_confirm_selection`. The `_present_*` slice owns the `safe_input(context="org-ap-upgrader.msp-confirm")` prompt loop. Rewrite the orchestrator.
  - **Done when:** analyzer shows `_confirm_msp_orgs` at `<=25` lines with no flags; every helper is `<=25` lines / CC `<=5`; every `input(` in this code path is `safe_input(..., context="org-ap-upgrader.msp-confirm")`.
- [X] **T-010** Decompose `_execute_org_upgrades` at pre-refactor line 264 (42 executable lines, STRUCT-LENGTH — the second-largest offender). Apply R-4 org phase helpers: `_org_phase_select`, `_org_phase_prepare_payload`, `_org_phase_invoke_api`, `_org_phase_record_result`. Rewrite `_execute_org_upgrades` as a 4-6 line orchestrator per the sample in research.md R-3. Because CC is elevated by the per-org iteration, ensure the loop lives in `_org_phase_invoke_api` and the orchestrator itself is CC `<=3`.
  - **Done when:** analyzer shows `_execute_org_upgrades` at `<=25` lines with no flags; every phase helper is `<=25` lines / `<=5` blocks / CC `<=5`; identical CSV output paths (via `os.path.join`) and log lines vs. pre-refactor.
- [X] **T-011** Decompose `_select_orgs_from_msp` at pre-refactor line 448 (31 executable lines, STRUCT-LENGTH) via PCPP: `_prepare_org_selection_context`, `_compute_org_selection_candidates`, `_present_org_selection_prompt`, `_persist_org_selection_result`. The `_present_*` slice owns the `safe_input(context="org-ap-upgrader.org-select")` prompt.
  - **Done when:** method `<=25` lines; every helper `<=25` lines / CC `<=5`; every `input(` in this code path is `safe_input(..., context="org-ap-upgrader.org-select")`.
- [X] **T-012** Decompose `_step1_select_site_scope` at pre-refactor line 761 (32 executable lines, STRUCT-LENGTH) via PCPP: `_prepare_site_scope_context`, `_compute_site_scope_options`, `_present_site_scope_prompt`, `_persist_site_scope_selection`. The `_present_*` slice owns the `safe_input(context="org-ap-upgrader.site-scope")` prompt.
  - **Done when:** method `<=25` lines; every helper `<=25` lines / CC `<=5`; nesting `<=4` throughout the extracted helpers.
- [X] **T-013** Decompose `_fetch_org_aps` at pre-refactor line 883 (27 executable lines, STRUCT-LENGTH + STRUCT-COMPLEXITY CC 6) via PCPP: `_prepare_fetch_aps_context`, `_compute_fetch_aps_query`, `_persist_fetch_aps_accumulator`. Because this method is pure I/O + accumulation, omit the `_present_*` slice (would be `<=3` lines — inline per FR-011). Preserve every `mistapi.*` invocation byte-for-byte (FR-003).
  - **Done when:** method `<=25` lines / CC `<=5`; every helper `<=25` lines / CC `<=5`; API call semantics unchanged; STRUCT-COMPLEXITY finding on this method also clears as a side effect.
- [X] **T-014** Decompose `_apply_version_selection` at pre-refactor line 1340 (28 executable lines, STRUCT-LENGTH) via PCPP: `_prepare_version_selection_context`, `_compute_version_selection_mapping`, `_present_version_selection_summary`, `_persist_version_selection_result`. The `_persist_*` slice writes the per-org CSV — use `os.path.join(...)` for the output path.
  - **Done when:** method `<=25` lines; every helper `<=25` lines / CC `<=5`; CSV output path uses `os.path.join`.
- [X] **T-015** Decompose `_configure_canary_phases` at pre-refactor line 1928 (26 executable lines, STRUCT-LENGTH). Apply R-4 canary phase helpers: `_canary_phase_read_count`, `_canary_phase_read_percentages`, `_canary_phase_read_delays`, `_canary_phase_build_config`. Rewrite `_configure_canary_phases` as a 4-6 line orchestrator. Every `input(...)` in these code paths -> `safe_input(..., context="org-ap-upgrader.canary-<phase>")`.
  - **Done when:** method `<=25` lines; every phase helper `<=25` lines / CC `<=5`; every `input(` in these code paths is `safe_input(..., context=...)`.
- [X] **T-016** Decompose `_execute_upgrades` at pre-refactor line 2242 (28 executable lines, STRUCT-LENGTH). Apply R-4 upgrade phase helpers: `_upgrade_phase_group_by_version`, `_upgrade_phase_post_one`, `_upgrade_phase_handle_response`. Rewrite `_execute_upgrades` as a 4-6 line orchestrator. Preserve every `mistapi.*` invocation byte-for-byte (FR-003). Note `_upgrade_phase_handle_response` delegates to `_process_upgrade_response` which is decomposed independently in T-017.
  - **Done when:** method `<=25` lines; every phase helper `<=25` lines / CC `<=5`; upgrade API call semantics unchanged.
- [X] **T-017** Decompose `_process_upgrade_response` at pre-refactor line 2347 (26 executable lines, STRUCT-LENGTH + STRUCT-COMPLEXITY CC 6) via PCPP: `_prepare_upgrade_response_context`, `_compute_upgrade_response_status`, `_persist_upgrade_response_record`. Omit the `_present_*` slice (this method is called from `_upgrade_phase_handle_response` and does not prompt). The `_compute_*` slice owns the HTTP-status branching — because CC 6 is driven by status-code branching, split into status-code family predicates (`_response_is_success`, `_response_is_retryable`, `_response_is_terminal`) per R-6 rather than a single compute slice.
  - **Done when:** method `<=25` lines / CC `<=5`; every helper `<=25` lines / CC `<=5`; STRUCT-COMPLEXITY finding on this method also clears as a side effect.

**Checkpoint**: All ten remaining STRUCT-LENGTH offenders removed. Score climbs substantially (baseline 60.0 -> ~75-80 expected). STRUCT-LENGTH finding count is 0. STRUCT-COMPLEXITY side-effect clears on `_fetch_org_aps` and `_process_upgrade_response` (2 of 14 CC offenders). Remaining CC work: 12 offenders addressed in Phase 5. MistHelper.py diff still empty.

---

## Phase 5: STRUCT-COMPLEXITY Remediation (12 Remaining Offenders)

**Goal**: Bring each of the twelve remaining STRUCT-COMPLEXITY offenders (all except `_fetch_org_aps` and `_process_upgrade_response` which cleared in Phase 4) to CC `<=5` by applying **dispatch tables** for the parser trio (research.md R-5) and **guard-clause predicate helpers** for the print/organize/build quartet (research.md R-6). Where an offender's complexity is driven by branching that overlaps with the STRUCT-LENGTH decomposition, the PCPP split already brought it under threshold; otherwise apply the dedicated dispatch/predicate strategy.

**Independent Test**: `python -m tools.compliance_analyzer src/firmware/org_ap_upgrader.py` reports zero STRUCT-COMPLEXITY findings. Zero STRUCT-BLOCKS. Zero STRUCT-NESTING. Score `>=90`.

**Rule for every task in this phase**: same helper ceilings as Phase 4 (`<=25` lines / `<=5` blocks / CC `<=5` / nesting `<=4` / `<=5` params). Every executable line new or edited carries `# WHY:` inline commentary. `logging.info` before / `logging.debug` after brackets on every helper. Predicates that return `bool` are excepted from the info/debug bracket rule if they are `<=3` lines and CC `<=2` (no I/O, no mutation). Every `input(...)` in touched code paths -> `safe_input(..., context="org-ap-upgrader.<kebab-tag>")`. Every filesystem path -> `os.path.join(...)` or `pathlib.Path(...)`.

Tasks are batched by cohesive strategy. All edit `src/firmware/org_ap_upgrader.py` sequentially (no [P]):

### Batch A: Parser Trio (Dispatch Tables — R-5)

- [X] **T-018** Convert `_parse_time_input` at pre-refactor line 1597 (CC 7) to a dispatch table per research.md R-5. Add class-level `_TIME_INPUT_HANDLERS: dict[str, Callable[..., ...]]` mapping the four pre-refactor branches (`""` -> immediate, `"now"` -> current UTC, `"after"` -> relative offset, absolute fall-through) to small handler methods (`_parse_time_empty`, `_parse_time_now`, `_parse_time_after` [reuse T-019's], `_parse_time_absolute`). Rewrite `_parse_time_input` as: normalize prefix -> dispatch dict lookup -> single call -> return. Every executable line carries `# WHY:`. Bracket with `logging.info` before / `logging.debug` after. Preserve exact pre-refactor parse semantics for every input format (FR-003).
  - **Done when:** analyzer shows `_parse_time_input` at CC `<=3` with no flags; dispatch dict is class-level (frozen at import time); every branch still parses identically vs. pre-refactor.
- [X] **T-019** Convert `_try_parse_after` at pre-refactor line 1637 (CC 6) to a dispatch table per research.md R-5. Add class-level `_AFTER_SUFFIX_HANDLERS: dict[str, Callable[..., ...]]` mapping the four pre-refactor suffix branches (`"m"`, `"h"`, `"d"`, `"w"`) to small handler methods (`_parse_after_minutes`, `_parse_after_hours`, `_parse_after_days`, `_parse_after_weeks`). Rewrite `_try_parse_after` as: extract suffix -> dispatch dict lookup -> single call -> return. Preserve exact pre-refactor arithmetic for every suffix (FR-003).
  - **Done when:** analyzer shows `_try_parse_after` at CC `<=3` with no flags; dispatch dict is class-level; every suffix parses identically vs. pre-refactor.
- [X] **T-020** Convert `_parse_canary_phase_values` at pre-refactor line 1906 (CC 7) to a dispatch table per research.md R-5. Add class-level `_CANARY_VALUE_HANDLERS: dict[str, Callable[..., ...]]` mapping the pre-refactor `kind` branches (`"percent"`, `"delay"`, `"model"`, ...) to small handler methods. Rewrite `_parse_canary_phase_values` as: extract kind -> dispatch dict lookup -> single call -> return. Preserve exact pre-refactor parse semantics for every kind (FR-003).
  - **Done when:** analyzer shows `_parse_canary_phase_values` at CC `<=3` with no flags; dispatch dict is class-level; every kind parses identically vs. pre-refactor.

### Batch B: Guard-Clause Quartet (Predicate Helpers — R-6)

- [X] **T-021** Lift `_organize_by_version` at pre-refactor line 1458 (CC 7 — the second-highest CC offender) into a guard-clause form per research.md R-6. Extract two `bool`-returning predicate helpers: `_ap_has_target(self, ap: dict) -> bool` and `_ap_at_target(self, ap: dict) -> bool`. Rewrite `_organize_by_version` per the sample in R-6: single-pass grouping loop with two `continue`-guard predicates, then the accumulator setdefault, then return. Every executable line carries `# WHY:`. Bracket with `logging.info` before / `logging.debug` after.
  - **Done when:** analyzer shows `_organize_by_version` at CC `<=3` with no flags; predicates are `<=5` lines each / CC `<=2`; grouping output identical vs. pre-refactor.
- [X] **T-022** Lift `_build_model_version_mapping` at pre-refactor line 1173 (CC 6) into a guard-clause form per research.md R-6. Extract `bool`-returning predicate helper `_should_include_version(self, version: dict) -> bool` (or similar — pick the smallest predicate that captures the pre-refactor skip logic). Rewrite `_build_model_version_mapping` as a single-pass loop with the predicate as an early-continue guard, then the accumulator update, then return.
  - **Done when:** analyzer shows `_build_model_version_mapping` at CC `<=3` with no flags; predicate `<=5` lines / CC `<=2`; mapping output identical vs. pre-refactor.
- [X] **T-023** Lift `_print_msp_summary` at pre-refactor line 670 (CC 6) into a guard-clause form per research.md R-6. Extract `bool`-returning predicate helpers (`_msp_has_orgs`, `_msp_has_name`, etc. — pick the smallest set that captures the pre-refactor conditional-print logic). Rewrite `_print_msp_summary` as: for each output row, predicate check -> continue-guard -> print row. Preserve every pre-refactor print string byte-for-byte (FR-003).
  - **Done when:** analyzer shows `_print_msp_summary` at CC `<=3` with no flags; predicates `<=5` lines each / CC `<=2`; every print string identical vs. pre-refactor.
- [X] **T-024** Lift `_print_dry_run_entry` at pre-refactor line 2199 (CC 6) into a guard-clause form per research.md R-6. Extract `bool`-returning predicate helpers (`_row_has_target`, `_row_has_delay`, etc.). Rewrite `_print_dry_run_entry` as: for each field, predicate check -> continue-guard -> print field. Preserve every pre-refactor print string byte-for-byte (FR-003).
  - **Done when:** analyzer shows `_print_dry_run_entry` at CC `<=3` with no flags; predicates `<=5` lines each / CC `<=2`; every dry-run row identical vs. pre-refactor.

### Batch C: Remaining CC Offenders (PCPP + Sub-Extraction)

- [X] **T-025** Reduce `run` (the main entry point) CC via PCPP-style sub-extraction. Identify the pre-refactor branching source (typically mode selection: MSP vs. org, dry-run vs. live) and extract a `_run_dispatch(mode: str) -> None` helper plus small mode-specific launchers (`_run_msp_mode`, `_run_org_mode`, `_run_dry_run_preview`). Rewrite `run` as: parse mode -> dispatch call -> return. Every executable line carries `# WHY:`. Bracket with `logging.info` before / `logging.debug` after. Preserve the exact prompt sequence at every entry point (FR-003).
  - **Done when:** analyzer shows `run` at CC `<=5` with no flags; every launcher `<=25` lines / CC `<=5`; entry-point prompt sequence identical vs. pre-refactor.
- [X] **T-026** Reduce `_fetch_msp_orgs` CC via PCPP-style sub-extraction. Extract `_prepare_msp_fetch_query`, `_compute_msp_fetch_response`, `_persist_msp_fetch_accumulator`. Omit `_present_*` (pure I/O, no prompt). Preserve every `mistapi.*` invocation byte-for-byte.
  - **Done when:** analyzer shows `_fetch_msp_orgs` at CC `<=5` with no flags; every helper `<=25` lines / CC `<=5`; MSP fetch semantics unchanged.
- [X] **T-027** Reduce `_get_org_inventory` and `_fetch_site_aps` CC in a single batched task (both are I/O + accumulation with elevated CC). Apply the same three-slice PCPP (prepare / compute / persist) to each. Every filesystem or CSV path -> `os.path.join(...)`. Preserve every `mistapi.*` invocation byte-for-byte.
  - **Done when:** analyzer shows both methods at CC `<=5` with no flags; every helper `<=25` lines / CC `<=5`; inventory + site-AP fetch semantics unchanged.
- [X] **T-028** Reduce `_step6_configure_upgrade` CC via PCPP. Extract `_prepare_upgrade_config_context`, `_compute_upgrade_config_plan`, `_present_upgrade_config_confirm`, `_persist_upgrade_config_record`. The `_present_*` slice owns the final `safe_input(context="org-ap-upgrader.upgrade-confirm")` prompt before commit.
  - **Done when:** analyzer shows `_step6_configure_upgrade` at CC `<=5` with no flags; every helper `<=25` lines / CC `<=5`; every `input(` in this code path is `safe_input(..., context="org-ap-upgrader.upgrade-confirm")`.

**Checkpoint**: All twelve remaining STRUCT-COMPLEXITY offenders removed. Every STRUCT-BLOCKS and STRUCT-NESTING finding is cleared as a side effect of the PCPP splits + predicate extractions. Analyzer buckets STRUCT-LENGTH / STRUCT-COMPLEXITY / STRUCT-BLOCKS / STRUCT-NESTING / STRUCT-PARAMS all report 0. Only CONV-COMMENTS remains non-zero (cleared in Phase 6). Score is `~85-90` at this checkpoint. MistHelper.py diff still empty.

---

## Phase 6: CONV-COMMENTS Sweep (Lift 16% -> >=80% Inline-Comment Coverage)

**Goal**: Push inline-comment coverage from 16.0% to `>=80%` (analyzer threshold — spec target is a small buffer above threshold). This is the largest single-diff phase in the plan because every executable line in the file that lacks `# WHY: <intent>` must acquire one. Most of the coverage is picked up incrementally in Phases 3-5 as helpers are extracted with `# WHY:` on every line; this phase is the sweep that closes the gap on methods the earlier phases did not touch.

**Independent Test**: `python -m tools.compliance_analyzer src/firmware/org_ap_upgrader.py` reports zero CONV-COMMENTS findings and inline-comment coverage `>=80%`. Grep `git grep -c "# WHY:" src/firmware/org_ap_upgrader.py` returns a count matching the analyzer's reported executable-line total scaled by 0.80.

- [X] **T-029** Sweep the constructor cohort in `src/firmware/org_ap_upgrader.py` — `__init__`, `_apply_config_to_attributes`, `OrgAPUpgraderConfig` (fields + `__post_init__`), and any `org_id` / `apisession` / `dry_run` properties — and confirm every executable line carries a `# WHY: <intent>` inline comment. Add missing comments. Every comment explains WHY the line exists (Constitution VI), not WHAT it does. Since these were introduced fresh in Phase 2-3, coverage should already be at 100% here — this task is the audit.
  - **Done when:** grep of the constructor cohort shows every executable line ends in `# WHY:` (or a functionally equivalent trailing `# <intent>` for the rare case where `# WHY:` reads awkwardly).
- [X] **T-030** Sweep every helper introduced in Phase 4 (the ~30-40 helpers from T-008..T-017) in `src/firmware/org_ap_upgrader.py` and confirm every executable line carries a `# WHY:` inline comment. Add missing comments. Also confirm each helper has `logging.info(...)` on its first executable line and `logging.debug(...)` on its last executable line before return (FR-012). This task may be split into two review-friendly sub-tasks (`T-030a` covering Batch A/B, `T-030b` covering Batch C) if the diff exceeds 500 changed lines.
  - **Done when:** grep on each Phase-4 helper's body shows every executable line ends in `# WHY:` and each helper is bracketed by info-before / debug-after logging.
- [X] **T-031** Sweep every helper introduced in Phase 5 (the ~20-30 helpers from T-018..T-028) in `src/firmware/org_ap_upgrader.py` and confirm every executable line carries a `# WHY:` inline comment. Add missing comments. Confirm each helper has the info/debug bracket (except predicates `<=3` lines / CC `<=2`).
  - **Done when:** analyzer's inline-comment coverage on the file is `>=80%`; grep confirms info-before / debug-after brackets at every non-predicate helper.
- [X] **T-032** Sweep every remaining executable line in `src/firmware/org_ap_upgrader.py` that was NOT touched by Phases 3-5 (i.e. methods the analyzer never flagged, but which still contribute to the file-wide `>=80%` coverage threshold). Add `# WHY:` comments to those lines. The measurement is file-wide, so untouched code that was already commented stays; untouched code that had no comment picks one up now. This is the largest sub-task in the phase and may be split into `T-032a` / `T-032b` / `T-032c` grouped by class-method-region if the diff exceeds 500 changed lines.
  - **Done when:** `python -m tools.compliance_analyzer src/firmware/org_ap_upgrader.py` reports CONV-COMMENTS count 0 and inline-comment coverage `>=80%`.

**Checkpoint**: Analyzer reports zero findings across every rule bucket. Inline-comment coverage `>=80%`. Compliance score is 100.0 / A+. **The refactor's compliance work is complete.** MistHelper.py diff still empty.

---

## Phase 7: Logging + Hygiene Sweep (ASCII / Lazy Format / safe_input / Path Hygiene)

**Goal**: Guarantee every `logging.*` call is ASCII-only lazy-form. Guarantee every `input(...)` is `safe_input(..., context=...)`. Guarantee every filesystem path is `os.path.join` / `pathlib.Path`. Most of this hygiene was handled opportunistically in Phases 4-5; this phase is the audit sweep that catches anything missed.

**Independent Test**: The two Python one-liners below (ASCII scan + f-string scan) emit zero lines. `grep -nE "^\\s*[^#]*[^_a-zA-Z]input\\(" src/firmware/org_ap_upgrader.py` (excluding `safe_input`) returns nothing. Every `logging.*` call uses `%s` / `%d` lazy form.

```bash
python -c "import re,sys; s=open('src/firmware/org_ap_upgrader.py',encoding='utf-8').read(); [print(f'{i+1}: {l}') for i,l in enumerate(s.splitlines()) if not l.isascii()]"
python -c "import re,sys; s=open('src/firmware/org_ap_upgrader.py',encoding='utf-8').read(); [print(f'{m.start()}: {m.group()}') for m in re.finditer(r'logging\\.\\w+\\(f[\"\\'']', s)]"
```

- [X] **T-033** Audit every `logging.*(...)` and every `print(...)` call in `src/firmware/org_ap_upgrader.py` for non-ASCII characters per FR-013 and for f-string usage per FR-012. Replace emoji with ASCII markers (`[OK]`, `[FAIL]`, `[SKIP]`), replace curly quotes with straight, replace en/em-dash with `-`, replace non-ASCII arrows with `->`. Convert any `logging.info(f"... {x}")` to `logging.info("... %s", x)` (lazy form). Every edited string carries an updated `# WHY:` inline comment.
  - **Done when:** both Python one-liners emit zero lines; grep confirms no f-strings inside `logging.*` calls.
- [X] **T-034** Audit every `input(...)` call in `src/firmware/org_ap_upgrader.py`. Every remaining raw `input(...)` (Phases 4-5 wrapped the touched ones opportunistically; this sweeps the rest) is wrapped in `safe_input(..., context="org-ap-upgrader.<kebab-tag>")`. Grep-verify: `grep -nE "^\\s*[^#]*[^_a-zA-Z]input\\(" src/firmware/org_ap_upgrader.py` returns nothing (excluding `safe_input` matches). Also audit every filesystem path construction — replace any raw `/` or `\\` string concatenation with `os.path.join(...)` or `pathlib.Path(...)`, particularly around CSV output paths. Every edited call carries a `# WHY:` inline comment.
  - **Done when:** no raw `input(...)` remains in the file; every prompt is `safe_input(..., context=...)`; every user-facing filesystem path uses `os.path.join` / `pathlib.Path` (URL patterns like `/api/v1/orgs/{org_id}` are unaffected — those are mistapi paths, not filesystem paths).

**Checkpoint**: All ASCII / lazy-format / safe_input / path hygiene sweeps complete. Analyzer still at 100.0 / A+. MistHelper.py diff still empty.

---

## Phase 8: Verification Gates (Polish & Cross-Cutting Concerns)

**Purpose**: Final verification, artifact capture, and reviewer-friendly documentation updates. Executes each of the six standing-gate commands in order and drops all outputs to `specs/1006-org-ap-upgrader-compliance/artifacts/`.

- [X] **T-035** Run the final compliance analyzer gate: `python -m tools.compliance_analyzer src/firmware/org_ap_upgrader.py`. Save output to `specs/1006-org-ap-upgrader-compliance/artifacts/final_compliance_report.md`. Confirm score is **exactly 100.0**, grade is **A+**, and every rule bucket (`CONV-COMMENTS`, `CONV-NAME`, `STRUCT-BLOCKS`, `STRUCT-COMPLEXITY`, `STRUCT-LENGTH`, `STRUCT-NESTING`, `STRUCT-PARAMS`) reports 0 findings (FR-001, FR-002, FR-003, SC-001, SC-002, SC-003). Any single LOW-severity finding is a failure — no partial credit.
  - **Done when:** artifact file reports `Score: 100.0`, `Grade: A+`, and zero findings across every rule bucket.
- [X] **T-036** [P] Run the final ruff gate: `python -m ruff check src/firmware/org_ap_upgrader.py`. Save output to `specs/1006-org-ap-upgrader-compliance/artifacts/final_ruff.txt`. Confirm zero errors, zero warnings (FR-005).
  - **Done when:** artifact file records exit code 0 and empty output.
- [X] **T-037** [P] Run the final black + mypy + py_compile gate: `python -m py_compile src/firmware/org_ap_upgrader.py`, `python -m black --check src/firmware/org_ap_upgrader.py`, `python -m mypy --strict src/firmware/org_ap_upgrader.py`. Save exit codes + any stderr to `specs/1006-org-ap-upgrader-compliance/artifacts/final_toolchain.txt`. Confirm all three exit 0 (FR-004, SC-006).
  - **Done when:** artifact file records exit code 0 for all three tools.
- [X] **T-038** [P] Run the byte-identity gate: `git diff main..HEAD -- MistHelper.py` and save output to `specs/1006-org-ap-upgrader-compliance/artifacts/misthelper_diff.txt`. Confirm output is **empty** (SC-007, FR-018). Also run `grep -n "from src\.firmware\.org_ap_upgrader" MistHelper.py` and confirm the four expected lines at 20247, 20269, 20289, 20305 match the baseline capture from T-003.
  - **Done when:** artifact file is empty (zero bytes or one trailing newline); MistHelper.py callsite grep matches T-003 baseline exactly.
- [X] **T-039** [P] Run the four-callsite construction smoke: for each of the four MistHelper.py callsite shapes (11-kwarg at 20247, 9-kwarg at 20269, 5-kwarg with `org_id=""` at 20289, 3-kwarg with `org_id=""` at 20305), open a Python REPL with `MagicMock` for `apisession` and construct `OrgLevelAPFirmwareUpgrader(**shape_kwargs)`. Confirm all four constructions succeed with no exception. Save the transcript to `specs/1006-org-ap-upgrader-compliance/artifacts/callsite_smoke.txt` (contracts C-1 through C-6).
  - **Done when:** transcript shows all four constructions returning an `OrgLevelAPFirmwareUpgrader` instance; no `TypeError` / `ValueError` raised.
- [X] **T-040** [P] Run the constructor-contract negative smoke: exercise the seven failure modes from `contracts/constructor.md` "Failure-Mode Diagnostics" — positional call raises `TypeError`, unknown kwarg raises `TypeError`, `org_id=None` raises `TypeError`, `apisession=None` raises `ValueError`, non-callable `*_fn` raises `TypeError`, non-list `msp_privileges` raises `TypeError`, post-construction attribute mutation raises `FrozenInstanceError`. Save the transcript to `specs/1006-org-ap-upgrader-compliance/artifacts/constructor_negative_smoke.txt`.
  - **Done when:** transcript shows all seven negative cases raising the expected exception type with the expected diagnostic string.
- [X] **T-041** Perform the pytest smoke gate: `python -m pytest tests/unit/ -k org_ap_upgrader -v`. Expected outcome: zero tests collected (no pre-existing tests reference this module and NG-001 forbids adding new ones). Save output to `specs/1006-org-ap-upgrader-compliance/artifacts/final_pytest.txt`. If any tests are collected, all must pass — a failing test is a merge blocker.
  - **Done when:** artifact file confirms `no tests ran` OR every collected test passes (exit code 0).
- [X] **T-042** [P] Update `.github/copilot-instructions.md` between the `<!-- SPECKIT START -->` and `<!-- SPECKIT END -->` markers to reference `specs/1006-org-ap-upgrader-compliance/plan.md` as the active plan. Every edited line carries a `# WHY:` inline comment where the target file's convention allows.
  - **Done when:** file diff shows only lines between the SPECKIT markers changed; those lines reference the 1006 plan.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies. Can start immediately.
- **Phase 2 (Foundational — T-DATACLASS)**: Depends on Phase 1 complete. **BLOCKS ALL STRUCTURAL WORK.**
- **Phase 3 (Constructor migration)**: Depends on T-005 (T-DATACLASS) complete.
- **Phase 4 (STRUCT-LENGTH)**: Depends on Phase 3 complete. Every task in Phase 4 reads collaborators via the same `self.<attr>` names — the `_apply_config_to_attributes()` helper must land first so no other helper needs to change simultaneously.
- **Phase 5 (STRUCT-COMPLEXITY)**: Depends on Phase 4 complete. All eleven tasks (T-018..T-028) edit the same file and must run sequentially.
- **Phase 6 (CONV-COMMENTS sweep)**: Depends on Phase 5 complete — comment sweeps land on the fully-decomposed code, not the pre-refactor shape (otherwise every comment is thrown away when a method is split).
- **Phase 7 (Logging + hygiene sweep)**: Depends on Phase 6 complete.
- **Phase 8 (Verification)**: Depends on all Phases 1-7 complete. T-036 / T-037 / T-038 / T-039 / T-040 / T-042 can run in parallel because they are read-only against the primary file (or edit an unrelated file).

### T-DATACLASS Blocking Diagram

```text
                       T-005 (T-DATACLASS)
                              |
                              v
                    T-006, T-007 (Constructor)
                              |
                              v
                  T-008..T-017 (STRUCT-LENGTH x10)
                              |
                              v
                  T-018..T-028 (STRUCT-COMPLEXITY x11)
                              |
                              v
              T-029..T-032 (CONV-COMMENTS sweep)
                              |
                              v
                  T-033..T-034 (Logging + hygiene)
                              |
                              v
                  T-035..T-042 (Phase 8 verification)
```

### Within Each Phase

- No formal test-first requirement (no test file exists per NG-001).
- Helpers before orchestrator rewrite (e.g. within each Phase-4 task, add the four PCPP helpers before rewriting the orchestrator).
- After each task the six-command gate (see top of file) must pass.
- Analyzer score must climb monotonically or stay flat — never regress by more than one within-task step that is recovered by the next task.
- `git diff main..HEAD -- MistHelper.py` must be empty after every single task without exception.

### Parallel Opportunities

- T-001 / T-002 / T-003 / T-004 (baseline capture) can run in parallel — different artifact files.
- T-036 / T-037 / T-038 / T-039 / T-040 / T-042 (final verification gates + doc update) can run in parallel — read-only against the primary file (or edit an unrelated file).
- Everything else touches `src/firmware/org_ap_upgrader.py` and must serialize.

---

## Parallel Example: Phase 8 Verification Fan-Out

```bash
# After T-035 (analyzer 100.0 / A+ confirmed):

# Terminal 1 (ruff artifact):
Task: T-036 python -m ruff check src/firmware/org_ap_upgrader.py > artifacts/final_ruff.txt

# Terminal 2 (toolchain artifact):
Task: T-037 python -m py_compile src/firmware/org_ap_upgrader.py; python -m black --check src/firmware/org_ap_upgrader.py; python -m mypy --strict src/firmware/org_ap_upgrader.py > artifacts/final_toolchain.txt

# Terminal 3 (byte-identity artifact):
Task: T-038 git diff main..HEAD -- MistHelper.py > artifacts/misthelper_diff.txt

# Terminal 4 (constructor positive smoke):
Task: T-039 python -c "..." > artifacts/callsite_smoke.txt

# Terminal 5 (constructor negative smoke):
Task: T-040 python -c "..." > artifacts/constructor_negative_smoke.txt

# Terminal 6 (doc update):
Task: T-042 edit .github/copilot-instructions.md between SPECKIT markers
```

All six terminals converge to a passing six-command gate (analyzer 100.0 / A+, ruff clean, black clean, mypy --strict clean, py_compile 0, MistHelper.py diff empty) and a signed-off artifacts directory.

---

## Implementation Strategy

### MVP First — This Refactor Has No Intermediate-Grade MVP

Unlike a partial merge, spec FR-001 through FR-003 require exactly 100.0 / A+ with zero findings. **There is no ship-able intermediate state.** Phases 1-8 must all complete before the branch merges. The recommended incremental delivery within the same branch is:

1. Phase 1 (Setup) -> baseline captured. **Score 60.0 / D-.**
2. Phase 2 (T-DATACLASS) -> config dataclass exists. **Score ~62.**
3. Phase 3 (Constructor) -> `__init__` collapsed to `**cfg`. **Score ~65.** `__init__` no longer flagged, two `# pylint: disable` markers removed.
4. Phase 4 (STRUCT-LENGTH x10) -> all length offenders cleared. **Score ~78.**
5. Phase 5 (STRUCT-COMPLEXITY x11) -> all CC offenders cleared. **Score ~85-90.** Only CONV-COMMENTS remains.
6. Phase 6 (CONV-COMMENTS sweep) -> comment coverage >=80%. **Score 100.0 / A+.** Compliance work done.
7. Phase 7 (Logging + hygiene sweep) -> audit-clean. Score unchanged (100.0 / A+).
8. Phase 8 (Verification) -> artifacts captured. Score unchanged.

### Recommended Commit Boundaries

- One commit per phase: `refactor(org-ap-upgrader): phase 1 baseline`, `refactor(org-ap-upgrader): phase 2 T-DATACLASS`, ..., `refactor(org-ap-upgrader): phase 8 verification`. Eight commits total.
- OR: one commit per task if the reviewer prefers finer-grained review. Estimated 42 commits.
- The "grade A+" milestone commit is `refactor(org-ap-upgrader): phase 6 CONV-COMMENTS sweep` — the branch is ship-ready compliance-wise from that point, pending only the Phase-7 hygiene audit and Phase-8 verification artifacts.

### Sub-Task Splitting Convention

If a task's diff becomes unwieldy for review (rule of thumb: >500 changed lines or >5 methods touched), split it into `T-XXXa`, `T-XXXb`, etc. rather than renumbering the rest of the plan. Prime candidates for pre-emptive sub-splitting:

- **T-032** (comment sweep across untouched code): estimate ~100+ untouched executable lines needing `# WHY:`. Split into T-032a / T-032b / T-032c grouped by class-method-region if the diff exceeds 500 lines.
- **T-030** (comment audit across all Phase-4 helpers): estimate ~30-40 helpers. Split into T-030a (Batch A/B tasks T-008..T-013) and T-030b (Batch C tasks T-014..T-017).

---

## Anti-Patterns — EXPLICITLY BANNED

The following are **hard-banned** by this task list. Any occurrence is a merge blocker:

1. `# noqa`, `# type: ignore`, `# pragma: no cover` on any line the analyzer would otherwise flag (FR-015).
2. Analyzer threshold relaxation via config file, environment variable, or command-line flag (FR-001).
3. Wrapper / delegator / alias / shim helpers that forward to another function with no additional logic (FR-011).
4. **Any** change to `MistHelper.py` — not a comment, not a whitespace, not a blank line, not a docstring tweak (FR-018, SC-007). The **only** permitted diff on this branch is inside `src/firmware/org_ap_upgrader.py` (and optionally `.github/copilot-instructions.md` between SPECKIT markers at T-042).
5. Unicode or emoji in log strings, print strings, or any user-facing output (FR-013). ASCII only. Use `[OK]` / `[FAIL]` / `[SKIP]` / `->` markers.
6. f-strings inside `logging.*(...)` calls (FR-012). Lazy `%s` / `%d` form only.
7. Creating new test files under `tests/unit/` or `tests/integration/` (NG-001). The pytest gate is spot-grep only; if it finds nothing, that is a passing state.
8. Modifying the pre-existing `baseline_compliance_report.md` or `baseline_lint.txt` under `specs/1006-org-ap-upgrader-compliance/artifacts/` (spec directive).

If a task's diff would introduce any of items 1-8, the task is not complete and the diff must be reworked before proceeding.

---

## Notes

- Every task edits `src/firmware/org_ap_upgrader.py` unless otherwise noted. One exception: T-042 edits `.github/copilot-instructions.md` between the SPECKIT markers only. Baseline/verification tasks (T-001..T-004, T-035..T-041) write to `specs/1006-org-ap-upgrader-compliance/artifacts/`.
- Every task's success is measured against the standing six-command gate at the top of this file — plus the task's own "Done when:" line.
- No wrapper / delegator / shim helpers may be introduced (FR-011). If a PCPP slice would be a 1-line forward, inline it.
- Every executable line new or edited must carry `# WHY:` inline commentary (Constitution VI, AGENTS.md non-negotiable, FR-005).
- Every new operation must be bracketed by `logging.info` before / `logging.debug` after (Constitution VII, AGENTS.md non-negotiable, FR-012).
- All log strings must be ASCII-only lazy `%s` / `%d` form (FR-013). All `input(...)` calls must use `safe_input(..., context=...)` (opportunistically applied in Phases 4-5, swept in Phase 7). All filesystem paths must use `os.path.join(...)` or `pathlib.Path(...)`.
- No `# noqa`, `# type: ignore`, or `# pragma: no cover` markers may be added by this refactor on lines the analyzer would otherwise flag (FR-015). The pre-existing `# pylint: disable=too-many-arguments` (line 41) and `# pylint: disable=too-many-lines,logging-fstring-interpolation` (line 9) are **removed** by T-007 — no suppression remains on the class or module after Phase 3.
- The `OrgAPUpgraderConfig` dataclass lives in `src/firmware/org_ap_upgrader.py` (FR-009). No new module is created (NG-004).
- **Zero MistHelper.py diff** is the strictest constraint of this refactor. It is asserted by `git diff main..HEAD -- MistHelper.py` returning empty output after every single task. Any drift halts the refactor.
- Task IDs are gap-friendly. If a task needs to be split during implementation, assign `T-XXXa`, `T-XXXb` rather than renumbering.

**Total task count: 42.** Phase 1: 4 tasks. Phase 2: 1 task. Phase 3: 2 tasks. Phase 4: 10 tasks. Phase 5: 11 tasks. Phase 6: 4 tasks. Phase 7: 2 tasks. Phase 8: 8 tasks.
