# Phase 0 Research: GetOrgNacPortalSamlMetadata

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/orgs/GET_orgs_org_id_nacportals_nacportal_id_saml_metadata.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the URL-mirroring module path:
`mistapi.api.v1.orgs.nacportals.saml_metadata.getOrgNacPortalSamlMetadata(apisession, org_id, nacportal_id)`.
The SDK returns a `mistapi.APIResponse` object whose `.data` attribute is the
parsed JSON body. The body is a single flat JSON object (not a list and not
paginated), with the following top-level keys per the enriched doc:

- `acs_url` (string, read-only) -- Assertion Consumer Service URL. Present when
  the parent NAC portal's `idp_type` is `saml`.
- `entity_id` (string, read-only) -- SAML Service-Provider entity ID URL.
  Present when `idp_type == saml`.
- `logout_url` (string, read-only) -- Single-Logout endpoint URL. Present when
  `idp_type == saml`.
- `metadata` (string, read-only) -- Embedded XML document (the full
  SP metadata that an IdP administrator uploads). Present when
  `idp_type == saml`. Typical size a few KB.
- `scim_base_url` (string) -- Present when `idp_type == oauth` and
  `scim_enabled == true` (mutually exclusive with the SAML fields above).

Required path parameters: `org_id` (UUID string) and `nacportal_id` (UUID
string). No query parameters. No request body.

**Rationale**:
The enriched per-endpoint doc lists the SDK module as
`mistapi.api.v1.orgs.nac_portals.getOrgNacPortalSamlMetadata()`, but the
OpenAPI URL is `/orgs/{org_id}/nacportals/{nacportal_id}/saml_metadata` and
MistHelper's existing usage at line 12614 imports from
`mistapi.api.v1.orgs.nacportals` (no underscore, matching the URL segment).
The `saml_metadata` URL trailing segment maps to a submodule of the same name.
The spec.md explicitly names `mistapi.api.v1.orgs.nacportals.saml_metadata` and
that path matches the URL one-for-one, so we follow the spec plus the existing
`nacportals.listOrgNacPortals` usage as the source of truth. Final
verification happens at implementation time via
`python -c "from mistapi.api.v1.orgs.nacportals import saml_metadata; help(saml_metadata)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/nacportals/{nacportal_id}/saml_metadata`.*
   Rejected -- the Constitution forbids direct HTTP when a mistapi method
   exists.
2. *Use the module path with underscore
   (`mistapi.api.v1.orgs.nac_portals`).* Rejected -- MistHelper.py already
   imports the URL-matching `nacportals` variant (`_nac_portals` helper at
   line 12611 uses `mistapi.api.v1.orgs.nacportals.listOrgNacPortals`). Two
   different casings in one file would be an inconsistency trap.
3. *Fetch the sibling XML endpoint
   (`/saml_metadata.xml`) and parse locally.* Rejected -- the JSON endpoint
   already returns the XML string embedded in a JSON field, plus the
   convenience URLs (`acs_url`, `entity_id`, `logout_url`) that the XML
   endpoint does not surface as separate fields. The JSON form is the
   authoritative shape for this feature.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** on a single output table:

- `org_nac_portal_saml_metadata`: PK = `(org_id, nacportal_id)` -- one row per
  (org, NAC portal). Both values are supplied by MistHelper (from user
  prompts) and injected into the row before write, because the API response
  body does not include either identifier.

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk`.

**Rationale**:
The endpoint's SAML metadata is a property *of* a specific NAC portal in a
specific org. A single MistHelper deployment may target multiple orgs and each
org may host multiple NAC portals, so neither identifier is unique on its own.
The pair `(org_id, nacportal_id)` is the natural business key. `INSERT OR
REPLACE` upserts the metadata every time the menu item is run against the same
portal, which is exactly the desired behavior when a NAC portal's SAML
configuration changes on the Mist side (metadata rotation, cert renewal).

**Alternatives Considered**:

1. *`natural_pk` on `entity_id` alone.* Rejected -- `entity_id` is a URL
   embedded in the *response*, not an identifier under the caller's control.
   Two portals in the same org could theoretically share an entity_id during a
   misconfiguration and would collide silently. `(org_id, nacportal_id)` is
   the safer key.
2. *`auto_increment_with_unique`.* Rejected -- would let repeated runs against
   the same portal accumulate duplicate snapshots, defeating the upsert
   behavior the spec requires (FR-005).
3. *Composite key including a poll timestamp.* Rejected -- SAML metadata is
   comparatively static (rotates on cert renewal, not per-second). Historical
   snapshots are out of scope; the current-state single-row-per-portal design
   matches how adjacent config-like exports are stored in MistHelper.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/org_<org_id_short>_nacportal_<nacportal_id_short>_saml_metadata.csv`
- SQLite table: `org_nac_portal_saml_metadata`
- `org_id_short` and `nacportal_id_short` are the first 8 hex characters of
  the respective UUIDs -- the same convention used by adjacent license and
  NAC exports in MistHelper for human-readable filenames without leaking full
  UUIDs into shell history.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"getOrgNacPortalSamlMetadata"`
(matching the OpenAPI operationId). The DataExporter uses that string as the
lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by `_nac_portals` (which writes
`OrgNacPortals.csv`) and other per-entity exports that need to disambiguate by
identifier. Including both short IDs in the filename lets an operator retrieve
metadata for multiple portals in the same org without file collisions. A
single table (as opposed to two like the reference license-claim example) is
correct here because the response is a flat object with no nested arrays.

**Alternatives Considered**:

1. *One CSV per NAC portal in a nested subdirectory
   (`data/nacportals/<uuid>/saml_metadata.csv`).* Rejected -- MistHelper
   convention keeps all outputs flat under `data/`; nested layouts break
   downstream CSV-consuming tools that assume a flat listing.
2. *Full org and nacportal UUIDs in the filename.* Rejected -- leaks the
   UUIDs into shell history and `ls` output unnecessarily. The short form is
   enough to disambiguate locally.
3. *Store the XML `metadata` in a separate `.xml` sidecar file.* Rejected --
   splitting the response across two artifacts breaks the single-row-per-poll
   contract and complicates the DataExporter interface. The XML string is
   stored inline in the `metadata` TEXT column; downstream consumers that
   want the raw XML can select-and-dump that column.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 89**, sitting inside the
Interactive Safe cluster (60-96). The category label is "Interactive Safe --
NAC Portals".

**Rationale**:
The `.github/copilot-instructions.md` menu-range table describes the ranges
as: 1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource
Intensive, 102-123 WebSocket, 124-152 Interactive, 154-194 Destructive. This
endpoint requires the user to select *one specific* NAC portal (via
`nacportal_id`), so it is inherently interactive and belongs in 60-96 rather
than the bulk-org-export cluster at 1-59. Number 89 is a currently
unallocated integer in that range, placed near the existing NAC-related
viewers so the menu grouping is intuitive. The number is provisional -- at
`/speckit.tasks` time, MistHelper.py is grep'd for the latest allocated menu
integer and 89 is shifted forward if a conflict exists.

**Alternatives Considered**:

1. *Slot inside the bulk-safe-org-exports cluster (1-59).* Rejected -- those
   operations iterate all sites/entities in an org without user selection.
   SAML metadata requires a specific `nacportal_id`.
2. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is a
   single GET that returns a small JSON object, with no pagination and no
   long-running work. It is not resource intensive.
3. *Append after the destructive block (e.g., 195+).* Rejected -- placing a
   read-only viewer above the destructive block visually mis-signals the
   risk level to a junior NOC engineer scrolling the menu.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via
`safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"org_nac_portal_saml:org_id"`. Default: the value of `MIST_ORG_ID` in
   `.env` if present (pressing Enter accepts the default). Validated via the
   existing `is_valid_uuid()` helper before the API call; on failure, log
   `WARNING` and return early.
2. `nacportal_id` -- prompt: `"NAC Portal ID (UUID): "`, context:
   `"org_nac_portal_saml:nacportal_id"`. No `.env` default (NAC portal IDs
   are per-org and not typically pinned in `.env`). Validated via
   `is_valid_uuid()` before the API call.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.

**Rationale**:
The Mist endpoint is org- and portal-scoped, and there are no query
parameters. Site and device identifiers are not involved. The user must know
the target NAC portal by its UUID; MistHelper already exposes the bulk-list
of NAC portals via `_nac_portals` (menu path that maps to
`listOrgNacPortals`), so the natural workflow is: run that first to grab a
`nacportal_id`, then run menu 89 to fetch its SAML metadata.

**Alternatives Considered**:

1. *Auto-select the first NAC portal when the org has exactly one.* Rejected
   -- adds hidden magic; the menu design principle is explicit prompts with
   safe defaults. If the operator wants that behavior they can pipe the
   nacportal_id in via a shell one-liner.
2. *Add a prompt for output filename override.* Rejected -- adds keystrokes
   without operational value. The deterministic filename scheme in Research
   Task 3 makes results easy to find under `data/`.
3. *Prompt for a boolean "also fetch XML sibling endpoint".* Rejected -- out
   of scope for this feature. If the raw XML endpoint is needed, a separate
   spec catalogs it.
