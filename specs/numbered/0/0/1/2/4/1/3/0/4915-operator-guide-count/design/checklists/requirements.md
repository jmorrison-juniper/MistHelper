# Specification Quality Checklist: Operator Guide Operation Count

**Purpose**: Check the spec quality before the plan and the tasks run.
**Created**: 2026-11-26
**Feature**: `spec.md` in this record

## Content Quality

- [x] The spec names exact repository paths. Explained: the success criteria and the requirements depend on those paths.
- [x] Each user story gives a priority, a reason, and an independent test.
- [x] Each functional requirement uses MUST and states one testable condition.
- [x] The spec states the outcome for the operator and the maintainer, not the code structure.

## Requirement Completeness

- [x] Each functional requirement maps to at least one task and one test (`analysis.md`, Coverage Summary).
- [x] Each success criterion is measurable (SC-001 to SC-005).
- [x] The edge cases cover the count pattern, the link, the missing target, and the STE mode.
- [x] The out-of-scope list names each related defect that stays outside this change.
- [x] The assumptions state the baseline commit and the merge authorization.
- [x] Each clarification records the answer and the evidence or decision.

## Feature Readiness

- [x] The record contains no placeholder text.
- [x] Each technical choice has a decision with alternatives (D-1 to D-8 in `design/research.md`).
- [x] No decision needs a human answer. The human decision count is 0.
- [x] Each claim about remote code cites a remote verification row (R-01 to R-92).

## Notes

- The spec names the test function `test_operator_guide_defers_the_count_to_the_menu_reference`. FR-007 requires that test, so the name is part of the requirement.
- Analysis item A-7 records a conflict between Principle IV and documentation-only changes. The conflict does not change the spec requirements.
