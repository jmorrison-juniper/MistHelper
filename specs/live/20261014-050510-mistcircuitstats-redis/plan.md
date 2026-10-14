# Implementation Plan: MistCircuitStats Redis Dashboard Migration

**Branch**: `3993-mistcircuitstats-redis` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

**Input**: Timestamp feature specification in `specs/live/20261014-050510-mistcircuitstats-redis/spec.md`

## Summary

Migrate only verified MistCircuitStats-Redis behavior that is not already owned by the MistCircuitStats or MistWANPerformance efforts. Keep one MistHelper portal, one Mist API session, the existing Compose group, and existing storage. Reuse existing Redis only for a bounded, feature-owned cache. Do not copy source code or assets before maintainers approve license compatibility.

The current proposals overlap on gateway, WAN port, peer-path, insight, and multi-site views. PR #4208 is the proposed canonical owner for these views, the refresh store, shared request admission, and offline preview. Issue #4195 remains active. Issue #4200 and PR #4208 remain open. The mapping in [contracts/ownership.md](contracts/ownership.md) records #4208 as a proposal, not merged product behavior. Do not add a second page, collector, cache, or API path. Any source-only refresh behavior remains blocked until the owners confirm its unique scope and path.

## Technical Context

**Language/Version**: Python 3.13 or newer, as required by `pyproject.toml`.

**Primary Dependencies**: The existing Mist API SDK (`mistapi>=0.64.0,<0.65`), Flask portal, Redis client, and project services. Add no dependency unless the implementation gate proves a need.

**Storage**: Existing MistHelper Redis for an approved transient snapshot cache. Use existing configured application storage only if an accepted journey requires durable history. Add no database.

**Testing**: Existing pytest suite, portal test client, and Playwright tests. Use mocked Mist responses and fictional records. Do not use production credentials.

**Target Platform**: Existing MistHelper web portal and its current Compose group on Windows, macOS, and Linux deployments.

**Project Type**: Existing Python web portal. Do not create a second application or service.

**Performance Goals**: Respect shared Mist API admission and bounded page sizes. The source implementation review reports a 300-second refresh interval, four parallel workers, and a 31-day cache TTL. Set MistHelper values only after measuring API-call limits and freshness needs.

**Constraints**: No separate Redis service, database, application, Compose group, or public port. Do not duplicate collection or views owned by #4195 or #4200. Do not claim undocumented source behavior as complete. Keep synthetic data distinct from live data.

**Scale/Scope**: One source migration into the existing portal. Support multiple authorized sites, gateways, WAN ports, and peer paths only where a source-to-target review confirms the behavior and ownership.

## Constitution Check

### Before Research

- **Managed records**: The feature uses the required `specs/live/` root. It adds one timestamped feature record, not a new direct root.
- **Process-folder debt**: The guard data shows 795 direct children, with 792 grandfathered entries and three present managed roots. The measured roots are `live` with four entries, `numbered` with one, and `skills` with five. This feature adds no direct child to `specs/`. T024 tracks a separate incremental debt-reduction action. Do not change the baseline to make this feature pass.
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

1. **One portal owner**: Treat the #4208 proposal as the canonical owner for shared WAN views and services. Reuse it only after it lands or its owner assigns the path. Do not treat open code as part of `main`.
2. **One collection owner**: Compare the source's org, site, gateway, port, peer, and insight calls with current MistHelper collection. Assign each data set to one collector. Do not issue duplicate calls for the same result.
3. **Existing Redis only**: If a cache remains necessary after overlap review, reserve `misthelper:wan:mcsr:v1:<org_id>:<site_id>:<record_type>:<record_id>` for this feature. The cache contract must define its owner, version, serializer, TTL, and invalidation before code.
4. **Freshness-aware refresh**: Preserve a successful snapshot until a complete replacement is ready. Mark stale, partial, failed, or unavailable data explicitly. Do not label a stale snapshot as live.
5. **Shared API admission**: Route collection through the existing MistHelper session and request admission. Bound pagination and concurrent work by the approved shared policy. Do not rotate independent tokens.
6. **No automatic source parity**: The source implementation review reports `PARALLEL_WORKERS=4`, `WORKER_INTERVAL=300`, `STALE_THRESHOLD=600`, incremental refresh, and cached-on-startup behavior. The guide reports five workers and a TTL of three intervals, while implementation reports a 31-day TTL. Verify remaining settings and behavior against source tests before deciding what MistHelper requires.
7. **No source copy**: Preserve provenance in planning artifacts. Use independently written code unless maintainers confirm license compatibility and approve reuse.

## Project Structure

### Documentation (this feature)

```text
specs/live/20261014-050510-mistcircuitstats-redis/
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

PR #4208 proposes WAN collection, storage, request admission, offline preview, and presentation under `src/interfaces/portals/wan_performance/`. It is open and is not part of `main`. Issue #4195 is active and overlaps on the same WAN data. This feature owns no standalone product path. Do not implement a second route, collector, cache, admission ledger, or preview. A source-only refresh lifecycle may proceed only after both owners confirm that no existing change owns it and assign one exact target path.

**Structure Decision**: No product source or test path is approved. Keep product files out of the planning PR. Keep all source-specific work blocked until owners approve unique scope, the gateway insight response mismatch is resolved, and the Redis contract passes.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None approved | The plan adds no executable code or project hierarchy. | No product structure decision is safe before overlap and ownership review. |
