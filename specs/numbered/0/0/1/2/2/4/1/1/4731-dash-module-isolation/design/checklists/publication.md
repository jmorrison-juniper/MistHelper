# Publication Checklist: Dash module isolation for map callback tests

**Purpose**: Track the owner hold, the serial order, and the contents of each pull request.
**Created**: 2026-11-26
**Feature**: spec.md, plan.md, and tasks.md

## Holds and Order

- [ ] PUB01 The owner released the publication hold before the first pull request opened (FR-023). Check the owner's message.
- [ ] PUB02 The publication order is wave A, wave B/C, wave D, and wave E2 (FR-024).
- [ ] PUB03 Each pull request waits for the previous pull request to merge (FR-025).

## Branch and Commit

- [ ] PUB04 Each branch uses one of the four names in tasks.md, and each starts from main (FR-016).
- [ ] PUB05 The commit subject and the pull request title start with `fix(maps):` and pass the title check (constitution Principle IV, step 4).
- [ ] PUB06 No held candidate commit was rebased, amended, or pushed (FR-027).

## Pull Request Body and Labels

- [ ] PUB07 Earlier pull requests use `Refs #4731`. The final pull request uses `Closes #4731` (FR-026).
- [ ] PUB08 The body lists the local gate results and the red-control result (FR-028).
- [ ] PUB09 The pull request carries the `bug` and `tests` labels (research row R50).

## Changelog and Scope

- [ ] PUB10 One changelog fragment is added. Its name starts with `pr-` and ends with the pull request number (FR-022).
- [ ] PUB11 The changed file list holds the slice file and the fragment only (FR-016, quickstart QS-16).
- [ ] PUB12 The wave E1 file and the baseline file have no diff (FR-029, FR-017).

## CI and Merge

- [ ] PUB13 Every check in the rollup reports SUCCESS before the `auto-merge` label is added (AGENTS rule, research row R38).
- [ ] PUB14 The orchestrator authorizes each merge (task T-MERGE).
- [ ] PUB15 The issue closes only after the final merge (SC-006).

## Notes

- Each item stays open until its pull request reaches the matching step.
- Caution: Publishing before the owner releases the hold breaks the owner's instruction.
