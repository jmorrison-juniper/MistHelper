# Spec: Maps Manager sub-menu (Menu 112)

Summary

This spec audits the Maps Manager sub-menu in MistHelper (menu id 112). The Maps Manager functions typically manage site maps, floor plans, and zone overlays. The goal is to verify each sub-command for correctness, error handling, presence of unit/integration tests, and SQL/CSV export support via the project's DataExporter abstraction.

Scope

- Review the Maps Manager sub-menu handler code path within MistHelper.py and supporting modules (e.g., maps_manager.py).
- Check for: input validation, pagination handling, API error handling, consistent use of DataExporter.write_with_format_selection, and definitions in ENDPOINT_PRIMARY_KEY_STRATEGIES if the operation exports data.
- Produce a plan and tasks to remediate missing tests or missing DataExporter integration.

Out of scope

- Executing live Mist API calls.
- Implementing code changes; this spec only requests remediation tasks and tests.

Acceptance criteria

- A clear mapping of menu commands to source functions and files.
- A plan describing remediation actions to add tests and DataExporter support.
- Tasks to create/augment unit tests and add ENDPOINT_PRIMARY_KEY_STRATEGIES entries for any endpoints that produce tabular output.
- All artifacts saved to specs/112-audit-menu-112-maps-manager-sub-menu/ and recorded in menu_audit table.

Target path

specs/112-audit-menu-112-maps-manager-sub-menu/

Menu metadata

- menu_id: 112
- display_text: "Maps Manager" (sub-menu)
- function_ref: maps_manager.py::MapsManager (or similar)
- sql_export_relevant: true (likely; many map lists are exportable)

Checklist

- [ ] Locate handler(s) in MistHelper.py and maps_manager.py
- [ ] Identify all sub-commands and their API calls
- [ ] Verify DataExporter usage, or mark missing
- [ ] Verify tests exist; if missing, produce test plan and tasks
- [ ] Produce ENDPOINT_PRIMARY_KEY_STRATEGIES entries for each exportable endpoint

Notes / Observations

- maps_manager.py exists in the repo root and contains helpers for floorplan and map management. Some functions currently return JSON that should be flattened before CSV/SQL export.
- Look for patterns in other modules (e.g., site_analytics) where DataExporter is used as a model to follow.

