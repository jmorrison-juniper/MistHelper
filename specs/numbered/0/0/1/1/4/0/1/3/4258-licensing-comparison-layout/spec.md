# Feature Specification: Licensing comparison layout

**Feature Branch**: `jmorrison-juniper-fix-4258-licensing-comparison-layout`

**Created**: 2026-10-16

**Status**: Approved for implementation

**Input**: Restore the source layout and workflow described in issue #4258.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read a comparison (Priority: P1)

The operator selects authorized organizations and reads license use, entitlements, and device counts without interpreting response objects.

**Why this priority**: The current table hides the useful comparison inside nested objects.

**Independent Test**: Compare two synthetic organizations and verify numeric columns, totals, descriptions, and summary cards.

**Acceptance Scenarios**:

1. **Given** authorized organizations, **When** the operator selects all, **Then** each checkbox and the selected count update.
2. **Given** two results, **When** the comparison completes, **Then** readable license and inventory columns include a totals row and summary cards.
3. **Given** a failed read, **When** results appear, **Then** unavailable values remain explicit and totals do not imply complete data.
4. **Given** the comparison page, **When** it opens, **Then** the shared navigation, theme control, and footer surround charcoal and magenta panels.

### User Story 2 - Adjust and export a comparison (Priority: P2)

The operator adds manual rows, enters purchased amounts, reads remaining amounts, and exports the results.

**Why this priority**: These controls preserve the existing comparison workflow.

**Independent Test**: Add a manual organization, enter purchases, compare, reload, remove the row, and export.

**Acceptance Scenarios**:

1. **Given** manual values and purchases, **When** the page reloads, **Then** the same browser session retains the values.
2. **Given** purchases, **When** comparison completes, **Then** remaining counts and bundle components appear with explicit calculation labels.
3. **Given** an export request, **When** the report downloads, **Then** the shared exporter retains formula neutralization.
4. **Given** refreshed access, **When** the organization list changes, **Then** removed organizations cannot remain selected.

### Edge Cases

- Empty discovery, missing sessions, denied access, and partial discovery show explicit status messages.
- Missing counts stay unavailable. Valid empty inventory has zero devices.
- Unknown license types retain their names and an explicit unavailable description.
- Invalid manual values prevent comparison rather than sending stale values.
- Organization names and license names that contain markup appear only as text.
- Purchase records for deselected or removed rows do not enter comparison requests.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Preserve the shared portal shell without changes to its template or registration.
- **FR-002**: Use charcoal panels, magenta accents, and responsive organization checkboxes with Select All, Refresh, and selection counts.
- **FR-003**: Show APs, switches, gateways, total devices, license use and entitlement columns, descriptions, totals, and summary cards.
- **FR-004**: Retain manual rows, purchased counts, remaining calculations, bundle details, browser-session storage, and CSV export.
- **FR-005**: Preserve authorization, CSRF protection, escaped values, formula neutralization, and shared portal services.
- **FR-006**: Distinguish absent or failed data from zero and identify incomplete totals.
- **FR-007**: Do not modify files owned by pull request #4208.

### Key Entities

- **Organization**: An authorized Mist organization or a browser-session manual row.
- **Comparison**: Organization status, device counts, license use, entitlements, and purchase balances.
- **Purchase balance**: Purchased count minus known use, including catalog-defined bundle components.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Two organization rows and one manual row produce correct device totals and license totals.
- **SC-002**: No result cell displays a serialized response object.
- **SC-003**: All selection, refresh, manual, purchase, and export controls work at desktop and 390-pixel widths.
- **SC-004**: Failed reads display unavailable values, and unauthorized organization requests make no organization-specific reads.
- **SC-005**: The comparison retains shared navigation and the source visual hierarchy in empty and populated states.

## Assumptions

- The source screenshot and original template define visual structure, not permission to copy source code.
- The implementation remains independently written and retains existing source attribution.
- Existing per-organization purchase semantics remain unchanged: purchased minus used, with catalog-defined bundles.
- The source uses a different aggregate purchase-minus-entitlement calculation. This repair labels the existing calculation explicitly rather than changing its contract.
- Numeric inputs replace JSON entry for standard counts. Unknown license types remain visible as result columns.
- No live credentials, cloud writes, new transport, or shared portal registration changes are necessary.
