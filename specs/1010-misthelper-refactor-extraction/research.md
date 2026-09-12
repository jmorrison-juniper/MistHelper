# Phase 0 Research: MistHelper.py Refactor Extraction

**Feature**: 1010-misthelper-refactor-extraction | **Date**: 2026-07-05
**Purpose**: Resolve every NEEDS CLARIFICATION and consolidate decisions before design.

All decisions below inform Phase 1 design (`data-model.md`, `contracts/*`, `quickstart.md`). No NEEDS CLARIFICATION markers remain.

---

## 1. Analyzer Classification Model

**Decision**: Consume `tools/refactor_analyzer/` output verbatim. Buckets are Unused (0 callers), Single-Use (exactly 1 caller), Low-Use (2-3 callers), Hot (4+ callers), Skipped (`SKIP_ALWAYS` list). Only Unused and Single-Use participate in first pass.

**Rationale**: The analyzer already implements AST-driven reference counting via `references.py` and applies the `SKIP_ALWAYS` filter in `analysis.py`. Its classification is the single source of truth per FR-010 and Assumption 1. Manual re-classification would fork the truth and re-introduce the drift that prior stalled attempts suffered.

**Alternatives considered**:
- *Manual grep-driven classification*: rejected — labor-intensive, no dynamic-dispatch handling, and re-inventing the analyzer contradicts FR-018.
- *`grep -R "ClassName("` heuristic*: rejected — high false-positive rate on common names, no AST scope awareness.
- *IDE find-references*: rejected — non-reproducible across contributors, not scriptable in CI verification.

**Domain vocabulary used downstream**: `guideline_flags` (per-candidate list of remediation targets: oversize_25_lines, missing_inline_comments, missing_action_logging, non_ascii_logs, hardcoded_separator, raw_input_call, too_many_params).

---

## 2. Callsite Discovery Pattern

**Decision**: For every Single-Use candidate, the callsite is read directly from `refactor_candidates.md`'s per-candidate line reference (analyzer already emits caller file + line). Before the PR is opened, a manual `grep -R "SymbolName(" --include="*.py"` sweep confirms the caller count is exactly 1 — this is the FR-004 discipline extended defensively to Single-Use candidates to guard against dynamic-dispatch false negatives.

**Rationale**: The analyzer's reference count is AST-based and will miss `getattr(module, "SymbolName")()` and `eval`/`exec` patterns. Confirming with a text grep in the same PR provides the belt-and-suspenders verification needed before any deletion or rewrite lands.

**Alternatives considered**:
- *Trust analyzer output blindly*: rejected — dynamic dispatch exists in the codebase (e.g. dispatch tables, string-keyed lookups) and could hide a second caller.
- *Full AST re-analysis with a second tool*: rejected — over-engineered for a one-caller confirmation; text grep is sufficient because a hit outside the analyzer-reported callsite is enough to abort.

**Callsite rewrite pattern**: The single caller's `from MistHelper import SymbolName` (or `SymbolName(...)` bare call) is rewritten in the same commit to `from src.refactors.new_module import SymbolName` and the original definition is deleted from `MistHelper.py`. No intermediate revision on the branch may leave a dangling import or dangling definition (FR-003).

---

## 3. Compliance-Baseline Interplay

**Decision**: Every extraction PR runs `py -m tools.compliance_analyzer` before opening the PR and again in CI. The affected-file set is (a) the new module and (b) `MistHelper.py`. New module must score A+/100; `MistHelper.py` must not regress its grade or lose any A+ file downstream. Baseline snapshot lives in `data/full_repo_compliance_current.md`.

**Rationale**: FR-012, FR-013, SC-004, SC-005, and SC-007 all key off compliance measurements. The analyzer emits per-file grades and a repo-wide aggregate; both are required to gate merge. This mirrors the constitution's Principle IV (Full Deployment Pipeline) and the existing repo cadence (commits e50a524, 4176bc8, 6c2e0b6 in recent history show the same "compliance A-/91.0 -> A+/100.0" pattern).

**Alternatives considered**:
- *Only check the new module's grade*: rejected — misses regressions caused by import churn or comment-density shifts in `MistHelper.py` from the deletion diff.
- *Sample-based baseline (subset of files)*: rejected — baseline is authoritative per FR-013; sampling would let a regression slip through.
- *Post-merge cleanup PRs to restore baseline*: rejected — violates the "resolve in-flight" discipline (FR-006) and defers debt.

**Guideline-flag resolution**: If `guideline_flags` on the extracted code includes `oversize_25_lines`, `missing_inline_comments`, `missing_action_logging`, `non_ascii_logs`, `hardcoded_separator`, or `raw_input_call`, each is remediated in the extraction PR before the compliance gate is evaluated. FR-006 makes deferral prohibited.

---

## 4. Bare-Function-to-Class Refactor Pattern

**Decision**: Module-level function candidates (`run_systematic_test`, `switch_to_interactive_login`, `run_interactive_test`, `listen_keyboard`) land as methods on a new cohesive class in the target module, not as bare `def` at module scope. The class name is derived from the module name (e.g. `SystematicTestRunner`, `InteractiveLoginSwitcher`, `InteractiveTestRunner`, `KeyboardListener`). The single caller is rewritten to instantiate the class and call the method: `NewClass().run(...)` or a domain-appropriate method name.

**Rationale**: Constitution Principle II (Class-Based Architecture) makes bare module functions a smell. FR-005 codifies the transformation. Extracting a function into a module without wrapping it in a class would re-create the very anti-pattern the constitution forbids — a lateral move rather than an improvement.

**Alternatives considered**:
- *Preserve bare function signature to minimize diff*: rejected — violates FR-005 and Principle II.
- *Static method / class method*: rejected in the general case — instance methods allow future state (loggers, config, cached deps) without another refactor; `@staticmethod` decoration is acceptable only when the function is truly stateless and remains a leaf.
- *Free-function module + separate wrapper class in a second PR*: rejected — violates FR-006 (in-flight resolution) and FR-002 (one candidate per PR would explode into two).

**Method-signature preservation**: The refactored method preserves the original callable's parameters verbatim so the callsite rewrite is a single-line change (`func(args)` becomes `NewClass().func(args)` or equivalent). This keeps the diff minimal and reviewable.

---

## 5. `AddressComparisonCounters` Fold-In Pattern (FR-015 Exception)

**Decision**: `AddressComparisonCounters` does NOT get its own file under `src/refactors/`. Instead it is folded into `src/inventory/csv_comparator.py::CsvComparatorManager` — either as a nested class, an inner data structure, or (preferred) inlined fields on `CsvComparatorManager` if the counter's shape is small enough. The sole caller already lives in `csv_comparator.py`, so the extraction is a *local move* from `MistHelper.py` into the caller's home module.

**Rationale**: FR-015 makes this an explicit exception to the "new module under `src/refactors/`" rule. Creating `src/refactors/address_comparison_counters.py` would introduce a cross-module import from `csv_comparator.py` back into `refactors/`, which is precisely the coupling this initiative is trying to reduce. Landing the symbol next to its only caller minimizes import surface and lets the caller reference it as a private class member (or module-private class in the same file).

**Alternatives considered**:
- *Create `src/refactors/address_comparison_counters.py`*: rejected by FR-015 — introduces avoidable cross-module import for a 62-LoC single-caller helper.
- *Fold into `csv_comparator.py` at module scope (private, underscore-prefixed)*: acceptable fallback if the counter cannot cleanly become a nested/inner class, but the preferred landing is inside `CsvComparatorManager` per FR-015's explicit target.
- *Split fields across `CsvComparatorManager` and delete the helper class entirely*: acceptable if the counter is just a bag of ints and the resulting `CsvComparatorManager` still lands at A+/100 with clear inline commentary — this collapses the class rather than moving it.

**Precedent**: Assumption 9 documents that other candidates whose sole caller lives outside `MistHelper.py` may follow the same "land next to caller" rule if discovered mid-extraction. Deviation requires PR-description note.

---

## 6. Analyzer Regeneration Protocol Between Merges

**Decision**: After every merged extraction PR, run `py -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md` on the current `main` head. Commit the regenerated `refactor_candidates.md` (typically as part of the next extraction PR, so the diff carrying the next candidate is preceded on `main` by an up-to-date catalog). The dispatcher for PR N+1 selects the next candidate from the freshest catalog, not from a stale snapshot.

**Rationale**: FR-010, SC-011, and User Story 3 all mandate this cadence. Reference counts shift as callsites move — a Single-Use candidate whose sole caller was itself extracted may become Unused, or vice versa. Operating on a stale catalog would produce incorrect callsite rewrites and violate FR-016.

**Alternatives considered**:
- *Regenerate only when reclassification is suspected*: rejected — introduces judgment where the spec demands a mechanical rule; SC-011 requires verifiability.
- *Batch-regenerate every 3 PRs*: rejected — a single stale count could invalidate two subsequent PRs before detection.
- *Auto-regenerate in a bot/hook*: acceptable future improvement but out of scope (FR-018 forbids analyzer modification; a wrapper bot is a separate initiative).

**Reclassification handling** (FR-016): If the fresh catalog shows a first-pass candidate has become Low-Use or Hot, it is *rerouted* to second-pass planning or Out-of-Scope, not force-extracted. If it has become Unused, it is *reclassified* into the Unused workflow (delete only, no new module). These are dispatcher-time decisions driven by the fresh catalog.

**Serial-workflow reinforcement** (Edge Cases in spec): Only one extraction PR is open at a time. This makes catalog-regeneration timing unambiguous — regenerate on `main` head after merge, before opening the next PR. Parallel branches are explicitly forbidden.

---

## Cross-cutting Decisions

**Merge protocol**: squash-and-merge, `--delete-branch`, no `--admin` bypass. Consult `mergeStateStatus`; only genuine BLOCKED/DIRTY/BEHIND states warrant investigation, and even then the fix is a rebase/push, not `--admin` (per `feedback_no_admin_bypass.md` guidance).

**Commit message convention**: `refactor: extract {SymbolName} to {target_path} (#PR)` for Single-Use PRs; `refactor: delete unused {SymbolName} (#PR)` for Unused PRs. Follows the existing repo history pattern (e.g. commit da4ae90, 4176bc8).

**PR title convention**: `refactor: extract {SymbolName} ({loc} lines)` or `refactor: delete unused {SymbolName} ({loc} lines)`.

**Test-preservation rule**: Any existing tests that reference the extracted symbol via `from MistHelper import ...` are updated to the new import path in the same PR. New tests are not mandated by the extraction — the initiative preserves behavior, not adds coverage — but existing tests must remain green (part of the 15 functional CI jobs).
