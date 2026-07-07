# Phase 0 Research: Hot-Functions Bounded Bundle

**Feature**: `specs/1012-misthelper-refactor-hot-functions/`
**Date**: 2026-07-06
**Predecessors**: 1010 (13 PRs) and 1011 (20 PRs) — both baseline >=99.6/A+.

This document consolidates the five clarification decisions (Q1-Q5) from `spec.md`, and the four design choices needed to lower the spec into implementable form. Each decision follows the SpecKit research contract: **Decision / Rationale / Alternatives considered**.

---

## Decision 1 — Delete `EnvironmentUtils.is_debug_mode` wrapper in the same PR (Q1)

**Decision**: The `EnvironmentUtils.is_debug_mode` wrapper at `MistHelper.py:5891-5900` is deleted outright in the same PR as the `is_debug_mode` extraction. No follow-up PR is needed.

**Rationale**: Clarification session Q1 executed a repo-wide grep audit and confirmed **0 external callers** of `EnvironmentUtils.is_debug_mode`. The wrapper was a dead legacy adapter. Keeping it would violate FR-003 (no wrapper shims) and would leave a second obsolete symbol in the file the PR is trying to shrink. Deletion is safe because:

1. The wrapper's body is a straight passthrough to the module-level `is_debug_mode()` (which is itself being extracted).
2. Grep coverage searched `.py`, `.pyi`, `.md`, `.toml`, and CI YAML files; no dynamic-lookup pattern was observed.
3. The extraction PR already touches `MistHelper.py`, so no additional file coordination is required.

**Alternatives considered**:

- *Defer to a follow-up PR*. Rejected because it would leave dead code in `main` and split the audit trail across two PRs, degrading the "one-shot bounded change" property the initiative is optimized for.
- *Keep the wrapper and route it through the new class*. Rejected because it recreates the shim pattern FR-003 prohibits and adds a maintenance vector for future analyzer catalogs.

---

## Decision 2 — Use `@staticmethod` for extracted seams (Q2)

**Decision**: Both `IsDebugMode.check()` and `ConnectionPoolExecutor.execute()` (plus 3 private `_pool_*()` helpers) are decorated with `@staticmethod`. No instance state, no `cls`, no factory methods.

**Rationale**: Neither extraction target uses `self`, mutates class state, or benefits from inheritance. `@staticmethod` communicates intent unambiguously: this is a namespaced free function, not a method. Precedent: the 1010/1011 assignment-constant extractions use `class Foo: VALUE = ...` for the same "namespace without instance" pattern; `@staticmethod` is the direct callable analog.

**Alternatives considered**:

- *`@classmethod` receiving `cls`*. Rejected — no subclass hook is planned; `cls` would be unused ceremony.
- *Instance method with a required construction step*. Rejected — every callsite would need a boilerplate `IsDebugMode().check()` invocation, adding noise without value.
- *Module-level function inside the new file* (no class wrapper). Rejected — Constitution II (Class-Based Architecture) requires cohesive class landing, and the class-body seam is the established 1010/1011 pattern.

---

## Decision 3 — Idiomatic short method names `check` and `execute` (Q3)

**Decision**: `def is_debug_mode()` -> `IsDebugMode.check()`. `def execute_with_connection_pool_management()` -> `ConnectionPoolExecutor.execute()`. The class name carries the domain; the method name carries the verb.

**Rationale**: The class name already conveys the subject (`IsDebugMode`, `ConnectionPoolExecutor`), so redundant duplication in the method name (`IsDebugMode.is_debug_mode`, `ConnectionPoolExecutor.execute_with_connection_pool_management`) reads as stuttering. Callsites become `IsDebugMode.check()` and `ConnectionPoolExecutor.execute(...)`, which are self-documenting and match idiomatic Python (`Path.exists()`, `Queue.get()`, `Lock.acquire()`).

**Alternatives considered**:

- *Preserve original names as method names*. Rejected — see stuttering argument above.
- *Custom names like `IsDebugMode.evaluate()` or `ConnectionPoolExecutor.run()`*. Rejected — `check` is the standard verb for boolean-returning predicates and `execute` is the standard verb for "run this callable in a managed context." Neither warrants novelty.

---

## Decision 4 — Rename DI slots (`is_debug_mode_fn` -> `check_fn`, `connection_pool_fn` -> `execute_fn`) (Q4)

**Decision**: All 12 occurrences of the two dependency-injection slot names (`is_debug_mode_fn` at 6 sites, `connection_pool_fn` at 6 sites) are renamed to `check_fn` and `execute_fn` respectively in the same PR, across all five naming layers (module-level slot, dataclass field, `global` list, LHS/RHS assignment, kwarg key).

**Rationale**: The DI slot name should track the underlying callable's identity. When `is_debug_mode` becomes `IsDebugMode.check`, keeping the slot named `is_debug_mode_fn` creates a permanent semantic drift that will confuse every future reader ("which name is the current one?"). Doing the rename atomically:

1. Eliminates a class of future bugs where a caller wires the wrong callable into a slot with a misleading name.
2. Costs 12 mechanical edits distributed across `src/export/site_export_utils.py`, `src/gateway/overrides/_deps.py`, `src/gateway/overrides/device_data_fetcher.py`, and `MistHelper.py` — well within the atomic-PR budget.
3. Is validated by the SC-014 breadcrumb-audit gate: each rename site carries the pinned template `# NOTE: renamed from <old-name>; wiring source <new-callable> at MistHelper.py:<line>.` for one-grep discoverability.

**Alternatives considered**:

- *Leave DI slot names unchanged*. Rejected — creates permanent naming drift and forces every future reader to mentally map the old name to the new callable.
- *Rename in a follow-up PR*. Rejected — splits the atomic change and leaves the codebase in a mid-migration state on `main` for however long the follow-up takes to land.
- *Rename only the module-level slot, leave dataclass fields alone*. Rejected — partial renames are worse than either extreme (creates two names for the same slot depending on the naming layer).

---

## Decision 5 — Mandatory NOTE breadcrumbs with pinned templates (Q5)

**Decision**: The PR lands mandatory NOTE breadcrumbs at 6 sites with two pinned template strings, verified by SC-014 grep audit:

- **Extraction/deletion breadcrumb**: `# NOTE: <symbol> extracted to <new-location>. See specs/1012-misthelper-refactor-hot-functions/spec.md.`
  - Sites: `MistHelper.py:635` (tqdm skip-pin, Action 1), `MistHelper.py` at the `is_debug_mode` delete site (Action 2), `MistHelper.py` at the `execute_with_connection_pool_management` delete site (Action 3).
- **DI slot rename breadcrumb**: `# NOTE: renamed from <old-name>; wiring source <new-callable> at MistHelper.py:<line>.`
  - Sites: `src/export/site_export_utils.py` at rename sites (Action 2), `src/gateway/overrides/_deps.py` at rename sites (Action 3), `src/gateway/overrides/device_data_fetcher.py:40` at rename site (Action 3).

**Rationale**: Breadcrumbs are the mechanism by which future refactor sweeps discover why a symbol looks the way it does. The pinned template shape (specifically `See specs/1012-misthelper-refactor-hot-functions/spec.md.` in the extraction template) makes SC-014 verifiable with a single grep: `grep -R "specs/1012-misthelper-refactor-hot-functions/spec.md" src/ MistHelper.py` must return exactly the expected count. Without pinned templates, breadcrumb quality drifts across contributors and the audit degrades to eyeballing.

**Alternatives considered**:

- *Optional breadcrumbs at contributor discretion*. Rejected — quality drift; SC-014 becomes unverifiable.
- *Single breadcrumb template covering both extraction and rename*. Rejected — the two cases carry different information (target location vs. wiring source); merging them creates a compound template that fits neither case cleanly.
- *No breadcrumbs, rely on `git blame` and the spec file*. Rejected — `git blame` requires a reader to already know a rename happened; the breadcrumb makes it discoverable at the point of confusion.

---

## Decision 6 — Bundle three actions into one atomic PR

**Decision**: Contrary to 1010/1011's serial-per-candidate pattern, this initiative bundles three independent actions into one PR.

**Rationale**: Each action alone is too small or too tightly coupled to warrant its own PR:

- **Action 1** is a zero-extraction convention pin (add 1 NOTE, optionally invoke `analyzer --skip`). A dedicated PR would be almost purely CI overhead.
- **Action 2** is a small extract + delete + 12 rewrites + 6 rename occurrences; splitting the wrapper delete from the extract would leave dead code in `main` between merges.
- **Action 3** extracts a public function and 3 private helpers that share a single lifecycle contract; splitting them would either require a temporary shim (violates FR-003) or leave the private helpers orphaned in `MistHelper.py` after the public extraction.

Bundling amortizes the CI cost across three actions and preserves atomicity for each action's internal invariants. The edit surface (37 symbol-level edits) is well within the reviewable-diff budget observed on prior extraction PRs (some 1011 candidates like `WLANRadiusTimerManager` touched >800 LoC in a single PR).

**Alternatives considered**:

- *Three serial PRs*. Rejected — 3x CI overhead for no additional safety benefit; the actions have no shared dependencies that would benefit from being staged.
- *Two PRs (Action 1 alone + Actions 2+3 combined)*. Rejected — same argument, plus Action 1's breadcrumb-only nature makes it functionally trivial to bundle.

---

## Decision 7 — Use analyzer `--skip` CLI flag for Action 1 if available, else NOTE-only

**Decision**: Action 1's skip-pin uses the refactor analyzer's `--skip` CLI flag (if present in the current analyzer version) to add `tqdm` to a permanent skip list, alongside the mandatory source-level NOTE at `MistHelper.py:635`. If the `--skip` flag is not available in the current analyzer, the NOTE-only pin still satisfies SC-001.

**Rationale**: The primary contract of Action 1 is the source-level NOTE (SC-001, SC-014); the analyzer-level pin is a secondary belt-and-suspenders measure. Making it conditional avoids blocking the PR on an analyzer capability that may or may not exist and preserves FR-018 (analyzer never modified — we only invoke it via its documented CLI surface).

**Alternatives considered**:

- *Modify the analyzer to add a skip mechanism*. Rejected — FR-018 explicitly forbids analyzer modification.
- *Rely on NOTE alone*. Acceptable fallback; documented in the plan and the quickstart as the safe default.

---

## Decision 8 — Extract 3 private `_pool_*` helpers alongside the public function

**Decision**: `ConnectionPoolExecutor` receives all 4 members (`execute` + 3 private `_pool_*` static methods) in the same class body. The private helpers do not become module-level free functions in the new file.

**Rationale**: The 3 helpers are only called by `execute()`; they have no other callers. Landing them as class-private static methods:

1. Preserves the "one class = one cohesive lifecycle" pattern from Constitution II.
2. Keeps the private helpers out of the module's public surface (no unintentional imports).
3. Matches the 1010 pattern for extractions with private helpers (e.g., `SQLiteDatabaseWriter` internal helpers).

**Alternatives considered**:

- *Module-level free `_pool_*()` functions*. Rejected — leaks private helpers into the module namespace; any future `from src.refactors.connection_pool_executor import *` would expose them.
- *Nested inside `execute()`*. Rejected — 3 helpers is enough size that nesting them makes `execute()` harder to read; and nesting prevents individual testing.

---

## Decision 9 — Update `.github/copilot-instructions.md` SPECKIT marker to point to 1012

**Decision**: Phase 1 step 3 updates the `<!-- SPECKIT START -->` block in `.github/copilot-instructions.md` to reference `specs/1012-misthelper-refactor-hot-functions/plan.md` (currently points to `specs/1010-misthelper-refactor-extraction/plan.md`).

**Rationale**: The marker exists to give the coding-assistant a stable pointer to the "current plan." With 1010 and 1011 both closed and 1012 now the active initiative, the pointer must move forward for downstream `/speckit.tasks`, `/speckit.implement`, and `/speckit.analyze` invocations to load the right context.

**Alternatives considered**:

- *Leave pointing at 1010*. Rejected — misdirects future SpecKit commands.
- *Point at 1011*. Rejected — 1011 is closed; the active initiative is 1012.

---

## Open Questions

None. All NEEDS CLARIFICATION items from Technical Context are resolved. The five clarification-session answers (Q1-Q5) plus the four design decisions above cover the entire implementation surface.
