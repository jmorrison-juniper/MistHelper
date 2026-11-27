# Tasks: Multi-site stable word and router channel lab verification

**Input**: The spec and plan in this record. Repository paths are exact paths on main. The lab steps run outside the repository.

**Status values**: open, verified-present, partial, or absent. Status describes the work named in the task at the audit time (2026-11-26).

**Verification**: Each task names one command from the Local gates table in `.github/copilot-instructions.md` (RC-05) or one guard test. A lab task names the regression run that follows its posted answer.

## Format

`[ID] [P?] Title`, then Requirements, Files, Acceptance, Verification, and Status. `[P]` marks a task that can run in parallel with other `[P]` tasks.

## Phase 1: Verification of this record

### T001 [P] Verify the record route

- Requirements: FR-011
- Files: `specs/numbered/0/0/1/0/2/0/3/2/3392-multisite-stable-channel-lab/`, `.specify/scripts/powershell/spec-route.ps1`
- Acceptance: The digits for 3392 are 0, 0, 1, 0, 2, 0, 3, 2, and the folder is absent before this record.
- Verification: `python -m pytest tests/guardrails/test_spec_route_contract.py`
- Status: verified-present (RC-13 to RC-15, RC-112)

### T002 [P] Verify the remote citations

- Requirements: FR-010
- Files: `design/research.md` (remote table)
- Acceptance: The table holds 120 rows. Each present row matches its blob SHA and line on main.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 design/research.md`, then the audit in `design/quickstart.md`
- Status: verified-present (RC-01 to RC-120)

### T003 [P] Verify the SDK functions and the pin

- Requirements: FR-010
- Files: `requirements.txt`, `.venv\Lib\site-packages\mistapi\api\v1\orgs\devices.py`, `.venv\Lib\site-packages\mistapi\api\v1\orgs\ssr.py`, `.venv\Lib\site-packages\mistapi\api\v1\sites\devices.py`
- Acceptance: Each SDK function named in the contracts exists at its stated line. The installed package is 0.64.1.
- Verification: `python -m pytest tests/integration/test_mistapi_sdk_compatibility.py`
- Status: verified-present (RC-25, RC-113 to RC-120)

### T004 [P] Verify the lab bodies and the job reads against the schema

- Requirements: FR-002, FR-004
- Files: `design/contracts/org-access-point-stable-request.md`, `design/contracts/ssr-channel-request.md`, `design/contracts/lab-answer-record.md`
- Acceptance: Each body field and each job read path appears in the OpenAPI lines of the contracts (RC-61, RC-63, RC-65, RC-68 to RC-78).
- Verification: `python -m pytest tests/contract/upgrade_portal/test_org_advanced_options.py`
- Status: verified-present

## Phase 2: Owner-only lab steps

Each step below runs only on the owner side. The agent sends no request and reads no credential (FR-002).

### T005 Owner selects the lab targets and the credential source

- Requirements: FR-002, FR-003
- Files: `design/checklists/lab-evidence.md` (owner items CHK001 and CHK002). The target list stays outside the repository.
- Acceptance: The owner records one lab organization, one lab site, one lab access point, and the lab routers in the owner session only. Decision D-18 applies.
- Verification: `python -m pytest tests/contract/upgrade_portal/test_org_advanced_options.py` after the owner posts the answers.
- Status: absent

### T006 Owner runs lab check L-AP-STABLE

- Requirements: FR-001, FR-002, FR-004
- Files: `design/contracts/org-access-point-stable-request.md`, `design/contracts/lab-answer-record.md`.
- Acceptance: The owner sends one minimal access point body with the stable word through `upgradeOrgDevices`. The owner reads the job with `getOrgDeviceUpgrade` and drafts one lab answer.
- Verification: `python -m pytest tests/contract/upgrade_portal/test_org_advanced_options.py`
- Status: absent
- Notes: Caution: the access point can reboot during the job. Warning: the call must target a lab device only.

### T007 Owner runs lab check L-SSR-STABLE

- Requirements: FR-002, FR-003, FR-004, FR-007
- Files: `design/contracts/ssr-channel-request.md`, `design/contracts/lab-answer-record.md`.
- Acceptance: The owner sends one router body with channel `stable` through `upgradeOrgSsrs`. The owner reads the job with `listOrgSsrUpgrades` and drafts one lab answer.
- Verification: `python -m pytest tests/unit/upgrade_portal/test_upgrade_ssr_options.py`
- Status: absent
- Notes: Caution: the router can reboot during the job.

### T008 Owner runs lab check L-SSR-BETA

- Requirements: FR-002, FR-003, FR-004, FR-007
- Files: `design/contracts/ssr-channel-request.md`, `design/contracts/lab-answer-record.md`.
- Acceptance: The owner sends one router body with channel `beta` and reads the job as in T007. The owner drafts one lab answer.
- Verification: `python -m pytest tests/unit/upgrade_portal/test_upgrade_ssr_options.py`
- Status: absent

### T009 Owner runs lab check L-SSR-ALPHA

- Requirements: FR-002, FR-003, FR-004, FR-007
- Files: `design/contracts/ssr-channel-request.md`, `design/contracts/lab-answer-record.md`.
- Acceptance: The owner sends one router body with channel `alpha` and reads the job as in T007. The owner drafts one lab answer.
- Verification: `python -m pytest tests/unit/upgrade_portal/test_upgrade_ssr_options.py`
- Status: absent

### T010 Owner posts the four lab answers

- Requirements: FR-004
- Files: `design/contracts/lab-answer-record.md`, `design/checklists/lab-evidence.md`. The owner posts the comments on issue #3392.
- Acceptance: Issue #3392 holds four lab answers, one comment for each check. Each answer uses the fixed fields of the lab answer record and holds no identifier, token, or response body.
- Verification: `python -m pytest tests/contract/upgrade_portal/test_org_advanced_options.py` after the posts, and the audit TST-13 in `design/quickstart.md`.
- Status: absent

## Phase 3: Gated branches and parity fixture

A gated task runs only when its named answer exists. Each branch uses the change map in `plan.md`.

### T011 [gated: T006 accepted] Remove the access point refusals and offer the stable build

- Requirements: FR-001, FR-005
- Files: `src/operations/execution/firmware/aggregate_upgrade_service.py` (delete lines 699 and 700), `src/interfaces/portals/upgrade_portal/upgrade/org_advanced_options.py` (delete lines 143 to 163), `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` (delete line 1287), `src/interfaces/portals/upgrade_portal/upgrade/options.py` (lines 317 to 322), `src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_options.html` (line 299)
- Acceptance: The stable word reaches each access point body in a plan. The multi-site page offers the stable build for access points. No refusal remains for the stable word.
- Verification: `python -m pytest tests/contract/upgrade_portal/test_org_advanced_options.py`
- Status: absent

### T012 [gated: T006 refused] Keep both refusals and record the refused answer

- Requirements: FR-006
- Files: `design/research.md`, `analysis.md` (in this record)
- Acceptance: The research file names the refused answer. Each refusal line stays active (RC-30, RC-31, RC-41 to RC-43).
- Verification: `python -m pytest tests/contract/upgrade_portal/test_org_advanced_options.py`
- Status: absent

### T013 [gated: T007 refused] Remove the stable value from the router channel controls

- Requirements: FR-007
- Files: `src/operations/execution/firmware/upgrade_service.py` (line 78), `src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_options.html` (lines 541 to 551), `src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/options.html` (lines 797 to 807), `src/operations/execution/firmware/firmware_manager.py` (lines 2314 to 2326)
- Acceptance: No page and no CLI prompt offers the stable value for a router.
- Verification: `python -m pytest tests/unit/upgrade_portal/test_upgrade_ssr_options.py`
- Status: absent

### T014 [gated: T008 refused] Remove the beta value from the router channel controls

- Requirements: FR-007
- Files: the files of T013
- Acceptance: No page and no CLI prompt offers the beta value for a router.
- Verification: `python -m pytest tests/unit/upgrade_portal/test_upgrade_ssr_options.py`
- Status: absent

### T015 [gated: T009 refused] Remove the alpha value from the router channel controls

- Requirements: FR-007
- Files: the files of T013
- Acceptance: No page and no CLI prompt offers the alpha value for a router. The warning text names only the values that remain.
- Verification: `python -m pytest tests/unit/upgrade_portal/test_upgrade_ssr_options.py`
- Status: absent

### T016 Update the tests for the branch outcome

- Requirements: FR-005, FR-007, FR-008
- Files:
  - `tests/contract/upgrade_portal/test_org_advanced_options.py` (lines 118 to 136 and 381 to 392, plus one new test for the accepted access point stable word)
  - `tests/unit/prod_readiness/operations/execution/firmware/upgraders/upgrades/test_org_advanced_bodies.py` (lines 96 and 158 to 161)
  - `tests/e2e/upgrade_portal/test_org_advanced_options.py` (lines 231 to 241)
  - `tests/unit/upgrade_portal/test_upgrade_ssr_options.py` (lines 158 to 195 and 349 to 350)
  - `tests/contract/upgrade_portal/test_upgrade_options.py` (line 1358)
- Acceptance: Each test matches the posted answers. No test pins a refused value or a removed refusal. A router body still carries the chosen channel only (RC-86, RC-87).
- Verification: `python -m pytest tests/contract/upgrade_portal/test_org_advanced_options.py`
- Status: absent

### T017 [P] Correct the parity rows C17 and C21

- Requirements: FR-009
- Files: `tests/e2e/upgrade_portal/journeys/parity_matrix.json` (rows C17 at lines 736 to 775 and C21 at lines 904 to 941)
- Acceptance: Row C17 shows a gap for the access point family until L-AP-STABLE has an accepted verdict. Row C21 cites the multi-site control at `org_options.html` line 535 (RC-45).
- Verification: `python -m pytest tests/e2e/upgrade_portal/journeys/test_parity_pages.py`
- Status: absent
- Notes: This task does not wait for the lab answers. Its evidence is the current refusal (RC-42) and the current control (RC-45).

### T018 [gated: any change of behavior] Add the changelog fragment

- Requirements: FR-012
- Files: `changelog.d/issue-3392-multisite-stable-channel-lab.md` before the pull request exists, then a file named `pr-` followed by the pull request number in `changelog.d` (RC-09, RC-110)
- Acceptance: The fragment holds one heading and one bullet that names issue #3392. The fragment name follows the rule.
- Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- Status: absent

### T019 Close the record with the posted answers

- Requirements: FR-004, FR-006, FR-010
- Files: `design/research.md`, `analysis.md`, `tasks.md` (in this record)
- Acceptance: The record holds each posted answer in fixed fields, the branch that the answers select, and the final status of each task. The remote check count stays 120 in all three places.
- Verification: `python -m pytest tests/guardrails/test_process_folder_structure.py`
- Status: absent

## Phase 4: Delivery

### T-LOCAL-GATES Run each applicable local gate

- Requirements: FR-012
- Files: each changed file named in the change map of `plan.md`
- Acceptance: Each applicable row of the Local gates table prints its expected result. The STE row covers each changed Markdown file and the fixed list (decision D-12).
- Verification: `python -m py_compile MistHelper.py`
- Status: absent
- Notes: The commands for each row are in `design/quickstart.md`. Run the complexity, security, and symbols rows for each changed package.

### T-PR Commit and open the pull request

- Requirements: FR-012
- Files: the changed files named in the change map, staged by explicit path
- Acceptance: The pull request title follows Conventional Commits. The branch starts with `fix/`, `feat/`, or `chore/`, then `3392-multisite-stable-channel-lab`. The body holds `Closes #3392` and the gate results.
- Verification: `python -m py_compile MistHelper.py`
- Status: absent

### T-REMOTE-CI Watch the CI run

- Requirements: FR-012
- Files: `.github/workflows/ci.yml` (the checks that report on the pull request)
- Acceptance: Each required check passes on the latest commit of the branch.
- Verification: `python -m pytest tests/guardrails`
- Status: absent

### T-MERGE Merge after review and authorization

- Requirements: FR-012
- Files: `.github/PULL_REQUEST_TEMPLATE.md` (the pull request body that the owner reviews)
- Acceptance: The orchestrator authorizes the merge after remote CI passes. The owner completes the review that the needs-human-review label requires. The merge is one squash commit on main.
- Verification: `python -m pytest tests/guardrails`
- Status: absent
- Notes: The auto-merge label waits until the owner review ends. Warning: a firmware upgrade can change production devices. The constitution requires typed confirmation for firmware upgrades (RC-11).

## Dependencies and Execution Order

- T001, T002, T003, and T004 run in parallel. They are complete for this record.
- T005 runs before T006, T007, T008, and T009.
- T006 selects T011 or T012. T007, T008, and T009 select T013, T014, and T015.
- T011 to T015 run before T016. T016 runs before T018. T018 runs before T019.
- T017 runs in parallel with T005 to T010, because it touches a different file.
- T-LOCAL-GATES runs after T016 and T018. T-PR runs after T-LOCAL-GATES. T-REMOTE-CI runs after T-PR. T-MERGE runs after T-REMOTE-CI and the owner review.

## Parallel Example

```text
T001 and T002 and T003 and T004 (verification of this record)
T017 (parity fixture) with T005 to T010 (owner steps)
```

## Implementation Strategy

1. Complete Phase 1. Its tasks are verified.
2. Post the four lab answers (T005 to T010).
3. Run one branch for each answer: T011 or T012 for the access point, and T013, T014, or T015 for each channel value.
4. Update the tests (T016), the parity fixture (T017), and the changelog (T018). Close the record (T019).
5. Run the delivery tasks in order.

## Guard Rules

- Remove no refusal before an accepted L-AP-STABLE answer. Warning: an early removal sends the stable word to a production device.
- Remove no channel value before its refused answer.
- Read each line again before an edit. The line numbers in this record come from main on 2026-11-26.
- Add files by explicit path. Do not use a wildcard for staging.
- Do not force-push. Warning: a force push can remove commits that a reviewer added.
