# Phase 0 -- Research: countOrgDeviceLastConfigs

All five research tasks for the
`/api/v1/orgs/{org_id}/devices/last_config/count` GET endpoint, resolved with
explicit Decision / Rationale / Alternatives blocks. No `NEEDS CLARIFICATION`
markers remain.

Primary source for every decision below:
`documentation/api/orgs/GET_orgs_org_id_devices_last_config_count.md`.

---

## Research Task 1 -- SDK Function Signature & Behavior

**Decision**: Call
`mistapi.api.v1.orgs.devices.last_config.count.countOrgDeviceLastConfigs(mist_session, org_id, type=None, distinct=None, start=None, end=None, duration="1d", limit=100, page=1)`.
Treat it as a single-shot call (no SDK pagination loop) that returns a
response object whose `.data` is `{"distinct", "end", "limit", "results":
[...], "start", "total"}`.

**Rationale**:

- The enriched endpoint doc lists exactly one path parameter (`org_id`) and
  the query parameters `type`, `distinct`, `start`, `end`,
  `duration` (default `1d`), `limit` (default `100`).
- The response schema's `required` list is `["distinct", "end", "limit",
  "results", "start", "total"]`, confirming `results` is always present and
  is an array of `{count, <field>: <string>}` objects.
- The endpoint says "Supports pagination. Use `limit` and `page` query
  parameters." Single-page handling is sufficient because the response also
  reports `total`; a follow-up loop is only needed if `total > limit`. Coded
  defensively with a `while page * limit < total` loop using
  `MIST_PAGE_LIMIT` (default 1000) instead of the API's default 100.
- The mistapi SDK module path was confirmed from the doc's "mistapi SDK"
  section (`mistapi.api.v1.orgs.devices.countOrgDeviceLastConfigs()` -- the
  documented surface; spec.md uses the deeper module path
  `mistapi.api.v1.orgs.devices.last_config.count.countOrgDeviceLastConfigs`
  which is the actual source location). Both resolve to the same callable.

**Alternatives Considered**:

- *Embed in Menu 14 as a "summary mode" flag*: rejected -- violates
  single-responsibility and complicates the existing handler.
- *Use raw HTTP via `requests` instead of mistapi*: rejected -- bypasses
  rate-limit/auth helpers and contradicts FR-001.
- *Server-side pagination via the `page` parameter*: deferred -- response
  carries `total`, so a one-shot call with `limit=MIST_PAGE_LIMIT` is enough
  for the typical fleet size; a paging loop is included as a safety net.

---

## Research Task 2 -- Primary Key Strategy

**Decision**: `auto_increment_with_unique` with internal PK
`misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT` and unique
constraint `UNIQUE(org_id, distinct, start, end, group_field, group_value)`.

**Rationale**:

- The response is an aggregation snapshot. The Mist API returns neither a
  UUID nor a timestamp suitable for use as a natural key on each
  `results[]` row -- each row is `{count, <distinct-field-name>: <value>}`.
- Composite PK is unattractive because the discriminator field name changes
  with the `distinct` query parameter (e.g., `model`, `version`, `mxedge_id`,
  `site_id`), so no fixed column set exists across all calls.
- Auto-increment with a unique tuple gives idempotent upserts (`INSERT OR
  REPLACE`) when the same (org, distinct, time window) is recomputed without
  duplicating rows, while still letting SQLite assign a stable internal ID.
- This matches the pattern used by `getOrgLicensesSummary` and other
  aggregation endpoints documented in `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Alternatives Considered**:

- *`natural_pk`*: rejected -- no stable API-provided ID per row.
- *`composite_pk` on `(org_id, distinct, group_value)`*: rejected -- the
  group field name is variable; two calls with different `distinct` would
  collide on the same `group_value` string.
- *No persistence at all (CSV only)*: rejected -- breaks Constitution
  principle III (multi-backend exporter must support SQLite + polyglot).

---

## Research Task 3 -- Output Filename and SQLite Table

**Decision**:

- CSV filename: `countOrgDeviceLastConfigs_<org_id>_<UTC_YYYYMMDD_HHMMSS>.csv`
  under `data/`.
- SQLite table name: `count_org_device_last_configs`.
- ArangoDB collection (polyglot mode): `count_org_device_last_configs`.

**Rationale**:

- Filename pattern follows the existing MistHelper convention
  (`<operationId>_<scope-id>_<timestamp>.csv`) so directory listings sort
  chronologically per operation per org.
- Snake-cased table name converted from camelCase operationId matches the
  in-repo convention (`get_org_licenses_summary`, `search_org_devices`).
- Single table is sufficient -- the response is flat once each `results[]`
  row is exploded to columns `[org_id, distinct, start, end, group_field,
  group_value, count]`.

**Alternatives Considered**:

- *Use the API operationId verbatim as table name (`countOrgDeviceLastConfigs`)*:
  rejected -- existing schema uses snake_case for SQL identifiers.
- *One table per `distinct` field*: rejected -- explodes schema, breaks
  uniform query patterns.

---

## Research Task 4 -- Menu Category Placement and Next Available Number

**Decision**: Append as **Menu 195**, label
`"Org -- Count device last-config history (aggregated)"`, category
`"Safe Org Exports"`.

**Rationale**:

- The repo currently spans Menus 1-194 (per `copilot-instructions.md` menu
  table). 195 is the next free integer and avoids renumbering existing
  destructive operations (154-194), which would break user-facing
  documentation, automation scripts, and `--menu N` invocations.
- The endpoint is read-only and org-scoped, so it logically belongs alongside
  Menu 14 (`searchOrgDeviceLastConfigs`) in the "Safe Org Exports" band, but
  inserting at 15 would shift every subsequent menu by one. Appending at the
  tail preserves backward compatibility.
- A future renumbering pass (out of scope here) can move it next to Menu 14
  if desired; until then, the README's menu table will list 195 in the same
  "Safe Org Exports" section.

**Alternatives Considered**:

- *Insert at 15, renumber 15-194*: rejected -- breaks all existing
  `--menu N` automation and SSH-runner scripts.
- *Insert at 59 (last safe-org-export slot)*: rejected -- 59 is already
  taken; would still cause renumbering.
- *Slot under "Insights" (73-79)*: rejected -- this is a count aggregation,
  not a Marvis/SLE insight.

---

## Research Task 5 -- Required User Prompts

**Decision**:

| Prompt | Source | safe_input context | Default | Validation |
|--------|--------|--------------------|---------|------------|
| `org_id` | `.env` `MIST_ORG_ID` first; prompt only if blank | `count_org_device_last_configs_org_id` | -- | non-empty UUID |
| `distinct` field (`model` / `version` / `mxedge_id` / `site_id` / etc.) | `safe_input` with default `"model"` | `count_org_device_last_configs_distinct` | `model` | non-empty string |
| `type` filter (optional, blank = all) | `safe_input` (optional) | `count_org_device_last_configs_type` | `""` | optional string |
| `duration` window | `safe_input` with default `"1d"` | `count_org_device_last_configs_duration` | `1d` | matches `^\d+[hdwmy]$` |
| Output backend (CSV / SQLite / both) | Existing `DataExporter.write_with_format_selection` prompt | (handled internally) | per `.env` `MIST_DEFAULT_OUTPUT` | -- |

**Rationale**:

- `MIST_ORG_ID` is already a documented `.env` variable; reusing it matches
  every other org-scoped menu method.
- `distinct` is the only required user choice that changes the result shape,
  so it must be prompted.
- `start` / `end` are not prompted -- the API accepts `duration` as a
  friendlier alternative; advanced users can still set them via a future
  `--start` / `--end` CLI flag.
- All prompts go through `safe_input(...)` per Constitution principle I --
  zero raw `input()` calls.

**Alternatives Considered**:

- *Prompt for every query parameter unconditionally*: rejected -- creates UX
  drag for the common case (count distinct models over last 24 h).
- *Pull `distinct` from `.env`*: rejected -- it is a per-invocation choice,
  not a deployment setting.
- *Skip prompts entirely and require CLI flags*: rejected -- breaks the
  interactive menu UX that NOC engineers rely on.
