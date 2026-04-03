# Quickstart: Audit Menu #5 — Show MAC Table via WebSocket

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md)

## Prerequisites

- Python 3.13+ installed
- Repository cloned: `C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper`
- Virtual environment active (`.venv`)

## Setup

```powershell
# Navigate to repository root
cd "C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper"

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Verify Python version
python --version  # Must be 3.13+
```

## Key Files

| File | Purpose |
|------|---------|
| `MistHelper.py` | Main source — `WebSocketCommands.show_mac_table` (line ~15817), `WebSocketManager` (line ~3961) |
| `tests/unit/test_show_mac_table.py` | NEW — unit tests for show_mac_table (to be created) |
| `tests/unit/test_websocket_manager.py` | NEW — unit tests for WebSocketManager (to be created) |
| `tests/conftest.py` | Shared pytest fixtures (`tmp_data_dir`, `isolate_working_directory`) |

## Running Tests

```powershell
# Run all unit tests
pytest tests/unit/ -v

# Run only the new MAC table tests (after creation)
pytest tests/unit/test_show_mac_table.py -v
pytest tests/unit/test_websocket_manager.py -v

# Run with coverage report
pytest tests/unit/test_show_mac_table.py tests/unit/test_websocket_manager.py --cov=MistHelper --cov-report=term-missing -v

# Syntax validation (required before every commit)
python -m py_compile MistHelper.py
```

## Test Patterns

All tests must follow the existing project conventions:

1. **No network calls** — mock all external dependencies (WebSocket, REST, mistapi)
2. **No `.env` loading** — tests run in isolated `tmp_path` directory (autouse fixture)
3. **Class-based organization** — `class TestShowMacTable:`, `class TestWebSocketManager:`
4. **30-second timeout** — unit tests must complete within 30 seconds
5. **Full word variable names** — `websocket_manager`, not `ws_mgr`

### Mocking Strategy

```python
# Example: mock WebSocketManager for show_mac_table tests
from unittest.mock import MagicMock, patch

@patch("MistHelper.WebSocketManager")
@patch("MistHelper.PromptUtils.select_device_id_from_inventory", return_value="device-uuid")
@patch("MistHelper.PromptUtils.select_site_id_from_csv", return_value="site-uuid")
def test_happy_path(mock_site, mock_device, MockWSManager):
    mock_manager = MockWSManager.return_value
    mock_manager.connect.return_value = True
    mock_manager.subscribe_to_channel.return_value = True
    mock_manager.wait_for_subscription_confirmation.return_value = True
    mock_manager.wait_for_command_result.return_value = {
        "raw": "Ethernet switching table : 44 entries, 40 learned",
        "session": "test-session-id",
    }
    # ... call show_mac_table and assert output
```

## Audit Finding → Code Location Map

| Finding | Description | Location in MistHelper.py |
|---------|-------------|---------------------------|
| AF-01 | Zero test coverage | N/A — tests to be created |
| AF-02 | `locals().get()` cleanup | Line ~16032 (`finally` block) |
| AF-03 | Unconfirmed subscription | Line ~15885 (`subscribe_to_channel` returns immediately) |
| AF-04 | Hardcoded `time.sleep(1)` | Line ~15896 |
| AF-05 | Raw `requests.post` | Line ~15928 |
| AF-06 | Fragile completion detection | Lines ~4398–4457 (`wait_for_command_result`) |
| AF-07 | Ambiguous empty table message | Lines ~15991–15993 |
| AF-08 | Inline `import traceback` | Line ~16023 |

## Commit Workflow

After making changes, follow the deployment pipeline (Constitution Principle IV):

```powershell
# 1. Validate syntax
python -m py_compile MistHelper.py

# 2. Run tests
pytest tests/unit/ -v

# 3. Commit
git add MistHelper.py tests/unit/test_show_mac_table.py tests/unit/test_websocket_manager.py
git commit -m "version YY.MM.DD.HH.MM - audit Menu #5 show_mac_table: fix AF-01 through AF-08"

# 4. Push
git push origin 092-audit-menu-5-show-mac-table-via

# 5. Wait for CI (if on main)
# gh run watch <run-id>
```
