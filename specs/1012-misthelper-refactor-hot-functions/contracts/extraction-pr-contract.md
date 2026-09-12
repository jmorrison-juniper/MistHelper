# Contract: Extraction PR (Single-PR Atomicity)

**Feature**: `specs/1012-misthelper-refactor-hot-functions/`
**Contract kind**: PR-shape contract — the PR body, diff, and merge conditions must all satisfy the invariants below.

---

## Contract Statement

**The initiative ships as exactly one PR** that lands all three actions (SC-001, SC-002, SC-003) atomically. Between opening and merging this PR, no intermediate state may exist on `main` where any action is partially applied.

## Diff-Shape Invariants

The PR diff MUST contain all of the following in a single atomic commit series (squashed at merge):

1. **Two new files**: `src/refactors/is_debug_mode.py`, `src/refactors/connection_pool_executor.py`.
2. **Two symbol deletions** from `MistHelper.py`: `def is_debug_mode()` at :318-320, and `def execute_with_connection_pool_management()` + 3 `_pool_*` helpers at :7503-7576.
3. **One wrapper deletion** from `MistHelper.py`: `EnvironmentUtils.is_debug_mode` at :5891-5900 (0 callers per clarification Q1).
4. **19 callsite rewrites**:
   - 12 for `is_debug_mode()` -> `IsDebugMode.check()` (all in `MistHelper.py`)
   - 4 for `execute_with_connection_pool_management(...)` -> `ConnectionPoolExecutor.execute(...)` in `MistHelper.py` (L6309, L10076, L15399, L15564)
   - 2 in `src/gateway/gateway_export_utils.py` (L48, L550)
   - 1 in `src/gateway/gateway_stats_exporter.py` (L32)
5. **12 DI-slot rename occurrences** (see `di-slot-rename-contract.md` for the layer-by-layer breakdown).
6. **5 mandatory NOTE breadcrumbs** matching the pinned templates (see `breadcrumb-audit-contract.md`) — 3 extraction breadcrumbs (E1/E2/E3 at MistHelper.py:635/~318/~7503) plus 2 DI rename canonical NOTEs (R-A at site_export_utils.py:32; R-B at _deps.py:18). The other 10 DI rename occurrences are silent renames.

The PR diff MUST NOT contain:

- Any wrapper shim, backward-compatible alias, or forwarding function preserving the old name (FR-003).
- Any change to files outside `MistHelper.py` and the 6 enumerated external files (`site_export_utils.py`, `_deps.py`, `device_data_fetcher.py`, `gateway_export_utils.py`, `gateway_stats_exporter.py`, and the two new files under `src/refactors/`).
- Any modification to `tools/refactor_analyzer/` (FR-018).
- Any change to the tqdm fallback shim source code at `MistHelper.py:635` (Action 1 is metadata-only).
- Any change to menu topology or `SKIP_ALWAYS` symbols beyond the Action 1 skip-pin.

## Merge-Condition Invariants

The PR MUST NOT merge until all of the following are true:

- All 15 functional CI jobs report success (green).
- `mergeStateStatus` is `CLEAN` (per `feedback_no_admin_bypass.md`; do not cargo-cult `--admin`).
- The pre-push local Black + Ruff gate has been run and produced no diff (per `feedback_prepush_black_ruff.md`).
- The compliance-gate contract (`compliance-gate-contract.md`) is satisfied: aggregate >=99.6/A+, pylint >=8.74/10, both new files A+/100.
- The DI-slot rename contract (`di-slot-rename-contract.md`) is satisfied: zero surviving occurrences of `is_debug_mode_fn` or `connection_pool_fn`.
- The breadcrumb-audit contract (`breadcrumb-audit-contract.md`) is satisfied: all 5 breadcrumbs discoverable by grep.

## Rollback Contract

If any post-merge signal indicates regression (CI job fails on a downstream branch, integration test surfaces an incompatibility, a caller path was missed), the rollback procedure is:

1. Open a single revert PR against `main` restoring the pre-1012 state of `MistHelper.py` and the 6 external files.
2. Restore the two deleted symbols and re-add the two deleted files (they were new — restoration means git deletion).
3. Delete the two new files under `src/refactors/`.
4. Do NOT attempt to partially revert (e.g., roll back only Action 3). The three actions were bundled precisely because their invariants interact; partial rollback would recreate the wrapper-shim state FR-003 prohibits.

## Success Criteria Traceability

| Contract clause | Traces to Spec SC |
|-----------------|-------------------|
| Two new files + two symbol deletions + one wrapper delete | SC-002, SC-003, SC-005, SC-011 |
| 19 callsite rewrites | SC-002 (12), SC-003 (7) |
| 12 DI-slot rename occurrences | SC-005 |
| 5 mandatory NOTE breadcrumbs | SC-014 |
| No wrapper shims | SC-008 (carry-forward from 1010/1011) |
| 15 CI jobs green + no --admin | SC-006 |
| Compliance >=99.6/A+, pylint >=8.74 | SC-007 |
| tqdm shim byte-identical | SC-001 |

## Non-Contracts

- The PR is not required to add unit tests for the new classes (existing integration tests exercise the callsites).
- The PR is not required to bring pre-existing non-A+ files up to A+/100 as a side effect of touching them (FR-019 carry-forward).
- The PR is not required to include analyzer output files in the diff (`refactor_candidates.md` is regenerated post-merge per FR-010 carry-forward).
