# Contract: Compliance Gate

**Feature**: `specs/1012-misthelper-refactor-hot-functions/`
**Contract kind**: Quality-gate contract — enumerates the numeric thresholds and file-level grades the PR must satisfy for merge eligibility.

---

## Contract Statement

**The PR preserves the aggregate compliance baseline and adds two A+/100 files.** No pre-existing A+ file may regress. Pylint aggregate score must not fall below `8.74/10`.

## Numeric Thresholds

| Metric | Threshold | Verified By |
|--------|-----------|-------------|
| Aggregate repo compliance | `>=99.6/A+` | `tools/compliance_analyzer` sweep against post-PR head |
| Pylint aggregate score | `>=8.74/10` | `pylint src/ MistHelper.py` |
| `src/refactors/is_debug_mode.py` grade | `A+/100` | Per-file `tools/compliance_analyzer` invocation |
| `src/refactors/connection_pool_executor.py` grade | `A+/100` | Per-file `tools/compliance_analyzer` invocation |
| `MistHelper.py` grade | Non-regressing (>= pre-PR grade) | Pre/post comparison |
| Every touched file grade | Non-regressing (>= pre-PR grade) | Pre/post comparison |

## Per-File Grade Contract

For every file in the edit surface (see plan.md Edit Surface manifest), the pre/post grade table MUST show:

- **New files** (`is_debug_mode.py`, `connection_pool_executor.py`): grade is `A+/100`.
- **Existing A+ files** touched by the PR: post grade is `A+/100` (no regression).
- **Existing non-A+ files** touched by the PR: post grade is `>=` pre grade (may improve; must not regress). Per FR-019 carry-forward, the PR is not required to bring these to A+/100.

The PR body MUST include this table (produced by comparing analyzer output on `main` head vs. PR head):

```
| File                                            | Pre-Grade | Post-Grade | Delta |
|-------------------------------------------------|-----------|------------|-------|
| src/refactors/is_debug_mode.py                  | (new)     | A+/100     | +new  |
| src/refactors/connection_pool_executor.py       | (new)     | A+/100     | +new  |
| MistHelper.py                                   | <X>       | <Y>        | >=0   |
| src/export/site_export_utils.py                 | <X>       | <Y>        | >=0   |
| src/gateway/gateway_export_utils.py             | <X>       | <Y>        | >=0   |
| src/gateway/gateway_stats_exporter.py           | <X>       | <Y>        | >=0   |
| src/gateway/overrides/_deps.py                  | <X>       | <Y>        | >=0   |
| src/gateway/overrides/device_data_fetcher.py    | <X>       | <Y>        | >=0   |
```

## Guideline Flag Resolution (FR-006 carry-forward)

The two new files MUST land with **zero** open `guideline_flags` from the analyzer catalog:

- No `missing_inline_comments` (Constitution VI, NON-NEGOTIABLE — 5-10 line cadence).
- No `missing_action_logging` (Constitution VII, NON-NEGOTIABLE).
- No `raw_input_call` (neither module prompts; vacuously satisfied).
- No `non_ascii_logs` (both modules use ASCII-only log format).
- No `oversize_25_lines` (Action 2's `check()` is trivially small; Action 3's `execute()` may exceed 25 lines but the origin already exceeded it and the flag applies to *new* violations only — pre-existing size is preserved).

If the pre-existing origin function `execute_with_connection_pool_management()` was flagged for `oversize_25_lines`, the flag is inherited to the new home and MUST be resolved in this PR (matches 1011's precedent for `FirmwareUpgradeStatusChecker`).

## CI Job Contract (15 Green Jobs)

The following 15 CI jobs MUST report success:

1-4. Matrix build (Python 3.13 x 4 OS combinations if applicable)
5. Ruff lint
6. Ruff format check
7. Black format check
8. Mypy type check
9. Pylint score gate (>=8.74)
10. Compliance analyzer (per-file A+ verification)
11. Refactor analyzer smoke (catalog regeneration)
12. Unit test suite
13. Integration test suite (gateway path)
14. Integration test suite (export path)
15. End-to-end smoke (import MistHelper + minimal CLI menu render)

If any job reports failure, the PR MUST NOT merge. **No `--admin` bypass** unless the failure has been triaged and root-caused per `feedback_no_admin_bypass.md`:

- Check `gh pr view --json mergeStateStatus`; if `CLEAN`, merge normally.
- If `BLOCKED` / `DIRTY` / `BEHIND`, do not reach for `--admin` reflexively. SKIPPED conditional jobs are NOT blocking.
- Document any required bypass with root-cause analysis in the PR body.

## Pre-Push Local Gate (feedback_prepush_black_ruff.md)

Before pushing any commit to this branch, the contributor MUST run:

```bash
black --check src/ MistHelper.py
ruff check src/ MistHelper.py
ruff format --check src/ MistHelper.py
```

All three MUST report zero diff / zero issues. Pushing a commit that fails any of these gates wastes CI cycles and is explicitly discouraged.

## Non-Contracts

- The contract does NOT require increasing test coverage as part of this PR. Coverage may be added in a follow-up if analyzer surfaces a gap.
- The contract does NOT require bringing every touched external file to A+/100. Only new files land A+; existing files stay non-regressing.
- The contract does NOT require `refactor_candidates.md` to be updated in the same PR. That file is regenerated post-merge per FR-010 carry-forward.
