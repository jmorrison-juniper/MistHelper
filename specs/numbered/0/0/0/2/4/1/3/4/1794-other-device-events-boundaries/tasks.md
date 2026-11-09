# Tasks: Other-device event failure boundaries

**Input**: [Specification](spec.md), [plan](plan.md), and supporting records under `design/`.

## Phase 1: Setup

- [x] T001 Inspect the installed SDK path and record evidence in `design/research.md`. (delivered: design/research.md)

## Phase 2: Foundational

- [x] T002 Block DNS and sockets and mock dependencies in `tests/unit/export/test_site_other_device_events_exporter.py`. (delivered: tests/unit/export/test_site_other_device_events_exporter.py)

## Phase 3: User Story 1 - Report the correct failure

**Goal**: Preserve local defects and protect exception text.

**Independent test**: Transform and writer failures propagate without cloud error messages.

- [x] T003 [US1] Add failing boundary and privacy cases to `tests/unit/export/test_site_other_device_events_exporter.py`. (delivered: tests/unit/export/test_site_other_device_events_exporter.py)
- [x] T004 [US1] Restrict the handler and sanitize messages in `src/operations/exporting/export/site_other_device_events_exporter.py`. (delivered: src/operations/exporting/export/site_other_device_events_exporter.py)

## Phase 4: User Story 2 - Preserve the menu experience

**Goal**: Preserve normal behavior and external-call fallbacks.

**Independent test**: Real SDK calls use offline HTTP responses and preserve menu results.

- [x] T005 [US2] Add endpoint, pagination, malformed-page, transport, success, empty, and cancellation cases to `tests/unit/export/test_site_other_device_events_exporter.py`. (delivered: tests/unit/export/test_site_other_device_events_exporter.py)

## Phase 5: Polish

- [x] T006 Add the operator change to `changelog.d/issue-1794-other-device-events-boundaries.md`. (delivered: changelog.d/issue-1794-other-device-events-boundaries.md)
- [x] T007 Record exact checks, reproduction results, limitations, and consistency analysis in `analysis.md`. (delivered: analysis.md)

## Dependencies and execution

T001 precedes T002. T002 precedes T003 and T005. T003 precedes T004.
T004 and T005 precede T006 and T007.
Both user stories share one test file, so no parallel edits are safe.
Implement the local defect boundary first, then prove the preserved SDK behavior.
All seven tasks use the checklist format. No optional commit hook is required before these tasks.
