# Requirements Checklist: Report a missing latest WAN rate

**Purpose**: Check the quality of `spec.md` before implementation starts.
**Created**: 2026-11-26
**Feature**: `spec.md` in the parent folder of this checklist.

## Content Quality

- [x] The spec states the operator impact of the defect in the Context section.
- [x] The spec names functions only as locations. The plan holds the design steps.
- [x] Each user story names an independent test.
- [x] All mandatory sections are complete and contain content.

## Requirement Completeness

- [x] Each functional requirement uses MUST and a testable condition.
- [x] Each success criterion names a count, a command, or a gate result.
- [x] Each edge case names the expected result.
- [x] Assumptions list the open risk for the interval start semantics (U-1).
- [x] Dependencies name pull request 4208 and its file ownership.
- [x] Out-of-scope items name the code that a later change replaces.

## Feature Readiness

- [x] Each functional requirement maps to at least one task and one test or check. The mapping is in `analysis.md`.
- [x] Each decision names the options, the chosen option, the reason, and the risk. The decisions are in `design/research.md`.
- [x] No decision requires a human decision. The decision list has no `HUMAN-DECISION-REQUIRED` marker.
- [ ] The implementation can start now. Not met: pull request 4208 owns the file (D-1). Task T001 must pass first.

## Traceability and Evidence

- [x] Each code claim cites a repository path and a line number.
- [x] Each remote check has one row in the remote verification table in `design/research.md`.
- [x] The remote check count matches in STATUS.json, `design/research.md`, and `summary.md`.
- [ ] The STE writing gate passes on the changed Markdown files. Not run in the drafting pass, because the brief forbids running linters. Tasks T004 and T005 run the gate.
- [ ] The Tests gate passes on the test module. Not run in the drafting pass, because the brief forbids running tests. Tasks T001 and T002 run the gate.

## Style

- [x] The record holds no placeholder text.
- [x] Prose avoids semicolons, contractions, Latin abbreviations, and phrasal verbs.
- [x] Each instruction in the tasks uses 20 words or fewer.
- [x] Each description in the spec uses 25 words or fewer.
