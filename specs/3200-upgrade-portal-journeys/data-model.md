# Data Model: Upgrade portal journey harness

**Feature**: #3200 | **Date**: 2026-09-23 | **Plan**: [plan.md](plan.md)

This model holds the entities of the harness. The spec defines the meaning of
each entity. This file adds the fields, the relations, the rules, and the state
transitions. Each entity lives in the process that the table names.

| Entity | Process | Package |
| - | - | - |
| `SimulatedOrganization` and its parts | Journey server | `harness/cloud/state/` |
| `CallRecord`, `HarnessGap` | Journey server | `harness/cloud/session.py` |
| `JourneyClock`, `ClockMove` | Journey server | `harness/server/clock.py` |
| `JourneyCase` | Runner | `harness/journeys/catalog.py` |
| `StepRecord`, `JourneyRecord` | Runner | `harness/journeys/evidence/` |
| `HarnessRun`, `ParityRow`, `PerformanceSample`, `Budget`, `InspectionEntry` | Runner | `harness/run/` |

## The fleet

```text
SimulatedOrganization 1 --- n SimulatedSite 1 --- n SimulatedDevice 1 --- n SimulatedClient
SimulatedOrganization 1 --- n UpgradeJob n --- n SimulatedDevice
SimulatedOrganization 1 --- 1 FaultBook
```

### SimulatedOrganization

| Field | Rule |
| - | - |
| `org_id`, `name` | A fake identifier. See [Identifier rules](#identifier-rules). |
| `sites`, `devices`, `clients` | Indexes by identifier and by MAC address. |
| `versions` | For each model, the version that runs now and two or more newer versions (FR-022). |
| `jobs` | Each accepted `UpgradeJob`, by job identifier. |
| `events` | Each device event, in time order, for the event search. |
| `faults` | One `FaultBook`. |
| `clock` | The one `JourneyClock` of the server. |

### SimulatedSite

| Field | Rule |
| - | - |
| `site_id`, `name`, `org_id` | A fake identifier. The default fleet names Site 1 to Site 5 (FR-020). |
| `device_macs` | The devices of the site. |

### SimulatedDevice

| Field | Rule |
| - | - |
| `mac`, `device_id` | A fake identifier. |
| `site_id`, `model`, `serial` | The model decides the offered versions. |
| `device_type` | `ap`, `switch`, or `gateway`. A Mist Edge device gets the type and model that the shipped classifier refuses. |
| `gateway_class` | `junos` or `ssr` for a gateway. The shipped classifier makes the decision, and the fleet only supplies the model. |
| `version`, `uptime_anchor` | The running version and the time of the last boot on the journey clock. |
| `state` | See [Device states](#device-states). |
| `outcome` | `normal`, `failed`, `lost`, or `mismatch` (FR-030). |

### SimulatedClient

| Field | Rule |
| - | - |
| `mac`, `kind` | `wireless`, `wired`, or `guest`. |
| `site_id`, `device_mac` | The access point or the switch of the client. |
| `connected` | False while the device of the client reboots (FR-028). |
| `after_upgrade` | `stay`, `move` to a different access point, or `gone` (FR-023). |

The default fleet holds 29 devices and 84 clients. The large fleet holds 150
sites with 12 access points, 6 switches, and 2 gateways each. It also holds 5
Mist Edge devices and one site with 200 devices and 2,000 clients (FR-024 and
FR-025). A fixed seed builds each fleet, so each harness run gets the same
fleet.

### Identifier rules

- Each organization, site, device, and job identifier starts with
  `00003200-`. No live Mist tenant uses that prefix (FR-026).
- Each MAC address starts with `02:32:00`. That prefix is a locally
  administered range.
- The same seed and the same fleet give the same identifiers.

## Device states

```text
idle --write accepted--> queued --start time--> downloading --> rebooting --> reconnected
queued --cancel--> cancelled
downloading --outcome failed--> failed
rebooting --outcome lost--> offline (stays)
rebooting --outcome mismatch--> reconnected (other version)
```

| State | Cloud answer | Rule |
| - | - | - |
| `idle` | Online, running version | No accepted write names the device. |
| `queued` | Online, job status `queued` | The device waits for `start_time` on the journey clock (FR-033). |
| `downloading` | Online, job status `downloading` | The device writes firmware now. A cancel reports it as a device that continues (FR-035). |
| `rebooting` | Offline, clients disconnected | The device waits for `reboot_at` when the write sets it. |
| `reconnected` | Online, new version, smaller uptime, reconnect event | The clients reconnect, except for the scripted changes (FR-029). |
| `failed` | Job status `failed` with the reported cause | The fault book sets the cause. |
| `offline` | Offline, no reconnect event | The run gets to the settle deadline. |
| `cancelled` | Job status `cancelled` | Only a device in `queued` can move to this state. |

Each move occurs at a scripted interval on the journey clock. The default
intervals are 30 seconds in `queued`, 120 seconds in `downloading`, and 90
seconds in `rebooting`.

## Upgrade jobs

### UpgradeJob

| Field | Rule |
| - | - |
| `job_id` | A fake identifier. |
| `call` | The SDK call name of the write, for example `upgradeOrgDevices`. |
| `scope` | `org`, `site`, `ssr`, or `device`. |
| `scope_id` | The organization identifier or the site identifier. |
| `device_macs` | The devices that the body selects. |
| `body` | A copy of the write body with no credential. |
| `created_at` | The journey time of the accepted write. |

The job status comes from the states of its devices. The answer of each status
read follows the OpenAPI schema of research R-05.

| Device states | Job status |
| - | - |
| Each device in `queued` | `queued` |
| One or more devices in `downloading` | `downloading` |
| One or more devices in `rebooting` | `upgrading` |
| Each device in `reconnected` with the target version | `completed` |
| More failures than the maximum of the body | `failed` |
| A cancel call on the job | `cancelled` |

### Write key

The write key of an accepted write is the call, the scope identifier, the
sorted device or site identifiers, and the device type. SR-005 requires one
write for each planned write and each claimed child. The harness checks that
each write key occurs one time in the ledger.

### FaultBook

| Field | Rule |
| - | - |
| `device_outcomes` | For a MAC address, the outcome, the cause, and the version after. |
| `write_answers` | For a call and a match rule, the answer `accept`, `reject` with a status of 400 or more, or `uncertain`. |
| `uses` | `once` or `always`. A `once` entry ends after its first match. |

An `uncertain` answer applies the write and then gives the caller no answer
(FR-032). The answer has the shape that `mistapi` gives when the transport
fails: `status_code` is `None`, and `data` is empty.

## The call ledger

### CallRecord

| Field | Rule |
| - | - |
| `sequence` | A number that grows by one for each call. |
| `call`, `method`, `path`, `template` | The SDK call name, the method, the path, and the route template. |
| `scope`, `identifiers` | The organization, the site, the device, or the job. |
| `body` | A copy with each credential key removed. |
| `status`, `kind` | The answer status. The kind is `answer`, `uncertain`, `shape_refused`, or `gap`. |
| `journey_time`, `wall_time` | The two clocks at the call. |
| `journey`, `step`, `request` | The marker of the journey control, and the request number or `background`. |
| `handler_seconds` | The time in the handler, for research R-12. |

### HarnessGap

| Field | Rule |
| - | - |
| `method`, `path`, `query_keys` | The unknown call. |
| `first_journey`, `first_step`, `count` | Where the call occurs first, and how many times. |

## The journey clock

| Field | Rule |
| - | - |
| `start` | The journey time at the start of the server. |
| `multiple` | The ratio of journey time to wall time. The default is 60. |
| `moves` | Each `ClockMove`: the wall time and the seconds. A move is never negative. |
| `sleeps` | Each sleep of the run driver, from `RehearsalClock.sleeps()`. |

## The journeys

### JourneyCase

| Field | Rule |
| - | - |
| `identifier` | A catalog identifier. A case that runs in each mode ends in `-S` or `-M`. |
| `story` | `US1` to `US8`. |
| `mode` | `single`, `multi`, or `shared`. |
| `families` | One of `A`, `S`, `G`, `AS`, `AG`, `SG`, `ASG`, or none. |
| `fault` | The fault identifier, or none. |
| `fleet` | `default` or `large`. |
| `server` | `shared` or `fresh`. A case that changes a lock, a session, or the clock uses `fresh`. |
| `capabilities` | The C identifiers that the case proves. |
| `expected_errors` | Each console text and each HTTP status that the case expects (FR-060). |
| `step_limit` | The time limit of each step, in wall seconds. |
| `issue` | The number, the kind `gap` or `defect`, and the symptom text that the case asserts. |

A case with an issue becomes a strict `xfail`. The case must see the symptom of
its issue, or the case fails.

### StepRecord

| Field | Rule |
| - | - |
| `number`, `name`, `url` | The step in sequence. |
| `wall_start`, `wall_end`, `journey_start`, `journey_end` | The four times of FR-061. |
| `screenshots` | One after the checks, and one at the problem for a failed step. |
| `console_errors`, `page_errors`, `failed_requests`, `error_responses` | The events of FR-059. |
| `navigation`, `api_timings` | The browser timing of research R-12. |
| `checks` | Each check name and its result. |
| `cloud_calls` | The ledger count of the step. |
| `result` | `passed` or `failed`. |

### JourneyRecord

| Field | Rule |
| - | - |
| `case`, `outcome` | `passed`, `failed`, `xfailed`, `xpassed`, or `skipped`. |
| `steps` | Each `StepRecord`. |
| `writes` | Each write key and its count. |
| `traps`, `gaps` | The trap counters and each `HarnessGap`. |
| `artifacts` | The trace, the server log excerpt, and the runner log excerpt. |

## The harness run

### HarnessRun

| Field | Rule |
| - | - |
| `run_id` | The UTC time and a short random suffix, for example `20260923T151200Z-4f2a`. |
| `fleet`, `selection`, `workers`, `multiple` | The options of the command. |
| `revision` | The Git commit of the code. |
| `started`, `ended` | Wall times. |

### ParityRow

| Field | Rule |
| - | - |
| `capability`, `name`, `group` | C01 to C54. The group `shared` holds the sign-in, the sign-out, and the theme control (FR-079). |
| `families` | The family combinations that apply. |
| `testids` | The `data-testid` values or fixed prefixes of the capability. |
| `single`, `multi` | `proven`, `partial`, `missing`, or `defect` (FR-073). A shared row has one status. |
| `journeys` | The cases that prove each status. |
| `verdict`, `issue` | `parity`, or `gap` with one issue number. |
| `out_of_date` | True when a gap case passes (FR-075). The run then fails. |

The parity percentage is the number of `parity` rows divided by the number of
rows (FR-076).

### PerformanceSample

| Field | Rule |
| - | - |
| `fleet`, `journey`, `step` | Where the sample occurs. |
| `kind` | `page`, `api`, or `poll`. |
| `method`, `path_template` | The path with each identifier replaced by its name. |
| `server_ms`, `ttfb_ms`, `dom_ms`, `load_ms`, `api_ms` | The timings of research R-12. |
| `cloud_calls` | The ledger count of the request. |

### Budget

| Field | Rule |
| - | - |
| `measure`, `fleet`, `limit` | A row of PR-008, or a named budget of PR-009 with its cause. |
| `value`, `result` | The 95th percentile, and `pass` or `breach`. |
| `issue` | The issue number of a breach (PR-010). |
| `delta` | The change from the earlier report (PR-011). |

### InspectionEntry

| Field | Rule |
| - | - |
| `screenshot`, `journey`, `step` | The screenshot that the engineer examines. |
| `verdict` | `ok`, `defect`, or `unclear`. |
| `note`, `issue` | The note, and the issue number of a defect (FR-067). |
