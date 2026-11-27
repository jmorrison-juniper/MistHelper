# Coordination Checklist: Rogue client exports use the client endpoint name

**Purpose**: Track each hold that limits the change, and show the state of each hold.
**Created**: 2026-11-26
**Feature**: `spec.md`, Clarifications and Assumptions

- [x] CHK-C01 The #2746 reservation covers the reserved test file only (issue comment 2, 2026-11-10T09:55:20Z).
- [x] CHK-C02 The preserved branch `preservation/2746-pr3011-turn0` stays untouched. The branch is absent from this checkout and from the remote (research U-A and R-51). The orchestrator confirms it before any test edit.
- [x] CHK-C03 The #2711 cache-hit no-write checks are part of this change (task T014, issue comment 1).
- [x] CHK-C04 The shared-writer files stay unchanged in Phase 1 (plan.md, Constitution Check).
- [x] CHK-C05 Open PR #4813 changes `data_exporter.py`. No Phase 1 path overlaps an open pull request (R-55).
- [ ] CHK-C06 Coordination with the owners of #4723, #4724, #4725, and #4726 is complete. Explained: the coordination is open. Phase 2 is on hold (`T-HOLD-COORD`).
- [ ] CHK-C07 The publication hold is released. Explained: the orchestrator releases the hold before `T-PR` (issue comment 3).
- [ ] CHK-C08 The managed-specification hold is released for the record route. Explained: the orchestrator releases the hold before the record is committed (issue comment 2).
- [ ] CHK-C09 The issue carries `in-progress`. Explained: task T001 adds the label before the branch is created.
- [ ] CHK-C10 The Phase 2 issue and the menu 24 issue exist. Explained: task T019 files them before `T-PR`.
- [ ] CHK-C11 The single serial merge slot is confirmed for this pull request. Explained: the slot is confirmed before `T-MERGE` (`.github/copilot-instructions.md`, section "Serial validation and merge queues").
