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

Device search results use the existing `devices` Arango vertex mapping. The
primary-key catalog already defines the required `["id", "mac"]` composite key.
The implementation keeps that strategy and makes the endpoint available through
the shared export pipeline.

## Menu placement

Menu 235 is already used by organization count operations. Menu 249 is the next
free menu number after the current highest operation, so it avoids collisions.
