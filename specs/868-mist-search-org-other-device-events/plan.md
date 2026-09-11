# Implementation Plan: searchOrgOtherDeviceEvents

## Scope

Record the completed `searchOrgOtherDeviceEvents` implementation. The operation
ships on `main` as menu 252 through pull request #2418.

## Design

1. Confirm the endpoint contract from the local OpenAPI source.
2. Confirm the installed `mistapi` SDK callable.
3. Confirm the exporter and menu binding on current `main`.
4. Confirm the composite primary-key strategy for event records.
5. Restore the missing SpecKit workflow records from pull request #2380.

## Validation

- Confirm that menu 252 calls `OrgExportUtils.other_device_events`.
- Confirm that the exporter uses the shared pagination and output path.
- Confirm that the primary key uses `id`, `mac`, and `timestamp`.
- Confirm that this pull request changes documentation only.
