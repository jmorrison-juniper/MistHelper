# Migration Tracker — Legacy Compat Shim Decomposition

## Symbol Inventory Status

| ID | File | Symbol | Decision | Status | Notes |
| - | - | - | - | - | - |
| S001 | `MistHelper.py` | `get_csv_file_path_legacy` | remove | ✅ done | Removed in US1 chunk A |
| S002 | `MistHelper.py` | `export_gateway_templates_to_csv_legacy` | remove | ✅ done | Removed in US1 chunk A |
| S003 | `MistHelper.py` | `export_const_insight_metrics_to_csv` legacy bridge behavior | replace behavior | 🔄 in-progress | Canonical cache refresh introduced in `SiteInsightsExporter.refresh_insight_metrics_cache()` |
| S004 | `src/export/site_insights/site_metric_operation.py` | `InsightMetricsUtils.export_legacy()` callsite | replace callsite | ✅ done | Replaced with canonical cache refresh API |
| S005 | `src/export/site_insights/device_metric_operation.py` | `InsightMetricsUtils.export_legacy()` callsite | replace callsite | ✅ done | Replaced with canonical cache refresh API |
| S006 | `src/capture/site_pcap_wait_download_workflow.py` | `run()` alias | temporary adapter | ✅ active | Expiry 2026-08-31 noted in docstring |
| S007 | `src/capture/org_pcap_wait_download_workflow.py` | `run()` alias | temporary adapter | ✅ active | Expiry 2026-08-31 noted in docstring |
| S008 | `__init__.py` | facade/shim branches | retire/replace | ⏳ pending | Scheduled US1 chunk B/C |
| S009 | `__init__.py` | `_noop_menu_action` fallback | temporary adapter | ⏳ pending | Scheduled with parity guard rollout |
| S010 | `__init__.py` | `_ensure_menu_coverage` fallback | temporary adapter | ⏳ pending | Scheduled with parity guard rollout |
| S011 | `src/capture/__init__.py` | lazy `PacketCaptureManager` facade | replace export map | ⏳ pending | Scheduled US1 chunk C |
| S012 | `tests/unit/test_no_export_legacy_callsites.py` | internal `export_legacy` guard | hardening test | ✅ done | Prevents legacy callsite reintroduction |
| S013 | `tests/unit/test_no_new_legacy_facade_imports.py` | test-time legacy facade growth guard | hardening test | ✅ done | Prevents new test migration debt |

## Task Mapping Snapshot

- Completed: T013 (partial scope), T015, T016, T017, T041, T042, T007, T047 (partial), T061 (partial), T063
- In progress: T014, T018-T040, T056-T060
- Pending: remaining US2/US3 gates and full facade retirement

## Current blocker snapshot

- Full US1 chunk B/C `__init__.py` shim-branch retirement is blocked by active runtime/test dependencies on facade symbols (`SiteExportUtils`, `InsightMetricsUtils`, `TimeUtils`, `OperationRegistry`, and `OrgExportUtils`) where canonical replacements are not fully decoupled yet.
- Approach: continue US3 migration of test/runtime callsites to canonical module paths, then retire branches in smaller verified batches.
