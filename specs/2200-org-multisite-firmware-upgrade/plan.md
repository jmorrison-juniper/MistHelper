# Implementation Plan: Organization Multi-Site Firmware Upgrade

**Issue**: #2475
**Status**: Planned
**Specification**: `spec.md`

## Summary

The portal adds one aggregate operation for a mixed device selection. The
aggregate contains child jobs for APs, switches, Junos gateways, and SSR
gateways.

The AP child uses the organization device endpoint. Switch and Junos gateway
children use site routes from `src/firmware/upgrade_service.py`. SSR children
use the existing organization SSR route. The planner rejects Mist Edge.

## Source Decision

The OpenAPI description limits
`POST /api/v1/orgs/{org_id}/devices/upgrade` to AP upgrades.

The schema permits `device_type` values `ap`, `switch`, and `gateway`. It also
permits `firmware_type` values `ap` and `junos`.

The saved organization guide shows an AP record and a Junos switch record in
one organization request. The example also contains syntax defects.

The plan follows the narrower verified description. Only the AP child uses the
organization device endpoint.

## Architecture

| Concern | Location |
| - | - |
| Portal routes | `src/upgrade_portal/app/routes/` |
| Aggregate records | `src/upgrade_portal/runtime/runs.py` |
| Existing family planning | `src/firmware/upgrade_service.py` |
| AP organization service | `src/firmware/org_upgrade_service.py` |
| Browser flow | Jinja templates and `portal.js` |
| Offline tests | `tests/unit`, `tests/contract`, `tests/integration`, `tests/e2e` |

## Phase 1: Build the Target Snapshot

1. Read the selected organization and sites.
2. Read the selected device identifiers.
3. Verify that each site belongs to the organization.
4. Verify that each device belongs to a selected site.
5. Normalize the UI families to AP, switch, or gateway.
6. Reject every Mist Edge target.
7. Classify each gateway as Junos or SSR.

The snapshot keeps the organization, sites, device identifiers, models, family,
and requested version. Later steps do not rebuild the target set.

## Phase 2: Build Child Plans

Create one AP organization child when the snapshot contains AP targets. Include
all selected AP sites in that child.

Call `plan_upgrade` for each site group of switches and Junos gateways. Preserve
the returned endpoint, scope, body, target identifiers, and warnings.

Call the same planner for gateway targets. If it classifies a gateway as SSR,
preserve the returned organization SSR route.

Each child receives a durable child identifier before confirmation.

## Phase 3: Store the Aggregate

Create the aggregate before a cloud write. Store the confirmed plan and all
child records in one durable operation.

Use atomic compare-and-set updates for these transitions:

- `planned` to `claimed`
- `claimed` to `accepted`, `failed`, or `unknown`
- an active state to `cancel_claimed`
- `cancel_claimed` to `cancelled`, `cancel_failed`, or `cancel_unknown`

The claim token prevents a second request from sending the same child.

## Phase 4: Protect the Submission

Check these conditions before the first child claim:

1. The authenticated user owns the operation.
2. The operation belongs to the active organization.
3. Every selected site belongs to that organization.
4. The user still holds each required site lock.
5. The posted confirmation matches the stored plan.
6. The confirmation text matches exactly.
7. The request has a valid CSRF token.

Repeat the ownership, organization, site, and lock checks before each child
claim. Stop the sequence when a check fails.

## Phase 5: Submit Without Retries

Use a write session with zero SDK retries and zero transport retries.

For each child:

1. Atomically claim the child.
2. Send one cloud request.
3. Store the cloud identity and raw status.
4. Store a clear error when the cloud rejects the request.
5. Store `unknown` when the result can include an accepted remote write.
6. Continue only when policy permits another independent child.

Never replay a claimed child. A later reconciliation read can resolve an
unknown child.

## Phase 6: Show Aggregate Progress

The progress page shows:

- The aggregate state.
- The organization and selected sites.
- One row for each child.
- The UI family term.
- The exact route and scope.
- The target count and target identifiers.
- The cloud job identifier.
- The submit and cancel states.
- The latest error.

The page polls read routes only. A page load or poll never submits a child.

## Phase 7: Cancel Safely

The server checks ownership, organization, CSRF, and confirmation before a
cancel request.

The aggregate cancellation worker processes only submitted children. It selects
the cancel route from the stored child route. It sends each cancel request at
most once.

The aggregate can end with mixed cancel results. It preserves `cancel_unknown`.
It does not mark a child as rolled back.

## Phase 8: Test Offline

### Unit tests

Test AP aggregation, site grouping, gateway classification, Mist Edge
rejection, aggregate state calculation, and claim transitions.

### Contract tests

Test the organization AP body, site bodies, SSR body, status reads, cancel
calls, and malformed answers.

### Integration tests

Test process restarts, partial submission, unknown outcomes, duplicate browser
posts, stale confirmations, lock loss, and cross-user access.

### Playwright tests

Test this sequence:

`organization -> mode -> sites -> options -> confirmation -> progress`

Test AP-only, switch-only, gateway-only, and mixed selections. Use network
stand-ins. Do not send a live Mist write.

## Validation

Run the smallest offline suites first. Then run the full portal suite. Run the
Markdown STE linter for every changed specification file.

Do not run a manual firmware upgrade as part of this issue.

## Risks and Controls

| Risk | Control |
| - | - |
| The schema suggests an unsafe organization route | Route only APs through that endpoint |
| A repeated post starts another child | Use a durable claim and reject replays |
| A timeout hides an accepted write | Store `unknown` and require reconciliation |
| A partial sequence loses completed work | Store every child transition durably |
| A stale site selection crosses organizations | Check organization and site ownership again |
| A lock expires during submission | Check each lock before each child claim |
| A cancel result is uncertain | Store `cancel_unknown` and do not retry |
| A gateway receives the wrong route | Use the existing gateway classifier |
