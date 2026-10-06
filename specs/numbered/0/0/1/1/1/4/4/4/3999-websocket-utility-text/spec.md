# Feature Specification: WebSocket Utility Text Catalog

**Feature Branch**: `3999-websocket-utility-text`

**Created**: 2026-10-06

**Status**: Draft

**Input**: Issue #3999: Move the WebSocket utility text catalog into the utilities package.

## User Scenarios & Testing

### User Story 1 - Keep the catalog structure within the project limit (Priority: P1)

As a maintainer, I need the utility text module under `utilities` so the catalog package has no more than five structural children.

**Independent Test**: Inspect both packages and run the focused package structure guard.

### User Story 2 - Preserve utility text behavior (Priority: P1)

As a developer, I need every active caller to use the new canonical path without a wrapper or alias.

**Independent Test**: Run the focused utility text tests and the public symbol preservation guard.

### User Story 3 - Record the bounded refactor (Priority: P2)

As a maintainer, I need a routed specification and a release note that define the exact change boundary.

**Independent Test**: Review the authorized file list and run the changelog and Markdown-link guards.

## Requirements

- **FR-001**: Move `utility_text.py` to `catalog/utilities/utility_text.py`.
- **FR-002**: Update active source and focused test imports to the new canonical path.
- **FR-003**: Preserve every module-level symbol and all utility text behavior.
- **FR-004**: Do not leave an old-path wrapper, alias, or fallback import.
- **FR-005**: Keep `catalog` and `catalog/utilities` within five structural children.
- **FR-006**: Update the exact old-to-new path mapping in the public symbol preservation guard.
- **FR-007**: Do not edit historical specifications 3574, 3889, or 3890.
- **FR-008**: Limit the implementation to the module move, active imports, focused tests, the symbol map, this routed specification, the plan, the tasks, and one release note.

## Success Criteria

- **SC-001**: The utility text module exists only at the new canonical path.
- **SC-002**: The catalog and utilities packages each have no more than five structural children.
- **SC-003**: Focused utility text tests pass with the new import path.
- **SC-004**: The public symbol preservation guard compares the old and new paths.
- **SC-005**: No historical specification changes occur.

## Assumptions

- The existing `UtilityText` source remains unchanged during the move.
- Existing focused tests provide behavior coverage for labels, sentences, hints, and annotations.
- No user interface, API, data, or runtime behavior changes.
