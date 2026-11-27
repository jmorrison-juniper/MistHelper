# Requirements Checklist: Other-Device Event Export Fails Closed on Failed Pages

**Purpose**: Spec quality checks for `spec.md`, `plan.md`, and `tasks.md`.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Content Quality

- [x] CHK001 Each user story has a priority, an independent test, and acceptance scenarios.
- [x] CHK002 Each functional requirement uses MUST and states one action.
- [x] CHK003 Each requirement maps to a task and a test or named check (analysis.md, section 1).
- [x] CHK004 Each success criterion names a test, a count, or a gate.
- [x] CHK005 Each edge case names the requirement that governs it.
- [x] CHK006 The Mist Cloud transport section names each mistapi method and each contract.

## Remote Evidence

- [x] CHK007 STATUS `remote_checks` and the remote table in research.md each hold 80 rows.
- [x] CHK008 Each file claim cites a path and a line range, or a remote check row.
- [x] CHK009 Each claim about GitHub state cites a remote check row.
- [ ] CHK010 Live Mist API behavior for `total` is not verified. Explained: the brief and the issue forbid live calls (research.md, U-2).

## Style and Completeness

- [x] CHK011 No placeholder marker appears in any deliverable.
- [x] CHK012 No semicolon appears in any deliverable.
- [x] CHK013 No contraction appears in any deliverable.
- [x] CHK014 Each harm statement begins with `Warning:` or `Caution:`.
- [x] CHK015 Each decision in research.md names alternatives, a choice, a reason, and a risk.
- [x] CHK016 The human-decision count is zero, and each decision records that no human decision applies.
- [ ] CHK017 Local gates have not run. Explained: the brief forbids gate runs for this task. T-LOCAL-GATES runs them after implementation.
