# Task List — Show SSR/SRX Routes (specs/095-audit-menu-08-show-ssr-routes)

- [ ] mh-095-01: discover-ws-payload
  - Description: Inspect WebSocketCommands.show_ssr_routes implementation and capture 2–3 example responses (happy path, empty, error). Save examples to specs/095-audit-menu-08-show-ssr-routes/samples/
  - Dependencies: none

- [ ] mh-095-02: design-data-model
  - Description: Define canonical route row fields (prefix, mask, next_hop, protocol, metric, age, interface, device_id, raw_payload_link). Decide CSV schema. Document in spec folder.
  - Dependencies: mh-095-01

- [ ] mh-095-03: implement-menu-adapter
  - Description: Add menu entry that invokes WebSocketCommands.show_ssr_routes, handles async response, validates JSON, and calls parser.
  - Dependencies: mh-095-01, mh-095-02

- [ ] mh-095-04: implement-parser-normalizer
  - Description: Implement flattening/normalization for route objects with defensive checks for missing fields and type variations.
  - Dependencies: mh-095-02

- [ ] mh-095-05: implement-renderer-and-ui
  - Description: Render routes in console with pagination, filtering (prefix, protocol), and an export prompt (Y/N). Keep render code non-blocking for other menu actions.
  - Dependencies: mh-095-03, mh-095-04

- [ ] mh-095-06: implement-csv-export
  - Description: Optional CSV saver using existing DataExporter.write_csv or minimal CSV writer; include timestamped filename and confirmation message.
  - Dependencies: mh-095-04, mh-095-05

- [ ] mh-095-07: add-tests
  - Description: Add unit tests for parser (multiple sample payloads), a mocked WebSocket integration test for adapter, and CSV verification test. Place tests under tests/ and use existing test harness.
  - Dependencies: mh-095-01, mh-095-03, mh-095-04, mh-095-06

- [ ] mh-095-08: docs-and-changelog
  - Description: Update README menu table, add a short how-to in specs/095 README, and add a UTC-versioned changelog entry.
  - Dependencies: mh-095-03, mh-095-06

- [ ] mh-095-09: review-and-qa
  - Description: Run manual verification against a staging SSR/SRX device; confirm timeouts, large-table behavior, and CSV output integrity. Fix issues found.
  - Dependencies: all implementation tasks

Notes on SQL: If snapshots are later required, create a separate task (mh-095-10) to design snapshot table and bulk-import flow using composite primary key [snapshot_id, device_id, prefix].
