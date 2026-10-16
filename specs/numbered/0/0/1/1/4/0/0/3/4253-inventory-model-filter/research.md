# Research: Inventory model filter

## Decision

Reuse `PolicyApi.inventory`, `PolicyResponse.collect`, and `PolicyCatalog.common`.
Change the unused gateway-only inventory query to `type="all"`.
The only existing inventory caller outside tests is absent.

## Rationale

The existing request boundary validates status, rows, identifiers, and pagination.
The existing catalog preserves authoritative SSR model constants and the repaired SRX classification.
Filter only display choices. Continue validating preparation against the complete compatible catalog.
The package-level `PolicyInventory` class receives an already checked catalog.
This keeps catalog methods unchanged and avoids a circular import.

## Alternatives considered

- Inventory intersection hides models owned by only one MSP target. Reject it.
- Full-catalog fallback conceals inventory failure. Reject it.
- Filtering catalog validation would prevent explicitly supported future equipment. Reject it.
- Independent SDK transport would duplicate admission and privacy controls. Reject it.

## Tool constraints

PowerShell is unavailable. Generate the equivalent artifacts directly.
The branch hook skill was invoked. Do not execute its branch-switch script because this app owns the current branch.
Optional commit hooks remain deferred until the completed change passes local validation.
