# Phase 0 Research: getOrgWxTunnel

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-07-01

This document resolves the unknowns required before design and implementation. Each task
follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_wxtunnels_wxtunnel_id.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the module path
`mistapi.api.v1.orgs.wxtunnels.getOrgWxTunnel(apisession, org_id, wxtunnel_id)`. The SDK
returns a `mistapi.APIResponse` object whose `.data` attribute is the parsed JSON body.
The body is a single JSON object (not a list, not paginated) representing a WxLAN
Tunnel with the following top-level keys per the enriched doc:

- `id` (UUID string, read-only)
- `org_id` (UUID string, read-only)
- `site_id` (UUID string, read-only)
- `name` (string, required)
- `for_mgmt` (bool -- management-tunnel marker, immutable after create)
- `for_site` (bool, read-only)
- `is_static` (bool -- unmanaged / no control session marker, immutable)
- `hello_interval` (int 1..300, default 60)
- `hello_retries` (int 2..30, default 7)
- `hostname` (string -- optional SCCRQ hostname override)
- `router_id` (string -- optional SCCRQ router-id override)
- `secret` (string -- L2TP auth secret; empty string when no auth)
- `mtu` (int 0..1500)
- `peers` (array of strings -- remote peer IP or hostname)
- `udp_port` (int)
- `use_udp` (bool, default false)
- `created_time` (number, epoch seconds, read-only)
- `modified_time` (number, epoch seconds, read-only)
- `dmvpn` (nested object: `{enabled, holding_time, host_routes[]}`)
- `ipsec` (nested object: `{enabled, psk}` -- **`psk` is a secret**)
- `sessions` (array of `wxlan_tunnel_session` objects; each element carries
  `ap_as_session_id`, `comment`, `enable_cookie`, `ethertype`,
  `local_session_id`, `pseudo_802.1ad_enabled`, `remote_id`, `remote_session_id`,
  `use_ap_as_session_ids`)

Both `org_id` and `wxtunnel_id` are required path parameters. There are no query
parameters. There is no request body.

**Rationale**:
The enriched per-endpoint doc explicitly names the SDK path
`mistapi.api.v1.orgs.wxtunnels.getOrgWxTunnel()`. The mistapi SDK generates its module
tree from the OpenAPI URL path, and this URL (`/api/v1/orgs/{org_id}/wxtunnels/
{wxtunnel_id}`) maps one-for-one to `mistapi.api.v1.orgs.wxtunnels`. Adjacent endpoints
(`GET /orgs/{org_id}/wxtunnels`, `PUT /orgs/{org_id}/wxtunnels/{wxtunnel_id}`) confirm
the module home. Final signature verification happens at implementation time via
`python -c "from mistapi.api.v1.orgs import wxtunnels; help(wxtunnels.getOrgWxTunnel)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/wxtunnels/{wxtunnel_id}`.* Rejected -- the
   constitution forbids direct HTTP transport when a mistapi method exists.
2. *Use the sibling list endpoint (`listOrgWxTunnels`) and filter client-side.*
   Rejected -- wastes bandwidth, defeats deep linking by tunnel UUID, and duplicates
   work covered by a separate spec / menu item.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **natural primary key** strategy for the parent tunnel and a **composite primary
key** strategy for the sessions sub-array. Two separate output tables:

- `org_wxtunnels`: PK = `id` (the Mist-assigned WxTunnel UUID from the response body).
  Type `natural_pk`. Secondary indexes on `org_id`, `site_id`, and `name`.
- `org_wxtunnel_sessions`: PK = `(wxtunnel_id, remote_id)` -- one row per session inside
  a tunnel. Type `composite_pk`. `wxtunnel_id` is the parent tunnel's `id` (renamed on
  write for FK clarity); `remote_id` is documented as unique within a tunnel by the
  Mist schema. Secondary index on `wxtunnel_id`.

Register both entries in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. `INSERT OR REPLACE` semantics
guarantee that repeated retrievals upsert cleanly without duplicates.

**Rationale**:
The parent tunnel has a stable UUID (`id`) returned by the API, satisfying the
constitution's preference for natural business keys. The `sessions` array does not have
a UUID per session, but the Mist schema documents that `remote_id` is unique within a
tunnel ("Remote-id of the session, has to be unique in the same tunnel"). Pairing it
with the parent `wxtunnel_id` produces a durable composite key. This mirrors the
approach used elsewhere in MistHelper for endpoints whose response contains nested
arrays (see reference plan `500-mist-get-org-license-async-claim-status`).

**Alternatives Considered**:

1. *`auto_increment_with_unique` for the parent.* Rejected -- would let repeated
   retrievals accumulate duplicate snapshots and hide the natural UUID from consumers.
2. *Store sessions as a JSON blob column on the parent row.* Rejected -- breaks SQL
   queryability, defeats indexing on `remote_id`, and conflicts with the flattening
   convention used throughout MistHelper.
3. *Composite PK `(wxtunnel_id, local_session_id)` for sessions.* Rejected --
   `local_session_id` is documented as an integer 1..2147483647 and the API allows it
   to be omitted (only used when the session is dynamic). `remote_id` is required and
   documented as unique-within-tunnel, so it is the safer natural key.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (parent): `data/org_<org_id_short>_wxtunnel_<wxtunnel_id_short>.csv`
- CSV (sessions): `data/org_<org_id_short>_wxtunnel_<wxtunnel_id_short>_sessions.csv`
- SQLite tables: `org_wxtunnels` and `org_wxtunnel_sessions`
- `<org_id_short>` and `<wxtunnel_id_short>` are the first 8 hex characters of the
  respective UUIDs -- the convention used by adjacent template and license exports for
  human-readable filenames without leaking full UUIDs into shell history.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"getOrgWxTunnel"` for the parent row and `"getOrgWxTunnelSessions"` for the sessions
sub-array (a MistHelper-internal identifier). The DataExporter uses either string as the
lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by other WLAN / template retrieval exports. Two output
files / two SQLite tables keeps the schema clean and lets a user query the parent
tunnel without joining when they don't need per-session detail. Truncating UUIDs to
their first 8 characters is the established MistHelper convention.

**Alternatives Considered**:

1. *Single output file with a JSON-encoded `sessions` column.* Rejected -- breaks SQL
   queryability and conflicts with the flattening convention.
2. *Full UUIDs in filenames.* Rejected -- leaks UUIDs into shell history and `ls`
   output unnecessarily.
3. *Combine all WxTunnel retrieval into a single file across many `wxtunnel_id`
   calls.* Rejected -- this spec covers exactly one call; batch retrieval belongs to
   the sibling `listOrgWxTunnels` endpoint.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 59**, sitting inside the Safe Org Exports /
Templates cluster (37-59). The category label is "Safe Org Exports -- Templates".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports (Sites 1-7, Inventory 8-14, Device stats 15-19, Events 20-26,
Clients 27-30, Gateways 31-36, **Templates 37-41**, Config/Admin 42-50, SLE 51-55, Misc
56-59); 60-96 Interactive Safe; 97-101 + 153 Resource Intensive; 102-123 WebSocket;
124-152 Interactive; 154-194 Destructive. WxTunnels are an org-level template resource,
so the Templates band (37-41) is the natural home; however, that band is documented as
fully occupied. Slot 59 is the last available integer in the wider Safe Org Exports
range, sitting just below the boundary at 60, and is consistent with placing a
read-only detail retrieval among the safe exports. The number is provisional -- at
`/speckit.tasks` time, MistHelper.py is grep'd for the latest allocated menu integer
and 59 is shifted forward if a conflict exists with an in-flight feature branch.

**Alternatives Considered**:

1. *Slot inside 37-41 (Templates band).* Rejected -- documented as full; renumbering
   adjacent operations creates unnecessary churn in the menu registration table.
2. *Append to the end (e.g., 195).* Rejected -- the destructive cluster ends at 194,
   and placing a read-only tunnel-detail retrieval above the destructive block
   visually mis-signals the risk level to a junior NOC engineer scrolling the menu.
3. *Slot inside Resource Intensive (96-101).* Rejected -- this endpoint is a single
   GET returning a small JSON object, with no pagination and no long-running work. It
   belongs in the safe block.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context: `"org_wx_tunnel:org_id"`.
   Default: the value of `MIST_ORG_ID` in `.env` if present (pressing Enter accepts
   the default). Validated via the existing `is_valid_uuid()` helper before the API
   call; on failure, log `WARNING` and return early.
2. `wxtunnel_id` -- prompt: `"WxTunnel ID (UUID): "`, context:
   `"org_wx_tunnel:wxtunnel_id"`. No default; the user must supply this each run
   because it is the identity of the resource being fetched. Validated the same way;
   on failure, `WARNING` and early return.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.

**Rationale**:
The endpoint is scoped to a specific WxTunnel by UUID. Both path parameters are
required by the OpenAPI contract, so both must be collected. Providing a default for
`org_id` is standard MistHelper practice; a default for `wxtunnel_id` would be
misleading because a WxTunnel is not a per-tenant singleton. There are no query
parameters, so no additional prompts are needed.

**Alternatives Considered**:

1. *Auto-discover the WxTunnel by name via `listOrgWxTunnels` and prompt for a name
   instead of a UUID.* Rejected -- expands scope beyond the single-endpoint contract
   in the spec, adds an extra API call, and complicates the safety-first UUID
   validation. Name-based lookup can be a separate menu item if operators request it.
2. *Prompt for a filename override for the CSV output.* Rejected -- adds keystrokes
   without operational value; the deterministic scheme in Research Task 3 keeps
   results easy to find under `data/`.
