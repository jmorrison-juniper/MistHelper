# Implementation Plan: searchOrgSites

## Scope

Add the read-only `searchOrgSites` endpoint as menu 248.

## Design

1. Extend `OrgSearchExporter` with a site-search entry point.
2. Call the installed SDK surface `mistapi.api.v1.orgs.sites.searchOrgSites`.
3. Reuse the existing organization search pagination and export path.
4. Register `searchOrgSites` with a natural `id` primary key.
5. Register menu 248 as a safe read-only operation.
6. Update the menu reference, README, and changelog.
7. Add unit coverage for endpoint binding, pagination, export, empty data, and errors.

## Validation

Run the focused exporter and primary-key tests, then run the required compile,
Ruff, and Black checks for changed Python files.
