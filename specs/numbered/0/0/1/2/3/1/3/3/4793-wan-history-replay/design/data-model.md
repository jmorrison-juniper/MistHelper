# Data Model: WAN history replay safety

## Entities

### SampleMeasurement

Defined in `src/interfaces/wan_performance/domain/measurement.py` (RC-45).

| Field | Meaning |
|-------|---------|
| `identity` | A `CircuitIdentity` for one port, or a `GatewayIdentity` for one gateway. |
| `sampled_at_utc` | The source time, in UTC. For an API sample, it is the API timestamp. For a poll sample, it equals the collection time. |
| `collected_at_utc` | The collection time, in UTC. It records when this tool read the value. |
| `metrics` | Named `MetricMeasurement` values, such as `rx_bps` and `tx_bps`. |
| `raw_fields` | Scalar source fields, such as loss, jitter, or latency. |
| `timestamp_source` | `api` for an API timestamp, or `poll` for a poll time. |
| `partial` | True when the source did not return every field. |
| `provenance` | `live` for every stored sample. Synthetic samples are refused (RC-37). |
| `is_up_observation` | The link state, or None when the source gave no state. |

Natural key: the identity natural key plus `sampled_at_utc.isoformat()` (RC-45).

Source payload: every persisted field except `collected_at_utc` (RC-38). Two samples with equal source payloads are replays.

### Stored SQLite sample row

Table `wan_performance_samples` in the configured SQLite file (RC-31).

| Column | Type | Content |
|--------|------|---------|
| `identity` | TEXT, not null | JSON of the identity natural key. |
| `sampled_at` | TEXT, not null | ISO 8601 source time in UTC. |
| `payload` | TEXT, not null | JSON of the full sample, including `collected_at_utc`. |

Primary key: `(identity, sampled_at)`.

### Stored Arango sample document

Collection `wan_performance_samples` in the configured ArangoDB database (RC-33).

| Field | Content |
|-------|---------|
| `_key` | SHA-256 hex digest of the JSON natural key. |
| `identity` | JSON of the identity natural key. |
| `sampled_at` | ISO 8601 source time in UTC. |
| `payload` | JSON of the full sample, including `collected_at_utc`. |

### Hourly record

Table `wan_performance_hours` in SQLite, and collection `wan_performance_hours` in ArangoDB (RC-30, RC-33).

Key: identity natural key plus the UTC hour. SQLite uses `ON CONFLICT(identity,hour) DO UPDATE` (RC-30). Each write replaces the payload of the same key (FR-011).

## State Transitions for One Sample Key

| Current state | Event | Next state | Rule |
|---------------|-------|------------|------|
| Absent | Write of one sample | Stored | One row or one document is inserted (FR-001, FR-002). |
| Stored | Replay with an equal source payload | Stored | No sample write. Collection time does not matter (FR-001, FR-002, FR-005). |
| Stored | Write with a changed source payload | Stored, unchanged | The whole write stops, and the error names the source time (FR-004, FR-013). |
| Absent | Two equal copies in one batch | Stored once | The batch keeps one copy before any write (FR-003). |
| Absent | Two different copies in one batch | Absent | The batch stops before any write (FR-004). |
| Commit pending (Arango) | Commit returns True | Committed | The writer reports success (FR-007). |
| Commit pending (Arango) | Commit returns any other value | Rolled back | The writer raises ConnectionError and keeps the original error path (FR-007, FR-008). |

## Natural Keys by Entity

| Entity | Natural key | Evidence |
|--------|-------------|----------|
| SampleMeasurement | Identity natural key, source time | RC-45 |
| Stored SQLite sample row | `(identity, sampled_at)` | RC-31 |
| Stored Arango sample document | SHA-256 of the JSON natural key | RC-33 |
| Hourly record | Identity natural key, UTC hour | RC-30 |
