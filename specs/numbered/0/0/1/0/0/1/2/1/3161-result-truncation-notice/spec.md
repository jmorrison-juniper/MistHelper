# Feature Specification: Result clipping notice

**Feature Branch**: `jmorrison-juniper-portal-result-truncation-notice`

**Created**: 2026-10-26

**Status**: Approved for bounded repair

**Input**: Issue #3161 requests a visible notice when the result table clips cell text.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read complete values (Priority: P1)

An operator needs to know when the table hides part of a value.
The operator needs direct access to the complete row and the output files.

**Why this priority**: A shortened value can look complete.

**Independent Test**: Show a long result value and compare its rendered width with its available width.

**Acceptance Scenarios**:

1. **Given** a clipped cell, **When** the table appears, **Then** a visible accessible notice identifies the clipping.
2. **Given** the notice, **When** the operator selects its row-details control, **Then** the existing detail displays the complete value.
3. **Given** the notice, **When** the operator selects Output Files, **Then** the existing output destination receives focus.
4. **Given** short values with no clipping, **When** the table appears, **Then** no clipping notice appears.

### User Story 2 - Keep the notice accurate (Priority: P2)

An operator changes the page, filter, order, file, or available table width.
The notice must describe the current table only.

**Why this priority**: A stale notice misrepresents the current result.

**Independent Test**: Alternate clipped and short results, resize the table, and reset the run.

**Acceptance Scenarios**:

1. **Given** a changed result or layout, **When** clipping changes, **Then** the notice updates without repeated controls.
2. **Given** a sort-limit warning, **When** cells also clip, **Then** both warnings remain visible.
3. **Given** a reset or failed load, **When** pending work completes, **Then** no previous result or notice returns.

### Edge Cases

- Empty results and read errors remove the previous clipping notice.
- An open detail does not count as a clipped data cell.
- Rapid file changes cannot restore an older response.
- A hidden result panel has no visible clipping notice.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Detect actual rendered cell clipping, not text length or row count.
- **FR-002**: Identify hidden text and provide keyboard access to existing row details and Output Files.
- **FR-003**: Preserve the existing sort-limit warning independently of cell clipping.
- **FR-004**: Update after data and layout changes without stale callbacks or duplicate handlers.
- **FR-005**: Preserve all values, pagination, sorting, row details, and downloads.
- **FR-006**: Keep changes within the released result JavaScript and new issue-scoped records and tests.

### Key Entities

- **Result page**: One page of complete values from an existing output file.
- **Clipped cell**: A rendered data cell whose content exceeds its visible area.
- **Notice**: A description of current clipping with complete-value access.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every tested clipped result shows the notice within one second after rendering or layout stabilization.
- **SC-002**: Every tested short control shows no clipping notice.
- **SC-003**: The complete 246-character value remains available in row details and the unchanged download.
- **SC-004**: Thirty records remain available across pages of 25 and five rows.
- **SC-005**: Reset, empty results, and errors leave zero stale notices or callbacks.

## Assumptions

- The historical sample and its 124.69-second timing are unavailable and remain unverified.
- Controlled local CSV results exercise the current renderer without a live Mist request.
- The repair addresses horizontal cell clipping, not missing export records or sorted total counts.
- The managed numeric route replaces the historical flat specification reservation.
- The user approved `tests/e2e/web_portal/result_truncation_notice/` so the existing CI shard collects the new browser tests.
- The current app-managed branch already exists. No branch-creation hook may replace it.
