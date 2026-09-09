# Implementation Plan: searchSiteNacClients

**Branch**: `feat/1400-search-site-nac-clients`  
**Issue**: #1400  
**Spec**: [spec.md](./spec.md)

## Summary

Add menu 249 for the read-only `searchSiteNacClients` site search. Reuse
`SiteSearchExporter._run_site_search` for site selection, pagination,
flattening, logging, and multi-backend export. The existing composite primary
key and Arango mapping already cover this operation.

## Files

- `src/export/site_search_exporter.py`: Add the endpoint binding and label.
- `MistHelper.py`: Register menu 248.
- `src/utils/operation_registry.py`: Classify menu 248 as `interactive_safe`.
- `tests/unit/export/test_site_search_exporter.py`: Test the endpoint binding.
- `README.md`: Update the operation count and menu description.
- `CHANGELOG.md`: Record the new menu operation.
- `documentation/menu_reference.md`: Regenerate the menu reference.
- `documentation/menu-highlights.md`: Regenerate the menu highlights.

## Design Decisions

1. Use `SiteSearchExporter` because this endpoint matches the existing
   site-scoped search flow.
2. Use menu 249 because menu 248 is claimed by an active PR for issue #1372.
3. Use the existing `searchSiteNacClients` composite key of `mac` and
   `timestamp`.
4. Call the installed SDK path
   `mistapi.api.v1.sites.nac_clients.searchSiteNacClients`.

## Validation

Run the focused exporter tests, syntax checks, Ruff, and Black. Run the menu
registry tests that cover the new operation classification.
