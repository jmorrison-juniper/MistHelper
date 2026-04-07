# Spec: Configure WAN Probe on Templates (Menu 113)

Summary

This spec audits the handler that applies WAN probe settings to templates (menu id 113). The operation typically updates template configurations in bulk and may touch template IDs, probe intervals, and probe targets.

Scope

- Locate the handler in the repo (likely MistHelper.py and/or a templates manager module).
- Verify input validation, idempotency, dry-run options, and DataExporter integration for reporting which templates were modified.
- Ensure appropriate primary key strategy exists if the operation exports a list of modified templates.

Out of scope

- Making live API changes to templates.

Acceptance criteria

- Mapping of CLI options to source functions and file locations.
- Plan and tasks to add tests and DataExporter usage for reporting changes.

Target path

specs/113-audit-menu-113-configure-wan-probe-on-templates/

Menu metadata

- menu_id: 113
- display_text: "Configure WAN Probe on Templates"
- function_ref: templates_manager.py::configure_wan_probe_on_templates
- sql_export_relevant: true

Checklist

- [ ] Locate handler and confirm behavior
- [ ] Ensure dry-run and confirmation prompts
- [ ] Verify DataExporter usage or add it
- [ ] Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry if reporting supported

Notes

- Ensure safety: bulk template modifications should default to dry-run with explicit confirmation to avoid accidental changes.

