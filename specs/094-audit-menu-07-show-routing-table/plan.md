# Implementation Plan — Show Routing Table

## High-level approach
1. Integrate a menu action that invokes WebSocketCommands.show_routing_table with a selected device/session. 
2. Normalize and sanitize the returned JSON into a predictable table model. 
3. Render to console (human-readable table). Provide an optional CLI flag to write a time-stamped snapshot to CSV or SQLite. 
4. Add unit and integration tests using a mocked WebSocket layer.

## Deliverables
- Code: menu registration, handler function WebSocketCommands.show_routing_table wrapper and parser.
- Tests: unit tests for parser/formatter; integration test with mocked WebSocket server.
- Docs: README entry and usage example for menu 7; note on snapshot/export policy.
- Optional: CSV/SQLite snapshot export implementation and configuration.

## Milestones
1. Design & spec sign-off (this artifact) — 0.5 day
2. Implement CLI handler and parser — 1 day
3. Add snapshot export (optional) — 0.5 day
4. Unit tests & integration test with mocked WS — 1 day
5. Docs, QA, commit & PR — 0.5 day

## People / Roles
- Engineer: single engineer (owner) responsible for design, implementation, tests, docs, and PR.

## Verification plan
Manual checks:
- Run menu, verify successful return for a known device; inspect columns and handle empty/error responses. 
- Run with export flag and confirm file output and naming (timestamped). 

Automated tests to add later:
- Unit: parser transforms diverse payload variants into canonical rows. 
- Integration: mocked WebSocket returns sample routing tables, verify the CLI handler returns correct exit code and output structure. 
- Edge cases: very large tables streamed vs paginated; missing fields; error responses.

Note: STOP before IMPLEMENT. This plan prepares for development; do not modify code in this step.