# Research: Inventory search status

## Decision

Validate the initial response in the existing exporter.
Use the writer boolean to control success messages.

## Rationale

The installed `APIResponse` initializes `status_code` to `None` for a transport failure.
The installed `get_all` reads rows and continuation links without validating the initial HTTP status.
The existing writer returns a boolean. The exporter currently ignores it.
The existing exception handler logs the failure and returns `None`.

## Alternatives Considered

A shared pagination change exceeds the reservation and affects unrelated operations.
A public return-type change breaks the required public behavior.
Both alternatives are excluded.

## Limitations

Later-page response validation is not part of this repair.
The tests do not claim that later pagination failures are detected.
