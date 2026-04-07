# Show SSR/SRX Routes — Specification

## Summary
Provide a WebSocket-driven MistHelper menu operation that requests and displays SSR/SRX routing tables via the existing WebSocketCommands.show_ssr_routes function. The operation is read-only, interactive, and intended as an audit/diagnostic utility for NOC engineers.

## Purpose
Quickly surface SSR/SRX route entries (active routes, next-hops, prefixes, route-types) from devices managed via the Mist platform using an existing WebSocket command channel. The output is human-friendly and optionally saveable as CSV for reporting.

## Stakeholders
- Primary: NOC engineers (operators running audits)
- Secondary: SRE/Platform owners, Release manager

## Acceptance Criteria
- PASS: Selecting "Show SSR/SRX Routes" opens a WebSocket request using WebSocketCommands.show_ssr_routes and returns a parsed list of routes shown on-screen within 10s for a normal-sized table (<=2000 entries). Routes include prefix, mask, next-hop, metric, age, and interface where available. Option to save to CSV works and file conforms to simple column schema.
- FAIL: WebSocket errors are unhandled; parsing crashes; output missing core fields (prefix/next-hop) for >5% of entries; UI hangs or blocks other operations.

## API function(s) used
- WebSocketCommands.show_ssr_routes — primary. Supporting utilities: existing JSON flattening helpers, logging, and DataExporter.write_csv (if CSV save supported).

## SQL export relevance & recommendation
- sql_export_relevant: false — SSR/SRX routes are ephemeral, frequently changing, and lack stable natural primary keys. SQL export is not recommended by default.
- Recommendation: If historical snapshots are desired, implement a snapshot table with composite primary key (snapshot_id, prefix, device_id) and timestamp metadata. Store snapshots (one row per route) as occasional bulk imports rather than continuous upsert.

## Primary key strategy suggestion
- If persisting: composite_pk using [snapshot_id, device_id, prefix, route_protocol] to ensure idempotent bulk inserts.

## Risks & Assumptions
- Assumes WebSocketCommands.show_ssr_routes returns structured JSON (not raw text). If raw, a parser will be required.
- Large tables may exceed memory; implement streaming or write-to-disk fallback.
- Access permissions: tool user must have rights to request SSR/SRX data.
- Network/timeouts: handle gracefully with retries and clear error messages.
