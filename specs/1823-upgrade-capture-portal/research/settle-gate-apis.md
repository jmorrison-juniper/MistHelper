# Settle Gate APIs — Technical Reference

**Feature**: 1823 upgrade capture portal
**Date**: 2026-08-19
**Status**: Research. No source code changed.

## 1. Scope and method

This document records the Mist API surface that the post-upgrade settle gate needs.

The settle gate rule under study is:

1. Poll the device events API every 20 seconds.
2. Wait for the device connected event.
3. Poll device statistics until the uptime resets **and** the firmware version changes.
4. Wait 60 more seconds.
5. Capture. Access points wait a further 60 seconds.

Every finding below carries a `file_path:line_number` citation. Sources are the
vendored API specification under `documentation/api/`, two vendor HTML renderings
under `documentation/`, the installed `mistapi` package version 0.63.3, and the
live MistHelper source. Where this document infers rather than reads, it says so
in plain words.

This document never read `.env`. It names configuration variables only.

---

## 2. Settle gate mapped to API calls

| Gate step | API call | Field to watch |
|---|---|---|
| Device reconnected | `searchOrgDeviceEvents` | `type` equals `AP_CONNECTED`, `SW_CONNECTED`, or `GW_CONNECTED` |
| Device rebooted | `searchOrgDeviceEvents` | `type` equals `AP_RESTARTED`, `SW_RESTARTED`, or `GW_RESTARTED` |
| Uptime reset | `listOrgDevicesStats` | `uptime` drops below the previous reading |
| Firmware changed | `listOrgDevicesStats` | `version` differs from the pre-upgrade reading |
| Upgrade job finished | `getSiteDeviceUpgrade` | `status` equals `completed` |

**Important**: the vendor documents `AP_RESTARTED` as the uptime-reset signal
itself. See section 4.1. The event stream and the statistics stream therefore
carry the same fact. The portal can use the event as a cheap trigger and the
statistics call as the authoritative confirmation.

---

## 3. Device event endpoints

### 3.1 Organization scope

**HTTP**: `GET /api/v1/orgs/{org_id}/devices/events/search`
(`documentation/api/orgs/GET_orgs_org_id_devices_events_search.md:7`)

**Query parameters**
(`documentation/api/orgs/GET_orgs_org_id_devices_events_search.md:27-42`)

| Name | Type | Default | Description |
|---|---|---|---|
| `mac` | string | — | Device mac |
| `model` | string | — | Device model |
| `device_type` | string | **`ap`** | Device family filter |
| `text` | string | — | Event message |
| `timestamp` | string | — | Event time |
| `type` | string | — | Event type filter |
| `last_by` | string | — | Return last or recent event for the passed field |
| `includes` | string | — | Include events from additional indices |
| `limit` | integer | `100` | Page size |
| `start` | string | — | Epoch seconds, or a relative string like `-1d` |
| `end` | string | — | Epoch seconds, or a relative string like `now` |
| `duration` | string | `1d` | Window length like `7d` |
| `sort` | string | `timestamp` | Sort field. A `-` prefix means descending |
| `search_after` | string | — | Pagination cursor |

**Warning — the `device_type` default is `ap`.** The portal must set
`device_type` explicitly for switch and gateway fleets. If the portal omits it,
the organization search silently returns access point events only. The gate
would then never observe a `SW_CONNECTED` or `GW_CONNECTED` event and would hang
until timeout. This is the single largest correctness risk in the event path.
The default appears at
`documentation/api/orgs/GET_orgs_org_id_devices_events_search.md:31`.

**`type` accepts a comma-separated list.** Live code proves this at
`src/firmware/firmware_manager.py:3825`, which passes
`type="SYSTEM_UPGRADE_COMPLETED,SYSTEM_UPGRADE_FAILED,SYSTEM_UPGRADE_STARTED"`.

### 3.2 Site scope

**HTTP**: `GET /api/v1/sites/{site_id}/devices/events/search`
(`documentation/api/sites/GET_sites_site_id_devices_events_search.md:7`)

The parameter set is identical **except that `device_type` does not exist**
(`documentation/api/sites/GET_sites_site_id_devices_events_search.md:27-41`).
Site scope therefore returns every device family by default. This asymmetry is
real and the portal must account for it.

### 3.3 Response envelope

Both endpoints return the same envelope
(`documentation/api/orgs/GET_orgs_org_id_devices_events_search.md:55-228`,
`documentation/api/sites/GET_sites_site_id_devices_events_search.md:54-227`):

```json
{ "end": 0, "limit": 0, "next": "", "results": [], "start": 0, "total": 0 }
```

Required keys are `end`, `limit`, `results`, `start`, and `total`
(`documentation/api/orgs/GET_orgs_org_id_devices_events_search.md:220-227`).
`next` is optional and carries the URL for the following page.

Each item in `results` uses the `device_event` schema. Required item keys are
`org_id`, `timestamp`, and `type`
(`documentation/api/orgs/GET_orgs_org_id_devices_events_search.md:74-78`).

Fields the settle gate needs from each event:

| Field | Type | Citation |
|---|---|---|
| `mac` | string | `documentation/api/orgs/GET_orgs_org_id_devices_events_search.md:131-133` |
| `device_type` | string, enum `ap`, `gateway`, `switch` | `...:120-122` |
| `device_name` | string | `...:116-118` |
| `type` | string | `...:197-199` |
| `timestamp` | number, epoch seconds | `...:192-196` |
| `version` | string | `...:205-207` |
| `reason` | string, optional | `...:172-174` |
| `text` | string, optional | `...:188-190` |
| `ev_type` | string, enum `notice`, `warn` | `...:124-126` |

The `ap` and `ap_name` fields are marked for deprecation. Use `mac` and
`device_name` (`documentation/api/orgs/GET_orgs_org_id_devices_events_search.md:81-87`).

### 3.4 Pagination

The cursor is `search_after`. The vendor description is explicit:

> Pagination cursor for retrieving subsequent pages of results. This value is
> automatically populated by Mist in the `next` URL from the previous response
> and should not be manually constructed.

(`documentation/api/orgs/GET_orgs_org_id_devices_events_search.md:42`)

**Documentation defect.** Both event search documents state under Pagination:
"Supports pagination. Use `limit` and `page` query parameters"
(`documentation/api/orgs/GET_orgs_org_id_devices_events_search.md:243` and
`documentation/api/sites/GET_sites_site_id_devices_events_search.md:242`).
No `page` parameter exists in either parameter table. The claim is wrong. The
site document contradicts it correctly at
`documentation/api/sites/GET_sites_site_id_devices_events_search.md:258`, which
says "Uses cursor-based pagination".

MistHelper pages with `mistapi.get_all(response=..., mist_session=...)`. See
`src/firmware/firmware_manager.py:3830`.

### 3.5 SDK signatures, verified against installed `mistapi` 0.63.3

```
mistapi.api.v1.orgs.devices.searchOrgDeviceEvents(
    mist_session, org_id, mac=None, model=None, device_type=None, text=None,
    type=None, last_by=None, includes=None, limit=None, start=None, end=None,
    duration=None, sort=None, search_after=None) -> APIResponse

mistapi.api.v1.sites.devices.searchSiteDeviceEvents(
    mist_session, site_id, mac=None, model=None, text=None, type=None,
    last_by=None, includes=None, limit=None, start=None, end=None,
    duration=None, sort=None, search_after=None) -> APIResponse
```

The documented SDK paths agree with the runtime for these two calls
(`documentation/api/orgs/GET_orgs_org_id_devices_events_search.md:251`,
`documentation/api/sites/GET_sites_site_id_devices_events_search.md:250`).

---

## 4. The event keys that matter

### 4.1 Confirmed from vendor documentation

The vendor describes the `device-updowns` webhook topic as a subset of device
events. The list is at `documentation/Site _ API _ Mist.html:15859-15864`:

| Key | Vendor description | Citation |
|---|---|---|
| `AP_DISCONNECTED` | "from our perspective, the AP is disconnected" | `documentation/Site _ API _ Mist.html:15860` |
| `AP_CONNECTED` | "AP is now connected, i.e. it was disconnected before" | `documentation/Site _ API _ Mist.html:15861` |
| `AP_RESTARTED` | "AP was restarted where we observe the uptime being reset, e.g. manual restart, upgrade, switch port bounced" | `documentation/Site _ API _ Mist.html:15862-15863` |

The `AP_RESTARTED` description is the most valuable sentence in this research.
The vendor states that `AP_RESTARTED` fires when Mist observes the uptime reset,
and the vendor names upgrade as a cause. `AP_RESTARTED` is therefore a direct
proxy for step 3 of the settle gate for access points.

The two quoted descriptions above keep the vendor spelling exactly, including
the Latin abbreviations. This document does not alter quoted vendor text.

Further access point keys appear at
`documentation/Org _ API _ Mist.html:10237-10255`:

| Key | Citation |
|---|---|
| `AP_CONFIG_CHANGED_BY_RRM` | `documentation/Org _ API _ Mist.html:10237` |
| `AP_CONFIG_CHANGED_BY_USER` | `documentation/Org _ API _ Mist.html:10240` |
| `AP_CONFIGURED` | `documentation/Org _ API _ Mist.html:10243` |
| `AP_RECONFIGURED` | `documentation/Org _ API _ Mist.html:10246` |
| `AP_RESTART_BY_USER` | `documentation/Org _ API _ Mist.html:10249` |
| `AP_RESTARTED` | `documentation/Org _ API _ Mist.html:10252` |
| `AP_RRM_ACTION` | `documentation/Org _ API _ Mist.html:10255` |

Switch keys visible in the same rendering:

| Key | Citation |
|---|---|
| `SW_DOT1XD_USR_AUTHENTICATED` | `documentation/Org _ API _ Mist.html:9121` |
| `SW_PORT_UP` | `documentation/Org _ API _ Mist.html:10298` |
| `SW_VC_MEMBER_ADDED` | `documentation/Org _ API _ Mist.html:10309` |

`AP_ASSIGNED` appears as the worked example in the constants document
(`documentation/api/constants/GET_const_device_events.md:63-74`).

### 4.2 Confirmed from live MistHelper code

`src/firmware/firmware_manager.py:3825` passes three keys to the live API:

- `SYSTEM_UPGRADE_STARTED`
- `SYSTEM_UPGRADE_COMPLETED`
- `SYSTEM_UPGRADE_FAILED`

This `SYSTEM_UPGRADE_*` family is device-family neutral. It carries no `AP_`,
`SW_`, or `GW_` prefix. The portal should treat it as the cross-family upgrade
lifecycle signal. The code strips the prefix for display at
`src/firmware/firmware_manager.py:3858`.

`SW_RESTARTED` appears in a MistHelper contract example at
`specs/561-mist-count-site-system-events/contracts/count_site_system_events.md:62`.
That is a MistHelper-authored sample and not vendor text. Treat it as weak
evidence.

### 4.3 Not confirmed — inference stated plainly

**This document could not confirm the following keys from any read source in
this repository.** They are named in the feature request, and the naming pattern
is consistent, but no file in this repository spells them:

- `SW_CONNECTED`
- `GW_CONNECTED`
- `GW_RESTARTED`
- `AP_UPGRADED`, `SW_UPGRADED`, `GW_UPGRADED`
- `AP_UPGRADE_FAILED`, `SW_UPGRADE_FAILED`, `GW_UPGRADE_FAILED`
- `SW_UPGRADE_PENDING`, `GW_UPGRADE_PENDING`
- `GW_UPGRADE_REBOOTING`

**This is an inference, not a reading.** The `AP_` family confirms the pattern
`{FAMILY}_CONNECTED` and `{FAMILY}_RESTARTED`. It is reasonable to expect
`SW_CONNECTED`, `GW_CONNECTED`, and `GW_RESTARTED` to exist. The portal must not
depend on that expectation without checking.

**Required action before implementation.** Call the live constants endpoint and
record the full result:

- **HTTP**: `GET /api/v1/const/device_events`
  (`documentation/api/constants/GET_const_device_events.md:7`)
- **SDK**: `mistapi.api.v1.constants.events.listDeviceEventsDefinitions()`
  (`documentation/api/constants/GET_const_device_events.md:100`)

Each returned item uses the `const_event` schema with fields `description`,
`display`, `example`, `group`, and `key`. Required fields are `display` and
`key` (`documentation/api/constants/GET_const_device_events.md:41-57`).

The vendored constants document contains the schema and one example only. It
does **not** contain the key list. That gap is why section 4.3 exists.

**Recommended defensive design.** Do not hard-code the connected-event key list.
Load the catalogue from `listDeviceEventsDefinitions` at portal start, filter for
keys that end in `_CONNECTED` and `_RESTARTED`, and cache the result. This
survives a vendor key rename and removes the guesswork above.

---

## 5. Device statistics endpoints

### 5.1 Endpoints

| Scope | HTTP | Citation |
|---|---|---|
| Site, all devices | `GET /api/v1/sites/{site_id}/stats/devices` | `documentation/api/sites/GET_sites_site_id_stats_devices.md:7` |
| Organization, all devices | `GET /api/v1/orgs/{org_id}/stats/devices` | `documentation/api/orgs/GET_orgs_org_id_stats_devices.md:7` |
| Site, one device | `GET /api/v1/sites/{site_id}/stats/devices/{device_id}` | Read from the installed SDK |

### 5.2 SDK signatures, verified against installed `mistapi` 0.63.3

```
mistapi.api.v1.orgs.stats.listOrgDevicesStats(
    mist_session, org_id, type=None, status=None, site_id=None, mac=None,
    evpntopo_id=None, evpn_unused=None, fields=None, start=None, end=None,
    duration=None, limit=None, page=None) -> APIResponse

mistapi.api.v1.sites.stats.listSiteDevicesStats(
    mist_session, site_id, type=None, status=None, limit=None,
    page=None) -> APIResponse

mistapi.api.v1.sites.stats.getSiteDeviceStats(
    mist_session, site_id, device_id, fields=None) -> APIResponse
```

**Key asymmetry.** `listOrgDevicesStats` accepts `mac`, `site_id`, and `fields`.
`listSiteDevicesStats` accepts none of those. The organization call is the only
list call that can narrow the payload. Section 8 explains why that matters.

**Gotcha.** The site call returns access point statistics only unless the caller
passes `type="all"`
(`documentation/api/sites/GET_sites_site_id_stats_devices.md:7599`). Live code
already does this at `src/firmware/firmware_manager.py:505-507`.

Both list calls page with `limit` and `page`
(`documentation/api/sites/GET_sites_site_id_stats_devices.md:7583`,
`documentation/api/orgs/GET_orgs_org_id_stats_devices.md:7592`). This is offset
paging and differs from the event search cursor paging.

### 5.3 Fields the settle gate needs

All citations point into `documentation/api/sites/GET_sites_site_id_stats_devices.md`.

| Field | Type | Description | Example | Line |
|---|---|---|---|---|
| `uptime` | number or null | "How long, in seconds, has the device been up (or rebooted)" | `13500` | `3080-3090` |
| `version` | string or null | Firmware version | `0.14.12345` | `3149-3158` |
| `status` | string or null | No enum declared in the schema | — | `3014-3020` |
| `serial` | string or null | "Serial Number" | `FXLH2015170017` | `2995-3005` |
| `model` | string or null | "Device model" | `AP200` | `1834-1844` |
| `mac` | string or null | "Device mac" | `5c5b35000010` | `1443-1453` |
| `last_seen` | number or null | "Last seen timestamp" | `1470417522` | `1074-1084` |

**`uptime` is measured in seconds.** The vendor states this directly at
`documentation/api/sites/GET_sites_site_id_stats_devices.md:3085`. The gate
detects a reboot when the current `uptime` reading is lower than the previous
reading for the same device.

**Caution — `uptime` is nullable.** The schema declares
`"type": ["number", "null"]`. A null reading must not be treated as zero,
because zero would look like a fresh reboot. Treat null as "no reading" and
retry.

**Caution — the `status` field carries no documented enum.** The schema at
`documentation/api/sites/GET_sites_site_id_stats_devices.md:3014-3020` declares
a bare nullable string with no description and no enum. Do not build gate logic
on `status` values. Use `uptime` and `version`.

### 5.4 The `fwupdate` progress blob

The blob is titled `fwupdate_stat`
(`documentation/api/sites/GET_sites_site_id_stats_devices.md:645-694`).

| Field | Type | Range or enum | Line |
|---|---|---|---|
| `progress` | integer or null | 0 to 100. Example `10` | `649-661` |
| `status` | object | enum `inprogress`, `failed`, `upgraded`, `success`, `scheduled`, `error` | `662-666` |
| `status_id` | integer or null | Example `5` | `667-677` |
| `timestamp` | number | "Epoch (seconds)" | `678-682` |
| `will_retry` | boolean or null | Example `false` | `683-692` |

**Schema defect.** The `status` field declares `"type": "object"` while its own
description names a string enum
(`documentation/api/sites/GET_sites_site_id_stats_devices.md:662-666`). The
declared type is wrong. Live MistHelper code reads `status` as a string and
lowercases it. See `src/firmware/firmware_manager.py:3319-3354`. Follow the code,
not the declared type.

**Enum drift between code and schema.** The documented `fwupdate.status` enum
does not include `upgrading` or `downloading`. Live code treats
`("inprogress", "upgrading", "downloading")` as the active set at
`src/firmware/firmware_manager.py:519` and `:3340-3354`. The two extra values
belong to the upgrade **job** enum in section 6, not to the statistics blob. The
code mixes two enumerations. The portal should keep them apart.

---

## 6. The upgrade job status endpoint

### 6.1 Read an upgrade by identifier

**HTTP**: `GET /api/v1/sites/{site_id}/devices/upgrade/{upgrade_id}`
(`documentation/api/utilities/GET_sites_site_id_devices_upgrade_upgrade_id.md:7`)

**SDK, verified against installed `mistapi` 0.63.3**:

```
mistapi.api.v1.sites.devices.getSiteDeviceUpgrade(
    mist_session, site_id, upgrade_id) -> APIResponse
mistapi.api.v1.orgs.devices.getOrgDeviceUpgrade(
    mist_session, org_id, upgrade_id) -> APIResponse
mistapi.api.v1.sites.devices.listSiteDeviceUpgrades(
    mist_session, site_id, status=None) -> APIResponse
mistapi.api.v1.orgs.devices.listOrgDeviceUpgrades(
    mist_session, org_id) -> APIResponse
```

**Documentation defect.** The vendored document names the SDK path
`mistapi.api.v1.utilities.upgrade.getSiteDeviceUpgrade()`
(`documentation/api/utilities/GET_sites_site_id_devices_upgrade_upgrade_id.md:237`).
That path does not match the installed package. The runtime path is
`mistapi.api.v1.sites.devices.getSiteDeviceUpgrade`, and live MistHelper code
uses the runtime path at `src/firmware/firmware_manager.py:3743-3754`. Trust the
runtime path.

### 6.2 The `status` enumeration

`cancelled`, `completed`, `created`, `downloaded`, `downloading`, `failed`,
`upgrading`, `queued`
(`documentation/api/utilities/GET_sites_site_id_devices_upgrade_upgrade_id.md:112-115`).

The only terminal success value is `completed`. The terminal failure values are
`failed` and `cancelled`. Every other value means the job is still running.

### 6.3 The phase field

**The field is named `current_phase`, not `phase`.** It is an int32 described as
"Current canary or rrm phase in progress"
(`documentation/api/utilities/GET_sites_site_id_devices_upgrade_upgrade_id.md:54-58`).

`current_phase` indexes into `canary_phases`, an array of percentages with
default `[1, 10, 50, 100]`
(`documentation/api/utilities/GET_sites_site_id_devices_upgrade_upgrade_id.md:40-53`).

`current_phase` is meaningful only when `strategy` is `canary` or `rrm`. The
`strategy` enum is `big_bang` (upgrade all at once), `canary`, `rrm` (access
points only), and `serial` (one at a time)
(`documentation/api/utilities/GET_sites_site_id_devices_upgrade_upgrade_id.md:116-119`).

### 6.4 `reboot_in_progress`

**`reboot_in_progress` is not a top-level boolean.** It is an array of MAC
address strings nested inside the `targets` object, described as "List of
devices MAC Addresses which are rebooting"
(`documentation/api/utilities/GET_sites_site_id_devices_upgrade_upgrade_id.md:156-162`).

This shape is useful to the settle gate. The portal can read
`targets.reboot_in_progress` to learn exactly which devices are mid-reboot,
without polling each device.

Full `targets` contents
(`documentation/api/utilities/GET_sites_site_id_devices_upgrade_upgrade_id.md:125-198`):

| Field | Type | Meaning |
|---|---|---|
| `download_requested` | string array | Cloud requested a firmware download |
| `downloaded` | string array | Firmware download finished |
| `downloading` | string array | Firmware download running |
| `failed` | string array | Upgrade failed |
| `reboot_in_progress` | string array | Device rebooting |
| `rebooted` | string array | Device rebooted successfully |
| `scheduled` | string array | Upgrade scheduled |
| `skipped` | string array | Requested version already running |
| `total` | int32 | Count of devices in this upgrade |
| `upgraded` | string array | Upgrade succeeded |

`targets` is `readOnly`
(`documentation/api/utilities/GET_sites_site_id_devices_upgrade_upgrade_id.md:197`).
The only required top-level field is `id`
(`documentation/api/utilities/GET_sites_site_id_devices_upgrade_upgrade_id.md:211-213`).

Other top-level fields worth noting:

| Field | Type | Notes | Line |
|---|---|---|---|
| `target_version` | string | Version to upgrade to | `120-124` |
| `start_time` | int32 | "Firmware download start time in epoch" | `107-111` |
| `reboot_at` | int32 | "reboot start time in epoch" | `102-106` |
| `enable_p2p` | boolean | Default `false`. Allows local access-point-to-access-point transfer | `59-63` |
| `force` | boolean | Upgrade even when the version already matches | `64-67` |
| `max_failure_percentage` | int32 | Failure tolerance | `77-81` |
| `upgrade_plan` | object | Phase number to device list, when strategy is not `big_bang` | `199-209` |

### 6.5 The matching cancel call

**HTTP**: `POST /api/v1/sites/{site_id}/devices/upgrade/{upgrade_id}/cancel`
(`documentation/api/utilities/POST_sites_site_id_devices_upgrade_upgrade_id_cancel.md:7`)

The vendor describes it as a best-effort operation:

> Best effort to cancel an upgrade. Devices which are already upgraded wont be
> touched

(`documentation/api/utilities/POST_sites_site_id_devices_upgrade_upgrade_id_cancel.md:11`)

**SDK, verified against installed `mistapi` 0.63.3**:

```
mistapi.api.v1.sites.devices.cancelSiteDeviceUpgrade(
    mist_session, site_id, upgrade_id) -> APIResponse
mistapi.api.v1.orgs.devices.cancelOrgDeviceUpgrade(
    mist_session, org_id, upgrade_id) -> APIResponse
```

The vendored document again names the wrong path,
`mistapi.api.v1.utilities.upgrade.cancelSiteDeviceUpgrade()`
(`documentation/api/utilities/POST_sites_site_id_devices_upgrade_upgrade_id_cancel.md:56`).
Use the runtime path.

The start call is
`mistapi.api.v1.orgs.devices.upgradeOrgDevices(mist_session, org_id, body)`,
where `body` is a dict or a list.

---

## 7. Timestamp semantics

This is settled from four independent sources. All timestamps in this API family
are **epoch seconds**, never milliseconds.

| Source | Evidence | Citation |
|---|---|---|
| Event schema | `"timestamp": {"type": "number", "description": "Epoch (seconds)"}` | `documentation/api/orgs/GET_orgs_org_id_devices_events_search.md:192-196` |
| `fwupdate` schema | `"timestamp": {"type": "number", "description": "Epoch (seconds)"}` | `documentation/api/sites/GET_sites_site_id_stats_devices.md:678-682` |
| Vendor example | `"timestamp": 1461220784` — ten digits | `documentation/Site _ API _ Mist.html:15760` |
| Constants example | `"timestamp": 1552408871` — ten digits | `documentation/api/constants/GET_const_device_events.md:63-74` |
| Live code | `(time.time() - fw_timestamp) / 3600` treated as hours | `src/firmware/firmware_manager.py:3356-3374` |
| Live code | `datetime.fromtimestamp(timestamp)` with no divisor | `src/firmware/firmware_manager.py:3403-3410` |

**Float capable.** The event `timestamp` and the `fwupdate.timestamp` both
declare `"type": "number"`, not `"integer"`. Sub-second precision is possible.
The portal must not assume an integer.

**Mixed encoding across objects.** The upgrade job object uses int32 for its
epoch fields. `start_time` and `reboot_at` are both declared
`"type": "integer", "contentEncoding": "int32"`
(`documentation/api/utilities/GET_sites_site_id_devices_upgrade_upgrade_id.md:102-111`).
The event envelope `start` and `end` are also int32
(`documentation/api/orgs/GET_orgs_org_id_devices_events_search.md:212-219`).
So the unit is uniform but the numeric type is not. Parse defensively.

**`uptime` is not a timestamp.** It is a duration in seconds since boot
(`documentation/api/sites/GET_sites_site_id_stats_devices.md:3085`). The example
value `13500` means the device has been up for 13500 seconds, which is 3 hours
and 45 minutes. The gate compares two consecutive readings and looks for a
decrease.

**Practical note for the gate.** A device that reboots quickly may report a small
positive `uptime` rather than a value near zero, because the statistics poll can
land some seconds after boot. The gate must test "current is less than previous",
not "current is near zero".

---

## 8. Rate limits

### 8.1 The documented limit

Every endpoint document repeats the same 429 text:

> Too Many Request. The API Token used for the request reached the 5000 API
> Calls per hour threshold

Citations:
`documentation/api/orgs/GET_orgs_org_id_devices_events_search.md:239`,
`documentation/api/sites/GET_sites_site_id_devices_events_search.md:238`,
`documentation/api/utilities/GET_sites_site_id_devices_upgrade_upgrade_id.md:225`.

The limit is **5000 calls per hour per API token**.

### 8.2 Repository constants that track the limit

| Constant | Value | Citation |
|---|---|---|
| `_DEFAULT_REQUEST_LIMIT` | `5000` | `src/utils/rate_limiting.py:56` |
| `_api_usage_cache["limit"]` | `5000` | `MistHelper.py:2275` |
| `_HOUR_SECONDS` | `3600` | `src/utils/rate_limiting.py:41` |
| `_DELAY_HARD_MIN` | `0.01` | `src/utils/rate_limiting.py:39` |
| `_DELAY_HARD_MAX` | `10.0` | `src/utils/rate_limiting.py:40` |
| `_REFRESH_THRESHOLD_REQUESTS` | `100` | `src/utils/rate_limiting.py:51` |
| `_REFRESH_ELAPSED_SECONDS` | `60` | `src/utils/rate_limiting.py:52` |

The governing class is `RateLimitingUtils` at `src/utils/rate_limiting.py:113`.
It is a static-method facade that runs a PID controller. The controller compares
actual usage against an ideal linear consumption curve and returns a per-call
delay clamped between 0.01 and 10.0 seconds. See
`src/utils/rate_limiting.py:326-333`.

The usage cache lives at `MistHelper.py:2272-2279`. MistHelper imports the
utilities at `MistHelper.py:3314`. A command line flag named `--fast` bypasses
rate limiting (`MistHelper.py:4937-4939`).

State files are `tuning_data.json` and `delay_metrics.json`, both resolved into
the `data` directory (`src/utils/rate_limiting.py:27-29`).

### 8.3 The arithmetic risk

A 20-second poll interval yields **180 polls per hour** per poll stream.

| Design | Calls per hour | Share of 5000 | Verdict |
|---|---|---|---|
| One organization event search per 20 seconds | 180 | 3.6 percent | Safe |
| One organization event search plus one organization statistics list per 20 seconds | 360 | 7.2 percent | Safe. Recommended |
| Per-site polling across 27 sites | 4860 | 97.2 percent | At the edge. Avoid |
| Per-device polling, 28 devices | 5040 | Over quota | Fails |
| Per-device polling, 300 devices | 54000 | 10.8 times quota | Fails badly |

**The decisive number**: 5000 divided by 180 equals 27.7. **A 20-second poll
cadence supports at most 27 independent poll streams before the token quota
runs out, and that leaves no headroom for anything else.**

Per-device polling is not viable. Per-site polling is not viable beyond roughly
a dozen sites once headroom is reserved.

### 8.4 Pagination multiplies the cost

The table above counts one call per poll. Pagination breaks that assumption.

- The event search defaults to `limit=100`
  (`documentation/api/orgs/GET_orgs_org_id_devices_events_search.md:37`). A busy
  organization can produce far more than 100 events in a 20-second window.
  `mistapi.get_all()` will then follow `next` repeatedly, and one logical poll
  becomes many HTTP calls.
- Live MistHelper code already raises the statistics page size to
  `limit=1000` (`src/firmware/firmware_manager.py:505-512`).

**Recommendation.** Raise `limit` on the event search and narrow the window with
`start` and `end` so that each poll fits in one page. Narrow further with
`type` so the search returns only connect and restart events. Both controls cut
the page count directly.

### 8.5 Batching options, ranked

1. **Poll once at organization scope, not per device.** Use
   `searchOrgDeviceEvents` with a `type` filter and an explicit `device_type`,
   then fan the results out to per-device state in memory. Cost stays flat as
   the fleet grows. This is the recommended design.
2. **Use `listOrgDevicesStats` with the `fields` parameter.** Only the
   organization statistics call accepts `fields`. Requesting a narrow field set
   shrinks the payload sharply. The site call cannot do this.
3. **Read `targets.reboot_in_progress` from the upgrade job.** One
   `getSiteDeviceUpgrade` call returns the reboot state of every device in the
   job. This can replace a whole class of per-device probes. See section 6.4.
4. **Widen the interval once the connected event arrives.** The 20-second
   cadence only needs to be tight while waiting for reconnection. After that the
   gate waits a fixed 60 seconds, and no polling is required during the wait.
5. **Reserve headroom.** The portal shares the token with the rest of
   MistHelper. Budget no more than half the quota for the settle gate.

**Note on the shared token.** The rate limit is per token. If several portal
sessions run at once with the same token, the quota is shared. The 5000 figure
is not per session.

---

## 9. Existing polling code

### 9.1 Menu 137

**Menu 137 is the firmware upgrade status check.** It is registered at
`MistHelper.py:3835-3840`:

```python
"137": (
    lambda: _build_firmware_manager(
        apisession, ConfigUtils.get_cached_or_prompted_org_id()
    ).check_firmware_upgrade_status(),
    "Check current firmware upgrade status across organization with detailed progress monitoring and export to CSV",
),
```

The operation registry agrees and classifies it as interactive
(`src/utils/operation_registry.py:110-113`).

The entry point is `FirmwareManager.check_firmware_upgrade_status` at
`src/firmware/firmware_manager.py:260-277`. It resolves a scope choice, resolves
an optional site filter, then dispatches
(`src/firmware/firmware_manager.py:305-316`):

- Scope `5` enters continuous monitoring.
- Scope `6` lists organization-level upgrade jobs.
- Any other scope runs a single status check.

### 9.2 The continuous monitoring loop

The loop is at `src/firmware/firmware_manager.py:341-351`:

```python
def _run_monitoring_loop(self, site_filter: str | None) -> None:
    """Drive the poll-print-sleep loop until all upgrades complete."""
    iteration = 0
    while True:
        iteration += 1
        self._clear_monitoring_screen()
        self._present_monitoring_iteration_header(iteration)
        result = self._execute_monitoring_check(site_filter)
        if self._handle_monitoring_result(result, iteration):
            return
        time.sleep(7)
```

**The sleep interval is 7 seconds**
(`src/firmware/firmware_manager.py:351`). The banner discloses the same cadence
at `src/firmware/firmware_manager.py:336`, and the audit log repeats it at
`src/firmware/firmware_manager.py:339`.

The loop exits on `KeyboardInterrupt`, caught at
`src/firmware/firmware_manager.py:324-327`.

**Caution for the portal.** The existing cadence is 7 seconds. The settle gate
specifies 20 seconds. These are different numbers for different jobs. The portal
must not reuse the 7-second constant. At 7 seconds a single stream costs 514
calls per hour, which is 10.3 percent of quota — nearly three times the
20-second cost.

The banner also warns that "Each refresh scans ALL devices for active upgrades"
(`src/firmware/firmware_manager.py:337`). That full scan at a 7-second cadence
is the existing cost model, and it does not scale to a per-device gate.

### 9.3 Data fetch inside the loop

`_fetch_device_stats_for_monitoring` at
`src/firmware/firmware_manager.py:504-514` selects the scope and pages the
result:

```python
if site_filter:
    stats_resp = mistapi.api.v1.sites.stats.listSiteDevicesStats(
        self.apisession, site_filter, type="all", limit=1000
    )
else:
    stats_resp = mistapi.api.v1.orgs.stats.listOrgDevicesStats(
        self.apisession, self.org_id, type="all", fields="*", limit=1000
    )
return mistapi.get_all(response=stats_resp, mist_session=self.apisession)
```

Note `fields="*"` on the organization branch. That requests every field and
gives up the payload saving described in section 8.5. The portal should pass a
narrow field list instead.

`FirmwareUpgradeStatusChecker` repeats the same two calls in
`_fetch_site_stats` (`src/firmware/firmware_manager.py:3227-3238`) and
`_fetch_org_stats` (`src/firmware/firmware_manager.py:3240-3251`).

### 9.4 `FirmwareUpgradeStatusChecker`

The class starts at `src/firmware/firmware_manager.py:3112`.

**The staleness constant** is at `src/firmware/firmware_manager.py:3132`:

```python
STALE_UPGRADE_HOURS = 1  # WHY: default staleness cutoff shared across helpers
```

`_is_stale_upgrade` at `src/firmware/firmware_manager.py:3356-3374` applies it.
It requires the timestamp to be an `int` or `float` and greater than zero, then
divides the elapsed seconds by 3600 and compares against the constant.

`_categorize_status` at `src/firmware/firmware_manager.py:3340-3354` buckets the
`fwupdate.status` value:

- active: `inprogress`, `upgrading`, `downloading`
- failed: `failed`
- complete: `upgraded`, `success`

`_parse_fwupdate_data` at `src/firmware/firmware_manager.py:3319-3338` reads
`status`, `progress`, `timestamp`, `status_id`, and `will_retry`. That matches
the schema in section 5.4 exactly.

**`_extract_device_info` does not read `uptime`.** At
`src/firmware/firmware_manager.py:3282-3295` it reads `id`, `name`, `mac`,
`model`, `type`, `version`, `site_id`, and `last_seen`. It reads neither
`uptime` nor `serial`. The settle gate needs `uptime`. **The portal cannot reuse
this extractor unchanged.**

`_check_active_operations` at `src/firmware/firmware_manager.py:3610-3618` runs
five probes: `_check_ssr_upgrades`, `_check_stored_upgrades`,
`_check_audit_logs`, `_check_device_events`, and `_check_site_upgrades`.

`_safe_get_site_upgrade_data` at `src/firmware/firmware_manager.py:3743-3754`
calls `getSiteDeviceUpgrade` and treats an empty response body as "upgrade no
longer active". That is a useful pattern for the portal.

### 9.5 Where tracker state is persisted

| Artifact | Path used | Correct? | Citation |
|---|---|---|---|
| `ActiveUpgrades.json` | bare relative filename | **No** | `src/firmware/firmware_manager.py:3713` |
| `ActiveUpgradeOperations_*.csv` | `os.path.join("data", ...)` | Yes | `src/firmware/firmware_manager.py:4001` |
| `FirmwareUpgradeStatus_*.csv` | routed by `DataExporter` | Yes | `src/firmware/firmware_manager.py:3966-3969` |
| `tuning_data.json` | `data` directory | Yes | `src/utils/rate_limiting.py:28` |
| `delay_metrics.json` | `data` directory | Yes | `src/utils/rate_limiting.py:29` |

---

## 10. Defects found

### 10.1 `ActiveUpgrades.json` is written to the working directory

**Severity: the defect the portal must not copy.**

`_check_stored_upgrades` at `src/firmware/firmware_manager.py:3710-3717`:

```python
def _check_stored_upgrades(self) -> None:
    """Check stored upgrade IDs from ActiveUpgrades.json."""
    print("   Checking for site-level upgrade operations...")
    upgrade_file = "ActiveUpgrades.json"  # WHY: persistent tracker path
    if not os.path.exists(upgrade_file):  # WHY: no tracker file yet
        print("   -> No site-level upgrade tracking file found")
        return
    org_upgrades = self._load_org_upgrades_from_file(upgrade_file)
```

`upgrade_file` is a bare relative filename. It resolves against the process
current working directory, not the `data` directory.
`_load_org_upgrades_from_file` at `src/firmware/firmware_manager.py:3699-3708`
opens the same bare path.

Consequences:

- The tracker is found or lost depending on where the operator launched the
  process.
- The file lands outside `data`, so it escapes the project data conventions and
  any cleanup that targets `data`.
- Two runs from two directories keep two separate trackers and neither sees the
  other.

The same class writes its CSV output correctly with
`os.path.join("data", ...)` at `src/firmware/firmware_manager.py:4001`. The
inconsistency is inside one class.

**The portal must resolve its own tracker path into `data`.**

### 10.2 Stale menu number in a docstring

`src/device/_utility_commands_show.py:384-385` claims menu 137:

```python
def run_top(self) -> None:
    """Menu 137: Run top command on switch/SRX (streaming)."""
    logging.info("Menu #137: Run Top (streaming)")
```

`run_top` is actually menu **125** (`MistHelper.py:4237`). The companion
`monitor_traffic` is menu **124** (`MistHelper.py:4234`). Menu 137 belongs to the
firmware status check (`MistHelper.py:3835`, `src/utils/operation_registry.py:110`).

Both the docstring and the log line are wrong. The log line is the worse of the
two, because it writes a false menu number into the audit trail.

### 10.3 Wrong SDK paths in the vendored documents

| Document claim | Runtime path | Citation |
|---|---|---|
| `mistapi.api.v1.utilities.upgrade.getSiteDeviceUpgrade()` | `mistapi.api.v1.sites.devices.getSiteDeviceUpgrade` | `documentation/api/utilities/GET_sites_site_id_devices_upgrade_upgrade_id.md:237` |
| `mistapi.api.v1.utilities.upgrade.cancelSiteDeviceUpgrade()` | `mistapi.api.v1.sites.devices.cancelSiteDeviceUpgrade` | `documentation/api/utilities/POST_sites_site_id_devices_upgrade_upgrade_id_cancel.md:56` |
| `mistapi.api.v1.sites.stats_-_devices.listSiteDevicesStats()` | `mistapi.api.v1.sites.stats.listSiteDevicesStats` | `documentation/api/sites/GET_sites_site_id_stats_devices.md:7591` |
| `mistapi.api.v1.orgs.stats_-_devices.listOrgDevicesStats()` | `mistapi.api.v1.orgs.stats.listOrgDevicesStats` | `documentation/api/orgs/GET_orgs_org_id_stats_devices.md:7600` |

The `stats_-_devices` fragment is not a valid Python identifier. It cannot be
imported. It looks like a generator artifact.

### 10.4 Wrong pagination advice in the event search documents

Both event search documents advise a `page` parameter that does not exist. See
section 3.4 for the citations. The real cursor is `search_after`.

### 10.5 Wrong menu attribution in a vendored document

`documentation/api/utilities/GET_sites_site_id_devices_upgrade_upgrade_id.md:254`
says the endpoint is "Used by Menu **90** (`FirmwareManager`)". The live
registration is menu 137 (`MistHelper.py:3835`). No menu 90 registration for the
firmware manager was found.

`documentation/api/sites/GET_sites_site_id_devices_events_search.md:268` says
"Menu **15** uses `searchOrgDeviceEvents` at org level", while
`documentation/api/orgs/GET_orgs_org_id_devices_events_search.md:269` says menus
2 and 63 use it. The two documents disagree. Live code also calls it from the
firmware status checker at `src/firmware/firmware_manager.py:3822`, which
neither document lists.

Treat the "MistHelper Notes" section of the vendored documents as unreliable.

---

## 11. Open gaps

| Gap | Impact | How to close |
|---|---|---|
| The full device event key list is unknown | The gate cannot hard-code connected-event keys for switches and gateways | Call `listDeviceEventsDefinitions` and record the result. See section 4.3 |
| The `SYSTEM_UPGRADE_*` family is only partly known | Three keys are proven in live code. Others may exist | Same call as above. Filter for the `SYSTEM_UPGRADE_` prefix |
| No enum for the device statistics `status` field | Cannot use `status` in gate logic | Do not use it. Use `uptime` and `version` |
| No documented settle time for switches and gateways | The 60-second and 120-second waits are the feature's own choice, not vendor guidance | Measure during pilot |

**Stated plainly**: sections 4.3 and the first two rows above are the only places
in this document where a needed fact could not be read from a source. Everything
else carries a citation.

---

## 12. Recommended gate design, one paragraph

Poll `searchOrgDeviceEvents` once every 20 seconds at organization scope. Set
`device_type` explicitly for each family in the fleet, because the default is
`ap`. Set `type` to the connected and restarted keys loaded from
`listDeviceEventsDefinitions` at start. Set `start` and `end` to a narrow window
and raise `limit` so each poll fits one page. When a device's connected or
restarted event arrives, switch that device to statistics confirmation. Call
`listOrgDevicesStats` once every 20 seconds for the whole fleet with a narrow
`fields` list, and confirm the device when its `uptime` reading falls below the
previous reading and its `version` differs from the pre-upgrade reading. Then
wait 60 seconds, plus another 60 seconds for access points, and capture. Keep
total polling under 360 calls per hour so the gate uses under 8 percent of the
5000-call quota. Store all tracker state under the `data` directory.
