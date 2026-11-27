# Contract: Log Events for Refused Writes

Each event uses the structured logger. Values use `%s` formatting. No event holds a path, a token, or a device value.

| Event | Level | Fields | Emitted when |
|-------|-------|--------|--------------|
| `web.artifact.batch.manifest.error` | ERROR | `status` (exception class name), `errno` (integer, when present), `winerror` (integer, when present) | A manifest replace is refused, during the run or at finalization |
| `web.artifact.replace.retry` | INFO | `errno` (integer, when present), `winerror` (integer, when present) | Each wait of a replace |
| `web.artifact.batch.finalize.error` | ERROR | `reason_code` with the value `manifest_not_final` | Finalization gives up after its last try |
| `web.artifact.batch.marker.error` | ERROR | `status` (exception class name), `errno` (integer, when present), `winerror` (integer, when present) | The marker write is refused |

Rules:

- The `status` field keeps the exception class name, as it does today (`artifacts.py:458`).
- The `errno` and `winerror` fields hold integers only.
- No event holds a path. The existing assertion at `test_ws_artifact_replace.py:171` checks this rule.
