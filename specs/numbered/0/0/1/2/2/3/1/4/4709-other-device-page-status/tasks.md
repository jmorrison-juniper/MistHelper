# Tasks: Other-device event page status

**Input**: [Specification](spec.md), [plan](plan.md), and records under `design/`.

## Phase 1: Setup

- [x] T001 Preserve #1794 artifacts and inspect shared helpers in `design/research.md`. (delivered: design/research.md)

## Phase 2: Foundational

- [x] T002 Extend real SDK response fixtures in `tests/unit/export/test_site_other_device_events_exporter.py`. (delivered: tests/unit/export/test_site_other_device_events_exporter.py)

## Phase 3: User Story 1 - Reject incomplete exports

**Goal**: Stop failed pages without writing partial records.

**Independent Test**: Initial 403, initial 503, and later empty-body 503 never write or report completion.

- [x] T003 [US1] Prove failures before repair in `tests/unit/export/test_site_other_device_events_exporter.py`. (delivered: tests/unit/export/test_site_other_device_events_exporter.py)
- [x] T004 [US1] Validate every page in `src/operations/exporting/export/site_other_device_events_exporter.py`. (delivered: src/operations/exporting/export/site_other_device_events_exporter.py)

## Phase 4: User Story 2 - Preserve complete results

**Goal**: Preserve valid results and local error boundaries.

**Independent Test**: Empty, single-page, and multiple-page results preserve exact output behavior.

- [x] T005 [US2] Verify complete results and #1794 boundaries in `tests/unit/export/test_site_other_device_events_exporter.py`. (delivered: tests/unit/export/test_site_other_device_events_exporter.py)

## Phase 5: Polish

- [x] T006 Add `changelog.d/issue-4709-other-device-page-status.md`. (delivered: changelog.d/issue-4709-other-device-page-status.md)
- [x] T007 Record exact validation and consistency evidence in `analysis.md`. (delivered: analysis.md)
- [x] T008 [US1] Prove and reject repeated cursors, invalid cursors, and malformed rows in `tests/unit/export/test_site_other_device_events_exporter.py` and `src/operations/exporting/export/site_other_device_events_exporter.py`.
- [x] T009 [US2] Prove and correct empty-string completion and local collection propagation in `tests/unit/export/test_site_other_device_events_exporter.py` and `src/operations/exporting/export/site_other_device_events_exporter.py`.
- [x] T010 [US1] Prove and reject contradictory JSON totals and malformed pagination headers in `tests/unit/export/test_site_other_device_events_exporter.py` and `src/operations/exporting/export/site_other_device_events_exporter.py`.
- [x] T011 [US1] Prove and correct a later absent total, empty present headers, and oversized counts in `tests/unit/export/test_site_other_device_events_exporter.py` and `src/operations/exporting/export/site_other_device_events_exporter.py`.
- [x] T012 [US1] Prove and correct cursor destination safety in `tests/unit/export/test_site_other_device_events_exporter.py` and `src/operations/exporting/export/site_other_device_events_exporter.py`.

## Dependencies and execution

T001 precedes T002. T002 precedes T003. T003 precedes T004.
T004 precedes T005. T005 precedes T006 and T007.
Both stories share the reserved source and test, so parallel edits are unsafe.
All nine tasks use the checklist format. Implement failure safety before validating complete results.
T008 follows T007 because the coordinator added cursor safety after the first local repair commit.
Update the feature evidence after T008.
T009 follows T008 after independent verification corrected the cursor contract and identified a local exception boundary defect.
T010 follows T009 after independent verification found incomplete terminal pages with present metadata.
T011 follows T010 after independent verification found three metadata boundary defects.
T012 follows T011 after independent verification found a cursor that changed the request host.
