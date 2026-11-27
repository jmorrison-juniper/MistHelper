# Specification Quality Checklist: Nested Source Package Child Counts

**Purpose**: Check the completeness and quality of `spec.md` before the wave 1 slices start.

**Created**: 2026-11-26

**Feature**: `spec.md` in this record

## Content Quality

- No open clarification marker remains.
- [x] The record names each violating directory. Explained: the measure needs exact paths, so implementation names appear.
- [x] Each user story states its priority and its independent test.
- [x] The record names the owner of each violation.
- [x] Mandatory sections are complete.

## Requirement Completeness

- [x] Each requirement FR-001 to FR-014 has a test or a gate. Each task in `tasks.md` lists the requirement IDs that it satisfies.
- [x] Each requirement uses MUST and a single verifiable action.
- [x] Each success criterion has a number or a yes or no check.
- [x] Each edge case names its handling.
- [x] Scope and out-of-scope items are listed.
- [x] Dependencies name each open issue or pull request.
- [x] Assumptions name each source of truth.

## Feature Readiness

- [x] Each functional requirement maps to at least one task.
- [x] Each task names exact repository paths and one verification command.
- [x] Each violation maps to exactly one slice and one task.
- [x] Each decision names its alternatives, reason, and risk.
- [x] Human decisions are zero. Each decision reports `human_decision_required` as false.

## Notes

- The record uses paths and commands for each slice. A slice needs exact paths to be verifiable.
- No placeholder marker appears in the record. The self-review scan checks for each forbidden token.
