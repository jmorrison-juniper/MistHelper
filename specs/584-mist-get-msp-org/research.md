# Phase 0 Research: getMspOrg

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/msps/GET_msps_msp_id_orgs_org_id.md`
(enriched OpenAPI doc) and the existing mistapi SDK module path convention
observed in adjacent endpoints under `mistapi.api.v1.msps.orgs`.

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that
mirrors the OpenAPI URL: `mistapi.api.v1.msps.orgs.getMspOrg(apisession,
msp_id, org_id)`. The SDK returns a `mistapi.APIResponse` object whose `.data`
attribute is the parsed JSON body. The body is a single JSON object (not a list,
not paginated) with the following top-level keys per the doc:

- `id` (string UUID -- the org id, server-confirmed echo of the path parameter)
- `msp_id` (string UUID -- the owning MSP id, read-only)
- `name` (string -- the org display name, required)
- `msp_name` (string -- the owning MSP display name, read-only)
- `msp_logo_url` (string -- only when the MSP uploaded a logo, read-only)
- `alarmtemplate_id` (string UUID or null -- linked alarm template, optional)
- `allow_mist` (boolean -- whether Mist support can access, default `true`)
- `orggroup_ids` (string[] of UUIDs -- org-group memberships)
- `session_expiry` (int32 minutes, 10..20160, default 1440 -- web UI session
  expiry)
- `created_time` (number epoch seconds, read-only)
- `modified_time` (number epoch seconds, read-only)

Required path parameters: `msp_id` (UUID) and `org_id` (UUID). No query
parameters. No request body.

**Rationale**:
The enriched per-endpoint doc explicitly lists the SDK as
`mistapi.api.v1.msps.orgs.getMspOrg()`. The URL `/api/v1/msps/{msp_id}/orgs/
{org_id}` matches the module path one-for-one. The mistapi SDK historically
generates module paths from URL tokens (drop `/api/v1/`, replace `/` with `.`,
strip path-parameter braces), and this endpoint follows that pattern exactly.
Final verification happens at implementation time via
`python -c "from mistapi.api.v1.msps import orgs; help(orgs.getMspOrg)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/msps/{msp_id}/orgs/
   {org_id}`.* Rejected -- the constitution forbids direct HTTP when a mistapi
   method exists.
2. *Reuse the list-orgs endpoint
   (`mistapi.api.v1.msps.orgs.listMspOrgs`) and filter client-side by
   `org_id`.* Rejected -- wasteful when the user already knows the org UUID;
   `getMspOrg` is the one-call canonical path.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **natural primary key** strategy keyed on the single field `id` (the org
UUID returned by the API and echoed from the path parameter). Register in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` with type `natural_pk`, primary_key `['id']`,
and supporting indexes on `msp_id`, `name`, and `alarmtemplate_id` to support
the most common analyst queries (list all orgs for an MSP, search by name,
find orgs that share an alarm template).

```python
'getMspOrg': {
    'type': 'natural_pk',
    'primary_key': ['id'],
    'indexes': ['msp_id', 'name', 'alarmtemplate_id'],
    'table': 'msp_org',
}
```

**Rationale**:
The response carries a stable server-issued UUID in `id` that uniquely
identifies the org across the entire Mist tenancy. `INSERT OR REPLACE` on `id`
gives the correct upsert semantics: repeated polls of the same org overwrite
the prior snapshot in place. `msp_id` is indexed because the most common
follow-up query is "show all orgs managed by MSP X". `name` and
`alarmtemplate_id` are indexed because they are the next two most common
filter fields when analysts triage MSP-managed estates. Composite PK is
unnecessary because the org UUID is globally unique by Mist API contract.

**Alternatives Considered**:

1. *`composite_pk` on `(msp_id, id)`.* Rejected -- redundant; `id` alone is
   globally unique by Mist's UUID contract and pairing with `msp_id` adds key
   overhead without disambiguation value.
2. *`auto_increment_with_unique`.* Rejected -- would let repeated polls
   accumulate duplicate snapshots, defeating the upsert behavior the spec
   requires and inflating SQLite over time.
3. *`natural_pk` on `(msp_id, org_id)` reconstructed from path parameters.*
   Rejected -- the API returns `id` directly, so reconstructing the key from
   the path tokens is unnecessary indirection.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/msp_<msp_id_short>_org_<org_id_short>.csv`
- SQLite table: `msp_org`
- `*_short` is the first 8 hex characters of the corresponding UUID -- the
  established MistHelper convention for human-readable filenames that do not
  leak full UUIDs into shell history or `ls` output.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"getMspOrg"` (matching the
operationId). The DataExporter uses that string as the lookup key into
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by adjacent MSP and org-config exports. A
single SQLite table is sufficient because the response contains no nested
arrays of records (only the small scalar `orggroup_ids` UUID list, which is
flattened to a `;`-joined TEXT column per MistHelper convention for short
UUID lists). The double-UUID-short filename keeps results disambiguated when
the same operator polls orgs across multiple MSPs in one session.

**Alternatives Considered**:

1. *Single output file per MSP that accumulates rows (e.g.,
   `msp_<msp_id_short>_orgs.csv`).* Rejected -- conflicts with the existing
   `listMspOrgs` exporter (spec target) which already owns that filename. Per-
   org filename keeps the two concerns separate.
2. *Full UUIDs in the filename.* Rejected -- leaks org UUIDs into shell history
   and `ls` output unnecessarily. The 8-character prefix is enough to
   disambiguate locally.
3. *JSON-encoded `orggroup_ids` column.* Rejected -- breaks SQL queryability;
   the `;`-joined TEXT convention used elsewhere in MistHelper handles short
   UUID lists with grep- and LIKE-friendly semantics.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 94**, sitting inside the Safe Org
Exports cluster between adjacent MSP and org-config reads. The category label is
"Safe Org Exports -- MSP".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges
as: 1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource
Intensive, 102-123 WebSocket, 124-152 Interactive, 154-194 Destructive. MSP
read operations are read-only, idempotent, and bounded -- a perfect fit for
the safe-org-exports cluster. Number 95 is already proposed by feature 500
(`getOrgLicenseAsyncClaimStatus`), so 94 is the next free integer below the
resource-intensive block at 96-101 and well above the destructive block at
154-194. The number is provisional -- at `/speckit.tasks` time, `MistHelper.py`
is grep'd for the latest allocated menu integer and 94 is shifted forward if a
conflict has appeared in another in-flight feature branch.

**Alternatives Considered**:

1. *Append to the end (e.g., 195).* Rejected -- the destructive cluster ends
   at 194, and placing a read-only MSP query above the destructive block
   visually mis-signals the risk level to a junior NOC engineer scrolling the
   menu.
2. *Slot inside Resource Intensive (96-101).* Rejected -- this endpoint is a
   single GET that returns a small JSON object, with no pagination and no long-
   running work. It belongs firmly in the safe block.
3. *Slot inside the Interactive cluster (124-152).* Rejected -- the menu item
   is non-interactive after the two UUID prompts; it does not warrant the
   "interactive" category label.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via `safe_input()`:

1. `msp_id` -- prompt: `"MSP ID (UUID): "`, context: `"msp_org:msp_id"`.
   Default: the value of `MIST_MSP_ID` in `.env` if present (pressing Enter
   accepts the default). Validated via the existing `is_valid_uuid()` helper
   before the API call; on failure, log `WARNING` and return early.
2. `org_id` -- prompt: `"Org ID (UUID): "`, context: `"msp_org:org_id"`.
   Default: the value of `MIST_ORG_ID` in `.env` if present. Same validation
   path as `msp_id`.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_MSP_ID` -- optional default for prompt 1.
- `MIST_ORG_ID` -- optional default for prompt 2.

**Rationale**:
The endpoint requires both `msp_id` and `org_id` path parameters; there are no
query parameters and no body. Two prompts is the minimum that satisfies the
contract. Defaulting from `.env` lets a NOC engineer who works in a single
MSP/org context simply press Enter twice -- matching the ergonomics of adjacent
menu items. Validating both UUIDs client-side avoids burning Mist API quota on
obvious typos and gives a clean ASCII log message instead of an unhelpful 400
or 404 stack trace.

**Alternatives Considered**:

1. *Prompt only for `org_id` and discover `msp_id` via a second list call.*
   Rejected -- doubles the API cost, leaks org-to-MSP mapping for orgs that
   are not MSP-managed (which would 404 the discovery call), and removes the
   user's ability to disambiguate which MSP view of a shared org they want.
2. *Take both IDs only from `.env` and reject the menu item if either is
   unset.* Rejected -- defeats the purpose of an interactive menu and breaks
   the workflow for SSH operators who manage multiple MSP relationships from a
   single MistHelper instance.
3. *Add a third prompt for an output filename override.* Rejected -- adds
   keystrokes without operational value. The deterministic filename scheme in
   Research Task 3 makes results easy to locate under `data/`.
