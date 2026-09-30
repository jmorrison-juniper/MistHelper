# Feature Specification: Readable Maps Title

**Feature Branch**: `jmorrison-juniper-map-title-contrast`

**Created**: 2026-09-30

**Status**: Specified

**Input**: Repair [issue #3365](https://github.com/jmorrison-juniper/MistHelper/issues/3365).
The Maps page title must use the current theme text color.
The repair must preserve the map and work after a theme change.

## User Scenarios & Testing

### User Story 1 - Read the selected map title (Priority: P1)

An operator selects a site and a floor plan on the Maps page.
The operator can read the floor plan title in the light theme and the dark theme.

**Why this priority**: The title identifies the floor plan that the operator views.
The current dark gray title has insufficient contrast on the dark card.

**Independent Test**: Select a site and a map in each theme.
Measure the rendered title color against the rendered map card background.

**Acceptance Scenarios**:

1. **Given** the dark theme, **When** an operator selects a map, **Then** the title uses the theme text color.
2. **Given** the light theme, **When** an operator selects a map, **Then** the title uses the theme text color.
3. **Given** either theme, **When** the title appears, **Then** its contrast against the card is at least 4.5:1.
4. **Given** a saved theme, **When** the operator returns to Maps, **Then** the title uses that saved theme.

### User Story 2 - Keep the title readable after a theme change (Priority: P1)

An operator changes the theme while a map remains visible.
The title changes to the new theme text color without another map selection.

**Why this priority**: A readable initial title does not repair a title that becomes unreadable after a theme change.

**Independent Test**: Change the theme in both directions while a floor plan remains visible.
Measure the title contrast after each change.
Confirm that the same floor plan, device positions, and viewing range remain.

**Acceptance Scenarios**:

1. **Given** a visible dark map, **When** the operator selects the light theme, **Then** the title remains readable.
2. **Given** a visible light map, **When** the operator selects the dark theme, **Then** the title remains readable.
3. **Given** a slow theme load, **When** the new theme becomes active, **Then** the title uses its text color.
4. **Given** no selected map, **When** the operator changes the theme, **Then** the page reports no script error.

### Edge Cases

- A floor plan image loads after a theme change.
- The operator changes the theme before selecting a map.
- The operator selects another map while an older map answer remains pending.
- A map has no image, or its image download fails.
- A map name is empty, so the existing default title appears.
- The contrast check cannot find the rendered title or the card.

## Requirements

### Functional Requirements

- **FR-001**: The map title MUST use the current theme text color, not a fixed color.
- **FR-002**: The title contrast against the actual map card background MUST be at least 4.5:1 in both required themes.
- **FR-003**: A theme change MUST update a visible title after the new theme becomes active.
- **FR-004**: A theme change MUST preserve the map selection, image, device positions, device colors, and viewing range.
- **FR-005**: The repair MUST preserve the existing image notes, responsive map, scroll zoom, and late-answer guard.
- **FR-006**: The browser journey MUST read the actual rendered title color and card background.
- **FR-007**: The contrast check MUST reject insufficient contrast and missing measurement inputs.
- **FR-008**: Tests MUST use simulated cloud answers and test-controlled files without production stores or credentials.

### Key Entities

- **Map title**: The selected floor plan name, or the existing default name when no name exists.
- **Theme text color**: The text color that the active theme applies to the map card.
- **Map card**: The visible background behind the map title.
- **Map view**: The selected floor plan, image, devices, and viewing range.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every measured light and dark title has at least 4.5:1 contrast against its card.
- **SC-002**: Both theme-change directions update the title without a page reload or a map reload.
- **SC-003**: The image, device positions, and viewing range remain unchanged after a theme change.
- **SC-004**: The browser check fails for the original dark gray title on the dark card.
- **SC-005**: Related map journeys continue to pass without skipped browser measurements.

## Assumptions

- The existing theme selector and saved theme preference remain the source of theme selection.
- The existing theme text colors already have sufficient contrast against their card backgrounds.
- This repair changes no API, database schema, menu operation, or deployment setting.
- The user authorizes a pull request and squash merge after all required checks pass.
- The app owns the branch. The SpecKit artifacts use the explicit issue directory without another branch.
