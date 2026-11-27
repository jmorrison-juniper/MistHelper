# Specification Quality Checklist: Raw shell history test failure (issue 3767)

**Purpose**: Confirm that `spec.md`, `plan.md`, and `tasks.md` meet the record rules.
**Created**: 2026-11-26
**Feature**: `spec.md`

## Content Quality

- [x] CHK001 The spec names the failing test, its assertion, and its file path. Explained: FR-001 and research rows R-01 to R-03.
- [x] CHK002 The spec describes outcomes, not implementation steps. Explained: the spec states what the record shows. The plan holds the technical steps.
- [x] CHK003 Each user story has a priority and an independent test. Explained: US1 to US3 in `spec.md`.
- [x] CHK004 The spec names no unverified technical fact as proven. Explained: unverified claims are listed in `design/research.md` under "Unverified" (U-1 to U-11).

## Requirement Completeness

- [x] CHK005 Each requirement has a number in the form FR-###. Explained: FR-001 to FR-010 in `spec.md`.
- [x] CHK006 Each success criterion is measurable. Explained: SC-001 to SC-005 name counts, signatures, scores, or markers.
- [x] CHK007 Edge cases name the expected behavior. Explained: five edge cases in `spec.md`.
- [x] CHK008 Out-of-scope items are listed. Explained: five items in `spec.md`.
- [x] CHK009 Assumptions are recorded. Explained: four assumptions in `spec.md`.
- [x] CHK010 Clarifications record each answer. Explained: four clarifications in `spec.md`.

## Traceability

- [x] CHK011 Each requirement maps to at least one task. Explained: `analysis.md`, "Consistency Review".
- [x] CHK012 Each task names exact paths and a verification command. Explained: `tasks.md` names the paths and the command for each task.
- [x] CHK013 Each remote claim has a path, a ref, a blob SHA, a result, and a line. Explained: `design/research.md`, "Remote Verification Table".
- [x] CHK014 The remote row count equals the STATUS count. Explained: 74 rows in both files.

## Governance

- [x] CHK015 The route follows the base-5 rule. Explained: R-41 and `plan.md`, "Constitution Check".
- [x] CHK016 The record names no human decision. Explained: `design/research.md`, "Decisions", states that none applies.
- [x] CHK017 The record makes no change to the repository. Explained: D-1 and FR-007.
- [x] CHK018 The record names the owner authorization gate for the fixture change. Explained: T008 and D-4.

## Notes

- Each item states its evidence in the explanation after the check mark.
- Items CHK001 to CHK018 pass for the draft at the time of writing.
