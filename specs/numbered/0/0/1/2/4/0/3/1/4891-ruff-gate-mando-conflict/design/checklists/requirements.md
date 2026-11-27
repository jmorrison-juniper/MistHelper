# Specification Quality Checklist: Ruff (lint) check failure from the mando 0.8.2 pin

**Purpose**: Check the spec and the record for quality before the fix starts.
**Created**: 2026-11-26
**Feature**: `spec.md` in this folder

## Content Quality

- [x] CHK-01 The spec names files and commands only where a reader must verify the change.
- [x] CHK-02 Each user story states the user value and an independent test.
- [x] CHK-03 Each user story has a priority (P1 or P2).

## Requirement Completeness

- [x] CHK-04 Each FR has one testable statement.
- [x] CHK-05 Each SC names a check, a count, or a state that a reader can verify.
- [x] CHK-06 The edge cases cover the ignore entry, the patch releases, PR #4888, and the lint step.
- [x] CHK-07 The out-of-scope list names each excluded item and its analysis item where one exists.
- [x] CHK-08 Each clarification records its answer and its decision number.
- [x] CHK-09 FR-009 (inline comments and action logging) is checked in T002 and T-LOCAL-GATES.

## Feature Readiness

- [x] CHK-10 Every FR maps to at least one task and one verification (analysis, Coverage Summary).
- [x] CHK-11 Every remote claim has a row in `research.md`, section 7, and the row count matches the STATUS file.
- [x] CHK-12 No placeholder token remains in the record (self-review scan of step 8, item c).
- [x] CHK-13 Each directory of the record holds five children or fewer (self-review count of step 8, item d).
- [x] CHK-14 The record uses no semicolon, contraction, or Latin abbreviation (self-review scan of step 8, item e).

## Notes

- No item is unchecked.
- No item needs a human decision.
- The counts in CHK-11 match across `4891-STATUS.json`, `research.md`, and `4891-summary.md` (self-review step 8, item f).
