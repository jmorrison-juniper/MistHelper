# Data Model: Split Database Package

This refactor changes module location only. It changes no stored record, schema, index, key, retention value, or result type.

## Backend Module

**Paths**:

- `src/foundation/persistence/db/backends/arango_writer.py`
- `src/foundation/persistence/db/backends/redis_writer.py`

**Responsibilities**: Write existing records to ArangoDB, Redis JSON, and Redis TimeSeries.

**Validation rules**:

- Preserve each module-level name and value.
- Preserve stored values, indexes, graph declarations, time-series rules, and error results.
- Preserve optional-service import safety.

## Coordination Module

**Paths**:

- `src/foundation/persistence/db/coordination/router.py`
- `src/foundation/persistence/db/coordination/retention.py`

**Responsibilities**: Select a backend, coordinate writes, and apply retention actions.

**Validation rules**:

- Preserve route selection and degraded-mode behavior.
- Preserve retention thresholds, scan limits, purge logic, and thread behavior.
- Preserve each `WriteResult` use and error path.

## Support Module

**Paths**:

- `src/foundation/persistence/db/support/database_schema_utils.py`
- `src/foundation/persistence/db/support/host_resolver.py`

**Responsibilities**: Build schemas and indexes, then resolve database hosts within existing limits.

**Validation rules**:

- Preserve DDL, index state, host results, cache behavior, worker limits, and exceptions.
- Preserve each public class, constant, and default resolver.

## Canonical Import

**Fields**:

- Old module path.
- New module path.
- Consumer path.
- Reference type: import, patch target, dependency string, or logger name.

**Relationship**: Each old path maps to exactly one new path. Each consumer uses only that new path.

## Behavior Baseline

**Fields**:

- Exact coordinator-provided `main` SHA.
- Baseline module path.
- Baseline module-level symbol set.
- Focused test result.
- Gate result.

**State transitions**:

1. `blocked`: PR #3980 owns the serial slot, or the #3959 coordinator has not supplied the exact SHA.
2. `ready`: The slot is free and `BASE_SHA` is recorded.
3. `moved`: All six canonical files exist and all six old files do not exist.
4. `verified`: Focused tests, symbol checks, and required gates pass.

No implementation step can enter `verified` with an old path, a lost symbol, or an unintended behavior difference.
