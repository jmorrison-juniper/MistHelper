# Implementation Plan: MistCircuitStats Redis Dashboard Migration

**Branch**: `3993-mistcircuitstats-redis` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

**Input**: Timestamp feature specification in `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/spec.md`

**Reviewed**: 2026-10-18. PR #4223 merged this planning record. This refresh changes no product files.

## Summary

Migrate only verified MistCircuitStats-Redis behavior that is not already owned by the MistCircuitStats or MistWANPerformance efforts. Keep one MistHelper portal, one Mist API session, the existing Compose group, and existing storage. Reuse existing Redis only for a bounded, feature-owned cache. Do not copy source code or assets before maintainers approve license compatibility.

PR #4252 delivered the existing WAN dashboard and closed #4195. Issue #4200 and draft PR #4208 remain open with overlapping proposed behavior. The mapping in [contracts/ownership.md](contracts/ownership.md) separates existing behavior from that proposal. Do not add a second page, collector, cache, or API path. Source-only refresh behavior remains blocked until the owners confirm its unique scope and path.

## Technical Context

**Language/Version**: Python 3.13 or newer, as required by `pyproject.toml`.

**Primary Dependencies**: The existing Mist API SDK (`mistapi>=0.64.0,<0.65`), Flask portal, Redis client, and project services. Add no dependency unless the implementation gate proves a need.

**Storage**: Reuse the existing dashboard cache only after owner approval. Its current namespace and TTL values appear in [contracts/redis-cache.md](contracts/redis-cache.md). No #4220 cache policy has approval. Add no database.

**Testing**: Existing pytest suite, portal test client, and Playwright tests. Use mocked Mist responses and fictional records. Do not use production credentials.

**Target Platform**: Existing MistHelper web portal and its current Compose group on Windows, macOS, and Linux deployments.

**Project Type**: Existing Python web portal. Do not create a second application or service.

**Performance Goals**: Respect shared Mist API admission and bounded page sizes. The source implementation review reports a 300-second refresh interval, four parallel workers, and a 31-day cache TTL. Set MistHelper values only after measuring API-call limits and freshness needs.

**Constraints**: No separate Redis service, database, application, Compose group, or public port. Do not duplicate collection or views owned by #4195 or #4200. Do not claim undocumented source behavior as complete. Keep synthetic data distinct from live data.

**Scale/Scope**: One source migration into the existing portal. Support multiple authorized sites, gateways, WAN ports, and peer paths only where a source-to-target review confirms the behavior and ownership.

## Constitution Check

### Before Research

- **Managed records**: Refresh the existing grouped `specs/live/` record. Create no feature directory and change no tracked feature selector.
- **Process-folder debt**: The established record exceeds five children. This refresh adds none and does not restructure unrelated records. T024 retains the separate debt action. Historical counts belong to the original review, not this refresh.
- **Product boundaries**: No product code, Compose file, public port, container, application service, or database changes belong in this planning PR.
- **Mist API**: All REST requests must use working `mistapi` methods. The candidate methods in [research.md](research.md) need source-to-SDK verification. Add no owned WebSocket transport.
- **Shared admission**: The design must use MistHelper's shared API request admission. It must not introduce a separate API client, token store, or hidden retry path.
- **Redis safety**: Any reused key needs one named owner, an isolated versioned namespace, a defined TTL and serialization, and explicit outage behavior. No shared key may overwrite another feature's value.
- **Source rights**: The source declares CC BY-NC-SA 4.0. No source code or assets may be copied until maintainers confirm rights and license compatibility.
- **Testing**: Contract, integration, and browser tests must use mocked API responses and synthetic records. Test API failures, Redis failures, partial refresh, tenant isolation, and secret redaction.
- **Logging and input**: Future code must validate organization and record identifiers, keep secrets out of logs, and follow the repository's action logging rules.

**Gate result**: Pass for planning. Product implementation may start only after the source behavior, license, API contract, Redis boundary, and single-owner decisions are recorded. Keep product implementation in a separate PR from this planning change.

### After Design

- One canonical owner must serve each view and collection path.
- Redis may hold transient dashboard snapshots only. It must not become a second application database or a durable history source.
- A failed refresh must not publish an invalid or partial replacement snapshot.
- Redis loss must not trigger unadmitted live Mist calls from portal reads.
- A source feature flag or tuning value may enter the target only after source implementation and test evidence confirm its behavior.
- All unknown API fields, pagination parameters, rate limits, cache limits, and license decisions remain implementation blockers until verified.
- Start only work with a verified, unique owner. Keep overlapping view or collection work blocked until the owners of #4195 and #4200 resolve the conflict.

## Phase 0: Research

See [research.md](research.md). The research records current repository evidence, unverified source claims, related proposal ownership, current OpenAPI candidates, source provenance, cache choices, and bounded investigation actions.

## Phase 1: Design and Contracts

See [data-model.md](data-model.md), [contracts/mist-api.md](contracts/mist-api.md), [contracts/redis-cache.md](contracts/redis-cache.md), and [quickstart.md](quickstart.md).

### Design Decisions

1. **One portal owner**: Reuse the existing #4252 dashboard where it meets the accepted journey. Treat #4208 as proposed behavior only. Require owner approval before changing either path.
2. **One collection owner**: Compare the source's org, site, gateway, port, peer, and insight calls with current MistHelper collection. Assign each data set to one collector. Do not issue duplicate calls for the same result.
3. **Existing Redis only**: Review the existing `wan-dashboard:v1:` cache before proposing any change. The old `misthelper:wan:mcsr:v1:` candidate is unreserved and unapproved. Approve one owner, version, serializer, TTL, and invalidation policy before code.
4. **Freshness-aware refresh**: Preserve a successful snapshot until a complete replacement is ready. Mark stale, partial, failed, or unavailable data explicitly. Do not label a stale snapshot as live.
5. **Shared API admission**: Route collection through the existing MistHelper session and request admission. Bound pagination and concurrent work by the approved shared policy. Do not rotate independent tokens.
6. **No automatic source parity**: The source implementation review reports `PARALLEL_WORKERS=4`, `WORKER_INTERVAL=300`, `STALE_THRESHOLD=600`, incremental refresh, and cached-on-startup behavior. The guide reports five workers and a TTL of three intervals, while implementation reports a 31-day TTL. Verify remaining settings and behavior against source tests before deciding what MistHelper requires.
7. **No source copy**: Preserve provenance in planning artifacts. Use independently written code unless maintainers confirm license compatibility and approve reuse.

## Project Structure

### Documentation (this feature)

```text
specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/
├── spec.md
├── checklists/
│   └── requirements.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/
│   ├── mist-api.md
│   ├── ownership.md
│   └── redis-cache.md
├── quickstart.md
├── tasks.md
└── analysis.md
```

### Product Code and Tests

The existing dashboard lives under `src/interfaces/portals/wan_dashboard/` and serves `/wan-dashboard`. Its tests live under `tests/integration/web_portal/wan_dashboard/`, with portal browser coverage under `tests/e2e/web_portal/`. PR #4208 proposes a separate `src/interfaces/portals/wan_performance/` package but remains open and is not part of `main`. These paths are evidence, not #4220 assignments. This feature owns no standalone product path. Do not implement a second route, collector, cache, admission ledger, or preview. A source-only refresh lifecycle requires approved unique scope and an exact owner-assigned path.

**Structure Decision**: No product source or test path is approved. Keep product files out of the planning PR. Keep all source-specific work blocked until owners approve unique scope, the gateway insight response mismatch is resolved, and the Redis contract passes.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None approved | The plan adds no executable code or project hierarchy. | No product structure decision is safe before overlap and ownership review. |
