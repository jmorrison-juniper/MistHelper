# Tasks: Organization Upgrade Mode for Many Sites

**Feature**: Organization upgrade mode for many sites
**Source of truth**: `spec.md`, `plan.md`, `research.md`, `data-model.md`,
`contracts/api-contract.md`, and `contracts/ui-contract.md`
**Application**: `src/upgrade_portal` (Flask, Jinja, plain JavaScript)

## Baseline

The route lane already exists. `src/upgrade_portal/app/routes/org_upgrade.py`
serves seven paths, and `factory.py` registers the blueprint `org_upgrade`.

Two offline suites already pass with 180 tests. They are
`tests/contract/upgrade_portal/test_org_upgrade_routes.py` and
`tests/unit/upgrade_portal/test_org_upgrade_service.py`.

These tasks close the remaining gaps. They keep every passing test green.

## Format

`[ID] [P?] [Story] Description`

`[P]` marks a task that runs beside another `[P]` task. Two parallel tasks touch
no common file.

`[Story]` names the user story of `spec.md`.

## Path Conventions

| Area | Root |
| - | - |
| Routes | `src/upgrade_portal/app/routes/` |
| Templates | `src/upgrade_portal/app/assets/templates/` |
| Browser code | `src/upgrade_portal/app/assets/static/js/portal.js` |
| Wiring | `src/upgrade_portal/app/wiring.py` |
| Run model | `src/upgrade_portal/runtime/runs.py` |
| Cloud service | `src/firmware/org_upgrade_service.py` |
| Body rules | `src/firmware/org_upgrade_body.py` |
| Tests | `tests/unit/`, `tests/contract/`, `tests/e2e/` |

## Phase 1: Confirm the Baseline

### T001 [P] Record the passing suites

Run the two present suites. Record the count and the duration.

- **Command**:
  `python -m pytest tests\contract\upgrade_portal\test_org_upgrade_routes.py tests\unit\upgrade_portal\test_org_upgrade_service.py -q`
- **Done when**: The report shows 180 passing tests in under 30 seconds.

### T002 [P] Confirm the offline guard

Prove that the socket block stops a live call.

- **Files**: `tests/conftest.py`
- **Done when**: A test that opens a socket fails with a clear message.

### T003 [P] Record the cloud answer shape

Read one organization job with a laboratory token. Save the answer as a fixture.

- **Files**: `tests/fixtures/org_upgrade_answer.json`
- **Done when**: The fixture holds `id`, `status`, and a nested `targets` object
  inside each entry of `upgrades`.

## Phase 2: Defects in the Present Lane

### T004 [Done] Fix the site count defect

- **Files**: `src/upgrade_portal/app/routes/org_upgrade.py`
- **Depends on**: T003
- **Work**: Read the counts from each site entry. Sum the totals.
- **Done when**: The answer shows a true total, a true upgraded count, and a
  true failed count.

### T005 Add the counts to each site entry

Add `site_name`, `total`, `upgraded`, and `failed` to each entry of
`site_upgrades`.

- **Files**: `src/upgrade_portal/app/routes/org_upgrade.py`
- **Depends on**: T004
- **Done when**: The progress page shows a count for each site.

### T006 [Done] Use a write session with no retry

Each portal sign-in sets zero SDK retries. The default transport adapter permits
zero retries.

- **Files**: `src/upgrade_portal/app/routes/auth.py`,
  `src/upgrade_portal/app/routes/org_upgrade.py`
- **Work**: Check both retry layers before a write.
- **Done when**: `OrgUpgradeService._check_write_session` passes for a live
  submission.

### T007 [P] Test the write session rule

Prove that a session with retries fails the write check.

- **Files**: `tests/contract/upgrade_portal/test_org_upgrade_routes.py`
- **Depends on**: T006
- **Done when**: The route answers a refusal and calls no SDK operation.

## Phase 3: User Story 5 - The Browser Confirmation Gate (Priority: P1)

### T008 [Done] [US5] Add the gate attributes

Add `data-confirm-word`, `data-confirm-target`, and `data-confirm-hint-for` to
the confirmation input. Add a hint element.

- **Files**: `src/upgrade_portal/app/assets/templates/upgrade/org_confirm.html`
- **Done when**: `applyConfirmGate` drives the button with no new JavaScript.

### T009 [Done] [US5] Disable the start button in the markup

Set the `disabled` attribute on the start button.

- **Files**: `src/upgrade_portal/app/assets/templates/upgrade/org_confirm.html`
- **Depends on**: T008
- **Done when**: The button stays disabled until the operator types `CONFIRM`.

### T010 [Done] [US5] Move the word into one Jinja variable

Hold the word in one variable, as `upgrade/confirm.html` does at line 74.

- **Files**: `src/upgrade_portal/app/assets/templates/upgrade/org_confirm.html`
- **Depends on**: T008
- **Done when**: One line changes the word on the page and in the attribute.

### T011 [P] [US5] Test the browser gate

- **Files**: `tests/e2e/upgrade_portal/test_org_upgrade_flow.py`
- **Done when**: A lower-case word keeps the button disabled.

## Phase 4: User Story 9 - Locks for Many Sites (Priority: P1)

### T012 [US9] Take one lock for each selected site

Request one lock in `select.choose_sites`. Store each grant under
`site_lock_records`.

- **Files**: `src/upgrade_portal/app/routes/select.py`
- **Done when**: Two sites give two grants in the session.

### T013 [US9] Release every lock when one acquire fails

Release each held grant when one request fails.

- **Files**: `src/upgrade_portal/app/routes/select.py`
- **Depends on**: T012
- **Done when**: A partial lock set leaves no held grant.

### T014 [US9] Add the lock guard to the write path

Read every lock again in `submit_upgrade`. Answer `site_locked` with HTTP 409.
Answer `lock_store_unreachable` with HTTP 503.

- **Files**: `src/upgrade_portal/app/routes/org_upgrade.py`
- **Depends on**: T012
- **Done when**: A locked site blocks the submission.

### T015 [US9] Beat every held lock in the browser

Extend `startLockBeat` to hold a list of site identifiers.

- **Files**: `src/upgrade_portal/app/assets/static/js/portal.js`,
  `src/upgrade_portal/app/assets/templates/partials/lock_banner.html`
- **Depends on**: T012
- **Done when**: The banner posts one heartbeat for each site.

### T016 [US9] Release every lock when the run ends

- **Files**: `src/upgrade_portal/app/routes/org_upgrade.py`
- **Depends on**: T014
- **Done when**: A final job state leaves no held grant.

### T017 [P] [US9] Test the lock refusals

Cover the five acceptance scenarios of User Story 9.

- **Files**: `tests/unit/upgrade_portal/test_org_upgrade_guards.py`
- **Done when**: HTTP 409 and HTTP 503 both appear with the right code.

## Phase 5: User Story 3 - Pre-Checks (Priority: P1)

### T018 [US3] Read the pre-check state of each site

Write a helper that reads the newest verified capture of each selected site.

- **Files**: `src/upgrade_portal/app/routes/org_upgrade.py`
- **Done when**: The helper returns one state for each site.

### T019 [US3] Show the pre-check column

Add a pre-check column and a capture link to the site table.

- **Files**: `src/upgrade_portal/app/assets/templates/upgrade/org_options.html`
- **Depends on**: T018
- **Done when**: A site with no capture shows `Missing` and a capture link.

### T020 [US3] Add the pre-check guard to the write path

Answer `precheck_missing` with HTTP 409 when one site holds no baseline.

- **Files**: `src/upgrade_portal/app/routes/org_upgrade.py`
- **Depends on**: T018
- **Done when**: A missing baseline blocks the submission.

### T021 [P] [US3] Test the pre-check gate

Cover the four acceptance scenarios of User Story 3.

- **Files**: `tests/unit/upgrade_portal/test_org_upgrade_guards.py`
- **Done when**: The refusal names the site with no baseline.

## Phase 6: User Story 4 - Options (Priority: P2)

### T022 [P] [US4] Test the body rules

Cover every rule of `OrgUpgradeBody`.

- **Files**: `tests/unit/firmware/test_org_upgrade_body.py`
- **Done when**: Each invalid input raises `ValueError` with a plain message.

### T023 [US4] Add the serial strategy option

Add a `serial` option to the strategy group.

- **Files**: `src/upgrade_portal/app/assets/templates/upgrade/org_options.html`
- **Done when**: The page offers four strategies.

### T024 [US4] Add the force control

Add a `force` control. `read_options` maps it to `versions[0].force`.

- **Files**: `src/upgrade_portal/app/assets/templates/upgrade/org_options.html`,
  `src/upgrade_portal/app/routes/org_upgrade.py`
- **Done when**: The body carries the boolean flag.

### T025 [US4] Hide the dependent controls

Hide the phases input outside the canary strategy. Hide the failure input for
the big bang strategy.

- **Files**: `src/upgrade_portal/app/assets/templates/upgrade/org_options.html`
- **Depends on**: T023
- **Done when**: `filterAdvancedUpgradeControls` drives both controls.

### T026 [US4] Move the stored body to the run record

The session holds `org_upgrade_options` today. A worker restart loses that
request context.

- **Files**: `src/upgrade_portal/app/routes/org_upgrade.py`,
  `src/upgrade_portal/runtime/runs.py`
- **Depends on**: T028
- **Done when**: The session holds a run identifier and no body.

## Phase 7: User Story 6 - The Run Record and the Audit (Priority: P2)

### T027 [US6] Extend the run record

Add the seven new fields of `data-model.md`.

- **Files**: `src/upgrade_portal/runtime/runs.py`
- **Fields**: `upgrade_mode`, `site_ids`, `org_upgrade_id`, `org_upgrade_body`,
  `pre_capture_ids`, `post_capture_ids`, `site_lock_ids`.
- **Done when**: The builder writes every field and the present tests pass.

### T028 [US6] Create a run record for the organization job

- **Files**: `src/upgrade_portal/app/routes/org_upgrade.py`
- **Depends on**: T027
- **Done when**: The store holds one record for each organization job.

### T029 [US6] Write the audit entry

Write one audit entry for each write. Mask the API token.

- **Files**: `src/upgrade_portal/app/routes/org_upgrade.py`,
  `src/upgrade_portal/audit/logger.py`
- **Depends on**: T028
- **Done when**: The entry names the organization, the sites, and the answer.

### T030 [P] [US6] Test the record and the audit

- **Files**: `tests/contract/upgrade_portal/test_org_upgrade_routes.py`
- **Depends on**: T029
- **Done when**: A submission writes one record and one audit entry.

## Phase 8: User Story 7 - Progress, Poll, and History (Priority: P2)

### T031 [US7] Add the browser poll

Add a poll block beside `refreshRunStatus`. Read the identifier from
`data-upgrade-id`.

- **Files**: `src/upgrade_portal/app/assets/static/js/portal.js`,
  `src/upgrade_portal/app/assets/templates/upgrade/org_progress.html`
- **Depends on**: T005
- **Done when**: The page refreshes without an operator action.

### T032 [US7] Stop the poll on a final state

Stop the poll on HTTP 401 and on a final job state.

- **Files**: `src/upgrade_portal/app/assets/static/js/portal.js`
- **Depends on**: T031
- **Done when**: A finished job stops the network traffic.

### T033 [US7] Add the job history route

Add `GET /api/org-upgrades`. Call `listOrgDeviceUpgrades`.

- **Files**: `src/upgrade_portal/app/routes/org_upgrade.py`,
  `src/firmware/org_upgrade_service.py`
- **Done when**: The operator finds a job after an uncertain answer.

### T034 [US7] Add the cancel control to the page

Add a control with `data-testid="org-upgrade-cancel"`. The control posts
`confirmation` with the word `CANCEL`.

- **Files**: `src/upgrade_portal/app/assets/templates/upgrade/org_progress.html`
- **Done when**: The page states that a cancellation restores no upgraded
  device.

### T035 [P] [US7] Test the poll and the history

- **Files**: `tests/contract/upgrade_portal/test_org_upgrade_routes.py`
- **Done when**: The history answer lists the jobs of the organization.

## Phase 9: User Story 8 - Post-Checks and Comparison (Priority: P2)

### T036 [US8] Start a post-check for each site

Start a capture for each selected site when the job reaches a final state.

- **Files**: `src/upgrade_portal/app/routes/org_upgrade.py`,
  `src/upgrade_portal/app/routes/capture.py`
- **Depends on**: T028
- **Done when**: The record holds one post-check identifier for each site.

### T037 [US8] Add the comparison links

Add one comparison link for each site to the progress page.

- **Files**: `src/upgrade_portal/app/assets/templates/upgrade/org_progress.html`
- **Depends on**: T036
- **Done when**: Each link opens the comparison of two captures.

### T038 [P] [US8] Test the post-check path

Cover the four acceptance scenarios of User Story 8.

- **Files**: `tests/e2e/upgrade_portal/test_org_upgrade_flow.py`
- **Done when**: A failed post-check marks one site and keeps the others.

## Phase 10: User Story 1 and User Story 2 - Scope Hygiene (Priority: P3)

### T039 [Done] [US1] Clear the stale site set

Clear `OperatorSession.selected_site_ids` when the operator changes the
organization or the mode.

- **Files**: `src/upgrade_portal/app/routes/select.py`
- **Done when**: A mode change removes the previous site set.

### T040 [US2] Refuse an empty site set

Refuse `POST /select/site` when the multi-site body names no site.

- **Files**: `src/upgrade_portal/app/routes/select.py`
- **Done when**: The answer names the empty selection.

### T041 [US2] Refuse a duplicate site

- **Files**: `src/upgrade_portal/app/routes/select.py`
- **Done when**: The answer names the duplicate site.

### T042 [P] [US1] [US2] Test the scope rules

- **Files**: `tests/contract/upgrade_portal/test_select_mode.py`
- **Done when**: The nine acceptance scenarios of the two stories pass.

## Phase 11: Polish

### T043 Align the confirmation field names

Change the organization lane to `confirm`, or change the single-site lane to
`confirmation`. Change both sides in one task.

- **Files**: `src/upgrade_portal/app/routes/org_upgrade.py`,
  `src/upgrade_portal/app/routes/upgrade.py`, both confirmation templates
- **Depends on**: T008
- **Done when**: One field name serves both lanes and every test passes.

### T044 [P] Lint the Python code

```powershell
python -m ruff check src\upgrade_portal src\firmware
python -m ruff format --check src\upgrade_portal src\firmware
```

- **Done when**: The command reports no violation.

### T045 [P] Grade every changed Markdown file

```powershell
python -m tools.ste_linter --min-score 80 specs\2200-org-multisite-firmware-upgrade\spec.md
```

- **Done when**: Every file scores 80 or more.

### T046 Run the whole portal suite

```powershell
python -m pytest tests\unit\upgrade_portal tests\contract\upgrade_portal tests\e2e\upgrade_portal -q
```

- **Done when**: Every test passes offline in under 30 seconds.

### T047 Check the single-site flow for a regression

- **Files**: `tests/contract/upgrade_portal/test_select.py`,
  `tests/e2e/upgrade_portal/test_site_selection.py`
- **Done when**: Every single-site test passes without a change.

### T048 Add the inline comments and the action logs

Add one inline comment to every new line. Add an information log before each
action and a debug log after it.

- **Files**: Every changed Python file
- **Done when**: A review finds no uncommented line and no silent action.

### T049 Record the answers to the open questions

Write the answers of `research.md` section 7 into that file.

- **Files**: `specs/2200-org-multisite-firmware-upgrade/research.md`
- **Done when**: Each open question holds a verified answer.

### T050 Update the changelog and the README

Add the feature to `CHANGELOG.md`. Add the mode to the portal section of
`README.md`.

- **Done when**: Both files name the access point limit.

## Dependencies

```text
T001, T002, T003 -> T004 -> T005 -> T031 -> T032
T006 -> T007
T008 -> T009, T010, T011, T043
T012 -> T013, T014, T015
T014 -> T016, T017
T018 -> T019, T020, T021
T023 -> T025
T027 -> T028 -> T026, T029, T036
T029 -> T030
T036 -> T037 -> T038
Every task -> T044, T045, T046, T047
```

## Parallel Opportunities

Run these groups together. Each group touches separate files.

**Group A (baseline)**: T001, T002, T003.

**Group B (tests)**: T007, T011, T017, T021, T022, T030, T035, T038, T042.

**Group C (polish)**: T044, T045.

## Implementation Strategy

### The safety release

Finish Phase 2 through Phase 5. The lane then holds a true device count and a
write session with no retry. It also holds a browser gate, a lock for each site,
and a baseline for each site.

Warning: do not ship the lane without Phase 4 and Phase 5, because a job can
interrupt service with no proof of the result.

### Incremental delivery

1. Phase 1 records the baseline.
2. Phase 2 repairs the present defects.
3. Phase 3 adds the browser gate.
4. Phase 4 adds the locks.
5. Phase 5 adds the baseline gate.
6. Phase 6 and Phase 7 add the options and the record.
7. Phase 8 and Phase 9 add the watch and the proof.
8. Phase 10 and Phase 11 add the hygiene and the quality gates.

## Notes

- Keep every view function under 25 lines.
- Keep the cloud calls in the service class.
- Keep the confirmation word in one Jinja variable.
- Keep the site operations of the single-site flow without a change.
- Add no automatic retry to any write path.
- Add no switch support and no gateway support in this feature.
- Add no SSR support and no Mist Edge support in this feature.
