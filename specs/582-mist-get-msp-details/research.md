# Phase 0 Research: getMspDetails

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each task
follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/msps/GET_msps_msp_id.md` (enriched OpenAPI
doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at:
`mistapi.api.v1.msps.msps.getMspDetails(apisession, msp_id)`. The SDK returns a
`mistapi.APIResponse` object whose `.data` attribute is the parsed JSON body. The body
is a single JSON object (not a list, not paginated) with the following top-level
fields per the doc:

- `id` (string UUID) -- unique MSP identifier; stable across calls
- `name` (string) -- MSP display name
- `tier` (string enum: `advanced`, `base`)
- `allow_mist` (boolean)
- `logo_url` (string; advanced tier / uMSPs only)
- `url` (string; advanced tier / uMSPs only)
- `created_time` (number, epoch seconds, readOnly)
- `modified_time` (number, epoch seconds, readOnly)

Required path parameter: `msp_id` (UUID string). No query parameters. No request body.

**Rationale**:
The enriched per-endpoint doc explicitly lists the SDK call as
`mistapi.api.v1.msps.msps.getMspDetails()`. The double-`msps` path segment is the
mistapi convention for tag-scoped modules (`mistapi.api.v1.<tag>.<module>.<operation>`)
and matches existing MistHelper calls into the same package. Final verification happens
at implementation time via `python -c "from mistapi.api.v1.msps import msps;
help(msps.getMspDetails)"` inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/msps/{msp_id}`.* Rejected --
   the constitution forbids direct HTTP when a mistapi method exists.
2. *Use the OrgConfigExporter shortcut to MSP listing already wired at menu 56.*
   Rejected -- menu 56 calls a different operation (`listOrgMsps` / org-level MSP
   config); `getMspDetails` returns the canonical per-MSP record and the spec requires
   that exact operationId.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **natural primary key** (`natural_pk`) strategy on a single output table
`msp_details`, with `PRIMARY KEY (id)` -- the UUID supplied by the API in the response
body. The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `natural_pk`,
`primary_key: ['id']`, and indexes `['tier', 'name']` for the two most likely query
patterns (filter MSPs by tier, look up by display name).

**Rationale**:
Per the response schema, `id` is a stable UUID assigned by Mist at MSP creation and is
guaranteed unique across the Mist cloud. Re-polling the same `msp_id` returns the same
`id` value, so `INSERT OR REPLACE` keyed on `id` cleanly upserts the latest snapshot.
This matches the strategy used by sibling natural-key entities such as `listOrgSites`
(PK = `['id']`) and `listOrgDevices` (PK = `['id']`).

**Alternatives Considered**:

1. *`composite_pk` on `(id, modified_time)`.* Rejected -- would let every config edit
   accumulate a new row, defeating the upsert behavior the spec requires (FR-005). The
   user wants the *current* MSP record, not a history table.
2. *`auto_increment_with_unique` with surrogate `misthelper_internal_id`.* Rejected --
   `id` is already a stable natural key, so introducing a surrogate adds no value and
   complicates joins to future MSP-scoped sub-tables (admins, orgs, SSOs).
3. *`natural_pk` on `name`.* Rejected -- MSP `name` is mutable; using it as the PK
   would mis-attribute history after a rename.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/msp_<msp_id_short>_details.csv`
- SQLite table: `msp_details`
- `msp_id_short` is the first 8 hex characters of the MSP UUID -- already the
  convention used by adjacent exports (e.g. `org_<org_id_short>_*.csv`) for
  human-readable filenames without leaking full UUIDs into shell history.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"getMspDetails"` (matching the operationId). DataExporter uses that string as the
lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming convention used by every other per-entity export in MistHelper. A
single output table is sufficient because the response is one flat JSON object -- no
nested arrays require splitting into sub-tables (contrast with the license-claim-status
endpoint which has a `details[]` array). The short UUID prefix in the filename keeps
shell completion useful while disambiguating across multiple MSPs.

**Alternatives Considered**:

1. *Full MSP UUID in the filename.* Rejected -- leaks identifiers into shell history
   and `ls` output unnecessarily; the 8-char prefix is enough to disambiguate locally.
2. *Single shared `msp` table holding all MSPs.* Accepted -- this is the SQLite layout.
   Each invocation upserts one row into `msp_details` by `id`; multiple runs against
   different MSPs accumulate cleanly in one table for cross-MSP queries.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 95**, sitting inside the Safe Org Exports
cluster between the existing org-config exports and the resource-intensive cluster that
begins at 96. The category label is "Safe Org Exports -- MSP".

**Rationale**:
Per `.github/copilot-instructions.md`, menu ranges are: 1-59 Safe Org Exports, 60-96
Interactive Safe, 97-101 + 153 Resource Intensive, 102-123 WebSocket, 124-152
Interactive, 154-194 Destructive. The MSP detail endpoint is read-only, returns a small
flat object, and is non-paginated, so it belongs squarely in the safe block. Menu 95
is the next contiguous integer below the resource-intensive boundary and far from any
destructive operations. Adjacent menu 56 (`OrgConfigExporter.msp`) already touches
MSP-related org config, so placing the new method on the same class and in the same
cluster keeps MSP behavior co-located. The number is provisional -- at
`/speckit.tasks` time, `MistHelper.py` is grep'd for the latest allocated menu integer
and 95 is shifted forward by one if a conflict exists with an in-flight feature branch.

**Alternatives Considered**:

1. *Append to the end (e.g., 195).* Rejected -- the destructive cluster ends at 194,
   and placing a read-only MSP lookup above the destructive block visually mis-signals
   the risk level to a junior NOC engineer scrolling the menu.
2. *Slot inside Resource Intensive (96-101).* Rejected -- this endpoint is a single
   GET that returns one tiny JSON object with no pagination. It does not belong in the
   heavy / long-running block.
3. *Co-locate with menu 56 by inserting at 57.* Rejected -- inserting in the middle of
   the existing 1-94 range would shift every subsequent menu number, breaking saved
   user automation scripts that reference numbered menu items.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly one** value via `safe_input()`:

1. `msp_id` -- prompt: `"MSP ID (UUID): "`, context: `"msp_details:msp_id"`.
   Default: the value of `MIST_MSP_ID` in `.env` if present (pressing Enter accepts
   the default). Validated via the existing `is_valid_uuid()` helper before the API
   call; on validation failure, log `WARNING` and return early.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_MSP_ID` -- optional default for the single prompt above.

**Rationale**:
The endpoint is MSP-scoped and takes a single path parameter. No org, site, or device
IDs are involved. Adding optional secondary prompts would inflate keystrokes without
operational value -- the operationId returns the complete MSP record in one call. The
`.env` default makes the menu usable from non-interactive CI / `--test` sweeps without
requiring a TTY.

**Alternatives Considered**:

1. *Add a prompt to also fetch the linked org list (`GET /msps/{msp_id}/orgs`) in the
   same menu item.* Rejected -- that is a different operationId
   (`listMspOrgs`) and out of scope for this spec. A future spec can chain the two.
2. *Add a prompt for an output filename override.* Rejected -- adds keystrokes without
   operational value; the deterministic filename scheme in Research Task 3 makes
   results easy to find under `data/`.
3. *No prompt at all -- require `MIST_MSP_ID` in `.env`.* Rejected -- the constitution
   prefers interactive prompts with `.env` defaults so a junior NOC engineer can run
   the menu against any MSP they have access to without editing `.env` first.
