# Feature Specification: MistHelper.py Refactor Extraction — Low-Use Bucket (Second Pass)

**Feature Branch**: `1011-misthelper-refactor-low-use`
**Created**: 2026-07-05
**Status**: Draft
**Predecessor**: [`1010-misthelper-refactor-extraction`](../1010-misthelper-refactor-extraction/spec.md) (13 PRs merged, first-pass Unused + Single-Use buckets cleared)
**Input**: User description: "Second-pass extraction: process the 20 Low-Use candidates (2-3 callers each) surfaced by `tools/refactor_analyzer/` after the first-pass initiative cleared Unused + Single-Use. Ordered by fresh, post-PR-13-merge catalog verification per FR-016 of the predecessor spec. Deliberately NOT batched into 1010 per Assumption 6 / FR-017 of the predecessor spec — reference counts shift as extractions land, so a fresh catalog dispatch is authoritative."

## Predecessor Context

The 1010 initiative closed with:

- Repository baseline: 99.6/A+
- MistHelper.py physical LoC drop: ≥600 lines across 13 merged PRs (PR #757-#769)
- `refactor_candidates.md` regenerated on post-PR-13-merge `main`: `unused=0, single-use=0, low-use=20, hot=80, skipped=1`
- All 12 first-pass Success Criteria (SC-001..SC-012) satisfied
- Zero wrapper shims left in MistHelper.py
- Zero SKIP_ALWAYS symbols modified, zero Hot symbols extracted

Per FR-017 of 1010 and Assumption 6, the 20 Low-Use candidates were **explicitly deferred** to a second-pass initiative rather than batched into the first pass. This spec is that second pass.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract Low-Use candidates whose sole caller cluster is inside MistHelper.py (Priority: P1)

The core value-delivery workflow for the second pass. For each Low-Use candidate whose 2-3 callsites all resolve to a single file (typically `MistHelper.py` itself), a refactor engineer opens a PR that (a) moves the class/function/assignment into a new cohesive module under `src/refactors/` (or, when a `Suggested class` names an existing shared destination like `FirmwareManager`, folds into that class body), (b) rewrites every callsite in the same commit, (c) deletes the original symbol from `MistHelper.py`, (d) resolves any analyzer `guideline_flags` in-flight, and (e) lands with all 15 functional CI jobs green and A+/100 compliance on affected files. No wrapper shims. Module-level functions land as class-body methods per FR-005 of 1010 (carried forward as FR-005 here).

**Why this priority**: Delivers the bulk of the second-pass LoC drop. The three largest candidates (`FirmwareUpgradeStatusChecker` at 958 LoC, `WLANRadiusTimerManager` at 787 LoC, `WANProbeConfigManager` at 473 LoC) alone total 2,218 LoC — nearly 4x the total 1010 first-pass reduction. Serial per-PR execution with catalog regeneration between merges is retained.

**Independent Test**: Any single Low-Use extraction (e.g. `AnomalyMetricsDiscovery` at MistHelper.py:19779-19869, refs at 12994, 12994 → `src/refactors/anomaly_metrics_discovery.py` with both callsite occurrences rewritten in the same commit) can be merged in isolation with the full CI matrix green.

**Acceptance Scenarios**:

1. **Given** a Low-Use candidate with all callsites inside `MistHelper.py`, **When** the extraction PR is opened, **Then** the new module exists at the mapped path, the original symbol is deleted from `MistHelper.py`, every listed callsite is rewritten to import from the new module, and no wrapper shim exists anywhere in the diff.
2. **Given** a candidate that is currently a module-level function or bare assignment, **When** it is extracted, **Then** it lands as a method or class-body attribute on a cohesive class in the new module — not as a bare `def` or module-level `X = ...` at module scope (FR-005 carry-forward).
3. **Given** an extraction PR is under CI, **When** the pipeline completes, **Then** all 15 functional CI jobs are green, the new module scores A+/100 on compliance, and no previously A+ file regresses.
4. **Given** the analyzer flagged the moved code with `guideline_flags` (e.g. `oversize_25_lines`, `non_ascii_logs`, `raw_input_call`, `missing_action_logging`, `missing_inline_comments`), **When** the extraction PR lands, **Then** each flagged violation is resolved in the same PR — not deferred.
5. **Given** the freshly regenerated Low-Use bucket, **When** dispatching the next PR, **Then** candidates are processed in LOC-DESC order within their landing-destination cluster (see Dispatch Queue below).

---

### User Story 2 - Extract Low-Use candidates with cross-file callsites (Priority: P2)

Three candidates in the fresh Low-Use bucket have callers outside `MistHelper.py`:

- `main` (function, 12 LoC) — caller in `src/maps/maps_manager.py:2794`
- `marvis_data_utils` (assignment, 4 LoC) — caller in `src/troubleshooting/marvis_troubleshoot_utils.py:21`
- `MIST_WAN_TARGET_PORTS` (assignment, 3 LoC) — caller in `src/gateway/gateway_export_utils.py:51`

These require multi-file rewrites in the same PR (move symbol + rewrite `MistHelper.py` internal callsites + rewrite external module's import) to maintain the FR-003 atomicity contract (no intermediate revision references a deleted symbol).

**Why this priority**: Same value proposition as P1 but higher blast radius (multi-file diff) so distinct from P1 dispatch ordering. Bundled as P2 to ensure P1's simpler single-file rewrites validate the second-pass workflow before multi-file diffs are attempted.

**Independent Test**: `MIST_WAN_TARGET_PORTS` extraction (~3 LoC constant, 3 callsites across 2 files) can be merged as a standalone PR that (a) creates `src/refactors/mist_wan_target_ports.py`, (b) rewrites `MistHelper.py:1992` (def-site removal) and `MistHelper.py:15638` (callsite) and `src/gateway/gateway_export_utils.py:51` (callsite), all in one commit with 15/15 CI green.

**Acceptance Scenarios**:

1. **Given** a Low-Use candidate with a caller outside `MistHelper.py`, **When** the extraction PR is opened, **Then** the diff touches (a) the new module file, (b) `MistHelper.py` (def-site deletion + internal callsite rewrite), AND (c) every external caller file — all in the same commit.
2. **Given** the multi-file rewrite, **When** CI runs, **Then** no intermediate revision references a deleted symbol (git bisectability across the merge commit only; the merge commit itself is the atomic unit).
3. **Given** the extraction affects a shared destination class (e.g. `FirmwareUpgradeStatusChecker` → `FirmwareManager` in `src/firmware/firmware_manager.py`), **When** the PR lands, **Then** `firmware_manager.py` continues to score A+/100 (no regression on the already-A+ shared destination).

---

### User Story 3 - Refresh the analyzer catalog after every merged extraction (Priority: P3)

Carry-forward of User Story 3 from 1010. Reference counts shift as extractions land. After every merged extraction PR in this initiative, the analyzer is re-run and `refactor_candidates.md` is regenerated before the next PR is dispatched. Some Low-Use candidates may drop to Single-Use (or Unused) after a prior merge removes one of their callers; the fresh catalog is authoritative and the dispatch queue is re-derived accordingly.

**Why this priority**: Workflow discipline that supports P1 and P2 rather than delivering standalone value. Especially important in this pass because several candidates share destination classes (three `FirmwareManager` candidates: `FirmwareUpgradeStatusChecker`, `BulkAPFirmwareUpgrader`, `BulkSwitchFirmwareUpgrader`) — merging one of them may shift the caller layout of the others.

**Independent Test**: After merging any second-pass extraction PR, running `python -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md` regenerates the catalog cleanly, and the diff of `refactor_candidates.md` reflects the just-completed extraction (removed from the Low-Use bucket, and any downstream reference-count shifts visible on remaining candidates).

**Acceptance Scenarios**:

1. **Given** an extraction PR has just merged to `main`, **When** the next PR is dispatched, **Then** `refactor_candidates.md` has been regenerated on the current `main` head first and the next candidate is selected from that fresh output.
2. **Given** the regenerated catalog shows a formerly Low-Use candidate has become Unused (2-ref candidate lost both callers when a prior extraction removed them), **When** the dispatcher plans the next PR, **Then** the candidate is reclassified into the Unused workflow (delete-only, no new module).
3. **Given** the regenerated catalog shows a formerly Low-Use candidate has become Hot (gained callers as ripple-effect of prior extractions), **When** the dispatcher plans the next PR, **Then** that candidate is deferred out of this initiative to a subsequent third-pass evaluation, and the initiative's SC-002 rationale is updated to document the reclassification.

---

### Edge Cases

- What happens when a Low-Use candidate's reference count fluctuates between catalog regenerations because of transient parse ambiguity? Manual grep wins for that PR; the discrepancy is filed as an analyzer bug in `tools/refactor_analyzer/` but does not block the extraction.
- How does the workflow handle a Low-Use candidate whose destination class (e.g. `FirmwareManager`) is currently in the Hot bucket? Extraction may still land in that class — Hot-bucket restrictions apply to the *source* symbol under extraction, not to the *destination* class receiving the extracted method. Confirm the destination file remains A+/100 after the move.
- What happens if two of the three `FirmwareManager` candidates are already merged and the third's reference count has changed? Regenerate the catalog before the third PR; if it dropped to Single-Use (or Unused), reroute per FR-016 carry-forward.
- How does the workflow handle multi-file callsite rewrites when one of the external callers is in a package that has its own compliance requirements (e.g. `src/gateway/gateway_export_utils.py`)? The external file's post-PR compliance MUST remain at its pre-PR grade or better. Analyzer flags on the external file are NOT in scope for this initiative unless the extraction directly introduces them.
- What happens when a candidate's `Suggested module` path uses double-underscore separators (e.g. `fast__mode__backoff__multiplier.py`)? Rename during landing to conventional single-underscore (`fast_mode_backoff_multiplier.py`) and record the rationale in the PR description.
- How does the workflow handle a `guideline_flags` list that includes `raw_input_call` (present on `WLANRadiusTimerManager`)? Rewrite raw `input()` to `safe_input()` per project non-negotiables (FR-007 of 1010, carried forward). Do NOT merge with `raw_input_call` unresolved.
- What happens if a large candidate (e.g. `FirmwareUpgradeStatusChecker` at 958 LoC) requires internal decomposition beyond the ≤25-line-per-method rule to satisfy A+/100? Split into ≤25-line methods with ≤5 params during the move — FR-006 carry-forward (decompose while moving).
- How does the workflow handle a merge conflict on `refactor_candidates.md` when a new first-party file is added to the module graph mid-flight (which would shift the "Definitions analyzed" count)? Serial per-PR workflow is non-negotiable — only one extraction PR is open at a time. Regenerate the catalog after each merge.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The second-pass extraction workflow MUST process Low-Use candidates in the LOC-DESC order specified by the freshest `refactor_candidates.md` at dispatch time, within their destination cluster (single-file P1 cluster processed before multi-file P2 cluster).
- **FR-002**: The workflow MUST process exactly one extraction candidate per PR. Batching multiple candidates into a single PR is prohibited (carry-forward from 1010).
- **FR-003**: For each Low-Use candidate, the PR MUST (a) create the target module file OR fold into the named `Suggested class`, (b) delete the original symbol from `MistHelper.py`, and (c) rewrite every listed callsite in the same commit. No wrapper shim, forwarding function, or backward-compatibility alias may be left in `MistHelper.py`.
- **FR-004**: For each candidate whose reference count has dropped to 0 by the time of dispatch (post-regeneration), the PR MUST be reclassified as a deletion PR (delete-only, no new module) — mirroring 1010's Unused workflow.
- **FR-005**: Module-level functions and bare module-level assignments that are extracted MUST be refactored into class-body methods/attributes on the new module, not preserved as bare module-level definitions (carry-forward from 1010 FR-005).
- **FR-006**: Analyzer-flagged `guideline_flags` on the extracted code (`oversize_25_lines`, `missing_inline_comments`, `missing_action_logging`, `non_ascii_logs`, `hardcoded_separator`, `raw_input_call`, and any other flags surfaced by the analyzer) MUST be resolved within the same extraction PR — never deferred to a follow-up (carry-forward from 1010 FR-006).
- **FR-007**: All extracted modules MUST comply with project non-negotiables: ASCII-only logs, `safe_input()` for interactive input, `pathlib.Path` in place of `os.path`, inline comments every 5-10 lines, action logging before/after every meaningful action with `%s` formatting, ≤25-line methods, ≤5 params per function (carry-forward from 1010 FR-007).
- **FR-008**: The initiative MUST NEVER touch symbols in the analyzer's `SKIP_ALWAYS` bucket (e.g. `GlobalImportManager`) (carry-forward from 1010 FR-008).
- **FR-009**: The initiative MUST NEVER touch symbols in the Hot bucket (4+ callers) — the destination class receiving an extracted method may itself be a Hot class, but the *source* symbol under extraction must be strictly Low-Use at dispatch time.
- **FR-010**: After every merged extraction PR, the workflow MUST regenerate `refactor_candidates.md` by running the analyzer against the current `main` head before the next PR is dispatched (carry-forward from 1010 FR-010).
- **FR-011**: An extraction PR MUST NOT merge until all 15 functional CI jobs report green. When `mergeStateStatus` reports BLOCKED, DIRTY, or BEHIND, the PR MUST be updated and re-run rather than force-merged. `--admin` merge bypass MUST NOT be used as a routine unblock. Reference `feedback_no_admin_bypass.md` (carry-forward from 1010 FR-011).
- **FR-012**: Every new module under `src/refactors/` (and any existing module receiving an extracted symbol, notably `src/firmware/firmware_manager.py` for the three `FirmwareManager` candidates) MUST land at A+/100 compliance score, and no file that was previously A+ may regress below A+ as a result of the extraction (carry-forward from 1010 FR-012).
- **FR-013**: The repository-wide compliance baseline MUST remain at or above 99.6/A+ after each merged extraction PR (carry-forward from 1010 FR-013).
- **FR-014**: The second-pass extraction budget covers exactly 20 candidates as enumerated in the "PR Dispatch Queue" section of `plan.md`. Additions to second-pass scope require explicit re-scoping in a new SpecKit revision.
- **FR-015**: Three candidates (`FirmwareUpgradeStatusChecker`, `BulkAPFirmwareUpgrader`, `BulkSwitchFirmwareUpgrader`) MUST be relocated into the existing `src/firmware/firmware_manager.py::FirmwareManager` class rather than into new `src/refactors/` modules, because their `Suggested class` explicitly targets that shared destination.
- **FR-016**: When the freshly regenerated `refactor_candidates.md` shows that a candidate has been reclassified out of the Low-Use bucket (e.g. Low-Use → Unused after a prior merge, or Low-Use → Hot after a caller-adding refactor elsewhere), the workflow MUST reroute or defer that candidate rather than force-extract it under the original classification (carry-forward from 1010 FR-016).
- **FR-017**: The initiative MUST NOT introduce new features, new commands, or scope beyond the extraction itself (carry-forward from 1010 FR-017).
- **FR-018**: The initiative MUST NOT modify `tools/refactor_analyzer/` itself; the analyzer is consumed as-is (carry-forward from 1010 FR-018).
- **FR-019** (new to 1011): The three candidates with cross-file callsites (`main`, `marvis_data_utils`, `MIST_WAN_TARGET_PORTS`) MUST have their external-file callsite rewrites verified by CI — not just by local pytest — before merge. Grep-based post-merge audit is the acceptance evidence.
- **FR-020** (new to 1011): Candidates whose `Suggested module` path uses double-underscore separators (e.g. `fast__mode__backoff__multiplier.py`) MUST be renamed to conventional single-underscore paths during landing (`fast_mode_backoff_multiplier.py`), and the rename rationale MUST be recorded in the PR description.

### Key Entities *(include if feature involves data)*

Same as 1010:

- **Extraction Candidate**: A class, function, or assignment in `MistHelper.py` catalogued by `tools/refactor_analyzer/` — for this initiative, restricted to Low-Use bucket entries (2-3 references) as of the freshest catalog at dispatch time.
- **Refactor Candidates Catalog** (`refactor_candidates.md`): Regenerated after every merged extraction PR (FR-010).
- **Extraction PR**: A single pull request delivering one candidate's move-or-delete plus its callsite rewrites plus any in-place `guideline_flags` remediation.
- **Target Module**: The new file under `src/refactors/` (or existing sibling module for `FirmwareManager` candidates) that receives an extracted symbol.
- **Callsite**: The exact location where a candidate is invoked — for Low-Use, may be 2-3 distinct locations, all of which must be rewritten atomically with the extraction.
- **Shared Destination Class**: A pre-existing class (e.g. `FirmwareManager`) that receives one or more extracted symbols as new methods, per the analyzer's `Suggested class` field.
- **Compliance Baseline**: The repo-wide compliance score maintained at ≥99.6/A+ with zero sub-A files.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Low-Use bucket of `refactor_candidates.md` reports 0 entries at second-pass completion (or documented rationale in the catalog's Limitations section explaining any deferrals — expected for candidates that transition to Hot mid-initiative).
- **SC-002**: `MistHelper.py` physical line count drops by at least 2,500 lines relative to its pre-initiative baseline (matches the 2,749 LoC extraction budget summed across the 20 Low-Use candidates minus small class-body overhead per new module).
- **SC-003**: Repository-wide compliance score is ≥99.6/A+ at every intermediate main-branch state throughout the initiative and at final completion.
- **SC-004**: Zero files that were A+/100 pre-initiative regress below A+ by the end of the initiative.
- **SC-005**: All second-pass PRs merge with 15/15 functional CI jobs green. Zero PRs merged via `--admin` bypass except where `mergeStateStatus` was genuinely BLOCKED/DIRTY/BEHIND with root cause documented in the PR.
- **SC-006**: Every new file created under `src/refactors/` during the initiative scores A+/100 on compliance.
- **SC-007**: Zero wrapper shims, forwarding functions, or backward-compatibility aliases remain in `MistHelper.py` after the initiative.
- **SC-008**: Zero symbols from the analyzer's `SKIP_ALWAYS` bucket are modified by any PR in this initiative.
- **SC-009**: Zero symbols from the Hot bucket (4+ callers) are extracted as *source* symbols during this second pass. (Destination classes may be Hot; that is allowed per FR-009.)
- **SC-010**: After every merged extraction PR, the analyzer is re-run and `refactor_candidates.md` is regenerated before the next PR is dispatched — verifiable by walking the merged-PR sequence.
- **SC-011**: Every analyzer-flagged `guideline_flag` on the extracted code is resolved within the extraction PR — zero forward-carried guideline violations attributable to this initiative.
- **SC-012**: The three cross-file candidates (`main`, `marvis_data_utils`, `MIST_WAN_TARGET_PORTS`) each have their external-file callsite rewrites verified by post-merge grep audit (FR-019).
- **SC-013**: The three `FirmwareManager` shared-destination candidates (`FirmwareUpgradeStatusChecker`, `BulkAPFirmwareUpgrader`, `BulkSwitchFirmwareUpgrader`) each land in `src/firmware/firmware_manager.py::FirmwareManager` without regressing that file's compliance grade below A+/100 (FR-015).

## Assumptions

- The analyzer at `tools/refactor_analyzer/` remains functionally correct for the Low-Use bucket across the initiative; discrepancies discovered during extraction are filed as analyzer bugs but do not block.
- The 15 functional CI jobs currently gating PRs on `main` remain the mergeability contract for the duration of this initiative.
- The current compliance baseline of 99.6/A+ is the floor; the initiative does not attempt to raise it beyond preserving it.
- The candidate-to-target-path mapping specified in `plan.md` reflects the fresh post-PR-13-merge catalog. If a candidate's callsite is discovered mid-extraction to have shifted (line number drift from an unrelated commit), the mapping is updated in the PR description.
- Serial per-PR workflow: at most one extraction PR is open at any time.
- The parent conversation controls PR dispatch cadence and branch creation. This spec exists to document the contract.
- Analyzer regeneration cost per run is negligible relative to CI cycle time; the "regenerate after every merge" discipline does not create a bottleneck.
- The 20-candidate scope reflects the fresh catalog at initiative kickoff. Mid-initiative reclassification (Low-Use → Unused, Low-Use → Hot) is expected and handled per FR-016; the initiative may complete with fewer than 20 merged PRs if candidates are legitimately deferred.
- Third-pass evaluation (any Low-Use candidate that transitions to Hot during this initiative, plus the 80 pre-existing Hot candidates) is out of scope for this specification.
