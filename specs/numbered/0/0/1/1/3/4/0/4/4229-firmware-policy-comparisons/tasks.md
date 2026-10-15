# Tasks: Firmware policy comparisons

## Phase 1: Setup

- [x] T001 Inspect baseline, issue ownership, and open PR overlap in `AGENTS.md` and `.github/copilot-instructions.md`.
- [x] T002 Resolve the app-owned branch hook and create `specs/numbered/0/0/1/1/3/4/0/4/4229-firmware-policy-comparisons/spec.md`.
- [x] T003 Prepare the isolated environment with `scripts/bootstrap_worktree.py`.

## Phase 2: Foundation

- [x] T004 Add schema-checked firmware cells and differences in `web_portal/routes/firmware_policy/restore/policies.py`.
- [x] T005 Preserve named workflow phases through request admission in `web_portal/routes/firmware_policy/jobs/manager.py`.
- [x] T006 Pass maximum supported list limits in `src/operations/execution/firmware_policy/sdk.py`.

## Phase 3: US1 - Examine prepared changes

Independent test: Expand one ready row in each workflow without applying settings.

- [x] T007 [US1] Test projection, presence, normalization, and privacy in `tests/unit/firmware_policy_jobs/comparisons/test_policies.py`.
- [x] T008 [US1] Add read-only private context comparisons in `web_portal/routes/firmware_policy/restore/inspection.py`.
- [x] T009 [US1] Add owner-checked local and remote comparison dispatch in `web_portal/routes/firmware_policy/jobs/manager.py`.
- [x] T010 [US1] Register protected comparison routes in `web_portal/routes/firmware_policy/restore/__init__.py`.
- [x] T011 [US1] Add accessible lazy comparison rows in `web_portal/static/js/firmware-policy.js`.
- [x] T012 [US1] Test both comparisons, proof preservation, and HTTP failures in `tests/integration/firmware_policy/recovery/comparisons/test_inspection.py`.

## Phase 4: US2 - Historical inspection

Independent test: Inspect and compare historical rows with zero backups or writes.

- [x] T013 [US2] Add source-integrity and ownership checks for historical inspection in `web_portal/routes/firmware_policy/restore/inspection.py`.
- [x] T014 [US2] Register explicit historical inspection in `web_portal/routes/firmware_policy/restore/__init__.py`.
- [x] T015 [US2] Add historical controls in `web_portal/routes/firmware_policy/restore/templates/firmware_restore.html`.
- [x] T016 [US2] Add historical viewing and explicit current comparison in `web_portal/static/js/firmware-policy.js`.
- [x] T017 [US2] Test immutability, ownership, and source changes in `tests/integration/firmware_policy/recovery/comparisons/test_inspection.py`.

## Phase 5: US3 - Preparation behavior

Independent test: Hold preparation, reload, fail, retry, and select mixed versions.

- [x] T018 [US3] Lock preparation through ready and uncertain states in `web_portal/static/js/firmware-policy.js`.
- [x] T019 [US3] Label capture, freshness, save, verification, and phase counts in `web_portal/static/js/firmware-policy.js` and both domain `workflow.py` files.
- [x] T020 [US3] Select the highest initial version without replacing manual choices in `web_portal/static/js/firmware-policy.js`.
- [x] T021 [US3] Explain preparation and selection in `web_portal/routes/firmware_policy/templates/firmware_policy.html`.
- [x] T022 [US3] Test phase retention, pagination, and request budgets in `tests/unit/firmware_policy_jobs/comparisons/test_progress.py`.

## Phase 6: Validation and delivery

- [x] T023 Exercise accessible comparisons, 800-pixel geometry, history, locking, retry, reload, and versions in `tests/e2e/web_portal/test_firmware_policy.py`. Retain rooted screenshots and failure traces through `tests/e2e/web_portal/firmware_restore/evidence.py`, `.github/workflows/ci.yml`, and `tests/unit/firmware_policy_jobs/comparisons/test_evidence.py`.
- [x] T024 Update `documentation/org-auto-upgrade-policy.md`, `documentation/backup-restoration.md`, and `changelog.d/issue-4229-firmware-policy-comparisons.md`.
- [x] T025 Run applicable local gates and record exact results in `specs/numbered/0/0/1/1/3/4/0/4/4229-firmware-policy-comparisons/quickstart.md`.
- [x] T026 Analyze requirement coverage across `specs/numbered/0/0/1/1/3/4/0/4/4229-firmware-policy-comparisons/spec.md`, `plan.md`, and `tasks.md`. Report findings in the PR.
- [x] T027 Commit explicit paths, rebase, push, and create a draft with `.github/PULL_REQUEST_TEMPLATE.md`.

## Dependencies

Setup precedes foundation. T004 precedes both inspection stories.
Prepared and historical inspection share projection but not preparation.
Preparation behavior can proceed after phase metadata is available.
Validation covers all three stories before draft delivery.

## Parallel opportunities

SDK paging tests and projection tests use separate files.
Documentation can proceed while synthetic browser validation runs.
Use direct implementation for the shared JavaScript file.

## Implementation strategy

Implement projection first, then prepared inspection, historical inspection,
and preparation controls. Preserve existing application gates throughout.
All 27 tasks use checklist IDs and concrete repository paths.
Story task counts are US1: 6, US2: 5, and US3: 5.
