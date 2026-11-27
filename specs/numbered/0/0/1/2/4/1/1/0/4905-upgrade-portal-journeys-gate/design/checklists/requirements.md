# Specification Quality Checklist: Upgrade Portal Journeys Gate on PR 4888

**Purpose**: Check the quality of `spec.md`, `plan.md`, and `tasks.md` before implementation.
**Created**: 2026-11-26
**Feature**: `spec.md` in the feature root

## Content Quality

- [x] CHK001 The spec names the failed check, job, run, step, and rule. (spec.md, FR-001)
- [x] CHK002 The spec states that no test ran. (spec.md, FR-002)
- [x] CHK003 The spec avoids implementation detail that a reader does not need. The plan holds the file-level detail.
- [x] CHK004 The spec gives user stories with priorities P1 and P2. Each story has an independent test.
- [x] CHK005 The spec writes each success criterion as a measurable result. (spec.md, SC-001 to SC-004)

## Requirement Completeness

- [x] CHK006 Each requirement FR-001 to FR-011 has at least one test or check. The mapping is in tasks.md.
- [x] CHK007 No placeholder text remains. The only marker is `HUMAN-DECISION-REQUIRED`, and no decision uses it.
- [x] CHK008 Each decision names two or more alternatives and a recommended option (research.md, D-1 to D-6).
- [x] CHK009 The edge cases name each boundary condition (spec.md, Edge Cases).
- [x] CHK010 The out-of-scope list names each excluded change (spec.md, Out of Scope).
- [x] CHK011 The assumptions state each external fact and its verification status (spec.md, Assumptions).
- [x] CHK012 The clarifications record each answer with its evidence (spec.md, Clarifications).
- [x] CHK013 The commit identity conflict is recorded. The issue cites the merge commit, and the job ran on the PR head (research.md, E-3).
- [ ] CHK014 The Dependabot range form is verified. Explained: U-1 remains open until the first pip update run after the merge.

## Feature Readiness

- [x] CHK015 Each requirement has an acceptance path in a user story or a check.
- [x] CHK016 The plan traces each file change to a requirement (plan.md, File Change Map).
- [x] CHK017 The tasks list the repository paths and one verification command for each task.
- [ ] CHK018 Every local gate passes on the fix branch. Explained: task T-LOCAL-GATES runs the gates after the implementation. Research did not run them.
- [ ] CHK019 Remote CI passes on the fix pull request. Explained: task T-REMOTE-CI watches the run after T-PR.
- [ ] CHK020 PR 4888 is closed with a preservation proof. Explained: task T-MERGE runs this step after the merge and the orchestrator authorization.

## Notes

- Items CHK014, CHK018, CHK019, and CHK020 remain open by design. Each names the task or the authorization that closes it.
- The checklist covers the specification only. The CI gate checklist is `ci-gate.md`, and the dependency checklist is `dependency-pin.md`.
