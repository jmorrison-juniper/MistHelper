# Contract: The stand-in cloud

**Feature**: `specs/1992-upgrade-rehearsal/` | **Date**: 2026-09-04

This contract records the call that each shipped reader makes through each
attachment point. `src/upgrade_portal/app/seam_shapes.py` states the rule of
issue #1991. A stand-in must answer the call that the caller really makes. This
document is the record of those calls.

The rehearsal suite reads this contract at run time. It compares the recorded
keyword names against the call that the stand-in received. A shipped reader that
changes its call then fails the suite.

## 1. The device statistics read

**Attachment point**: `mistapi.api.v1.orgs.stats.listOrgDevicesStats`

**Caller**: `gate.read_fleet_statistics` at `src/upgrade_portal/upgrade/gate.py`
line 845.

**Call**: 2 positional arguments, and the keywords `type`, `site_id`, `fields`,
and `limit`.

```python
def listOrgDevicesStats(  # The stand-in copies this signature exactly.
    session: Any,
    org_id: str,
    *,
    type: str = "all",
    site_id: str | None = None,
    fields: str | None = None,
    limit: int = 100,
    **extra: Any,
) -> StandInResponse: ...
```

**Answer**: A `StandInResponse` with `status_code` set to 200. The `data` field
holds a mapping of 3 keys.

| Key | Type | Meaning |
| - | - | - |
| `results` | `list[dict]` | One record for each device of the fleet. |
| `total` | `int` | The count of the records. |
| `next` | `str \| None` | The URL of the next page, or `None`. |

Each record holds `mac`, `type`, `version`, `uptime`, and `last_seen`.
`gate.reading_from_record` reads those five fields.

**Rule**: `total` always equals the length of `results` on a whole read. A test
that proves the page guard sets a larger `total`, and the guard then reports a
short read.

## 2. The page walk

**Attachment point**: `mistapi.get_all`

**Caller**: `gate.read_fleet_statistics` at line 856.

**Call**: The keywords `mist_session` and `response`.

```python
def get_all(mist_session: Any, response: Any) -> list[dict]: ...
```

**Answer**: The `results` list of the response. The stand-in reads the same body
that the shipped page helper reads, so the two agree.

## 3. The device event search

**Attachment point**: `mistapi.api.v1.orgs.devices.searchOrgDeviceEvents`

**Caller**: `events.read_device_events` at
`src/upgrade_portal/upgrade/events.py` line 430.

**Call**: 2 positional arguments, and the keywords `device_type`, `start`,
`end`, `limit`, and `search_after`.

```python
def searchOrgDeviceEvents(  # The stand-in copies this signature exactly.
    session: Any,
    org_id: str,
    *,
    device_type: str = "ap",
    start: str | None = None,
    end: str | None = None,
    limit: int = 100,
    search_after: str | None = None,
    **extra: Any,
) -> StandInResponse: ...
```

**Answer**: A `StandInResponse` with `status_code` set to 200. The `data` field
holds `results`, `total`, and `next`. Each event record holds `mac`, `type`, and
`timestamp`.

**Rules**:

1. The default of `device_type` is `ap`. A caller that passes no device type
   therefore reads access points only. FR-010 asks for that behavior, and the
   real cloud shares it.
2. `start` and `end` arrive as text, and both hold epoch seconds. The shipped
   caller passes text, because the installed library types both as text.
3. The stand-in answers an event only when the timestamp falls inside the
   window. The window comes from `events.build_window` and the clock.

## 4. The event key catalogue

**Attachment point**:
`mistapi.api.v1.const.device_events.listDeviceEventsDefinitions`

**Caller**: `events.EventCatalogue` in the same module.

**Call**: 1 positional argument.

```python
def listDeviceEventsDefinitions(session: Any) -> StandInResponse: ...
```

**Answer**: A `StandInResponse` that lists the event definitions. The list holds
the reconnect keys that `events.reconnect_macs` matches.

**Rule**: The catalogue answers one time for the life of the process, because
the shipped class caches the answer. A test that needs a fresh catalogue clears
that cache first.

## 5. The upgrade endpoint resolver

**Attachment point**: `src.firmware.upgrade_service._resolve_endpoint`

**Callers**: `read_upgrade_status` at `src/firmware/upgrade_service.py` line
1620, and `cancel_upgrade` at line 1486. `stop.py` reaches both.

**Call**: 1 positional argument, which is the endpoint name.

```python
def _resolve_endpoint(name: str) -> Callable[..., StandInResponse]: ...
```

**Answer**: The stand-in returns a callable for each read endpoint and each
cancel endpoint. It raises `RehearsalFirmwareError` for each write endpoint.

| Endpoint name | What the stand-in does |
| - | - |
| `getSiteDeviceUpgrade` | Answers the upgrade status of the site scope. |
| `getOrgDeviceUpgrade` | Answers the upgrade status of the organization scope. |
| `getSiteSsrUpgrade` | Answers the status of a session smart router. |
| `cancelSiteDeviceUpgrade` | Records the cancel and answers the outcome. |
| `cancelOrgDeviceUpgrade` | Records the cancel and answers the outcome. |
| `cancelOrgSsrUpgrade` | Records the cancel of the organization scope. |
| `upgradeSiteDevices` | Raises `RehearsalFirmwareError`. |
| `upgradeDevice` | Raises `RehearsalFirmwareError`. |
| `upgradeOrgSsrs` | Raises `RehearsalFirmwareError`. |

**The upgrade status answer**: The status carries these fields. The shipped
reader `_normalize_status` reads each one.

| Field | Type | Meaning |
| - | - | - |
| `status` | `str` | The state of the upgrade job. |
| `current_phase` | `str` | The phase name that the cloud reports. |
| `targets` | `dict` | Holds `reboot_in_progress` as a list of addresses. |
| `upgrade_id` | `str` | The identifier that the submission returned. |
| `status_known` | `bool` | True when the answer is an upgrade job. |

**Rule**: The organization scope read of a session smart router answers device
statistics and no upgrade job. The stand-in therefore sets `status_known` to
false for that read. `stop.status_is_known` at `stop.py:192` reads that field.

## 6. The response object

The stand-in builds one small record for every answer.

```python
@dataclass(frozen=True, slots=True)
class StandInResponse:
    data: Any           # The body, as the shipped readers expect it.
    status_code: int = 200   # The HTTP status that the page guard reads.
    headers: Mapping[str, str] = field(default_factory=dict)
```

**Rule**: The record holds no method. Every shipped reader takes the two
attributes with `getattr`, so a plain record answers the whole contract.

## 7. The call record

The stand-in records each call. A test reads the record and proves the shape.

| Field | Type | Meaning |
| - | - | - |
| `name` | `str` | The attachment point that the caller reached. |
| `positional` | `tuple` | The arguments that the caller passed by position. |
| `keywords` | `frozenset[str]` | The keyword names that the caller passed. |
| `at` | `float` | The clock reading of the call. |

**Rule**: The count of the three firmware write names always stays at zero.
SC-005 reads that count.
