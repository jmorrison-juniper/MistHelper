# Data Model: Clear Stale Operation Results

This feature adds no persistent data model.

## Runtime State

- **Execution panel state**: The logs, debug logs, output files, progress, status badge, and status message for the active selection.
- **Result table state**: The selected output file, columns, rows, sort order, filter text, pagination, and truncation notice.

## State Transition

When the operator selects another operation, the browser clears both runtime states before it loads parameter controls for the new selection.
