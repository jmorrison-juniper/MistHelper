# Feature Specification: Preserve CSV Carriage Returns

**Feature Branch**: `jmorrison-juniper-csv-carriage-return-preservation`

**Created**: 2026-11-15

**Status**: Draft

**Input**: Issue #4776 reports that CSV multiline escaping discards carriage returns.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preserve exported text (Priority: P1)

An operator exports text with carriage returns and can distinguish each return in the CSV output.

**Why this priority**: Lost characters change the meaning of exported data.

**Independent Test**: Export synthetic records and read the CSV cells.

**Acceptance Scenarios**:

1. **Given** a text value with a carriage return, **When** an operator exports CSV, **Then** the cell contains a literal `\r`.
2. **Given** a text value with a carriage return and a line feed, **When** an operator exports CSV, **Then** the cell contains literal `\r\n`.
3. **Given** a normalized record, **When** CSV presentation is prepared, **Then** its raw values remain unchanged.

### Edge Cases

- A value has only a carriage return, only a line feed, repeated line breaks, or no line break.
- A value has a leading formula marker or a literal backslash.
- Records contain lists and non-string values.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: CSV presentation MUST replace each carriage return with a literal backslash and `r`.
- **FR-002**: CSV presentation MUST preserve the order of carriage returns and line feeds.
- **FR-003**: CSV presentation MUST retain existing line-feed escaping and CSV safety behavior.
- **FR-004**: CSV presentation MUST NOT change the raw normalized values supplied by the caller.
- **FR-005**: Non-CSV output MUST NOT receive newly introduced carriage-return escaping.
- **FR-006**: Existing list conversion and scalar handling MUST remain compatible.

### Key Entities

- **Normalized record**: A data record before output-specific presentation.
- **CSV cell**: The presentation of a record field in a CSV file.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All tested carriage returns appear as literal `\r` in the corresponding CSV cells.
- **SC-002**: All tested normalized records retain their original values after CSV export.
- **SC-003**: All tested non-CSV outputs retain their original carriage returns.

## Assumptions

- Existing shared line-feed escaping remains in use, including before backend selection.
- This change does not alter logging or the held hardware report.
