# Feature Specification: Audit Renderer Structure

**Feature Branch**: `jmorrison-juniper-3824-audit-renderer-structure`

**Created**: 2026-10-31

**Status**: Draft

**Input**: User description: "Reduce nested source package child counts by relocating audit renderer modules while preserving public behavior."

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

### Edge Cases

- An audit result with no timelines, changes, or rollback diffs keeps the existing empty report behavior.
- A tracked diagnostic script or test that imports a moved module uses the new path.
- The source debt count decreases, and the change does not add a new structural violation.

## Requirements

### Functional Requirements

- **FR-001**: The audit report renderer MUST keep its current Mermaid and HTML output behavior.
- **FR-002**: The renderer MUST preserve its current public report methods and test-visible delta helpers.
- **FR-003**: The renderer modules MUST reside in a source hierarchy where each affected directory has no more than five structural children.
- **FR-004**: All active callers and tests MUST use the new module paths.
- **FR-005**: The change MUST remove the old renderer module paths without aliases or compatibility wrappers.
- **FR-006**: The nested source package measurement MUST report fewer violations after the change.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The audit source package and each new renderer directory contain no more than five structural children.
- **SC-002**: The repository-wide nested source measure reports 34 violations, down from 35, with no increase in total excess.
- **SC-003**: The audit renderer tests pass for Mermaid output, HTML output, delta behavior, and empty results.
- **SC-004**: New renderer import paths resolve, and all old renderer module paths fail to resolve.

## Assumptions

- The existing renderer methods and output content define the behavior to preserve.
- This slice addresses only the audit renderer package and the active callers that import it.
- Historical analysis records may retain path names that were accurate when those records were written.
- The renderer class module path changes. Code that inspects `__module__` will see the new path.
