# Specification Quality Checklist: Narrow the pylint W0613 unused-argument suppression

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-07-29
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Feature-Specific Validation

- [x] All 21 measured findings appear in the site inventory
- [x] Every inventory row names a file, a line, a function, and a parameter
- [x] The three triage outcomes are defined with entry conditions
- [x] The spec forbids a file-wide and a repository-wide suppression
- [x] The spec forbids a silent parameter deletion at an Outcome C site
- [x] The spec requires the removal of `W0613` from the `disable` list as the final step
- [x] The spec requires a Linux continuous integration run to confirm the score
- [x] The spec states that a local Windows pylint run is not a safe proxy
- [x] The spec excludes `W0718` and the mypy `src.db` override
- [x] The spec records the maps clone confirmation-text observation without expanding scope
- [x] The spec records the inline-comment, Simplified Technical English, no-wrapper, and no-shim conventions

## Notes

### Content Quality justification

This feature changes a static-analysis configuration. The rule identifier `W0613`, the
configuration file `pyproject.toml`, and the threshold `9.5` are the subject of the
feature, not incidental implementation choices. The spec names them because a reader
cannot verify the outcome without them. The Success Criteria section still states the
outcomes in tool-neutral language.

### Open items carried into planning

- The triage must re-measure the baseline. The count of 21 is correct at commit `45c7b8d`
  on `main`. Other work may change it.
- Sixteen of the 21 findings have no verified outcome yet. The plan must schedule the
  per-site code reading.
- Two companion issues are expected. One covers the maps clone confirmation text. Any
  Outcome C site raises one more.
