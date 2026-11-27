# CI Gate Checklist: Upgrade Portal Journeys Gate on PR 4888

**Purpose**: Check that the record names the failed gate, the failed rule, and the evidence for each claim.
**Created**: 2026-11-26
**Feature**: `spec.md`, `analysis.md`, and `design/research.md`

## Failure Identity

- [x] CHK101 The record names the check `Upgrade portal journeys` and its job key `upgrade_portal_journeys` (research.md, E-1).
- [x] CHK102 The record names workflow run 45064243269 and job 137339161249 (research.md, R-62).
- [x] CHK103 The record names the failed step `Install dependencies` (research.md, R-62).
- [x] CHK104 The record names the failed rule. The rule is the pip resolution rule `ResolutionImpossible` between line 365 and `mando==0.8.2` (research.md, E-1).
- [x] CHK105 The record states that no journey test ran (research.md, E-1).
- [x] CHK106 The record explains the upload failure as a consequence of the install failure (research.md, E-1).

## Commit Identity

- [x] CHK107 The record names the merge commit that the issue cites and the PR head that the job ran on (research.md, E-3).
- [x] CHK108 The record names the base commit of the merge (research.md, E-3).

## Comparison With Main

- [x] CHK109 The record shows that main passes the same job (research.md, E-4).
- [x] CHK110 The record names the sibling gate issues from the same PR (research.md, E-2).
- [x] CHK111 The record names the two aggregator jobs and their upstream cause (research.md, E-2).
- [x] CHK112 The record names the two other failed workflow runs on the same head (research.md, E-2).

## Guard Behavior

- [x] CHK113 The record explains why the journeys guard test passes on the failing PR (analysis.md, A-7).
- [x] CHK114 The record explains why the export guard would fail after a pip fix (analysis.md, A-6).

## Verification

- [ ] CHK115 The journeys gate passes on the fix pull request. Explained: task T-REMOTE-CI reads the job conclusion after the run completes.
- [ ] CHK116 The journeys guard test passes after the change. Explained: task T-LOCAL-GATES runs `tests/guardrails/test_upgrade_portal_journey_ci.py`.
- [ ] CHK117 The gate on main passes after the merge. Explained: task T-MERGE reads the job conclusion on the merge commit.
