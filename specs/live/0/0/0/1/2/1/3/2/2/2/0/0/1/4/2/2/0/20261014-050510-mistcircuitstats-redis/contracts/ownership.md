# WAN Feature Ownership: MistCircuitStats Redis Dashboard

**Status**: Reviewed 2026-10-18. No product change is authorized by this record.

## Current Main

PR #4252 merged on 2026-10-16 and closed #4195. The existing dashboard serves `/wan-dashboard` from `src/interfaces/portals/wan_dashboard/`.

Its `services.py` supplies SDK collection, request admission, and the shared-client Redis cache. Its `routes.py` supplies the dashboard and read routes. Integration tests live in `tests/integration/web_portal/wan_dashboard/`. These are existing paths, not assignments to #4220.

`main` does not include draft PR #4208. Do not treat its `wan_performance` files as available product behavior.

## Existing and Proposed Owners

| Capability | Existing baseline | Remaining proposal or decision |
|---|---|---|
| WAN overview and gateway views | Merged #4252 dashboard | #4208 overlaps. Add no second view. |
| WAN port and peer-path views | Merged #4252 dashboard | Reconcile any unique gap with the owners. |
| Gateway insight collection | #4252 SDK collector | Source request and response parity remains unproven. |
| Mist API request admission | #4252 shared-session collection path | #4208 proposes additional admission behavior. Do not duplicate it. |
| Snapshot cache and refresh store | #4252 `wan-dashboard:v1:` cache | #4208 proposes a refresh store. No #4220 cache policy has approval. |
| Offline preview and synthetic data | #4252 synthetic test coverage | #4208 proposes offline preview. No source screenshot reuse has approval. |
| Source-specific background refresh behavior | Unassigned | Require unique scope, one writer, and an exact owner-assigned path. |

Issue #4195 is closed. Issue #4200 remains open. The feature owners must approve any unique #4220 assignment before product work begins.

## MistCircuitStats-Redis Boundary

This feature owns no independent dashboard page, WAN collector, gateway insight request, peer-path request, Redis store, request-admission mechanism, or offline preview.

A source-specific periodic refresh may be unique, but this review grants no approval. Compare it with the existing dashboard and #4208 proposal. Do not create a worker until owners approve the behavior and its exact path.

## Blocking Contract

The gateway insight response shape remains unverified against the source's expected fields. The current OpenAPI candidate does not by itself prove that source metrics, units, timestamps, and port identifiers map to the selected SDK response. Resolve this mismatch in `contracts/mist-api.md` before any insight request or dashboard change.

## Implementation Gate

1. Confirm the accepted and landed scope of #4195, #4200, and #4208.
2. Confirm one owner for each view, request, cache key, and refresh worker.
3. Resolve the gateway insight response mismatch with source and SDK evidence.
4. Confirm Redis key ownership, serialization, TTL, lease, and outage behavior.
5. Implement only an independently assigned behavior. Otherwise, keep #4220 planning-only.
