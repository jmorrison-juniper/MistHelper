# Implementation Plan: Polyglot Database Migration

**Branch**: `184-polyglot-db-migration` | **Date**: 2026-04-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/184-polyglot-db-migration/spec.md`

## Summary

Replace SQLite with ArangoDB (graph/document store) and Redis TimeSeries (metrics/stats) for containerized MistHelper deployments. The existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary (~53 entries) drives automatic routing: `natural_pk` and `auto_increment_with_unique` types route to ArangoDB, `composite_pk` types route to Redis TimeSeries. CSV output is preserved for all modes. Standalone mode (no containers) continues with CSV-only output. New `python-arango` and `redis` dependencies provide the Python client libraries. ArangoDB and Redis Stack services are added to `compose.yml` alongside the existing MistHelper and Ollama services.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: `mistapi>=0.61.4`, `python-arango>=8.3.2`, `redis>=7.4.0` (with hiredis)
**Storage**: ArangoDB 3.12 (documents + graph), Redis Stack (TimeSeries module), CSV files (always)
**Testing**: `pytest` + `pytest-cov`, `hypothesis` (property-based), `MistHelper.py --test`
**Target Platform**: Linux containers (Podman/Docker), Windows 11 standalone
**Project Type**: CLI tool with containerized multi-service deployment
**Performance Goals**: Data ingestion at least equivalent to current SQLite throughput (SC-003); time-series queries <1s for 100K data points (SC-004)
**Constraints**: Single-node only (no clustering); ArangoDB Community Edition 100GB dataset limit; all outputs to `data/` directory; non-root container user
**Scale/Scope**: 160+ menu operations, ~53 endpoint strategies, single-org deployments

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| - | - | - |
| I. Five-Item Rule | PASS | New classes (`ArangoDBWriter`, `RedisTimeSeriesWriter`, `DatabaseRouter`, `RetentionManager`, `SnapshotManager`) each under 5 public methods. `src/db/` package has max 5 modules. |
| II. Class-Based Architecture | PASS | All DB backends are classes (no wrapper functions). `DatabaseRouter` replaces direct SQLite calls. |
| III. Safety-First | PASS | No destructive operations added. DB credentials via `.env` only, never logged. Connection failures degrade gracefully to CSV. |
| IV. Full Deployment Pipeline | PASS | compose.yml updated; container build triggers on push to main. |
| V. Observability & Logging | PASS | New DB modules use `structlog` for structured, ASCII-only logging. Connection events logged at Info, queries at Debug. |
| Tech: Dual Output | PASS | CSV output preserved for all 160+ operations regardless of backend availability (FR-002). |
| Tech: Natural Business Keys | PASS | Mist API UUIDs used as ArangoDB `_key` values. No artificial IDs introduced. |
| Tech: ENDPOINT_PRIMARY_KEY_STRATEGIES | PASS | Existing dictionary drives routing logic. No strategy entries are removed or renamed. |
| Tech: File Paths | PASS | All new outputs use `os.path.join()` / `pathlib.Path()`. ArangoDB and Redis data stored under `data/` volume mount. |

## Project Structure

### Documentation (this feature)

```text
specs/184-polyglot-db-migration/
├── plan.md              # This file
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: entity/collection design
├── quickstart.md        # Phase 1: developer setup guide
├── contracts/           # Phase 1: interface contracts
│   └── database-router.md
└── tasks.md             # Phase 2 output (speckit.tasks)
```

### Source Code (repository root)

```text
src/
└── db/
    ├── __init__.py          # Package init, public exports
    ├── router.py            # DatabaseRouter: routes data by PK strategy type
    ├── arango_writer.py     # ArangoDBWriter: document/graph operations
    ├── redis_writer.py      # RedisTimeSeriesWriter: time-series operations
    └── retention.py         # RetentionManager: storage-aware rollover

MistHelper.py                # Modified: DataExporter delegates to DatabaseRouter
compose.yml                  # Modified: add arangodb + redis-stack services
requirements.txt             # Modified: add python-arango, redis[hiredis]
deploy/.env.example          # Modified: add DB connection vars

tests/
├── unit/
│   ├── test_router.py       # DatabaseRouter routing logic
│   ├── test_arango_writer.py # ArangoDB upsert/graph operations (mocked)
│   └── test_redis_writer.py  # Redis TimeSeries operations (mocked)
└── integration/
    └── test_compose_deploy.py # Container deployment validation
```

**Structure Decision**: New database code lives in `src/db/` package (4 modules + `__init__.py` = 5 files, satisfying Five-Item Rule). This isolates the polyglot logic from the monolithic `MistHelper.py` while the `DataExporter` class remains the entry point, delegating to `DatabaseRouter` when backends are available.

## Complexity Tracking

> No constitution violations detected. All five principles pass.
