# Tasks: The pre-check captures of a multi-site upgrade

**Issue**: #3243
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

## Phase 1. The red tests

- [x] T001 Write `tests/unit/upgrade_portal/test_org_precheck.py`. Cover the ready rule, the missing names, and the stored list. Cover a reader fault and a gate with no reader. Cover the stored rows of a record and the projection of the store query.
- [x] T002 Write `tests/contract/upgrade_portal/test_org_precheck_routes.py`. Cover the card, the hint, and the disabled field. Cover each refusal of the endpoint, the 202 answer, and the lock with no run. Cover the start refusal, the lock bind, and the refusal of another run. Cover the stored list and the progress card.
- [x] T003 Add a parity test to `tests/contract/upgrade_portal/test_org_precheck_routes.py`. Prove the same status and the same refusal code in both modes.
- [x] T004 Run the new tests. Record the red result in the session folder.

## Phase 2. The view layer and the store

- [x] T005 Add `src/upgrade_portal/upgrade/org_precheck.py` with `SitePrecheck`, `OrgPrecheckState`, and `OrgPrecheckGate`.
- [x] T006 Change `_PRECHECK_QUERY` in `src/upgrade_portal/capture/store.py` to return the seven fields of the plan.

## Phase 3. The routes

- [x] T007 Add `precheck_gate`, the gate of `confirm_page`, and the gate of `submit_upgrade` to `org_upgrade.py`.
- [x] T008 Add `_record_prechecks` to `_submit_aggregate`.
- [x] T009 Split `_acquire_operation_locks`. Add `_operation_lock` and `_bind_precheck_lock`.
- [x] T010 Add `prechecks` to `_aggregate_record_view`.
- [x] T011 Add `src/upgrade_portal/app/routes/org_precheck.py`. Register `org_precheck` in `BLUEPRINT_NAMES` of `factory.py`.

## Phase 4. The pages and the script

- [x] T012 Add the card and the gate to `org_confirm.html`.
- [x] T013 Add the card to `org_progress.html`.
- [x] T014 Add `initOrgPrecheckCard` to `portal.js`, and call it from `initPortal`.

## Phase 5. The existing tests

- [x] T015 Add a stand-in adopter to the four contract files that start a multi-site upgrade.
- [x] T016 Change `stand_in_capture_runner` to store a verified document for a pre-check with no run at the second site.
- [x] T017 Add `tests/e2e/upgrade_portal/org_precheck_steps.py`. Call it in each multi-site journey that starts an upgrade.

## Phase 6. The browser journey

- [x] T018 Write `tests/e2e/upgrade_portal/test_org_missing_precheck_journey.py`.
- [x] T019 Take a screenshot before the capture, after the capture, and on the progress page. Read each screenshot.
- [x] T020 Run the complete browser suite of the upgrade portal.

## Phase 7. The gates and the merge

- [x] T021 Measure the store read with and without the projection on the live store. Record both numbers.
- [x] T022 Run py_compile, ruff, black, mypy, bandit, radon, vulture, pydocstyle, interrogate, and the STE linter.
- [x] T023 Add `changelog.d/issue-3243-multisite-precheck.md`.
- [x] T024 Open the pull request. Wait for each check and CodeQL. Merge with a squash.
