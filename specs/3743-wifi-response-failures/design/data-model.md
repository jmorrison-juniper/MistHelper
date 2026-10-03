# Data Model: WiFi response failures

No stored schema or primary-key strategy changes.

## Response Page

The native page supplies `status_code`, `data`, `raw_data`, and `next`.
Status acceptance precedes body acceptance.
A complete page contains a list of objects or an object with a `results` list.

A failed page ends the export before final output.
Previously accepted pages do not become a partial export.
The accepted record list remains local until both endpoint reads succeed.

## Site Stamp

The existing site stamp carries `site_id` and `site_name`.
The repair does not change lookup, fallback, scope, or record stamping.

## Merged Record

The existing merge joins client and session records by MAC.
It selects the latest matching session and retains the existing session count.
Session-only rows retain their existing prefix and site information.
The repair changes no merge field or record order.
