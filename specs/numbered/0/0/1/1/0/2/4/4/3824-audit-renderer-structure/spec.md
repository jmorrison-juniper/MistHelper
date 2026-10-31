# Feature Specification: Nested Source Package Remediation

**Feature Branch**: `refactor/3824-websocket-catalog-structure`

**Created**: 2026-10-31

**Status**: Draft

**Input**: User description: "Reduce nested source package child counts in bounded slices while preserving public behavior."

## User Scenarios & Testing

### User Story 1 - Generate audit reports (Priority: P1)

An operations engineer generates Mermaid and HTML reports from audit analysis. The report keeps its current content and format after the internal package changes.

**Why this priority**: Operators depend on these reports to review organization changes.

**Independent Test**: Render a representative audit result in both formats and check expected report content and file creation.

**Acceptance Scenarios**:

1. The Mermaid report retains its summary, timeline, changelogs, and rollback details for audit results with timeline, change, and rollback data.
2. The HTML report retains its chart, summary, and change details for audit results with timeline, change, and rollback data.
3. **Given** an empty audit result, **When** the engineer renders either report, **Then** the existing empty-state content remains available.

### User Story 2 - Maintain the audit package (Priority: P2)

A maintainer locates audit rendering code in a bounded package structure without keeping obsolete import paths.

**Why this priority**: A bounded structure makes the code easier to maintain and reduces recorded source-package violations.

**Independent Test**: Measure tracked Python source children and import each new renderer module while confirming that each old renderer path is absent.

**Acceptance Scenarios**:

1. **Given** the audit source package, **When** the structural check measures its renderer packages, **Then** each affected directory has no more than five structural children.
2. A caller uses the new renderer path and calls the public report methods. The caller receives the same report behavior.
3. **Given** a caller imports an obsolete renderer module path, **When** Python resolves that path, **Then** the import fails rather than using a compatibility wrapper.

### User Story 3 - Maintain the WebSocket utility catalog (Priority: P2)

A network operations engineer reads utility names, descriptions, and input hints in the WebSocket portal. The package change keeps each displayed value unchanged.

**Why this priority**: Operators need clear and correct text when they select a WebSocket utility.

**Independent Test**: Run the utility text tests and confirm that the new module path resolves while the old path does not.

**Acceptance Scenarios**:

1. Utility labels, descriptions, and input hints retain their current text.
2. The utility text module resides in the existing utility package, and every affected source file and test uses that path.
3. **Given** a caller imports the old utility text path, **When** Python resolves that path, **Then** the import fails without a compatibility wrapper.

### Edge Cases

- An audit result with no timelines, changes, or rollback diffs keeps the existing empty report behavior.
- A tracked diagnostic script or test that imports a moved module uses the new path.
- The utility text logger and `UtilityText.__module__` use the new module path.
- The source debt count decreases, and the change does not add a new structural violation.

## Requirements

### Functional Requirements

- **FR-001**: The audit report renderer MUST keep its current Mermaid and HTML output behavior.
- **FR-002**: The renderer MUST preserve its current public report methods and test-visible delta helpers.
- **FR-003**: The renderer modules MUST reside in a source hierarchy where each affected directory has no more than five structural children.
- **FR-004**: All active callers and tests MUST use the new module paths.
- **FR-005**: The change MUST remove the old renderer module paths without aliases or compatibility wrappers.
- **FR-006**: The nested source package measurement MUST report fewer violations after the change.
- **FR-007**: WebSocket utility labels, descriptions, and input hints MUST remain unchanged.
- **FR-008**: All active callers and tests MUST use the new utility text module path without retaining the old path.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The audit source package and each new renderer directory contain no more than five structural children.
- **SC-002**: The repository-wide nested source measure reports 33 violations and 236 total excess, down from 34 violations and 237 excess.
- **SC-003**: The audit renderer tests pass for Mermaid output, HTML output, delta behavior, and empty results.
- **SC-004**: Each source directory affected by the WebSocket utility text move has no more than five structural children.
- **SC-005**: The utility text tests confirm that labels, descriptions, and input hints retain their current values.
- **SC-006**: The new utility text import path resolves, and the old path fails to resolve.

## Assumptions

- The existing renderer methods and output content define the behavior to preserve.
- The existing utility labels, descriptions, and hints define the behavior to preserve.
- This slice moves the utility text module into the existing utility package.
- The utility text logger name and `UtilityText.__module__` value change with the module path.
- This slice addresses the audit renderer package and the WebSocket utility text module.
- Historical analysis records may retain path names that were accurate when those records were written.
- The renderer class module path changes. Code that inspects `__module__` will see the new path.
