# UI Contract: Status Fallback for Quiet Operation Streams

## Stream contract

When `startSSEStream(runId)` starts, the browser must arm one silence fallback for that run.

Each stream event must refresh the fallback timer. A terminal stream event must clear the timer.

## Status fallback contract

When the fallback timer fires, the browser must call `/api/operations/status/<run_id>` for the active run.

If the route reports `completed`, the browser must show `Complete`, show output files, and reset the run controls.

If the route reports `failed`, the browser must show `Error`, append an error log line, and reset the run controls.

If the route reports `running`, the browser must arm another silence fallback.
