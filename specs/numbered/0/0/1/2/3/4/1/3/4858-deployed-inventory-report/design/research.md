# Research: Deployed Inventory Report

## Decision 1: Add Deployed Inventory to Menu 308

**Decision**: Extend menu 308 with deployed inventory detail and summary reports.

**Rationale**: The existing stock report filters out records with a site ID. This behavior is correct for stock, but it hides deployed AP, switch, gateway, and SSR inventory. The live 2026-11-19 run showed 152 T-Mobile USA Retail stock devices. The separate 2026-11-11 snapshot recorded 27,030 deployed devices for the same organization.

**Alternatives considered**:
- Use the stock report only: rejected because it omits all assigned devices.
- Run menu 144 separately: not accepted because the customer needs one menu operation.
- Combine only console counts: rejected because operators need exportable evidence.

## Decision 2: Use SDK Pagination for Inventory

**Decision**: Fetch inventory through the mistapi SDK continuation path and request Virtual Chassis records explicitly.

**Rationale**: The existing MSP inventory exporter reads a first page and calls the SDK continuation helper. This pattern reconciles inventory sets larger than 1000 devices.

**Alternatives considered**:
- Direct page loops: retained as an implementation fallback only if the SDK continuation contract fails a test.
- Direct HTTP: rejected by repository policy.

## Decision 3: Split Deployed and Stock Records

**Decision**: A record with a site ID enters deployed inventory. A record with no site ID enters stock inventory.

**Rationale**: This rule separates the two report subjects without double counting a serial.

**Alternatives considered**:
- Infer stock from connected status: rejected because connected stock-like records can be ambiguous.
- Infer deployment from JSI evidence: rejected because JSI is contract evidence, not the deployment source.

## Decision 4: Export Linked Detail and Summary Rows

**Decision**: Add a deployed inventory detail CSV and a deployed inventory summary CSV.

**Rationale**: Detail rows support serial review. Summary rows support fast renewal totals and organization comparison.

**Alternatives considered**:
- Detail only: rejected because 27,000 rows are difficult to reconcile in a console.
- Summary only: rejected because serial, site, model, and connection evidence would be lost.

## Decision 5: Use Structlog as the Frontend

**Decision**: Configure structlog as the event frontend and keep stdlib logging as the console and file backend.

**Rationale**: Structlog produces concise key-value diagnostics. Stdlb handlers still provide level filtering, file rotation, ANSI terminal control, traceback handling, and the existing redaction filter.

**Alternatives considered**:
- Replace stdlib logging with a standalone structlog setup: rejected because existing handlers and filters depend on stdlib integration.
- Keep separate structlog JSON output: rejected because it bypasses the configured console and file level behavior.
- Use only stdlib formatting: rejected because it does not provide the concise structured frontend requested for database and DNS diagnostics.
