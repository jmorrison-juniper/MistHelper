# Contract: Metrics Gateway Module Paths

## File

This contract names the import paths, the logger names, and the root exports of the metrics gateway package. It applies to `src/interfaces/monitoring/metrics_gateway/`. The export list comes from the local checkout at the same commit as `main`. Line 68 of `__init__.py` on `main` opens the `__all__` list (row C54).

## Module Map

| Old path (removed) | Canonical path | Logger name |
| - | - | - |
| `src/interfaces/monitoring/metrics_gateway/cache.py` | `src/interfaces/monitoring/metrics_gateway/core/cache.py` | `src.interfaces.monitoring.metrics_gateway.core.cache` |
| `src/interfaces/monitoring/metrics_gateway/catalog.py` | `src/interfaces/monitoring/metrics_gateway/core/catalog.py` | `src.interfaces.monitoring.metrics_gateway.core.catalog` |
| `src/interfaces/monitoring/metrics_gateway/collector.py` | `src/interfaces/monitoring/metrics_gateway/core/collector.py` | `src.interfaces.monitoring.metrics_gateway.core.collector` |
| `src/interfaces/monitoring/metrics_gateway/samples.py` | `src/interfaces/monitoring/metrics_gateway/core/samples.py` | `src.interfaces.monitoring.metrics_gateway.core.samples` |

An import of an old name, such as `src.interfaces.monitoring.metrics_gateway.catalog`, raises `ModuleNotFoundError` after the change. No alias exists at an old path.

## Root Exports

The root package keeps these names in `__all__`. Each moved name imports from its core module. Each root module name imports from the root module.

- `GatewaySettings`
- `MetricCatalog`
- `MetricDefinition`
- `MetricKind`
- `MetricSample`
- `MetricScope`
- `MetricSnapshot`
- `MetricsCache`
- `MistMetricsCollector`
- `MistStatsReader`
- `OidTree`
- `PrometheusRenderer`
- `SnmpPassPersistResponder`
- `build_cache`
- `create_app`
- `start_refresh_thread`

## Unchanged Paths

`__init__.py`, `prometheus.py`, `service.py`, `snmp.py`, and `web.py` stay at the gateway root. The root `__init__.py` keeps the same export names.

## Consumers

The consumers are the MIB generator modules, the contract tests, the unit tests, and the root package. `MistHelper.py` imports the root modules `service`, `web`, and `snmp` at lines 7093, 7098, 7154, and 7161 on `main` (row L09 in `design/research.md`). That file does not change.

## Generated Text

The MIB header names `src/interfaces/monitoring/metrics_gateway/core/catalog.py`. The generator template in `src/operations/hardware/mib_generator/mib.py` line 428 writes that text. The stored file `documentation/mibs/MISTHELPER-MIB.mib` line 20 holds the same text after regeneration.

## Logger Contract

Each moved module names its logger with `logging.getLogger(__name__)`. Its logger name therefore follows the core module path in the table above. The five logger assertions in the unit tests use the core names.
