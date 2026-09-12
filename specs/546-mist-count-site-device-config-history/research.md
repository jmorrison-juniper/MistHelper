# Phase 0 Research: countSiteDeviceConfigHistory

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/sites/GET_sites_site_id_devices_config_history_count.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK using the canonical URL-based module
path:

```python
mistapi.api.v1.sites.devices.config_history.count.countSiteDeviceConfigHistory(
    apisession,
    site_id,
    distinct=None,
    mac=None,
    start=None,
    end=None,
    duration="1d",
    limit=100,
)
```

The SDK returns a `mistapi.APIResponse` whose `.data` attribute is the parsed
JSON body. Per the enriched doc, the 200 OK body is a single JSON object with
the following top-level keys (all required by schema):

- `distinct` (string) -- echo of the requested distinct field.
- `start` (int32 epoch seconds) -- echo of the resolved window start.
- `end` (int32 epoch seconds) -- echo of the resolved window end.
- `limit` (int32) -- echo of the page size (default 100 from the API).
- `total` (int32) -- total distinct values matched (may exceed `limit`).
- `results` (array, uniqueItems=true) -- aggregated buckets. Each item has a
  required `count` (int32) plus arbitrary additional string-valued properties
  corresponding to the distinct field requested (e.g., when `distinct=mac`
  each item is `{"mac": "aabbcc...", "count": 42}`).

Required path parameter: `site_id` (UUID string).
Optional query parameters: `distinct`, `mac`, `start`, `end`, `duration`,
`limit`.

**Rationale**:
The OpenAPI URL is `/api/v1/sites/{site_id}/devices/config_history/count` and
mistapi historically derives module paths directly from URL segments (verified
by inspecting adjacent SDK modules under `mistapi.api.v1.sites.devices.*`).
The spec.md (the authoritative feature contract) names
`mistapi.api.v1.sites.devices.config_history.count` and that matches the URL
one-for-one, so the plan follows the spec. The enriched per-endpoint doc lists
the SDK as `mistapi.api.v1.sites.devices.countSiteDeviceConfigHistory()` (a
flat name under the `devices` module); this is a common mistapi shorthand for
count/search endpoints where the leaf URL segment is collapsed into the
function name. Final verification happens at implementation time via:

```powershell
python -c "import mistapi; help(mistapi.api.v1.sites.devices.config_history.count.countSiteDeviceConfigHistory)"
```

If the shorthand form is the only one installed in the user's `mistapi`
version, the implementation falls back to
`mistapi.api.v1.sites.devices.countSiteDeviceConfigHistory(apisession, ...)`
with no behavioral difference.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/sites/{site_id}/devices/config_history/count`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method
   exists.
2. *Treat the response as a list and skip the summary row.* Rejected -- the
   schema explicitly requires `distinct`, `start`, `end`, `limit`, `total`
   on the top-level object. Discarding them loses the user-visible context
   for the aggregation (which distinct field was used, which time window).

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on two separate output tables:

- `site_device_config_history_count_summary`: PK =
  `(site_id, distinct_field, window_start, window_end, polled_at_utc)`. One
  row per (site, query parameters, poll moment). The poll timestamp is part
  of the PK so a user can run the same count repeatedly to capture history.
- `site_device_config_history_count_results`: PK =
  `(site_id, distinct_field, distinct_value, window_start, window_end, polled_at_utc)`.
  One row per aggregated bucket. `distinct_value` is the string value of the
  requested distinct field (e.g., a MAC address when `distinct=mac`).

Both entries in `ENDPOINT_PRIMARY_KEY_STRATEGIES` use `type='composite_pk'`.
`site_id`, `polled_at_utc`, `window_start`, and `window_end` are injected by
MistHelper before the upsert (the API does not return `site_id` in the body,
and `polled_at_utc` is the local poll clock).

**Rationale**:
The endpoint is a *count* (aggregation), so the response is sensitive to
which filters were applied. Two runs with different `distinct` or different
time windows produce semantically different results that must coexist. Two
runs with identical parameters at different times still differ -- the
underlying config history grows -- so the snapshot timestamp must be part of
the PK to preserve history. Splitting summary from results keeps the
flattened CSV/SQLite schema clean: the summary row holds query metadata
(distinct, window, total, limit), and the results rows hold the actual
aggregation values, joined back through the composite key.

**Alternatives Considered**:

1. *`auto_increment_with_unique`.* Rejected -- count endpoints are run
   repeatedly for trending; without a stable PK on `(site, params, time)`
   the upsert semantic loses meaning and the rows table grows without a
   natural way to find the latest snapshot.
2. *`natural_pk` on `(distinct, distinct_value)` alone.* Rejected -- the
   same site can be polled with different windows on the same day; ignoring
   `polled_at_utc` would overwrite the morning poll with the afternoon poll
   silently.
3. *Single combined table with all summary fields plus a JSON-encoded
   `results` column.* Rejected -- breaks SQL queryability and conflicts with
   the flattening convention used elsewhere in MistHelper.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/site_<site_id_short>_config_history_count_summary.csv`
- CSV (results): `data/site_<site_id_short>_config_history_count_results.csv`
- SQLite tables: `site_device_config_history_count_summary` and
  `site_device_config_history_count_results`
- `site_id_short` is the first 8 hex characters of the site UUID -- the
  convention used by adjacent site exports in `MistHelper.py` for
  human-readable filenames without leaking full UUIDs into shell history.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is
`"countSiteDeviceConfigHistory"` for the summary write and the
MistHelper-internal sub-table key `"countSiteDeviceConfigHistoryResults"` for
the results write. DataExporter uses these strings as the lookup keys into
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by adjacent site-devices exports (operations
60-72). Two output files / two SQLite tables keep the schema clean and let a
user query the summary without joining when they only need the total / total
distinct count.

**Alternatives Considered**:

1. *Single output file with JSON-encoded `results` column.* Rejected --
   breaks SQL queryability.
2. *Full site UUID in the filename.* Rejected -- leaks UUID into shell
   history. The short form is enough to disambiguate locally.
3. *Drop the `site_<>_` prefix and use a global filename.* Rejected -- a
   user who polls multiple sites would silently overwrite the CSV.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 73**, sitting at the top of the
Insights cluster (73-79) immediately adjacent to the Site Devices cluster
(60-72). Category label: "Interactive Safe -- Site Insights".

**Rationale**:
The menu ranges documented in `.github/copilot-instructions.md` are:

- 1-59 Safe Org Exports
- 60-96 Interactive Safe (Site devices 60-72, Insights 73-79, Stats 80-91,
  Viewers 92-96)
- 97-101, 153 Resource Intensive
- 102-123 WebSocket
- 124-152 Interactive
- 154-194 Destructive

A *count* of device config history is operationally an insight (aggregated
analytics over time-series device records), so it belongs in 73-79 rather
than 60-72 (which are concrete device list/read operations). Position 73 is
the first slot in the Insights cluster and is directly adjacent to the
site-devices block, making it the most discoverable position for a junior
NOC engineer who just learned to list config history and now wants to count
it. The number is provisional -- at `/speckit.tasks` time, `MistHelper.py` is
grep'd for the latest allocated menu integer and 73 is shifted forward if a
conflict exists.

**Alternatives Considered**:

1. *Slot inside Site Devices (60-72).* Rejected -- 60-72 are concrete record
   reads (list, get, search). A count aggregation is a different operational
   shape and belongs with the Insights cluster.
2. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint
   returns a small aggregation payload bounded by `limit` (default 100). No
   pagination, no long-running work.
3. *Append to the end of the menu (e.g., 195).* Rejected -- the destructive
   cluster ends at 194 and placing a read-only count above the destructive
   block visually mis-signals risk level.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for the following values via
`safe_input()`. All prompts honor a `.env` default where applicable; pressing
Enter accepts the default.

1. `site_id` -- prompt: `"Site ID (UUID): "`, context:
   `"site_device_config_history_count:site_id"`. Default: the value of
   `MIST_SITE_ID` in `.env` if present. Validated via the existing
   `is_valid_uuid()` helper before the API call; on failure, log `WARNING`
   and return early.
2. `distinct` -- prompt:
   `"Distinct field to group by [mac]: "`, context:
   `"site_device_config_history_count:distinct"`. Default: `mac` (the most
   common grouping for config history). Allowed values are validated
   loosely (non-empty string) -- the Mist API rejects unknown distinct
   fields with HTTP 400, which is logged as a warning.
3. `mac` (optional filter) -- prompt:
   `"Filter to a specific device MAC (blank for all): "`, context:
   `"site_device_config_history_count:mac"`. Default: empty -- omit the
   `mac` query parameter.
4. `duration` -- prompt:
   `"Time window duration [1d]: "`, context:
   `"site_device_config_history_count:duration"`. Default: `1d` (matches the
   Mist API default). Accepts strings like `7d`, `2w`.
5. `limit` -- prompt: `"Result limit [100]: "`, context:
   `"site_device_config_history_count:limit"`. Default: `100` (the Mist API
   default). Coerced via `int(...)`; on `ValueError` log `WARNING` and use
   the default.

`start` and `end` are intentionally not prompted in v1 of this menu item to
keep the prompt count tight; users who need explicit start/end can extend
the method via the existing pattern in adjacent exports. Adding the prompts
later is a non-breaking change.

`.env` values used (loaded via the existing `python-dotenv` bootstrap and
never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_SITE_ID` -- optional default for prompt 1.

**Rationale**:
The endpoint is site-scoped, so `site_id` is mandatory. `distinct` is the
key knob that changes the response shape -- without it the API still returns
a count, but the grouping defaults are not useful for a NOC engineer
investigating per-device churn. `duration` and `limit` are documented Mist
API parameters with well-defined defaults, and exposing them lets the user
trade off coverage versus speed without editing code. The five prompts fit
within the 5-Item Rule for method parameters (`self`, `site_id`, `distinct`,
`time_window`, `limit`) when the method is invoked programmatically; `mac`
is a single optional field on a small dataclass-like local dict.

**Alternatives Considered**:

1. *Prompt for every query parameter every time.* Rejected -- six prompts
   for a single count makes the menu painful, especially on SSH where
   typing is slow. Defaults plus the two most-changed knobs is the right
   trade.
2. *Hardcode `distinct=mac` and remove the prompt.* Rejected -- the API
   supports grouping by other fields, and removing the prompt costs nothing
   yet preserves future usefulness.
3. *Read every prompt value from `.env`.* Rejected -- `.env` is for
   credentials and stable identifiers, not per-run query knobs.
