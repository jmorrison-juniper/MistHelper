# Feature Specification: Multi-site model versions

**Issue**: #3204
**Branch**: `fix/3204-model-versions`

## Problem

The multi-site options page gives one version control to each device type.
The save copies that version to every selected model of that type.
The compatibility check then refuses a version that one model does not offer.

The aggregate service also places every access point in one organization child.
That child accepts one target version only.

## User story

As a NOC engineer, I select several sites with different device models.
I want to select a supported version for each device.
I want Junos gateways and session smart routers to keep separate choices.

## Functional requirements

- **FR-001**: The multi-site page must show one target version control for each device.
- **FR-002**: Each control must offer only versions for that device model.
- **FR-003**: The save must preserve the selected version for each device address.
- **FR-004**: The save must validate each selected version against its device model.
- **FR-005**: Junos gateways and session smart routers must keep separate controls and plans.
- **FR-006**: If access points use different versions, the aggregate service must use explicit site plans.
- **FR-007**: If all access points use one version, the existing organization AP route must remain in use.

## Acceptance scenarios

1. Four access point models with supported model versions reach the confirmation page.
2. One Junos gateway and one session smart router keep separate version choices.
3. A version that its model does not offer is refused before confirmation.
4. A homogeneous access point plan still creates one organization AP child.
