# WAN Feature Ownership: MistCircuitStats Redis Dashboard

**Status**: Proposal only. No product change is authorized by this record.

## Current Main

`main` does not include PR #4208. Do not treat files from that pull request as available in this branch.

## Proposed Canonical Owner

PR #4208 is the proposed canonical owner for the overlapping WAN dashboard feature. Its current changed-file list and description include:

| Capability | Proposed owner | Status |
|---|---|---|
| WAN overview and gateway views | #4208 | Open, not merged |
| WAN port and peer-path views | #4208 | Open, not merged |
| Gateway insight collection | #4208 | Open, not merged |
| Mist API request admission | #4208 | Open, not merged |
| Snapshot cache and refresh store | #4208 | Open, not merged |
| Offline preview and synthetic data | #4208 | Open, not merged |
| Source-specific background refresh behavior | Unassigned | Verify against source and ask both feature owners |

Issue #4195 remains active and covers overlapping MistCircuitStats WAN views. Issue #4200 remains open. The feature owners must confirm these assignments before product work begins.

## MistCircuitStats-Redis Boundary

This feature owns no independent dashboard page, WAN collector, gateway insight request, peer-path request, Redis store, request-admission mechanism, or offline preview.

The source-specific worker may be a unique behavior because the source guide documents periodic refresh. The current source implementation and the #4195 work are not verified here. Do not create a worker until both owners confirm that the behavior is unique and assign its exact path.

## Blocking Contract

The gateway insight response shape remains unverified against the source's expected fields. The current OpenAPI candidate does not by itself prove that source metrics, units, timestamps, and port identifiers map to the selected SDK response. Resolve this mismatch in `contracts/mist-api.md` before any insight request or dashboard change.

## Implementation Gate

1. Confirm the accepted and landed scope of #4195, #4200, and #4208.
2. Confirm one owner for each view, request, cache key, and refresh worker.
3. Resolve the gateway insight response mismatch with source and SDK evidence.
4. Confirm Redis key ownership, serialization, TTL, lease, and outage behavior.
5. Implement only an independently assigned behavior. Otherwise, keep #4220 planning-only.
