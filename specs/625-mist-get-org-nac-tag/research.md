# Phase 0 Research: getOrgNacTag

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_nactags_nactag_id.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the path documented in the
enriched doc: `mistapi.api.v1.orgs.nac_tags.getOrgNacTag(apisession, org_id,
nactag_id)`. The SDK returns a `mistapi.APIResponse` object whose `.data`
attribute is the parsed JSON body. The body is a single JSON object (not a
list, not paginated) representing one NAC tag, with the following top-level
keys per the doc:

- `id` (string UUID, read-only, always present) -- unique NAC tag identifier.
- `org_id` (string UUID, read-only) -- parent org.
- `name` (string, required) -- human-readable tag name.
- `type` (string enum, required) -- one of `egress_vlan_names`, `gbp_tag`,
  `match`, `radius_attrs`, `radius_group`, `radius_vendor_attrs`,
  `redirect_nacportal_id`, `session_timeout`, `username_attr`, `vlan`.
- `created_time` (number epoch seconds, read-only).
- `modified_time` (number epoch seconds, read-only).
- Conditional fields keyed on `type`:
  - `egress_vlan_names` (string[]) when `type==egress_vlan_names`.
  - `gbp_tag` (object) when `type==gbp_tag`.
  - `match` (string enum) and `values` (string[]) when `type==match`; also
    `match_all` (bool, default false).
  - `radius_attrs` (string[]) when `type==radius_attrs`.
  - `radius_group` (string) when `type==radius_group`.
  - `radius_vendor_attrs` (string[]) when `type==radius_vendor_attrs`.
  - `nacportal_id` (string UUID) when `type==redirect_nacportal_id`.
  - `session_timeout` (int seconds) when `type==session_timeout`.
  - `username_attr` (string enum: `automatic`, `cn`, `dns`, `email`, `upn`)
    when `type==username_attr`.
  - `vlan` (string) when `type==vlan`.
- `allow_usermac_override` (bool, default false) -- always allowed.

Required path parameters: `org_id` (UUID) and `nactag_id` (UUID). No query
parameters.

**Rationale**:
The enriched per-endpoint doc lists the SDK path explicitly as
`mistapi.api.v1.orgs.nac_tags.getOrgNacTag()`. The URL path uses `nactags`
(no underscore) but the Python module uses `nac_tags` (with underscore) --
this is a well-documented mistapi convention where camel/compound URL
segments become snake_case Python module names. Final verification happens at
implementation time via
`python -c "from mistapi.api.v1.orgs import nac_tags; help(nac_tags.getOrgNacTag)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/nactags/{nactag_id}`.* Rejected --
   the constitution forbids direct HTTP when a mistapi method exists.
2. *Use `mistapi.api.v1.orgs.nactags` (no underscore) as the module path.*
   Rejected -- the enriched doc explicitly documents `nac_tags`, and adjacent
   mistapi conventions favor snake_case module names. Verified at
   implementation.

## Research Task 2: Primary Key Strategy

**Decision**:
Use `natural_pk` on `id` (the API-provided UUID). Add an index on `org_id`
(so per-org listings from the sibling list endpoint join efficiently) and on
`name` and `type` (common human-facing filters).

`ENDPOINT_PRIMARY_KEY_STRATEGIES` entry type: `natural_pk`,
`primary_key: ['id']`, `indexes: ['org_id', 'name', 'type']`,
`table: 'org_nac_tags'`.

**Rationale**:
NAC tags are first-class Mist configuration objects with a stable
Mist-generated UUID (`id`) that never changes for the lifetime of the tag.
This matches the exact pattern used by other `natural_pk` entities such as
`listOrgSites` (documented in `.github/copilot-instructions.md` as the
canonical natural_pk example). Re-running the menu item on the same tag must
update the existing row rather than duplicate; `INSERT OR REPLACE` on the
single-column PK `id` guarantees that. Adding `org_id` to the index list
enables efficient scoping to a single org when the same SQLite file
accumulates tags from multiple orgs.

**Alternatives Considered**:

1. *`composite_pk` on `(org_id, id)`.* Rejected -- while defensively correct
   (an `id` is a UUID and therefore already globally unique), the API's `id`
   is guaranteed unique across the entire Mist installation, so the extra
   column adds nothing and complicates the PK definition. `org_id` is still
   captured as an indexed column, not a PK column.
2. *`composite_pk` on `(org_id, name)`.* Rejected -- `name` is user-editable
   (renaming a tag would create a duplicate row instead of an update).
   Business keys chosen for a PK must be stable across the object's
   lifetime, and only `id` qualifies here.
3. *`auto_increment_with_unique`.* Rejected -- explicitly documented for
   aggregated / summary data without stable keys. NAC tags have a stable
   Mist-provided UUID, so a synthetic surrogate key would be wasteful.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/org_<org_id_short>_nac_tag_<nactag_id_short>.csv`
- SQLite table: `org_nac_tags`
- `org_id_short` is the first 8 hex characters of the org UUID;
  `nactag_id_short` is the first 8 hex characters of the NAC tag UUID.
  Truncating both to 8 chars is the convention used by adjacent
  single-object viewers in MistHelper for human-readable filenames without
  leaking full UUIDs into shell history.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"getOrgNacTag"` -- matching
the operationId exactly. The DataExporter uses that string as the lookup key
into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Follows the naming pattern established by adjacent single-object viewer menus
(90-96 range). The single-record output as a one-row CSV is intentional:
operators frequently open the file directly to inspect a specific tag's
configuration and copy fields into RADIUS troubleshooting notes. The SQLite
table `org_nac_tags` is deliberately shared with the sibling list endpoint
(`listOrgNacTags` in menu 44), so listing and single-record retrieval both
upsert into the same table -- callers can then run
`SELECT * FROM org_nac_tags WHERE id = ?` without knowing which menu item
last wrote the row.

**Alternatives Considered**:

1. *Full UUIDs in filename.* Rejected -- leaks UUIDs into shell history and
   `ls` output unnecessarily. Short form is enough to disambiguate locally.
2. *Separate SQLite table per menu item (`org_nac_tag_single` vs
   `org_nac_tags_list`).* Rejected -- both endpoints return the same NAC tag
   entity shape, so a shared table is the simpler and more useful data
   model. The composite index on `org_id` handles multi-org accumulation.
3. *JSON-encoded single-column output.* Rejected -- breaks CSV queryability
   and conflicts with the flattening convention used everywhere else in
   MistHelper.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 89**, sitting inside the
Interactive Safe cluster (60-96 per `.github/copilot-instructions.md`). The
category label is "Interactive Safe -- NAC / Access Control".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu
ranges as: 1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153
Resource Intensive, 102-123 WebSocket, 124-152 Interactive, 154-194
Destructive. This endpoint requires two user-supplied UUIDs (org and tag) --
that interactive prompting pattern fits the 60-96 block rather than the
1-59 block (where operations tend to loop over the whole org without asking
for a specific object ID). The sibling list menu is at 44 in the Safe Org
Exports block, which is the correct home for "give me everything" bulk
retrieval; the single-record variant belongs in Interactive Safe. Number 89
is provisional -- at `/speckit.tasks` time, MistHelper.py is grep'd for the
latest allocated menu integer and 89 is shifted forward if a conflict
exists.

**Alternatives Considered**:

1. *Slot immediately next to menu 44 (e.g., 45).* Rejected -- 1-59 is the
   "Safe Org Exports" block for bulk retrievals that iterate without needing
   an object-specific ID prompt. This endpoint prompts for a specific
   `nactag_id`, so it belongs in Interactive Safe.
2. *Slot inside Resource Intensive (96-101).* Rejected -- single GET
   returning one small JSON object, no pagination, no long-running work.
3. *Append to the end (e.g., 195).* Rejected -- the destructive cluster ends
   at 194, and placing a read-only viewer above the destructive block
   visually mis-signals the risk level to a junior NOC engineer scrolling
   the menu.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via
`safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context: `"org_nac_tag:org_id"`.
   Default: the value of `MIST_ORG_ID` in `.env` if present (pressing Enter
   accepts the default). Validated via the existing `is_valid_uuid()` helper
   before the API call; on failure, log `WARNING` and return early.
2. `nactag_id` -- prompt: `"NAC Tag ID (UUID): "`, context:
   `"org_nac_tag:nactag_id"`. No default (there is no `.env` variable for
   NAC tag IDs, and defaulting would risk silently reading the wrong tag).
   Validated via `is_valid_uuid()`; on failure, log `WARNING` and return
   early. Operators typically obtain this UUID from a prior run of the
   sibling list menu (44) or from the Mist UI.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.

**Rationale**:
The endpoint is scoped by both `org_id` and `nactag_id` per the OpenAPI path
signature -- neither is optional and neither can be defaulted from any other
Mist context. Site, device, and template IDs are not involved. Prompting
individually (rather than accepting a combined `org_id/nactag_id` string) is
consistent with adjacent single-object viewers in MistHelper.

**Alternatives Considered**:

1. *Auto-list all NAC tags first and let the operator pick by index.*
   Rejected for the initial implementation -- adds a full second API call
   (`listOrgNacTags`) to every invocation, which defeats the point of a
   targeted single-record read. The sibling menu 44 already covers the
   "browse then pick" workflow.
2. *Accept a combined `org_id:nactag_id` colon-delimited string in one
   prompt.* Rejected -- error-prone for junior NOC engineers, and
   `safe_input()` context tags are cleaner when scoped one-per-value.
3. *Default `nactag_id` from a new `.env` variable.* Rejected -- creates
   the risk of an operator running the menu with a stale default from a
   previous investigation and reading the wrong tag.
