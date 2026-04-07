# Implementation Plan - Show Forwarding Table

## High-level approach
1. Integrate the existing WebSocketCommands.show_forwarding_table invocation into the menu action, maintaining read-only behavior.
2. Parse streaming payloads into a stable display model (mac, vlan, port, age, type). Keep processing lightweight to prevent backpressure.
3. Provide an optional "Snapshot to DB" toggle that, when enabled, records periodic snapshots (configurable interval) using a composite primary-key strategy.
4. Surface explicit error handling and graceful socket teardown.

## Deliverables
- Menu wiring that triggers WebSocketCommands.show_forwarding_table
- Parser and display model for forwarding entries
- Optional snapshot-to-DB implementation (config flag) + composite PK design
- Unit tests for parser and snapshot writer
- README update documenting the operation and snapshot trade-offs

## Milestones
1. Wire WebSocket command and basic display (day 1)
2. Implement efficient streaming parser with unit tests (day 2)
3. Add optional snapshot-to-DB with composite PK and tests (day 3)
4. Docs, manual verification checklist, final review (day 4)

## People / Roles
- Single Engineer: implementer, tester, and doc author.

## Verification plan
Manual checks:
- Connect to device, run the menu operation, confirm live entries appear and update.
- Simulate socket failure and confirm user-visible error.
- If snapshot enabled, confirm a snapshot row set is written and primary keys behave as expected.
Automated tests to add later:
- Parser unit tests for typical and malformed payloads.
- Snapshot writer tests for composite PK upsert semantics.
- Small integration test that mocks WebSocket stream to exercise end-to-end flow.

Note: STOP BEFORE IMPLEMENT — produce only planning artifacts and tasks next.