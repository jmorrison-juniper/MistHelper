# Implementation Plan: Audit Menu #6 — Show Forwarding Table via WebSocket

**Branch**: `093-audit-menu-6-show-forwarding-table-via` | **Date**: 2026-04-03 | **Spec**: specs/093-audit-menu-6-show-forwarding-table-via/spec.md
**Input**: Feature specification from `specs/093-audit-menu-6-show-forwarding-table-via/spec.md`

## Summary

This plan implements fixes and tests for Menu #6 (`WebSocketCommands.show_forwarding_table`) addressing eight audit findings (AF-01..AF-08). Primary goals:

- Restore test coverage for the forwarding-table workflow (unit + integration with mocked WebSocket/REST).
- Make the flow robust: explicit input validation, clear INFO logs on cancellation, replace raw requests with `mistapi` usage, remove fixed sleeps, add retry/backoff for transient failures, and harden JSON parsing.
- Preserve WebSocket lifecycle guarantees and ensure deterministic cleanup in all exit paths.

Deliverables (this spec directory): plan.md (this file), research.md, data-model.md, quickstart.md, contracts/ (if applicable), and tasks.md generated in Phase 2.

## Technical Context

**Language/Version**: Python 3.13 (repository-wide requirement per constitution)
**Primary Dependencies**: mistapi (>=0.59), websocket-client, pytest, pytest-mock, tenacity, ipaddress (stdlib)
**Storage**: N/A (CLI operation; ephemeral results)
**Testing**: pytest for unit tests; integration tests use a mocked WebSocket server harness
**Target Platform**: Cross-platform CLI (Windows dev + Linux containers)
**Project Type**: CLI tool (MistHelper menu command)
**Performance Goals**: end-to-end operation completes within 90s for typical forwarding tables (SC-001); parser should handle large tables without excessive memory usage
**Constraints**: Must use `mistapi` where available (Constitution). ASCII-only logs. No secrets in logs.
**Scale/Scope**: Single-operator interactive CLI; concurrency is out-of-scope for initial delivery

## Constitution Check

GATE evaluation against MistHelper Constitution (v1.0.0):

1. Technology & Compatibility Constraints: "mistapi is the sole interface to Mist API; direct HTTP calls prohibited when a mistapi method exists." Current code violates this (AF-08). Plan: replace raw requests with mistapi method calls or implement a narrow `mistapi_wrapper` that centralizes authentication and host resolution. This remediation is required before merge; if mistapi lacks an endpoint, document and justify any temporary exception and schedule upstream fix.

2. Safety-First: Input validation and safe_input patterns will be applied. Plan includes CIDR validation, explicit node validation, and no silent discards.

3. Full Deployment Pipeline: Tests will be added and must pass pre-commit and CI.

4. Observability & Logging: Add INFO-level log on user cancellation; redact secrets at logging boundary.

5. Five-Item Rule / Complexity: Refactors will extract helpers to keep functions small and adhere to the Five-Item Rule.

GATE result: PASS once AF-08 remediation path is implemented or formally justified with a tracked follow-up.

## Project Structure

### Documentation (this feature)

```text
specs/093-audit-menu-6-show-forwarding-table-via/
├── plan.md              # This file
├── research.md          # Phase 0 output (research & decisions)
├── data-model.md        # Phase 1 output (entities & validations)
├── quickstart.md        # Phase 1 output (how to run locally/tests)
├── contracts/           # Phase 1: API/command payload examples
└── tasks.md             # Phase 2: actionable tasks (tests, fix, review)
```

### Source Code (repository root)

```text
misthelper/
├── commands/
│   └── websocket_commands.py        # WebSocketCommands.show_forwarding_table (refactor target)
├── utils/
│   ├── routing_utils.py             # execute_show_forwarding_table, parsing helpers
│   └── websocket_manager.py         # shared WebSocket lifecycle (unchanged)
tests/
├── unit/
│   ├── test_routing_utils.py
│   └── test_websocket_commands.py
└── integration/
    └── test_show_forwarding_table_end_to_end.py  # uses mocked WS server
```

**Structure Decision**: Keep code as a CLI module under `misthelper/commands` with routing-specific helpers in `misthelper/utils`. Tests follow existing repo pattern `tests/unit` and `tests/integration`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Exception to `mistapi` rule (if needed) | If `mistapi` lacks the exact convenience wrapper for `show_forwarding_table`, a temporary direct HTTP call may be required to unblock users. Any exception must be narrowly scoped and accompanied by a task to implement a proper `mistapi` method or wrapper. | Implementing a proper mistapi wrapper upstream is preferred but may take longer; temporary exception is timeboxed and documented.


## Phase 0 — Outline & Research (summary)

Research goals (resolve NEEDS CLARIFICATION from Technical Context):

- Confirm mistapi provides a POST helper for `show_forwarding_table` or determine the exact REST path and auth flow to implement a thin wrapper.
- Best practices for WebSocket subscription confirmation (replace time.sleep(1) with subscription ACK or subscribe-and-wait-for-confirmation pattern).
- Recommended JSON parsing strategies for mixed-text + multi-chunk JSON (streaming assembly, lenient extraction using json.JSONDecoder.raw_decode).
- Retry/backoff libraries and patterns (tenacity recommended) and safe limits for interactive CLI.

Decisions (to be recorded in research.md):

- Use `mistapi` for authenticated POST; if missing, implement `mistapi_wrapper.show_forwarding_table(site_id, device_id, payload)` that centralizes auth/host resolution and respects SSL verification and timeouts.
- Replace time.sleep(1) with subscription-confirmation by waiting up to 5s for a server-sent subscribe_ack message on the channel; fall back to continue after timeout with a warning.
- Implement JSON reassembly by scanning the stream for JSON text spans and using json.JSONDecoder().raw_decode in a loop to extract JSON objects, supporting arrays and single objects, merging arrays of rows into single result list.
- Use tenacity for retries with exponential backoff for REST POST (3 attempts) and short reconnect attempts for WebSocket (2 attempts) for transient network errors.

(Full research outputs will be placed in research.md)

## Phase 1 — Design & Contracts (summary)

Prerequisite: research.md completed.

Phase 1 deliverables (to be created in spec directory):
- data-model.md: entity definition for Forwarding Table Entry and WebSocket Session result envelope
- contracts/: JSON payload examples for `show_forwarding_table` request and expected result shapes (success, empty, error)
- quickstart.md: instructions to run unit and integration tests locally (including starting mocked WS server)

Key design decisions:

1. Input validation
   - Use stdlib ipaddress.ip_network() to validate CIDR; prompt operator to re-enter on invalid input. Default to 0.0.0.0/0 when empty.
   - Validate node value strictly against {"node0","node1"} and re-prompt; do not silently discard.
   - Trim and limit service/VRF strings to a sane length (e.g., 128 chars) and reject control characters.

2. WebSocket subscription
   - Wait for subscription ACK message or a bounded period (5s) before proceeding; remove arbitrary time.sleep(1).
   - Use WebSocketManager's message callback to capture subscribe_ack and session results, demultiplexed by session ID.

3. Command execution and session management
   - Use mistapi session helper to POST the command. If mistapi lacks a helper, implement `mistapi_wrapper` to centralize auth/host resolution and respect SSL verification and timeouts.
   - Parse REST response and extract session ID. If not present, raise a handled error shown to the operator.
   - Implement tenacity-based retry on transient HTTP errors (5xx, connection errors) with idempotent retry semantics where safe.

4. JSON parsing
   - Implement a robust _parse_forwarding_table that assembles raw chunks into a buffer and uses json.JSONDecoder().raw_decode repeatedly to extract JSON objects, supporting arrays and single objects, merging arrays of rows into single result list.
   - On empty/whitespace output return []. On parse failure, log details and return [] while making raw output available to operator via 'Show raw output' option.

5. Logging and user feedback
   - INFO-level logs for user cancellations and normal progress messages.
   - ERROR-level logs for parse failures and exceptions with tracebacks.
   - Ensure no API token or secrets are logged.

6. Tests
   - Unit tests for: parameter validation, device selection behavior (including cancellation), subscription ACK handling, REST POST behavior (mocked), JSON parser cases (5+ variations), and cleanup on exceptions.
   - Integration test: mocked WS server that simulates subscription ack, session results, timeouts, and large payloads.

7. Quickstart / developer guidance
   - Instructions to run unit tests: `python -m pytest tests/unit -k forwarding_table` and the integration harness with a helper script `tests/integration/run_mock_ws_server.py`.

## Agent Context Update

Run the provided update script to add new technology notes for AI agents (tenacity, ipaddress, json parsing patterns) to the copilot context file so future agents are aware of the decisions.

Command (executed as part of this plan workflow):

`.specify/scripts/powershell/update-agent-context.ps1 -AgentType copilot`

(Re-run after Phase 1 if new technologies are introduced.)

## Phase 2 — Tasks (high level; detailed tasks.md to be generated)

Planned tasks (examples):

- implement parameter validation helpers; unit tests
- implement mistapi wrapper or replace raw requests with mistapi
- implement subscription-ack wait in WebSocketManager usage
- implement robust JSON parser and unit tests covering 5+ variations
- implement retry/backoff for REST POST and WebSocket reconnects; tests
- add INFO logs on cancellation; tests
- integration test harness using mocked WS server; large payload test
- docs (quickstart, contracts, data-model)
- code review and CI pipeline execution

## Acceptance Criteria Mapping

Map each acceptance criterion from spec to tasks and tests. Example:
- FR-002 (CIDR validation): unit tests for valid/invalid CIDRs + CLI prompt behavior
- FR-007 (parser robustness): parser unit tests covering all specified formats
- FR-011 (tests): ensure coverage thresholds met before merge

---

For implementation, the next step is Phase 0 research output (research.md) and then Phase 1 artifacts (data-model.md, contracts/, quickstart.md). The agent context update script will be executed now to register new technologies in agent context.
