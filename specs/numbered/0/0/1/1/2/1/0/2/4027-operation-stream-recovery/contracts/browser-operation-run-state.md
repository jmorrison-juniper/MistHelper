# Contract: Browser Operation Run State

## Scope

This contract applies to `web_portal/static/js/operations.js`.
It does not change a server route or a service response.

## Existing Server Contract

The browser requests:

```text
GET /api/operations/status/<run_id>
```

The browser uses these existing fields:

```json
{
  "run_id": "run-identifier",
  "status": "running | completed | failed",
  "completion_message": "completed text or null",
  "error_message": "failure text or null",
  "output_files": ["exact/server/path.csv"]
}
```

No field is added, removed, or renamed.

## Active Stream Recovery Contract

1. Start one status timer when the browser starts the stream.
2. Request status after 5,000 milliseconds.
3. Keep no more than one status request active.
4. Schedule the next check only after the current request settles.
5. Keep a healthy stream open when status remains `running`.
6. Accept `completed` or `failed` from the status endpoint.
7. Do not require `EventSource.onerror`.
8. Reject a response for a run that is no longer active.
9. Reject any result after the same run becomes terminal.
10. Close the stream and clear the timer after a terminal transition.

## Stream Event Contract

Each stream handler captures the run identifier and its `EventSource`.
The handler can update the page only when both still own the active run.

A late `status: running` event cannot replace a terminal presentation.
A late terminal event cannot render output twice after status recovery.

## Completed Presentation Contract

A completed transition must:

1. Set progress to 100 percent.
2. Show the completion message.
3. Apply the terminal output set.
4. Clear the status timer.
5. Close the matching stream.
6. Finish the matching active run.

## Failed Presentation Contract

A failed transition must:

1. Show the failure message.
2. Add the failure to the operation log.
3. Clear the status timer.
4. Close the matching stream.
5. Finish the matching active run.

## Output Identity Contract

The browser identifies one output with:

```text
run_id + exact_server_file_path
```

The browser must not use only the base file name.
The browser must not share output state between run identifiers.

## Output Set Application Contract

For each delivery:

1. Remove repeated exact paths from that delivery.
2. Preserve the first order of distinct paths.
3. Build a canonical run-scoped identity set.
4. Compare it with the last applied identity set.
5. Return without rendering when the identity set is identical.
6. Replace the link list when the identity set changes.
7. Call the preview controller once for each changed nonempty set.

An identical status replay and terminal replay must produce one link.
They must start one preview load.

Two different exact paths must produce two links.
The paths remain different when their base file names match.

The same exact path under two run identifiers must create separate run-scoped
state.

## Empty Terminal Output Contract

The first terminal empty output set for a run must:

1. Clear the visible output links.
2. Hide the output link panel.
3. Reset the results preview.
4. Clear a stale loading presentation.
5. Keep the completed or failed message visible.

The browser must not reset the whole execution panel.

## Cleanup Contract

The browser must clear the timer and close the stream when:

- A run completes.
- A run fails.
- The operator starts another run.
- The operator reconnects to another run.
- The current stream enters its error path.

Cleanup must check run ownership.
Cleanup for an old run must not close a new stream.

## Playwright Evidence Contract

The dedicated module is:

```text
tests/e2e/web_portal/test_operation_stream_recovery.py
```

The #4027 proof must report:

- Status checks examined.
- Terminal transitions examined.
- Stream error calls.
- Requested five-second delays.

The #4032 proof must report:

- Replay sources examined.
- Exact paths examined.
- Rendered links.
- Preview loads.

The #4027 test commit must fail before the #4027 repair.
The #4032 test commit must fail before the #4032 repair.
Each repair must have a separate commit.
