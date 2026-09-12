# Research: Organization Multi-Site Firmware Upgrade

**Issue**: #2475
**Method**: Local source review only
**Live Mist writes**: None

## 1. Source Authority

The primary source is
`documentation/mist-api-openapi31json.json`. The generated endpoint page gives
the same operation details in a readable form:

`documentation/api/utilities/POST_orgs_org_id_devices_upgrade.md`

The saved organization guide is:

`documentation/Org _ API _ Mist.html`

The repository routing source is:

`src/firmware/upgrade_service.py`

## 2. Verified Operation Description

The operation is `upgradeOrgDevices`.

The method and path are:

`POST /api/v1/orgs/{org_id}/devices/upgrade`

The OpenAPI description states:

> Upgrade Multiple Sites (Only supported for Access Points upgrades)

This sentence is the verified behavioral limit for issue #2475.

## 3. Conflicting OpenAPI Schema

The request schema permits these `device_type` values:

- `ap`
- `gateway`
- `switch`

The `versions` record permits these `firmware_type` values:

- `ap`
- `junos`

The same schema includes switch and gateway fields. Examples include
`reboot_at`, `snapshot`, and `model_version`.

This schema conflicts with the operation description. The schema describes a
possible body shape. It does not verify safe organization upgrades for switches
or gateways.

## 4. Conflicting Saved Organization Guide

The saved guide section `Upgrade Multiple Sites` uses the same organization
path. Its example includes:

- An AP version record with `firmware_type` set to `ap`.
- A switch version record with `firmware_type` set to `junos`.
- A `model_version` map for an EX switch.

The example also contains syntax defects. It omits commas in several places.
It includes comments inside the JSON block.

The guide therefore conflicts with the OpenAPI description. The example does
not provide sufficient evidence for a disruptive switch or gateway write.

## 5. Safe Interpretation

Use the narrow description for the organization device endpoint.

Send only AP targets to `upgradeOrgDevices`. Set `device_type` to `ap`. Include
only the AP firmware record.

Do not use the conflicting schema fields as permission for organization switch
or gateway upgrades.

## 6. Existing Site Routing

`src/firmware/upgrade_service.py` already plans mixed device upgrades.

It provides these routes:

- `upgradeSiteDevices` for a site batch.
- `upgradeDevice` for an eligible single device.
- `upgradeOrgSsrs` for SSR gateways.

The service groups targets by device type, gateway family, and target version.
It builds a separate plan for each group.

The service sends switches and Junos gateways at site scope. It selects the
batch or single-device call through its existing rules.

## 7. Gateway Classification

The function `classify_gateway` uses the device type and model.

It classifies a gateway as SSR when the type is `ssr`. It also recognizes model
text that contains `SSR` or `128T`.

Every other gateway uses the Junos family.

An SSR plan uses `upgradeOrgSsrs` at organization scope. A Junos gateway plan
uses a site device route.

## 8. Mist Edge

The inspected upgrade planner has no approved Mist Edge firmware route for this
flow.

Issue #2475 excludes Mist Edge. The planner must reject a Mist Edge target
before confirmation.

## 9. Durable Aggregate Decision

One user action can produce several cloud writes. A single cloud job identifier
cannot represent the complete operation.

The portal therefore needs one durable aggregate operation. The aggregate owns
all child plans and all child results.

Each child records:

- A durable child identifier.
- The route and scope.
- The organization identifier.
- The site identifier when the route uses a site.
- The UI family and the planned family.
- The target device identifiers.
- The cloud job identifier.
- The submit status and raw HTTP status.
- The error and uncertainty details.
- The cancel status and cancel error.

## 10. Partial Submission and Unknown Outcomes

A sequence can stop after one child succeeds. The aggregate must keep accepted,
failed, unknown, and unsubmitted children as different states.

A timeout can occur after the cloud accepts a write. The child must then use
`unknown`. The service must not retry that child.

A process can stop after the durable claim and before the answer write. The
claim proves that a write may exist. Recovery must preserve `unknown` until a
read reconciles the result.

## 11. Exact-Once Boundary

The portal can guarantee one application write attempt for each durable child
claim. It cannot guarantee one remote effect after an uncertain network result.

The design uses these controls:

1. Create the child before the write.
2. Claim the child with an atomic transition.
3. Reject a second claim.
4. Disable SDK and transport retries.
5. Store an uncertain result as `unknown`.
6. Reconcile with read operations only.

This boundary prevents a deliberate replay. It also reports uncertainty
truthfully.

## 12. Security Findings

The existing browser flow requires an authenticated session and CSRF
protection. The aggregate adds ownership checks.

Each write must verify:

- The authenticated user owns the aggregate.
- The active organization matches the aggregate.
- Every site belongs to that organization.
- Every target belongs to a selected site.
- Every required site lock remains valid.
- The posted confirmation matches the stored plan.
- The CSRF token is valid.

## 13. Test Decision

All verification for this issue stays offline.

Unit tests cover pure planning and state rules. Contract tests cover request and
answer shapes. Integration tests cover storage and failure boundaries.
Playwright tests cover the complete browser sequence.

No test uses a Mist credential. No test sends a live firmware write.
