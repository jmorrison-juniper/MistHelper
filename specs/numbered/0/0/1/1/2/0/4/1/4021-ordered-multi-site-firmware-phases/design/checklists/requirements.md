# Requirements Quality Checklist: Ordered Multi-Site Firmware Families

**Purpose**: Check the quality of `spec.md` before planning starts.
**Created**: 2026-11-26
**Feature**: `spec.md` in this record.

- [x] CHK001 Each functional requirement has a unique identifier from FR-001 to FR-020 in order.
- [x] CHK002 Each functional requirement uses MUST for a required behavior.
- [x] CHK003 Each user story has a priority and an independent test.
- [x] CHK004 Each success criterion names a measurable outcome in a mocked run.
- [x] CHK005 The edge cases cover refusal, unknown outcome, gate timeout, lock loss, cancellation, and process loss.
- [x] CHK006 The out of scope list excludes durable resume, which belongs to issue #4022.
- [x] CHK007 The assumptions name the owner decisions 1, 2, and 3 on issue #4020.
- [x] CHK008 Each clarification states the answer and its source.
- [x] CHK009 The spec holds no unfinished marker. The only template token appears in `design/contracts/stop-record.md`, where the text explains it.
- [x] CHK010 The spec holds no semicolon and no contraction.
- [x] CHK011 Each requirement maps to at least one task and one test (`design/analysis.md`, section 1).
- [x] CHK012 The Mist transport section names each mistapi function that the change reuses.
- [x] CHK013 The key entities name the parent record, the child, the family gate result, and the stop record.
- [x] CHK014 Each safety statement starts with the signal word Warning or Caution.
- [x] CHK015 No requirement needs a human decision under section 6 of the brief. The explanation appears in `design/research.md`, section 5.
