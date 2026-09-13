# Phase 0 Research: downloadOrgNacPortalSamlMetadata

**Branch**: `572-mist-download-org-nac-portal-saml-metadata`
**Date**: 2026-06-29
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

This document captures the five Phase 0 research tasks that unblock the Phase 1
design artifacts (`data-model.md`, `quickstart.md`, `contracts/`). Every
decision below cites the enriched per-endpoint doc
`documentation/api/orgs/GET_orgs_org_id_nacportals_nacportal_id_saml_metadata.xml.md`
and the constitution file `.specify/memory/constitution.md`.

---

## Research Task 1: SDK function signature and behavior

**Decision**: Use the `mistapi` SDK function
`mistapi.api.v1.orgs.nac_portals.downloadOrgNacPortalSamlMetadata(apisession, org_id, nacportal_id)`.
The call returns a `mistapi.APIResponse` object whose `.data` attribute holds
the raw XML payload as a string (or bytes, depending on `mistapi` version);
the SDK does not pre-parse XML, so MistHelper treats the body as opaque text
for storage and parses only two attributes (`entityID` and `validUntil`) with
`xml.etree.ElementTree` for the summary row.

**Rationale**:
- The enriched doc lists the SDK path as
  `mistapi.api.v1.orgs.nac_portals.downloadOrgNacPortalSamlMetadata()`
  (snake-case module `nac_portals`, camelCase function name -- consistent
  with the rest of the mistapi SDK).
- The HTTP contract is `GET /api/v1/orgs/{org_id}/nacportals/{nacportal_id}/saml_metadata.xml`
  with two required path parameters and no query / body parameters.
- The 200 response schema declared in the enriched doc is
  `{"type": "string", "description": "File", "contentEncoding": "base64"}`
  -- a single string body. In practice the server returns the metadata as
  `application/xml`; mistapi exposes it through `APIResponse.data` without
  decoding. MistHelper therefore writes the body verbatim to a `.xml`
  sibling file and extracts only the two SAML attributes needed for SQLite
  upsert into the summary table.
- Error envelope is standard Mist: 400 / 401 / 403 / 404 / 429. Existing
  rate-limit / retry plumbing handles 429; 404 is the most common
  "wrong UUID" case and is logged at WARNING.

**Alternatives Considered**:
- *Use the JSON sibling endpoint `getOrgNacPortalSamlMetadata` instead.*
  Rejected -- the spec explicitly catalogs the `.xml` variant (operationId
  `downloadOrgNacPortalSamlMetadata`). Adding the JSON sibling is a separate
  spec (the related-endpoints section of the enriched doc lists it
  separately).
- *Parse the full XML with `xml.etree.ElementTree` and flatten every
  `<md:*>` element into its own SQLite row.* Rejected -- the SAML metadata
  document is a single logical artifact intended for direct IdP upload,
  not a queryable collection. Flattening it would create dozens of
  ad-hoc tables with no operator value and would violate the 5-Item Rule
  (>5 child entities per parent). Storing the raw XML in one column plus
  a small set of summary attributes is both simpler and more useful for
  re-import.
- *Skip the raw XML file and store XML only in SQLite.* Rejected -- the
  raison d'etre of this endpoint is direct IdP import, which expects a
  standalone `.xml` file. Writing the file to `data/` is part of the user
  story.

---

## Research Task 2: Primary Key Strategy

**Decision**: `natural_pk` with primary key columns `('org_id', 'nacportal_id')`.

**Rationale**:
- A NAC portal has exactly one SAML metadata document at any given moment.
  The tuple `(org_id, nacportal_id)` uniquely identifies the resource, and
  re-downloading it should update the row in place, not insert a duplicate.
- `org_id` and `nacportal_id` are both API-provided UUIDs that are stable
  for the life of the portal -- the textbook definition of a natural key
  per the `ENDPOINT_PRIMARY_KEY_STRATEGIES` documentation in
  `.github/copilot-instructions.md`.
- `composite_pk` is reserved for time-series rows where a timestamp is
  part of the identity. Here we explicitly want overwrite-on-refresh
  semantics, not history retention.
- `auto_increment_with_unique` is reserved for aggregated/summary data
  with no stable key. This response has a stable key, so the lighter
  natural-pk strategy is the correct fit.

**Alternatives Considered**:
- *Composite PK including `retrieved_at`.* Rejected -- would create one
  row per refresh and bloat the table with near-duplicate metadata. If
  history is ever required, a separate `org_nac_portal_saml_metadata_history`
  table can be added later without disturbing this design.
- *Include `entity_id` in the PK.* Rejected -- `entity_id` is derived
  from `nacportal_id` and adds no uniqueness. It is stored as an indexed
  attribute for searchability instead.

---

## Research Task 3: Output filename and SQLite table

**Decision**:
- **Base CSV filename**: `orgs_<org_id>_nacportals_<nacportal_id>_saml_metadata.csv`
- **Raw XML sidecar filename**: `orgs_<org_id>_nacportals_<nacportal_id>_saml_metadata.xml`
- **SQLite table name**: `org_nac_portal_saml_metadata`
- Both files land under `data/` (the only writable runtime directory per
  the Constitution).

**Rationale**:
- MistHelper's existing convention is `<scope>_<id>_<resource>.csv` where
  `<scope>` is the parent path component(s) and `<id>` is the parent
  resource id (e.g. `sites_<site_id>_devices.csv`,
  `orgs_<org_id>_nacportals.csv`). Extending the same convention to the
  two-level scope (`orgs_<org_id>_nacportals_<nacportal_id>`) produces a
  filename that is unambiguous when multiple portals are exported in
  sequence.
- The `.xml` sidecar uses the identical stem so operators can locate the
  raw payload next to its summary CSV.
- The SQLite table name `org_nac_portal_saml_metadata` follows the
  existing pattern of `<scope>_<resource>` (e.g.
  `org_licenses_summary`, `org_inventory`) -- singular `org`, no UUID in
  the table name (UUIDs are columns, not table-name fragments).
- `DataExporter.write_with_format_selection()` accepts a single base
  filename and resolves the per-backend variant; the API-function-name
  argument (`api_function_name="downloadOrgNacPortalSamlMetadata"`) is
  what `DataExporter` uses to look up the PK strategy from
  `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Alternatives Considered**:
- *Single global table `org_saml_metadata` without `nac_portal` in the
  name.* Rejected -- the NAC portal SAML metadata is distinct from any
  future org-level SAML metadata (e.g. admin SSO). Keeping the resource
  scope in the table name avoids future migrations.
- *Filename with no `org_id`.* Rejected -- collides across multiple orgs
  in the same `data/` directory.
- *Use a timestamp in the filename.* Rejected -- overwrite semantics
  match the natural-pk strategy; timestamping breaks idempotent re-runs.

---

## Research Task 4: Menu category placement and next available menu number

**Decision**: Place the new operation at menu number **96**, inside the
Interactive Safe cluster (60-96).

**Rationale**:
- The existing menu layout per `.github/copilot-instructions.md` and
  `README.md`:
  - 1-59  Safe Org Exports (single-prompt org-scoped reads)
  - 60-96  Interactive Safe (multi-prompt site/device-scoped reads)
  - 97-101, 153  Resource Intensive
  - 102-150  WebSocket / Interactive diagnostics
  - 151-152  Continuous monitoring loops
  - 154-194  Destructive
- The new operation requires **two** UUID prompts (org + nacportal),
  which places it in the Interactive Safe cluster (60-96) rather than
  the single-prompt Safe Org Exports cluster (1-59).
- 96 is the last slot in the Interactive Safe cluster and is currently
  documented as the cap of the cluster in the README menu table -- using
  it does not collide with the Resource Intensive block at 97-101.
- If concurrent feature branches consume 96 first, the task generator
  reassigns to the next free integer in the same cluster (e.g. 95-down)
  and updates the README + CHANGELOG accordingly.

**Alternatives Considered**:
- *Place at 1-59 (Safe Org Exports).* Rejected -- this cluster is for
  single-prompt org-scoped reads. Two-prompt reads belong in 60-96.
- *Place at 97-101 (Resource Intensive).* Rejected -- a single GET
  returning a bounded XML document does not qualify as
  resource-intensive.
- *Place at 154-194 (Destructive).* Rejected -- the endpoint is HTTP GET
  with no side effects; placing read-only operations in the destructive
  range would dilute the safety signal of that range.

---

## Research Task 5: Required user prompts

**Decision**: The method prompts for two values via `safe_input()`:

1. `org_id` -- defaults to the `MIST_ORG_ID` value loaded from `.env`
   when present. The prompt accepts an empty enter-key to take the
   default. `context="download_org_nac_portal_saml_metadata:org_id"`.
2. `nacportal_id` -- no `.env` default; the user must paste the UUID or
   pick from a numbered list produced by `listOrgNacPortals` when
   available in the same session.
   `context="download_org_nac_portal_saml_metadata:nacportal_id"`.

The API token (`MIST_API_TOKEN`) and host (`MIST_HOST`) are loaded from
`.env` by the existing `mistapi.APISession` bootstrap -- the method never
sees or logs them.

**Rationale**:
- `org_id` is virtually always known to the operator and is already a
  documented `.env` variable, so defaulting from `.env` matches the
  established UX in adjacent menu items.
- `nacportal_id` is not a documented `.env` variable today and there is
  no reason to add one for a per-portal export; prompting the user is
  the correct path.
- `safe_input()` is mandatory per Constitution III (Safety-First) and
  the existing pattern in `.github/copilot-instructions.md`. Explicit
  `context=` strings make EOF / cancel logs greppable.

**Alternatives Considered**:
- *Single prompt that accepts `org_id:nacportal_id` as one string.*
  Rejected -- error-prone for junior NOC engineers; two clearly-labelled
  prompts are friendlier and easier to validate independently.
- *Auto-discover all NAC portals for the org and loop.* Rejected for
  this menu item -- crosses into the resource-intensive cluster and
  expands scope. A separate "export SAML metadata for ALL portals in an
  org" item can be added later if demand emerges.
- *Read `nacportal_id` from `.env`.* Rejected -- portal IDs are not
  global per-environment constants; they are per-portal identifiers
  selected at runtime.
