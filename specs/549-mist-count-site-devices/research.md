# Phase 0 Research: countSiteDevices

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/sites/GET_sites_site_id_devices_count.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.sites.devices.count.countSiteDevices(apisession, site_id,
distinct=None, hostname=None, model=None, mac=None, version=None, mxtunnel_status=None,
mxedge_id=None, lldp_system_name=None, lldp_system_desc=None, lldp_port_id=None,
lldp_mgmt_addr=None, map_id=None, start=None, end=None, duration="1d", limit=100)`.
The SDK returns a `mistapi.APIResponse` object whose `.data` attribute is the parsed
JSON body. The body is a single "count envelope" JSON object with these top-level
keys (all required per the response schema):

- `distinct` (string) -- the grouping field actually used by the server (echoes the
  request's `distinct` value, or the API's default field when the user omits it)
- `start` (int32, epoch seconds) -- start of the time window the count covers
- `end` (int32, epoch seconds) -- end of the time window
- `limit` (int32) -- the page size cap that was honored
- `total` (int32) -- total number of distinct buckets the server matched
- `results` (array of `count_result` objects) -- one entry per bucket; each entry
  has a required `count` field (int32) plus a free-form `additionalProperties: string`
  field that names the bucket (e.g. `{"count": 42, "model": "AP43"}` when
  `distinct=model`)

Required path parameter: `site_id` (UUID string).
Optional query parameters: `distinct`, `hostname`, `model`, `mac`, `version`,
`mxtunnel_status`, `mxedge_id`, `lldp_system_name`, `lldp_system_desc`,
`lldp_port_id`, `lldp_mgmt_addr`, `map_id`, `start`, `end`, `duration` (default
`1d`), `limit` (default `100`).

**Rationale**:
The enriched per-endpoint doc lists the SDK module as
`mistapi.api.v1.sites.devices.countSiteDevices()` and the spec.md names
`mistapi.api.v1.sites.devices.count`. The mistapi SDK organizes modules from the
URL path (verified by adjacent endpoints under the same parent path:
`/sites/{site_id}/devices` -> `mistapi.api.v1.sites.devices`,
`/sites/{site_id}/devices/search` -> `mistapi.api.v1.sites.devices.search`). The
URL-derived path `mistapi.api.v1.sites.devices.count` is the canonical match.
Final verification happens at implementation time via
`python -c "from mistapi.api.v1.sites.devices import count; help(count)"` inside
the venv.

The doc explicitly flags a gotcha: like `listSiteDevices`, this endpoint may default
to APs only unless the caller passes a `type` filter. The OpenAPI schema does not
document `type` as a query parameter, so MistHelper does not expose it on the prompt
surface, but the menu help text warns the operator that APs-only is the most likely
default. If the SDK exposes an undocumented `type` parameter, the implementer adds
it during `/speckit.implement`.

**Alternatives Considered**:

1. *Direct `requests.get` against the URL with manual query-string construction.*
   Rejected -- the constitution forbids direct HTTP when a mistapi SDK method
   exists.
2. *Use the path implied by the doc's tag (`Sites Devices`).* Rejected -- the SDK
   organizes modules by URL path, not OpenAPI tag, and spec.md (the authoritative
   feature contract) names the URL-based path.
3. *Iterate all `distinct` values in a single menu run.* Rejected -- forces N
   sequential API calls when the operator typically only wants one bucketing
   dimension. The menu prompt asks for a single `distinct` value per invocation.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on a single output table
`site_devices_count`:

- PK = `(site_id, distinct_field, bucket_value, polled_at_utc)`

Where:

- `site_id` is the user-supplied UUID, injected by MistHelper before write (the API
  does not echo it in the body).
- `distinct_field` is the grouping dimension actually returned by the server in the
  response's `distinct` field (e.g. `model`, `version`, `hostname`).
- `bucket_value` is the value of the `additionalProperties` string slot for each
  result entry (e.g. `"AP43"`, `"0.14.x"`). When the server returns a count without
  a discriminator (rare, summary-only mode), `bucket_value` is the literal string
  `"__total__"`.
- `polled_at_utc` is the MistHelper-generated ISO8601 UTC timestamp of the poll.

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk` with
this four-column key.

**Rationale**:
The endpoint reports the *current* count of distinct device buckets at a site for a
given time window. Two operationally important behaviors must be preserved:

1. Repeat polls with the same `distinct` value at the same site should produce
   distinct historical snapshots (so the operator can chart counts over time), not
   overwrite each other. Including `polled_at_utc` in the PK guarantees this.
2. Within a single poll, no two rows can share the same `(site_id, distinct_field,
   bucket_value)` triple (the API enforces `uniqueItems: true` on `results`), so
   the composite key is naturally unique without auto-increment.

Including `distinct_field` in the PK also lets the operator run the menu item
multiple times with different `distinct` values against the same site without
collisions (e.g. first `distinct=model`, then `distinct=version`).

**Alternatives Considered**:

1. *`auto_increment_with_unique` on `(site_id, distinct_field, bucket_value,
   polled_at_utc)`.* Rejected -- the composite values are already unique and stable,
   so the surrogate ID column adds no value and breaks the natural-key convention
   used elsewhere in MistHelper.
2. *`natural_pk` on the API's `total` envelope.* Rejected -- the envelope is a
   single object per call, not a stable entity. The interesting business data is
   the `results` array, which is what the table models.
3. *Use `polled_at_utc` alone.* Rejected -- a single timestamp is not unique across
   the rows produced by one poll (one envelope yields many bucket rows, all sharing
   the same `polled_at_utc`).
4. *Drop `polled_at_utc` and upsert in place.* Rejected -- destroys the historical
   snapshot value the operator needs for trend analysis.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/site_<site_id_short>_devices_count_<distinct_field>.csv`
- SQLite table: `site_devices_count` (single shared table; `distinct_field` is a
  column so all `distinct` choices share one table)
- `site_id_short` is the first 8 hex characters of the site UUID -- the same
  convention used by adjacent site-scoped exports for human-readable filenames
  without leaking full UUIDs into shell history.
- When the user omits the `distinct` prompt, the filename suffix is `_summary`
  (e.g. `data/site_0a1b2c3d_devices_count_summary.csv`).

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"countSiteDevices"` (matching the
operationId). The DataExporter uses that string as the lookup key into
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
The shared SQLite table with a `distinct_field` discriminator column matches the
shape of the `searchSiteDeviceEvents` and `searchSiteAlarms` tables already in
MistHelper, where a single physical table holds rows differing only in the
grouping dimension. The per-CSV split by `distinct_field` keeps individual CSVs
narrow and easy to load into a spreadsheet for ad-hoc inspection. The short
`site_id_short` prefix matches the adjacent `listSiteDevices` and per-site
device-stats CSV naming.

**Alternatives Considered**:

1. *One SQLite table per `distinct` value (e.g. `site_devices_count_model`,
   `site_devices_count_version`).* Rejected -- N tables for the same logical entity
   complicates ad-hoc SQL joins and forces the operator to know table names per
   poll. Single table with a `distinct_field` column is cleaner.
2. *Full site UUID in the filename.* Rejected -- leaks the site UUID into shell
   history and `ls` output unnecessarily. The 8-char short form is enough to
   disambiguate locally.
3. *No `distinct_field` in the CSV filename suffix.* Rejected -- consecutive polls
   with different `distinct` values would overwrite the same CSV.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 72**, sitting at the top of the Site
Devices interactive-safe cluster (range 60-72), immediately adjacent to the
existing `listSiteDevices` and per-site device-stats menu items. The category label
is "Interactive Safe -- Site Devices".

**Rationale**:
The menu ranges documented in `.github/copilot-instructions.md` and the constitution
are:

| Range | Category |
|-------|----------|
| 1-59 | Safe Org Exports |
| 60-72 | Site Devices (subset of 60-96 Interactive Safe) |
| 73-79 | Insights |
| 80-91 | Site Stats |
| 92-96 | Viewers |
| 97-101 + 153 | Resource Intensive |
| 102-123 | WebSocket |
| 124-150 | Interactive (diagnostics, mgmt, packet captures, tools, config) |
| 151-152 | Continuous monitoring |
| 154-194 | Destructive |

`countSiteDevices` is a site-scoped, read-only, fast GET that returns a small count
envelope. It belongs squarely in the Site Devices cluster. Number 72 is the next
contiguous integer at the top of that cluster, far away from any destructive or
resource-intensive operations. The number is provisional -- at `/speckit.tasks`
time, `MistHelper.py` is grep'd for the latest allocated menu integer and 72 is
shifted forward if a conflict exists with an in-flight feature branch.

**Alternatives Considered**:

1. *Slot inside Site Stats (80-91).* Rejected -- `countSiteDevices` is about
   inventory aggregation, not real-time stats; it belongs with the other devices
   exports.
2. *Append to the very end (e.g., 195).* Rejected -- the destructive cluster ends
   at 194, and placing a read-only count above the destructive block visually
   mis-signals the risk level to a junior NOC engineer scrolling the menu.
3. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is a
   single GET that returns a small JSON object with no long-running work. It does
   not belong in the resource-intensive block.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly three** values via `safe_input()`:

1. `site_id` -- prompt: `"Site ID (UUID): "`, context:
   `"site_devices_count:site_id"`. Default: the value of `MIST_SITE_ID` in `.env`
   if present (pressing Enter accepts the default). Validated via the existing
   `is_valid_uuid()` helper before the API call; on failure, log `WARNING` and
   return early.
2. `distinct_field` -- prompt: `"Group by which field? (model/version/hostname/mac/
   mxedge_id/lldp_system_name -- press Enter for server default): "`, context:
   `"site_devices_count:distinct"`. Default: empty string (server applies its own
   default). The answer is passed as the `distinct=` SDK argument verbatim; an
   empty answer means the parameter is omitted from the request entirely.
3. `limit` -- prompt: `"Result limit (default 100, max documented by Mist API):
   "`, context: `"site_devices_count:limit"`. Default: `100` (matches the OpenAPI
   default). Parsed as `int`; on `ValueError` the method logs `WARNING`, falls
   back to 100, and proceeds.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_SITE_ID` -- optional default for prompt 1.

The other 13 documented query parameters (`hostname`, `model`, `mac`, `version`,
`mxtunnel_status`, `mxedge_id`, `lldp_system_name`, `lldp_system_desc`,
`lldp_port_id`, `lldp_mgmt_addr`, `map_id`, `start`, `end`, `duration`) are
deliberately not surfaced as interactive prompts in v1 of this menu item. The
menu's primary use case is "what is the count of devices at site X grouped by
field Y?", and forcing the operator to step through 14 prompts would degrade
usability. A power user can pass these as Python kwargs by calling the method
from a script. A future spec (out of scope here) may add an "advanced filters"
sub-menu if real user feedback warrants it.

**Rationale**:
Three prompts keep the menu fast for the common case (count by model / by version
/ by hostname) while leaving room for the server default when the operator wants
a single total. The `limit` prompt matters because operators with thousands of
distinct device versions sometimes need to raise it explicitly.

**Alternatives Considered**:

1. *Prompt for all 14 optional query parameters.* Rejected -- adds 13 prompts that
   are almost never used and turns a 5-second menu into a 90-second interrogation.
2. *Prompt only for `site_id` and apply server defaults for everything else.*
   Rejected -- the `distinct` choice fundamentally changes the shape of the
   results array and is the single most useful tuning knob; surfacing it directly
   is worth one extra prompt.
3. *Read `distinct` from `.env`.* Rejected -- the choice varies per invocation
   (sometimes the operator wants `model`, sometimes `version`); an `.env` default
   would be wrong half the time. Interactive prompt is the right fit.
