# Requirements Checklist: Upgrade Portal Session Recovery

**Purpose**: Check the quality of the specification and its links to the plan and the tasks.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

## Specification Quality

- [x] CHK001 Each user story has a priority, an independent test, and acceptance scenarios.
- [x] CHK002 Each functional requirement uses MUST and states one observable behavior.
- [x] CHK003 Each success criterion is measurable and names a test or a gate.
- [x] CHK004 Edge cases cover expiry, rotation, store failure, token change, and concurrent recovery.
- [x] CHK005 The out-of-scope list names each excluded item and the reason for its exclusion.
- [x] CHK006 The assumptions name each external dependency (Redis, cryptography, mistapi, and the worker count).
- [x] CHK007 Each clarification records its answer and the evidence ID (RC or LC).
- [x] CHK008 The spec contains no placeholder marker. The only approval marker is HUMAN-DECISION-REQUIRED in design/research.md.
- [x] CHK009 One term names each concept: registry, store, store record, owner key, cloud session, and credential mode.
- [x] CHK010 The spec states that implementation waits for decisions D-1 and D-2.
- [x] CHK011 The Mist transport section names each mistapi call with its local source path and line.
- [x] CHK012 Each functional requirement maps to at least one task and one planned test (tasks.md, Requirement Coverage).
- [x] CHK013 The spec uses American spelling and avoids semicolons and contractions.
