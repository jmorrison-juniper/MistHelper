# Phase 0 Research: getOrgNetwork

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and implementation. Each task
follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_networks_network_id.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.orgs.networks.getOrgNetwork(apisession, org_id, network_id)`.
The SDK returns a `mistapi.APIResponse` object whose `.data` attribute is the parsed JSON
body. The body is a single JSON object describing one Network -- not a list, not
paginated. Top-level keys per the 200 OK schema:

- `id` (string, UUID, read-only) -- unique identifier of the Network object.
- `org_id` (string, UUID, read-only) -- the owning organization.
- `name` (string, required) -- human-readable network label.
- `subnet` / `subnet6` (string, CIDR) -- IPv4 / IPv6 subnet.
- `gateway` / `gateway6` (string, IP) -- default gateway.
- `vlan_id` (object) -- VLAN identifier (may be numeric or a variable expression).
- `isolation` (boolean) -- client-to-client blocking.
- `disallow_mist_services` (boolean) -- whether Mist AP / gateway devices are excluded.
- `routed_for_networks` (string[]) -- other network names routed via this network.
- `created_time` / `modified_time` (number, epoch seconds, read-only).
- `internal_access` (object) -- `{ enabled: boolean }` scalar-only sub-object.
- `internet_access` (object) -- nested with `enabled`, `restricted`,
  `create_simple_service_policy`, and two `additionalProperties` maps:
  `destination_nat` and `static_nat` (property key is an external IP / CIDR / port).
- `multicast` (object) -- `enabled`, `disable_igmp`, plus a `groups`
  `additionalProperties` map keyed by CIDR, value `{ rp_ip }`.
- `tenants` (object) -- `additionalProperties` map keyed by tenant name, value
  `{ addresses: string[] }`.
- `vpn_access` (object) -- `additionalProperties` map keyed by VPN name, value is a
  `network_vpn_access_config` sub-object with 14 fields including nested
  `destination_nat`, `static_nat`, and `source_nat` sub-maps.

Required path parameters: `org_id` (UUID) and `network_id` (UUID). No query parameters.
No request body.

**Rationale**:
The enriched per-endpoint doc explicitly lists the SDK path as
`mistapi.api.v1.orgs.networks.getOrgNetwork()`. This is consistent with the OpenAPI URL
`/api/v1/orgs/{org_id}/networks/{network_id}` and matches how adjacent endpoints under
the same URL prefix are exposed by the SDK -- e.g. `listOrgNetworks` at
`mistapi.api.v1.orgs.networks.listOrgNetworks` (already used in `MistHelper.py` at line
16888). Final verification happens at implementation time via
`python -c "from mistapi.api.v1.orgs import networks; help(networks.getOrgNetwork)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/networks/{network_id}`.* Rejected -- the
   constitution forbids direct HTTP when a mistapi method exists.
2. *Reuse `listOrgNetworks` and filter client-side by `id`.* Rejected -- pulls the full
   network list every time (potentially hundreds of records) just to return one row,
   wasting API budget against the 5000/hour token cap. The by-ID endpoint is the correct
   tool for the by-ID use case.

## Research Task 2: Primary Key Strategy

**Decision**:
Register `getOrgNetwork` in `ENDPOINT_PRIMARY_KEY_STRATEGIES` as
**`type: natural_pk`** with `primary_key: ['id']` and secondary indexes on `org_id` and
`name`. Child `additionalProperties` maps are stored in dedicated tables with composite
primary keys that include the parent Network `id` plus the map key:

- `org_network` (parent) -- PK `id`, secondary indexes on `org_id`, `name`.
- `org_network_destination_nat` -- PK `(network_id, external_key)` where `external_key`
  is the original `additionalProperties` map key (external IP, CIDR, or port).
- `org_network_static_nat` -- PK `(network_id, external_key)`.
- `org_network_multicast_groups` -- PK `(network_id, group_cidr)`.
- `org_network_tenants` -- PK `(network_id, tenant_name)`.
- `org_network_vpn_access` -- PK `(network_id, vpn_name)`.

The primary entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` is the `getOrgNetwork` key with
`natural_pk` on `id`. Child tables are registered under MistHelper-internal identifiers
(`getOrgNetworkDestinationNat`, `getOrgNetworkStaticNat`,
`getOrgNetworkMulticastGroups`, `getOrgNetworkTenants`, `getOrgNetworkVpnAccess`) as
`composite_pk` entries, matching the pattern used elsewhere in MistHelper when a Mist
endpoint returns nested `additionalProperties` maps.

**Rationale**:
The 200 OK response contains a stable, server-generated UUID (`id`) that uniquely
identifies the Network object across polls. This is exactly the `natural_pk` case
described in `.github/copilot-instructions.md` -- it is also identical to the strategy
already in use for `listOrgNetworks` at MistHelper.py:4727 (`natural_pk` on `id`,
indexes `org_id`, `name`). Reusing the same key keeps SQLite consistent whether the
row was written from the list export or the by-ID export -- both write into the same
`org_network` table under `INSERT OR REPLACE` semantics. Child tables are needed because
`additionalProperties` maps in the OpenAPI schema have variable keys (external IPs,
tenant names, VPN names) and cannot be represented as scalar columns without flattening
into rows.

**Alternatives Considered**:

1. *`composite_pk` on `(org_id, id)`.* Rejected -- the Mist `id` is already globally
   unique (Mist assigns UUIDs from a single pool), so adding `org_id` to the PK adds
   width without adding uniqueness. `org_id` is retained as an index for scoped queries.
2. *`auto_increment_with_unique` on the whole row.* Rejected -- would accumulate
   duplicate snapshots on every poll, defeating idempotent upserts.
3. *Denormalize the nested maps into a single JSON blob column.* Rejected -- breaks SQL
   queryability, violates the flattening convention used everywhere else in MistHelper,
   and makes the ArangoDB / Redis backends inconsistent with the CSV / SQLite backend.

## Research Task 3: Output filename and SQLite table

**Decision**:

- Parent CSV: `data/org_<org_id_short>_network_<network_id_short>.csv`
- Child CSVs (one per non-empty `additionalProperties` map):
  - `data/org_<org_id_short>_network_<network_id_short>_destination_nat.csv`
  - `data/org_<org_id_short>_network_<network_id_short>_static_nat.csv`
  - `data/org_<org_id_short>_network_<network_id_short>_multicast_groups.csv`
  - `data/org_<org_id_short>_network_<network_id_short>_tenants.csv`
  - `data/org_<org_id_short>_network_<network_id_short>_vpn_access.csv`
- SQLite tables: `org_network`, `org_network_destination_nat`,
  `org_network_static_nat`, `org_network_multicast_groups`, `org_network_tenants`,
  `org_network_vpn_access`.
- `_short` is the first 8 hex characters of the respective UUID -- consistent with the
  filename convention used by adjacent org-scoped exports in `MistHelper.py`.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"getOrgNetwork"` for the parent row and the MistHelper-internal identifiers
(`getOrgNetworkDestinationNat`, etc.) for each child map. DataExporter uses these
strings as lookup keys into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
The filename encodes both the org and the specific network so multiple concurrent
exports do not collide under `data/`. The `_short` suffix keeps filenames readable in
shell history without leaking full UUIDs. Splitting the nested maps into sibling files
mirrors the SQLite table split and lets a user open just the piece they care about in
Excel or a diff tool.

**Alternatives Considered**:

1. *Single file with JSON-encoded columns for every nested map.* Rejected -- breaks SQL
   queryability, conflicts with the flattening convention, and prevents joins across
   the parent and children.
2. *Full org UUID + full network UUID in the filename.* Rejected -- 72 characters of
   UUID plus separators is unreadable at a glance in `ls` / `Get-ChildItem` output.
3. *Overwrite the same base filename regardless of `network_id`.* Rejected -- pulling
   multiple networks back-to-back would clobber earlier exports.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 58**, inside the Safe Org Exports Misc band
(56-59) of the 1-59 category range documented in `.github/copilot-instructions.md`. The
category label is "Safe Org Exports -- Networks (by ID)".

**Rationale**:
The menu range table in `.github/copilot-instructions.md` splits 1-59 into Sites (1-7),
Inventory (8-14), Device stats (15-19), Events (20-26), Clients (27-30), Gateways
(31-36), Templates (37-41), Config/Admin (42-50), SLE (51-55), and Misc (56-59). A
by-ID read of an org-level Network configuration best fits Config/Admin or Misc; the
Misc slot 58 is chosen because:

1. Menu 4 already hosts `listOrgNetworks` (the sibling list operation). Placing the
   by-ID variant nearby in the Misc slot keeps them findable in a single scroll.
2. 58 is well below the resource-intensive block at 96-101 and the destructive block at
   154-194, correctly signalling to a junior NOC engineer that the operation is safe.
3. 58 is the highest unused slot in the Safe Org Exports block that does not push into
   the Interactive Safe range (60-96), preserving room for future contiguous list-then-
   detail pairs.

The number is provisional. At `/speckit.tasks` time, `MistHelper.py` is grep'd for the
latest allocated menu integer; if 58 collides with an in-flight feature branch, the
next free integer inside the same Misc band is used and the change is reflected across
`plan.md`, `research.md`, and `contracts/get_org_network.md` in a single edit.

**Alternatives Considered**:

1. *Slot inside Templates (37-41).* Rejected -- Networks are a distinct resource type;
   grouping them under Templates would mislead operators searching for Network config.
2. *Slot inside Interactive Safe (60-96).* Rejected -- this is a plain GET with no
   long-running work or interactive follow-up beyond the two prompts required to
   identify the target; it belongs in the safe read-only block.
3. *Append to the end (e.g., 195).* Rejected -- the destructive cluster ends at 194;
   placing a read-only network read after the destructive block visually mis-signals
   the risk level.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context: `"org_network:org_id"`. Default:
   the value of `MIST_ORG_ID` in `.env` if present (pressing Enter accepts the default).
   Validated via the existing `is_valid_uuid()` helper before the API call; on failure,
   log `WARNING ("Invalid org_id ...")` and return early.
2. `network_id` -- prompt:
   `"Network ID (UUID -- run menu 4 first if you need to look this up): "`, context:
   `"org_network:network_id"`. No default (this value is not part of `.env`). Validated
   via `is_valid_uuid()` before the API call; on failure, log `WARNING` and return
   early.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.

**Rationale**:
The endpoint has exactly two required path parameters -- `org_id` and `network_id` --
and no query parameters. The prompt set therefore mirrors the URL parameters
one-for-one. Site ID, device ID, and template ID are not involved. Providing an `.env`
default for `org_id` matches the pattern used by other Safe Org Exports and lets the
menu run in a single Enter-Enter pair when the user has already picked a target network
from an earlier `listOrgNetworks` run. `network_id` intentionally has no default: it
must be a conscious selection by the operator, and forcing an explicit paste discourages
accidental repeat runs against the wrong network.

**Alternatives Considered**:

1. *Also accept a `network_name` string and resolve it to `network_id` via a client-side
   `listOrgNetworks` call.* Rejected -- doubles the API cost (a list call plus the
   by-ID call), adds a fuzzy-match branch that fights the natural-key design, and can
   fail ambiguously when two networks share the same name across sibling orgs.
2. *Auto-loop over every network in the org (like the list export does).* Rejected --
   that is exactly what `listOrgNetworks` (menu 4) already does; the by-ID endpoint
   exists to fetch a single record cheaply.
3. *Add a third prompt for output filename override.* Rejected -- adds keystrokes with
   no operational value. The deterministic filename scheme in Research Task 3 makes
   results easy to find under `data/`.
