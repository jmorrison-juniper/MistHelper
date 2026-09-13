# Phase 0 Research: getOrgAAMWProfile

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each task
follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_aamwprofiles_aamwprofile_id.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.orgs.aamwprofiles.getOrgAAMWProfile(apisession, org_id,
aamwprofile_id)`. The SDK returns a `mistapi.APIResponse` object whose `.data` attribute
is the parsed JSON body. The body is a single JSON object (not a list, not paginated),
with the following top-level keys per the doc:

- `id` (string UUID, readOnly) -- profile UUID.
- `org_id` (string UUID, readOnly) -- owning org.
- `site_id` (string UUID, readOnly) -- optional site scope.
- `name` (string) -- profile display name (e.g. `"aamw-custom"`).
- `created_time` (number, epoch seconds, readOnly).
- `modified_time` (number, epoch seconds, readOnly).
- `fallback_action` (string enum: `block`, `permit`) -- action when verdict is unknown.
- `file_action` (string enum: `block`, `permit`) -- action when file matches.
- `verdict_threshold` (integer 1..10, default 8) -- malicious-score cutoff.
- `categories` (array of `aamw_profile_category` objects). Each item:
  - `category` (string enum: `archive`, `document`, `pdf`, `executable`,
    `rich_application`, `library`, `os_package`, `mobile`, `java`, `configuration`,
    `script`).
  - `hash_lookup_only` (boolean, default false).

Required path parameters: `org_id` (UUID string) and `aamwprofile_id` (UUID string). No
query parameters.

**Rationale**:
The enriched per-endpoint doc lists the SDK module as
`mistapi.api.v1.orgs.advanced_anti_malware_profiles.getOrgAAMWProfile()`, but the
OpenAPI path uses the abbreviated token `aamwprofiles`. The mistapi SDK historically
generates module paths from the URL, not from a long-form tag (verified by adjacent
endpoints under the same URL, e.g. `GET /orgs/{org_id}/aamwprofiles` ->
`mistapi.api.v1.orgs.aamwprofiles`). The spec.md (the authoritative feature contract)
explicitly names `mistapi.api.v1.orgs.aamwprofiles`, and that path matches the URL
one-for-one. Final verification happens at implementation time via
`python -c "from mistapi.api.v1.orgs import aamwprofiles; help(aamwprofiles)"` inside
the venv; if the SDK actually exposes the long-form module name, the import is updated
accordingly in a single line change with no impact on the contract.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/aamwprofiles/{aamwprofile_id}`.* Rejected --
   the constitution forbids direct HTTP when a mistapi method exists.
2. *Use the long-form path implied by the doc tag
   (`mistapi.api.v1.orgs.advanced_anti_malware_profiles`).* Rejected for the initial
   import -- the URL-based short form matches every adjacent AAMW endpoint and the
   spec.md. If `pip show mistapi` reveals the SDK only ships the long-form, we switch
   the import at implementation time; the contract is unaffected.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **two-table split** that mirrors the response structure:

- `org_aamw_profile_summary`: PK = `id` (the profile UUID returned by Mist, stable). PK
  type = **`natural_pk`**. One row per profile UUID.
- `org_aamw_profile_categories`: PK = `(aamwprofile_id, category)` -- one row per
  (profile, category-enum) pair. PK type = **`composite_pk`**. `aamwprofile_id` is the
  FK back to the summary table; `category` is the enum string from the API and is
  unique within a profile's `categories` array.

`org_id` is injected by MistHelper before the upsert and stored on both tables for fast
filtering, but is not part of the primary key (the profile `id` is globally unique in
Mist's namespace, so adding `org_id` to the PK would be redundant).

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses:
- `getOrgAAMWProfile` -> `natural_pk` on `['id']` with `indexes: ['org_id', 'site_id',
  'name']`.
- `getOrgAAMWProfileCategories` -> `composite_pk` on `['aamwprofile_id', 'category']`
  with `indexes: ['org_id']`. The key suffix `Categories` is a MistHelper-internal
  identifier for the flattened sub-array (Mist has no operationId for it).

**Rationale**:
The response schema names `id` as a read-only UUID -- the canonical stable identifier
used by every Mist UUID-keyed entity. `natural_pk` lets the SQLite backend `INSERT OR
REPLACE` cleanly on repeated polls of the same profile. The nested `categories[]` array
is unbounded (up to 11 enum values), and a junior NOC engineer expects to query
"which profiles block `executable`?" -- which is far easier against a flat
`org_aamw_profile_categories` table than against a JSON-encoded blob.

**Alternatives Considered**:

1. *Single combined table with JSON-encoded `categories` column.* Rejected -- breaks
   SQL queryability and conflicts with the flattening convention used everywhere else
   in MistHelper.
2. *`composite_pk` on `(org_id, id)` for the summary table.* Rejected -- the profile
   `id` is globally unique across orgs in Mist; including `org_id` in the PK is
   redundant and would also break cross-org dedupe if a profile were ever cloned.
3. *`auto_increment_with_unique`.* Rejected -- the API gives us a stable UUID; we
   should use it.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/org_<org_id_short>_aamw_profile_<aamwprofile_id_short>_summary.csv`
- CSV (categories): `data/org_<org_id_short>_aamw_profile_<aamwprofile_id_short>_categories.csv`
- SQLite tables: `org_aamw_profile_summary` and `org_aamw_profile_categories`
- `*_short` is the first 8 hex characters of the relevant UUID -- the convention used
  by adjacent license / template exports for human-readable filenames without leaking
  full UUIDs into shell history.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"getOrgAAMWProfile"` (matching the operationId) for the summary, and
`"getOrgAAMWProfileCategories"` for the per-category sub-table. DataExporter uses
those strings as the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the filename pattern used by adjacent single-object org exports in MistHelper.
Two output files / two SQLite tables keeps the schema flat and queryable. Including
both the org short id and the profile short id in the filename disambiguates results
when the same operator runs the menu item against multiple profiles across multiple
orgs in the same session.

**Alternatives Considered**:

1. *Single output file with JSON-encoded `categories`.* Rejected (see Research Task 2).
2. *Full UUIDs in the filename.* Rejected -- leaks UUIDs into shell history and
   directory listings unnecessarily. The 8-char short form is enough to disambiguate
   locally.
3. *Filename keyed only by profile UUID (no org segment).* Rejected -- a NOC engineer
   may export AAMW profiles from multiple orgs and needs the org segment to find the
   right file fast.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 58**, sitting inside the Safe Org Exports
cluster (1-59) next to the existing org-scoped security-profile reads (AV, IDP). The
category label is "Safe Org Exports -- Security Profiles (AAMW)".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource Intensive,
102-123 WebSocket, 124-152 Interactive, 154-194 Destructive. AAMW profiles are
configuration objects that mirror `avprofiles` and `idpprofiles`, which live in the
Safe Org Exports range alongside the other config exports (42-50 Config/Admin per the
canonical instruction file). 58 is the next contiguous integer at the upper end of the
Safe Org Exports cluster and is far away from any destructive cluster.

The number is provisional -- at `/speckit.tasks` time, MistHelper.py is grep'd for the
latest allocated menu integer and 58 is shifted forward if a conflict exists. The class
chosen at implementation time is the same class that owns `getOrgAVProfile` /
`getOrgIDPProfile`, ensuring all three security-profile reads sit together.

**Alternatives Considered**:

1. *Append to the end (e.g., 195).* Rejected -- the destructive cluster ends at 194,
   and placing a read-only security-profile read above the destructive block visually
   mis-signals the risk level to a junior NOC engineer scrolling the menu.
2. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is a single
   GET returning a small JSON object with one bounded enum array. It is not
   resource-intensive.
3. *Slot inside Interactive Safe (60-96).* Rejected -- no interactive selection beyond
   the two UUID prompts; this is a pure org-export and belongs alongside the other
   org-scoped security-profile reads.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context: `"org_aamw_profile:org_id"`.
   Default: the value of `MIST_ORG_ID` in `.env` if present (pressing Enter accepts the
   default). Validated via the existing `is_valid_uuid()` helper before the API call;
   on failure, log `WARNING` and return early.
2. `aamwprofile_id` -- prompt: `"AAMW Profile ID (UUID): "`, context:
   `"org_aamw_profile:aamwprofile_id"`. No default (the profile UUID is specific to the
   org and is not a sensible `.env` value). Validated via `is_valid_uuid()` before the
   API call.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g. `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.

**Rationale**:
The endpoint requires exactly two path parameters and has zero query parameters
(verified against the enriched OpenAPI doc). Asking for both UUIDs covers the entire
contract. The profile UUID is not stored in `.env` because operators typically discover
it by first running the sibling list endpoint (`getOrgAAMWProfiles`) -- making
`aamwprofile_id` a default in `.env` would encourage incorrect operator habits.

**Alternatives Considered**:

1. *Allow a profile-name prompt and resolve to UUID via a list-call.* Rejected --
   doubles the API surface this menu touches and complicates the contract. A separate
   helper menu item that lists profiles already exists for that workflow (the sibling
   `getOrgAAMWProfiles` operation is or will be cataloged in its own spec).
2. *Take a `--profile-id` CLI flag instead of an interactive prompt.* Deferred -- this
   spec keeps the interactive prompt to match the project pattern. A CLI flag can be
   layered on later without breaking the prompt path.
