# Phase 5 Menu Parity Evidence (Operations 70-86)

Date: 2026-05-26

## Menu Routing Preservation

- Menu IDs `70-86` remain unchanged in `menu_actions`.
- `MistHelper.py` now delegates `SiteExportUtils` behavior to extracted modules while preserving call signatures and operation descriptions.
- Relevant delegated operations preserved for this phase scope:
  - `70`: `ospf_stats`
  - `71`: `mxedge_upgrade_status`
  - `72`: `auto_map_assignment_status`
  - `73`: `insights`
  - `74`: `insight_metrics`
  - `76`: `device_insights`
  - `80`: `site_stats`
  - `81`: `gateway_metrics`
  - `82`: `switches_metrics`
  - `83`: `beacons_stats`
  - `84`: `wxrules_usage`
  - `85`: `assets_stats`
  - `86`: `current_channel_planning`

## Delegation Integrity

- `SiteExportUtils` implementation ownership moved from `MistHelper.py` to `src/export/site_export_utils.py`.
- High-complexity insights branch moved to `src/export/site_insights_exporter.py`.
- `MistHelper.py` remains orchestration-only for affected paths.

## Conclusion

- Menu dispatch keys and user-facing menu descriptions for the Phase 5 scope remain stable.
- Phase 5 extraction preserves menu routing contract for operations `70-86`.
