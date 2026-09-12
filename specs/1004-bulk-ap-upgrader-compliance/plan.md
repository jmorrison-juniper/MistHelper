# Implementation Plan: Bulk AP Upgrader Compliance Refactor

**Branch**: `refactor/bulk-ap-upgrader-compliance` | **Date**: 2026-07-01 | **Spec**: `specs/1004-bulk-ap-upgrader-compliance/spec.md`
**Input**: Feature specification from `specs/1004-bulk-ap-upgrader-compliance/spec.md`

## Summary

Refactor `src/firmware/bulk_ap_upgrader.py` (1,673 lines, grade F / 50.0 / 62 violations) to grade B (>=80.0) by:

1. Collapsing the 10-parameter `__init__` into a `BulkAPUpgraderConfig` frozen dataclass so the constructor accepts at most 3 arguments (`self, org_id, apisession, config`) — or, per the recommendation in `research.md`, exactly one argument (`self, config`) with `org_id`/`apisession` folded into the config.
2. Decomposing `__init__`, `execute`, and the ten enumerated MEDIUM-severity offenders (`_select_strategy`, `_estimate_api_calls`, `_offer_additional_model_versions`, `_fetch_ap_model_families`, `_configure_auto_upgrade_schedule`, `_step11_write_results`, `_apply_version_selection`, `_upgrade_version_group`, `_log_upgrade_results`, plus `execute`) into <=25-line, <=5-block helpers using a shared decomposition pattern (see `research.md` R-3).
3. Applying `# WHY` inline comments to every executable line the refactor touches. Existing lines outside the touched range are left alone (avoids scope creep while still clearing the 80% coverage floor because the refactor will naturally touch the majority of the file).
4. Wrapping every I/O, mutation, or branch decision with `logging.info(...)` before / `logging.debug(...)` after per Constitution VII.
5. Renaming single-letter loop variables in touched code paths (Constitution II; FR-013).
6. Migrating the two known callers (`MistHelper.py:19796` thin wrapper; `tests/unit/test_bulk_ap_upgrader.py:69` `_make_upgrader` factory) to construct and pass `BulkAPUpgraderConfig` in the same commit as the constructor change.

## Technical Context

**Language/Version**: Python 3.13+ (per Constitution Technology & Compatibility Constraints)
**Primary Dependencies**: `mistapi` 0.59+ (session shape only, no new mistapi surface added), stdlib `dataclasses`, stdlib `logging`, stdlib `os.path`, `safe_input` utility (already imported via `_input_fn` injection)
**Storage**: N/A (refactor is code-shape only; no schema or file format changes)
**Testing**: `pytest` — existing suite at `tests/unit/test_bulk_ap_upgrader.py` (644 lines, 88.2 KB) is the primary regression harness. Acceptance is also `python -m tools.compliance_analyzer`, `python -m ruff check`, and `python -m py_compile`.
**Target Platform**: Cross-platform (Windows 11 dev, Linux container prod) — must remain path-safe via `os.path.join` (FR-010)
**Project Type**: Refactor of an existing single Python module inside a larger CLI/tool codebase. No new packages, no new modules unless a circular import forces it (FR-018 permits a separate module only under that specific justification, which does not apply here — everything stays in-file).
**Performance Goals**: No performance regression relative to pre-refactor. Constructor now allocates one dataclass instance instead of assigning 10 attributes directly; the cost is negligible (<1 microsecond at object creation).
**Constraints**: Every helper <=25 lines, <=5 params, <=5 logical blocks, <=5 cyclomatic complexity, <=4 nesting levels (FR-004, FR-005, FR-016). No wrappers/shims/delegators (FR-011). ASCII-only log strings (FR-008). `safe_input(context=...)` for every input (FR-009).
**Scale/Scope**: Single file, ~1,673 lines pre-refactor. Expected post-refactor line count: ~2,400-2,900 lines due to added inline comments and helper boilerplate. Total file length is uncapped by policy; only per-method size is capped.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluating this feature against each Core Principle:

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Five-Item Rule | PASS | Refactor is defined by this principle. Every extracted helper conforms to <=5 params, <=25 lines, <=5 blocks. FR-004 through FR-016 encode this. |
| II | Class-Based Architecture (No Wrappers) | PASS | The refactor stays inside `BulkAPFirmwareUpgrader`. FR-011 explicitly bans wrapper/delegator helpers. Loop variables renamed per FR-013. |
| III | Safety-First | PASS | FR-009 requires `safe_input(context=...)` for every `input(...)` call in the refactored file. No destructive-op semantics change (bulk AP upgrade is already inside the destructive-op envelope; the refactor does not add or remove a confirm gate). |
| IV | Full Deployment Pipeline | N/A at plan phase | Pipeline runs during `/speckit.implement`, not `/speckit.plan`. Plan documents that ruff, py_compile, compliance_analyzer, and pytest are the gates. |
| V | Observability & Logging | PASS | FR-007 requires `logging.info` before / `logging.debug` after every non-trivial operation. FR-008 mandates ASCII-only log strings. |
| VI | Inline Comments (NON-NEGOTIABLE) | PASS | FR-006 requires >=80% inline-comment coverage. Plan targets 100% coverage on every touched executable line (see research R-4). |
| VII | Action Logging (NON-NEGOTIABLE) | PASS | Same coverage as V. Every helper extracted during decomposition will get the info-before / debug-after pattern per FR-007. |

No violations. **Constitution Check PASSED.** No entries needed in the Complexity Tracking table.

## Project Structure

### Documentation (this feature)

```text
specs/1004-bulk-ap-upgrader-compliance/
├── plan.md              # This file
├── spec.md              # Written before /speckit.plan
├── research.md          # Phase 0 output — decisions on config dataclass, caller migration, decomposition patterns
├── data-model.md        # Phase 1 output — BulkAPUpgraderConfig dataclass shape
├── quickstart.md        # Phase 1 output — how a reviewer verifies the refactor
├── contracts/
│   └── constructor.md   # Phase 1 output — pre/post constructor signature contract
├── checklists/          # Pre-existing (unchanged by this plan)
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
└── firmware/
    └── bulk_ap_upgrader.py         # SOLE FILE MODIFIED by this refactor (FR-018)

tests/
└── unit/
    └── test_bulk_ap_upgrader.py    # Updated: _make_upgrader factory now builds BulkAPUpgraderConfig

MistHelper.py                       # Updated: thin wrapper at line 19783 now builds BulkAPUpgraderConfig

src/firmware/firmware_manager.py    # NOT MODIFIED — line 1463 calls the MistHelper.py thin wrapper,
                                    # not the impl class directly, so it is insulated from the
                                    # signature change by the wrapper.
```

**Structure Decision**: Single-project layout. The refactor is scoped to one implementation file (`src/firmware/bulk_ap_upgrader.py`) plus its two direct callers (`MistHelper.py`, `tests/unit/test_bulk_ap_upgrader.py`). No new files are created inside `src/`. The `BulkAPUpgraderConfig` dataclass lives in the same module (FR-018) — there is no circular-import risk because the dataclass has no imports of its own beyond `dataclasses.dataclass` and the type aliases already at the top of the file.

## Phase 0 Deliverables

Written to `research.md`:

- **R-1**: Backward-compat approach — recommendation and rationale (config-object migration vs. preserved signature).
- **R-2**: `__init__` helper decomposition pattern (3 helpers: config unpacking, state initialization, session context).
- **R-3**: `execute` decomposition — 3 phase helpers (`_run_precheck_steps`, `_run_planning_steps`, `_run_execution_steps`) plus preserved 11-step method identity.
- **R-4**: Shared long-method decomposition pattern for the remaining 8 MEDIUM offenders (`_select_strategy`, `_estimate_api_calls`, etc.).
- **R-5**: Inline-comment strategy — coverage math showing why 80% floor is reachable without touching untouched lines.
- **R-6**: Testing strategy — existing test file at `tests/unit/test_bulk_ap_upgrader.py` provides regression coverage; compliance analyzer + py_compile + ruff are the additional acceptance gates. Correction to the user's stated assumption: the test file DOES exist (`tests/unit/`, not `tests/`).

## Phase 1 Deliverables

- **`data-model.md`**: `BulkAPUpgraderConfig` frozen dataclass definition, field-by-field mapping from the current 10 constructor parameters, and validation rules.
- **`contracts/constructor.md`**: Pre-refactor and post-refactor constructor signatures side by side, along with the two known caller-site changes.
- **`quickstart.md`**: Step-by-step verification recipe a reviewer runs on the refactored branch (analyzer, ruff, py_compile, pytest, manual REPL smoke).
- **Agent context update**: `.github/copilot-instructions.md` plan reference updated between `<!-- SPECKIT START -->` and `<!-- SPECKIT END -->` markers to point at this plan file.

## Complexity Tracking

*No entries — Constitution Check passed without violations.*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                             |
