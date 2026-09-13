# Research: searchOrgInventory

## SDK contract

The installed `mistapi` package exposes
`mistapi.api.v1.orgs.inventory.searchOrgInventory` with the following optional
query parameters: `type`, `mac`, `model`, `name`, `site_id`, `serial`, `master`,
`sku`, `version`, `status`, `text`, `limit`, `sort`, and `search_after`.

The issue text lists `vc_mac` and `master_mac`, but those names are not present
in the installed SDK signature or generated API documentation. The exporter
therefore uses the installed contract so the call cannot fail with unexpected
keyword arguments.

## Existing project patterns

- Organization search exporters resolve the cached organization and use
  `mistapi.get_all` for pagination.
- `DataProcessingUtils.flatten_nested_fields` and
  `DataProcessingUtils.escape_multiline` prepare rows before output.
- `DataExporter.write_with_format_selection` selects CSV, SQLite, or ArangoDB.
- `OperationRegistry` classifies prompt-driven read operations as
  `interactive_safe`.
- `searchOrgInventory` already has a composite `id` plus `mac` primary-key
  strategy in the endpoint catalog.
