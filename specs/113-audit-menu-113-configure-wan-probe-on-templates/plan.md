# Plan: Audit Configure WAN Probe on Templates (Menu 113)

Goal

Audit the bulk-template WAN probe configuration command and produce remediation tasks to ensure safe execution and reporting.

Approach

1. Locate handler and dependencies
2. Static review for idempotency and confirmation prompts
3. Identify reporting endpoints and add DataExporter calls
4. Produce test skeletons and fixtures

Milestones & Deliverables

- discovery.json: mapping of template IDs
- tasks.md: list of small tickets to implement reporting and tests

Risks

- Bulk operations without dry-run can be dangerous; require confirmation.

