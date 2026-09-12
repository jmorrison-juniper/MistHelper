# Offender 08 Evidence: security_events

## Scope
- Symbol: `OrgClientSecurityExporter.security_events`
- Source file: `MistHelper.py`
- Refactor target: `src/refactors/serial_cc/security_events.py`

## Change Summary
- Extracted organization security export workflow into `SecurityEventsService.execute(fast)`.
- Converted `MistHelper.py` method into thin delegator that imports and calls the service.
- Preserved fast-mode cache behavior, progress emission, security policies export, secintel export, rogue AP/client aggregation, and output filenames.

## Radon Complexity
- Before: `D (25)`
- After: `A (1)` in `MistHelper.py`

## Validation Commands
- `python -m pytest tests/unit/serial_cc/test_security_events.py tests/integration/serial_cc/test_security_events_integration.py -q`
- `python -m radon cc MistHelper.py -a -s | Select-String "security_events" -Context 0,2`
- `python -m pytest tests/guardrails/test_wave1_entry_routing_guardrails.py tests/guardrails/test_wave1_safety_classification_guardrails.py tests/unit/test_exports.py tests/unit/test_menu_13_device_stats.py tests/unit/websocket/test_service_ping_manager.py -q`

## Validation Results
- Serial CC offender tests: `4 passed`
- High-signal regression subset: `34 passed`
- Radon offender symbol: `A (1)`

## Notes
- MistHelper-Go `go test ./...` access-denied issue remains environmental and unrelated to this Python refactor.
