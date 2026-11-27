# Verification Checklist: WLAN fixture host teardown

**Purpose**: List each proof that the implementation phase must produce before the merge.

**Feature**: `spec.md`, `plan.md`, and `design\quickstart.md`

## Reproduction

- [ ] The three-node sequence reports no failed tests after the fix (quickstart Scenario 2).
- [ ] The mutation proof reports two failed tests without the restore line (quickstart Scenario 4).
- [ ] The fixture block matches plan.md, with 3 matches and 0 removed-call matches (quickstart Scenario 3).

## Gates

- [ ] Ruff reports `All checks passed` (quickstart Scenario 5).
- [ ] Black reports `No file needs a change` (quickstart Scenario 5).
- [ ] The test-quality preflight passes (quickstart Scenario 6).
- [ ] The test-quality gate reports `gate: 0 new findings vs baseline` for the changed-from run and the full run (quickstart Scenario 6).
- [ ] `symbol-diff` reports `no module-level name changed` (quickstart Scenario 5).
- [ ] Both pytest-chunks shards report no failed tests (quickstart Scenario 7).
- [ ] The diff contains only the three intended paths (quickstart Scenario 8).

## Remote

- [ ] The pull request body contains `Closes #4492` (quickstart Scenario 9).
- [ ] Each required check on the pull request reports success (quickstart Scenario 9).
- [ ] The main root-units shard reports success after the merge (quickstart Scenario 9).

**Notes**: Every item is open. The authoring phase ran no gate (brief rule 2). The implementation phase checks each item and records its result in the pull request body.
