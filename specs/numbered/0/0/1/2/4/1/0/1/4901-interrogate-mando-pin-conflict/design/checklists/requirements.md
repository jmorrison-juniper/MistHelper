# Specification Quality Checklist: Interrogate Gate Failure on PR #4888

**Purpose**: Check the specification before planning and before the implementation starts.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Content Quality

- [x] No code appears in the specification. Code appears only in the plan and the tasks.
- [x] The specification focuses on the CI result and the policy outcome.
- [x] The specification uses plain words for a junior engineer.
- [x] All mandatory sections are complete.

## Requirement Completeness

- [x] No open marker remains. The clarifications record each answer.
- [x] Each requirement names a task and a test or check. The coverage table in `analysis.md` lists them.
- [x] Each success criterion uses a count, a check state, or a file state.
- [x] Edge cases list the expected behavior.
- [x] Scope excludes the workflow change, the radon upgrade, and the shared devtools change.
- [x] Dependencies and assumptions are listed.

## Feature Readiness

- [x] Each functional requirement maps to at least one task.
- [x] The user stories cover the failing check, the fix, and the closure of PR #4888.
- [x] The record names the failing check, the failing step, and the failing rule (FR-009, research R1).
- [x] No human decision applies. The section 6 categories do not match any decision.

## Notes

- Check 1, the failing identity: run 45064243269, job 137336719025, step `Run pip install -r requirements-dev.txt`. The source is research R1.
- Check 2, the failing rule: the resolver rejects `mando==0.8.2` against `radon==6.0.1`, which requires `mando<0.8`. The source is research R1 and R2.
- Check 3, the scope: 26 of 28 failed jobs share the resolver message. Two fail in aggregator steps. The source is research R2.
- Check 4, the rule for each new requirement: each requirement has a task in `tasks.md` and a check in `analysis.md`.
