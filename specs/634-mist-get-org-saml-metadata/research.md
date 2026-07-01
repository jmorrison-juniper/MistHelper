# Phase 0 Research: getOrgSamlMetadata

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_ssos_sso_id_metadata.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the module path that mirrors the OpenAPI
URL: `mistapi.api.v1.orgs.ssos.metadata.getOrgSamlMetadata(apisession, org_id,
sso_id)`. The SDK returns a `mistapi.APIResponse` object whose `.data` attribute is
the parsed JSON body. The body is a single JSON object (not a list, not paginated)
with the following top-level keys per the enriched doc:

- `acs_url` (string) -- SAML Assertion Consumer Service URL, present when
  `idp_type == "saml"`. Example: `https://api.mist.com/api/v1/saml/llDfa13f/login`.
- `entity_id` (string) -- SAML SP entity ID, present when `idp_type == "saml"`.
- `logout_url` (string) -- SAML single-logout URL, present when
  `idp_type == "saml"`. Example: `https://api.mist.com/api/v1/saml/llDfa13f/logout`.
- `metadata` (string) -- The complete SAML SP metadata as a single XML document
  (multi-line, potentially several KB), present when `idp_type == "saml"`.
- `scim_base_url` (string) -- SCIM provisioning base URL, present only when
  `idp_type == "oauth"` AND `scim_enabled == true`.

Required path parameters: `org_id` (UUID string), `sso_id` (UUID string).
Query parameters: none.

**Rationale**:
The enriched per-endpoint doc lists the SDK module as
`mistapi.api.v1.orgs.sso.getOrgSamlMetadata()` (singular `sso`), but the OpenAPI URL
uses the plural `ssos` collection and the metadata sub-resource
(`/orgs/{org_id}/ssos/{sso_id}/metadata`). The spec.md explicitly names
`mistapi.api.v1.orgs.ssos.metadata` and that path matches the URL one-for-one, so we
follow the spec. The mistapi SDK historically generates module paths from the URL,
not the OpenAPI tag (verified by inspecting adjacent endpoints whose URL segments
match their SDK dotted paths). Final verification happens at implementation time
via `python -c "from mistapi.api.v1.orgs.ssos import metadata; help(metadata)"`
inside the venv; if the actual attribute name differs, the caller uses whichever of
the two candidate paths resolves.

The response is a small object (five string fields), so no pagination handling,
streaming, or chunking is required.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/ssos/{sso_id}/metadata`.* Rejected -- the
   constitution forbids direct HTTP when a mistapi method exists.
2. *Use the XML variant endpoint
   (`GET /api/v1/orgs/{org_id}/ssos/{sso_id}/metadata.xml`).* Rejected -- the
   feature spec targets the JSON variant. The XML variant returns
   `Content-Type: application/xml` (a raw XML document, not a JSON object), which
   would need a different flattening path. A follow-up spec can catalog the XML
   variant separately.
3. *Use the path implied by the enriched doc (`...orgs.sso...`, singular).*
   Rejected -- the spec.md (the authoritative feature contract) names the
   URL-based path with plural `ssos`. If the SDK actually publishes the singular
   form, implementation-time verification catches it.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on a single output table
`org_sso_saml_metadata`, with PK = `(org_id, sso_id)`. Register the operation in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` with `type: 'composite_pk'`.

The `org_id` is injected by MistHelper before the upsert (the response body does not
contain `org_id`, but MistHelper always knows which org the call targeted). The
`sso_id` is likewise injected from the request context (the response body does not
contain `sso_id` either).

**Rationale**:
The endpoint returns exactly one metadata object per (org, SSO configuration) tuple.
Repeated calls for the same SSO configuration must upsert the same row (metadata
may rotate when the SP re-signs its assertions, so the row content can change but
the identity is stable). `(org_id, sso_id)` is the natural business key -- both are
UUIDs assigned by Mist and never reused. `INSERT OR REPLACE` under this composite
key gives correct upsert semantics on every poll.

**Alternatives Considered**:

1. *`natural_pk` on `sso_id` alone.* Rejected -- a single MistHelper deployment may
   target multiple orgs; `sso_id` in isolation is not guaranteed unique across
   orgs (Mist reuses UUID namespaces per org).
2. *`auto_increment_with_unique`.* Rejected -- would let repeated polls accumulate
   duplicate snapshots (the metadata blob is several KB per row), inflating the
   SQLite file without value.
3. *Composite key including `entity_id` from the response.* Rejected --
   `entity_id` is derived from `sso_id` (it embeds the SSO short-id in the URL),
   so including it in the PK adds noise without adding uniqueness. Kept as an
   indexed column instead.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/org_<org_id_short>_sso_<sso_id_short>_saml_metadata.csv`
- SQLite table: `org_sso_saml_metadata`
- `org_id_short` = first 8 hex characters of the org UUID.
- `sso_id_short` = first 8 hex characters of the SSO UUID.
- CSV output uses `csv.QUOTE_ALL` quoting (the `metadata` column contains embedded
  newlines from the XML blob; standard minimal quoting would break the row on
  parse). The existing `DataExporter` already enforces `QUOTE_ALL` for TEXT columns
  containing newline characters.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"getOrgSamlMetadata"` (matching the
operationId). The DataExporter uses that string as the lookup key into
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
The short-UUID naming pattern matches adjacent org-scoped exports in MistHelper
(e.g., license and SSO-config exports) and keeps filenames human-scannable in `ls`
output without leaking full UUIDs into shell history. Including both short IDs in
the filename lets the user run the menu item repeatedly for different SSO
configurations within the same org and get distinct files on disk (SQLite still
consolidates into one table via the composite PK).

**Alternatives Considered**:

1. *Emit the raw XML blob to a separate `.xml` file and store only the URL fields
   in CSV.* Rejected -- would introduce a two-artifact export that is inconsistent
   with the rest of MistHelper (every other menu item emits exactly one CSV per
   logical entity table). Users who want just the XML can `SELECT metadata FROM
   org_sso_saml_metadata WHERE ...` from SQLite, or open the CSV in a tool that
   handles quoted multi-line fields (Excel, LibreOffice, `csv` module).
2. *Full org and SSO UUIDs in the filename.* Rejected -- leaks UUIDs into shell
   history and `ls` output. Short prefix is enough to disambiguate locally.
3. *Single-file monolith table for all SSO-related endpoints (metadata, config,
   etc.).* Rejected -- each endpoint has a distinct response schema and a
   distinct PK strategy. One table per endpoint keeps schema stable and
   queryable.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 58**, sitting inside the Safe Org
Exports cluster (1-59) and adjacent to the existing Config/Admin sub-cluster
(roughly menu 42-50). The category label is "Safe Org Exports -- SSO / SAML".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource Intensive,
102-123 WebSocket, 124-152 Interactive, 154-194 Destructive. SSO configuration data
is org-admin metadata (read-only, low-risk, non-paginated), which fits the safe
export band. Menu 58 is the last free integer in the 1-59 band before the boundary
into the Interactive Safe cluster, and it sits above the existing Config/Admin
sub-cluster (42-50) so the SSO-related items form a small, discoverable tail. The
number is provisional -- at `/speckit.tasks` time, `MistHelper.py` is grep'd for the
latest allocated menu integer and 58 is shifted forward (still within 1-59) if a
conflict exists.

**Alternatives Considered**:

1. *Slot inside Interactive Safe (60-96).* Rejected -- this endpoint is a
   non-interactive, one-shot org export. It belongs in the safe-export band.
2. *Append to the end (e.g., 195).* Rejected -- the destructive cluster ends at
   194, and placing a read-only SSO export above the destructive block visually
   mis-signals the risk level to a junior NOC engineer scrolling the menu.
3. *Slot inside Resource Intensive (97-101).* Rejected -- single non-paginated
   GET returning a few-KB JSON object; nothing about this endpoint qualifies as
   resource intensive.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"org_saml_metadata:org_id"`. Default: the value of `MIST_ORG_ID` in `.env` if
   present (pressing Enter accepts the default). Validated via the existing
   `is_valid_uuid()` helper before the API call; on failure, log `WARNING` and
   return early.
2. `sso_id` -- prompt: `"SSO ID (UUID): "`, context:
   `"org_saml_metadata:sso_id"`. Default: the value of `MIST_SSO_ID` in `.env` if
   present (new optional variable; if absent, no default and the user must supply
   the value). Validated via `is_valid_uuid()` before the API call; on failure,
   log `WARNING` and return early. The user can discover their SSO IDs via the
   existing `listOrgSsos` menu item, so no discovery flow is embedded here.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.
- `MIST_SSO_ID` -- optional default for prompt 2 (new; documented in
  `deploy/.env.example` at implementation time).

**Rationale**:
This endpoint is scoped to a single (org, SSO configuration) pair. Site, device,
and template IDs are not involved. Two prompts is the minimum needed to hit the
endpoint; adding an output-filename override or a format-selection prompt would
add keystrokes without operational value (the deterministic filename scheme in
Research Task 3 makes results easy to find, and format selection is already a
global MistHelper setting, not a per-menu-item toggle).

**Alternatives Considered**:

1. *Auto-loop over every SSO in the org (call `listOrgSsos` first, then iterate).*
   Rejected -- adds a chained API call and a batch behavior that is not what the
   spec describes. A follow-up "export all SAML metadata for org" menu item can
   be added later as a distinct spec.
2. *Prompt for `sso_id` only if not in `.env`, silently use the `.env` default
   otherwise.* Rejected -- the user should see the effective SSO ID at every run
   for auditability. The prompt shows the default and the user can accept with
   Enter.
3. *Add a third prompt for an output filename override.* Rejected -- adds
   keystrokes without operational value. The deterministic filename scheme in
   Research Task 3 makes results easy to find under `data/`.
