# Spec: Org-Level AP Firmware Upgrade (Menu 116)

Summary

Audit the organization-level AP firmware upgrade command. Verify filter options, device selection logic, dry-run, error handling, retry/backoff strategies, and reporting via DataExporter.

Scope

- Find the upgrade handler (likely in firmware management module or MistHelper.py).
- Confirm it supports batching, concurrency limits, and proper retry semantics.
- Ensure DataExporter is used to report upgrade status per device.

Acceptance criteria

- Plan and tasks to add missing DataExporter calls and tests.
- ENDPOINT_PRIMARY_KEY_STRATEGIES entries for any exported upgrade status data.

Target path

specs/116-audit-menu-116-org-level-ap-firmware-upgrade/

Menu metadata

- menu_id: 116
- display_text: "Org-Level AP Firmware Upgrade"
- function_ref: firmware_manager.py::org_level_ap_upgrade
- sql_export_relevant: true

Checklist

- [ ] Confirm concurrency and rate-limit handling
- [ ] Dry-run and confirm prompts
- [ ] Add DataExporter reporting if missing

Notes

- Firmware upgrades involve stateful device changes; emphasize safe defaults (dry-run) and idempotency.

