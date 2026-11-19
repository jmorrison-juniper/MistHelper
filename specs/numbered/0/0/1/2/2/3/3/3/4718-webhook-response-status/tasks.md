# Tasks: Webhook response status

**Input**: [Specification](spec.md), [plan](plan.md), and records under `design/`.

## Phase 1: Setup

- [x] T001 Verify issue ownership, the previous commit, and the managed route in `plan.md`. (delivered: plan.md)

## Phase 2: Foundational

- [x] T002 Preserve offline socket, DNS, and SQLite guards in `tests/unit/export/test_org_webhook_deliveries_exporter.py` and the session runner. (delivered: tests/unit/export/test_org_webhook_deliveries_exporter.py)

## Phase 3: User Story 1 - Correct initial response classification

**Goal**: Reject failed or invalid initial responses without false empty results.
**Independent test**: Supply native synthetic responses to both endpoint boundaries.

- [x] T003 [US1] Add rejection and control tests in `tests/unit/export/test_org_webhook_deliveries_exporter.py`. Prove failures against the previous source. (delivered: tests/unit/export/test_org_webhook_deliveries_exporter.py)
- [x] T004 [US1] Validate initial list and delivery statuses in `src/operations/exporting/export/org_webhook_deliveries_exporter.py`. (delivered: src/operations/exporting/export/org_webhook_deliveries_exporter.py)
- [x] T005 [US1] Update successful doubles in `tests/unit/export/test_issue_3188_webhook_id_selection.py` without changing its assertions. (delivered: tests/unit/export/test_issue_3188_webhook_id_selection.py)
- [x] T006 [US1] Run related tests, independent native-response cases, and applicable local gates for the exporter and both tests. (delivered: tests/unit/export/test_org_webhook_deliveries_exporter.py)

## Phase 4: Final evidence

- [x] T007 Add `changelog.d/issue-4718-webhook-response-status.md` and record cross-artifact consistency in `analysis.md`. (delivered: changelog.d/issue-4718-webhook-response-status.md, analysis.md)
- [x] T008 Prepare the local commit and reproducible export procedure in the session `issue4718/export_candidate.py` file. Export final committed bytes and evidence after the commit. (delivered: /Users/jmorrison/.copilot/session-state/02858623-f9db-492d-a9bc-f107f7564a86/files/issue4718/export_candidate.py)

## Dependencies

T001 precedes T002. T002 precedes T003. T003 precedes T004 and T005.
T004 and T005 precede T006. T006 precedes T007. T007 precedes T008.

## Parallel execution

Independent code-quality checks can run together after T004 and T005.
Do not start a competing branch for either reserved test.

## Implementation strategy

Complete the single operator story on the existing integration branch.
Keep both issue commits intact and unpublished.
