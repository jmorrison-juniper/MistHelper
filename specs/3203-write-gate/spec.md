# Feature Specification: Configure the multi-site write gate

**Issue**: #3203
**Feature Branch**: `fix/3203-write-gate`
**Status**: Implemented

## Problem

The multi-site submit and cancel routes read `ORG_UPGRADE_WRITES_ENABLED` from
the Flask configuration. Production did not set that key. The confirmation
page and both routes for writes stayed closed in every deployment.

Warning: these routes can change firmware at many sites. The default must stay
closed, and the deployment must enable the gate explicitly.

## User Story: Enable reviewed multi-site writes

An operator completes the multi-site safety checks. A deployment administrator
sets the documented environment variable and restarts the portal.

**Acceptance scenarios**:

1. **Given** no setting, **When** the portal starts, **Then** multi-site submit
   and cancel requests stay disabled.
2. **Given** `ORG_UPGRADE_WRITES_ENABLED=true`, **When** the portal starts,
   **Then** the multi-site submit and cancel routes can pass the write gate.
3. **Given** another value, **When** the portal starts, **Then** the write gate
   stays closed and the log names the invalid setting.
4. **Given** a closed gate, **When** the operator opens the confirmation page,
   **Then** the warning names `ORG_UPGRADE_WRITES_ENABLED=true`.

## Requirements

- **FR-001**: The portal MUST read `ORG_UPGRADE_WRITES_ENABLED` at startup.
- **FR-002**: Only the value `true`, with any letter case, MUST
  enable the write gate.
- **FR-003**: An absent, blank, false, or unknown value MUST disable the gate.
- **FR-004**: The deployment example MUST document the setting and its risk.
- **FR-005**: A contract test MUST prove the open and closed page states.

## Non-goals

- The change does not remove the typed confirmation, pre-check, lock, replay,
  identity, or ownership guards.
- The change does not enable multi-site writes by default.
