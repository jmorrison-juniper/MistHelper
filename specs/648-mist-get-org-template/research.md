# Phase 0 Research: GetOrgTemplate

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-07-01

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/orgs/GET_orgs_org_id_templates_template_id.md` (enriched
OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical WLAN-templates
module path:
`mistapi.api.v1.orgs.wlan_templates.getOrgTemplate(apisession, org_id,
template_id)`.
The SDK returns a `mistapi.APIResponse` object whose `.data` attribute is the
parsed JSON body -- a single JSON object (not a list and not paginated) with
the following top-level keys per the doc:

- `id` (string UUID, read-only) -- template ID.
- `org_id` (string UUID, read-only) -- owning org.
- `name` (string, **required**) -- template display name.
- `created_time` (number epoch seconds, read-only).
- `modified_time` (number epoch seconds, read-only).
- `filter_by_deviceprofile` (boolean) -- whether to further filter by device
  profile.
- `deviceprofile_ids` (array of UUID strings) -- device profiles bound to this
  template.
- `applies` (object) -- where the template is applied: `org_id`, `site_ids[]`,
  `sitegroup_ids[]`.
- `exceptions` (object) -- where the template must NOT be applied (takes
  precedence): `site_ids[]`, `sitegroup_ids[]`.

Required path parameters: `org_id`, `template_id` (both UUID strings). No
query parameters. No pagination.

**Rationale**:
The enriched per-endpoint doc explicitly lists the SDK as
`mistapi.api.v1.orgs.wlan_templates.getOrgTemplate()`. Although the OpenAPI
URL segment is `templates`, the mistapi SDK groups WLAN templates under the
`wlan_templates` submodule (a naming choice made by the SDK author to
disambiguate WLAN templates from site templates, network templates, and
gateway templates -- all of which share the `templates` URL segment shape).
Final verification happens at implementation time via
`python -c "from mistapi.api.v1.orgs import wlan_templates; help(wlan_templates.getOrgTemplate)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/templates/{template_id}`.* Rejected --
   the constitution forbids direct HTTP when a mistapi method exists.
2. *Use `mistapi.api.v1.orgs.templates.getOrgTemplate()` (URL-path derived).*
   Rejected -- the enriched doc explicitly names the `wlan_templates`
   submodule, and the mistapi SDK does not expose a plain `.templates` module
   for org WLAN templates. If the runtime import fails, the fallback is
   `mistapi.api.v1.orgs.templates.getOrgTemplate()`, verified at implementation.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **natural primary key** strategy for the parent template row, plus a
**composite primary key** for a scope-mapping child table:

- `org_wlan_templates`: PK = `id` (the template UUID). Type `natural_pk`.
  Indexes: `org_id`, `name`.
- `org_wlan_template_scopes`: PK = `(template_id, scope_type, scope_id)`.
  Type `composite_pk`. Indexes: `scope_type`, `scope_id`. Foreign key
  `(template_id) -> org_wlan_templates(id)`.

The scope-mapping child table stores one row per site / sitegroup listed in
either `applies` or `exceptions`, tagged with a `scope_type` discriminator
(`applies_site`, `applies_sitegroup`, `exceptions_site`,
`exceptions_sitegroup`). This design keeps the parent row queryable without
JSON parsing.

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `natural_pk` for
the parent and a MistHelper-internal sub-table key with type `composite_pk`
for the child (Mist has no operationId for the flattened sub-array).

**Rationale**:
The Mist template object supplies a stable UUID `id` field that never changes
for the lifetime of the template -- the canonical `natural_pk` case per
`.github/copilot-instructions.md`. Re-running the menu against the same
template must upsert (`INSERT OR REPLACE`) the existing row, not append a
duplicate. The scope arrays inside `applies` and `exceptions` are variable-
length and need their own table for clean SQL queryability; the composite
`(template_id, scope_type, scope_id)` tuple is uniquely identifying and
matches the pattern used by `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries that
already exist for other endpoints with nested arrays.

**Alternatives Considered**:

1. *`auto_increment_with_unique` on parent.* Rejected -- the API supplies a
   stable UUID, so an artificial ID would violate the constitution's
   preference for natural business keys.
2. *Single flat table with JSON-encoded `applies` and `exceptions` columns.*
   Rejected -- breaks SQL queryability and conflicts with the flattening
   convention used elsewhere in MistHelper (see the license-by-site export).
3. *One child table per (applies/exceptions) x (site/sitegroup) combination
   (four tables).* Rejected -- multiplies schema surface for no gain when a
   single scope-type discriminator column solves the problem.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (parent template row): `data/org_<org_id_short>_wlan_template_<tpl_id_short>.csv`
- CSV (scope rows): `data/org_<org_id_short>_wlan_template_<tpl_id_short>_scopes.csv`
- SQLite tables: `org_wlan_templates` (parent) and `org_wlan_template_scopes`
  (child).
- `org_id_short` and `tpl_id_short` are the first 8 hex characters of the
  respective UUIDs -- the convention already used by adjacent template
  exports in MistHelper for human-readable filenames without leaking full
  UUIDs into shell history.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"getOrgTemplate"` for the
parent write and `"getOrgTemplateScopes"` (MistHelper-internal identifier)
for the child write. The DataExporter uses that string as the lookup key
into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by `listOrgTemplates` (which writes
`data/org_<short>_wlan_templates.csv`) and other org-scoped detail exports.
Two output files / two SQLite tables keeps the schema clean and mirrors the
child-table pattern established by other endpoints with nested arrays. The
short-UUID scheme keeps ls output readable and disambiguates local files
without exposing full UUIDs.

**Alternatives Considered**:

1. *Single output file with JSON-encoded `applies`, `exceptions`, and
   `deviceprofile_ids` columns.* Rejected -- breaks SQL queryability.
2. *Full UUIDs in the filename.* Rejected -- leaks UUIDs into shell history
   and ls output unnecessarily.
3. *One file per scope-type combination.* Rejected -- multiplies file count
   without operational value; the discriminator column is enough.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 58**, sitting inside the Safe Org
Exports cluster (1-59), immediately after the existing WLAN/network template
list operations at 37-41 and the licensing / SLE operations at 42-55. The
category label is "Safe Org Exports -- Templates (WLAN Template Detail)".

**Rationale**:
Per `.github/copilot-instructions.md` the menu ranges are: 1-59 Safe Org
Exports, 60-96 Interactive Safe, 97-101 + 153 Resource Intensive, 102-123
WebSocket, 124-152 Interactive, 154-194 Destructive. This endpoint is a
single GET returning one JSON object -- unambiguously safe. Placing it at 58
keeps it visually adjacent to the existing template list operations
(operations 37-41 in the same 1-59 block), well below the Resource-Intensive
threshold at 97 and far from the Destructive block at 154. The number is
provisional -- at `/speckit.tasks` time, `MistHelper.py` is grep'd for the
latest allocated menu integer and 58 is shifted forward inside the 42-59
sub-range if a conflict exists.

**Alternatives Considered**:

1. *Slot between 41 and 42 (next to `listOrgTemplates`).* Rejected -- would
   require renumbering 42-59, which touches unrelated menu items.
2. *Append to the end (e.g., 195).* Rejected -- destructive cluster ends at
   194; placing a read-only template detail lookup above the destructive
   block mis-signals risk level to a junior NOC engineer scrolling the menu.
3. *Slot inside Resource Intensive (96-101).* Rejected -- a single small GET
   is not resource intensive.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via
`safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"org_template_detail:org_id"`. Default: the value of `MIST_ORG_ID` in
   `.env` if present (pressing Enter accepts the default). Validated via the
   existing `is_valid_uuid()` helper before the API call; on failure, log
   `WARNING` and return early.
2. `template_id` -- prompt: `"WLAN Template ID (UUID): "`, context:
   `"org_template_detail:template_id"`. Default: the value of
   `MIST_TEMPLATE_ID` in `.env` if present (rarely set in practice); if
   absent, no default -- an empty answer logs a warning and exits early.
   Validated via `is_valid_uuid()` before the API call.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.
- `MIST_TEMPLATE_ID` -- optional default for prompt 2 (rare -- most callers
  will paste a UUID interactively after listing templates via the existing
  `listOrgTemplates` menu item).

**Rationale**:
The endpoint requires both `org_id` and `template_id` path parameters; both
are UUIDs, both must be validated client-side to avoid burning API quota on
malformed calls. Defaulting `org_id` from `.env` matches the convention
already used by every other org-scoped menu item. Defaulting `template_id`
from an optional `.env` variable helps the automation / test path (menu 58
in `--test` sweep can read from `.env`) while keeping the interactive path
paste-friendly. No third prompt is required -- the endpoint has no query
parameters.

**Alternatives Considered**:

1. *Pre-list templates and let the user pick by index.* Rejected -- doubles
   the API calls and duplicates functionality that `listOrgTemplates` (a
   separate menu item) already provides. Composition beats coupling.
2. *Accept the template name as an alternative to the UUID.* Rejected -- the
   Mist API does not support name-based lookup on this endpoint; adding a
   name-to-UUID resolution step would require a second API call and violates
   the "one endpoint per menu item" invariant this catalog work follows.
3. *Add an output-filename override prompt.* Rejected -- adds keystrokes
   without operational value; the deterministic filename scheme in Research
   Task 3 makes results easy to find under `data/`.
