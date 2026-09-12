# Phase 0 Research: countOrgMxEdges

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_mxedges_count.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that
mirrors the OpenAPI URL: `mistapi.api.v1.orgs.mxedges.count.countOrgMxEdges(
apisession, org_id, distinct=None, mxedge_id=None, site_id=None,
mxcluster_id=None, model=None, distro=None, tunterm_version=None,
sort=None, stats=None, start=None, end=None, duration="1d", limit=100,
page=1)`. The SDK returns a `mistapi.APIResponse` object whose `.data`
attribute is the parsed JSON body. The body is a single JSON object with the
following keys per the enriched doc:

- `distinct` (string -- echoes back the field that was grouped on)
- `start`, `end` (int32 epoch seconds -- the resolved time window)
- `limit` (int32 -- echoes the request limit)
- `total` (int32 -- total number of distinct values across all pages)
- `results` (array of objects: each has a required `count` int plus one
  additional string property whose key equals the `distinct` field name and
  whose value is the grouping value, e.g. `{"model": "ME-X1", "count": 12}`)

Required path parameter: `org_id` (UUID string).
Optional query parameters: `distinct` (string, controls grouping field),
`mxedge_id`, `site_id`, `mxcluster_id`, `model`, `distro`, `tunterm_version`
(string filters), `sort` (string), `stats` (boolean), `start`/`end` (epoch
or relative), `duration` (default `1d`), `limit` (default `100`).

**Rationale**:
The enriched doc explicitly lists the SDK as
`mistapi.api.v1.orgs.mxedges.countOrgMxEdges()` and the operationId is
`countOrgMxEdges` from the `Orgs MxEdges` tag. The OpenAPI URL maps one-for-
one to `mistapi.api.v1.orgs.mxedges.count` under the `mxedges` package,
consistent with adjacent `count` endpoints in the same SDK (e.g.
`mistapi.api.v1.orgs.devices.count.countOrgDevices`). Final verification
happens at implementation time via
`python -c "from mistapi.api.v1.orgs.mxedges import count; help(count)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/orgs/{org_id}/mxedges/count`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method
   exists.
2. *Use `mistapi.api.v1.orgs.mxedges.listOrgMxEdges` and aggregate client-
   side.* Rejected -- defeats the purpose of the dedicated count endpoint,
   wastes API quota on full payloads, and produces inconsistent totals when
   pagination is involved.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on two separate output tables:

- `org_mxedge_count_summary`: PK = `(org_id, distinct, start, end)` -- one
  row per (org, grouping field, time window). Echoes the API response's
  top-level `distinct`, `start`, `end`, `limit`, and `total` fields.
- `org_mxedge_count_results`: PK = `(org_id, distinct, start, end,
  distinct_value)` -- one row per grouping bucket returned in `results`.
  `distinct_value` holds the per-row grouping key (e.g. the actual model
  name when `distinct=model`).

Both entries are registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` with type
`composite_pk`. MistHelper injects `org_id`, `distinct`, `start`, and `end`
before the upsert (the API does not return `org_id` in the body but
MistHelper always knows the targeted org and the requested grouping field).

**Rationale**:
The endpoint reports the *current* aggregate state of Mist Edges for a given
distinct grouping and time window. Re-running the menu item with the same
inputs must update the existing rows rather than append duplicates.
`(org_id, distinct, start, end)` is the natural composite key for a summary
snapshot, and adding `distinct_value` extends it for the per-bucket detail.
`INSERT OR REPLACE` upserts every poll's view cleanly.

**Alternatives Considered**:

1. *`auto_increment_with_unique`.* Rejected -- repeated polls would
   accumulate duplicate snapshots, defeating the upsert behavior the spec
   requires for SQLite.
2. *Single combined table with the `distinct_value` joined as a column on
   the summary.* Rejected -- when `distinct` is omitted the API may return a
   single aggregate row with no distinct value, so a combined design forces
   nullable PK columns. Splitting into summary and results tables handles
   both shapes cleanly.
3. *`natural_pk` on the API-returned `total` or `timestamp` alone.*
   Rejected -- the response carries no globally unique identifier; without
   `(org_id, distinct, start, end)` the row cannot be matched back to its
   original query.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/org_<org_id_short>_mxedge_count_<distinct>_summary.csv`
- CSV (results): `data/org_<org_id_short>_mxedge_count_<distinct>_results.csv`
- SQLite tables: `org_mxedge_count_summary` and `org_mxedge_count_results`
- `org_id_short` is the first 8 hex characters of the org UUID -- existing
  convention used by adjacent org-mxedges exports for human-readable
  filenames without leaking full UUIDs into shell history.
- `<distinct>` is the validated grouping field name (lowercased,
  non-alphanumerics stripped); when the user omits `distinct`, the literal
  string `all` is substituted so files remain easy to find on disk.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"countOrgMxEdges"`
(matching the operationId) for the summary write and
`"countOrgMxEdgesResults"` for the per-bucket detail write. The
DataExporter uses these strings as the lookup key into
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by `listOrgMxEdges` and `searchOrgMxEdges`
(the two adjacent Mist Edge org exports). Two output files / two SQLite
tables keep the schema clean and let a user query bucket counts without
joining when they don't need the summary metadata.

**Alternatives Considered**:

1. *Single output file with JSON-encoded `results` column.* Rejected --
   breaks SQL queryability and conflicts with the flattening convention
   used everywhere else in MistHelper.
2. *Full org UUID in the filename.* Rejected -- leaks the org UUID into
   shell history and ls output unnecessarily.
3. *Omit `<distinct>` from the filename and rely on the latest write
   overwriting prior runs.* Rejected -- the user often pivots `distinct`
   across runs to compare groupings; embedding the grouping in the filename
   preserves each pivot side by side under `data/`.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 96**, sitting at the boundary
between the Safe Org Exports / Interactive Safe cluster (1-95) and the
Resource Intensive cluster (97-101, 153). Category label: "Safe Org Exports
-- Mist Edges". The proposed number is provisional and is re-verified at
`/speckit.tasks` time against the latest allocated menu integer in
`MistHelper.py`; if 96 is already taken or has been re-zoned into the
resource-intensive block, the next free integer in the safe cluster is used
(falling back to a slot inside 56-94 or shifting forward to 97 only if 97
remains administratively safe).

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu
ranges as: 1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153
Resource Intensive, 102-123 WebSocket, 124-152 Interactive, 154-194
Destructive. The `count` endpoint is a single GET that returns a small JSON
object (no large payloads, no destructive effect), so it belongs in the
safe range. 96 is the highest slot in the Interactive Safe cluster and
directly adjacent to the other org-level Mist Edge inventory operations.

**Alternatives Considered**:

1. *Append to the end (e.g., 195).* Rejected -- the destructive cluster
   ends at 194, and placing a read-only count above the destructive block
   visually mis-signals the risk level to a junior NOC engineer scrolling
   the menu.
2. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is
   a single GET returning a small aggregate JSON object with no
   long-running work. It belongs in the safe block.
3. *Reuse an existing Mist Edge menu number and add a sub-prompt for
   "count vs list".* Rejected -- breaks the one-operationId-per-menu-item
   convention and complicates the automated `--test` sweep.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **two required values** and accepts
**one optional override** via `safe_input()`:

1. `org_id` (required) -- prompt: `"Org ID (UUID): "`, context:
   `"org_mxedge_count:org_id"`. Default: the value of `MIST_ORG_ID` in
   `.env` if present (pressing Enter accepts the default). Validated via
   the existing `is_valid_uuid()` helper before the API call; on failure,
   log `WARNING` and return early.
2. `distinct` (required) -- prompt: `"Distinct field to group by [model]: "`,
   context: `"org_mxedge_count:distinct"`. Default: `model`. Validated
   against the allow-list `{mxedge_id, site_id, mxcluster_id, model,
   distro, tunterm_version}` derived from the OpenAPI query parameter
   list; on failure, log `WARNING` listing the valid choices and return
   early.
3. `duration` (optional) -- prompt: `"Duration [1d]: "`, context:
   `"org_mxedge_count:duration"`. Default: `1d` (matches the API default).
   Pressing Enter accepts the default; advanced users may supply `7d`,
   `2w`, etc. Other time-window parameters (`start`, `end`) are left at
   API defaults to keep the menu simple; power users can override via
   `--menu 96 --duration 7d` once direct-invocation flag support is wired
   in a follow-up spec.

`.env` values used (loaded via the existing `python-dotenv` bootstrap,
never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.

**Rationale**:
The endpoint is org-scoped, so site/device/template IDs are not in scope.
The `distinct` parameter is the single most important knob -- it controls
the entire response shape -- so it warrants an explicit prompt with a sane
default (`model` is the most common Mist Edge inventory pivot). All other
query parameters either have safe defaults (`limit=100`, `duration=1d`) or
are advanced filters that rarely change between routine NOC operations.

**Alternatives Considered**:

1. *Prompt for every optional query parameter.* Rejected -- explodes the
   prompt count to 13 and overwhelms a junior NOC engineer. Defaults
   match upstream API defaults.
2. *Skip the `distinct` prompt and always group by `model`.* Rejected --
   the endpoint's whole purpose is flexible grouping; hard-coding the
   grouping would force a code change every time the user wants a different
   pivot.
3. *Read the entire query parameter set from a JSON sidecar file.*
   Rejected -- adds a new file format and parsing surface for what is
   currently a two-prompt operation. Revisit if/when the spec grows.
