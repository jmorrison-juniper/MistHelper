# Phase 0 Research: getOrgSettings

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_setting.md`
(enriched OpenAPI doc, ~50 KB of schema).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that
mirrors the OpenAPI URL:
`mistapi.api.v1.orgs.setting.getOrgSettings(apisession, org_id)`. The SDK
returns a `mistapi.APIResponse` object whose `.data` attribute is the parsed
JSON body. The body is a single JSON object (not a list, not paginated) whose
top-level keys are, per the enriched doc:

- Simple scalars: `allow_mist`, `ap_updown_threshold`, `blacklist_url`,
  `created_time`, `device_updown_threshold`, `disable_pcap`,
  `disable_remote_shell`, `for_site`, `gateway_tunnel_updown_threshold`,
  `gateway_updown_threshold`, `id`, `modified_time`, `msp_id`, `org_id`,
  `pcap_bucket_verified`, `switch_updown_threshold`, `ui_no_tracking`.
- Nested single objects: `api_policy`, `auto_device_naming`,
  `auto_deviceprofile_assignment`, `auto_site_assignment`, `cacerts`,
  `celona`, `cloudshark`, `cradlepoint`, `device_cert`, `gateway_mgmt`,
  `installer`, `jcloud`, `jcloud_ra`, `juniper`, `juniper_srx`,
  `junos_shell_access`, `marvis`, `mgmt`, `mist_nac`, `mxedge_mgmt`,
  `optic_port_config`, `password_policy`, `pcap`, `security`, `simple_alert`,
  `ssr`, `switch`, `switch_mgmt`, `synthetic_test`, `tags`, `ui_idle_timeout`,
  `vpn_options`, `wan_pma`, `wired_pma`, `wireless_pma`.
- Nested arrays: `auto_device_naming.rules[]` (title
  `org_setting_auto_device_naming_rule`), `auto_deviceprofile_assignment.rules[]`
  (title `org_setting_auto_deviceprofile_assignment_rule`).

Required path parameter: `org_id` (UUID string). No query parameters. No
request body. No pagination.

**Rationale**:
The enriched per-endpoint doc lists the SDK module as
`mistapi.api.v1.orgs.setting.getOrgSettings()` and the URL path is
`/api/v1/orgs/{org_id}/setting` -- the mistapi SDK generates module paths
one-for-one from the URL. Final verification happens at implementation time
via `python -c "from mistapi.api.v1.orgs import setting; help(setting)"`
inside the venv. Wrapping the body's ~50 top-level keys as one flat row (with
nested objects JSON-serialized into their column) plus two side tables for the
two nested arrays keeps the SQLite schema query-friendly without exploding
into 30+ tables.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/setting`.* Rejected -- the
   Constitution forbids direct HTTP when a mistapi method exists.
2. *One SQLite table per nested object (~30 side tables).* Rejected --
   over-normalizes a settings blob that is naturally read as a whole; adds
   >30 CREATE TABLE statements for no query-time benefit.
3. *Fully denormalized single column of raw JSON.* Rejected -- defeats the
   SQL queryability requirement and conflicts with the flattening convention
   used everywhere else in MistHelper.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **natural primary key** strategy on the parent settings table and a
**composite primary key** strategy on each rule side table:

- `org_settings`: `type = 'natural_pk'`, `primary_key = ['org_id']` -- one row
  per organization. The Mist API returns `org_id` in the body itself
  (confirmed at line 1041 of the enriched doc), and even if it were absent
  MistHelper always knows which org the call targeted. Re-running the menu
  item against the same org must upsert the single row.
- `org_settings_auto_device_naming_rules`: `type = 'composite_pk'`,
  `primary_key = ['org_id', 'rule_index']` -- one row per array element.
  The API does not expose a stable id for these rules, so the ordinal
  `rule_index` (0-based position within the source array) is used as part of
  the key.
- `org_settings_auto_deviceprofile_assignment_rules`: `type = 'composite_pk'`,
  `primary_key = ['org_id', 'rule_index']` -- same rationale as above.

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration lists all three keys under
one operationId (`getOrgSettings`) with sub-table entries for the two rule
arrays.

**Rationale**:
Org settings are a singleton per organization -- there is exactly one settings
document per org, and it is updated in place by administrators. `natural_pk`
on `org_id` gives `INSERT OR REPLACE` semantics that keep the SQLite row
current with the last poll. For the rule arrays, the API returns them as
ordered lists with no stable per-rule identifier, so the ordinal position is
the least-bad composite key partner. Wiping and re-inserting the rule rows on
every poll (delete-by-`org_id` then insert-by-`(org_id, rule_index)`) is the
correct pattern here; the DataExporter's `INSERT OR REPLACE` handles that
automatically when the composite PK includes the org.

**Alternatives Considered**:

1. *`auto_increment_with_unique` on the parent table.* Rejected -- would let
   repeated polls accumulate duplicate snapshots of a settings blob that
   should be current-state only. There is no operational value in keeping a
   snapshot history in the primary table; if history is desired, a separate
   audit table is the right pattern (out of scope for this spec).
2. *`composite_pk` on `(org_id, modified_time)` for the parent.* Rejected --
   `modified_time` changes only when an admin edits settings, but the caller
   is polling and expects each poll to overwrite the prior row for the same
   org. Using `modified_time` in the PK would accumulate a snapshot per edit,
   which is out of scope.
3. *Hash-of-rule-content as PK for the rule side tables.* Rejected -- opaque,
   non-human-readable, and breaks trivially when a single character in the
   rule expression changes (defeats upsert semantics for ordered lists).

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (parent):  `data/org_<org_id_short>_settings.csv`
- CSV (rule 1):  `data/org_<org_id_short>_settings_auto_device_naming_rules.csv`
- CSV (rule 2):  `data/org_<org_id_short>_settings_auto_deviceprofile_assignment_rules.csv`
- SQLite tables: `org_settings`, `org_settings_auto_device_naming_rules`,
  `org_settings_auto_deviceprofile_assignment_rules` (all in `data/mist_data.db`)
- `org_id_short` is the first 8 hex characters of the org UUID -- the
  convention already used by adjacent org-export methods in MistHelper for
  human-readable filenames without leaking full UUIDs into shell history.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"getOrgSettings"` (matching
the operationId) for the parent write, and the two MistHelper-internal
sub-table identifiers `"getOrgSettingsAutoDeviceNamingRules"` and
`"getOrgSettingsAutoDeviceprofileAssignmentRules"` for the side tables. The
DataExporter uses those strings as the lookup key into
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the file-naming pattern used by other org-scoped exports (short UUID
prefix keeps output greppable while avoiding UUID leakage into shell history).
Three output files / three SQLite tables keeps the schema clean and lets a
user query the parent settings without joining when they don't need the rule
side-tables.

**Alternatives Considered**:

1. *Single output file with JSON-encoded rule columns.* Rejected -- the two
   rule arrays are naturally tabular (each rule has `expression`,
   `match_device`, `prefix`, `src`, `suffix` for auto_device_naming; and a
   similar shape for auto_deviceprofile_assignment). Splitting them into side
   tables preserves query-ability.
2. *Full org UUID in the filename.* Rejected -- leaks the org UUID into shell
   history and `ls` output unnecessarily. The short 8-char form is enough to
   disambiguate locally.
3. *Filename keyed by `modified_time` for point-in-time snapshots.* Rejected
   -- current-state export is the goal; SQLite upsert semantics make
   time-series snapshots unnecessary here.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 58**, sitting inside the Safe Org
Exports cluster (1-59), immediately below the SLE / miscellaneous slots
(51-57) and above the last-slot boundary at 59. The category label is
"Safe Org Exports -- Org Settings".

**Rationale**:
The Constitution and `.github/copilot-instructions.md` describe the menu
ranges as:

- 1-59 Safe Org Exports (sites 1-7, inventory 8-14, device stats 15-19,
  events 20-26, clients 27-30, gateways 31-36, templates 37-41, config/admin
  42-50, SLE 51-55, misc 56-59).
- 60-96 Interactive Safe.
- 97-101 + 153 Resource Intensive.
- 102-123 WebSocket.
- 124-152 Interactive.
- 154-194 Destructive.

Org settings is an org-wide read-only config export, so it belongs in the
Safe Org Exports block, and specifically in the config/admin sub-cluster
(42-50 is already dense). The next contiguous free integer at the tail of the
Safe Org Exports range is 58 (56-57 are in the misc sub-cluster, 59 is the
range boundary). The number is provisional -- at `/speckit.tasks` time
MistHelper.py is grep'd for the latest allocated menu integer and 58 is
shifted forward if a conflict exists.

**Alternatives Considered**:

1. *Slot inside Interactive Safe (60-96).* Rejected -- this endpoint requires
   only a single `org_id` and returns a static JSON blob, with no menu-level
   interactivity beyond the standard `safe_input()` prompt. It is a
   non-interactive org export, so it belongs in 1-59.
2. *Append at the end (e.g., 195).* Rejected -- the destructive cluster ends
   at 194 and placing a read-only org config export above the destructive
   block visually mis-signals the risk level to a junior NOC engineer
   scrolling the menu.
3. *Wedge into 42-50 (existing org-config/admin cluster).* Rejected -- that
   sub-cluster is already fully allocated; injecting into the middle would
   force renumbering of adjacent operations, breaking automation that
   references menu numbers by integer.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly one** value via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context: `"org_settings:org_id"`.
   Default: the value of `MIST_ORG_ID` in `.env` if present (pressing Enter
   accepts the default). Validated via the existing `is_valid_uuid()` helper
   before the API call; on failure, log `WARNING` and return early.

No query parameters exist for this endpoint (per the OpenAPI schema), and
there are no optional flags for the caller to toggle. Site/device/template
IDs are not involved.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for the org_id prompt.

**Rationale**:
Mist's settings endpoint is org-scoped and takes no query parameters. Adding
extra prompts (e.g., which nested domain to extract) would be premature
optimization -- the full-settings blob is small enough (typically 5-50 KB)
that the always-export-everything default is correct. If a caller needs only
a subset of the settings domains, a follow-up spec can add a filtered menu
item.

**Alternatives Considered**:

1. *Prompt for a filter (e.g., "which nested domain?").* Rejected -- adds
   keystrokes without operational value for the common "give me everything"
   case. A future spec can add a filtered variant if a real need surfaces.
2. *Skip the prompt entirely and always use `MIST_ORG_ID` from `.env`.*
   Rejected -- a Mist admin often manages multiple orgs from the same
   deployment; forcing them to edit `.env` between orgs is friction. The
   default-with-Enter pattern already offers a one-keystroke path for the
   single-org case.
3. *Add a prompt for an output filename override.* Rejected -- the
   deterministic filename scheme in Research Task 3 makes results easy to
   find under `data/` and matches the convention used by adjacent org
   exports.
