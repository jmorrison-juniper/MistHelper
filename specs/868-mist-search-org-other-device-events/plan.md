# Implementation Plan: searchOrgOtherDeviceEvents

## Scope

Add organization other-device event search to the MistHelper menu.

## Design

1. Bind the installed Mist API callable in `OrgExportUtils`.
2. Reuse `export_data` for organization input, pagination, retries, and output.
3. Register menu 249 as a safe read-only operation.
4. Verify the existing composite primary-key strategy.
5. Update generated menu documentation, README, and CHANGELOG.

## Validation

Run the focused unit tests, Python compilation, Ruff, and Black checks.
