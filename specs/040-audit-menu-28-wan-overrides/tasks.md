Tasks: Audit Menu 28 - with_wan_overrides

T001 - Document current behavior
- Read MistHelper.py: GatewayExportUtils.with_wan_overrides
- Confirm CSV and API call flow
- Output: spec.md (done)
- Est: 0.5h

T002 - Identify API function name and PK strategy
- Propose canonical api_function_name (e.g., getGatewayOverriddenPorts)
- Propose PK strategy: composite ['device_id','port_name']
- Update plan.md with rationale
- Est: 0.5h

T003 - Implement minor code changes (separate PR)
- Update with_wan_overrides to call DataExporter.write_with_format_selection(..., api_function_name="getGatewayOverriddenPorts")
- Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry for 'getGatewayOverriddenPorts' with composite_pk
- Est: 1.5h

T004 - Add unit tests
- New tests to cover: missing MIST_WAN_TARGET_PORTS, no overrides, overrides present (fast and non-fast), API 403 error handling
- Use monkeypatch to stub CacheUtils and mistapi responses; assert DataExporter.write_with_format_selection called with api_function_name
- Est: 2.0h

T005 - Run CI and lint
- python -m py_compile MistHelper.py
- pytest -q
- Fix issues if any
- Est: 0.5h

Dependencies
- T002 must complete before T003 and T004
- T003 and T004 should be included in same PR

Done: This audit spec and task list created. DO NOT implement changes in this task.
