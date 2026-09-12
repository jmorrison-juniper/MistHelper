# Phase 0 Research: getOrgOtherDeviceStats

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_stats_otherdevices_device_mac.md`
(enriched OpenAPI doc for this exact operationId).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.orgs.stats.otherdevices.getOrgOtherDeviceStats(apisession,
org_id, device_mac)`. The SDK returns a `mistapi.APIResponse` object whose `.data`
attribute is the parsed JSON body. The body is a single JSON object (not a list and
not paginated), with the following top-level fields per the enriched doc:

- `cached_stats` (boolean -- true when the response came from the cache layer)
- `config_status` (string, e.g. `synced`)
- `connected_devices` (object -- **map keyed by MAC address**; each value is a
  `stats_device_other_connected_device` object with `mac`, `name`, `port_id`, `type`)
- `interfaces` (object -- **map keyed by interface name**; each value is a
  `stats_device_other_interface` object with cellular / link stats: `bytes_in`,
  `bytes_out`, `carrier`, `imei`, `imsi`, `ip`, `link`, `mode`, `mtu`, `rsrp`, `rsrq`,
  `rssi`, `service_mode`, `sinr`, `state`, `type`, `uptime`)
- `last_config` (int32 epoch seconds)
- `last_seen` (number epoch seconds, nullable)
- `lldp_enabled` (boolean)
- `mac` (string -- the device's own MAC)
- `status` (string, e.g. `online`)
- `uptime` (int32 seconds)
- `vendor` (string, e.g. `cradlepoint`)
- `vendor_specific` (object -- present when `vendor` is a known vendor; contains
  `interfaces` map and `target_version` string)
- `version` (string, e.g. `7.22.70`)

Required path parameters: `org_id` (UUID string) and `device_mac` (12-hex-char MAC,
no separators). No query parameters. No request body.

**Rationale**:
The enriched per-endpoint doc lists the SDK as
`mistapi.api.v1.orgs.stats_-_other_devices.getOrgOtherDeviceStats()`, but that string
contains a `-` character which is not a legal Python identifier -- the enriched doc
is derived from the OpenAPI tag ("Orgs Stats - Other Devices") rather than a real
importable module. The mistapi SDK generates module paths from the URL, not the tag
(verified by inspecting adjacent endpoints: `GET /orgs/{org_id}/stats/devices` lives
in `mistapi.api.v1.orgs.stats.devices`, `GET /orgs/{org_id}/otherdevices` lives in
`mistapi.api.v1.orgs.otherdevices`). Combining those two patterns yields
`mistapi.api.v1.orgs.stats.otherdevices` for the URL
`/orgs/{org_id}/stats/otherdevices/{device_mac}`. The spec.md explicitly names this
same module path, so we follow the spec. Final verification happens at implementation
time via `python -c "from mistapi.api.v1.orgs.stats import otherdevices; help(otherdevices)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/orgs/{org_id}/stats/otherdevices/{device_mac}`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method exists.
2. *Trust the enriched doc's tag-based path.* Rejected -- the tag string contains
   `-` and spaces, which cannot form a valid Python module path. The URL-based path
   is the canonical mistapi convention.
3. *Look up the endpoint via `mistapi.APISession.mist_get(url_path)` low-level
   helper.* Rejected -- this is a private/legacy escape hatch; the high-level SDK
   function exists and gives us typed access to the response.

## Research Task 2: Primary Key Strategy

**Decision**:
Use **composite_pk** across four separate tables, one for each logical entity in the
response:

- `org_other_device_stats_summary`: PK = `(org_id, device_mac)` -- one row per
  polled device.
- `org_other_device_connected_devices`: PK = `(org_id, device_mac, connected_mac)`
  -- one row per neighbor discovered on the other device.
- `org_other_device_interfaces`: PK = `(org_id, device_mac, interface_name)` -- one
  row per interface reported by the device.
- `org_other_device_vendor_interfaces`: PK = `(org_id, device_mac, port_name)` -- one
  row per vendor-specific interface (e.g. Cradlepoint modem ports like
  `mdm-4d0e073b`).

All four tables register in `ENDPOINT_PRIMARY_KEY_STRATEGIES` with `type =
composite_pk`. `org_id` is injected by MistHelper before the upsert (the API body
does not repeat `org_id`), and `device_mac` is normalized (lowercase, no separators)
to match the API's canonical MAC format.

**Rationale**:
The endpoint reports the *current* state of one third-party device. Re-polling the
same device must **update** the existing rows, not append duplicate snapshots.
Splitting into four tables mirrors how existing MistHelper exports handle nested
maps (`connected_devices`, `interfaces`, `vendor_specific.interfaces`) and keeps
each table's schema flat and SQL-queryable without JSON blobs. `(org_id, device_mac)`
is the natural key at the summary level; adding the sub-entity's own key (neighbor
MAC, interface name, or vendor port name) forms the child composite key.
`INSERT OR REPLACE` upserts every poll's view cleanly.

**Alternatives Considered**:

1. *`natural_pk` on `device_mac` alone.* Rejected -- MistHelper may target multiple
   orgs from one install; `device_mac` is not globally unique across orgs (MAC
   collisions are unlikely for hardware but possible for virtual devices).
2. *`auto_increment_with_unique`.* Rejected -- repeated polls would accumulate
   duplicate snapshots, defeating the upsert behavior spec.md requires (edge case:
   "Given repeated runs, When SQLite is the active backend, Then rows upsert").
3. *Single denormalized table with JSON-encoded columns for `connected_devices`,
   `interfaces`, `vendor_specific`.* Rejected -- breaks SQL queryability, conflicts
   with the flattening convention used everywhere else in MistHelper, and prevents
   per-interface indexing.
4. *Two tables (summary + one merged "sub-entities" table with a `kind` column).*
   Rejected -- would collapse three schemas with different columns into one
   sparse-column table, making both writes and reads harder.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV summary: `data/org_<org_id_short>_<device_mac>_other_device_stats.csv`
- CSV connected devices: `data/org_<org_id_short>_<device_mac>_other_device_connected.csv`
- CSV interfaces: `data/org_<org_id_short>_<device_mac>_other_device_interfaces.csv`
- CSV vendor-specific: `data/org_<org_id_short>_<device_mac>_other_device_vendor_interfaces.csv`
- SQLite tables: `org_other_device_stats_summary`,
  `org_other_device_connected_devices`, `org_other_device_interfaces`, and
  `org_other_device_vendor_interfaces`.
- `org_id_short` is the first 8 hex characters of the org UUID -- the convention
  already used by other org-scoped exports for human-readable filenames without
  leaking full UUIDs into shell history.
- `device_mac` in filenames is the lowercase, separator-stripped 12-hex-char form,
  keeping filenames short and shell-safe.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is the operationId `"getOrgOtherDeviceStats"` for the summary write, and
MistHelper-internal sub-table identifiers
`"getOrgOtherDeviceStatsConnectedDevices"`,
`"getOrgOtherDeviceStatsInterfaces"`, and
`"getOrgOtherDeviceStatsVendorInterfaces"` for the three child writes. The
DataExporter uses each string as the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by adjacent device-stats exports (e.g. the
`getOrgDeviceStats` family). Four output files / four SQLite tables keep each schema
flat and let a user query the summary without a join when they don't need per-interface
detail. Including the device MAC in the filename lets an operator poll several devices
in sequence without overwriting each other's CSVs.

**Alternatives Considered**:

1. *One file per poll containing the raw JSON.* Rejected -- breaks SQL queryability
   and conflicts with the flattening convention.
2. *Omit device MAC from filenames.* Rejected -- polling two devices back-to-back
   would overwrite the first device's CSVs before the operator could archive them.
3. *Include the full org UUID.* Rejected -- leaks the org UUID into shell history
   and `ls` output. The 8-char prefix is enough to disambiguate locally.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 630**, matching the feature branch
numeric prefix (`630-mist-get-org-other-device-stats`). Category label: "Interactive
Safe -- Org Stats (Other Devices)", conceptually adjacent to the existing device
stats menu items (80-91) but placed in the extended range dedicated to this API
cataloging batch.

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource Intensive,
102-123 WebSocket, 124-152 Interactive, 154-194 Destructive. This endpoint is a
single non-paginated GET returning small JSON per device -- it belongs in an
Interactive Safe cluster. Because the current API-cataloging effort is producing
many new menu items in a 500-999 numeric range that matches spec branch prefixes,
menu 630 keeps spec / branch / CHANGELOG numbering consistent. The 600-series range
was reserved during the cataloging batch precisely to hold the new safe read
operations without renumbering the historical 1-194 menu.

The number is provisional -- at `/speckit.tasks` time, `MistHelper.py` and other
open PRs are grep'd for the latest allocated menu integer and 630 is shifted forward
if a conflict exists in the same series.

**Alternatives Considered**:

1. *Slot inside the historical safe cluster (e.g. 59 or 91).* Rejected -- would
   force renumbering of the historical menu, breaking user muscle memory and
   README/CHANGELOG history.
2. *Place inside Resource Intensive (96-101).* Rejected -- one non-paginated GET
   per device is not resource-intensive.
3. *Place inside Destructive (154-194).* Rejected -- read-only GET; misplacing it
   in the destructive block would visually mis-signal risk to a junior NOC engineer.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"org_other_device_stats:org_id"`. Default: the value of `MIST_ORG_ID` in `.env`
   if present (pressing Enter accepts the default). Validated via the existing
   `is_valid_uuid()` helper before the API call; on failure, log `WARNING` and
   return early.
2. `device_mac` -- prompt: `"Other-device MAC (12 hex chars, colons/dashes OK): "`,
   context: `"org_other_device_stats:device_mac"`. No default (the whole point of
   the menu item is to poll one specific device). Input is normalized to lowercase
   with `:` and `-` stripped, then validated against `^[0-9a-f]{12}$`. On failure,
   log `WARNING` and return early.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g. `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.

**Rationale**:
Both `org_id` and `device_mac` are path parameters on the endpoint -- neither can
be defaulted from the response schema, and both must be supplied per call. The
endpoint has no query parameters, so no third prompt is required. Normalizing the
MAC before validation lets operators paste MACs in any common format (aa:bb:cc:...,
AA-BB-CC-..., or aabbcc...) without the menu rejecting valid input on formatting.

**Alternatives Considered**:

1. *Add a third prompt to override the output filename stem.* Rejected -- adds
   keystrokes without operational value. The deterministic scheme in Research
   Task 3 makes results easy to find under `data/`.
2. *Accept a comma-separated list of MACs and loop internally.* Rejected -- creeps
   toward a bulk operation that belongs in its own spec; violates the 5-Item Rule
   by inflating the method's logical block count and its parameter list.
3. *Default the MAC to the last one polled (stateful).* Rejected -- introduces
   hidden state that surprises operators and complicates the safe-input contract.
