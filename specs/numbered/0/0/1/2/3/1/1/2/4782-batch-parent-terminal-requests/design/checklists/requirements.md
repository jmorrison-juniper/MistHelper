# Specification Quality Checklist: Batch Parent Terminal Requests

**Purpose**: Check the quality of `spec.md`, `plan.md`, and `tasks.md` before implementation starts.
**Created**: 2026-11-26
**Feature**: `spec.md` in this record

## Content Quality

- [x] CHK001 The user problem appears in plain words. Evidence: `spec.md` Input and User Story 1.
- [x] CHK002 The spec names both routes exactly. Evidence: `design/contracts/session-terminal-routes.md` Routes table (R-30, R-31).
- [x] CHK003 Code references appear only where a reviewer must find code. Evidence: `plan.md` Architecture. Each line number is verified (R-17 to R-64).

## Requirement Completeness

- [x] CHK004 Each requirement has an ID and a testable statement. Evidence: `spec.md` FR-001 to FR-007.
- [x] CHK005 Each requirement maps to a task and a test or verification. Evidence: `analysis.md` Traceability.
- [x] CHK006 Each success criterion names a measure, a time window, or a command. Evidence: `spec.md` SC-001 to SC-005.
- [x] CHK007 Each edge case states whether a test covers it. Evidence: `spec.md` Edge Cases.
- [x] CHK008 Assumptions and preconditions appear in separate sections. Evidence: `spec.md` Assumptions and Preconditions.
- [x] CHK009 Out-of-scope items are listed. Evidence: `spec.md` Out of Scope.
- [x] CHK010 Each code, test, configuration, and document claim has a remote row or an Unverified entry. Evidence: `design/research.md` remote table and U-1 to U-7.

## Feature Readiness

- [x] CHK011 The ownership hold is a precondition with its own task, not a human decision. Evidence: `tasks.md` T001 and `analysis.md` Unresolved items.
- [x] CHK012 The only human decision uses the marker HUMAN-DECISION-REQUIRED. Evidence: `design/research.md` D-8.
- [x] CHK013 Each new folder level holds five children or fewer. Evidence: `plan.md` Constitution Check row I and remote row R-67.
- [x] CHK014 The record uses no forbidden token, semicolon, contraction, or phrasal verb. Evidence: the self-review scan that ran after the last edit.
- [x] CHK015 The counts agree across STATUS, research, and summary. Evidence: 68 remote rows in `design/research.md`, 68 `remote_checks` entries in STATUS, and 68 in `summary.md`.

## Notes

- Every item is checked. Each item cites the file or the evidence that supports it.
- The ownership hold stays open until task T001 records the owner release.
