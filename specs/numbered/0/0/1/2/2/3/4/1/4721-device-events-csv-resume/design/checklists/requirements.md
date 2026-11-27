# Specification Quality Checklist: Resumed 52-week device-event CSV export

**Purpose**: Check that `spec.md`, `plan.md`, and `tasks.md` meet the quality rules before implementation.
**Created**: 2026-11-26
**Feature**: `..\spec.md`

## Content Quality

- [x] The spec names the user, the menu, and the outcome. Menu 97 and the operator are named in `spec.md`.
- [x] The spec uses plain words and short sentences for each requirement.
- [x] The spec names no implementation details beyond the exact paths and methods that the plan needs.
- [x] Every mandatory section has content. No section holds a placeholder.

## Requirement Completeness

- [x] Each requirement has an ID in the form `FR-###`. FR-001 to FR-015 are present.
- [x] Each success criterion has a measurable check. SC-001 to SC-005 name a test, a count, or a gate.
- [x] Edge cases cover refusal, empty input, failed writes, and SQLite. Each out-of-scope edge case names its tracking issue or follow-up.
- [x] Assumptions name the one unverified fact. Item U-1 covers the live form of `next`.
- [x] Out of scope names each excluded issue (#1794, #4722, #4723, #4724) and each follow-up.
- [x] Dependencies on other PRs and issues are named. PR #4813 is named in `plan.md` and `analysis.md`.

## Feature Readiness

- [x] Each requirement maps to at least one task and one test or check (`analysis.md` Coverage Summary).
- [x] Each user story has an independent test and acceptance scenarios.
- [x] The plan names the exact files and lines that change. No new module, directory, or test file is needed.
- [x] The constitution check has a result for each rule. Pre-existing debt is recorded in `plan.md` Complexity Tracking.
- [x] Each task names one verification command from the local gates table, except the four delivery steps. Those steps name the CI check.

## Traceability

- [x] Each remote claim has a row in `design\research.md` and in `4721-STATUS.json`. The count is 65 in both places.
- [x] Each decision names alternatives, the chosen option, the reason, and the risk (`design\research.md` Decisions).
- [x] Each unverified claim appears in the Unverified list with a reason (U-1 to U-6).

## Notes

- Items are checked against the record on 2026-11-26. No gate has run. The implementer must run the gates in `plan.md` Local gate plan.
- The live form of `next` (U-1) remains open. Its owner must confirm it before merge.
