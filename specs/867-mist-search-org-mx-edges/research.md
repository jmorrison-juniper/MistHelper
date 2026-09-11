# Research: searchOrgMxEdges

## Findings

- The installed SDK exposes `mistapi.api.v1.orgs.mxedges.searchOrgMxEdges`.
- The operation accepts organization scope and optional search filters.
- `OrgSearchExporter` provides the shared pagination and export path.
- The endpoint uses a composite primary key strategy.
- Menu 253 contains the merged operation.

## Decision

Use `OrgSearchExporter` for this organization search.
Use the shared data exporter for all output backends.
Keep the operation in the `safe` registry category.
