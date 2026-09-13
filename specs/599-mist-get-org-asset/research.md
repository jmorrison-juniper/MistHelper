# Phase 0 Research: getOrgAsset

**Feature**: 599-mist-get-org-asset | **Date**: 2026-06-29

This document captures the design decisions made before Phase 1 artifacts (data model,
quickstart, contracts) are produced. Each task uses the Decision / Rationale /
Alternatives Considered format mandated by the SpecKit template.

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Invoke the endpoint through `mistapi.api.v1.orgs.assets.getOrgAsset(apisession, org_id, asset_id)`,
treating the response `.data` payload as a single JSON object (not a list).

**Rationale**:
- The enriched documentation at
  `documentation/api/orgs/GET_orgs_org_id_assets_asset_id.md` explicitly maps the
  endpoint `GET /api/v1/orgs/{org_id}/assets/{asset_id}` to
  `mistapi.api.v1.orgs.assets.getOrgAsset()`.
- Path parameters are `org_id` (string, required) and `asset_id` (string, required); no
  query parameters, no request body, no pagination ("Pagination: Not paginated").
- The 200 response schema is a single `Asset` object whose required fields are `mac` and
  `name`, with optional fields `created_time`, `for_site`, `id`, `map_id`,
  `modified_time`, `org_id`, `site_id`, `tag_id`. The `id` field is the natural primary
  key emitted by Mist as a UUID.
- The existing `mistapi` SDK convention (verified by the adjacent `searchOrgAssets`
  endpoint already used in `OrgExportUtils._assets`) is that the SDK returns a
  `mistapi.api_response.APIResponse` whose `.data` attribute holds the raw JSON; for a
  single-object endpoint this attribute is a `dict`, not a `list`.

**Alternatives Considered**:
- *Direct HTTP via `requests`*: rejected -- violates the project rule that all Mist API
  calls go through `mistapi` (Principle II, Class-Based Architecture, and the
  `mistapi` SDK constraint in `agents.md`).
- *Reuse `searchOrgAssets` and post-filter for one ID*: rejected -- wasteful (a full
  search call versus one direct GET), defeats the purpose of cataloging this endpoint,
  and breaks the 1:1 mapping between menu items and Mist API operations.

## Research Task 2: Primary Key Strategy

**Decision**: Register `getOrgAsset` in `ENDPOINT_PRIMARY_KEY_STRATEGIES` as a
`natural_pk` strategy keyed on `["id"]` with secondary indexes on `["org_id", "name",
"mac", "site_id"]`.

**Rationale**:
- The response schema explicitly defines `id` as a stable UUID
  (`contentEncoding: uuid`, `readOnly: true`) -- the textbook signature of a natural
  primary key per the `agents.md` Database Strategy section.
- The peer list endpoint `listOrgAssets` is already registered with the identical
  strategy (`{"type": "natural_pk", "primary_key": ["id"], "indexes": ["org_id",
  "name", "mac", "site_id"]}` at `MistHelper.py` line ~3998). Using the same strategy
  for the singleton-fetch variant keeps the two endpoints' rows in the same SQLite
  shape and lets a single asset row upsert cleanly over a row previously loaded by the
  list endpoint without duplicate-key collisions.
- `INSERT OR REPLACE` semantics on a `natural_pk` strategy let re-runs against a known
  asset update the row in place rather than creating duplicates.

**Alternatives Considered**:
- *`composite_pk` on `[id, modified_time]`*: rejected -- creates a fresh row every time
  the asset is modified, breaking the upsert contract and inflating the table over time.
- *`auto_increment_with_unique`*: rejected -- the API already provides a stable UUID,
  so a synthetic `misthelper_internal_id` would be inferior on every axis (storage,
  join cost, debuggability).

## Research Task 3: Output Filename and SQLite Table

**Decision**: Use the canonical filename / table name `get_org_asset` (singular, no
suffix). The CSV file lands at `data/get_org_asset.csv`; the SQLite table is
`get_org_asset` inside `data/mist_data.db`; ArangoDB collections inherit the same
identifier per the existing `DataExporter` convention.

**Rationale**:
- `DataExporter.write_with_format_selection(data, filename, api_function_name=...)`
  derives the storage target from the `api_function_name` argument when present;
  passing `api_function_name="getOrgAsset"` produces a snake-cased table and filename
  `get_org_asset` consistent with all other catalog entries.
- The singular form (`get_org_asset` not `get_org_assets`) matches the singleton
  semantics of the endpoint and disambiguates it from the existing
  `list_org_assets` / `search_org_assets` outputs already produced by adjacent menu
  items. A reader scanning `data/` can tell at a glance whether a file holds the full
  asset roster or a single asset record.
- Aligns with the precedent set by other single-resource read endpoints already in the
  codebase that use the GET verb in their identifier.

**Alternatives Considered**:
- *Reuse the `list_org_assets` table*: rejected -- mixes singleton-fetch rows with
  full-roster rows in the same table, making it impossible to tell from the table
  alone which menu populated which row.
- *`assets_detail.csv`*: rejected -- the project convention is `verb_noun` keyed off
  the operationId, not free-form English.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Propose **menu number 195**. By category the endpoint is a "Safe Org
Export" (read-only, single GET, no destructive side effect), which is the 1-59 cluster
per `agents.md`. Because that cluster and every other cluster up to 194 is fully
allocated, the new item takes the next free integer above the current ceiling.

**Rationale**:
- `agents.md` documents the full menu range as 1-194 with categories already assigned;
  the spec generator and several open feature branches consume the remaining safe-org
  and interactive-safe slots, leaving no room inside 1-194.
- Choosing 195 keeps menu numbers strictly sequential without renumbering existing
  operations -- a renumber would invalidate every `--menu N` script and test reference
  already in production.
- The menu remains read-only despite its position above 154-194 (the destructive
  cluster); the menu's category label in the README's menu table is set to
  "Safe Org Exports" so the reader is not misled by the integer alone.

**Alternatives Considered**:
- *Squeeze into a gap below 194*: rejected -- no documented gap exists, and inserting
  the new operation into a destructive slot label would mislead the NOC engineer
  audience (Principle III: Safety-First, clarity for junior operators).
- *Wait for a 200-block renumber*: rejected -- renumbering breaks running automation
  and is out of scope for a single-endpoint addition.

## Research Task 5: Required User Prompts

**Decision**: The new menu method collects two inputs through `safe_input()` -- `org_id`
and `asset_id` -- both as Mist UUID strings. Other context (`MIST_HOST`,
`MIST_API_TOKEN`) is loaded from `.env` via the existing `mistapi.APISession`. The
default `org_id` (if `MIST_DEFAULT_ORG_ID` is set in `.env`) is offered as the prompt
default; the asset_id has no `.env` default and must always be supplied interactively
or via `--menu 195 --asset-id ...` automation.

**Rationale**:
- The endpoint requires exactly two path parameters and no query parameters per
  `documentation/api/orgs/GET_orgs_org_id_assets_asset_id.md`.
- The existing project convention (verified against `LicenseExportUtils` and other
  org-scoped menu items) is to source `org_id` from `MIST_DEFAULT_ORG_ID` when the
  user just presses Enter, and to demand explicit input for any non-org identifier
  because the .env file is shared across the whole org. Treating `asset_id` as an
  always-prompt parameter prevents an automation accident from pulling the wrong
  asset.
- Both prompts use explicit `context=` strings (`"org_asset:org_id"`,
  `"org_asset:asset_id"`) so `safe_input()`'s EOF handler logs which prompt was
  abandoned, making SSH-disconnect debugging trivial.

**Alternatives Considered**:
- *Prompt only for `asset_id`, always use the .env org*: rejected -- a NOC engineer
  often holds delegated access to multiple orgs and must be able to override the
  default per call.
- *Read both IDs from a CSV batch file*: rejected -- the spec scope is a single read
  call; batch is a future enhancement and would warrant its own spec.
