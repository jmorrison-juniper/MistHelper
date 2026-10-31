# Layout research

## Decision

Apply `overflow-wrap: anywhere` to the dependency panel table addresses.

## Evidence

The unchanged reported journey failed on `/auth/signin`.
At a 390-pixel viewport, the document width was 400 pixels.
The service-check table extended to 399.72 pixels.
Its long service names, addresses, and recovery text determined its minimum content width.

## Rationale

Wrapping reduces the minimum content width and keeps every service detail readable.
The selector changes only the formatted addresses, so headings and state words retain normal line breaks.

## Alternatives considered

- A document overflow clip hides content and does not repair the table.
- A fixed table layout can compress columns unnecessarily on large screens.
- A horizontal table scroller requires a template change and an extra operator action.

## Hook decisions

The mandatory feature hook ran once with the current app branch and `--dry-run`.
The app already supplied the worktree and branch.
Optional commit hooks are deferred until the local gates pass.
Disabled companion hooks do not run.
PowerShell was absent. A session-local official PowerShell release ran the required numeric route resolver and planning setup.
