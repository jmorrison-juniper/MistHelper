Plan for auditing Menu Option #25

Steps:
1. Inspect OrgInventoryExporter.combined_inventory_with_site_info implementation in MistHelper.py.
2. Locate corresponding ENTRY in ENDPOINT_PRIMARY_KEY_STRATEGIES and validate primary key strategy.
3. Confirm DataExporter.write_with_format_selection is invoked with api_function_name parameter.
4. Search tests/ for unit/integration tests covering this method; record coverage gaps.
5. Produce tasks.md with recommended fixes and ownership.

Assumptions: repository is authoritative; no runtime required.

Deliverables: spec.md, plan.md, tasks.md, and a short audit summary.
