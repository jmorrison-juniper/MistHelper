# Spec: Show Sessions on SSR/SRX (Menu 128)

Summary

Audit the command to show sessions on SSR/SRX devices. Ensure that results are paginated (if large), include necessary fields (src,dst,proto,bytes), and are exportable.

Scope

- Find the handler and verify filters (e.g., by IP, time range)
- Ensure sensitive data is handled appropriately
- Confirm DataExporter usage and PK strategy for session records

Acceptance

- tasks.md with discovery, exporter, and test tasks

Target path

specs/128-audit-menu-128-show-sessions-on-ssr-srx/

Menu metadata

- menu_id: 128
- display_text: "Show Sessions on SSR/SRX"
- function_ref: session_tools.py::show_sessions_on_ssr_srx
- sql_export_relevant: true

Notes

- Session lists can be large; prefer streaming/export-by-chunk to avoid memory spikes.

