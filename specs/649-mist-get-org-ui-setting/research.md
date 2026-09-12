# Phase 0 Research: getOrgUiSetting

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-07-01

Source of truth for endpoint metadata:
`documentation/api/orgs/GET_orgs_org_id_uisettings_uisetting_id.md`.

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Call the SDK as
`mistapi.api.v1.orgs.ui_settings.getOrgUiSetting(apisession, org_id, uisetting_id)`.
The call takes exactly three positional arguments (the shared `APISession` instance and
the two path parameters) and returns a `mistapi.APIResponse` whose `.data` attribute
holds a single JSON object (not a list) matching the OpenAPI response schema
(`created_time`, `description`, `for_site`, `id`, `isCustomDataboard`, `modified_time`,
`name`, `org_id`, `purpose`, `site_id`, `tiles[]`). No query parameters, no request
body, no pagination.

**Rationale**: The enriched documentation at
`documentation/api/orgs/GET_orgs_org_id_uisettings_uisetting_id.md` names the SDK path
`mistapi.api.v1.orgs.ui_settings.getOrgUiSetting()` (the snake-case module `ui_settings`
matches the mistapi 0.59+ convention for the `uisettings` tag). The response schema is
a single object; the API doc explicitly states "Not paginated." The 200 example shows
the `tiles` field is an inline array within that same object, so no follow-up call is
needed to retrieve tile detail.

**Alternatives Considered**:

- Using the plural list endpoint `listOrgUiSettings` and filtering client-side by
  `uisetting_id`. Rejected: wastes API budget, does not scale if an org has many
  databoards, and mixes concerns -- the list endpoint is cataloged separately in a
  sibling spec.
- Passing `uisetting_id` as a query string instead of a path parameter. Rejected: the
  OpenAPI contract makes it a required path parameter; the SDK signature enforces this.
- Wrapping the SDK call in `try/except mistapi.APIError` at method scope. Rejected:
  MistHelper's convention is to let `mistapi` surface HTTP errors as return-code-bearing
  `APIResponse` objects; `logging.warning` on non-200 status codes, `logging.exception`
  only for truly unexpected exceptions.

## Research Task 2: Primary Key Strategy

**Decision**: Use `natural_pk` for both output tables.
- `org_ui_setting` (summary): `primary_key = ['id']` with secondary index on `org_id`.
- `org_ui_setting_tiles` (per-tile detail): `primary_key = ['id']` (each tile carries a
  Mist-provided UUID in its `id` field) with secondary index on `uisetting_id`
  (foreign key to the summary row).

**Rationale**: The response schema documents both the databoard `id` and each tile `id`
as `contentEncoding: uuid`, `readOnly: true`. Mist owns and stabilizes these UUIDs, so
they meet the constitution's definition of natural business keys and are safe for
`INSERT OR REPLACE` upserts. No timestamp is required in the PK because the endpoint
returns current-state (not time-series); repeated calls should update the same row, not
append duplicates.

**Alternatives Considered**:

- `composite_pk` on `(id, modified_time)`. Rejected: `modified_time` changes on every
  edit, so re-fetching after a user edits the databoard would create duplicate rows
  instead of updating in place. That defeats upsert semantics.
- `auto_increment_with_unique` on `(org_id, id)`. Rejected: the tile `id` and
  databoard `id` are already globally unique UUIDs, so a synthetic surrogate key adds
  no value and breaks join symmetry with other tables that use natural UUIDs.
- Storing tiles as a JSON blob column on the summary row. Rejected: violates the
  multi-backend contract -- ArangoDB stores documents natively but CSV/SQLite consumers
  expect flat rows, and downstream tooling (grep, `sqlite3` CLI) cannot filter by tile
  name without JSON functions.

## Research Task 3: Output Filename and SQLite Table

**Decision**:

- CSV / SQLite filename base for the summary row:
  `org_ui_setting_<org_id_short>_<uisetting_id_short>` where `_short` is the first 8
  characters of each UUID (matches MistHelper's naming convention for scoped exports).
  The full string is passed to `DataExporter.write_with_format_selection()` as the
  `filename` argument; the exporter appends `.csv` or writes the SQLite table without
  extension.
- SQLite table name for the summary: `org_ui_setting`.
- SQLite table name for the per-tile detail: `org_ui_setting_tiles`.

**Rationale**: Matches the pattern used by adjacent single-object read operations
(e.g. `GetOrgLicenseAsyncClaimStatus` uses `org_claim_status_summary` +
`org_claim_status_details`). The `_<short>` suffix on the CSV path lets a user run the
export twice for two different databoards without overwriting the first file, while
SQLite table names stay singular and upsert by natural PK. `api_function_name` is
passed as `"getOrgUiSetting"` for both writes so `ENDPOINT_PRIMARY_KEY_STRATEGIES` can
resolve the correct strategy per table via the tuple key
`(operation_id, table_suffix)`.

**Alternatives Considered**:

- One flat table with `tile_*` columns exploded into the summary row (one row per
  tile, summary fields repeated). Rejected: denormalizes the databoard summary into N
  rows, breaks natural PK on `id`, and inflates CSV size unnecessarily.
- CSV filename without the `_short` suffix. Rejected: silently overwrites data when
  the user exports a second databoard.

## Research Task 4: Menu Category Placement and Next Available Number

**Decision**: Menu number **58**, placed in the "Misc" sub-cluster (56-59) of the Safe
Org Exports category (1-59). Label: `Export Org UI Setting (single databoard)`.

**Rationale**: The endpoint is:
- Org-scoped (not site-scoped, not device-scoped),
- A configuration read (not stats, not events, not clients, not gateways, not
  templates, not SLE),
- Non-destructive (safe to test, no confirmation prompt required),
- Single-object per call (not a heavy paginated pull).

That combination points at the "Misc" sub-cluster (56-59) in the agents.md menu-category
table rather than the interactive-safe range (60-96) or the resource-intensive block
(97+). Slot 58 is the next available integer in that cluster as of this spec drafting.

**Alternatives Considered**:

- Menu 41 in the "Templates" sub-cluster (37-41). Rejected: UI settings are databoards
  / dashboard preferences, not device templates -- the taxonomic fit is worse.
- A new interactive-safe slot (e.g. 96+). Rejected: this call requires no live device
  interaction, no long-running loop, and no per-site iteration; it belongs with the
  org-scoped one-shot reads.
- Deferring the number decision to task-generation time. Rejected: the spec asks
  explicitly for a proposal; the plan documents 58 with a collision-resolution rule
  (fall through to the next free integer in the same cluster if a parallel branch
  claims 58 first).

## Research Task 5: Required User Prompts

**Decision**: Two prompts, both via `safe_input()`.

1. `org_id` -- prompted with default from `.env` `MIST_DEFAULT_ORG_ID` if set; context
   string `"org_ui_setting:org_id"`. Validated against the Mist UUID regex before use.
2. `uisetting_id` -- no `.env` default (databoard IDs are per-user and rarely stable
   enough for a shell env var); context string `"org_ui_setting:uisetting_id"`.
   Validated against the Mist UUID regex.

Both values are then passed to
`mistapi.api.v1.orgs.ui_settings.getOrgUiSetting(apisession, org_id, uisetting_id)`.
The `apisession` is the module-level singleton constructed once from `.env` values
`MIST_HOST` and `MIST_API_TOKEN`.

**Rationale**: `org_id` has a sensible `.env` default because most users work in a
single org and MistHelper already stores `MIST_DEFAULT_ORG_ID` for this purpose.
`uisetting_id` is a per-databoard UUID and would clutter `.env` if defaulted; prompting
every time is the right ergonomics for a single-object read. Both prompts route through
`safe_input()` to give SSH / container users a clean EOF-driven exit (code 0, no
traceback) if they Ctrl-D out.

**Alternatives Considered**:

- Auto-discover `uisetting_id` by pre-calling `listOrgUiSettings` and offering a
  numbered picker. Rejected as scope creep -- the sibling spec for `listOrgUiSettings`
  already exposes that list; users can chain the two menu items if they need
  discovery, and this menu stays focused on a single-object fetch (matches the
  five-item / structural-discipline principle).
- Take `uisetting_id` from a CLI flag (`--uisetting-id`). Rejected: the direct-invoke
  path (`--menu 58`) already inherits the interactive prompts, and adding a
  per-menu-item CLI flag pollutes the top-level argument surface.
- Silently fall back to the first databoard returned by the list endpoint if the user
  hits Enter. Rejected: violates the safety-first principle -- guessing which
  databoard the user wants is worse than a clear prompt.
