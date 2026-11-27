# Requirements Checklist: Hold mando below 0.8 for the mypy gate

**Purpose**: Spec quality check for `spec.md` before the code change starts.
**Created**: 2026-11-26
**Feature**: `spec.md` in this record.

## Content quality

- [x] CHK001 The spec names the failing check `mypy (strict)` and the run ID 45064243269.
- [x] CHK002 Each user story states a priority, an independent test, and acceptance scenarios.
- [x] CHK003 The spec states the user value of each story in plain words.
- [x] CHK004 The spec names no implementation tool except the existing repository tools.

## Requirement completeness

- [x] CHK005 Each functional requirement has a `FR-###` ID and uses MUST for each obligation.
- [x] CHK006 Each success criterion has a `SC-###` ID and a measurable result.
- [x] CHK007 Edge cases cover radon release, patch updates, manual pin edits, and unexplained jobs.
- [x] CHK008 Out of scope names the other quality-gate issues and the folder debt.
- [x] CHK009 Key Entities is marked not applicable, with a reason.
- [x] CHK010 Mist Cloud Transport Requirements is marked not applicable, with a reason.

## Feature readiness

- [x] CHK011 Each FR maps to at least one task in `tasks.md` (analysis.md section 1).
- [x] CHK012 Each FR maps to at least one test or gate (analysis.md section 1).
- [x] CHK013 Assumptions name their evidence in research.md, or they name the unverified item (section 8).
- [x] CHK014 Clarifications record an answer for each question.
- [x] CHK015 No human decision category applies, so no item needs a human decision.
- [x] CHK016 The spec and the plan name the same revisions and the same pins.

## Notes

- Items CHK001 to CHK016 are checked. Each check uses the evidence in `design/research.md`.
- The unverified items in research.md section 8 are open until T-LOCAL-GATES or T-REMOTE-CI verifies them.
