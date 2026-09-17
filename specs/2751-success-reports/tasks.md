# Tasks: Success Report Audit Slice

**Input**: Design documents from `specs\2751-success-reports\`

**Prerequisites**: `plan.md`, `spec.md`, and `triage.md`

**Tests**: Issue #2751 requires tests.

## Phase 1: Audit Setup

- [x] T001 Read issue #2751, parent issue #1924, and the #1924 inventory. (delivered: `specs\2751-success-reports\triage.md`)
- [x] T002 Read repository instructions and STE guidance. (delivered: `specs\2751-success-reports\plan.md`)
- [x] T003 Create the worktree and verify `mistapi` version 0.64.0. (delivered: pull request #2860)

## Phase 2: Bounded Triage

- [x] T004 Classify each candidate read as a correct announcement, a premature success claim, or a correct completion report. (delivered: `specs\2751-success-reports\triage.md`)
- [x] T005 Select destructive write paths for WAN probes for repair. (delivered: `src\gateway\wan_probe_device_override_manager.py`, `src\refactors\wanprobe_config_manager.py`)
- [x] T006 File follow-up issues for deferred candidate areas. (delivered: issues #2865, #2866, and #2867)

## Phase 3: User Story 1 - Trust destructive write logs

- [x] T007 Reword the local message about the template probe payload from `Updated` to `Prepared`. (delivered: `src\refactors\wanprobe_config_manager.py`)
- [x] T008 Reword the local message about the device probe payload from `Updated` to `Prepared`. (delivered: `src\gateway\wan_probe_device_override_manager.py`)
- [x] T009 Add a template failure test that asserts the old success line is absent. (delivered: `tests\unit\refactors\test_wanprobe_config_manager.py`)
- [x] T010 Add a device failure test that asserts the old success line is absent. (delivered: `tests\unit\gateway\test_wan_probe_override_pipeline.py`)

## Phase 4: Validation and Shipping

- [x] T011 Add the release-note fragment. (delivered: `changelog.d\issue-2751-success-reports.md`)
- [x] T012 Run local gates and record limitations in the pull request body. (delivered: pull request #2860)
- [ ] T013 Update pull request #2860 with final counts, evidence, and deferred issues.
- [ ] T014 Watch required CI checks and add `auto-merge` only if policy permits.
