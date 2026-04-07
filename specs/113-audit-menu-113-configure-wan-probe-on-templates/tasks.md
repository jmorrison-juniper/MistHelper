# Tasks: Configure WAN Probe on Templates (Menu 113)

1. Discovery task
- id: audit-113-discovery
- description: Find the handler code and enumerate options and API calls.

2. Safety/task: dry-run & confirmation
- id: audit-113-dry-run
- description: Add explicit dry-run flag and confirmation prompt for bulk modifications.

3. Reporting/task: DataExporter
- id: audit-113-reporting
- description: Add DataExporter.write_with_format_selection to report which templates would be modified and which were modified in non-dry-run.

4. Test skeletons
- id: audit-113-tests
- description: Add pytest skeletons to validate dry-run vs actual run behaviors using fixtures.

Estimated effort: 1-2 days.

