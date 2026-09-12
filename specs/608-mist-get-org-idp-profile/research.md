# Phase 0 Research: getOrgIdpProfile

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/orgs/GET_orgs_org_id_idpprofiles_idpprofile_id.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path
`mistapi.api.v1.orgs.idpprofiles.getOrgIdpProfile(apisession, org_id,
idpprofile_id)`. The SDK returns a `mistapi.APIResponse` object whose `.data`
attribute is the parsed JSON body. The body is a single JSON object (not a
list, not paginated) with the following top-level keys per the enriched doc:

- `id` (string UUID) -- profile UUID, stable, read-only.
- `org_id` (string UUID) -- owning org, read-only (echoed by API).
- `name` (string) -- human-readable label (e.g. `"relaxed"`).
- `base_profile` (string enum: `critical`, `standard`, `strict`) -- baseline rule set.
- `created_time` (number, epoch seconds, read-only).
- `modified_time` (number, epoch seconds, read-only).
- `overwrites` (array of objects) -- per-rule customizations. Each item:
  - `name` (string) -- overwrite rule name (unique within the profile).
  - `action` (string enum: `alert` [default], `drop`, `close`).
  - `matching` (object) with `attack_name[]`, `dst_subnet[]`, `severity[]`
    (each a string array; `severity` values are `critical`, `info`, `major`,
    `minor`).

Required path parameters: `org_id` (UUID string), `idpprofile_id` (UUID string).
No query parameters. No request body.

**Rationale**:
The enriched per-endpoint doc lists the SDK module as
`mistapi.api.v1.orgs.idp_profiles.getOrgIdpProfile()` (with an underscore),
while the spec.md and OpenAPI path use `idpprofiles` (no underscore). The
mistapi SDK generates module paths directly from the URL segment, and the URL
segment is `idpprofiles` -- so the spec.md path
`mistapi.api.v1.orgs.idpprofiles` is correct. The underscore form in the
enriched doc is a doc-generator artifact (snake_case auto-conversion). Final
verification happens at implementation time via
`python -c "from mistapi.api.v1.orgs import idpprofiles; help(idpprofiles)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/idpprofiles/{idpprofile_id}`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method
   exists.
2. *Use the underscored path from the enriched doc
   (`mistapi.api.v1.orgs.idp_profiles`).* Rejected -- the existing
   `listOrgIdpProfiles` PK strategy entry at line 3923 of `MistHelper.py`
   already names the operation without underscore, confirming the SDK uses
   the URL-derived path.
3. *Fetch the full list via `listOrgIdpProfiles` and filter client-side.*
   Rejected -- defeats the point of a per-profile detail endpoint, wastes
   bandwidth and rate-limit budget, and would not surface a clean 404 when
   the profile id is wrong.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **natural primary key** strategy for the profile summary and a
**composite primary key** strategy for the overwrite rules:

- `org_idp_profile_summary`: `type = "natural_pk"`, `primary_key = ["id"]`.
  The Mist API returns `id` as a stable UUID for the profile -- this is the
  natural business key. Indexed on `org_id` and `name` for fast lookup.
- `org_idp_profile_overwrites`: `type = "composite_pk"`,
  `primary_key = ["idpprofile_id", "name"]`. Each overwrite rule has a
  `name` field that is unique within its parent profile (overwrite rule
  names are how users reference them in the Mist UI). Pairing with
  `idpprofile_id` (the parent profile UUID, injected by MistHelper before
  the upsert) yields a unique row per (profile, rule).

Both entries are registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` with the
operationId `getOrgIdpProfile` (summary) and the MistHelper-internal
identifier `getOrgIdpProfileOverwrites` (sub-table). This pattern matches the
existing `listOrgIdpProfiles` natural_pk entry already at line 3923 of
`MistHelper.py`, so the new summary entry is consistent with how the org's
list endpoint already persists.

**Rationale**:
The endpoint returns a single profile object whose `id` is a server-assigned
UUID -- the textbook case for `natural_pk`. The nested `overwrites` array
holds rule-level customizations whose only stable identifier within the
profile is the rule `name` (Mist does not assign per-rule UUIDs). Splitting
into a summary table and an overwrites table:

1. Mirrors how MistHelper already splits other endpoints whose response
   contains nested arrays.
2. Lets a user query the profile summary without joining when they only need
   the base profile / metadata.
3. Enables clean `INSERT OR REPLACE` upserts on both tables for repeated
   polls of the same profile (e.g. after a UI edit).

**Alternatives Considered**:

1. *Single combined table with all summary fields plus the overwrite columns,
   with `name` nullable when no overwrites exist.* Rejected -- breaks
   queryability (one profile with N overwrites would produce N near-duplicate
   summary rows) and conflicts with the flatten-then-split convention used
   throughout MistHelper.
2. *`auto_increment_with_unique` on the overwrites table.* Rejected --
   repeated polls would accumulate duplicate rules, defeating the upsert
   contract the spec requires.
3. *Store `overwrites` as a JSON-encoded blob column on the summary table.*
   Rejected -- breaks SQL queryability for downstream consumers and
   conflicts with the flattening convention used elsewhere in the codebase.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/org_<org_id_short>_idp_profile_<idp_id_short>_summary.csv`
- CSV (overwrites): `data/org_<org_id_short>_idp_profile_<idp_id_short>_overwrites.csv`
- SQLite tables: `org_idp_profile_summary` and `org_idp_profile_overwrites`
- `org_id_short` / `idp_id_short` are the first 8 hex characters of the
  respective UUIDs -- the convention used by adjacent exporters in
  `MistHelper.py` for human-readable filenames without leaking full UUIDs
  into shell history.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"getOrgIdpProfile"` for the
summary row and `"getOrgIdpProfileOverwrites"` for the overwrite rows. The
DataExporter uses those strings as the lookup keys into
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Naming matches the pattern used by adjacent per-object exports (e.g. the
license summary/by-site pair in spec 500). Two output files plus two SQLite
tables keeps the schema clean and lets a user query the summary without a
join when they only need the base profile / metadata. The double-short-UUID
filename (`<org_id_short>_idp_profile_<idp_id_short>`) disambiguates multiple
IDP profiles fetched against the same org over time.

**Alternatives Considered**:

1. *Single output file with a JSON-encoded `overwrites` column.* Rejected --
   breaks SQL queryability and conflicts with the flattening convention used
   everywhere else in MistHelper.
2. *Full UUIDs in the filename.* Rejected -- leaks UUIDs into shell history
   and ls output unnecessarily. The 8-char short form is enough to
   disambiguate locally.
3. *Filename keyed only on `name`.* Rejected -- profile names are not
   guaranteed unique across orgs and may contain spaces or characters that
   are unsafe for filenames.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 96**, sitting at the top of the
Interactive Safe cluster (60-96) immediately before the Resource Intensive
cluster (97-101 + 153). The category label is "Interactive Safe -- Org
Security".

**Rationale**:
The `.github/copilot-instructions.md` menu range table defines:
1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource
Intensive, 102-123 WebSocket, 124-152 Interactive, 154-194 Destructive.
This endpoint requires the user to enter **two** identifiers (`org_id` and
`idpprofile_id`), which by convention places it in the Interactive Safe
band rather than the bulk-list Safe Org Exports band (1-59 covers operations
that need at most an org context). Slot 96 is the last free integer in the
Interactive Safe range and is the natural neighbor of the existing
`listOrgIdpProfiles` PK strategy. The number is provisional -- at
`/speckit.tasks` time, `MistHelper.py` is grep'd for the latest allocated
menu integer and 96 is shifted forward if a conflict exists.

**Alternatives Considered**:

1. *Slot in Safe Org Exports (1-59).* Rejected -- the user must supply a
   second non-org identifier (`idpprofile_id`), which is exactly the
   discriminator between the two ranges per the menu convention.
2. *Slot in Resource Intensive (97-101).* Rejected -- a single GET against a
   small JSON object with no pagination is the opposite of resource
   intensive.
3. *Append to the end (e.g., 195).* Rejected -- the destructive cluster
   ends at 194; placing a read-only IDP profile fetch above the destructive
   block visually mis-signals the risk level to a junior NOC engineer
   scrolling the menu.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via
`safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"org_idp_profile:org_id"`. Default: the value of `MIST_ORG_ID` in `.env`
   if present (pressing Enter accepts the default). Validated via the
   existing `is_valid_uuid()` helper before the API call; on failure, log
   `WARNING` and return early.
2. `idpprofile_id` -- prompt: `"IDP Profile ID (UUID): "`, context:
   `"org_idp_profile:idpprofile_id"`. Default: the value of
   `MIST_IDP_PROFILE_ID` in `.env` if present (optional convenience for
   repeated local testing). Validated via `is_valid_uuid()`; on failure,
   log `WARNING` and return early.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.
- `MIST_IDP_PROFILE_ID` -- optional default for prompt 2 (new variable,
  documented in `quickstart.md` and `deploy/.env.example`).

**Rationale**:
Mist's per-IDP-profile detail endpoint is doubly-scoped: it identifies the
profile by both org and profile UUID. There is no broader scope (site,
device, template) involved. The endpoint takes no query parameters, so no
third prompt is needed. Two prompts is the minimum that satisfies the
endpoint contract while honoring the safety-first principle of asking
before acting.

**Alternatives Considered**:

1. *Auto-discover the `idpprofile_id` by calling `listOrgIdpProfiles` first
   and prompting the user to pick from a numbered list.* Rejected for the
   v1 menu item -- adds a chained API call (extra rate-limit budget),
   doubles the menu method length, and breaks the "one endpoint = one menu
   item" convention. A future menu wrapper could compose the list + detail
   pattern, but it should be its own spec.
2. *Add a third prompt for an output filename override.* Rejected -- adds
   keystrokes without operational value. The deterministic filename scheme
   in Research Task 3 makes results easy to find under `data/`.
3. *Accept the profile id as a CLI flag instead of an interactive prompt.*
   Rejected -- inconsistent with the menu-driven UX. `--menu 96` will pick
   up `MIST_ORG_ID` and `MIST_IDP_PROFILE_ID` from `.env` for non-
   interactive smoke tests, which covers the automation case without
   inventing a new flag.
