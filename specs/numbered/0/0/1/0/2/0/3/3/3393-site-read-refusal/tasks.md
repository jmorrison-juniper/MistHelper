# Tasks: Site read refusal

**Input**: [spec.md](spec.md), [plan.md](plan.md), and the supporting artifacts under `design/`.

Each task names its exact repository path and one verification command. Status values are `verified-present`, `open`, `partial`, or `absent`. A `verified-present` task names the delivered file in its evidence note.

## Phase 1: Verified repair on main

- [x] T001 [P] [FR-001, FR-002, FR-010] Confirm the save answers 503 for a transport fault at the site list read.
  - Files: `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` (lines 22, 230 to 231, 1227 to 1229).
  - Acceptance: The save answers 503 with the envelope of `design/contracts/refusal.md`. The envelope holds no transport text.
  - Verification: `python -m pytest tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py`
  - Evidence: RC-07, RC-08, RC-10, RC-37. (delivered: `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`)
  - Status: verified-present. The test run is outside this record (authoring brief, rule 2).

- [x] T002 [P] [FR-001, FR-005] Confirm the options page and the confirmation page answer 503.
  - Files: `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` (lines 1145 to 1149, 1348 to 1352).
  - Acceptance: Both GET routes answer 503 with the same envelope. A saved plan stays unchanged.
  - Verification: `python -m pytest tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py`
  - Evidence: RC-09, RC-11, contract lines 79 to 96. (delivered: `tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py`)
  - Status: verified-present.

- [x] T003 [FR-003, FR-005] Confirm a refused save writes no session key, nonce, or plan.
  - Files: `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` (lines 1232 to 1234 after the try block, line 1301 for the plan write).
  - Acceptance: The session writes follow the try block. The plan write follows the site read.
  - Verification: `python -m pytest tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py`
  - Evidence: RC-13, RC-14, contract lines 56 to 62 and 96. (delivered: `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`)
  - Status: verified-present.

- [x] T004 [P] [FR-004] Confirm the browser keeps each entered value after a refused save.
  - Files: `tests/e2e/upgrade_portal/test_org_upgrade_flow.py` (lines 50 to 76).
  - Acceptance: The form snapshot after the refusal equals the snapshot before the refusal.
  - Verification: `python -m pytest tests/e2e/upgrade_portal/test_org_upgrade_flow.py`
  - Evidence: RC-38. (delivered: `tests/e2e/upgrade_portal/test_org_upgrade_flow.py`)
  - Status: verified-present.

- [x] T005 [P] [FR-002] Confirm the release fragment names the change.
  - Files: `changelog.d/issue-3393-site-read-refusal.md`.
  - Acceptance: The fragment holds one heading and one Fixed bullet that names issue 3393.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
  - Evidence: RC-43, RC-44. (delivered: `changelog.d/issue-3393-site-read-refusal.md`)
  - Status: verified-present.

- [x] T006 [FR-006, FR-007, FR-008] Confirm the regression cases for the 404 refusal, the device family refusal, and the all-empty refusal still exist.
  - Files: `tests/contract/upgrade_portal/test_org_site_records_routes.py` (lines 246, 291, 300), `tests/contract/upgrade_portal/test_org_upgrade_routes.py`.
  - Acceptance: Each named case stays in its module and names its current refusal.
  - Verification: `python -m pytest tests/contract/upgrade_portal/test_org_site_records_routes.py tests/contract/upgrade_portal/test_org_upgrade_routes.py`
  - Evidence: RC-39, RC-40, RC-41. (delivered: `tests/contract/upgrade_portal/test_org_site_records_routes.py`)
  - Status: verified-present.

## Phase 2: Follow-up work

- [ ] T007 [P] [FR-009] Add an inline comment to each of the eleven lines that lack one.
  - Files: `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` (lines 230, 231, 1147, 1148, 1149, 1227, 1228, 1229, 1350, 1351, 1352).
  - Acceptance: Each line carries one comment that states its purpose. The change alters no code. The symbol gate reports no changed name.
  - Verification: `python -m ruff check .`
  - Evidence: analysis A-3. Principle VI of the constitution, RC-48.
  - Status: open. A human reviews the change before merge (D-2, D-8).

- [ ] T008 [P] [FR-011, FR-001] Prove the production answer for a transport fault below the SDK boundary.
  - Files: `tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py` (add one parametrized test with three cases: the save, the options page, and the confirmation page).
  - Acceptance: The test sets the requests session of the mistapi API session to raise `requests.exceptions.ConnectionError`. It asserts the observed status and code of each case. It asserts that no case answers 500, and that the save creates no plan. The contract file records the observed values. Analysis A-1 gives the predicted values.
  - Verification: `python -m pytest tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py`
  - Evidence: analysis A-1 and A-8, RC-69 to RC-72, RC-15, RC-17, RC-25, and RC-26.
  - Status: open. The observed values decide D-10 and the scope of the follow-up issue (D-11).

## Phase 3: Final tasks

- [ ] T-LOCAL-GATES [FR-007, FR-009, FR-011] Run each applicable gate of the gate map on the files of T007 and T008.
  - Files: `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`, `tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py`, and each changed Markdown file of the record.
  - Acceptance: Each applicable gate reports its expected result in plan.md. Each gate marked not applicable keeps its reason in the gate map. The run reports the number of files that each gate examined.
  - Verification: `python -m ruff check .`
  - Evidence: plan.md "Gate Map for T-LOCAL-GATES".
  - Status: open. Depends on T007 and T008.

- [ ] T-PR [FR-009, FR-011] Commit the T007 and T008 changes and open one pull request.
  - Files: the two files of T007 and T008 only. The record files stay out of this pull request.
  - Acceptance: The commit title uses Conventional Commits, for example `test(upgrade-portal): prove the cloud read refusal below the SDK`. The pull request body contains `Refs #3393` (D-9). The body names the local gates and the results. It states that T007 changes comments only. The pull request carries no auto-merge label.
  - Verification: `python -m pytest tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py`
  - Evidence: D-8, D-9. The pull request title uses the form of the Conventional Commits check.
  - Status: open. Depends on T-LOCAL-GATES. A human reviews it (D-2).

- [ ] T-REMOTE-CI [FR-011] Watch the remote checks of the T-PR pull request until each required check reports SUCCESS.
  - Files: `.github/workflows/ci.yml`, which defines the checks that the pull request reports. Each required check reports SUCCESS. No check reports FAILURE. The rollup of PR 4413 (RC-02) is the baseline.
  - Verification: `python -m pytest tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py` (the local twin of the upgrade contract shard)
  - Evidence: RC-02, and the PR 4413 check rollup in analysis.md.
  - Status: open. Depends on T-PR.

- [ ] T-MERGE [FR-011] Squash-merge the T-PR pull request after the human authorizes the merge and T-REMOTE-CI is green.
  - Files: `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`, the file that the symbol gate checks before the merge.
  - Acceptance: A human authorizes the merge in writing. The merge commit title uses Conventional Commits. The branch and the worktree are removed after the merge. No auto-merge label is added.
  - Verification: `symbol-diff --base origin/main src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`
  - Evidence: D-2, and Principle IV steps 9 and 10 of the constitution.
  - Status: open. Depends on T-REMOTE-CI and the human authorization.

Warning: a change to the save path can start a firmware write from a wrong plan. A human must review the diff before the merge.

## Dependencies

- T001 to T006 have no open dependency. Each one is verified-present.
- T007 and T008 can run in parallel. They edit different files.
- T-LOCAL-GATES depends on T007 and T008.
- T-PR depends on T-LOCAL-GATES.
- T-REMOTE-CI depends on T-PR.
- T-MERGE depends on T-REMOTE-CI and on the human authorization.
