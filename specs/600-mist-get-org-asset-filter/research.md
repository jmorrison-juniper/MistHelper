# Phase 0 Research: getOrgAssetFilter

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-06-29

This document captures the Phase 0 research decisions that ground the implementation
plan. Every section uses the Decision / Rationale / Alternatives Considered format
required by the constitution.

## Research Task 1: SDK function signature and behavior

**Decision**: Call the SDK via
`mistapi.api.v1.orgs.asset_filters.getOrgAssetFilter(apisession, org_id,
assetfilter_id)`. Treat the response as a single JSON object (not a list) and pass it
to `DataExporter.write_with_format_selection()` wrapped in a one-element list so the
exporter's row-iteration contract is preserved.

**Rationale**: The enriched per-endpoint doc
`documentation/api/orgs/GET_orgs_org_id_assetfilters_assetfilter_id.md` states that the
HTTP path is `GET /api/v1/orgs/{org_id}/assetfilters/{assetfilter_id}`, the response is
an object (not an array) with a `"required": ["name"]` constraint, and the SDK path is
`mistapi.api.v1.orgs.asset_filters.getOrgAssetFilter()`. Both path parameters are
mandatory strings. The endpoint is not paginated, so no pagination loop is needed.
Authentication uses the existing `mistapi.APISession` already loaded from `.env`. The
SDK returns a `mistapi.APIResponse`-shaped object whose `.data` attribute is the parsed
JSON; we read `.data` (or `.json()` -- both are supported by mistapi 0.59+) defensively
and fall back to an empty dict if the SDK returns `None` on a 404.

**Alternatives Considered**:
1. *Use `requests` directly with the bearer token from `.env`.* Rejected because the
   constitution mandates `mistapi` as the sole permitted Mist interface and the SDK
   already handles rate limiting, retry, and pagination conventions consistently.
2. *Treat the response as a list and iterate.* Rejected because the OpenAPI schema is
   an `object`, not an `array`. Iterating would silently shred the dict into one row
   per key.
3. *Combine this with the list endpoint `getOrgAssetFilters`.* Rejected because the
   spec scopes this feature to the single-object GET; the list endpoint is a separate
   operation and a separate spec/PR.

## Research Task 2: Primary Key Strategy

**Decision**: `natural_pk` with `primary_key = ['id']` and secondary `indexes =
['org_id', 'name']`.

**Rationale**: The response schema declares `id` as a `readOnly` UUID assigned by the
Mist control plane. The same UUID is returned on every GET against the same filter,
making it a stable natural primary key. `org_id` is included as a non-unique index so
that the same SQLite table can hold filters from multiple organizations (each org's
filters are scoped under its UUID), and `name` is indexed so engineers can run ad hoc
queries like "show me filters named Visitor Tags across all orgs". This matches the
pattern documented in `.github/copilot-instructions.md` under "Database Strategy ->
Hybrid Primary Key System -> Natural PK".

**Alternatives Considered**:
1. *Composite PK on `('id', 'org_id')`.* Rejected because `id` alone is globally
   unique within Mist; adding `org_id` to the PK adds no uniqueness guarantee and
   complicates upserts.
2. *Auto-increment with unique constraint on `id`.* Rejected because a real natural
   key exists; introducing a synthetic key would violate the "prefer natural business
   keys" guidance in the project instructions.
3. *Composite time-series PK like the events endpoints.* Rejected because this object
   is configuration, not time-series; there is no `timestamp` field in the response
   schema.

## Research Task 3: Output filename and SQLite table

**Decision**:
- CSV / JSON output filename: `org_asset_filter.csv` (singular -- one filter per call).
- SQLite table: `org_asset_filter`.
- The DataExporter call is
  `DataExporter.write_with_format_selection([record], "org_asset_filter",
  api_function_name="getOrgAssetFilter")`.

**Rationale**: The MistHelper convention (visible across existing menu items) is
`snake_case` filenames that mirror the response entity name; singular nouns are used
when the endpoint returns a single object, plural when it returns a list. The
`api_function_name` argument lets `DataExporter` look up the PK strategy registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`. Keeping the CSV and SQLite table name identical
avoids a mental-mapping step for the NOC engineer auditing exports.

**Alternatives Considered**:
1. *Plural `org_asset_filters.csv`.* Rejected -- collides semantically with the future
   list endpoint and misleads the operator into thinking multiple rows are expected.
2. *Per-org-prefixed filename like `org_<id>_asset_filter.csv`.* Rejected because
   `DataExporter` already partitions by org internally for the SQLite backend (via the
   `org_id` column), and CSV / JSON consumers prefer one stable filename per endpoint.

## Research Task 4: Menu category placement and next available menu number

**Decision**: Place the new item at menu number **97** in the existing Safe Org
Exports cluster (currently 1-59 and 60-96 per `.github/copilot-instructions.md`). The
final number is re-verified at task generation time; if 97 is claimed by an in-flight
PR, the next free integer in the same cluster is used. The menu label will be
`Get Org Asset Filter (BLE) details by ID`.

**Rationale**: The instructions categorise menu 1-59 and 60-96 as Safe Org Exports
(read-only) and 97-101 as Resource Intensive. This endpoint is a single non-paginated
GET that returns at most a few KB of JSON -- it is firmly read-only and low-cost, so
the Safe Org Exports cluster is the correct home. Placing it at the boundary slot 97
keeps related org-level retrieval items near each other and makes the operation
discoverable when an engineer scrolls past the org-stats block.

**Alternatives Considered**:
1. *Slot it inside the destructive 154-194 range.* Rejected -- the endpoint is GET
   only; placing it among destructive operations would mislead operators and trigger
   the destructive-confirmation gate unnecessarily.
2. *Slot it inside the WebSocket cluster 102-123.* Rejected -- this is a REST call,
   not a WebSocket subscription.
3. *Append to the end (e.g. 195+).* Rejected -- there is room inside the Safe Org
   Exports cluster, and clustering by safety profile is the documented convention.

## Research Task 5: Required user prompts

**Decision**: Two prompts via `safe_input()`:
1. `safe_input("Organization ID (UUID): ", context="org_asset_filter:org_id")`
2. `safe_input("Asset Filter ID (UUID): ",
   context="org_asset_filter:assetfilter_id")`

The `org_id` is also offered as an `.env`-defaulted value: if `MIST_ORG_ID` is set in
the environment, the prompt displays it as the default and pressing Enter accepts it.
`MIST_API_TOKEN` and `MIST_HOST` come from `.env` via the existing `mistapi.APISession`
construction; they are never prompted for and never logged.

**Rationale**: The OpenAPI doc lists exactly two required path parameters (`org_id`
and `assetfilter_id`) and zero query parameters. Both are UUIDs. There is no
discoverable list inside this endpoint, so prompting for the asset-filter UUID is
unavoidable; engineers obtain it from the related list endpoint
`getOrgAssetFilters` or from the Mist UI. Defaulting `org_id` from `.env` matches the
ergonomic pattern used by every other org-scoped menu item and keeps the SSH
non-interactive flow short.

**Alternatives Considered**:
1. *Auto-discover the asset filter ID by calling the list endpoint first.* Rejected
   for this spec -- it expands scope beyond a single endpoint and would couple two
   API calls under one menu item, complicating PK strategy and inflating the method
   beyond the 25-line ceiling. A future "interactive asset-filter chooser" menu item
   can be scoped separately.
2. *Read `assetfilter_id` from a CSV file.* Rejected -- adds a file-handling
   dependency for a single ID. Operators with bulk needs should use the list
   endpoint.
3. *Skip the `org_id` prompt entirely and require `MIST_ORG_ID` to be set.*
   Rejected -- forces an environment edit for ad hoc work and breaks the SSH-friendly
   interactive flow.
