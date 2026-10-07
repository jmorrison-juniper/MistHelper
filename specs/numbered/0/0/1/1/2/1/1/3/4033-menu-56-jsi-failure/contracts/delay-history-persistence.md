# Contract: Delay History Persistence

## Scope

This contract applies to `RateLimitingUtils._append_delay_metrics_log`.
It does not change the menu 56 export or web portal outcome contract.

## Inputs

- `delay_metrics`: The current delay result object.
- `api_cache`: The current API usage snapshot.
- `tuning_data`: The current PID tuning snapshot.
- `filename`: The destination name or path.
- `max_entries`: The maximum retained row count.

## Success Contract

1. Resolve the destination path.
2. Build one row with the existing field shape.
3. Acquire the single delay history process lock.
4. Read the prior destination while the lock is held.
5. Treat a missing or zero-byte destination as empty history.
6. Append the new row and apply the retention cap.
7. Create a temporary file in the destination directory.
8. Write each retained row as complete JSON and one newline.
9. Close the temporary file.
10. Replace the destination with `os.replace`.
11. Release the lock.

The successful destination contains each retained row exactly once.
The successful cycle leaves no temporary file.

## Concurrent Writer Contract

One writer owns the full read-modify-write cycle.
A second writer waits before it reads the destination.
Each writer reads the result of the previous completed writer.

The final destination contains all expected unique rows within the retention cap.
No reader observes a temporary empty or partial destination.

## Failure Contract

If a temporary write fails, keep the prior destination unchanged.
If `os.replace` fails, keep the prior destination unchanged.
If a temporary path exists after failure, remove it before lock release.

Catch only expected JSON and filesystem exceptions.
Use every bound exception in an ASCII log record.
Do not use a broad catch.

If cleanup fails, log the cleanup exception with the temporary path.
Do not replace the original write or replacement failure with a success result.

## Test Contract

The unit tests must prove these outcomes:

- The baseline concurrent test is red before the source repair.
- The red output contains `File I/O: Failed to read data/delay_metrics.json`.
- Concurrent writers preserve every expected complete row.
- A zero-byte destination accepts the next row without a corruption warning.
- A replacement failure preserves the prior destination bytes.
- A replacement failure leaves no temporary file.
- A successful replacement leaves no temporary file.
- Existing retention and custom-filename behavior remains unchanged.
