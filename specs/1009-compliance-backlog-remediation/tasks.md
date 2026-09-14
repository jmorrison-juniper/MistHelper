# Tasks: Compliance Backlog Remediation

**Updated**: 2026-09-14
**Measured source**: `rtk python tools/check_compliance.py src/ -r -q`
**Overall baseline**: 94.5 A

## Reconciled task set

- [x] T001 Record the current `src/` measurement. Evidence: the analyzer reported 94.5 A overall.
- [x] T002 Replace the stale issue #1000 backlog with the ranked table in `spec.md` and `plan.md`.
- [x] T003 Mark issue #1003 superseded by the 1009 backlog. Evidence: `src\maps\maps_manager.py` scored 100.0 A+.
- [x] T004 Repair `src\utils\zscaler_catalogue.py` CONV-COMMENTS. Evidence: the file improved from 60.0 D- to 66.0 D.
- [x] T005 Prove the source repair preserved the module symbol table. Evidence: `symbol_diff: no module-level name changed`.
- [x] T006 Run the targeted behavior tests before the source change. Evidence: 323 passed.
- [x] T007 Run the targeted behavior tests after the source change. Evidence: 323 passed.
- [ ] T008 Refactor `src\org\org_synthetic_probes_manager.py` STRUCT-LENGTH and STRUCT-COMPLEXITY. follow-up issue #2645 owns this work.
- [ ] T009 Refactor `src\device\ap_profile_migration_manager.py` STRUCT-LENGTH, STRUCT-PARAMS, and STRUCT-COMPLEXITY. follow-up issue #2645 owns this work.
- [ ] T010 Refactor `src\utils\zscaler_catalogue.py` STRUCT-LENGTH and STRUCT-COMPLEXITY. follow-up issue #2645 owns this work.
- [ ] T011 Refactor `src\utils\zscaler_probe.py` STRUCT-LENGTH and STRUCT-COMPLEXITY. follow-up issue #2645 owns this work.
- [ ] T012 Record `MistHelper.py` debt without editing the file. follow-up issue #2645 owns this work after the hot-file lock ends.

## Reconciliation count

The former 1009 list had 115 stale items. This file replaces them with 12 measured tasks. Seven tasks are complete in this pull request. Five tasks move to the follow-up issue #2645.
