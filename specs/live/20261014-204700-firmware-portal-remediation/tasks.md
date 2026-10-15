# Tasks: Firmware portal remediation

## Phase 1: Setup

- [x] T001 Inspect issue, ownership, and active feature pointer in `.specify/feature.json`.
- [x] T002 Write specification and design in `specs/live/20261014-204700-firmware-portal-remediation/`.
- [x] T003 Bootstrap the missing environment with `scripts/bootstrap_worktree.py`.

## Phase 2: Foundation

- [x] T004 Separate verified preparation and confirmed application in `src/operations/execution/firmware_policy/workflow.py`.
- [x] T005 Connect request admission and sanitized progress in `src/operations/execution/firmware_policy/sdk.py`.
- [x] T006 Add private, session-owned pollable jobs in `web_portal/routes/firmware_policy/`.

## Phase 3: Policy workflow

**Goal**: Configure settings through the integrated workspace after verified backups.
**Independent test**: Fixture browser journey and exact settings request evidence.

- [x] T007 [P] [US1] Integrate dedicated category rows in `web_portal/routes/operations.py` and workspace selection in `web_portal/static/js/operations.js`.
- [x] T008 [P] [US1] Replace raw output and dynamic model controls in `web_portal/static/js/firmware-policy.js`.
- [x] T009 [US1] Resolve organization names and pre-confirmation backup jobs in `web_portal/routes/firmware_policy/__init__.py`.
- [x] T010 [US1] Test numerical versions, defaults, layout, and confirmation sequence in `tests/e2e/web_portal/test_firmware_policy.py`.

## Phase 4: Restoration workflow

**Goal**: Restore large complete private bundles without arbitrary aggregate limits.
**Independent test**: More than 4,000 sites and a bundle above 17,402,805 bytes.

- [x] T011 [P] [US2] Stream and validate legacy records in `src/operations/execution/firmware_policy/recovery/bundle.py`.
- [x] T012 [US2] Preserve complete recovery and ordered freshness checks in `src/operations/execution/firmware_policy/recovery/workflow.py`.
- [x] T013 [US2] Integrate restored record choices, status, and confirmation in `web_portal/routes/firmware_policy/restore/templates/firmware_restore.html`.
- [x] T014 [US2] Test large, tampered, partial, private, and uncertain outcomes in `tests/integration/firmware_policy/recovery/`.

## Phase 5: Long-run visibility

**Goal**: Keep safe progress readable through quota waits and process interruption.
**Independent test**: Simulated waits above ten minutes, restart state, and duplicate submissions.

- [x] T015 [US3] Persist sanitized job progress and reject duplicate consumption in `web_portal/routes/firmware_policy/`.
- [x] T016 [US3] Test ownership, waiting, restart, complete call counts, and partial outcomes in `tests/unit/firmware_policy/` and `tests/e2e/web_portal/`.
- [x] T017 [US3] Capture fixture screenshots and snapshots beneath `specs/live/20261014-204700-firmware-portal-remediation/evidence/`.

## Phase 6: Completion

- [x] T018 Update `documentation/org-auto-upgrade-policy.md`, `documentation/backup-restoration.md`, related wiki sections, and narrow `README.md` links.
- [x] T019 Add `changelog.d/issue-4227-firmware-portal.md`.
- [x] T020 Run relevant gates and record exact results in `specs/live/20261014-204700-firmware-portal-remediation/analysis.md`.
- [x] T021 Complete acceptance mapping and Spec Kit analysis in `specs/live/20261014-204700-firmware-portal-remediation/analysis.md`.
- [x] T022 Commit milestones, create the template-based pull request, and inspect final CI artifacts without merging.

## Dependencies

T004 and T005 precede T009 and T012. T006 precedes T009 and T015.
T007 and T008 can proceed beside domain work.
T011 precedes T014. Browser evidence follows route and UI integration.
All stories precede completion gates and the pull request.

## Parallel execution

Domain work owns only the firmware policy source package and non-browser tests.
Portal job work owns only firmware policy Python routes and job tests.
Workspace UI and documentation work proceed independently in this session.

## Implementation strategy

Preserve the full requested scope. First establish safety and job contracts.
Then integrate both UI workflows, run fixture acceptance, and collect sanitized evidence.
The parent performs connected acceptance. The user confirmed Morrison House as the intended live scope.
This implementation session performs only fixture changes and never accesses the production volume.

## User-directed firmware-only revision

- [x] T023 [US2] Revise `src/operations/execution/firmware_policy/recovery/schema.py` and workflow readback for FR-017 through FR-020.
- [x] T024 [US2] Update `firmware_restore.html`, `firmware-policy.js`, CLI wording, operator docs, wiki, and `README.md`.
- [x] T025 [US2] Test all policy classes, absence, sibling preservation, malformed content, and scale in the existing `tests/unit/firmware_policy/`, `tests/integration/firmware_policy/`, and `tests/e2e/web_portal/` suites.
- [x] T026 Run revised gates and analysis, capture fixture evidence in `evidence/after-restore.png`, and provide a committed archive with the settings-free validator.
- [x] T027 Record parent connected acceptance and final CI inspection in `acceptance.md` and the draft pull request without merging or deployment.
- [x] T028 [US3] Preserve the prepared form and saved job during delayed initialization in `firmware-policy.js`, with waiting and ready reload tests.

T023 precedes T025. T024 can proceed beside T023.
T026 follows T023 through T025. T027 follows the candidate handoff.
The user approved firmware-policy-only restoration instead of complete settings restoration.
