# Spec: Show OSPF Interfaces (Menu 125)

Summary

Audit the "Show OSPF Interfaces" command to ensure consistent interface-level OSPF data, including interface name, area, state, and metrics. Ensure exporter support and primary key strategy.

Scope

- Find handler and verify fields returned
- Ensure DataExporter usage and define PK strategy (device_id + interface)

Acceptance criteria

- tasks.md with exporter and tests

Target path

specs/125-audit-menu-125-show-ospf-interfaces/

Menu metadata

- menu_id: 125
- display_text: "Show OSPF Interfaces"
- function_ref: ospf_tools.py::show_ospf_interfaces
- sql_export_relevant: true

Notes

- Interface names may vary by platform; include 'device_id' in PK.

