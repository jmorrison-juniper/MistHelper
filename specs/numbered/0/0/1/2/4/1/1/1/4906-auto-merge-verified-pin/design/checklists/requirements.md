# Requirements Checklist: Pin the verified auto-merge commit

**Purpose**: Check the quality of `spec.md` and its link to the plan and the tasks.
**Created**: 2026-11-26
**Feature**: `spec.md` in this record

## Content Quality

- [x] CHK001 Each requirement names one observable result. Evidence: FR-001 to FR-007 name a file, a value, a gate, or a folder route.
- [x] CHK002 The spec names no implementation detail beyond the paths and lines to change. Evidence: `plan.md` section "File-by-File Change Map" holds the paths and lines.
- [x] CHK003 Each user story has an independent test. Evidence: `spec.md` lists one independent test for each of the three stories.

## Requirement Completeness

- [x] CHK004 Each functional requirement maps to at least one task and one test. Evidence: `analysis.md` section "Consistency: Requirements, Tasks, and Tests".
- [x] CHK005 Each success criterion has a measurable result. Evidence: SC-001 to SC-004 name a check result, a line value, or a blob SHA.
- [x] CHK006 Each edge case names a result. Evidence: `spec.md` section "Edge Cases" lists five cases, and each names an action.
- [x] CHK007 Assumptions cite their remote evidence. Evidence: `spec.md` section "Assumptions" cites rows R-14 to R-16 in `design/research.md`.
- [x] CHK008 The out-of-scope list names each excluded change. Evidence: `spec.md` section "Out of Scope" names five exclusions.
- [x] CHK009 No placeholder text remains in the record. Evidence: a text search of the record finds no placeholder token.

## Feature Readiness

- [x] CHK010 Each task names one verification command from the local gates table. Evidence: `tasks.md` lists one command for each task. The two remote tasks name the watch command as a second step after the local command.
- [x] CHK011 The remote check count matches across the research table, the STATUS file, and the summary. Evidence: 48 rows in `design/research.md`, 48 entries in `remote_checks`, and the same count in the summary.
- [x] CHK012 No decision requires human approval. Evidence: decisions D-1 to D-9 each record `human_decision_required` as false.
