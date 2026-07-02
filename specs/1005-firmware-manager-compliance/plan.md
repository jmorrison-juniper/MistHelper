# Implementation Plan: Firmware Manager Compliance Refactor

**Branch**: `refactor/firmware-manager-compliance` | **Date**: 2026-07-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/1005-firmware-manager-compliance/spec.md`

## Summary

Lift `src/firmware/firmware_manager.py` from **51.0 / F (82 violations)** to **100.0 / A+ (zero violations)** through a real structural refactor while preserving exact observable behavior for the six MistHelper.py callsites of `FirmwareManager.create(apisession, org_id)`. Concretely:

1. Collapse the eight-parameter `__init__` into a single positional `FirmwareManagerConfig` frozen `slots=True` dataclass (resolves the sole STRUCT-PARAMS violation and enables downstream simplifications).
2. Decompose the 36 STRUCT-LENGTH offenders — including four HIGH-severity ones (`check_firmware_upgrade_status`, `_continuous_monitoring_mode`, `_upgrade_ap_firmware_by_gateway_template`, `_execute_msp_upgrade_plan`) — via the PCPP pattern (Prepare / Compute / Present / Persist) so every helper is `<=25` lines and `<=5` blocks.
3. Split the 28 STRUCT-COMPLEXITY hotspots (top five all with CC=9–10) into linear helpers whose branching factor is `<=5`.
4. Flatten the two STRUCT-NESTING offenders (lines 750, 1740) using early-return guards.
5. Rename the three CONV-NAME loop variables `r` at lines 1364/1373/1381 to descriptive names (`result`, `record`, `report_row` depending on context).
6. Add `# WHY: <purpose>` inline comments to every executable line, raising coverage from **6.3% -> >=80%** (spec target 90%+).
7. Wrap every action method with `logging.info(...)` at entry and `logging.debug(...)` before return, using ASCII-only lazy `%s`/`%d` form (never f-strings inside logging calls).
8. Preserve the module-global side effects (`msp_privileges`, `apisession`, `org_id`, `PROGRESS_EMITTER`) via a private `_bind_module_globals(config)` helper called once from the new `__init__`.
9. Update `MistHelper.py` factory body at lines 18791-18807 only (the sole permitted diff outside the target file per FR-011) to construct a `FirmwareManagerConfig` and pass it to the class constructor.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility Constraints)
**Primary Dependencies**: `mistapi` (existing), `dataclasses` (stdlib), `logging` (stdlib) — **no new deps** (NG-002)
**Storage**: N/A (no persistent state introduced; existing CSV outputs unchanged)
**Testing**: `pytest` for optional smoke test only — **no new test files** (NG-001). `python -m py_compile`, `ruff`, and `tools.compliance_analyzer` are the primary gates.
**Target Platform**: CLI (MistHelper.py menu 196 primary launcher, plus five secondary callsites)
**Project Type**: Single-project refactor within existing MistHelper codebase.
**Performance Goals**: No behavior change — identical prompt sequence, log lines, and API call cadence for menu 196 vs. pre-refactor branch (FR-017).
**Constraints**: Only two files touched: `src/firmware/firmware_manager.py` (full rewrite permitted) and `MistHelper.py` lines 18791-18807 (factory wrapper body only). Total LOC estimated to grow from **2450 -> ~4000** due to inline comment coverage + helper decomposition (NG-003 permits growth for compliance).
**Scale/Scope**: 82 functions, 1348 executable lines, six MistHelper.py callsites (18795 import, 19809, 22097, 22154, 22237, 22246 usage), zero pre-existing unit tests for this module.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How Refactor Complies | Status |
|-----------|-----------------------|--------|
| I. Five-Item Rule (menu safety) | Menu 196 (and secondary callers) unchanged; only internals refactored. Prompt sequence identical (FR-017). | PASS |
| II. Class-Based Architecture | Reinforces class boundary — all helpers become methods on `FirmwareManager` receiving a single `FirmwareManagerConfig`. | PASS |
| III. Safety-First (dry-run + user confirm) | All existing dry-run branches and `safe_input(context=...)` prompts preserved verbatim (FR-016). | PASS |
| IV. Deployment Pipeline | No changes to `deploy_release.py` or SSH surface. | PASS (N/A) |
| V. Observability | `logging.info` before every action, `logging.debug` after — expansion vs. current 6.3% coverage (FR-007, FR-008). | PASS |
| VI. Inline Comments (non-negotiable) | Every executable line receives a `# WHY: ...` comment. Coverage target >=90% (FR-006, SC-009). | PASS |
| VII. Action Logging (non-negotiable) | Lazy-form `%s`/`%d`, ASCII-only strings, no f-strings inside logging calls (FR-008). | PASS |

**Constitution gate: all seven principles PASS.** No violations, no complexity justifications required.

## Project Structure

### Documentation (this feature)

```text
specs/1005-firmware-manager-compliance/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/
│   └── constructor.md   # Phase 1 output — the new __init__ contract
├── spec.md              # Feature specification (existing)
├── checklists/
│   └── requirements.md  # Quality checklist (existing)
├── artifacts/
│   └── baseline_compliance_report.md   # F=51.0 baseline snapshot (existing)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created here)
```

### Source Code (repository root)

Only two files are modified — no additions, no deletions:

```text
src/firmware/
└── firmware_manager.py             # FULL REWRITE — 2450 -> ~4000 LOC, F -> A+

MistHelper.py                       # Lines 18791-18807 ONLY (FirmwareManager.create body)
```

**Structure Decision**: This is a **surgical single-file refactor** with one insulation-layer diff. No new modules, no new packages, no new test files (NG-001). The prior-art `bulk_ap_upgrader.py` refactor at `specs/1004-bulk-ap-upgrader-compliance/` is the exact structural template.

## Phase 0 Deliverables (research.md)

Six research items resolve every open question before design:

- **R-1**: Backward-compat strategy for the eight-parameter constructor — Options A (kwargs-still-accepted), B (dual-mode), C (config-object, chosen). Rationale: matches 1004 precedent; only the factory wrapper needs to change.
- **R-2**: `__init__` decomposition — how the module-global side effects (`msp_privileges`, `apisession`, `org_id`, `PROGRESS_EMITTER`) are re-bound from the config via a private `_bind_module_globals(config)` helper.
- **R-3**: `execute`-style entry-point decomposition — four HIGH-severity STRUCT-LENGTH offenders (`check_firmware_upgrade_status` 90+ lines, `_continuous_monitoring_mode` 90+ lines, `_upgrade_ap_firmware_by_gateway_template` 90+ lines, `_execute_msp_upgrade_plan` 90+ lines) each split into `<=25`-line PCPP helpers.
- **R-4**: PCPP pattern (Prepare / Compute / Present / Persist) applied to the remaining 32 MEDIUM-severity STRUCT-LENGTH offenders and the 28 STRUCT-COMPLEXITY hotspots (CC 6-10).
- **R-5**: Inline-comment strategy — `# WHY: <intent>` on every executable line, target coverage >=90% (spec SC-009).
- **R-6**: Testing strategy — no new test files (NG-001); analyzer + ruff + optional REPL constructor smoke as sole gates.
- **R-7**: STRUCT-NESTING flattening — two offenders at lines 750 and 1740 converted via early-return guards.
- **R-8**: CONV-NAME loop-variable renames — three `for r in ...` sites at lines 1364/1373/1381 renamed to intent-revealing names.
- **R-9**: Six-callsite factory-wrapper insulation — grep confirms all callers go through `FirmwareManager.create(apisession, org_id)`, so only the wrapper body needs to change (FR-011).

**Output**: `research.md` with all NEEDS CLARIFICATION resolved.

## Phase 1 Deliverables

- `data-model.md` — the frozen `slots=True` `FirmwareManagerConfig` dataclass definition, its field-mapping table from the current 8-parameter constructor, validation rules, and state transitions (none — the object is immutable after construction).
- `contracts/constructor.md` — pre/post signature contract, contract invariants (C-1 through C-6), and the exact before/after diff for `MistHelper.py` lines 18791-18807.
- `quickstart.md` — reviewer-facing 6-step verification recipe (py_compile+ruff, analyzer 100.0/A+, factory-wrapper smoke, comment-coverage spot check, logging-pattern spot check, REPL constructor smoke).
- Agent context update — insert plan reference into `.github/copilot-instructions.md` between `<!-- SPECKIT START -->` and `<!-- SPECKIT END -->` markers.

**Output**: `data-model.md`, `contracts/constructor.md`, `quickstart.md`, updated agent context.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No Constitution violations. Table intentionally left empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
