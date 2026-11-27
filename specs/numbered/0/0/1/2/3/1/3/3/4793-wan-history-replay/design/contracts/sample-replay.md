# Contract: Sample replay writes

## Scope

This contract covers three writers and one policy:

- `SQLiteHistory.upsert` in `src/interfaces/wan_performance/integration/sqlite_history.py` (RC-30).
- `ArangoHistory.upsert` in `src/interfaces/wan_performance/integration/arango_history.py` (RC-33).
- `SnapshotRates._rate_samples` in `src/interfaces/wan_performance/collection/snapshot_records.py` (RC-41).
- `SampleReplayPolicy` in `src/interfaces/wan_performance/integration/record_codec.py` (RC-37).

## Inputs

- `records`: a tuple of `HourlyMeasurement`. Each record names one identity and one UTC hour.
- `samples`: a tuple of `SampleMeasurement`. Each sample names one identity and one source time.

## Sample Key

The sample key is the identity natural key and `sampled_at_utc` in ISO 8601 UTC form (RC-45). The SQLite primary key uses the same two values (RC-31).

## Write Rules

| Event | Result | Error type | Error text |
|-------|--------|------------|------------|
| A stored sample returns with an equal source payload | The sample is skipped. The call returns None. | None | None |
| One batch holds two equal copies of a sample | One copy is written. | None | None |
| One batch holds two different copies of a sample | No row is written. | ValueError | `WAN sample replay conflicts with stored source data for the same natural key at 2024-01-01T12:34:00+00:00.` |
| A stored sample returns with a changed source payload | No row is written. The hourly records of the batch stay unchanged. | ValueError | Same text as above, with the time of the changed sample. |
| One API response gives two values for one metric and timestamp | No write runs. | ValueError | `WAN API response gives two values for one metric and timestamp at 2024-01-01T12:34:00+00:00.` |
| Arango commit returns a value other than True | The writer attempts the rollback. The rollback result is logged. | ConnectionError | `WAN ArangoDB history transaction did not confirm its commit.` |
| The Arango rollback fails after another error | The writer logs the rollback failure and raises the original error. | The original error type | The original error text |
| SQLite write error | The transaction rolls back. The writer raises the original error. | sqlite3.Error or the original error type | The original error text |

The example times in the table are examples. The writer names the actual source time of the sample.

## Output

- A successful call returns None.
- A replay returns None, and the stored row is unchanged.
- A failed call raises the error in the table. The stored rows of earlier calls stay unchanged.

## Logging

- Before the Arango commit check, the writer writes an info line with the hourly and sample counts.
- After a confirmed commit, the writer writes a debug line with the same counts.
- Each error writes one exception line through the existing handler of the writer. A changed-sample error names the source time in its text. The line holds no secret.
- Each log line uses ASCII text and `%s` values.

## Portal Behavior

The portal route keeps its current behavior in this change (Decision D-6). A store error, including a conflict, renders the generic message and status 503 (RC-43, RC-44).
