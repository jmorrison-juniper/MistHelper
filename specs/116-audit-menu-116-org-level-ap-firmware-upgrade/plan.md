# Plan: Audit Org-Level AP Firmware Upgrade (Menu 116)

Goal

Ensure safe, tested firmware upgrade flows with reporting.

Approach

1. Locate code and understand batch/concurrency handling
2. Confirm retry and backoff policies
3. Add DataExporter reporting for per-device statuses
4. Create tests that mock firmware upgrade flows and capture exporter outputs

Deliverables

- tasks.md with actionable tickets and estimated effort

