# Rollout Readiness Checklist: Stranded branch pull request coverage

**Purpose**: Show which rollout inputs are ready and which wait for an event.
**Created**: 2026-11-26
**Feature**: `tasks.md` in this record folder

## Inputs

- [x] RDY001 The scope count is recorded: 537 stranded branches on 2026-11-26 (research.md R2, RC-049).
- [x] RDY002 The repository visibility is recorded: public (RC-050).
- [x] RDY003 The duplicate trackers are recorded: issues 4302, 4583, 4719, and 4911 (RC-052).
- [x] RDY004 The rate limits are recorded: 80 content-generating requests per minute and 500 per hour (S-2).
- [x] RDY005 The pilot list is built from the replica: five oldest stranded heads (plan.md, Pilot Scope).
- [x] RDY006 The contract fields are defined in `design\contracts\preservation-pull-request.md`.
- [x] RDY007 The stop rule is defined in FR-006 and FR-008 (spec.md).

## Waiting Inputs

- [ ] RDY008 The pilot quality-gate count is recorded. Explained: the pilot runs after `T-MERGE` (T006, T007).
- [ ] RDY009 The owner approves the rollout volume. Explained: the owner decides after the pilot (T010, D-12).
- [ ] RDY010 The batch manifest is built. Explained: the manifest waits for the approval (T011).
- [ ] RDY011 The owner names the two private-corpus branches. Explained: the owner input is pending (A-9, U-3, T023).

## Notes

- Each waiting input has one task. The rollout starts only after RDY008 and RDY009 hold.
