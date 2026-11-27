# Specification Quality Checklist: Test quality: triage weak_is_not_none findings

**Purpose**: Check that the spec, plan, and tasks meet the quality rules before the first slice.
**Created**: 2026-11-26
**Feature**: `specs/numbered/0/0/0/4/1/3/1/3/2708-weak-is-not-none-triage/spec.md`

## Content Quality

- [x] CHK001 Each task names exact repository paths and lines. Explanation: the analyzer identity uses the file path and the line number.
- [x] CHK002 Each requirement is testable. Explanation: FR-004 and FR-006 name a controlled run and an analyzer confirmation.
- [x] CHK003 Each success criterion is measurable. Explanation: SC-001 to SC-005 use counts, gate results, and check results.
- [x] CHK004 The assumptions are stated. Explanation: the spec Assumptions section names the base commit, the analyzer, and the venv.

## Requirement Completeness

- [x] CHK005 Each functional requirement maps to at least one task. Explanation: the Coverage Summary in `analysis.md` lists each mapping.
- [x] CHK006 The edge cases are listed. Explanation: the spec Edge Cases section lists six cases.
- [x] CHK007 Each hold names its owner and its release condition. Explanation: tasks T011 to T014 and decisions D-5 and D-16.
- [x] CHK008 The out-of-scope items are listed. Explanation: the spec Non-Goals section lists five items.

## Feature Readiness

- [x] CHK009 Each task has an acceptance statement and a verification command. Explanation: `tasks.md` Phases 1 to 5 and the final tasks.
- [x] CHK010 Each remote claim has one row in the remote table. Explanation: `design/research.md` holds 139 rows, and the STATUS file holds the same count.
- [x] CHK011 Each conflict and defect in existing work is listed. Explanation: `analysis.md` findings A-1 to A-17.
- [x] CHK012 Each count appears with the same value in each file. Explanation: 84 entries, 65 present, 19 stale, 22 tasks, and 139 remote checks.

## Notes

- The checked items confirm the record as written. The analyzer run in task T001 confirms the counts on main.
- Unchecked items are not present. Each open question appears under Unresolved Items in `analysis.md` or under Unverified in `design/research.md`.
