# Data Model: Status Fallback for Quiet Operation Streams

This feature adds no persistent data model.

## Runtime State

- **Active run ID**: The run that the page currently follows.
- **Stream object**: The current `EventSource` connection.
- **Fallback timer**: The pending timer that asks the status route after stream silence.

## State Transition

When any stream event arrives, the browser arms a fresh fallback timer. When the run finishes, the browser clears the timer and resets the controls.
