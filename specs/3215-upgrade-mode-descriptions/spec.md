# Feature Specification: Upgrade mode descriptions

**Feature Branch**: `jmorrison-juniper-upgrade-mode-descriptions`

**Created**: 2026-10-01

**Status**: Specified

**Input**: Repair [issue #3215](https://github.com/jmorrison-juniper/MistHelper/issues/3215) without a product behavior change.

## User Scenarios & Testing

### User Story 1 - Understand each upgrade mode (Priority: P1)

The operator reads the mode page before the site selection.
The page explains each mode's workflow, cloud routes, and capture features.

**Why this priority**: The current text incorrectly describes one organization cloud job for all device families.

**Independent Test**: Render the real mode route with an offline client and open it with isolated Chromium.

**Acceptance Scenarios**:

1. **Given** an organization, **When** the operator reads either mode, **Then** the text states the actual cloud scopes.
2. **Given** either mode, **When** the operator reads the capture guidance, **Then** it describes verified pre-check adoption.
3. **Given** either mode, **When** the operator reads the post-check guidance, **Then** it distinguishes automatic and manual captures.

### User Story 2 - Understand the selected site's workflow (Priority: P1)

The site page explains the active mode before the operator selects a site.
The explanation stays correct after a saved selection.

**Why this priority**: The site page repeats the false organization cloud job claim.

**Independent Test**: Read both site page modes with no saved sites, one saved site, and two saved sites.

**Acceptance Scenarios**:

1. **Given** single-site mode, **When** the operator opens a site, **Then** the existing inventory and capture routes remain available.
2. **Given** multi-site mode, **When** the operator saves the sites, **Then** the existing options route remains unchanged.
3. **Given** a saved selection, **When** the operator returns to the site page, **Then** the page retains the selected checkboxes.

### Edge Cases

- A mode page without an organization still directs the operator to the organization picker.
- A selected organization can have no selected mode.
- Multi-site mode can select one site.
- A comparison needs a verified pre-check and post-check pair.
- Manual post-check mode must not promise an automatic capture.
- A site with no accepted upgrade job must not receive a promised automatic post-check capture.

## Requirements

### Functional Requirements

- **FR-001**: Both pages must remove the false claim that multi-site mode uses one organization cloud job.
- **FR-002**: Single-site guidance must describe the inventory, pre-check, and upgrade options workflow for one site.
- **FR-003**: Single-site guidance must name the site routes for access points, switches, and Junos gateways.
- **FR-004**: Multi-site guidance must distinguish one portal operation from its separate child jobs.
- **FR-005**: Multi-site guidance must name the organization AP route and the site routes for switches and Junos gateways.
- **FR-006**: Both modes must name the organization SSR route.
- **FR-007**: Both pages must describe the newest verified standalone pre-check capture of each site.
- **FR-008**: Multi-site guidance must name the confirmation page as the place to take missing pre-check captures.
- **FR-009**: Both pages must distinguish automatic and manual post-check modes and require verified capture pairs for comparison.
- **FR-010**: Form actions, route destinations, mode values, CSRF fields, selected states, and typed confirmations must remain unchanged.
- **FR-011**: New descriptions must have stable test identifiers and use Simplified Technical English.
- **FR-012**: All new test cases must run offline without live credentials, cloud writes, or production stores.

### Key Entities

No entity, schema, primary key, lock, or stored record changes.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The rendered mode and site pages contain zero instances of the false organization cloud job claim.
- **SC-002**: Both modes state their actual device routes and current capture features.
- **SC-003**: The site page preserves zero, one, and two selected-site states.
- **SC-004**: Every new offline and Chromium case runs without a skip.
- **SC-005**: The change alters only the ten reserved files.

## Assumptions

The live implementation takes precedence over the issue's older missing-feature statement.
Issues #3243 and #3244 added multi-site pre-check and post-check features after the original report.
Spec 2200 and the current services establish the cloud routing rules.
The parent controls publication and any later protected merge.
