# Phase 1 Data Model: Per-Module Test Manifest

**Feature**: 1017-remove-coverage-omits
**Refs**: #878
**Success criteria**: SC-001 (6 retained), SC-003 (fail_under=90), SC-006 (no gate gaming)

## 1. Retained non-source inventory (frozen per FR-011)

The following 6 entries remain in `[tool.coverage.run].omit` after T-Final. They MUST match verbatim.

```
tests/*
venv/*
.venv/*
setup.py
*/site-packages/*
src/interfaces/visualization/maps/*
```

## 2. Per-module test manifest

For each of the 36 in-scope modules: target test file path, external touch points, expected fixture bundle, and per-PR mapping.

### P1 — Utilities (PR-1)

| Source module | Test file | External touch points | Fixtures needed |
|--------------|-----------|----------------------|-----------------|
| `src/foundation/support/utils/environment_utils.py` | `tests/unit/utils/test_environment_utils.py` | `os.environ`, `pathlib.Path` | `monkeypatch`, `tmp_path` |
| `src/foundation/support/utils/filter_operator_engine.py` | `tests/unit/utils/test_filter_operator_engine.py` | none (pure logic) | none |
| `src/mist/intelligence/troubleshooting/troubleshoot_utils.py` | `tests/unit/troubleshooting/test_troubleshoot_utils.py` | `mistapi.APISession`, stdin prompt | `MagicMock(spec=mistapi.APISession)`, `monkeypatch` |
| `src/foundation/runtime/input/prompt_client_utils.py` | `tests/unit/input/test_prompt_client_utils.py` | stdin prompt, `mistapi.APISession` | `MagicMock(spec=mistapi.APISession)`, `monkeypatch` |

### P2 — Export helpers (PR-2)

| Source module | Test file | External touch points | Fixtures needed |
|--------------|-----------|----------------------|-----------------|
| `src/operations/exporting/export/org_export_utils.py` | `tests/unit/export/test_org_export_utils.py` | filesystem (JSON writer) | `tmp_path`, `MagicMock(spec=mistapi.APISession)` |
| `src/operations/exporting/export/license_export_utils.py` | `tests/unit/export/test_license_export_utils.py` | filesystem | `tmp_path` |
| `src/operations/exporting/export/const_definitions_exporter.py` | `tests/unit/export/test_const_definitions_exporter.py` | filesystem | `tmp_path` |
| `src/operations/exporting/export/gateway_test_exporter.py` | `tests/unit/export/test_gateway_test_exporter.py` | filesystem, mistapi | `tmp_path`, `MagicMock(spec=mistapi.APISession)` |
| `src/operations/exporting/export/data_exporter.py` | `tests/unit/export/test_data_exporter.py` | filesystem (CSV writer) | `tmp_path` |

### P3 — API / DB / analytics (PR-3)

| Source module | Test file | External touch points | Fixtures needed |
|--------------|-----------|----------------------|-----------------|
| `src/mist/access/api/api_data_fetcher.py` | `tests/unit/api/test_api_data_fetcher.py` | `mistapi.APISession` pagination | `mock_mistapi_paginated_response` (new), `MagicMock(spec=mistapi.APISession)` |
| `src/mist/access/api/api_fetch_utils.py` | `tests/unit/api/test_api_fetch_utils.py` | `mistapi.APISession` | `mock_mistapi_session` (new, repo-wide) |
| `src/mist/access/api/api_core_fetch_utils.py` | `tests/unit/api/test_api_core_fetch_utils.py` | `mistapi.APISession` cursor iteration | `mock_mistapi_paginated_response` |
| `src/foundation/persistence/cache/cache_utils.py` | `tests/unit/cache/test_cache_utils.py` | filesystem cache | `tmp_path`, `monkeypatch` |
| `src/foundation/persistence/db/database_schema_utils.py` | `tests/unit/db/test_database_schema_utils.py` | none (pure DDL string builder) | none |
| `src/mist/intelligence/analytics/data_collection_manager.py` | `tests/unit/analytics/test_data_collection_manager.py` | `mistapi.APISession` | `mock_mistapi_session` |
| `src/mist/intelligence/analytics/insight_metrics_utils.py` | `tests/unit/analytics/test_insight_metrics_utils.py` | `mistapi.APISession` | `mock_mistapi_session` |

### P4a — Org exporters (stats/templates/admin) (PR-4a)

| Source module | Test file | Fixtures needed |
|--------------|-----------|-----------------|
| `src/operations/exporting/export/org_device_stats_exporter.py` | `tests/unit/export/test_org_device_stats_exporter.py` | `mock_mistapi_session`, `tmp_path`, `golden_json_writer` (new) |
| `src/operations/exporting/export/org_template_exporter.py` | `tests/unit/export/test_org_template_exporter.py` | Same as above |
| `src/operations/exporting/export/org_admin_exporter.py` | `tests/unit/export/test_org_admin_exporter.py` | Same as above |

**PR-4a introduces** `tests/unit/export/conftest.py` housing `golden_json_writer`, `golden_csv_writer`, and org-exporter mock factories reused by PR-4b/PR-5a/PR-5b.

### P4b — Org exporters (config/alarms/security/sites) (PR-4b)

| Source module | Test file | Fixtures needed |
|--------------|-----------|-----------------|
| `src/operations/exporting/export/org_config_exporter.py` | `tests/unit/export/test_org_config_exporter.py` | PR-4a shared fixtures |
| `src/operations/exporting/export/org_alarm_event_exporter.py` | `tests/unit/export/test_org_alarm_event_exporter.py` | PR-4a shared fixtures |
| `src/operations/exporting/export/org_client_security_exporter.py` | `tests/unit/export/test_org_client_security_exporter.py` | PR-4a shared fixtures |
| `src/operations/exporting/export/org_site_exporter.py` | `tests/unit/export/test_org_site_exporter.py` | PR-4a shared fixtures |

### P5a — Site exporters + gateway HA (PR-5a)

| Source module | Test file | Fixtures needed |
|--------------|-----------|-----------------|
| `src/operations/exporting/export/site_anomaly_exporter.py` | `tests/unit/export/test_site_anomaly_exporter.py` | PR-4a shared fixtures |
| `src/operations/exporting/export/site_config_exporter.py` | `tests/unit/export/test_site_config_exporter.py` | PR-4a shared fixtures |
| `src/operations/exporting/export/site_device_exporter.py` | `tests/unit/export/test_site_device_exporter.py` | PR-4a shared fixtures |
| `src/operations/exporting/export/sites_by_ap_model_exporter.py` | `tests/unit/export/test_sites_by_ap_model_exporter.py` | PR-4a shared fixtures |
| `src/mist/resources/gateway/gateway_ha_exporter.py` | `tests/unit/gateway/test_gateway_ha_exporter.py` | `mock_mistapi_session` |

### P5b — Reports + inventory facade (PR-5b)

| Source module | Test file | Fixtures needed |
|--------------|-----------|-----------------|
| `src/mist/intelligence/reports/global_wired_client_report_generator.py` | `tests/unit/reports/test_global_wired_client_report_generator.py` | `mock_mistapi_session`, `tmp_path` |
| `src/mist/intelligence/reports/offline_device_reporter.py` | `tests/unit/reports/test_offline_device_reporter.py` | `mock_mistapi_session`, `tmp_path` |
| `src/mist/intelligence/reports/sfp_transceiver_data_processor.py` | `tests/unit/reports/test_sfp_transceiver_data_processor.py` | `mock_mistapi_session` |
| `src/mist/intelligence/reports/wired_client_manufacturer_report_generator.py` | `tests/unit/reports/test_wired_client_manufacturer_report_generator.py` | `mock_mistapi_session`, `tmp_path` |
| `src/mist/resources/inventory/org_device_inventory_summary_facade.py` | `tests/unit/inventory/test_org_device_inventory_summary_facade.py` | `mock_mistapi_session` |

### P6 — State-changing managers (PR-6) — Principle III

| Source module | Test file | Confirmation path tested | Fixtures |
|--------------|-----------|-------------------------|----------|
| `src/mist/resources/device/arp_command_manager.py` | `tests/unit/device/test_arp_command_manager.py` | Accept + reject | `mock_mistapi_session`, `monkeypatch` on `safe_input` |
| `src/mist/resources/device/device_reboot_manager.py` | `tests/unit/device/test_device_reboot_manager.py` | Accept + reject (destructive) | Same |
| `src/operations/execution/firmware/firmware_manager.py` | `tests/unit/firmware/test_firmware_manager.py` | `confirmation == "UPGRADE"` + reject early-return | Same |
| `src/mist/resources/site/bulk_radius_wlan_config_manager.py` | `tests/unit/site/test_bulk_radius_wlan_config_manager.py` | Rollback exercised via injected exception | Same |
| `src/mist/resources/org/org_ticket_manager.py` | `tests/unit/org/test_org_ticket_manager.py` | Accept + reject | Same |

### P7 — SSH / TUI / prompt (PR-7)

| Source module | Test file | External touch points | Fixtures |
|--------------|-----------|----------------------|----------|
| `src/operations/execution/ssh/cli_shell_manager.py` | `tests/unit/ssh/test_cli_shell_manager.py` | `paramiko.SSHClient`, `Channel`, interactive prompt | `mock_paramiko_ssh_client` (new) |
| `src/interfaces/visualization/ui/tui.py` | `tests/unit/ui/test_tui.py` | `sshkeyboard.listen_keyboard`, terminal render | `mock_sshkeyboard_listen` (extend existing `tests/unit/ui/conftest.py`) |
| `src/interfaces/visualization/ui/prompt_utils.py` | `tests/unit/ui/test_prompt_utils.py` | stdin, `safe_input()` | `monkeypatch` |

FR-015 candidates: `tui.py` and `cli_shell_manager.py` (per plan.md Decision 5). Escape hatch cap = 2.

### P8 — Websocket wildcard (PR-8a/b/c)

**PR-8a (toplevel, 5 files)**

| Source | Test file |
|--------|-----------|
| `src/mist/realtime/websocket/__init__.py` | `tests/unit/websocket/test_init.py` |
| `src/mist/realtime/websocket/commands.py` | `tests/unit/websocket/test_commands.py` |
| `src/mist/realtime/websocket/context.py` | `tests/unit/websocket/test_context.py` |
| `src/mist/realtime/websocket/manager.py` | `tests/unit/websocket/test_manager.py` |
| `src/mist/realtime/websocket/service_ping_discovery.py` + `service_ping_manager.py` | `tests/unit/websocket/test_service_ping_discovery.py`, `test_service_ping_manager.py` |

**PR-8b (diagnostics, 4 files)**

| Source | Test file |
|--------|-----------|
| `src/mist/realtime/websocket/diagnostics/__init__.py` | `tests/unit/websocket/diagnostics/test_init.py` |
| `src/mist/realtime/websocket/diagnostics/arp_executor.py` | `tests/unit/websocket/diagnostics/test_arp_executor.py` |
| `src/mist/realtime/websocket/diagnostics/common.py` | `tests/unit/websocket/diagnostics/test_common.py` |
| `src/mist/realtime/websocket/diagnostics/ping_executor.py` | `tests/unit/websocket/diagnostics/test_ping_executor.py` |

**PR-8c (polling, 5 files)**

| Source | Test file |
|--------|-----------|
| `src/mist/realtime/websocket/polling/__init__.py` | `tests/unit/websocket/polling/test_init.py` |
| `src/mist/realtime/websocket/polling/completion_detector.py` | `tests/unit/websocket/polling/test_completion_detector.py` |
| `src/mist/realtime/websocket/polling/message_router.py` | `tests/unit/websocket/polling/test_message_router.py` |
| `src/mist/realtime/websocket/polling/result_collector.py` | `tests/unit/websocket/polling/test_result_collector.py` |
| `src/mist/realtime/websocket/polling/result_combiner.py` | `tests/unit/websocket/polling/test_result_combiner.py` |

All websocket tests use `mock_websocket_transport` fixture from `tests/unit/websocket/conftest.py` (introduced PR-8a).

## 3. Integration-only paths (mock vs `@pytest.mark.integration`)

The following code paths CANNOT be faithfully mocked and MUST use `@pytest.mark.integration` (gated by `.env` credentials — excluded from default CI run per SC-007).

| Path | Reason for integration marker | Alternative considered |
|------|------------------------------|----------------------|
| `troubleshoot_utils.py` end-to-end Marvis query flow | Marvis response shape is model-dependent; mock cannot mimic real semantics | Rejected: shape mocks would not exercise real branch logic |
| `firmware_manager.py` actual upgrade RPC | State-changing device call; NEVER mocked as if real | Not applicable — real test only in staged integration environment |
| `bulk_radius_wlan_config_manager.py` multi-step rollback under real API errors | API error taxonomy is broader than any mock | Mock covers happy path + one injected exception; integration marker covers real error surface |

All three integration paths remain covered by mocked unit tests for the code-under-test that lives in the module. Integration marker is additive, not a substitute.

## 4. Fixture registry (source of truth)

| Fixture | Location | Scope | Contract file |
|---------|----------|-------|---------------|
| `mock_mistapi_session` | `tests/conftest.py` | function | `contracts/shared_fixtures.md` §1 |
| `mock_config` | `tests/conftest.py` | function | `contracts/shared_fixtures.md` §2 |
| `mock_mistapi_paginated_response` | `tests/unit/api/conftest.py` | function | `contracts/shared_fixtures.md` §3 |
| `golden_json_writer` | `tests/unit/export/conftest.py` | function | `contracts/shared_fixtures.md` §4 |
| `golden_csv_writer` | `tests/unit/export/conftest.py` | function | `contracts/shared_fixtures.md` §4 |
| `mock_paramiko_ssh_client` | `tests/unit/ssh/conftest.py` | function | `contracts/shared_fixtures.md` §5 |
| `mock_sshkeyboard_listen` | `tests/unit/ui/conftest.py` | function | `contracts/shared_fixtures.md` §6 |
| `mock_websocket_transport` | `tests/unit/websocket/conftest.py` | function | `contracts/shared_fixtures.md` §7 |
