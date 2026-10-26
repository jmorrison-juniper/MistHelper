# Tasks: Result clipping notice

**Input**: [Specification](spec.md), [plan](plan.md), and supporting records under `design/`.

## Phase 1: Setup

- [x] T001 Check the managed route and write `spec.md` and `plan.md` before implementation. (delivered: spec.md, plan.md)

## Phase 2: Foundational

- [x] T002 Measure current clipping with a failing regression. (delivered: tests/e2e/web_portal/result_truncation_notice/test_notice.py)

## Phase 3: User Story 1

**Goal**: Identify clipped text and provide complete-value access.

**Independent test**: Compare rendered cell widths, open row details, focus Output Files, and verify the download.

- [x] T003 [US1] Add the short control and complete-value browser cases. (delivered: tests/e2e/web_portal/result_truncation_notice/test_notice.py)
- [x] T004 [US1] Implement the notice controller. (delivered: web_portal/static/js/operation_results.js)

## Phase 4: User Story 2

**Goal**: Keep the notice accurate during data and layout changes.

**Independent test**: Change pages, filters, files, order, and width, then reset with pending work.

- [x] T005 [US2] Add lifecycle checks. (delivered: tests/unit/web_portal/result_truncation_notice/test_lifecycle.py)
- [x] T006 [US2] Add layout, paging, and combined-warning cases. (delivered: tests/e2e/web_portal/result_truncation_notice/test_notice.py)
- [x] T007 [US2] Cancel stale work and preserve sort warnings. (delivered: web_portal/static/js/operation_results.js)

## Phase 5: Validation and delivery

- [x] T008 Add the release note. (delivered: changelog.d/issue-3161-result-truncation-notice.md)
- [x] T009 Run relevant regressions and applicable gates. (delivered: analysis.md)
- [x] T010 Verify the explicit file set and `main` base before publication. (delivered: analysis.md)
- [x] T011 Move the new browser files to the user-approved shard namespace and verify collection. (delivered: tests/e2e/web_portal/result_truncation_notice/test_notice.py)

## Dependencies

T001 precedes T002. T002 must prove the defect before T004.
T003 and T005 can proceed independently after T002.
T006 and T007 require T004.
T008 and T009 require both stories. T010 requires completed validation with each limitation recorded.

## Implementation strategy

First prove the current defect, then deliver both stories in one bounded repair.
Do not publish a source change if the defect cannot be reproduced.
After local completion, commit the explicit file set and run the committed test-quality check.
Then push the branch and create the authorized pull request against `main`.
Do not merge or enable automatic merge.
