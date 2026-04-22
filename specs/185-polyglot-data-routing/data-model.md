# Data Model: Polyglot Data Routing Refactor

**Feature**: 185-polyglot-data-routing | **Date**: 2026-04-22

## Entities

### 1. EndpointStrategy (updated)

**Location**: `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict in `MistHelper.py`

```python
# Existing fields (unchanged)
{
    "type": str,              # "natural_pk" | "composite_pk" | "timeseries_pk" | "auto_increment_with_unique"
    "primary_key": list[str], # Key fields for upsert
    "indexes": list[str],     # Fields to index
    "unique_constraints": list[str],
    "description": str,
}

# New fields for timeseries_pk only
{
    "ts_value_fields": list[str],  # Numeric fields → TS data points
    "ts_label_fields": list[str],  # Text fields → TS labels
}
```

**Routing rules**:
| Strategy Type | ArangoDB | Redis JSON | Redis TimeSeries |
|---|---|---|---|
| `natural_pk` | Raw documents (upsert) | -- | -- |
| `composite_pk` | Raw documents (archive) | Full documents (recent) | -- |
| `timeseries_pk` | -- | -- | Numeric values + labels |
| `auto_increment_with_unique` | Raw documents (upsert) | -- | -- |

### 2. WriteResult (unchanged)

```python
@dataclass
class WriteResult:
    success: bool
    backend: str      # "arangodb", "redis", "redis_json", "dual", "csv_only"
    records_written: int
    records_failed: int
    error_message: str = ""
```

**Change**: `backend` field gains new values: `"redis_json"` for JSON-only writes, `"dual"` for composite_pk dual-write results.

### 3. DualWriteResult (new)

```python
@dataclass
class DualWriteResult:
    arango_result: WriteResult
    redis_result: WriteResult

    @property
    def combined(self) -> WriteResult:
        """Merge both results into a single WriteResult for logging."""
        ...
```

**Purpose**: Captures independent success/failure of both backends for composite_pk dual-write.

## Routing Constants (updated)

```python
# Current (router.py)
ARANGO_PK_TYPES = {"natural_pk", "auto_increment_with_unique"}
REDIS_PK_TYPES = {"composite_pk"}

# New
ARANGO_ONLY_TYPES = {"natural_pk", "auto_increment_with_unique"}
DUAL_WRITE_TYPES = {"composite_pk"}      # Redis JSON + ArangoDB
TIMESERIES_TYPES = {"timeseries_pk"}      # Redis TimeSeries only
```

## Redis Key Patterns

### Redis JSON keys (composite_pk)
```
Pattern: {endpoint}:{pk_field1_value}:{pk_field2_value}:...
Example: searchOrgAlarms:alarm-uuid-123:org-uuid-456:1713800000
TTL:     7 days (configurable via REDIS_JSON_TTL_DAYS env var)
```

### Redis TimeSeries keys (timeseries_pk, unchanged)
```
Pattern: {endpoint}:{entity_id}:{field_name}
Example: listOrgDevicesStats:device-uuid-123:cpu_util
```

## Endpoint Reclassification Table

### Moving from composite_pk to timeseries_pk
| Endpoint | Primary Key | ts_value_fields (examples) | ts_label_fields |
|---|---|---|---|
| `listOrgDevicesStats` | `[device_id, timestamp]` | `cpu_util, mem_util, uptime, num_clients` | `hostname, model, type, site_id` |
| `listSiteDevicesStats` | `[device_id, timestamp]` | `cpu_util, mem_util, uptime, num_clients` | `hostname, model, type` |
| `listSiteWirelessClientsStats` | `[client_mac, timestamp]` | `rssi, snr, rx_rate, tx_rate` | `ssid, hostname, device_id` |
| `searchOrgSwOrGwPorts` | `[device_id, port_id, timestamp]` | `rx_bytes, tx_bytes, rx_errors, tx_errors` | `port_id, device_id, org_id` |
| `searchSiteSwOrGwPorts` | `[device_id, port_id, timestamp]` | `rx_bytes, tx_bytes, rx_errors, tx_errors` | `port_id, device_id, site_id` |
| `searchOrgPeerPathStats` | `[from_device, to_device, timestamp]` | `latency, jitter, loss` | `from_device, to_device, org_id` |

### Remaining as composite_pk (→ dual-write: Redis JSON + ArangoDB)
| Endpoint | Reason |
|---|---|
| `searchOrgAlarms` | Text-heavy (severity, type, description) |
| `searchOrgDeviceEvents` | Text-heavy (event type, text, device name) |
| `searchOrgClientEvents` | Text-heavy (event type, client info) |
| `searchOrgSystemEvents` | Text-heavy (system messages) |
| `searchOrgWirelessClients` | Mixed text/numeric client data |
| `searchOrgWiredClients` | Mixed text/numeric client data |
| All device utility commands | Text-heavy diagnostic output |
| All SSID consolidation endpoints | Configuration analysis data |

### Remaining as natural_pk (→ ArangoDB raw documents)
All entity endpoints unchanged (sites, devices, templates, maps, etc.)

### Remaining as auto_increment_with_unique (→ ArangoDB)
License summary/list endpoints unchanged.
