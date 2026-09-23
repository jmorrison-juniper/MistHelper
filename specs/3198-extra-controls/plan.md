# Implementation Plan: Remove stale portal controls

## Root Cause
`web_portal/services/operation.py` declared site, device, and service ping controls for handlers that use only organization context. Menu 87 reaches one site prompt, not the old gateway ping prompt set. Menu 88 reaches one raw AP model selection prompt.

## Design
- Remove parameter registry entries for organization-wide rows that do not prompt.
- Change menu 87 to a single site parameter.
- Change menu 88 to one required AP model number parameter.
- Move menus 66 and 68 to the static-audit undercount list, because their prompt is injected through `SiteExportUtils._export_data`.
- Extend `tests/unit/web_portal/test_portal_required_controls.py` to lock each repaired row.

## Risks
Menu 88 cannot build a model pick list before the handler fetches inventory. The field therefore states that SSH shows the model table.
