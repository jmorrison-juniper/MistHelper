# Spec: Site Analytics Configuration (Menu 120)

Summary

Audit the Site Analytics Configuration menu which manages SLEs, insight metrics, and analytics reporting. Ensure that configuration exports and reporting use DataExporter and that any exportable metrics have ENDPOINT_PRIMARY_KEY_STRATEGIES defined.

Scope

- Locate the configuration handler and related modules.
- Verify proper validation, default settings, and export hooks.
- Ensure tests exist or create tasks for test creation.

Acceptance criteria

- tasks.md with remediation steps and sample test skeletons
- ENDPOINT_PRIMARY_KEY_STRATEGIES entries for exported analytics data

Target path

specs/120-audit-menu-120-site-analytics-configuration/

Menu metadata

- menu_id: 120
- display_text: "Site Analytics Configuration"
- function_ref: analytics_manager.py::site_analytics_configuration
- sql_export_relevant: true

Notes

- Analytics data may be time-series; ensure composite primary keys are used per project policy.

