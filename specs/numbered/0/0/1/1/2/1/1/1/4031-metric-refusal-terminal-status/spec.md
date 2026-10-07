# Feature Specification: Metric Refusals Must Fail Menus 74 and 76

**Feature Branch**: `jmorrison-jnpr-fix/4031-partial-metric-failure`

**Created**: 2026-10-07

**Status**: Draft

**Input**: Issue #4031: Menus 74 and 76 report Complete after repeated upstream HTTP 400 responses.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report refused metrics as a failed operation (Priority: P1)

As a network operator, I need Menus 74 and 76 to report a failed operation when
Mist refuses metric requests. I must not receive a Complete status after
repeated upstream HTTP 400 responses.

**Why this priority**: A false Complete status hides upstream failure and
causes operators to trust an incomplete metric export.

**Independent Test**: Run each menu with successful metric responses followed by
repeated HTTP 400 responses. Verify that the export keeps successful rows and
the existing handled-error log contract causes the terminal status to be Failed.

**Acceptance Scenarios**:

1. **Given** Menu 74 receives valid rows for some site metrics and HTTP 400
   responses for other site metrics, **When** the export finishes, **Then** it
   writes every successful row, records each refused metric, and emits the
   existing handled-error marker so the operation is not reported Complete.
2. **Given** Menu 76 receives valid rows for some device metrics and HTTP 400
   responses for other device metrics, **When** the export finishes, **Then** it
   writes every successful row, records each refused metric, and emits the
   existing handled-error marker so the operation is not reported Complete.
3. **Given** a metric request is refused, **When** the batch continues, **Then**
   the refused error body does not become an export row and later metrics still
   run.

### User Story 2 - Preserve successful and non-refused behavior (Priority: P2)

As a network operator, I need valid metric responses to retain their current
export behavior while refused responses change only the terminal outcome.

**Why this priority**: Partial results remain useful, and the repair must not
discard data that Mist returned successfully.

**Independent Test**: Replay a mixed response set and a fully successful
response set through the focused site and device metric tests. Compare exported
rows, counts, and success messages.

**Acceptance Scenarios**:

1. **Given** all requested metrics return valid non-empty data, **When** the
   export finishes, **Then** all rows, counts, and successful completion behavior
   remain unchanged.
2. **Given** a mixed response set contains successful, empty, and refused
   responses, **When** the export finishes, **Then** successful non-empty rows
   remain, empty responses remain excluded, and refused responses remain
   excluded.
3. **Given** no metric request is refused, **When** the export finishes, **Then**
   the existing success path does not emit a refusal failure marker.

### Edge Cases

- A single refused metric still changes the terminal outcome.
- Repeated HTTP 400 responses record all refused metrics without stopping the
  remaining requests.
- A refused response with a missing, non-text, or very long error detail keeps
  the existing refusal report behavior.
- A transport exception remains distinct from an HTTP refusal and keeps its
  existing per-metric behavior.
- A batch with only refused responses writes the existing empty export form,
  reports the refusals, and does not report Complete.
- A cancelled prompt and an empty metric list keep their current behavior.
- Menu 74 and Menu 76 use their existing site and device scope labels.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Menu 74 MUST continue each metric request after an upstream HTTP
  400 or other refusal response.
- **FR-002**: Menu 76 MUST continue each metric request after an upstream HTTP
  400 or other refusal response.
- **FR-003**: A refused metric response MUST NOT become an exported row.
- **FR-004**: Every valid non-empty metric response MUST remain an exported row,
  even when other metrics in the same batch are refused.
- **FR-005**: The site metric operation MUST count only valid non-empty site
  metric rows as retrieved.
- **FR-006**: The device metric operation MUST count only valid non-empty device
  metric rows as retrieved.
- **FR-007**: Each refused metric MUST remain available to the existing
  `MetricRefusalLog` report with its metric name, status, and reason.
- **FR-008**: When one or more metric requests are refused, each independent
  metric operation MUST emit the existing handled-error log marker before the
  operation ends.
- **FR-009**: The refused request count and handled-error marker MUST affect the
  existing terminal outcome so Menus 74 and 76 do not report Complete after
  refused requests.
- **FR-010**: A batch with no refused requests MUST retain its existing terminal
  success behavior.
- **FR-011**: The focused site metric tests MUST cover mixed successful and
  refused responses, repeated refusals, preserved successful rows, refusal
  reporting, and the no-refusal success path.
- **FR-012**: The focused device metric tests MUST cover mixed successful and
  refused responses, repeated refusals, preserved successful rows, refusal
  reporting, and the no-refusal success path.
- **FR-013**: The implementation scope MUST be limited to
  `src/operations/exporting/export/site_insights/site_metric_operation.py`,
  `src/operations/exporting/export/site_insights/device_metric_operation.py`,
  `tests/unit/export/site_insights/test_site_insight_path.py`,
  `tests/unit/export/site_insights/test_device_metric_refusals.py`, and
  the issue #4031 changelog fragment.
- **FR-014**: The implementation MUST NOT edit
  `web_portal/services/operation.py`, the shared refusal helper, or unrelated
  operation and test files.
- **FR-015**: The implementation MUST add a changelog fragment for issue
  #4031. The fragment is part of the later implementation work, not this
  specification artifact.
- **FR-016**: This feature specification MUST NOT implement product code.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100 percent of focused Menu 74 mixed-response tests, every
  successful metric row is exported and every refused metric is excluded.
- **SC-002**: In 100 percent of focused Menu 76 mixed-response tests, every
  successful metric row is exported and every refused metric is excluded.
- **SC-003**: In 100 percent of focused Menu 74 and Menu 76 tests with one or
  more refusals, the existing handled-error log contract produces a non-Complete
  terminal outcome.
- **SC-004**: In 100 percent of focused no-refusal tests, existing successful
  counts, rows, and terminal success behavior remain unchanged.
- **SC-005**: Repeated refusal tests prove that all refused requests are counted
  and reported while later metric requests still execute.
- **SC-006**: The focused site and device test modules pass without edits to
  `web_portal/services/operation.py`.

## Assumptions

- The existing handled-error log contract remains the terminal outcome boundary
  for these menus during this feature.
- HTTP status values at or above 400 use the existing refusal classification.
- Mist returns successful metric payloads and refusal responses through the
  existing response shape.
- The existing export writer continues to accept partial row sets and empty
  result sets.
- The implementation can use the existing focused test modules without adding
  a new shared test fixture.

## Dependencies

- **Existing handled-error log contract**: The portal reads the established
  operator log marker to determine whether the operation failed.
- **Existing refusal report**: The independent metric files already record and
  report refused metric requests.
- **Issue #4031 changelog fragment**: The implementation must document the
  corrected terminal outcome.

## Out of Scope

- Changes to `web_portal/services/operation.py`.
- Replacement of the handled-error log contract with a new typed outcome API.
- Changes to the shared `metric_refusals.py` helper.
- Changes to metric endpoint selection, response parsing, export formats, or
  successful row transformation.
- New portal controls, broad operation refactors, or unrelated metric tests.
