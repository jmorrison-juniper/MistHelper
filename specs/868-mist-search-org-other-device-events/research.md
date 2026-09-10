# Research: searchOrgOtherDeviceEvents

## Findings

- The installed SDK exposes `mistapi.api.v1.orgs.otherdevices.searchOrgOtherDeviceEvents`.
- `OrgExportUtils.export_data` supplies organization input, pagination, retries, and output.
- The endpoint returns event records.
- The event key uses `id`, `mac`, and `timestamp`.
- Menu 252 contains the merged operation.

## Decision

Use `OrgExportUtils` for this organization export.
Use the shared data exporter for all output backends.
Keep the operation in the `safe` registry category.
