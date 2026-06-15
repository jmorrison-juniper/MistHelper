# Quickstart: device_utils Adoption

**Date**: 2026-06-11 | **Plan**: [plan.md](plan.md)

## Prerequisites

- Python 3.13+
- mistapi >= 0.61.0 (`pip install "mistapi>=0.61.0"`)
- Existing MistHelper environment with `.env` configured

## Verify device_utils Availability

```python
python -c "import mistapi.device_utils; print('device_utils available')"
```

## Development Workflow

### 1. Update mistapi

```bash
pip install "mistapi>=0.61.0" --upgrade
# or with UV:
uv pip install "mistapi>=0.61.0"
```

### 2. Run Tests

```bash
python -m pytest tests/unit/test_device_utils_adapter.py -v
```

### 3. Verify Behavioral Equivalence

For each migrated command, run against the same device and diff CSV output:

```bash
# Before migration (save baseline)
python MistHelper.py --menu 5  # Show MAC table → data/show_mac_table_BEFORE.csv

# After migration (compare)
python MistHelper.py --menu 5  # Show MAC table → data/show_mac_table_AFTER.csv
diff data/show_mac_table_BEFORE.csv data/show_mac_table_AFTER.csv
```

### 4. Fallback Verification

To test fallback behavior, temporarily downgrade mistapi:

```bash
pip install "mistapi==0.59.0"
python MistHelper.py --menu 5  # Should use raw API + WebSocket (log shows fallback)
```

## Key Files

| File | Purpose |
| - | - |
| `src/device/device_utils_adapter.py` | New adapter class |
| `tests/unit/test_device_utils_adapter.py` | Unit tests with mock UtilResponse |
| `MistHelper.py` line ~8868 | `WebSocketCommands` class (rewired to adapter) |
| `MistHelper.py` line ~2338 | `WebSocketManager` class (retained for pcaps/monitoring) |
