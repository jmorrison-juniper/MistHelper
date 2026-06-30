# Phase 1 Data Model: getApiToken

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)
**Endpoint**: `GET /api/v1/self/apitokens/{apitoken_id}`

## Entities

The endpoint returns a single entity: `UserApiToken`. There are no nested arrays, no
embedded sub-resources, and no pagination envelope.

### Entity: UserApiToken

Represents one API token issued to the authenticated admin account. Token secrets are
NEVER returned by this endpoint; only metadata and a redacted fingerprint of the key are
exposed.

| Field          | JSON Type            | SQLite Type | Nullable | Source / Notes                                              |
|----------------|----------------------|-------------|----------|-------------------------------------------------------------|
| `id`           | string (uuid)        | TEXT        | No       | Mist-issued UUID. **Natural primary key.** Read-only.       |
| `name`         | string               | TEXT        | Yes      | Human-friendly token label, e.g. `org_token_xyz`.           |
| `key`          | string               | TEXT        | Yes      | Redacted fingerprint (e.g. `1qkb...QQCL`). Never the secret. Read-only. |
| `created_time` | number (epoch sec)   | REAL        | Yes      | Token creation timestamp. Read-only.                        |
| `last_used`    | integer (epoch sec) or null | INTEGER | Yes  | Last observed use; null if never used. Read-only.           |

**Primary Key**: `id` (single-column natural PK).

**Foreign Keys**: None at the Mist API level. The token is implicitly owned by the
authenticated admin account; MistHelper does not currently model the `admin_id` because
this endpoint does not return it. Cross-linking to the parent admin record (via
`getSelf`) is a future enhancement and is out of scope.

**Indexes** (for read efficiency):

- `idx_self_api_tokens_name` on `name`
- `idx_self_api_tokens_last_used` on `last_used DESC`

## State Transitions

**N/A -- read-only endpoint.** MistHelper observes token state but does not mutate it.
The Mist control plane is the sole source of truth for state transitions (create / use /
rotate / delete); those are governed by sibling endpoints (`POST`, `PUT`, `DELETE`)
which are explicitly out of scope per `spec.md`.

The `last_used` field will advance over time as the token is exercised. When the user
re-runs menu 96 for the same `id`, the SQLite row is upserted via `INSERT OR REPLACE`,
so the stored `last_used` value is refreshed in place. No history table is created --
historical usage tracking is a future spec.

## SQLite DDL

```sql
-- Table created on first run by DataExporter when SQLite backend is active.
CREATE TABLE IF NOT EXISTS self_api_tokens (
    id            TEXT    PRIMARY KEY,    -- natural PK: Mist-issued UUID
    name          TEXT,                   -- human label for the token
    key           TEXT,                   -- redacted fingerprint, never the secret
    created_time  REAL,                   -- epoch seconds at creation
    last_used     INTEGER,                -- epoch seconds at last observed use; nullable
    misthelper_fetched_at REAL NOT NULL   -- UTC epoch when MistHelper persisted the row
);

CREATE INDEX IF NOT EXISTS idx_self_api_tokens_name
    ON self_api_tokens (name);

CREATE INDEX IF NOT EXISTS idx_self_api_tokens_last_used
    ON self_api_tokens (last_used DESC);
```

The `misthelper_fetched_at` column is added by `DataExporter` for every row across every
backend; it is the audit timestamp of when MistHelper observed the API response and is
not part of the Mist payload.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

The entry added to the strategy dictionary in `MistHelper.py` (existing dictionary --
roughly line 1672 per the canonical instructions):

```python
'getApiToken': {                              # operationId from Mist OpenAPI spec
    'type': 'natural_pk',                     # API issues a stable UUID -> natural key
    'primary_key': ['id'],                    # single-column PK on the UUID
    'indexes': ['name', 'last_used'],         # supports viewer queries by label and recency
    'table': 'self_api_tokens',               # SQLite/Arango target collection name
    'csv_filename_template':                  # per-id CSV avoids overwrite when inspecting
        'self_api_token_{apitoken_id}.csv',   # multiple tokens in one session
},
```

Every line carries an inline comment per Constitution Principle VI. The dictionary key
`'getApiToken'` matches the SDK `operationId` exactly (case-sensitive) so the dispatch
inside `DataExporter.write_with_format_selection(...,
api_function_name='getApiToken')` can look it up without translation.
