# Phase 0 Research: countOrgInventory

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each task
follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_inventory_count.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the module path that mirrors the OpenAPI
URL: `mistapi.api.v1.orgs.inventory.count.countOrgInventory(apisession, org_id,
distinct=None, type=None, limit=100, page=None)`. The SDK returns a
`mistapi.APIResponse` object whose `.data` attribute is the parsed JSON body. The body
is a single JSON object with the following top-level keys per the doc:

- `distinct` (string -- echoes the grouping field the server used)
- `start` (int32 -- epoch seconds of the result window start)
- `end` (int32 -- epoch seconds of the result window end)
- `limit` (int32 -- bucket cap honored by the server, default 100)
- `total` (int32 -- total number of inventory items considered across all buckets)
- `results` (array of `count_result` objects -- one element per distinct bucket)

Each `count_result` element has:

- `count` (int32 -- required -- number of inventory items in this bucket)
- `additionalProperties` -- one extra string field whose key is the value of the
  `distinct` parameter (e.g. when `distinct=model`, each bucket carries `{model:
  "AP43", count: 12}`).

Required path parameter: `org_id` (UUID string).
Optional query parameters: `type` (string -- inventory type filter such as `ap`,
`switch`, `gateway`); `distinct` (string -- field to group by, e.g. `model`, `type`,
`site_id`, `hw_rev`, `mac`); `limit` (int -- max number of buckets to return, default
100). The doc notes pagination is supported via `limit`/`page`, but in practice the
count endpoint is single-page for any realistic distinct field (cardinality of model /
type / site is small).

**Rationale**:
The spec.md authoritatively names the SDK module path
`mistapi.api.v1.orgs.inventory.count`. The enriched doc also lists
`mistapi.api.v1.orgs.inventory.countOrgInventory()`, but mistapi historically generates
module paths from the URL one-for-one (verified against adjacent endpoints such as
`/orgs/{org_id}/inventory/search` which lives in `mistapi.api.v1.orgs.inventory.search`).
The `inventory.count` path matches the URL leaf `inventory/count` exactly. Final
verification happens at implementation time via `python -c "from
mistapi.api.v1.orgs.inventory import count; help(count)"` inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/inventory/count`.* Rejected -- the constitution
   forbids direct HTTP when a mistapi method exists.
2. *Use the flatter path the doc summary line implies
   (`mistapi.api.v1.orgs.inventory.countOrgInventory`).* Rejected -- the SDK organizes
   modules by URL path segments, not by operationId nesting. The spec.md (the
   authoritative feature contract) names the URL-based path, and that matches the
   convention of all other endpoints in this category.
3. *Cache the response client-side to avoid a follow-up call.* Rejected -- the spec is
   for a read-only export menu item; caching is out of scope and is already handled by
   the multi-backend `DataExporter`.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on a single output table named
`org_inventory_count`. The composite PK is `(org_id, type_filter, distinct_field,
distinct_value)` -- four columns. MistHelper injects `org_id`, `type_filter`,
`distinct_field` (the value the user supplied for the `distinct` query parameter), and
`distinct_value` (the additional property on each `count_result` bucket, e.g. the actual
model name or site UUID) before the upsert. The API does not return `org_id`,
`type_filter`, or `distinct_field` in the body, so MistHelper supplies them from the
request context.

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk` with
`primary_key=['org_id', 'type_filter', 'distinct_field', 'distinct_value']` and
`indexes=['distinct_field', 'distinct_value', 'count']`.

**Rationale**:
The count endpoint summarizes the inventory grouped by one chosen attribute. Repeated
runs with the same `(org_id, type, distinct)` triple must update the same bucket rows
rather than append duplicates. Including `distinct_value` (the per-bucket grouping
value) as the fourth PK column lets multiple buckets coexist in one table for the same
query. Including `type_filter` and `distinct_field` in the PK lets the user run the
menu item with different `distinct` choices (e.g. once by `model`, once by `site_id`)
without overwriting each other's results. `INSERT OR REPLACE` then refreshes the count
for each bucket on every poll.

**Alternatives Considered**:

1. *`auto_increment_with_unique`.* Rejected -- would let repeated polls accumulate
   duplicate snapshots of the same bucket, defeating the upsert behavior the spec
   requires and breaking dashboards that join on the bucket key.
2. *`natural_pk` on `distinct_value` alone.* Rejected -- `distinct_value` is not unique
   across orgs (two orgs can both have an `AP43` bucket) and is not unique across
   distinct-field choices (the value `"ap"` could be a bucket under `distinct=type`
   *and* a bucket under `distinct=model_family` in adjacent runs). The composite key is
   the only correct option.
3. *One table per `(org, distinct_field)` combination.* Rejected -- explodes the
   sqlite schema, breaks the single `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry pattern,
   and makes cross-distinct queries painful.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/org_<org_id_short>_inventory_count_<distinct_field>.csv` (one file per
  `(org, distinct_field)` combination so an operator can keep snapshots of different
  groupings without clobbering each other).
- SQLite table: `org_inventory_count` (single table, multi-key as described in Research
  Task 2).
- `org_id_short` is the first 8 hex characters of the org UUID -- the convention
  already used by adjacent inventory exports in MistHelper for human-readable filenames
  without leaking full UUIDs into shell history.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"countOrgInventory"` (matching the operationId). The DataExporter uses that string
as the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by `getOrgInventory` and other inventory exports. A
single SQLite table keeps the schema flat and lets a user `SELECT ... WHERE
distinct_field = 'model'` to filter to a specific grouping. Per-distinct CSV filenames
make it obvious from a directory listing which grouping each snapshot captured.

**Alternatives Considered**:

1. *Single CSV per org regardless of distinct choice, with `distinct_field` as a
   column.* Rejected -- successive runs with different distinct fields would overwrite
   the same file, losing earlier snapshots.
2. *Full org UUID in the filename.* Rejected -- leaks the org UUID into shell history
   and `ls` output unnecessarily. The 8-char short form disambiguates locally and is
   the established convention.
3. *Separate SQLite tables per `distinct_field`.* Rejected -- schema explosion as
   discussed in Research Task 2.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 59**, the last slot inside the Safe Org
Exports band (1-59) immediately before the Interactive Safe band begins at 60. The
category label is "Safe Org Exports -- Inventory Counts". A late-band slot is chosen
because the early inventory cluster (8-14) is already saturated and re-numbering
existing menu items is out of scope for this feature.

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource Intensive, 102-123
WebSocket, 124-152 Interactive, 154-194 Destructive. The count endpoint is a single
read-only GET that returns a bounded result (default 100 buckets), so it belongs
squarely in the Safe Org Exports band and absolutely not in the Destructive band. Slot
59 is provisional -- at `/speckit.tasks` time, MistHelper.py is grep'd for the latest
allocated menu integer and 59 is shifted forward into the next free safe-band slot if a
conflict exists.

**Alternatives Considered**:

1. *Append to the end of the file (e.g., 195).* Rejected -- the destructive cluster
   ends at 194, and placing a safe read-only count operation above the destructive
   block visually mis-signals the risk level to a junior NOC engineer scrolling the
   menu.
2. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is a single
   GET that returns a small aggregated payload with no long-running work. It does not
   belong in the heavy block.
3. *Slot inside the early inventory cluster (8-14).* Rejected -- those numbers are
   already occupied by the existing `getOrgInventory` exports; renumbering would be a
   breaking change to operators' muscle memory and is out of scope.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **up to four** values via `safe_input()`. Only
`org_id` and `distinct_field` are required; the rest have sensible defaults that let
the operator press Enter through them.

1. `org_id` -- prompt: `"Org ID (UUID): "`, context: `"org_inventory_count:org_id"`.
   Default: the value of `MIST_ORG_ID` in `.env` if present (pressing Enter accepts the
   default). Validated via the existing `is_valid_uuid()` helper before the API call;
   on failure, log `WARNING` and return early.
2. `distinct_field` -- prompt: `"Distinct field to group by (model | type | site_id |
   hw_rev | mac | sku | version): "`, context: `"org_inventory_count:distinct"`.
   Default: `model` (the most common grouping when counting AP inventory). No
   server-side enum is enforced by the API; the prompt's suggested list mirrors the
   conventional values exposed elsewhere in the Mist UI.
3. `type_filter` -- prompt: `"Inventory type filter (ap | switch | gateway | blank for
   all): "`, context: `"org_inventory_count:type"`. Default: blank (all types). Empty
   answer omits the query parameter entirely so the server returns counts across all
   device types.
4. `limit` -- prompt: `"Bucket limit (Enter for API default 100): "`, context:
   `"org_inventory_count:limit"`. Default: `100`. Parsed with `int(...)` inside a
   try/except; on parse failure log `WARNING` and fall back to `100`.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.

**Rationale**:
Mist's inventory count endpoint is org-scoped only -- no site or device IDs are
involved. The `distinct` parameter materially changes which buckets the server returns,
so asking the user upfront avoids hard-coding a single grouping choice. The `type` and
`limit` parameters are optional and rarely changed in practice, so they default
through. Keeping the prompts short and well-defaulted matches the pattern used by
adjacent inventory menu items and keeps SSH-on-2200 sessions responsive for junior NOC
operators.

**Alternatives Considered**:

1. *Loop over a fixed list of distinct fields and run the call for each, producing one
   combined CSV.* Rejected -- multiplies API calls, hits rate limits faster, and
   couples the menu's behavior to a hard-coded enum that may drift from the API.
2. *Skip the `limit` prompt and hard-code 1000.* Rejected -- a junior operator may
   want to cap output for a quick spot-check; honoring the API default of 100 plus
   allowing override is more flexible at trivial code cost.
3. *Ask for a custom output filename.* Rejected -- adds keystrokes without operational
   value. The deterministic filename scheme in Research Task 3 makes results easy to
   find under `data/`.
