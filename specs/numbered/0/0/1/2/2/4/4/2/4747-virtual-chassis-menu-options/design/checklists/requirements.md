# Specification Quality Checklist: Virtual Chassis Menu Guidance

**Purpose**: Confirm that `spec.md` is complete and testable before planning.
**Created**: 2026-11-26
**Feature**: `spec.md` in this record

## Content Quality

- [x] CHK001 The spec states the operator harm in plain words. Each user story names the wrong menu and its effect.
- [x] CHK002 The spec names no new technology. It names existing modules, menus, and tests only.
- [x] CHK003 Each mandatory section has content. The spec contains no placeholder text.

## Requirement Completeness

- [x] CHK004 Each functional requirement uses MUST and names an observable result.
- [x] CHK005 Each requirement maps to a task in `tasks.md` and to a test or gate. The coverage table in `analysis.md` shows the mapping. FR-008 and FR-012 map to the offline design and to gates, as the table states.
- [x] CHK006 Each success criterion names a check that can fail.
- [x] CHK007 Edge cases name each path that keeps its behavior.
- [x] CHK008 Assumptions and out-of-scope items are explicit.
- [x] CHK009 The spec contains no clarification marker. The Clarifications section records each answer with its evidence row.

## Feature Readiness

- [x] CHK010 Acceptance scenarios cover User Stories 1 to 3.
- [x] CHK011 The spec states the Mist Cloud impact (none) and the safety statements.
- [x] CHK012 Each fact that the spec cites has a row in `design/research.md`.
- [x] CHK013 The spec excludes the stale rename claim and the partial queue claim from the requirements. Both appear in Clarifications with their evidence.

## Notes

- CHK005 explanation: FR-008 is satisfied by design, because the tested helpers take no API session. FR-012 is satisfied by the menu reference gate and the registry guard.
