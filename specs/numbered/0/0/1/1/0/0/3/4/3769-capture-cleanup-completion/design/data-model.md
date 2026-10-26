# Utility lifecycle

No stored model changes.

## Execution result

The lifecycle retains either normal completion or the execution exception until cleanup ends.
The existing finisher maps that result after successful cleanup.

## Cleanup boundary

The existing stream client closes before capture cleanup.
Capture cleanup reads the capture scope and identifier from the existing run context.
Only a matching capture receives a deletion request.

## Terminal transition

Successful cleanup permits the existing stopped, finished, timed-out, or failed result.
A cleanup exception produces one failed result with a safe reason.
The cleanup failure result overrides an operator stop or execution error.
