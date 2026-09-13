# Quickstart: mistapi Upgrade Alignment Implementation

## Prerequisites

- Python 3.13+
- mistapi >= 0.61.3 (`pip install mistapi>=0.61.3`)
- MistHelper.py on feature branch `017-mistapi-upgrade-alignment`

## Implementation Order

### Step 1: Version Pin (requirements.txt)

Change `mistapi>=0.59.1` to `mistapi>=0.61.3`.

### Step 2: Startup Version Check (MistHelper.py)

Add version check near the top of `main()`:

```python
import importlib.metadata
version = importlib.metadata.version("mistapi")
if tuple(int(x) for x in version.split(".")) < (0, 61, 3):
    print(f"ERROR: mistapi {version} is too old. Please upgrade: pip install mistapi>=0.61.3")
    sys.exit(1)
```

### Step 3: Session Exception Handling

Wrap `mistapi.APISession()` calls in try/except per `contracts/session-exceptions.md`.

### Step 4: Device Utility Migration (Per Menu)

For each migrable command in `data-model.md` Entity 4:
1. Import the appropriate `device_utils` submodule
2. Replace the raw API call with the device_utils function
3. Replace WebSocket result polling with `result.wait(timeout=30)`
4. Run `python -m py_compile MistHelper.py` after each menu change
5. Test with `python MistHelper.py --test` for non-destructive menus

### Step 5: WebSocket Module Migration

Follow `contracts/websocket-pattern.md`. Start with PacketCaptureManager, then WebSocketManager.

### Step 6: Verify All

```powershell
python -m py_compile MistHelper.py
python MistHelper.py --test
```

## Validation Between Each Menu

After each menu operation is modified:
1. `python -m py_compile MistHelper.py` — must produce no output
2. Verify the modified function's import paths resolve
3. Run the specific menu with `--menu N` if safe (data extraction operations only)
