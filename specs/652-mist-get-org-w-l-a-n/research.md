# Phase 0 Research: getOrgWLAN

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-07-01

This document resolves the unknowns required before design and implementation. Each task
follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_wlans_wlan_id.md`
(enriched OpenAPI doc, ~2040 lines including full 200 OK schema and SDK/Errors sections).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL:
`mistapi.api.v1.orgs.wlans.getOrgWLAN(apisession, org_id, wlan_id)`. The SDK returns a
`mistapi.APIResponse` object whose `.data` attribute is the parsed JSON body. The body
is a single JSON object (not a list, not paginated) representing the full WLAN
configuration document. Top-level keys observed in the enriched schema include:

- Identity / audit: `id`, `org_id`, `site_id`, `msp_id`, `for_site`, `created_time`,
  `modified_time`.
- Radio: `band`, `bands`, `band_steer`, `disable_ht_vht_rates`, `dtim`, `rateset`,
  `roam_mode`.
- SSID / visibility: `ssid` (present in the full schema although trimmed here for brevity),
  `hide_ssid`, `enabled`, `apply_to`, `interface`.
- Authentication: `auth` (nested object -- `type`, `psk`, `eap_reauth`, etc.),
  `auth_servers`, `acct_servers`, `coa_servers`, `auth_servers_nas_id`,
  `auth_servers_nas_ip`, `auth_servers_retries`, `auth_servers_timeout`,
  `auth_server_selection`, `disable_message_authenticator_check`, `mist_nac`,
  `radsec`, `dynamic_psk`, `dynamic_vlan`, `enable_local_keycaching`.
- Accounting: `acct_immediate_update`, `acct_interim_interval`.
- Access control: `allow_mdns`, `allow_ssdp`, `arp_filter`, `bonjour`,
  `block_blacklist_clients`, `isolation`, `max_num_clients`, `max_idletime`,
  `client_limit_up`, `client_limit_down`, `client_limit_up_enabled`,
  `client_limit_down_enabled`, `app_limit`, `app_qos`, `qos`.
- Portal / captive: `portal`, `portal_allowed_hostnames`, `portal_allowed_subnets`,
  `portal_api_secret`, `portal_denied_hostnames`, `portal_image`, `portal_sso_url`,
  `portal_template_url`, `cisco_cwa`, `airwatch`.
- Overlay / tunneling: `mxtunnel_id`, `mxtunnel_ids`, `mxtunnel_name`,
  `disable_when_gateway_unreachable`, `disable_when_mxtunnel_down`,
  `reconnect_clients_when_roaming_mxcluster`.
- Scheduling / lifecycle: `schedule`, `sle_excluded`, `no_static_dns`, `no_static_ip`,
  `dns_server_rewrite`, `hostname_ie`, `limit_bcast`, `limit_probe_response`,
  `legacy_overds`, `enable_wireless_bridging`,
  `enable_wireless_bridging_dhcp_tracking`, `ap_ids`, `disable_uapsd`,
  `disable_wmm`.

Required path parameters: `org_id` (UUID string) and `wlan_id` (UUID string). No query
parameters are defined by the endpoint; no request body applies (HTTP GET).

**Rationale**:
The enriched per-endpoint doc explicitly names the SDK entry point as
`mistapi.api.v1.orgs.wlans.getOrgWLAN()`, and this matches the mistapi SDK convention
of deriving module paths from the OpenAPI URL (`/orgs/{org_id}/wlans/{wlan_id}` ->
`mistapi.api.v1.orgs.wlans`). The adjacent list endpoint (`listOrgWlans`) already
resides in the same module and is exercised by menu 48, so the module import is
already validated at runtime. Final verification happens at implementation time via
`python -c "from mistapi.api.v1.orgs import wlans; help(wlans.getOrgWLAN)"` inside the
active venv.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/orgs/{org_id}/wlans/{wlan_id}`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method exists, and
   the SDK already handles token injection, retry, and rate-limit signaling.
2. *Fetch the entire list via `listOrgWlans` and filter client-side.* Rejected -- for
   orgs with thousands of WLANs the extra bandwidth and CPU is wasteful, and the
   whole point of the new menu item is to be a targeted single-record viewer.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **natural primary key** on the WLAN's stable UUID. The
`ENDPOINT_PRIMARY_KEY_STRATEGIES` entry:

```python
'getOrgWLAN': {
    'type': 'natural_pk',
    'primary_key': ['id'],
    'indexes': ['org_id', 'site_id', 'ssid', 'enabled'],
    'table': 'org_wlan_detail',
}
```

`INSERT OR REPLACE` on `id` produces the desired upsert behavior on repeated polls.

**Rationale**:
The response contains a top-level `id` field of type UUID that is stable across polls,
matches the value the caller passed in as `wlan_id`, and is globally unique across
orgs. This is the textbook case for `natural_pk` per the codebase's Database Strategy
section of `.github/copilot-instructions.md` -- entities with stable API-provided
UUIDs use `natural_pk` with `primary_key: ['id']`. `org_id`, `site_id`, `ssid`, and
`enabled` are all high-value filter columns for downstream queries (e.g. "show all
enabled WLANs at site X") so they are added as secondary indexes without contributing
to the primary key.

**Alternatives Considered**:

1. *`composite_pk` on `(org_id, id)`.* Rejected -- `id` is already globally unique,
   so `org_id` in the PK adds no discrimination and only hurts index cardinality.
2. *`auto_increment_with_unique`.* Rejected -- the WLAN has a stable UUID; using an
   auto-increment surrogate would let repeated polls accumulate duplicate snapshots
   unless the unique constraint were also on `id`, at which point the surrogate is
   redundant.
3. *`composite_pk` on `(id, modified_time)` to keep history.* Rejected -- the spec
   is a read-only snapshot exporter, not a history tracker; users who want history
   run the export on a cron and archive the CSVs. Adding `modified_time` to the PK
   would break the upsert-cleanly acceptance scenario in spec.md.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/org_<org_id_short>_wlan_<wlan_id_short>_detail.csv` (one row per file --
  the endpoint returns one WLAN).
- SQLite table: `org_wlan_detail`.
- `org_id_short` and `wlan_id_short` are each the first 8 hex characters of the
  respective UUID -- the convention already used by adjacent WLAN and license
  exporters for human-readable filenames that do not leak full UUIDs into shell
  history.
- The `api_function_name` argument passed to
  `DataExporter.write_with_format_selection()` is `"getOrgWLAN"` (matching the
  operationId). The DataExporter uses that string as the lookup key into
  `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by `listOrgWlans` (which writes
`org_<org_id_short>_wlans.csv`). Including the WLAN's short UUID in the filename
disambiguates repeated captures of different WLANs for the same org without
overwriting prior CSVs. Nested arrays (`auth_servers`, `acct_servers`,
`coa_servers`, `portal_allowed_hostnames`, `portal_denied_hostnames`,
`ap_ids`, `mxtunnel_ids`) are re-serialized to JSON strings by the flatten helper
so the CSV row remains rectangular -- the same convention used by the list
exporter.

**Alternatives Considered**:

1. *Split nested arrays into separate child tables.* Rejected -- adds four to six
   sibling tables for what is a single-record viewer; downstream users querying
   "what auth servers does WLAN X use?" can `json_each()` the column in SQLite.
   Additional child tables would violate the 5-Item Rule at the module level.
2. *Use only `wlan_id_short` in the filename.* Rejected -- collides across orgs
   when the same operator manages multiple orgs, matching the same rejection
   reasoning used for the license status research task.
3. *Full UUID in the filename.* Rejected -- leaks the full org and WLAN UUIDs
   into shell history and `ls` output unnecessarily; the short form is enough
   to disambiguate locally.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 96**, sitting inside the Interactive Safe
cluster in the Viewers sub-range (92-96). The category label is
"Interactive Safe -- Viewers (WLAN detail)".

**Rationale**:
The menu range map from `.github/copilot-instructions.md` is:

- 1-59: Safe Org Exports
- 60-96: Interactive Safe (Site devices 60-72, Insights 73-79, Stats 80-91,
  Viewers 92-96)
- 97-101 + 153: Resource Intensive
- 102-123: WebSocket
- 124-152: Interactive
- 154-194: Destructive

This endpoint requires interactive input (two UUIDs from the user) but is otherwise
strictly safe (read-only single-record GET, no fan-out, no pagination). That matches
the Viewers sub-range exactly. Menu 96 is the next available integer in the Viewers
block, immediately below the Resource Intensive cluster at 97. Placing it here keeps
it visually adjacent to related WLAN operations without misleading a junior NOC
engineer about risk level. The number is provisional; at `/speckit.tasks` time the
main menu dispatch in `MistHelper.py` is grep'd for the latest allocated integer and
the assignment is shifted forward if a conflict exists inside the 60-96 cluster.

**Alternatives Considered**:

1. *Slot inside Safe Org Exports (1-59).* Rejected -- Safe Org Exports are
   traditionally zero-prompt or single-prompt org-wide dumps. This menu item needs
   two prompts (org and WLAN) and returns exactly one record, so it fits Viewers
   better than bulk exports.
2. *Slot into Interactive (124-152).* Rejected -- that band is reserved for
   diagnostics, packet captures, and management actions. A read-only config viewer
   does not belong there.
3. *Append after the Destructive block (195).* Rejected -- puts a safe viewer above
   the destructive cluster and visually mis-signals risk to a junior operator
   scrolling the menu, matching the reasoning used for spec 500 menu 95.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context: `"org_wlan_detail:org_id"`.
   Default: the value of `MIST_ORG_ID` in `.env` if present (pressing Enter accepts
   the default). Validated via the existing `is_valid_uuid()` helper before the API
   call; on failure, log `WARNING` and return early.
2. `wlan_id` -- prompt: `"WLAN ID (UUID): "`, context: `"org_wlan_detail:wlan_id"`.
   No default (this is per-invocation and cannot be preset via `.env`). Validated
   via the same `is_valid_uuid()` helper before the API call.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g. `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.

`MIST_WLAN_ID` is *not* introduced as a new env var because the whole purpose of this
menu item is to inspect an ad hoc WLAN by UUID; forcing a default in `.env` would
encourage stale muscle memory.

**Rationale**:
The endpoint requires both `org_id` and `wlan_id` in the URL. Neither can be
inferred from the other. Site scope is *not* required -- the endpoint is org-scoped
even though the returned record contains `site_id`. Guiding the user to first run
menu 48 (`listOrgWlans`) to discover valid `wlan_id` values is documented in
`quickstart.md`.

**Alternatives Considered**:

1. *Prompt for site_id and derive wlan_id from a site-scoped list.* Rejected -- the
   endpoint is `/orgs/{org_id}/wlans/{wlan_id}`, not the site-scoped variant; a site
   prompt would be misleading.
2. *Accept a comma-separated list of wlan_ids to fetch several in one invocation.*
   Rejected -- keeps the menu item under 25 lines and preserves the one-record,
   one-CSV filename mapping. Bulk retrieval is already covered by `listOrgWlans`
   (menu 48).
3. *Add a third prompt for output filename override.* Rejected -- adds keystrokes
   without operational value. The deterministic filename scheme in Research Task 3
   makes results easy to find under `data/`.
