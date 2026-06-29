# Phase 0 Research: downloadMspSamlMetadata

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each task
follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/msps/GET_msps_msp_id_ssos_sso_id_metadata.xml.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical URL-derived module path
`mistapi.api.v1.msps.ssos.metadata_xml.downloadMspSamlMetadata(apisession, msp_id, sso_id)`
(matching the path token `metadata.xml` after `.` is normalized to `_`, as documented in
spec.md). The SDK returns a `mistapi.APIResponse` object whose `.data` attribute holds the
response body. **Critical**: the body is an XML string (`Content-Type: application/xml`),
*not* a JSON object. MistHelper must avoid passing `.data` through `json.loads`; instead
the raw string is captured as-is for the `.xml` file dump and is shallow-parsed with
`xml.etree.ElementTree.fromstring` for summary-field extraction.

Required path parameters (both UUID strings):
- `msp_id` -- identifies the Managed Service Provider.
- `sso_id` -- identifies the specific SSO configuration inside that MSP.

No query parameters. No request body. Not paginated.

Expected runtime behavior:
- Document size is typically 1-10 KB on the wire.
- The document contains an `EntityDescriptor` root element whose child
  `SPSSODescriptor` carries the SAML SP metadata (entityID, validUntil, NameIDFormat,
  SingleLogoutService, AssertionConsumerService, AttributeConsumingService).
- The same logical metadata is also available in JSON form via the sibling endpoint
  `GET /api/v1/msps/{msp_id}/ssos/{sso_id}/metadata` (operationId
  `getMspSamlMetadata`). MistHelper cataloging treats the XML and JSON variants as two
  separate menu items because IdP import tools expect the XML form byte-for-byte.

**Rationale**:
The enriched per-endpoint doc lists the SDK module as
`mistapi.api.v1.msps.sso.downloadMspSamlMetadata()` (singular `sso`), but the OpenAPI
URL uses the plural path token `/ssos/`. The mistapi SDK generator pluralizes module
paths to match the URL exactly (verified by inspecting adjacent MSP endpoints under
`/msps/{msp_id}/ssos/` which live in `mistapi.api.v1.msps.ssos.*`). The spec.md
authoritatively names `mistapi.api.v1.msps.ssos.metadata_xml`, and the dotted file
token `metadata.xml` is normalized to the Python-safe identifier `metadata_xml`. We
follow the spec. Final verification happens at implementation time via
`python -c "from mistapi.api.v1.msps.ssos import metadata_xml; help(metadata_xml)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/msps/{msp_id}/ssos/{sso_id}/metadata.xml`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method exists, and
   the mistapi `APISession` handles authentication, base URL, retries, and the
   adaptive delay metrics that the rest of MistHelper relies on.
2. *Use the JSON-metadata sibling (`getMspSamlMetadata`) and serialize back to XML
   client-side.* Rejected -- IdPs expect the canonical XML produced by Mist (correct
   `validUntil`, correct certificate fingerprint ordering, correct namespace
   declarations). Re-serializing client-side risks breaking signature validation.
3. *Use the path implied by the enriched doc (`...msps.sso.downloadMspSamlMetadata`,
   singular).* Rejected -- the SDK organizes modules by URL path (plural `ssos`),
   not the doc's prose hint, and the spec.md (the authoritative feature contract)
   names the URL-based path.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on a single output table
`msp_sso_saml_metadata`. PK = `(msp_id, sso_id)`. One row per SSO configuration, with
the row carrying the parsed summary fields (`entity_id`, `valid_until`,
`single_logout_url`, `acs_url`, `nameid_format`, `metadata_bytes`,
`metadata_sha256`, `polled_at_utc`, `raw_xml_path`).

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk`. Both
`msp_id` and `sso_id` are supplied by the user and injected before the upsert; the
API itself returns only the XML body and does not echo these IDs in the payload.

**Rationale**:
The endpoint reports the *current* SAML SP metadata for one specific SSO config. The
metadata document changes whenever the Mist-side SP certificate is rotated or
`validUntil` is advanced (typically yearly). Re-running the menu item against the
same `(msp_id, sso_id)` pair must update the existing row rather than append a
duplicate, so that the SQLite table answers "what does the current metadata look
like for this SSO?" with a single deterministic query. `(msp_id, sso_id)` is the
natural composite key because both IDs are immutable UUIDs from the API's perspective,
and together they uniquely identify the SP configuration. `INSERT OR REPLACE` upserts
every download's view of the metadata. The `metadata_sha256` field gives the operator
a cheap way to detect that the SP certificate has actually rotated between two polls.

**Alternatives Considered**:

1. *`auto_increment_with_unique`.* Rejected -- the spec requires upsert semantics on
   repeated runs (see spec.md Acceptance Scenario 3); auto-increment would let
   repeated downloads accumulate duplicate snapshots, defeating the upsert behavior.
   History tracking is handled separately by versioning the `.xml` file on disk
   (out of scope for this spec).
2. *`natural_pk` on `sso_id` alone.* Rejected -- a single MistHelper deployment may
   target multiple MSPs over the same MistHelper instance; `sso_id` is not guaranteed
   unique across MSPs.
3. *Auto-increment with `(msp_id, sso_id, metadata_sha256)` UNIQUE constraint to
   preserve history.* Rejected for v1 -- adds storage cost without a documented user
   need. The raw `.xml` files on disk already form a versioned history (the operator
   can rename them out of the way before re-running). A future spec can add a
   history table if NOC engineers ask for it.
4. *Single combined table that includes the full raw XML as a TEXT column.* Rejected
   -- bloats SQLite rows to 10 KB+ and forces ArangoDB/Redis backends to round-trip
   large strings on every read. Storing only a `raw_xml_path` reference keeps the
   summary table small; the raw XML lives on disk where IdP import tools expect it.

## Research Task 3: Output filename and SQLite table

**Decision**:

- Raw XML on disk: `data/msp_<msp_id_short>_sso_<sso_id_short>_saml_metadata.xml`
  (written byte-for-byte from the API response; this is the file an operator hands to
  the IdP).
- CSV summary: `data/msp_<msp_id_short>_sso_<sso_id_short>_saml_metadata.csv` (one row
  with the flattened summary fields plus a pointer to the `.xml` file path).
- SQLite table: `msp_sso_saml_metadata` (single table, one row per `(msp_id, sso_id)`).
- `*_short` is the first 8 hex characters of the corresponding UUID -- the convention
  used elsewhere in MistHelper for human-readable filenames without leaking full UUIDs
  into shell history.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"downloadMspSamlMetadata"` (matching the operationId verbatim). The DataExporter
uses that string as the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Splitting raw XML from the summary record matches how every IdP import tool on the
market consumes SP metadata: the operator clicks "Import metadata from file" and
selects the `.xml` file. Forcing the operator to extract the XML from a CSV cell or a
SQLite TEXT column would defeat the purpose. The summary CSV + SQLite row keeps the
operation queryable ("show me every SSO whose metadata expires within 30 days" is one
SQL `WHERE valid_until < ...`). Naming pattern matches MistHelper's existing
short-form-UUID convention.

**Alternatives Considered**:

1. *Single output that JSON-encodes the XML inside a `raw_xml` column.* Rejected --
   forces the operator to base64-decode or JSON-decode before handing the file to
   the IdP; high friction for the target NOC engineer audience.
2. *Write the raw XML into ArangoDB only and skip the disk file.* Rejected -- the
   raw XML file is the primary deliverable for an SSO setup workflow; making it
   conditional on an ArangoDB-enabled deployment would break the local dev / Podman
   container path.
3. *Full UUIDs in filenames.* Rejected -- leaks UUIDs into shell history, terminal
   scrollback, and `ls` output. Short form is enough to disambiguate locally and
   matches the rest of the codebase.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 94**, sitting inside the Safe Org Exports
cluster. The category label is "Safe Org Exports -- MSP SSO".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource Intensive,
102-123 WebSocket, 124-152 Interactive, 154-194 Destructive. MSP SSO read operations
are admin/config reads -- safe and read-only -- so they belong in the safe block. 95
is taken by the in-flight spec 500 (`getOrgLicenseAsyncClaimStatus`). 94 is the next
free integer below 95, comfortably away from both the resource-intensive block at
96-101 and the destructive block at 154-194. The number is provisional -- at
`/speckit.tasks` time, MistHelper.py is grep'd for the latest allocated menu integer
and 94 is shifted to the next free integer if a conflict exists.

**Alternatives Considered**:

1. *Slot near the destructive cluster (e.g., 155+).* Rejected -- this is a read-only
   endpoint, and placing it adjacent to destructive operations visually mis-signals
   the risk level to a junior NOC engineer scrolling the menu.
2. *Slot inside Resource Intensive (96-101).* Rejected -- this endpoint is a single
   non-paginated GET returning a small XML document. It belongs in the safe block.
3. *Slot inside Interactive (124-152).* Rejected -- the operation needs two `safe_input()`
   prompts, but so does almost every other safe-org-export operation; the
   "Interactive" range historically captures operations that drive multi-step UI
   loops (configuration wizards, packet captures, SSH session launchers), which this
   endpoint does not.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via `safe_input()`:

1. `msp_id` -- prompt: `"MSP ID (UUID): "`, context: `"msp_saml_metadata:msp_id"`.
   Default: the value of `MIST_MSP_ID` in `.env` if present (pressing Enter accepts
   the default). Validated via the existing `is_valid_uuid()` helper before the API
   call; on failure, log `WARNING` and return early.
2. `sso_id` -- prompt: `"SSO ID (UUID): "`, context: `"msp_saml_metadata:sso_id"`.
   Default: the value of `MIST_SSO_ID` in `.env` if present. Validated identically.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_MSP_ID` -- optional default for prompt 1.
- `MIST_SSO_ID` -- optional default for prompt 2.

**Rationale**:
The Mist endpoint is purely MSP-scoped: no org_id, site_id, or device_id is involved.
Both required path parameters are UUIDs that an MSP admin can fetch with one prior
call to `listMspSsos` (a separate cataloging spec). Defaulting both via `.env`
supports the common case of an operator who manages a single MSP / single SSO config
and wants the menu item to one-shot via `--menu 94` without prompts.

**Alternatives Considered**:

1. *Add a third prompt for an output filename override.* Rejected -- adds keystrokes
   without operational value. The deterministic filename scheme in Research Task 3
   makes results easy to find under `data/`, and the file path is also returned via
   the DataExporter summary row's `raw_xml_path` column.
2. *Pre-resolve `sso_id` by listing all SSOs in the MSP and presenting a picker.*
   Rejected -- couples this menu item to a separate endpoint that has not yet been
   cataloged, and adds a second API call to every invocation. A future "interactive
   picker" spec can layer that experience on top once `listMspSsos` is cataloged.
3. *Always download every SSO under the supplied MSP in one menu invocation.*
   Rejected -- breaks the one-endpoint-one-menu-item rule that the cataloging
   initiative is following.
