# Specification Quality Checklist: Quality gate failure from the mando 0.8.2 pin

**Purpose**: Validate the record completeness before implementation starts.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Content Quality

- [x] The failing check, the failing step, and the failing rule are named with log or line evidence (FR-001, research R02 and R03).
- [x] Each requirement uses MUST or an active verb in one sentence.
- [x] All mandatory sections are complete.
- [x] Implementation names appear only where the issue names them or a requirement needs an exact path.

## Requirement Completeness

- [x] Each FR maps to at least one task and at least one test (analysis Coverage Summary).
- [x] Each success criterion is measurable.
- [x] Edge cases are listed.
- [x] Out of scope is stated.
- [x] Assumptions are listed. Each unverified assumption points to an item in research Unverified.
- [x] Clarifications list each recorded answer.

## Feature Readiness

- [x] Each user story has an independent test.
- [x] Each factual claim in the spec cites a research row, a constitution line, or an Unverified item.
- [x] No unfinished text remains in any file of the record.

## Notes

- The evidence check passes. Each claim in `spec.md` cites a row from `design/research.md` (R01 to R51).
- The clarification check passes. The Session 2026-11-26 entries record four answers and their sources.
- The unverified check passes. Items U-1 to U-7 in `design/research.md` name each claim that the spec phase did not verify.
