# Requirements Checklist — spec-025

| ID | Requirement | Status |
| - | - | - |
| FR-001 | APIDataFetcher receives correct params (api_call, filename, sort_key, type, duration, limit) | [ ] |
| FR-002 | Dual output (CSV + SQLite) via DataExporter.write_with_format_selection | [ ] |
| FR-003 | SQLite upsert idempotency (composite PK on device_id, timestamp) | [ ] |
| FR-004 | Indexes created for query performance on device_id, timestamp, org_id, site_id, type | [ ] |
| FR-005 | Progress emitter lifecycle (emit_progress_start + emit_progress_complete with menu_id="13") | [ ] |
| FR-006 | Fast mode cache-hit skips API call when CSV fresh | [ ] |
| FR-007 | Dynamic lookback hours from TimeUtils used in duration param | [ ] |
| US-001 | NOC engineer exports device stats (all device types) | [ ] |
| US-002 | Repeated export doesn't create duplicates (upsert idempotency) | [ ] |
| US-003 | CSV schema is stable with expected column headers | [ ] |
| US-004 | Progress tracking emits start/complete for web UI | [ ] |
| US-005 | Fast mode cache-hit/miss behavior correct | [ ] |
| US-006 | Dynamic lookback value passed to API duration param | [ ] |
