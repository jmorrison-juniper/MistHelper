# Offender 06 Evidence: _start_site_client_capture_wireless

## Scope
- Symbol: `_LegacyPacketCaptureManager._start_site_client_capture_wireless`
- Source file: `MistHelper.py`
- Refactor target: `src/refactors/serial_cc/start_site_client_capture_wireless.py`

## Change Summary
- Extracted wireless client capture flow into `SiteWirelessClientCaptureService.execute(manager)`.
- Converted `MistHelper.py` method into thin delegator that imports and calls the service.
- Preserved prompt text, payload keys, validation ranges, and execution routing (`_execute_site_capture_loop` vs `_execute_site_capture`).

## Radon Complexity
- Before: `D (26)`
- After: `A (1)` in `MistHelper.py`

## Validation Commands
- `python -m py_compile MistHelper.py src/refactors/serial_cc/start_site_client_capture_wireless.py`
- `python -m pytest tests/unit/serial_cc/test_start_site_client_capture_wireless.py tests/integration/serial_cc/test_start_site_client_capture_wireless_integration.py -q`
- `python -m pytest tests/unit/test_packet_capture.py -k wireless -q`
- `python -m pytest tests/guardrails/test_wave1_entry_routing_guardrails.py tests/guardrails/test_wave1_safety_classification_guardrails.py tests/unit/test_exports.py tests/unit/test_menu_13_device_stats.py tests/unit/websocket/test_service_ping_manager.py -q`
- `python -m radon cc MistHelper.py -a -s | Select-String "_start_site_client_capture_wireless" -Context 0,1`

## Validation Results
- Syntax: pass
- Serial CC offender tests: `5 passed`
- Targeted packet-capture tests: `4 passed`
- High-signal regression subset: `34 passed`
- Radon offender symbol: `A (1)`

## Notes
- Current MistHelper-Go `go test ./...` failure remains environmental (`Access is denied` for generated test executable in `internal/menu`), unrelated to this Python refactor.
