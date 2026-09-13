# Phase 0 Research: countSiteDeviceLastConfig

This document captures the design decisions taken before Phase 1 artifacts are
written. Source of truth for the endpoint is
`documentation/api/sites/GET_sites_site_id_devices_last_config_count.md`.

## Research Task 1: SDK function signature & behavior

**Decision**: Invoke
`mistapi.api.v1.sites.devices.last_config.countSiteDeviceLastConfig(apisession, site_id, distinct=None, start=None, end=None, duration="1d", limit=100, page=None)`.
The wrapper used inside MistHelper passes the existing `mistapi.APISession`
created at startup. The MistHelper menu method calls the SDK exactly once per
invocation; pagination via `page` is only used if `total > limit`.

**Rationale**: The enriched documentation file at
`documentation/api/sites/GET_sites_site_id_devices_last_config_count.md` lists
the HTTP path as `GET /api/v1/sites/{site_id}/devices/last_config/count` with
one required path parameter (`site_id`) and five optional query parameters
(`distinct`, `start`, `end`, `duration` default `1d`, `limit` default `100`).
The 200 response is a single JSON object with keys `distinct`, `start`, `end`,
`limit`, `total`, and `results` -- an array of `{count, <distinct_value>}`
objects. The mistapi SDK function name documented in the same file is
`countSiteDeviceLastConfig` under `mistapi.api.v1.sites.devices.last_config`.
The doc explicitly says pagination is supported via `limit` and `page`, so
MistHelper checks `total` vs `limit` to decide whether further pages are
needed.

**Alternatives Considered**:
- Calling the lower-level `mistapi.APISession.mist_get()` directly: rejected --
  violates Principle II (class-based, no wrappers) and bypasses the typed SDK
  surface; also fails the constitution constraint that mistapi 0.59+ is the
  sole permitted interface.
- Building an asynchronous wrapper with `asyncio.gather()` for multi-site
  count fan-out: rejected for v1 -- the spec is one site per invocation, and
  multi-site fan-out is a separate future enhancement.

## Research Task 2: Primary Key Strategy

**Decision**: `composite_pk` with primary key
`['site_id', 'distinct', 'group_value', 'window_start', 'window_end']` for the
`site_device_last_config_count_results` table, and `composite_pk` with primary
key `['site_id', 'distinct', 'window_start', 'window_end']` for the
`site_device_last_config_count_summary` table.

**Rationale**: The response is a *count*, not an entity with a stable UUID,
so `natural_pk` does not apply. The same site can be queried repeatedly with
different `distinct` fields and different time windows; each combination is a
logically distinct record that must upsert (overwrite the prior count for that
exact combination) rather than accumulate duplicates. The four-tuple
(site_id, distinct, window_start, window_end) uniquely identifies one
summary record; the same tuple plus `group_value` uniquely identifies one
per-group result row. Because `window_start` and `window_end` are derived from
the request parameters (resolved from `duration` when only `duration` is
supplied), they are deterministic for the user's input and stable across runs.
`auto_increment_with_unique` was considered but rejected because it would
force callers to query by a synthetic ID and would lose the natural-key
upsert semantics that `INSERT OR REPLACE` provides.

**Alternatives Considered**:
- `natural_pk` keyed on a synthetic `result_id`: rejected -- no such field
  exists in the API response, and minting one client-side defeats Principle
  III (Safety-First) by hiding the user's actual filter scope.
- `auto_increment_with_unique`: rejected -- the count table is small and
  read-mostly; the upsert pattern of `composite_pk` aligns with the rest of
  the codebase (e.g. `searchOrgDeviceEvents`).

## Research Task 3: Output filename and SQLite table

**Decision**:
- CSV summary: `data/site_<site_id>_device_last_config_count_summary.csv`
- CSV results: `data/site_<site_id>_device_last_config_count_results.csv`
- SQLite tables: `site_device_last_config_count_summary` and
  `site_device_last_config_count_results`
- The mistapi `api_function_name` argument passed to
  `DataExporter.write_with_format_selection()` is
  `"countSiteDeviceLastConfig"`.

**Rationale**: MistHelper's naming convention is
`<scope>_<resource>_<operation>.csv`. The site_id is interpolated into the
filename so multiple sites can be exported without collision. SQLite table
names omit the site_id because the table holds rows for many sites at once
(the site_id is a primary-key column instead). The `_summary` / `_results`
suffix split mirrors the response object's two-level shape (one top-level
header row plus a `results` array). Naming aligns with the existing
`searchOrgDeviceEvents` and `getOrgLicensesSummary` precedents in the
codebase.

**Alternatives Considered**:
- One flattened table mixing the summary scalars with the `results` rows:
  rejected -- different cardinality (1 vs N), violates first normal form, and
  makes the SQLite primary key harder to define.
- JSON file output: rejected -- not consistent with multi-backend
  `DataExporter` contract, and the CSV/SQLite paths already serialize JSON
  blobs via the standard helpers.

## Research Task 4: Menu category placement and next available menu number

**Decision**: Place at menu number **72**, the next available slot at the
tail of the site-devices cluster (60-72) defined in
`.github/copilot-instructions.md`. Category: "Interactive Safe -- Site
Devices".

**Rationale**: The category table in `.github/copilot-instructions.md`
defines the 60-72 range as "Site devices" under "Interactive Safe". The
endpoint returns counts about device config history scoped to one site --
this is squarely a site-device read operation. 72 is the upper bound of that
cluster and the most natural next slot. The adjacent operations in 60-71 are
the site-device queries that share the same input pattern (prompt for
site_id, run a read-only query). Operations 73-79 are SLE/insight
operations on a different conceptual axis. Operations 80-91 are stats
endpoints. Placing this count operation with the other site-device queries
keeps related menu items together for the junior NOC operator.

**Alternatives Considered**:
- Menu number in the 80-91 stats range: rejected -- the endpoint is a config
  *history count*, not a real-time stat; semantically belongs with config
  queries.
- Menu number in the 73-79 insights range: rejected -- this is not an SLE
  metric; it is a config-history count.
- Reuse an existing menu slot via a sub-prompt: rejected -- violates the
  one-menu-item-per-operation pattern, which is non-negotiable for the
  junior NOC audience.

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

**Decision**: Prompts collected via `safe_input()`:

1. `site_id` -- required, prompted with default from `MIST_DEFAULT_SITE_ID`
   in `.env` if present; otherwise the user types it. Context string:
   `"count_last_config:site_id"`.
2. `distinct` -- optional, prompted with empty default. Common values
   (`hostname`, `version`, `device_type`) are listed in the prompt text.
   Context string: `"count_last_config:distinct"`.
3. `duration` -- optional, prompted with default `"1d"`. Format `Nd`/`Nw`/`Nh`
   accepted. Context string: `"count_last_config:duration"`.
4. `limit` -- optional, prompted with default `100`. Clamped to `[1, 1000]`
   before the SDK call. Context string: `"count_last_config:limit"`.

The org_id and `MIST_API_TOKEN` come from `.env` via the existing
`mistapi.APISession` and are never prompted. `start` and `end` are not
prompted directly in v1; they are computed from `duration` by the SDK. If a
power user needs absolute epoch bounds, they can edit the call interactively
in a future enhancement -- out of scope here.

**Rationale**: The endpoint requires only `site_id` per the OpenAPI
specification. All other parameters have safe defaults. Asking for absolute
`start`/`end` epoch seconds is unfriendly to the junior NOC audience;
`duration` covers the same need with friendlier syntax. `limit` is exposed
because the response can grow when `distinct` is set to a high-cardinality
field. `safe_input()` with explicit `context=` strings preserves the
project's SSH/container EOF safety guarantee.

**Alternatives Considered**:
- Prompting for raw epoch `start` and `end`: rejected -- error-prone for
  junior operators; `duration` is the documented friendly form.
- Hard-coding `distinct="hostname"`: rejected -- removes a useful axis of
  the endpoint without operator override.
- Skipping the `limit` prompt and always using `1000`: rejected -- can
  surprise the operator with large CSV exports; explicit prompt with default
  100 matches the API default.
