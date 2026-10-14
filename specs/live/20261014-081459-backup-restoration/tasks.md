# Tasks: Backup restoration

**Input**: [Specification](spec.md), [plan](plan.md), and design records under `evidence/`.

## Phase 1: Setup

- [x] T001 Select this feature in `.specify/feature.json` after the owner handover.
- [x] T002 Add the schema validation dependency in `pyproject.toml` and `requirements.txt`.

## Phase 2: Foundation

- [x] T003 Move the private backup implementation into `src/operations/execution/firmware_policy/recovery/backup.py` and update every import.
- [x] T004 Preserve private output denial in `web_portal/services/data_browser.py` and `web_portal/services/output_scan.py`.

## Phase 3: User Story 1

**Goal**: Produce safe, complete, cloud-bound previews without writes.

**Independent test**: Hostile and valid fixture bundles exercise parsing, schema validation, ownership, selection, and sanitized effects.

- [x] T005 [US1] Test hostile private bundles in `tests/unit/firmware_policy/recovery/test_bundle.py` and Windows ACL decisions in `tests/unit/firmware_policy/recovery/test_windows_access.py`.
- [x] T006 [US1] Implement bounded private bundle validation in `src/operations/execution/firmware_policy/recovery/bundle.py`.
- [x] T007 [US1] Test exact writable projection and unsupported deletion in `tests/unit/firmware_policy/recovery/test_schema.py`.
- [x] T008 [US1] Implement local schema validation in `src/operations/execution/firmware_policy/recovery/schema.py`.
- [x] T009 [US1] Implement cloud binding, membership, scope dependencies, and sanitized previews in `src/operations/execution/firmware_policy/recovery/workflow.py`.

## Phase 4: User Story 2

**Goal**: Restore only after confirmation and complete verified recovery coverage.

**Independent test**: Mocked SDK request evidence proves ordered writes, saved-state checks, and first-failure stopping.

- [x] T010 [US2] Add recovery, freshness, cancellation, and partial-result tests in `tests/integration/firmware_policy/recovery/test_restore_workflow.py`.
- [x] T011 [US2] Implement guarded application in `src/operations/execution/firmware_policy/recovery/workflow.py`.
- [x] T012 [US2] Implement CLI choices and exact confirmation in `src/operations/execution/firmware_policy/recovery/cli.py`.
- [x] T013 [US2] Register unused destructive menu 306 in `MistHelper.py` and `src/foundation/support/utils/operation_registry.py`.
- [x] T014 [US2] Prove settings-only SDK requests, HTTP failure redaction, SDK console privacy, and one-attempt writes in `tests/contract/firmware_policy/recovery/test_sdk.py`.

## Phase 5: User Story 3

**Goal**: Provide the protected graphical flow with the same guards.

**Independent test**: Chromium completes selection, preview, typed confirmation, completion, and failure reporting.

- [x] T015 [US3] Add protected restore routes and controls under `web_portal/routes/firmware_policy/restore/`.
- [x] T016 [US3] Connect the menu link in `web_portal/templates/operations.html` and `tests/support/data_preview_harness.py`.
- [x] T017 [US3] Add protected API and Chromium tests in `tests/e2e/web_portal/firmware_restore/`.

## Phase 6: Documentation and acceptance

- [x] T018 Update menu counts and generated references in `README.md`, `.github/copilot-instructions.md`, and `documentation/`.
- [x] T019 Add `changelog.d/issue-4218-backup-restoration.md` and the operator restoration guide.
- [x] T020 Run relevant local gates and repair feature failures. Record acceptance mapping in `evidence/analysis.md`.
- [ ] T021 Analyze specification, plan, and tasks. Commit and run the clean committed-test quality procedure.
- [ ] T022 Create the templated pull request, wait for all checks and CodeQL, and squash merge when green.
- [ ] T023 Send the merged revision and verified evidence to the parent for persistent-runtime deployment.

## Dependencies

T001 and T002 precede foundation work.
T003 precedes recovery implementation.
US1 precedes US2. US2 precedes US3 application.
Documentation and acceptance require all three stories.
T022 requires T020 and T021. T023 requires T022.

## Parallel opportunities

Bundle tests and schema tests use separate files.
CLI and graphical presentation can proceed independently after the shared workflow.
Do not parallelize shared menu or registry edits.

## Implementation strategy

First prove safe preview. Then prove guarded restoration. Finally connect both interfaces and execute acceptance tests.
No partial story is the final delivery.

## Hooks

Optional before-task and after-task commit hooks are deferred.
Disabled companion hooks do not run.
Safe explicit artifact paths replace unavailable PowerShell setup commands.
