# Phase 0 Research: getOrgStats

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-07-01

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_stats.md` (enriched
OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors
the OpenAPI URL: `mistapi.api.v1.orgs.stats.getOrgStats(apisession, org_id,
start=None, end=None, duration="1d", limit=100, page=1)`. The SDK returns a
`mistapi.APIResponse` object whose `.data` attribute is the parsed JSON body. The
body is a **single JSON object** (not a list) describing the org statistics
snapshot, with the following top-level keys per the doc:

- `id` (string UUID -- org UUID, required)
- `name` (string -- org name, required)
- `msp_id` (string UUID -- parent MSP if any, required, read-only)
- `alarmtemplate_id` (string UUID -- required)
- `allow_mist` (boolean -- required)
- `orggroup_ids` (array of UUID strings -- required)
- `session_expiry` (int64 seconds -- required)
- `num_sites` (int32 -- required)
- `num_inventory` (int32 -- required)
- `num_devices` (int32 -- required)
- `num_devices_connected` (int32 -- required)
- `num_devices_disconnected` (int32 -- required)
- `created_time` (number epoch seconds -- required, read-only)
- `modified_time` (number epoch seconds -- required, read-only)
- `sle` (array of objects with unique items: each `{path: string,
  user_minutes: {ok: number, total: number}}`, required)

Required path parameter: `org_id` (UUID string).
Optional query parameters: `start` (epoch or relative string), `end` (epoch or
relative), `duration` (string, default `1d`), `limit` (integer, default 100),
`page` (integer, default 1). Although the endpoint advertises pagination, the
200 response schema shows a single object body -- pagination parameters exist for
API-family consistency but do not fan out multiple pages in practice for this
path. MistHelper therefore passes at most `duration` (from user prompt) and does
not loop pages.

**Rationale**:
The enriched per-endpoint doc lists the SDK module as
`mistapi.api.v1.orgs.stats.getOrgStats()`, and adjacent stats endpoints under the
same URL path (`GET /orgs/{org_id}/stats/sites` ->
`mistapi.api.v1.orgs.stats.sites`, `GET /orgs/{org_id}/stats/devices` ->
`mistapi.api.v1.orgs.stats.devices`) confirm the mistapi SDK organizes modules by
URL path, not OpenAPI tag. Final verification happens at implementation time via
`python -c "from mistapi.api.v1.orgs import stats; help(stats.getOrgStats)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/stats`.* Rejected -- the constitution
   forbids direct HTTP when a mistapi method exists.
2. *Iterate `page=1..N` until an empty response.* Rejected -- the 200 schema is a
   single object body; there are no additional pages to fetch. Adding a page
   loop would waste API quota on identical responses.
3. *Always pass `duration=7d` for richer trend data.* Rejected -- the endpoint
   returns aggregated counts scoped by the requested window; a 1-day default
   matches other adjacent org-summary exports and keeps first-run cost small.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on two tables:

- `org_stats_summary`: PK = `(id, polled_at_utc)` -- one row per (org UUID,
  MistHelper poll timestamp). `id` is the org UUID returned in the response
  body; `polled_at_utc` is an ISO8601 UTC timestamp injected by MistHelper at
  write time (the API does not return a per-snapshot timestamp).
- `org_stats_sle`: PK = `(org_id, polled_at_utc, path)` -- one row per SLE path
  (`wifi`, `wan`, `wired`, etc.) inside the response `sle` array. Joins back to
  the summary row on `(org_id, polled_at_utc)`.

The existing entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` at `MistHelper.py:4331`
uses `auto_increment_with_unique` -- this feature **upgrades** it to
`composite_pk` so repeated polls upsert cleanly on the same day instead of
accumulating duplicate snapshots. A second MistHelper-internal key
`getOrgStatsSleRows` is added for the flattened SLE sub-table.

**Rationale**:
Org stats are inherently time-series: counts and health percentages drift over
time. Without a stable time key the choices are (a) `auto_increment` and accept
unbounded snapshot growth, or (b) `natural_pk` on `id` alone and lose historical
snapshots on each poll. Option (c), composite on `(id, polled_at_utc)`, preserves
history while giving `INSERT OR REPLACE` upsert semantics for polls that happen
inside the same minute (idempotent re-runs during debugging). The SLE array has
no stable unique identifier of its own; `path` is unique inside the array (the
schema declares `uniqueItems: true`), so `(org_id, polled_at_utc, path)` is the
natural composite for the child table.

**Alternatives Considered**:

1. *Keep the existing `auto_increment_with_unique`.* Rejected -- snapshots
   accumulate without deduplication, and the resulting table is only useful
   with an explicit `ORDER BY misthelper_internal_id DESC LIMIT 1` filter. The
   composite key is more self-documenting and enables clean upserts.
2. *`natural_pk` on `id` (org UUID) alone.* Rejected -- overwrites the prior
   snapshot on every poll, destroying the trending signal the endpoint exists to
   provide.
3. *Single flat table with SLE fields JSON-encoded into one column.* Rejected --
   breaks SQL queryability and conflicts with the flattening convention used
   everywhere else in MistHelper.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/org_<org_id_short>_stats_summary.csv`
- CSV (SLE): `data/org_<org_id_short>_stats_sle.csv`
- SQLite tables: `org_stats_summary` and `org_stats_sle`
- `org_id_short` is the first 8 hex characters of the org UUID -- matches the
  naming convention used by adjacent org exports in MistHelper (e.g. the license
  summary exports).

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"getOrgStats"` (matching the
operationId) for the summary write, and `"getOrgStatsSleRows"` (MistHelper-
internal key) for the SLE sub-table write.

**Rationale**:
Matches the two-table pattern used by other endpoints whose response contains a
top-level object plus a nested array (see the reference plan for
`getOrgLicenseAsyncClaimStatus`). Two output files / two SQLite tables keep the
schema clean and let a user query the org-level counts without joining when
per-SLE detail is not needed.

**Alternatives Considered**:

1. *Single flat table with SLE fields prefixed
   (`sle_wifi_ok`, `sle_wifi_total`, `sle_wan_ok`, ...).* Rejected -- the SLE
   path list is not fixed (new categories can appear), so a wide-column schema
   is brittle.
2. *Full org UUID in the filename.* Rejected -- leaks the org UUID into shell
   history and ls output. The short form is enough to disambiguate locally.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 58**, sitting inside the Safe Org
Exports cluster (1-59) adjacent to other org-level snapshot exports. The category
label is "Safe Org Exports -- Org Statistics".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges
as: 1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource
Intensive, 102-123 WebSocket, 124-152 Interactive, 154-194 Destructive. Org-level
statistics is a read-only summary that fits the Safe Org Exports intent
perfectly; 58 is the next uncontested integer inside that range that reads
naturally as a snapshot exporter. The number is provisional -- at
`/speckit.tasks` time, `MistHelper.py` is grep'd for the latest allocated menu
integer and 58 is shifted forward if a conflict exists.

**Alternatives Considered**:

1. *Slot inside Interactive Safe (60-96).* Rejected -- the menu item is fully
   automatable via `.env` defaults; interactive-prompt-heavy operations belong
   in that range.
2. *Slot inside Resource Intensive (97-101).* Rejected -- a single GET returning
   one JSON object is not resource intensive.
3. *Append past 194.* Rejected -- the destructive cluster ends at 194; placing a
   read-only snapshot export past the destructive block mis-signals risk to a
   junior NOC engineer scrolling the menu.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context: `"org_stats:org_id"`.
   Default: the value of `MIST_ORG_ID` in `.env` if present (pressing Enter
   accepts the default). Validated via the existing `is_valid_uuid()` helper
   before the API call; on failure, log `WARNING` and return early.
2. `duration` -- prompt: `"Stats window (e.g. 1d, 7d, 2w) [1d]: "`, context:
   `"org_stats:duration"`. Default: `1d` (the API default). Passed through
   verbatim to the SDK; the SDK / Mist API validate the format.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.

The `start`, `end`, `limit`, and `page` query parameters are **not** exposed to
the user in this menu item. `start`/`end` are covered by the simpler `duration`
window (the two are mutually exclusive at the API); `limit`/`page` are irrelevant
because the 200 response schema is a single object body.

**Rationale**:
The Mist org-stats endpoint is org-scoped; site, device, and template IDs are
not involved. Exposing `duration` as an optional prompt keeps the menu efficient
for the common daily-snapshot case while letting an operator widen the window
without editing code. Suppressing `start`/`end`/`limit`/`page` avoids overloading
the junior-NOC-friendly UI with API-mechanic detail.

**Alternatives Considered**:

1. *No prompts beyond `org_id` -- always use `duration=1d`.* Rejected -- the
   endpoint's `duration` parameter is a genuine operator concern (weekly rollups
   are common), and adding it later would require a menu redesign.
2. *Add prompts for `start` and `end` epochs.* Rejected -- epoch entry is
   error-prone for a NOC engineer; `duration=7d` accomplishes the same window
   more safely.
3. *Add a third prompt for an output filename override.* Rejected -- adds
   keystrokes without operational value. The deterministic filename scheme in
   Research Task 3 makes results easy to find under `data/`.
