# Specification Quality Checklist: Mando pin conflict in the pip-audit gate

**Purpose**: Check the spec, the plan, and the tasks before the implementation starts.
**Created**: 2026-11-26
**Feature**: `spec.md`

## Content Quality

- [x] No unresolved marker remains. A search of the records found no forbidden marker.
- [x] The spec names the failing check, the failing step, and the failing rule (spec, Clarifications).
- [x] Each claim in the research cites a remote row or a local source. The rows are in `design/research.md`.
- [x] Each requirement uses MUST or MUST NOT.
- [x] The writing follows the Simplified Technical English rules that AGENTS.md sets.

## Requirement Completeness

- [x] Each FR maps to at least one task. The mapping is in `analysis.md`, Coverage Summary.
- [x] Each FR maps to a test or a named manual check. FR-008, FR-011, and FR-012 use a manual check, and `analysis.md` explains why.
- [x] Success criteria SC-001 to SC-005 are measurable.
- [x] Edge cases name each conflict path that the spec covers.
- [x] Non-goals list each item that the change excludes.
- [x] Assumptions state the owner authorization. U-1 names the unverified effect on security updates.

## Feature Readiness

- [x] Each task names a verification command from the local gates table, or the check that proves the result.
- [x] Each decision names two or more alternatives, the choice, the reason, and the risk (`design/research.md`).
- [x] No human decision is required. The decisions fall outside the four human-decision categories.
- [x] The record names the owner step, Principle IV step 12, and the owner authority for it (D-8).

## Notes

- All items are checked for the state of the remote repository on 2026-11-26.
- Twelve items remain unverified. They are listed in `design/research.md`, under Unverified.
