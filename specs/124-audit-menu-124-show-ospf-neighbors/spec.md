# Spec: Show OSPF Neighbors (Menu 124)

Summary

Audit the "Show OSPF Neighbors" command which retrieves OSPF neighbor information from devices or from aggregated state. Ensure data shape is consistent, pagination is handled, and results support export.

Scope

- Find the handler and whether it queries devices directly or reads consolidated state
- Verify fields included (neighbor ID, addr, state, uptime)
- Ensure DataExporter usage and primary key strategy (composite with device_id + neighbor_id)

Acceptance criteria

- tasks.md with mapping, exporter, and test tasks

Target path

specs/124-audit-menu-124-show-ospf-neighbors/

Menu metadata

- menu_id: 124
- display_text: "Show OSPF Neighbors"
- function_ref: ospf_tools.py::show_ospf_neighbors
- sql_export_relevant: true

Notes

- OSPF neighbor lists are natural candidates for CSV exports; ensure index fields are defined.

