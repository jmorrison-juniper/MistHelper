# Implementation Plan — Show SSR/SRX Routes

## High-level approach
1. Inspect WebSocketCommands.show_ssr_routes to confirm message/response schema. 2. Implement a menu adapter that triggers the WebSocket call, awaits response, validates JSON, flattens route objects, and renders a paginated console view. 3. Add an optional CSV export path (no direct SQL). 4. Add unit tests and a mock WebSocket integration test.

## Deliverables
- Updated menu entry wiring invoking WebSocketCommands.show_ssr_routes
- Parser/normalizer for SSR/SRX route JSON -> canonical rows
- Console renderer with pagination and filters (prefix, protocol)
- Optional CSV exporter and tests
- Spec + README snippet and changelog entry

## Milestones
1. Discovery (read existing WebSocket command and sample payloads) — 0.5 day
2. Implementation (adapter, parser, renderer, CSV save) — 1.5 days
3. Tests (unit + mocked integration) — 0.5–1 day
4. Review, docs, and final QA — 0.5 day

## People / Roles
- Engineer: 1 (implementer, tester, committer). Responsibilities: code, tests, docs, and verify.

## Verification plan
- Manual checks: run menu operation against a staging device, verify displayed columns (prefix, next-hop, metric, age, interface), and save CSV; inspect CSV column values and counts.
- Automated tests to add later: unit tests for parser (various payload shapes), a mocked WebSocket integration test simulating success and error payloads, and a CSV roundtrip test verifying header/row correctness.

Notes: Stop before implement — this plan covers discovery, design, and test strategy only.
