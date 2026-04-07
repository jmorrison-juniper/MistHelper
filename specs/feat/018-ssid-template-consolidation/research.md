# Research Notes — SSID Template Consolidation

- Mist API endpoints of interest: `listOrgWlans`, `listOrgTemplates`, `listSiteDevices`, `updateSite`, `createSiteGroup`, `updateWlanTemplate`.
- Rate limiting strategy: examine `MistHelper.py` existing `request_with_retries()` wrapper and reuse its retry/backoff configuration.
- Template naming: prefer `MIST_TEMPLATE_BASENAME` env var; fallback `MIST_TARGET_SSID`.
- Data export: reuse `DataExporter.write_with_format_selection()` helpers already used elsewhere in MistHelper.
- Edge cases when a template references multiple Mist Edge clusters: treat as anomaly in Phase 1 and skip automatic modifications.
