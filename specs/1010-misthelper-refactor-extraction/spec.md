# Feature Specification: MistHelper.py Refactor Extraction Initiative

**Feature Branch**: `1010-misthelper-refactor-extraction`
**Created**: 2026-07-05
**Status**: Draft
**Input**: User description: "Systematically decompose MistHelper.py (24K+ line entrypoint monolith) into cohesive class modules under `src/refactors/` by extracting analyzer-identified candidates. Multi-PR extraction workflow driven by `tools/refactor_analyzer/`, which produces `refactor_candidates.md` — a ranked catalog of extraction candidates classified by reference count."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract Single-Use candidates from the monolith (Priority: P1)

The core value-delivery workflow. For each Single-Use candidate (exactly one caller in the codebase), a refactor engineer opens a PR that (a) moves the class/function into a new cohesive module under `src/refactors/` (or, when the caller lives in an existing dedicated module, alongside that caller), (b) rewrites the single callsite in the same commit, and (c) deletes the original symbol from `MistHelper.py`. No wrapper shims are left behind. Guideline violations detected on the moved code (oversize, missing action logging, hardcoded separators) are corrected in the extraction PR — never carried forward. Module-level functions are refactored into class-body methods on landing, not left as bare module functions.

**Why this priority**: Delivers the bulk of the LOC drop (11 PRs, ~761 LoC of the 811 LoC first-pass budget). Rewriting the callsite atomically with the move is the non-negotiable that distinguishes this initiative from prior stalled attempts, so P1 is where the discipline is enforced.

**Independent Test**: Any single Single-Use extraction (e.g. `SQLiteDatabaseWriter` at MistHelper.py:6949-7265 → `src/refactors/sqlite_database_writer.py` with callsite MistHelper.py:7468 rewritten) can be merged in isolation with the full CI matrix green. The initiative delivers value one candidate at a time.

**Acceptance Scenarios**:

1. **Given** a Single-Use candidate identified in `refactor_candidates.md` with a known callsite, **When** the extraction PR is opened, **Then** the new module exists at the mapped path, the original symbol is deleted from `MistHelper.py`, the single callsite is rewritten to import from the new module, and no `def old(...): return NewClass().new(...)` wrapper exists anywhere in the diff.
2. **Given** a candidate that is currently a module-level function, **When** it is extracted, **Then** it lands as a method on a cohesive class in the new module — not as a bare `def` at module scope.
3. **Given** an extraction PR is under CI, **When** the pipeline completes, **Then** all 15 functional CI jobs are green, the new module scores A+/100 on compliance, and no previously A+ file regresses.
4. **Given** the analyzer flagged the moved code with `guideline_flags` (e.g. oversize, missing action logging, hardcoded separator), **When** the extraction PR lands, **Then** each flagged violation is resolved in the same PR — not deferred.
5. **Given** the Single-Use bucket in `refactor_candidates.md`, **When** dispatching the next PR, **Then** candidates are processed in LOC-DESC order (largest first) so early merges deliver the biggest line-count wins.

---

### User Story 2 - Delete Unused candidates outright (Priority: P2)

For candidates with 0 references in the codebase, the workflow is a pure deletion: remove the class or function definition from `MistHelper.py`, no new module, no callsite rewrite. The analyzer's zero-reference count is verified by a manual grep of the codebase in the same PR to guard against dynamic-dispatch false negatives.

**Why this priority**: Lowest-risk portion of the first pass (2 PRs, ~49 LoC), but strictly smaller value than Single-Use extraction. Deletion PRs also validate the analyzer's zero-ref accuracy on a small sample before the higher-stakes Single-Use PRs consume analyzer output as ground truth.

**Independent Test**: `PerformanceMonitor` (MistHelper.py:365-404, 40 LoC) can be deleted in its own PR and merged with all CI jobs green, delivering an immediate LOC reduction and demonstrating the analyzer's zero-reference verdict is trustworthy.

**Acceptance Scenarios**:

1. **Given** an Unused candidate (`PerformanceMonitor`, `MapViewerConfig`), **When** the deletion PR is opened, **Then** the definition is removed from `MistHelper.py` and no new file is created.
2. **Given** the deletion PR, **When** the diff is reviewed, **Then** a repo-wide grep confirming 0 remaining references to the symbol name is included in the PR description as manual verification of the analyzer output.
3. **Given** the deletion PR merges, **When** CI runs on `main`, **Then** all 15 functional jobs stay green and compliance baseline is unchanged or improved.

---

### User Story 3 - Refresh the analyzer catalog after every merged extraction (Priority: P3)

Reference counts shift as extractions land — a symbol that was Single-Use pre-extraction may become Unused after its caller is itself moved elsewhere, and vice versa. After every merged extraction PR, the analyzer is re-run and `refactor_candidates.md` is regenerated before the next PR is dispatched. The dispatch queue is always derived from the freshest analyzer output, never from a stale snapshot.

**Why this priority**: Workflow discipline that supports P1 and P2 rather than delivering standalone value. Without it, later PRs in the queue risk operating on stale reference-count data and producing incorrect callsite rewrites.

**Independent Test**: After merging any extraction PR, running `py -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md` regenerates the catalog cleanly, and the diff of `refactor_candidates.md` reflects the just-completed extraction (removed from the appropriate bucket, and any downstream reference-count shifts visible).

**Acceptance Scenarios**:

1. **Given** an extraction PR has just merged to `main`, **When** the next PR is dispatched, **Then** `refactor_candidates.md` has been regenerated on the current `main` head first and the next candidate is selected from that fresh output.
2. **Given** the regenerated catalog shows a formerly Single-Use candidate has become Unused, **When** the dispatcher plans the next PR, **Then** the candidate is reclassified into the Unused workflow (delete-only, no new module).
3. **Given** the regenerated catalog shows a formerly Single-Use candidate has gained callers and become Low-Use or Hot, **When** the dispatcher plans the next PR, **Then** that candidate is skipped from the first pass and rescheduled to the second-pass (Low-Use) evaluation or the Out-of-Scope Hot bucket.

---

### Edge Cases

- What happens when `refactor_candidates.md` disagrees with a manual grep about reference count? Manual grep wins for that PR; the discrepancy is filed as an analyzer bug in `tools/refactor_analyzer/` but does not block the extraction.
- How does the workflow handle a Single-Use candidate whose only caller is inside a Skipped (`SKIP_ALWAYS`) symbol like `GlobalImportManager`? Defer to second-pass; do not extract until the skip constraint is re-evaluated separately.
- What happens if a candidate's extraction would require reaching into a Hot symbol (4+ callers) to rewrite the callsite? Abort the extraction, document the coupling in the PR description, and reroute the candidate to second-pass planning.
- How does the workflow handle a merge conflict on `refactor_candidates.md` when multiple extraction PRs are open simultaneously? Serial per-PR workflow is non-negotiable — only one extraction PR is open at a time. Regenerate the catalog after each merge; do not maintain parallel branches.
- What happens if CI surfaces a regression that was masked in the pre-extraction monolith (e.g. an import ordering bug that only appears once the symbol moves)? Fix in the same PR; do not merge with any of the 15 functional CI jobs failing, and do not use `--admin` bypass — check `mergeStateStatus` per `feedback_no_admin_bypass.md`.
- How does the workflow handle a candidate whose LOC has drifted since the catalog was generated (e.g. an unrelated commit expanded the function body)? Re-run the analyzer to refresh the LOC estimate; use the fresh number for the PR budget.
- What happens when an extracted module would collide with an existing file at the mapped path? Rename the target module (e.g. `_v2` or a domain-specific prefix) and record the rationale in the PR description.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The extraction workflow MUST process candidates in the order Unused → Single-Use, and within each bucket in LOC-DESC order (largest LOC first) as specified in the input queue.
- **FR-002**: The workflow MUST process exactly one extraction candidate per PR. Batching multiple candidates into a single PR is prohibited.
- **FR-003**: For each Single-Use candidate, the PR MUST (a) create the target module file, (b) delete the original symbol from `MistHelper.py`, and (c) rewrite the single callsite — all in the same commit. No wrapper shim, forwarding function, or backward-compatibility alias may be left in `MistHelper.py`.
- **FR-004**: For each Unused candidate, the PR MUST delete the definition from `MistHelper.py` with no new module created. A manual repo-wide reference grep MUST be included in the PR description as verification of the analyzer's zero-reference verdict.
- **FR-005**: Module-level functions that are extracted MUST be refactored into class-body methods on the new module, not preserved as bare module-level functions.
- **FR-006**: Analyzer-flagged `guideline_flags` on the extracted code (oversize, missing action logging, hardcoded separators, and any other flags surfaced by the analyzer) MUST be resolved within the same extraction PR — never deferred to a follow-up.
- **FR-007**: All extracted modules MUST comply with project non-negotiables: ASCII-only logs, `safe_input()` for interactive input, `pathlib.Path` in place of `os.path`, and any other conventions enumerated in `AGENTS.md` and `.github/copilot-instructions.md`.
- **FR-008**: The initiative MUST NEVER touch symbols in the analyzer's `SKIP_ALWAYS` bucket (e.g. `GlobalImportManager`) regardless of downstream reclassification.
- **FR-009**: The initiative MUST NEVER touch symbols in the Hot bucket (4+ callers) during the first pass. Second-pass Low-Use evaluation is a distinct effort scoped after first pass completes.
- **FR-010**: After every merged extraction PR, the workflow MUST regenerate `refactor_candidates.md` by running the analyzer against the current `main` head before the next PR is dispatched.
- **FR-011**: An extraction PR MUST NOT merge until all 15 functional CI jobs report green. When `mergeStateStatus` reports BLOCKED, DIRTY, or BEHIND, the PR MUST be updated and re-run rather than force-merged. `--admin` merge bypass MUST NOT be used as a routine unblock.
- **FR-012**: Every new module under `src/refactors/` (and any existing module receiving an extracted symbol) MUST land at A+/100 compliance score, and no file that was previously A+ may regress below A+ as a result of the extraction.
- **FR-013**: The repository-wide compliance baseline MUST remain at or above 99.6/A+ after each merged extraction PR. Any PR that would regress the baseline MUST be reworked before merge.
- **FR-014**: The first-pass extraction budget covers exactly 13 candidates: 2 Unused (`PerformanceMonitor`, `MapViewerConfig`) plus 11 Single-Use (LOC-DESC: `SQLiteDatabaseWriter`, `TUILauncher`, `DataDirectoryChecker`, `MapsManagerLauncher`, `AddressComparisonCounters`, `ServicePingManager`, `WAN2MigrationManager`, `run_systematic_test`, `switch_to_interactive_login`, `run_interactive_test`, `listen_keyboard`). Additions to first-pass scope require explicit re-scoping.
- **FR-015**: `AddressComparisonCounters` MUST be relocated into the existing `src/inventory/csv_comparator.py::CsvComparatorManager` class rather than into a new `src/refactors/` module, because its sole caller already lives there. All other Single-Use candidates map to fresh files under `src/refactors/`.
- **FR-016**: When the freshly regenerated `refactor_candidates.md` shows that a candidate has been reclassified out of the first-pass buckets (e.g. Single-Use → Low-Use or Hot after a prior merge), the workflow MUST reroute or defer that candidate rather than force-extract it under the original classification.
- **FR-017**: The initiative MUST NOT introduce new features, new commands, or scope beyond the extraction itself (e.g. issue #421 Menu 195 packet capture and other feature backlogs remain out of scope).
- **FR-018**: The initiative MUST NOT modify `tools/refactor_analyzer/` itself; the analyzer is consumed as-is. Analyzer improvements are a separate initiative.

### Key Entities *(include if feature involves data)*

- **Extraction Candidate**: A class or function in `MistHelper.py` catalogued by `tools/refactor_analyzer/` with attributes name, kind (class/function), line range, LOC count, reference count, classification bucket (Unused / Single-Use / Low-Use / Hot / Skipped), callsite locations, and `guideline_flags`.
- **Refactor Candidates Catalog** (`refactor_candidates.md`): The analyzer's ranked output; the single source of truth for the dispatch queue. Sections: Summary, Unused, Single-Use, Low-Use, Hot, Skipped, Limitations. Regenerated after every merged extraction PR.
- **Extraction PR**: A single pull request delivering one candidate's move-or-delete plus its callsite rewrite plus any in-place `guideline_flags` remediation. Gated by 15 functional CI jobs and A+/100 compliance on affected files.
- **Target Module**: The new file under `src/refactors/` (or existing sibling module in the case of `AddressComparisonCounters`) that receives an extracted symbol. Must land at A+/100 compliance.
- **Callsite**: The exact location where a Single-Use candidate is invoked. Rewritten atomically with the extraction so that no intermediate revision references a deleted symbol.
- **Compliance Baseline**: The repo-wide compliance score maintained at ≥99.6/A+ with zero sub-A files; each extraction PR must preserve or improve this baseline.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Unused bucket of `refactor_candidates.md` reports 0 entries at first-pass completion (or documented rationale in the catalog's Limitations section explaining any deferrals).
- **SC-002**: The Single-Use bucket of `refactor_candidates.md` reports 0 entries at first-pass completion (or documented rationale for any explicitly deferred candidate).
- **SC-003**: `MistHelper.py` physical line count drops by at least 600 lines relative to its pre-initiative baseline (matches the 811 LoC extraction budget minus small class-body overhead per new module).
- **SC-004**: Repository-wide compliance score is ≥99.6/A+ at every intermediate main-branch state throughout the initiative and at final completion.
- **SC-005**: Zero files that were A+/100 pre-initiative regress below A+ by the end of the initiative.
- **SC-006**: All 13 first-pass PRs merge with 15/15 functional CI jobs green. Zero PRs merged via `--admin` bypass except where `mergeStateStatus` was genuinely BLOCKED/DIRTY/BEHIND with root cause documented in the PR.
- **SC-007**: Every new file created under `src/refactors/` during the initiative scores A+/100 on compliance.
- **SC-008**: Zero wrapper shims, forwarding functions, or backward-compatibility aliases remain in `MistHelper.py` after the initiative — every extracted symbol is either fully removed or (for Unused) simply deleted.
- **SC-009**: Zero symbols from the analyzer's `SKIP_ALWAYS` bucket are modified by any PR in this initiative.
- **SC-010**: Zero symbols from the Hot bucket (4+ callers) are extracted during the first pass.
- **SC-011**: After every merged extraction PR, the analyzer is re-run and `refactor_candidates.md` is regenerated before the next PR is dispatched — verifiable by checking that the commit that opens PR N+1 is preceded on `main` by a catalog-regeneration commit or that PR N+1's dispatch record references a catalog run on the post-PR-N main head.
- **SC-012**: Every analyzer-flagged `guideline_flag` on the extracted code is resolved within the extraction PR — zero forward-carried guideline violations attributable to this initiative.

## Assumptions

- The analyzer at `tools/refactor_analyzer/` is functionally correct for the first-pass buckets; discrepancies discovered during extraction are filed as analyzer bugs but do not block the initiative.
- The 15 functional CI jobs currently gating PRs on `main` remain the mergeability contract for the duration of this initiative; if a new required check is added mid-flight, subsequent PRs are held to the new bar.
- The current compliance baseline of 99.6/A+ with 0 sub-A files (from `data/full_repo_compliance_current.md`) is the floor; the initiative does not attempt to raise it beyond preserving it.
- The candidate-to-target-path mapping specified in the input queue is authoritative for first-pass PRs. If a candidate's callsite is discovered mid-extraction to live in a different module than expected, the target path may shift but the mapping change is recorded in the PR description.
- Serial per-PR workflow: at most one extraction PR is open at any time, so `refactor_candidates.md` regeneration is unambiguous between PRs.
- Second-pass (Low-Use, 20 candidates) is a distinct initiative scoped after first pass completes; success of second pass is not a success criterion of this specification.
- The parent conversation (not this spec or its downstream `/speckit.plan`/`/speckit.tasks`) controls PR dispatch cadence and branch creation. This spec exists to document the contract, not to trigger execution.
- Analyzer regeneration cost (per run) is negligible relative to CI cycle time; the "regenerate after every merge" discipline does not create a bottleneck.
- The mapping specifies `AddressComparisonCounters` lands in `src/inventory/csv_comparator.py::CsvComparatorManager`; this is a deliberate exception to the "new module under `src/refactors/`" pattern because the sole caller already lives in `csv_comparator.py`. Other candidates whose sole caller lives outside `MistHelper.py` may follow the same "land next to caller" rule if discovered during extraction.
