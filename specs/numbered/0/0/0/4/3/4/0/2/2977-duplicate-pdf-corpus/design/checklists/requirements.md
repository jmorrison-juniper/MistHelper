# Specification Quality Checklist: Duplicate PDF Corpus

**Purpose**: Check that `spec.md` is complete, testable, and ready for planning.

**Created**: 2026-11-26

**Feature**: `spec.md` in this record

## Content Quality

- [x] CHK001 The spec names the affected classes and files only where the issue names them. The plan holds the implementation detail.
- [x] CHK002 Each user story states the operator or owner value.
- [x] CHK003 The spec uses plain words for an operator who reads the report.
- [x] CHK004 Every mandatory section holds content: user stories, requirements, success criteria, assumptions, out of scope, and clarifications.

## Requirement Completeness

- [x] CHK005 Each requirement FR-001 to FR-013 is testable. `tasks.md` maps each one to a task and a test.
- [x] CHK006 No clarification marker remains. The Clarifications section records each answer.
- [x] CHK007 Each success criterion states a measure. SC-001, SC-002, and SC-004 are measured by tests. SC-003, SC-005, and SC-006 are measured by the copy run.
- [x] CHK008 Edge cases cover equal sizes, empty files, moved or removed canonical files, sorter failures, and copy-root overlap.
- [x] CHK009 The Out of Scope section lists each excluded change and its decision identifier.
- [x] CHK010 Assumptions name the data path, the harvest stop, the disk capacity, the test data, and the successor issue.

## Feature Readiness

- [x] CHK011 Each functional requirement has a user story or an acceptance scenario that covers it.
- [x] CHK012 The user stories cover the three open parts: prevention evidence, sorter paths, and the copy run.
- [x] CHK013 The success criteria follow the requirements. Each criterion names its requirement set.
- [x] CHK014 The spec leaves the implementation detail to `plan.md` and the contracts.
- [x] CHK015 Two decisions need a human: D-9 and D-10. Both carry the HUMAN-DECISION-REQUIRED marker in `research.md`. The spec does not resolve them.
- [ ] CHK016 SC-003, SC-005, and SC-006 remain unchecked. Their measures need the copy run. The copy run waits for owner inputs (T010), so this item stays open until T012 completes.
