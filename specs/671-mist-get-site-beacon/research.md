# Research: getSiteBeacon

## Decision 1: SDK invocation pattern

- **Decision**: Use `mistapi.api.v1.sites.beacons.getSiteBeacon(apisession, site_id=..., beacon_id=...)` as a single-record read operation with no pagination loop.
- **Rationale**: Official API docs for `/api/v1/sites/{site_id}/beacons/{beacon_id}` define a single object response and no query params; this avoids unnecessary iteration complexity.
- **Alternatives considered**:
  - Reusing list endpoint (`listSiteBeacons`) and filtering client-side — rejected because it over-fetches and can miss exact server-side semantics.
  - Raw HTTP request wrapper — rejected because constitution and project constraints prefer `mistapi` SDK when method exists.

## Decision 2: Primary key strategy

- **Decision**: Register `getSiteBeacon` in `ENDPOINT_PRIMARY_KEY_STRATEGIES` as `natural_pk` with primary key `id`.
- **Rationale**: Beacon entities already use globally stable UUID `id` in existing strategy entries (`listSiteBeacons`), and get-by-id responses represent the same resource model.
- **Alternatives considered**:
  - Composite key (`site_id`, `id`) — rejected as redundant because `id` is unique and simpler for upsert behavior.
  - Auto-increment strategy — rejected because it breaks natural-key consistency and repeat-run dedupe behavior.

## Decision 3: Input, resilience, and export flow

- **Decision**: Follow existing menu operation pattern: collect IDs with `safe_input()`, log before/after API calls, honor existing retry/rate-limit controls, and persist via `DataExporter.write_with_format_selection(..., api_function_name='getSiteBeacon')`.
- **Rationale**: This directly satisfies FR-002/003/004/006 and maintains behavior parity across CSV, SQLite, and ArangoDB/Redis.
- **Alternatives considered**:
  - Custom exporter path for beacon-only output — rejected to avoid bypassing backend router and snapshot logic.
  - Silent failures on 404/429 — rejected; operator-visible warnings are required for observability.

## Decision 4: Documentation and menu registration scope

- **Decision**: Keep scope limited to Issue #1420 by updating the next available menu entry plus README/CHANGELOG and endpoint strategy records only.
- **Rationale**: Spec requires additive endpoint coverage without broader UI or architectural changes.
- **Alternatives considered**:
  - Bundle adjacent missing endpoint work in same change — rejected due to scope creep and issue isolation requirement.
