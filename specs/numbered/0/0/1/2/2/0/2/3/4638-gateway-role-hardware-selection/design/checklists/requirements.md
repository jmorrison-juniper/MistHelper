# Specification Quality Checklist: Add explicit gateway role and hardware selection

## Content Quality

- [x] Each user story names a role, a family, a model, or a port, and the value that the user gets.
- [x] The spec names no implementation library and no class design. The plan holds the class design.
- [x] Each requirement uses the word MUST and names one observable result.
- [x] No placeholder text appears in the record.

## Requirement Completeness

- [x] Each FR row cites a source line in the parity map, the OpenAPI file, the cabling text, or the issue.
- [x] Each FR maps to at least one task and at least one test in `tasks.md` and `analysis.md`.
- [x] Each success criterion has a measurable result and a test or gate.
- [x] Edge cases name each blocker code in `proposal-json.md`.
- [x] Out-of-scope items name the issue that owns each item.
- [x] Assumptions name the issues that must merge first (A-1 and A-2).

## Feature Readiness

- [x] Each user story has an independent test.
- [x] The change adds no Mist call, no route registration, and no apply path (FR-018, D-13).
- [x] Human decisions: none. D-18 records the reason.
- [x] The clarifications record each answer with its decision number.
- [x] The safety statements begin with `Warning:` or `Caution:` and state a consequence.

## Notes

- Items that need issue 4634 stay open until that issue records field semantics (T001).
- The Branch mapping is unverified (UV-01). The spec blocks it and does not claim a verified mapping.
