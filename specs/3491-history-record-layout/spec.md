# Feature Specification: Compact history records

**Feature Branch**: `jmorrison-juniper-history-record-layout`

**Created**: 2026-10-03

**Status**: Locally verified. Publication is not authorized.

**Input**: [Issue #3491](https://github.com/jmorrison-juniper/MistHelper/issues/3491), including all comments.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read compact records (Priority: P1)

An operator reads Runs, Multi-site upgrades, and Audit log without broken identifiers or tall rows.

**Why this priority**: Broken identifiers make the records difficult to read.

**Independent Test**: Measure the actual route at 1024, 1280, and 1440 pixels in both history scopes.

**Acceptance Scenarios**:

1. **Given** either scope, **When** the operator reads a record, **Then** each value stays on one line.
2. **Given** a long value, **When** the cell cannot contain it, **Then** an ellipsis marks the clip and a title retains the value.
3. **Given** a populated table, **When** the browser paints a row, **Then** its height does not exceed 48 pixels.

### User Story 2 - Read consistent surfaces (Priority: P2)

The row header uses the same surface color as the other cells in both supported themes.

**Why this priority**: A different surface separates one cell from its record.

**Independent Test**: Compare computed colors before and during hover in `magenta` and `default`.

**Acceptance Scenarios**:

1. **Given** either theme, **When** a row has no hover, **Then** all cells use the surface token.
2. **Given** either theme, **When** a pointer enters a row, **Then** all cells use the hover token.

### User Story 3 - Retain every action and protected description (Priority: P1)

An operator can reach each column and activate existing links with a keyboard or touch.

**Why this priority**: A compact row must not hide an action or change the meaning of a record.

**Independent Test**: Measure each column and scroll container, activate links, and execute unchanged adjacent tests.

**Acceptance Scenarios**:

1. **Given** a narrow window, **When** a table needs more width, **Then** its container scrolls and the page does not.
2. **Given** a link outside the visible part of a table, **When** the operator reaches it, **Then** the link remains usable.
3. **Given** either scope, **When** the page renders, **Then** descriptions, accessible names, empty statements, values, and privacy decisions remain unchanged.

### Edge Cases

- An operation from another browser retains its explanation on a separate compact line.
- A run retains its age, stale badge, selection control, and capture links.
- An audit row retains its complete digests and any inference explanation.
- An empty or unavailable source retains the exact existing statement.
- The Captures table retains its widths, device type fields, and 48-pixel row contract.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Load one page component through the existing `head_extra` hook after `portal.css`.
- **FR-002**: Scope every new rule to the three record tables.
- **FR-003**: Use a fixed column budget without smaller fonts or changes to shared assets.
- **FR-004**: Retain the complete original value in each clipped value's title.
- **FR-005**: Retain existing titles that contain original stored moments.
- **FR-006**: Use the existing surface and hover tokens for row headers.
- **FR-007**: Preserve all routes, source readers, escaping, scope text, identifiers, links, and row attributes.
- **FR-008**: Prove failures on the unchanged baseline or a bounded mutation of actual component styles.
- **FR-009**: Verify the native asset response and the actual wheel and source distribution resources.
- **FR-010**: Keep the original 603 browser cases, markers, order, fixture lifetimes, and artifact defaults unchanged.

### Key Entities

The existing run, operation, audit, and capture records do not change.
No schema, primary key, route context, or source projection changes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All populated record rows measure at most 48 pixels.
- **SC-002**: Each measured value occupies one text line, including UUIDs, addresses, moments, and digests.
- **SC-003**: Every clipped value retains its full text and title.
- **SC-004**: Header and body cells align, and row-header colors match body colors in both themes.
- **SC-005**: The page has no horizontal overflow. Any table overflow stays inside its own scroll container.
- **SC-006**: Both scopes pass at all three widths in both themes.
- **SC-007**: Six controlled screenshots cover both scopes and all three widths. Each image receives a visual inspection.
- **SC-008**: All protected source hashes and original browser membership remain unchanged.

## Assumptions

- The accepted local base is `0317b944388fb9f927ce4a20368070408542c4b1`.
- A table may require horizontal scrolling. This repair does not claim that every column fits the viewport.
- Only the coordinator can grant publication or release the next owner.
- Licensed dictionary grading can remain partial when the dictionary is absent.
