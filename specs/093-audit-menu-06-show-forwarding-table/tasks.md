# Tasks (todo list) - Show Forwarding Table

- [ ] sf-001: wire-menu-command - Wire menu entry to call WebSocketCommands.show_forwarding_table (depends: none)
  - Details: Add menu metadata, hook function_ref -> invoke websocket command and open stream.

- [ ] sf-002: parse-stream-model - Implement streaming parser and in-memory model (depends: sf-001)
  - Details: Normalize fields to {mac, vlan, port, age, type, device_id, received_at}; include validation and safe defaults.

- [ ] sf-003: ui-renderer - Build or adapt UI/table renderer for forwarding entries (depends: sf-002)
  - Details: Support incremental updates, pagination/limit, and stop/refresh controls.

- [ ] sf-004: error-handling - Add robust socket/error handling and user messaging (depends: sf-001)
  - Details: Retry policy for transient errors, auth-expiry messages, graceful teardown.

- [ ] sf-005: snapshot-opt-in - Add optional Snapshot-to-DB toggle and configuration (depends: sf-002)
  - Details: Configurable interval, retention policy, and privacy warning in UI.

- [ ] sf-006: snapshot-writer - Implement snapshot writer using composite_pk (device_id, mac, vlan, port, snapshot_ts) (depends: sf-005)
  - Details: Write as INSERT OR REPLACE or upsert; compress/ dedupe before write.

- [ ] sf-007: unit-tests - Add unit tests for parser and snapshot writer (depends: sf-002, sf-006)
  - Details: Cover typical, large, and malformed stream entries.

- [ ] sf-008: integration-test-mock - Create a mock WebSocket stream test harness for end-to-end tests (depends: sf-001, sf-002, sf-003)

- [ ] sf-009: docs-readme - Update README and specs/093-audit-menu-06-show-forwarding-table with usage, snapshot guidance, and acceptance criteria (depends: sf-001..sf-006)

- [ ] sf-010: manual-verification - Manual QA checklist execution and sign-off (depends: sf-003, sf-004, sf-007)

Each task is scoped for a single engineer; tasks are ordered for minimal dependencies. Stop before writing implementation code; these tasks will be converted to issues when ready.