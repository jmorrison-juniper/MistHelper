# Tasks: Org-Level AP Firmware Upgrade (Menu 116)

1. Discovery task
- id: audit-116-discovery
- description: Locate upgrade handler, understand parameters (who initiates, target filters)

2. Safety task
- id: audit-116-dryrun
- description: Ensure upgrades default to dry-run and require confirmation to proceed

3. Reporting task
- id: audit-116-reporting
- description: Add DataExporter.write_with_format_selection to log per-device upgrade results

4. Tests task
- id: audit-116-tests
- description: Add pytest tests mocking firmware upgrade APIs and verifying exporter outputs

Estimated effort: 2 days.

