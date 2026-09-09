# Research: searchOrgOtherDeviceEvents

## Findings

- The installed `mistapi` package exposes the operation as
  `mistapi.api.v1.orgs.otherdevices.searchOrgOtherDeviceEvents`.
- `OrgExportUtils.export_data` provides organization input, pagination, retries,
  and multi-backend output.
- The endpoint returns event rows. The existing strategy uses the composite key
  `id`, `mac`, and `timestamp`.

## Decision

Add one `OrgExportUtils` entry point and one menu binding. Reuse the shared
export pipeline. Keep the operation in the `safe` registry category.
