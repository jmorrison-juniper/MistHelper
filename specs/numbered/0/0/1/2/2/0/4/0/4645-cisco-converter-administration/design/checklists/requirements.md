# Specification Quality Checklist: Gated Converter Administration and Unassignment

**Purpose**: Confirm that the specification, plan, tasks, and analysis meet the quality rules before implementation starts.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

## Content Quality

- [x] CHK001 Requirements use stable IDs from FR-001 through FR-028. Source: `spec.md`, Requirements.
- [x] CHK002 Success criteria SC-001 through SC-007 name a measurable check. Source: `spec.md`, Success Criteria.
- [x] CHK003 Each user story names an independent test and at least one acceptance scenario. Source: `spec.md`, User Scenarios.
- [x] CHK004 Each requirement maps to at least one task and at least one test or verification command. Source: `analysis.md`, Coverage Summary.
- [x] CHK005 The record names no placeholder text. Source: the self-review in this record, which searches for each forbidden token.
- [x] CHK006 Assumptions name each dependency on issues 4634, 4636, 4643, and 4648. Source: `spec.md`, Assumptions A-2 to A-6.
- [x] CHK007 Out of Scope names each excluded operation and each excluded issue. Source: `spec.md`, Out of Scope.
- [x] CHK008 Clarifications record each answer and the decision that holds it. Source: `spec.md`, Clarifications.

## Requirement Completeness

- [x] CHK009 Human decisions are limited to D-1, D-2, and D-3, and each carries the marker HUMAN-DECISION-REQUIRED. Source: `design/research.md`, Decisions.
- [x] CHK010 Each Warning statement starts with the word Warning. Each Caution statement starts with the word Caution. Source: `spec.md`, Out of Scope.
- [x] CHK011 Each Mist claim cites the local OpenAPI line or the SDK line. Source: `design/contracts/mist-administration.md`.
- CHK012 Each code, test, configuration, and document claim has one remote check row. The count is 72 in `design/research.md` and in the STATUS file. Source: `design/research.md`, Remote Verification.
- [x] CHK013 Each unknown has an identifier and an owner. Source: `design/research.md`, Unverified, and `analysis.md`, Unresolved Items.
- [x] CHK014 The record cites no upstream source that it did not fetch. Source: `design/research.md`, Sources.

## Feature Readiness

- [x] CHK015 The route folder holds five children or fewer after this record. Source: `design/research.md`, RC-47, and `plan.md`, Constitution Check.
- [x] CHK016 The test folders hold five children or fewer. Source: `plan.md`, Complexity Tracking, and `design/research.md`, D-5.
- [x] CHK017 The source change depends on a root slot. The dependency is recorded as finding F-01 and task T002. Source: `analysis.md`.
- [x] CHK018 No task starts a live Mist write. Source: `tasks.md`, Prerequisites, and `design/quickstart.md`, Scenario 9.
- [x] CHK019 The design includes the refusal path for each gate. Source: `design/contracts/portal-administration.md`, Gate Order.
- [x] CHK020 The record names a verification command for each task. Source: `tasks.md`.

## Notes

- Each item is checked. The record states no exception.
- Decisions D-1, D-2, and D-3 need owner decisions before any implementation task starts.
