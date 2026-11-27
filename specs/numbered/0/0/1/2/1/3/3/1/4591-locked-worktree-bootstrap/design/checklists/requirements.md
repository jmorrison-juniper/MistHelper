# Requirements Checklist: Locked Worktree Bootstrap

**Purpose**: Check the quality of `spec.md` before the change starts.
**Created**: 2026-11-26
**Feature**: `spec.md` in the parent folder

## Content Quality

- [x] CHK001 Each user story states who acts, what happens, and why it matters.
- [x] CHK002 Each user story has a priority and an independent test.
- [x] CHK003 The spec names no code change as a user benefit. Code locations appear only in `plan.md` and `design/research.md`.

## Requirement Quality

- [x] CHK004 Each FR has one ID, from FR-001 to FR-011.
- [x] CHK005 Each FR uses MUST and names one observable result.
- [x] CHK006 No FR depends on an unverified fact without a note. Extra-index behavior is listed as U-05 in `design/research.md`.
- [x] CHK007 Each FR maps to at least one task in `tasks.md`.

## Success Criteria

- [x] CHK008 Each SC names a measurable result or a command.
- [x] CHK009 Each SC has an owner task. SC-005 depends on task T006, which needs gate G-1.

## Scope and Assumptions

- [x] CHK010 The out-of-scope list names each excluded change, including the lock and dependency files.
- [x] CHK011 Each assumption has a source or the note "unverified". A-002 names its evidence and its limit.
- [x] CHK012 Gate G-1 names the data, the source, and the effect.

## Clarifications

- [x] CHK013 Each open question has an answer or a gate. Q1, Q2, and Q3 refer to gate G-1.

## Writing Style

- [x] CHK014 The text uses no placeholder marker. The only allowed marker is the decision marker, and this record uses none.
- [x] CHK015 The text uses no semicolon, no contraction, and no Latin abbreviation. The check ran with a text scan (see `analysis.md`, section 5).
- [x] CHK016 Each safety statement starts with `Warning:` or `Caution:`.
