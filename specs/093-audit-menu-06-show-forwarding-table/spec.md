# Show Forwarding Table - Specification

## Summary
Show Forwarding Table (menu_id: 6) is a WebSocket-driven operation that requests and displays the device forwarding/bridging (L2) table via an interactive WebSocket command: WebSocketCommands.show_forwarding_table. The operation displays live/near-real-time entries (MAC, VLAN, port, age, type) for a selected device or site.

## Purpose
Provide NOC engineers a quick, low-latency view of forwarding table entries for troubleshooting MAC-flap, access, or L2 reachability issues. This is an interactive diagnostic (read-only) view surfaced from the WebSocket API.

## Stakeholders
- NOC Engineers (primary users)
- Network Ops Team Lead
- Platform Owner / DevOps

## Acceptance Criteria
Pass:
- WebSocket command sent and acknowledged to target device/service
- Forwarding entries rendered in UI (columns: mac, vlan, port, age, entry_type)
- Errors surfaced when socket/auth fails
- Operation completes or streams until user stop
Fail:
- No socket connection or invalid auth
- Malformed payload or missing required fields

## API function(s) used
- WebSocketCommands.show_forwarding_table (initiates request; receives streaming updates)

## SQL export relevance & recommendation
SQL export: NO (current: false). Reason: forwarding table is ephemeral, high-volume, and time-sensitive. Raw long-term storage is rarely useful without aggregation. Recommendation: do NOT add full SQL export by default. If persistence is desired, implement an optional snapshot-to-DB feature that captures periodic snapshots (configurable) and writes only diffs or aggregated counts.

## Primary key strategy suggestion
If snapshots are persisted: use composite_pk strategy: [device_id, mac, vlan, port, snapshot_timestamp]. Use "composite_pk" to avoid deduplication conflicts across time.

## Risks / Assumptions
- Assumes WebSocket auth and device capabilities exist.
- Large tables may stream many entries; risk of UI/ memory pressure.
- Time synchronization for snapshots must be reliable.
- Assumes privacy/compliance rules allow storing MAC data if persistence enabled.
