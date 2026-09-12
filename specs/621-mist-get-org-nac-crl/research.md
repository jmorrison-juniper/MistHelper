# Phase 0 Research: getOrgNacCrl

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/orgs/GET_orgs_org_id_setting_mist_nac_crls.md` (enriched OpenAPI
doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors
the OpenAPI URL:
`mistapi.api.v1.orgs.setting.mist_nac_crls.getOrgNacCrl(apisession, org_id)`. The
SDK returns a `mistapi.APIResponse` object whose `.data` attribute is the parsed
JSON body. The body is a single JSON object (not a list, not paginated) with one
top-level key:

- `results` -- array of `nac_crl_file` objects. Each object has the following
  fields per the enriched response schema:
  - `id` (string UUID, read-only) -- "Unique ID for the uploaded CRL file, used to
    reference the file". Example: `a1ca26f3-44dd-4833-9a7b-97bbb2ab5230`.
  - `name` (string) -- "Issuer name for the CRL file". Example:
    `SampleCertificateSigner`.
  - `url` (string) -- "URL to download the uploaded CRL file".
  - `created_time` (number, epoch seconds, read-only) -- creation time.
  - `modified_time` (number, epoch seconds, read-only) -- last-modified time.

Required path parameter: `org_id` (UUID string). No query parameters. No request
body.

**Rationale**:
The enriched per-endpoint doc lists the SDK module under "mistapi SDK" as
`mistapi.api.v1.orgs.nac_crl.getOrgNacCrl()`, but the spec.md (the authoritative
feature contract) and the OpenAPI path both point to
`mistapi.api.v1.orgs.setting.mist_nac_crls`. The mistapi SDK historically generates
module paths from the URL, not from a free-form tag (verified by inspecting
adjacent setting endpoints such as `GET /orgs/{org_id}/setting/mist_scep` which
lives under `mistapi.api.v1.orgs.setting.mist_scep`). We therefore follow the
URL-derived path the spec already documents. Final verification happens at
implementation time inside the venv:

```powershell
python -c "from mistapi.api.v1.orgs.setting import mist_nac_crls; help(mist_nac_crls)"
```

If the SDK actually exposes the function under
`mistapi.api.v1.orgs.nac_crl` instead, the implementation switches to that import
path with no other change to the design (function arguments and return type are
identical across the two locations the SDK might place it).

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/setting/mist_nac_crls`.* Rejected -- the
   constitution forbids direct HTTP when a mistapi method exists. The SDK is the
   sole permitted interface to the Mist Cloud.
2. *Use the path implied by the doc's "mistapi SDK" hint
   (`mistapi.api.v1.orgs.nac_crl`).* Held as the fallback path -- the spec.md
   names the URL-derived path, and that is what we code against first. The
   implementation task will confirm with `help()` and switch only if the SDK truly
   organizes this endpoint under the tag-derived path.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **natural primary key** strategy keyed on the API-supplied UUID:

- Table: `org_nac_crl_files`
- Primary key: `id` (the API's UUID for the uploaded CRL file).
- Secondary indexes: `org_id`, `name`.

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `natural_pk`. The
`org_id` (not returned in the body) is injected by MistHelper before the upsert,
so re-running the menu against multiple orgs from the same MistHelper instance
keeps rows segregated by org while still using the stable Mist-side UUID as the
join key for the CRL itself.

**Rationale**:
The Mist API treats each uploaded CRL file as a first-class resource with a stable
UUID (`id`) -- the same UUID is referenced by the companion
`DELETE /orgs/{org_id}/setting/mist_nac_crls/{naccrl_id}` endpoint, which is the
definitive evidence that `id` is the canonical identifier. Re-running this menu
must update existing rows (e.g., when the `modified_time` ticks because an
operator re-uploaded the same issuer's CRL) rather than appending duplicates.
`INSERT OR REPLACE` on `id` provides exactly that behavior.

**Alternatives Considered**:

1. *`composite_pk` on (`org_id`, `id`).* Rejected -- `id` is already globally
   unique (Mist UUIDs do not collide across orgs). Adding `org_id` to the PK adds
   no uniqueness guarantee and forces every join to include `org_id`. Keeping
   `org_id` as a non-PK indexed column is cleaner.
2. *`auto_increment_with_unique`.* Rejected -- the API returns a stable UUID, so
   the artificial-ID strategy is unnecessary and would let repeated polls
   accumulate duplicate snapshots, defeating upsert behavior.
3. *`composite_pk` on (`org_id`, `name`).* Rejected -- `name` is the issuer name
   and is human-editable on upload; two different uploads may share the same
   issuer name with different `id` UUIDs. `id` is the authoritative key.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/org_<org_id_short>_nac_crl_files.csv`
- SQLite table: `org_nac_crl_files`
- `org_id_short` = the first 8 hex characters of the org UUID. This is the
  filename convention already in use by adjacent org-level read exports in
  MistHelper -- it keeps filenames human-readable in `ls` / Get-ChildItem output
  without leaking the full UUID into shell history.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"getOrgNacCrl"` (matching the
operationId exactly). The DataExporter uses that string as the lookup key into
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by adjacent NAC / `mist_nac_*` setting exports
(`org_<short>_nac_tags.csv`, `org_<short>_nac_rules.csv`). A single CSV / single
SQLite table is sufficient because the response shape is a flat list of homogeneous
file records -- no nested arrays to split, no need for a parent/child schema like
the async-claim-status reference design.

**Alternatives Considered**:

1. *Single output named `org_<short>_mist_nac_crls.csv` (mirroring the URL path
   segment).* Rejected -- the existing MistHelper convention strips the
   `mist_nac_` prefix from filenames because it is redundant (every file under
   `data/` is already Mist-sourced).
2. *Full org UUID in the filename.* Rejected -- leaks the org UUID into shell
   history and listings. The 8-char short form is enough to disambiguate locally.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 58**, sitting inside the Safe Org
Exports cluster (1-59) in the "Safe Org Exports -- NAC / Settings" sub-group. The
final integer is provisional and is re-checked at `/speckit.tasks` time by
grepping `MistHelper.py` for the highest currently-allocated number in that
cluster; if 58 is taken, the next free integer in the same cluster (e.g., 59, or
the first gap below 60) is used.

**Rationale**:
The menu ranges documented in `.github/copilot-instructions.md` are: 1-59 Safe Org
Exports, 60-96 Interactive Safe, 97-101 + 153 Resource Intensive, 102-123
WebSocket, 124-152 Interactive, 154-194 Destructive. This endpoint is a single
read-only GET that returns a small JSON object listing uploaded CRL files, so it
belongs in the safe block. The 51-59 range is the tail of safe org exports where
miscellaneous org-setting reads already live (license summary, license-by-site,
etc.), so 58 is the natural neighbor. Placement well below the destructive block
(154+) correctly signals to a junior NOC engineer scrolling the menu that this is
a low-risk operation.

**Alternatives Considered**:

1. *Append to the end (e.g., 195).* Rejected -- the destructive cluster ends at
   194, and placing a read-only NAC CRL list above the destructive block visually
   mis-signals risk level.
2. *Slot inside Interactive Safe (60-96).* Rejected -- the endpoint is
   non-interactive; it asks for one identifier and returns a list. It belongs in
   the safe-org-exports cluster, not the interactive cluster.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly one** value via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context: `"org_nac_crl:org_id"`.
   Default: the value of `MIST_ORG_ID` from `.env` if present (pressing Enter
   accepts the default). Validated via the existing `is_valid_uuid()` helper
   before the API call; on validation failure, log `WARNING` and return early.

`.env` values used (loaded by the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for the org_id prompt.

**Rationale**:
The endpoint is org-scoped only. There is no site, device, or template parameter,
and there are no query parameters that materially change the response shape, so a
single prompt is the minimum necessary. The implementation is simpler than the
reference (async claim status) because there is no optional `detail` flag --
keeping the prompt count to one matches the spirit of the constitution's safety
and clarity principles for a junior NOC audience.

**Alternatives Considered**:

1. *Prompt for an output filename override.* Rejected -- adds keystrokes without
   operational value. The deterministic filename scheme in Research Task 3 makes
   results easy to find under `data/`.
2. *Prompt for a name-substring filter to narrow the result list client-side.*
   Rejected -- the API returns the full list (typically <=10 entries per org) so
   filtering at output stage is unnecessary; downstream SQL on the
   `org_nac_crl_files` table handles any filter need.
