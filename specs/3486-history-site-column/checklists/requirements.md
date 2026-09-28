# Specification Quality Checklist: The Captures table of the history with no site names the site of each row

**Purpose**: Validate the completeness and the quality of the specification
before the plan.
**Created**: 2026-09-27
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] The specification holds no implementation detail. The module names
  appear only in the plan and in the research.
- [x] The specification states the value for the operator.
- [x] A reader with no technical background can read the specification.
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
- [x] No implementation detail leaks into the specification.

## Notes

- FR-003 names the `title` attribute, and FR-004 names a test identifier. The
  user interface contract of the portal fixes both, so a browser test and a
  screen reader depend on them.
- The requirements quote the exact caption, because the caption is part of
  the feature.
- The requirements name the query value `site_id`, because the contract of the
  history page names it.
- The work depends on issue #3482, which adds the scope of the history page.
  The code starts after the merge of that change.
