# Feature Specification: MistHelper Hot-Classes Refactor (Classes With `src/` Callers)

**Feature Branch**: `1014-misthelper-refactor-hot-classes-with-src-callers`
**Created**: 2026-07-08
**Status**: Draft
**Predecessors**:
- [`1010-misthelper-refactor-extraction`](../1010-misthelper-refactor-extraction/spec.md) — first-pass Unused + Single-Use bucket clearance (13 PRs, closed)
- [`1011-misthelper-refactor-low-use`](../1011-misthelper-refactor-low-use/spec.md) — second-pass 20-candidate Low-Use serial workflow (closed)
- [`1012-misthelper-refactor-hot-functions`](../1012-misthelper-refactor-hot-functions/spec.md) — third-pass Hot-function bounded single-PR bundle (closed)
- [`1013-misthelper-refactor-hot-classes`](../1013-misthelper-refactor-hot-classes/spec.md) — fourth-pass 47-candidate Hot-class serial workflow, MistHelper-only callsite scope (closed)

**Input**: User description: "Fifth-pass Hot-classes serial extraction from `MistHelper.py`. Target the 24 Hot-bucket classes that survived after 1013 completed — every one has at least one `src/` external caller (the scope 1013 deliberately excluded). Two action-types coexist: **Cat A** (facade removal — `src/` already holds authoritative implementation, delete the wrapper and rewire callers) and **Cat E** (fresh cross-package extraction — MistHelper.py holds the real class body while `src/` modules lazy-import it via `importlib.import_module('MistHelper')`; the extraction must atomically rewire MistHelper.py callsites AND every `src/` caller in the same commit). One class per PR (24 PRs). Extraction order: refs ascending, then LOC descending. Same landing pattern as 1013; same CI-clean merge discipline; analyzer score ≥ 99.6/A+; `black --check`, `ruff check`, and `python MistHelper.py --test` all clean."

## Predecessor Context

The four closed predecessor initiatives together cleared the low-friction extraction surface plus the MistHelper-only Hot-class surface:

- **1010** established the extraction contract (FR-003 no wrappers, FR-005 class-body landing, FR-007 project non-negotiables, FR-011 CI-clean merge discipline). It landed 13 PRs against the Unused + Single-Use buckets.
- **1011** extended that contract across 20 Low-Use candidates using a serial per-PR workflow. Its SC-009 explicitly forbade extracting Hot-bucket **source** symbols during that pass.
- **1012** carved out three specific Hot-bucket entries as a bounded single-PR bundle (`tqdm` skip-pin, `is_debug_mode` extraction, and `execute_with_connection_pool_management` + `_pool_*` family). It narrowed 1011's SC-009 prohibition for those three symbols.
- **1013** cleared the 47-candidate MistHelper-only Hot-class surface across 4 Cat A (facade removal) + 43 Cat B (fresh extraction) PRs. Its FR-012 explicitly excluded any Hot-bucket class with a `src/` external caller from scope, deferring those 24 classes to a future initiative. **This initiative is that future initiative.**

All four predecessors closed with analyzer score ≥ 99.6/A+, `black --check` clean, `ruff check` clean, and `python MistHelper.py --test` passing (0 failed, exit 0).

Post-1013 catalog snapshot (regenerated on 2026-07-08 from `origin/main` at 2aacb20): 24 remaining Hot-bucket classes, every one of which has at least one `src/` caller. Twelve MistHelper-only Hot-bucket classes remain unaddressed and are recorded here as **out of scope** — those were the tail-band candidates that 1013 explicitly deferred to a follow-up when its Cat B queue exhausted early (see the "Out of Scope" section below).

This initiative (1014) restores the serial per-PR workflow of 1010/1011/1013 (one class per PR) and introduces one new action-type — **Cat E** — to cover the fresh-cross-package-extraction case where MistHelper.py holds the real class body and `src/` modules import it back via lazy `importlib.import_module("MistHelper")` patterns.

## Scope Boundary

The initiative targets exactly the **24 Hot-bucket classes** whose reference sites include at least one callsite outside `MistHelper.py` (in `src/`, primarily) as confirmed by the audit tool `tools/_scratch_audit_hot_classes.py` run against the post-1013 catalog on 2026-07-08. Extraction order is:

1. Reference count ascending (fewest callers first — smallest blast radius extracts earliest).
2. Ties broken by LOC descending (at the same refs band, bigger LOC lands earlier so the largest surface gets exercised first at that band).

The 24 candidates are enumerated in the "Dispatch Queue" section below. Each row lands as one PR. Two action-type designations coexist in the queue:

- **Cat A — Facade removal** (6 candidates). The `MistHelper.py` class is a delegation wrapper; the real implementation already lives in `src/` at the noted landing target. The PR deletes the facade, rewires every callsite (both `MistHelper.py` and — if the wrapper is imported from `src/` — the corresponding `src/` callers) to reference the `src/` implementation directly, and MUST verify method-parity between facade and real impl before deletion (per FR-025 carry-forward from 1013).
- **Cat E — Fresh cross-package extraction** (18 candidates). No pre-existing `src/` implementation. The class body currently lives in `MistHelper.py`, and one or more `src/` modules import it via `importlib.import_module("MistHelper")` and access `mh.<ClassName>`. The PR (a) creates the target module file inside the landing package, (b) deletes the class body from `MistHelper.py`, (c) rewrites every `MistHelper.py` callsite in the same commit, AND (d) rewrites every `src/` (and any other first-party) callsite in the same commit — replacing the `mh.<ClassName>` lazy-import pattern with a direct import from the new landing module.

Excluded from scope (and explicitly not touched by this initiative):

- The 12 residual MistHelper-only Hot-bucket classes that 1013 did not dispatch (surfaced in the fresh catalog as still MistHelper-only). Those remain deferred to a follow-up initiative (`1015+`) that will restart the MistHelper-only serial workflow if pursued.
- All classes already extracted in 1010, 1011, 1012, or 1013. Those symbols are fully migrated.
- The refactor analyzer itself (`tools/refactor_analyzer/`) — consumed as-is.
- Any Hot-bucket **function** or **assignment** — this initiative is Hot **classes** only. Non-class Hot symbols remain deferred.
- The two Low-Use / Single-Use residuals in the post-1013 catalog — tracked separately.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Extract a Cat A facade by deleting it and rewiring callers to the authoritative `src/` implementation (Priority: P1)

The facade-removal workflow. For each Cat A candidate in the Dispatch Queue, a refactor engineer opens a PR that (a) verifies method-parity between the `MistHelper.py` facade and the corresponding `src/` implementation (audit output recorded in the PR description), (b) deletes the entire facade class body from `MistHelper.py`, (c) rewrites every `MistHelper.py` callsite in the same commit to reference the real `src/` class directly (no `_Impl` alias, no `_configure_module()` helper, no `create()` factory indirection surviving), (d) resolves any analyzer `guideline_flags` in-flight, and (e) lands with all 15 functional CI jobs green, analyzer score ≥ 99.6/A+, `black --check` clean, `ruff check` clean, and `python MistHelper.py --test` passing (0 failed, exit 0). No new file is created. No wrapper shim. No re-export module. No compatibility alias.

**Why this priority**: Delivers the initiative's lowest-risk PRs — the `src/` implementation is already merged and CI-proven, so Cat A carries strictly a callsite-rewrite discipline. Front-loading Cat A within each refs-band validates the workflow before the higher-risk Cat E extractions.

**Independent Test**: Any single Cat A Dispatch Queue candidate (e.g. `RoutingUtils` at 12 refs / 22 LoC, the lowest-refs Cat A) can be merged in isolation. The PR (a) records the method-parity audit output in a fenced code block in the description, (b) deletes the class body from `MistHelper.py`, (c) rewrites all callsites to import from `src/network/routing_utils.py`, (d) leaves a NOTE breadcrumb at the extraction site, and (e) lands green.

**Acceptance Scenarios**:

1. **Given** a Cat A candidate whose `src/` implementation already exists, **When** the extraction PR is opened, **Then** the PR description contains a fenced code block enumerating every public method / static method / classmethod / instance attribute of the facade with the equivalent exposed by the `src/` implementation, and no missing-method row is left un-remediated.
2. **Given** the parity audit surfaces a method absent from the `src/` implementation, **When** the PR is opened, **Then** the PR either (i) ports the missing method to the `src/` class in the same commit and rewires callers, or (ii) is deferred with the gap recorded in the "Deferred Candidates" section.
3. **Given** the facade is deleted, **When** the PR is under CI, **Then** all 15 functional CI jobs are green, the aggregate analyzer score is ≥ 99.6/A+, and no previously A+ file regresses.
4. **Given** the pre-push local gate, **When** the contributor pushes the refactor branch, **Then** `black --check` and `ruff check` both pass locally before the PR opens, and `python MistHelper.py --test` reports 0 failed with exit code 0.

---

### User Story 2 — Extract a Cat E real class from `MistHelper.py` into a cohesive class-body module AND rewire every `src/` lazy importer atomically (Priority: P1)

The novel Cat E workflow — the extraction discipline that this initiative adds on top of the 1013 contract. For each Cat E candidate, MistHelper.py holds the **real** class body while one or more `src/` modules currently reach it via `mh = importlib.import_module("MistHelper")` + `mh.<ClassName>.<method>(...)`. Extraction is inseparable across the two: the class body moves out of MistHelper.py, all MistHelper.py callsites are rewritten, AND every `src/` lazy importer is rewritten to `from src.<package>.<module> import <ClassName>` in the SAME commit. The PR does NOT land in two parts. The pre-dispatch grep audit enumerates the exact set of `src/` callsites to be rewritten and their count is recorded in the PR description alongside the callsite table.

**Why this priority**: Same P1 as User Story 1 because the two are the only value-delivery paths in this initiative. Cat E is the higher-risk of the two: a partial extraction (class body moved but `src/` callers still doing `mh.<ClassName>`) would leave a circular import graph and break `python MistHelper.py --test`. Atomicity is not optional.

**Independent Test**: Any single Cat E Dispatch Queue candidate (e.g. `SSHExecutionConfig` at 5 refs / 8 LoC, the queue head) can be merged in isolation. The PR (a) creates `src/ssh/batch/execution_config.py` (or the mapped landing target from the Dispatch Queue), (b) deletes the class body from `MistHelper.py`, (c) rewrites all MistHelper.py callsites, (d) rewrites all `src/ssh/batch/*.py` lazy-import callsites to `from src.ssh.batch.execution_config import SSHExecutionConfig`, (e) leaves a NOTE breadcrumb at the extraction site, (f) lands green.

**Acceptance Scenarios**:

1. **Given** a Cat E candidate with N `src/` lazy-import callsites, **When** the PR is opened, **Then** the diff shows the class body moved to the landing target, deleted from `MistHelper.py`, and every one of the N `src/` callsites rewritten from `mh.<ClassName>` to a direct import — with zero `importlib.import_module("MistHelper")` + `mh.<ClassName>` combinations surviving for that class name.
2. **Given** the callsite table in the PR description enumerates M `MistHelper.py` callsites and N `src/` callsites, **When** the reviewer runs `grep -rn "<ClassName>" .` against the merged PR, **Then** every match is either in the new landing module, in a `src/` file importing from the landing module, or a NOTE breadcrumb — with zero stale `mh.<ClassName>` matches.
3. **Given** the extracted class carried analyzer `guideline_flags`, **When** the PR lands, **Then** each flag is resolved in-flight — decomposition to ≤ 25 lines per method, `logging.info`/`logging.debug` envelopes on every method, inline comments on every executable line, ASCII-only log literals, `pathlib.Path` in place of `os.path`, `InputUtils.safe_input()` in place of raw `input()`.
4. **Given** the pre-push local gate, **When** the contributor pushes the refactor branch, **Then** `black --check` and `ruff check` both pass, and `python MistHelper.py --test` reports 0 failed with exit code 0 — verifying the atomic rewire kept the import graph healthy.

---

### User Story 3 — Regenerate the analyzer catalog and re-derive dispatch order after every merged extraction (Priority: P2)

Carry-forward of 1010/1011/1013 User Story 3. Reference counts and callsite locations shift as extractions land — a Cat E extraction that removes a `src/` module's `mh.<ClassName>` import may reduce another Hot class's ref count if the two co-occur in the same call chain. After every merged extraction PR in this initiative, the analyzer is re-run against the new `main` head and `refactor_candidates.md` is regenerated before the next PR is dispatched. Refs-ASC / LOC-DESC ordering is applied to the fresh catalog. The Cat A / Cat E designation is re-verified against the fresh catalog — a Cat E candidate whose `src/` callers have all been coincidentally removed by a prior extraction may reclassify to MistHelper-only and drop out of this initiative (see FR-020).

**Why this priority**: Workflow discipline that supports P1 rather than delivering standalone value.

**Independent Test**: After merging any extraction PR, running `python -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md` regenerates the catalog cleanly. The just-extracted class no longer appears in the Hot bucket. Any reference-count shifts on remaining candidates are reflected in the fresh dispatch order derived from the new catalog.

**Acceptance Scenarios**:

1. **Given** an extraction PR has merged to `main`, **When** the next PR is dispatched, **Then** `refactor_candidates.md` has been regenerated on the current `main` head first and the next candidate is selected from that fresh output using Refs-ASC / LOC-DESC.
2. **Given** the regenerated catalog shows a formerly Hot candidate has dropped to Low-Use or below, **When** the dispatcher plans the next PR, **Then** the candidate is deferred out of this initiative and recorded.
3. **Given** the regenerated catalog shows a formerly Cat E candidate has become MistHelper-only (its `src/` callers were removed indirectly), **When** the dispatcher plans the next PR, **Then** the candidate's Cat designation shifts to a MistHelper-only Cat B extraction using 1013's workflow, and the shift is recorded in "Reclassifications" (a subsection under "Deferred Candidates") — extraction proceeds under the new designation.

---

### Edge Cases

- **E-1** — Landing target selection for Cat E. Each Cat E candidate has a suggested landing target in the Dispatch Queue. The dispatch PR MAY override the suggestion at PR time if a closer semantic fit exists. The PR description records the destination-selection rationale in one sentence. When both are viable, prefer the existing semantic package over creating a new `src/refactors/*.py` module.
- **E-2** — Guideline-flag decomposition mid-move. If a Cat E candidate carries `oversize_25_lines` (e.g. `OrgInventoryExporter` at 686 LoC, `PromptUtils` at 441 LoC, `DataExporter` at 345 LoC, `InsightMetricsUtils` at 328 LoC, `CacheUtils` at 264 LoC, `APIFetchUtils` at 221 LoC, `DataProcessingUtils` at 158 LoC), the move includes method-level decomposition per FR-006. Deferral of any flag to a follow-up PR is prohibited.
- **E-3** — Callsite drift between catalog regeneration and PR opening. If the analyzer's recorded line numbers drift, the PR uses fresh grep against the current `main` head at branch time. Line-number drift alone does not block the extraction; only a *count* change (ref count changed, or a Cat A candidate becoming Cat E because a new `src/` caller was added mid-initiative, or a Cat E candidate reclassifying to Cat A because a `src/` module was refactored to fold in the class) triggers deferral or re-classification.
- **E-4** — NOTE breadcrumb at the extraction site. Every extraction PR MUST leave a single-line NOTE breadcrumb at the deletion site in `MistHelper.py` (per FR-007 below): `# NOTE: <ClassName> extracted to <new-module-path>::<ClassName>. See specs/1014-misthelper-refactor-hot-classes-with-src-callers/spec.md.` Silent (breadcrumbless) deletion is rejected.
- **E-5** — Class name collision at destination. If the target destination already contains a class with a name that would collide, rename the incoming class only if renaming is genuinely necessary; otherwise the destination is changed. Record the choice in the PR description.
- **E-6** — Reference count discrepancy between spec-time table and catalog regeneration at dispatch. The 24-row table quotes ref counts as of the 2026-07-08 catalog. If a fresh regeneration at dispatch time shows a candidate's ref count has shifted, the dispatch ordering is re-derived from the fresh catalog per FR-014. The 24-row table is documentation, not a runtime contract.
- **E-7** — `python MistHelper.py --test` regression. If the test-suite invocation begins failing mid-initiative because of an unrelated commit landing on `main`, extraction PRs pause until the underlying regression is fixed.
- **E-8** — Analyzer score regression below 99.6/A+. If any single extraction PR would drop the aggregate analyzer score below 99.6/A+, the PR is revised rather than merged. The score floor is a merge gate.
- **E-9** — SKIPPED CI conditionals. Per `feedback_no_admin_bypass.md`, SKIPPED conditionals are non-blocking and do not count against the 15/15 green tally. `--admin` merge bypass is not used as a routine unblock.
- **E-10** — Very large Cat E candidates: `OrgInventoryExporter` (686 LoC), `PromptUtils` (441 LoC), `DataExporter` (345 LoC), `InsightMetricsUtils` (328 LoC), `CacheUtils` (264 LoC), `APIFetchUtils` (221 LoC). These MUST land as one PR each (no splitting across multiple PRs) but the PR MAY carry substantial internal decomposition to satisfy the ≤ 25-line-per-method rule and the aggregate score floor.
- **E-11** — Circular-import trap. Cat E candidates often have a `src/` module that today lazy-imports MistHelper.py *specifically to avoid* the import cycle that would occur if it did `from MistHelper import <ClassName>` at module-load time. When the class body moves to a fresh landing target, that circular concern MAY re-emerge if the new landing module itself imports symbols still living in `MistHelper.py` (e.g. globals such as `apisession`). The Cat E extraction MUST verify import-graph health post-move — `python -c "import <landing_module>"` must succeed without traversing `MistHelper.py`. If a genuine cycle remains, the extraction MAY inject a small dependency-injection surface (a `configure_*_dependencies()` function pattern already used elsewhere in `src/`) but MUST NOT leave a `mh.<name>` lazy-import in the new module.
- **E-12** — Cat A / Cat E reclassification mid-initiative. If a Cat A candidate has a `src/` file added or extended that adds a new `mh.<facade-class-name>` lazy import between catalog regenerations, the candidate reclassifies to Cat E (the facade cannot be silently deleted while a `src/` caller still references it). Conversely, if a Cat E candidate has its `src/` callers refactored away by an unrelated commit and now reads MistHelper-only, the candidate reclassifies out of this initiative (per FR-020) and is deferred to a follow-up MistHelper-only initiative.
- **E-13** — `dataclass` and small-body candidates. The queue head contains two `@dataclass` bodies (`SSHConnectionConfig` at 9 LoC, `SSHExecutionConfig` at 8 LoC). These extractions still follow the same discipline — cohesive module, callsite rewire in one commit, NOTE breadcrumb — but the `guideline_flags` set is typically empty and the PR is nearly a pure move. These are used deliberately at the queue head to validate the Cat E workflow at minimum blast radius.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The initiative MUST process exactly the 24 Hot-bucket classes enumerated in the Dispatch Queue table in Refs-ASC / LOC-DESC order. Additions require a new SpecKit revision recording the reclassification event.
- **FR-002**: The initiative MUST process exactly one class per PR. Batching multiple classes into a single PR is prohibited (carry-forward from 1010/1011/1013 FR-002).
- **FR-003**: For each candidate, the PR MUST match its **action-type** designation (Cat A or Cat E in the Dispatch Queue):
  - **Cat A — Facade removal**: (a) delete the entire delegation-wrapper class body from `MistHelper.py`, (b) rewrite every `MistHelper.py` callsite to reference the real `src/` implementation directly (no `_Impl` alias, no `_configure_module()` helper, no factory `create()` indirection surviving), (c) do NOT create a new file — the `src/` implementation already exists and is authoritative, (d) verify method-parity per FR-025 before deletion.
  - **Cat E — Fresh cross-package extraction**: (a) create the target module file inside the landing package OR fold into an existing class body within that package when semantically appropriate, (b) delete the original class body from `MistHelper.py`, (c) rewrite every `MistHelper.py` callsite in the same commit, AND (d) rewrite every `src/` (or other first-party) callsite currently using `mh = importlib.import_module("MistHelper")` + `mh.<ClassName>` — replacing the lazy pattern with a direct `from src.<package>.<module> import <ClassName>`.
  - **Both categories**: No wrapper shim, forwarding function, re-export module, or backward-compatibility alias may be left in `MistHelper.py`. (Carry-forward of 1013 FR-003, extended for the Cat E dual-side rewrite.)
- **FR-004**: Every extracted class MUST land as a cohesive class body — either as the top-level class of a new module or folded into an existing class body when semantically appropriate. Bare module-level function/assignment landings are prohibited.
- **FR-005**: For each candidate, all `MistHelper.py` references AND all `src/` (and other first-party) references to the extracted class MUST be rewritten to import from the new location in the same commit as the extraction. Zero stale references — including zero `importlib.import_module("MistHelper")` + `mh.<ClassName>` remainders — may survive the merge. (Extended from 1013 FR-005 to require dual-side atomicity for Cat E.)
- **FR-006**: Analyzer-flagged `guideline_flags` on the moved class MUST be resolved within the same extraction PR — never deferred. Decomposition during the move includes: methods ≤ 25 lines with ≤ 5 params, `logging.info`/`logging.debug` envelopes on every method (`%s` formatting), inline comments on every executable line, ASCII-only log literals, `pathlib.Path` in place of `os.path`, `InputUtils.safe_input()` in place of raw `input()`.
- **FR-007**: A **mandatory** single-line NOTE breadcrumb comment MUST be added at each extraction site in `MistHelper.py`, following the pinned template: `# NOTE: <ClassName> extracted to <new-module-path>::<ClassName>. See specs/1014-misthelper-refactor-hot-classes-with-src-callers/spec.md.` Silent (breadcrumbless) extraction is rejected.
- **FR-008**: All extracted modules MUST comply with project non-negotiables: ASCII-only logs, `InputUtils.safe_input()` for interactive input, `pathlib.Path` in place of `os.path`, inline comments every 5-10 lines, action logging before/after every meaningful action with `%s` formatting, ≤ 25-line methods, ≤ 5 params per function.
- **FR-009**: The initiative MUST NOT touch symbols in the analyzer's `SKIP_ALWAYS` bucket (`GlobalImportManager`, `tqdm`).
- **FR-010**: The initiative MUST NOT re-refactor any class already extracted in 1010, 1011, 1012, or 1013. Those symbols are fully migrated.
- **FR-011**: The initiative MUST NOT modify `tools/refactor_analyzer/` itself; the analyzer is consumed as-is.
- **FR-012**: The initiative MUST NOT touch any of the 12 residual MistHelper-only Hot-bucket classes surfaced in the post-1013 catalog (see "Out of Scope"). Those are the follow-up initiative's scope.
- **FR-013**: Before opening each extraction PR, the workflow MUST run `grep -rn "<ClassName>" src/ tests/` and enumerate every callsite in the PR description. For Cat A, the audit confirms the callsite list matches the facade-removal plan. For Cat E, the audit produces the exact set of `src/` files whose lazy-import lines will be rewritten in the same commit.
- **FR-014**: After every merged extraction PR, the workflow MUST regenerate `refactor_candidates.md` by running the analyzer against the current `main` head before the next PR is dispatched. The next candidate is selected from that fresh catalog using Refs-ASC / LOC-DESC ordering.
- **FR-015**: An extraction PR MUST NOT merge until all 15 functional CI jobs report green AND `mergeStateStatus` is CLEAN AND `black --check` is clean AND `ruff check` is clean AND `python MistHelper.py --test` reports 0 failed with exit code 0. `--admin` merge bypass MUST NOT be used as a routine unblock. Reference `feedback_no_admin_bypass.md` and `feedback_prepush_black_ruff.md`.
- **FR-016**: Every new module under the landing package MUST land at A+/100 compliance score. No file that was previously A+ may regress below A+.
- **FR-017**: The repository-wide aggregate compliance MUST remain ≥ 99.6/A+ after each merged extraction PR.
- **FR-018**: `MistHelper.py`'s pylint score MUST be non-regressing against the pre-initiative baseline established on the first branch commit. Regression blocks merge.
- **FR-019**: No new SKIPPED conditionals in CI may be introduced by any extraction PR.
- **FR-020**: If a candidate's `refactor_candidates.md` classification shifts mid-initiative (Hot → Low-Use, or Cat E → MistHelper-only because `src/` callers were removed indirectly, or Cat A → Cat E because a new `src/` caller was added), the candidate MUST be deferred, reclassified, or re-dispatched per the applicable rule. Force-extracting under a stale classification is prohibited.
- **FR-021**: The initiative MUST NOT introduce new features, new commands, new CLI flags, or user-facing behavior changes.
- **FR-022**: When a candidate class is folded into an existing destination package's class body (rather than a new `src/<pkg>/*.py` module), the existing destination file's compliance grade MUST remain at A+/100 after the fold. If the fold would regress the destination below A+, the destination is changed or the extracted class receives further decomposition within the same PR.
- **FR-023**: The Dispatch Queue's ordering (Refs-ASC / LOC-DESC) is a **dispatch rule**, not a merge order guarantee. Concurrent open PRs are not permitted (one PR open at a time).
- **FR-024**: The initiative is considered complete when the freshest `refactor_candidates.md` shows that all 24 Dispatch Queue candidates have been either (a) extracted and no longer appear in the Hot bucket, or (b) recorded as deferred with documented rationale.
- **FR-025**: Every Cat A (facade-removal) PR MUST verify **method-parity** between the `MistHelper.py` facade and its `src/` counterpart before deletion. Verification: (a) enumerate every public method / static method / classmethod / instance attribute exposed by the facade; (b) confirm each is exposed with a semantically-equivalent signature by the real `src/` implementation; (c) record the audit output in the PR description in a fenced code block. If the facade exposes a method absent from the `src/` implementation, the PR MUST either (i) port the missing method to the `src/` class in the same commit and rewire callers, or (ii) be deferred and the gap recorded in "Deferred Candidates".
- **FR-026**: The Dispatch Queue is ordered purely by Refs-ASC / LOC-DESC across BOTH categories combined — Cat A and Cat E interleave freely. The 1013 practice of front-loading Cat A as a warmup block is not repeated here because Cat A candidates in this queue cluster at higher refs bands and would push their dispatch to the tail; a strict global Refs-ASC ordering better front-loads small-blast-radius extractions regardless of category.
- **FR-027**: Every Cat E PR MUST record a **callsite table** in the PR description enumerating: (a) the total count of `MistHelper.py` callsites rewritten, (b) the exact list of `src/` files (with line numbers) whose lazy-import lines were rewritten, (c) the exact list of any `tests/` or other first-party callsites rewritten. The table is verifiable by post-merge grep. Silent extraction without a callsite table is prohibited.
- **FR-028**: Every Cat E PR MUST verify import-graph health post-move: `python -c "import <landing_module>"` succeeds without traversing `MistHelper.py` (verifiable via `sys.modules` inspection immediately after the import) AND `python MistHelper.py --test` reports 0 failed / exit 0. If a genuine circular import remains after the naive extraction, the PR MAY inject a dependency-injection surface (`configure_*_dependencies()` pattern) but MUST NOT leave a `mh.<name>` lazy-import in the new landing module.
- **FR-029**: Cat E landing targets are advisory in the Dispatch Queue. The PR MAY override the suggestion if a closer semantic fit exists at dispatch time. Overrides are recorded in the PR description with one-sentence rationale (per E-1).
- **FR-030**: This initiative's completion does NOT close the MistHelper Hot-class refactor family. The 12 residual MistHelper-only Hot-bucket classes surfaced in the post-1013 catalog remain for a follow-up initiative. This spec does not attempt to enumerate that follow-up's scope.

### Key Entities *(include if feature involves data)*

- **Extraction Candidate**: A class in `MistHelper.py` catalogued by `tools/refactor_analyzer/` — for this initiative, restricted to Hot-bucket entries (4+ references) whose callsites include at least one `src/` (or other first-party) reference. Enumerated in the Dispatch Queue.
- **Refactor Candidates Catalog** (`refactor_candidates.md`): Regenerated after every merged extraction PR (FR-014). The freshest catalog is the authoritative source for dispatch order.
- **Extraction PR**: A single pull request delivering one class's move plus its callsite rewrites (BOTH `MistHelper.py` and `src/` for Cat E), any in-place `guideline_flags` remediation, and the NOTE breadcrumb.
- **Target Module (Cat E)**: The new file receiving the extracted class body. Landing targets are advisory in the Dispatch Queue and may be overridden per FR-029.
- **Authoritative `src/` Implementation (Cat A)**: The existing `src/` module holding the real class body — the target of the Cat A callsite rewire.
- **Callsite**: The exact location where a candidate class is instantiated, referenced, or imported. Cat A rewires `MistHelper.py` callsites; Cat E rewires BOTH `MistHelper.py` and `src/` (via lazy `mh.<name>`) callsites atomically.
- **Callsite Table (Cat E)**: The mandatory PR-description artifact per FR-027 enumerating the exact file:line list of every rewritten callsite.
- **Dispatch Queue**: The Refs-ASC / LOC-DESC-ordered list of 24 candidates. Ordering is re-derived from the freshest catalog after every merge.
- **Deferred Candidate**: A queue entry removed from active dispatch mid-initiative (per FR-013, FR-020, FR-025-ii, or Edge Case E-6/E-12). Deferrals are recorded in "Deferred Candidates" (initially empty).
- **Compliance Baseline**: Repo-wide ≥ 99.6/A+ aggregate; every new/edited module at A+/100; `MistHelper.py` pylint non-regressing against pre-initiative baseline.

## Dispatch Queue

The 24 candidates in dispatch order, Refs-ASC / LOC-DESC. Each row lands as one PR. Every row carries a **Cat** (action-type) designation and a **Landing target** (destination module or package). No Cat A / Cat E warmup separation — the queue interleaves both categories per FR-026, ordering purely by refs then LOC.

**Action-type legend**:
- **Cat A — Facade removal**: The `MistHelper.py` class is a delegation wrapper; the real implementation already lives in `src/` at the noted landing target. The PR deletes the facade, rewires every callsite to reference the `src/` implementation directly, and verifies method-parity per FR-025.
- **Cat E — Fresh cross-package extraction**: MistHelper.py holds the real class body; `src/` modules import it via lazy `importlib.import_module("MistHelper")` + `mh.<ClassName>`. The PR extracts the class body to the landing target, rewires MistHelper.py callsites, AND rewires every `src/` lazy-import callsite in the same commit (per FR-003 Cat E + FR-005 + FR-027).

Cat A / Cat E audit performed 2026-07-08 against all 24 candidates confirmed **6 Cat A facades** and **18 Cat E fresh-cross-package-extractions**. Zero Cat B (fresh MistHelper-only extractions) — all 24 have external `src/` callers by construction of the initiative's scope. Zero Cat C (name-clash-distinct) entries.

| # | Refs | LOC | Class | Cat | Landing target |
|---:|---:|---:|---|:-:|---|
| 1 | 5 | 8 | SSHExecutionConfig | E | `src/ssh/batch/execution_config.py` |
| 2 | 6 | 22 | SiteAutoUpgradeConfigurator | E | `src/firmware/site_auto_upgrade.py` (fold-in) |
| 3 | 6 | 9 | SSHConnectionConfig | E | `src/ssh/batch/connection_config.py` |
| 4 | 12 | 22 | RoutingUtils | A | `src/network/routing_utils.py` |
| 5 | 15 | 90 | ValidationUtils | E | `src/validation/validation_utils.py` |
| 6 | 27 | 29 | TimeUtils | E | `src/time/time_utils.py` |
| 7 | 33 | 79 | OrgLevelAPFirmwareUpgrader | E | `src/firmware/org_ap_upgrader.py` (fold-in) |
| 8 | 34 | 221 | APIFetchUtils | E | `src/api/api_fetch_utils.py` |
| 9 | 43 | 112 | OrgSiteExporter | E | `src/export/org_site_exporter.py` |
| 10 | 43 | 47 | APICoreFetchUtils | E | `src/api/api_core_fetch_utils.py` |
| 11 | 51 | 328 | InsightMetricsUtils | E | `src/analytics/insight_metrics_utils.py` |
| 12 | 52 | 28 | GatewayStatsExporter | A | `src/gateway/gateway_stats_exporter.py` |
| 13 | 78 | 98 | GatewayExportUtils | A | `src/gateway/gateway_export_utils.py` |
| 14 | 81 | 264 | CacheUtils | E | `src/cache/cache_utils.py` |
| 15 | 82 | 26 | SSHRunnerManager | A | `src/ssh/ssh_runner_manager.py` |
| 16 | 86 | 145 | SiteExportUtils | A | `src/export/site_export_utils.py` |
| 17 | 86 | 46 | FilePathUtils | E | `src/utils/file_path_utils.py` |
| 18 | 90 | 441 | PromptUtils | E | `src/ui/prompt_utils.py` |
| 19 | 104 | 686 | OrgInventoryExporter | E | `src/export/org_inventory_exporter.py` |
| 20 | 104 | 78 | VirtualChassisManager | A | `src/device/virtual_chassis.py` |
| 21 | 125 | 158 | DataProcessingUtils | E | `src/data/data_processing_utils.py` |
| 22 | 146 | 70 | ConfigUtils | E | `src/config/config_utils.py` |
| 23 | 168 | 345 | DataExporter | E | `src/export/data_exporter.py` |
| 24 | 229 | 74 | InputUtils | E | `src/ui/input_utils.py` |

**Category distribution**: 6 Cat A (positions 4, 12, 13, 15, 16, 20) + 18 Cat E (all remaining).

**Landing distribution**: `src/export/` = 5, `src/ssh/` = 2 (Cat E) + 1 (Cat A), `src/api/` = 2, `src/firmware/` = 2 (fold-ins), `src/gateway/` = 2 Cat A, `src/ui/` = 2, `src/utils/` = 1, `src/analytics/` = 1, `src/cache/` = 1, `src/config/` = 1, `src/data/` = 1, `src/device/` = 1 Cat A, `src/network/` = 1 Cat A, `src/time/` = 1, `src/validation/` = 1. Note: `src/refactors/` receives **zero** candidates — every row lands in a domain-fitting existing or new package.

**Cat A method-parity risk flag**: Six Cat A candidates in this initiative each require a full method-parity audit per FR-025 before facade deletion. The highest-fanout Cat A candidate is `SiteExportUtils` (position 16, 86 refs) which the audit script confirms delegates a large number of static methods via `_configure_module()` — the dispatch PR MUST enumerate every static/classmethod exposed by the facade in the parity table.

**Cat E queue-head validation candidates**: The three smallest Cat E candidates cluster at the queue head — `SSHExecutionConfig` (5r/8L, position 1), `SiteAutoUpgradeConfigurator` (6r/22L, position 2), `SSHConnectionConfig` (6r/9L, position 3). Two of the three are `@dataclass` bodies with typically empty `guideline_flags` — deliberately chosen at the queue head to validate the Cat E dual-side callsite-rewrite workflow at minimum blast radius.

## Deferred Candidates

*(Initially empty. Populated during the initiative if any Dispatch Queue candidate is deferred per FR-013, FR-020, FR-025-ii, or Edge Case E-6/E-12.)*

| # | Class | Reason for Deferral | Recording PR / Commit |
|---:|---|---|---|

### Reclassifications

*(Initially empty. Populated during the initiative if any Cat A ↔ Cat E reclassification event occurs per E-12.)*

| # | Class | Original Cat | New Cat | Cause | Recording PR / Commit |
|---:|---|:-:|:-:|---|---|

## Out of Scope

The 2026-07-08 catalog surfaced 36 total Hot-bucket classes. 24 have `src/` external callers (this initiative's queue). The remaining 12 are MistHelper-only and are **explicitly deferred** to a follow-up initiative (`1015+`):

| # | Refs | LOC | Class |
|---:|---:|---:|---|
| 1 | 32 | 251 | GlobalWiredClientReportGenerator |
| 2 | 32 | 245 | GatewayTestExporter |
| 3 | 34 | 179 | DatabaseSchemaUtils |
| 4 | 36 | 127 | TroubleshootUtils |
| 5 | 37 | 110 | FilterOperatorEngine |
| 6 | 46 | 414 | OrgDeviceStatsExporter (may be extracted / verify) |
| 7 | 46 | 396 | DeviceRebootManager |
| 8 | 46 | 289 | ARPCommandManager |
| 9 | 54 | 341 | SiteAnomalyExporter (may be extracted / verify) |
| 10 | 54 | 273 | OfflineDeviceReporter |
| 11 | 66 | 475 | OrgTicketManager |
| 12 | 110 | 653 | OrgExportUtils |

Any of these 12 candidates may have been dispatched in 1013 already; a follow-up initiative will re-audit against the freshest catalog before starting. This list is a snapshot, not a scope statement for the follow-up.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Hot bucket of `refactor_candidates.md` reports **zero** of the 24 Dispatch Queue classes at initiative completion, OR each remaining Dispatch Queue class is recorded in the "Deferred Candidates" section with documented rationale.
- **SC-002**: `MistHelper.py` physical line count drops by at least **3,000 lines** relative to the pre-initiative baseline. (Sum of the 24 candidates' LoC in the Dispatch Queue is ~3,395; SC-002 gives modest headroom for class-body overhead in new modules and reasonable decomposition retention.)
- **SC-003**: Repository-wide aggregate compliance score is ≥ 99.6/A+ at every intermediate `main`-branch state throughout the initiative and at final completion.
- **SC-004**: Zero files that were A+/100 pre-initiative regress below A+ by the end of the initiative.
- **SC-005**: All extraction PRs merge with 15/15 functional CI jobs green, `mergeStateStatus: CLEAN`, `black --check` clean, `ruff check` clean, `python MistHelper.py --test` reporting 0 failed / exit 0. Zero `--admin` bypasses except where `mergeStateStatus` was genuinely BLOCKED/DIRTY/BEHIND with root cause documented.
- **SC-006**: Every new file created during the initiative scores A+/100 on compliance.
- **SC-007**: Zero wrapper shims, forwarding functions, re-export modules, or backward-compatibility aliases remain in `MistHelper.py` after the initiative.
- **SC-008**: Zero symbols from the analyzer's `SKIP_ALWAYS` bucket (`GlobalImportManager`, `tqdm`) are modified by any PR in this initiative.
- **SC-009**: Zero `importlib.import_module("MistHelper")` + `mh.<ClassName>` remainders survive for any Cat E-extracted class name — verifiable via post-merge grep against the merged `main`.
- **SC-010**: After every merged extraction PR, the analyzer is re-run and `refactor_candidates.md` is regenerated before the next PR is dispatched — verifiable by walking the merged-PR sequence.
- **SC-011**: Every analyzer-flagged `guideline_flag` on each extracted class is resolved within the extraction PR — zero forward-carried guideline violations attributable to this initiative.
- **SC-012**: Every extraction PR contains exactly one NOTE breadcrumb at the deletion site in `MistHelper.py` matching the pinned FR-007 template — verifiable via `grep -rn "extracted to .*::" MistHelper.py`.
- **SC-013**: Pre-push local gate: `black --check` and `ruff check` both pass on every refactor branch before the PR opens, and `python MistHelper.py --test` reports 0 failed with exit code 0.
- **SC-014**: The workflow processes candidates in Refs-ASC / LOC-DESC order derived from the freshest catalog at each dispatch — verifiable by walking the merged-PR sequence against the sequence of regenerated catalog snapshots.
- **SC-015**: `MistHelper.py`'s pylint score is non-regressing against the pre-initiative baseline. No merged PR reduces the score.
- **SC-016**: Zero new SKIPPED conditionals are introduced in CI by any extraction PR. Pre-existing SKIPPED conditionals remain non-blocking per Edge Case E-9.
- **SC-017**: Every Cat A PR contains a fenced-code-block method-parity audit in the description matching FR-025 — verifiable by PR-description grep.
- **SC-018**: Every Cat E PR contains a callsite table in the description matching FR-027 (MistHelper.py + `src/` + tests/ callsites enumerated) — verifiable by PR-description grep.
- **SC-019**: Every Cat E PR verifies import-graph health per FR-028 — verifiable by post-merge `python -c "import <landing_module>; print('OK')"` succeeding without side effects.
- **SC-020**: The initiative closes with a documented final-state summary in the last-merged PR (or a follow-up docs commit) recording: (a) count of PRs merged (target: 24), (b) final `MistHelper.py` LoC and pylint score, (c) final aggregate compliance score, (d) list of deferred candidates with rationale, (e) count of remaining Hot-bucket classes.

## Assumptions

- The analyzer at `tools/refactor_analyzer/` remains functionally correct for the Hot bucket across the initiative; discrepancies discovered during extraction are filed as analyzer bugs but do not block extraction PRs.
- The 15 functional CI jobs currently gating PRs on `main` remain the mergeability contract for the duration of this initiative.
- The current compliance baseline (≥ 99.6/A+) is the floor; the initiative does not attempt to raise it beyond preserving it.
- The 24-row Dispatch Queue reflects the 2026-07-08 catalog snapshot regenerated from `origin/main` at 2aacb20. Mid-initiative reclassification is expected and handled per FR-020 / E-12.
- Serial per-PR workflow: at most one extraction PR is open at any time.
- Analyzer regeneration cost per run is negligible relative to CI cycle time.
- Refs-ASC / LOC-DESC ordering front-loads the smallest-blast-radius extractions and back-loads the largest-LoC candidates. Global ordering across Cat A + Cat E per FR-026 (no warmup separation).
- Cat E landing targets are advisory; the PR chooses at dispatch time per FR-029.
- The Cat E lazy-import-back-into-MistHelper.py pattern (`mh = importlib.import_module("MistHelper")` + `mh.<ClassName>`) is the exact `src/`-side pattern that this initiative eliminates. It is not a design pattern to preserve; it is an interim workaround for the circular-import problem that class extraction resolves definitively.
- Black + Ruff pre-push discipline (`feedback_prepush_black_ruff.md`) is followed by the contributor.
- `python MistHelper.py --test` is the initiative's smoke-test contract, run as a merge gate per FR-015.
- The 12 MistHelper-only Hot-bucket residuals surfaced in the post-1013 catalog are outside scope; a future initiative addresses them separately.
- EMU-related `gh pr create` (401) / MCP `create_pull_request` (403) restrictions carry over from prior initiatives — the contributor opens PRs via the GitHub web URL after `git push` when EMU blocks automated creation.
