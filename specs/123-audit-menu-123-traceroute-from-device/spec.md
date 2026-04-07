# Spec: Traceroute from device (Menu 123)

Summary

Audit the traceroute-from-device command that runs traceroute from a network device to a destination. Verify parameter validation, timeout handling, and result exports.

Scope

- Locate handler and ensure proper input validation (IP or hostname)
- Verify timeout and max-hops defaults
- Ensure results are exportable via DataExporter and include primary key strategy

Acceptance

- tasks.md with discovery and reporting tasks

Target path

specs/123-audit-menu-123-traceroute-from-device/

Menu metadata

- menu_id: 123
- display_text: "Traceroute from device"
- function_ref: network_tools.py::traceroute_from_device
- sql_export_relevant: true

Notes

- Traceroute results are time-series per probe; consider composite PK for timestamped entries.

