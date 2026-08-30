# Data Model: Upgrade Pre-Check and Post-Check Portal

**Feature**: 1823-upgrade-capture-portal
**Date**: 2026-08-19
**Source**: `spec.md` Key Entities, plus `research/storage-and-locking.md`

## 1. Overview

The model holds three stored entities and four computed entities.

| Entity | Kind | Store | Key |
| --- | --- | --- | --- |
| Capture | Stored document | ArangoDB collection `upgrade_captures` | `cap-{run_hex}-{ordinal}` |
| UpgradeRun | Stored document | ArangoDB collection `upgrade_runs` | `run-{uuid4hex}` |
| CaptureForRun | Stored edge | ArangoDB edge collection `capture_for_run` | `edge-{capture_key}` |
| SiteLock | Stored value, short life | Redis string | `misthelper:lock:site:{org_id}:{site_id}` |
| Comparison | Computed | None | Derived from two captures |
| DeviceDelta | Computed | None | Derived from two `device_index` maps |
| ClientDelta | Computed | None | Derived from two client lists |

Two words never appear in this model. The word `snapshot` is reserved, because the
cloud upgrade body already uses that field name for a Junos file action. The word
`capture` in this feature always means a record of site state, never a packet
capture.

## 2. Schema version convention

The repository holds two conventions that disagree. This feature chooses **the
integer convention** and records the choice here.

- `schema_version` is an integer.
- The first release writes the value `1`.
- A reader that finds a higher value than it understands refuses to render and
  says so plainly.
- A range query on the field works, which a text value does not support.

## 3. Capture

A Capture holds everything the portal read from one site at one moment.

### 3.1 Top-level fields

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `_key` | string | yes | `cap-{run_hex}-{ordinal:02d}`. Holds no slash and no colon, so the key sanitizer leaves it alone. |
| `capture_id` | string | yes | Same value as `_key`. This is the natural business key. |
| `schema_version` | integer | yes | `1` in the first release. |
| `run_id` | string | yes | The owning UpgradeRun key. |
| `ordinal` | integer | yes | `1` for the pre-check. `2` for the post-check. Higher for a repeat. |
| `role` | string | yes | `pre` or `post`. |
| `org_id` | string | yes | Mist organization identifier. |
| `org_name` | string | yes | Shown in the interface and in an export. |
| `site_id` | string | yes | Mist site identifier. |
| `site_name` | string | yes | Shown in the interface and in an export. |
| `tier` | integer | yes | `2` or `3`. Tier 2 is the default. |
| `started_at` | string | yes | ISO 8601 in UTC. |
| `finished_at` | string | yes | ISO 8601 in UTC. |
| `duration_seconds` | number | yes | Measured, not estimated. |
| `actor_email` | string | yes | The signed-in operator. Never a credential. |
| `capture_status` | string | yes | `complete`, `partial`, or `failed`. Reports how much data the capture holds. This is not the lifecycle state. |
| `partial_reasons` | array of object | yes | Empty when `capture_status` is `complete`. |
| `state` | string | yes | The lifecycle state. See section 3.8. Reports how far the capture moved, not how much data it holds. |
| `verified` | boolean | yes | `true` only after the store read the key back and matched the digest. FR-031 requires this proof, because a successful write is not proof. Section 7.1 admits a capture into a comparison only when this field is `true`. |
| `stored_size_bytes` | integer | yes | The measured size of the stored document. Satisfies FR-032b. |
| `digests` | object | yes | See section 3.2. |
| `device_index` | object | yes | See section 3.3. |
| `devices` | array of object | yes | The full device records. |
| `clients` | object | yes | See section 3.4. |
| `extras` | object | no | Present only when `tier` is `3`. See section 3.5. |
| `counts` | object | yes | See section 3.6. |

### 3.2 `digests`

A flat map from a section name to a hexadecimal digest of that section. A
comparison reads the digests first. When two digests match, the comparison skips
the section and reports no change. This keeps the 3-second render target for a
large site.

```text
digests = {
  "devices":  "<hex>",
  "clients_wired": "<hex>",
  "clients_wireless": "<hex>",
  "clients_guest": "<hex>",
  "extras": "<hex>",        # absent at tier 2
  "whole":  "<hex>"
}
```

The digest input is the canonical JSON form of the section, with every volatile
field removed. A volatile field is one that changes without a real change in the
site. The volatile list is `timestamp`, `last_seen`, `uptime`, `_ts`, and any
counter of bytes or packets.

### 3.3 `device_index`

A flat map. The key is the device MAC address in lower case with no separator. The
value is a small fixed record. A comparison of two captures is a shallow map
comparison over this field, which is the reason the field exists.

```text
device_index = {
  "5c5b350e0001": {
    "name": "bld1-idf2-sw01",
    "type": "switch",
    "model": "EX4400-48P",
    "serial": "JW0000000000",
    "version": "23.4R2-S3.9",
    "status": "connected",
    "uptime": 1832140,
    "site_id": "<uuid>",
    "vc_role": "master",
    "vc_mac": "5c5b350e0001",
    "num_members": 2,
    "ip": "10.20.30.40"
  }
}
```

Rules for this field.

- The physical view fills this map. The capture path calls the inventory with
  `vc=True`, so every chassis member appears as its own entry.
- `vc_role` is `standalone` when the device is not a member of a virtual chassis.
- The map never holds a `timestamp`, because a timestamp makes every entry look
  new.

### 3.4 `clients`

```text
clients = {
  "wired":    [ ClientRecord, ... ],
  "wireless": [ ClientRecord, ... ],
  "guest":    [ ClientRecord, ... ]
}
```

A `ClientRecord` holds these fields.

| Field | Type | Notes |
| --- | --- | --- |
| `mac` | string | The match key. Lower case, no separator. |
| `hostname` | string | May be empty. |
| `ip` | string | May be empty. |
| `device_mac` | string | The access point or the switch that serves the client. |
| `device_name` | string | Shown in the moved-client report. |
| `port_id` | string | Wired only. |
| `vlan` | integer | May be absent. |
| `ssid` | string | Wireless and guest only. |
| `band` | string | Wireless only. |
| `rssi` | integer | Wireless only. From the client statistics call. |
| `snr` | integer | Wireless only. From the client statistics call. |
| `random_mac` | boolean | Wireless only. From the client search call. |
| `username` | string | May be empty. Never a password. |
| `manufacture` | string | Wired only. May be empty. |

The wireless list is a join. The portal calls `listSiteWirelessClientsStats` for
signal strength and `searchSiteWirelessClients` for the random MAC flag, then
joins the two results on `mac`. A client that appears in one source only still
enters the list, with the missing fields absent.

### 3.5 `extras`

Present only at tier 3. Each member is a list.

```text
extras = {
  "switch_ports": [ ... ],   # port state, speed, duplex, errors
  "poe": [ ... ],            # per-port power draw and budget
  "radios": [ ... ],         # per-radio channel, width, power
  "tunnels": [ ... ],        # gateway tunnel state
  "bgp_peers": [ ... ],      # peer state and prefix counts
  "alarms": [ ... ]          # open alarms at the moment of capture
}
```

### 3.6 `counts`

A small map of integers used by the summary line and by the comparison heading.

```text
counts = {
  "devices_total": 0, "devices_connected": 0, "devices_disconnected": 0,
  "gateways": 0, "switches": 0, "access_points": 0,
  "clients_wired": 0, "clients_wireless": 0, "clients_guest": 0
}
```

The history view reads `gateways`, `switches`, and `access_points` from this map
and names the device types of the stored capture set. FR-084a asks for that
column. The view lists the three words in the cascade order of section 4.1,
which runs gateways, then switches, then access points.

The view reads the device types from this map and never from the upgrade run.
One capture reads every device type at one time, so a capture set holds more
than one type. The run holds no single type either, because section 4.2 puts
`device_type` on one entry of `targets` and one run can carry many entries.

### 3.7 Validation rules

1. `ordinal` is 1 or greater.
2. `role` is `pre` when `ordinal` is 1.
3. `finished_at` is not earlier than `started_at`.
4. `capture_status` is `partial` only when `partial_reasons` holds at least one
   entry.
5. Each entry of `partial_reasons` holds `section`, `reason`, and `http_status`.
6. `stored_size_bytes` is greater than zero after a successful write.
7. Every key of `device_index` appears in `devices` and the reverse is also true.
8. `digests.whole` covers every present section.

### 3.8 State transitions

```text
pending -> collecting -> assembling -> writing -> verified
                                          |
                                          +-> write_failed
collecting -> partial -> assembling
any state that is not final -> failed
```

The final states are `verified`, `write_failed`, and `failed`. A capture in a
final state moves nowhere. A repeat capture takes a higher ordinal and becomes a
new document.

Every state that is not final reaches `failed`, which matches the run diagram of
section 4.1. An earlier version of this diagram allowed `failed` from
`collecting` alone. A capture that then failed while it assembled had nowhere to
move, so it stayed in `assembling` for ever and appeared as a live capture in the
index of section 9 that finds every run still active after a restart.

`verified` means the portal read the key back and matched the digest. Only a
`verified` capture may take part in a comparison. FR-031 requires this step,
because `WriteResult.success` alone is not proof.

## 4. UpgradeRun

An UpgradeRun ties one site, one operator, one pre-check, one upgrade, and one
post-check together.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `_key` | string | yes | `run-{uuid4hex}`. |
| `run_id` | string | yes | Same value as `_key`. The natural business key. |
| `schema_version` | integer | yes | `1`. |
| `org_id`, `org_name` | string | yes | |
| `site_id`, `site_name` | string | yes | |
| `actor_email` | string | yes | The operator who owns the run. |
| `browser_id` | string | yes | Identifies the browser that holds the lock. |
| `created_at` | string | yes | ISO 8601 in UTC. |
| `updated_at` | string | yes | Written on every state change. |
| `state` | string | yes | See section 4.1. |
| `tier` | integer | yes | The capture tier for both captures. |
| `targets` | array of object | yes | One entry for each device the run upgrades. |
| `options` | object | yes | The upgrade options the operator chose. |
| `phases` | array of object | yes | One entry for each cascade phase. |
| `stop_request` | object or null | yes | See section 4.3. |
| `pre_capture_id` | string or null | yes | |
| `post_capture_id` | string or null | yes | |
| `error` | object or null | yes | Holds `stage`, `message`, and `at`. |

### 4.1 Run states

```text
created
  -> pre_capture_running -> pre_capture_done
  -> awaiting_confirmation
  -> upgrade_submitting -> upgrade_running
  -> settling_gateways -> settling_switches -> settling_aps -> settling_clients
  -> post_capture_running -> post_capture_done
  -> complete

any state -> stopping -> stopped
any state -> failed
```

The cascade order is fixed: gateways, then switches, then access points, then
wireless clients. A phase starts only after the phase before it reports settled.

### 4.2 `targets` entry

| Field | Type | Notes |
| --- | --- | --- |
| `mac` | string | Lower case, no separator. |
| `name` | string | |
| `device_type` | string | `ap`, `switch`, or `gateway`. |
| `gateway_family` | string or null | `junos` or `ssr`. Null unless `device_type` is `gateway`. |
| `model` | string | |
| `version_before` | string | |
| `version_target` | string | |
| `version_after` | string or null | Filled after the settle gate passes. |
| `upgrade_id` | string or null | Returned by the cloud. Needed by the cancel call. |
| `scope` | string | `site` or `org`. A session smart router always uses `org`. |
| `state` | string | `pending`, `submitted`, `rebooting`, `settled`, `cancelled`, or `failed`. |
| `uptime_before` | integer or null | The gate compares against this value. Null means the portal read no uptime. |
| `reboot_seen_at` | string or null | Set when the uptime decreases. |
| `settled_at` | string or null | |

If the portal read no uptime, `uptime_before` is null, never zero. A stored zero
would make every later reading look larger. The settle gate would then never see
the reboot, and the run would wait forever.

The `scope` field exists because the cancel path differs by family. A session
smart router has an organization-scope cancel only, so the run submits every
session smart router upgrade at organization scope.

### 4.3 `stop_request`

Null until an operator asks for a stop.

```text
stop_request = {
  "requested_by": "<email>",
  "requested_at": "<iso>",
  "confirmation_text": "STOP",
  "scope": "run",
  "outcome": {
     "cancelled": ["<mac>", ...],
     "already_writing": ["<mac>", ...],
     "no_cancel_available": ["<mac>", ...],
     "message": "<plain sentence for the operator>"
  }
}
```

`no_cancel_available` stays empty in the first release, because a cancel path
exists for every family in scope. The field exists so that FR-038f has a place to
report a future gap without a schema change.

## 5. CaptureForRun edge

A thin edge so that a graph traversal can move from a run to its captures.

| Field | Type | Notes |
| --- | --- | --- |
| `_key` | string | `edge-{capture_key}`. |
| `_from` | string | `upgrade_runs/{run_key}`. |
| `_to` | string | `upgrade_captures/{capture_key}`. |
| `role` | string | `pre` or `post`. |

### 5.1 Run-less capture (FR-100)

A capture that names no run writes no run document and no edge. The portal
derives its key from a fresh nonce, so two run-less captures never share a key.
The `run_id` field of that capture stays empty. The upgrade start adopts the
standalone pre-check and writes the `pre` edge at adoption time. A one-time
repair at worker start removes any dangling edge that an earlier build wrote for
an invented run.

## 6. SiteLock

The lock lives in Redis and never in process memory. The existing portal keeps its
duplicate guard in memory, which does not survive a restart. This feature must
work across worker processes and across a restart.

| Item | Value |
| --- | --- |
| Key | `misthelper:lock:site:{org_id}:{site_id}` |
| Value | JSON with `actor_email`, `browser_id`, `lock_token`, `run_id`, `acquired_at`, `refreshed_at` |
| Acquire | One atomic `SET key value NX EX 300` |
| Refresh | A Lua script that compares `lock_token` and then extends the expiry |
| Release | A Lua script that compares `lock_token` and then deletes the key |
| Cooldown | 300 seconds. After the cooldown a different operator may take over. |
| Takeover | Requires the typed word `CONFIRM` |
| Resume | The same `actor_email` and `browser_id` may continue without typing |

Viewing data never needs the lock and never needs typed text.

## 7. Computed entities

### 7.1 Comparison

Built from two verified captures with the same `site_id`. Holds a header, a device
section, a client section, and a statistics section. The comparison compares
`digests` first and skips a section whose digest matches.

### 7.2 DeviceDelta

One entry for each MAC address in the union of the two `device_index` maps.

| Outcome | Meaning |
| --- | --- |
| `unchanged` | Every compared field matches |
| `changed` | At least one field differs. The entry lists each field with the value before and the value after. |
| `added` | Present in the post-check only |
| `removed` | Present in the pre-check only |

The compared fields are `status`, `version`, `model`, `name`, `ip`, `vc_role`, and
`num_members`. `uptime` is excluded from the change test, because uptime always
differs. The gate reads `uptime` separately.

### 7.3 ClientDelta

One entry for each MAC address in the union of the two client lists. The match key
is `mac` alone.

| Outcome | Meaning |
| --- | --- |
| `present` | In both captures on the same serving device |
| `moved` | In both captures on a different serving device. Reported as its own statistic, never as a loss. |
| `added` | In the post-check only |
| `missing` | In the pre-check only |

### 7.4 Statistics

Counts for each outcome above, plus the client return rate, plus the device
version change count, plus the elapsed time of the whole run.

## 8. ArangoDB indexes

| Collection | Index | Fields | Reason |
| --- | --- | --- | --- |
| `upgrade_captures` | persistent | `site_id`, `started_at` | The history view lists captures for one site in time order |
| `upgrade_captures` | persistent | `run_id`, `ordinal` | Find the pre-check and post-check of one run |
| `upgrade_captures` | persistent | `org_id`, `started_at` | The organization history view |
| `upgrade_captures` | persistent | `actor_email` | Show an operator their own work |
| `upgrade_runs` | persistent | `site_id`, `created_at` | The run history for one site |
| `upgrade_runs` | persistent | `state` | Find every run that is still active after a restart |
| `upgrade_runs` | persistent | `actor_email`, `created_at` | The operator history view |
| `capture_for_run` | edge | `_from`, `_to` | Created by the edge collection itself |

## 9. Registry entries

Two rows join `ENDPOINT_PRIMARY_KEY_STRATEGIES` in
`src/refactors/endpoint_primary_key_strategies.py`.

| Operation | Strategy | Key field |
| --- | --- | --- |
| `upgradeCaptureWrite` | `natural_pk` | `capture_id` |
| `upgradeRunWrite` | `natural_pk` | `run_id` |

`natural_pk` is the only correct choice.

- `composite_pk` dual-writes to Redis, and the Redis JSON writer sets an expiry on
  every key (`src/db/redis_writer.py:598`). FR-032a forbids an expiring path.
- `auto_increment_with_unique` mints a fresh identifier on every write
  (`src/db/arango_writer.py:4039`). A retry would duplicate the record instead of
  replacing it.
