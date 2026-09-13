# Research: `searchOrgVars`

## Existing implementation

- `src/org_data_collector.py` already includes `searchOrgVars` in the organization search collection.
- `src/export/org_search_exporter.py` owns the shared organization search export flow.
- `MistHelper.py` registers organization search menus 230 through 234.
- `src/refactors/endpoint_primary_key_strategies.py` already contains a placeholder strategy.

## Reference behavior

- The SDK callable is `mistapi.api.v1.orgs.vars.searchOrgVars`.
- The endpoint requires `org_id` and supports optional variable filters.
- `mistapi.get_all` handles pagination for the response.
- `DataExporter.write_with_format_selection` selects CSV, SQLite, or ArangoDB output.
- `ConfigUtils.get_cached_or_prompted_org_id` uses the EOF-safe input path.

## Design decision

Add organization variable export as menu 250. Reuse `OrgSearchExporter` so the
new operation receives the same pagination, flattening, output, logging, and
error handling as the existing organization search menus.

Use `site_id`, `var`, and `src` as the composite key. These are the stable
fields returned by the endpoint. The previous `name` key is not in the response.
