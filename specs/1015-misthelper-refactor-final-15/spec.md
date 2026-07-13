# Feature Specification: MistHelper Refactor — Final 15 (All Remaining Analyzer Candidates)

**Feature Branch**: `1015-misthelper-refactor-final-15`
**Created**: 2026-07-09
**Status**: Draft
**Catalog snapshot**: `refactor_candidates.md` regenerated 2026-07-09 against `origin/main` at commit `8523596` (PR #914 — SiteExportUtils facade removal — merged).

**Predecessors** (all closed):

- [`1010-misthelper-refactor-extraction`](../1010-misthelper-refactor-extraction/spec.md) — Unused + Single-use bucket clearance (13 PRs).
- [`1011-misthelper-refactor-low-use`](../1011-misthelper-refactor-low-use/spec.md) — Low-Use serial workflow (20 candidates).
- [`1012-misthelper-refactor-hot-functions`](../1012-misthelper-refactor-hot-functions/spec.md) — Hot-function bounded bundle (`tqdm` skip-pin, `is_debug_mode`, `_pool_*` family).
- [`1013-misthelper-refactor-hot-classes`](../1013-misthelper-refactor-hot-classes/spec.md) — 47-candidate MistHelper-only Hot-class serial workflow.
- [`1014-misthelper-refactor-hot-classes-with-src-callers`](../1014-misthelper-refactor-hot-classes-with-src-callers/spec.md) — 24-candidate Hot-class initiative with `src/` external callers (Cat A facade removal + Cat E fresh cross-package extraction). Closed by PR #914 removing the last Cat A facade (`SiteExportUtils`).

**Input**: User description: "Extract all remaining MistHelper.py refactor candidates from analytics report (excluding `menu_actions` and `GlobalImportManager`). Sixteen prior extraction PRs (P1-P16) closed initiatives 1010-1014. The freshly regenerated analyzer report at `refactor_candidates.md` surfaces 17 remaining catalog entries: 3 Single-use, 2 Low-Use, 11 Hot, and 1 Skipped. Removing `menu_actions` (deferred indefinitely per user directive) and the pinned `GlobalImportManager` (`SKIP_ALWAYS`, module-load-order-critical) leaves **15 tasks**, one per PR, in the same serial workflow discipline established by 1010/1011/1013/1014. This initiative retires the analyzer report to `menu_actions` + `GlobalImportManager` only."

## Predecessor Context

The five closed predecessor initiatives (1010-1014) collectively cleared every actionable extraction the analyzer has surfaced across four buckets:

- **1010** cleared 13 candidates in the Unused + Single-Use buckets and established the extraction contract (no wrapper shims, class-body landing, callsite rewrite in the same PR).
- **1011** cleared 20 Low-Use candidates using the serial per-PR workflow.
- **1012** cleared three specific Hot-bucket entries as a bounded single-PR bundle.
- **1013** cleared 47 MistHelper-only Hot-bucket classes across 4 Cat A + 43 Cat B PRs.
- **1014** cleared the 24-candidate Hot-class queue whose callsites span `src/` (6 Cat A facades + 18 Cat E fresh cross-package extractions). Closed by PR #914 (SiteExportUtils, Cat A, position 16 of the 1014 queue). Note: 1014's queue was expanded mid-initiative — the "24" in its spec was the initial snapshot; the actual merged count differs slightly as candidates reclassified per 1014 FR-020 / E-12.

After PR #914 (2026-07-08), the analyzer was re-run against `origin/main` at commit `8523596`. The regenerated `refactor_candidates.md` shows 17 catalog entries. **Two are explicitly out of scope for this initiative** — `menu_actions` (887 LoC, 17 refs; deferred indefinitely per user directive) and `GlobalImportManager` (1003 LoC, 1 ref; pinned by bootstrap / module-load ordering; the analyzer's `SKIP_ALWAYS` list). The remaining **15 candidates** are this initiative's Dispatch Queue.

This initiative retires the analyzer output. When it closes, `refactor_candidates.md` will show only `menu_actions` (deferred by policy) and `GlobalImportManager` (skipped by policy). No further MistHelper.py refactor initiative is planned unless net-new extractable symbols are added to the entrypoint.

## Scope Boundary

The initiative targets exactly **15 candidates**, enumerated in the Dispatch Queue below. Each row lands as one PR. The queue interleaves three category-buckets (Single-use → Low-use → Hot) in the analyzer's canonical order (highest-ROI, smallest-blast-radius first) rather than a strict global Refs-ASC sort — this differs from 1014's ordering rule because the bucket-boundary is itself a meaningful risk gradient (Single-use PRs have 1 caller each; Low-use have 2-3; Hot have 4+ up to 195).

Two action-type designations coexist in the queue:

- **Cat A — Facade removal** (0 candidates in this initiative). No candidate in the current catalog is a delegation wrapper over an existing `src/` implementation — 1013 and 1014 have already retired every Cat A facade the analyzer surfaced. If a candidate reclassifies to Cat A mid-initiative (e.g. a new facade is introduced by an unrelated commit), the FR-025 method-parity discipline from 1014 applies.
- **Cat E — Fresh cross-package extraction** (all 15 candidates). MistHelper.py holds the real body (class body, function body, or module-level constant / assignment); one or more callsites currently reference the symbol via a direct name resolution in MistHelper.py's namespace. For hot candidates with `src/` callers (T-06 through T-15), one or more `src/` modules also reference the symbol via `mh = importlib.import_module("MistHelper")` + `mh.<Name>` lazy imports. Each PR (a) creates the landing module (or folds into an existing module when semantically appropriate), (b) deletes the original body from `MistHelper.py`, (c) rewrites every `MistHelper.py` callsite in the same commit, AND (d) rewrites every `src/` (or other first-party) callsite in the same commit.

**Explicit exclusions**:

- **`menu_actions`** (887 LoC, 17 refs, Hot). Deferred indefinitely per user directive. Not in this initiative's queue and not planned for any follow-up initiative.
- **`GlobalImportManager`** (1003 LoC, 1 ref, Skipped). Pinned by module-load / bootstrap ordering. Static analysis cannot detect the load-order dependency; the analyzer curates it via the `--skip NAME` CLI flag. Moving it would break import wiring. Not in this initiative's queue and not planned for any follow-up initiative.
- All classes already extracted in 1010, 1011, 1012, 1013, or 1014. Those symbols are fully migrated.
- The refactor analyzer itself (`tools/refactor_analyzer/`) — consumed as-is.

The 15 in-scope candidates cover three analyzer categories:

- **Single-use bucket (3 candidates)** — T-01 through T-03. One PR each. Sole caller is the sole rewrite site (plus the extraction itself in MistHelper.py).
- **Low-use bucket (2 candidates)** — T-04, T-05. Two callers each. Two-callsite PRs.
- **Hot bucket (10 candidates)** — T-06 through T-15. 11 to 195 refs each; every candidate has at least one `src/` caller. Same Cat E discipline as the 18 Cat E candidates from 1014.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Extract a Single-use or Low-use candidate to `src/refactors/*.py` (or the sole caller's semantic module) and rewrite its callsites atomically (Priority: P1)

The queue-head workflow. For each of T-01 through T-05, the refactor engineer opens a PR that (a) creates the landing module (either the analyzer's `Suggested module` path or a semantically closer target per E-1), (b) deletes the symbol body from `MistHelper.py`, (c) rewrites every callsite in the same commit (1-2 sites for Single-use / Low-use), (d) resolves any analyzer `guideline_flags` in-flight, and (e) lands with all 15 functional CI jobs green, aggregate analyzer score ≥ 99.6/A+, `black --check` clean, `ruff check` clean, and `python MistHelper.py --test` passing (0 failed, exit 0).

**Why this priority**: These are the lowest-blast-radius extractions in the initiative — Single-use has one caller, Low-use has two. Front-loading them validates the workflow before the higher-refs Hot-bucket PRs and produces early merges that thin the queue quickly.

**Independent Test**: Any single Single-use candidate (e.g. `DeviceFetchConfig` at 1 ref / 9 LoC, the smallest) can be merged in isolation. The PR (a) moves `DeviceFetchConfig` into `src/refactors/device_data_fetcher.py`'s `DeviceDataFetcherManager` class body (or a top-level dataclass in that module, per E-1), (b) deletes the definition from `MistHelper.py`, (c) rewrites the single callsite at `src/refactors/device_data_fetcher.py:49`, (d) resolves the `missing_action_logging` flag, (e) leaves a NOTE breadcrumb at the extraction site in `MistHelper.py`, (f) lands green.

**Acceptance Scenarios**:

1. **Given** a Single-use or Low-use candidate with N callsites (N ∈ {1, 2}), **When** the PR is opened, **Then** the diff shows the body moved to the landing module, deleted from `MistHelper.py`, and every one of the N callsites rewritten — with zero stale references surviving.
2. **Given** the extracted candidate carried analyzer `guideline_flags`, **When** the PR lands, **Then** each flag is resolved in-flight — decomposition to ≤ 25 lines per method, `logging.info` / `logging.debug` envelopes on every method, inline comments on every executable line, ASCII-only log literals, `pathlib.Path` in place of `os.path`, `InputUtils.safe_input()` in place of raw `input()`, hardcoded separators replaced with `os.sep` or `pathlib` idioms.
3. **Given** the pre-push local gate, **When** the contributor pushes the refactor branch, **Then** `black --check` and `ruff check` both pass locally before the PR opens, and `python MistHelper.py --test` reports 0 failed with exit code 0.
4. **Given** T-04 (`ENDPOINT_PRIMARY_KEY_STRATEGIES`, 2327 LoC, 2 refs) is the largest LOC line-item in the initiative, **When** its PR is opened, **Then** the move is atomic (no split across multiple PRs) but the new module MAY carry substantial internal decomposition (broken into ≤ 25-line methods, inline comments every 5-10 lines, action logging envelopes) to satisfy compliance.

---

### User Story 2 — Extract a Hot-bucket candidate from `MistHelper.py` into a cohesive class-body / module-body module AND rewire every `MistHelper.py` and `src/` callsite atomically (Priority: P1)

The Cat E dual-side rewire workflow — carried forward from 1014 User Story 2. For each of T-06 through T-15, MistHelper.py holds the real body while one or more `src/` modules reach it either (a) directly via a resolution against MistHelper.py's namespace at import time, or (b) via `mh = importlib.import_module("MistHelper")` + `mh.<Name>` lazy imports (the pattern 1014 spent extensive effort eliminating). Extraction is inseparable across the two sides: the body moves to the landing target, all `MistHelper.py` callsites are rewritten, AND every `src/` callsite is rewritten to `from src.<package>.<module> import <Name>` in the SAME commit. The PR does NOT land in two parts. The pre-dispatch grep audit enumerates the exact set of `src/` callsites to be rewritten and their count is recorded in the PR description alongside the callsite table.

**Why this priority**: Same P1 as User Story 1. Cat E is the higher-risk of the two workflow paths because these are the highest-refs candidates (`InputUtils` at 195, `DataExporter` at 118, `OrgInventoryExporter` at 102, `VirtualChassisManager` at 104, `ConfigUtils` at 102, `PromptUtils` at 96, `DataProcessingUtils` at 69, `tqdm` at 51, `FilePathUtils` at 50, `MIST_SITE_EXCLUDE_PREFIX` at 11). A partial extraction (body moved but callers still doing direct-namespace or `mh.<Name>` resolution) would break `python MistHelper.py --test`. Atomicity is not optional.

**Independent Test**: Any single Hot-bucket candidate can be merged in isolation. Example: T-15 (`MIST_SITE_EXCLUDE_PREFIX`, 3 LoC, 11 refs — the smallest LOC hot candidate) can be extracted as: (a) create `src/refactors/mist_site_exclude_prefix.py` with a module-level constant, (b) delete the definition from `MistHelper.py`, (c) rewrite the MistHelper.py callsites, (d) rewrite the `src/gateway/*.py` callsites, (e) leave a NOTE breadcrumb, (f) land green.

**Acceptance Scenarios**:

1. **Given** a Cat E candidate with M `MistHelper.py` callsites and N `src/` callsites, **When** the PR is opened, **Then** the diff shows the body moved to the landing target, deleted from `MistHelper.py`, every one of the M `MistHelper.py` callsites rewritten, and every one of the N `src/` callsites rewritten — with zero stale references surviving.
2. **Given** the callsite table in the PR description enumerates M `MistHelper.py` callsites and N `src/` callsites, **When** the reviewer runs `grep -rn "<Name>" .` against the merged PR, **Then** every match is either in the new landing module, in a `src/` file importing from the landing module, or a NOTE breadcrumb — with zero stale namespace-lookup or `mh.<Name>` matches.
3. **Given** the extracted class carried analyzer `guideline_flags`, **When** the PR lands, **Then** each flag is resolved in-flight (per FR-006).
4. **Given** the pre-push local gate, **When** the contributor pushes the refactor branch, **Then** `black --check` and `ruff check` both pass, and `python MistHelper.py --test` reports 0 failed with exit code 0.
5. **Given** T-06 (`OrgInventoryExporter`, 686 LoC, 102 refs) and T-07 (`PromptUtils`, 441 LoC, 96 refs) are the largest LOC Hot candidates, **When** their PRs are opened, **Then** the moves are atomic but MAY carry substantial internal decomposition (per FR-006) to satisfy the ≤ 25-line-per-method rule and the aggregate score floor.
6. **Given** T-09 (`InputUtils`, 74 LoC, 195 refs) is the highest-refs candidate in the initiative and spans 17 files, **When** the PR is opened, **Then** the callsite table enumerates the exact file:line list of every rewritten site and the pre-dispatch grep audit is recorded in the PR description.
7. **Given** T-14 (`tqdm`, 3 LoC, 51 refs) is a bare function wrapper flagged `missing_action_logging`, **When** the PR is opened, **Then** the wrapper is extracted from MistHelper.py's `SKIP_ALWAYS`-adjacent surface without violating FR-009 (T-14 is emphatically NOT in the `SKIP_ALWAYS` bucket — 1012 skip-pinned it only for that initiative; the analyzer now surfaces `tqdm` again for this initiative because it is a normal Hot candidate).

---

### User Story 3 — Regenerate the analyzer catalog and re-derive dispatch order after every merged extraction (Priority: P2)

Carry-forward of 1010/1011/1013/1014 User Story 3. Reference counts and callsite locations shift as extractions land. After every merged extraction PR, the analyzer is re-run against the new `main` head and `refactor_candidates.md` is regenerated before the next PR is dispatched. Bucket ordering (Single-use → Low-use → Hot) is applied to the fresh catalog. Category designation is re-verified against the fresh catalog — a Hot candidate whose `src/` callers have all been coincidentally removed by a prior extraction may reclassify to MistHelper-only Cat B or drop to Low-use, but every candidate stays in this initiative's scope unless it drops to Unused (in which case a deletion PR replaces the extraction PR).

**Why this priority**: Workflow discipline that supports P1 rather than delivering standalone value.

**Independent Test**: After merging any extraction PR, running `python -m tools.refactor_analyzer` regenerates the catalog cleanly. The just-extracted symbol no longer appears in any bucket except (possibly) as a new definition in its new home. Any reference-count shifts on remaining candidates are reflected in the fresh dispatch order.

**Acceptance Scenarios**:

1. **Given** an extraction PR has merged to `main`, **When** the next PR is dispatched, **Then** `refactor_candidates.md` has been regenerated on the current `main` head first and the next candidate is selected from that fresh output following the bucket ordering rule.
2. **Given** the regenerated catalog shows a formerly Hot candidate has dropped to Low-use or Unused, **When** the dispatcher plans the next PR, **Then** the candidate's task ID stays in the queue but its category is updated in "Reclassifications", and (if Unused) the PR becomes a pure-deletion PR.
3. **Given** the regenerated catalog surfaces a new symbol not in the original 15-row queue (e.g. an unrelated commit adds a new module-scope symbol to MistHelper.py that meets the extraction criteria), **When** the dispatcher plans the next PR, **Then** the new symbol is appended to this initiative's Deferred/Reclassifications table and evaluated for inclusion — do NOT silently expand the queue mid-initiative.

---

### Edge Cases

- **E-1** — Landing target selection. Each candidate has a suggested landing target in the Dispatch Queue (drawn from the analyzer's `Suggested module` field or a curated override). The dispatch PR MAY override the suggestion at PR time if a closer semantic fit exists. Prefer an existing semantic package over creating a new `src/refactors/*.py` module when both are viable. The PR description records the destination-selection rationale in one sentence.
- **E-2** — Guideline-flag decomposition mid-move. If a candidate carries `oversize_25_lines` (e.g. `OrgInventoryExporter` at 686 LoC, `PromptUtils` at 441 LoC, `DataExporter` at 345 LoC, `ENDPOINT_PRIMARY_KEY_STRATEGIES` at 2327 LoC, `DataProcessingUtils` at 158 LoC, `InsightMetricsUtils` — retired in 1014), the move includes method-level decomposition per FR-006. Deferral of any flag to a follow-up PR is prohibited.
- **E-3** — Callsite drift between catalog regeneration and PR opening. If the analyzer's recorded line numbers drift, the PR uses fresh grep against the current `main` head at branch time. Line-number drift alone does not block extraction; only a *count* change triggers re-evaluation.
- **E-4** — NOTE breadcrumb at the extraction site. Every extraction PR MUST leave a single-line NOTE breadcrumb at the deletion site in `MistHelper.py` (per FR-007): `# NOTE: <Name> extracted to <new-module-path>::<Name>. See specs/1015-misthelper-refactor-final-15/spec.md.` Silent (breadcrumbless) deletion is rejected.
- **E-5** — Name collision at destination. If the target destination already contains a symbol whose name would collide, rename the incoming symbol only if renaming is genuinely necessary; otherwise the destination is changed. Record the choice in the PR description.
- **E-6** — Reference count discrepancy between spec-time table and catalog regeneration at dispatch. The 15-row table quotes ref counts as of the 2026-07-09 catalog. If a fresh regeneration at dispatch time shows a candidate's ref count has shifted, the fresh catalog wins. The 15-row table is documentation, not a runtime contract.
- **E-7** — `python MistHelper.py --test` regression. If the test-suite invocation begins failing mid-initiative because of an unrelated commit landing on `main`, extraction PRs pause until the underlying regression is fixed. **Pre-existing flake exception**: `test_menu_196_dispatches_to_async_claim_exporter` is a known flake that is NOT considered a blocking regression for this initiative.
- **E-8** — Analyzer score regression below 99.6/A+. If any single extraction PR would drop the aggregate analyzer score below 99.6/A+, the PR is revised rather than merged.
- **E-9** — SKIPPED CI conditionals. Per `feedback_no_admin_bypass.md`, SKIPPED conditionals are non-blocking and do not count against the 15/15 green tally. `--admin` merge bypass is not used as a routine unblock.
- **E-10** — Very large candidates. `ENDPOINT_PRIMARY_KEY_STRATEGIES` (2327 LoC), `OrgInventoryExporter` (686 LoC), `PromptUtils` (441 LoC), `DataExporter` (345 LoC), `DataProcessingUtils` (158 LoC). These MUST land as one PR each (no splitting) but the PR MAY carry substantial internal decomposition to satisfy the ≤ 25-line-per-method rule and the aggregate score floor.
- **E-11** — Circular-import trap. Hot-bucket candidates often have `src/` modules that today lazy-import MistHelper.py *specifically to avoid* import cycles. When the body moves to the landing target, cycles MAY re-emerge if the new landing module itself imports symbols still living in `MistHelper.py` (e.g. globals such as `apisession`). Verify import-graph health post-move per FR-028 — `python -c "import <landing_module>"` must succeed without traversing `MistHelper.py`. If a genuine cycle remains, inject a small dependency-injection surface (Pattern 1 — constructor injection) but do NOT leave a `mh.<name>` lazy-import in the new module.
- **E-12** — `tqdm` clarification. T-14 (`tqdm`, 3 LoC, 51 refs, `missing_action_logging`) is emphatically NOT in the analyzer's `SKIP_ALWAYS` bucket for this initiative. 1012's skip-pin was per-initiative. The current catalog surfaces `tqdm` as a normal Hot candidate. FR-009's `SKIP_ALWAYS` exclusion applies only to `GlobalImportManager` for this initiative.
- **E-13** — Constructor injection for hot classes with runtime deps. Where the extracted symbol is a hot class with runtime dependencies (e.g. `apisession`, `logger`, config accessors), the extraction MUST follow Pattern 1 established by 1013/1014 — `__init__(self, **deps)` accepting all needed dependencies; every callsite constructs the instance inline with the full kwargs list spelled out. No factory helpers, no module-level cached instance, no self-resolving via `sys.modules`, no `_configure_module()` shims. Pure static helpers with no runtime deps remain `@staticmethod`.
- **E-14** — Module-level constant candidates (T-02, T-03, T-15). These are pure module-level assignments with no runtime deps. The landing pattern is a bare module-level constant in the new file (or folded into an existing constants module in the destination package). The analyzer's `Suggested class` (e.g. `FastModeMaxConcurrentConnectionsManager`) is a naming hint only — the PR MAY implement the landing as a plain module-level constant when semantically appropriate, and the destination-selection rationale is recorded in the PR description.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The initiative MUST process exactly the 15 candidates enumerated in the Dispatch Queue. Additions require a new spec revision recording the reclassification event.
- **FR-002**: The initiative MUST process exactly one candidate per PR. Batching multiple candidates into a single PR is prohibited (carry-forward from 1010-1014 FR-002).
- **FR-003**: For each candidate, the PR MUST perform a **Cat E fresh cross-package extraction**: (a) create the landing module OR fold into an existing module / class body within the landing package when semantically appropriate, (b) delete the original body from `MistHelper.py`, (c) rewrite every `MistHelper.py` callsite in the same commit, AND (d) rewrite every `src/` (or other first-party) callsite currently referencing the symbol via direct namespace resolution or `mh = importlib.import_module("MistHelper")` + `mh.<Name>`. No wrapper shim, forwarding function, re-export module, or backward-compatibility alias may be left in `MistHelper.py`.
- **FR-004**: Every extracted symbol MUST land in a cohesive destination — top-level of a new module for class or function extractions, module-level constant (or existing constants module) for assignments. Bare unmotivated module-level function landings are prohibited when a semantic class body already exists in the destination package.
- **FR-005**: For each candidate, all `MistHelper.py` references AND all `src/` (and other first-party) references MUST be rewritten to import from the new location in the same commit as the extraction. Zero stale references — including zero `importlib.import_module("MistHelper")` + `mh.<Name>` remainders — may survive the merge.
- **FR-006**: Analyzer-flagged `guideline_flags` on the moved symbol MUST be resolved within the same extraction PR — never deferred. Decomposition during the move includes: methods ≤ 25 lines with ≤ 5 params, `logging.info` / `logging.debug` envelopes on every method (`%s` formatting), inline comments on every executable line, ASCII-only log literals, `pathlib.Path` in place of `os.path`, `InputUtils.safe_input()` in place of raw `input()`, hardcoded separators replaced with `os.sep` or `pathlib` idioms.
- **FR-007**: A **mandatory** single-line NOTE breadcrumb comment MUST be added at each extraction site in `MistHelper.py`, following the template: `# NOTE: <Name> extracted to <new-module-path>::<Name>. See specs/1015-misthelper-refactor-final-15/spec.md.` Silent (breadcrumbless) extraction is rejected.
- **FR-008**: All extracted modules MUST comply with project non-negotiables: ASCII-only logs, `InputUtils.safe_input()` for interactive input, `pathlib.Path` in place of `os.path`, inline comments every 5-10 lines, action logging before/after every meaningful action with `%s` formatting, ≤ 25-line methods, ≤ 5 params per function.
- **FR-009**: The initiative MUST NOT touch symbols in the analyzer's `SKIP_ALWAYS` bucket. For this initiative that means **only `GlobalImportManager`**. `tqdm` was skip-pinned per-initiative by 1012 and is NOT in `SKIP_ALWAYS` here (see E-12); T-14 explicitly targets `tqdm`.
- **FR-010**: The initiative MUST NOT touch `menu_actions`. Deferred indefinitely per user directive. No follow-up initiative is planned for `menu_actions`.
- **FR-011**: The initiative MUST NOT re-refactor any symbol already extracted in 1010, 1011, 1012, 1013, or 1014.
- **FR-012**: The initiative MUST NOT modify `tools/refactor_analyzer/` itself; the analyzer is consumed as-is.
- **FR-013**: Before opening each extraction PR, the workflow MUST run `grep -rn "<Name>" src/ tests/` and enumerate every callsite in the PR description. The audit produces the exact set of files whose reference lines will be rewritten in the same commit.
- **FR-014**: After every merged extraction PR, the workflow MUST regenerate `refactor_candidates.md` by running `python -m tools.refactor_analyzer` against the current `main` head. The regenerated file is committed in a follow-up `chore(1015): regenerate refactor_candidates.md after P<N> merge` commit (or the same PR when the extraction PR includes the regeneration).
- **FR-015**: An extraction PR MUST NOT merge until all 15 functional CI jobs report green AND `mergeStateStatus` is CLEAN AND `black --check` is clean AND `ruff check` is clean AND `python MistHelper.py --test` reports 0 failed with exit code 0 (modulo the known `test_menu_196_dispatches_to_async_claim_exporter` flake — see E-7). `--admin` merge bypass MUST NOT be used as a routine unblock. Reference `feedback_no_admin_bypass.md` and `feedback_prepush_black_ruff.md`.
- **FR-016**: Every new module under the landing package MUST land at A+/100 compliance score. No file that was previously A+ may regress below A+.
- **FR-017**: The repository-wide aggregate compliance MUST remain ≥ 99.6/A+ after each merged extraction PR.
- **FR-018**: `MistHelper.py`'s pylint score MUST be non-regressing against the pre-initiative baseline established on the first branch commit. Regression blocks merge.
- **FR-019**: No new SKIPPED conditionals in CI may be introduced by any extraction PR.
- **FR-020**: If a candidate's classification shifts mid-initiative (Hot → Low-use, Low-use → Single-use, or a symbol's `src/` callers are removed indirectly), the candidate stays in this initiative's scope but its Dispatch Queue metadata is updated in "Reclassifications". Only a drop to Unused converts the extraction PR to a deletion PR.
- **FR-021**: The initiative MUST NOT introduce new features, new commands, new CLI flags, or user-facing behavior changes.
- **FR-022**: When a candidate is folded into an existing destination package's class body (rather than a new `src/<pkg>/*.py` module), the existing destination file's compliance grade MUST remain at A+/100 after the fold. If the fold would regress the destination below A+, the destination is changed or the extracted symbol receives further decomposition within the same PR.
- **FR-023**: The Dispatch Queue's ordering (Single-use → Low-use → Hot descending by LOC within Hot) is a **dispatch rule**, not a merge order guarantee. Concurrent open PRs are not permitted (one PR open at a time).
- **FR-024**: The initiative is considered complete when `refactor_candidates.md` regenerated on `main` shows exactly two remaining entries — `menu_actions` and `GlobalImportManager` — both explicitly out of scope per FR-010 and FR-009.
- **FR-025**: Cat A method-parity verification (from 1014 FR-025) applies if any candidate reclassifies to Cat A mid-initiative. No candidate is Cat A at initiative start.
- **FR-026**: The queue is ordered by bucket first (Single-use → Low-use → Hot) then by descending LOC within Hot. Within Single-use / Low-use the analyzer's canonical order is preserved. This bucket-first ordering differs from 1014's strict global Refs-ASC ordering because the bucket-boundary is itself a meaningful risk gradient in this catalog.
- **FR-027**: Every extraction PR MUST record a **callsite table** in the PR description enumerating: (a) the total count of `MistHelper.py` callsites rewritten, (b) the exact list of `src/` files (with line numbers) whose reference lines were rewritten, (c) the exact list of any `tests/` or other first-party callsites rewritten. The table is verifiable by post-merge grep.
- **FR-028**: Every extraction PR MUST verify import-graph health post-move: `python -c "import <landing_module>"` succeeds without traversing `MistHelper.py` AND `python MistHelper.py --test` reports 0 failed / exit 0 (modulo E-7). If a genuine circular import remains after the naive extraction, inject a Pattern 1 constructor-injection surface (per E-13) but do NOT leave a `mh.<name>` lazy-import in the new landing module.
- **FR-029**: Landing targets in the Dispatch Queue are advisory. The PR MAY override the suggestion if a closer semantic fit exists at dispatch time. Overrides are recorded in the PR description with one-sentence rationale (per E-1).
- **FR-030**: Existing tests MUST be converted to the new import path AND the new Pattern 1 construction contract (constructor injection) in the same commit as the extraction. Where the move surfaces a testable seam not previously tested, add a new test — do not defer.
- **FR-031**: No new mypy strict violations may be introduced by any extraction PR. Any pre-existing violations in `MistHelper.py` that touch the extracted symbol MUST be resolved in-flight during the move.
- **FR-032**: This initiative closes the MistHelper.py refactor family for the analyzer's current output. When the last of the 15 PRs merges and `refactor_candidates.md` is regenerated, the report will show only `menu_actions` + `GlobalImportManager`. No further initiative is planned unless net-new extractable symbols are added to `MistHelper.py` by subsequent unrelated work.

### Key Entities *(include if feature involves data)*

- **Extraction Candidate**: A symbol in `MistHelper.py` catalogued by `tools/refactor_analyzer/` — for this initiative, the 15 entries surfaced in `refactor_candidates.md` at commit `8523596` (2026-07-09) minus `menu_actions` (excluded by policy) and `GlobalImportManager` (excluded by `SKIP_ALWAYS`).
- **Refactor Candidates Catalog** (`refactor_candidates.md`): Regenerated after every merged extraction PR (FR-014). The freshest catalog is the authoritative source for dispatch order.
- **Extraction PR**: A single pull request delivering one symbol's move plus its callsite rewrites (both `MistHelper.py` and `src/` and any `tests/`), in-place `guideline_flags` remediation, a NOTE breadcrumb, a callsite table in the description, and updated tests.
- **Target Module**: The new file (or existing module) receiving the extracted symbol. Landing targets are advisory in the Dispatch Queue and may be overridden per FR-029.
- **Callsite**: The exact location where a candidate symbol is instantiated, referenced, or imported. Each PR rewires ALL callsites atomically.
- **Callsite Table**: The mandatory PR-description artifact per FR-027 enumerating the exact file:line list of every rewritten callsite.
- **Dispatch Queue**: The bucket-ordered (Single-use → Low-use → Hot descending-LOC) list of 15 candidates. Ordering is re-derived from the freshest catalog after every merge.
- **Reclassification**: A queue entry whose analyzer category shifts mid-initiative (per FR-020). Recorded in the "Reclassifications" table. Reclassification does NOT remove the entry from scope unless it drops to Unused (in which case the PR becomes a deletion PR).
- **Compliance Baseline**: Repo-wide ≥ 99.6/A+ aggregate; every new/edited module at A+/100; `MistHelper.py` pylint non-regressing; no new mypy strict violations.
- **Pattern 1 (Constructor Injection)**: The extraction landing pattern for hot classes with runtime deps, established by 1013 and 1014. `__init__(self, **deps)` accepting all needed dependencies; every callsite constructs the instance inline with the full kwargs list spelled out. No factory helpers, no module-level cached instance, no self-resolving via `sys.modules`, no `_configure_module()` shims.

## Dispatch Queue

The 15 candidates in dispatch order (bucket-first: Single-use → Low-use → Hot descending by LOC). Each row lands as one PR. Every row is Cat E (fresh cross-package extraction) at initiative start; a reclassification to Cat A would require a mid-initiative parity audit per FR-025.

**Action-type legend**:

- **Cat E — Fresh cross-package extraction**: MistHelper.py holds the real body; callers reference the symbol via direct namespace resolution or `mh = importlib.import_module("MistHelper")` + `mh.<Name>` lazy-imports (for hot candidates with `src/` callers). The PR extracts the body to the landing target, rewires every `MistHelper.py` callsite, AND rewires every `src/` / `tests/` callsite in the same commit (per FR-003 + FR-005 + FR-027).

Bucket / category audit performed 2026-07-09 against all 15 candidates confirmed **15 Cat E** and **0 Cat A**. Zero Cat B (fresh MistHelper-only extractions surviving from the 1013 era) — the analyzer's `Reference sites` field on every hot candidate lists at least one `src/` (or `tests/`) file, matching the 1014 Cat E discipline.

### Single-use bucket (3 tasks)

| # | Task | Kind | Refs | LOC | Symbol | Cat | Landing target | Flags |
|---:|:---:|---|---:|---:|---|:-:|---|---|
| 1 | T-01 | class | 1 | 9 | `DeviceFetchConfig` | E | `src/refactors/device_data_fetcher.py` (fold into `DeviceDataFetcherManager` or top-level dataclass per E-1) | missing_action_logging |
| 2 | T-02 | assignment | 1 | 3 | `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` | E | `src/refactors/fast__mode__max__concurrent__connections.py` (or existing constants module per E-1 / E-14) | missing_inline_comments, missing_action_logging |
| 3 | T-03 | assignment | 1 | 3 | `FAST_MODE_USE_CONNECTION_AWARE_THREADING` | E | `src/refactors/fast__mode__use__connection__aware__threading.py` (or existing constants module per E-1 / E-14) | missing_action_logging |

### Low-use bucket (2 tasks)

| # | Task | Kind | Refs | LOC | Symbol | Cat | Landing target | Flags |
|---:|:---:|---|---:|---:|---|:-:|---|---|
| 4 | T-04 | assignment | 2 | 2327 | `ENDPOINT_PRIMARY_KEY_STRATEGIES` | E | `src/refactors/endpoint__primary__key__strategies.py` (or a domain-fitting `src/api/*.py` per E-1) | oversize_25_lines, missing_inline_comments, missing_action_logging, non_ascii_logs |
| 5 | T-05 | function | 2 | 25 | `detect_msp_privileges` | E | `src/refactors/detect_msp_privileges.py` (or a domain-fitting `src/msp/*.py` per E-1) | missing_action_logging |

### Hot bucket (10 tasks, descending by LOC)

| # | Task | Kind | Refs | LOC | Symbol | Cat | Landing target | Flags |
|---:|:---:|---|---:|---:|---|:-:|---|---|
| 6 | T-06 | class | 102 | 686 | `OrgInventoryExporter` | E | `src/export/org_inventory_exporter.py` | oversize_25_lines, missing_inline_comments |
| 7 | T-07 | class | 96 | 441 | `PromptUtils` | E | `src/ui/prompt_utils.py` | oversize_25_lines |
| 8 | T-08 | class | 118 | 345 | `DataExporter` | E | `src/export/data_exporter.py` | oversize_25_lines, non_ascii_logs |
| 9 | T-10 | class | 69 | 158 | `DataProcessingUtils` | E | `src/data/data_processing_utils.py` | oversize_25_lines, missing_inline_comments, hardcoded_separator |
| 10 | T-11 | class | 104 | 78 | `VirtualChassisManager` | E | `src/device/virtual_chassis.py` (fold-in) | oversize_25_lines, missing_inline_comments, missing_action_logging |
| 11 | T-09 | class | 195 | 74 | `InputUtils` | E | `src/ui/input_utils.py` | oversize_25_lines, raw_input_call |
| 12 | T-12 | class | 102 | 70 | `ConfigUtils` | E | `src/config/config_utils.py` | oversize_25_lines |
| 13 | T-13 | class | 50 | 46 | `FilePathUtils` | E | `src/utils/file_path_utils.py` | oversize_25_lines, missing_inline_comments |
| 14 | T-14 | function | 51 | 3 | `tqdm` | E | `src/utils/tqdm_wrapper.py` (or a domain-fitting `src/ui/*.py` per E-1) | missing_action_logging |
| 15 | T-15 | assignment | 11 | 3 | `MIST_SITE_EXCLUDE_PREFIX` | E | `src/refactors/mist_site_exclude_prefix.py` (or an existing constants module per E-1 / E-14) | missing_inline_comments, missing_action_logging |

**Category distribution**: 15 Cat E + 0 Cat A + 0 Cat B.

**Landing distribution**: `src/refactors/` = 5 (or fewer if E-1 overrides land elsewhere), `src/ui/` = 2 (`prompt_utils.py`, `input_utils.py`), `src/export/` = 2 (`org_inventory_exporter.py`, `data_exporter.py`), `src/utils/` = 1 (`file_path_utils.py`), `src/data/` = 1 (`data_processing_utils.py`), `src/device/` = 1 (fold-in to `virtual_chassis.py`), `src/config/` = 1 (`config_utils.py`), plus 2 destinations pending E-1 override (`tqdm`, `detect_msp_privileges`). Every row lands in a domain-fitting existing or new package; `src/refactors/` is used as a fallback when no closer semantic fit exists.

**Queue-head validation candidates**: The three Single-use candidates cluster at the queue head — `DeviceFetchConfig` (1r/9L, T-01), `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` (1r/3L, T-02), `FAST_MODE_USE_CONNECTION_AWARE_THREADING` (1r/3L, T-03). These are 1-callsite extractions and validate the Cat E workflow at minimum blast radius before the Low-use and Hot PRs.

**Largest-LOC candidate**: T-04 (`ENDPOINT_PRIMARY_KEY_STRATEGIES`, 2327 LoC, 2 refs) is the single largest LOC win in the initiative — a Low-use assignment whose extraction reclaims 2,327 lines from `MistHelper.py` against a mere 2-callsite rewrite. This is the highest-ROI PR in the queue and the primary driver of SC-002.

**Highest-refs candidate**: T-09 (`InputUtils`, 195 refs, 74 LoC) has the highest ref count in the initiative and spans 17 files. The Cat E dual-side rewire touches every `input()` and `safe_input()` callsite across the codebase.

## Deferred Candidates

*(Initially empty. Populated during the initiative if any Dispatch Queue candidate is deferred per FR-013, FR-020, or Edge Case E-6.)*

| # | Task | Symbol | Reason for Deferral | Recording PR / Commit |
|---:|:---:|---|---|---|

### Reclassifications

*(Initially empty. Populated during the initiative if any Cat E → Cat A / Cat A → Cat E reclassification event or a bucket-shift occurs per FR-020.)*

| # | Task | Symbol | Original Bucket / Cat | New Bucket / Cat | Cause | Recording PR / Commit |
|---:|:---:|---|:-:|:-:|---|---|

## Out of Scope

The 2026-07-09 catalog surfaced 17 total entries. This initiative addresses 15. The remaining 2 are **explicitly excluded**:

| # | Refs | LOC | Symbol | Reason |
|---:|---:|---:|---|---|
| 1 | 17 | 887 | `menu_actions` | Deferred indefinitely per user directive. No follow-up initiative planned. |
| 2 | 1 | 1003 | `GlobalImportManager` | Pinned by module-load / bootstrap ordering. `SKIP_ALWAYS` in the analyzer. Static analysis cannot detect the load-order dependency; moving it would break import wiring. |

When this initiative closes, `refactor_candidates.md` regenerated on `main` will show exactly these 2 entries and no others (barring net-new symbols added by unrelated work).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `refactor_candidates.md` regenerated on `main` at initiative completion shows exactly 2 remaining entries — `menu_actions` and `GlobalImportManager` — with all 15 Dispatch Queue candidates removed from every bucket (or, if any deferred, recorded in "Deferred Candidates" with documented rationale).
- **SC-002**: `MistHelper.py` physical line count drops by at least **3,500 lines** relative to the pre-initiative baseline. (Sum of the 15 candidates' LoC in the Dispatch Queue is 4,271 — `ENDPOINT_PRIMARY_KEY_STRATEGIES` alone contributes 2,327; SC-002 gives modest headroom for class-body overhead in new modules and reasonable decomposition retention.)
- **SC-003**: Repository-wide aggregate compliance score is ≥ 99.6/A+ at every intermediate `main`-branch state throughout the initiative and at final completion.
- **SC-004**: Zero files that were A+/100 pre-initiative regress below A+ by the end of the initiative.
- **SC-005**: All extraction PRs merge with 15/15 functional CI jobs green, `mergeStateStatus: CLEAN`, `black --check` clean, `ruff check` clean, `python MistHelper.py --test` reporting 0 failed / exit 0 (modulo the known `test_menu_196_dispatches_to_async_claim_exporter` flake per E-7). Zero `--admin` bypasses except where `mergeStateStatus` was genuinely BLOCKED/DIRTY/BEHIND with root cause documented.
- **SC-006**: Every new file created during the initiative scores A+/100 on compliance.
- **SC-007**: Zero wrapper shims, forwarding functions, re-export modules, delegators, pointers, helpers, or backward-compatibility aliases remain in `MistHelper.py` after the initiative.
- **SC-008**: Zero symbols from the analyzer's `SKIP_ALWAYS` bucket (`GlobalImportManager` for this initiative) are modified by any PR.
- **SC-009**: Zero `importlib.import_module("MistHelper")` + `mh.<Name>` remainders survive for any extracted symbol name — verifiable via post-merge grep against merged `main`.
- **SC-010**: After every merged extraction PR, the analyzer is re-run and `refactor_candidates.md` is regenerated before the next PR is dispatched — verifiable by walking the merged-PR sequence.
- **SC-011**: Every analyzer-flagged `guideline_flag` on each extracted symbol is resolved within the extraction PR — zero forward-carried guideline violations attributable to this initiative.
- **SC-012**: Every extraction PR contains exactly one NOTE breadcrumb at the deletion site in `MistHelper.py` matching the pinned FR-007 template — verifiable via `grep -rn "extracted to .*::" MistHelper.py`.
- **SC-013**: Pre-push local gate: `black --check` and `ruff check` both pass on every refactor branch before the PR opens, and `python MistHelper.py --test` reports 0 failed with exit code 0 (modulo E-7).
- **SC-014**: The workflow processes candidates in bucket-first (Single-use → Low-use → Hot descending by LOC) order derived from the freshest catalog at each dispatch — verifiable by walking the merged-PR sequence against the sequence of regenerated catalog snapshots.
- **SC-015**: `MistHelper.py`'s pylint score is non-regressing against the pre-initiative baseline. No merged PR reduces the score.
- **SC-016**: Zero new SKIPPED conditionals are introduced in CI by any extraction PR.
- **SC-017**: Every extraction PR contains a callsite table in the description matching FR-027 (MistHelper.py + `src/` + tests/ callsites enumerated) — verifiable by PR-description grep.
- **SC-018**: Every extraction PR verifies import-graph health per FR-028 — verifiable by post-merge `python -c "import <landing_module>; print('OK')"` succeeding without traversing `MistHelper.py`.
- **SC-019**: Zero new mypy strict violations are introduced by any extraction PR (per FR-031).
- **SC-020**: `menu_actions` is not touched by any PR in this initiative (per FR-010) — verifiable via post-merge `git log` showing no diff hunks against the `menu_actions` definition or any of its 17 callsites.
- **SC-021**: `GlobalImportManager` is not touched by any PR in this initiative (per FR-009) — verifiable via post-merge `git log` showing no diff hunks against the `GlobalImportManager` class body.
- **SC-022**: The initiative closes with a documented final-state summary in the last-merged PR (or a follow-up docs commit) recording: (a) count of PRs merged (target: 15), (b) final `MistHelper.py` LoC and pylint score, (c) final aggregate compliance score, (d) list of deferred candidates with rationale, (e) confirmation that the regenerated `refactor_candidates.md` shows only `menu_actions` + `GlobalImportManager`.
- **SC-023**: Existing tests are converted to the new import path and Pattern 1 construction contract for every extracted hot class (per FR-030) — verifiable by post-merge grep for the old MistHelper.py import path in `tests/` (zero matches expected for each extracted symbol).

## Assumptions

- The analyzer at `tools/refactor_analyzer/` remains functionally correct across the initiative; discrepancies discovered during extraction are filed as analyzer bugs but do not block extraction PRs.
- The 15 functional CI jobs currently gating PRs on `main` remain the mergeability contract for the duration of this initiative.
- The current compliance baseline (≥ 99.6/A+) is the floor; the initiative does not attempt to raise it beyond preserving it.
- The 15-row Dispatch Queue reflects the 2026-07-09 catalog snapshot regenerated on `origin/main` at commit `8523596`. Mid-initiative reclassification is expected and handled per FR-020 / E-6.
- Serial per-PR workflow: at most one extraction PR is open at any time.
- Analyzer regeneration cost per run is negligible relative to CI cycle time.
- Bucket-first ordering (Single-use → Low-use → Hot descending by LOC within Hot) front-loads the smallest-blast-radius extractions and reserves the highest-LOC / highest-refs candidates (`ENDPOINT_PRIMARY_KEY_STRATEGIES`, `OrgInventoryExporter`, `PromptUtils`, `DataExporter`, `InputUtils`) for later dispatch when the workflow is fully validated.
- Landing targets are advisory; the PR chooses at dispatch time per FR-029.
- The Cat E lazy-import-back-into-MistHelper.py pattern (`mh = importlib.import_module("MistHelper")` + `mh.<Name>`) is exactly the pattern this initiative eliminates for the remaining 10 hot candidates. It is not preserved.
- Black + Ruff pre-push discipline (`feedback_prepush_black_ruff.md`) is followed by the contributor.
- `python MistHelper.py --test` is the initiative's smoke-test contract, run as a merge gate per FR-015, with the known `test_menu_196_dispatches_to_async_claim_exporter` flake exempt (per E-7).
- Constructor injection (Pattern 1) established by 1013/1014 is the landing pattern for every hot class with runtime deps (per E-13). Pure static helpers remain `@staticmethod`.
- `menu_actions` is out of scope by user directive and no follow-up initiative is planned for it. If a future user directive reverses that decision, a new spec will be authored.
- `GlobalImportManager` is out of scope by the analyzer's `SKIP_ALWAYS` policy and no initiative can move it without breaking import wiring. This is a permanent exclusion, not a deferral.
- EMU-related `gh pr create` (401) / MCP `create_pull_request` (403) restrictions carry over from prior initiatives — the contributor opens PRs via the GitHub web URL after `git push` when EMU blocks automated creation.
- After the last PR (T-15 or the final reclassified equivalent) merges and `refactor_candidates.md` is regenerated one final time, no further MistHelper.py refactor initiative is planned. This spec effectively closes the MistHelper.py refactor family for the analyzer's current output.
