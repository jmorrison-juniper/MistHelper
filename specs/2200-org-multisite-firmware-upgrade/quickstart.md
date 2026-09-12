# Quickstart: Organization Multi-Site Firmware Upgrade

**Issue**: #2475
**Scope**: Specification implementation guide

## Goal

Implement one safe portal flow for AP, switch, and gateway upgrades across many
sites in one organization.

## Read First

Read these files before implementation:

- `spec.md`
- `research.md`
- `data-model.md`
- `contracts/api-contract.md`
- `contracts/ui-contract.md`
- `src/firmware/upgrade_service.py`
- `src/firmware/org_upgrade_service.py`

## Step 1: Keep the API Boundary

Use `upgradeOrgDevices` for AP targets only.

Do not use the conflicting `device_type` and `firmware_type` schema values as
permission for organization switch or gateway writes.

## Step 2: Build the Target Snapshot

Read the selected organization, sites, device families, and device identifiers.
Verify every ownership relation.

Reject Mist Edge. Classify every gateway with the existing classifier.

## Step 3: Build the Child Plan

Create one organization AP child for all selected AP targets.

Create site children for switches and Junos gateways through
`src/firmware/upgrade_service.py`.

Keep the existing organization SSR route when the planner classifies an SSR
gateway.

Store the route, scope, organization, site, family, body, and target identifiers
for every child.

## Step 4: Create the Aggregate

Write the aggregate and every child before confirmation. Give each child a
stable identifier.

Create a canonical confirmation snapshot. Store its digest in `plan_hash`.

## Step 5: Protect the Write

Before submission, verify:

1. The user owns the aggregate.
2. The active organization matches.
3. Every site belongs to the organization.
4. Every target belongs to a selected site.
5. Every site lock remains valid.
6. The confirmation snapshot still matches.
7. The typed confirmation text matches exactly.
8. The CSRF token is valid.

## Step 6: Submit Each Child Once

Atomically claim one child before its cloud write. Reject a second claim.

Set SDK retries to zero. Set transport retries to zero.

Send one request for the claimed child. Store `unknown` when the outcome can
include an accepted cloud write.

Warning: do not retry an unknown write. A retry can start a second firmware
operation.

## Step 7: Show Progress

Show one progress page for the aggregate. Include one row for each child.

Show the UI family, route, scope, site, target count, cloud identity, status,
error, and cancel status.

Use read-only polling. A refresh must not submit a write.

## Step 8: Cancel Safely

Require ownership, organization, confirmation, and CSRF checks.

Claim each cancel action before the cloud call. Send no cancel retry.

Preserve mixed results and unknown outcomes. Do not claim a rollback.

## Offline Validation

Run unit tests for planning and state transitions.

Run contract tests for the organization AP route, the site routes, and the SSR
route.

Run integration tests for durable claims, restarts, partial submission, unknown
outcomes, and cancellation.

Run Playwright tests for:

`organization -> mode -> sites -> options -> confirmation -> progress`

Use network stand-ins. Keep outbound sockets blocked. Use no Mist credential.

## Documentation Validation

Grade every changed Markdown file with the repository STE linter. Repair each
score below 80.

## Completion Checklist

- The organization endpoint receives AP targets only.
- Site routes receive switch and Junos gateway targets.
- The organization SSR route receives classified SSR targets.
- The planner rejects Mist Edge.
- The aggregate survives a process restart.
- Each child has no more than one write attempt.
- Repeated form posts start no second cloud write.
- Partial and unknown results remain visible.
- All tests run offline.
- No live Mist write occurs.
