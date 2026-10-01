# Tasks: Read-only retry evidence

**Input**: Design documents from `specs/2752-read-only-retry-evidence/`.

**Prerequisites**: [plan.md](plan.md) and [spec.md](spec.md).

**Tests**: The specification requires red and green evidence with blocked network and output boundaries.

## Phase 1: Setup

- [x] T001 Check live ownership and every open PR file page before claiming exact paths. (delivered: specs/2752-read-only-retry-evidence/validation.md)
- [x] T002 Write the bounded specification and plan before behavior edits. (delivered: specs/2752-read-only-retry-evidence/spec.md)

## Phase 2: User Stories 1 and 2

- [x] T003 Add native SDK regression cases and measure the unchanged source's missing status evidence. (delivered: tests/unit/api/test_api_data_fetcher_retry_evidence.py)
- [x] T004 Pass the failed response to the existing helper and retain guarded status evidence. (delivered: src/api/api_data_fetcher.py)
- [x] T005 Migrate the existing direct helper assertion without a line-count change. (delivered: tests/unit/api/test_api_data_fetcher.py)

## Phase 3: User Story 3

- [x] T006 Prove unchanged retry behavior, safe diagnostics, adjacent contracts, and changed-region coverage. (delivered: specs/2752-read-only-retry-evidence/validation.md)
- [x] T007 Prove that incorrect first-status evidence fails, then remove the temporary mutation. (delivered: tests/unit/api/test_api_data_fetcher_retry_evidence.py)

## Phase 4: Local Handoff

- [x] T008 Record gate results and capability limits. (delivered: specs/2752-read-only-retry-evidence/validation.md)
- [x] T009 Add the unique release note. (delivered: changelog.d/issue-2752-read-only-retry-evidence.md)
- [x] T010 Prepare the complete offline PR template and the explicit local-commit file manifest. Publication and actual-main verification remain with the parent. (delivered: specs/2752-read-only-retry-evidence/validation.md)

## Dependencies & Execution Order

T001 and T002 precede T003.
T003 precedes T004 and T005.
T004 and T005 precede T006 and T007.
T006 and T007 precede T008 through T010.

## Implementation Strategy

Deliver only this diagnostic slice.
Keep the campaign open and use `Part of #2752`.
Do not publish or run a live operation before the parent's explicit full verified-main SHA grant.
