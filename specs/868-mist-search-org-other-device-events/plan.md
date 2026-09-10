# Implementation Plan: searchOrgOtherDeviceEvents

## Scope

Add the read-only `searchOrgOtherDeviceEvents` operation to MistHelper.
Keep the existing export backends and retry behavior.

## Design

1. Add `OrgExportUtils.other_device_events` for menu 252.
2. Reuse the organization selection and input handling.
3. Call the installed `searchOrgOtherDeviceEvents` SDK operation.
4. Export all result pages through the shared data exporter.
5. Use the existing event composite primary key strategy.

## Files

- `MistHelper.py` registers menu 252.
- `src/export/org_export_utils.py` implements the operation.
- `src/utils/operation_registry.py` marks the menu as safe.
- `src/refactors/endpoint_primary_key_strategies.py` defines the key strategy.
- `tests/unit/export/test_org_export_utils.py` verifies the operation.

## Validation

- Run the focused organization export tests.
- Run the Python compile check.
- Run Ruff and Black checks.
- Generate the menu reference and confirm that it has no difference.
