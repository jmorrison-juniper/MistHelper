# Capture Data Sources — Technical Reference

**Feature**: 1823 upgrade capture portal
**Date**: 2026-08-19
**Status**: Research. No source code changed.

## 1. Scope and method

This document lists every Mist API call that supplies a capture field. It also
lists every repository helper that already collects one of those fields.

A capture is a point-in-time snapshot of one site. The portal takes one capture
before a firmware upgrade and one capture after the upgrade. The portal then
compares the two captures.

Two tiers exist:

- **Tier 2** is the default capture. Tier 2 holds device state and the full
  client list.
- **Tier 3** is an optional per-run toggle. Tier 3 holds port state, radio
  state, tunnel state, peer state, and alarms.

Sources used for this document:

1. The installed `mistapi` package at version `0.63.3`. The package root is
   `.venv/Lib/site-packages/mistapi` in the sibling `MistHelper` checkout. The
   pin lives at `requirements.txt:5`.
2. The vendored API specification under `documentation/api/`. Those files carry
   the response body schema, which the SDK does not.
3. The repository source under `src/`.

This document never read `.env`. It names configuration variables only.

Every claim below carries a `file_path:line_number` citation. Where this
document infers rather than reads, the text says so.

---

## 2. Device state calls

Tier 2 needs firmware version, status, uptime, model, and serial number for
access points, switches, and gateways.

### 2.1 The recommended call

| Item | Value |
|------|-------|
| Function | `mistapi.api.v1.sites.stats.listSiteDevicesStats` |
| SDK definition | `.venv/Lib/site-packages/mistapi/api/v1/sites/stats.py:1031` |
| HTTP path | `GET /api/v1/sites/{site_id}/stats/devices` |
| Specification | `documentation/api/sites/GET_sites_site_id_stats_devices.md:7` |
| Parameters | `type`, `status`, `limit`, `page` |
| Required argument | `type="all"` |

The response is a `oneOf` union of three record shapes. The specification names
them `stats_ap` at `documentation/api/sites/GET_sites_site_id_stats_devices.md:50`,
`stats_switch` at `:3183`, and `stats_gateway` at `:4822`.

All three shapes carry the tier 2 fields:

| Tier 2 field | Response key | AP line | Switch line | Gateway line |
|--------------|--------------|---------|-------------|--------------|
| Firmware version | `version` | 3149 | 4808 | 7445 |
| Status | `status` | 3014 | 4732 | 7293 |
| Uptime | `uptime` | 3080 | 4752 | 7435 |
| Model | `model` | 1834 | 3809 | 5942 |
| Serial number | `serial` | 2995 | 4684 | 7062 |
| MAC address | `mac` | 1443 | 3771 | 5888 |
| Device type | `type` | 3074 | 4747 | 7429 |
| Last seen | `last_seen` | 1074 | 3742 | 5877 |

All citations in the table point at
`documentation/api/sites/GET_sites_site_id_stats_devices.md`.

The AP shape also carries `radio_stat` at `:2386` and `port_stat` at `:1899`.
The switch shape and the gateway shape carry `if_stat` at `:3510` and `:5538`.
Section 5 uses those blobs.

### 2.2 The critical trap

The device listing calls default to access points only. The server applies the
default. The client sends no parameter at all.

The vendored specification states the trap in one line:

```
- By default returns only AP stats. Use `type=all` to include switches and gateways.
```

That quote is at `documentation/api/sites/GET_sites_site_id_stats_devices.md:7599`.

The SDK repeats the default in its docstring. `listSiteDevicesStats` documents
`type : str, default: ap` at
`.venv/Lib/site-packages/mistapi/api/v1/sites/stats.py:1053`. The clearest
wording in the whole package sits on the org variant. `listOrgDevicesStats`
documents `type : str{'all','ap','switch','gateway'}, default: ap` at
`.venv/Lib/site-packages/mistapi/api/v1/orgs/stats.py:427`. The next line adds
that comma-separated values are not supported.

**The exact argument to pass is `type="all"`.**

The repository already contains a line that demonstrates the trap. The AP MAC
helper passes `type="ap"` on purpose:

```python
rawdata = mistapi.api.v1.sites.devices.listSiteDevices(apisession, site_id, type="ap").data
```

That line is `src/device/device_utils.py:35`. The helper is
`get_all_ap_macs_from_site` at `src/device/device_utils.py:22`. That helper
wants access points only, so the argument is correct there. Do not copy the
pattern into the capture.

The repository also contains the correct capture pattern:

```python
response = mistapi.api.v1.sites.stats.listSiteDevicesStats(mh.apisession, site_id, type="all", limit=1000)
```

That line is `src/export/site_device_exporter.py:144`. The firmware manager uses
the same argument at `src/firmware/firmware_manager.py:508` and
`src/firmware/firmware_manager.py:3231`.

### 2.3 Calls that carry the same trap

| Function | Definition | Docstring default |
|----------|-----------|-------------------|
| `listSiteDevices` | `mistapi/api/v1/sites/devices.py:17` | `type : str, default: ap` at `:39` |
| `listSiteDevicesStats` | `mistapi/api/v1/sites/stats.py:1031` | `type : str, default: ap` at `:1053` |
| `listOrgDevicesStats` | `mistapi/api/v1/orgs/stats.py:397` | `default: ap` at `:427` |
| `searchOrgDevices` | `mistapi/api/v1/orgs/devices.py:538` | `type : str{'ap','gateway','switch'}, default: ap` at `:672` |

All paths above are relative to `.venv/Lib/site-packages/`.

`searchOrgDevices` needs a warning of its own. Its docstring lists only `ap`,
`gateway`, and `switch`. It does not list `all`. Do not assume `type="all"`
works on `searchOrgDevices`. Call it three times, once per device type, or use
`listOrgDevicesStats` instead.

`listSiteDevices` body lines 56 and 57 show why the omission is silent:

```python
if type:
    query_params["type"] = str(type)
```

An omitted `type` sends no query parameter. The server then applies its own
default of `ap`. No error and no warning appears.

### 2.4 Org scope alternatives

| Function | Definition | Note |
|----------|-----------|------|
| `listOrgDevices` | `mistapi/api/v1/orgs/devices.py:17` | Takes `(mist_session, org_id)` only. No type filter and no pagination. Not useful for a capture. |
| `listOrgDevicesStats` | `mistapi/api/v1/orgs/stats.py:397` | Accepts `site_id`, `type`, `status`, `fields`, `limit`, `page`. `site_id` and `mac` accept comma-separated values. |
| `searchOrgDevices` | `mistapi/api/v1/orgs/devices.py:538` | 44 parameters. Includes `stats: bool` at `:573` and the `band_*_channel` and `band_*_power` filters. |
| `getOrgInventory` | Used at `src/api/api_core_fetch_utils.py:61` | Inventory, not live state. Section 4.2 covers it. |

**Recommendation.** The capture targets one site. Use the site call. Pass
`type="all"` and `limit=DEFAULT_API_PAGE_LIMIT`. Do not use the org call, because
the org call returns every site and wastes payload.

---

## 3. Client calls

### 3.1 The two wireless endpoints differ in an important way

Two wireless client endpoints exist. They are not interchangeable.

| Item | `listSiteWirelessClientsStats` | `searchSiteWirelessClients` |
|------|-------------------------------|----------------------------|
| SDK path | `mistapi.api.v1.sites.stats.listSiteWirelessClientsStats` | `mistapi.api.v1.sites.clients.searchSiteWirelessClients` |
| SDK definition | Named at `documentation/api/sites/GET_sites_site_id_stats_clients.md:735` | `mistapi/api/v1/sites/clients.py:336` |
| HTTP path | `GET /api/v1/sites/{site_id}/stats/clients` (`:7`) | `GET /api/v1/sites/{site_id}/clients/search` (`:7`) |
| Scope | Currently connected clients only | Every client seen inside a time window |
| Field values | Scalars | Arrays |
| Signal strength | Yes | No |
| Randomized MAC flag | No | Yes |

The stats endpoint gotcha is explicit:

```
- Returns currently connected clients only. For historical data, use the search/insights endpoints.
```

That quote is at `documentation/api/sites/GET_sites_site_id_stats_clients.md:743`.

The search endpoint defaults to `duration = 1d`. That default is at
`documentation/api/sites/GET_sites_site_id_clients_search.md:44`. The search
endpoint therefore aggregates a whole day. Its `ap`, `ssid`, `vlan`, `ip`, and
`hostname` values are arrays, not scalars.

**Recommendation.** A capture is a point-in-time snapshot. Use
`listSiteWirelessClientsStats` as the primary wireless source. It matches the
capture concept, and it is the only source of signal strength.

Add a second call to `searchSiteWirelessClients` only if the compare view needs
the `random_mac` flag. Section 7.4 explains why that flag matters.

### 3.2 Wireless field mapping, stats endpoint

Source file for every line below is
`documentation/api/sites/GET_sites_site_id_stats_clients.md`.

| Tier 2 field | Response key | Line | Note |
|--------------|--------------|------|------|
| MAC address | `mac` | 269 | Scalar |
| Hostname | `hostname` | 239 | Scalar |
| IP address | `ip` | 247 | Scalar |
| VLAN | `vlan_id` | 490 | Scalar |
| SSID | `ssid` | 399 | Scalar |
| Signal strength | `rssi` | 308 | Described as "Signal strength" |
| Parent access point | `ap_mac` | 96 | Required field, see `:52`-`:54` |
| Parent access point ID | `ap_id` | 91 | Required field, see `:52`-`:54` |
| Band | `band` | 104 | Enum `24`, `5`, `6` |
| Channel | `channel` | 111 | Current channel |
| Signal over noise | `snr` | 395 | Useful supplement to `rssi` |
| Connected time | `uptime` | 460 | Seconds since connect |
| Idle time | `idle_time` | 243 | Seconds since last receive |
| Last seen | `last_seen` | 258 | Epoch seconds |
| WLAN ID | `wlan_id` | 494 | UUID |
| Protocol | `proto` | 299 | 802.11 amendment |

**A wireless client reports its parent access point through `ap_mac`.** The
specification marks `ap_id` and `ap_mac` as required at
`documentation/api/sites/GET_sites_site_id_stats_clients.md:52`-`:54`. Both fields
are always present. The example payload shows the pair at `:666`-`:667`.

Caution. The field `random_mac` also appears in this file at `:214`. That
occurrence sits inside the `guest` sub-object, which starts at `:127`. It is a
guest registration attribute. It is not the top-level randomized-MAC flag.

### 3.3 Wireless field mapping, search endpoint

Source file for every line below is
`documentation/api/sites/GET_sites_site_id_clients_search.md`.

The search endpoint returns one array field and one scalar field for most
concepts. The array covers the whole window. The `last_` scalar covers the
latest observation.

| Tier 2 field | Array key | Line | Scalar key | Line |
|--------------|-----------|------|-----------|------|
| MAC address | — | — | `mac` | 256 |
| Hostname | `hostname` | 133 | `last_hostname` | 180 |
| IP address | `ip` | 146 | `last_ip` | 187 |
| VLAN | `vlan` | 407 | `last_vlan` | 240 |
| SSID | `ssid` | 378 | `last_ssid` | 230 |
| Parent access point | `ap` | 79 | `last_ap` | 159 |
| Band | — | — | `band` | 104 |
| Randomized MAC | — | — | `random_mac` | 341 |
| Protocol | — | — | `protocol` | 309 |
| Timestamp | — | — | `timestamp` | 390 |

**This endpoint returns no signal strength.** The property list runs from `:79`
to `:432`. No `rssi` key and no `snr` key appear in it. Any design that expects
signal strength from `searchSiteWirelessClients` will silently return nothing.

The `random_mac` field carries the description "Whether the client is using
randomized MAC Address or not" at `:343`.

Warning. The description text on `last_ssid` at `:232` reads "If dot1x
authentication, the username used during the latest authentication." That text
belongs to `last_username`. The vendored specification carries a copy-and-paste
error at that line. The key name `last_ssid` is still correct. Treat the
description as wrong and the key as right.

### 3.4 Wired client mapping

| Item | Value |
|------|-------|
| Function | `mistapi.api.v1.sites.wired_clients.searchSiteWiredClients` |
| SDK definition | `.venv/Lib/site-packages/mistapi/api/v1/sites/wired_clients.py:93` |
| HTTP path | `GET /api/v1/sites/{site_id}/wired_clients/search` |
| Specification | `documentation/api/sites/GET_sites_site_id_wired_clients_search.md:7` |

No point-in-time wired equivalent of `listSiteWirelessClientsStats` exists. The
search endpoint is the only full wired client list. It carries the same
`duration = 1d` default, documented at
`documentation/api/sites/GET_sites_site_id_wired_clients_search.md:46`.

Source file for every line below is
`documentation/api/sites/GET_sites_site_id_wired_clients_search.md`.

| Tier 2 field | Response key | Line | Type | Note |
|--------------|--------------|------|------|------|
| MAC address | `mac` | 201 | String | The only scalar identity field |
| Hostname | `dhcp_hostname` | 175 | String | See the warning below |
| IP address | `ip` | 193 | Array of string | |
| VLAN | `vlan` | 234 | Array of integer | |
| Switch MAC | `device_mac` | 93 | Array of string | "MAC Address of the switch the client is connected to" |
| Switch port | `port_id` | 213 | Array of string | |
| Switch port detail | `device_mac_port` | 101 | Array of object | Preferred, see below |
| Authentication state | `auth_state` | 87 | String | |
| Authentication method | `auth_method` | 81 | String | |
| Timestamp | `timestamp` | 229 | Number | Epoch seconds |

**Warning. A wired client has no `hostname` field.** The property list runs from
`:81` to `:242`. It contains `dhcp_hostname` at `:175` and `dhcp_fqdn` at `:169`.
It contains no plain `hostname` key. Any code that reads `client["hostname"]` on
a wired record returns nothing.

**A wired client reports its switch port through `device_mac_port`.** That field
is an array of objects at `:101`-`:140`. Each object carries:

| Sub-key | Line | Meaning |
|---------|------|---------|
| `device_mac` | 108 | Switch MAC address |
| `port_id` | 116 | Port name, for example `ge-0/0/0` |
| `port_parent` | 120 | Parent port for an aggregate |
| `vlan` | 127 | VLAN on that port |
| `ip` | 112 | IP on that port |
| `start` | 123 | Session start |
| `when` | 132 | Last observation |

Use `device_mac_port` rather than the parallel `device_mac` and `port_id`
arrays. The parallel arrays force the reader to assume index alignment. The
object array states the pairing directly.

### 3.5 Org scope client calls

| Function | Definition |
|----------|-----------|
| `searchOrgWirelessClients` | `.venv/Lib/site-packages/mistapi/api/v1/orgs/clients.py:320` |
| `searchOrgWiredClients` | `.venv/Lib/site-packages/mistapi/api/v1/orgs/wired_clients.py:73` |

Both org calls take the site parameters plus a leading `org_id` and an optional
`site_id` filter. `searchOrgWiredClients` adds `auth_state` and `auth_method` as
filters.

**Warning. The parameter order differs between the site variant and the org
variant.** Always pass keyword arguments. Positional arguments will bind to the
wrong parameter without raising an error.

The capture targets one site, so the site calls are the correct choice.

---

## 4. Existing repository helpers

### 4.1 The client helper that tags each record with a client type

| Item | Value |
|------|-------|
| Function | `_fetch_all_clients` |
| Signature | `_fetch_all_clients(org_id: str, site_id: str \| None) -> list[dict]` |
| File | `src/ui/prompt_utils.py` |
| Line | 242 |

The helper branches on `site_id` at `src/ui/prompt_utils.py:250`. A present
`site_id` selects the site calls. An absent `site_id` selects the org calls. The
helper returns a sorted list at `src/ui/prompt_utils.py:266`. The sort key is
`(hostname, mac)`.

Four private fetchers sit under it:

| Fetcher | Line | API call | Line | Tags added |
|---------|------|----------|------|-----------|
| `_fetch_site_wireless_clients` | 269 | `searchSiteWirelessClients` | 273 | `client_type="wireless"` at 291, `source_site_id` at 292 |
| `_fetch_site_wired_clients` | 285 | `searchSiteWiredClients` | 289 | `client_type="wired"` at 292, `source_site_id` at 293 |
| `_fetch_org_wireless_clients` | 301 | `searchOrgWirelessClients` | 305 | `client_type` only |
| `_fetch_org_wired_clients` | 316 | `searchOrgWiredClients` | 320 | `client_type` only |

**The tag is `client_type`.** Its two values are `"wireless"` and `"wired"`.

Supporting formatters exist because the search endpoints return arrays:

| Formatter | Line | Behavior |
|-----------|------|----------|
| `_get_client_status` | 422 | Maps `connected` to `[+]` or `[-]`. Maps a `last_seen` older than 300 seconds to `[~]` at 429-433 |
| `_format_client_ip` | 438 | Reads `ip`. Takes element zero when the value is a list |
| `_format_client_ssid_vlan` | 446 | Reads `ssid`, falls back to `vlan`. Handles a list value |
| `_print_client_type_summary` | 346 | Counts records by `client_type` at 348-349 |

**Reuse assessment.** This helper is a good starting point for the tier 2 client
capture. Three changes are needed:

1. The helper calls the search endpoints. It therefore returns no signal
   strength and no scalar parent access point. Section 3.1 explains why. The
   capture needs `listSiteWirelessClientsStats` for those fields.
2. The helper sorts and drops nothing, which is correct for a capture.
3. The helper is a private function inside a prompt module. A capture module
   should not import a private prompt helper. Copy the pattern rather than the
   symbol, or promote the fetchers into a shared module.

### 4.2 The org device inventory summary helper

| Item | Value |
|------|-------|
| Module | `src/inventory/org_device_inventory_summary.py` |
| Facade | `src/inventory/org_device_inventory_summary_facade.py:29`-`:34` |
| Dependency setter | `configure_org_device_inventory_summary_dependencies` |

The module counts physical devices by category. It handles virtual chassis in
two different ways, one per device family.

**Switches use member summation.** The fetcher is
`_fetch_switch_physical_inventory(target_org_id) -> list[dict]` at
`src/inventory/org_device_inventory_summary.py:66`. It runs a manual cursor loop.
It reads `results` at `:77` and `next` at `:81`.

The aggregator is `_aggregate_switch_counts(switch_records, distinct) -> list[dict]`
at `src/inventory/org_device_inventory_summary.py:90`. The virtual chassis answer
is two lines:

```python
num_members = int(record.get("num_members") or 1)  # WHY: VC stacks count as members, not one chassis
counts[value] = counts.get(value, 0) + num_members
```

Those lines are `src/inventory/org_device_inventory_summary.py:98` and `:99`. One
switch record can represent four physical units. The `num_members` field is the
only member signal.

**Gateways use one record per node.** The fetcher is
`_fetch_gateway_physical_inventory` at
`src/inventory/org_device_inventory_summary.py:108`. It calls `getOrgInventory`
with `type="gateway"` and `vc=True` at `:112`-`:113`. The `vc=True` argument
expands the virtual chassis server-side, so each physical node returns its own
record. The aggregator at `:125` therefore adds one per record at `:133`.

**Access points use a plain count.** The fetcher is `_fetch_ap_inventory` at
`src/inventory/org_device_inventory_summary.py:142`. It calls `getOrgInventory`
with `type="ap"` at `:146`-`:147`.

The same `vc=True` pattern appears in the shared fetch helper:

```python
response = mistapi.api.v1.orgs.inventory.getOrgInventory(
    mh.apisession, org_id, vc=True, limit=mh.DEFAULT_API_PAGE_LIMIT
)  # vc=True includes all physical VC member devices
```

Those lines are `src/api/api_core_fetch_utils.py:60`-`:62`.

**Reuse assessment.** The capture needs live state, not inventory. Do not reuse
these fetchers directly. Do reuse the `num_members` rule. A capture that counts
switches without `num_members` will under-report a stacked site.

### 4.3 The CSV comparison helper

| Item | Value |
|------|-------|
| Adapter class | `InventoryCSVComparator` |
| Adapter file | `src/refactors/inventory_csvcomparator.py:35` |
| Adapter signature | `__init__(self, fast: bool = False, address_check: bool = False, debug: bool = False, skip_ssl_verify: bool = True) -> None` at `:84` |
| Adapter entry point | `execute(self) -> None` at `:102` |
| Implementation class | `src/inventory/csv_comparator.py:155` |
| Implementation signature | `__init__(self, flags: ComparatorFlags, deps: ComparatorDependencies) -> None` at `:215` |
| Menu registration | `MistHelper.py:3842` and `:3846` |

The adapter builds two dataclasses and forwards them.
`_build_flags(fast, address_check, debug, skip_ssl_verify)` sits at
`src/refactors/inventory_csvcomparator.py:39`. `_build_deps()` sits at `:62`.

`ComparatorFlags` is defined at `src/inventory/csv_comparator.py:101`. Its four
fields are `fast`, `address_check`, `debug`, and `skip_ssl_verify`.

`ComparatorDependencies` is defined at `src/inventory/csv_comparator.py:111`. It
carries ten injected fields, listed at
`src/refactors/inventory_csvcomparator.py:70`-`:79`:
`apisession`, `get_csv_path_fn`, `check_and_generate_csv_fn`,
`create_parse_failures_csv_fn`, `devices_with_site_info_fn`, `get_org_id_fn`,
`get_device_identifier_fn`, `address_utils_cls`, `nominatim_validator_cls`, and
`address_validation_config_cls`.

**Warning. This helper is not a generic row comparison helper.** The class
docstring at `src/refactors/inventory_csvcomparator.py:36` states its purpose as
comparing Mist inventory with a CSV file. Its comparison methods are
`_compare_and_record` at `src/inventory/csv_comparator.py:783` and
`_compare_addresses` at `:823`. Six of its ten dependencies exist only to serve
street-address matching. The menu text at `MistHelper.py:3846` describes a
"configurable address similarity threshold".

The capture-compare view cannot reuse this class. It needs a new, small,
field-agnostic diff function. The dependency-injection shape of
`ComparatorFlags` and `ComparatorDependencies` is still a good pattern to copy,
because it keeps the new comparator testable without a live session.

---

## 5. Tier 3 calls

### 5.1 Switch port state and PoE state

| Item | Value |
|------|-------|
| Function | `mistapi.api.v1.sites.stats.searchSiteSwOrGwPorts` |
| SDK definition | `.venv/Lib/site-packages/mistapi/api/v1/sites/stats.py:2100` |
| HTTP path | `GET /api/v1/sites/{site_id}/stats/ports/search` |
| Specification | `documentation/api/sites/GET_sites_site_id_stats_ports_search.md:7` |
| Scope filter | `device_type` |

This is a dedicated call. It is not a statistics blob. It returns one record per
port for the whole site in one request.

**The scope parameter here is `device_type`, not `type`.** Its docstring at
`.venv/Lib/site-packages/mistapi/api/v1/sites/stats.py:2142` reads
`str{'switch','gateway','all'}, default: all`. **This call is safe.** Its default
already covers both families. It does not carry the trap from section 2.2.

The response requires four fields. They are listed at
`documentation/api/sites/GET_sites_site_id_stats_ports_search.md:94`-`:97`:
`mac`, `org_id`, `port_id`, and `site_id`.

Source file for every line below is
`documentation/api/sites/GET_sites_site_id_stats_ports_search.md`.

| Tier 3 field | Response key | Line | Type | Note |
|--------------|--------------|------|------|------|
| Port up state | `up` | 405 | Boolean | "Indicates if interface is up" |
| Port speed | `speed` | 325 | Integer | |
| Duplex | `full_duplex` | 119 | Boolean | |
| Port name | `port_id` | 237 | String | Example `ge-0/0/0` |
| Switch MAC | `mac` | 167 | String | |
| Port role | `port_usage` | 252 | String | Example `lan` |
| PoE disabled | `poe_disabled` | 219 | Boolean | |
| PoE mode | `poe_mode` | 224 | String | Enum `802.3af`, `802.3at`, `802.3bt` |
| PoE attached | `poe_on` | 228 | Boolean | "Is the device attached to POE" |
| PoE priority | `poe_priority` | 233 | String | Enum `low`, `high` |
| **PoE draw** | `power_draw` | 258 | Number | **Watts.** "Amount of power being used by the interface" |
| Learned MAC count | `mac_count` | 174 | Integer | |
| Neighbor MAC | `neighbor_mac` | 187 | String | |
| Neighbor port | `neighbor_port_desc` | 195 | String | |
| Neighbor name | `neighbor_system_name` | 203 | String | |

**PoE needs no new API call.** The repository already calls this endpoint. It
simply never reads the PoE fields. A search across `src/` finds no read of
`poe_disabled`, `poe_mode`, `poe_on`, `poe_priority`, or `power_draw`. The only
`POE` string in the source is a hardware model name, `"SRX320-POE"`, at
`src/export/const_definitions_exporter.py:40`. Adding PoE to tier 3 costs zero
extra requests.

Existing call sites:

| File and line | Note |
|---------------|------|
| `src/device/prompt_utils.py:399` | Passes `mac=device_mac`, so it fetches one device only |
| `src/export/site_device_exporter.py:178` | Site-wide, through the shared export runner |
| `src/export/org_device_stats_exporter.py:181` | Site-wide |
| `src/export/org_device_stats_exporter.py:416` | Org variant `searchOrgSwOrGwPorts` |
| `src/export/count_exporter.py:69` and `:105` | Count variants |
| `src/org_data_collector.py:340` | Collector path |

The unwrap pattern is at `src/device/prompt_utils.py:405`:

```python
results = response.data.get("results", [])
```

The same file keys the results by `port_id` at `:416`-`:418`.

**Warning.** Do not copy `src/device/prompt_utils.py:399` into the capture. That
call filters by one device MAC. A capture that loops over 50 switches makes 50
requests. One unfiltered site-wide call makes about 3 requests. Section 9 shows
the arithmetic.

### 5.2 Access point port state

Access point ports are **only available through a device statistics blob**.

`searchSiteSwOrGwPorts` covers switches and gateways. Its `device_type` enum at
`.venv/Lib/site-packages/mistapi/api/v1/sites/stats.py:2142` lists `switch`,
`gateway`, and `all`. Access points are not in the enum.

Access point port data lives under `port_stat` in the `stats_ap` shape, at
`documentation/api/sites/GET_sites_site_id_stats_devices.md:1899`. The repository
reads it at `src/device/prompt_utils.py:432`, through `getSiteDeviceStats`. That
read shows a shape difference:

- The dedicated endpoint returns a **list** of port records.
- The `port_stat` blob returns a **dict keyed by port name**.

A compare view must normalize the two shapes before diffing them.

The switch shape and the gateway shape carry `if_stat` instead, at
`documentation/api/sites/GET_sites_site_id_stats_devices.md:3510` and `:5538`.
`src/device/_utility_commands_selection.py:134` reads `stats.get("ports", [])`
for gateways and `:138` reads `stats.get("if_stat", {})`.

**Recommendation.** Skip access point ports in tier 3. The value is low and the
shape handling is expensive.

### 5.3 Access point radio channel and transmit power

Two routes exist. One is free. One is a dedicated call.

**Route A, free. Read the tier 2 device statistics blob.**

The `stats_ap` shape carries `radio_stat` at
`documentation/api/sites/GET_sites_site_id_stats_devices.md:2386`. Its title is
`stats_ap_radio_stat` at `:2387`. It holds one object per band, named `band_24`,
`band_5`, and `band_6`. The `band_24` object starts at `:2390`.

Each band object carries:

| Field | Line | Description from the specification |
|-------|------|-----------------------------------|
| `channel` | 2397 | "Current channel the radio is running on" |
| `power` | 2446 | "Transmit power (in dBm)" |
| `bandwidth` | 2393 | Channel width. Enum `0`, `20`, `40`, `80`, `160` |
| `noise_floor` | 2422 | Example value `-90` |
| `num_clients` | 2433 | Clients on that radio |
| `num_wlans` | 2441 | WLANs applied to the radio |
| `mac` | 2414 | Radio base MAC |

Every one of those fields is nullable. The type is `["integer", "null"]` or
`["string", "null"]`. A capture must handle `None`.

Tier 2 already fetches this response. Route A therefore costs **zero extra API
calls**. Section 2.1 requires `type="all"`, and `radio_stat` only appears on the
access point shape, so no extra argument is needed.

The repository never reads `radio_stat` or `radio_config`. A search across `src/`
finds no such read. This is a confirmed gap, not an existing helper.

**Route B, dedicated call.**

| Item | Value |
|------|-------|
| Function | `mistapi.api.v1.sites.rrm.getSiteCurrentChannelPlanning` |
| Repository call site | `src/export/site_export_utils.py:477` |
| Registry primary key | `["ap", "band"]` at `src/refactors/endpoint_primary_key_strategies.py:2594`-`:2600` |

The repository call is:

```python
response = self.mistapi.api.v1.sites.rrm.getSiteCurrentChannelPlanning(self.apisession, site_id)
```

The flattener at `src/export/site_export_utils.py:55`-`:69` shows the response
shape. It is a nested dict of the form `{ap_mac: {band: {assignment_fields}}}`.
The flattener spreads the innermost dict wholesale with `row.update(payload)`, so
it never names `channel`, `power`, or `bandwidth`. Those keys pass through
without being read by name.

**Route B returns the plan, not the live radio state.** Route A returns the live
state. Use Route A.

Two related endpoints appear in the registry but are never called:
`listSiteDeviceRadioChannels` at `src/refactors/endpoint_primary_key_strategies.py:601`
and `listSiteCurrentRrmNeighbors` at `:256`.

### 5.4 Gateway tunnel state

**Warning. No site-scope tunnel endpoint exists in `mistapi` 0.63.3.**

The names `listSiteVpnPeers` and `searchSiteVpnPeers` do not exist in the
package. The name `searchOrgPeerPaths` also does not exist. The real name is
`searchOrgPeerPathStats`.

Tunnel data is org-scoped only. Filter it by `site_id`.

| Function | SDK definition | Repository call site | Output |
|----------|---------------|---------------------|--------|
| `searchOrgTunnelsStats` | `mistapi/api/v1/orgs/stats.py:1395` | `src/export/org_export_utils.py:576` | `OrgTunnelStats.csv` |
| `searchOrgPeerPathStats` | `mistapi/api/v1/orgs/stats.py:1592` | `src/export/org_device_stats_exporter.py:464` | `OrgVPNPeerStats.csv` |

`searchOrgTunnelsStats` takes 24 parameters. They include `site_id`, `ap`, `mac`,
`node`, `peer_ip`, `peer_host`, `ip`, `tunnel_name`, `protocol`, `auth_algo`,
`encrypt_algo`, `ike_version`, `up`, and `type`.

`searchOrgPeerPathStats` takes `mac`, `site_id`, `type`, `limit`, `start`, `end`,
`duration`, `sort`, and `search_after`. Its `type` enum is `ipsec` and `svr`.

Registry entries confirm the record shape:

| Endpoint | Primary key | Registry line |
|----------|------------|---------------|
| `searchOrgTunnelsStats` | `["id", "device_id", "timestamp"]` | `src/refactors/endpoint_primary_key_strategies.py:2353`-`:2359` |
| `searchOrgPeerPathStats` | `["from_device", "to_device", "timestamp"]` | `src/refactors/endpoint_primary_key_strategies.py:204`-`:212` |

The peer path entry lists `latency`, `jitter`, and `loss` as its time-series
fields.

The method wrapper is `_tunnel_stats()` at `src/export/org_export_utils.py:573`.
The collector calls both at `src/org_data_collector.py:339` and `:341`.

**False positive warning.** A text search for `tunnel` in `src/` returns many
`mxtunnel` and `wxtunnel` hits. Those are wireless Mist Edge tunnel
**configuration** objects. They are not gateway VPN telemetry. Ignore them.

### 5.5 Gateway BGP peer state

Three scopes exist. All three are dedicated calls.

| Scope | Function | SDK definition | Repository call site |
|-------|----------|---------------|---------------------|
| Site | `searchSiteBgpStats` | `mistapi/api/v1/sites/stats.py:532` | `src/export/site_search_exporter.py:157` |
| Org | `searchOrgBgpStats` | Registry at `endpoint_primary_key_strategies.py:2132` | `src/export/org_export_utils.py:569` |
| Device | `showSiteDeviceBgpSummary` | Registry at `endpoint_primary_key_strategies.py:870` | `src/device/_utility_commands_show.py:115`-`:119` |

`searchSiteBgpStats` takes `mac`, `neighbor_mac`, `vrf_name`, `limit`, `start`,
`end`, `duration`, `sort`, and `search_after`. A count variant sits at
`.venv/Lib/site-packages/mistapi/api/v1/sites/stats.py:486`.

The site call runs through the shared export runner. That runner is visible at
`src/export/site_search_exporter.py:126`-`:128`:

```python
response = api_call(mh.apisession, site_id, *extra_args)
```

The site menu entry is 217, at `src/export/site_search_exporter.py:154`.

Peer state fields come from the registry entry at
`src/refactors/endpoint_primary_key_strategies.py:214`-`:220`. The primary key is
`["mac", "neighbor", "timestamp"]`. The indexes are `["site_id", "org_id",
"state", "neighbor_as"]`. **The peer state field is `state`.**

The org variant keys on `["device_id", "neighbor", "timestamp"]` at
`src/refactors/endpoint_primary_key_strategies.py:2132`-`:2138`. The org export
sorts on `peer_ip` at `src/export/org_export_utils.py:569`, so the org shape
surfaces the peer under `peer_ip`.

**Warning. Do not call `clearSiteSsrBgpRoutes`.** It appears at
`src/device/_utility_commands_clear.py:161`. It is a write operation. A capture
must never write.

**Recommendation.** Use the site call. It matches the capture scope and needs one
request.

### 5.6 Active alarms

| Scope | Function | SDK definition | Repository call site |
|-------|----------|---------------|---------------------|
| Site | `searchSiteAlarms` | `mistapi/api/v1/sites/alarms.py:160` | `src/export/site_search_exporter.py:137` |
| Org | `searchOrgAlarms` | `mistapi/api/v1/orgs/alarms.py:135` | `src/export/org_alarm_event_exporter.py:70`-`:77` |

`searchSiteAlarms` takes `group`, `severity`, `type`, `ack_admin_name`, `acked`,
`limit`, `start`, `end`, `duration`, `sort`, and `search_after`.

The `group` enum at `.venv/Lib/site-packages/mistapi/api/v1/sites/alarms.py:189`-`:190`
is `certificate_expiry`, `infrastructure`, `marvis`, and `security`. The
`severity` enum at `:191` is `critical`, `info`, and `warn`.

**The parameter that restricts results to active alarms is `acked=False`.** The
org exporter uses it at `src/export/org_alarm_event_exporter.py:70`-`:77`,
together with `limit=1000` and `duration=f"{hours}h"`. The method is `alarms()`
at `:62`.

**Warning.** The site path at `src/export/site_search_exporter.py:137` passes no
filter arguments. It therefore returns acknowledged alarms as well. A capture
must pass `acked=False` explicitly.

The alarm record carries `id`, `org_id`, `site_id`, `timestamp`, `severity`, and
`type`. It carries a device `mac` when the alarm is device-scoped. Those fields
are visible at `src/db/arango_writer.py:2463`-`:2483`.

Registry entries:

| Endpoint | Primary key | Indexes | Line |
|----------|------------|---------|------|
| `searchOrgAlarms` | `["id", "org_id", "timestamp"]` | `["org_id", "timestamp", "severity", "type", "site_id"]` | `endpoint_primary_key_strategies.py:129`-`:135` |
| `searchSiteAlarms` | `["id", "timestamp"]` | `["site_id", "type", "severity"]` | `endpoint_primary_key_strategies.py:366`-`:372` |

**Warning.** `listSiteAlarms` does not exist in this repository. Do not reference
it.

### 5.7 Tier 3 summary

| Block | Dedicated call | Blob only | Extra requests |
|-------|---------------|-----------|----------------|
| Switch port state | Yes, `searchSiteSwOrGwPorts` | No | About 3 |
| PoE state | Yes, same call | No | 0 |
| Access point port state | No | Yes, `port_stat` in `stats_ap` | 0 if tier 2 runs |
| Radio channel and power | Optional, `getSiteCurrentChannelPlanning` | Yes, `radio_stat` in `stats_ap` | 0 with Route A |
| Gateway tunnel state | Yes, org scope only | No | 2 |
| BGP peer state | Yes, `searchSiteBgpStats` | No | 1 |
| Active alarms | Yes, `searchSiteAlarms` | No | 1 |

---

## 6. Pagination

### 6.1 The repository convention

The convention is two lines. Call the API with an explicit `limit`. Then hand
the response to `mistapi.get_all`.

The canonical example is `src/api/api_core_fetch_utils.py:44`-`:45`:

```python
response = mistapi.api.v1.orgs.sites.listOrgSites(mh.apisession, org_id, limit=mh.DEFAULT_API_PAGE_LIMIT)
return mistapi.get_all(response=response, mist_session=mh.apisession)
```

The module is `APICoreFetchUtils`. `all_sites_with_limit(org_id) -> list[dict]`
sits at `src/api/api_core_fetch_utils.py:32`.
`all_inventory_with_limit(org_id) -> list[dict]` sits at `:48`.
`get_api_response_data(response) -> Any` sits at `:66` and returns
`getattr(response, "data", response)` at `:69`.

The lazy import at `src/api/api_core_fetch_utils.py:43` avoids a circular
dependency between `src/` and `MistHelper.py`.

### 6.2 The pagination helper

| Item | Value |
|------|-------|
| Function | `mistapi.get_all` |
| Definition | `.venv/Lib/site-packages/mistapi/__pagination.py:39` |
| Re-export | `.venv/Lib/site-packages/mistapi/__init__.py:15` |
| Signature | `get_all(mist_session: _APISession, response: _APIResponse) -> list` |
| Companion | `get_next` at `.venv/Lib/site-packages/mistapi/__pagination.py:17` |

The behavior sits at `.venv/Lib/site-packages/mistapi/__pagination.py:55`-`:70`:

1. If `response.data` is a list, the helper concatenates it across pages.
2. If `response.data` is a dict that holds a `results` key, the helper
   concatenates `data["results"]` across pages.
3. **For any other shape, the helper returns an empty list. It raises nothing and
   it logs nothing.**

Point 3 is a silent-failure hazard. A capture must check the returned length
against the `total` field the specification promises at
`documentation/api/sites/GET_sites_site_id_clients_search.md:440`-`:443`. A
zero-length result with a non-zero `total` means the shape assumption broke.

The helper drives paging from `response.next`. It therefore handles both the
`page` cursor and the `search_after` cursor without extra code. The
specification describes `search_after` at
`documentation/api/sites/GET_sites_site_id_clients_search.md:46` and states that
Mist populates it inside the `next` URL.

### 6.3 Page size

| Item | Value |
|------|-------|
| Constant | `DEFAULT_API_PAGE_LIMIT` |
| Definition | `MistHelper.py:1133` |
| Clamp | 1 to 1000 |
| Environment variable | `MIST_PAGE_LIMIT` |

The definition line is:

```python
DEFAULT_API_PAGE_LIMIT = max(1, min(_parsed_limit, 1000))  # Clamp to the 1..1000 range the Mist API accepts
```

Lines `MistHelper.py:1134`-`:1140` log the clamp result and the active page size.
The guidance comment at `MistHelper.py:1125` tells callers to pass
`limit=DEFAULT_API_PAGE_LIMIT` to `getOrgInventory`. The documented default is
1000, recorded at `.github/copilot-instructions.md:213`.

**The 1000 ceiling is a MistHelper rule, not an SDK rule.** No maximum appears
anywhere in the `mistapi` package. Its docstrings state only `limit : int,
default: 100` or `default: 10`. The vendored specification agrees. It shows
`limit | integer | No | 100` at
`documentation/api/sites/GET_sites_site_id_clients_search.md:41`. The same
specification adds an informal note at `:484`: "Specify `limit` for large result
sets, max typically 1000."

Several modules hardcode 1000 rather than reading the constant:

| File and line | Value |
|---------------|-------|
| `src/ui/prompt_utils.py:273` | `limit=1000` |
| `src/export/wifi_clients_exporter.py:12` | `_API_PAGE_LIMIT = 1000` |
| `src/export/site_device_exporter.py:144` | `limit=1000` |
| `src/export/site_client_exporter.py:70` | `limit=1000` |
| `src/firmware/firmware_manager.py:508` and `:3231` | `limit=1000` |
| `src/maps/launcher/_viewer_url_switch.py:30` | `_DEVICES_PAGE_LIMIT = 1000` |

**Recommendation.** The capture should read `DEFAULT_API_PAGE_LIMIT`. That gives
one place to lower the page size if a large site hits a payload limit.

### 6.4 The configured request limit

The request quota is a different concept from the page size. Do not confuse the
two.

| Item | Value |
|------|-------|
| Environment variable name | `API_REQUEST_LIMIT` |
| Where the name appears | `documentation/sample.env:30` |
| Runtime fallback constant | `_DEFAULT_REQUEST_LIMIT` |
| Fallback definition | `src/utils/rate_limiting.py:56` |
| Cache assignment | `src/utils/rate_limiting.py:290` |

The fallback line is:

```python
_DEFAULT_REQUEST_LIMIT = 5000  # WHY: fallback API request quota per hour if API omits it.
```

The cache line reads the live value from the API when the API supplies one:

```python
api_usage_cache["limit"] = usage.get("request_limit", _DEFAULT_REQUEST_LIMIT)
```

**This document did not read any value from `.env`.** It names the variable
`API_REQUEST_LIMIT` only. The value 5000 above is the in-source fallback
constant, not a configured value.

Every vendored specification file confirms the same quota in its error table.
`documentation/api/sites/GET_sites_site_id_clients_search.md:463` reads: "Too
Many Request. The API Token used for the request reached the 5000 API Calls per
hour threshold."

---

## 7. Identity and matching

A compare needs a stable key per record. The key must survive a firmware upgrade
and a device reboot.

### 7.1 Device identity

**Recommended key: `mac`.**

| Candidate | Present on | Stability | Verdict |
|-----------|-----------|-----------|---------|
| `mac` | All three stats shapes, at `GET_sites_site_id_stats_devices.md:1443`, `:3771`, `:5888` | Survives reboot and firmware change | **Use this** |
| `serial` | All three shapes, at `:2995`, `:4684`, `:7062` | Survives reboot and firmware change | Carry as an attribute and a cross-check |
| `id` | Mist device UUID | Most stable of all | Carry as an attribute, but confirm it is present on every shape before keying on it |
| `name` | `:1860`, `:4296`, `:6692` | An operator can rename a device at any time | Never key on this |

Use `DeviceUtils.get_device_identifier` for display text only. Its signature is
`get_device_identifier(device: dict[str, Any], warn_on_missing: bool = False) -> str`
at `src/device/device_utils.py:100`. Its resolution order at
`src/device/device_utils.py:102` is `name`, then `serial`, then `id`, then the
string `"UNKNOWN"`. That order starts with the unstable field, so it is a display
helper, not an identity helper.

**Virtual chassis caution.** A switch stack reports one `mac` for the whole
stack. A member-level change is invisible at that key. The only member signal in
this repository is `num_members`, read at
`src/inventory/org_device_inventory_summary.py:98`. If a stack loses a member
during an upgrade, the device count will not change. Record `num_members` as a
captured attribute and compare it directly.

### 7.2 Wired client identity

**Recommended key: `mac` alone.**

`mac` is the only scalar identity field on a wired record. It sits at
`documentation/api/sites/GET_sites_site_id_wired_clients_search.md:201`.

**Do not put `device_mac` or `port_id` in the key.** Both are arrays, at `:93`
and `:213`. Both change when a cable moves. Treat the whole `device_mac_port`
object array at `:101`-`:140` as attributes, not identity.

Treat `dhcp_hostname` at `:175` as an attribute. DHCP can hand back a different
name.

### 7.3 Wireless client identity

**Recommended key: `mac` alone.**

`mac` sits at `documentation/api/sites/GET_sites_site_id_stats_clients.md:269` on
the stats endpoint and at
`documentation/api/sites/GET_sites_site_id_clients_search.md:256` on the search
endpoint.

**Do not put `ap_mac`, `ssid`, `band`, or `channel` in the key.** All four are
attributes of the current association. All four change on a normal roam.

### 7.4 The two matching risks

**Risk 1. A client roams to a different access point between the two captures.**

An upgrade reboots access points in sequence. Clients move as each access point
drops. This is expected behavior, not a fault.

The parent access point field changes across the two captures. On the stats
endpoint that field is `ap_mac`, at
`documentation/api/sites/GET_sites_site_id_stats_clients.md:96`. On the search
endpoint it is `last_ap`, at
`documentation/api/sites/GET_sites_site_id_clients_search.md:159`.

If the key includes the access point, the compare reports **one false
disappearance plus one false appearance** for every roamed client. On a
200-access-point site, that error can reach hundreds of rows.

**Mitigation.** Key on `mac` alone. Then report the access point change as its
own statistic, named "clients that moved access point". Present that number as
information, not as a fault.

**Risk 2. A client uses a randomized MAC address.**

Modern phones and laptops rotate a private MAC address. The rotation can happen
between the two captures. When it happens, the same physical device appears as
one disappearance plus one appearance.

**No identity key can fix this. State the limit plainly in the report.** The MAC
address is the only stable client identifier the API returns, and a randomized
MAC address is by definition not stable.

There is a partial mitigation. The API exposes a flag:

| Item | Value |
|------|-------|
| Field | `random_mac` |
| Type | Boolean |
| Description | "Whether the client is using randomized MAC Address or not" |
| Location | `documentation/api/sites/GET_sites_site_id_clients_search.md:341`-`:344` |

**Warning. That flag is on `searchSiteWirelessClients` only.** It is not a
top-level field on `listSiteWirelessClientsStats`. The string `random_mac` does
appear in that file at
`documentation/api/sites/GET_sites_site_id_stats_clients.md:214`, but it sits
inside the `guest` sub-object that starts at `:127`. It is a guest registration
attribute there, not the randomization flag.

This forces a design choice:

| Option | Wireless calls | Gets signal strength | Gets `random_mac` |
|--------|---------------|---------------------|-------------------|
| A | `listSiteWirelessClientsStats` only | Yes | No |
| B | `searchSiteWirelessClients` only | No | Yes |
| C | Both | Yes | Yes |

**Recommendation. Take option C.** The extra cost is about 3 requests per
capture. Section 9 shows the arithmetic. Join the two result sets on `mac`.

Then split every client statistic into two buckets:

1. `random_mac = false`. Trust the appeared count and the disappeared count in
   this bucket.
2. `random_mac = true`. Report the total count only. Add a caution note that says
   appeared and disappeared numbers in this bucket are unreliable.

If the design takes option A, then state in the report that the randomization
risk is unmeasured.

### 7.5 Drop the timestamp from the match key

The repository registry uses composite keys that include `timestamp`:

| Endpoint | Primary key | Line |
|----------|------------|------|
| `searchSiteWirelessClients` | `["mac", "timestamp"]` | `src/refactors/endpoint_primary_key_strategies.py:511` |
| `searchSiteWiredClients` | `["mac", "timestamp"]` | `src/refactors/endpoint_primary_key_strategies.py:518` |
| `listSiteDevicesStats` | `["device_id", "timestamp"]` | `src/refactors/endpoint_primary_key_strategies.py:168`-`:176` |
| `searchSiteSwOrGwPorts` | `["device_id", "port_id", "timestamp"]` | `src/refactors/endpoint_primary_key_strategies.py:186`-`:203` |

Those keys exist for time-series storage. Every capture writes a new timestamp.

**Warning. If the compare uses those keys unchanged, every single row will look
new.** Strip `timestamp` from the key before matching. Keep `timestamp` as an
attribute.

The index lists in the same registry are useful. The wireless entry lists
`["mac", "timestamp", "site_id", "ssid", "ap"]` at `:512`. The wired entry lists
`["mac", "timestamp", "site_id", "device_mac"]` at `:519`.

---

## 8. Comparison statistics

Every statistic below names a field this document read in a real response
schema. No statistic below is invented.

| # | Statistic | Source field | Source call | Citation |
|---|-----------|-------------|-------------|----------|
| 1 | Device count by status | `status` | `listSiteDevicesStats` | `GET_sites_site_id_stats_devices.md:3014`, `:4732`, `:7293` |
| 2 | Firmware version distribution, before and after | `version` | `listSiteDevicesStats` | `GET_sites_site_id_stats_devices.md:3149`, `:4808`, `:7445` |
| 3 | Client count by band | `band` | `listSiteWirelessClientsStats` | `GET_sites_site_id_stats_clients.md:104` |
| 4 | Client count by SSID | `ssid` | `listSiteWirelessClientsStats` | `GET_sites_site_id_stats_clients.md:399` |
| 5 | Clients that disappeared | `mac` set difference | Both client calls | `GET_sites_site_id_stats_clients.md:269` |
| 6 | Clients that appeared | `mac` set difference | Both client calls | `GET_sites_site_id_stats_clients.md:269` |
| 7 | Signal strength distribution shift | `rssi` | `listSiteWirelessClientsStats` | `GET_sites_site_id_stats_clients.md:308` |
| 8 | Switch ports that changed state | `up` | `searchSiteSwOrGwPorts` | `GET_sites_site_id_stats_ports_search.md:405` |
| 9 | PoE draw change | `power_draw` | `searchSiteSwOrGwPorts` | `GET_sites_site_id_stats_ports_search.md:258` |
| 10 | Alarms raised | `id` set difference | `searchSiteAlarms` | `endpoint_primary_key_strategies.py:366`-`:372` |

### 8.1 Detail per statistic

**1. Device count by status.** Group the tier 2 device records by `status`. Show
a before column, an after column, and a delta column. The specification types
`status` as `["string", "null"]` at
`documentation/api/sites/GET_sites_site_id_stats_devices.md:3015`-`:3018`. Handle
a null status as its own bucket. Split the table by `type`, at `:3074`, so
access points, switches, and gateways report separately.

**2. Firmware version distribution.** Group by `version` and by `type`. This is
the primary success measure. The expected result is a full move from the old
version to the new version. Any device left on the old version is a failed
upgrade. Sum switch rows with `num_members` from
`src/inventory/org_device_inventory_summary.py:98` if the capture also records
inventory, so a stack does not count as one unit.

**3. Client count by band.** The `band` enum is `24`, `5`, and `6`, documented at
`documentation/api/sites/GET_sites_site_id_stats_clients.md:106`. A band shift
after an upgrade often means a radio failed to come back on one band. Cross-check
against `radio_stat.band_*.channel`, which is null when a radio is down.

**4. Client count by SSID.** Group by `ssid`. An SSID that loses all its clients
means a WLAN failed to reapply. This is a common and serious upgrade fault.

**5 and 6. Clients that disappeared and appeared.** Take the `mac` set from each
capture. The disappeared set is `before - after`. The appeared set is
`after - before`. Split both sets by `random_mac` per section 7.4. Report the two
buckets separately. Never merge them into one headline number.

**7. Signal strength distribution shift.** Build a histogram of `rssi` in 10 dBm
buckets. Compare the two histograms. Add `snr` from `:395` as a second series. A
shift toward weaker values means transmit power did not restore. Confirm that
reading against `radio_stat.band_*.power` from
`documentation/api/sites/GET_sites_site_id_stats_devices.md:2446`.

**8. Switch ports that changed state.** Match port records on `(mac, port_id)`,
from `documentation/api/sites/GET_sites_site_id_stats_ports_search.md:167` and
`:237`. Report every port whose `up` value changed. Split the report into "went
down" and "came up". A port that went down and stayed down is the highest-value
finding in the whole compare. Add `speed` at `:325` and `full_duplex` at `:119`
as secondary change columns, because a renegotiated link is also a fault.

**9. PoE draw change.** Sum `power_draw` per switch and for the whole site.
`power_draw` is in watts, per `:260`. A large drop means powered devices did not
come back. Also count ports where `poe_on` at `:228` changed from true to false.
That count names the exact ports that lost power. **This statistic needs no new
API call.** Section 5.1 explains why.

**10. Alarms raised.** Take the alarm `id` set from each capture. The raised set
is `after - before`. Group the raised set by `severity` and by `type`. Both keys
are registry indexes at
`src/refactors/endpoint_primary_key_strategies.py:372`. Pass `acked=False` so
the set holds active alarms only. Report `critical` alarms at the top of the
compare view.

### 8.2 Two more statistics worth adding

**Clients that moved access point.** Match clients on `mac`. Count the clients
whose `ap_mac` changed. Source field
`documentation/api/sites/GET_sites_site_id_stats_clients.md:96`. Present this as
information. A rolling upgrade always produces a large number here.

**Device uptime reset check.** Compare `uptime` from
`documentation/api/sites/GET_sites_site_id_stats_devices.md:3080`. A device whose
after-uptime is larger than its before-uptime never rebooted. That device did not
take the new firmware, even if its `status` reads connected. This is a
low-cost, high-value cross-check on statistic 2.

---

## 9. Cost estimate

### 9.1 The test site

| Item | Count |
|------|-------|
| Switches | 50 |
| Access points | 200 |
| Gateways | 2, assumed |
| Clients | 3000 total |
| Wireless clients | 2500, assumed |
| Wired clients | 500, assumed |

The gateway count and the client split are assumptions, not measurements. The
brief supplied only the three headline numbers.

Page size is 1000, per `MistHelper.py:1133`.

### 9.2 Tier 2 arithmetic

| Call | Records | Pages | Requests |
|------|---------|-------|----------|
| `listSiteDevicesStats(type="all")` | 50 + 200 + 2 = 252 | ceil(252 / 1000) = 1 | **1** |
| `listSiteWirelessClientsStats` | 2500 | ceil(2500 / 1000) = 3 | **3** |
| `searchSiteWiredClients` | 500 | ceil(500 / 1000) = 1 | **1** |
| `searchSiteWirelessClients`, option C only | 2500 | 3 | **3** |

**Tier 2 total: 5 requests.** With option C from section 7.4, tier 2 is 8
requests.

Caution on the search endpoints. They aggregate a time window. Their default
`duration` is `1d`, at
`documentation/api/sites/GET_sites_site_id_clients_search.md:44`. A busy site can
return far more than its currently connected count. If the day window returns
6000 distinct wireless MAC addresses, that call becomes 6 pages instead of 3.
Set a short `duration` on the search calls to hold the count down.

### 9.3 Tier 3 arithmetic

Port count assumption. A 48-port switch carries about 52 interfaces once uplinks
are counted. A gateway carries about 12.

| Call | Records | Pages | Requests |
|------|---------|-------|----------|
| `searchSiteSwOrGwPorts` | (50 x 52) + (2 x 12) = 2624 | ceil(2624 / 1000) = 3 | **3** |
| Radio channel and power, Route A | Read from the tier 2 response | 0 | **0** |
| `searchOrgTunnelsStats(site_id=...)` | Small | 1 | **1** |
| `searchSiteBgpStats` | Small | 1 | **1** |
| `searchSiteAlarms(acked=False)` | Small | 1 | **1** |

**Tier 3 total: 6 requests.**

#### Peer path statistics are out of scope

`searchOrgPeerPathStats` costs 1 more request, and section 5.4 above records
its shape. The capture does not call it. The reason is the section contract in
`data-model.md` section 3.5, which defines exactly six section keys and gives
each key one `reason` field and one `http_status` field.

A peer path record and a tunnel record do not share a shape. The peer path
primary key is `["from_device", "to_device", "timestamp"]`, and the tunnel
primary key is `["id", "device_id", "timestamp"]`. Putting both under the one
`tunnels` key would put two shapes under one status pair. If one of the two
calls then failed, the section could report neither a clean success nor a clean
failure, and the operator would read a half-empty table as a complete one.

A seventh section key would fix that. It is deliberate future work, not an
oversight. The tunnel data already answers the gateway question that the
upgrade comparison asks, so the capture ships with six sections.

### 9.4 The virtual chassis multiplier

Section 4.2 showed that one switch record can represent several physical units.

If the 50 switches are 4-member stacks, the physical port count becomes
50 x 4 x 52 = 10400. That is 11 pages instead of 3.

| Scenario | Port requests | Tier 3 total |
|----------|--------------|--------------|
| 50 standalone switches | 3 | 7 |
| 50 stacks of 4 members | 11 | 15 |

**The port call is the only tier 3 item that scales with site size.** Everything
else is a fixed small number.

### 9.5 Totals

| Scenario | Tier 2 | Tier 3 | Per capture | Per upgrade, two captures |
|----------|--------|--------|-------------|--------------------------|
| Option A, standalone switches | 5 | 7 | **12** | **24** |
| Option C, standalone switches | 8 | 7 | **15** | **30** |
| Option C, 4-member stacks | 8 | 15 | **23** | **46** |
| Option C, stacks and a busy day window | 11 | 15 | **26** | **52** |

Compare against the hourly quota. The in-source fallback quota is 5000 requests
per hour, at `src/utils/rate_limiting.py:56`. The vendored specification states
the same figure at
`documentation/api/sites/GET_sites_site_id_clients_search.md:463`.

The worst case above is 52 requests for a complete upgrade. That is about **1
percent of the hourly quota**.

### 9.6 What this means for the threading design

**The capture is not request-bound. It is payload-bound and latency-bound.**

Three conclusions follow.

**Conclusion 1. Rate limiting is not a design constraint here.** At 52 requests
against a 5000-per-hour quota, no throttle is needed for the capture itself. Keep
the existing rate-limit guard as a safety net. Do not build a new one.

**Conclusion 2. A small bounded pool is enough.** The capture has six independent
call groups: devices, wireless stats, wireless search, wired clients, ports, and
the small tier 3 calls. Those six groups have no ordering dependency. Run them
concurrently with a pool of about 4 workers.

Sequential execution costs about 12 to 26 round trips. At roughly 1 second per
round trip, that is 12 to 26 seconds per capture. Concurrent execution over 6
groups cuts the wall time to roughly the slowest single group, which is the
wireless client group at 3 pages. That is about 3 to 5 seconds.

Pages inside one group must stay sequential, because `mistapi.get_all` follows
the `next` cursor. A cursor cannot be parallelized. Concurrency belongs at the
group level, not at the page level.

**Conclusion 3. Never fan out per device.** This is the single most important
cost rule.

| Anti-pattern | Requests | Correct pattern | Requests |
|-------------|----------|-----------------|----------|
| `getSiteDeviceStats` per device | 252 | `listSiteDevicesStats(type="all")` | 1 |
| `searchSiteSwOrGwPorts(mac=...)` per switch | 50 | `searchSiteSwOrGwPorts` site-wide | 3 |
| `getSiteDeviceStats` per access point for radio data | 200 | Read `radio_stat` from tier 2 | 0 |

A design that makes all three mistakes costs 502 requests instead of 4. That is a
125-fold increase, and it turns a 5-second capture into a multi-minute capture.

The repository already contains one of the anti-patterns. The call at
`src/device/prompt_utils.py:399` passes `mac=device_mac`. That is correct for its
own single-device use. It is wrong for a capture. Do not copy it.

---

## 10. Open items and stated inferences

This section lists every place where this document reasoned rather than read.

| # | Item | Status |
|---|------|--------|
| 1 | The gateway count of 2 and the 2500 to 500 client split in section 9.1 | Assumption. The brief gave three numbers only. |
| 2 | The 52-interface-per-switch figure in section 9.3 | Assumption based on a 48-port switch plus uplinks. |
| 3 | The 1-second round-trip figure in section 9.6 | Estimate. This document ran no timing test. |
| 4 | Whether `id` is present on all three device stats shapes | Not verified. `mac` and `serial` were verified. Section 7.1 keys on `mac` for that reason. |
| 5 | Whether `listSiteWirelessClientsStats` supports `search_after` or `page` paging | Inferred. `mistapi.get_all` follows `response.next` and is shape-agnostic, so both work. The repository already pages it at `src/export/site_client_exporter.py:71`. |
| 6 | Whether `type="all"` is legal on `searchOrgDevices` | Believed illegal. The docstring at `mistapi/api/v1/orgs/devices.py:672` lists only `ap`, `gateway`, and `switch`. Section 2.3 says to avoid the call. |
| 7 | The description text on `last_ssid` | Confirmed wrong in the vendored specification at `GET_sites_site_id_clients_search.md:232`. The key name is right. |

Verified facts that a reader may find surprising:

1. `searchSiteWirelessClients` returns no signal strength. Section 3.3.
2. `listSiteWirelessClientsStats` returns no top-level `random_mac`. Section 7.4.
3. A wired client record has no `hostname` key. Section 3.4.
4. `searchSiteSwOrGwPorts` uses `device_type`, and its default is already `all`.
   Section 5.1.
5. No site-scope tunnel or peer-path endpoint exists in `mistapi` 0.63.3.
   Section 5.4.
6. PoE data needs zero new API calls. Section 5.1.
7. Access point radio channel and transmit power need zero new API calls.
   Section 5.3.
8. `mistapi.get_all` returns an empty list without any warning when the response
   shape is unexpected. Section 6.2.
