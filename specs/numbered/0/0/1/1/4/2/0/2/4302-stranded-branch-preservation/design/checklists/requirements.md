# Specification Quality Checklist: Stranded Branch Preservation

**Purpose**: Check that `spec.md` meets the quality rules before the tasks run.
**Created**: 2026-11-26
**Feature**: `spec.md`

## Content Quality

- [x] Each requirement uses the word MUST and names one behavior.
- [x] The spec names no implementation tool beyond the commands in `design/quickstart.md`.
- [x] Each user story has a priority, an independent test, and acceptance scenarios.
- [x] Edge cases name the response for each case.

## Requirement Completeness

- [x] Each FR maps to at least one task in `tasks.md`.
- [x] Each FR maps to at least one test in `design/quickstart.md`.
- [x] Each success criterion has a measurable result.
- [x] No placeholder marker appears, except the three `HUMAN-DECISION-REQUIRED` markers (D-3, D-7, and D-10).
- [x] The scope decision is explained in the clarifications (D-1).
- [x] The out-of-scope list names each excluded action.
- [x] The assumptions name each dependency that the spec relies on.

## Feature Readiness

- [x] The three human decisions have a recommended option in `design/research.md`.
- [x] The publication steps have a gate that stops them.
- [x] Each hold has a named releaser or a named human reviewer.
- [x] The scope count matches the remote verification table (TST-01 and TST-02).

## Notes

- The scope is 505 rows, not one branch. Decision D-1 records the reason.
- No check in this checklist needs an explanation, because each item is checked.
