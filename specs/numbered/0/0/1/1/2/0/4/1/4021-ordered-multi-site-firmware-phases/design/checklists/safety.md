# Safety Checklist: Destructive Family Boundary

**Purpose**: Check the destructive firmware boundary of the change before implementation.
**Created**: 2026-11-26
**Feature**: `spec.md`, `plan.md`, and `design/contracts/stop-record.md`.

- [x] CHK001 A refused child stops its family and every later family (FR-007, test 4).
- [x] CHK002 An unknown outcome never resends the child (FR-008, FR-009, test 5).
- [x] CHK003 A failed or unknown family gate stops the run before the next family (FR-005, tests 6 and 7).
- [x] CHK004 The stop record persists before the background run ends (FR-010, test 10).
- [x] CHK005 The site locks renew during each wait. The release rule stays unchanged (FR-014, test 14).
- [x] CHK006 No client receives a firmware call (FR-012, test 9).
- [x] CHK007 A process loss writes a stop record and sends no child (FR-019, test 11).
- [x] CHK008 The operator confirmation of the route stays unchanged. The change alters only the background start.
- [x] CHK009 No stop sentence names a host, a token, or a cloud body (FR-017, test 12).
- [x] CHK010 No test in this change sends a live Mist request. Every test uses doubles (`design/quickstart.md`, section 3).
- [x] CHK011 The change adds no auto-merge label. A human reviews the pull request (`tasks.md`, T-MERGE).
- [x] CHK012 Menu 239 keeps its destructive category. The change does not edit the registry (`design/research.md`, row 54).
- [x] CHK013 The change adds no retry, no timeout, and no resume path (FR-009, FR-018, D-15).
