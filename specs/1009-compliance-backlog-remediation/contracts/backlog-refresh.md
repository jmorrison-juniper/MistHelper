# Contract: Backlog Refresh Cadence

**Feature**: 1009-compliance-backlog-remediation
**Scope**: The rule that governs when and how `data/compliance_backlog.tsv` is regenerated.

---

## Trigger

Regenerate the backlog after every **5 merged remediation PRs**, OR whenever a merged PR is known to have modified a shared helper likely to lift multiple downstream files (operator discretion, but the every-5 cadence is the hard floor).

The initial backlog snapshot (authoring time, 99 files) is not a refresh -- it is the seed.

## Preconditions

- All 5 PRs since the last refresh have been `squash_merged`.
- The local checkout of `main` is up to date (`git pull --ff-only`).
- No `RemediationPR` is currently `opened` or `gates_green`.

## Commands (in order)

1. **Full recursive scan**:

   ```
   py -m tools.compliance_analyzer src -r -o data/full_repo_compliance.md -q
   ```

   `data/` is gitignored; the output stays local.

2. **Regenerate the TSV** using the same split-parser that produced the authoring-time snapshot. The parser MUST:
   - Consume `data/full_repo_compliance.md`.
   - Emit rows for every file with `score < 94.0` (i.e., sub-A).
   - Compute `rank` by sorting on the FR-002 rule: `total` desc, `critical` desc, `high` desc, `score` asc.
   - Write `data/compliance_backlog.tsv` with header `rank\ttotal\tcritical\thigh\tmedium\tlow\tscore\tgrade\tpath`.

3. **Diff-check** (operator visual sanity, not automated):
   - Confirm the file count has decreased (or is unchanged if transitive lift did not fire).
   - Confirm no file previously at A+ has appeared in the new TSV (would signal a regression covered by FR-017 / SC-003).

## Postconditions

- `data/compliance_backlog.tsv` reflects the freshly-computed queue.
- If any file transitioned A+ -> sub-A since the last refresh, that file is treated as a blocker: the next `Picked` transition MUST target it before any new `BacklogRow` from the ranked queue.
- Any picked file whose refreshed grade has already crossed >=A/94.0 is dropped (FR-016) -- it does not consume a PR slot.

## Rejection reasons (a refresh MUST be redone if any hold)

- The recursive scan output timestamp is older than the most recent squash-merge on `main`.
- The TSV was hand-edited between generation and use.
- The sort order in the TSV does not match the FR-002 rule.

## Termination check

After each refresh, check:

- If `data/compliance_backlog.tsv` is empty (no sub-A files) AND the recursive scan's overall score >=94.0, the initiative is complete (SC-001 + SC-002).
- If the TSV is empty but the recursive scan overall score is <94.0, the initiative continues; the operator identifies which file dragged the overall score down and opens a remediation PR against it (this indicates the analyzer's per-file grading and its overall aggregate can diverge on rare files near the boundary).
