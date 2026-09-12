# Phase 0 Research: getOrgPsk Menu Item

**Feature**: 631-mist-get-org-psk
**Date**: 2026-06-30

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Call `mistapi.api.v1.orgs.psks.getOrgPsk(apisession, org_id, psk_id)`
directly against an authenticated `mistapi.APISession` object; expect the SDK to
return a `requests.Response`-shaped wrapper whose `.data` attribute is the single
PSK JSON object (a dict, not a list).

**Rationale**: The enriched endpoint doc at
`documentation/api/orgs/GET_orgs_org_id_psks_psk_id.md` states the SDK path
`mistapi.api.v1.orgs.psks.getOrgPsk()` and documents both required path parameters
(`org_id`, `psk_id`) with no query parameters and no request body. The 200
response schema is `type: object` (single record, not an array). This mirrors the
call-shape used by the sibling `listOrgPsks` at `MistHelper.py:11993`
(`mistapi.api.v1.orgs.psks.listOrgPsks`), which is invoked through
`OrgExportUtils.export_data(api_call=..., data_type="psks", sort_key="name")`.
The tmunzer/mistapi_python SDK convention is `func(apisession, path_param_1,
path_param_2, ...)` returning a response wrapper; MistHelper elsewhere reads
`.data` off that wrapper. No client-side pagination loop is needed because the
endpoint returns exactly one object per call.

**Alternatives Considered**:
- **Raw `requests.get()` to `MIST_HOST + /api/v1/orgs/{org_id}/psks/{psk_id}`**:
  Rejected. Bypassing the SDK breaks the constitution's "sole permitted
  interface to Mist Cloud is mistapi" rule and forfeits the SDK's built-in
  retry/back-off wiring.
- **Reuse the existing `listOrgPsks` bulk export and filter client-side by
  psk_id**: Rejected. It costs an org-wide list call for a single-record fetch,
  wastes API quota, and does not exercise the dedicated GET-by-ID endpoint the
  spec is cataloging.

## Research Task 2: Primary Key Strategy

**Decision**: `natural_pk` with `primary_key=["id"]` and secondary indexes on
`org_id`, `site_id`, and `ssid`.

**Rationale**: The 200 response schema exposes `id` as a `contentEncoding: uuid`
field flagged `readOnly: true` -- the Mist-server-assigned PSK UUID that is
stable across calls. This matches the "Natural PK" pattern documented in
`.github/copilot-instructions.md` (Database Strategy section) for entities with
stable server-issued UUIDs (e.g. `sites`, `devices`). Using `id` as the natural
PK enables `INSERT OR REPLACE` upserts so repeated menu-96 runs against the same
PSK do not create duplicate rows. `org_id` is always present and indexed for
scoped lookups; `site_id` is optional (`readOnly`) and indexed to support
site-scoped joins with the graph edges added in spec 188; `ssid` is indexed
because operators commonly search PSKs by the network they bind to. The sibling
`listOrgPsks` entry at `MistHelper.py:3103` already uses the same natural-PK
shape keyed on `id`, so consistency across the PSK operation family is
preserved.

**Alternatives Considered**:
- **Composite PK on `(org_id, id)`**: Rejected. `id` is already globally unique
  in Mist; a composite key adds no protection and duplicates the org_id storage
  in every row of every index.
- **`auto_increment_with_unique`**: Rejected. This strategy is reserved for
  endpoints that return aggregated / summary rows without stable server IDs.
  The PSK object carries a first-class UUID.

## Research Task 3: Output Filename and SQLite Table

**Decision**:
- CSV / display filename: `org_psk_detail.csv`
- SQLite table: `org_psk_detail`
- Filename template passed to `DataExporter.write_with_format_selection`:
  `f"org_psk_detail_{org_id}_{psk_id}"` so multi-org / multi-psk sessions do
  not overwrite prior extractions when CSV backend is active.

**Rationale**: The naming follows the existing pattern for single-record
lookups in the org export cluster (`org_<entity>_detail` for the single-record
form vs `org_<entities>` for the bulk-list form). The bulk PSK list at menu 46
writes `org_psks` -- adding `_detail` disambiguates the two artifacts on disk
and in SQLite. Including `{org_id}_{psk_id}` in the CSV filename is required by
the DataExporter contract when the endpoint's PK includes identifiers not
otherwise visible in the row; here every row DOES contain `id` and `org_id`
columns, but the filename convention keeps parity with adjacent single-record
menus.

**Alternatives Considered**:
- **`psk_<psk_id>.csv`**: Rejected. It buries the org scope in the folder
  hierarchy and does not sort adjacent to `org_psks.csv` in a directory listing.
- **`psks_get_by_id.csv`**: Rejected. It reads as an internal operation name,
  not an operator-facing artifact label.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Register the new operation as **menu 96** in the "Interactive
Safe" category (menus 60-96 per `.github/copilot-instructions.md`).

**Rationale**: The endpoint is read-only (HTTP GET, no side effects) so it
belongs in a Safe category. It requires two interactive prompts (`org_id` and
`psk_id`), which disqualifies it from the fully-automated Safe Org Exports
range (1-59). The Interactive Safe cluster (60-96) is the correct home; the
last unclaimed slot at the top of that cluster is 96 (95 was claimed by spec
500 for `GetOrgLicenseAsyncClaimStatus`). Placing the operation at 96 keeps
the "Viewers" sub-cluster (92-96) grouped and leaves 97-101 available for the
Resource-Intensive block per the documented layout.

**Alternatives Considered**:
- **Menu 46b or inserting adjacent to 46 (`listOrgPsks`)**: Rejected. MistHelper
  uses monotonically increasing integer menu numbers. Renumbering to insert an
  adjacent slot would shift every downstream menu number, breaking automation
  scripts and prior CHANGELOG references.
- **A new Resource-Intensive slot (97-101)**: Rejected. A single-record GET is
  not resource-intensive; the operation completes in <=5s and does not iterate.

## Research Task 5: Required User Prompts (User vs .env)

**Decision**: Two prompts, both via `safe_input()`:
1. `org_id` -- prompt with a default sourced from `.env` `MIST_ORG_ID`; the user
   may press Enter to accept the default.
2. `psk_id` -- prompt with no default; the user must supply the PSK UUID. If
   `.env` defines `MIST_PSK_ID_TEST` and `--test` is active, that value is used
   without prompting.

**Rationale**: `MIST_ORG_ID` is a well-established convention across the
codebase (used by dozens of existing menu items) and is set once per operator
per environment; carrying the same default here matches operator muscle memory.
The PSK UUID, by contrast, is per-call context that the operator obtains from
the menu 46 output; there is no persistent `.env` convention for it and
carrying a stale default would silently return the wrong record. Both prompts
use `safe_input(prompt, context=...)` with context strings
`"org_psk_detail:org_id"` and `"org_psk_detail:psk_id"` so EOF in SSH /
container sessions exits cleanly per Principle III.

**Alternatives Considered**:
- **Pass both IDs as CLI flags (`--org-id`, `--psk-id`)**: Rejected. MistHelper
  is a menu-driven tool; CLI-flag parity is only added for the `--menu N`
  entry point. Adding per-endpoint flags for every menu bloats argparse.
  Automation callers already have `--menu 96` plus stdin piping of the two
  responses, which reuses the `safe_input()` path unchanged.
- **Read `psk_id` from a `.env` fallback in production runs**: Rejected. The
  PSK UUID is per-call context; a stale default is a correctness hazard. The
  `.env` fallback is scoped to `--test` mode only.
