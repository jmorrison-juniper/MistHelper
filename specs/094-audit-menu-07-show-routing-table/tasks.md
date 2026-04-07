# Tasks — Show Routing Table (menu_id:7)

- [ ] rt-001: spec-create — Finalize and commit spec files into specs/094-audit-menu-07-show-routing-table. (depends: none)
  - Description: Place this spec_md artifact and basic JSON metadata in the spec dir.

- [ ] rt-002: ws-wrapper — Implement WebSocket wrapper call for WebSocketCommands.show_routing_table. (depends: rt-001)
  - Description: Create a small, testable function that sends the WS request and returns raw JSON or raises a structured error.

- [ ] rt-003: parser-format — Write parser to normalize routing entries.
  - Description: Accept raw payload, return list of dicts with keys: prefix, next_hop, interface, metric, protocol, age. (depends: rt-002)

- [ ] rt-004: cli-handler — Add menu entry and CLI handler that ties selection -> ws-wrapper -> parser -> render. (depends: rt-002, rt-003)
  - Description: Hook into menu system (menu_id 7) and implement optional --export-snapshot flag.

- [ ] rt-005: snapshot-export — (optional) Implement CSV/SQLite snapshot exporter.
  - Description: If enabled, write time-stamped file and (if SQLite) table with composite PK [device_id, prefix, protocol, snapshot_ts]. (depends: rt-004)

- [ ] rt-006: unit-tests — Add unit tests for parser and exporter.
  - Description: Cover normal payloads, missing fields, and error payloads. (depends: rt-003, rt-005)

- [ ] rt-007: integration-tests — Add integration test using a mocked WebSocket server that returns sample routing tables and error cases.
  - Description: Verify end-to-end flow from menu invocation to output. (depends: rt-002, rt-004, rt-006)

- [ ] rt-008: docs-update — Update README/menu doc with usage example and snapshot/export notes.
  - Description: Include sample command, flags, and explanation why SQL export is disabled by default. (depends: rt-004, rt-005)

- [ ] rt-009: review-and-merge — Create PR, address review comments, include commit message with version and Co-authored-by trailer. (depends: all above)

- [ ] rt-010: final-qa — Manual acceptance checklist execution and sign-off.

Dependencies summary: parser & ws-wrapper must exist before CLI handler; exporter and tests follow handler; docs and PR finalize after tests pass.