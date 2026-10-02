---
description: "Bounded reporting repair for issue #3329"
---

# Tasks: Rejected Child Counts

**Input**: [spec.md](spec.md) and [plan.md](plan.md).

**Tests**: Write the proof first. Reproduce the count defect before the product edit.

## Phase 1: Setup

- [x] T001 Read the complete live issue, all comments, and all paginated open pull request file lists. Claim the exact reservation. (delivered: specs/3329-rejected-child-counts/plan.md)
- [x] T002 Generate the feature-only spec, plan, and tasks with the current templates. Record unavailable hooks honestly. (delivered: specs/3329-rejected-child-counts/spec.md)
- [x] T003 Recover only the owned ignored environment after the real bootstrap failure. Confirm Python 3.13 and Chromium. (delivered: specs/3329-rejected-child-counts/plan.md)

## Phase 2: Foundational Proof

- [x] T004 [US1] Add helper counts, uncertainty controls, native and nested counts, completed proof, and negative assertions. (delivered: tests/unit/upgrade_portal/test_issue_3329_rejected_child_counts.py)
- [x] T005 [US1] Add actual status route and rendered page contracts with owned durable records. (delivered: tests/contract/upgrade_portal/test_issue_3329_rejected_child_counts_routes.py)
- [x] T006 [US3] Add Chromium proof of the shipped page and real status poll. (delivered: tests/e2e/upgrade_portal/test_issue_3329_rejected_child_counts_journey.py)
- [x] T007 Reproduce red through all three boundaries. The failures are count assertions, not setup failures. (delivered: specs/3329-rejected-child-counts/plan.md)

## Phase 3: User Story 1 - Known Failed Targets

- [x] T008 Repair only `_aggregate_child_counts` and its approved public import. (delivered: src/upgrade_portal/app/routes/org_upgrade.py)
- [x] T009 Prove known refused one-target and not_submitted two-target counts in both reporting surfaces. (delivered: tests/contract/upgrade_portal/test_issue_3329_rejected_child_counts_routes.py)
- [x] T010 Prove mixed counts, empty targets, multiple sites and families, and no double counting. (delivered: tests/unit/upgrade_portal/test_issue_3329_rejected_child_counts.py)

## Phase 4: User Story 2 - Genuine Outcomes and Uncertainty

- [x] T011 Preserve native active failures, nested AP arrays, and proven completed counts. (delivered: tests/unit/upgrade_portal/test_issue_3329_rejected_child_counts.py)
- [x] T012 Preserve unknown, submission_unknown, read_unknown, waiting, active, and cancelled controls. (delivered: tests/contract/upgrade_portal/test_issue_3329_rejected_child_counts_routes.py)
- [x] T013 Run unchanged aggregate model, child outcome, retry hold, and cancellation contracts under relevant CI collection. (delivered: specs/3329-rejected-child-counts/plan.md)

## Phase 5: User Story 3 - Shipped Browser Refresh

- [x] T014 Assert summary and matching child Failed values before and after real browser polls. (delivered: tests/e2e/upgrade_portal/test_issue_3329_rejected_child_counts_journey.py)
- [x] T015 Preserve exact statuses, reasons, cancellation text, device content, and row order. (delivered: tests/e2e/upgrade_portal/test_issue_3329_rejected_child_counts_journey.py)
- [x] T016 Run unchanged cancellation browser journeys from accepted pull requests #3630 and #3621 under full E2E collection semantics. (delivered: specs/3329-rejected-child-counts/plan.md)
- [x] T017 Count positive records, rows, polls, and zero forbidden callbacks. Verify owned server and resource cleanup. (delivered: tests/e2e/upgrade_portal/test_issue_3329_rejected_child_counts_journey.py)

## Phase 6: Local Commit and Handoff

- [x] T018 Measure all 19 statements and four branches. Preserve 234 unrelated source AST nodes. (delivered: specs/3329-rejected-child-counts/plan.md)
- [x] T019 Run configured local checks without suppression. Record the normal audit failure, approved substitute, and partial STE limitation. (delivered: specs/3329-rejected-child-counts/plan.md)
- [x] T020 Run required input preflight and the configured test-quality gate. Explicitly measure all three new files with `--include-mist-api`. (delivered: specs/3329-rejected-child-counts/plan.md)
- [x] T021 Add the unique release note and exact local evidence. (delivered: changelog.d/issue-3329-rejected-child-counts.md)
- [x] T022 Preserve the complete current 23-item pull request template in the offline draft. Record unavailable and remote checks honestly. (delivered: specs/3329-rejected-child-counts/plan.md)
- [ ] T023 Create one clean validated local commit with `Part of #3329` and the exact Copilot App co-author trailer. Never amend.
- [ ] T024 Run committed-scope test quality against the intended fetched base. Verify full SHA, clean state, and cleanup.
- [ ] T025 Send the unpublished local handoff to the parent. Retain position 41 after #3326.

## Dependencies & Execution Order

T001 through T003 precede test creation.
T004 through T007 precede T008.
T009 through T017 depend on T008.
T018 through T022 depend on the acceptance proof.
T023 requires all applicable local checks to pass.
T024 follows T023 with clean relevant content.
T025 follows T024.

## Implementation Strategy

One owner controls the count method and three proof modules.
No production template, JavaScript, CSS, authentication, or firmware policy file changes.
No shared fixture, manifest, configuration, baseline, or exclusion changes.

Publication remains unauthorized until the parent supplies an explicit full verified-main SHA grant.
Do not push, create a pull request, merge, run Actions, or deploy.

T023 through T025 occur after this tracked task list enters the local commit.
Their immutable issue-comment receipt records the actual commit, committed-scope gate, clean state, and handoff.
Do not mark these steps complete before that receipt exists.
Do not create another commit only to change these administrative boxes.
Delivery and issue closure remain unauthorized.
