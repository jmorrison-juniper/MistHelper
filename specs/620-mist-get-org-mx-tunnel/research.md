# Phase 0 Research: getOrgMxTunnel

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and implementation. Each task
follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_mxtunnels_mxtunnel_id.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical URL-derived module path:
`mistapi.api.v1.orgs.mxtunnels.getOrgMxTunnel(apisession, org_id, mxtunnel_id)`. The SDK
returns a `mistapi.APIResponse` whose `.data` attribute is the parsed JSON body. The body
is a single JSON object describing one mxtunnel (not a list, not paginated), with these
top-level keys per the response schema:

- `id` (string UUID, read-only) -- the natural primary key.
- `org_id` (string UUID, read-only).
- `site_id` (string UUID, read-only) -- present only when `for_site` is true.
- `for_site` (boolean, read-only).
- `name` (string or null).
- `protocol` (string enum: `ip`, `udp`).
- `mtu` (integer 0-1500; 0 enables PMTU).
- `hello_interval` (integer 1-300 seconds, default 60).
- `hello_retries` (integer 2-30, default 7).
- `vlan_ids` (integer array) -- VLAN IDs carried by the tunnel.
- `mxcluster_ids` (string UUID array) -- mxclusters the tunnel deploys to.
- `anchor_mxtunnel_ids` (string UUID array) -- used for edge-to-edge tunneling.
- `auto_preemption` (object: `day_of_week`, `enabled`, `time_of_day`) -- scheduled
  preemption window for non-preferred peers.
- `ipsec` (object titled `mxtunnel_ipsec`):
  - `enabled` (bool), `use_mxedge` (bool), `split_tunnel` (bool).
  - `dns_servers` (string array or null), `dns_suffix` (unique string array).
  - `extra_routes` (object array of `mxtunnel_ipsec_extra_route`: `{dest, next_hop}`).
- `created_time` (number epoch seconds, read-only).
- `modified_time` (number epoch seconds, read-only).

Required path parameters: `org_id` (UUID), `mxtunnel_id` (UUID). No query parameters,
no request body, no pagination.

**Rationale**:
The enriched doc lists the SDK as `mistapi.api.v1.orgs.mxtunnels.getOrgMxTunnel()`. This
matches the URL path one-for-one (`/orgs/{org_id}/mxtunnels/{mxtunnel_id}` ->
`mistapi.api.v1.orgs.mxtunnels`) and matches the mistapi SDK convention of generating
module paths from the URL. Final verification happens at implementation time via
`python -c "from mistapi.api.v1.orgs import mxtunnels; help(mxtunnels.getOrgMxTunnel)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against the URL.* Rejected -- the constitution forbids direct
   HTTP when a mistapi method exists.
2. *Use a hypothetical tag-derived path (`mistapi.api.v1.orgs.mxtunnels`).* This is the
   same path the URL produces, so there is no real alternative; the tag derivation
   confirms the URL derivation rather than competing with it.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **`natural_pk`** strategy for the mxtunnel summary table, and a **`composite_pk`**
strategy for the IPSec extra-routes child table:

- `org_mxtunnels`: PK = `id` (the mxtunnel UUID, supplied by the API). Type
  `natural_pk`. Secondary indexes on `org_id`, `site_id`, `name`, and `protocol`.
- `org_mxtunnel_ipsec_extra_routes`: PK = `(mxtunnel_id, dest, next_hop)`. Type
  `composite_pk`. The Mist API does not assign a stable identifier to individual extra
  routes; the natural composite of the parent tunnel UUID plus the route's destination
  and next-hop strings is the only stable key.

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses two entries: one keyed on the
operationId `getOrgMxTunnel` (summary), and one MistHelper-internal key
`getOrgMxTunnelIpsecExtraRoutes` (extra-routes sub-table).

**Rationale**:
The mxtunnel object has a real, server-supplied UUID (`id`) -- the textbook case for
`natural_pk`, identical to how MistHelper handles sites, devices, and templates. Repeat
runs of the menu item for the same mxtunnel upsert the same row cleanly. The IPSec
extra-routes array has no per-item ID, so a composite of parent UUID plus the natural
business fields (`dest`, `next_hop`) gives a deterministic primary key without inventing
a synthetic surrogate. `INSERT OR REPLACE` continues to give upsert semantics on both
tables.

**Alternatives Considered**:

1. *`auto_increment_with_unique` on both tables.* Rejected -- the mxtunnel `id` is a
   stable natural key, and using auto-increment would defeat the upsert semantics that
   the spec requires.
2. *Single combined table with a JSON-encoded `ipsec` column.* Rejected -- it breaks SQL
   queryability for extra routes and conflicts with the flattening convention used
   everywhere else in MistHelper.
3. *`composite_pk` on `(org_id, id)` for the summary.* Rejected -- the mxtunnel UUID is
   already globally unique (per Mist API semantics); adding `org_id` to the PK adds no
   uniqueness and bloats the index. `org_id` is captured as a regular column with a
   secondary index instead.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/org_<org_id_short>_mxtunnel_<mxtunnel_id_short>.csv`.
- CSV (extra routes): `data/org_<org_id_short>_mxtunnel_<mxtunnel_id_short>_ipsec_extra_routes.csv`.
- SQLite tables: `org_mxtunnels` (summary), `org_mxtunnel_ipsec_extra_routes` (child).
- `org_id_short` and `mxtunnel_id_short` are the first 8 hex characters of the
  respective UUIDs -- the convention used by adjacent exports in MistHelper for
  human-readable filenames without leaking full UUIDs into shell history.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"getOrgMxTunnel"` for the summary write and `"getOrgMxTunnelIpsecExtraRoutes"` for
the child write. Each operationId is the lookup key into
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Two output files and two SQLite tables keeps the schema clean and lets users query the
tunnel record without joining when they don't need IPSec extra routes. The naming
pattern matches the precedent set by other split-table exports in MistHelper.

**Alternatives Considered**:

1. *Single output file with JSON-encoded `ipsec` column.* Rejected for the same reasons
   as in Research Task 2 -- it breaks SQL queryability.
2. *Full UUIDs in the filename.* Rejected -- leaks tenant identifiers into shell
   history and `ls` output. The 8-character short form is enough to disambiguate.
3. *Per-org / per-tunnel directory tree.* Rejected -- the rest of MistHelper writes
   flat into `data/`, and changing the convention for one endpoint would surprise NOC
   engineers.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 96**, sitting at the boundary between Safe
Org Exports (1-95) and Interactive Safe (60-96 in the documented overlap). The category
label is "Safe Org Exports -- MxTunnels".

**Rationale**:
The `.github/copilot-instructions.md` menu range table places safe org exports through
95, with interactive safe operations spanning 60-96 and the resource-intensive cluster
starting at 97. This endpoint is a non-paginated single-object GET -- light enough to
sit in the safe block, but operator-driven (requires picking a specific mxtunnel UUID),
so the top of the safe block at 96 is the natural slot. Far from the destructive
cluster at 154-194; no risk of mis-signaling severity to a junior NOC engineer.

The number is provisional -- at `/speckit.tasks` time, MistHelper.py is grep'd for the
latest allocated menu integer and 96 is shifted forward if a conflict exists. Adjacent
mxtunnel and mxcluster operations (when added in future specs) should claim the next
integers after 96 to keep the cluster contiguous.

**Alternatives Considered**:

1. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is a single GET
   that returns a small JSON object with no pagination. It belongs in the safe block.
2. *Append to the end (e.g., 195).* Rejected -- the destructive cluster ends at 194,
   and placing a read-only mxtunnel reader above the destructive block visually
   mis-signals risk.
3. *Slot inside Interactive (124-152).* Rejected -- nothing about reading a tunnel
   record requires interactive WebSocket / show-command behavior. It is a plain
   read-only export.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context: `"org_mxtunnel:org_id"`. Default:
   `MIST_ORG_ID` from `.env` if present (Enter accepts the default). Validated via the
   existing `is_valid_uuid()` helper before the API call; on failure, log `WARNING` and
   return early.
2. `mxtunnel_id` -- prompt: `"MxTunnel ID (UUID): "`, context:
   `"org_mxtunnel:mxtunnel_id"`. Default: `MIST_MXTUNNEL_ID` from `.env` if present.
   Validated via `is_valid_uuid()` before the API call; on failure, log `WARNING` and
   return early.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.
- `MIST_MXTUNNEL_ID` -- optional default for prompt 2 (newly introduced by this menu
  item; documented in `quickstart.md` and `deploy/.env.example` will gain a commented
  example line at task time).

**Rationale**:
The endpoint is scoped to a specific mxtunnel inside a specific org; no other
identifiers are required. There are no optional query parameters for this GET, so no
third prompt is needed. Both prompts come with `.env`-backed defaults so that the
non-interactive `--menu 96` test run can succeed without operator input.

**Alternatives Considered**:

1. *Three prompts including an optional output filename override.* Rejected -- adds
   keystrokes without operational value. The deterministic filename scheme in Research
   Task 3 makes results easy to find under `data/`.
2. *Discover the mxtunnel list first, then prompt the user to pick by index.*
   Rejected for this single-endpoint spec; that interactive pattern belongs to a future
   `listOrgMxTunnels` menu item, not the direct-lookup `getOrgMxTunnel` endpoint. The
   user is expected to already have the mxtunnel UUID in hand (e.g., from the Mist UI
   or from the future list export).
