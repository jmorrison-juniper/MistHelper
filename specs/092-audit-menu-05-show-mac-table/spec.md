# Show MAC table — Specification

## Summary
A WebSocket-driven interactive operation that queries a target device/site and returns the current MAC address table (bridging/forwarding table) to the operator UI. Implemented by WebSocketCommands.show_mac_table, it streams a snapshot or updates until the operator ends the session.

## Purpose
Provide NOC engineers a fast, low-latency view of MAC-to-port mappings for troubleshooting bridging/forwarding problems, loop detection, or device verification. Designed for live troubleshooting rather than long-term analytics.

## Stakeholders
- NOC Engineers (primary users)
- Platform Developer (implementer)
- QA/Oncall (validation)

## Acceptance Criteria (pass/fail)
Pass:
- Operator can open a WebSocket session and invoke Show MAC table for a single device or site and receive a correctly formatted MAC table snapshot within 5 seconds.
- Entries include: MAC, VLAN (if applicable), port/interface, age/timestamp, entry type (static/dynamic), and source device id.
- Stream closes cleanly on operator exit; errors return structured error messages.
Fail:
- Missing required fields, malformed payloads, inconsistent timestamps, or session leaks after close.

## API function(s) used
- WebSocketCommands.show_mac_table (entry point). Underlying platform calls depend on device adapter (SNMP/NETCONF/CLI) but must be encapsulated by the WebSocket handler.

## SQL export relevance & recommendation
SQL export: false. Rationale: MAC table is ephemeral and high-cardinality time-series; primary intent is live troubleshooting. Recommendation: do NOT add continuous SQL export by default. Offer an opt-in "snapshot to DB" action to capture a point-in-time export (see plan) for forensic/analytics needs.

## Primary key strategy suggestion
If snapshot export is enabled: composite_pk using [device_id, mac, vlan, port, snapshot_ts]. Use INSERT OR REPLACE for idempotent snapshots.

## Risks / Assumptions
- Assumes underlying device adapter can return MAC table reliably.
- WebSocket session scaling under high concurrent users needs capacity testing.
- Snapshot export may produce large volumes; retention must be defined.

> STOP BEFORE IMPLEMENT: This spec covers up through planning only.