# Requirements Checklist: Multi-site stable word and router channel lab verification

**Purpose**: Check the quality of `spec.md` before the owner runs the lab checks.
**Created**: 2026-11-26
**Feature**: `spec.md` in this record

## Content quality

- [x] CHK001 Each user story has a priority from P1 to P3 (spec.md, User Scenarios).
- [x] CHK002 Each user story names an independent test that a reader can run.
- [x] CHK003 Each functional requirement FR-001 to FR-012 maps to a task and a TST item (analysis.md, Coverage Summary).
- [x] CHK004 Each success criterion gives a count or a yes-or-no result (SC-001 to SC-006).
- [x] CHK005 Edge cases EC-1 to EC-8 cover field errors, unnamed statuses, split results, queued jobs, reboots, wrong targets, posted secrets, and the cancel-path function.
- [x] CHK006 The out-of-scope list names each item that this issue does not change.
- [x] CHK007 The assumptions name the owner control, the pinned SDK, the local schema, and the device behavior.
- [x] CHK008 Each clarification records its answer and its source (spec.md, Clarifications).
- [x] CHK009 The spec names no implementation detail that the owner needs to run a lab check. The owner uses the contracts.

## Requirement quality

- [x] CHK010 Each requirement uses MUST for a rule that the system or the owner must follow.
- [x] CHK011 Each requirement names one measurable result or one observable behavior.
- [x] CHK012 Each requirement that names a file or a line cites a remote check row (research.md).
- [x] CHK013 No requirement depends on an unverified claim. The unverified items are listed in research.md.

## Style and writing

- [x] CHK014 The record uses no unfinished marker from rule 9 of the brief (self-review of each file in this record).
- [x] CHK015 The record uses no semicolon (self-review of each file in this record).
- [x] CHK016 The record uses no contraction (self-review of each file in this record).
- [x] CHK017 Each statement about a harm begins with Warning or Caution (spec.md, Edge Cases).
- [x] CHK018 Each folder in this record holds five children or fewer (plan.md, Project Structure).
- [x] CHK019 Each remote check count reads 120 in STATUS.json, in research.md, and in the summary.
