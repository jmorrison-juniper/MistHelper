# Phase 1 Data Model: Hot-Functions Bounded Bundle

**Feature**: `specs/1012-misthelper-refactor-hot-functions/`
**Date**: 2026-07-06

This document captures the entities the PR operates on. These are not runtime data structures — they are refactor entities (source-code objects the PR reads, writes, moves, or deletes). Each entity carries: name, purpose, identifying fields, invariants preserved by the PR, and validation rules the PR verifies before merge.

---

## Entity: Extraction Candidate

Represents a single symbol targeted for a code-organization change.

**Fields**:

- `symbol_name` — e.g., `is_debug_mode`, `execute_with_connection_pool_management`, `tqdm`.
- `kind` — one of `function` (Actions 2 and 3), `import_fallback` (Action 1).
- `source_file` — always `MistHelper.py` for this initiative.
- `source_line_range` — e.g., `318-320` or `7503-7576` or `635`.
- `caller_count` — 12 (Action 2 primary target), 7 (Action 3), 0 (Action 2 wrapper).
- `action_id` — `SC-001`, `SC-002`, or `SC-003` from the spec.

**Invariants**:

- Every extraction candidate has an audited caller list (from the analyzer catalog and validated by grep) before the PR opens.
- Every extraction candidate maps to exactly one target (class or skip-pin), not multiple.
- No extraction candidate belongs to `SKIP_ALWAYS` unless the action is Action 1 (which pins rather than extracts).

**Validation rules**:

- `caller_count` for Action 2 primary = 12; for Action 3 = 7; for Action 2 wrapper = 0 (grep-audited before delete).
- `source_line_range` is verified against the analyzer's fresh output; drift within tolerance is acceptable (per FR-010 carry-forward).

---

## Entity: Skip-Pinned Symbol

Represents a symbol the PR marks as intentionally not extracted (Action 1).

**Fields**:

- `symbol_name` — `tqdm` (Action 1 target).
- `source_file` — `MistHelper.py`.
- `source_line` — 635.
- `pin_mechanism` — one of `analyzer_skip_flag`, `source_note_only`.
- `rationale` — free text: "Fallback shim bootstrap-critical for `GlobalImportManager` rebind pattern."

**Invariants**:

- The mandatory NOTE breadcrumb (extraction template variant, referencing the spec file for context) is present at `MistHelper.py:635` regardless of `pin_mechanism`.
- The symbol's source code is unchanged by the PR (skip-pin is metadata-only).

**Validation rules**:

- SC-014 grep `grep -R "specs/1012-misthelper-refactor-hot-functions/spec.md" MistHelper.py` returns a hit at line ~635.
- The tqdm fallback shim at `MistHelper.py:635` is byte-identical before and after the PR.

---

## Entity: Target Module

Represents a new file the PR creates under `src/refactors/`.

**Fields**:

- `path` — `src/refactors/is_debug_mode.py` or `src/refactors/connection_pool_executor.py`.
- `contains_class` — `IsDebugMode` or `ConnectionPoolExecutor`.
- `member_count` — 1 (Action 2) or 4 (Action 3: 1 public + 3 private static methods).
- `compliance_grade` — must be `A+/100` at merge.
- `logging_convention` — ASCII-only, `%s`-formatted, `[EXECUTE]/[SUCCESS]/[FAILURE]` prefix preserved from origin.

**Invariants**:

- Every target module has a module docstring explaining the extraction rationale and referencing the spec.
- Every target module uses `from __future__ import annotations` for forward-ref compatibility (matches 1011 convention).
- Every target module lands with inline comments every 5-10 lines (Constitution VI, NON-NEGOTIABLE).
- No target module uses `input()`; where user prompts are needed the origin uses `safe_input()` (neither Action 2 nor Action 3 prompt, so this is vacuously satisfied).

**Validation rules**:

- `python -m tools.compliance_analyzer src/refactors/is_debug_mode.py` reports `A+ / 100`.
- `python -m tools.compliance_analyzer src/refactors/connection_pool_executor.py` reports `A+ / 100`.
- Aggregate compliance snapshot at `data/full_repo_compliance_current.md` stays `>=99.6/A+`.

---

## Entity: Target Class

Represents the class-body seam inside a target module.

**Fields**:

- `class_name` — `IsDebugMode` or `ConnectionPoolExecutor`.
- `method_names` — `["check"]` (Action 2) or `["execute", "_pool_setup", "_pool_teardown", "_pool_error_handler"]` (Action 3 — exact private names carried from origin).
- `decorator` — always `@staticmethod` for every method (per Decision 2, research.md).
- `preserves_signature` — every method's `(args, kwargs) -> return` matches the origin's exact signature.

**Invariants**:

- Every method is `@staticmethod` — no `self`, no `cls`.
- Every public method (`check`, `execute`) matches the origin function's byte-for-byte behavior (validated by the CI integration suites).
- Every private method (`_pool_*`) is only called by `execute()` inside the same class body.

**Validation rules**:

- `mypy` on the new module produces zero errors.
- Callsite rewrites at all 12 (Action 2) or 7 (Action 3) sites parse and type-check.

---

## Entity: Callsite

Represents one location in the codebase that calls one of the two extracted callables.

**Fields**:

- `file` — `MistHelper.py` (majority), `src/gateway/gateway_export_utils.py`, `src/gateway/gateway_stats_exporter.py`.
- `line_number` — original line before PR (may shift within tolerance during rewrite).
- `original_call` — `is_debug_mode()` or `execute_with_connection_pool_management(...)`.
- `rewritten_call` — `IsDebugMode.check()` or `ConnectionPoolExecutor.execute(...)`.
- `import_added` — the target class must be imported in the caller's file (validated).

**Invariants**:

- Every callsite is rewritten in the same PR as the extraction (FR-003 — no wrapper shims left behind).
- Every rewritten callsite preserves the original argument list and keyword arguments verbatim.
- Every caller file that previously did not import from `src.refactors.is_debug_mode` or `src.refactors.connection_pool_executor` gains the appropriate import statement.

**Validation rules**:

- Post-PR `grep -R "is_debug_mode()" MistHelper.py src/` returns zero hits.
- Post-PR `grep -R "execute_with_connection_pool_management(" MistHelper.py src/` returns zero hits.
- Post-PR `python -c "import MistHelper"` succeeds (import-time smoke).

---

## Entity: DI Slot (Dependency-Injection Slot)

Represents one of the two DI slot names being renamed across five naming layers.

**Fields**:

- `old_name` — `is_debug_mode_fn` or `connection_pool_fn`.
- `new_name` — `check_fn` or `execute_fn`.
- `occurrence_count` — 6 for `is_debug_mode_fn`, 6 for `connection_pool_fn` (both across 5 naming layers; canonical NOTE breadcrumb lands on the module-level slot only — the other 5 occurrences per cluster are silent renames).
- `naming_layers_touched` — each occurrence exists at one of these five layers:
  1. Module-level slot declaration (e.g., `_deps.py` module scope)
  2. Dataclass field name
  3. `global <name>` list inside a function
  4. Assignment LHS or RHS
  5. Kwarg key in a function call

**Invariants**:

- Every occurrence is renamed atomically. Zero old-name occurrences survive the PR.
- Exactly ONE canonical rename NOTE lands per DI cluster, at the module-level slot declaration, using the pinned template `# NOTE: renamed from <bare-old-symbol>; wiring source <new-callable> at MistHelper.py:<line>.` (where `<bare-old-symbol>` is `is_debug_mode` or `execute_with_connection_pool_management`, NOT the `_fn` suffix form). The other 5 rename occurrences per cluster are silent renames.
- The wiring source is always the extracted class's static method (`IsDebugMode.check` or `ConnectionPoolExecutor.execute`) — not the original function name.

**Validation rules**:

- Post-PR `grep -R "is_debug_mode_fn" src/ MistHelper.py` returns zero hits.
- Post-PR `grep -R "connection_pool_fn" src/ MistHelper.py` returns zero hits.
- Post-PR `grep -R "renamed from is_debug_mode" src/` returns exactly 1 hit (canonical NOTE at site_export_utils.py:32).
- Post-PR `grep -R "renamed from execute_with_connection_pool_management" src/` returns exactly 1 hit (canonical NOTE at _deps.py:18).

---

## Entity: Breadcrumb

Represents one mandatory NOTE inserted by the PR.

**Fields**:

- `template_kind` — one of `extraction_deletion`, `di_rename`.
- `site_file` — the file the NOTE is inserted into.
- `site_line` — approximate line (drift within tolerance is OK; grep audit is line-agnostic).
- `template_string` — the exact pinned template from spec FR-024:
  - Extraction/deletion: `# NOTE: <symbol> extracted to <new-location>. See specs/1012-misthelper-refactor-hot-functions/spec.md.`
  - DI rename: `# NOTE: renamed from <old-name>; wiring source <new-callable> at MistHelper.py:<line>.`
- `placeholder_values` — the runtime-substituted values for `<symbol>`, `<new-location>`, `<old-name>`, `<new-callable>`, `<line>`.

**Invariants**:

- Every extraction site has exactly one extraction/deletion breadcrumb.
- Every rename site has exactly one DI-rename breadcrumb.
- Template strings match byte-for-byte (except placeholder substitutions).

**Validation rules**:

- SC-014 grep audit: `grep -R "specs/1012-misthelper-refactor-hot-functions/spec.md" src/ MistHelper.py` returns exactly the count enumerated in plan.md's Edit Surface manifest (3 extraction breadcrumbs — Action 1 at MistHelper.py:635, Action 2 at delete site, Action 3 at delete site).
- SC-014 grep audit: `grep -R "renamed from" src/ MistHelper.py` returns exactly 2 hits (1 for `is_debug_mode` canonical NOTE at site_export_utils.py:32, 1 for `execute_with_connection_pool_management` canonical NOTE at _deps.py:18).

---

## Entity: Compliance Baseline

Represents the repo-wide compliance snapshot that must be preserved.

**Fields**:

- `snapshot_file` — `data/full_repo_compliance_current.md`.
- `baseline_grade` — `>=99.6/A+` (established by 1010, preserved through 1011).
- `pylint_score` — `>=8.74/10` (non-regressing per FR-011).
- `affected_file_grades` — every file touched by the PR must land `A+/100` if it was `A+/100` before; every new file must land `A+/100`.

**Invariants**:

- Pre-existing A+ files stay A+ (no regressions on existing modules).
- Both new files (`is_debug_mode.py`, `connection_pool_executor.py`) land A+/100.
- `MistHelper.py` compliance is non-regressing (the PR shrinks the file, so compliance should improve or match).

**Validation rules**:

- `python -m tools.compliance_analyzer --repo-wide` on post-PR head reports `>=99.6/A+`.
- `pylint MistHelper.py src/` reports `>=8.74/10`.
- The affected-file table in the PR body enumerates every file grade before/after.

---

## Cross-Entity Relationships

```
ExtractionCandidate --produces--> TargetModule --contains--> TargetClass --exposes--> Method(@staticmethod)
                                                                                          ^
                                                                                          |
Callsite ----------------------------------------------------------------------------- calls
                                                                                          
DISlot --carries new wiring reference to--> Method(@staticmethod)

Breadcrumb --documents--> {ExtractionCandidate, DISlot rename}

ComplianceBaseline --gates--> {TargetModule, all touched Callsites' files, MistHelper.py}
```

---

## Non-Entities (Explicitly Out of Scope)

- **Test doubles for the extracted classes**: Not created in this PR. Existing integration tests exercise the callsites; adding unit tests is deferred to a subsequent QA-focused initiative unless a coverage gap is flagged during review.
- **Backward-compatible aliases** (e.g., `is_debug_mode = IsDebugMode.check`): Explicitly prohibited by FR-003 (no wrapper shims).
- **Type-stub (`.pyi`) files for the new modules**: Not required — the modules' inline type annotations suffice for `mypy`.
