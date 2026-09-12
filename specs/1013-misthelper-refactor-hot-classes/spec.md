# Feature Specification: MistHelper Hot-Classes Refactor (MistHelper-Only References)

**Feature Branch**: `1013-misthelper-refactor-hot-classes`
**Created**: 2026-07-07
**Status**: Draft
**Predecessors**:
- [`1010-misthelper-refactor-extraction`](../1010-misthelper-refactor-extraction/spec.md) — first-pass Unused + Single-Use bucket clearance (13 PRs, closed)
- [`1011-misthelper-refactor-low-use`](../1011-misthelper-refactor-low-use/spec.md) — second-pass 20-candidate Low-Use serial workflow (closed)
- [`1012-misthelper-refactor-hot-functions`](../1012-misthelper-refactor-hot-functions/spec.md) — third-pass Hot-function bounded single-PR bundle (closed)

**Input**: User description: "Fourth-pass Hot-classes serial extraction from `MistHelper.py`. Target the 47 Hot-bucket classes in `refactor_candidates.md` whose reference sites are exclusively inside `MistHelper.py` (no `src/` callers). One class per PR (47 PRs). Extraction order: refs ascending, then LOC descending. Mirrors the 1010/1011 landing pattern; deliberately does NOT bundle like 1012. Each PR delivers class-body extraction, all-callsite rewrite, in-flight `guideline_flags` remediation, analyzer score ≥ 99.6/A+, black + ruff + `python MistHelper.py --test` all clean."

## Predecessor Context

The three closed predecessor initiatives together cleared the low-friction extraction surface:

- **1010** established the extraction contract (FR-003 no wrappers, FR-005 class-body landing, FR-007 project non-negotiables, FR-011 CI-clean merge discipline). It landed 13 PRs against the Unused + Single-Use buckets.
- **1011** extended that contract across 20 Low-Use candidates using a serial per-PR workflow. Its SC-009 explicitly forbade extracting Hot-bucket **source** symbols during that pass.
- **1012** carved out three specific Hot-bucket entries as a bounded single-PR bundle (`tqdm` skip-pin, `is_debug_mode` extraction, and `execute_with_connection_pool_management` + `_pool_*` family). It narrowed 1011's SC-009 prohibition for those three symbols and expressly kept the remainder of the Hot bucket deferred.

All three predecessors closed with analyzer score ≥ 99.6/A+, `black --check` clean, `ruff check` clean, and `python MistHelper.py --test` passing (0 failed, exit 0). The residuals in the current post-1012 catalog are 0 Unused / 1 Single-Use / 2 Low-Use (tracked separately) and 76 Hot classes still awaiting extraction — of which 47 are the subject of this initiative.

This initiative (1013) restores the serial per-PR workflow of 1010/1011 (one class per PR) rather than the bounded-bundle pattern of 1012. Each Hot-class extraction gets its own PR, its own analyzer regeneration, and its own CI-clean merge.

## Scope Boundary

The initiative targets exactly the **47 Hot-bucket classes** whose reference sites are exclusively inside `MistHelper.py` — i.e. no `src/`, `tests/`, or other first-party module references. Extraction order is:

1. Reference count ascending (fewest callers first — smallest blast radius extracts earliest).
2. Ties broken by LOC descending (at the same refs band, bigger LOC lands earlier so the largest surface gets exercised first at that band).

The 47 candidates are enumerated in the "Dispatch Queue" section below, quoted verbatim from the user-supplied ordered table. Each row lands as one PR.

Excluded from scope (and explicitly not touched by this initiative):

- The 29 Hot-bucket classes whose reference sites include any callsite outside `MistHelper.py` (any `src/` reference). Those remain deferred to a future initiative that will need multi-file rewrite discipline analogous to 1011's User Story 2.
- All classes already extracted in 1010, 1011, or 1012.
- The refactor analyzer itself (`tools/refactor_analyzer/`) — consumed as-is.
- Any Hot-bucket **function** or **assignment** — this initiative is Hot **classes** only. Non-class Hot symbols remain deferred.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Extract a low-reference Hot class into a cohesive class-body module (Priority: P1)

The core value-delivery workflow. For each Hot-bucket class in the Dispatch Queue whose 4-plus references are all inside `MistHelper.py`, a refactor engineer opens a PR that (a) moves the class body into a new cohesive module under `src/refactors/` (or, when the class semantically belongs to an existing package such as `src/export/`, `src/gateway/`, `src/site/`, folds into that package), (b) rewrites every `MistHelper.py` callsite in the same commit, (c) deletes the original class definition from `MistHelper.py`, (d) resolves any analyzer `guideline_flags` in-flight (decomposing during the move rather than deferring), and (e) lands with all 15 functional CI jobs green, analyzer score ≥ 99.6/A+, `black --check` clean, `ruff check` clean, and `python MistHelper.py --test` passing (0 failed, exit 0). No wrapper shims. No re-export modules. No compatibility aliases.

**Why this priority**: Delivers the initiative's entire LoC drop and constitutes its unit of progress. Serial per-PR dispatch (one class per PR) preserves the mergeability contract that 1010/1011 proved out and keeps every intermediate `main` state analyzer-green. Refs-ascending, LOC-descending dispatch ordering front-loads the smallest-blast-radius extractions so the workflow validates against low-refs classes before the 128-refs `OrgExportUtils` monolith at the tail.

**Independent Test**: Any single Dispatch Queue candidate (e.g. `OrgConfigMigrationManager` at 4 refs / 675 LoC, the queue's first entry) can be merged in isolation. The PR (a) creates `src/refactors/org_config_migration_manager.py` (or folds into an existing fitting package), (b) deletes the class body from `MistHelper.py`, (c) rewrites all 4 callsites, (d) leaves a NOTE breadcrumb at the extraction site, (e) lands with the analyzer reporting the class removed from Hot and the aggregate score still ≥ 99.6/A+, and (f) passes `black --check`, `ruff check`, and `python MistHelper.py --test` (0 failed, exit 0).

**Acceptance Scenarios**:

1. **Given** a Hot-bucket class whose 4-plus callsites are all inside `MistHelper.py`, **When** the extraction PR is opened, **Then** the target module file exists at the mapped path, the original class body is deleted from `MistHelper.py`, every listed callsite is rewritten to import from the new module, and no wrapper shim, forwarding function, or re-export module exists anywhere in the diff.
2. **Given** the analyzer flagged the moved class with `guideline_flags` (e.g. `oversize_25_lines`, `missing_inline_comments`, `missing_action_logging`, `non_ascii_logs`, `hardcoded_separator`, `raw_input_call`), **When** the extraction PR lands, **Then** each flagged violation is resolved during the move — methods ≤ 25 lines with ≤ 5 params, `logging.info`/`logging.debug` envelopes on every method, inline comments on every executable line, ASCII-only log literals, `pathlib.Path` in place of `os.path`, and `InputUtils.safe_input()` in place of raw `input()`.
3. **Given** an extraction PR is under CI, **When** the pipeline completes, **Then** all 15 functional CI jobs are green, the new/edited module scores A+/100 on compliance, and no previously A+ file regresses.
4. **Given** the freshly regenerated `refactor_candidates.md`, **When** dispatching the next PR, **Then** candidates are processed in Refs-ASC / LOC-DESC order from the fresh catalog, so any candidate whose reference count shifted mid-initiative is re-ranked before it becomes the next dispatch head.
5. **Given** the pre-push local gate, **When** the contributor pushes the refactor branch, **Then** `black --check` and `ruff check` both pass locally before the PR opens, and `python MistHelper.py --test` reports 0 failed with exit code 0.

---

### User Story 2 — Preserve strict callsite exclusivity so no `src/`-callsite class is touched (Priority: P1)

The initiative's scoping discipline. The 47 Dispatch Queue candidates are precisely those Hot-bucket classes whose call sites are exclusively inside `MistHelper.py`. Every extraction PR must, before opening, verify via grep that the target class has zero references from `src/`, `tests/`, or any other first-party path outside `MistHelper.py`. If verification surfaces an external caller (e.g. because a merge landed between catalog regeneration and PR opening that added a new `src/` reference), the PR is deferred and the candidate is moved to the excluded 29-class deferred pool.

**Why this priority**: Same P1 as User Story 1 because the two are inseparable — extraction without this verification risks silently breaking an external caller. Deferral is the correct response to a discovered external caller; force-extracting under the MistHelper-only assumption would be an FR-002 violation.

**Independent Test**: Before opening any Dispatch Queue PR, `grep -rn "<ClassName>" src/ tests/` returns zero matches. If matches surface, the candidate is deferred, the deferral is recorded in the PR description of the *next* dispatched candidate (or in a standalone commit that updates this spec's "Deferred Candidates" section), and the workflow continues from the next queue head.

**Acceptance Scenarios**:

1. **Given** a Dispatch Queue candidate at the top of the queue, **When** the pre-dispatch grep audit runs, **Then** it confirms zero references to the class from `src/`, `tests/`, or any first-party path other than `MistHelper.py`, and the PR proceeds.
2. **Given** the pre-dispatch grep audit surfaces an external caller (e.g. a new `src/export/*` file imported the class between catalog regenerations), **When** the dispatcher plans the PR, **Then** the candidate is skipped, the skip is recorded in this spec's "Deferred Candidates" section, and the workflow advances to the next queue head.
3. **Given** the extraction PR is under review, **When** the reviewer runs the same grep against the merged `main`, **Then** the audit continues to return zero external matches — no ninja imports have crept in during the review window.

---

### User Story 3 — Regenerate the analyzer catalog and update dispatch order after every merged extraction (Priority: P2)

Carry-forward of 1010/1011 User Story 3. Reference counts shift as extractions land — a class that removes 3 callers from `MistHelper.py` may reduce another class's ref count if the two share upstream/downstream call chains. After every merged extraction PR in this initiative, the analyzer is re-run against the new `main` head and `refactor_candidates.md` is regenerated before the next PR is dispatched. Refs-ASC / LOC-DESC ordering is applied to the fresh catalog, so a mid-initiative reference-count shift can re-rank the remaining candidates.

**Why this priority**: Workflow discipline that supports P1 and P2 rather than delivering standalone value. Particularly important for the tail of the queue where the largest LoC candidates cluster (`OrgTicketManager` at 66 refs / 475 LoC, `DeviceUtilityCommands` at 70 refs / 188 LoC, `OrgExportUtils` at 128 refs / 653 LoC) — ripple effects from earlier extractions can shift their ref counts and reorder them within the tail band.

**Independent Test**: After merging any extraction PR, running `python -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md` regenerates the catalog cleanly. The just-extracted class no longer appears in the Hot bucket. Any reference-count shifts on remaining candidates are reflected in the fresh dispatch order derived from the new catalog.

**Acceptance Scenarios**:

1. **Given** an extraction PR has merged to `main`, **When** the next PR is dispatched, **Then** `refactor_candidates.md` has been regenerated on the current `main` head first and the next candidate is selected from that fresh output using Refs-ASC / LOC-DESC.
2. **Given** the regenerated catalog shows a formerly Hot candidate has dropped to Low-Use or below (e.g. an earlier extraction removed 3 of its 4 references indirectly), **When** the dispatcher plans the next PR, **Then** the candidate is deferred out of this initiative (it no longer belongs to the Hot bucket) and the deferral is recorded.
3. **Given** the regenerated catalog shows a formerly excluded (external-caller) candidate has become MistHelper-only (e.g. a `src/` caller was itself removed by an unrelated refactor), **When** the dispatcher plans the next PR, **Then** the candidate MAY be added to the dispatch queue only via an explicit spec revision recording the reclassification — it is not silently added mid-initiative.

---

### Edge Cases

- **E-1** — Destination package selection. Some candidates fit an existing package cleanly (`SiteConfigExporter` → `src/site/`, `OrgAlarmEventExporter` → `src/export/`, `GatewayTemplateConfigManager` → `src/gateway/`); others have no obvious existing home and land in `src/refactors/`. The PR description MUST record the destination-selection rationale in one sentence. When both are viable, prefer the existing semantic package over `src/refactors/`.
- **E-2** — Guideline-flag decomposition mid-move. If a candidate carries `oversize_25_lines` (e.g. `ConstDefinitionsExporter` at 759 LoC or `OrgConfigMigrationManager` at 675 LoC), the move includes method-level decomposition: split methods > 25 lines into helpers each ≤ 25 lines with ≤ 5 params, add inline comments on every executable line, wrap every method body with `logging.info`/`logging.debug` envelopes, convert non-ASCII log literals to ASCII, replace `os.path` with `pathlib.Path`, replace raw `input()` with `InputUtils.safe_input()`. Deferral of any flag to a follow-up PR is prohibited (FR-006 carry-forward).
- **E-3** — Callsite drift between catalog regeneration and PR opening. If the analyzer's recorded line numbers drift (line-number churn from unrelated commits landing on `main` after the catalog was regenerated), the PR uses fresh grep against the current `main` head at branch time. Line-number drift alone does not block the extraction; only a *count* change (ref count changed or an external `src/` caller appeared) triggers deferral.
- **E-4** — NOTE breadcrumb at the extraction site. Every extraction PR MUST leave a single-line NOTE breadcrumb at the deletion site in `MistHelper.py` pointing to the new location and this spec (per FR-007 below): `# NOTE: <ClassName> extracted to <new-module-path>::<ClassName>. See specs/1013-misthelper-refactor-hot-classes/spec.md.` Silent (breadcrumbless) deletion is rejected.
- **E-5** — Class name collision at destination. If the target destination already contains a class with a name that would collide (unlikely but possible for common names like `DeviceUtils`), rename the incoming class only if renaming is genuinely necessary; otherwise the destination is changed. Record the choice in the PR description.
- **E-6** — Reference count discrepancy between spec-time table and catalog regeneration at dispatch. The user-supplied 47-row table quotes ref counts as of the post-1012 catalog. If a fresh regeneration at dispatch time shows a candidate's ref count has shifted, the dispatch ordering is re-derived from the fresh catalog per User Story 3. The 47-row table is documentation, not a runtime contract.
- **E-7** — `python MistHelper.py --test` regression. If the test-suite invocation begins failing mid-initiative because of an unrelated commit landing on `main`, extraction PRs pause until the underlying regression is fixed. The extraction workflow does not attempt to work around a broken test suite.
- **E-8** — Analyzer score regression below 99.6/A+. If any single extraction PR would drop the aggregate analyzer score below 99.6/A+, the PR is revised (typically by resolving additional guideline flags in the same PR) rather than merged. The score floor is a merge gate.
- **E-9** — SKIPPED CI conditionals. Per `feedback_no_admin_bypass.md`, SKIPPED conditionals (jobs whose gating condition evaluates false in a normal PR context) are recognised as non-blocking and do not count against the 15/15 green tally. `--admin` merge bypass is not used as a routine unblock.
- **E-10** — Very large candidates (`OrgExportUtils` at 653 LoC / 128 refs, `OrgTicketManager` at 475 LoC / 66 refs, `OrgConfigMigrationManager` at 675 LoC / 4 refs, `OrgDeviceStatsExporter` at 414 LoC / 58 refs, `DeviceRebootManager` at 396 LoC / 46 refs, `MSPInventoryExporter` at 386 LoC / 5 refs, `SiteAnomalyExporter` at 341 LoC / 54 refs, `APIDataFetcher` at 328 LoC / 16 refs, `OrgConfigExporter` at 168 LoC / 24 refs but often internally sprawling, `BulkRadiusWLANConfigManager` at 587 LoC / 13 refs). These MUST land as one PR each (no splitting across multiple PRs) but the PR MAY carry substantial internal decomposition (Edge Case E-2) to satisfy the ≤ 25-line-per-method rule and the aggregate score floor.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The initiative MUST process exactly the 47 Hot-bucket classes enumerated in the Dispatch Queue table in Refs-ASC / LOC-DESC order. Additions require a new SpecKit revision recording the reclassification event.
- **FR-002**: The initiative MUST process exactly one class per PR. Batching multiple classes into a single PR is prohibited (contrast with 1012's bounded-bundle pattern, which is not repeated here).
- **FR-003**: For each candidate, the PR MUST match its **action-type** designation (Cat A or Cat B in the Dispatch Queue):
  - **Cat A — Facade removal**: (a) delete the entire delegation-wrapper class body from `MistHelper.py`, (b) rewrite every `MistHelper.py` callsite to reference the real `src/` implementation directly (no `_Impl` alias, no `_configure_module()` helper, no factory `create()` indirection surviving), (c) do NOT create a new file — the `src/` implementation already exists and is authoritative, (d) verify method-parity per FR-025 before deletion.
  - **Cat B — Fresh extraction**: (a) create the target module file inside the landing package OR fold into an existing class body within that package when semantically appropriate, (b) delete the original class body from `MistHelper.py`, and (c) rewrite every `MistHelper.py` callsite in the same commit.
  - **Both categories**: No wrapper shim, forwarding function, re-export module, or backward-compatibility alias may be left in `MistHelper.py`. (Constitution FR-003 carry-forward, extended to formalize the two action-types.)
- **FR-004**: Every extracted class MUST land as a cohesive class body — either as the top-level class of a new module or folded into an existing class body when semantically appropriate. Bare module-level function/assignment landings are prohibited (carry-forward from 1010/1011 FR-005).
- **FR-005**: For each candidate, all `MistHelper.py` references to the extracted class MUST be rewritten to import from the new location in the same commit as the extraction. Zero stale references may survive the merge.
- **FR-006**: Analyzer-flagged `guideline_flags` on the moved class (`oversize_25_lines`, `missing_inline_comments`, `missing_action_logging`, `non_ascii_logs`, `hardcoded_separator`, `raw_input_call`, and any other flags surfaced) MUST be resolved within the same extraction PR — never deferred to a follow-up. Decomposition during the move includes: methods ≤ 25 lines with ≤ 5 params, `logging.info`/`logging.debug` envelopes on every method (with `%s` placeholder formatting), inline comments on every executable line, ASCII-only log literals, `pathlib.Path` in place of `os.path`, and `InputUtils.safe_input()` in place of raw `input()`. (Carry-forward from 1010/1011 FR-006.)
- **FR-007**: A **mandatory** single-line NOTE breadcrumb comment MUST be added at each extraction site in `MistHelper.py`, following the pinned template: `# NOTE: <ClassName> extracted to <new-module-path>::<ClassName>. See specs/1013-misthelper-refactor-hot-classes/spec.md.` Silent (breadcrumbless) extraction is explicitly rejected. Breadcrumb presence at the extraction site is verified by the PR reviewer's grep audit.
- **FR-008**: All extracted modules and destination files MUST comply with project non-negotiables: ASCII-only logs, `InputUtils.safe_input()` for interactive input, `pathlib.Path` in place of `os.path`, inline comments every 5-10 lines, action logging before/after every meaningful action with `%s` formatting, ≤ 25-line methods, ≤ 5 params per function (carry-forward from 1010/1011/1012 FR-007).
- **FR-009**: The initiative MUST NOT touch symbols in the analyzer's `SKIP_ALWAYS` bucket (`GlobalImportManager`, and `tqdm` by convention per 1012) (carry-forward from 1010/1011/1012 FR-008).
- **FR-010**: The initiative MUST NOT re-refactor any class that was already extracted in 1010, 1011, or 1012. Those symbols are considered fully migrated and are outside scope.
- **FR-011**: The initiative MUST NOT modify `tools/refactor_analyzer/` itself; the analyzer is consumed as-is (carry-forward from 1010/1011/1012 FR-018).
- **FR-012**: The initiative MUST NOT touch any Hot-bucket class whose references include any callsite outside `MistHelper.py` (any reference from `src/`, `tests/`, or any other first-party path). Those 29 classes are the deferred pool and are not in scope for this initiative.
- **FR-013**: Before opening each extraction PR, the workflow MUST run `grep -rn "<ClassName>" src/ tests/` (and any additional first-party paths surfaced by the module graph) and confirm zero matches. If any match is found, the candidate is deferred and recorded in the "Deferred Candidates" section of this spec.
- **FR-014**: After every merged extraction PR, the workflow MUST regenerate `refactor_candidates.md` by running the analyzer against the current `main` head before the next PR is dispatched. The next candidate is selected from that fresh catalog using Refs-ASC / LOC-DESC ordering (carry-forward from 1010/1011 FR-010).
- **FR-015**: An extraction PR MUST NOT merge until all 15 functional CI jobs report green AND `mergeStateStatus` is CLEAN AND `black --check` is clean AND `ruff check` is clean AND `python MistHelper.py --test` reports 0 failed with exit code 0. `--admin` merge bypass MUST NOT be used as a routine unblock. Reference `feedback_no_admin_bypass.md` and `feedback_prepush_black_ruff.md` (carry-forward from 1010/1011/1012 FR-011).
- **FR-016**: Every new module under `src/refactors/` (or extended module in an existing destination package) MUST land at A+/100 compliance score. No file that was previously A+ may regress below A+ as a result of any extraction (carry-forward from 1010/1011/1012 FR-012).
- **FR-017**: The repository-wide aggregate compliance MUST remain ≥ 99.6/A+ after each merged extraction PR (carry-forward from 1010/1011/1012 FR-013).
- **FR-018**: `MistHelper.py`'s pylint score MUST be non-regressing against the pre-initiative baseline established on the first branch commit. Regression blocks merge for the PR that caused it.
- **FR-019**: No new SKIPPED conditionals in CI may be introduced by any extraction PR (per the user-specified "no new SKIPPED conditionals" gate). SKIPPED conditionals that pre-date the initiative continue to be non-blocking per Edge Case E-9.
- **FR-020**: If a candidate's `refactor_candidates.md` classification shifts mid-initiative (e.g. Hot → Low-Use because a prior extraction removed several of its references indirectly), the candidate MUST be deferred out of this initiative and recorded in "Deferred Candidates". Force-extracting under a stale classification is prohibited (carry-forward from 1010/1011/1012 FR-016).
- **FR-021**: The initiative MUST NOT introduce new features, new commands, new CLI flags, or user-facing behavior changes. Extraction is source-level only; user-facing behavior is preserved exactly (carry-forward from 1010/1011/1012 FR-017).
- **FR-022**: When a candidate class is folded into an existing destination package's class body (rather than a new `src/refactors/*.py` module), the existing destination file's compliance grade MUST remain at A+/100 after the fold. If the fold would regress the destination below A+, the destination is changed or the extracted class receives further decomposition within the same PR.
- **FR-023**: The Dispatch Queue's ordering (Refs-ASC / LOC-DESC) is a **dispatch rule**, not a merge order guarantee. If a PR later in the queue is ready to merge before an earlier PR because the earlier PR is under revision, the later PR MAY merge first — but only if the earlier PR is deferred or withdrawn. Concurrent open PRs are not permitted (one PR open at a time per FR-002's serial workflow).
- **FR-024**: The initiative is considered complete when the freshest `refactor_candidates.md` shows that all 47 Dispatch Queue candidates have been either (a) extracted and no longer appear in the Hot bucket, or (b) recorded as deferred in the "Deferred Candidates" section with documented rationale.
- **FR-025**: Every Cat A (facade-removal) PR MUST verify **method-parity** between the `MistHelper.py` facade and its `src/` counterpart before deletion. Verification consists of: (a) enumerating every public method, static method, classmethod, and instance attribute exposed by the facade; (b) confirming each is exposed with a semantically-equivalent signature by the real `src/` implementation; (c) recording the audit output in the PR description in a fenced code block. If the facade exposes a method absent from the `src/` implementation, the PR MUST either (i) port the missing method to the `src/` class in the same commit and rewire callers, or (ii) be deferred and the gap recorded in "Deferred Candidates". Silent facade deletion without a parity audit is prohibited. This applies with particular rigour to `DeviceUtilityCommands` at dispatch position 4, whose facade fans out to 35 operation-subclasses.
- **FR-026**: The Dispatch Queue orders the 4 Cat A candidates first (positions 1-4) as a warmup ahead of the 43 Cat B candidates. This ordering is deliberate: Cat A carries a lower semantic risk (the `src/` implementation is already merged and CI-proven) and validates the initiative's callsite-rewrite discipline against a smaller edit surface before the fresh-extraction workflow begins at position 5. Within the Cat A block, ordering is Refs-ASC / LOC-DESC (same rule as Cat B). Within the Cat B block, ordering is Refs-ASC / LOC-DESC from the freshest catalog per FR-014.

### Key Entities *(include if feature involves data)*

- **Extraction Candidate**: A class in `MistHelper.py` catalogued by `tools/refactor_analyzer/` — for this initiative, restricted to Hot-bucket entries (4+ references) whose callsites are all inside `MistHelper.py`. Enumerated in the Dispatch Queue table.
- **Refactor Candidates Catalog** (`refactor_candidates.md`): Regenerated after every merged extraction PR (FR-014). The freshest catalog is the authoritative source for dispatch order.
- **Extraction PR**: A single pull request delivering one class's move plus its callsite rewrites plus any in-place `guideline_flags` remediation plus the NOTE breadcrumb.
- **Target Module**: The new or extended file receiving the extracted class. Typically `src/refactors/<snake_name>.py` for classes without an obvious semantic home, or an existing package file (e.g. `src/export/site_config_exporter.py`, `src/gateway/gateway_template_config_manager.py`, `src/site/site_client_exporter.py`) when the semantic fit is clear.
- **Callsite**: The exact location where a candidate class is instantiated, referenced, or imported. For Hot-bucket classes, may be 4-128 distinct locations, all inside `MistHelper.py`, all rewritten atomically in one commit.
- **Dispatch Queue**: The Refs-ASC / LOC-DESC-ordered list of 47 candidates below. Ordering is re-derived from the freshest catalog after every merge.
- **Deferred Candidate**: A queue entry that has been removed from active dispatch mid-initiative because (a) a fresh catalog regeneration surfaced a new `src/` caller, or (b) its classification shifted out of the Hot bucket, or (c) the pre-dispatch grep audit surfaced an unexpected external reference. Deferrals are recorded in the "Deferred Candidates" section (initially empty).
- **Compliance Baseline**: Repo-wide ≥ 99.6/A+ aggregate; every new/edited module at A+/100; `MistHelper.py` pylint non-regressing against the pre-initiative baseline.

## Dispatch Queue

The 47 candidates in dispatch order. Each row lands as one PR. Every row carries a **Cat** (action-type) designation and a **Landing target** (destination module or package). The queue front-loads the 4 Category A **facade-removal** candidates as a low-risk warmup (the `src/` implementation is already merged and CI-proven — the PR only removes the dead facade + rewires callsites), then continues with the 43 Category B **fresh-extraction** candidates in Refs-ASC / LOC-DESC order.

**Action-type legend**:
- **Cat A — Facade removal**: The `MistHelper.py` class is a delegation wrapper; the real implementation already lives in `src/` at the noted landing target. The PR deletes the facade, rewires imports at each callsite to reference the `src/` implementation directly, and MUST verify method-parity between facade and real impl before deletion (per FR-025). No new file is created.
- **Cat B — Fresh extraction**: No `src/` collision exists. The PR extracts the class body from `MistHelper.py` to the landing package (new file created inside the noted package) and rewrites callsites (per FR-003). This is the 1010/1011 pattern.

Collision audit performed 2026-07-07 against all 47 candidates confirmed exactly 4 Cat A facades and 43 Cat B fresh-extractions. Zero Cat C name-clash-distinct entries were found.

| # | Refs | LOC | Class | Cat | Landing target |
|---:|---:|---:|---|:-:|---|
| 1 | 6 | 56 | GatewayTemplateConfigManager | A | `src/gateway/template_config.py` |
| 2 | 8 | 22 | FirmwareManager | A | `src/firmware/firmware_manager.py` |
| 3 | 16 | 43 | SiteConfigManager | A | `src/site/site_config_manager.py` |
| 4 | 70 | 188 | DeviceUtilityCommands | A | `src/device/utility_commands.py` |
| 5 | 4 | 675 | OrgConfigMigrationManager | B | `src/org/` |
| 6 | 4 | 97 | DeviceUtils | B | `src/device/` |
| 7 | 4 | 40 | SelfExportUtils | B | `src/export/` |
| 8 | 5 | 386 | MSPInventoryExporter | B | `src/export/` |
| 9 | 5 | 214 | TelemetryEmitter | B | `src/analytics/` |
| 10 | 8 | 72 | InteractiveDisplayUtils | B | `src/ui/` |
| 11 | 8 | 70 | DisplayUtils | B | `src/ui/` |
| 12 | 8 | 66 | AuditAnalysisOps | B | `src/audit/` |
| 13 | 9 | 461 | OperationRegistry | B | `src/utils/` |
| 14 | 10 | 85 | SiteClientExporter | B | `src/export/` |
| 15 | 13 | 587 | BulkRadiusWLANConfigManager | B | `src/site/` |
| 16 | 13 | 10 | EndpointConfig | B | `src/dataclasses/` |
| 17 | 14 | 759 | ConstDefinitionsExporter | B | `src/export/` |
| 18 | 14 | 129 | OrgAlarmEventExporter | B | `src/export/` |
| 19 | 14 | 100 | SiteConfigExporter | B | `src/export/` |
| 20 | 14 | 94 | OrgAdminExporter | B | `src/export/` |
| 21 | 16 | 328 | APIDataFetcher | B | `src/api/` |
| 22 | 18 | 144 | OrgTemplateExporter | B | `src/export/` |
| 23 | 18 | 139 | GatewayHaExporter | B | `src/export/` |
| 24 | 20 | 168 | LicenseExportUtils | B | `src/export/` |
| 25 | 20 | 156 | DataCollectionManager | B | `src/analytics/` |
| 26 | 20 | 129 | WiredClientManufacturerReportGenerator | B | `src/reports/` |
| 27 | 22 | 180 | SFPTransceiverDataProcessor | B | `src/reports/` |
| 28 | 22 | 146 | SitesByAPModelExporter | B | `src/export/` |
| 29 | 22 | 69 | OrgDeviceInventorySummary | B | `src/inventory/` |
| 30 | 23 | 161 | CLIShellManager | B | `src/ssh/` |
| 31 | 24 | 168 | OrgConfigExporter | B | `src/export/` |
| 32 | 26 | 162 | OrgClientSecurityExporter | B | `src/export/` |
| 33 | 28 | 114 | EnvironmentUtils | B | `src/utils/` |
| 34 | 30 | 203 | SiteDeviceExporter | B | `src/export/` |
| 35 | 31 | 210 | PromptClientUtils | B | `src/input/` |
| 36 | 32 | 251 | GlobalWiredClientReportGenerator | B | `src/reports/` |
| 37 | 34 | 245 | GatewayTestExporter | B | `src/export/` |
| 38 | 34 | 179 | DatabaseSchemaUtils | B | `src/db/` |
| 39 | 36 | 127 | TroubleshootUtils | B | `src/troubleshooting/` |
| 40 | 37 | 110 | FilterOperatorEngine | B | `src/utils/` |
| 41 | 46 | 396 | DeviceRebootManager | B | `src/device/` |
| 42 | 46 | 289 | ARPCommandManager | B | `src/device/` |
| 43 | 54 | 341 | SiteAnomalyExporter | B | `src/export/` |
| 44 | 54 | 273 | OfflineDeviceReporter | B | `src/reports/` |
| 45 | 58 | 414 | OrgDeviceStatsExporter | B | `src/export/` |
| 46 | 66 | 475 | OrgTicketManager | B | `src/org/` |
| 47 | 128 | 653 | OrgExportUtils | B | `src/export/` |

**Landing distribution**: `src/export/` = 20 (largest cluster — accepted as flat layout for this initiative; sub-partitioning deferred pending noise emergence), `src/device/` = 4 (+1 Cat A), `src/utils/` = 4, `src/reports/` = 4, `src/analytics/` = 2, `src/ui/` = 2, `src/org/` = 2, `src/site/` = 2, `src/gateway/` = 1 Cat A, `src/firmware/` = 1 Cat A, all others = 1. Note: `src/refactors/` receives **zero** candidates — every row lands in a domain-fitting existing package.

**Resolution of the `FirmwareManager` row-10 ambiguity** (previously flagged): confirmed as Cat A. The `MistHelper.py` `FirmwareManager` class at `MistHelper.py:17376` is a factory facade (`create()` builds `FirmwareManagerConfig` + returns `_Impl(config)` sourced from `src/firmware/firmware_manager.py::FirmwareManager` at 270 defs). The dispatch PR deletes the facade and rewires the 8 callsites to construct the real `src/firmware/firmware_manager.py::FirmwareManager` directly. No new file is created.

**Cat A method-parity risk flag**: The `DeviceUtilityCommands` facade at `MistHelper.py:13527` fans out to 35 operation-subclasses in `src/device/utility_commands.py`. Its extraction PR (dispatch position 4) MUST run an exhaustive method-parity audit — enumerate every method exposed by the facade, confirm the identical method is exposed by the real `src/` class (including all 35 sub-op wrappers), record the audit output in the PR description — before deleting the facade. This is a Cat A-specific gate per FR-025.

## Deferred Candidates

*(Initially empty. Populated during the initiative if any Dispatch Queue candidate is deferred per FR-013, FR-020, or Edge Case E-6.)*

| # | Class | Reason for Deferral | Recording PR / Commit |
|---:|---|---|---|

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Hot bucket of `refactor_candidates.md` reports **zero** of the 47 Dispatch Queue classes at initiative completion, OR each remaining Dispatch Queue class is recorded in the "Deferred Candidates" section with documented rationale.
- **SC-002**: `MistHelper.py` physical line count drops by at least **8,000 lines** relative to the pre-initiative baseline (the sum of the 47 candidates' LoC in the Dispatch Queue is ~ 12,150 LoC; SC-002 gives headroom for class-body overhead in the new modules and reasonable decomposition retention).
- **SC-003**: Repository-wide aggregate compliance score is ≥ 99.6/A+ at every intermediate `main`-branch state throughout the initiative and at final completion.
- **SC-004**: Zero files that were A+/100 pre-initiative regress below A+ by the end of the initiative.
- **SC-005**: All extraction PRs merge with 15/15 functional CI jobs green, `mergeStateStatus: CLEAN`, `black --check` clean, `ruff check` clean, and `python MistHelper.py --test` reporting 0 failed / exit 0. Zero PRs merged via `--admin` bypass except where `mergeStateStatus` was genuinely BLOCKED/DIRTY/BEHIND with root cause documented in the PR.
- **SC-006**: Every new file created under `src/refactors/` (or extended file in an existing destination package) during the initiative scores A+/100 on compliance.
- **SC-007**: Zero wrapper shims, forwarding functions, re-export modules, or backward-compatibility aliases remain in `MistHelper.py` after the initiative.
- **SC-008**: Zero symbols from the analyzer's `SKIP_ALWAYS` bucket (`GlobalImportManager`, `tqdm`) are modified by any PR in this initiative.
- **SC-009**: Zero Hot-bucket classes outside the 47 Dispatch Queue entries are extracted by this initiative — the 29 excluded classes (those with any `src/` reference) remain deferred to a future initiative that will address multi-file rewrite discipline.
- **SC-010**: After every merged extraction PR, the analyzer is re-run and `refactor_candidates.md` is regenerated before the next PR is dispatched — verifiable by walking the merged-PR sequence.
- **SC-011**: Every analyzer-flagged `guideline_flag` on each extracted class is resolved within the extraction PR — zero forward-carried guideline violations attributable to this initiative.
- **SC-012**: Every extraction PR contains exactly one NOTE breadcrumb at the deletion site in `MistHelper.py` matching the pinned FR-007 template — verifiable by post-merge grep of `# NOTE: <ClassName> extracted to`.
- **SC-013**: Pre-push local gate: `black --check` and `ruff check` both pass on every refactor branch before the PR opens, and `python MistHelper.py --test` reports 0 failed with exit code 0. Enforcement is by the pre-push hook and by the contributor's `feedback_prepush_black_ruff.md` habit.
- **SC-014**: The workflow processes candidates in Refs-ASC / LOC-DESC order derived from the freshest catalog at each dispatch — verifiable by walking the merged-PR sequence against the sequence of regenerated catalog snapshots.
- **SC-015**: `MistHelper.py`'s pylint score is non-regressing against the pre-initiative baseline (established on the first branch commit). No merged PR reduces the score.
- **SC-016**: Zero new SKIPPED conditionals are introduced in CI by any extraction PR (per FR-019). Pre-existing SKIPPED conditionals remain non-blocking per Edge Case E-9.
- **SC-017**: The initiative closes with a documented final-state summary in the last-merged PR (or a follow-up docs commit) recording: (a) count of PRs merged (target: 47, actual may be lower if any candidates deferred), (b) final `MistHelper.py` LoC and pylint score, (c) final aggregate compliance score, (d) list of deferred candidates with rationale, and (e) count of remaining Hot-bucket classes (target: the original 76 minus 47 extracted minus any deferred, i.e. ~ 29 + deferred).

## Assumptions

- The analyzer at `tools/refactor_analyzer/` remains functionally correct for the Hot bucket across the initiative; discrepancies discovered during extraction are filed as analyzer bugs but do not block extraction PRs.
- The 15 functional CI jobs currently gating PRs on `main` remain the mergeability contract for the duration of this initiative.
- The current compliance baseline (≥ 99.6/A+) is the floor; the initiative does not attempt to raise it beyond preserving it.
- The 47-row Dispatch Queue reflects the post-1012 catalog snapshot supplied by the user at initiative kickoff (2026-07-07). Mid-initiative reclassification (Hot → Low-Use, or MistHelper-only → external-caller) is expected and handled per FR-020 / FR-013.
- Serial per-PR workflow: at most one extraction PR is open at any time (contrast with 1012's single-PR bundle).
- Analyzer regeneration cost per run is negligible relative to CI cycle time; the "regenerate after every merge" discipline does not create a bottleneck.
- Refs-ASC / LOC-DESC ordering front-loads the smallest-blast-radius extractions and back-loads the largest-LoC candidates. This ordering is a dispatch rule; the merge order MAY deviate slightly if an earlier PR is under revision (per FR-023), but concurrent PRs are not permitted.
- The `src/refactors/` layout established by 1010, extended by 1011, and continued by 1012 remains the correct destination for classes without an obvious semantic home. Classes with a clear semantic fit (e.g. `SiteConfigExporter` → `src/site/`, `OrgAlarmEventExporter` → `src/export/`, `GatewayTemplateConfigManager` → `src/gateway/`) land in the existing package (per E-1).
- Black + Ruff pre-push discipline (`feedback_prepush_black_ruff.md`) is followed by the contributor. This spec documents the requirement in SC-013 but does not add a new CI job to enforce it — the enforcement remains local.
- `python MistHelper.py --test` is the initiative's smoke-test contract. It runs as a merge gate per FR-015. Its passing state is a strict requirement (0 failed, exit 0) on every merged extraction PR.
- The 29 excluded Hot-bucket classes (those with any `src/` reference) are outside scope. A future initiative (post-1013) will address them with multi-file rewrite discipline analogous to 1011's User Story 2. This spec does not attempt to enumerate that future initiative's scope.
- The user-supplied ref counts in the Dispatch Queue reflect direct name occurrences at analyzer-scan time. Line-number drift alone does not invalidate an entry; only a change in classification (ref count band or external-caller presence) triggers deferral.
- `FirmwareManager` at row 10 may be a duplicate reference to the existing `src/firmware/firmware_manager.py::FirmwareManager` established in 1011 (see note under the Dispatch Queue table). The extraction PR resolves the ambiguity at dispatch time.
