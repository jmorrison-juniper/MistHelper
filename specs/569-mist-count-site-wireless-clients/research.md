# Phase 0 Research: countSiteWirelessClients

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/sites/GET_sites_site_id_clients_count.md`
(enriched OpenAPI doc for `GET /api/v1/sites/{site_id}/clients/count`).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.sites.clients.count.countSiteWirelessClients(apisession,
site_id, distinct=None, ssid=None, ap=None, ip=None, vlan=None, hostname=None, os=None,
model=None, device=None, start=None, end=None, duration="1d", limit=100)`. The SDK
returns a `mistapi.APIResponse` object whose `.data` attribute is the parsed JSON body.
The body is a single JSON object (not paginated as a stream, though `limit`/`page`
query parameters apply when the `results` array would exceed `limit`), with the
following top-level keys per the doc:

- `distinct` (string -- the group-by field actually used by the server)
- `start` (int epoch seconds -- start of the count window)
- `end` (int epoch seconds -- end of the count window)
- `limit` (int -- the server-side cap on returned distinct values)
- `total` (int -- total distinct values matched)
- `results` (array of `count_result` objects: `{count: int, <distinct field>: string}`
  -- one entry per distinct value with its associated count)

Required path parameter: `site_id` (UUID string).
Optional query parameters (all string except `limit` which is int): `distinct`, `ssid`,
`ap`, `ip`, `vlan`, `hostname`, `os`, `model`, `device`, `start`, `end`, `duration`,
`limit`. The `distinct` parameter selects the grouping field; the same field name then
appears as a key on every `results[]` object. When `distinct` is omitted the server
falls back to its default (treated by MistHelper as `device` for consistency with
adjacent search endpoints).

**Rationale**:
The enriched per-endpoint doc lists the SDK module as
`mistapi.api.v1.sites.clients_-_wireless.countSiteWirelessClients()`, but the dash
characters in `clients_-_wireless` are invalid in a Python module name. The mistapi SDK
historically generates module paths from the URL, not the OpenAPI tag (verified by
inspecting adjacent endpoints under the same path, e.g.
`GET /sites/{site_id}/clients/search` which lives in `mistapi.api.v1.sites.clients`
and `GET /sites/{site_id}/clients/count` which lives in
`mistapi.api.v1.sites.clients.count`). The spec.md explicitly names
`mistapi.api.v1.sites.clients.count` and that path matches the URL one-for-one, so we
follow the spec. Final verification happens at implementation time via
`python -c "from mistapi.api.v1.sites.clients import count; help(count)"` inside the
venv.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/sites/{site_id}/clients/count`.* Rejected -- the constitution
   forbids direct HTTP when a mistapi method exists.
2. *Use the path implied by the doc tag (`...sites.clients_-_wireless...`).* Rejected
   -- Python module names cannot contain dashes; the SDK organizes modules by URL
   path, not OpenAPI tag.
3. *Reuse the wired-client count endpoint (`/sites/{site_id}/wired_clients/count`).*
   Rejected -- different endpoint, different operationId
   (`countSiteWiredClients`), different SDK module. A separate menu item for the
   wired counterpart belongs in a separate spec.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on two separate output tables:

- `site_wireless_client_count_summary`: PK =
  `(site_id, distinct, window_start, window_end)` -- one row per count query.
  `window_start` / `window_end` are the API-echoed `start` / `end` epochs from the
  response body, guaranteeing a stable snapshot identifier even when the user supplies
  a relative time string like `-1d`.
- `site_wireless_client_count_results`: PK =
  `(site_id, distinct, window_start, window_end, distinct_value)` -- one row per
  distinct value returned in the `results` array. `distinct_value` is the per-row
  value of whatever field the user grouped by (e.g., the SSID name, the AP MAC, the
  hostname).

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk` for both
tables, with `site_id` and `distinct` injected by MistHelper before the upsert (Mist
echoes `distinct` in the body but `site_id` is the MistHelper caller context).

**Rationale**:
This endpoint reports an aggregated *count snapshot* parameterized by (site, group-by
field, time window). Re-running the menu item against the same site / distinct / window
tuple must update the existing row rather than append a duplicate (the user is asking
"give me the current count for this window again"). `INSERT OR REPLACE` upserts every
snapshot. Splitting summary and results lets a user query "how many SSIDs are active
at this site right now" without scanning every per-SSID detail row, and lets
`DataExporter` emit two CSVs that match the two SQLite tables.

**Alternatives Considered**:

1. *`auto_increment_with_unique`.* Rejected -- would let repeated polls accumulate
   duplicate snapshots, defeating the upsert behavior the spec requires.
2. *Single combined table with one row per `(site_id, distinct, distinct_value,
   start, end)` and the summary fields denormalized onto every row.* Rejected --
   duplicates the summary across every result row, breaks normalization, and makes
   "list all count queries" queries quadratically expensive.
3. *`natural_pk` on the API's own `start`/`end`/`distinct` triple.* Rejected --
   ignores `site_id` and would collide across sites in a multi-site MistHelper
   deployment.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/site_<site_id_short>_wireless_client_count_summary.csv`
- CSV (results): `data/site_<site_id_short>_wireless_client_count_results.csv`
- SQLite tables: `site_wireless_client_count_summary` and
  `site_wireless_client_count_results`
- `site_id_short` is the first 8 hex characters of the site UUID -- already the
  convention used by adjacent site exports in MistHelper for human-readable filenames
  without leaking full UUIDs into shell history.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"countSiteWirelessClients"` (matching the operationId). The `DataExporter` uses
that string as the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`; the results sub-
table is registered under the MistHelper-internal id `"countSiteWirelessClientsResults"`
following the same nested-array pattern used by other split exports (precedent:
`getOrgLicenseAsyncClaimStatusDetails`).

**Rationale**:
Matches the naming pattern used by `searchSiteWirelessClients` (menus 30 and 34) and
other adjacent site exports. Two output files / two SQLite tables keep the schema clean
and let a user query the summary without joining when only the count totals are needed.

**Alternatives Considered**:

1. *Single output file with JSON-encoded `results` column.* Rejected -- breaks SQL
   queryability and conflicts with the flattening convention used everywhere else in
   MistHelper.
2. *Full site UUID in the filename.* Rejected -- leaks the site UUID into shell
   history and `ls` output unnecessarily. The short form is enough to disambiguate
   locally.
3. *Per-distinct-field filename suffix (e.g.,
   `..._wireless_client_count_by_ssid.csv`).* Rejected -- generates an
   unbounded set of files over time as the user runs the menu with different `distinct`
   values; the `distinct` column inside the table is sufficient to filter at query
   time.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 89**, sitting inside the Interactive Safe
site-stats cluster (80-91). The category label is "Interactive Safe -- Site Stats".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource Intensive,
102-123 WebSocket, 124-152 Interactive, 154-194 Destructive. Site-scoped counting
operations belong with site stats (80-91). 89 is the next contiguous integer inside the
stats sub-cluster before the resource-intensive block at 90 (test skip list) / 97-101.
Crucially, 89 is **not** in the heavy/destructive skip list (14, 18, 63-65, 90-100), so
it will be exercised automatically by `python MistHelper.py --test`. The number is
provisional -- at `/speckit.tasks` time, `MistHelper.py` is grep'd for the latest
allocated menu integer and 89 is shifted forward if a conflict exists.

**Alternatives Considered**:

1. *Append to the end (e.g., 195).* Rejected -- the destructive cluster ends at 194,
   and placing a read-only count check above the destructive block visually mis-signals
   the risk level to a junior NOC engineer scrolling the menu.
2. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is a single
   GET that returns a small JSON object with a bounded `results` array, with no
   long-running work. It belongs in the Interactive Safe block.
3. *Slot in the Safe Org Exports range (1-59).* Rejected -- this endpoint is
   site-scoped, not org-scoped. Org-scoped exports do not require a site UUID prompt;
   this one does.
4. *Slot adjacent to menus 30 / 34 (the existing `searchSiteWirelessClients` menus).*
   Rejected -- 30 / 34 sit in the Safe Org Exports range because they target the
   org-wide client search endpoint, not a single site. The count endpoint requires a
   site UUID, placing it correctly in the site-scoped Interactive Safe block.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly four** values via `safe_input()`:

1. `site_id` -- prompt: `"Site ID (UUID): "`, context:
   `"site_wireless_client_count:site_id"`. Default: the value of `MIST_SITE_ID` in
   `.env` if present (pressing Enter accepts the default). Validated via the existing
   `is_valid_uuid()` helper before the API call; on failure, log `WARNING` and return
   early.
2. `distinct_field` -- prompt: `"Group-by field [ssid|ap|ip|vlan|hostname|os|model|
   device] (default: device): "`, context:
   `"site_wireless_client_count:distinct"`. Validated against the allow-list above
   before the SDK call; on failure, log `WARNING` and return early. Default value
   passed to the SDK when the user accepts the default is `"device"`.
3. `time_window_start` -- prompt:
   `"Start (epoch or relative e.g. -1d, blank for default): "`, context:
   `"site_wireless_client_count:start"`. Empty string means omit the parameter.
4. `time_window_end` -- prompt:
   `"End (epoch or relative e.g. now, blank for default): "`, context:
   `"site_wireless_client_count:end"`. Empty string means omit the parameter.

The `limit` query parameter is not exposed to the user; it stays at the SDK's documented
default (100). Power users who need a different cap can pass it via a future
`--menu 89 --limit 500` argument flag (out of scope for this spec).

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_SITE_ID` -- optional default for prompt 1.

**Rationale**:
The Mist count endpoint is site-scoped and group-by configurable; both inputs change
the semantic meaning of the response. The time window is genuinely optional (the API
defaults to "current associations" which is usually what an operator wants). Asking for
only the two essentials by default (site + distinct) keeps the menu friendly for the
common case, while the time-window prompts give the operator a clean upgrade path when
historical counts are needed. All four prompts use `safe_input()` so EOF from an SSH
disconnect exits cleanly with code 0 and no traceback.

**Alternatives Considered**:

1. *Single prompt asking the user to type a full query string like `distinct=ssid&
   duration=7d`.* Rejected -- error-prone for junior NOC engineers and violates the
   spec's "professional, no jargon" tone requirement.
2. *Always use `distinct=ssid` as a fixed value to reduce prompt count to one.*
   Rejected -- different operators need different group-by fields (SSID for capacity
   planning, AP MAC for radio planning, hostname for client discovery). Forcing one
   field would require additional menu numbers per distinct value.
3. *Skip the time-window prompts entirely and always use the SDK default.* Rejected
   -- historical count queries are a documented use case in the spec's User Story 1
   edge cases; exposing the prompts here costs almost nothing and unlocks the
   feature.
