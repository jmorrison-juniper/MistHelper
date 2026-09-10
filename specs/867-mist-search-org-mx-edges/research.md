# Research: searchOrgMxEdges

## HTTP contract

- The local endpoint index lists `searchOrgMxEdges` as
  `GET /api/v1/orgs/{org_id}/mxedges/search`.
- The OpenAPI 3.1 snapshot confirms the same path and operationId.
- The saved endpoint page lists one required path parameter, `org_id`, and the
  optional query parameters `mxedge_id`, `site_id`, `mxcluster_id`, `model`,
  `distro`, `tunterm_version`, `stats`, `limit`, `start`, `end`, `duration`,
  `sort`, and `search_after`.

## SDK contract

The fresh worktree virtual environment installs `mistapi 0.63.3`. The verified
callable is:

`mistapi.api.v1.orgs.mxedges.searchOrgMxEdges(mist_session, org_id, hostname=None, mxedge_id=None, mxcluster_id=None, model=None, distro=None, tunterm_version=None, site_id=None, stats=None, limit=None, start=None, end=None, duration=None, sort=None, search_after=None)`

The installed SDK accepts `hostname` in addition to the issue body parameter
list. The current exporter therefore prompts for `hostname` so the local code
matches the real SDK contract.

## Current MistHelper state on main

- `MistHelper.py` already registers menu 253 as
  `OrgSearchExporter.mx_edges`.
- `src/export/org_search_exporter.py` already calls
  `mistapi.api.v1.orgs.mxedges.searchOrgMxEdges`, prompts with
  `InputUtils.safe_input`, paginates with `mistapi.get_all`, and persists
  through `DataExporter.write_with_format_selection`.
- `src/refactors/endpoint_primary_key_strategies.py` already registers
  `searchOrgMxEdges` with the composite primary key `["id", "mac"]`.
- `tests/unit/export/test_org_search_exporter.py` already covers the menu
  binding, the optional filters, the hostname prompt, the empty-filter path,
  and the export call.

## Retry conclusion

This retry does not need a new menu number. The latest `origin/main` already
contains the feature as menu 253 through commit `d5bfe0bf`, which also updated
the README, changelog, and generated menu references. Issue #1375 remained open
because the earlier pull requests closed without merge and did not auto-close
the issue.
