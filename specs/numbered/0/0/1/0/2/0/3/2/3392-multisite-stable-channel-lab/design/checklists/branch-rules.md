# Branch Rules Checklist: Issue #3392

**Purpose**: Check each gated branch before its tasks change the repository.
**Created**: 2026-11-26
**Feature**: `plan.md`, Branch Rules and File-by-File Change Map

## Access point branch

- [ ] CHK001 The branch matches the posted verdict of L-AP-STABLE. An accepted verdict selects T011. A refused verdict selects T012.
- [ ] CHK002 The save refusal (org_advanced_options.py lines 143 to 163, org_upgrade.py line 1287) and the builder refusal (aggregate_upgrade_service.py lines 699 and 700) change together. Both change only for an accepted verdict.
- [ ] CHK003 The multi-site page offers the stable build for access points only in the accepted branch (org_options.html line 299).
- [ ] CHK004 The parity row C17 shows a gap for access points until the accepted verdict exists (T017).

## Router channel branches

- [ ] CHK005 A refused channel value leaves all three controls and the CLI prompt. Check upgrade_service.py line 78, org_options.html lines 541 to 551, options.html lines 797 to 807, and firmware_manager.py lines 2314 to 2326.
- [ ] CHK006 Each accepted channel value stays in every control. No control changes for that value.
- [ ] CHK007 A value with a split result (EC-3) follows the refused branch.
- [ ] CHK008 The warning text names only the values that remain.

## Tests, fixtures, and delivery

- [ ] CHK009 The tests in T016 match the posted verdicts. No test pins a refused value or a removed refusal.
- [ ] CHK010 The changelog fragment exists when a behavior changes (T018), and it names issue #3392.
- [ ] CHK011 Each changed file appears in the change map of plan.md. No branch changes a file outside the map.
- [ ] CHK012 The local gates pass for each changed file (T-LOCAL-GATES).
- [ ] CHK013 The pull request does not add the auto-merge label until the owner review ends (T-MERGE).
