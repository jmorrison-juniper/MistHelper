# Tasks: Reject failed beacon responses

**Input**: [Specification](spec.md), [plan](plan.md), and supporting records under `design/`.

## Phase 1: Setup

- [x] T001 Inspect the SDK contract and current main implementation. Record findings in `design/research.md`. (delivered: design/research.md)

## Phase 2: Foundational

- [x] T002 Define preserved behavior and the failure boundary in `design/contracts/beacon-response.md`. (delivered: design/contracts/beacon-response.md)

## Phase 3: User Story 1 - Report failed requests

**Goal**: An error body cannot become an export row.
**Independent test**: Returned HTTP 404, 503, and redirect responses produce a failure message and no export.

- [x] T003 [US1] Add returned-status regression cases in `tests/unit/export/test_site_client_exporter.py`. Confirm failure before the repair. (delivered: tests/unit/export/test_site_client_exporter.py)
- [x] T004 [US1] Reject non-2xx integer statuses before normalization in `src/operations/exporting/export/site_client_exporter.py`. (delivered: src/operations/exporting/export/site_client_exporter.py)

## Phase 4: User Story 2 - Preserve success and retries

**Goal**: Keep valid output and bounded adaptive retries.
**Independent test**: Successful responses write exact expected rows. Returned rate limits use the existing delay and limit.

- [x] T005 [US2] Add returned-success, rate-limit recovery, and exhaustion cases in `tests/unit/export/test_site_client_exporter.py`. (delivered: tests/unit/export/test_site_client_exporter.py)

## Phase 5: Completion

- [x] T006 [P] Document the repair in `changelog.d/issue-4028-menu-209-http-error-export.md`. (delivered: changelog.d/issue-4028-menu-209-http-error-export.md)
- [x] T007 Run focused tests and applicable local gates. Record evidence in `analysis.md`. (delivered: analysis.md)
- [x] T008 Compare `spec.md`, `plan.md`, and `tasks.md` with the delivered change in `analysis.md`. (delivered: analysis.md)

## Dependencies

T002 depends on T001. T003 depends on T002. T004 depends on T003.
T005 depends on T004. T007 depends on T004, T005, and T006.
T008 depends on T007.

## Parallel execution

T006 can run independently after the contract is defined.
Both stories edit the same test module, so execute their tests sequentially.

## Implementation strategy

First prove the reported error-row defect. Then add the status check.
Finally verify preserved behavior, document the repair, and commit the verified result.
