# Phase 0 Research: getOrgRfTemplate

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/orgs/GET_orgs_org_id_rftemplates_rftemplate_id.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the module path that mirrors the
OpenAPI URL, with the underscore normalization the SDK applies to hyphenated
resource names:
`mistapi.api.v1.orgs.rf_templates.getOrgRfTemplate(apisession, org_id,
rftemplate_id)`. The SDK returns a `mistapi.APIResponse` object whose `.data`
attribute is the parsed JSON body. The body is a single JSON object (not a
list and not paginated), with the following top-level keys per the doc:

- `id` (string, UUID, read-only) -- unique object ID inside the org
- `org_id` (string, UUID, read-only) -- owning org UUID
- `name` (string, required) -- human-readable template name
- `country_code` (string, optional) -- ISO country code applied to sites
  using this template
- `for_site` (boolean, read-only) -- whether the template is site-scoped
- `created_time` (number, epoch seconds, read-only)
- `modified_time` (number, epoch seconds, read-only)
- `scanning_enabled` (boolean) -- whether the scanning radio is enabled
- `band_24_usage` (string enum: `24`, `5`, `6`, `auto`)
- `ant_gain_24` / `ant_gain_5` / `ant_gain_6` (int32) -- top-level antenna
  gain overrides
- `band_24` / `band_5` / `band_6` (object) -- per-band radio settings
  (`allow_rrm_disable`, `ant_gain`, `antenna_mode`, `bandwidth`, `channels`,
  `disabled`, `power`, `power_max`, `power_min`, `preamble`; plus
  `standard_power` on `band_6`)
- `model_specific` (object) -- per-AP-model overrides. Property keys are AP
  model names (e.g. `"AP63"`); each value is a nested object with the same
  `band_24` / `band_5` / `band_6` shape as above.

Required path parameters: `org_id` (UUID) and `rftemplate_id` (UUID). No
query parameters. No request body.

**Rationale**:
The enriched per-endpoint doc explicitly names the SDK path as
`mistapi.api.v1.orgs.rf_templates.getOrgRfTemplate()`. Adjacent endpoints in
the same OpenAPI cluster (`GET /orgs/{org_id}/rftemplates`,
`POST /orgs/{org_id}/rftemplates`, `PUT
/orgs/{org_id}/rftemplates/{rftemplate_id}`, `DELETE
/orgs/{org_id}/rftemplates/{rftemplate_id}`) all live under the same module
namespace, confirming the SDK organizes RF templates under `rf_templates`
(underscore-separated) even though the URL uses `rftemplates` (concatenated).
The spec.md declares `mistapi.api.v1.orgs.rftemplates` for the tag; final
verification happens at implementation time via `python -c "from
mistapi.api.v1.orgs import rf_templates; help(rf_templates)"` inside the
venv, and both the underscore and concatenated forms are attempted if the
first fails.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/rftemplates/{rftemplate_id}`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method
   exists.
2. *Use the concatenated module path `mistapi.api.v1.orgs.rftemplates`
   verbatim from the spec.md.* Held as a fallback -- attempted second if the
   underscore-separated form fails. Real-world mistapi versions have shipped
   both forms in different releases.
3. *Fetch via `listOrgRfTemplates` (menu 35) then filter by ID locally.*
   Rejected -- wasteful, and does not exercise the per-ID endpoint the spec
   requires. Also loses per-template freshness because the list endpoint may
   be cached upstream.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **natural primary key** strategy on the summary table and a
**composite primary key** strategy on the model-overrides detail table:

- `org_rf_templates`: PK = `id` (the API-supplied UUID). Registered type
  `natural_pk` in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. Indexes on `org_id` and
  `name` for common lookups.
- `org_rf_template_model_overrides`: PK = `(id, model_name, band)` where
  `id` is the parent template's UUID, `model_name` is the AP model string
  key (e.g. `"AP63"`), and `band` is one of `24`, `5`, `6`. Registered type
  `composite_pk`. This lets one row exist per (template, model, band)
  combination and upserts cleanly on re-poll.

**Rationale**:
The endpoint's response schema exposes `id` as a top-level UUID with
`readOnly: true` -- exactly the stable, API-supplied identifier the
`natural_pk` strategy was designed for. Re-running the menu against the same
`(org, rftemplate_id)` pair must update the existing summary row rather than
append a duplicate, which `INSERT OR REPLACE` on `id` guarantees. The
`model_specific` sub-object is an unordered map whose keys are AP model
names, and each value carries its own `band_24` / `band_5` / `band_6`
sub-blocks; the natural composite `(id, model_name, band)` avoids
JSON-encoded blob columns and keeps the model-override table cleanly
queryable ("show me all bandwidth=80 rules for AP63" is a simple `WHERE`
clause).

**Alternatives Considered**:

1. *Composite PK on the summary table (`org_id`, `id`).* Rejected -- `id` is
   already unique per org (the OpenAPI description says "Unique ID of the
   object instance in the Mist Organization"), so `org_id` in the PK adds no
   uniqueness and would only make queries more verbose.
2. *`auto_increment_with_unique` on both tables.* Rejected -- would let
   repeated polls accumulate duplicate snapshots, defeating the upsert
   behavior the spec requires and inflating the DB over time.
3. *Store `model_specific` as a JSON-encoded TEXT column on the summary
   row.* Rejected -- breaks SQL queryability, conflicts with the flattening
   convention used everywhere else in MistHelper, and cannot participate in
   ArangoDB graph edges cleanly.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/org_<org_id_short>_rf_template_<rft_id_short>.csv`
- CSV (model overrides):
  `data/org_<org_id_short>_rf_template_<rft_id_short>_model_overrides.csv`
- SQLite tables: `org_rf_templates` (summary, one row per template) and
  `org_rf_template_model_overrides` (detail, zero-or-more rows per template)
- `org_id_short` and `rft_id_short` are the first 8 hex characters of the
  respective UUIDs -- the established MistHelper convention for
  human-readable filenames without leaking full UUIDs into shell history.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"getOrgRfTemplate"` for the
summary write (matching the operationId) and
`"getOrgRfTemplateModelOverrides"` for the model-override detail write (a
MistHelper-internal sub-table key). The DataExporter uses these strings as
lookup keys into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by adjacent template exports
(`listOrgRfTemplates` at menu 35 writes to `org_rf_templates_list.csv`, per
existing MistHelper convention). Two output files / two SQLite tables keeps
the schema clean and lets a user query the summary without joining when they
don't need per-model detail. The `rft_id_short` in the filename makes it
trivial to identify which template a file belongs to when several are
exported in the same session.

**Alternatives Considered**:

1. *Single output file with JSON-encoded `model_specific` column.* Rejected
   -- same reasoning as in Research Task 2: breaks queryability, breaks
   flattening convention.
2. *Full org and template UUIDs in the filename.* Rejected -- leaks the
   UUIDs into shell history and `ls` output unnecessarily. The short form
   is enough to disambiguate locally.
3. *Append to a single global `org_rf_templates.csv` on every run.*
   Rejected -- makes it impossible to hand a single-template CSV to a
   downstream tool without pre-filtering. The per-template file is the
   deliverable requested by the spec.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 96**. The category label is
"Interactive Safe -- Templates" (the operation requires an interactive
`rftemplate_id` prompt, so the Interactive Safe cluster is more accurate
than the Safe Org Exports cluster).

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu
ranges as: 1-59 Safe Org Exports (Templates cluster at 37-41), 60-96
Interactive Safe, 97-101 + 153 Resource Intensive, 102-123 WebSocket,
124-152 Interactive, 154-194 Destructive. `listOrgRfTemplates` already sits
at menu 35 inside Safe Org Exports because it takes only `org_id`. The new
per-template getter requires *both* `org_id` and `rftemplate_id`, making it
an Interactive Safe operation by category definition. Slot 96 is the
highest available integer in the Interactive Safe cluster (60-96) and sits
immediately below the resource-intensive block at 97-101. The number is
provisional -- at `/speckit.tasks` time, `MistHelper.py` is grep'd for the
latest allocated menu integer, and 96 is shifted forward if any of the
other in-flight feature branches (notably spec 500's proposed menu 95) has
already claimed it.

**Alternatives Considered**:

1. *Place next to `listOrgRfTemplates` at menu 36 or 42.* Rejected -- those
   slots are inside Safe Org Exports (1-59), which is reserved for
   operations that require only `org_id`. This operation requires
   `rftemplate_id` too, so it belongs in Interactive Safe (60-96).
2. *Append to the end of the menu (e.g., 195).* Rejected -- the destructive
   cluster ends at 194, and placing a read-only template getter above the
   destructive block visually mis-signals the risk level to a junior NOC
   engineer scrolling the menu.
3. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is
   a single GET that returns a small JSON object, with no pagination and
   no long-running work. It belongs in the safe block.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via
`safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"org_rf_template:org_id"`. Default: the value of `MIST_ORG_ID` in
   `.env` if present (pressing Enter accepts the default). Validated via
   the existing `is_valid_uuid()` helper before the API call; on failure,
   log `WARNING` and return early.
2. `rftemplate_id` -- prompt: `"RF Template ID (UUID): "`, context:
   `"org_rf_template:rftemplate_id"`. Default: the value of
   `MIST_RFTEMPLATE_ID` in `.env` if present (optional). Validated via
   `is_valid_uuid()` before the API call; on failure, log `WARNING` and
   return early. If the user does not know the ID, the log message advises
   running menu 35 (`listOrgRfTemplates`) first to discover it.

`.env` values used (loaded via the existing `python-dotenv` bootstrap,
never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.
- `MIST_RFTEMPLATE_ID` -- optional default for prompt 2 (new; documented in
  `.env.example`).

**Rationale**:
The endpoint is scoped to a single RF template inside a single org. Neither
site, device, nor any other identifier is involved. Both required IDs are
UUIDs, so UUID validation is a strict prerequisite before spending an API
call on a request that is guaranteed to 404. The `MIST_RFTEMPLATE_ID`
default supports the common workflow where an operator repeatedly polls the
same template while iterating on radio-plan tuning.

**Alternatives Considered**:

1. *Prompt for template name instead of ID and resolve via
   `listOrgRfTemplates` under the hood.* Rejected -- adds an extra API call
   per invocation and creates ambiguity when two templates share a name.
   The ID prompt with a `.env` default is both simpler and faster.
2. *Skip UUID validation and let the API return 404.* Rejected -- wastes an
   API call against the 5000/hour token budget and returns a less helpful
   error message. Client-side validation is documented in the Safety-First
   principle.
3. *Add a third prompt for output filename override.* Rejected -- adds
   keystrokes without operational value. The deterministic filename scheme
   in Research Task 3 makes results easy to find under `data/`.
