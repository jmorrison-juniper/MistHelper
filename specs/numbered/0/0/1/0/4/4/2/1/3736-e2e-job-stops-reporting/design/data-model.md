# Data model: E2E diagnostic records

## Entities

### PhaseRecord

One JSON object in the phase trail. The fields appear in `design/contracts/e2e-diagnostic-files.md`.
The natural key is the pair `node_id` and `phase`. Each item writes each phase once for each session.

### ItemLifecycle

The derived state of one item. The state comes from the `PhaseRecord` entries that share one `node_id`.

### StackDump

The text of one threshold crossing. The dump file has no item field.
The stalled-item rule identifies the item, as described below.

### ShardRow

One matrix row of the `playwright_shards` job in `.github/workflows/ci.yml`.
The natural key is the `shard` value. The attributes are `test_paths`, the job limit, and the per-test budget.
The current values are `upgrade-portal`, `web-portal`, and `websockets-tab`, with a 20-minute job limit.

## State transitions for ItemLifecycle

| From | Event | To |
| - | - | - |
| NotStarted | A `protocol_start` record is written. | Started |
| Started | A `setup` record is written. | SetupRecorded |
| SetupRecorded | A `call` record is written. | CallRecorded |
| CallRecorded | A `teardown` record is written. | TeardownRecorded |
| TeardownRecorded | A `protocol_end` record is written. | Finished |
| Started, SetupRecorded, CallRecorded, or TeardownRecorded | The job is cancelled. | Stalled or Interrupted |

A state becomes Stalled when the silent interval exceeds the per-test budget.
The silent interval is the time from the last record to the cancellation.
Otherwise, the state becomes Interrupted.

## Stalled-item rule

The stalled item is the last `protocol_start` record without a later `protocol_end` record.
If every item finished, no item is stalled.
