# Research: Search Organization Other-Device Events

## Findings

- The endpoint is `GET /api/v1/orgs/{org_id}/otherdevices/events/search`.
- The installed `mistapi` package exposes the callable at
  `mistapi.api.v1.orgs.otherdevices.searchOrgOtherDeviceEvents`.
- `OrgSearchExporter` already provides the shared organization prompt,
  pagination, flattening, multiline escaping, and `DataExporter` write path.
- The sibling site-scoped endpoint uses a dedicated exporter and the same
  `search...OtherDeviceEvents` operation naming pattern.
- `ENDPOINT_PRIMARY_KEY_STRATEGIES` already defines
  `searchOrgOtherDeviceEvents` as a composite key with `id`, `mac`, and
  `timestamp`.

## Decision

Implement the menu in `OrgSearchExporter` instead of `OrgExportUtils`, because
the issue requires safe prompts for the optional query filters. Register the
menu at 261. Keep the existing primary-key strategy and output filename
`OrgOtherDeviceEvents.csv`.
