# Phase 1 Data Model: generateSecretFor2faVerification

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)

This document defines the persisted entity, its fields, primary key strategy, SQLite DDL,
and the `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration entry.

## Entity Inventory

The Mist API endpoint returns a single JSON object with one business field. MistHelper
augments it with audit metadata at persistence time. There is only one entity.

### Entity: `self_two_factor_token`

Persisted snapshot of one invocation of the `generateSecretFor2faVerification` endpoint.

| Field                    | Type                | Required | Source                              | Notes                                                                                              |
|--------------------------|---------------------|----------|-------------------------------------|----------------------------------------------------------------------------------------------------|
| `misthelper_internal_id` | INTEGER             | yes      | DataExporter auto-increment         | Primary key. Synthetic; never exposed in CSV header export but present in SQLite.                  |
| `captured_at`            | TEXT (ISO 8601 UTC) | yes      | `datetime.now(UTC).isoformat()`     | Unique key. Records the exact moment the secret was generated. Used for audit and idempotency.    |
| `output_mode`            | TEXT                | yes      | User prompt (`json` or `qrcode`)    | Records which response variant was requested.                                                      |
| `two_factor_secret`      | TEXT                | no       | API response `two_factor_secret`    | Base32-encoded TOTP seed. NULL when `output_mode == 'qrcode'` (binary PNG is stored separately).  |
| `qrcode_path`            | TEXT                | no       | Local filename                      | Set only when `output_mode == 'qrcode'`. Points to `data/self_two_factor_qrcode_<captured_at>.png`.|
| `account_token_hint`     | TEXT                | yes      | Last 4 chars of `MIST_API_TOKEN`    | Audit aid: identifies which token generated the secret without revealing the token.                |
| `mist_host`              | TEXT                | yes      | `.env` `MIST_HOST`                  | Records the Mist cloud region (e.g. `api.mist.com`, `api.eu.mist.com`).                            |
| `source_operation_id`    | TEXT                | yes      | Hardcoded                           | Always `generateSecretFor2faVerification`. Used by the cross-endpoint audit table.                |

**Primary Key**: `misthelper_internal_id` (auto-increment).
**Unique Key**: `captured_at` (prevents accidental double-insert from a fast-fire retry).
**Foreign Keys**: None. The endpoint is account-scoped and does not reference any other
entity in the MistHelper schema.
**Indexes**: `captured_at`, `account_token_hint` (so an operator can quickly list every
secret ever minted from a particular API token).

## State Transitions

**N/A -- read-only endpoint.** Each row represents one immutable historical event (the
moment a TOTP seed was minted for the calling account). Rows are never updated. Rows are
not deleted by MistHelper; routine database hygiene (e.g. a manual `DELETE WHERE
captured_at < ?` for retention) is the operator's responsibility and outside this spec's
scope.

## SQLite DDL

DataExporter creates this table automatically on first run using the registered primary
key strategy. The DDL below is what gets emitted; it is recorded here so reviewers can
spot drift between the registry entry and the materialized schema.

```sql
CREATE TABLE IF NOT EXISTS self_two_factor_token (
    misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at TEXT NOT NULL,
    output_mode TEXT NOT NULL,
    two_factor_secret TEXT,
    qrcode_path TEXT,
    account_token_hint TEXT NOT NULL,
    mist_host TEXT NOT NULL,
    source_operation_id TEXT NOT NULL,
    UNIQUE (captured_at)
);

CREATE INDEX IF NOT EXISTS idx_self_two_factor_token_captured_at
    ON self_two_factor_token (captured_at);

CREATE INDEX IF NOT EXISTS idx_self_two_factor_token_token_hint
    ON self_two_factor_token (account_token_hint);
```

## `ENDPOINT_PRIMARY_KEY_STRATEGIES` Registration

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py` (located near line ~1672 per the canonical project instructions). Inline
comments are required per Principle VI:

```python
# Self / MFA: generateSecretFor2faVerification (GET /api/v1/self/two_factor/token)
'generateSecretFor2faVerification': {
    'type': 'auto_increment_with_unique',          # no stable Mist UUID; each call mints a fresh secret
    'primary_key': ['misthelper_internal_id'],     # synthetic surrogate so audit history survives
    'unique_keys': ['captured_at'],                # prevents double-insert from fast retries within the same second
    'indexes': ['captured_at', 'account_token_hint'],  # audit-friendly lookups for retention sweeps
    'sensitive_columns': ['two_factor_secret'],    # signals DataExporter to omit value from any log line
},
```

The `sensitive_columns` hint is consumed by `DataExporter.write_with_format_selection`
to ensure the secret value is written to the chosen backend but never echoed into the
application log (Principle V, observability without leakage).

## Cross-Backend Considerations

- **CSV**: All columns including `misthelper_internal_id` appear in the header row. The
  secret value is written verbatim -- the operator's file system controls are the
  protection boundary.
- **SQLite** (`data/mist_data.db`): As DDL above.
- **ArangoDB + Redis** (per spec 188): The row becomes one document in the
  `self_two_factor_token` vertex collection. No edges are created (no foreign keys).
  Redis cache key: `mist:self_two_factor_token:<captured_at>` with a 60-second TTL so a
  fast UI re-render does not re-hit the Mist API.

## Validation

Data validation performed before persistence:

1. `two_factor_secret` (when present) MUST match the regex `^[A-Z2-7]+$` (RFC 4648 base32
   alphabet). On mismatch, the row is still written but a `WARNING` is logged.
2. `captured_at` MUST be a valid ISO 8601 UTC string ending in `Z` or `+00:00`. Generated
   by `datetime.now(UTC).isoformat()`; no user input path can corrupt it.
3. `output_mode` MUST be one of `{"json", "qrcode"}`. Enforced by the prompt loop in
   the menu method before the SDK call is issued.
