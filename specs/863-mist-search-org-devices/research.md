# Research: searchOrgDevices

## SDK surface

The installed SDK exposes the endpoint as
`mistapi.api.v1.orgs.devices.searchOrgDevices`. It accepts the active session
and the organization ID, then returns a paginated response.

## Existing implementation pattern

`src/export/org_search_exporter.py` already owns organization search endpoints.
Its `_run_org_search` helper resolves the organization, calls the SDK, uses
`mistapi.get_all`, and persists flattened rows through `DataExporter`.

## Storage strategy

The existing primary-key catalog defines `searchOrgDevices` with the composite
key `["id", "mac"]` and indexes for organization, site, model, type, and host.
No storage change is required.

## Menu placement

Menu 235 is used by organization count operations. Menu 249 is the next free
menu number after the current highest operation.
