# Tasks: Ordered Multi-Site Firmware Families

**Input**: Numeric record `specs/numbered/0/0/1/1/2/0/4/1/4021-ordered-multi-site-firmware-phases/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, `design/contracts/`.

**Tests**: Tests are required by the constitution. The plan names 17 tests: 15 new and 2 rewritten.

**Status values**: `open` means the change does not exist yet. `verified-present` means the defect exists on remote `main`. Each task names one verification command from the local gates table.

## Format

- `[P]` marks a task that can run in parallel with its neighbors.
- `[US#]` names the user story. `FR-###` names the requirement.
- Each task names exact repository paths. Function names identify the code area.

## Phase 1: Baseline Evidence

- [ ] T001 [P] [US1] Confirm that the aggregate build places access points first. Requirement FR-001. Paths: `src/operations/execution/firmware/aggregate_upgrade_service.py`. Acceptance: research rows 2 and 3 match the current code. Verification: `python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py -q`. Status: verified-present.
- [ ] T002 [P] [US2] Confirm that the submit loop continues after a refusal and after an unknown outcome. Requirements FR-007, FR-008. Paths: `src/operations/execution/firmware/aggregate_upgrade_service.py`. Acceptance: research rows 1 and 4 match the current code. Verification: `python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py -q`. Status: verified-present.

## Phase 2: Shared Model and Seams

- [ ] T003 [US1] Add the family rank for each child. Map an SSR child to the gateway family. Reuse `upgrade_service.PLAN_FAMILY_ORDER`. Requirements FR-001, FR-012. Paths: `src/operations/execution/firmware/aggregate_upgrade_service.py`. Acceptance: the rank returns gateway, switch, AP in that order, and clients have no rank. Verification: `python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py -q`. Status: open.
- [ ] T004 [US1] Add the portal-neutral `FamilySettleGate` protocol and the `FamilyGateResult` type. Requirement FR-003. Paths: `src/operations/execution/firmware/aggregate_upgrade_service.py`. Acceptance: the module imports no portal module, and the protocol names `settle` with three result states. Verification: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`. Status: open.
- [ ] T005 [US1] Order the children by family rank in `_children`. Keep the site order inside each family. Requirement FR-001. Paths: `src/operations/execution/firmware/aggregate_upgrade_service.py`. Acceptance: the children list starts with the gateway family and ends with the AP family. Verification: `python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py -q`. Status: open.

## Phase 3: Family Loop and Stops

- [ ] T006 [US2] Add the family loop to `submit` with one parent claim for each family send. Map the state `family_waiting` to `running` in `_aggregate_state`. Requirements FR-002, FR-013. Paths: `src/operations/execution/firmware/aggregate_upgrade_service.py`. Acceptance: no parent claim exists during a gate wait, and the state reads running. Verification: `python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py -q`. Status: open.
- [ ] T007 [US2] Stop the family and every later family on a refusal, an unknown outcome, a lock loss, or a cancellation. Requirements FR-007, FR-008, FR-011. Paths: `src/operations/execution/firmware/aggregate_upgrade_service.py`. Acceptance: a refused child sends no later child, and an unknown child never resends. Verification: `python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py -q`. Status: open.
- [ ] T008 [US2] Call the family gate after each family. Record the result. Stop on a result that is not settled. Requirements FR-002, FR-004, FR-005, FR-006. Paths: `src/operations/execution/firmware/aggregate_upgrade_service.py`. Acceptance: an empty family skips the gate, and a failed gate stops the run. Verification: `python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py -q`. Status: open.
- [ ] T009 [US2] Write the stop record through the compare-and-set helper before the run ends. Requirements FR-010, FR-011. Paths: `src/operations/execution/firmware/aggregate_upgrade_service.py`. Acceptance: the stop record reads back after a JSON round trip with every contract field. Verification: `python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py -q`. Status: open.
- [ ] T010 [US2] Add the `process_lost` branch to `_recover_for_status`. Requirement FR-019. Paths: `src/operations/execution/firmware/aggregate_upgrade_service.py`. Acceptance: a stale wait marker writes a stop record and sends no child. Verification: `python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py -q`. Status: open.
- [ ] T015 [US2] Add the stop sentences. Each sentence names the family and the next operator action. Requirement FR-017. Paths: `src/operations/execution/firmware/aggregate_upgrade_service.py`. Acceptance: each sentence has no host, token, or cloud body, and each sentence has at most 25 words. Verification: `python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py -q`. Status: open.

## Phase 4: Portal Side

- [ ] T011 [US3] Add `OrgFamilyGate` in the phase watch module. It wraps `OrgPhaseGates` and maps each `PhaseOutcome` to a `FamilyGateResult`. Requirements FR-003, FR-004, FR-005. Paths: `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py`. Acceptance: a state other than settled or failed maps to unknown. Verification: `python -m pytest tests/unit/upgrade_portal/test_org_cascade_walk.py -q`. Status: open.
- [ ] T012 [US3] Add `AggregateRunRegistry` in the phase watch module. It starts one background run for each operation. Requirement FR-015. Paths: `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py`. Acceptance: a second start for one operation returns without a second thread. Verification: `python -m pytest tests/unit/upgrade_portal/test_org_cascade_walk.py -q`. Status: open.
- [ ] T013 [US3] Make `OrgCascade._settle` read the stored family gate result first. Stop after a stop record. Requirement FR-016. Paths: `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py`. Acceptance: a stored result causes no gate call, and a stop record marks later families as not submitted. Verification: `python -m pytest tests/unit/upgrade_portal/test_org_cascade_walk.py -q`. Status: open.
- [ ] T014 [US3] Renew the site locks during each family gate wait. Use the lease created in the route. Requirement FR-014. Paths: `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py`, `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`. Acceptance: each gate poll renews the lease once. Verification: `python -m pytest tests/unit/upgrade_portal/test_org_cascade_walk.py -q`. Status: open.
- [ ] T020 [US3] Split `_send_aggregate` into a synchronous check and a background start. Keep the error mapping of the check. Requirement FR-015. Paths: `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`, `tests/contract/upgrade_portal/test_org_upgrade_routes.py`. Acceptance: the route returns before any family gate wait, and a replay returns the existing conflict response. Verification: `python -m pytest tests/contract/upgrade_portal/test_org_upgrade_routes.py -q`. Status: open.

## Phase 5: Tests

- [ ] T016 [US1] Rewrite `test_partial_submission_keeps_each_child_and_blocks_replay`. Assert a refusal stop in place of the continuation. Requirement FR-020. Paths: `tests/unit/firmware/test_aggregate_upgrade_service.py`. Acceptance: the docstring names the replaced behavior, and no later family call appears. Verification: `python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py -q`. Status: open.
- [ ] T017 [US1] Rewrite `test_lock_loss_marks_current_and_untouched_children` for the family order. Requirement FR-020. Paths: `tests/unit/firmware/test_aggregate_upgrade_service.py`. Acceptance: the first call is the gateway family, and the lock loss stops the later families. Verification: `python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py -q`. Status: open.
- [ ] T018 [US1] Add three order tests. They cover the family order, the SSR family, and the wait before the next family. Requirements FR-001, FR-002, FR-003. Paths: `tests/unit/firmware/test_aggregate_upgrade_service.py`. Acceptance: each test fails on the current code. Verification: `python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py -q`. Status: open.
- [ ] T019 [US2] Add eight stop tests. They cover refusal, unknown outcome, failed gate, unknown gate result, empty family, clients, durable stop record, and process loss. Requirements FR-005 to FR-010, FR-012, FR-019. Paths: `tests/unit/firmware/test_aggregate_upgrade_service.py`. Acceptance: each test asserts one rule from the spec. Verification: `python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py -q`. Status: open.
- [ ] T021 [US2] Run each affected file in research rows 35 to 50. Change only the assertion that the new rule breaks. Requirement FR-020. Paths: `tests/contract/upgrade_portal/`, `tests/unit/prod_readiness/operations/execution/firmware/upgraders/`, `tests/support/org_cascade_seams.py`, `tests/e2e/upgrade_portal/conftest.py`. Acceptance: each changed assertion names the replaced behavior. Verification: `python -m pytest tests/unit/prod_readiness/operations/execution/firmware/upgraders/aggregations -q`. Status: open.
- [ ] T022 [P] [US4] Add one changelog fragment for the change. Paths: `changelog.d/issue-4021-ordered-multi-site-firmware-phases.md`. Acceptance: the fragment has one heading and one bullet that names the issue. Verification: `python -m pytest tests/guardrails`. Status: open.
- [ ] T023 [P] [US4] Update the module docstrings of the two production modules in the same change. Paths: `src/operations/execution/firmware/aggregate_upgrade_service.py`, `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py`. Acceptance: the walk docstring no longer says the watch sends no firmware request. Verification: `python -m pydocstyle src/ wsgi.py web_portal`. Status: open.

## Final Tasks

- [ ] T-LOCAL-GATES Run every local gate that applies to the changed files. Requirements all. Paths: the changed files listed above. Acceptance: each gate prints its expected result, or the record names the gate as not applicable with a reason. Verification: `python -m ruff check .`. Status: open.
- [ ] T-PR Commit with a Conventional Commits message. Push the branch `feat/4021-ordered-multi-site-firmware-phases`. Open a pull request with `Closes #4021` in the body. Requirements all. Paths: the changed files listed above. Acceptance: the pull request title passes the title rule, and the body names the manifest expansion. Verification: `python -m pytest tests/guardrails`. Status: open.
- [ ] T-REMOTE-CI Watch the CI run on the pull request with `gh pr checks <number> --watch`. Requirements all. Paths: none. Acceptance: each required check passes on the head commit. Verification: `python -m pytest tests/guardrails`. Status: open.
- [ ] T-MERGE Squash merge after a human reviews the change. Do not add the `auto-merge` label. Requirements all. Paths: none. Acceptance: the owner authorizes the merge, and the squash commit lands on `main`. Verification: `python -m pytest tests/guardrails`. Status: open.

## Dependencies

- T001 and T002 run first. They prove the baseline.
- T003 and T004 run before T005. T005 runs before T006.
- T006 to T010 run before T015 and T011.
- T011 to T014 run before T020.
- T016 and T017 run before T018 and T019.
- T018 to T021 run before T-LOCAL-GATES.
- T-LOCAL-GATES runs before T-PR. T-PR runs before T-REMOTE-CI. T-REMOTE-CI runs before T-MERGE.
- T022 and T023 are parallel with each other and run after T006.

## Notes

- Each task names one verification command from the local gates table.
- The change adds no `auto-merge` label. Issue #4021 requires a human reader.
- Resume belongs to issue #4022. No task implements resume.
