# Implementation Plan: WAN Performance portal integration

**Branch**: `feat/4200-wan-portal-integration` (planned) | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification from `specs/numbered/0/0/1/1/3/3/0/0/4200-wan-portal-integration/spec.md`.

Keep `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Add a WAN Performance area to the existing MistHelper web portal. The area has four pages: overview, gateway, WAN port, and VPN peer. It also has a synthetic preview. Live data uses mistapi functions, bounded calls, the configured store, and `misthelper:wan:v1:` Redis keys. PR 4208 holds a draft of this work, but it is DIRTY and fails the five-child rule. This plan keeps main as the base and ports the reviewed parts of PR 4208.

## Technical Context

**Language/Version**: Python 3.15 (`pyproject.toml` requires `>=3.15`).

**Primary Dependencies**: `mistapi>=0.64.0,<0.65` (installed 0.64.1, R118), Flask portal in `web_portal/`, `redis` client already imported by main WAN modules (`request_admission.py` L10-12, `refresh_store.py` L8-10).

**Storage**: Configured store only: SQLite `data/mist_data.db` or ArangoDB, selected through `DataExporter.write_with_format_selection()` (D-7). Redis keys for coordination only (D-4).

**Testing**: pytest unit tests under `tests/unit/wan_performance/`, pytest and Playwright browser tests under `tests/e2e/web_portal/`, and `tests/guardrails` for structure guards.

**Target Platform**: Windows 11, macOS, and Linux. The container runs the same code on Podman. The feature adds no container and no port.

**Project Type**: Web portal feature inside the `src/interfaces/` package.

**Performance Goals**: 100 records per Mist page (`SNAPSHOT_PAGE_LIMIT`, R60). 2 peer rows (`PEER_ROW_LIMIT`, R58). 5000 requests per rolling hour (`RequestLedger.LIMIT`, R59). Overview request uses at most 2 gateway calls (FR-009).

**Constraints**: No new service, port, database, or container (FR-011, FR-012, SC-008). Constitution rules in the next section.

**Scale/Scope**: One organization lease per worker. Four pages. Thirteen new test modules, one of them a guard (tests_planned in `4200-STATUS.json`).

## Constitution Check

Each rule has a result and a reason. "Fail as found" means that PR 4208 breaks the rule. The remediation column names the task that fixes it.

| Rule | Result | Reason and evidence | Remediation task |
|---|---|---|---|
| I. Five-item rule | Fail as found | PR 4208 gives `src/interfaces/wan_performance/`, `collection/`, `domain/`, `integration/`, and `presentation/` six children each (R106). | T033 |
| I. Five-item rule | Pass for this record | `specs/numbered/` managed root, route from `spec-route.ps1` base 5 (R87). Feature root holds five children. | none |
| II. Class-based architecture | Fail as found | Route handlers `overview()` (`routes.py` L78, `live_routes.py` L269) are module-level functions (R92, R93). The existing WAN dashboard uses page classes (R79). | T017, T018 |
| III. Safety first | Pass with tasks | Identifier validation exists (`IdentityValidator`, R63). Redaction and tests are in T021 and T022. | T021, T022 |
| IV. Full pipeline | Pass with tasks | Gates, pull request, CI, and merge are T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. | final tasks |
| V. Observability | Fail as found | PR 4208 WAN modules use `logging.getLogger` (R107). 22 repository files use structlog (R134). | T021 |
| VI. Inline comments | Fail as found | Sampled line `routes.py` L80 has no inline comment (R93). | T017, T018 |
| VII. Action logging | Partial as found | PR 4208 logs some actions but not each action (R90, R107). | T021 |
| Technology: mistapi only | Pass | Calls use mistapi functions (R119-R123). No direct HTTP. | T007 |
| Technology: owned WebSocket | Not applicable | The feature opens no WebSocket transport. | none |
| Technology: test containers | Pass | No container and no published port (R81, R82). | T028 |
| Technology: output backends | Fail as found | PR 4208 writes SQLite and ArangoDB rows directly (`integration/sqlite_history.py`, `integration/arango_history.py`, R133). The constitution requires `DataExporter.write_with_format_selection()` (line 312). | T012 |
| Technology: operational store | Pass with definition | Redis coordination has fail-closed behavior, TTLs, and no backup need (D-4, FR-012). | T009, T010 |
| Technology: database keys | Pass | Natural keys in `4200-wan-portal-integration/design/data-model.md`. | T012 |
| Technology: data directory | Pass | Product output stays in `data/`. | T012 |
| Escalation rule | Pass | This record exists because the change touches more than three files. | none |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/3/3/0/0/4200-wan-portal-integration/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      routes.md
      mist-api-calls.md
      storage-and-cache.md
    checklists/
      requirements.md
      security.md
```

### Target source layout

Each directory holds five children or fewer. The nested layout replaces the PR 4208 layout (R106, D-15).

```text
src/interfaces/wan_performance/
  __init__.py
  collection/            (__init__, live_service, peer_insights, snapshot_client, snapshot_records)
  domain/                (__init__, identity, measurement, metric_validation, aggregation)
    aggregation/         (__init__, calendar, summary)
  integration/           (__init__, admission, refresh, storage)
    admission/           (__init__, request_admission)
    refresh/             (__init__, background_refresh, refresh_store)
    storage/             (__init__, history_repository, sqlite_history, arango_history, record_codec)
  presentation/          (__init__, live, offline, routes.py, templates)
    live/                (__init__, live_routes, inspection)
    offline/             (__init__, offline_preview)
```

## File-by-File Change Map

Action values: add, modify, move, or delete. The "Source" column gives the row in `design/research.md`.

| Action | Repository path | Purpose | Source |
|---|---|---|---|
| modify | `web_portal/app.py` | Register the WAN performance blueprint. Gate the nav on `wan_performance.live.overview`. Start the worker only when `WAN_BACKGROUND_REFRESH=true`. | R71, R97 |
| modify | `web_portal/templates/base.html` | Add the nav entry inside the `WAN_PERFORMANCE_NAV_ENABLED` block. | R72, R98 |
| modify | `deploy/.env.example` | Document `WAN_BACKGROUND_REFRESH` with default `false`. Keep `WAN_SHARED_ADMISSION` commented. | R73, R105 |
| modify | `src/foundation/support/refactors/initialize_mist_session.py` | Add the shared admission hook. Keep existing private helper names unless the symbol gate approves a rename. | R74, R99 |
| modify | `src/interfaces/wan_performance/__init__.py` | Keep the package export list. | R56 |
| modify | `src/interfaces/wan_performance/collection/__init__.py` | Export the collection classes. | R57 |
| modify | `src/interfaces/wan_performance/collection/peer_insights.py` | Keep the peer row limit of 2. | R58 |
| modify | `src/interfaces/wan_performance/collection/snapshot_client.py` | Keep mistapi calls and the 100-record page limit. | R60, R130 |
| modify | `src/interfaces/wan_performance/collection/snapshot_records.py` | Keep the snapshot record builders. | R61 |
| move | `src/interfaces/wan_performance/collection/request_admission.py` to `src/interfaces/wan_performance/integration/admission/request_admission.py` | Shared admission ledger. Change the Redis failure path per D-4. | R59 |
| modify | `src/interfaces/wan_performance/domain/__init__.py` | Export the domain classes. | R62 |
| modify | `src/interfaces/wan_performance/domain/identity.py` | Keep `IdentityValidator` and the identity classes. | R63 |
| modify | `src/interfaces/wan_performance/domain/measurement.py` | Keep the measurement classes. | R64 |
| modify | `src/interfaces/wan_performance/domain/metric_validation.py` | Keep the metric validator. | R65 |
| add | `src/interfaces/wan_performance/domain/aggregation/calendar.py` | UTC calendar windows for daily, weekly, and monthly summaries. | R133 |
| add | `src/interfaces/wan_performance/domain/aggregation/summary.py` | Summary values from hourly rows with equal weights. | R133 |
| move | `src/interfaces/wan_performance/integration/refresh_store.py` to `src/interfaces/wan_performance/integration/refresh/refresh_store.py` | Refresh lease and snapshot keys with TTLs. | R66 |
| add | `src/interfaces/wan_performance/integration/refresh/background_refresh.py` | Background worker with one lease per organization. Replaces the PR 4208 path at `src/interfaces/wan_performance/background_refresh.py`. | R68, R90 |
| add | `src/interfaces/wan_performance/integration/storage/history_repository.py` | Repository for hourly rows and declarations through the configured store. | R133 |
| add | `src/interfaces/wan_performance/integration/storage/sqlite_history.py` | SQLite adapter behind `DataExporter`. | R133 |
| add | `src/interfaces/wan_performance/integration/storage/arango_history.py` | ArangoDB adapter behind `DataExporter`. | R133 |
| add | `src/interfaces/wan_performance/integration/storage/record_codec.py` | Record encoding for stored rows. | R133 |
| add | `src/interfaces/wan_performance/collection/live_service.py` | Live service that combines snapshot, history, and admission. | R91 |
| add | `src/interfaces/wan_performance/presentation/routes.py` | Synthetic preview blueprint at `/wan-performance/preview/`. Class-based page handlers. | R93 |
| add | `src/interfaces/wan_performance/presentation/live/live_routes.py` | Live blueprint at `/wan-performance/live/`. Class-based page handlers. | R92 |
| add | `src/interfaces/wan_performance/presentation/offline/offline_preview.py` | Synthetic records with `data_origin` set to `synthetic`. | R94 |
| add | `src/interfaces/wan_performance/presentation/templates/wan_performance/overview.html` | Overview page with stable `data-testid` attributes. | R96 |
| add | `src/interfaces/wan_performance/presentation/templates/wan_performance/live.html` | Live page template. | R95 |
| add | `web_portal/static/css/wan_performance.css` | Page styles. | R104 |
| add | `documentation/wan-performance.md` | Feature document with the source attribution and the no-copy rule. | R102 |
| add | `changelog.d/issue-4200-wan-portal-integration.md` | One fragment for the change. | R89 |
| add | `tests/guardrails/test_wan_portal_attribution.py` | Guard for source attribution and the changelog fragment (FR-020, FR-021). | R102, R89 |
| add | `tests/unit/wan_performance/__init__.py` | Test package marker. | R70 |
| add | `tests/unit/wan_performance/collection/test_snapshot_client.py` | Mistapi calls, page bounds, and missing data. | R60 |
| add | `tests/unit/wan_performance/collection/test_peer_insights.py` | Peer row bound and loss, latency, and jitter values. | R58 |
| add | `tests/unit/wan_performance/collection/test_live_service.py` | Live service states and API errors. | R91 |
| add | `tests/unit/wan_performance/domain/test_domain.py` | Identifier and measurement rules. | R63, R64 |
| add | `tests/unit/wan_performance/domain/test_calendar_summaries.py` | UTC windows and summary values. | R133 |
| add | `tests/unit/wan_performance/domain/test_offline_fixtures.py` | Synthetic record labels. | R94 |
| add | `tests/unit/wan_performance/integration/test_request_admission.py` | Shared admission limit and Redis outage. | R59 |
| add | `tests/unit/wan_performance/integration/test_refresh_store.py` | Refresh lease and snapshot TTL. | R66 |
| add | `tests/unit/wan_performance/integration/test_background_refresh.py` | Worker lease and stop behavior. | R90 |
| add | `tests/unit/wan_performance/integration/test_history_repository.py` | Natural keys and configured store writes. | R133 |
| add | `tests/e2e/web_portal/test_wan_performance_live.py` | Live browser journey. | R100 |
| add | `tests/e2e/web_portal/test_wan_performance_offline.py` | Synthetic browser journey. | R101 |
| keep | `tests/e2e/web_portal/test_wan_dashboard_cache_only.py` | Existing WAN dashboard tests. Must still pass. | R77 |
| keep | `tests/guardrails/test_src_public_symbol_preservation.py` | Public symbol guard. | R67 |
| delete | `tests/unit/wan_dashboard/wan_performance/` | Eight main test files moved to `tests/unit/wan_performance/`. Delete only after the moved tests pass. | R78 |

## Dependencies

- PR 4208 (draft, DIRTY, R01). The owner resolves the 11 add/add files, or this plan ports the changes (D-11).
- PR 4629 (merged, R06). Its 11 WAN files are the base (R56-R66).
- PR 4291 (merged, R10). Its Redis migration gates apply to the Redis keys.
- mistapi pin `>=0.64.0,<0.65` (R118).
- Redis service `misthelper-redis` in `compose.yml` (R81). No new Redis service.
- Configured store: SQLite or ArangoDB (R81).
- Playwright browser for the e2e tests (`documentation/quality-gates.md` playwright row, R83).

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| PR 4208 reconciliation drops merged PR 4629 content | Main is the base. Each port has a unit test (D-11). |
| Nav link breaks when live routes fail | The nav gate tests `wan_performance.live.overview` (FR-002, T004). |
| Background refresh exceeds Mist limits | Default off (D-5). Per-hour ceiling of 5000 requests (R59). |
| Redis outage blocks operator reads | Bounded local ceiling for operator reads (D-4). Stale state label (FR-015). |
| Historical writes bypass configured backends | Writes go through `DataExporter` (D-7, T012). |
| Closing keyword closes issue 4200 at merge | Pull request body uses `Refs #4200` (D-13). |
| Synthetic data appears on a live page | Separate route and `data_origin` check (D-10, SC-005). |
| Source reuse without rights | Independent implementation. Human decision D-1 owns any copy. |
| Five-child rule breaks in the new layout | Guard `tests/guardrails` reports counts. Each directory has five children or fewer (T033). |
| Retention purge destroys production history | No purge job in this feature. Human decision D-2 owns retention. |

## Rollback Steps

1. Set `WAN_BACKGROUND_REFRESH=false` in the environment and restart the portal. The worker stops.
2. Remove the nav gate by setting `WAN_PERFORMANCE_NAV_ENABLED` to `false`. The nav entry disappears.
3. Revert the merge commit of the feature pull request. Use a new pull request, not a force push.
4. Caution: deleting a Redis key stops its lease or snapshot. Delete only keys in the namespace `misthelper:wan:v1:`. Leave `misthelper:api:v1:` keys in place.
5. Warning: deleting store rows destroys history. Remove rows only in a separate reviewed change with a verified backup.

## Complexity Tracking

Each row names a violation that remains after the remediation. Each row names one grandfathered parent or one new direct child.

| Violation | Why needed | Simpler alternative rejected because |
|---|---|---|
| `tests/unit/` gains the direct child `wan_performance/` | Unit tests for the feature need one package with ownership | Adding the tests to another package hides the feature owner. |
| `tests/e2e/web_portal/` gains two direct children | Browser tests need the fixtures in `tests/e2e/conftest.py` (R76) | A nested package still adds one direct child to the grandfathered parent. |
| `documentation/` gains `wan-performance.md` | FR-021 requires one feature document | A nested folder still adds one direct child to the grandfathered parent. |

Remediation: the next incremental change moves each grandfathered folder into a nested package. The guard baseline (R88) records the debt.

## Contracts

The `design/contracts/` folder holds three files: `routes.md`, `mist-api-calls.md`, and `storage-and-cache.md`. The folder is not omitted.
