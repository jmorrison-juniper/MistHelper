# Show MAC table — Implementation Plan

## High-level approach
1. Extend WebSocketCommands.show_mac_table to accept parameters (device_id, site_id, capture_snapshot=false, timeout, filters).
2. Query device adapter for MAC table (synchronous snapshot), transform into canonical schema, and stream via WebSocket. Support optional single snapshot persistence when requested.
3. Add opt-in DB export path to persist snapshot (not continuous capture).
4. Add JSON schema/contract for client and tests.

## Deliverables
- Updated WebSocket handler and contract (request/response schema).
- Adapter integration call and canonicalization code (transformer/serializer).
- Optional snapshot persistence method (writes to SQLite/DB) behind a feature flag.
- Unit tests, integration tests (WebSocket emulation), and QA checklist.
- README snippet documenting usage and snapshot export tradeoffs.

## Milestones
- M1 (Design) — finalize request/response schema and snapshot DB schema (1 day).
- M2 (Implementation) — implement handler + transformer + optional snapshot export (2 days).
- M3 (Testing) — unit and integration tests, load test for concurrent WebSocket sessions (1 day).
- M4 (Docs & QA) — user docs and acceptance verification (0.5 day).

## People / Roles
Single engineer (implementer) responsible for design, implementation, tests, and docs. Collaborate with QA for validation scenarios.

## Verification plan
Manual checks:
- Open WebSocket session, request MAC table, validate fields and types, confirm clean close.
- Trigger snapshot export and verify DB row(s) present with composite PK.
Automated tests to add later:
- Unit tests for transformer and schema validation.
- Integration test that mocks adapter and asserts WebSocket messages stream as expected.
- Concurrency test that simulates N concurrent sessions and measures memory/connection stability.

> STOP BEFORE IMPLEMENT: This plan stops at verification and readiness to implement.