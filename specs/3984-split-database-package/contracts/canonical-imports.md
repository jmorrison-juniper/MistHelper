# Contract: Canonical Database Imports

## Canonical Path Map

| Old module | Canonical module |
|---|---|
| `src.foundation.persistence.db.arango_writer` | `src.foundation.persistence.db.backends.arango_writer` |
| `src.foundation.persistence.db.redis_writer` | `src.foundation.persistence.db.backends.redis_writer` |
| `src.foundation.persistence.db.router` | `src.foundation.persistence.db.coordination.router` |
| `src.foundation.persistence.db.retention` | `src.foundation.persistence.db.coordination.retention` |
| `src.foundation.persistence.db.database_schema_utils` | `src.foundation.persistence.db.support.database_schema_utils` |
| `src.foundation.persistence.db.host_resolver` | `src.foundation.persistence.db.support.host_resolver` |

Imports, patch targets, dependency strings, and logger-name expectations must use this map. Package initializers must not provide another path.

## Arango Writer Consumers

Update these files to `src.foundation.persistence.db.backends.arango_writer`:

- `src/foundation/persistence/db/coordination/router.py`
- `tests/integration/test_arango_declared_indexes_live.py`
- `tests/contract/test_arango_declared_indexes.py`
- `tests/unit/_test_arango_writer_helpers.py`
- `tests/unit/arango_indexes/test_retry_concurrency.py`
- `tests/unit/arango_indexes/test_preservation.py`
- `tests/unit/arango_indexes/fakes.py`
- `tests/unit/db_discovery/test_probe.py`
- `tests/unit/db_discovery/test_config.py`
- `tests/unit/web_portal/test_portal_log_routing.py`
- `tests/unit/test_arango_writer.py`

## Redis Writer Consumers

Update these files to `src.foundation.persistence.db.backends.redis_writer`:

- `src/foundation/persistence/db/coordination/router.py`
- `tests/contract/test_arango_declared_indexes.py`
- `tests/unit/db_discovery/test_probe.py`
- `tests/unit/db_discovery/test_config.py`
- `tests/unit/test_redis_writer.py`
- `tests/unit/test_redis_json_writer.py`
- `tests/unit/test_unparseable_response_guards.py`
- `tests/unit/test_webhook_ingestion.py`

## Router Consumers

Update these files to `src.foundation.persistence.db.coordination.router`:

- `MistHelper.py`
- `src/operations/exporting/export/data_exporter.py`
- `tests/integration/test_compose_deploy.py`
- `tests/contract/upgrade_portal/test_health.py`
- `tests/contract/test_arango_declared_indexes.py`
- `tests/test_upgrade_portal_audit.py`
- `tests/unit/container/session_database/harness.py`
- `tests/unit/db_discovery/test_config.py`
- `tests/unit/test_standalone.py`
- `tests/unit/test_router.py`
- `tests/unit/test_webhook_ingestion.py`

## Retention Consumers

Update these files to `src.foundation.persistence.db.coordination.retention`:

- `tests/unit/test_retention.py`
- `tests/unit/db/test_retention_redis_scan.py`

## Database Schema Utility Consumers

Update these files to `src.foundation.persistence.db.support.database_schema_utils`:

- `MistHelper.py`
- `src/foundation/persistence/db/backends/arango_writer.py`
- `src/foundation/runtime/config/source_dependency_resolver.py`
- `tests/unit/arango_indexes/test_retry_concurrency.py`
- `tests/unit/refactors/test_sqlite_database_writer.py`
- `tests/unit/db/test_database_schema_utils.py`

## Host Resolver Consumers

Update these files to `src.foundation.persistence.db.support.host_resolver`:

- `src/foundation/persistence/db/__init__.py`
- `src/foundation/persistence/db/backends/arango_writer.py`
- `src/foundation/persistence/db/backends/redis_writer.py`
- `tests/unit/test_standalone.py`
- `tests/unit/test_redis_writer.py`
- `tests/unit/db_discovery/test_resolver.py`
- `tests/unit/db_discovery/test_probe.py`
- `tests/unit/db_discovery/test_config.py`
- `tests/unit/db_discovery/fakes.py`
- `tests/unit/upgrade_portal/test_store.py`

The root initializer must import only the required resolver symbol with a private name. Tests must import the support module directly.

## Rejection Rules

- Reject each old import path.
- Reject `from src.foundation.persistence.db import` for any moved module.
- Reject an initializer re-export.
- Reject a compatibility file at an old path.
- Reject a fallback import.
- Reject any consumer change beyond its import, patch target, dependency string, or logger-name expectation.
