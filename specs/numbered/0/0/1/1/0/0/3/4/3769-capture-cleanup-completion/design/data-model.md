# Utility completion model

The existing run context remains unchanged.

| Value | Meaning | Lifetime |
| --- | --- | --- |
| Execution exception | An error from startup or monitoring | Retained until cleanup returns |
| Capture identity | Existing trigger scope and answer identifier | Unchanged |
| Cleanup outcome | Return or exception from `_close()` | Determines whether finalization can proceed |
| Terminal result | One sink notification | Published after cleanup |

Normal execution follows existing stopped, finished, and timed-out classifications.
An execution exception follows existing error classification after successful cleanup.
A cleanup exception produces failed state and a safe reason, even when the stop flag is set.
No schema, stored record, or public payload changes.
