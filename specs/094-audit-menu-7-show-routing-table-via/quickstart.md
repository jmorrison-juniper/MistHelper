# Quickstart: Audit Menu #7 — Show Routing Table via WebSocket

**Feature**: 094-audit-menu-7-show-routing-table-via
**Date**: 2025-07-24

## What This Audit Covers

Menu #7 ("Show routing table on switches via WebSocket") in MistHelper. The audit adds test coverage, fixes safety violations, and improves reliability for the routing table WebSocket pipeline.

**Key classes**: `RoutingUtils` (lines 17095–18723), `WebSocketCommands.show_routing_table()` (line 16060)

## Prerequisites

- Python 3.13+ with venv activated
- pytest installed (`pip install pytest`)
- No Mist API credentials needed (all tests run offline)

## Running the Tests

```bash
# Run all routing table tests
pytest tests/unit/test_routing_table.py -v

# Run a specific test class
pytest tests/unit/test_routing_table.py::TestParseRoutingTable -v

# Run with coverage (if pytest-cov installed)
pytest tests/unit/test_routing_table.py --cov=. --cov-report=term-missing
```

## Test Architecture: R1 Pattern

This project uses the **R1 (duplicate-to-isolate)** test pattern. Pure functions from `MistHelper.py` are duplicated into the test file to avoid import side effects.

**Why**: `MistHelper.py` is an 18,700-line monolith with module-level globals (`apisession`, logging config) that crash on import without a configured Mist environment.

**What this means for developers**:
- Do NOT add `import MistHelper` to test files
- When modifying a production function, update its duplicate in the test file too
- Each duplicated function has a comment referencing its source line number

## Key Files

| File | Purpose |
|------|---------|
| `MistHelper.py` lines 17095–18723 | Production code (`RoutingUtils` class) |
| `MistHelper.py` line 16060 | Entry point (`WebSocketCommands.show_routing_table`) |
| `MistHelper.py` lines 3961–4801 | WebSocket infrastructure (`WebSocketManager`) |
| `tests/unit/test_routing_table.py` | All Menu #7 tests (43+ test cases) |
| `tests/conftest.py` | Shared fixtures (`tmp_data_dir`, `isolate_working_directory`) |

## Bug Fixes Included

| Fix | Location | What Changed |
|-----|----------|-------------|
| `input()` to `safe_input()` | `_get_routing_table_params`, `_display_routing_device_guidance` | 7 raw `input()` calls replaced with `InputUtils.safe_input()` for EOF safety |
| Prefix validation | `_get_routing_table_params` | Added `ipaddress.ip_network()` validation with warn-and-confirm |
| Protocol notification | `_get_routing_table_params` | User is notified when unrecognized protocol defaults to "any" |
| Subscription confirmation | `_connect_websocket` | `time.sleep(1)` replaced with `wait_for_subscription_confirmation()` |
| Connection leak | `_connect_websocket` | try/except ensures `disconnect()` on any exception after `connect()` |
| Session ID error | `_execute_routing_table_command` | Added `logging.error()` for missing session ID |

## Verifying Production Behavior

After making changes, verify the monolith compiles:

```bash
python -m py_compile MistHelper.py
```

To test Menu #7 interactively (requires Mist API credentials):

```bash
python MistHelper.py
# Select Menu Option 7
# Choose a site and switch device
# Enter routing table parameters (or press Enter for defaults)
```
