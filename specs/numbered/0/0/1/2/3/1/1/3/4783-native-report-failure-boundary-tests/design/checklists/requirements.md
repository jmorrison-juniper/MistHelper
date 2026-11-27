# Specification Quality Checklist: Native Report Failure-Boundary Tests

**Purpose**: Check that `spec.md` is complete, testable, and traceable before implementation.
**Created**: 2026-11-26
**Feature**: `spec.md` in the parent folder

## Content Quality

- [x] CHK001 Each user story states a priority, an independent test, and acceptance scenarios. (`spec.md`, User Scenarios)
- [x] CHK002 Each user story names the product boundary it tests, not an internal helper. (`spec.md`, User Stories 1 and 2)
- [x] CHK003 The glossary defines each term that the requirements use. (`spec.md`, Glossary)
- [x] CHK004 The Mist Cloud transport section states that the rule does not apply, with the reason. (`spec.md`, Mist Cloud Transport Requirements)

## Requirement Quality

- [x] CHK005 Each FR uses MUST or MUST NOT and names one checkable outcome. (`spec.md`, FR-001 to FR-016)
- [x] CHK006 Each FR maps to at least one task in `tasks.md`. (`tasks.md`, Requirement Coverage)
- [x] CHK007 Each FR maps to at least one planned test or to a check command. (`tasks.md`, Requirement Coverage)
- [x] CHK008 FR-009 and FR-010 name the blob SHAs and the `src/` rule that the check uses. (`spec.md`, FR-009, and `spec.md`, SC-004 and SC-005)
- [x] CHK009 FR-014 names the dependency and the rule that forbids a stacked branch. (`spec.md`, FR-014, and `research.md`, R-H)

## Success Criteria

- [x] CHK010 Each SC names a value, an exit code, or a printed line that a reviewer can read. (`spec.md`, Success Criteria)
- [x] CHK011 SC-003 names the seven cases that `plan.md` lists. (`plan.md`, Planned Test Cases)

## Edge Cases and Scope

- [x] CHK012 Each edge case names an input and an expected result. (`spec.md`, Edge Cases)
- [x] CHK013 Out of Scope names each excluded path, rule, or concern. (`spec.md`, Out of Scope)
- [x] CHK014 Assumptions name the external state that the record relies on. (`spec.md`, Assumptions)

## Clarifications and Evidence

- [x] CHK015 Each recorded answer in Clarifications cites a remote or local evidence row. (`spec.md`, Clarifications, and `research.md`, Remote Verification Table)
- [x] CHK016 No placeholder marker appears in the record. Each file was searched for the forbidden tokens. (`analysis.md`, Structure and Style Review)
- [x] CHK017 The human decision D-2 is the only item that needs a human. (`research.md`, Decisions, and the decisions array of `4783-STATUS.json` in META_DIR)
