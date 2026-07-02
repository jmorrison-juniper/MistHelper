# Implementation Plan: Org AP Upgrader Compliance Refactor

**Branch**: `refactor/org-ap-upgrader-compliance` | **Date**: 2026-07-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/1006-org-ap-upgrader-compliance/spec.md`

## Summary

Lift `src/firmware/org_ap_upgrader.py` from **60.0 / D- (27 violations)** to **100.0 / A+ (zero violations)** through a structural refactor that preserves exact observable behavior for the four MistHelper.py lazy-import callsites at lines 20247, 20269, 20289, and 20305. Concretely:

1. Introduce an `OrgAPUpgraderConfig` frozen `slots=True` `kw_only=True` dataclass carrying the 11 current constructor parameters as fields, with `__post_init__` validation (non-empty `org_id`, callable-or-None hooks, list/dict shape checks for `msp_privileges` / `selected_msp`, boolean coercion for `dry_run`). This resolves the sole **STRUCT-PARAMS** violation on `__init__` (line 41, 11 params, limit 5).
2. Reshape `OrgLevelAPFirmwareUpgrader.__init__` to accept `**cfg` and internally build the config via `OrgAPUpgraderConfig(**cfg)`, keeping the 4 MistHelper.py callsites byte-identical (all four call with `org_id=..., apisession=..., ...` kwargs). Remove the existing `# pylint: disable=too-many-arguments` — no suppressions needed post-refactor.
3. Decompose the **11 STRUCT-LENGTH** offenders (`__init__`, `_execute_msp_mode`, `_confirm_msp_orgs`, `_execute_org_upgrades`, `_select_orgs_from_msp`, `_step1_select_site_scope`, `_fetch_org_aps`, `_apply_version_selection`, `_configure_canary_phases`, `_execute_upgrades`, `_process_upgrade_response`) using the **PCPP pattern** (Prepare / Compute / Present / Persist) plus phase helpers (`_msp_phase_*`, `_org_phase_*`, `_canary_phase_*`, `_upgrade_phase_*`).
4. Reduce the **14 STRUCT-COMPLEXITY** offenders (CC 6-7 across `run`, `_fetch_msp_orgs`, `_print_msp_summary`, `_fetch_org_aps`, `_get_org_inventory`, `_fetch_site_aps`, `_build_model_version_mapping`, `_organize_by_version`, `_step6_configure_upgrade`, `_parse_time_input`, `_try_parse_after`, `_parse_canary_phase_values`, `_print_dry_run_entry`, `_process_upgrade_response`) via dispatch tables for the parser trio and guard-clause helpers for the print/organize/build functions.
5. Lift **inline comment coverage from 16.0% to >=80%** by attaching `# WHY: <intent>` to every executable line, resolving the sole **CONV-COMMENTS** high violation.
6. Wrap every observable operation with `logging.info` before / `logging.debug` after, using ASCII-only lazy `%s`/`%d` form.
7. Keep MistHelper.py lines 20237-20314 (docstring plus the four `from src.firmware.org_ap_upgrader import ... as _Impl` shims and their `_Impl(...)` call blocks) **byte-identical** — no callsite diff outside the target module.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility Constraints)
**Primary Dependencies**: `mistapi` (existing), `dataclasses` (stdlib), `logging` (stdlib), `datetime` (stdlib), `re` (stdlib) — **no new deps** (NG-002).
**Storage**: N/A (no persistent state introduced; existing CSV outputs unchanged).
**Testing**: existing pytest suite; **no new test files** required (spec allows regression-only testing). `python -m py_compile`, `ruff check`, `black --check`, `mypy --strict`, and `tools.compliance_analyzer` are the primary gates (SC-004, SC-005).
**Target Platform**: CLI (MistHelper.py org-level AP upgrader menu path, four lazy-import shims).
**Project Type**: Single-file surgical refactor within the existing MistHelper codebase.
**Performance Goals**: No behavior change — identical prompt sequence, log lines, and Mist API payloads for every entry point vs. `main` HEAD (FR-003, SC-008).
**Constraints**: Only one file modified — `src/firmware/org_ap_upgrader.py`. MistHelper.py stays untouched (FR-018, SC-007). Total LOC estimated to grow from **2393 -> ~3800** due to `# WHY:` comment coverage plus helper decomposition (spec permits growth for compliance).
**Scale/Scope**: 157 functions in one class (`OrgLevelAPFirmwareUpgrader`), 27 baseline violations, 4 MistHelper.py callsites, zero direct consumers outside MistHelper.py.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How Refactor Complies | Status |
|-----------|-----------------------|--------|
| I. Five-Item Rule (menu safety) | Menu entry points unchanged; only class internals refactored. Prompt sequence byte-identical (FR-003). | PASS |
| II. Class-Based Architecture | Reinforces class boundary — every helper becomes a method on `OrgLevelAPFirmwareUpgrader` reading `self._config`. | PASS |
| III. Safety-First (dry-run + user confirm) | All existing dry-run branches (`self.dry_run`) and `safe_input(context=...)` prompts preserved verbatim (FR-014). | PASS |
| IV. Deployment Pipeline | No changes to `deploy_release.py` or SSH surface. | PASS (N/A) |
| V. Observability | `logging.info` before every action, `logging.debug` after — expansion vs. current sparse coverage (FR-012). | PASS |
| VI. Inline Comments (non-negotiable) | Every executable line receives a `# WHY: ...` comment. Coverage target >=80% (FR-005, SC-002). | PASS |
| VII. Action Logging (non-negotiable) | Lazy-form `%s`/`%d`, ASCII-only strings, no f-strings inside logging calls (FR-012, FR-013). | PASS |

**Constitution gate: all seven principles PASS.** No violations, no complexity justifications required.

## Project Structure

### Documentation (this feature)

```text
specs/1006-org-ap-upgrader-compliance/
|-- plan.md              # This file (/speckit.plan command output)
|-- research.md          # Phase 0 output (/speckit.plan command)
|-- data-model.md        # Phase 1 output (/speckit.plan command)
|-- contracts/
|   `-- constructor.md   # Phase 1 output — the new __init__ contract
|-- spec.md              # Feature specification (existing)
|-- checklists/          # (empty — no additional quality checklist required)
`-- artifacts/
    |-- baseline_compliance_report.md   # 60.0 / D- baseline snapshot (existing)
    `-- baseline_lint.txt               # baseline lint state (existing)
```

Note: no `tasks.md` and no `quickstart.md` are produced by this plan command; the user's directive is plan-only.

### Source Code (repository root)

Only one file is modified — no additions, no deletions, no MistHelper.py diff:

```text
src/firmware/
`-- org_ap_upgrader.py             # FULL REWRITE — 2393 -> ~3800 LOC, D- -> A+

MistHelper.py                      # UNCHANGED (four lazy imports at 20247/20269/20289/20305 stay byte-identical)
```

**Structure Decision**: This is a **surgical single-file refactor**. Unlike the 1005 firmware-manager pattern (which permitted a single-block factory-body diff in MistHelper.py at lines 18791-18807), here the callsite constraint is stricter: **zero MistHelper.py diff**. The class constructor must therefore continue to accept the same kwargs shape the four callsites already pass. This drives the `__init__(self, **cfg)` design decision documented in `research.md` R-1.

## Phase 0 Deliverables (research.md)

Nine research items resolve every open question before design:

- **R-1**: Constructor decomposition strategy — three options considered (config-object-only breaking change; dual-mode; kwargs-passthrough with internal config build). Selected: kwargs-passthrough — preserves the four MistHelper.py callsites byte-identical while collapsing formal parameter count under the analyzer threshold.
- **R-2**: `OrgAPUpgraderConfig` field roster — all 11 current constructor parameters map 1:1 to config fields. Justification for holding runtime references (mistapi session, injected callables) inside a `frozen=True` dataclass: freezing prevents reassignment of the reference; the underlying objects remain mutable at their own contract, which matches pre-refactor behavior.
- **R-3**: PCPP decomposition for the 11 STRUCT-LENGTH offenders — one uniform pattern (Prepare / Compute / Present / Persist), applied to `__init__` (state init already delegated to three `_init_*_state` helpers; extend to config binding), `_execute_msp_mode`, `_confirm_msp_orgs`, `_execute_org_upgrades`, `_select_orgs_from_msp`, `_step1_select_site_scope`, `_fetch_org_aps`, `_apply_version_selection`, `_configure_canary_phases`, `_execute_upgrades`, `_process_upgrade_response`.
- **R-4**: Phase helpers for MSP / org / canary / upgrade flows — extracted from `_execute_msp_mode` (`_msp_phase_*`), `_execute_org_upgrades` (`_org_phase_*`), `_configure_canary_phases` (`_canary_phase_*`), `_execute_upgrades` (`_upgrade_phase_*`).
- **R-5**: Dispatch tables for the parser trio — `_parse_time_input` (CC 7), `_try_parse_after` (CC 6), `_parse_canary_phase_values` (CC 7) each get a `{prefix: handler_fn}` lookup dict that collapses their chain of `if / elif` branches to a single dispatch.
- **R-6**: Guard-clause helpers for the print/organize/build trio — `_organize_by_version` (CC 7), `_build_model_version_mapping` (CC 6), `_print_msp_summary` (CC 6), `_print_dry_run_entry` (CC 6) get their branching lifted into small predicate helpers (`_should_include_version`, `_row_has_target`, etc.) so the caller drops to CC <= 5.
- **R-7**: Inline-comment strategy — `# WHY: <intent>` on every executable line, target coverage >=80% (spec FR-005 / SC-002). Reference implementation matches the 1005 pattern.
- **R-8**: Logging convention — `logging.info` at each phase-helper entry, `logging.debug` at exit; ASCII-only strings; lazy `%s`/`%d` formatting; no f-strings inside `logging.*` calls (FR-012, FR-013).
- **R-9**: Four-callsite byte-identity verification — grep `MistHelper.py` for `from src.firmware.org_ap_upgrader` and confirm the exact set at lines 20247, 20269, 20289, 20305 remains unchanged. Diff test: `git diff main..HEAD -- MistHelper.py` must show zero lines touched in the 20237-20314 range (SC-007).

**Output**: `research.md` with all NEEDS CLARIFICATION resolved.

## Phase 1 Deliverables

- `data-model.md` — the frozen `slots=True` `kw_only=True` `OrgAPUpgraderConfig` dataclass definition, its 11-field mapping table from the current constructor, `__post_init__` validation rules, and immutability contract.
- `contracts/constructor.md` — pre-/post-refactor `__init__` signature contract, C-1 through C-6 invariants, and the byte-identity proof for the four MistHelper.py callsites (nothing changes outside `src/firmware/org_ap_upgrader.py`).
- Agent context update — insert plan reference into `.github/copilot-instructions.md` between `<!-- SPECKIT START -->` and `<!-- SPECKIT END -->` markers.

**Output**: `data-model.md`, `contracts/constructor.md`, updated agent context.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No Constitution violations. Table intentionally left empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
