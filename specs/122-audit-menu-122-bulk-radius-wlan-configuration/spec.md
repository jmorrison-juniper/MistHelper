# Spec: Bulk RADIUS WLAN Configuration (Menu 122)

Summary

Audit the bulk RADIUS WLAN configuration flow which likely configures RADIUS settings across multiple WLANs. Focus on safe updates, dry-run, and reporting which WLANs were updated.

Scope

- Locate handler and verify input validation and idempotency.
- Confirm DataExporter usage for reporting results.

Acceptance criteria

- tasks.md with remediation steps

Target path

specs/122-audit-menu-122-bulk-radius-wlan-configuration/

Menu metadata

- menu_id: 122
- display_text: "Bulk RADIUS WLAN Configuration"
- function_ref: wlan_manager.py::bulk_radius_config
- sql_export_relevant: true

Notes

- Changes to WLAN security settings are impactful; enforce dry-run and confirmation flows.

