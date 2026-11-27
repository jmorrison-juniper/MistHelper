# Requirements Checklist: Menu 270 Live Resolve Acceptance Evidence

**Purpose**: Check the quality of `spec.md` before the plan and tasks use it.
**Created**: 2026-11-26
**Feature**: `spec.md`

Each item is checked, or it gives the reason that it is not checked.

- [x] CHK001 Each user story states a priority and an independent test.
- [x] CHK002 Each FR uses MUST or MUST NOT and names one checkable behavior.
- [x] CHK003 Each FR maps to a task and to a test or an owner step in the traceability table of `tasks.md`. FR-010 and FR-011 map to owner steps, because no automated test can prove a process rule.
- [x] CHK004 Each SC states a checkable result. SC-001 and SC-005 name the evidence source.
- [x] CHK005 The edge cases cover the outcomes `error`, `sent_unverified`, `not_sent`, and `skipped`.
- [x] CHK006 The assumptions name the owner approval and the open HTTP 403 cause.
- [x] CHK007 The out-of-scope section names the HTTP 403 cause, the resolve body, the cap, and the acknowledge live test.
- [x] CHK008 The clarifications record the conflict between the issue body and the 2026-10-21 comment, and they record its resolution.
- [x] CHK009 No open marker remains in the record. The only human markers are D-1 and D-5, and `research.md` explains each one.
- [x] CHK010 The Mist transport section names each SDK method and gives the SDK insufficiency evidence (rows 43 to 50 of `research.md`).
- [x] CHK011 The writing follows AGENTS.md. Self-review checked each sentence. The `ste-linter` gate runs in T-LOCAL-GATES, because the brief forbids running a linter during authoring.
- [x] CHK012 Each code claim cites a row of the remote verification table. The row count matches the `remote_checks` array in the status file and the summary (52 rows).
