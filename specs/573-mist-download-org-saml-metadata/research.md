# Phase 0 Research: downloadOrgSamlMetadata

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each task
follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_ssos_sso_id_metadata.xml.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.orgs.ssos.metadata_xml.downloadOrgSamlMetadata(apisession,
org_id, sso_id)`. The SDK returns a `mistapi.APIResponse` object. Because this endpoint
returns XML (Content-Type `application/xml` or `text/xml`) rather than JSON, the parsed
body is exposed on `response.data` as either a raw `str` (the XML document) or as bytes,
depending on the SDK version. MistHelper normalizes both shapes to a `str` before
persistence.

Required path parameters: `org_id` (UUID string) and `sso_id` (UUID string).
No query parameters. No request body.

The 200 OK response shape per the enriched doc is documented as a single string-typed
field containing the metadata XML. There is no JSON envelope and no pagination.

**Rationale**:
The enriched per-endpoint doc names the SDK as `mistapi.api.v1.orgs.sso.downloadOrgSamlMetadata()`
(singular `sso`), but the OpenAPI URL is `/api/v1/orgs/{org_id}/ssos/{sso_id}/metadata.xml`
and adjacent endpoints under the same URL path (e.g. `GET /orgs/{org_id}/ssos/{sso_id}`,
`PUT /orgs/{org_id}/ssos/{sso_id}`) live in `mistapi.api.v1.orgs.ssos`. The mistapi SDK
generates module paths from the URL, not the OpenAPI tag, so the canonical path is
`mistapi.api.v1.orgs.ssos.metadata_xml` (the `.xml` suffix becomes `_xml` in the module
name because dots are illegal in Python module names). The spec.md authoritative line
agrees. Final verification happens at implementation time via
`python -c "from mistapi.api.v1.orgs.ssos import metadata_xml; help(metadata_xml)"`
inside the venv. If the SDK exposes a slightly different name, the implementation aligns
to the SDK actual symbol and updates only the import line.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/orgs/{org_id}/ssos/{sso_id}/metadata.xml`
   with an `Authorization: Token` header.* Rejected -- the constitution forbids direct
   HTTP when a mistapi method exists, and bypassing the SDK loses the adaptive delay
   and retry hooks already wired into `mistapi.APISession`.
2. *Use the path implied by the doc tag (`...orgs.sso...`, singular).* Rejected -- the
   SDK organizes modules by URL path, not OpenAPI tag, and the URL uses the plural
   `ssos` segment.
3. *Wrap the call in a try/except that falls back to `response.raw`.* Rejected for
   Phase 0 -- the SDK contract is stable enough that an explicit shape check
   (`isinstance(body, bytes)` -> decode UTF-8) is sufficient. A fallback path adds
   complexity without a documented failure mode.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on a single output table `org_sso_saml_metadata`:

- PK = `(org_id, sso_id)` -- one row per SSO configuration per organization. The
  Mist SSO config object is a long-lived entity with a stable UUID, and SAML metadata is
  a property of that config that changes only when the operator rotates the SP entity
  (rare). Repeated polls of the same `(org_id, sso_id)` must update the existing row
  rather than append a duplicate.

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk` with
`org_id` and `sso_id` both injected by MistHelper before the upsert (the XML body
itself does not carry these IDs in a machine-friendly shape; MistHelper always knows
which IDs the call targeted).

**Rationale**:
This endpoint returns the *current* state of an SSO config's SAML metadata. A user who
polls the same config twice should see one row that updates, not two rows with
duplicate keys. `(org_id, sso_id)` is the natural business key from the URL. `INSERT OR
REPLACE` upserts every poll's view of the metadata XML, the byte count, and the
SHA-256 fingerprint -- letting an operator detect rotation by comparing fingerprints
across polls.

**Alternatives Considered**:

1. *`natural_pk` on `sso_id` alone.* Rejected -- a single MistHelper deployment may
   target multiple orgs over its lifetime; `sso_id` alone is not guaranteed unique
   across orgs (and even if it is in practice, including `org_id` makes the FK
   relationship to other org-scoped tables explicit and queryable).
2. *`auto_increment_with_unique` keyed on `(org_id, sso_id, polled_at_utc)`.* Rejected
   -- would let repeated polls accumulate duplicate snapshots, defeating the upsert
   behavior the spec requires (FR-005 + edge case "Given repeated runs ... rows upsert
   by the configured primary key strategy (no duplicates)").
3. *Hash the XML body itself as the PK.* Rejected -- two distinct SSO configs could in
   principle share a metadata document during a copy-paste rollout, which would collide
   PKs and lose data. The org+sso composite is unambiguous.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/org_<org_id_short>_sso_<sso_id_short>_saml_metadata.csv`
- SQLite table: `org_sso_saml_metadata`
- ArangoDB collection: `org_sso_saml_metadata` (same name; the polyglot backend uses
  the same identifier across stores).
- `org_id_short` and `sso_id_short` are the first 8 hex characters of each UUID,
  matching the convention used by other multi-ID exports in MistHelper for
  human-readable filenames that do not leak full UUIDs into shell history or `ls`
  output.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"downloadOrgSamlMetadata"` (matching the operationId verbatim). DataExporter uses
that string as the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

The single row written to the CSV / SQLite row carries the XML text in a `metadata_xml`
TEXT column (UTF-8). The XML is *not* parsed inside MistHelper -- it is stored verbatim
so downstream tooling (XML parsers, SAML inspectors) can consume it. A `metadata_bytes`
column carries the byte size and a `metadata_sha256` column carries a 64-char hex
fingerprint, both for change detection without parsing.

**Rationale**:
Matches the naming pattern used by other dual-ID exports in MistHelper (e.g.
`org_<short>_site_<short>_*`). A single output file / single SQLite table is sufficient
because the response is one document per SSO config -- there is no nested array to
split. Storing the XML verbatim avoids brittle in-process XML parsing and keeps the
menu method under the 5-Item Rule.

**Alternatives Considered**:

1. *Write the XML to a `.xml` sidecar file under `data/saml_metadata/` and write only
   the path + metadata into CSV / SQLite.* Rejected -- breaks single-backend semantics
   (ArangoDB / Redis would still need the body) and adds a new directory to manage. A
   single TEXT column is simpler and queryable.
2. *Parse the XML and flatten `EntityID`, `SingleLogoutService`, etc. into columns.*
   Rejected for the read-only catalog endpoint -- parsing increases blast radius (any
   schema drift in SAML 2.0 metadata could break the menu item) and consumers who
   actually need the parsed fields can run a separate parser on the stored TEXT. Spec
   FR-001 explicitly asks for the SDK call, not for SAML semantics.
3. *Full org / SSO UUIDs in the filename.* Rejected -- leaks UUIDs into shell history
   and `ls` output unnecessarily. The 8-character short form is enough to disambiguate
   locally and matches the rest of MistHelper.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 95**, sitting inside the Safe Org Exports
cluster. The category label is "Safe Org Exports -- Org SSO".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource Intensive,
102-123 WebSocket, 124-152 Interactive, 154-194 Destructive. Org-level read-only SSO
catalog operations belong inside the safe-org-export prefix. Menu number 95 is the
next contiguous integer below the resource-intensive block at 96-101, and is far
removed from the destructive cluster at 154-194 -- which matters for visual risk
signalling to a junior NOC engineer scrolling the menu. The number is provisional --
at `/speckit.tasks` time, `MistHelper.py` is grep'd for the latest allocated menu
integer and 95 is shifted forward to the next free slot if a conflict exists.

**Alternatives Considered**:

1. *Append to the end (e.g. 195).* Rejected -- the destructive cluster ends at 194, and
   placing a read-only SAML metadata download above the destructive block visually
   mis-signals the risk level to a junior NOC engineer scrolling the menu.
2. *Slot inside Resource Intensive (96-101).* Rejected -- this endpoint is a single
   non-paginated GET returning a few KB of XML. It is not resource-intensive.
3. *Slot inside Interactive (124-152).* Rejected -- the menu method is straightforward
   prompt + call + write with no extended interactive session, no multi-step
   confirmations, and no live-monitoring loop.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context: `"org_saml_metadata:org_id"`.
   Default: the value of `MIST_ORG_ID` in `.env` if present (pressing Enter accepts
   the default). Validated via the existing `is_valid_uuid()` helper before the API
   call; on failure log `WARNING` and return early.
2. `sso_id` -- prompt: `"SSO ID (UUID): "`, context: `"org_saml_metadata:sso_id"`.
   Default: the value of `MIST_SSO_ID` in `.env` if present (used by the `--test`
   sweep). Validated via `is_valid_uuid()` before the API call; on failure log
   `WARNING` and return early.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g. `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.
- `MIST_SSO_ID` -- optional default for prompt 2; primarily used to let `--test` run
  the menu non-interactively.

**Rationale**:
The endpoint takes two required path parameters and zero query parameters, so two
prompts is the minimum and the maximum needed. There is no benefit to prompting for an
output filename override (the deterministic naming scheme in Research Task 3 makes
results trivially findable under `data/`). Listing all SSO configs in the org first and
letting the user pick by index was considered but rejected -- it requires a second SDK
call (`listOrgSsos`) per menu invocation and a fall-through path when the org has no
SSO configs, both of which push the method past the 5-Item Rule.

**Alternatives Considered**:

1. *Auto-iterate: call `listOrgSsos(org_id)` first and download metadata for every SSO
   in the org.* Rejected for this spec -- belongs in a separate "bulk" menu item with
   its own spec. Keeping this menu item one-call-per-invocation matches the rest of the
   safe-org-export pattern.
2. *Accept the SSO config name instead of `sso_id` and resolve internally.* Rejected
   -- adds an extra SDK call and an extra failure mode (name collisions, name
   changes). UUIDs are the canonical identifier in MistHelper.
3. *Read both IDs only from `.env` with no prompt at all.* Rejected -- a junior NOC
   engineer in an interactive session needs the prompt to confirm what they are
   downloading, especially when the org has multiple SSO configs.
