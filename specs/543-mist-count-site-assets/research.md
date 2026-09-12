# Phase 0 Research: countSiteAssets

This document captures the five Phase 0 research questions for the new
`countSiteAssets` menu item. Each task records a Decision, Rationale, and
Alternatives Considered.

## Research Task 1: SDK Function Signature and Behavior

**Decision**: Use the `mistapi` SDK call
`mistapi.api.v1.sites.stats_-_assets.countSiteAssets(apisession, site_id,
distinct=None, limit=100, page=1)`. The endpoint is a HTTP `GET` against
`/api/v1/sites/{site_id}/stats/assets/count` and returns a JSON object with
fields `distinct`, `start`, `end`, `limit`, `total`, and `results` (an array
of `{count: int, <distinct-key>: str}` objects).

**Rationale**: Grounded in the enriched per-endpoint documentation at
`documentation/api/sites/GET_sites_site_id_stats_assets_count.md`, which shows
the full 200 response schema. The endpoint accepts two query parameters
(`distinct`, `limit`) and no request body. The SDK module path
(`mistapi.api.v1.sites.stats_-_assets`) follows Thomas Munzer's mistapi
convention -- the dash-tag `Sites Stats - Assets` is converted to `stats_-_assets`
as the Python submodule name. The function returns a `mistapi.APIResponse`
object whose `.data` attribute holds the parsed JSON envelope.

**Alternatives Considered**:

- Direct `requests.get` against the Mist host: rejected -- the constitution
  mandates `mistapi` as the sole interface.
- Calling `searchSiteAssets` and counting locally: rejected -- defeats the
  purpose of the distinct-count endpoint and is inefficient at scale.

## Research Task 2: Primary Key Strategy

**Decision**: Use `composite_pk` for the per-bucket `results` rows with primary
key `[site_id, distinct, bucket_value]`. The single-row summary envelope uses
`auto_increment_with_unique` with a unique index on `[site_id, distinct,
captured_at]` so repeated identical runs collapse to one row while different
distinct attributes coexist.

**Rationale**: The endpoint returns no stable UUID for the result rows -- each
bucket is identified only by its distinct attribute value (for example, a
floor name or asset class) plus the count. Two calls with the same
`site_id` + `distinct` value produce the same logical buckets, so a composite
PK on those three columns is correct. The summary envelope (`total`, `limit`,
`start`, `end`) has no natural key; an internal autoincrement with a unique
business constraint on `(site_id, distinct, captured_at)` lets the SQLite
upsert behave correctly without producing duplicates on a re-run of the same
distinct value within the same minute window.

**Alternatives Considered**:

- `natural_pk` on results: rejected -- there is no API-provided UUID; the
  bucket key is the distinct attribute value, which can be empty for the
  default summarization, breaking PK uniqueness.
- Skipping PK registration and relying on append-only writes: rejected --
  violates the project convention that every operationId is registered in
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` so SQLite upsert is deterministic.

## Research Task 3: Output Filename and SQLite Table

**Decision**:

- Summary CSV / SQLite table: `site_assets_count_summary`
  (file `data/site_assets_count_summary.csv`).
- Per-bucket CSV / SQLite table: `site_assets_count_results`
  (file `data/site_assets_count_results.csv`).

Both feed through `DataExporter.write_with_format_selection(data, filename,
api_function_name="countSiteAssets")` so CSV / SQLite / ArangoDB+Redis all
receive the right shape.

**Rationale**: Two logical entities (envelope vs results array) map to two
tables. Names mirror the operationId in lowercase snake_case with the
`site_` prefix that matches sibling site-stats exports in MistHelper, keeping
discovery predictable for NOC engineers. Splitting into two files keeps each
CSV flat -- no nested JSON columns -- which matches existing project style.

**Alternatives Considered**:

- A single denormalized table repeating envelope fields on every results row:
  rejected -- it duplicates `total`, `limit`, `start`, `end` N times and
  breaks the project convention of one entity per table.
- Naming the file `count_site_assets.csv` to mirror the operationId
  verbatim: rejected -- existing site-stats exports use `site_*` prefix
  (`site_assets`, `site_devices`, etc.); the new name follows that pattern.

## Research Task 4: Menu Category and Number

**Decision**: Place the new operation in the **Safe Site Stats / Interactive
Safe** category at menu number **95**.

**Rationale**: Operations 80-95 in the established menu taxonomy cover Site
Stats and similar safe, interactive site-scoped read operations. Operation 95
is the next available slot below the resource-intensive block at 96-101.
The new item is read-only, prompts the user for `site_id`, and produces
bounded output -- exactly the profile of the 80-95 range. The full menu list
is re-verified at task generation time; if 95 collides with another
in-flight feature branch, the next free integer in the same cluster is used.

**Alternatives Considered**:

- Placing in 1-59 (Safe Org Exports): rejected -- this is site-scoped, not
  org-scoped.
- Placing in 60-72 (Safe Site Devices): rejected -- this is a stats endpoint,
  not a device-config endpoint.
- Placing in 154-194 (Destructive): rejected -- the endpoint is HTTP GET only.

## Research Task 5: User Prompts (UI vs .env)

**Decision**:

| Input | Source | Notes |
|-------|--------|-------|
| `MIST_HOST` | `.env` | Loaded by existing `mistapi.APISession` bootstrap. Never prompted. |
| `MIST_API_TOKEN` | `.env` | Loaded by existing `mistapi.APISession` bootstrap. Never prompted. |
| `org_id` | `.env` (default) | Read from `MIST_ORG_ID`; user only re-prompted if missing. |
| `site_id` | User prompt | `safe_input("Site ID (UUID): ", context="site_assets_count:site_id")`. Required. UUID-shape validated; on failure log warning and return. |
| `distinct` | User prompt | `safe_input("Distinct attribute (default: map_id): ", context="site_assets_count:distinct")`. Optional; empty string -> use SDK default. Accepted values documented in the contract file. |
| `limit` | User prompt | `safe_input("Limit (default 100, max 1000): ", context="site_assets_count:limit")`. Optional; empty -> 100. Validated as int in `[1, 1000]`. |

**Rationale**: Site identifiers cannot be safely defaulted from `.env` because
an org typically has many sites and the user must choose. Secrets stay in
`.env` per the constitution Security principle. `distinct` and `limit` are
optional and benefit from sensible defaults so junior NOC engineers can run
the menu item with no Mist API knowledge. All prompts route through
`safe_input()` so SSH / container EOF exits cleanly per Principle III.

**Alternatives Considered**:

- Prompting for `org_id` and `MIST_HOST`: rejected -- they live in `.env` for
  every other menu item; surfacing them here would break consistency.
- Hardcoding `distinct="map_id"`: rejected -- the endpoint's value lies in
  letting the operator pick the distinct dimension; an empty prompt with a
  documented default preserves flexibility.
- Skipping `limit` entirely and always using the SDK default: rejected -- on
  very large sites the default of 100 may truncate; exposing the parameter
  matches existing site-stats exports.
