# Spec: Show OSPF Summary (Menu 127)

Summary

Audit the "Show OSPF Summary" command which provides aggregated OSPF status across devices or the site. Ensure the summary is consistent and exportable.

Scope

- Locate handler and ensure metrics and totals are well-defined
- Add exporter hooks if missing

Acceptance

- tasks.md with exporter and tests

Target path

specs/127-audit-menu-127-show-ospf-summary/

Menu metadata

- menu_id: 127
- display_text: "Show OSPF Summary"
- function_ref: ospf_tools.py::show_ospf_summary
- sql_export_relevant: true

Notes

- Provide clear columns for CSV exports (e.g., device_id, total_neighbors, bdr_count).

