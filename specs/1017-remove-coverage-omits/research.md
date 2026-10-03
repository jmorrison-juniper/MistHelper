# Phase 0 Research: Coverage Omit Removal Audit

**Feature**: 1017-remove-coverage-omits
**Branch cut**: `main` @ `3044717` (2026-07-13, post-#966 merge)
**Refs**: #878

## 1. Omit-list snapshot at branch cut

Read verbatim from `pyproject.toml [tool.coverage.run].omit` (lines 238-287) at HEAD `3044717`.

### Retained non-source (6 entries, FR-011 / SC-001 — frozen)

| # | Entry | Rationale |
|---|-------|-----------|
| 1 | `tests/*` | Test files themselves — coverage does not measure test code. |
| 2 | `venv/*` | Virtualenv site-packages — third-party code. |
| 3 | `.venv/*` | Alternate venv location. |
| 4 | `setup.py` | Legacy build stub (project builds via `hatchling`). |
| 5 | `*/site-packages/*` | Any third-party install path. |
| 6 | `src/interfaces/visualization/maps/*` | Vendored maps subsystem — separate lifecycle. |

### In-scope for removal (35 explicit + 1 wildcard = 36 modules total)

**P1 — Utilities (4)**
- `src/mist/intelligence/troubleshooting/troubleshoot_utils.py`
- `src/foundation/runtime/input/prompt_client_utils.py`
- `src/foundation/support/utils/environment_utils.py`
- `src/foundation/support/utils/filter_operator_engine.py`

**P2 — Export helpers (5, incl. FR-016 delta `data_exporter.py`)**
- `src/operations/exporting/export/const_definitions_exporter.py`
- `src/operations/exporting/export/data_exporter.py`
- `src/operations/exporting/export/gateway_test_exporter.py`
- `src/operations/exporting/export/license_export_utils.py`
- `src/operations/exporting/export/org_export_utils.py`

**P3 — API / DB / analytics (7, incl. FR-016 deltas `api_core_fetch_utils`, `cache_utils`, `insight_metrics_utils`)**
- `src/mist/intelligence/analytics/data_collection_manager.py`
- `src/mist/intelligence/analytics/insight_metrics_utils.py`
- `src/mist/access/api/api_data_fetcher.py`
- `src/mist/access/api/api_fetch_utils.py`
- `src/mist/access/api/api_core_fetch_utils.py`
- `src/foundation/persistence/cache/cache_utils.py`
- `src/foundation/persistence/db/database_schema_utils.py`

**P4a — Org exporters, stats/templates/admin (3)**
- `src/operations/exporting/export/org_device_stats_exporter.py`
- `src/operations/exporting/export/org_template_exporter.py`
- `src/operations/exporting/export/org_admin_exporter.py`

**P4b — Org exporters, config/alarms/security/sites (4, incl. FR-016 delta `org_site_exporter.py`)**
- `src/operations/exporting/export/org_config_exporter.py`
- `src/operations/exporting/export/org_alarm_event_exporter.py`
- `src/operations/exporting/export/org_client_security_exporter.py`
- `src/operations/exporting/export/org_site_exporter.py`

**P5a — Site exporters + gateway HA (5)**
- `src/operations/exporting/export/site_anomaly_exporter.py`
- `src/operations/exporting/export/site_config_exporter.py`
- `src/operations/exporting/export/site_device_exporter.py`
- `src/operations/exporting/export/sites_by_ap_model_exporter.py`
- `src/mist/resources/gateway/gateway_ha_exporter.py`

**P5b — Reports + inventory facade (5, reshuffled from spec P6 per plan.md Decision 4)**
- `src/mist/intelligence/reports/global_wired_client_report_generator.py`
- `src/mist/intelligence/reports/offline_device_reporter.py`
- `src/mist/intelligence/reports/sfp_transceiver_data_processor.py`
- `src/mist/intelligence/reports/wired_client_manufacturer_report_generator.py`
- `src/mist/resources/inventory/org_device_inventory_summary_facade.py`

**P6 — State-changing managers (5, Principle III)**
- `src/mist/resources/device/arp_command_manager.py`
- `src/mist/resources/device/device_reboot_manager.py`
- `src/operations/execution/firmware/firmware_manager.py`
- `src/mist/resources/site/bulk_radius_wlan_config_manager.py`
- `src/mist/resources/org/org_ticket_manager.py`

**P7 — SSH + TUI + prompt (3, FR-015 candidates)**
- `src/operations/execution/ssh/cli_shell_manager.py`
- `src/interfaces/visualization/ui/tui.py`
- `src/interfaces/visualization/ui/prompt_utils.py`

**P8 — Websocket wildcard (`src/mist/realtime/websocket/*` → 15 files)**

Enumerated at branch cut:

- `src/mist/realtime/websocket/__init__.py`
- `src/mist/realtime/websocket/commands.py`
- `src/mist/realtime/websocket/context.py`
- `src/mist/realtime/websocket/manager.py`
- `src/mist/realtime/websocket/service_ping_discovery.py`
- `src/mist/realtime/websocket/service_ping_manager.py`
- `src/mist/realtime/websocket/diagnostics/__init__.py`
- `src/mist/realtime/websocket/diagnostics/arp_executor.py`
- `src/mist/realtime/websocket/diagnostics/common.py`
- `src/mist/realtime/websocket/diagnostics/ping_executor.py`
- `src/mist/realtime/websocket/polling/__init__.py`
- `src/mist/realtime/websocket/polling/completion_detector.py`
- `src/mist/realtime/websocket/polling/message_router.py`
- `src/mist/realtime/websocket/polling/result_collector.py`
- `src/mist/realtime/websocket/polling/result_combiner.py`

Split across PR-8a (toplevel), PR-8b (diagnostics), PR-8c (polling).

## 2. Per-cluster mocking decisions

Per plan.md Decision 5 risk register and Technical Context.

| Cluster | Primary external touchpoint | Mocking library | Rationale |
|---------|---------------------------|-----------------|-----------|
| P1 utilities | `os.environ`, stdin, filesystem | `monkeypatch` + `tmp_path` | pytest built-ins are sufficient; no third-party deps. |
| P2 export helpers | filesystem (JSON/CSV write) | `tmp_path` + `unittest.mock` for `mistapi` | Golden-file comparison in-memory buffer inspection. |
| P3 API/DB/analytics | `mistapi.APISession`, `python-arango`, `redis` | `MagicMock(spec=mistapi.APISession)`, `MagicMock(spec=arango.database.StandardDatabase)`, `fakeredis` or `MagicMock(spec=redis.Redis)` | Spec-bound mocks catch typos; no live network. `database_schema_utils` is a pure string builder — no DB fixture. |
| P4 org exporters | `mistapi` + filesystem | `MagicMock(spec=mistapi.APISession)` + `tmp_path` | Shared fixture `mock_mistapi_session` in `tests/unit/export/conftest.py` (introduced PR-4a). |
| P5 site exporters + reports | `mistapi` + filesystem | Same as P4 — reuses PR-4a fixtures | Column-order + header + one-row-of-data assertions. |
| P6 state-changing managers | `mistapi` + `safe_input()` prompts | `MagicMock(spec=mistapi.APISession)` + `monkeypatch.setattr("...safe_input", lambda *_: "UPGRADE")` | Both accept AND reject paths tested (Principle III). |
| P7 SSH / TUI | `paramiko.SSHClient`, `sshkeyboard.listen_keyboard` | `MagicMock(spec=paramiko.SSHClient)`, `monkeypatch.setattr("sshkeyboard.listen_keyboard", fake)` | Interactive prompts via `monkeypatch` on `safe_input()`. |
| P8 websocket | `websocket.WebSocketApp` (sync `websocket-client` + threading), injected `utility` deps | `MagicMock(spec=websocket.WebSocketApp)`; for `service_ping_*` mock injected utility deps | Project uses **synchronous** `websocket-client`, NOT `websockets` (async). Assert loop exits after ≤ 2 mocked iterations. |

**No `sqlite3` fixture** — `src/foundation/persistence/db/database_schema_utils.py` is a pure DDL string builder (verified: only imports `inspect`, `logging`, `re`, `datetime`, `typing`).

## 3. Fixture-migration order

Fixtures introduced in early PRs are reused by later PRs. Placement is deliberate.

| Fixture | Introduced in | Location | Consumers |
|---------|--------------|----------|-----------|
| `mock_mistapi_session` | PR-3 | `tests/conftest.py` (repo-wide) | PR-3, PR-4a, PR-4b, PR-5a, PR-5b, PR-6 |
| `mock_config` | PR-3 | `tests/conftest.py` | PR-3, PR-4a-b, PR-5a-b, PR-6 |
| `mock_mistapi_paginated_response` | PR-3 | `tests/unit/api/conftest.py` | PR-3, PR-4a-b, PR-5a-b |
| Golden-file writer helpers | PR-4a | `tests/unit/export/conftest.py` | PR-4a, PR-4b, PR-5a, PR-5b |
| `mock_paramiko_ssh_client` | PR-7 | `tests/unit/ssh/conftest.py` | PR-7 |
| `mock_sshkeyboard_listen` | PR-7 | `tests/unit/ui/conftest.py` (extend existing) | PR-7 |
| `mock_websocket_transport` | PR-8a | `tests/unit/websocket/conftest.py` | PR-8a, PR-8b, PR-8c |

## 4. Success criteria references

- SC-001: exactly 6 retained non-source omits after T-Final.
- SC-003: `pytest --cov --cov-fail-under=90` passes.
- SC-006: no new `# pragma: no cover` / `# type: ignore` / `# noqa` in workflow-added tests.
- SC-007: default CI suite makes zero live network calls (verify with `podman run --network=none`).
- SC-010: pylint `fail-under=9.5` unchanged.
- FR-009: `fail_under=90` line unchanged.
- FR-011: retained omit set unchanged.
- FR-015: max 2 modules retain omit + `# TODO(1017): refactor pending` comment.
