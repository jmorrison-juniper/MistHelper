# Tasks: Refuse a Checked Device Type With No Target Version

**Input**: `spec.md` and `plan.md` in this folder.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, and `design/contracts/options-refusal.md`.

## Format

`[ID] [P?] Description`. The `[P]` marker means the task touches a different file and has no open dependency. Each task names its requirement IDs, its exact paths, its acceptance statement, one verification command, and its status. The status values are `open`, `verified-present`, `partial`, and `absent`. All tasks in this record start as `open`.

Evidence keys such as RC51 refer to the remote verification table in `design/research.md`.

## Phase 1: Tests First (Red)

- [ ] T001 Replace the xfail test with the legacy refusal test.
  - Requirements: FR-001, FR-002, FR-003, FR-004, FR-010, FR-012. SC-001.
  - Paths: `tests/contract/upgrade_portal/test_org_upgrade_routes.py` at lines 65-98 [RC51, RC52].
  - Acceptance: Remove the `xfail` marker at line 65. Rename the test to `test_checked_switch_without_target_version_creates_no_plan`. Post `selected_types` `["ap", "switch"]`, `version_ap` `0.15.1`, and an empty `version_switch`. Assert HTTP 400, code `org_upgrade_options_invalid`, and the text `Choose the switch target version, or clear Switches.`. Assert the store is empty and that no browser session write occurs. Use `caplog` to assert one warning that names `switch` and holds no device address.
  - Verification: `python -m pytest tests/contract/upgrade_portal/test_org_upgrade_routes.py -k checked_switch_without_target_version`. This test must fail before T008.
  - Status: open.

- [ ] T002 Add the explicit-target refusal test.
  - Requirements: FR-002, FR-003, FR-006. SC-002.
  - Paths: `tests/contract/upgrade_portal/test_org_upgrade_routes.py` after line 98.
  - Acceptance: Name the test `test_checked_switch_without_target_version_is_refused_on_explicit_targets`. Post `selected_types` `["ap", "switch"]`, `strategy` `big_bang`, and a `targets` list with one access point entry. Assert HTTP 400, the same code, the same text, and an empty store.
  - Verification: `python -m pytest tests/contract/upgrade_portal/test_org_upgrade_routes.py -k explicit_targets`. This test must fail before T008.
  - Status: open.

- [ ] T003 Add the mixed-type valid plan test.
  - Requirements: FR-001 (the case with no refusal). SC-003.
  - Paths: `tests/contract/upgrade_portal/test_org_upgrade_routes.py` after line 98.
  - Acceptance: Name the test `test_checked_ap_and_switch_targets_reach_the_saved_plan`. Post one access point target and one switch target. Assert HTTP 200 and `next` equal to `ORG_CONFIRM_PAGE` [RC101]. Assert the stored plan holds both device addresses. This guard test passes before and after T008.
  - Verification: `python -m pytest tests/contract/upgrade_portal/test_org_upgrade_routes.py -k reach_the_saved_plan`.
  - Status: open.

- [ ] T004 Add the per-device opt-out test.
  - Requirements: FR-008. SC-004.
  - Paths: `tests/contract/upgrade_portal/test_org_upgrade_routes.py` after line 98.
  - Acceptance: Name the test `test_checked_switch_with_one_targeted_device_keeps_the_opt_out`. The site view holds two switches. Post a target for one switch only. Assert HTTP 200 and a plan that holds only the targeted switch. This guard test passes before and after T008.
  - Verification: `python -m pytest tests/contract/upgrade_portal/test_org_upgrade_routes.py -k opt_out`.
  - Status: open.

- [ ] T005 Add the no-device type test.
  - Requirements: FR-007. SC-005.
  - Paths: `tests/contract/upgrade_portal/test_org_upgrade_routes.py` after line 98.
  - Acceptance: Name the test `test_checked_type_without_devices_at_the_sites_is_not_refused`. The site view holds access points only. Post `selected_types` `["ap", "switch"]` with one access point target. Assert HTTP 200. This guard test passes before and after T008.
  - Verification: `python -m pytest tests/contract/upgrade_portal/test_org_upgrade_routes.py -k without_devices`.
  - Status: open.

- [ ] T006 Add the narrowed retry view unit test.
  - Requirements: FR-009. SC-006.
  - Paths: `tests/contract/upgrade_portal/test_org_upgrade_routes.py` after line 98. The test calls `org_upgrade._selected_target_rows`, which starts at `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py:775` [RC21].
  - Acceptance: Name the test `test_narrowed_retry_view_refuses_a_checked_type_without_target`. The view holds one switch and no target. Use `pytest.raises(ValueError, match="Choose the switch target version")`. The narrowing happens before the call at `org_upgrade.py:759-760` [RC100].
  - Verification: `python -m pytest tests/contract/upgrade_portal/test_org_upgrade_routes.py -k narrowed_retry_view`. This test must fail before T008.
  - Status: open.

- [ ] T007 [P] Add the browser refusal test.
  - Requirements: FR-003, FR-004, FR-005. SC-007.
  - Paths: `tests/e2e/upgrade_portal/test_org_upgrade_flow.py`, inside class `TestOrganizationUpgradeBrowserFlow` (line 47), after the method at line 50 [RC98, RC55].
  - Acceptance: Name the test `test_checked_switch_without_target_keeps_each_entered_option`. Follow the setup steps of the sibling method. Check access points and switches. Choose a target for one access point. Leave the switch at "Do not upgrade this device". Save. Assert the flash message, the access point control value, and that no confirmation page loads. Check the seeded constants at lines 25-28 first (research unverified item U1).
  - Verification: `python -m pytest tests/e2e/upgrade_portal/test_org_upgrade_flow.py -k checked_switch_without_target`. This test must fail before T008. It needs Playwright and Chromium from the bootstrap.
  - Status: open.

## Phase 2: Implementation (Green)

- [ ] T008 Add the check and call it from the row selector.
  - Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-012, FR-014.
  - Paths: `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`. Insert the static method `require_family_versions` after `whole_number`, which ends at line 406 [RC18, RC19]. Change `_selected_target_rows` at lines 775-792 to call the method once and return one result [RC21-RC25].
  - Acceptance: The method follows the design in `plan.md`. Each changed line carries an inline comment. The info, debug, and warning lines follow FR-012. The method has at most three parameters and at most 25 lines. No other behavior changes.
  - Verification: `python -m pytest tests/contract/upgrade_portal/test_org_upgrade_routes.py`. All tests pass.
  - Status: open.

## Phase 3: Delivery Gates

- [ ] T009 [P] Add the changelog fragment.
  - Requirements: FR-011.
  - Paths: `changelog.d/issue-3394-multi-site-empty-version.md`, a new file [RC11, RC57, RC58].
  - Acceptance: One `###` heading. One `**Fixed**` bullet that names issue #3394 at its end.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`.
  - Status: open.

- [ ] T010 Check scope and module-level names.
  - Requirements: FR-013, FR-015.
  - Paths: the four changed paths in the change map of `plan.md`.
  - Acceptance: Only the four paths change. `symbol-diff` reports no module-level name changed for `org_upgrade.py`. For the test module, `symbol-diff` reports the one renamed test. The pull request states that rename.
  - Verification: `symbol-diff --base origin/main src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`.
  - Status: open.

- [ ] T011 Check docstrings, logs, and inline comments.
  - Requirements: FR-012, FR-014.
  - Paths: `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`.
  - Acceptance: The new method has a docstring. Each changed line has an inline comment. The log lines match FR-012. `radon cc` reports no block above complexity 10.
  - Verification: `interrogate $INTERROGATE_PATHS --fail-under 90`. Read `$INTERROGATE_PATHS` from `.github/workflows/ci.yml` [RC66].
  - Status: open.

- [ ] T-LOCAL-GATES Run every local gate that applies to the changed files.
  - Requirements: SC-001 to SC-007.
  - Paths: the four changed paths in the change map.
  - Acceptance: Each applicable row of the local gates table passes. The rows are Lint, Format, Types, Tests, Full tests, Coverage, Test quality, Complexity, Security lint, Code quality, Dead code, Docstrings, and Symbols. Read the path variables from `.github/workflows/ci.yml` [RC66]. Report each command and its result.
  - Verification: `python -m ruff check .` prints `All checks passed`.
  - Status: open.

- [ ] T-PR Commit, push, and open the pull request.
  - Requirements: FR-015, FR-011.
  - Paths: the four changed paths only. Stage no other file.
  - Acceptance: Create `fix/3394-multi-site-empty-version` from `main` in a worktree. The commit subject is `fix(upgrade-portal): refuse a multi-site save when a checked device type has no target version`. The commit body holds `Closes #3394`. The pull request body holds `Closes #3394` and the local gate results. Apply the labels `bug`, `web-portal`, and `needs-human-review`. Add `in-progress` while the work runs. Check the open pull requests for file overlap before the push.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`.
  - Status: open.

- [ ] T-REMOTE-CI Watch the remote checks.
  - Requirements: SC-007, FR-015.
  - Paths: the pull request from T-PR.
  - Acceptance: Every required check is green on the latest commit. The `Conventional Commits PR title` check is green. CodeQL is green. No local gate row covers remote checks, so the remote command is the verification.
  - Verification: `gh pr checks <number> --watch`.
  - Status: open.

- [ ] T-MERGE Merge after human review.
  - Requirements: FR-015.
  - Paths: the pull request from T-PR.
  - Acceptance: A human reviews the change and approves it. The orchestrator authorizes the merge. Then add the `auto-merge` label and let the squash merge run. Delete the branch and the worktree after the merge. No local gate row covers a merge.
  - Verification: `gh pr view <number> --json state,mergedAt,autoMergeRequest`.
  - Status: open.

## Requirement Coverage

| Requirement | Tasks | Test or check |
| - | - | - |
| FR-001 | T001, T003, T008 | pytest T001 and T003 |
| FR-002 | T001, T002, T008 | pytest T001 and T002 |
| FR-003 | T001, T002, T007, T008 | pytest T001 and T002, and browser T007 |
| FR-004 | T001, T007, T008 | pytest T001 (store and session), and browser T007 |
| FR-005 | T007, T008 | browser T007 |
| FR-006 | T001, T002, T008 | pytest T001 (type-wide fields) and T002 (explicit targets) |
| FR-007 | T005, T008 | pytest T005 |
| FR-008 | T004, T008 | pytest T004 |
| FR-009 | T006, T008 | pytest T006 |
| FR-010 | T001 | pytest T001 (xfail marker removed) |
| FR-011 | T009 | changelog guard test |
| FR-012 | T001, T008, T011 | pytest T001 (`caplog`), and review T011 |
| FR-013 | T010 | scripted check (symbol gate and file list) |
| FR-014 | T008, T011 | review T011 (no pytest case) |
| FR-015 | T-PR, T-REMOTE-CI, T-MERGE | remote checks and human review |

## Dependencies and Execution Order

- T001 to T006 change the same file. Run them in sequence.
- T007 and T009 change other files. They may run in parallel with the other tasks.
- T008 depends on T001 to T007, because the tests must fail first.
- T010 and T011 depend on T008.
- T-LOCAL-GATES depends on T008, T009, T010, and T011.
- T-PR depends on T-LOCAL-GATES.
- T-REMOTE-CI depends on T-PR.
- T-MERGE depends on T-REMOTE-CI and on the human approval.

## Notes

- Guard tests T003, T004, and T005 pass before and after T008. All other Phase 1 tests fail before T008.
- Every task names its exact paths and one verification command. The two remote tasks name remote commands, because the local gate table has no remote check.
