# Phase 0 Research: getOrgJseInfo

**Feature**: 609-mist-get-org-jse-info
**Spec**: [spec.md](./spec.md)
**Date**: 2026-06-30

This document captures the five research tasks that ground the implementation plan in
real Mist API behavior, real `mistapi` SDK structure, and real MistHelper conventions.
Each task uses the **Decision / Rationale / Alternatives Considered** format mandated by
the SpecKit plan template.

Source of truth for the endpoint:
`documentation/api/orgs/GET_orgs_org_id_setting_jse_info.md` (the enriched per-endpoint
reference generated from the Mist OpenAPI v3 spec under `documentation/`).

---

## Research Task 1: SDK function signature and behavior

**Decision**: Invoke the endpoint through
`mistapi.api.v1.orgs.integration_jse.getOrgJseInfo(apisession, org_id)` -- the
canonical SDK call surfaced by the enriched documentation file. The spec.md notes a
`mistapi.api.v1.orgs.setting.jse.info` module path derived directly from the OpenAPI
URL; the implementation will import whichever module name the installed `mistapi`
0.59+ wheel actually exports for this operationId. The `/speckit.tasks` step will
confirm the import name by running
`python -c "import mistapi; help(mistapi.api.v1.orgs.integration_jse.getOrgJseInfo)"`
inside the active venv before committing the import line.

**Rationale**: The enriched docs file explicitly lists
`mistapi.api.v1.orgs.integration_jse.getOrgJseInfo()` as the SDK entry point. The Mist
SDK groups related endpoints under tag-aligned module names (the OpenAPI tag for this
endpoint is `Orgs Integration JSE`), so `integration_jse` is the expected canonical
module. The call returns an `APIResponse` object whose `.data` attribute is a single
JSON dict with three fields (`cloud_name`, `org_names`, `username`); no pagination
helper is needed because the docs file states "Not paginated".

**Alternatives Considered**:

1. Calling the REST endpoint directly with `requests` -- rejected because the
   MistHelper constitution requires `mistapi` as the sole permitted Mist Cloud
   interface (Principle II, Class-Based Architecture and the documented dependency
   policy).
2. Looping with `mistapi.get_next()` -- rejected because the endpoint is explicitly
   non-paginated.
3. Caching the response in Redis ahead of write -- deferred; the existing polyglot
   backend already populates Redis when ArangoDB is the active store, and there is no
   need for a bespoke cache layer for a three-field payload.

---

## Research Task 2: Primary Key Strategy

**Decision**: Use **`natural_pk`** with `primary_key=['org_id']`. The endpoint
returns a singleton object describing the JSE integration bound to one organization,
so the natural business key is the caller-supplied `org_id`. The `org_id` is not
present in the response payload itself, so the implementation must inject it into the
row before handing the data to `DataExporter.write_with_format_selection()`. Add a
secondary index on `cloud_name` to support future "all orgs pointing at the same JSE
cloud" cross-org queries.

**Rationale**: Per the database strategy in `.github/copilot-instructions.md`,
`natural_pk` is reserved for entities with stable, API-provided unique identifiers --
`org_id` qualifies because it is the Mist organization UUID and is unique by
definition. Re-running the menu item for the same org must UPSERT (not INSERT) so the
SQLite row is overwritten with the latest cloud / username / org_names values, which
is exactly the behavior `INSERT OR REPLACE` plus a single-column primary key
delivers. `auto_increment_with_unique` is unnecessary because no payload field is
artificial; `composite_pk` is unnecessary because the endpoint is not time-series.

**Alternatives Considered**:

1. `composite_pk` on `(org_id, cloud_name)` -- rejected because `cloud_name` is a
   *value* of the integration, not a key. If a user re-points their org at a
   different JSE cloud, the old row would orphan instead of update.
2. `auto_increment_with_unique` on `(org_id)` -- rejected as redundant; the natural
   key already provides the unique constraint without the surrogate id column.
3. Concatenating `username` into the key -- rejected because the JSE username can
   change without the integration identity changing; making it part of the key would
   leave orphan rows on every credential rotation.

---

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV / JSON filename: `org_jse_info_<org_id>.csv` (and the matching `.json` /
  `.xlsx` extensions the DataExporter writes when configured).
- SQLite table name: `org_jse_info`.
- ArangoDB collection name: `org_jse_info` with an edge `org_has_jse_info` linking
  the existing `orgs` vertex to each new row.

**Rationale**: The MistHelper naming convention is
`<scope>_<operation_subject>[_<scope_id>].csv` -- e.g. `org_sites_<org_id>.csv`,
`site_devices_<site_id>.csv`. `org_jse_info_<org_id>.csv` mirrors that pattern
exactly, embedding the scope id so multi-org dumps do not collide on disk. The
SQLite table name drops the scope id (one shared table, one row per org) and uses
snake_case lowercase to match the rest of the schema. Embedding `org_id` in the
filename also matches the precedent set by other org-setting export operations in
the same Safe Org Exports cluster.

**Alternatives Considered**:

1. `jse_info.csv` (no scope prefix) -- rejected because it loses the org-scope
   discriminator and conflicts with the parallel site-scoped JSE info file
   (`documentation/api/sites/GET_sites_site_id_setting_jse_info.md`) that a future
   spec will catalog.
2. `org_integration_jse_info_<org_id>.csv` -- rejected as needlessly verbose; the
   `org_` prefix already disambiguates the scope and `integration_` adds no
   user-visible value.
3. Per-org SQLite table (`org_jse_info_<org_id>`) -- rejected because it explodes
   the schema and breaks cross-org queries; the single-table model with `org_id` as
   primary key is the idiomatic choice.

---

## Research Task 4: Menu category placement and next available menu number

**Decision**: Add the new operation as menu number **58** under the **Safe Org
Exports / Misc (56-59)** sub-band. The `/speckit.tasks` step will re-verify against
the live `MistHelper.py` menu registry; if 58 is already claimed by another in-flight
feature branch, the next free integer in the same cluster (59, then 56-57 if those
are open) is used.

**Rationale**: The menu category table in `.github/copilot-instructions.md` allocates
1-59 to Safe Org Exports, with the Misc sub-band at 56-59 for read-only org-scoped
calls that do not fit the Sites / Inventory / Device-stats / Events / Clients /
Gateways / Templates / Config-Admin / SLE buckets. `getOrgJseInfo` is exactly such a
call: it is org-scoped, read-only, and concerns an integration setting rather than a
device, client, or event stream. Slot 58 keeps it cleanly inside the safe range
(below the resource-intensive band at 97+) and adjacent to other org-setting
read operations the user is likely to invoke in the same session.

**Alternatives Considered**:

1. Place in the Config/Admin band (42-50) -- rejected because that band is reserved
   for org-wide configuration *templates* and admin operations (alarm templates, RF
   templates, device profiles), not third-party integration settings.
2. Place in the resource-intensive band (97-101) -- rejected because the endpoint is
   non-paginated and returns a tiny payload; it does not warrant the special
   handling that band signals.
3. Reserve the number until task time -- rejected because the plan template
   explicitly asks for an explicit menu number proposal so reviewers can spot
   conflicts at planning time, not implementation time.

---

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

**Decision**: The menu method requires exactly one identifier -- `org_id` -- which is
resolved in this order:

1. If `os.environ.get("MIST_ORG_ID")` is set (loaded from `.env` by
   `python-dotenv` at process start), use it as the default and prompt the user to
   confirm or override.
2. Otherwise, prompt for `org_id` with no default.
3. Either way, validate the resulting value against the Mist UUID regex
   (`^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`) before the
   SDK call; on failure log a `WARNING` and return early.

All prompts use `safe_input()` with `context="org_jse_info:org_id"` so SSH and
container EOF exits cleanly with code 0. No other identifiers are needed -- no site
id, no device id, no time range, no query parameters of any kind (the endpoint has
zero query parameters per the enriched documentation).

The Mist host (`MIST_HOST`) and API token (`MIST_API_TOKEN`) are loaded from `.env`
by the existing `mistapi.APISession` constructor; the new method does not touch them
directly and they are never logged.

**Rationale**: The endpoint's only path parameter is `org_id`, and there are zero
query parameters. Reading `MIST_ORG_ID` from `.env` as a default matches the
behavior of every other org-scoped export in the Safe Org Exports cluster -- a
junior NOC engineer running multiple org-scoped exports in a row should not have to
re-type the same UUID on every prompt. Validating the UUID shape before the SDK
call prevents an obvious typo from becoming a 404 noise event in the API logs.

**Alternatives Considered**:

1. Prompt unconditionally with no `.env` default -- rejected as user-hostile in the
   common case of a single-org operator.
2. Accept the `org_id` as a command-line flag in addition to the interactive prompt
   -- deferred; the existing `--menu N` direct invocation pattern already supports
   passing identifiers through `.env`, and adding a per-operation flag would inflate
   the CLI argument surface without proportional benefit.
3. Auto-detect the org from the API token's permissions list -- rejected as
   brittle; tokens with multi-org access would still require disambiguation and the
   detection logic would add complexity disproportionate to the value.
