# Specification Quality Checklist: Backlog Handoff Recovery

## Content Quality

- [x] CHK001 The requirements name checks and rules, not code. The change has no code, so no implementation detail appears.
- [x] CHK002 Each user story names the maintainer action and its value.
- [x] CHK003 The spec has each mandatory section of the spec template: user scenarios, requirements, and success criteria.

## Requirement Completeness

- [x] CHK004 Each requirement uses MUST and states one testable rule.
- [x] CHK005 Each requirement maps to a task and a check. The coverage table in tasks.md shows the mapping, and TST-27 repeats the test.
- [x] CHK006 Each success criterion gives a count, a state, or a pass result.
- [x] CHK007 The edge cases cover rate limits, drift, account identity, hold phrases, Windows guard failures, and route changes.
- [x] CHK008 The out-of-scope list names each excluded action.
- [x] CHK009 Each assumption names its source, or it states that it is an assumption.

## Feature Readiness

- [x] CHK010 Each human decision names its options and its recommended option in design/research.md (D-2, D-12, D-13, and D-14).
- [x] CHK011 The clarifications record each answer with its session date.
- [x] CHK012 The route 0/0/1/2/3/4/4/0 matches the base-5 form of 4870. Check TST-19 shows the derivation.
- [x] CHK013 The counts in spec.md match design/research.md: 166 open issues, 7 open PRs, 63 recovery refs, 169 archive tags, and 79 remote rows.

## Notes

- All thirteen items are checked against the files of this record. The gate results are not part of this checklist. Task T-LOCAL-GATES runs the STE gate and the two guard tests on the implementer machine.
