# Show Routing Table — Specification

## Summary
Show Routing Table is a WebSocket-driven MistHelper menu operation that requests and displays the routing table from a connected device via the WebSocket command WebSocketCommands.show_routing_table. This operation returns a live snapshot of routing entries for the selected device and renders them to the console (and optional file). It is intended as a diagnostics / troubleshooting view, not a long-term datastore.

## Purpose
Provide NOC engineers with a fast, interactive way to retrieve and inspect a device's routing table over the existing WebSocket channel. Deliver readable, filtered output and an optional snapshot export for audit or offline analysis.

## Stakeholders
- Primary: NOC engineers (consumers of the menu)
- Secondary: Platform engineers maintaining MistHelper
- Reviewer: Release owner for CLI features

## Acceptance Criteria (clear pass/fail)
Pass: 
- Invoking menu_id 7 triggers WebSocketCommands.show_routing_table and returns a non-error payload within configured timeout. 
- Output displays columnized entries: prefix, next-hop, interface, metric, protocol, age. 
- Handles empty tables and error responses gracefully. 
Fail: 
- Command times out without helpful error. 
- Returned payload cannot be parsed or crashes the CLI.

## API function(s) used
- WebSocketCommands.show_routing_table (WebSocket request/response pattern)

## SQL export relevance & recommendation
SQL export relevance: false — this operation returns transient, device-specific snapshots with no stable natural key; it is primarily a troubleshooting view. Recommendation: keep SQL export disabled by default. If archival is desired, add an optional snapshot export path (CSV/SQLite) that writes a time-stamped snapshot table with a composite primary key (see below) and document storage retention.

## Primary key strategy suggestion (if adding export)
If snapshots are stored in SQL, use composite_pk: [device_id, route_prefix, route_protocol, snapshot_timestamp]. Index on device_id and snapshot_timestamp for efficient retrieval.

## Risks / Assumptions
- Assumes WebSocket connectivity and appropriate device permissions. 
- Payload format must be stable or parse logic must be robust to missing fields. 
- Large routing tables may cause performance or display issues — include pagination or streaming fallback. 
- Snapshot archival introduces storage and privacy considerations (avoid storing sensitive next-hop details without policy).
