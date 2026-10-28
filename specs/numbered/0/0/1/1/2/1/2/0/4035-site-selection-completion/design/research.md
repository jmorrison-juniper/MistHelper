# Research: Site selection completion

## Decision

Interpret the selected identifier only for menu 92 at the existing handler-outcome boundary.

## Evidence

Current `main` was `9991d30a1` during inspection.
The terminal assessment reproduced `status=failed` with the returned identifier `site-1` and no output files.
The error was `Operation finished without an output file or a no-data message.`
The actual selector reproduced this failure for a name selection.
Index selection instead produced an empty-export message because the legacy marker scan matched `0 ` in its selection log.
Current code already retains handler return values and supports `OperationOutcome`.
The shared selector has multiple callers that require a string identifier.
The issue artifact list returned HTTP 404. The issue screenshot confirms the reported false failure.
The open pull request inventory showed no overlap with the intended files.

## Rationale

A nonblank identifier proves selection, not an export. The menu-specific boundary preserves the existing helper contract.

## Alternatives Considered

- A selection-log marker remains dependent on wording and does not use the returned result.
- A shared selector return-type change breaks identifier callers.
- Removing menu 92 from the portal changes availability without repairing its result.
