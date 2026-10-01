# Data model: Bounded database discovery

## Lookup identity

The key contains the exact configured hostname, address family, and socket type.
The query uses no port, the default protocol, and zero flags.
The cache does not mix different query identities.

## Cached result

Each entry contains immutable socket address records, an explicit error, and one monotonic expiry time.
An empty address tuple with an error represents a failed lookup or a caller timeout.
The first failure emits a diagnostic.
Expiry removes the result before another lookup starts.
The cache holds at most 128 entries.

## Active lookup

Each entry contains one result future and one daemon thread.
The active map holds at most two entries.
The finite handoff queue shares the two-query admission limit.
It creates no extra job behind two blocked workers.
Concurrent requests for the same identity share the future.
The worker remains active after a caller timeout.

## State transitions

| State | Event | Result |
| - | - | - |
| No cached or active result | A worker slot is free. | Start one lookup. |
| No cached or active result | Both query slots are occupied. | Report capacity refusal without additional queueing. |
| An active result exists | Another caller requests the same identity. | Share the existing future. |
| A caller waits | The caller deadline expires. | Cache a failed result and retain the active worker. |
| A worker completes | No unexpired result exists. | Publish the result and release the worker slot. |
| A worker completes | A timeout result remains unexpired. | Retain its original expiry and release the worker slot. |
| A cached result exists | Its monotonic expiry arrives. | Remove it and permit another lookup. |
| The resolver closes | A worker remains blocked. | Stop new admission and end the join after its deadline. |

## Persistent data

This feature changes no schema, primary key, data strategy, file format, or persistent database record.
