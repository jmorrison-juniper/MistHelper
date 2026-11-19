# Data Model: Inventory search status

## Initial Response

`status_code` must be an integer from 200 through 299 and must not be a boolean.
Absent, null, malformed, and non-success statuses stop the operation before pagination.
`data` retains the SDK list or results-envelope shape.
`next` remains the SDK continuation field.

## Writer Result

The existing writer returns a boolean.
False records an error and stops the persistence and export-success messages.
True retains the existing successful path.
No schema, primary key, or storage format changes.
