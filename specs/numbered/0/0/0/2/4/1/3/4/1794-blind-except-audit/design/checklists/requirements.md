# Checklist: requirements quality

**Purpose**: Check that `spec.md` is complete, testable, and traceable before the first slice.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

## User stories and scope

- [x] CHK001 Each user story has a priority, an independent test, and acceptance scenarios (spec.md, User Scenarios).
- [x] CHK002 The out-of-scope list names each excluded item and its owner or decision (spec.md, Out of Scope, and D-7, D-8).
- [x] CHK003 The assumptions cite a research row or a repository rule (spec.md, Assumptions).
- [x] CHK004 The dependencies name each issue that gates or coordinates a slice (spec.md, Dependencies).

## Requirements

- [x] CHK005 Each functional requirement uses MUST and names one behavior that a test or a command can check (spec.md, FR-001 to FR-038).
- [x] CHK006 Each requirement maps to at least one task and at least one check (analysis.md, Coverage matrix).
- [x] CHK007 Each success criterion has a number or a command (spec.md, SC-001 to SC-012).
- [x] CHK008 The edge cases name the handler type and the outcome for each type (spec.md, Edge Cases).

## Evidence and clarifications

- [x] CHK009 Each remote claim in the spec cites a row in `design/research.md` (129 rows, RC-001 to RC-129).
- [x] CHK010 Each clarification records its answer and its citation (spec.md, Clarifications).
- [x] CHK011 Each unverified item has an owner, a disposition, or both (analysis.md, Unresolved items).

## Writing rules

- [x] CHK012 Each deliverable is complete. No unfinished marker or empty section remains.
- [x] CHK013 The deliverables contain no semicolon in prose, and no contraction or Latin abbreviation.
- [x] CHK014 No human decision is required. The record marks zero decisions as human decisions.
- [x] CHK015 The legacy records are superseded and not deleted (FR-030, D-11, T036).
