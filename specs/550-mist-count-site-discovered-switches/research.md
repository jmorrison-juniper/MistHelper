# Phase 0 Research: countSiteDiscoveredSwitches

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each task
follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/sites/GET_sites_site_id_stats_discovered_switches_count.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL:
`mistapi.api.v1.sites.stats.discovered_switches.count.countSiteDiscoveredSwitches(
apisession, site_id, distinct=None, start=None, end=None, duration="1d", limit=100)`.
The SDK returns a `mistapi.APIResponse` whose `.data` attribute is the parsed JSON body.
The body is a single JSON object (not paginated by `page`, though `limit` caps the
embedded `results` array size). Top-level keys per the doc:

- `distinct` (string -- echoes the requested grouping attribute, may be empty)
- `start` (int epoch seconds -- start of the time window the count covers)
- `end` (int epoch seconds -- end of the time window)
- `limit` (int -- echoes the requested limit, default 100)
- `total` (int -- total count across all groups)
- `results` (array of `count_result` objects -- one per distinct value when grouping is
  requested; required field per group: `count` (int). Additional string properties carry
  the actual distinct value, e.g. `vendor`, `model`, `version` -- the API permits
  arbitrary additional string properties on each group object.)

Required path parameter: `site_id` (UUID string).
Optional query parameters: `distinct` (string), `start` (string -- epoch seconds or
relative like `-1d`), `end` (string -- same), `duration` (string -- e.g. `1d`, `7d`,
`2w`; default `1d`), `limit` (int, default 100).

**Rationale**:
The enriched per-endpoint doc lists the SDK module as
`mistapi.api.v1.sites.stats_-_discovered_switches.countSiteDiscoveredSwitches()`. The
doubled `_-_` is a doc-generator artifact; the mistapi SDK organizes modules from URL
path tokens, dropping dashes inside path segments. The spec.md authoritatively names
`mistapi.api.v1.sites.stats.discovered_switches.count`, which matches the OpenAPI URL
one-for-one and follows the same convention used by neighboring SDK modules
(`mistapi.api.v1.sites.stats.devices`, `mistapi.api.v1.sites.stats.clients`, etc.). We
follow the spec. Final verification happens at implementation time via
`python -c "from mistapi.api.v1.sites.stats.discovered_switches import count; help(count)"`
inside the venv. The `count_result` schema permits arbitrary additional string
properties on each group, so the flatten helper must enumerate `dict.items()` rather
than hard-coding field names.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/sites/{site_id}/stats/discovered_switches/count`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method exists.
2. *Hard-code the expected group fields (`vendor`, `model`, `version`).* Rejected --
   the OpenAPI schema explicitly allows arbitrary additional string properties on each
   `count_result`. Hard-coding would silently drop unknown attributes.
3. *Pass `duration=None` to omit the default.* Rejected -- the SDK and API both default
   to `1d` when omitted; passing the explicit `"1d"` makes the value visible in logs and
   reproducible across runs.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on two separate output tables:

- `site_discovered_switches_count_summary`: PK =
  `(site_id, distinct, start, end)` -- one row per (site, grouping attribute, time
  window) poll. `distinct` is normalized to the empty string `""` when the caller did
  not group, so the PK never contains NULL.
- `site_discovered_switches_count_groups`: PK =
  `(site_id, distinct, start, end, group_value)` -- one row per distinct value within
  the same poll. `group_value` is the resolved value of the distinct attribute (vendor
  name, model string, etc.), normalized to `""` when no grouping is in effect (the
  ungrouped case yields exactly one group row with `count = total`).

Both entries register as `composite_pk` in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. The
`site_id` is injected by MistHelper before write -- the API does not echo it in the
response body.

**Rationale**:
The endpoint reports a *current* aggregate over a time window. Re-polling the same
site with the same `distinct` and the same time window must upsert the existing summary
row (and refresh its child group rows) rather than accumulate duplicates. The composite
key `(site_id, distinct, start, end)` uniquely identifies a single poll's question;
re-running with a wider `duration` produces a different `(start, end)` and therefore a
distinct row. Splitting summary from groups keeps the group rows queryable with one row
per `(vendor, model, version, ...)` without nullable PK columns in the ungrouped case.
`INSERT OR REPLACE` upserts every poll's view of the count cleanly.

**Alternatives Considered**:

1. *`auto_increment_with_unique`.* Rejected -- repeated polls of the same site would
   pile up snapshots in the summary table, defeating the upsert contract the spec
   requires.
2. *Single combined table with `total` plus a JSON-encoded `groups` column.* Rejected --
   breaks SQL queryability and conflicts with MistHelper's flattening convention.
3. *`natural_pk` on `start` alone.* Rejected -- not unique across sites or `distinct`
   values, and stable identity for the request requires all four components.
4. *Use `polled_at_utc` in the PK.* Rejected -- would force a new row on every poll,
   eliminating upsert semantics for repeat polls of the same window.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/site_<site_id_short>_discovered_switches_count_summary.csv`
- CSV (groups): `data/site_<site_id_short>_discovered_switches_count_groups.csv`
- SQLite tables: `site_discovered_switches_count_summary` and
  `site_discovered_switches_count_groups`
- `site_id_short` is the first 8 hex characters of the site UUID -- already the
  convention used by adjacent site-stats exports in MistHelper for human-readable
  filenames without leaking full UUIDs into shell history.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"countSiteDiscoveredSwitches"` (matching the operationId). The DataExporter uses
that string as the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES` for the summary
write; the groups write uses the MistHelper-internal sub-table id
`"countSiteDiscoveredSwitchesGroups"`.

**Rationale**:
Matches the naming pattern used by adjacent site-stats exports (`searchSite*`,
`listSite*`). Two output files / two SQLite tables keep the schema clean and let a user
query the summary without joining when they only need the `total`.

**Alternatives Considered**:

1. *Single output file with JSON-encoded groups column.* Rejected -- breaks SQL
   queryability.
2. *Full site UUID in the filename.* Rejected -- leaks the site UUID into shell history
   and `ls` output unnecessarily.
3. *Plain `discovered_switches_count.csv` without site prefix.* Rejected -- adjacent
   site exports always prefix with the short site id so multiple sites can coexist in
   the same `data/` directory.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 91**, sitting inside the Interactive Safe
range (60-96), specifically the site-stats sub-cluster (80-91). The category label is
"Interactive Safe -- Site Stats -- Discovered Switches".

**Rationale**:
Menu ranges per `.github/copilot-instructions.md`: 1-59 Safe Org Exports, 60-96
Interactive Safe (60-72 Site Devices, 73-79 Insights, 80-91 Stats, 92-96 Viewers),
97-101 + 153 Resource Intensive, 102-123 WebSocket, 124-152 Interactive, 154-194
Destructive. A site-scoped *count* of discovered switches is read-only, lightweight,
and site-stats-flavored -- it belongs in the 80-91 stats sub-cluster. 91 is the highest
contiguous integer in that sub-cluster, sitting one slot below the viewers sub-cluster
at 92-96 and well above the destructive bracket at 154+. The number is provisional --
at `/speckit.tasks` time, `MistHelper.py` is grep'd for the latest allocated menu
integer and 91 is shifted (89 -> 88 -> 92+) if a conflict exists.

**Alternatives Considered**:

1. *Append at the end (e.g., 195).* Rejected -- the destructive cluster ends at 194,
   and placing a read-only site-stats count above the destructive block visually
   mis-signals risk to a junior NOC engineer scrolling the menu.
2. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is a single
   GET that returns a small JSON object, with no pagination loop and no long-running
   work. It does not belong in the resource-intensive bracket.
3. *Slot inside Org Exports (1-59).* Rejected -- the endpoint is site-scoped, not
   org-scoped. The org / site split in the menu is a deliberate safety affordance.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for up to **five** values via `safe_input()`:

1. `site_id` -- prompt: `"Site ID (UUID): "`, context:
   `"site_discovered_switches_count:site_id"`. Default: value of `MIST_SITE_ID` in
   `.env` if present (Enter accepts the default). Validated via the existing
   `is_valid_uuid()` helper before the API call; on failure log `WARNING` and return
   early.
2. `distinct` -- prompt:
   `"Group by distinct attribute (vendor/model/version/...), blank for no grouping: "`,
   context: `"site_discovered_switches_count:distinct"`. Default: empty string. Passed
   to the SDK as `distinct=value or None` so the query parameter is omitted when blank.
3. `duration` -- prompt: `"Duration (e.g. 1d, 7d, 2w) [1d]: "`, context:
   `"site_discovered_switches_count:duration"`. Default: `"1d"`. Forwarded to the SDK
   verbatim; the API parses the value and rejects malformed strings with 400, which
   MistHelper logs as a `WARNING`.
4. `start` -- prompt:
   `"Start time (epoch seconds or relative like -1d), blank to omit: "`, context:
   `"site_discovered_switches_count:start"`. Default: empty. Passed as
   `start=value or None`. Ignored by the API when `duration` is supplied; surfaced to
   the user for parity with the OpenAPI parameter list.
5. `limit` -- prompt: `"Result limit (max items in results array) [100]: "`, context:
   `"site_discovered_switches_count:limit"`. Default: `100`. Validated to be a positive
   integer; on failure log `WARNING` and clamp to `100`.

`end` is *not* prompted separately -- the constitution-driven UX preference is to keep
prompt count <=5 (Five-Item Rule applied to the prompt list). If a user wants an
absolute end, they supply it via `MIST_DISCOVERED_SWITCHES_END` in `.env` (read at
runtime, never logged) and the method picks it up if present, otherwise omits the
parameter.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_SITE_ID` -- optional default for prompt 1.
- `MIST_DISCOVERED_SWITCHES_END` -- optional override for the `end` query parameter
  (epoch seconds or relative string). When unset, the parameter is omitted from the
  SDK call.

**Rationale**:
The endpoint is site-scoped; org / device IDs are not involved. The `distinct`,
`duration`, and `limit` parameters materially change the response shape and size, so
they are exposed as prompts. The `start` prompt is kept because operators sometimes need
to point at a fixed historical window; `end` is demoted to `.env` to respect the
5-prompt budget while remaining reachable.

**Alternatives Considered**:

1. *Always group by `model` to keep the prompt count to two.* Rejected -- different
   sites have different distinct fields of interest (`vendor` for mixed-vendor
   environments, `version` for upgrade planning). Hard-coding loses operational value.
2. *Promote `end` to a prompt, removing `limit`.* Rejected -- a missing `limit`
   silently yields whatever the server defaults to (100), which is the right default
   for nearly every use case; explicit confirmation of `limit` reads more clearly than
   a less-frequently-changed `end`.
3. *Read every parameter from `.env` and prompt for none.* Rejected -- violates the
   spec's User Story 1 ("supplies the required identifiers"). The site_id must remain
   an explicit, auditable prompt.
