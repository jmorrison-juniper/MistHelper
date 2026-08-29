# Feature Specification: Per-Type Upgrade Version Defaults

**Feature Branch**: `1824-upgrade-capture-defaults`  
**Created**: 2026-08-28  
**Status**: Draft  
**Input**: "In the upgrade capture portal, select a default target version as the numerically highest compatible returned version unless an environment variable provides an override. Replace the current single global version dropdown with one dropdown per device type (AP, switch, gateway). Each type default uses an environment override when it is compatible; otherwise it uses the numerically highest compatible version for every model/device in that type. Preserve safety: never select an unavailable version or submit an upgrade during validation. Identify appropriate variable names and acceptance tests."

## User Scenarios & Testing

### User Story 1 - Receive safe defaults for each device type (Priority: P1)

An operator opening upgrade options sees a separate target-version dropdown for access points, switches, and gateways. Each populated type is preselected to the highest numbered version that every eligible device in that type can install, so the operator can review a safe plan without manually finding a shared release.

**Why this priority**: This supplies the requested safe default and removes the highest-risk manual selection work.

**Independent Test**: Open options for a site containing multiple models of each type with overlapping version lists; verify that each type control selects the highest numeric value in that type's common compatible versions and that every affected device receives only that offered value.

**Acceptance Scenarios**:

1. **Given** a device type has two or more devices with one or more versions common to every device, **When** the operator opens upgrade options, **Then** its dropdown selects the numerically highest common version.
2. **Given** version strings are not ordered lexically, **When** the portal chooses a default, **Then** it compares their version components numerically and selects the true highest compatible version.
3. **Given** access points, switches, and gateways each have eligible devices, **When** options load, **Then** the portal shows one independent dropdown for each of those three types and no single all-device version dropdown.
4. **Given** a device type has no version shared by all of its eligible devices, **When** options load, **Then** that type has no preselected target and the portal does not assign an unavailable version to any device.

### User Story 2 - Apply an approved operational override safely (Priority: P2)

An operations administrator can set a type-specific environment setting to prefer an approved release. The portal applies that setting only when every eligible device of the relevant type offers the exact version; otherwise it safely falls back to the normal highest-compatible default.

**Why this priority**: Overrides support planned release windows without weakening the compatibility guarantee.

**Independent Test**: Configure each override in turn for compatible and incompatible values, open the options page, and verify the selected target and device assignments for the associated type.

**Acceptance Scenarios**:

1. **Given** `CAPTURE_DEFAULT_AP_VERSION` names a version offered by every eligible access point, **When** options load, **Then** the access-point dropdown selects that override instead of the highest compatible version.
2. **Given** `CAPTURE_DEFAULT_SWITCH_VERSION` or `CAPTURE_DEFAULT_GATEWAY_VERSION` names a version unavailable to at least one eligible device of its type, **When** options load, **Then** the relevant dropdown selects the highest numerically compatible version rather than the override.
3. **Given** an override is blank, malformed, or names no returned version, **When** options load, **Then** the portal treats it as unavailable and uses the safe fallback without failing the options page.
4. **Given** a compatible override exists for one type, **When** options load, **Then** it does not change the default selected for either other device type.

### User Story 3 - Validate selections without triggering an upgrade (Priority: P1)

An operator or automated validation can load and save the proposed target selections without starting firmware work. The portal rejects stale, tampered, or incompatible choices before they can become an upgrade plan.

**Why this priority**: Firmware changes are consequential; validation must remain read-only and must never turn an invalid default into an unsafe action.

**Independent Test**: Submit a selection containing a version not returned for a device and inspect the resulting run and external-service calls; verify rejection, no persisted invalid target, and no upgrade submission.

**Acceptance Scenarios**:

1. **Given** a browser submits a type target that at least one device of that type does not offer, **When** the portal validates the options, **Then** it rejects the selection and does not save an upgrade target for that unavailable version.
2. **Given** the available-version data changes after the page loads, **When** the operator saves defaults, **Then** the portal revalidates the choices against current compatible availability before accepting them.
3. **Given** the portal is calculating defaults or validating an options save, **When** any compatible-version read or validation fails, **Then** it does not submit an upgrade.
4. **Given** defaults have been reviewed and saved, **When** the operator has not completed the existing explicit confirmation and start action, **Then** no upgrade is submitted.

## Edge Cases

- A site has no devices of a supported type, or all type-specific inventory records are incomplete.
- A type has one device, so its returned options are its full compatibility set.
- Different models report duplicate, whitespace-padded, or differently formatted version strings.
- A device is removed, changes type, or loses an offered version between page display and option save.
- A type has no common compatible version, including after an administrator supplied an incompatible override.
- A client posts a missing, unknown, or cross-type device target.
- The options page reloads after a save; valid saved operator choices remain distinguishable from a newly calculated default.

## Requirements

### Functional Requirements

- **FR-001**: The portal MUST replace the single all-device target-version dropdown with distinct target-version dropdowns for access points, switches, and gateways.
- **FR-002**: The portal MUST calculate each type's compatible candidates as only the returned versions available for every eligible device and model in that device type.
- **FR-003**: When no valid override applies, the portal MUST preselect the numerically highest candidate version for each populated device type.
- **FR-004**: The portal MUST compare candidate versions by numeric version components rather than by their display-string ordering.
- **FR-005**: The portal MUST read `CAPTURE_DEFAULT_AP_VERSION`, `CAPTURE_DEFAULT_SWITCH_VERSION`, and `CAPTURE_DEFAULT_GATEWAY_VERSION` as the respective optional type-default override settings.
- **FR-006**: The portal MUST apply a type override only when its exact value is among the compatible candidates for every eligible device of that type.
- **FR-007**: When a type override is blank, malformed, unavailable, or incompatible, the portal MUST select that type's numerically highest compatible candidate or leave the type unselected when no candidate exists.
- **FR-008**: The portal MUST assign a selected type target only to devices of that type that offer the selected version.
- **FR-009**: The portal MUST revalidate every submitted target against current device availability before saving an upgrade plan.
- **FR-010**: The portal MUST reject a submitted unavailable, unknown, or incompatible version without persisting that target.
- **FR-011**: The portal MUST NOT submit or invoke an upgrade while it calculates defaults or validates a selection.
- **FR-012**: The portal MUST preserve the existing explicit confirmation requirement before an accepted saved plan can start an upgrade.
- **FR-013**: The portal SHOULD explain when a device type has no common compatible version and therefore no default selection.

## Key Entities

- **Device type**: One of access point, switch, or gateway; groups devices that receive one shared default target selection.
- **Eligible device**: A site device with a recognized type, model, identity, and returned version availability that can participate in type compatibility calculation.
- **Returned version**: A target release reported as available for a particular device model.
- **Compatible candidate**: A returned version common to every eligible device in one device type.
- **Type override**: An administrator-provided preferred version for one device type that is used only after compatibility validation.
- **Target selection**: The reviewed target version assigned to a device and later used in the existing confirmation process.

## Success Criteria

### Measurable Outcomes

- **SC-001**: For every populated device type with at least one common compatible version, the initial selection matches that type's highest numeric compatible version in 100% of automated test cases without a valid override.
- **SC-002**: In 100% of automated override test cases, a compatible type override is selected only for its own type and an incompatible override falls back safely.
- **SC-003**: In 100% of automated invalid-selection and stale-availability test cases, no unavailable target is saved and no upgrade is submitted during validation.
- **SC-004**: Automated browser tests verify three independent type controls and verify that the retired global version control is absent.
- **SC-005**: In 100% of test cases where a type has no shared candidate, the portal leaves that type without a target and communicates the condition to the operator.

## Assumptions

- The existing returned model-version data is authoritative for whether a device may receive a target version.
- Only access points, switches, and gateways participate in this feature; unsupported device types remain outside its selection controls.
- A compatible version means an exact normalized match in every eligible device's returned availability list.
- Numeric comparison follows the release-number components in the returned version value; nonnumeric suffixes do not make a lower numeric release outrank a higher numeric release.
- Saving options remains separate from the existing confirmation and start actions.
- The selected environment variable names are `CAPTURE_DEFAULT_AP_VERSION`, `CAPTURE_DEFAULT_SWITCH_VERSION`, and `CAPTURE_DEFAULT_GATEWAY_VERSION`.

## Non-Goals

- Changing the existing upgrade execution, confirmation wording, or post-upgrade verification workflow.
- Adding overrides for individual devices or individual models.
- Inventing target versions that are not returned by the existing availability source.
