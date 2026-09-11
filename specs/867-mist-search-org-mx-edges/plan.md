# Implementation Plan: searchOrgMxEdges

## Scope

Add the read-only `searchOrgMxEdges` operation to MistHelper.
Keep the existing export backends and pagination behavior.

## Design

1. Add `OrgSearchExporter.mx_edges` for menu 253.
2. Collect optional filters through `InputUtils.safe_input`.
3. Call the installed `searchOrgMxEdges` SDK operation.
4. Export all result pages through the shared data exporter.
5. Use the existing composite primary key strategy.

## Files

- `MistHelper.py` registers menu 253.
- `src/export/org_search_exporter.py` implements the operation.
- `src/utils/operation_registry.py` marks the menu as safe.
- `src/refactors/endpoint_primary_key_strategies.py` defines the key strategy.
- `tests/unit/export/test_org_search_exporter.py` verifies the operation.

## Validation

- Run the focused organization search tests.
- Run the Python compile check.
- Run Ruff and Black checks.
- Generate the menu reference and confirm that it has no difference.
