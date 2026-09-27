# Specification Quality Checklist: The browser seed captures hold the counts of a real capture

**Purpose**: Validate the completeness and the quality of the specification
before the plan.
**Created**: 2026-09-27
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] The specification holds no implementation detail that the feature does
  not need. The notes below name each exception.
- [x] The specification states the value for the operator and for the test
  author.
- [x] A reader with no technical background can read the problem, the user
  stories, and the success criteria.
- [x] Each mandatory section is complete.

## Requirement Completeness

- [x] No marker of an open question remains.
- [x] Each requirement is testable and clear.
- [x] Each success criterion is measurable.
- [x] Each success criterion is free of technology.
- [x] Each acceptance scenario is defined.
- [x] The edge cases are identified.
- [x] The scope has clear limits.
- [x] The dependencies and the assumptions are identified.

## Feature Readiness

- [x] Each functional requirement has a clear acceptance scenario.
- [x] The user scenarios cover the primary flows.
- [x] The feature meets the measurable results of the success criteria.
- [x] No implementation detail leaks into the specification without a reason.

## Notes

- The feature changes the test seeds, and the users of a seed are test
  authors. The shipped function `build_counts` is the contract of a real
  capture, so FR-001 and FR-002 must name it.
- FR-004 names the `title` attribute. The user interface contract of the
  history page fixes it, and a keyboard user or a screen reader depends on it.
- The row budget of 48 pixels comes from issue #2106. The success criteria
  quote the number, because a browser test measures it.
- The state counts of a seed follow the builder. Issue #3494 holds the state
  gap of the seed index, so this change adds no state count by hand.
