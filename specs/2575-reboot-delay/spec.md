# Feature Specification: Multi-Site Reboot Delay

**Issue**: #2575
**Feature Branch**: `fix/2575-reboot-delay`
**Created**: 2026-09-16
**Status**: Specified
**Application**: `src/upgrade_portal`

## Purpose

The multi-site upgrade workflow must let an operator delay the reboot of each
switch and each gateway. The control must match the single-site workflow.

A multi-site run can affect many production sites. A wrong reboot time can
interrupt traffic outside an approved window. The portal must fail closed when
it cannot validate the delay.

## Matching Single-Site Behavior

The single-site options page uses this control name:
`Reboot each switch and each gateway after this much time`.

The control accepts a duration such as `8h`. The duration uses the same units
as the single-site path: `s`, `m`, `h`, and `d`. The route carries the field
name `reboot_at`. The option mapper converts the duration to epoch seconds for
the Mist request body.

The multi-site workflow must reuse that route and service shape. It must not
create a second name or a second unit model.

## User Scenarios and Testing

### User Story 1 - Schedule a safe reboot window (Priority: P1)

An operator selects switches or gateways across many sites and writes a reboot
delay. The portal applies that delay to every selected site.

**Independent Test**: A unit test builds an aggregate plan for two sites and
confirms that each site child body carries the same `reboot_at` epoch seconds.

**Acceptance Scenarios**:

1. **Given** two selected sites with switch targets, **When** the operator sets
   an 8 hour reboot delay, **Then** each site child carries that delay.
2. **Given** a selected switch target, **When** the operator reviews the plan,
   **Then** the confirmation page names the reboot delay.

### User Story 2 - Keep the current no-delay path (Priority: P1)

An operator leaves the reboot delay empty. The portal must keep the current
immediate-reboot behavior.

**Independent Test**: A contract test saves multi-device options with no
`reboot_at` value and confirms that the service option has no reboot moment.

**Acceptance Scenarios**:

1. **Given** no reboot delay, **When** the operator saves the options, **Then**
   the plan omits `reboot_at`.
2. **Given** no reboot delay, **When** the route stores the options, **Then** no
   new default value appears.

### User Story 3 - Refuse unsafe delay input (Priority: P1)

An operator enters an invalid or past reboot delay. The portal must refuse the
request before any confirmation or cloud write.

**Independent Test**: A contract test submits an old epoch value through
`reboot_at` and receives a clear 400 response that names the control.

**Acceptance Scenarios**:

1. **Given** a past `reboot_at` value, **When** the operator saves the options,
   **Then** the portal returns `org_upgrade_options_invalid`.
2. **Given** an invalid unit, **When** the operator saves the options, **Then**
   the portal does not create an aggregate operation.

## Requirements

### Functional Requirements

- **FR-001**: The multi-site options form MUST include the control named
  `Reboot each switch and each gateway after this much time`.
- **FR-002**: The multi-site route MUST read and store the field named
  `reboot_at`.
- **FR-003**: The multi-site route MUST validate `reboot_at` with the same
  duration parser that the single-site path uses.
- **FR-004**: The aggregate service MUST carry the converted `reboot_at` epoch
  seconds into each selected switch and gateway site child.
- **FR-005**: The route MUST omit `reboot_at` when the operator leaves the
  control empty.
- **FR-006**: The route MUST refuse an invalid or past `reboot_at` value with a
  clear message.
- **FR-007**: The confirmation page MUST show the reboot delay when the operator
  set one.

### Key Entities

- **Organization options record**: The signed browser record that stores the
  submitted `reboot_at` duration before confirmation.
- **Aggregate child**: A durable child job for one route and site. A switch or
  gateway child carries the `reboot_at` epoch seconds when the operator set a
  delay.
- **Mist request body**: The cloud body that receives epoch seconds in the
  `reboot_at` field.

## Safety Constraints

- The portal must never turn a refused `reboot_at` value into an immediate
  reboot.
- The portal must not send `reboot_at` to an access point organization child.
- The empty field must keep the current immediate-reboot behavior.
- The form text must use the same term as the single-site path.

## Test Plan

- Add a contract test for the new form control and its stable `data-testid`.
- Add a contract test that valid `reboot_at` reaches the confirmed options and
  appears on the confirmation page.
- Add a contract test that an empty `reboot_at` keeps `None` in the service
  options.
- Add a contract test that a past `reboot_at` returns 400 and names the control.
- Add a unit test that the aggregate service applies one `reboot_at` value to
  each selected non-AP site child.

## Interaction With Issue #2644

This change makes issue #2644 reachable from the multi-site workflow, because
operators can now schedule a reboot after a long delay. This change does not
change the twelve hour site lock life. It also does not add a ceiling that
matches the lock life. Issue #2644 must still add that ceiling or a stop rule.

## Success Criteria

- **SC-001**: The multi-site options page shows the new `reboot_at` control with
  a stable test identifier.
- **SC-002**: A valid delay reaches every selected switch or gateway site child.
- **SC-003**: An empty delay produces no `reboot_at` value.
- **SC-004**: A past or invalid delay returns 400 before confirmation.
