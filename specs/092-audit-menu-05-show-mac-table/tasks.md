# Show MAC table — Task List

- showmac-001: Define contract/schema (Dependencies: none)
  - Produce request/response JSON schema, fields: device_id/site_id, filters, capture_snapshot (bool), timeout.

- showmac-002: Adapter integration spec (Dependencies: showmac-001)
  - Identify underlying adapter calls (SNMP/CLI/NETCONF) and required params; define adapter interface method signature.

- showmac-003: Implement WebSocket handler (Dependencies: showmac-001, showmac-002)
  - Implement WebSocketCommands.show_mac_table parameter parsing, validation, and session lifecycle management.

- showmac-004: Implement transformer/serializer (Dependencies: showmac-002)
  - Canonicalize adapter output to fields: mac, vlan, port, age/timestamp, type, device_id.

- showmac-005: Implement optional snapshot persistence (Dependencies: showmac-003, showmac-004)
  - Add opt-in snapshot writer that persists composite_pk [device_id, mac, vlan, port, snapshot_ts]. Feature-flagged.

- showmac-006: Unit tests (Dependencies: showmac-003, showmac-004)
  - Tests for input validation, transformer correctness, and error handling.

- showmac-007: Integration tests (Dependencies: showmac-003, showmac-006)
  - WebSocket emulation test mocking adapter, verify message stream, snapshot write.

- showmac-008: Load/concurrency test (Dependencies: showmac-003)
  - Synthetic test to simulate multiple concurrent sessions; capture resource usage and failure modes.

- showmac-009: Docs & README update (Dependencies: showmac-001, showmac-005)
  - Document usage examples, snapshot export tradeoffs, schema, and troubleshooting.

- showmac-010: QA acceptance & sign-off (Dependencies: showmac-006, showmac-007, showmac-009)
  - Execute acceptance checklist and obtain QA approval.

Notes: Keep tasks small for issue conversion. Stop before coding — these tasks prepare the repo for implementation.