# Preservation Checklist: Preserve Pending Work Before Branch Cleanup

**Purpose**: Track the preservation and removal checks for issue #4822. An unchecked item is open. This record verified each checked item by a read-only command.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Inventory

- [x] CHK001 The nine snapshot tags are listed with their commits (T001, TST-001).
- [x] CHK002 The four recovery branches are listed with their tips and bases (T002, TST-002).
- [x] CHK003 Each snapshot file is classified against main (T003, TST-003).
- [x] CHK004 The Labs snapshots share twenty-nine identical files (T004, TST-004).
- [ ] CHK005 The private Labs folders share twenty-nine identical files by SHA-256 (T005, TST-005). Open: the private store is outside this record.

## Verification

- [ ] CHK006 The nine private archives match their SHA-256 manifest (T006, TST-006). Open: the private store is outside this record.
- [ ] CHK007 The archive entry total matches the owner count (T006, TST-007). Open: the private store is outside this record.
- [ ] CHK008 The ignored output of each worktree appears in an archive (T007, TST-008). Open: the folders moved to the private store.
- [ ] CHK009 The bundle verifies and restores thirteen references (T008, TST-009 and TST-010). Open: the bundle is in the private store.

## Removal

- [ ] CHK010 The four removed branches each have a recovery tag, and their original names are recorded (T009, TST-012). Open: the original names are not public.
- [ ] CHK011 The two prunable admin directories are gone after the app sessions close (T010, TST-022). Open: Windows locks held the directories in the owner report.
- [ ] CHK012 The two merged branches are deleted with `git branch -d` only (T011, TST-011 and TST-013). Open: waits for CHK008 and CHK011.
- [x] CHK013 This record ran no removal command. The text names `git branch -D` only as a prohibited command.

## Publication

- [ ] CHK014 The secret review finds no credential or operational data (T012). Open: the review is not run.
- [x] CHK015 No recovery tag or recovery branch exists on GitHub (TST-014, RC-20 to RC-37).
- [ ] CHK016 The owner records the publication decision (T013). Open: this is a human decision.

## Report

- [ ] CHK017 The issue report names each of the seven blockers with its cause (T014, TST-017). Open: the report is not posted.
- [x] CHK018 The record holds no private path (TST-016). The scan covers the record files in this folder.
- [x] CHK019 The main commit is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` at the time of this record (TST-015, RC-01).
