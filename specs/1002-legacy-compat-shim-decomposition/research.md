# Research: Legacy Compat Shim Decomposition

## Decision 1: Canonical ownership stays in existing `src` modules, no new utility sink
- **Decision**: Keep migrated behavior in current domain modules (`src/export/site_insights`, `src/capture`, `src/menu`, and existing utility owners) and do not add a new aggregation helper.
- **Rationale**: Matches FR-002 and constitution class-based architecture constraints; reduces future indirection and ownership ambiguity.
- **Alternatives considered**:
  - Create a new central shim-replacement helper module: rejected because it recreates indirection and violates explicit ownership intent.
  - Keep dynamic facade with additional branches: rejected because it extends compatibility debt.

## Decision 2: Shim retirement by controlled adapter lifecycle
- **Decision**: Classify every inventory row into remove/direct-import/temporary-adapter and enforce adapter expiry dates as hard gates.
- **Rationale**: Meets FR-003, FR-009, and SC-001 while preventing indefinite compatibility drift.
- **Alternatives considered**:
  - Immediate hard removal for all shims: rejected due to menu/test harness break risk.
  - Open-ended deprecations: rejected because no enforcement leads to permanent debt.

## Decision 3: `__init__.py` compatibility hub decomposed into explicit imports and scoped adapters
- **Decision**: Retire listed `__getattr__` branches and replace retained compatibility needs with direct import bindings or narrowly scoped temporary adapters.
- **Rationale**: Satisfies FR-006 and lowers runtime surprise from dynamic attribute dispatch.
- **Alternatives considered**:
  - Keep `__getattr__` and add warnings only: rejected because it preserves hidden control flow.

## Decision 4: Capture workflows standardize on `execute()` with temporary `run()` adapters
- **Decision**: Keep `run()` only as temporary adapter in site/org pcap workflows until 2026-08-31, then remove.
- **Rationale**: Supports FR-005 and phased test migration without immediate breakage.
- **Alternatives considered**:
  - Keep both methods permanently: rejected as permanent alias debt.

## Decision 5: Site insights callsites move off `InsightMetricsUtils.export_legacy()`
- **Decision**: Replace callsites in `site_metric_operation.py` and `device_metric_operation.py` with direct canonical export/cache refresh entry points in `src/export/site_insights`.
- **Rationale**: Required by FR-004 and FR-006; directly targets SC-003.
- **Alternatives considered**:
  - Keep bridge and wrap canonical inside legacy API: rejected because it hides migration completion.

## Decision 6: Menu fallback retirement uses parity checkpoints and rollback criteria
- **Decision**: `_noop_menu_action` and `_ensure_menu_coverage` remain only as transitional adapters until registry parity is proven; then retire.
- **Rationale**: Supports FR-007 and SC-005 while managing operational risk.
- **Alternatives considered**:
  - Remove fallback immediately: rejected because incomplete registry parity could break operator flows.

## Decision 7: Validation relies on static callsite guards + parity suite + migration inventory checks
- **Decision**: Add static checks for prohibited symbols, run scoped parity checks after each phase, and validate decision completeness against migration inventory.
- **Rationale**: Covers SC-002/SC-003/SC-004/SC-006 and prevents shim reintroduction.
- **Alternatives considered**:
  - Manual review-only verification: rejected as too error-prone for long-lived decomposition work.

## Decision 8: Documentation/changelog delivered in same release window as code migration
- **Decision**: Ship `README.md` compatibility notes and `CHANGELOG.md` entries concurrently with each decommission phase.
- **Rationale**: Required by FR-010 and SC-007; avoids hidden behavior changes.
- **Alternatives considered**:
  - Batch docs at end only: rejected because users lose migration visibility during phased rollout.
