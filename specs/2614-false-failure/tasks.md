# Tasks: False Failure Reconciliation

**Input**: Design documents from `specs/2614-false-failure/`

**Prerequisites**: `spec.md` and `plan.md`

**Tests**: Required by issue #2614.

## Phase 1: Setup

- [X] T001 Read issue #2614 and add the `in-progress` label. (delivered: GitHub issue)
- [X] T002 Create the isolated worktree `..\MistHelper-2614-false-failure`. (delivered: worktree)
- [X] T003 Verify `mistapi` version `0.64.0`. (delivered: `.venv`)
- [X] T004 Confirm test collection has zero errors. (delivered: pytest collect output)

## Phase 2: Specification

- [X] T005 Create `specs/2614-false-failure/spec.md`. (delivered: specs/2614-false-failure/spec.md)
- [X] T006 Create `specs/2614-false-failure/plan.md`. (delivered: specs/2614-false-failure/plan.md)
- [X] T007 Create `specs/2614-false-failure/tasks.md`. (delivered: specs/2614-false-failure/tasks.md)

## Phase 3: User Story 1 - Repair a proven false failure

**Goal**: A failed timeout run with positive current firmware evidence becomes a
complete run without invented settle times.

**Independent Test**: Run the issue #2614 regression test.

- [X] T008 [US1] Add the issue #2614 regression test in `tests/unit/upgrade_portal/test_runs/test_reconciliation.py`. (delivered: tests/unit/upgrade_portal/test_runs/test_reconciliation.py)
- [X] T009 [US1] Extend target evidence fields in `src/upgrade_portal/persistence/actions/models.py`. (delivered: src/upgrade_portal/persistence/actions/models.py)
- [X] T010 [US1] Add failed-timeout repair logic in `src/upgrade_portal/api/run_controls/services/reconciliation.py`. (delivered: src/upgrade_portal/api/run_controls/services/reconciliation.py)
- [X] T011 [US1] Preserve null reboot and settle fields with an explicit note. (delivered: src/upgrade_portal/api/run_controls/services/reconciliation.py)

## Phase 4: User Story 2 - Keep true failures failed

**Goal**: Missing, active, conflicting, or mismatched evidence does not repair a
failed run.

**Independent Test**: Use the same service path with incomplete evidence.

- [X] T012 [US2] Require all failed targets to have positive firmware evidence. (delivered: src/upgrade_portal/api/run_controls/services/reconciliation.py)
- [X] T013 [US2] Keep unknown or refused outcomes when evidence is incomplete. (delivered: src/upgrade_portal/api/run_controls/services/reconciliation.py)

## Phase 5: User Story 3 - Use only running-version evidence

**Goal**: The production evidence reader uses the site statistics endpoint and
the shared running-version rule.

**Independent Test**: Inspect the reader and run local gates.

- [X] T014 [US3] Add `SiteStatsFirmwareEvidenceReader` in `src/upgrade_portal/api/run_controls/routes.py`. (delivered: src/upgrade_portal/api/run_controls/routes.py)
- [X] T015 [US3] Use `RunningFirmwareVersionResolver.index_stats_rows()` for evidence. (delivered: src/upgrade_portal/api/run_controls/routes.py)
- [X] T016 [US3] Show the reconciliation control for the narrow failed-timeout shape. (delivered: src/upgrade_portal/app/routes/upgrade.py)

## Phase 6: Release and validation

- [X] T017 Add `changelog.d/issue-2614-false-failure.md`. (delivered: changelog.d/issue-2614-false-failure.md)
- [X] T018 Run `python -m ruff check .`. (delivered: local gate output)
- [X] T019 Run `python -m black --check .`. (delivered: local gate output)
- [X] T020 Run `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`. (delivered: local gate output)
- [X] T021 Run `python -m pytest tests/unit/upgrade_portal tests/contract/upgrade_portal -q`. (delivered: local gate output)
- [ ] T022 Commit, push, open the pull request, and wait for required checks.

## Dependencies

- T005 through T007 depend on T001 through T004.
- T010 depends on T008 and T009.
- T014 depends on T010.
- T018 through T021 depend on implementation tasks.
- T022 depends on all local gates passing.
