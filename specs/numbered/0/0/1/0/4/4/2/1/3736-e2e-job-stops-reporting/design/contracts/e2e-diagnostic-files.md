# Contract: E2E diagnostic files

This contract defines the two diagnostic files that each E2E shard writes.
Operators read these files after a failed or cancelled shard.

## Files

| File | Path | Writer | Format |
| - | - | - | - |
| Phase trail | `test-artifacts/e2e-phase-trail.jsonl` | `PhaseTrailWriter` in `tests/e2e/conftest.py` | ASCII JSON Lines. One object for each record. |
| Stack dump | `test-artifacts/e2e-stack-dumps.txt` | `StackDumpWatch` in `tests/e2e/conftest.py` | ASCII text written by the `faulthandler` module. |

## Trail record fields

| Field | Type | Meaning |
| - | - | - |
| `node_id` | string | The pytest node ID of the item. |
| `phase` | string | `protocol_start`, `setup`, `call`, `teardown`, or `protocol_end`. |
| `outcome` | string | `started`, `passed`, `failed`, `skipped`, or `finished`. |
| `duration_seconds` | number or null | The phase duration. The value is null for `protocol_start` and `protocol_end`. |
| `timestamp_utc` | string | The UTC time in ISO 8601 form with the offset `+00:00`. |

The phase records keep the field set of the existing `PhaseTrailWriter.record` method.

## Stack dump format

- Each dump starts with a line that begins with `Timeout (`.
- Each dump lists the stack of each thread. The most recent call comes first.
- Each frame names the file, the function, and the line number. A frame holds no variable value.

## Invariants

1. Each item writes one `protocol_start` record before its first phase record.
2. Each item that completes its protocol writes one `protocol_end` record.
3. The stalled item is the last `protocol_start` record without a later `protocol_end` record.
4. The stack dump file exists after the session starts. The file holds text only when an item exceeds the watch threshold.
5. Both files hold ASCII text only.
6. Neither file holds a credential, a token, or a response body.

## Failure behavior

If a diagnostic file cannot open, the session stops before the first item.
The error message names the path and the cause.

## Consumers

The `e2e-diagnostics-<shard>` artifact in `.github/workflows/ci.yml` holds both files.
The artifact uploads on failure or cancellation of the shard.
