# Implementation Plan: searchSiteDiscoveredSwitches

**Branch**: `feat/1395-search-site-discovered-switches`  
**Spec**: `specs/887-mist-search-site-discovered-switches/spec.md`

## Summary

Use the existing site-scoped search exporter for menu 228. The exporter resolves
one site, calls the Mist SDK once, pages through the response, flattens rows,
and writes through `DataExporter`.

## Existing implementation

- `MistHelper.py` registers menu 228.
- `src/export/site_search_exporter.py` calls
  `mistapi.api.v1.sites.stats.searchSiteDiscoveredSwitches`.
- `src/refactors/endpoint_primary_key_strategies.py` uses the composite key
  `system_name`, `mgmt_addr`, and `timestamp`.
- The API and menu reference pages already document the endpoint.

## Scope

This delivery completes the Spec 887 evidence without changing neighboring
endpoint behavior.

1. Add the missing SpecKit plan, research, tasks, and quickstart artifacts.
2. Add a focused unit test for the menu 228 call and persistence contract.
3. Correct the existing changelog issue reference from #1396 to #1395.
4. Run targeted and required local quality checks.

## Design decisions

- Reuse `SiteSearchExporter._run_site_search` because the endpoint has the same
  session, site, pagination, and persistence shape as adjacent site searches.
- Keep the SDK callable at `mistapi.api.v1.sites.stats.searchSiteDiscoveredSwitches`.
  The installed SDK exposes this callable from the `stats` module.
- Keep the composite primary key because discovered switch rows are time-series
  records and do not expose one stable identifier.
- Do not add live API tests. Unit tests mock the SDK and the output backend.

## Verification

Run the focused exporter tests, then run syntax, lint, format, and type checks
required by the repository before commit.
