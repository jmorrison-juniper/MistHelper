# Tasks: Organization Auto-Upgrade Policy

**Input**: [plan.md](plan.md), [spec.md](spec.md), and `design/`.

**Tests**: The constitution and feature specification require mocked tests.

**Organization**: Tasks follow the three user stories. Do not use live Mist credentials.

## Phase 1: Setup

- [x] T001 Verify the worktree dependencies from `requirements.txt` and `requirements-dev.txt`.
- [x] T002 Establish the bounded package at `src/operations/execution/firmware_policy/__init__.py`.

## Phase 2: Foundation

- [x] T003 Add validated settings and version reads in `src/operations/execution/firmware_policy/sdk.py`. Identifiers must be valid UUID strings.
- [x] T004 Add settings-body planning in `src/operations/execution/firmware_policy/changes.py`. Preserve every unrelated nested sibling.

## Phase 3: User Story 1 - Organization Standards (P1)

**Goal**: Save selected organization policies by model with AP-only schedules.

**Independent test**: Assert exact settings bodies and verified model values for each device type.

- [x] T005 [P] [US1] Add model-map, enabled-state, and schedule cases in `tests/unit/firmware_policy/test_changes.py`.
- [x] T006 [US1] Implement model/version selection in `src/operations/execution/firmware_policy/cli.py`. Version values must match available versions.
- [x] T007 [US1] Add organization settings write and read-back verification in `src/operations/execution/firmware_policy/workflow.py`.
- [x] T008 [US1] Reuse menu 168's MSP selectors in `src/operations/execution/firmware_policy/cli.py`.

## Phase 4: User Story 2 - Site Inheritance (P1)

**Goal**: Remove every supported local site override after organization verification.

**Independent test**: Assert absent local policies and unchanged unrelated settings after settings replacement.

- [x] T009 [P] [US2] Add removal and sibling-preservation cases in `tests/contract/firmware_policy/test_settings_contract.py`.
- [x] T010 [US2] Implement site read, removal, and verification in `src/operations/execution/firmware_policy/workflow.py`.
- [x] T011 [US2] Report unchanged, completed, failed, and remaining sites in `src/operations/execution/firmware_policy/cli.py`.

## Phase 5: User Story 3 - Safe Preview (P1)

**Goal**: Show the full change and require typed confirmation without sending firmware requests.

**Independent test**: Dry run, cancel, EOF, malformed reads, HTTP 4xx/5xx, and partial failure never produce false success.

- [x] T012 [P] [US3] Add mocked end-to-end tests in `tests/integration/firmware_policy/test_workflow.py`.
- [x] T013 [US3] Add preview, dry run, `CONFIGURE`, and cancellation in `src/operations/execution/firmware_policy/cli.py`.
- [x] T014 [US3] Register destructive menu 305 in `MistHelper.py` and `src/foundation/support/utils/operation_registry.py`.

## Phase 6: Cross-Cutting Validation

- [x] T015 Update `README.md`, `.github/copilot-instructions.md`, `documentation/diagrams/operations/operations-reference.md`, and generated menu references.
- [x] T016 Add `documentation/org-auto-upgrade-policy.md` and `changelog.d/issue-4217-org-auto-upgrade-settings.md`.
- [x] T017 Run applicable local gates and specification analysis against `src/operations/execution/firmware_policy/` and the changed tests.
- [x] T018 Add full settings backups and the pre-write verification gate in `src/operations/execution/firmware_policy/backup.py` and `workflow.py`.
- [x] T019 Add backup corruption and failure cases in `tests/unit/firmware_policy/test_backup.py` and `tests/integration/firmware_policy/test_workflow.py`.
- [x] T020 Add protected dynamic preview and apply routes in `web_portal/routes/firmware_policy/__init__.py`.
- [x] T021 Add the graphical controls in `web_portal/routes/firmware_policy/templates/firmware_policy.html` and `web_portal/static/js/firmware-policy.js`.
- [x] T022 Block backup listing and download in `web_portal/services/data_browser.py` and backup discovery in `web_portal/services/output_scan.py`.
- [x] T023 Add browser and route flows in `tests/e2e/web_portal/test_firmware_policy.py`.

## Dependencies

T001 and T002 precede T003 and T004.
Foundation tasks precede all user stories.
US1 precedes US2's apply flow. US3 confirms both stories before a write.
T014 requires all three stories. T015 through T017 follow working menu integration.
T018 and T019 must complete before any apply flow. T020 and T021 depend on the shared workflow.
T022 precedes portal publication. T023 and T017 validate the complete expanded scope.

## Parallel Examples

US1 model-map tests and US2 settings-contract tests can use different files after the foundation exists.
US3 mocked integration tests and the operator guide can use different files after the public CLI contract exists.

## Implementation Strategy

First prove payload planning and SDK boundaries. Then implement verified writes, followed by selection and preview.
Finish all three stories before publishing the operation.
Keep every test offline. Track merge and container synchronization separately after local validation.
