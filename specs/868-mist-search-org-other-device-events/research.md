# Research: searchOrgOtherDeviceEvents

## Sources

- Local API page:
  `documentation/api/orgs/GET_orgs_org_id_otherdevices_events_search.md`
- Operation ID: `searchOrgOtherDeviceEvents`
- Method: `GET`
- Path: `/api/v1/orgs/{org_id}/otherdevices/events/search`

## Findings

- The installed `mistapi` package exposes the operation through the organization
  other-device API group.
- `OrgExportUtils.export_data` supplies organization selection, pagination,
  retry handling, and output selection.
- The endpoint returns event records. The primary key uses `id`, `mac`, and
  `timestamp`.
- Pull request #2380 preserved the original workflow records but did not merge.
- Pull request #2418 merged the implementation as menu 252.

## Decision

Restore the workflow records as documentation. Do not change the merged
implementation.
