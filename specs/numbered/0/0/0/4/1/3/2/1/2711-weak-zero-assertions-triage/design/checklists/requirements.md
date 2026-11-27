# Specification Quality Checklist: Weak zero-assertion triage

**Purpose**: Check that the specification, plan, and tasks meet the quality rules before the implementation starts.

**Created**: 2026-11-26

**Feature**: `spec.md` in the feature root.

## Content Quality

- [x] No implementation detail appears in the user stories. The stories describe the maintainer's result.
- [x] The stories name the reader and the outcome.
- [x] Each mandatory section holds content. No section is empty.
- [x] Each requirement uses the `FR-###` form.
- [x] Each success criterion uses the `SC-###` form and a measurable result.

## Requirement Completeness

- [x] Every requirement maps to at least one task. The map appears in `analysis.md` section 3.
- [x] Every requirement names a check, a test, or a review step.
- [x] The edge cases name the failure condition and the expected handling.
- [x] The out-of-scope list names each excluded change.
- [x] The assumptions name the external dependency: the pinned analyzer and CI.
- [x] The Mist Cloud transport section states that the work does not apply.

## Feature Readiness

- [x] Each user story has an independent test.
- [x] Each task names exact repository paths.
- [x] Each task names one verification command from the local gates table or the test-quality ratchet.
- [x] The final tasks are T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE.
- [x] The plan passes the constitution check. The table in `plan.md` holds one result for each principle.
- [x] The remote verification table in `design/research.md` holds 37 rows. The `remote_checks` count in `2711-STATUS.json` and the summary count match it.

## Notes

- The count of 244 current findings is a prediction. T002 confirms it. The item remains open until T002 finishes.
- The 18-finding report in comment 167 is not reproduced. The item is recorded as `U-1` in `design/research.md`.
- No item is left unchecked. Each unverified claim appears in the `Unverified` list of `design/research.md`.
