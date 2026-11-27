# Tasks: Persist resumable firmware phase state

**Input**: `spec.md`, `plan.md`, and `design/research.md`. Numeric route `specs/numbered/0/0/1/1/2/0/4/2/4022-resumable-phase-state/`.

**Status values**: `open` for a gate or process step that has not run. `absent` for code that does not exist on `main`. `verified-present` for behavior that already exists on `main`.

**Parallel marker**: `[P]` means the task touches files that no other open task touches.

## Phase 1: Owner approval and baseline

### T000 - Obtain owner approval to start

- **Status**: open
- **Requirements**: FR-030 (scope), HUMAN-DECISION-REQUIRED D-11
- **Files**: none. The owner posts an approval comment on issue #4022.
- **Depends on**: none
- **Acceptance**: The owner approves D-1 to D-12 in a comment after the 2026-11-10 hold comment. The owner files a separate issue for the single-site unknown-outcome defect. AGENTS.md requires one issue for each concern.
- **Verification**: `gh issue view 4022 -R jmorrison-juniper/MistHelper --json comments`

### T001 - Confirm the ordered single-site submission on main

- **Status**: verified-present (RC-017, RC-018, RC-021)
- **Requirements**: FR-016 (baseline)
- **Files**: `src/interfaces/portals/upgrade_portal/upgrade/driver.py`, `src/interfaces/portals/upgrade_portal/app/wiring.py`
- **Depends on**: none
- **Acceptance**: The cascade loop submits one phase at a time. The existing phase-order tests pass without a change.
- **Verification**: `python -m pytest tests/unit/upgrade_portal/test_upgrade_driver.py`

## Phase 2: Single-site unknown outcomes (safety fix)

### T002 - Classify each firmware reply as accepted, refused, or unknown

- **Status**: absent (RC-022, RC-023, RC-024, RC-027)
- **Requirements**: FR-002, FR-019, FR-020, FR-021
- **Files**: `src/interfaces/portals/upgrade_portal/app/wiring.py` (modify `_send`, `_dispatch_plan`, and `_persist_refusal`, and add `SubmissionOutcomeClassifier`). `src/foundation/support/submission_certainty.py` (read it and use `is_known_refusal`, RC-034).
- **Depends on**: T000
- **Acceptance**: A transport fault, HTTP 408, 429, 499, any 5xx, an undocumented status, and a 200 without identity each store `unknown`. Documented refusals 400, 401, 403, and 404 with no conflicting evidence store `refused`. The unknown text does not say "refused".
- **Verification**: `python -m pytest tests/unit/upgrade_portal/test_wiring_submitter.py`

### T003 - Keep the site hold for unknown and unsettled outcomes

- **Status**: absent (RC-014, RC-015, RC-016)
- **Requirements**: FR-017, FR-018
- **Files**: `src/interfaces/portals/upgrade_portal/upgrade/driver.py` (modify `run`, `_free_lock`, `_final_state`). `tests/unit/upgrade_portal/test_upgrade_driver.py` (TC-05 to TC-08).
- **Depends on**: T002, T005
- **Acceptance**: At `stopped` or `failed`, the driver keeps the lock while a hold is active. A clean stop and a clean failure still release the lock. Before the change, audit RC-071 and RC-072. Each assertion that pins the unknown-outcome release is replaced in this change.
- **Verification**: `python -m pytest tests/unit/upgrade_portal/test_upgrade_driver.py -k "releases_the_site_lock or keeps_the_site_lock"`

### T015 - Share the settlement predicate for lock release on the org path and the lease

- **Status**: absent (RC-012, RC-013, RC-047, RC-048)
- **Requirements**: FR-018
- **Files**: `src/foundation/support/submission_certainty.py` (add a settlement classmethod). `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` (use it). `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/locks.py` (guard the release). `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py` (guard the lease release).
- **Depends on**: none. This defect exists on `main` today. File it as a separate issue (see analysis.md, F-03).
- **Acceptance**: The org release path and the lease release both require the shared predicate before a release. TC-28 passes.
- **Verification**: `python -m pytest tests/unit/upgrade_portal/test_org_cascade_walk.py`

## Phase 3: Run model, recovery point, and reconciliation

### T004 - Keep observation and reset the recovery phase for resume

- **Status**: absent (RC-010, RC-011, RC-073, RC-074)
- **Requirements**: FR-023
- **Files**: `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/record.py`, `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py`. `tests/unit/upgrade_portal/test_org_cascade_walk.py` (TC-17, TC-18).
- **Depends on**: T005
- **Acceptance**: Observation keeps a failed phase as ended. The walk starts no new wait for it. The resume resets the recovery phase to `pending` before observation. TC-17 changes only the failed-phase assertion. TC-18 passes.
- **Verification**: `python -m pytest tests/unit/upgrade_portal/test_org_cascade_walk.py`

### T005 - Add the state, the phase key, and the recovery point to the run model

- **Status**: absent (RC-001, RC-002, RC-003, RC-004, RC-005, RC-006, RC-007, RC-008)
- **Requirements**: FR-001, FR-002, FR-006
- **Files**: `src/interfaces/portals/upgrade_portal/runtime/runs.py` (add `RunState.RESUMING`, `RunStateMachine.resume`, the `submission` key in `RunRecordBuilder.initial_phases`, and the recovery point in `RunStatusView`). `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/record.py` (add the `submission` key to `OrgPhaseEntries`).
- **Depends on**: T001
- **Acceptance**: Each phase entry has `submission` with the default `not_sent`. The machine moves `stopped` to `resuming` only when a recovery point exists. No other new move exists.
- **Verification**: `python -m pytest tests/unit/upgrade_portal/test_upgrade_driver.py tests/unit/upgrade_portal/test_org_cascade_walk.py`

### T006 - Verify each recovery point and resume attempt by read-back

- **Status**: absent (RC-064, RC-065, RC-066)
- **Requirements**: FR-003, FR-004
- **Files**: `src/interfaces/portals/upgrade_portal/upgrade/driver.py` (modify `_save`). `src/interfaces/portals/upgrade_portal/capture/store.py` (read only, `verify_write`). `tests/unit/upgrade_portal/test_upgrade_driver.py` (TC-10).
- **Depends on**: T005
- **Acceptance**: A recovery point or attempt write that the read-back does not confirm keeps the site hold. The run does not report a clean stop. No success message appears.
- **Verification**: `python -m pytest tests/unit/upgrade_portal/test_upgrade_driver.py -k "lost_run_write or unverified"`

### T007 - Write the recovery point at stop and failure

- **Status**: absent (RC-017, RC-019)
- **Requirements**: FR-001, FR-002, FR-005
- **Files**: `src/interfaces/portals/upgrade_portal/upgrade/driver.py` (modify `_stop`, `_fail`, `_cascade_phase`, `_run_phase`). `src/interfaces/portals/upgrade_portal/app/wiring.py` (set the submission state).
- **Depends on**: T002, T005, T006
- **Acceptance**: A stop writes one recovery point with the recovery phase, the reason, the submission state, and the hold flag. A stop during the settle wait writes no phase outcome. TC-09 passes.
- **Verification**: `python -m pytest tests/unit/upgrade_portal/test_upgrade_driver.py -k "stop"`

### T008 - Reconcile the live state before a resume write

- **Status**: absent (RC-056, RC-057, RC-058, RC-059, RC-060, RC-061, RC-063)
- **Requirements**: FR-010, FR-011, FR-014
- **Files**: `src/interfaces/portals/upgrade_portal/api/run_controls/services/reconciliation.py` (add `ResumeReconciler`. Refuse a complete outcome while a phase is unresolved). `src/interfaces/portals/upgrade_portal/api/run_controls/routes.py` (read only, `listSiteDevicesStats` read). `tests/unit/upgrade_portal/test_runs/test_reconciliation.py` (TC-19).
- **Depends on**: T005
- **Acceptance**: The reconciler reads device stats and the job list. It returns one verdict for each device. An unknown phase with no proof returns no write permission. TC-14 and TC-19 pass.
- **Verification**: `python -m pytest tests/unit/upgrade_portal/test_runs/test_reconciliation.py`

## Phase 4: Single-site resume

### T009 - Resume one recovery phase in place

- **Status**: absent (RC-017, RC-018, RC-019)
- **Requirements**: FR-009, FR-011, FR-012, FR-013, FR-015, FR-016, FR-021, FR-029
- **Files**: `src/interfaces/portals/upgrade_portal/upgrade/driver.py` (add a `resume` method and a cascade start index). `src/interfaces/portals/upgrade_portal/runtime/runs.py` (use the transition). `src/interfaces/portals/upgrade_portal/app/wiring.py` (use `RunDispatchGate` for each call).
- **Depends on**: T004, T005, T007, T008
- **Acceptance**: The resume sends at most one call for the recovery phase. It sends no call to a settled, skipped, or at-target device. It observes an accepted phase. Later phases wait. An info line precedes and a debug line follows each action. TC-11 to TC-16 pass.
- **Verification**: `python -m pytest tests/unit/upgrade_portal/test_upgrade_driver.py -k "resume"`

### T010 - Add the typed RESUME route (single-site)

- **Status**: absent (RC-050, RC-053)
- **Requirements**: FR-006, FR-007, FR-008, FR-009
- **Files**: `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py` (add `RESUME_TEXT` beside `CONFIRM_TEXT` at line 172. Add the resume route beside the start route at line 2286). `src/interfaces/portals/upgrade_portal/app/wiring.py` (add the service seam).
- **Depends on**: T009
- **Acceptance**: A missing or wrong word returns `confirmation_required` before any Mist request. A run that is not stopped returns `run_not_resumable`. Another holder returns `site_locked`. TC-20 passes.
- **Verification**: `python -m pytest tests/contract/upgrade_portal/test_retry_failed_run.py`

### T011 - Guard start, pre-check, takeover, and retry with the site hold

- **Status**: absent (RC-051, RC-052, RC-054, RC-055)
- **Requirements**: FR-022
- **Files**: `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py` (modify the start route at line 2286, the retry route at line 2808, and the pre-check acquire path). `tests/contract/upgrade_portal/test_retry_failed_run.py` (TC-21, TC-22).
- **Depends on**: T005, T007
- **Acceptance**: While a hold is active, the start route, the pre-check, and the retry route refuse the request with `site_hold_active`. The active-run check at line 209 counts a held stopped run as active. TC-21 and TC-22 pass.
- **Verification**: `python -m pytest tests/contract/upgrade_portal/test_retry_failed_run.py`

## Phase 5: Operator surfaces

### T012 - Show the recovery card and the resume control on the single-site page

- **Status**: absent (RC-069, RC-070, RC-129)
- **Requirements**: FR-005, FR-006, FR-027
- **Files**: `src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/progress.html`. `src/interfaces/portals/upgrade_portal/app/assets/static/js/portal.js`. `tests/e2e/upgrade_portal/test_run_controls/test_existing.py` (TC-23, TC-24).
- **Depends on**: T010
- **Acceptance**: The card names the recovery phase, the reason, and one next step. The resume control has a stable `data-testid`, stays disabled until `RESUME` is typed, and is absent without a recovery point. The retry control is hidden while a hold is active. TC-23 and TC-24 pass.
- **Verification**: `python -m pytest tests/e2e/upgrade_portal/test_run_controls/test_existing.py`

### T013 - Update operator text and the tests that pin it

- **Status**: absent (RC-009, RC-024, RC-067, RC-068, RC-077, RC-078)
- **Requirements**: FR-025, FR-026
- **Files**: `src/interfaces/portals/upgrade_portal/runtime/runs.py` (the `stopped` message, RC-009). `src/interfaces/portals/upgrade_portal/app/wiring.py` (the refusal and unknown texts, RC-024). `src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/progress.html`. `tests/unit/upgrade_portal/test_org_phase_list_parity.py` (TC-25). `tests/contract/upgrade_portal/test_org_phase_watch_contract.py` (TC-26).
- **Depends on**: T007, T010, T012
- **Acceptance**: Before the change, search `tests/` for each old string with the grep tool. Each stop, failure, and unknown message names the phase, the reason, and one next step. Each changed string has its test updated in the same change. The grep returns no old string.
- **Verification**: `python -m pytest tests/unit/upgrade_portal/test_org_phase_list_parity.py tests/contract/upgrade_portal/test_org_phase_watch_contract.py`

## Phase 6: Multi-site (blocked by issue #4021)

### T014 - Resume multi-site phases after issue #4021 merges

- **Status**: absent (RC-044, RC-045, RC-046, RC-047, RC-048, RC-049)
- **Requirements**: FR-024, FR-015, FR-016, FR-017, FR-018
- **Files**: `src/operations/execution/firmware/aggregate_upgrade_service.py`. `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`. `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py`. `src/interfaces/portals/upgrade_portal/app/assets/templates/partials/org_phase_list.html`. `tests/unit/firmware/test_aggregate_upgrade_service.py` (TC-27). `tests/e2e/upgrade_portal/test_org_phase_cascade_journey.py` (TC-29).
- **Depends on**: issue #4021 merged. T009, T010, T013, T015.
- **Acceptance**: The multi-site resume submits only unresolved children, in phase order, with the same hold rules. TC-27 and TC-29 pass.
- **Verification**: `python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py tests/e2e/upgrade_portal/test_org_phase_cascade_journey.py`

## Phase 7: Documentation and changelog

### T016 - Update the operator guide, the README, and the lock contract

- **Status**: absent (RC-039, RC-087, RC-088, RC-128)
- **Requirements**: FR-025
- **Files**: `documentation/upgrade_capture_portal.md` (add a `RESUME` row beside the `STOP` row at line 61. Add a resume section beside the stop section at line 673. Correct the lock life row at line 625 to the key expiry of 3600 seconds and the quiet period of 300 seconds). `README.md` (update the upgrade capture portal section). `specs/1823-upgrade-capture-portal/contracts/site-lock.md` (add the hold to the release rule at lines 105 and 106).
- **Depends on**: T010, T012, T013
- **Acceptance**: Each document names `RESUME`, the site hold, one next step, and the lock values from `lock.py` (RC-041, RC-042). The STE gate passes for each changed Markdown file.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 documentation/upgrade_capture_portal.md README.md specs/1823-upgrade-capture-portal/contracts/site-lock.md`

### T017 - Add the changelog fragment

- **Status**: absent (RC-091)
- **Requirements**: constitution documentation rule
- **Files**: `changelog.d/issue-4022-resumable-phase-state.md` (new file)
- **Depends on**: T001 to T016
- **Acceptance**: The fragment has one `###` heading. It has one bullet for each change type that a user sees, and the bullet names issue 4022.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4022-resumable-phase-state.md`

## Phase 8: Delivery gates

### T-LOCAL-GATES - Run each applicable local gate

- **Status**: open
- **Requirements**: FR-028, FR-030, SC-006
- **Files**: every changed file in plan.md
- **Depends on**: T002 to T013, T015, T016, T017. T014 runs only after issue #4021 merges.
- **Acceptance**: Each gate reports its expected result from the gate table in `.github/copilot-instructions.md`. A gate that does not apply names its reason in the pull request body.
  - Compile: `python -m py_compile MistHelper.py`. The file does not change. The gate runs as the constitution requires.
  - Lint: `python -m ruff check .` reports `All checks passed`.
  - Format: `python -m black --check .` reports no change needed.
  - Types: `python -m mypy $MYPY_PATHS --config-file pyproject.toml` reports `Success`.
  - Tests: `python -m pytest` on each changed test file.
  - Full tests: the two `pytest-chunks` commands in `.github/copilot-instructions.md`.
  - Coverage: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` reports 80 percent or above.
  - Test quality: the `test-quality-analyzer --gate` procedure reports zero new findings.
  - Complexity: `radon cc src/interfaces/portals/upgrade_portal -j | complexity-gate --max 10`.
  - Security lint: `bandit -c pyproject.toml -r src/interfaces/portals/upgrade_portal -q`.
  - Code quality: `pylint src/ --fail-under=9.5`.
  - Dead code: `vulture $VULTURE_PATHS --min-confidence 70`.
  - Docstrings: `pydocstyle $PYDOCSTYLE_PATHS` and `interrogate $INTERROGATE_PATHS --fail-under 90`.
  - Symbols: `symbol-diff --base origin/main <file>` for each changed Python file.
  - STE: `ste-linter --config .ste-linter.toml --min-score 80` on each changed Markdown file.
  - SDK guard: `python -m pytest tests/integration/test_mistapi_sdk_compatibility.py` (FR-028).
  - Menu guard: `python -m pytest tests/guardrails/test_destructive_menu_docs.py` (FR-030).
  - Not applicable: menu reference generation (no menu row changes), ops portal gates (no change under `ops-portal/`), and ops platform gate (no change under `mist-ops-platform/`). Also not applicable: `pip-audit` (no dependency manifest changes).
- **Verification**: the commands listed in Acceptance.

### T-PR - Commit, push, and open the pull request

- **Status**: open
- **Requirements**: constitution Principle IV, multi-agent workflow
- **Files**: changed files only, staged by explicit path. The change never uses `git add -A`.
- **Depends on**: T-LOCAL-GATES
- **Acceptance**: The branch `feat/4022-resumable-phase-state` starts from `main`. The commit subject is `feat(upgrade): persist resumable firmware phase state`. The body contains `Closes #4022` and the Co-authored-by trailer. The pull request title uses the same subject. The body lists each gate result. The `auto-merge` label is not added.
- **Verification**: `gh pr view <number> -R jmorrison-juniper/MistHelper --json title,body,labels`

### T-REMOTE-CI - Watch the CI run

- **Status**: open
- **Requirements**: constitution Principle IV
- **Files**: none
- **Depends on**: T-PR
- **Acceptance**: Each required check reports success on the pull request head. CodeQL reports success.
- **Verification**: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`

### T-MERGE - Merge after authorization, then verify the deployed revision

- **Status**: open
- **Requirements**: constitution Principle IV, D-11
- **Files**: none
- **Depends on**: T-REMOTE-CI, owner approval (T000), human safety review (`needs-human-review` label)
- **Acceptance**: The orchestrator authorizes the merge after the human review. The squash merge creates one commit on `main`. The `container-build.yml` run on the merged revision succeeds. The image revision label equals the merged commit SHA. The container health check passes after deployment.
- **Verification**: `gh run list --workflow container-build.yml -R jmorrison-juniper/MistHelper --limit 1`

## Dependencies

- T000 blocks T002 to T013, T015, and T016.
- T001 blocks T005.
- T002 blocks T003 and T007.
- T005 blocks T003, T004, T006, T008, and T011.
- T006 blocks T007.
- T007 blocks T009, T011, and T013.
- T008 blocks T009.
- T009 blocks T010 and T014.
- T010 blocks T011, T012, T013, and T016.
- T012 blocks T013 and T016.
- T015 blocks T014.
- T013 blocks T014 and T016.
- T016 and T017 block T-LOCAL-GATES.
- T-LOCAL-GATES blocks T-PR. T-PR blocks T-REMOTE-CI. T-REMOTE-CI blocks T-MERGE.

## Test Cases

| ID | File | Case | Kind | Task |
| - | - | - | - | - |
| TC-01 | `tests/unit/upgrade_portal/test_wiring_submitter.py` | A transport fault stores `unknown`, and the text does not say "refused". | new | T002 |
| TC-02 | `tests/unit/upgrade_portal/test_wiring_submitter.py` | An HTTP 503 reply stores `unknown`. | new | T002 |
| TC-03 | `tests/unit/upgrade_portal/test_wiring_submitter.py` | An HTTP 200 without an upgrade identity stores `unknown`. | new | T002 |
| TC-04 | `tests/unit/upgrade_portal/test_wiring_submitter.py` | A documented refusal stores `refused` in the phase entry. | new | T002 |
| TC-05 | `tests/unit/upgrade_portal/test_upgrade_driver.py` | An `unknown` phase keeps the site lock at `stopped`. | new | T003 |
| TC-06 | `tests/unit/upgrade_portal/test_upgrade_driver.py` | An `unknown` phase keeps the site lock at `failed`. | new | T003 |
| TC-07 | `tests/unit/upgrade_portal/test_upgrade_driver.py` | A clean stop releases the site lock. The existing assertion at line 1992 is audited first. | changed | T003 |
| TC-08 | `tests/unit/upgrade_portal/test_upgrade_driver.py` | A clean failure releases the site lock. The existing assertion at line 2009 is audited first. | changed | T003 |
| TC-09 | `tests/unit/upgrade_portal/test_upgrade_driver.py` | A stop writes one recovery point with the phase, the reason, and the submission state. | new | T007 |
| TC-10 | `tests/unit/upgrade_portal/test_upgrade_driver.py` | An unverified recovery point write keeps the hold and reports no clean stop. | new | T006 |
| TC-11 | `tests/unit/upgrade_portal/test_upgrade_driver.py` | A resume sends one call for the recovery phase and logs an info line before and a debug line after it. | new | T009 |
| TC-12 | `tests/unit/upgrade_portal/test_upgrade_driver.py` | A resume sends nothing to a settled or skipped phase. | new | T009 |
| TC-13 | `tests/unit/upgrade_portal/test_upgrade_driver.py` | A resume sends nothing to a device at its target version. | new | T009 |
| TC-14 | `tests/unit/upgrade_portal/test_upgrade_driver.py` | An `unknown` phase sends nothing before reconciliation proves the outcome. | new | T008 |
| TC-15 | `tests/unit/upgrade_portal/test_upgrade_driver.py` | An `accepted` phase is observed and never submitted again. | new | T009 |
| TC-16 | `tests/unit/upgrade_portal/test_upgrade_driver.py` | A later phase waits until the recovery phase settles. | new | T009 |
| TC-17 | `tests/unit/upgrade_portal/test_org_cascade_walk.py` | A failed phase is observed without a new wait. The failed-phase assertion at line 217 changes. | changed | T004 |
| TC-18 | `tests/unit/upgrade_portal/test_org_cascade_walk.py` | The resume resets the recovery phase to `pending` before observation. | new | T004 |
| TC-19 | `tests/unit/upgrade_portal/test_runs/test_reconciliation.py` | A reconcile does not mark a run complete while a phase is unresolved. | new | T008 |
| TC-20 | `tests/contract/upgrade_portal/test_retry_failed_run.py` | A wrong or missing word, a run that is not stopped, or another holder sends no Mist request. | new | T010 |
| TC-21 | `tests/contract/upgrade_portal/test_retry_failed_run.py` | The start route refuses with `site_hold_active` during a hold. | new | T011 |
| TC-22 | `tests/contract/upgrade_portal/test_retry_failed_run.py` | The retry route refuses with `site_hold_active` during a hold. | new | T011 |
| TC-23 | `tests/e2e/upgrade_portal/test_run_controls/test_existing.py` | The stopped page shows the phase, the reason, and one next step. Without a recovery point, no resume control appears. | new | T012 |
| TC-24 | `tests/e2e/upgrade_portal/test_run_controls/test_existing.py` | The resume control stays disabled until `RESUME` is typed, and it has a stable `data-testid`. | new | T012 |
| TC-25 | `tests/unit/upgrade_portal/test_org_phase_list_parity.py` | The cadence text assertion at line 145 matches the changed text. | changed | T013 |
| TC-26 | `tests/contract/upgrade_portal/test_org_phase_watch_contract.py` | The warning assertion at line 471 matches the changed text. | changed | T013 |
| TC-27 | `tests/unit/firmware/test_aggregate_upgrade_service.py` | A multi-site resume submits only the unresolved children, in phase order. | new | T014 |
| TC-28 | `tests/unit/upgrade_portal/test_org_cascade_walk.py` | A lease release waits for the shared settlement predicate. | new | T015 |
| TC-29 | `tests/e2e/upgrade_portal/test_org_phase_cascade_journey.py` | A stopped multi-site phase shows the next step and the resume journey. | new | T014 |

Count: 29 test cases. 24 are new and 5 are changed (TC-07, TC-08, TC-17, TC-25, TC-26).
