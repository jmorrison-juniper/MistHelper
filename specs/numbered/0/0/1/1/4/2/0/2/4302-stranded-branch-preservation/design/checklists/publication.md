# Publication Checklist: Stranded Branch Preservation

**Purpose**: Check each publication batch before any draft PR opens.
**Created**: 2026-11-26
**Feature**: `spec.md`, decision D-3, and task T-PR

Use one copy of this checklist for each batch. Mark each item with `[x]` only after its test passes.

## Before Any PR

- [ ] The owner comment on #4302 names the batch, and TST-14 passes.
- [ ] The repository visibility is PUBLIC (TST-04).
- [ ] The batch refs match the batch membership in `tasks.md`.
- [ ] No ref in the batch is a hold, or the hold is released in writing (TST-18).
- [ ] The scope check repeats, and the counts match `design/research.md` (TST-01 and TST-02).

## For Each Head

- [ ] The head commit equals the recorded head commit (TST-06).
- [ ] The content scan has no finding (TST-17). The scan records the head commit.
- [ ] The head commit has no PR-kept match that makes the PR unnecessary (D-4).

## For Each Draft PR

- [ ] The PR is a draft (TST-15).
- [ ] The PR head equals the recorded head (TST-15).
- [ ] The PR has no auto-merge label (TST-15).
- [ ] The PR body contains `Refs #4302` and omits `Closes #4302` (TST-15).
- [ ] The PR uses the branch name as its head, so the report matches it by name.

## After the Batch

- [ ] Each ref keeps its recorded head (TST-16).
- [ ] The proof comment follows `design/contracts/branch-disposition-table.md` (TST-24).
- [ ] The next scope check shows the batch as PR-kept or on the report (TST-02).
- [ ] No branch was deleted, rewritten, rebased, merged, or force-pushed (FR-008).

Warning: a published head stays readable after its PR closes. Complete every item before the PR opens.
