# Specification Quality Checklist: A failed multi-site journey ends each operation that it started

**Purpose**: Validate the completeness and the quality of the specification before the plan starts.
**Created**: 2026-09-28
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] The spec names the tests, the fixtures, and the routes that the change touches.
  The users of this change are the maintainers of the test suite, and they read those objects.
  The spec names no class design and no code structure.
- [x] The spec focuses on the value for the maintainer: a failed test leaves no operation that holds a site.
- [x] A maintainer who knows the browser suite can read each section.
- [x] Each mandatory section is complete.

## Requirement Completeness

- [x] No marker for a clarification remains.
- [x] Each requirement can be tested, and each requirement has one meaning.
- [x] Each success criterion can be measured.
- [x] The success criteria name results that a maintainer can see: a server log line, a status, a result line, and a time.
- [x] Each acceptance scenario is defined.
- [x] The edge cases are identified. They are a late start, a race between the end and the cancel, a refused cancel, and a bad body.
- [x] The scope is bounded: one conftest fixture, one browser module, one new journey, one support module, and the direct tests.
- [x] The dependencies and the assumptions are identified.

## Feature Readiness

- [x] Each functional requirement has a clear acceptance criterion.
- [x] The user scenarios cover the primary flows.
- [x] The feature meets the measurable outcomes of the success criteria.
- [x] No detail of the code structure is in the specification.

## Notes

- The users of this change are maintainers who run the browser suite.
  So the spec names test fixtures and portal routes, because a maintainer reads those objects.
- The spec names no library and no framework.
- The success criteria read the server log, the status of the operation, the result line, and the time of the teardown.
