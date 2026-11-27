# Contract: storage and cache

## Redis keys

Redis is coordination only. Redis holds no product history. Each key family has one writer, one TTL, and one failure rule (D-4, FR-012).

| Key | Writer | TTL | Failure behavior | Source |
|---|---|---|---|---|
| `misthelper:api:v1:requests:{fingerprint}` | shared admission ledger | 3600-second window with a 3601-second expiry | Background refresh stops. Operator reads continue under the per-process ceiling. | R59 (lines 82, 87-97) |
| `misthelper:api:v1:org:{org_id}` | shared admission ledger | 3600-second window | Same as above. | R59 (line 85) |
| `misthelper:wan:v1:refresh:{org_id}` | refresh store | 300-second lease (proposed) | The refresh does not start. | R66 (line 24) |
| `misthelper:wan:v1:snapshot:{org_id}` | refresh store | 3600 seconds | Pages show the stale state with the capture time. | R66 (line 90) |
| `misthelper:wan:v1:worker:{org_id}` | background worker | lease owned by one worker per organization (renewal interval proposed) | The worker stops and releases the lease. | R90 (line 23) |

The prefix `misthelper:wan:v1:` is the only namespace for WAN keys (FR-012).

## Product storage

- Historical rows go through `DataExporter.write_with_format_selection()` (D-7, constitution line 312).
- Each row uses a natural key from `design/data-model.md`.
- The SQLite store is `data/mist_data.db`. The ArangoDB store is the configured alternative.
- A failed write returns a store-error state. No success message appears.
- Synthetic records never reach the store (D-10).

## Deletion

- The feature deletes no product row (D-2).
- Redis keys expire by TTL. No code deletes a key except the lease owner on release.
