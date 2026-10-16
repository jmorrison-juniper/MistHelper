# Feature Specification: Inventory model filter

**Feature Branch**: `jmorrison-juniper-inventory-model-filter`

**Created**: 2026-10-16

**Status**: Approved for planning

**Input**: “for our option 305, can we filter the model list to only display by default, models types that already exist in the Org inventory?”

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select installed models (Priority: P1)

An operator sees only inventory models when selecting organization firmware policies.

**Why this priority**: A shorter list reduces incorrect selections.

**Independent Test**: Supply inventory and supported models, then compare the default CLI and graphical lists.

**Acceptance Scenarios**:

1. **Given** an organization owns AP41, **When** the operator loads AP choices, **Then** absent AP models remain hidden.
2. **Given** multiple organizations, **When** the operator loads choices, **Then** models from any selected inventory appear only with versions supported by every organization.
3. **Given** SSR and SRX inventory, **When** the operator selects switches, **Then** gateway models remain excluded.

### User Story 2 - Select other supported models (Priority: P2)

An operator can explicitly select all supported models for future equipment.

**Why this priority**: The default filter must not prevent planned additions.

**Independent Test**: Select Show all supported models and confirm that absent, compatible models appear.

**Acceptance Scenarios**:

1. **Given** a filtered list, **When** the operator selects Show all supported models, **Then** all mutually supported choices appear.
2. **Given** an empty inventory, **When** the operator loads default choices, **Then** an explicit empty message appears without a full-list fallback.
3. **Given** an inventory failure, **When** the operator loads default choices, **Then** the operation reports failure without returning unfiltered choices.

### Edge Cases

- Pagination must include every inventory page.
- Duplicate inventory models must appear once.
- Missing or malformed inventory models must produce a checked error.
- Type distinctions and exact supported version validation remain unchanged.
- Changing filter scope invalidates prior graphical selections and prepared confirmation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Default CLI and graphical choices MUST include only models present in at least one selected organization inventory.
- **FR-002**: Every displayed model/version pair MUST remain supported by every selected organization.
- **FR-003**: Both interfaces MUST provide an explicit Show all supported models control.
- **FR-004**: Empty inventory MUST remain empty, with an explanation and an explicit all-model choice.
- **FR-005**: Inventory failures and malformed records MUST report an error without an automatic full-list fallback.
- **FR-006**: Filtering MUST preserve AP, switch, SSR, and SRX distinctions.
- **FR-007**: Backup verification, typed confirmation, and settings validation MUST remain unchanged.
- **FR-008**: Tests MUST use mock responses and MUST NOT change production settings or trigger upgrades.

### Key Entities

- Organization inventory: owned hardware models, including equipment not assigned to a site.
- Compatible catalog: model/version pairs shared by all selected organizations.
- Display scope: inventory models by default, or all supported models by explicit choice.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero absent models appear in default choices.
- **SC-002**: Both interfaces can reveal all compatible models with one explicit scope selection.
- **SC-003**: Every failure case reports a visible error and performs zero settings writes.
- **SC-004**: Every selected organization retains model/version compatibility checks.

## Assumptions

“By default” permits an explicit Show all supported models control.
For multiple organizations, inventory membership uses the union, while supported model/version pairs use the intersection.
This permits policies for models owned by only some targets without weakening compatibility checks.
