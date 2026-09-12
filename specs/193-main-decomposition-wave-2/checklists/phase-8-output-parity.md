# Phase 8 Output Parity Evidence (API/Backend)

Date: 2026-05-26

## Scope

- WebSocket service ping extraction for menu operation `120`.
- Extracted manager and discovery/payload composition logic:
  - `src/websocket/service_ping_manager.py`
  - `src/websocket/service_ping_discovery.py`

## Parity Verification Approach

- Preserved API intent and request payload contract by moving the existing payload composition logic without changing payload keys:
  - `host`
  - `service`
  - `count`
  - `size`
  - optional `tenant`
  - optional `node`
- Preserved websocket transport/result handling contract:
  - same command channel shape: `/sites/{site_id}/devices/{device_id}/cmd`
  - same extended timeout behavior for SSR gateways
  - same raw/parsed output display ordering
- Preserved terminal output semantics for success and timeout paths.

## Backend Output Note

- Menu `120` does not write CSV, SQLite, or polyglot backend artifacts.
- Therefore backend parity for this phase is `N/A` for file/database outputs.
- Phase 8 output parity is satisfied by preserving the API payload schema and websocket/terminal result contract rather than exporter artifacts.

## Test Gate Evidence

- Executed required gate suite:
  - `python -m py_compile MistHelper.py`
  - `python -m ruff check MistHelper.py`
  - `python -m black --check MistHelper.py`
  - `python -m pytest tests/unit/websocket/test_service_ping_manager.py tests/unit/websocket/test_service_ping_discovery.py tests/contract/test_import_graph.py tests/integration/test_runtime_coupling.py -q`
- Final result after parity-strengthening additions: `27 passed, 1 warning in 0.51s`.

## Conclusion

- Phase 8 extracted websocket modules preserve operation `120` API payload and runtime output contracts.
- No CSV/SQLite/polyglot backend artifact drift applies to this menu path.
