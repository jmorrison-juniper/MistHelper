# Spec: Show OSPF Database (Menu 126)

Summary

Audit the "Show OSPF Database" command which returns OSPF LSDB entries. Ensure data normalization, export support, and PK strategy (likely composite: lsa_id + type + device_id).

Scope

- Locate handler and fields returned
- Normalize nested structures (LSA contents) for tabular export
- Add DataExporter usage

Acceptance

- tasks.md with normalization and exporter tasks

Target path

specs/126-audit-menu-126-show-ospf-database/

Menu metadata

- menu_id: 126
- display_text: "Show OSPF Database"
- function_ref: ospf_tools.py::show_ospf_database
- sql_export_relevant: true

Notes

- LSDB entries are nested; require flattening.

