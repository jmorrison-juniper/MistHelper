# Feature Specification: Organization Multi-Site Firmware Upgrade

**Issue**: #2475
**Feature Branch**: `feat/2200-org-multisite-firmware-upgrade`
**Updated**: 2026-09-11
**Status**: Specified
**Application**: `src/upgrade_portal`

## Purpose

The portal lets an operator upgrade devices at many sites in one organization.
The portal presents one flow for access points, switches, and gateways.

The portal creates one durable aggregate operation. The operation owns all child
jobs and records every cloud write outcome.

## Verified Mist Contract

The primary OpenAPI description for
`POST /api/v1/orgs/{org_id}/devices/upgrade` states this limit:
"Upgrade Multiple Sites (Only supported for Access Points upgrades)".

The schema conflicts with that description. The `device_type` field permits
`ap`, `switch`, and `gateway`. The `versions[].firmware_type` field permits
`ap` and `junos`.

The saved organization guide also conflicts with the description. Its
`Upgrade Multiple Sites` example includes an AP version and a Junos switch
version in one organization request.

The portal treats the OpenAPI description as the safe limit. The portal sends
only AP targets to the organization device upgrade endpoint.

## Safe Routing Decision

The planner separates the selected devices by site and device family.

| Family | Scope | Route |
| - | - | - |
| AP | Organization | One `upgradeOrgDevices` child job for all selected AP targets |
| Switch | Site | One or more child jobs through `src/firmware/upgrade_service.py` |
| Junos gateway | Site | One or more child jobs through `src/firmware/upgrade_service.py` |
| SSR gateway | Organization | The existing SSR route from `src/firmware/upgrade_service.py` |
| Mist Edge | None | The planner rejects the target |

The planner uses the existing gateway classifier. If the classifier returns
SSR, the planner uses the organization SSR route. The planner does not infer
SSR from the selected UI term alone.

The AP child uses explicit site identifiers. It sets `all_sites` to false. It
sets `device_type` to `ap`. It includes only the AP version record.

The site child plans use the existing service rules. Those rules select
`upgradeSiteDevices` or `upgradeDevice`. The rules also build the correct body
for a switch or a Junos gateway.

## Operator Flow

The portal uses one continuous sequence:

1. The operator selects an organization.
2. The operator selects the multi-site mode.
3. The operator selects one or more sites.
4. The operator selects AP, switch, or gateway targets.
5. The operator sets the options for each selected family.
6. The portal shows the complete child plan.
7. The operator types the confirmation text.
8. The portal submits each planned child once.
9. The progress page shows the aggregate and every child.

The UI uses the terms `AP`, `switch`, and `gateway`. It does not ask the
operator to select `Junos` or `SSR`. The planner classifies each gateway.

## User Stories

### User Story 1: Select the scope

The operator selects an organization, the multi-site mode, and a set of sites.

**Independent test**: A contract test selects three sites from one organization.
The stored selection keeps the same order.

**Acceptance scenarios**:

1. The portal clears old sites when the operator changes the organization.
2. The portal clears old targets when the operator changes the mode.
3. The portal rejects a site from another organization.
4. The portal rejects an empty or duplicate site selection.

### User Story 2: Select device families and options

The operator selects AP, switch, or gateway targets at the selected sites.

**Independent test**: A unit test supplies a mixed inventory. The planner
creates the required family routes.

**Acceptance scenarios**:

1. The options page uses the terms AP, switch, and gateway.
2. The portal offers only options that apply to the selected family.
3. The gateway classifier separates Junos gateways from SSR gateways.
4. The portal rejects every Mist Edge target.

### User Story 3: Review one aggregate plan

The confirmation page shows the organization, sites, families, target counts,
routes, versions, schedules, and warnings.

**Independent test**: A contract test compares the confirmed plan with the
stored plan.

**Acceptance scenarios**:

1. The page shows one AP organization child when AP targets exist.
2. The page shows site children for switch and Junos gateway targets.
3. The page shows the organization SSR route for SSR targets.
4. The page does not show a Mist Edge route.

### User Story 4: Submit each child once

The portal creates the aggregate record before the first cloud write. It claims
each child before its write.

**Independent test**: An integration test sends a repeated browser request. The
service records one write attempt for each child.

**Acceptance scenarios**:

1. The server checks the exact confirmation text.
2. The server checks the CSRF token.
3. The server checks the operation owner.
4. The server checks the organization, sites, locks, and confirmed plan.
5. The server rejects a replay after a child claim.
6. The service uses no SDK retry or transport retry.
7. An uncertain answer sets the child status to `unknown`.
8. The portal does not send an unknown child again.

### User Story 5: Track and cancel the aggregate

The progress page shows the aggregate state and each child state. The operator
can request cancellation for the owned operation.

**Independent test**: An integration test creates accepted, failed, and unknown
children. The aggregate keeps all three outcomes.

**Acceptance scenarios**:

1. A partial submission keeps every submitted child identity.
2. An unsubmitted child keeps a distinct `not_submitted` status.
3. An uncertain child keeps the `unknown` status.
4. Aggregate status never converts `unknown` to success or failure.
5. Cancellation calls only a valid cancel route for a submitted child.
6. Cancellation never claims that a device rollback occurred.
7. Cancellation records an unknown result when the cloud answer is uncertain.

## Functional Requirements

- **FR-001**: The portal MUST use the sequence organization, mode, sites,
  options, confirmation, and progress.
- **FR-002**: The portal MUST use AP, switch, and gateway terms in the UI.
- **FR-003**: The portal MUST create one durable aggregate operation.
- **FR-004**: The aggregate MUST store every planned child before submission.
- **FR-005**: The planner MUST create at most one organization AP child.
- **FR-006**: The AP child MUST contain AP targets only.
- **FR-007**: The planner MUST route switches by site through
  `src/firmware/upgrade_service.py`.
- **FR-008**: The planner MUST route Junos gateways by site through
  `src/firmware/upgrade_service.py`.
- **FR-009**: The planner MUST use the existing organization SSR route when the
  gateway classifier returns SSR.
- **FR-010**: The planner MUST reject Mist Edge targets.
- **FR-011**: The progress page MUST show the aggregate and every child.
- **FR-012**: The portal MUST support partial submission without data loss.
- **FR-013**: The portal MUST preserve unknown write and cancel outcomes.
- **FR-014**: The portal MUST support cancellation by child route.

## Safety Requirements

- **SR-001**: The portal MUST make exactly one application write attempt for
  each claimed child.
- **SR-002**: The portal MUST disable SDK and transport retries for writes.
- **SR-003**: The portal MUST reject a repeated submission for a claimed child.
- **SR-004**: The portal MUST not retry an uncertain write.
- **SR-005**: The portal MUST verify the operation owner before each action.
- **SR-006**: The portal MUST verify the organization and every site.
- **SR-007**: The portal MUST verify a live lock for every selected site.
- **SR-008**: The portal MUST verify the stored confirmation snapshot.
- **SR-009**: The portal MUST verify the CSRF token for every browser write.
- **SR-010**: The portal MUST not treat HTTP acceptance as completion.
- **SR-011**: The portal MUST not claim that cancellation restores firmware.
- **SR-012**: The portal MUST mask credentials in records, logs, and errors.

## Aggregate Status Rules

Each child reports its own state. The aggregate derives a display state without
removing child detail.

| Condition | Aggregate display state |
| - | - |
| No child has a claim | `planned` |
| A submit sequence is active | `submitting` |
| At least one child is unknown | `attention_required` |
| Some children failed and others did not | `partial` |
| All submitted children are active | `running` |
| All children completed | `complete` |
| All possible cancel calls completed | `cancelled` or `partial` |

The record remains authoritative. A page refresh does not start a write.

## Edge Cases

- The AP organization child succeeds before a later site child fails.
- The process stops after a child claim but before it stores the cloud answer.
- The cloud accepts a write but the client receives no answer.
- One site lock expires after another child starts.
- A gateway changes classification before confirmation.
- A user opens an operation that another user owns.
- A cancellation route does not exist for a child.
- A Mist Edge device appears in a gateway inventory result.

## Test Requirements

- **TR-001**: Unit tests MUST cover grouping, gateway classification, and route
  selection.
- **TR-002**: Contract tests MUST cover each Mist request and answer shape.
- **TR-003**: Integration tests MUST cover durable claims, partial submission,
  unknown outcomes, replay prevention, and cancellation.
- **TR-004**: Playwright tests MUST cover the complete UI sequence.
- **TR-005**: All tests MUST use stand-ins and blocked outbound sockets.
- **TR-006**: No test MUST use an API token or a live Mist write.

## Success Criteria

- The confirmed plan and the stored plan have the same child identities.
- Each child has no more than one application write attempt.
- A repeated submit request starts no second cloud write.
- A partial submission remains visible after a process restart.
- An unknown outcome remains unknown until a read reconciles it.
- The progress page shows AP, switch, and gateway results in one view.
- All new tests run offline.

## Non-Goals

- Do not send switch or gateway targets to the organization device endpoint.
- Do not add a Mist Edge firmware route.
- Do not add automatic retries for write or cancel operations.
- Do not replace the existing family planners in `upgrade_service.py`.
- Do not run a live Mist write during implementation or validation.
